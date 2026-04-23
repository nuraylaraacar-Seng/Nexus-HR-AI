import os
import requests

class HRConsultantAI:
    def __init__(self):
        self.api_key = os.getenv("Llama_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-70b-versatile"

        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing!")

    def generate_executive_summary(self, risk_data: dict):
        prompt = f"""
        You are an HR analytics consultant. Based on the following HR metrics,
        generate a concise and professional executive summary in Turkish.
        Use a corporate tone and include 3–5 actionable recommendations.

        HR Metrics:
        - Total employees: {risk_data.get('total_employees')}
        - Average salary: {risk_data.get('avg_salary')}
        - High-risk employees: {risk_data.get('high_risk_count')}
        - Average engagement score: {risk_data.get('avg_engagement')}

        Requirements:
        - Output must be in Turkish.
        - Keep the summary structured and business-oriented.
        - Avoid emotional or informal language.
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
