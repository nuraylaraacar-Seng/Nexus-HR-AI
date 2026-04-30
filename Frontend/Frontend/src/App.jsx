import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Activity, Users, DollarSign, BrainCircuit, AlertTriangle } from 'lucide-react';

const API_BASE = 'https://nexus-hr-ai-production.up.railway.app/api/v1';

function App() {
  const [aiReport, setAiReport] = useState(null);
  const [riskList, setRiskList] = useState([]);
  const [payGap, setPayGap] = useState([]);
  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchKPI();
    fetchFlightRisk();
    fetchPayGap();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/upload-dataset`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (data.status === "error") {
      alert(data.message);
      return;
    }

    setSummary(data.summary);

    // Yeni dataset yüklendi → dashboard'u güncelle
    fetchKPI();
    fetchFlightRisk();
    fetchPayGap();
  };

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
      setError("AI raporu alınamadı. Backend'in çalıştığından emin ol.");
    }
    setLoading(false);
  };

  return (
    <div style={styles.page}>

      {/* DOSYA YÜKLEME */}
      <div style={{ marginBottom: "20px" }}>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
        />
      </div>

      {/* HEADER */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>🎯 Nexus HR: Enterprise AI Dashboard</h1>
          <p style={styles.subtitle}>Kurumsal Veri Analiz ve Karar Destek Platformu</p>
          <div style={{
            width: '120px',
            height: '4px',
            margin: '12px auto 0',
            borderRadius: '4px',
            background: 'linear-gradient(90deg, #9b59b6, #3498db)'
          }} />
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
            {summary
              ? `%${((riskList.length / summary.total_employees) * 100).toFixed(0)}`
              : '...'}
          </p>
        </div>
      </div>

      {/* YÜKLENEN DATASET ÖZETİ */}
      {summary && (
        <div className="uploaded-summary">
          <h3>📁 Yüklenen Dataset Özeti</h3>
          <p>Toplam çalışan: {summary.total_employees}</p>
          <p>Ortalama maaş: {summary.average_salary}</p>
          <p>Yüksek riskli çalışan: {summary.flight_risk_count}</p>
          <p>Bağlılık skoru: {summary.average_engagement}</p>
        </div>
      )}

      {/* GRAFİKLER VE RİSK LİSTESİ */}
      <div style={styles.twoCol}>
        <div style={styles.panel}>
          <h2 style={styles.panelTitle}>📊 Departman Bazlı Maaş Uçurumu (%)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={payGap}>
              <XAxis dataKey="department" />
              <YAxis />
              <Tooltip formatter={(v) => `%${v}`} />
              <Bar dataKey="gap">
                {payGap.map((entry, i) => (
                  <Cell key={i} fill={entry.gap > 0 ? '#e74c3c' : '#2ecc71'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={styles.panel}>
          <h2 style={styles.panelTitle}>⚠️ İstifa Riski Yüksek Çalışanlar</h2>
          <div style={styles.riskList}>
            {riskList.length === 0 && <p style={{ color: '#999' }}>Yükleniyor...</p>}
            {riskList.map((emp, i) => (
              <div key={i} style={styles.riskItem}>
                <div>
                  <strong>{emp.Employee_Name}</strong>
                  <span style={styles.dept}>{emp.Department}</span>
                </div>
                <span style={styles.salary}>${emp.Salary?.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI PANEL */}
      <div style={styles.aiPanel}>
        <div style={styles.aiHeader}>
          <BrainCircuit size={32} color="#9b59b6" />
          <h2>Yapay Zeka Strateji Merkezi</h2>
        </div>

        <button onClick={fetchAIReport} style={styles.button} disabled={loading}>
          {loading ? '⏳ AI Analiz Ediyor...' : '🚀 AI Stratejik Özetini Üret'}
        </button>

        {error && <div style={styles.errorBox}>{error}</div>}

        {aiReport && (
          <div style={styles.aiResult}>
            <h3>{aiReport.report_title}</h3>
            <p style={{ whiteSpace: 'pre-line' }}>{aiReport.ai_insight}</p>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
    width: '100%',
    padding: '0',
    backgroundColor: '#f0f4f8',
    minHeight: '100vh',
  },
  header: { textAlign: 'center', marginBottom: '40px' },
  title: { fontSize: '32px', fontWeight: '900', color: '#2c3e50' },
  subtitle: { color: '#7f8c8d' },
  cardRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '16px',
    marginBottom: '24px'
  },
  card: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.07)'
  },
  cardLabel: { fontSize: '13px', color: '#7f8c8d' },
  cardValue: { fontSize: '22px', fontWeight: '700' },
  twoCol: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px'
  },
  panel: {
    backgroundColor: 'white',
    padding: '24px',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.07)'
  },
  panelTitle: { fontSize: '16px', fontWeight: '600' },
  riskList: { display: 'flex', flexDirection: 'column', gap: '10px' },
  riskItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px',
    backgroundColor: '#fff5f5',
    borderLeft: '4px solid #e74c3c'
  },
  dept: { fontSize: '12px', color: '#999', marginLeft: '8px' },
  salary: { fontWeight: '600', color: '#27ae60' },
  aiPanel: {
    backgroundColor: 'white',
    padding: '30px',
    borderRadius: '12px',
    marginTop: '30px'
  },
  aiHeader: { display: 'flex', alignItems: 'center', gap: '12px' },
  button: {
    backgroundColor: '#9b59b6',
    color: 'white',
    padding: '12px 28px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600'
  },
  errorBox: {
    marginTop: '16px',
    padding: '14px',
    backgroundColor: '#fdecea',
    borderRadius: '8px',
    color: '#c0392b'
  },
  aiResult: {
    marginTop: '20px',
    padding: '20px',
    backgroundColor: '#faf5ff',
    borderLeft: '5px solid #9b59b6'
  }
};

export default App;
