"""
Nexus HR: Enterprise AI Dashboard API
Session bazlı engine yönetimi ile her kullanıcı kendi dataset'ini yükler,
kendi session'ına özel hesaplamalar alır.
"""

import os
import uuid
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, field_validator
from typing import Optional

from Backend.data_engine import HRDataEngine
from Backend.ai_service import HRConsultantAI
from Backend.config import ALLOWED_METRICS, ALLOWED_CALC_TYPES
from dotenv import load_dotenv

load_dotenv()

from fastapi import UploadFile, File
import pandas as pd
from io import BytesIO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- RATE LİMİTER ---
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Nexus HR: Enterprise AI Dashboard API",
    description="İK Verileri için Yapay Zeka Destekli Analitik API",
    version="2.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DIZIN YAPISI ---
BASE_DIR = Path(__file__).parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "Data" / "HRDataset_v14.csv"

# Kullanıcı bazlı geçici dataset'lerin kaydedileceği klasör
SESSION_DATA_DIR = BASE_DIR / "Data" / "sessions"
SESSION_DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- SESSION DEPOSU ---
# { session_id: HRDataEngine instance }
# Production'da Redis/DB kullanılmalı; burada in-memory yeterli
_session_engines: dict[str, HRDataEngine] = {}

ai_engine = HRConsultantAI()


# --- YARDIMCI FONKSİYONLAR ---

def get_engine_for_session(session_id: Optional[str]) -> HRDataEngine:
    """
    Verilen session_id için engine döndürür.
    session_id yoksa ya da geçersizse varsayılan dataset'i kullanır.
    """
    if session_id and session_id in _session_engines:
        return _session_engines[session_id]

    # Varsayılan engine: ilk istekte oluşturulur, sonra cache'lenir
    if "default" not in _session_engines:
        if not DEFAULT_DATA_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="Varsayılan dataset bulunamadı. Lütfen önce bir dataset yükleyin."
            )
        _session_engines["default"] = HRDataEngine(str(DEFAULT_DATA_PATH))
        logging.info("Varsayılan engine oluşturuldu.")

    return _session_engines["default"]


# --- İSTEK MODELLERİ ---

class KPIRequest(BaseModel):
    department: str
    metric: str
    calc_type: str

    @field_validator('metric')
    @classmethod
    def metric_must_be_valid(cls, v):
        if v not in ALLOWED_METRICS:
            raise ValueError(f"Geçersiz metrik. İzin verilenler: {ALLOWED_METRICS}")
        return v

    @field_validator('calc_type')
    @classmethod
    def calc_type_must_be_valid(cls, v):
        if v not in ALLOWED_CALC_TYPES:
            raise ValueError(f"Geçersiz hesaplama tipi. İzin verilenler: {ALLOWED_CALC_TYPES}")
        return v


# --- ENDPOİNTLER ---

