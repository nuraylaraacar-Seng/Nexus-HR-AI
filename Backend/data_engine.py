import pandas as pd
import numpy as np
from pathlib import Path
import logging
from Backend.config import ALLOWED_METRICS, ALLOWED_CALC_TYPES


class HRDataEngine:
    def __init__(self, file_path: str):
        BASE_DIR = Path(__file__).parent.parent  # Projenin kök dizini (Backend'in bir üstü)

        # Güvenli dizinler: hem varsayılan Data/ hem de session'a özel Data/sessions/
        allowed_bases = [
            (BASE_DIR / "Data").resolve(),
            (BASE_DIR / "Data" / "sessions").resolve(),
        ]

        resolved = Path(file_path).resolve()

        # Güvenlik kontrolü: dosya izin verilen dizinlerden birinde mi?
        if not any(str(resolved).startswith(str(base)) for base in allowed_bases):
            raise ValueError(
                f"Güvensiz dosya yolu! İzin verilen dizinler: {[str(b) for b in allowed_bases]}"
            )

        self.file_path = resolved
        self.df = pd.DataFrame()
        self.load_and_clean_data()

    def load_and_clean_data(self):
        """
        ETL (Extract-Transform-Load) işlemi:
        1. CSV'yi oku (Extract)
        2. Eksik kritik verileri temizle (Transform)
        3. Veriyi analiz için hazır hale getir (Load)
        """
        try:
            raw_data = pd.read_csv(self.file_path)
            self.df = raw_data.dropna(subset=['Salary', 'PerformanceScore', 'EngagementSurvey']).copy()
            self.df['DateofHire'] = pd.to_datetime(self.df['DateofHire'], errors='coerce')
            self.df['Log_Salary'] = np.log1p(self.df['Salary'])
            self.df['Sex'] = self.df['Sex'].str.strip()
            logging.info(
                f"Veri yüklendi: {self.file_path.name} | "
                f"Toplam geçerli kayıt: {len(self.df)}"
            )
        except FileNotFoundError:
            logging.error(f"Kritik Hata: {self.file_path} bulunamadı!")
            self.df = pd.DataFrame()

    def calculate_dynamic_kpi(self, department: str, metric: str, calc_type: str) -> dict:
        """
        Kullanıcının dinamik olarak tanımladığı KPI'ları hesaplar.
        Whitelist tabanlı input validation ile güvenli hale getirilmiştir.
        """
        if self.df.empty:
            return {"error": "Veri seti boş veya yüklenemedi."}

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

        # Korelasyon için istenen sütunlar dataset'te yoksa esnek davran
        available_cols = [
            c for c in ['EngagementSurvey', 'EmpSatisfaction', 'SpecialProjectsCount']
            if c in corr_matrix.columns
        ]
        if not available_cols or 'Salary' not in corr_matrix.columns:
            return {}

        critical_corr = corr_matrix.loc['Salary', available_cols]
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
        Kural tabanlı model ile yüksek risk taşıyan çalışanları tespit eder.

        Risk Kriterleri (4 koşulun tamamı sağlanmalı):
        1. Bağlılık skoru 3.0'ın altında  → düşük motivasyon
        2. En az 2 yıldır şirkette         → öğrendiklerini götürme riski
        3. Özel projeye atanmamış          → gelişim fırsatı verilmemiş
        4. Hâlâ aktif çalışan              → işten çıkarılmamış
        """
        if self.df.empty:
            return []

        # df mutate edilmez, local kopya kullanılır
        local_df = self.df.copy()
        current_year = pd.Timestamp.now().year

        local_df['Hire_Year'] = pd.to_datetime(local_df['DateofHire']).dt.year
        local_df['Tenure_Years'] = current_year - local_df['Hire_Year']

        # Dataset'te bu sütunlar yoksa boş liste döndür
        required = ['EngagementSurvey', 'Tenure_Years', 'SpecialProjectsCount', 'Termd']
        if not all(c in local_df.columns for c in required):
            logging.warning("Flight risk için gerekli sütunlar eksik.")
            return []

        risk_conditions = (
            (local_df['EngagementSurvey'] < 3.0) &
            (local_df['Tenure_Years'] >= 2) &
            (local_df['SpecialProjectsCount'] == 0) &
            (local_df['Termd'] == 0)
        )

        high_risk_employees = local_df[risk_conditions]

        # Frontend'e sadece mevcut sütunlar döndürülür
        return_cols = [
            c for c in ['Employee_Name', 'Department', 'Salary', 'ManagerName']
            if c in high_risk_employees.columns
        ]
        return high_risk_employees[return_cols].to_dict(orient='records')
