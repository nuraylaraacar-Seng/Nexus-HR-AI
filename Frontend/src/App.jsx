import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Activity, Users, DollarSign, BrainCircuit, AlertTriangle, Upload, X, CheckCircle, Database, LogOut } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

function makeHeaders(sid) {
  return sid ? { 'X-Session-ID': sid } : {};
}

const fmtSize = (bytes) =>
  bytes < 1024 * 1024
    ? `${(bytes / 1024).toFixed(1)} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

export default function App() {
  const [sessionId, setSessionId] = useState(
    () => sessionStorage.getItem('nexus_session') || null
  );
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
  const fileInputRef = useRef();

  // ★ sid'i doğrudan parametre olarak alır — state closure tuzağını önler
  const fetchAll = async (sid) => {
    setLoading(true);
    setAiReport(null);
    setError(null);
    const h = makeHeaders(sid);
    try {
      const [kpiRes, riskRes, gapRes] = await Promise.all([
        axios.post(
          `${API_BASE}/analytics/kpi`,
          { department: 'All', metric: 'Salary', calc_type: 'mean' },
          { headers: h }
        ),
        axios.get(`${API_BASE}/analytics/flight-risk`, { headers: h }),
        axios.get(`${API_BASE}/analytics/gender-pay-gap`, { headers: h }),
      ]);

      setKpiData(kpiRes.data.data);
      setRiskList(riskRes.data.data ?? []);

      const formatted = Object.entries(gapRes.data.data ?? {}).map(([dept, vals]) => ({
        department: dept,
        gap:    vals.Pay_Gap_Percentage ?? 0,
        male:   vals.M   ?? 0,
        female: vals.F   ?? 0,
      }));
      setPayGap(formatted);
    } catch (e) {
      console.error('fetchAll hatası:', e);
      setError('Veriler alınamadı. Backend bağlantısını kontrol et.');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAll(sessionId);
  }, []); // eslint-disable-line

  const fetchAIReport = async () => {
    setAiLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/ai/executive-summary`, {
        headers: makeHeaders(sessionId),
      });
      setAiReport(res.data.data);
    } catch {
      setError("AI raporu alınamadı. Backend'in çalıştığından ve API key'in tanımlı olduğundan emin ol.");
    }
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

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', uploadFile);
    try {
      const res = await axios.post(`${API_BASE}/upload-dataset`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.status === 'error') {
        setUploadError(res.data.message);
      } else {
        const newSid = res.data.session_id;
        sessionStorage.setItem('nexus_session', newSid);
        setSessionId(newSid);
        setSummary(res.data.summary);
        setUploadFile(null);
        // ★ State güncellemesini beklemeden yeni sid'i doğrudan geç
        await fetchAll(newSid);
      }
    } catch (e) {
      setUploadError(e.response?.data?.message || 'Yükleme başarısız.');
    }
    setUploading(false);
  };

  const handleLogout = async () => {
    if (!sessionId) return;
    try {
      await axios.delete(`${API_BASE}/session`, { headers: makeHeaders(sessionId) });
    } catch {}
    sessionStorage.removeItem('nexus_session');
    setSessionId(null);
    setSummary(null);
    setAiReport(null);
    await fetchAll(null);
  };

  const totalEmployees = kpiData?.total_employees ?? 0;
  const riskRate = totalEmployees > 0
    ? `${((riskList.length / totalEmployees) * 100).toFixed(1)}%`
    : '—';

  return (
    <div style={s.page}>

      <header style={s.topbar}>
        <div style={s.tbLeft}>
          <div style={s.logo}>NX</div>
          <div>
            <h1 style={s.title}>Nexus HR</h1>
            <p style={s.sub}>Enterprise Intelligence Platform</p>
          </div>
        </div>
        {sessionId ? (
          <div style={{...s.badge, ...s.badgeCustom}}>
            <CheckCircle size={13} />
            <span>Özel dataset aktif</span>
            <button style={s.logoutBtn} onClick={handleLogout} title="Session'ı sil">
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <div style={{...s.badge, ...s.badgeDefault}}>
            <Database size={13} />
            <span>Varsayılan dataset</span>
          </div>
        )}
      </header>

      {/* UPLOAD */}
      <div
        style={{
          ...s.dropzone,
          ...(dragOver ? s.dzOver : {}),
          ...(uploadFile ? s.dzHasFile : {}),
        }}
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
          <div style={{ textAlign: 'center' }}>
            <Upload size={26} style={{ color: '#94a3b8', marginBottom: 8 }} />
            <p style={s.dzLabel}>CSV dosyanı sürükle bırak ya da <u>seç</u></p>
            <p style={s.dzHint}>Zorunlu kolonlar: Salary · Department · Termd · EngagementSurvey</p>
          </div>
        ) : (
          <div style={s.filePrev}>
            <CheckCircle size={18} color="#10b981" />
            <span style={s.fileName}>{uploadFile.name}</span>
            <span style={s.fileSize}>{fmtSize(uploadFile.size)}</span>
            <button style={s.removeBtn} onClick={(e) => { e.stopPropagation(); setUploadFile(null); }}>
              <X size={13} />
            </button>
          </div>
        )}
      </div>

      {uploadFile && (
        <button style={s.uploadBtn} onClick={handleUpload} disabled={uploading}>
          {uploading ? '⏳ Yükleniyor…' : '📤 Dataset Yükle & Analiz Et'}
        </button>
      )}
      {uploadError && <p style={s.uploadErr}>⚠ {uploadError}</p>}

      {summary && (
        <div style={s.summaryStrip}>
          <CheckCircle size={14} color="#16a34a" />
          <span>Dataset yüklendi</span>
          <span style={s.sep}>·</span>
          <span><strong>{summary.total_employees?.toLocaleString()}</strong> çalışan</span>
          <span style={s.sep}>·</span>
          <span>Ort. maaş <strong>${summary.average_salary?.toLocaleString()}</strong></span>
          <span style={s.sep}>·</span>
          <span>Risk <strong>{summary.flight_risk_count}</strong> kişi</span>
          <span style={s.sep}>·</span>
          <span>Bağlılık <strong>{summary.average_engagement}</strong></span>
        </div>
      )}

      {/* KPI */}
      <div style={s.kpiRow}>
        {[
          { icon: <Users size={20} />,        label: 'Toplam çalışan', value: loading ? '…' : (totalEmployees ? totalEmployees.toLocaleString() : '—'), acc: '#3b82f6' },
          { icon: <DollarSign size={20} />,    label: 'Ort. maaş',     value: loading ? '…' : (kpiData ? `$${kpiData.value.toLocaleString()}` : '—'), acc: '#10b981' },
          { icon: <AlertTriangle size={20} />, label: 'İstifa riski',  value: loading ? '…' : `${riskList.length} kişi`, acc: '#f59e0b' },
          { icon: <Activity size={20} />,      label: 'Risk oranı',    value: loading ? '…' : riskRate, acc: '#ef4444' },
          { icon: <Database size={20} />,      label: 'Departman',     value: loading ? '…' : (payGap.length || '—'), acc: '#8b5cf6' },
        ].map((k, i) => (
          <div key={i} style={{ ...s.kpiCard, borderTop: `3px solid ${k.acc}` }}>
            <div style={{ color: k.acc }}>{k.icon}</div>
            <div>
              <p style={s.kpiLabel}>{k.label}</p>
              <p style={s.kpiValue}>{k.value}</p>
            </div>
          </div>
        ))}
      </div>

      <div style={s.twoCol}>
        <div style={s.panel}>
          <h2 style={s.panelTitle}>Cinsiyet Maaş Uçurumu (%)</h2>
          {loading && <p style={s.muted}>Yükleniyor…</p>}
          {!loading && payGap.length === 0 && <p style={s.muted}>Veri bulunamadı.</p>}
          {payGap.length > 0 && (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={payGap} margin={{ top: 8, right: 8, left: -18, bottom: 48 }}>
                <XAxis dataKey="department" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v) => [`${v}%`, 'Pay Gap']}
                  contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 16px rgba(0,0,0,.1)' }}
                />
                <Bar dataKey="gap" radius={[5, 5, 0, 0]}>
                  {payGap.map((e, i) => (
                    <Cell key={i} fill={e.gap > 0 ? '#ef4444' : '#10b981'} />
                  ))}
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
            {!loading && riskList.length === 0 && <p style={s.muted}>Risk taşıyan çalışan bulunamadı.</p>}
            {riskList.map((emp, i) => (
              <div key={i} style={s.riskItem}>
                <div style={s.avatar}>{emp.Employee_Name?.[0] ?? '?'}</div>
                <div style={s.riskInfo}>
                  <strong style={{ fontSize: 13 }}>{emp.Employee_Name}</strong>
                  <span style={s.riskDept}>{emp.Department}</span>
                </div>
                <span style={s.riskSalary}>${emp.Salary?.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={s.aiPanel}>
        <div style={s.aiHeader}>
          <BrainCircuit size={26} color="#6366f1" />
          <div>
            <h2 style={s.aiTitle}>Yapay Zeka Strateji Merkezi</h2>
            <p style={s.aiSub}>
              {sessionId
                ? 'Yüklediğin dataset üzerinden analiz yapılacak.'
                : 'Varsayılan dataset üzerinden analiz yapılacak.'}
            </p>
          </div>
        </div>
        <button style={s.aiBtn} onClick={fetchAIReport} disabled={aiLoading}>
          {aiLoading ? '⏳ Analiz ediliyor…' : '🚀 Stratejik Özet Üret'}
        </button>
        {error && <div style={s.errorBox}>{error}</div>}
        {aiReport && (
          <div style={s.aiResult}>
            <h3 style={s.aiReportTitle}>{aiReport.report_title}</h3>
            <p style={s.aiReportBody}>{aiReport.ai_insight}</p>
          </div>
        )}
      </div>
    </div>
  );
}

const s = {
  page:      { padding: '28px 24px 60px', fontFamily: "'DM Sans','Segoe UI',sans-serif", background: '#f1f5f9', minHeight: '100vh', maxWidth: 1280, margin: '0 auto' },
  topbar:    { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  tbLeft:    { display: 'flex', alignItems: 'center', gap: 12 },
  logo:      { width: 42, height: 42, borderRadius: 10, background: '#1e293b', color: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 14, letterSpacing: 1 },
  title:     { fontSize: 20, fontWeight: 700, color: '#0f172a', margin: 0 },
  sub:       { fontSize: 12, color: '#64748b', margin: '2px 0 0' },
  badge:     { display: 'flex', alignItems: 'center', gap: 6, padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 500 },
  badgeCustom:  { background: '#dcfce7', color: '#166534' },
  badgeDefault: { background: '#f1f5f9', color: '#64748b', border: '1px solid #e2e8f0' },
  logoutBtn: { background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', display: 'flex', alignItems: 'center', padding: '0 0 0 4px', opacity: 0.7 },
  dropzone:  { border: '2px dashed #cbd5e1', borderRadius: 14, padding: '26px 20px', textAlign: 'center', cursor: 'pointer', background: '#fff', transition: 'all .2s', marginBottom: 12 },
  dzOver:    { borderColor: '#3b82f6', background: '#eff6ff' },
  dzHasFile: { borderStyle: 'solid', borderColor: '#10b981', background: '#f0fdf4', cursor: 'default' },
  dzLabel:   { fontSize: 14, color: '#334155', marginBottom: 4 },
  dzHint:    { fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' },
  filePrev:  { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, flexWrap: 'wrap' },
  fileName:  { fontSize: 14, fontWeight: 600 },
  fileSize:  { fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' },
  removeBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', display: 'flex', alignItems: 'center', padding: '2px 6px', borderRadius: 6 },
  uploadBtn: { padding: '10px 22px', background: '#1e293b', color: '#f8fafc', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer', marginBottom: 10, display: 'block' },
  uploadErr: { color: '#ef4444', fontSize: 12, marginBottom: 10 },
  summaryStrip: { display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', padding: '10px 16px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 10, fontSize: 13, color: '#166534', marginBottom: 16 },
  sep:       { color: '#86efac' },
  kpiRow:    { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 18 },
  kpiCard:   { background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 12 },
  kpiLabel:  { fontSize: 11, color: '#64748b', margin: '0 0 3px' },
  kpiValue:  { fontSize: 20, fontWeight: 700, color: '#0f172a', margin: 0, fontFamily: 'monospace' },
  twoCol:    { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16, marginBottom: 18 },
  panel:     { background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: 22 },
  panelTitle:{ fontSize: 14, fontWeight: 600, color: '#0f172a', margin: '0 0 14px' },
  hint:      { fontSize: 11, color: '#94a3b8', marginTop: 8 },
  muted:     { fontSize: 13, color: '#94a3b8', padding: '20px 0', textAlign: 'center' },
  riskList:  { display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 260, overflowY: 'auto' },
  riskItem:  { display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px', background: '#fff7ed', borderRadius: 9, borderLeft: '3px solid #f59e0b' },
  avatar:    { width: 32, height: 32, borderRadius: '50%', background: '#fef3c7', color: '#92400e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13, flexShrink: 0 },
  riskInfo:  { flex: 1, display: 'flex', flexDirection: 'column' },
  riskDept:  { fontSize: 11, color: '#94a3b8', marginTop: 2 },
  riskSalary:{ fontFamily: 'monospace', fontSize: 13, color: '#10b981', fontWeight: 600 },
  aiPanel:   { background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', borderTop: '3px solid #6366f1', padding: 26 },
  aiHeader:  { display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 18 },
  aiTitle:   { fontSize: 16, fontWeight: 700, color: '#0f172a', margin: 0 },
  aiSub:     { fontSize: 12, color: '#64748b', margin: '4px 0 0' },
  aiBtn:     { padding: '11px 26px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer' },
  errorBox:  { marginTop: 14, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 10, color: '#b91c1c', fontSize: 13 },
  aiResult:  { marginTop: 18, padding: '18px 22px', background: '#f5f3ff', borderRadius: 12, borderLeft: '4px solid #6366f1' },
  aiReportTitle: { fontSize: 15, fontWeight: 700, color: '#3730a3', margin: '0 0 12px' },
  aiReportBody:  { fontSize: 13, color: '#374151', lineHeight: 1.85, whiteSpace: 'pre-line', margin: 0 },
};
