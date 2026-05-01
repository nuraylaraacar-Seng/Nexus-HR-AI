import os
import requests


class HRConsultantAI:
    def __init__(self):
        self.api_key = os.getenv("Llama_API_KEY")  # .env'deki key adı korundu
        self.url     = "https://api.groq.com/openai/v1/chat/completions"
        self.model   = "llama-3.3-70b-versatile"

        if not self.api_key:
            raise ValueError("Llama_API_KEY environment variable eksik! .env dosyanı kontrol et.")

    def generate_executive_summary(self, risk_data: dict) -> dict:
        """
        Groq / Llama-3.3 ile stratejik İK raporu üretir.
        Dönen dict her zaman 'error' key'i içerir (hata varsa) ya da
        'report_title' + 'ai_insight' içerir (başarılı ise).
        main.py "error" in result ile kontrol eder.
        """
        prompt = f"""
[ROLE]
You are a Senior Managing Partner at a top-tier global management consultancy (McKinsey, BCG, or Bain).
Your expertise lies in Strategic Human Capital Management and Organizational Resilience.

[CONTEXT]
You are reviewing the "Nexus HR" analytics dashboard for a high-growth enterprise.
The CHRO and Board of Directors expect a high-stakes, data-driven assessment.

[DATASET SNAPSHOT]
- Total Headcount: {risk_data.get('total_employees', 'N/A')}
- Financial Baseline (Avg Salary): ${risk_data.get('average_salary', 'N/A')}
- Talent Leakage Risk: {risk_data.get('flight_risk_count', 'Analiz Edilemedi')} employees identified as High Risk.
- Employee Sentiment: {risk_data.get('average_engagement', 'N/A')}/5.0 Engagement Score.

[STRICT DELIVERABLE STRUCTURE - RESPONSE MUST BE IN TURKISH]

1. Stratejik Durum Değerlendirmesi
   - Organizasyon sağlığını 2-3 güçlü cümleyle özetle.
   - Bağlılık skorunu yetenek kaybı riskiyle doğrudan ilişkilendir.

2. Kritik Veri Matrisi
   - Veriyi analitik ağırlıkla sun.

3. Derinlemesine Risk Analizi
   - Yüksek riskli çalışan kaybının finansal etkisini hesapla.
   - Hangi departmanların "Stratejik Kırmızı Bölge" teşkil ettiğini belirt.

4. C-Level Aksiyon Planı
   - 3-4 kararlı, yüksek etkili öneri sun.
   - "Kritik öncelik taşımaktadır", "ivedilikle uygulanmalıdır" gibi ifadeler kullan.

[CONSTRAINTS]
- Dil: YALNIZCA TÜRKÇE.
- Ton: Soğuk, profesyonel, veri merkezli, otoriter. Gereksiz dolgu yok.
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a top-tier HR Data Strategist. Turkish only. No fluff."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=60)

            if response.status_code != 200:
                return {
                    "error": f"Groq API Hatası {response.status_code}: {response.text[:300]}"
                }

            data     = response.json()
            ai_text  = data["choices"][0]["message"]["content"]

            return {
                "report_title": "Nexus AI — Stratejik Yönetici Raporu",
                "ai_insight":   ai_text,
            }

        except requests.exceptions.Timeout:
            return {"error": "Groq API zaman aşımına uğradı (60s). Tekrar dene."}
        except Exception as e:
            return {"error": f"AI servis hatası: {str(e)}"}
