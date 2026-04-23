import os
import logging
import requests

class HRConsultantAI:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = True
        
        if not self.api_key:
            logging.error("GOOGLE_API_KEY tanımlı değil!")
            self.client = None
            return
            
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent"


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
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            response = requests.post(self.url, headers=headers, json=body)
            data = response.json()
            
            if "candidates" not in data:
                logging.error(f"AI yanıt hatası: {data}")
                return {"error": f"AI yanıt üretemedi: {data}"}
                
            ai_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {
                "report_title": "AI Stratejik Yönetici Özeti",
                "ai_insight": ai_text,
                "status": "Success"
            }
        except Exception as e:
            logging.error(f"AI Yanıt Üretemedi: {str(e)}")
            return {"error": str(e)}
