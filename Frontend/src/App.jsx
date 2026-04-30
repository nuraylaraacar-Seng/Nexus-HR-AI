import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Activity, Users, DollarSign, BrainCircuit, AlertTriangle, Upload, X, CheckCircle, Database, LogOut } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

// Axios instance — session_id varsa her isteğe otomatik ekler
const createApi = (sessionId) => axios.create({
  baseURL: API_BASE,
  headers: sessionId ? { 'X-Session-ID': sessionId } : {},
});

// ── Dosya boyutu formatlayıcı
const fmtSize = (bytes) => bytes < 1024 * 1024
  ? `${(bytes / 1024).toFixed(1)} KB`
  : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

export default function App() {
  const [sessionId,   setSessionId]   = useState(() => sessionStorage.getItem('nexus_session'));
  const [summary,     setSummary]     = useState(null);

  const [aiReport,    setAiReport]    = useState(null);
  const [riskList,    setRiskList]    = useState([]);
  const [payGap,      setPayGap]      = useState([]);
  const [kpiData,     setKpiData]     = useState(null);

  const [loading,     setLoading]     = useState(false);
  const [aiLoading,   setAiLoading]   = useState(false);
  const [error,       setError]       = useState(null);

  // Upload state
  const [uploadFile,  setUploadFile]  = useState(null);
  const [uploading,   setUploading]   = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragOver,    setDragOver]    = useState(false);
  const fileInputRef = useRef();

  // API instance her sessionId değişiminde yeniden oluşur
  const api = useCallback(() => createApi(sessionId), [sessionId])();

  // Session değişince veriyi yeniden çek
  useEffect(() => {
    setAiReport(null);
    setError(null);
    setLoading(true);
    Promise.all([fetchKPI(), fetchFlightRisk(), fetchPayGap()])
      .finally(() => setLoading(false));
  }, [sessionId]); // eslint-disable-line

  const fetchKPI = async () => {
    try {
      const res = await api.post('/analytics/kpi', {
        department: 'All', metric: 'Salary', calc_type: 'mean'
      });
      setKpiData(res.data.data);
    } catch (e) { console.error('KPI hatası:', e); }
  };

  const fetchFlightRisk = async () => {
    try {
      const res = await api.get('/analytics/flight-risk');
      setRiskList(res.data.data);
    } catch (e) { console.error('Flight risk hatası:', e); }
  };

  const fetchPayGap = async () => {
    try {
      const res = await api.get('/analytics/gender-pay-gap');
      const formatted = Object.entries(res.data.data).map(([dept, vals]) => ({
        department: dept,
        gap:    vals.Pay_Gap_Percentage ?? 0,
        male:   vals.M   ?? 0,
        female: vals.F   ?? 0,
      }));
      setPayGap(formatted);
    } catch (e) { console.error('Pay gap hatası:', e); }
  };

  const fetchAIReport = async () => {
    setAiLoading(true);
    setError(null);
    try {
      const res = await api.get('/ai/executive-summary');
      setAiReport(res.data.data);
    } catch {
      setError("AI raporu alınamadı. Backend'in çalıştığından emin ol.");
    }
    setAiLoading(false);
  };

  // ── UPLOAD
  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      setUploadError('Sadece .csv dosyaları kabul edilir.');
      return;
    }
    setUploadFile(file);
    setUploadError(null);
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', uploadFile);
    try {
      const res = await axios.post(`${API_BASE}/upload-dataset`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.status === 'error') {
        setUploadError(res.data.message);
      } else {
        const newSession = res.data.session_id;
        sessionStorage.setItem('nexus_session', newSession);
        setSessionId(newSession);
        setSummary(res.data.summary);
        setUploadFile(null);
      }
    } catch (e) {
      setUploadError(e.response?.data?.message || 'Yükleme başarısız.');
    }
    setUploading(false);
  };

  const handleLogout = async () => {
    if (!sessionId) return;
    try { await api.delete('/session'); } catch {}
    sessionStorage.removeItem('nexus_session');
    setSessionId(null);
    setSummary(null);
    setAiReport(null);
  };

  const totalEmployees = kpiData?.total_employees ?? 0;
  const riskRate = totalEmployees > 0
    ? `${((riskList.length / totalEmployees) * 100).toFixed(1)}%`
    : '—';

  return (
    <div className="page">

      {/* ── TOP BAR */}
      <header className="topbar">
        <div className="topbar-left">
          <span className="logo-mark">NX</span>
          <div>
            <h1 className="title">Nexus HR</h1>
            <p className="subtitle">Enterprise Intelligence Platform</p>
          </div>
        </div>
        <div className="topbar-right">
          {sessionId ? (
            <div className="session-badge">
              <CheckCircle size={14} />
              <span>Özel Dataset</span>
              <button className="logout-btn" onClick={handleLogout} title="Session'ı Sil">
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <div className="session-badge default">
              <Database size={14} />
              <span>Varsayılan Dataset</span>
            </div>
          )}
        </div>
      </header>

      {/* ── UPLOAD PANEL */}
      <section className="upload-section">
        <div
          className={`dropzone ${dragOver ? 'drag-over' : ''} ${uploadFile ? 'has-file' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); }}
          onClick={() => !uploadFile && fileInputRef.current.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            style={{ display: 'none' }}
            onChange={(e) => handleFileSelect(e.target.files[0])}
          />
          {!uploadFile ? (
            <>
              <Upload size={28} className="dz-icon" />
              <p className="dz-label">CSV dosyanı sürükle bırak ya da <u>seç</u></p>
              <p className="dz-hint">Zorunlu kolonlar: Salary, Department, Termd, EngagementSurvey</p>
            </>
          ) : (
            <div className="file-preview">
              <CheckCircle size={20} color="#10b981" />
              <span className="file-name">{uploadFile.name}</span>
              <span className="file-size">{fmtSize(uploadFile.size)}</span>
              <button className="remove-btn" onClick={(e) => { e.stopPropagation(); setUploadFile(null); }}>
                <X size={14} />
              </button>
            </div>
          )}
        </div>

        {uploadFile && (
          <button className="upload-btn" onClick={handleUpload} disabled={uploading}>
            {uploading ? '⏳ Yükleniyor...' : '📤 Dataset Yükle & Analiz Et'}
          </button>
        )}

        {uploadError && <p className="upload-error">⚠ {uploadError}</p>}

        {summary && (
          <div className="summary-strip">
            <span>✅ Dataset yüklendi</span>
            <span className="sep">·</span>
            <span><strong>{summary.total_employees}</strong> çalışan</span>
            <span className="sep">·</span>
            <span>Ort. maaş <strong>${summary.average_salary?.toLocaleString()}</strong></span>
            <span className="sep">·</span>
            <span>Risk <strong>{summary.flight_risk_count}</strong> kişi</span>
          </div>
        )}
      </section>

      {/* ── KPI KARTI SATIRLARI */}
      <div className="kpi-row">
        {[
          { icon: <Users size={22} />,         label: 'Toplam Çalışan',  value: loading ? '…' : (totalEmployees || '—'), color: '#3b82f6' },
          { icon: <DollarSign size={22} />,     label: 'Ort. Maaş',      value: loading ? '…' : (kpiData ? `$${kpiData.value.toLocaleString()}` : '—'), color: '#10b981' },
          { icon: <AlertTriangle size={22} />,  label: 'İstifa Riski',   value: loading ? '…' : `${riskList.length} kişi`, color: '#f59e0b' },
          { icon: <Activity size={22} />,       label: 'Risk Oranı',     value: loading ? '…' : riskRate, color: '#ef4444' },
          { icon: <Database size={22} />,       label: 'Departman',      value: loading ? '…' : (payGap.length || '—'), color: '#8b5cf6' },
        ].map((k, i) => (
          <div className="kpi-card" key={i} style={{ '--accent': k.color }}>
            <div className="kpi-icon">{k.icon}</div>
            <div className="kpi-body">
              <span className="kpi-label">{k.label}</span>
              <span className="kpi-value">{k.value}</span>
            </div>
          </div>
        ))}
      </div>

      {/* ── ANA İÇERİK */}
      <div className="content-grid">

        {/* Maaş Uçurumu Grafik */}
        <div className="panel">
          <h2 className="panel-title">Departman Bazlı Cinsiyet Maaş Uçurumu (%)</h2>
          {payGap.length === 0 && !loading && (
            <p className="empty-state">Veri bulunamadı ya da yükleniyor.</p>
          )}
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={payGap} margin={{ top: 8, right: 8, left: -16, bottom: 40 }}>
              <XAxis
                dataKey="department"
                tick={{ fontSize: 11, fill: '#64748b' }}
                angle={-35}
                textAnchor="end"
                interval={0}
              />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                formatter={(v) => [`${v}%`, 'Pay Gap']}
                contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
              />
              <Bar dataKey="gap" radius={[5, 5, 0, 0]}>
                {payGap.map((e, i) => (
                  <Cell key={i} fill={e.gap > 0 ? '#ef4444' : '#10b981'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="chart-legend">
            <span className="dot red" /> Erkek lehine &nbsp;
            <span className="dot green" /> Kadın lehine
          </p>
        </div>

        {/* İstifa Riski Listesi */}
        <div className="panel">
          <h2 className="panel-title">İstifa Riski Yüksek Çalışanlar</h2>
          <div className="risk-list">
            {loading && <p className="empty-state">Yükleniyor…</p>}
            {!loading && riskList.length === 0 && (
              <p className="empty-state">Risk taşıyan çalışan bulunamadı.</p>
            )}
            {riskList.map((emp, i) => (
              <div key={i} className="risk-item">
                <div className="risk-avatar">{emp.Employee_Name?.[0] ?? '?'}</div>
                <div className="risk-info">
                  <strong>{emp.Employee_Name}</strong>
                  <span className="risk-dept">{emp.Department}</span>
                </div>
                <span className="risk-salary">${emp.Salary?.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── AI PANELİ */}
      <div className="ai-panel">
        <div className="ai-header">
          <BrainCircuit size={28} />
          <div>
            <h2 className="ai-title">Yapay Zeka Strateji Merkezi</h2>
            <p className="ai-sub">
              {sessionId ? 'Yüklediğin dataset üzerinden analiz yapılacak.' : 'Varsayılan dataset üzerinden analiz yapılacak.'}
            </p>
          </div>
        </div>

        <button className="ai-btn" onClick={fetchAIReport} disabled={aiLoading}>
          {aiLoading ? '⏳ Analiz ediliyor…' : '🚀 Stratejik Özet Üret'}
        </button>

        {error && <div className="error-box">{error}</div>}

        {aiReport && (
          <div className="ai-result">
            <h3 className="ai-report-title">{aiReport.report_title}</h3>
            <p className="ai-report-body">{aiReport.ai_insight}</p>
          </div>
        )}
      </div>

      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
          --bg:       #f1f5f9;
          --surface:  #ffffff;
          --border:   #e2e8f0;
          --text:     #0f172a;
          --muted:    #64748b;
          --radius:   14px;
          --shadow:   0 2px 12px rgba(0,0,0,0.06);
          --font:     'DM Sans', 'Segoe UI', sans-serif;
        }

        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

        body { font-family: var(--font); background: var(--bg); color: var(--text); }

        .page { max-width: 1280px; margin: 0 auto; padding: 28px 24px 60px; }

        /* TOPBAR */
        .topbar {
          display: flex; justify-content: space-between; align-items: center;
          margin-bottom: 28px;
        }
        .topbar-left { display: flex; align-items: center; gap: 14px; }
        .logo-mark {
          width: 44px; height: 44px; border-radius: 12px;
          background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
          color: #f8fafc; font-weight: 700; font-size: 16px; letter-spacing: 1px;
          display: flex; align-items: center; justify-content: center;
        }
        .title { font-size: 22px; font-weight: 700; color: var(--text); }
        .subtitle { font-size: 13px; color: var(--muted); margin-top: 2px; }
        .topbar-right { display: flex; align-items: center; gap: 12px; }

        .session-badge {
          display: flex; align-items: center; gap: 6px;
          padding: 6px 12px; border-radius: 20px;
          background: #dcfce7; color: #166534; font-size: 13px; font-weight: 500;
        }
        .session-badge.default { background: #f1f5f9; color: var(--muted); }
        .logout-btn {
          background: none; border: none; cursor: pointer;
          color: inherit; display: flex; align-items: center; padding: 0 0 0 4px;
          opacity: 0.7;
        }
        .logout-btn:hover { opacity: 1; }

        /* UPLOAD */
        .upload-section { margin-bottom: 24px; }

        .dropzone {
          border: 2px dashed var(--border); border-radius: var(--radius);
          padding: 28px; text-align: center; cursor: pointer;
          background: var(--surface); transition: all .2s;
        }
        .dropzone:hover, .dropzone.drag-over {
          border-color: #3b82f6; background: #eff6ff;
        }
        .dropzone.has-file { cursor: default; border-style: solid; border-color: #10b981; background: #f0fdf4; }
        .dz-icon { color: var(--muted); margin-bottom: 10px; }
        .dz-label { font-size: 15px; color: var(--text); margin-bottom: 4px; }
        .dz-hint { font-size: 12px; color: var(--muted); font-family: 'DM Mono', monospace; }

        .file-preview {
          display: flex; align-items: center; gap: 10px;
          justify-content: center; flex-wrap: wrap;
        }
        .file-name { font-weight: 600; font-size: 15px; }
        .file-size { font-size: 12px; color: var(--muted); font-family: 'DM Mono', monospace; }
        .remove-btn {
          background: none; border: none; cursor: pointer; color: #ef4444;
          display: flex; align-items: center; padding: 4px;
          border-radius: 6px; transition: background .15s;
        }
        .remove-btn:hover { background: #fee2e2; }

        .upload-btn {
          margin-top: 14px; padding: 11px 28px;
          background: #1e293b; color: #f8fafc;
          border: none; border-radius: 10px; font-family: var(--font);
          font-size: 15px; font-weight: 600; cursor: pointer; transition: background .2s;
        }
        .upload-btn:hover:not(:disabled) { background: #334155; }
        .upload-btn:disabled { opacity: .55; cursor: not-allowed; }

        .upload-error { margin-top: 10px; color: #ef4444; font-size: 13px; }

        .summary-strip {
          margin-top: 14px; padding: 12px 18px;
          background: #f0fdf4; border: 1px solid #bbf7d0;
          border-radius: 10px; display: flex; align-items: center; gap: 10px;
          font-size: 14px; color: #166534; flex-wrap: wrap;
        }
        .sep { color: #86efac; }

        /* KPI */
        .kpi-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 14px; margin-bottom: 22px;
        }
        .kpi-card {
          background: var(--surface); border-radius: var(--radius);
          box-shadow: var(--shadow); padding: 18px 20px;
          display: flex; align-items: center; gap: 14px;
          border-top: 3px solid var(--accent);
        }
        .kpi-icon { color: var(--accent); flex-shrink: 0; }
        .kpi-body { display: flex; flex-direction: column; }
        .kpi-label { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
        .kpi-value { font-size: 22px; font-weight: 700; color: var(--text); font-family: 'DM Mono', monospace; }

        /* CONTENT GRID */
        .content-grid {
          display: grid; grid-template-columns: 1fr 1fr;
          gap: 20px; margin-bottom: 22px;
        }
        @media (max-width: 768px) {
          .content-grid { grid-template-columns: 1fr; }
        }

        .panel {
          background: var(--surface); border-radius: var(--radius);
          box-shadow: var(--shadow); padding: 24px;
        }
        .panel-title { font-size: 15px; font-weight: 600; margin-bottom: 18px; color: var(--text); }
        .empty-state { color: var(--muted); font-size: 14px; padding: 20px 0; text-align: center; }

        .chart-legend { font-size: 12px; color: var(--muted); margin-top: 10px; display: flex; align-items: center; gap: 4px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .dot.red { background: #ef4444; }
        .dot.green { background: #10b981; }

        /* RISK LIST */
        .risk-list { display: flex; flex-direction: column; gap: 8px; max-height: 260px; overflow-y: auto; padding-right: 4px; }
        .risk-item {
          display: flex; align-items: center; gap: 12px;
          padding: 10px 14px; background: #fff7ed;
          border-radius: 10px; border-left: 4px solid #f59e0b;
        }
        .risk-avatar {
          width: 34px; height: 34px; border-radius: 50%;
          background: #fef3c7; color: #92400e;
          display: flex; align-items: center; justify-content: center;
          font-weight: 700; font-size: 14px; flex-shrink: 0;
        }
        .risk-info { flex: 1; display: flex; flex-direction: column; }
        .risk-info strong { font-size: 14px; color: var(--text); }
        .risk-dept { font-size: 12px; color: var(--muted); margin-top: 2px; }
        .risk-salary { font-family: 'DM Mono', monospace; font-size: 14px; font-weight: 600; color: #10b981; }

        /* AI PANEL */
        .ai-panel {
          background: var(--surface); border-radius: var(--radius);
          box-shadow: var(--shadow); padding: 30px;
          border-top: 4px solid #6366f1;
        }
        .ai-header { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 22px; color: #6366f1; }
        .ai-title { font-size: 18px; font-weight: 700; color: var(--text); }
        .ai-sub { font-size: 13px; color: var(--muted); margin-top: 4px; }
        .ai-btn {
          padding: 12px 28px; background: #6366f1; color: #fff;
          border: none; border-radius: 10px; font-family: var(--font);
          font-size: 15px; font-weight: 600; cursor: pointer; transition: background .2s;
        }
        .ai-btn:hover:not(:disabled) { background: #4f46e5; }
        .ai-btn:disabled { opacity: .55; cursor: not-allowed; }

        .error-box {
          margin-top: 16px; padding: 14px 18px;
          background: #fef2f2; border: 1px solid #fecaca;
          border-radius: 10px; color: #b91c1c; font-size: 14px;
        }
        .ai-result {
          margin-top: 22px; padding: 22px 26px;
          background: #f5f3ff; border-radius: 12px;
          border-left: 5px solid #6366f1;
        }
        .ai-report-title {
          font-size: 17px; font-weight: 700; color: #3730a3;
          margin-bottom: 14px;
        }
        .ai-report-body {
          white-space: pre-line; color: #374151;
          line-height: 1.85; font-size: 14px;
        }
      `}</style>
    </div>
  );
}
