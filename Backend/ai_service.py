import google.generativeai as genai
import os
import logging


class HRConsultantAI:
    def __init__(self):
        #API anahtarı .env dosyasından okunur.
        #Kod içine yazılmadı (güvenlik riskinden dolayı)
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            logging.error("GEMINI_API_KEY tanımlı değil!")
            self.client = None
            return

        try:
            #Gemini istemcisi başlatılıyor
            self.client = genai.Client(api_key=self.api_key)
            logging.info("AI Motoru başarıyla başlatıldı.")
        except Exception as e:
            logging.error(f"AI Başlatılma Hatası: {str(e)}")
            self.client = None

    def _sanitize_value(self, value) -> str:
        """
        Güvenlik: Prompt Injection saldırısını önler.
        Dışarıdan gelen tüm veriler sayıya dönüştürülür.
        Sayıya dönüşmeyen değerler '0" ile değiştirilir.
        """
        try:
            return str(round(float(value), 2))
        except (ValueError, TypeError):
            return "0"

    def generate_executive_summary(self, hr_data: dict) -> dict:
        """
        Gelen ham İK verilerini analiz edip yöneticiye
        stratejik tavsiyeler üretir.
        
        Args:
            hr_data(dict):Veri motorundan özet ris verileri.
            -total_employees:Toplam çalışan sayısı
            -avearage_salary:Ortalama maaş
            -flight_risk_count:İstifa riski yüksek çalışan sayısı
            -avearage_engagement:Ortalama bağlılık skoru

        Returns:
            dict:AI tarafından üretilen stratejik rapor
            veya hata mesajı.
        """
        if not self.client:
            return {"error": "AI modeli aktif değil."}
        #Tüm dış veriler sanitize edildikten sonra Prompt'a eklenir.
        total_emp  = self._sanitize_value(hr_data.get('total_employees', 0))
        avg_sal    = self._sanitize_value(hr_data.get('average_salary', 0))
        risk_count = self._sanitize_value(hr_data.get('flight_risk_count', 0))
        avg_eng    = self._sanitize_value(hr_data.get('average_engagement', 0))

        # Gemini'ye gönderilecek prompt.
        # Rol tanımı + veri bağlamı + çıktı formatı belirtilir.

        prompt = f"""
        Sen kıdemli bir İnsan Kaynakları Stratejistisin.
        - Toplam Çalışan: {total_emp}
        - Ortalama Maaş: ${avg_sal}
        - İstifa Riski Yüksek: {risk_count}
        - Bağlılık Skoru: {avg_eng}/5

        Yönetim Kuruluna sunulmak üzere:
        1. Mevcut durumun 2 cümlelik özeti
        2. İstifa riskini azaltmak için 3 aksiyon maddesi
        Sadece istenen formatta cevap ver.
        """

        try:
            # Gemini 2.5 Flash modeline istek gönderili


            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )
            return {
                "report_title": "AI Stratejik Yönetici Özeti",
                "ai_insight": response.text,
                "status": "Success"
            }
        except Exception as e:
            print("HATA DETAYI:", str(e))
            logging.error(f"AI Yanıt Üretemedi: {str(e)}")
            return {"error": str(e)}
