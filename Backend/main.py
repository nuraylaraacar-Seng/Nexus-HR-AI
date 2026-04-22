"""
Nexus HR: Enterprise AI Dashboard API
Bu dosya, uygulamanın ana giriş noktasıdır (Entry Point).
Gelen HTTP isteklerini karşılar, güvenlik (CORS, Rate Limiting) kontrollerinden gecirir,
Pydantic ile verileri doğrular ve ilgili iş motorlarına (Data Engine, AI Service) yönlendirir.
"""

import os
import logging
from pathlib import Path
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, field_validator

from Backend.data_engine import HRDataEngine
from Backend.ai_service import HRConsultantAI
from Backend.config import ALLOWED_METRICS, ALLOWED_CALC_TYPES
from dotenv import load_dotenv
#Çevresel değişeknleri/variable ları (.env) sisteme yükler
#API anahtarları ve dosya yolları buradan okunur.
load_dotenv()




logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- RATE LİMİTER ---
#DDOS saldırılarını ve gereksiz aşırı yuklenme için IP tabanlı sınırlandırma başlatılıyor
limiter = Limiter(key_func=get_remote_address)

#Fastapı uygulaması başlatılıyor.
#openAPI(Swagger) dokumantasyonu için meta veriler ekleniyor
app = FastAPI(
    title="Nexus HR: Enterprise AI Dashboard API",
    description="İK Verileri için Yapay Zeka Destekli Analitik API",
    version="1.0.0"
)

#SlowAPI, FastAPI uygulamasına bağlanıyor ve limit aşımı durumunda verilecek özel hata tanımlanıyor
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS: ENV'DEN OKU ---
# Sadece güvenilir frontend adreslerinin (origins) bu API'ye erişmesine izin verilir.
# Güvenlik açığı yaratmamak için 'allow_origins' kısmında joker karakter (*) kullanılmamıştır.
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Guvenlik amaciyla çerez (cookie) kullanımı devre dışı.
    allow_credentials=False,
    # Gerekirse ileride sadece GET ve POST olarak kısıtlanabilinir.
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- MOTORLAR ---


# Projenin kök dizinini bulur (Backend klasörünün bir üstü)
BASE_DIR = Path(__file__).parent.parent

# Varsayılan dataset yolu
default_path = BASE_DIR / "Data" / "HRDataset_v14.csv"

# .env içinden DATA_PATH okunur, yoksa default_path kullanılır
DATA_PATH = os.getenv("DATA_PATH", str(default_path))


#Veri analizi ve Yapay Zeka motorları
engine = HRDataEngine(DATA_PATH)
ai_engine = HRConsultantAI()


# --- İSTEK MODELLERİ -Pytandic---
#Gelen isteklerde sadece bu metriklerin ve
#hesaplama tiplerinin kullanılmasına izin verilir


class KPIRequest(BaseModel):
    """Client tarafından gelen KPI Hesaplama
    tiplerinin kullanılmasına izin verir"""
    department: str
    metric: str
    calc_type: str

    @field_validator('metric')
    @classmethod
    def metric_must_be_valid(cls, v):
        """izin verilmeyen bir metrik gelirse
        422 Unprocessable Entity hatası fırlatır"""
        if v not in ALLOWED_METRICS:
            raise ValueError(f"Geçersiz metrik. İzin verilenler: {ALLOWED_METRICS}")
        return v

    @field_validator('calc_type')
    @classmethod
    def calc_type_must_be_valid(cls, v):
        #Hesaplama tipinin Güvenli olup olmadığını denetler.
        if v not in ALLOWED_CALC_TYPES:
            raise ValueError(f"Geçersiz hesaplama tipi. İzin verilenler: {ALLOWED_CALC_TYPES}")
        return v


# --- API ENDPOİNTLERİ ---

@app.post("/api/v1/analytics/kpi")
@limiter.limit("30/minute")
async def get_kpi(request: Request, body: KPIRequest):
    """Dinamik KPI hesaplar."""
    result = engine.calculate_dynamic_kpi(body.department, body.metric, body.calc_type)
    #Motor tarfından döndürülen mantıksal hatalar(buisness logic errors)
    #400 koduyla HTTP hatasina çevrilir
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@app.get("/api/v1/analytics/correlation")
@limiter.limit("20/minute")
async def get_correlation(request: Request):
    """Değişkenler arasındaki istatistiksel ilişkiyi(Korelasyon Matrisi) döndürür."""
    data = engine.get_correlation_matrix()
    if not data:
        raise HTTPException(status_code=500, detail="Korelasyon hesaplanamadı.")
    return {"status": "success", "data": data}


@app.get("/api/v1/analytics/gender-pay-gap")
@limiter.limit("20/minute")
async def get_gender_pay_gap(request: Request):
    """Cinsiyet bazlı maaş uçurumu (Pay Gap) analizi."""
    data = engine.analyze_gender_pay_gap()
    if not data:
        raise HTTPException(status_code=500, detail="Cinsiyet maaş analizi hesaplanamadı.")
    return {"status": "success", "data": data}


@app.get("/api/v1/analytics/flight-risk")
@limiter.limit("20/minute")
async def get_flight_risk(request: Request):
    """Algoritmik istifa riski listesini döndürür."""
    return {"status": "success", "data": engine.predict_flight_risk_advanced()}


@app.post("/executive-summary")
#Yapay Zeka daha maliyetli bir işlem olduğu için
#AI endpoint → daha kısıtlı
@limiter.limit("5/minute")  
async def get_ai_summary(request: Request):
    """Yapay Zeka (Gemini) Stratejik Yönetici Özeti"""
    #önce veri motorundan risk özeti alınır
    risk_data = engine.get_risk_summary()
    if not risk_data:
        raise HTTPException(status_code=500, detail="Risk verileri hesaplanamadı.")
    
    #Alınan bu veriler context olarak AI motoruna gönderilir
    ai_report = ai_engine.generate_executive_summary(risk_data)
    if "error" in ai_report:
        #AI servisine ulaşılmazsa 503 döner
        raise HTTPException(status_code=503, detail=ai_report["error"])

    return {"status": "success", "data": ai_report}

"""API'nin ve bağlı alt sistemlerin anlık sağlık durumunu (Health Check) raporlar.
           Kubernetes, Docker ve bulut yük dengeleyicileri (Load Balancers) tarafından 
           uygulamanın trafik kabul etmeye hazır olup olmadığını (Liveness ve Readiness)
           denetlemek amacıyla kullanılır"""

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "data_loaded": not engine.df.empty,
        "ai_ready": ai_engine.client is not None  # model → client
    }
@app.get("/test")
async def test():
    return {"test": "ok"}
