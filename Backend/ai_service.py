import os
import logging
import requests
import json
import pandas as pd

class HRConsultantAI:
    def __init__(self):
        # Groq API entegrasyonu. Key yoksa uygulama çökmesin diye available bayrağı kullanılıyor.
        self.api_key = os.getenv("GROQ_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = os.getenv("AI_MODEL", "gpt-oss-120b")
        self.available = bool(self.api_key)

    def generate_executive_summary(self, risk_data: dict) -> dict:
        """
        Yapay Zeka Entegrasyonu: Dashboard verilerine dayanarak stratejik, C-Level bir İK raporu üretir.
        Groq kullanarak statik metin yerine dinamik içgörüler döndürür.
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
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=15)

            if response.status_code != 200:
                logging.error(f"Groq API hatası {response.status_code}: {response.text[:500]}")
                return {"error": "AI servisi şu anda yanıt veremiyor. Lütfen daha sonra tekrar deneyin."}

            data = response.json()
            ai_text = data["choices"][0]["message"]["content"]

            return {
                "report_title": "Nexus HR — Stratejik Yönetici Raporu",
                "ai_insight": ai_text,
            }

        except requests.exceptions.Timeout:
            logging.error("Groq API timeout (15s)")
            return {"error": "AI servisi zaman aşımına uğradı. Lütfen tekrar deneyin."}
        except Exception as e:
            logging.error(f"AI servis hatası: {e}")
            return {"error": "AI servisinde beklenmeyen bir hata oluştu."}

    def _profile_column_pandas(self, series: pd.Series) -> str:
        """
        Ekstra ağır kütüphanelere girmeden, sadece Pandas ile verinin şemasını çıkartır.
        """
        clean_series = series.dropna()
        if clean_series.empty: return "unknown"
        
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
        """
        LLM kullanarak TAM OTONOM (Zero-Touch) şema haritalandırması yapar.
        Kullanıcıya modal göstermemek için LLM'i zorunlu seçim yapmaya iter.
        """
        if not self.available or df.empty:
            return {}

        actual_cols = list(df.columns)
        schema_info = []

        for col in actual_cols:
            inferred_type = self._profile_column_pandas(df[col])

            # KVKK güvenliği gereği
            if inferred_type == "text":
                safe_values = ["[KVKK GEREĞİ GİZLENDİ]"]
            elif inferred_type == "numeric":
                safe_values = [f"Range: {df[col].min()} to {df[col].max()}"]
            else:
                safe_values = df[col].dropna().value_counts().head(3).index.tolist()

            schema_info.append(f"- Column: '{col}' | Type: {inferred_type} | Samples: {safe_values}")

        schema_text = "\n".join(schema_info)
        all_targets = required_cols + optional_cols

        prompt = f"""
You are an elite AI Data Architect. Your mission is 100% AUTONOMOUS schema mapping.
The system requires zero human intervention.

TARGET REQUIRED COLUMNS (MUST be mapped, NEVER use null):
{', '.join(required_cols)}

TARGET OPTIONAL COLUMNS (Can be null only if completely irrelevant):
{', '.join(optional_cols)}

AVAILABLE CSV COLUMNS:
{actual_cols}

DATASET SAMPLES & TYPES:
{schema_text}

AUTONOMY RULES:
1. ZERO HUMAN INTERVENTION: For the REQUIRED COLUMNS, you must forcefully deduce the best possible match from the available columns. Look at data types and samples. 
2. NEVER RETURN NULL FOR A REQUIRED COLUMN. Make your best educated guess.
3. You must select the exact string from the AVAILABLE CSV COLUMNS list.
4. Output ONLY a valid JSON object. No explanations, no markdown.

Example format:
{{"Salary": "MonthlyIncome", "Department": "Dept", "Termd": "Attrition"}}
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an autonomous HR mapping engine. Output ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=15)

            if response.status_code != 200:
                logging.error(f"Schema Agent API hatası {response.status_code}: {response.text[:1000]}")
                return {}

            data = response.json()
            message_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not message_content:
                logging.error("Groq API başarılı yanıt verdi fakat içerik BOŞ döndü.")
                return {}

            cleaned_content = message_content.replace("```json", "").replace("```", "").strip()
            raw_mapping = json.loads(cleaned_content)

            # --- TOLERANS KATMANI ---
            # AI inisiyatif alıp ufak harf/boşluk hatası yapsa bile veriyi çöpe atma.
            clean_actual_cols = {col.strip().lower(): col for col in actual_cols}

            validated_mapping = {}
            for target, source in raw_mapping.items():
                if not source or not isinstance(source, str):
                    continue
                
                clean_source = source.strip().lower()
                if target in all_targets and clean_source in clean_actual_cols:
                    validated_mapping[target] = clean_actual_cols[clean_source]

            logging.info(f"Otonom Eşleştirme Başarılı: {validated_mapping}")
            return validated_mapping

        except Exception as e:
            logging.error(f"Schema Agent Exception: {e}")
            return {}
