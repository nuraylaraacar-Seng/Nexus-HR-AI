import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import {
  Users, DollarSign, BrainCircuit, AlertTriangle,
  Upload, X, CheckCircle, Database, LogOut, Activity, ArrowRight
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

const REQUIRED_COLS = ["Salary", "Department", "Termd", "EngagementSurvey"];
const OPTIONAL_COLS = [
  "PerformanceScore", "SpecialProjectsCount", "DateofHire",
  "Employee_Name", "ManagerName", "EmpSatisfaction", "Sex"
];
const ALL_COLS = [...REQUIRED_COLS, ...OPTIONAL_COLS];

const COL_LABELS = {
  Salary: "Maaş", Department: "Departman", Termd: "Ayrılma durumu (0/1)",
  EngagementSurvey: "Bağlılık skoru", PerformanceScore: "Performans notu",
  SpecialProjectsCount: "Özel proje sayısı", DateofHire: "İşe giriş tarihi",
  Employee_Name: "Çalışan adı", ManagerName: "Yönetici adı",
  EmpSatisfaction: "Memnuniyet skoru", Sex: "Cinsiyet (M/F)",
};

function makeHeaders(sid) {
  return sid ? { 'X-Session-ID': sid } : {};
}
const fmtSize = (b) =>
  b < 1048576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1048576).toFixed(1)} MB`;

// ─── MAPPING MODAL ───────────────────────────────────────────────────────────
function MappingModal({ pendingId, datasetColumns, autoDetected, onSuccess, onCancel }) {
  const [mapping, setMapping] = useState(() => {
    const init = {};
    ALL_COLS.forEach(std => { init[std] = autoDetected[std] || ""; });
    return init;
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr]       = useState(null);

  const missingRequired = REQUIRED_COLS.filter(c => !mapping[c]);

  const handleConfirm = async () => {
    if (missingRequired.length > 0) {
      setErr(`Şu zorunlu alanları eşleştir: ${missingRequired.map(c => COL_LABELS[c]).join(', ')}`);
      return;
    }
    setSaving(true); setErr(null);
    try {
      const res = await axios.post(
        `${API_BASE}/upload-dataset/confirm-mapping/${pendingId}`,
        { mapping }
      );
      if (res.data.status === 'success') {
        onSuccess(res.data.session_id, res.data.summary);
      } else {
        setErr(res.data.detail || 'Eşleştirme kaydedilemedi.');
      }
    } catch (e) {
      setErr(e.response?.data?.detail || 'Sunucu hatası. Konsolu kontrol et.');
    }
    setSaving(false);
  };

  return (
    <div style={ms.overlay}>
      <div style={ms.modal}>
        {/* Başlık */}
        <div style={ms.head}>
          <div>
            <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>🔗 Kolon Eşleştirme</h2>
            <p style={{ margin: '4px 0 0', fontSize: 12, color: '#94a3b8' }}>
              CSV kolonlarını sistem alanlarıyla eşleştir.{' '}
              <span style={{ color: '#ef4444' }}>*</span> zorunlu.
            </p>
          </div>
          <button style={ms.closeBtn} onClick={onCancel}><X size={16} /></button>
        </div>

        {/* Liste */}
        <div style={ms.body}>
          {ALL_COLS.map(std => {
            const isReq = REQUIRED_COLS.includes(std);
            const val   = mapping[std];
            const ok    = !!val;
            return (
              <div key={std}
                style={{
                  ...ms.row,
                  borderColor: ok ? 'rgba(16, 185, 129, 0.4)' : isReq ? 'rgba(239, 68, 68, 0.4)' : 'rgba(255,255,255,0.05)',
                  background:  ok ? 'rgba(16, 185, 129, 0.1)' : isReq ? 'rgba(239, 68, 68, 0.1)' : 'transparent',
                }}
              >
                <div style={ms.leftCol}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>
                    {COL_LABELS[std]}
                    {isReq && <span style={{ color: '#ef4444' }}> *</span>}
                  </span>
                  <code style={{ fontSize: 10, color: '#64748b' }}>{std}</code>
                </div>
                <ArrowRight size={13} color="#64748b" style={{ flexShrink: 0 }} />
                <select
                  style={{
                    ...ms.select,
                    borderColor: ok ? '#10b981' : 'rgba(255,255,255,0.1)',
                    color: val ? '#fff' : '#94a3b8',
                    background: 'rgba(15, 23, 42, 0.8)',
                  }}
                  value={val}
                  onChange={e => setMapping(p => ({ ...p, [std]: e.target.value }))}
                >
                  <option value="">— seç —</option>
                  {datasetColumns.map(col => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
            );
          })}
        </div>

        {err && <div style={ms.err}>⚠ {err}</div>}

        {/* Footer */}
        <div style={ms.foot}>
          <button style={ms.cancelBtn} onClick={onCancel}>İptal</button>
          <button
            style={{ ...ms.confirmBtn, opacity: missingRequired.length > 0 ? .45 : 1 }}
            onClick={handleConfirm}
            disabled={saving || missingRequired.length > 0}
          >
            {saving ? '⏳ Kaydediliyor…' : '✓ Eşleştirmeyi Onayla'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── ANA UYGULAMA ────────────────────────────────────────────────────────────
export default function App() {
  const [sessionId, setSessionId] = useState(() => sessionStorage.getItem('nexus_session') || null);
  const [summary,   setSummary]   = useState(null);
  const [aiReport,  setAiReport]  = useState(null);
  const [riskList,  setRiskList]  = useState([]);
  const [payGap,    setPayGap]    = useState([]);
  const [kpiData,   setKpiData]   = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error,     setError]     = useState(null);
  const [uploadFile,  setUploadFile]  = useState(null);
  const [uploading,   setUploading]   = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragOver,    setDragOver]    = useState(false);
  const [mappingData, setMappingData] = useState(null);
  const fileInputRef = useRef();

  
const fetchAll = async (sid) => {
  if (!sid) return; 
  setLoading(true); setAiReport(null); setError(null);
  const h = makeHeaders(sid);
  
  try {
    const [kpiRes, riskRes, gapRes] = await Promise.all([
      axios.post(`${API_BASE}/analytics/kpi`,
        { department: 'All', metric: 'Salary', calc_type: 'mean' }, { headers: h }),
      axios.get(`${API_BASE}/analytics/flight-risk`, { headers: h }),
      axios.get(`${API_BASE}/analytics/gender-pay-gap`, { headers: h }),
    ]);

    setKpiData(kpiRes.data.data || kpiRes.data); 
    setRiskList(riskRes.data.data || riskRes.data || []);
    
    const gapRaw = gapRes.data.data || gapRes.data || {};
    setPayGap(
      Object.entries(gapRaw).map(([dept, v]) => ({
        department: dept,
        gap: v.Pay_Gap_Percentage || 0,
        male: v.M || 0,
        female: v.F || 0,
      }))
    );
  } catch (e) {
    console.error("Fetch Hatası:", e.response?.data || e.message);
    setError('Veriler alınamadı. Backend veya Kimlik (Session) hatası.');
  } finally {
    setLoading(false);
  }
};
useEffect(() => {
  if (sessionId) {
    fetchAll(sessionId);
  }
}, [sessionId]);

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.name.endsWith('.csv')) { setUploadError('Sadece .csv dosyaları kabul edilir.'); return; }
    setUploadFile(file); setUploadError(null);
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true); setUploadError(null);
    const fd = new FormData();
    fd.append('file', uploadFile);
    try {
      const res = await axios.post(`${API_BASE}/upload-dataset`, fd);
      const d = res.data;
      if (d.status === 'error') {
        setUploadError(d.message);
      } else if (d.needs_mapping) {
        setMappingData({
          pendingId:      d.pending_id,
          datasetColumns: d.dataset_columns,
          autoDetected:   d.auto_detected || {},
        });
        setUploadFile(null);
      } else {
        activateSession(d.session_id, d.summary);
      }
    } catch (e) {
      console.error(e);
      setUploadError('Yükleme başarısız. Backend çalışıyor mu?');
    }
    setUploading(false);
  };

  const activateSession = (newSid, newSummary) => {
    sessionStorage.setItem('nexus_session', newSid);
    setSessionId(newSid);
    setSummary(newSummary);
    setUploadFile(null);
    setMappingData(null);
    fetchAll(newSid); 
  };

  const handleLogout = async () => {
    if (!sessionId) return;
    try { await axios.delete(`${API_BASE}/session`, { headers: makeHeaders(sessionId) }); } catch {}
    sessionStorage.removeItem('nexus_session');
    setSessionId(null); setSummary(null); setAiReport(null);
    fetchAll(null);
  };

  const fetchAI = async () => {
    setAiLoading(true); setError(null);
    try {
      const res = await axios.get(`${API_BASE}/ai/executive-summary`, { headers: makeHeaders(sessionId) });
      setAiReport(res.data.data);
    } catch {
      setError("AI raporu alınamadı. API key tanımlı mı?");
    }
    setAiLoading(false);
  };

  // KALKAN 1: Çökmeyi önleyen güvenli okumalar
  const totalEmp = summary?.total_employees ?? 0;
  const riskRate = totalEmp > 0 ? `${(((riskList?.length || 0) / totalEmp) * 100).toFixed(1)}%` : '—';

  return (
    <div style={s.page}>
      {/* MAPPING MODAL */}
      {mappingData && (
        <MappingModal
          pendingId={mappingData.pendingId}
          datasetColumns={mappingData.datasetColumns}
          autoDetected={mappingData.autoDetected}
          onSuccess={activateSession}
          onCancel={() => setMappingData(null)}
        />
      )}

      {/* TOPBAR */}
      <header style={s.topbar}>
        <div style={s.tbLeft}>
          <BrainCircuit size={32} color="#4f46e5" />
          <h1 style={s.titleGradient}>Nexus HR</h1>
        </div>
        {sessionId ? (
          <div style={{ ...s.badge, ...s.badgeCustom }}>
            <CheckCircle size={13} />
            <span>Özel dataset aktif</span>
            <button style={s.logoutBtn} onClick={handleLogout}><LogOut size={13} /></button>
          </div>
        ) : (
          <div style={{ ...s.badge, ...s.badgeDefault }}>
            <Database size={13} /><span>Varsayılan dataset</span>
          </div>
        )}
      </header>

      {/* UPLOAD ZONE */}
      <div
        style={{ ...s.dropzone, ...(dragOver ? s.dzOver : {}), ...(uploadFile ? s.dzHasFile : {}) }}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); }}
        onClick={() => !uploadFile && fileInputRef.current.click()}
      >
        <input ref={fileInputRef} type="file" accept=".csv" style={{ display: 'none' }}
               onChange={e => handleFileSelect(e.target.files[0])} />
        {!uploadFile ? (
          <div style={{ textAlign: 'center' }}>
            <Upload size={26} style={{ color: '#38bdf8', marginBottom: 8 }} />
            <p style={s.dzLabel}>CSV dosyanı sürükle bırak ya da <u style={{color:'#38bdf8'}}>seç</u></p>
          </div>
        ) : (
          <div style={s.filePrev}>
            <CheckCircle size={18} color="#10b981" />
            <span style={s.fileName}>{uploadFile.name}</span>
            <span style={s.fileSize}>{fmtSize(uploadFile.size)}</span>
            <button style={s.removeBtn} onClick={e => { e.stopPropagation(); setUploadFile(null); }}>
              <X size={13} />
            </button>
          </div>
        )}
      </div>

      {uploadFile && (
        <button style={s.uploadBtn} onClick={handleUpload} disabled={uploading}>
          {uploading ? '⏳ Yükleniyor…' : '📤 Dosyayı Oku ve Eşleştir'}
        </button>
      )}
      {uploadError && <p style={s.uploadErr}>⚠ {uploadError}</p>}

      {summary && (
        <div style={s.strip}>
          <CheckCircle size={14} color="#34d399" />
          <span>Dataset aktif</span>
          <span style={s.sep}>·</span>
          <span><b style={{color:'#f8fafc'}}>{summary.total_employees?.toLocaleString()}</b> çalışan</span>
          <span style={s.sep}>·</span>
          <span>Ort. maaş <b style={{color:'#f8fafc'}}>${summary.average_salary?.toLocaleString()}</b></span>
          <span style={s.sep}>·</span>
          <span>Risk <b style={{color:'#ef4444'}}>{summary.flight_risk_count}</b> kişi</span>
          <span style={s.sep}>·</span>
          <span>Bağlılık <b style={{color:'#f8fafc'}}>{summary.average_engagement}</b></span>
        </div>
      )}

      {/* KPI KARTLARI (Kalkanlar eklendi) */}
      <div style={s.kpiRow}>
        {[
          { icon: <Users size={20} />,        label: 'Toplam çalışan', value: loading ? '…' : (totalEmp ? totalEmp.toLocaleString() : '—'), acc: '#38bdf8' },
          { icon: <DollarSign size={20} />,    label: 'Ort. maaş',     value: loading ? '…' : (kpiData?.value ? `$${kpiData.value.toLocaleString()}` : '—'), acc: '#10b981' },
          { icon: <AlertTriangle size={20} />, label: 'İstifa riski',  value: loading ? '…' : `${riskList?.length || 0} kişi`, acc: '#f97316' },
          { icon: <Activity size={20} />,      label: 'Risk oranı',    value: loading ? '…' : riskRate, acc: '#ef4444' },
          { icon: <Database size={20} />,      label: 'Departman',     value: loading ? '…' : (payGap?.length || '—'), acc: '#8b5cf6' },
        ].map((k, i) => (
          <div key={i} style={{ ...s.kpiCard, borderTop: `2px solid ${k.acc}` }}>
            <div style={{ color: k.acc, filter: `drop-shadow(0 0 8px ${k.acc}80)` }}>{k.icon}</div>
            <div>
              <p style={s.kpiLabel}>{k.label}</p>
              <p style={s.kpiValue}>{k.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* İÇERİK */}
      <div style={s.twoCol}>
        <div style={s.panel}>
          <h2 style={s.panelTitle}>Cinsiyet Maaş Uçurumu (%)</h2>
          {loading && <p style={s.muted}>Yükleniyor…</p>}
          {!loading && (!payGap || payGap.length === 0) && <p style={s.muted}>Veri bulunamadı.</p>}
          {payGap?.length > 0 && (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={payGap} margin={{ top: 8, right: 8, left: -18, bottom: 48 }}>
                <XAxis dataKey="department" tick={{ fontSize: 11, fill: '#94a3b8' }} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip
                  formatter={v => [`${v}%`, 'Pay Gap']}
                  contentStyle={{ borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(15, 23, 42, 0.9)', color: '#f8fafc' }}
                />
                <Bar dataKey="gap" radius={[5, 5, 0, 0]}>
                  {payGap.map((e, i) => <Cell key={i} fill={e.gap > 0 ? '#ef4444' : '#10b981'} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
          <p style={s.hint}>
            <span style={{ color: '#ef4444' }}>● </span>Erkek lehine &nbsp;
            <span style={{ color: '#10b981' }}>● </span>Kadın lehine
          </p>
        </div>

        <div style={s.panel}>
          <h2 style={s.panelTitle}>İstifa Riski Yüksek Çalışanlar</h2>
          <div style={s.riskList}>
            {loading && <p style={s.muted}>Yükleniyor…</p>}
            {!loading && (!riskList || riskList.length === 0) && <p style={s.muted}>Risk taşıyan çalışan bulunamadı.</p>}
            
            {/* KALKAN 2: Array.isArray kontrolü */}
            {Array.isArray(riskList) && riskList.map((emp, i) => (
              <div key={i} style={s.riskItem}>
                <div style={s.avatar}>{(emp.Employee_Name || '?')[0]}</div>
                <div style={s.riskInfo}>
                  <strong style={{ fontSize: 13, color: '#f8fafc' }}>{emp.Employee_Name ?? '—'}</strong>
                  <span style={s.riskDept}>{emp.Department}</span>
                </div>
                <span style={s.riskSal}>${emp.Salary?.toLocaleString() ?? '—'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI */}
      <div style={s.aiPanel}>
        <div style={s.aiHeader}>
          <div style={{ filter: 'drop-shadow(0 0 10px rgba(99,102,241,0.8))' }}>
             <BrainCircuit size={32} color="#818cf8" />
          </div>
          <div>
            <h2 style={s.aiTitle}>Yapay Zeka Strateji Merkezi</h2>
          </div>
        </div>
        <button style={s.aiBtn} onClick={fetchAI} disabled={aiLoading}>
          {aiLoading ? '⏳ AI Analiz Ediyor...' : '🚀 Stratejik Özet Üret'}
        </button>
        {error && <div style={s.errBox}>{error}</div>}
        {aiReport && (
          <div style={s.aiResult}>
            <h3 style={s.aiRT}>{aiReport.report_title}</h3>
            <p style={s.aiRB}>{aiReport.ai_insight}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── STİLLER (CYBERPUNK / FANTASTİK DARK VERSİYON) ──────────────────────────
const s = {
  page:      { padding: '24px 3%', fontFamily: "'Inter', sans-serif", background: 'radial-gradient(circle at 50% 0%, #1e1b4b, #020617)', minHeight: '100vh', width: '100%', boxSizing: 'border-box', color: '#e2e8f0' },
  topbar:    { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  tbLeft:    { display: 'flex', alignItems: 'center', gap: 14 },
  titleGradient: { fontSize: 28, fontWeight: 900, margin: 0, background: 'linear-gradient(to right, #00f2fe, #4facfe, #00f2fe)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', textShadow: '0 0 20px rgba(0, 242, 254, 0.4)' },
  
  badge:     { display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700, letterSpacing: '0.5px' },
  badgeCustom:  { background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.5)', boxShadow: '0 0 15px rgba(16, 185, 129, 0.2)' },
  badgeDefault: { background: 'rgba(255, 255, 255, 0.05)', color: '#94a3b8', border: '1px solid rgba(255, 255, 255, 0.1)' },
  logoutBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', padding: '0 0 0 6px', display: 'flex', alignItems: 'center', filter: 'drop-shadow(0 0 5px rgba(239,68,68,0.5))' },
  
  dropzone:  { border: '2px dashed rgba(56, 188, 248, 0.4)', borderRadius: 16, padding: '32px 20px', textAlign: 'center', cursor: 'pointer', background: 'rgba(15, 23, 42, 0.6)', transition: 'all .3s ease-in-out', marginBottom: 12, backdropFilter: 'blur(10px)' },
  dzOver:    { borderColor: '#38bdf8', background: 'rgba(56, 188, 248, 0.1)', transform: 'scale(1.02)', boxShadow: '0 0 30px rgba(56, 188, 248, 0.2)' },
  dzHasFile: { borderStyle: 'solid', borderColor: '#10b981', background: 'rgba(16, 185, 129, 0.05)', cursor: 'default', boxShadow: '0 0 20px rgba(16, 185, 129, 0.1)' },
  dzLabel:   { fontSize: 15, fontWeight: 600, color: '#e2e8f0', margin: 0 },
  filePrev:  { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, flexWrap: 'wrap' },
  fileName:  { fontSize: 14, fontWeight: 700, color: '#38bdf8' },
  fileSize:  { fontSize: 11, color: '#64748b', fontFamily: 'monospace' },
  removeBtn: { background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', cursor: 'pointer', color: '#ef4444', display: 'flex', alignItems: 'center', padding: '4px 8px', borderRadius: 6 },
  
  uploadBtn: { padding: '14px 24px', background: 'linear-gradient(90deg, #0f172a, #1e1b4b)', color: '#38bdf8', border: '1px solid rgba(56, 188, 248, 0.4)', borderRadius: 12, fontSize: 14, fontWeight: 700, cursor: 'pointer', marginBottom: 16, display: 'block', width: '100%', textTransform: 'uppercase', letterSpacing: '1px', boxShadow: '0 0 20px rgba(56, 188, 248, 0.15)' },
  uploadErr: { color: '#f87171', fontSize: 13, marginBottom: 10, fontWeight: 600, textShadow: '0 0 10px rgba(248,113,113,0.5)' },
  
  strip:     { display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', padding: '12px 20px', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: 12, fontSize: 14, color: '#34d399', marginBottom: 20, boxShadow: '0 0 20px rgba(16, 185, 129, 0.1)' },
  sep:       { color: '#059669' },
  kpiRow:    { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 20, marginBottom: 28 },
  
  kpiCard:   { background: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(16px)', borderRadius: 16, border: '1px solid rgba(255,255,255,0.05)', padding: '20px 22px', display: 'flex', alignItems: 'center', gap: 16, boxShadow: '0 10px 30px rgba(0,0,0,0.5)' },
  kpiLabel:  { fontSize: 12, color: '#94a3b8', margin: '0 0 6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' },
  kpiValue:  { fontSize: 28, fontWeight: 900, color: '#f8fafc', margin: 0, fontFamily: 'monospace' },
  twoCol:    { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(350px,1fr))', gap: 24, marginBottom: 28 },
  
  panel:     { background: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(16px)', borderRadius: 18, border: '1px solid rgba(255,255,255,0.05)', padding: 26, boxShadow: '0 15px 40px rgba(0,0,0,0.4)' },
  panelTitle:{ fontSize: 16, fontWeight: 800, color: '#e2e8f0', margin: '0 0 20px', letterSpacing: '0.5px', textTransform: 'uppercase' },
  hint:      { fontSize: 12, color: '#64748b', marginTop: 12, fontWeight: 600 },
  muted:     { fontSize: 14, color: '#475569', padding: '24px 0', textAlign: 'center' },
  riskList:  { display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 280, overflowY: 'auto', paddingRight: 6 },
  
  riskItem:  { display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: 'rgba(0, 0, 0, 0.3)', borderRadius: 12, borderLeft: '4px solid #f97316', border: '1px solid rgba(249, 115, 22, 0.1)' },
  avatar:    { width: 38, height: 38, borderRadius: '50%', background: 'rgba(249, 115, 22, 0.1)', color: '#fb923c', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 15, flexShrink: 0, border: '1px solid rgba(249, 115, 22, 0.3)', textShadow: '0 0 10px rgba(249,115,22,0.5)' },
  riskInfo:  { flex: 1, display: 'flex', flexDirection: 'column' },
  riskDept:  { fontSize: 12, color: '#94a3b8', marginTop: 2 },
  riskSal:   { fontFamily: 'monospace', fontSize: 15, color: '#10b981', fontWeight: 800, textShadow: '0 0 10px rgba(16,185,129,0.4)' },
  
  aiPanel:   { background: 'rgba(30, 27, 75, 0.4)', backdropFilter: 'blur(20px)', borderRadius: 20, border: '1px solid rgba(99, 102, 241, 0.2)', padding: 32, boxShadow: '0 0 40px rgba(99, 102, 241, 0.1)' },
  aiHeader:  { display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 },
  aiTitle:   { fontSize: 22, fontWeight: 900, color: '#c7d2fe', margin: 0, letterSpacing: '1px', textShadow: '0 0 15px rgba(199, 210, 254, 0.3)' },
  
  aiBtn:     { padding: '16px 36px', background: 'linear-gradient(90deg, #4f46e5 0%, #db2777 100%)', color: '#fff', border: 'none', borderRadius: 12, fontSize: 16, fontWeight: 800, cursor: 'pointer', transition: 'all .2s', boxShadow: '0 0 25px rgba(219, 39, 119, 0.6)', textTransform: 'uppercase', letterSpacing: '2px' },
  errBox:    { marginTop: 16, padding: '14px 18px', background: 'rgba(185, 28, 28, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 10, color: '#fca5a5', fontSize: 14 },
  
  aiResult:  { marginTop: 28, padding: '26px 30px', background: 'rgba(0, 0, 0, 0.4)', borderRadius: 14, borderLeft: '5px solid #818cf8', boxShadow: 'inset 0 0 20px rgba(99,102,241,0.1)' },
  aiRT:      { fontSize: 18, fontWeight: 900, color: '#818cf8', margin: '0 0 16px', letterSpacing: '1px', textTransform: 'uppercase', textShadow: '0 0 10px rgba(129, 140, 248, 0.4)' },
  aiRB:      { fontSize: 15, color: '#cbd5e1', lineHeight: 1.85, whiteSpace: 'pre-line', margin: 0 },
};

const ms = {
  overlay:   { position: 'fixed', inset: 0, background: 'rgba(15,23,42,.85)', backdropFilter: 'blur(10px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 },
  modal:     { background: '#1e1b4b', borderRadius: 18, width: '100%', maxWidth: 660, maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: '0 24px 60px rgba(0,0,0,.6)', border: '1px solid rgba(255,255,255,0.05)' },
  head:      { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '20px 24px 12px' },
  closeBtn:  { background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', padding: 4, borderRadius: 6, flexShrink: 0 },
  body:      { overflowY: 'auto', padding: '0 24px 4px', display: 'flex', flexDirection: 'column', gap: 7 },
  row:       { display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.05)', transition: 'all .15s' },
  leftCol:   { display: 'flex', flexDirection: 'column', minWidth: 170, flexShrink: 0 },
  select:    { flex: 1, padding: '7px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', fontSize: 13, background: 'transparent', outline: 'none', cursor: 'pointer' },
  err:       { margin: '10px 24px 0', padding: '10px 14px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 8, color: '#fca5a5', fontSize: 13 },
  foot:      { display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px 18px', borderTop: '1px solid rgba(255,255,255,0.05)', marginTop: 12 },
  cancelBtn: { padding: '9px 20px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', borderRadius: 9, fontSize: 14, cursor: 'pointer', fontWeight: 500 },
  confirmBtn:{ padding: '9px 22px', background: 'linear-gradient(135deg, #6366f1 0%, #db2777 100%)', color: '#fff', border: 'none', borderRadius: 9, fontSize: 14, fontWeight: 700, cursor: 'pointer', transition: 'opacity .15s' },
};
