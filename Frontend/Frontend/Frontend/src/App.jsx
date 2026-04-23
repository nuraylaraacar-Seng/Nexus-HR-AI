import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Activity, Users, DollarSign, BrainCircuit, AlertTriangle } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [aiReport, setAiReport]       = useState(null);
  const [riskList, setRiskList]       = useState([]);
  const [payGap, setPayGap]           = useState([]);
  const [kpiData, setKpiData]         = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);

  // Sayfa açılınca KPI + risk + pay-gap çek
  useEffect(() => {
    fetchKPI();
    fetchFlightRisk();
    fetchPayGap();
  }, []);

  const fetchKPI = async () => {
    try {
      const res = await axios.post(`${API_BASE}/analytics/kpi`, {
        department: 'All',
        metric: 'Salary',
        calc_type: 'mean'
      });
      setKpiData(res.data.data);
    } catch (e) {
      console.error('KPI hatası:', e);
    }
  };

  const fetchFlightRisk = async () => {
    try {
      const res = await axios.get(`${API_BASE}/analytics/flight-risk`);
      setRiskList(res.data.data);
    } catch (e) {
      console.error('Flight risk hatası:', e);
    }
  };

  const fetchPayGap = async () => {
    try {
      const res = await axios.get(`${API_BASE}/analytics/gender-pay-gap`);
      // Recharts için array formatına çeviriyoruz
      const formatted = Object.entries(res.data.data).map(([dept, vals]) => ({
        department: dept,
        gap: vals.Pay_Gap_Percentage ?? 0,
        male: vals.M ?? 0,
        female: vals.F ?? 0,
      }));
      setPayGap(formatted);
    } catch (e) {
      console.error('Pay gap hatası:', e);
    }
  };

  const fetchAIReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/ai/executive-summary`);
      setAiReport(res.data.data);
    } catch (e) {
      setError("AI raporu alınamadı. Backend'in çalıştığından ve GEMINI_API_KEY'in tanımlı olduğundan emin ol.");
    }
    setLoading(false);
  };

  return (
    <div style={styles.page}>
      {/* HEADER */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>🎯 Nexus HR: Enterprise AI Dashboard</h1>
          <p style={styles.subtitle}>Kurumsal Veri Analiz ve Karar Destek Platformu</p>
        </div>
      </header>

      {/* KPI KARTLARI */}
      <div style={styles.cardRow}>
        <div style={styles.card}>
          <Users size={28} color="#3498db" />
          <h3 style={styles.cardLabel}>İstifa Riski</h3>
          <p style={styles.cardValue}>{riskList.length} Çalışan</p>
        </div>
        <div style={styles.card}>
          <DollarSign size={28} color="#2ecc71" />
          <h3 style={styles.cardLabel}>Ort. Maaş</h3>
          <p style={styles.cardValue}>
            {kpiData ? `$${kpiData.value.toLocaleString()}` : '...'}
          </p>
        </div>
        <div style={styles.card}>
          <Activity size={28} color="#e74c3c" />
          <h3 style={styles.cardLabel}>Departman Sayısı</h3>
          <p style={styles.cardValue}>{payGap.length}</p>
        </div>
        <div style={styles.card}>
          <AlertTriangle size={28} color="#f39c12" />
          <h3 style={styles.cardLabel}>Risk Oranı</h3>
          <p style={styles.cardValue}>
            {riskList.length && kpiData
              ? `%${((riskList.length / 12) * 100).toFixed(0)}`
              : '...'}
          </p>
        </div>
      </div>

      <div style={styles.twoCol}>
        {/* CİNSİYET MAAŞ UÇURUMU GRAFİĞİ */}
        <div style={styles.panel}>
          <h2 style={styles.panelTitle}>📊 Departman Bazlı Maaş Uçurumu (%)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={payGap} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
              <XAxis dataKey="department" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => `%${v}`} />
              <Bar dataKey="gap" radius={[6, 6, 0, 0]}>
                {payGap.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.gap > 0 ? '#e74c3c' : '#2ecc71'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p style={styles.hint}>Kırmızı = Erkek lehine uçurum | Yeşil = Kadın lehine</p>
        </div>

        {/* UÇUŞ RİSKİ LİSTESİ */}
        <div style={styles.panel}>
          <h2 style={styles.panelTitle}>⚠️ İstifa Riski Yüksek Çalışanlar</h2>
          <div style={styles.riskList}>
            {riskList.length === 0 && <p style={{ color: '#999' }}>Yükleniyor...</p>}
            {riskList.map((emp, i) => (
              <div key={i} style={styles.riskItem}>
                <div>
                  <strong style={{ color: '#2c3e50' }}>{emp.Employee_Name}</strong>
                  <span style={styles.dept}>{emp.Department}</span>
                </div>
                <span style={styles.salary}>${emp.Salary?.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI STRATEJİ MERKEZİ */}
      <div style={styles.aiPanel}>
        <div style={styles.aiHeader}>
          <BrainCircuit size={32} color="#9b59b6" />
          <h2 style={{ margin: 0, color: '#2c3e50' }}>Yapay Zeka Strateji Merkezi</h2>
        </div>

        <button onClick={fetchAIReport} style={styles.button} disabled={loading}>
          {loading ? '⏳ AI Analiz Ediyor...' : '🚀 AI Stratejik Özetini Üret'}
        </button>

        {error && (
          <div style={styles.errorBox}>{error}</div>
        )}

        {aiReport && (
          <div style={styles.aiResult}>
            <h3 style={{ marginTop: 0, color: '#2c3e50' }}>{aiReport.report_title}</h3>
            <p style={{ whiteSpace: 'pre-line', color: '#34495e', lineHeight: '1.8' }}>
              {aiReport.ai_insight}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
  width: '100%',
  maxWidth: '100%',
  padding: '32px',
  fontFamily: 'system-ui, sans-serif',
  backgroundColor: '#f0f4f8',
  minHeight: '100vh'
},

  header:     { marginBottom: '28px' },
  title:      { fontSize: '24px', fontWeight: '700', color: '#2c3e50', margin: 0 },
  subtitle:   { color: '#7f8c8d', margin: '4px 0 0' },
  cardRow:    { display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' },
  card:       { flex: 1, minWidth: '160px', backgroundColor: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.07)', textAlign: 'center' },
  cardLabel:  { fontSize: '13px', color: '#7f8c8d', margin: '8px 0 4px' },
  cardValue:  { fontSize: '22px', fontWeight: '700', color: '#2c3e50', margin: 0 },
  twoCol: {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
  gap: '20px',
  marginBottom: '24px'
},

  panel: {
  flex: 1,
  backgroundColor: 'white',
  padding: '24px',
  borderRadius: '12px',
  boxShadow: '0 2px 8px rgba(0,0,0,0.07)'
  },
  panelTitle: { fontSize: '16px', fontWeight: '600', color: '#2c3e50', marginTop: 0 },
  hint:       { fontSize: '12px', color: '#aaa', marginTop: '8px' },
  riskList:   { display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '240px', overflowY: 'auto' },
  riskItem:   { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', backgroundColor: '#fff5f5', borderRadius: '8px', borderLeft: '4px solid #e74c3c' },
  dept:       { fontSize: '12px', color: '#999', marginLeft: '8px' },
  salary:     { fontWeight: '600', color: '#27ae60' },
  aiPanel:    { backgroundColor: 'white', padding: '30px', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' },
  aiHeader:   { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' },
  button:     { backgroundColor: '#9b59b6', color: 'white', border: 'none', padding: '12px 28px', borderRadius: '8px', fontSize: '15px', cursor: 'pointer', fontWeight: '600' },
  errorBox:   { marginTop: '16px', padding: '14px', backgroundColor: '#fdecea', borderRadius: '8px', color: '#c0392b', fontSize: '14px' },
  aiResult:   { marginTop: '20px', padding: '20px', backgroundColor: '#faf5ff', borderRadius: '8px', borderLeft: '5px solid #9b59b6' },
};

export default App;
