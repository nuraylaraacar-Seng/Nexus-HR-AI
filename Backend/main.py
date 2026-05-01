"""
Nexus HR: Enterprise AI Dashboard API v2.1
- Session bazlı engine yönetimi
- Esnek kolon eşleştirme (column mapping)
"""

import os, uuid, logging
from pathlib import Path
from typing import Optional
from io import BytesIO

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

BASE_DIR          = Path(__file__).parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "Data" / "HRDataset_v14.csv"
SESSION_DATA_DIR  = BASE_DIR / "Data" / "sessions"
SESSION_DATA_DIR.mkdir(parents=True, exist_ok=True)

_session_engines: dict[str, HRDataEngine] = {}
_pending_sessions: dict[str, dict]        = {}

ai_engine = HRConsultantAI()

REQUIRED_COLUMNS = ["Salary", "Department", "Termd", "EngagementSurvey"]
OPTIONAL_COLUMNS = ["PerformanceScore", "SpecialProjectsCount", "DateofHire",
                    "Employee_Name", "ManagerName", "EmpSatisfaction", "Sex"]
ALL_STANDARD = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def get_engine(sid: Optional[str]) -> HRDataEngine:
    if sid and sid in _session_engines:
        return _session_engines[sid]
    if "default" not in _session_engines:
        if not DEFAULT_DATA_PATH.exists():
            raise HTTPException(status_code=503, detail="Varsayılan dataset bulunamadı.")
        _session_engines["default"] = HRDataEngine(str(DEFAULT_DATA_PATH))
    return _session_engines["default"]


class KPIRequest(BaseModel):
    department: str
    metric: str
    calc_type: str

    @field_validator('metric')
    @classmethod
    def metric_ok(cls, v):
        if v not in ALLOWED_METRICS:
            raise ValueError(f"Geçersiz metrik. İzin verilenler: {ALLOWED_METRICS}")
        return v

    @field_validator('calc_type')
    @classmethod
    def calc_ok(cls, v):
        if v not in ALLOWED_CALC_TYPES:
            raise ValueError(f"Geçersiz hesaplama tipi. İzin verilenler: {ALLOWED_CALC_TYPES}")
        return v


class ColumnMappingRequest(BaseModel):
    mapping: dict[str, str]


@app.post("/api/v1/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if not contents:
            return {"status": "error", "message": "Boş dosya yüklenemez."}

        df = pd.read_csv(BytesIO(contents))
        actual_cols = list(df.columns)
        temp_id     = str(uuid.uuid4())
        save_path   = SESSION_DATA_DIR / f"{temp_id}_raw.csv"
        
        with open(save_path, "wb") as f:
            f.write(contents)

        missing_required = [c for c in REQUIRED_COLUMNS if c not in actual_cols]
        auto_mapping     = {c: c for c in ALL_STANDARD if c in actual_cols}

        if not missing_required:
            engine = HRDataEngine(str(save_path), column_mapping=auto_mapping)
            _session_engines[temp_id] = engine
            return {
                "status": "success",
                "needs_mapping": False,
                "session_id": temp_id,
                "summary": engine.get_risk_summary(),
            }
        else:
            _pending_sessions[temp_id] = {"raw_path": str(save_path), "columns": actual_cols}
            return {
                "status": "success",
                "needs_mapping": True,
                "pending_id": temp_id,
                "dataset_columns": actual_cols,
                "required_columns": REQUIRED_COLUMNS,
                "optional_columns": OPTIONAL_COLUMNS,
                "auto_detected": auto_mapping,
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
async def get_kpi(request: Request, body: KPIRequest,
                  x_session_id: Optional[str] = Header(default=None)):
    result = get_engine(x_session_id).calculate_dynamic_kpi(body.department, body.metric, body.calc_type)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@app.get("/api/v1/analytics/correlation")
@limiter.limit("20/minute")
async def get_correlation(request: Request,
                          x_session_id: Optional[str] = Header(default=None)):
    data = get_engine(x_session_id).get_correlation_matrix()
    if not data:
        raise HTTPException(status_code=500, detail="Korelasyon hesaplanamadı.")
    return {"status": "success", "data": data}


@app.get("/api/v1/analytics/gender-pay-gap")
@limiter.limit("20/minute")
async def get_gender_pay_gap(request: Request,
                             x_session_id: Optional[str] = Header(default=None)):
    data = get_engine(x_session_id).analyze_gender_pay_gap()
    if not data:
        raise HTTPException(status_code=500, detail="Cinsiyet maaş analizi hesaplanamadı.")
    return {"status": "success", "data": data}


@app.get("/api/v1/analytics/flight-risk")
@limiter.limit("20/minute")
async def get_flight_risk(request: Request,
                          x_session_id: Optional[str] = Header(default=None)):
    return {"status": "success", "data": get_engine(x_session_id).predict_flight_risk_advanced()}

@app.get("/api/v1/ai/executive-summary")
@limiter.limit("5/minute")
async def get_ai_summary(request: Request,
                         x_session_id: Optional[str] = Header(default=None)):
    # AI engine kontrolü
    if ai_engine is None:
        raise HTTPException(
            status_code=503,
            detail="AI servisi devre dışı. Llama_API_KEY .env dosyasında tanımlı mı kontrol et."
        )
 
    engine    = get_engine(x_session_id)
    risk_data = engine.get_risk_summary()
    if not risk_data:
        raise HTTPException(status_code=500, detail="Risk verileri hesaplanamadı.")
 
    # ★ ai_service artık "error" key döndürüyor, "status" değil
    ai_report = ai_engine.generate_executive_summary(risk_data)
 
    if "error" in ai_report:
        raise HTTPException(status_code=503, detail=ai_report["error"])
 
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
    return {
        "status": "healthy",
        "active_sessions": len([k for k in _session_engines if k != "default"]),
        "pending_mappings": len(_pending_sessions),
    }
