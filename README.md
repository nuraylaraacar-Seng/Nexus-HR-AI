# 🚀 Nexus HR — AI-Augmented HR Analytics Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-61dafb)
![Render](https://img.shields.io/badge/Backend-Render-46E3B7)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-black)
![Status](https://img.shields.io/badge/Project-Active-success)

## 📺 Video Demo
[![Nexus HR Demo](https://img.shields.io/badge/Watch-Demo%20Video-red?style=for-the-badge&logo=youtube)]
 
🔗 Live Demo: [https://nexus-hr-ai.vercel.app/](https://nexus-hr-ai.vercel.app/)

🔗 Backend API: Render (deployed)

Nexus HR is an end-to-end HR analytics platform that processes employee data, computes risk scores, and generates AI-powered executive insights for decision-making. The system is designed to automate KPI generation and handle unstructured CSV data pipelines efficiently.

---

## 🎯 Objective

The goal of this system is to extend traditional HR data workflows by:

* Making raw HR data usable for analysis
* Automating KPI generation
* Computing employee risk scores
* Generating AI-assisted executive summaries

---

## 🧠 System Architecture

```text
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

## 🏗️ System Components

### 1. Data Ingestion Layer

* CSV upload interface
* Encoding-safe parsing
* 20MB file size limit

---

### 2. ETL & Data Processing Layer

* Pandas-based cleaning pipeline
* Missing value handling
* Feature engineering (log salary, normalization)
* Data type standardization

---

### 3. Analytics Engine

#### KPI Engine

* Aggregated metrics (mean, sum, count)
* Department-level segmentation
* Controlled metric exposure via whitelist

#### Risk Engine

* Rule-based scoring model
* Salary, performance, engagement signals
* Employee-level risk estimation

---

### 4. AI Layer (Groq LLM)

The LLM is used only for high-level summarization.

* No raw employee data is sent
* Only aggregated and anonymized metrics are passed
* Produces executive-level summaries

This keeps the AI layer safe and predictable while reducing data exposure.

---

### 5. Cache Layer (Redis - Optional)

* Used for performance optimization
* Reduces repeated computation overhead
* System works normally without Redis (fallback mode)

---

### 6. API Layer (FastAPI)

* REST API design
* Session-based processing
* Pydantic validation
* Rate limiting (SlowAPI)

---

### 7. Frontend Layer (React)

* Interactive HR dashboard
* KPI visualizations (Recharts)
* AI insight panel
* Session-based state handling

---

## 🔐 Security & Reliability

* Path traversal protection
* 20MB upload limit
* Session isolation (max 500 sessions)
* Input validation at API level
* Rate limiting for abuse prevention
* Fail-safe architecture (AI/cache independence)

---

## 📄 Documentation

The project is accompanied by a set of software engineering documents created during the analysis and design process, including:

* Vision & Scope
* Stakeholder Analysis
* Software Requirements Specification (SRS)
* Analysis Models
* Requirements Classification
* Requirements Traceability Matrix (RTM)
* Risk Analysis
* Prototype Evolution Report
* Requirements Validation & Change Management

These documents describe the project's requirements, design decisions, and development process, complementing the implementation available in this repository.

See the `/docs` directory for the complete documentation.

---

## ⚙️ Deployment

* Frontend: Vercel
* Backend: Render
* Cold start: ~20–40 seconds (free tier limitation)

---

## 🧪 Testing & CI/CD

* Pytest unit and integration tests
* Mock API tests
* GitHub Actions CI pipeline
* Data pipeline test coverage

---

## 🧠 Design Principles

* Modular, layered architecture
* AI-assisted, not AI-dependent system design
* Fail-safe execution model
* Testable and observable data flow
* Human-in-the-loop AI usage where needed

---

## 📌 Data Flow

CSV → API → ETL → KPI/Risk Engine → Aggregation → LLM → Dashboard

---

## 🚀 Project Summary

This project combines data processing, analytics, and AI-based summarization into a single modular HR system.

It is designed as a working engineering prototype rather than a static dashboard.

---

## 📎 Note

Built individually and improved iteratively over time using software engineering practices.

---




