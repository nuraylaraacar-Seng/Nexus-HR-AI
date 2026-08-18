import os
import logging
import requests
import json
import pandas as pd

class HRConsultantAI:
    def __init__(self):
        # Groq API  entegrasyonu. Key yoksa uygulama çökmesin diye available bayrağı kullanıyorum.
        self.api_key   = os.getenv("GROQ_API_KEY")
        self.url       = "https://api.groq.com/openai/v1/chat/completions"
        self.model = os.getenv("AI_MODEL", "openai/gpt-oss-20b")
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
prompt = f"""
You are an expert Data Engineer performing HR dataset schema mapping.

Your task is to map incoming CSV columns to our standard HR schema.

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
8. If a target cannot be identified confidently, return null.
9. Return ONLY a valid JSON object. Do not include markdown formatting or explanations.
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise HR data schema mapping engine. Output ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.0,
            "max_tokens": 500,
            # reasoning_effort sildik.
            # strict json_schema yerine evrensel json_object kullandık.
            "response_format": {
                "type": "json_object"
            }
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
        
    def infer_unknown_columns(
        self,
        df: pd.DataFrame,
        required_cols: list,
        optional_cols: list
    ) -> dict:

        if not self.available or df.empty:
            return {}

        actual_cols = list(df.columns)

        schema_info = []

        for col in actual_cols:
            inferred_type = self._profile_column_pandas(df[col])

            # KVKK güvenliği gereği
            if inferred_type == "text":
                safe_values = ["[KVKK GEREĞİ GİZLENDİ]"]

            # Hassas sayısal değerleri doğrudan göndermiyoruz
            elif inferred_type == "numeric":
                safe_values = [
                    f"Range: {df[col].min()} to {df[col].max()}"
                ]

            else:
                safe_values = (
                    df[col]
                    .dropna()
                    .value_counts()
                    .head(3)
                    .index
                    .tolist()
                )

            schema_info.append(
                f"- Column: '{col}' | "
                f"Type: {inferred_type} | "
                f"Samples: {safe_values}"
            )

        schema_text = "\n".join(schema_info)

        all_targets = required_cols + optional_cols

        properties = {}

        for target in all_targets:
            properties[target] = {
                "anyOf": [
                    {
                        "type": "string",
                        "enum": actual_cols
                    },
                    {
                        "type": "null"
                    }
                ]
            }

        mapping_schema = {
            "type": "object",
            "properties": properties,
            "required": all_targets,
            "additionalProperties": False
        }



        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                logging.error(
                    f"Schema Agent API hatası "
                    f"{response.status_code}: {response.text[:1000]}"
                )
                return {}

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            logging.info(
                f"Schema Agent mapping response: {content}"
            )

            raw_mapping = json.loads(content)

            # Güvenlik katmanı: yalnızca gerçek CSV kolonlarını kabul eder..
            validated_mapping = {}

            for target, source in raw_mapping.items():

                if target not in all_targets:
                    continue

                if source is None:
                    continue

                if source in actual_cols:
                    validated_mapping[target] = source

            return validated_mapping

        except requests.exceptions.Timeout:
            logging.error("Schema Agent API timeout")
            return {}

        except json.JSONDecodeError as e:
            logging.error(
                f"Schema Agent JSON parse hatası: {e}"
            )
            return {}

        except Exception as e:
            logging.error(
                f"Schema Agent Exception: {e}"
            )
            return {}
