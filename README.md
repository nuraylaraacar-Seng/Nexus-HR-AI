
---

# 🚀 Nexus HR — AI-Augmented HR Analytics Platform

🔗 Live Demo: [https://nexus-hr-ai.vercel.app/](https://nexus-hr-ai.vercel.app/)

Nexus HR, HR verilerini analiz eden, risk skorlayan ve yapay zekâ destekli yönetici içgörüleri üreten uçtan uca bir HR analytics sistemidir.

Proje, “Yazılım Gereksinimleri ve Analizi” dersi kapsamında başlayan bir fikrin, yazılım mühendisliği prensipleriyle çalışan bir sistem prototipine dönüştürülmüş halidir.

---

## 🎯 Amaç

Bu sistem, geleneksel HR veri yapılarının ötesine geçerek:

* Veriyi analiz edilebilir hale getirmek
* KPI üretimini otomatikleştirmek
* Çalışan risk skorlaması yapmak
* Yönetici seviyesinde AI destekli özetler üretmek

amacıyla tasarlanmıştır.

---

## 🧠 Sistem Mimarisi

```
CSV Upload
     │
     ▼
FastAPI API Layer
     │
     ▼
Pandas ETL Engine
     │
     ▼
KPI & Risk Scoring Engine
     │
 ┌───┴───────────┐
 ▼               ▼
Groq LLM     REST API Layer
 │               │
 └──────┬────────┘
        ▼
   React Dashboard
```

---

## 🏗️ Sistem Bileşenleri

### 1. Data Ingestion Layer

* CSV dosya yükleme
* Encoding-safe parsing
* Dosya boyutu kontrolü (20MB)

### 2. ETL & Data Processing Layer

* Pandas tabanlı veri temizleme
* Eksik veri yönetimi
* Feature engineering (log salary, normalization)
* Veri tip standardizasyonu

### 3. Analytics Engine

**KPI Engine**

* Temel metrik hesaplama (mean, sum, count)
* Departman bazlı kırılım
* Kontrollü metrik sistemi (whitelist)

**Risk Engine**

* Rule-based risk skorlama modeli
* Salary, performance ve engagement temelli analiz

---

### 4. AI Layer (Groq LLM)

LLM sadece **özetlenmiş ve anonimleştirilmiş veriler** ile çalışır:

* Ham veri gönderilmez
* Sadece aggregate metrikler iletilir
* Executive summary üretimi yapılır

Bu yaklaşım veri gizliliğini artırır ve model riskini azaltır.

---

### 5. Cache Layer (Redis - Optional)

* Performans optimizasyonu için Redis cache
* Kullanılmadığında sistem fallback modda çalışır
* Sistem Redis bağımlı değildir

---

### 6. API Layer (FastAPI)

* REST API mimarisi
* Session-based yapı
* Rate limiting (SlowAPI)
* Pydantic validation

---

### 7. Frontend Layer (React)

* KPI dashboard
* Veri görselleştirme (Recharts)
* AI insight paneli
* Session bazlı veri akışı

---

## 🔐 Güvenlik & Dayanıklılık

* Path traversal protection
* 20MB dosya limiti
* Session isolation (max 500 aktif session)
* Fail-safe mimari (AI / cache bağımsız)
* Input validation
* Rate limiting

---

## 📄 Dokümantasyon

Proje kapsamında şu dokümanlar hazırlanmıştır:

* Software Requirements Specification (SRS)
* Vision & Scope Document
* Risk Analysis
* Requirements Traceability Matrix (RTM)

Bu dokümanlar, sistemin gereksinim odaklı tasarlandığını ve kontrollü şekilde geliştirildiğini gösterir.

---

## ⚙️ Deployment

* Frontend: Vercel
* Backend: Render
* Cold start: ~20–40 saniye (free tier)

---

## 🧪 Test & CI/CD

* Pytest unit & integration testleri
* Mock API test yapısı
* GitHub Actions CI pipeline
* Data engine test coverage

---

## 🧠 Tasarım Prensipleri

* Modüler ve katmanlı mimari
* AI destekli ama AI bağımlı olmayan yapı
* Fail-safe sistem tasarımı
* Test edilebilir veri akışı
* Human-in-the-loop yaklaşımı

---

## 📌 Veri Akışı

CSV → FastAPI → ETL → KPI/Risk Engine → Aggregation → LLM → Dashboard

---

## 🚀 Proje Notu

Bu sistem, veri işleme, analitik hesaplama ve yapay zekâ destekli yorumlama katmanlarını birleştiren modüler bir HR analytics prototipidir.

---

## 📎 Not

Proje bireysel olarak geliştirilmiş ve iteratif şekilde olgunlaştırılmıştır.

---


İstersen bir sonraki adımda bunu **GitHub repo görünümüne (badge’ler + screenshot + architecture PNG)** çevirip “gerçek product repo” seviyesine de yükseltebiliriz.
