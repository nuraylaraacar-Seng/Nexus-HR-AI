import os
import logging
import requests
import json
import pandas as pd

class HRConsultantAI:
    def __init__(self):
        # Groq API ve Llama 3.3 entegrasyonu. Key yoksa uygulama çökmesin diye available bayrağı kullanıyorum.
        self.api_key   = os.getenv("Llama_API_KEY")
        self.url       = "https://api.groq.com/openai/v1/chat/completions"
        self.model     = "llama-3.3-70b-versatile"
        self.available = bool(self.api_key)

    def generate_executive_summary(self, risk_data: dict) -> dict:
        """
        Yapay Zeka Entegrasyonu: Dashboard verilerine dayanarak stratejik, C-Level bir İK raporu üretir.
        Groq Llama 3.3 kullanarak statik metin yerine dinamik içgörüler döndürür.
        """
        if not self.available:
            return {"error": "AI servisi şu anda devre dışı."}

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
        -Yüksek riskli çalışan kaybının finansal etkisini hesapla.
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
                logging.error(f"Groq API hatası {response.status_code}: {response.text[:500]}")
                return {"error": "AI servisi şu anda yanıt veremiyor. Lütfen daha sonra tekrar deneyin."}

            data     = response.json()
            ai_text  = data["choices"][0]["message"]["content"]

            return {
                "report_title": "Nexus AI — Stratejik Yönetici Raporu",
                "ai_insight":   ai_text,
            }

        except requests.exceptions.Timeout:
            logging.error("Groq API timeout (60s)")
            return {"error": "AI servisi zaman aşımına uğradı. Lütfen tekrar deneyin."}
        except Exception as e:
            logging.error(f"AI servis hatası: {e}")
            return {"error": "AI servisinde beklenmeyen bir hata oluştu."}

    def _profile_column_pandas(self, series: pd.Series) -> str:
        """
        Ekstra ağır kütüphanelere girmeden, sadece Pandas ile verinin şemasını çıkartıyorum.
        Amacım LLM'e temiz ve net bir analitik bağlam sunmak.
        """
        clean_series = series.dropna()
        if clean_series.empty: return "unknown"
        
        # Hızdan ödün vermemek için tüm veriyi değil, 100 satırlık rastgele bir örneklemi inceliyorum.
        sample_size = min(100, len(clean_series))
        sample = clean_series.sample(sample_size, random_state=42)
        
        if clean_series.nunique() <= 2: return "binary"
        if pd.api.types.is_numeric_dtype(clean_series): return "numeric"
        
        try:
            pd.to_datetime(sample, errors='raise')
            return "date"
        except: pass
            
        if sample.nunique() < (sample_size * 0.3): return "categorical"
        return "text"

    def infer_unknown_columns(self, df: pd.DataFrame, required_cols: list, optional_cols: list) -> dict:
        if not self.available or df.empty:
            return {}

        schema_info = []
        for col in df.columns:
            inferred_type = self._profile_column_pandas(df[col])
            
            # Veri güvenliği her şeydir. KVKK ihlali olmasın diye LLM'e gitmeden önce veriyi maskeliyorum.
            # İsim veya hassas veri olma ihtimaline karşı metinleri tamamen gizliyorum.
            if inferred_type == "text":
                safe_values = ["[KVKK GEREĞİ GİZLENDİ]"]
            # Sayısal verilerde (örn: maaş) nokta atışı değer yollamak yerine sadece minimum-maksimum aralığını belirtiyorum.
            elif inferred_type == "numeric":
                safe_values = [f"Range: {df[col].min()} to {df[col].max()}"]
            else:
                safe_values = df[col].dropna().value_counts().head(3).index.tolist()

            schema_info.append(f"- Column: '{col}' | Type: {inferred_type} | Samples: {safe_values}")
        
        schema_text = "\n".join(schema_info)

        # LLM'in kafasına göre eşleştirme yapmasını engellemek için kuralları katı tuttum.
        prompt = f"""
You are an expert Data Engineer. Map an unknown HR dataset's columns to our standard schema.

[TARGET SCHEMA]
Required: {', '.join(required_cols)}
Optional: {', '.join(optional_cols)}

[CRITICAL RULE]
Do not map numeric columns to categorical targets (like PerformanceScore). Leave unmapped if unsure.

[INCOMING DATASET]
{schema_text}

Return ONLY a valid JSON object where keys are the Target Schema columns and values are the Incoming Column names.
"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise JSON-only API. Strictly follow data types."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            response = requests.post(self.url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return json.loads(data["choices"][0]["message"]["content"])
            else:
                logging.error(f"Schema Agent API hatası: {response.text}")
                return {}
        except Exception as e:
            logging.error(f"Schema Agent Exception: {e}")
            return {}
