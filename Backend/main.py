"""
Nexus HR: Enterprise AI Dashboard API v2.1
Mimari Notlarım:
- Session-Based Memory Management (Oturuma özel bellek yönetimi)
- LLM-Powered Schema Mapping (Groq API, Pandas Profiling ve KVKK Kalkanı ile akıllı eşleştirme)
- Robust CSV Parsing & Memory Leak Protection (Çökmeleri ve RAM şişmesini önleyen güvenlik katmanları)
"""

import os, uuid, logging
from pathlib import Path
from typing import Optional
from io import BytesIO
from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from Backend.data_engine import HRDataEngine
from Backend.ai_service import HRConsultantAI
from Backend.config import ALLOWED_METRICS, ALLOWED_CALC_TYPES

# Başlatma & Güvenlik Ayarları
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Nexus HR API", version="2.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware, allow_origins=allowed_origins,
    allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
SESSION_DATA_DIR = BASE_DIR / "Data" / "sessions"
SESSION_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Sunucu uzun süre açık kaldığında memory leak (RAM şişmesi) olmasın diye aktif oturum limitini 500 olarak belirledim.
_session_engines: dict[str, HRDataEngine] = {}
_pending_sessions: dict[str, dict]        = {}
MAX_ACTIVE_SESSIONS = 500

# Kullanıcılar devasa dosyalar yükleyip sistemi kilitlemesin diye upload limitini 20MB'a çektim.
MAX_UPLOAD_SIZE = 20 * 1024 * 1024

ai_engine = HRConsultantAI()

REQUIRED_COLUMNS = ["Salary", "Department", "Termd", "EngagementSurvey"]
OPTIONAL_COLUMNS = ["PerformanceScore", "SpecialProjectsCount", "DateofHire",
                    "Employee_Name", "ManagerName", "EmpSatisfaction", "Sex"]
ALL_STANDARD = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def get_engine(sid: Optional[str]) -> HRDataEngine:
    if sid and sid in _session_engines:
        return _session_engines[sid]
    raise HTTPException(status_code=503, detail="Geçerli bir oturum bulunamadı. Lütfen dataset yükleyin.")

def read_csv_robust(contents: bytes) -> pd.DataFrame:
    """
    Burası hayat kurtaran kısım. Farklı sistemlerden veya Türkçe Excel'lerden gelen 
    bozuk encoding'li CSV'leri uygulamanın çökmeden okuyabilmesi için bu robust yapıyı kurdum.
    """
    encodings = ["utf-8-sig", "utf-8", "windows-1254", "cp1254", "latin1"]
    last_error = None

    for enc in encodings:
        try:
            # sep=None diyerek delimiter'ı (virgül mü noktalı virgül mü) Pandas'ın kendisinin tespit etmesini sağlıyorum.
            return pd.read_csv(BytesIO(contents), encoding=enc, sep=None, engine="python")
        except Exception as e:
            last_error = e

    raise ValueError(f"CSV formatı hiçbir şekilde okunamadı. Son hata: {last_error}")


class KPIRequest(BaseModel):
    department: str
    metric: str
    calc_type: str

    @field_validator('metric')
    @classmethod
    def metric_ok(cls, v):
        if v not in ALLOWED_METRICS: raise ValueError(f"Geçersiz metrik: {ALLOWED_METRICS}")
        return v

    @field_validator('calc_type')
    @classmethod
    def calc_ok(cls, v):
        if v not in ALLOWED_CALC_TYPES: raise ValueError(f"Geçersiz hesaplama: {ALLOWED_CALC_TYPES}")
        return v

class ColumnMappingRequest(BaseModel):
    mapping: dict[str, str]

# --- ENDPOINTS ---

@app.post("/api/v1/upload-dataset")
async def upload_dataset(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if not contents:
            return {"status": "error", "message": "Boş dosya yüklenemez."}

        # Dosya boyutu güvenliği
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="Dosya boyutu limiti aşıldı (Max: 20MB)")

        # ROBUST CSV PARSING
        try:
            df = read_csv_robust(contents)
        except Exception as e:
            return {"status": "error", "message": f"CSV Parse Hatası: {str(e)}"}

        actual_cols = list(df.columns)
        temp_id     = str(uuid.uuid4())
        save_path   = SESSION_DATA_DIR / f"{temp_id}_raw.csv"
        
        with open(save_path, "wb") as f:
            f.write(contents)
            
        # --- GROQ LLM SCHEMA AGENT ---
        auto_detected = {}
        if ai_engine.available:
            raw_ai_mapping = ai_engine.infer_unknown_columns(df, REQUIRED_COLUMNS, OPTIONAL_COLUMNS)
            
            # Yapay zekaya körü körüne güvenmek risklidir.
            # Olmayan bir kolonu uydurmasın diye burada sağlam bir double-check yapıyorum.
            validated_mapping = {}
            for target, source in raw_ai_mapping.items():
                if target in ALL_STANDARD and source in actual_cols:
                    validated_mapping[target] = source
            
            auto_detected = validated_mapping

        missing_required = [c for c in REQUIRED_COLUMNS if c not in auto_detected.keys() or not auto_detected.get(c)]

        # Bellek şişmesine karşı aldığım önlem. Sınırı geçersek en eski oturumu temizliyorum.
        if len(_session_engines) > MAX_ACTIVE_SESSIONS:
            oldest = next(iter(_session_engines))
            del _session_engines[oldest]

        if not missing_required:
            # LLM tüm zorunlu kolonları eksiksiz bulduysa doğrudan dashboard'u başlatıyorum.
            engine = HRDataEngine(str(save_path), column_mapping=auto_detected)
            _session_engines[temp_id] = engine
            return {
                "status": "success",
                "needs_mapping": False,
                "session_id": temp_id,
                "summary": engine.get_risk_summary()
            }
        else:
            # Yapay zeka emin olamadıysa inisiyatifi kullanıcıya bırakıyorum (Human-in-the-loop).
            # İleride 1 saatten eski oturumları temizleyen bir cron/task yazmak kolay olsun diye timestamp ekledim.
            _pending_sessions[temp_id] = {
                "raw_path": str(save_path), 
                "columns": actual_cols,
                "created_at": datetime.utcnow()
            }
            return {
                "status": "success",
                "needs_mapping": True,
                "pending_id": temp_id,
                "dataset_columns": actual_cols,
                "required_columns": REQUIRED_COLUMNS,
                "optional_columns": OPTIONAL_COLUMNS,
                "auto_detected": auto_detected, 
            }
    except Exception as e:
        logging.error(f"Upload hatası: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/upload-dataset/confirm-mapping/{pending_id}")
