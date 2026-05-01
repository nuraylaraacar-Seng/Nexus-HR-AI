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

            # Kolon yeniden adlandırma: { standart_ad: kullanici_ad } → ters çevir
            if self.column_mapping:
                rename_map = {v: k for k, v in self.column_mapping.items() if v and v in raw.columns}
                raw = raw.rename(columns=rename_map)

            # Zorunlu kolonlardan sadece mevcut olanlarla dropna yap
            drop_cols = [c for c in ['Salary', 'PerformanceScore', 'EngagementSurvey'] if c in raw.columns]
            self.df = raw.dropna(subset=drop_cols).copy() if drop_cols else raw.copy()

            if 'DateofHire' in self.df.columns:
                self.df['DateofHire'] = pd.to_datetime(self.df['DateofHire'], errors='coerce')
            if 'Salary' in self.df.columns:
                self.df['Log_Salary'] = np.log1p(self.df['Salary'])
            if 'Sex' in self.df.columns:
                self.df['Sex'] = self.df['Sex'].str.strip()

            logging.info(f"Veri yüklendi: {self.file_path.name} | {len(self.df)} kayıt | Kolonlar: {list(self.df.columns)}")
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

        # Flight risk: mevcut kolonlara göre esnek hesapla
        mask = pd.Series([True] * len(self.df), index=self.df.index)
        if 'Salary' in self.df.columns:
            mask &= self.df['Salary'] < avg_salary
        if 'PerformanceScore' in self.df.columns:
            mask &= self.df['PerformanceScore'].isin(['Exceeds', 'Fully Meets'])
        if 'EngagementSurvey' in self.df.columns:
            mask &= self.df['EngagementSurvey'] < 3.5

        result["flight_risk_count"] = int(mask.sum())
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
            pivot['Pay_Gap_Percentage'] = (
                ((pivot['M'] - pivot['F']) / pivot['M'].replace(0, float('nan'))) * 100
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
        else:
            local['Tenure_Years'] = 999  # bilinmiyorsa koşulu geç

        mask = (local['EngagementSurvey'] < 3.0) & (local['Termd'] == 0) & (local['Tenure_Years'] >= 2)
        if 'SpecialProjectsCount' in local.columns:
            mask &= local['SpecialProjectsCount'] == 0

        cols = [c for c in ['Employee_Name', 'Department', 'Salary', 'ManagerName'] if c in local.columns]
        return local[mask][cols].to_dict(orient='records')
