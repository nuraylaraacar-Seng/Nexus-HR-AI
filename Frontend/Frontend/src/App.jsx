import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Activity, Users, DollarSign, BrainCircuit, AlertTriangle, Upload, X, CheckCircle, Database, LogOut, ArrowRight } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

// --- Axios Interceptor: Artık tüm isteklere X-Session-ID otomatik ekleniyor ---
axios.interceptors.request.use((config) => {
  const session = sessionStorage.getItem('nexus_session');
  if (session) {
    config.headers['X-Session-ID'] = session;
  }
  return config;
});

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

  // Upload & Mapping States
  const [uploadFile,  setUploadFile]  = useState(null);
  const [uploading,   setUploading]   = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragOver,    setDragOver]    = useState(false);
  
  // YENİ: Eşleştirme (Mapping) Stateleri
  const [showMapping, setShowMapping] = useState(false);
  const [availableCols, setAvailableCols] = useState([]);
  const [mapping, setMapping] = useState({
    Salary: '',
    Department: '',
    Termd: '',
    EngagementSurvey: ''
  });

  const fileInputRef = useRef();

  useEffect(() => {
    if (!sessionId || showMapping) return; // Mapping bitmeden veri çekmeye çalışma
    setAiReport(null);
    setError(null);
    setLoading(true);
    Promise.all([fetchKPI(), fetchFlightRisk(), fetchPayGap()])
      .finally(() => setLoading(false));
  }, [sessionId, showMapping]);

  const fetchKPI = async () => {
    try {
      const res = await axios.post(`${API_BASE}/analytics/kpi`, { department: 'All', metric: 'Salary', calc_type: 'mean' });
      setKpiData(res.data.data);
    } catch (e) { console.error('KPI hatası:', e); }
  };

  const fetchFlightRisk = async () => {
    try {
      const res = await axios.get(`${API_BASE}/analytics/flight-risk`);
      setRiskList(res.data.data);
    } catch (e) { console.error('Flight risk hatası:', e); }
  };

  const fetchPayGap = async () => {
    try {
      const res = await axios.get(`${API_BASE}/analytics/gender-pay-gap`);
      const formatted = Object.entries(res.data.data).map(([dept, vals]) => ({
        department: dept, gap: vals.Pay_Gap_Percentage ?? 0, male: vals.M ?? 0, female: vals.F ?? 0,
      }));
      setPayGap(formatted);
    } catch (e) { console.error('Pay gap hatası:', e); }
  };

  const fetchAIReport = async () => {
    setAiLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/ai/executive-summary`);
      setAiReport(res.data.data);
    } catch { setError("AI raporu alınamadı."); }
    setAiLoading(false);
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      setUploadError('Sadece .csv dosyaları kabul edilir.');
      return;
    }
    setUploadFile(file);
    setUploadError(null);
  };

  // 1. AŞAMA: Dosyayı Yükle ve Kolonları Al
  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', uploadFile);
    try {
      // Interceptor'un eski session'ı yollamasını engellemek için headers'ı temizliyoruz
      const res = await axios.post(`${API_BASE}/upload-dataset`, formData, {
        headers: { 'Content-Type': 'multipart/form-data', 'X-Session-ID': '' }
      });
      
      if (res.data.status === 'error') {
        setUploadError(res.data.message);
      } else {
        const newSession = res.data.session_id;
        sessionStorage.setItem('nexus_session', newSession);
        setSessionId(newSession);
        setAvailableCols(res.data.columns); // Backend'den gelen kolonları state'e at
        setShowMapping(true); // Eşleştirme ekranını aç!
      }
    } catch (e) { setUploadError('Yükleme başarısız.'); }
    setUploading(false);
  };

  // 2. AŞAMA: Eşleştirmeyi Gönder ve Motoru Başlat
  const handleMappingSubmit = async () => {
    setUploading(true);
    try {
      // Frontend'deki mapping objesinde ters çevirme yapıyoruz: { "KullanıcıKolonu": "BizimKolon" }
      const finalMapping = {};
      Object.entries(mapping).forEach(([ourTarget, userCol]) => {
        if (userCol) finalMapping[userCol] = ourTarget;
      });

      const res = await axios.post(`${API_BASE}/session/apply-mapping`, { mapping: finalMapping });
      
      setSummary(res.data.summary);
      setShowMapping(false); // Modal'ı kapat, dashboard'a geç
      setUploadFile(null); // Yükleme alanını temizle
    } catch (e) {
      setUploadError("Eşleştirme uygulanırken hata oluştu.");
    }
    setUploading(false);
  };

  const handleLogout = async () => {
    if (!sessionId) return;
    try { await axios.delete(`${API_BASE}/session`); } catch {}
    sessionStorage.removeItem('nexus_session');
    setSessionId(null); setSummary(null); setAiReport(null);
  };

  return (
    <div className="page">
      {/* MAPPING MODAL (EŞLEŞTİRME EKRANI) */}
      {showMapping && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Veri Eşleştirme (Data Mapping)</h3>
            <p>Sistemin verinizi doğru analiz etmesi için sütunlarınızı eşleştirin.</p>
            
            <div className="mapping-grid">
              {Object.keys(mapping).map((targetCol) => (
                <div key={targetCol} className="mapping-row">
                  <label className="target-label">{targetCol} <ArrowRight size={14}/></label>
                  <select 
                    value={mapping[targetCol]} 
                    onChange={(e) => setMapping({...mapping, [targetCol]: e.target.value})}
                  >
                    <option value="">-- Sütun Seçiniz --</option>
                    {availableCols.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
            
            <button 
              className="upload-btn" style={{width: '100%', marginTop: '20px'}}
              onClick={handleMappingSubmit} 
              disabled={uploading || Object.values(mapping).some(v => v === '')}
            >
              {uploading ? 'İşleniyor...' : 'Eşleştir ve Analizi Başlat'}
            </button>
          </div>
        </div>
      )}

      {/* --- ÜST BAR (TOPBAR) --- */}
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
              <CheckCircle size={14} /> <span>Özel Dataset</span>
              <button className="logout-btn" onClick={handleLogout}><LogOut size={14} /></button>
            </div>
          ) : (
            <div className="session-badge default"><Database size={14} /> <span>Varsayılan Dataset</span></div>
          )}
        </div>
      </header>

      {/* --- UPLOAD BÖLÜMÜ --- */}
      {!showMapping && (
      <section className="upload-section">
        <div
          className={`dropzone ${dragOver ? 'drag-over' : ''} ${uploadFile ? 'has-file' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); }}
          onClick={() => !uploadFile && fileInputRef.current.click()}
        >
          <input ref={fileInputRef} type="file" accept=".csv" style={{ display: 'none' }} onChange={(e) => handleFileSelect(e.target.files[0])} />
          {!uploadFile ? (
            <>
              <Upload size={28} className="dz-icon" />
              <p className="dz-label">CSV dosyanı sürükle bırak ya da <u>seç</u></p>
            </>
          ) : (
            <div className="file-preview">
              <CheckCircle size={20} color="#10b981" />
              <span className="file-name">{uploadFile.name}</span>
              <span className="file-size">{fmtSize(uploadFile.size)}</span>
              <button className="remove-btn" onClick={(e) => { e.stopPropagation(); setUploadFile(null); }}><X size={14} /></button>
            </div>
          )}
        </div>
        {uploadFile && <button className="upload-btn" onClick={handleUpload} disabled={uploading}>📥 Sütunları Oku ve Eşleştir</button>}
        {uploadError && <p className="upload-error">⚠ {uploadError}</p>}
      </section>
      )}

      {/* --- KPI VE GRAFİKLER (Aşağısı eskisiyle aynı, sadece stilleri koruyoruz) --- */}
      <div className="kpi-row">
        {[
          { icon: <Users size={22} />, label: 'Toplam Çalışan', value: loading ? '…' : (kpiData?.total_employees || '—'), color: '#3b82f6' },
          { icon: <DollarSign size={22} />, label: 'Ort. Maaş', value: loading ? '…' : (kpiData ? `$${kpiData.value.toLocaleString()}` : '—'), color: '#10b981' },
          { icon: <AlertTriangle size={22} />, label: 'İstifa Riski', value: loading ? '…' : `${riskList.length} kişi`, color: '#f59e0b' },
          { icon: <Database size={22} />, label: 'Departman', value: loading ? '…' : (payGap.length || '—'), color: '#8b5cf6' },
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

      <div className="content-grid">
        <div className="panel">
          <h2 className="panel-title">Maaş Uçurumu (%)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={payGap} margin={{ top: 8, right: 8, left: -16, bottom: 40 }}>
              <XAxis dataKey="department" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [`${v}%`, 'Pay Gap']} />
              <Bar dataKey="gap" radius={[5, 5, 0, 0]}>
                {payGap.map((e, i) => <Cell key={i} fill={e.gap > 0 ? '#ef4444' : '#10b981'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="panel">
          <h2 className="panel-title">Riskli Çalışanlar</h2>
          <div className="risk-list">
            {riskList.map((emp, i) => (
              <div key={i} className="risk-item">
                <div className="risk-avatar">{emp.Employee_Name?.[0] ?? '?'}</div>
                <div className="risk-info">
                  <strong>{emp.Employee_Name}</strong><span className="risk-dept">{emp.Department}</span>
                </div>
                <span className="risk-salary">${emp.Salary?.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="ai-panel">
        <div className="ai-header">
          <BrainCircuit size={28} />
          <div>
            <h2 className="ai-title">Yapay Zeka Strateji Merkezi</h2>
          </div>
        </div>
        <button className="ai-btn" onClick={fetchAIReport} disabled={aiLoading}>🚀 Stratejik Özet Üret</button>
        {aiReport && (
          <div className="ai-result">
            <h3 className="ai-report-title">{aiReport.report_title}</h3>
            <p className="ai-report-body">{aiReport.ai_insight}</p>
          </div>
        )}
      </div>

      <style>{`
        /* ... Eski CSS'in tamamı ... */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root { --bg: #f1f5f9; --surface: #ffffff; --border: #e2e8f0; --text: #0f172a; --muted: #64748b; --radius: 14px; --shadow: 0 2px 12px rgba(0,0,0,0.06); --font: 'DM Sans', sans-serif; }
        body { font-family: var(--font); background: var(--bg); color: var(--text); }
        .page { max-width: 1280px; margin: 0 auto; padding: 28px 24px 60px; }
        .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; }
        .topbar-left { display: flex; align-items: center; gap: 14px; }
        .logo-mark { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #1e293b, #334155); color: #f8fafc; font-weight: 700; display: flex; align-items: center; justify-content: center; }
        .title { font-size: 22px; font-weight: 700; }
        .subtitle { font-size: 13px; color: var(--muted); }
        .topbar-right { display: flex; align-items: center; gap: 12px; }
        .session-badge { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; background: #dcfce7; color: #166534; font-size: 13px; font-weight: 500; }
        .session-badge.default { background: #f1f5f9; color: var(--muted); }
        .logout-btn { background: none; border: none; cursor: pointer; color: inherit; padding: 0 0 0 4px; opacity: 0.7; }
        
        .upload-section { margin-bottom: 24px; }
        .dropzone { border: 2px dashed var(--border); border-radius: var(--radius); padding: 28px; text-align: center; cursor: pointer; background: var(--surface); }
        .dropzone:hover { border-color: #3b82f6; background: #eff6ff; }
        .dz-icon { color: var(--muted); margin-bottom: 10px; }
        .dz-label { font-size: 15px; }
        .file-preview { display: flex; align-items: center; gap: 10px; justify-content: center; }
        .file-name { font-weight: 600; font-size: 15px; }
        .file-size { font-size: 12px; color: var(--muted); }
        .remove-btn { background: none; border: none; cursor: pointer; color: #ef4444; }
        .upload-btn { margin-top: 14px; padding: 11px 28px; background: #1e293b; color: #f8fafc; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; }
        
        .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 22px; }
        .kpi-card { background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); padding: 18px 20px; display: flex; align-items: center; gap: 14px; border-top: 3px solid var(--accent); }
        .kpi-icon { color: var(--accent); }
        .kpi-body { display: flex; flex-direction: column; }
        .kpi-label { font-size: 12px; color: var(--muted); }
        .kpi-value { font-size: 22px; font-weight: 700; }
        
        .content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 22px; }
        .panel { background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); padding: 24px; }
        .panel-title { font-size: 15px; font-weight: 600; margin-bottom: 18px; }
        
        .risk-list { display: flex; flex-direction: column; gap: 8px; max-height: 260px; overflow-y: auto; }
        .risk-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #fff7ed; border-radius: 10px; border-left: 4px solid #f59e0b; }
        .risk-avatar { width: 34px; height: 34px; border-radius: 50%; background: #fef3c7; color: #92400e; display: flex; align-items: center; justify-content: center; font-weight: 700; }
        .risk-info { flex: 1; display: flex; flex-direction: column; }
        .risk-salary { font-weight: 600; color: #10b981; }
        
        .ai-panel { background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); padding: 30px; border-top: 4px solid #6366f1; }
        .ai-header { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 22px; color: #6366f1; }
        .ai-btn { padding: 12px 28px; background: #6366f1; color: #fff; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; }
        .ai-result { margin-top: 22px; padding: 22px 26px; background: #f5f3ff; border-radius: 12px; border-left: 5px solid #6366f1; }
        .ai-report-title { font-size: 17px; font-weight: 700; color: #3730a3; margin-bottom: 14px; }
        .ai-report-body { white-space: pre-line; color: #374151; line-height: 1.85; font-size: 14px; }

        /* YENİ: MAPPING MODAL CSS */
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: white; padding: 30px; border-radius: 16px; width: 500px; max-width: 90vw; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
        .modal-content h3 { font-size: 20px; color: #0f172a; margin-bottom: 8px; }
        .modal-content p { font-size: 14px; color: #64748b; margin-bottom: 24px; }
        .mapping-grid { display: flex; flex-direction: column; gap: 16px; }
        .mapping-row { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 12px 16px; border-radius: 8px; border: 1px solid #e2e8f0; }
        .target-label { font-weight: 600; color: #334155; display: flex; align-items: center; gap: 8px; width: 160px; }
        .mapping-row select { flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; outline: none; font-family: inherit; }
      `}</style>
    </div>
  );
}
