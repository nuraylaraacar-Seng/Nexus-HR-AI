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
You are an elite Data Detective and HR AI Agent. 
Your ONLY job is to map incoming dirty CSV columns to our standard HR schema.

TARGET SCHEMA
Required columns:
{', '.join(required_cols)}

Optional columns:
{', '.join(optional_cols)}

INCOMING DATASET (Pay close attention to Types and Samples!)
{schema_text}

CRITICAL DEDUCTION RULES:
1. IGNORE WEIRD COLUMN NAMES. A column might be named "Adem", "XYZ", or "Var1". Do not rely on the name alone.
2. DEDUCE FROM SAMPLES: Look at the "Samples" and "Type" provided for each column.
   - If a column has numeric ranges like 30,000 to 150,000, it is DEFINITELY the "Salary" or "MonthlyIncome" column, regardless of its name.
   - If a column contains binary data (0/1, Yes/No, True/False) or terms like "Voluntary", "Fired", it is DEFINITELY the "Attrition" or "Termd" column.
   - If a column contains text like "Sales", "IT", "Engineering", it is the "Department" column.
   - If a column contains scores (e.g., 1 to 5), it is likely the "EngagementSurvey" or performance score.
3. Map a target ONLY to an exact column name that exists in the INCOMING DATASET list.
4. Never invent a column name.
5. Output your response entirely in valid JSON format.

Example JSON output format:
{{"Salary": "Adem_veya_farkli_isim", "Department": "Dept", "Termd": "Status_Column"}}
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
        LLM kullanarak dinamik şema haritalandırması yapar.
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
You are an expert Data Engineer performing HR dataset schema mapping.

Your task is to map incoming CSV columns to our standard HR schema.
You must respond with a valid JSON object.

TARGET SCHEMA
Required columns:
{', '.join(required_cols)}

Optional columns:
{', '.join(optional_cols)}

INCOMING DATASET
{schema_text}

RULES
1. Map a target only to a column that actually exists in the incoming dataset.
2. Never invent a column name.
3. Use the semantic meaning and data type of the columns.
4. Salary should map to a salary/compensation column.
5. Department should map to a department/business-unit column.
6. Termd should map to termination/terminated status data.
7. EngagementSurvey should map to employee engagement/survey score data.
8. If a target cannot be identified confidently, use null.
9. Respond with a JSON object where keys are the target column names and values are the matched source column names or null.

Example JSON output format:
{{"Salary": "MonthlyIncome", "Department": "Dept", "Termd": null}}
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise HR data schema mapping engine. You must output ONLY a valid JSON object. Do not include any text before or after the JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.0,
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(self.url, json=payload, headers=headers, timeout=15)

            if response.status_code != 200:
                logging.error(f"Schema Agent API hatası {response.status_code}: {response.text[:1000]}")
                return {}

            data = response.json()

            content = data["choices"][0]["message"]["content"]

            content = content.replace("```json", "").replace("```", "").strip()
            
            logging.info(f"Schema Agent mapping response: {content}")
            

            raw_mapping = json.loads(content)

            # Güvenlik katmanı: yalnızca gerçek CSV kolonlarını kabul eder.
            validated_mapping = {}
            for target, source in raw_mapping.items():
                if target in all_targets and source in actual_cols:
                    validated_mapping[target] = source

            return validated_mapping

        except requests.exceptions.Timeout:
            logging.error("Schema Agent API timeout")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Schema Agent JSON parse hatası: {e}")
            return {}
        except Exception as e:
            logging.error(f"Schema Agent Exception: {e}")
            return {}
