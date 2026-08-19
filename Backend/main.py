"""
Nexus HR: Enterprise AI Dashboard API v2.1
Mimari Notlarım:
- Session-Based Memory Management (Oturuma özel bellek yönetimi)
- LLM-Powered Schema Mapping (Groq API, Pandas Profiling ve KVKK Kalkanı ile akıllı eşleştirme)
- Zero-Touch Autonomous Fallback & Data Cleansing (Manuel modalı tarihe gömen otonom katman)  
-eklendi 
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

BASE_DIR = Path(__file__).parent.parent
SESSION_DATA_DIR = BASE_DIR / "Data" / "sessions"
SESSION_DATA_DIR.mkdir(parents=True, exist_ok=True)

_session_engines: dict[str, HRDataEngine] = {}
MAX_ACTIVE_SESSIONS = 500
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

def sanitize_and_normalize_df(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
    Farklı Kaggle ve kurumsal veri setlerindeki tip ve format uyuşmazlıklarını 
    otomatik olarak temizleyen ve standartlaştıran veri mühendisliği katmanı.
    """
    df = df.copy()
    rename_dict = {v: k for k, v in mapping.items() if v and v in df.columns}
    df = df.rename(columns=rename_dict)

    if 'Salary' in df.columns:
        df['Salary'] = pd.to_numeric(
            df['Salary'].astype(str).str.replace(r'[^0-9.]', '', regex=True), 
            errors='coerce'
        ).fillna(0)

    if 'Termd' in df.columns:
        def parse_termd(val):
            if pd.isna(val): return 0
            v_str = str(val).strip().lower()
            if v_str in ['1', 'true', 'yes', 'terminated', 'left', 'evet', 'y']:
                return 1
            return 0
        df['Termd'] = df['Termd'].apply(parse_termd)

    if 'EngagementSurvey' in df.columns:
        df['EngagementSurvey'] = pd.to_numeric(df['EngagementSurvey'], errors='coerce').fillna(3.0)

    return df

def auto_fallback_mapping(actual_cols: list, ai_mapping: dict) -> dict:
    """
    ZERO-TOUCH MOTORU: AI eksik bıraksa bile, Python tarafında akıllı kelime 
    taraması yaparak zorunlu kolonları tamamlar ve kullanıcının önüne ASLA modal atmaz.
    """
    mapping = ai_mapping.copy()
    lower_cols = {c.lower(): c for c in actual_cols}

    # Her hedef için olası alternatif anahtar kelimeler sözlüğü
    aliases = {
        "Salary": ["salary", "monthlyincome", "income", "basepay", "compensation", "wage"],
        "Department": ["department", "dept", "businessunit", "unit", "division", "team"],
        "Termd": ["termd", "attrition", "status", "left", "quit", "terminated", "active"],
        "EngagementSurvey": ["engagementsurvey", "satisfaction", "score", "environmentsatisfaction", "engagement"]
    }

    for req in REQUIRED_COLUMNS:
        if not mapping.get(req):
            # 1. Önce birebir eşleşme var mı
            if req.lower() in lower_cols:
                mapping[req] = lower_cols[req.lower()]
                continue
            
            # 2. Yoksa alias listesinden bulmaya çalış
            found = False
            for alias in aliases.get(req, []):
                if alias in lower_cols:
                    mapping[req] = lower_cols[alias]
                    found = True
                    break
            
            # 3. Hala bulunamadıysa, ilk bulduğu uygun kolonu zorla ata (Sistem çökmesin diye)
            if not found and actual_cols:
                mapping[req] = actual_cols[0]

    return mapping

def read_csv_robust(contents: bytes) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "windows-1254", "cp1254", "latin1"]
    last_error = None
    for enc in encodings:
        try:
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


# --- ENDPOINTS ---

@app.post("/api/v1/upload-dataset")
async def upload_dataset(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if not contents:
            return {"status": "error", "message": "Boş dosya yüklenemez."}

        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="Dosya boyutu limiti aşıldı (Max: 20MB)")

        try:
            df = read_csv_robust(contents)
        except Exception as e:
            return {"status": "error", "message": f"CSV Parse Hatası: {str(e)}"}

        actual_cols = list(df.columns)
        temp_id     = str(uuid.uuid4())
        save_path   = SESSION_DATA_DIR / f"{temp_id}.csv"
        
        # 1. AI ile eşleştirmeyi dene
        raw_ai_mapping = {}
        if ai_engine.available:
            raw_ai_mapping = ai_engine.infer_unknown_columns(df, REQUIRED_COLUMNS, OPTIONAL_COLUMNS)

        # 2. Zero-Touch Fallback ile eksikleri otomatik tamamla (MODALI TAMAMEN DEVRE DIŞI BIRAKIR)
        final_mapping = auto_fallback_mapping(actual_cols, raw_ai_mapping)

        # 3. Veriyi temizle ve kaydet
        cleaned_df = sanitize_and_normalize_df(df, final_mapping)
        cleaned_df.to_csv(save_path, index=False)

        # 4. Bellek yönetimi ve oturum başlatma
        if len(_session_engines) > MAX_ACTIVE_SESSIONS:
            oldest = next(iter(_session_engines))
            del _session_engines[oldest]

        engine = HRDataEngine(str(save_path), column_mapping=final_mapping)
        _session_engines[temp_id] = engine

        return {
            "status": "success",
            "needs_mapping": False,  # ARTIK ASLA MODAL AÇILMAZ
            "session_id": temp_id,
            "summary": engine.get_risk_summary()
        }

    except Exception as e:
        logging.error(f"Upload hatası: {e}")
        return {"status": "error", "message": str(e)}


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
    p = SESSION_DATA_DIR / f"{x_session_id}.csv"
    if p.exists():
        p.unlink()
    return {"status": "success", "message": "Session silindi."}

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "ai_available": ai_engine.available,
        "active_sessions": len(_session_engines),
    }
