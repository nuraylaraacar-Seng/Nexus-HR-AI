import pandas as pd
import numpy as np
from pathlib import Path
import logging
from Backend.config import ALLOWED_METRICS, ALLOWED_CALC_TYPES

class HRDataEngine:
    def __init__(self, file_path: str, column_mapping: dict = None):
        """
        file_path      : CSV dosyasının yolu
        column_mapping : { "Salary": "maas_tl", "Department": "bolum", ... }
                         None veya boş ise kolonlar olduğu gibi kullanılır.
        """
        BASE_DIR = Path(__file__).parent.parent
        allowed_bases = [
            (BASE_DIR / "Data").resolve(),
            (BASE_DIR / "Data" / "sessions").resolve(),
        ]
        resolved = Path(file_path).resolve()
        
        if not any(str(resolved).startswith(str(b)) for b in allowed_bases):
            raise ValueError(f"Güvensiz dosya yolu! İzin verilenler: {[str(b) for b in allowed_bases]}")

        self.file_path = resolved
        self.column_mapping = column_mapping or {}
        self.df = pd.DataFrame()
        self.load_and_clean_data()

    def load_and_clean_data(self):
        try:
            raw = pd.read_csv(self.file_path)

            # Kolon yeniden adlandırma
            if self.column_mapping:
                rename_map = {v: k for k, v in self.column_mapping.items() if v and v in raw.columns}
                raw = raw.rename(columns=rename_map)

            self.df = raw.copy()

            # --- 1. VERİ TEMİZLEME ---
            self.df.columns = self.df.columns.astype(str)

            if 'Termd' in self.df.columns:
                self.df['Termd'] = self.df['Termd'].astype(str).str.strip().str.lower()
                self.df['Termd'] = self.df['Termd'].apply(lambda x: 1 if x in ['yes', '1', 'true', '1.0'] else 0)

            if 'Department' in self.df.columns:
                self.df['Department'] = self.df['Department'].astype(str)
            
            if 'Sex' in self.df.columns:
                self.df['Sex'] = self.df['Sex'].astype(str).str.strip()


            # --- 2. Akıllı Veri Doldurma ---
            #eksik veriyi silmiyoruz , eksikleri  olarak dolduruyoruz.

            if 'Salary' in self.df.columns:
                # Sayısal olmayan bozuk maaş verilerini (örn: "Gizli") tespit edip NaN (boş) yap
                self.df['Salary'] = pd.to_numeric(self.df['Salary'], errors='coerce')
                
                # Her departmanın kendi maaş ortalamasını hesapla ve o departmandaki boş maaşları bununla doldur
                if 'Department' in self.df.columns:
                    dept_means = self.df.groupby('Department')['Salary'].transform('mean')
                    self.df['Salary'] = self.df['Salary'].fillna(dept_means)
                
                # Eğer hala boşluk kaldıysa (örneğin tüm departmanın maaşı gizliyse), şirketin genel ortalamasını hesapla
                global_mean = self.df['Salary'].mean()
                self.df['Salary'] = self.df['Salary'].fillna(global_mean if pd.notna(global_mean) else 0)
                
                # maaş algoritmasını logaritmesı alınır outlier'ı engelemek için
                self.df['Log_Salary'] = np.log1p(self.df['Salary'])
                
            # Backend/data_engine.py içindeki load_and_clean_data fonksiyonuna ekle:
            if 'Sex' in self.df.columns:
                # 1. Önce temizle ve string yap
                self.df['Sex'] = self.df['Sex'].astype(str).str.strip().str.title()
        
                # 2. Male -> M, Female -> F dönüşümünü yap 
                #Veri Normalizasyonu
                self.df['Sex'] = self.df['Sex'].replace({
                    'Male': 'M',
                    'Female': 'F',
                    'Man': 'M',
                    'Woman': 'F',
                    'Boy': 'M',
                    'Girl': 'F'
                })

            # Tarih formatını güvene al
            if 'DateofHire' in self.df.columns:
                self.df['DateofHire'] = pd.to_datetime(self.df['DateofHire'], errors='coerce')

            logging.info(f"Veri ZEKİCE yüklendi: {self.file_path.name} | {len(self.df)} kayıt | Kolonlar: {list(self.df.columns)}")
        
        except FileNotFoundError:
            logging.error(f"Dosya bulunamadı: {self.file_path}")
            self.df = pd.DataFrame()
        except Exception as e:
            logging.error(f"Veri yükleme hatası: {e}")
            self.df = pd.DataFrame()

    def calculate_dynamic_kpi(self, department: str, metric: str, calc_type: str) -> dict:
        if self.df.empty:
            return {"error": "Veri seti boş veya yüklenemedi."}
        if metric not in ALLOWED_METRICS:
            return {"error": f"Geçersiz metrik: {metric}"}
        if calc_type not in ALLOWED_CALC_TYPES:
            return {"error": f"Geçersiz hesaplama tipi: {calc_type}"}
        if metric not in self.df.columns:
            return {"error": f"'{metric}' kolonu bu dataset'te mevcut değil."}

        target = self.df if department == "All" else self.df[self.df.get('Department', pd.Series()) == department]
        if target.empty:
            return {"error": f"'{department}' departmanı bulunamadı."}

        try:
            ops = {"mean": target[metric].mean, "sum": target[metric].sum,
                "max": target[metric].max, "count": target[metric].count}
            val = ops[calc_type]()
            return {
                "department": department, "metric": metric,
                "calculation": calc_type, "value": round(float(val), 2),
                "total_employees": len(self.df), "status": "Reliable"
            }
        except Exception as e:
            logging.error(f"KPI hatası: {e}")
            return {"error": "Hesaplama hatası."}

    def get_risk_summary(self) -> dict:
        if self.df.empty:
            return {}
        result = {"total_employees": len(self.df)}
        if 'Salary' in self.df.columns:
            result["average_salary"] = round(self.df['Salary'].mean(), 2)
            avg_salary = result["average_salary"]
        else:
            result["average_salary"] = 0
            avg_salary = 0

        if 'EngagementSurvey' in self.df.columns:
            result["average_engagement"] = round(self.df['EngagementSurvey'].mean(), 2)
        else:
            result["average_engagement"] = 0

        # Flight risk(istifa riski): mevcut kolonlara göre esnek hesapla
        mask = pd.Series([True] * len(self.df), index=self.df.index)
        if 'Salary' in self.df.columns:
            mask &= self.df['Salary'] < avg_salary
        if 'PerformanceScore' in self.df.columns:
            mask &= self.df['PerformanceScore'].isin(['Exceeds', 'Fully Meets'])
        if 'EngagementSurvey' in self.df.columns:
            mask &= self.df['EngagementSurvey'] < 3.5

        
        # Maskeyi ana veriye kalıcı kolon olarak ekle:
        self.df['Is_Risk'] = mask.astype(int)
        
        result["flight_risk_count"] = int(mask.sum())
        
    
        if len(self.df) > 0:
            result["flight_risk_rate"] = round((result["flight_risk_count"] / len(self.df)) * 100, 1)
        else:
            result["flight_risk_rate"] = 0

        return result
    
    
    
    
    
    def get_correlation_matrix(self) -> dict:
        if self.df.empty:
            return {}
        numeric_df = self.df.select_dtypes(include=[np.number])
        if 'Salary' not in numeric_df.columns or len(numeric_df.columns) < 2:
            return {}
        corr = numeric_df.corr().round(2)
        available = [c for c in ['EngagementSurvey', 'EmpSatisfaction', 'SpecialProjectsCount'] if c in corr.columns]
        if not available:
            return {}
        return corr.loc['Salary', available].to_dict()

    def analyze_gender_pay_gap(self) -> dict:
        if self.df.empty:
            return {}
        needed = {'Salary', 'Department', 'Sex'}
        if not needed.issubset(self.df.columns):
            missing = needed - set(self.df.columns)
            logging.warning(f"Pay gap için eksik kolonlar: {missing}")
            return {}
        df = self.df.copy()
        df['Sex'] = df['Sex'].str.strip()
        pivot = df.pivot_table(values='Salary', index='Department', columns='Sex', aggfunc='mean').round(2).fillna(0)
        if 'M' in pivot.columns and 'F' in pivot.columns:
            # 0'a bölme hatasını engellemek için replace kullanıyoruz
            pivot['Pay_Gap_Percentage'] = (
                ((pivot['M'] - pivot['F']) / pivot['M'].replace(0, np.nan)) * 100
            ).round(1).fillna(0)
        return pivot.to_dict(orient='index')

    def predict_flight_risk_advanced(self) -> list:
        if self.df.empty:
            return []
        local = self.df.copy()
        needed = ['EngagementSurvey', 'Termd']
        if not all(c in local.columns for c in needed):
            logging.warning("Flight risk için EngagementSurvey veya Termd eksik.")
            return []

        if 'DateofHire' in local.columns:
            local['Hire_Year'] = pd.to_datetime(local['DateofHire'], errors='coerce').dt.year
            local['Tenure_Years'] = pd.Timestamp.now().year - local['Hire_Year']
            local['Tenure_Years'] = local['Tenure_Years'].fillna(0)
        else:
            local['Tenure_Years'] = 999  # bilinmiyorsa koşulu geç

        mask = (local['EngagementSurvey'] < 3.0) & (local['Termd'] == 0) & (local['Tenure_Years'] >= 2)
        if 'SpecialProjectsCount' in local.columns:
            mask &= local['SpecialProjectsCount'] == 0

        cols = [c for c in ['Employee_Name', 'Department', 'Salary', 'ManagerName'] if c in local.columns]
        return local[mask][cols].to_dict(orient='records')
    
