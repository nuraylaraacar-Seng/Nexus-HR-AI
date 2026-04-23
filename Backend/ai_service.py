import os
import requests

class HRConsultantAI:
    def __init__(self):
        self.api_key = os.getenv("Llama_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"



        if not self.api_key:
            raise ValueError("Nexus_API_KEY environment variable is missing!")

    def generate_executive_summary(self, risk_data: dict):
        prompt = prompt = f"""
        
        You are a senior HR analytics strategist. Using the HR metrics provided, generate a highly structured, executive‑level summary in **Turkish**.
        Your output MUST follow this exact structure:

        1. **Genel Durum Özeti (2–3 sentences)**
         - Provide a concise, high‑level overview of the organization’s current HR landscape.

        2. **Kritik Bulgular**
        - Toplam çalışan: {risk_data.get('total_employees')}
        - Ortalama maaş: {risk_data.get('avg_salary') or "Veri mevcut değil"}
        - Yüksek riskli çalışan sayısı: {risk_data.get('high_risk_count') or "Veri mevcut değil"}
        - Ortalama bağlılık skoru: {risk_data.get('avg_engagement') or "Veri mevcut değil"}

       3. **Stratejik Değerlendirme**
       - Provide analytical insights explaining what these metrics imply.
       - If any metric is missing, explicitly state: “Eksik veri nedeniyle analiz sınırlıdır.”

      4. **Önerilen Aksiyonlar (3–5 items)**
      - Provide short, actionable, C‑level recommendations.

      STRICT RULES:
     - Output MUST be in Turkish.
     - Do NOT fabricate or assume any numbers.
     - Maintain a corporate, analytical, concise tone.
     - Follow the structure exactly as written.
"""


        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a senior HR analytics consultant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.url, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            return {
                "status": "error",
                "detail": response.text
            }

        data = response.json()
        ai_text = data["choices"][0]["message"]["content"]

        return {
            "status": "success",
            "report_title": "AI Stratejik Yönetici Özeti",
            "ai_insight": ai_text
        }
