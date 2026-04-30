import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache
import logging
from Backend.config import ALLOWED_METRICS, ALLOWED_CALC_TYPES



#log1p=log(1+x)

# GÜVENLİK: SQL Injection / parametre manipülasyonunu önlemek için
# izin verilen metrik ve hesaplama tipleri sabit listede tanımlanır.
# Bu listelerin dışındaki hiçbir değer işleme alınmaz.



class HRDataEngine:
    def __init__(self, file_path: str):
        """
        Veri motorunu başlatır ve güvenlik kontrolü yapar.

        Path Traversal saldırılarını engellemek için:
        - Kullanıcının verdiği path resolve edilir (mutlak hale getirilir)
        - Sadece Data klasörü altındaki dosyalara izin verilir
        """
        # Backend klasörünün üstü
        BASE_DIR = Path(__file__).parent
        allowed_base = (BASE_DIR / "Data").resolve()

        # Kullanıcının verdiği path'i mutlak hale getir
        resolved = Path(file_path).resolve()

        # Güvenlik kontrolü: resolved path allowed_base ile başlamalı
      

    if not str(resolved).startswith(str(allowed_base)):
        raise ValueError("Güvensiz dosya yolu!")



        self.file_path = resolved

        self.df = pd.DataFrame()
        self.load_and_clean_data()

    def load_and_clean_data(self):
        """
        ETL (Extract-Transform-Load) işlemi:
        1. CSV'yi oku (Extract)
        2. Eksik kritik verileri temizle (Transform)
        3. Veriyi analiz için hazır hale getir (Load)
 
        Veri kalitesi (Data Quality) güvencesi:
        - Salary, PerformanceScore, EngagementSurvey eksik olan satırlar çıkarılır.
        - Tarih sütunu standart formata dönüştürülür.
        - Cinsiyet sütunundaki boşluklar temizlenir ('M ' → 'M').
        - Log dönüşümü ile maaş dağılımı normalize edilir.
        """
        try:
            # Kritik sütunlarda eksik değer olan satırlar veri bütünlüğü için çıkarılır.
            raw_data = pd.read_csv(self.file_path)
            self.df = raw_data.dropna(subset=['Salary', 'PerformanceScore', 'EngagementSurvey']).copy()
            # Tarih sütunu datetime formatına çevrilir; hatalı değerler NaT olur.
            self.df['DateofHire'] = pd.to_datetime(self.df['DateofHire'], errors='coerce')
            #Maaş dağılımını normalize etmek için logaritmik dönüşüm uygulanır.
            # Bu, aykırı değerlerin (outlier) etkisini azaltır.
            self.df['Log_Salary'] = np.log1p(self.df['Salary'])
            # Veri setindeki 'M ' gibi boşluklu değerleri temizle.
            # Bu olmadan cinsiyet pivot tablosu yanlış hesaplar.
            self.df['Sex'] = self.df['Sex'].str.strip()
            logging.info(f"Veri başarıyla yüklendi. Toplam geçerli kayıt: {len(self.df)}")
        except FileNotFoundError:
            logging.error(f"Kritik Hata: {self.file_path} bulunamadı!")
            self.df = pd.DataFrame()

    def calculate_dynamic_kpi(self, department: str, metric: str, calc_type: str) -> dict:
        """
        Kullanıcının dinamik olarak tanımladığı KPI'ları hesaplar.
        Whitelist tabanlı input validation ile güvenli hale getirilmiştir.
 
        Args:
            department (str): Hedef departman adı. "All" tüm şirketi kapsar.
            metric (str): Hesaplanacak sütun adı (ALLOWED_METRICS içinden).
            calc_type (str): Hesaplama tipi (ALLOWED_CALC_TYPES içinden).
 
        Returns:
            dict: Hesaplama sonucu veya hata mesajı.
        """
        if self.df.empty:
            return {"error": "Veri seti boş veya yüklenemedi."}

        # GÜVENLİK: Sadece izin verilen metrik ve hesaplama tiplerine izin ver
        if metric not in ALLOWED_METRICS:
            return {"error": f"Geçersiz metrik: {metric}. İzin verilenler: {ALLOWED_METRICS}"}
        if calc_type not in ALLOWED_CALC_TYPES:
            return {"error": f"Geçersiz hesaplama tipi. İzin verilenler: {ALLOWED_CALC_TYPES}"}

        target_df = self.df if department == "All" else self.df[self.df['Department'] == department]
        if target_df.empty:
            return {"error": f"'{department}' departmanı bulunamadı."}

        try:
            operations = {
                "mean": target_df[metric].mean,
                "sum": target_df[metric].sum,
                "max": target_df[metric].max,
                "count": target_df[metric].count,
            }
            val = operations[calc_type]()
            return {
                "department": department,
                "metric": metric,
                "calculation": calc_type,
                "value": round(float(val), 2),
                "total_employees": len(self.df),
                "status": "Reliable"
            }
        except Exception as e:
            logging.error(f"KPI Hesaplama Hatası: {str(e)}")
            return {"error": "Matematiksel hesaplama hatası."}

    def get_risk_summary(self) -> dict:
        """Yapay zeka için özet risk verilerini hazırlar."""
        if self.df.empty:
            return {}

        avg_salary = self.df['Salary'].mean()
        risk_df = self.df[
            (self.df['Salary'] < avg_salary) &
            (self.df['PerformanceScore'].isin(['Exceeds', 'Fully Meets'])) &
            (self.df['EngagementSurvey'] < 3.5)
        ]

        return {
            "total_employees": len(self.df),
            "average_salary": round(avg_salary, 2),
            "flight_risk_count": len(risk_df),
            "average_engagement": round(self.df['EngagementSurvey'].mean(), 2)
        }

    def get_correlation_matrix(self) -> dict:
        """Değişkenler arasındaki istatistiksel ilişkiyi hesaplar."""
        if self.df.empty:
            return {}

        numeric_df = self.df.select_dtypes(include=[np.number])
        corr_matrix = numeric_df.corr().round(2)
        critical_corr = corr_matrix.loc[
            'Salary',
            ['EngagementSurvey', 'EmpSatisfaction', 'SpecialProjectsCount']
        ]
        return critical_corr.to_dict()

    def analyze_gender_pay_gap(self) -> dict:
        if self.df.empty:
            return {}

        df = self.df.copy()
        df['Sex'] = df['Sex'].str.strip()

        pivot = df.pivot_table(
        values='Salary',
        index='Department',
        columns='Sex',
        aggfunc='mean'
        ).round(2).fillna(0)
        
        if 'M' in pivot.columns and 'F' in pivot.columns:
            pivot['Pay_Gap_Percentage'] = (
            ((pivot['M'] - pivot['F']) / pivot['M'].replace(0, float('nan'))) * 100
            ).round(1).fillna(0)

        return pivot.to_dict(orient='index')



    def predict_flight_risk_advanced(self) -> list:
        """
        Algoritmik İstifa Tahmini (Churn Prediction):
        Kural tabanlı (rule-based) model ile yüksek risk taşıyan
        çalışanları tespit eder.
 
        Risk Kriterleri (4 koşulun tamamı sağlanmalı):
        1. Bağlılık skoru 3.0'ın altında  → düşük motivasyon
        2. En az 2 yıldır şirkette         → öğrendiklerini götürme riski
        3. Özel projeye atanmamış          → gelişim fırsatı verilmemiş
        4. Hâlâ aktif çalışan              → işten çıkarılmamış
 
        NOT: self.df mutate edilmez, local kopya kullanılır.
        Bu olmadan her çağrıda df'e Hire_Year/Tenure_Years sütunları birikir.
 
        Returns:
            list: Yüksek risk taşıyan çalışanların listesi.
        """
        if self.df.empty:
            return []


        local_df = self.df.copy()
        current_year = pd.Timestamp.now().year

        # Kıdem hesabı: işe giriş yılından bugünü çıkar.
        local_df['Hire_Year'] = pd.to_datetime(local_df['DateofHire']).dt.year
        local_df['Tenure_Years'] = current_year - local_df['Hire_Year']

        # 4 koşulun tamamı AND operatörü ile birleştirilir.
        risk_conditions = (
            (local_df['EngagementSurvey'] < 3.0) &
            (local_df['Tenure_Years'] >= 2) &
            (local_df['SpecialProjectsCount'] == 0) &
            (local_df['Termd'] == 0)
        )

        # Frontend'e sadece gerekli sütunlar döndürülür (veri minimizasyonu).
        high_risk_employees = local_df[risk_conditions]
        return high_risk_employees[
            ['Employee_Name', 'Department', 'Salary', 'ManagerName']
        ].to_dict(orient='records')