@app.post("/api/v1/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Dataset yükler ve bu kullanıcıya özel bir session_id döndürür.
    Sonraki tüm isteklerde bu session_id Header'da gönderilmelidir:
        X-Session-ID: <session_id>
    """
    try:
        contents = await file.read()

        if not contents:
            return {"status": "error", "message": "Boş dosya yüklenemez."}

        # DataFrame olarak doğrula
        df = pd.read_csv(BytesIO(contents))

        required_cols = ["Salary", "Department", "Termd", "EngagementSurvey"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return {"status": "error", "message": f"Eksik kolonlar: {missing}"}

        # Benzersiz session ID üret
        session_id = str(uuid.uuid4())

        # Bu session'a ait dosyayı diske kaydet
        save_path = SESSION_DATA_DIR / f"{session_id}.csv"
        with open(save_path, "wb") as f:
            f.write(contents)

        # Bu session için özel engine oluştur
        _session_engines[session_id] = HRDataEngine(str(save_path))
        logging.info(f"Yeni session oluşturuldu: {session_id} | Dosya: {save_path.name}")

        summary = _session_engines[session_id].get_risk_summary()

        return {
            "status": "success",
            "message": "Dataset başarıyla yüklendi.",
            "session_id": session_id,   # ← Frontend bunu saklamalı ve header'da göndermelidir
            "summary": summary
        }

    except Exception as e:
        logging.error(f"Upload hatası: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/analytics/kpi")
@limiter.limit("30/minute")
async def get_kpi(
    request: Request,
    body: KPIRequest,
    x_session_id: Optional[str] = Header(default=None)
):
    """Dinamik KPI hesaplar. X-Session-ID header'ı ile session'a özel veri kullanır."""
    engine = get_engine_for_session(x_session_id)
    result = engine.calculate_dynamic_kpi(body.department, body.metric, body.calc_type)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@app.get("/api/v1/analytics/correlation")
@limiter.limit("20/minute")
async def get_correlation(
    request: Request,
    x_session_id: Optional[str] = Header(default=None)
):
    """Değişkenler arasındaki korelasyon matrisini döndürür."""
    engine = get_engine_for_session(x_session_id)
    data = engine.get_correlation_matrix()
    if not data:
        raise HTTPException(status_code=500, detail="Korelasyon hesaplanamadı.")
    return {"status": "success", "data": data}


@app.get("/api/v1/analytics/gender-pay-gap")
@limiter.limit("20/minute")
async def get_gender_pay_gap(
    request: Request,
    x_session_id: Optional[str] = Header(default=None)
):
    """Cinsiyet bazlı maaş uçurumu analizi."""
    engine = get_engine_for_session(x_session_id)
    data = engine.analyze_gender_pay_gap()
    if not data:
        raise HTTPException(status_code=500, detail="Cinsiyet maaş analizi hesaplanamadı.")
    return {"status": "success", "data": data}


@app.get("/api/v1/analytics/flight-risk")
@limiter.limit("20/minute")
async def get_flight_risk(
    request: Request,
    x_session_id: Optional[str] = Header(default=None)
):
    """Algoritmik istifa riski listesini döndürür."""
    engine = get_engine_for_session(x_session_id)
    return {"status": "success", "data": engine.predict_flight_risk_advanced()}


@app.get("/api/v1/ai/executive-summary")
@limiter.limit("5/minute")
async def get_ai_summary(
    request: Request,
    x_session_id: Optional[str] = Header(default=None)
):
    """Yapay Zeka (Groq/Llama) Stratejik Yönetici Özeti — session'a özel veri ile."""
    engine = get_engine_for_session(x_session_id)
    risk_data = engine.get_risk_summary()
    if not risk_data:
        raise HTTPException(status_code=500, detail="Risk verileri hesaplanamadı.")

    ai_report = ai_engine.generate_executive_summary(risk_data)
    if "error" in ai_report:
        raise HTTPException(status_code=503, detail=ai_report["error"])

    return {"status": "success", "data": ai_report}


@app.get("/api/v1/session/info")
async def get_session_info(x_session_id: Optional[str] = Header(default=None)):
    """
    Aktif session bilgisini döndürür.
    Frontend'in hangi dataset ile çalıştığını doğrulaması için kullanılır.
    """
    if x_session_id and x_session_id in _session_engines:
        engine = _session_engines[x_session_id]
        return {
            "status": "success",
            "session_id": x_session_id,
            "is_custom": True,
            "employee_count": len(engine.df)
        }
    return {
        "status": "success",
        "session_id": None,
        "is_custom": False,
        "note": "Varsayılan dataset kullanılıyor."
    }


@app.delete("/api/v1/session")
async def delete_session(x_session_id: Optional[str] = Header(default=None)):
    """
    Session'ı ve ilgili geçici dosyayı temizler.
    Kullanıcı logout yaptığında çağrılmalıdır.
    """
    if not x_session_id or x_session_id not in _session_engines:
        return {"status": "error", "message": "Geçerli bir session bulunamadı."}

    # Engine'i bellekten sil
    del _session_engines[x_session_id]

    # Diske yazılan geçici dosyayı sil
    session_file = SESSION_DATA_DIR / f"{x_session_id}.csv"
    if session_file.exists():
        session_file.unlink()
        logging.info(f"Session temizlendi: {x_session_id}")

    return {"status": "success", "message": "Session başarıyla silindi."}


@app.get("/api/v1/health")
async def health_check():
    """
    API sağlık durumu.
    Kubernetes/Docker liveness probe için kullanılır.
    """
    return {
        "status": "healthy",
        "active_sessions": len([k for k in _session_engines if k != "default"]),
        "default_dataset_loaded": "default" in _session_engines
    }
