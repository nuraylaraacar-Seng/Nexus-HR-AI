import google.generativeai as genai
import os
import logging


class HRConsultantAI:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            logging.error("GEMINI_API_KEY tanımlı değil!")
            self.model = None
            return

        try:
            # Gemini yapılandırma
            genai.configure(api_key=self.api_key)

            # Modeli başlat
            self.model = genai.GenerativeModel("gemini-1.5-pro-latest")


            logging.info("AI Motoru başarıyla başlatıldı.")
        except Exception as e:
            logging.error(f"AI Başlatılma Hatası: {str(e)}")
            self.model = None

    def _sanitize_value(self, value) -> str:
        try:
            return str(round(float(value), 2))
        except (ValueError, TypeError):
            return "0"

    def generate_executive_summary(self, hr_data: dict) -> dict:
        if not self.model:
            return {"error": "AI modeli aktif değil."}

        total_emp  = self._sanitize_value(hr_data.get('total_employees', 0))
        avg_sal    = self._sanitize_value(hr_data.get('average_salary', 0))
        risk_count = self._sanitize_value(hr_data.get('flight_risk_count', 0))
        avg_eng    = self._sanitize_value(hr_data.get('average_engagement', 0))

        prompt = f"""
        Sen kıdemli bir İnsan Kaynakları Stratejistisin.
        - Toplam Çalışan: {total_emp}
        - Ortalama Maaş: ${avg_sal}
        - İstifa Riski Yüksek: {risk_count}
        - Bağlılık Skoru: {avg_eng}/5

        Yönetim Kuruluna sunulmak üzere:
        1. Mevcut durumun 2 cümlelik özeti
        2. İstifa riskini azaltmak için 3 aksiyon maddesi
        Sadece istenen formatta cevap ver.
        """

        try:
            response = self.model.generate_content(prompt)
            return {
                "report_title": "AI Stratejik Yönetici Özeti",
                "ai_insight": response.text,
                "status": "Success"
            }
        except Exception as e:
            logging.error(f"AI Yanıt Üretemedi: {str(e)}")
            return {"error": str(e)}
