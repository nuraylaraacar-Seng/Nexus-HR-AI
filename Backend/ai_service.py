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
        prompt = f"""
You are an elite HR analytics strategist with a communication style comparable to McKinsey, BCG, and Bain partners.
Using the HR metrics provided, produce a high-authority, insight-dense, CEO-level executive summary **in Turkish**.

Your writing must be sharp, assertive, and strategically oriented — the kind of output that would convince a CHRO or CEO
that the author is a top-tier HR data strategist.

Your output MUST follow this exact structure (titles remain in Turkish), but the content must be powerful, analytical,
and business-impact focused:

1. Genel Durum Özeti
   - Deliver a commanding, high-level assessment of the organization’s HR landscape in 2–3 sentences.
   - The tone must be confident, outcome-focused, and reflective of senior strategic thinking.

2. Kritik Bulgular
   - Toplam çalışan: {risk_data.get('total_employees')}
   - Ortalama maaş: {risk_data.get('average_salary') or "Veri mevcut değil"}
   - Yüksek riskli çalışan sayısı: {risk_data.get('flight_risk_count') or "Veri mevcut değil"}
   - Ortalama bağlılık skoru: {risk_data.get('average_engagement') or "Veri mevcut değil"}

3. Stratejik Değerlendirme
   - Provide sharp, insight-driven commentary on what these metrics imply for organizational health, workforce stability,
     talent risk, and HR strategy.
   - Even if some metrics are missing, maintain a strong analytical tone and extract meaningful strategic implications.
   - Avoid generic HR statements; focus on business impact, risk exposure, operational vulnerabilities, and strategic priorities.

4. Önerilen Aksiyonlar
   - Provide 3–5 short, high-impact, C-level recommendations.
   - Use decisive, executive language such as:
     “kritik öncelik taşımaktadır”,
     “stratejik olarak ele alınması gerekmektedir”,
     “organizasyonel riskleri azaltmak için öncelikli olarak uygulanmalıdır”.
   - Recommendations must be actionable, measurable, and aligned with enterprise-level decision making.

STRICT RULES:
- Output MUST be in Turkish.
- Do NOT fabricate or assume numbers.
- Tone MUST be authoritative, corporate, and insight-driven.
- No soft language. No filler. No generic HR advice.
- Follow the structure exactly.
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