async def confirm_mapping(pending_id: str, body: ColumnMappingRequest):
    if pending_id not in _pending_sessions:
        raise HTTPException(status_code=404, detail="Geçersiz ya da süresi dolmuş pending session.")

    pending     = _pending_sessions[pending_id]
    raw_path    = pending["raw_path"]
    actual_cols = pending["columns"]

    # Arayüzden veya API üzerinden kafalarına göre geçersiz kolon yollayıp 
    # sistemi bozmasınlar diye buraya bir güvenlik kalkanı çektim.
    unknown_targets = set(body.mapping.keys()) - set(ALL_STANDARD)
    if unknown_targets:
        raise HTTPException(status_code=400, detail=f"Geçersiz hedefler tespit edildi: {list(unknown_targets)}")

    for std, user_col in body.mapping.items():
        if user_col and user_col not in actual_cols:
            raise HTTPException(status_code=400, detail=f"'{user_col}' kolonu CSV'de yok.")

    for req in REQUIRED_COLUMNS:
        if not body.mapping.get(req):
            raise HTTPException(status_code=400, detail=f"Zorunlu kolon eşleştirilmedi: '{req}'")

    try:
        session_id = str(uuid.uuid4())
        engine     = HRDataEngine(raw_path, column_mapping=body.mapping)
        _session_engines[session_id] = engine
        del _pending_sessions[pending_id]

        new_path = SESSION_DATA_DIR / f"{session_id}.csv"
        Path(raw_path).rename(new_path)

        return {
            "status": "success",
            "session_id": session_id,
            "summary": engine.get_risk_summary(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analytics/kpi")
@limiter.limit("30/minute")
async def get_kpi(request: Request, body: KPIRequest, x_session_id: Optional[str] = Header(default=None)):
    result = get_engine(x_session_id).calculate_dynamic_kpi(body.department, body.metric, body.calc_type)
    if "error" in result: raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}

@app.get("/api/v1/analytics/correlation")
@limiter.limit("20/minute")
async def get_correlation(request: Request, x_session_id: Optional[str] = Header(default=None)):
    data = get_engine(x_session_id).get_correlation_matrix()
    if not data: raise HTTPException(status_code=500, detail="Korelasyon hesaplanamadı.")
    return {"status": "success", "data": data}

@app.get("/api/v1/analytics/gender-pay-gap")
@limiter.limit("20/minute")
async def get_gender_pay_gap(request: Request, x_session_id: Optional[str] = Header(default=None)):
    data = get_engine(x_session_id).analyze_gender_pay_gap()
    if not data: raise HTTPException(status_code=500, detail="Cinsiyet maaş analizi hesaplanamadı.")
    return {"status": "success", "data": data}

@app.get("/api/v1/analytics/flight-risk")
@limiter.limit("20/minute")
async def get_flight_risk(request: Request, x_session_id: Optional[str] = Header(default=None)):
    return {"status": "success", "data": get_engine(x_session_id).predict_flight_risk_advanced()}

@app.get("/api/v1/ai/executive-summary")
@limiter.limit("5/minute")
async def get_ai_summary(request: Request, x_session_id: Optional[str] = Header(default=None)):
    if not ai_engine.available:
        raise HTTPException(status_code=503, detail="AI servisi devre dışı.")
 
    engine    = get_engine(x_session_id)
    risk_data = engine.get_risk_summary()
    if not risk_data:
        raise HTTPException(status_code=500, detail="Risk verileri hesaplanamadı.")
 
    ai_report = ai_engine.generate_executive_summary(risk_data)
    if "error" in ai_report: raise HTTPException(status_code=503, detail=ai_report["error"])
 
    return {"status": "success", "data": ai_report}

@app.delete("/api/v1/session")
async def delete_session(x_session_id: Optional[str] = Header(default=None)):
    if not x_session_id or x_session_id not in _session_engines:
        return {"status": "error", "message": "Geçerli session bulunamadı."}
    del _session_engines[x_session_id]
    for ext in [".csv", "_raw.csv"]:
        p = SESSION_DATA_DIR / f"{x_session_id}{ext}"
        if p.exists():
            p.unlink()
    return {"status": "success", "message": "Session silindi."}

@app.get("/api/v1/health")
async def health():
    # Canlı ortamda (prod) sistemin sağlığını, yükünü ve açık oturum sayısını 
    # monitörlerken bu detaylı metrikler çok işime yarayacak.
    return {
        "status": "healthy",
        "ai_available": ai_engine.available,
        "active_sessions": len(_session_engines),
        "pending_mappings": len(_pending_sessions),
    }
