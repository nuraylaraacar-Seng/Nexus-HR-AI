import os
import logging
import requests

class HRConsultantAI:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = "models/gemini-1.5-pro"

        if not self.api_key:
            logging.error("GEMINI_API_KEY tanımlı değil!")
            return

        self.url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent"

    def generate_executive_summary(self, hr_data: dict):
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        prompt = f"""
        Sen kıdemli bir İnsan Kaynakları Stratejistisin.
        - Toplam Çalışan: {hr_data.get('total_employees')}
        - Ortalama Maaş: ${hr_data.get('average_salary')}
        - İstifa Riski Yüksek: {hr_data.get('flight_risk_count')}
        - Bağlılık Skoru: {hr_data.get('average_engagement')}/5

        Yönetim Kuruluna sunulmak üzere:
        1. Mevcut durumun 2 cümlelik özeti
        2. İstifa riskini azaltmak için 3 aksiyon maddesi
        """

        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        try:
            response = requests.post(self.url, headers=headers, json=body)
            data = response.json()

            return {
                "report_title": "AI Stratejik Yönetici Özeti",
                "ai_insight": data["candidates"][0]["content"]["parts"][0]["text"],
                "status": "Success"
            }

        except Exception as e:
            logging.error(f"AI Yanıt Üretemedi: {str(e)}")
            return {"error": str(e)}
