

---

# 🚀 Nexus HR — AI-Augmented HR Analytics Platform

🔗 Live Demo: [https://nexus-hr-ai.vercel.app/](https://nexus-hr-ai.vercel.app/)

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-61dafb)
![Status](https://img.shields.io/badge/Project-Active-success)

---

Nexus HR is an end-to-end HR analytics platform that processes employee data, computes risk scores, and generates AI-powered executive insights for decision-makers.

The project originated as part of a “Software Requirements and Analysis” course and was iteratively developed into a working system based on software engineering principles.

---

## 🎯 Objective

This system is designed to extend traditional HR data systems by:

* Making raw HR data analyzable
* Automating KPI generation
* Computing employee risk scores
* Producing AI-assisted executive summaries

---

## 🧠 System Architecture

```text id="9ad09v"
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
* File size limit (20MB)

---

### 2. ETL & Data Processing Layer

* Pandas-based data cleaning
* Missing value handling
* Feature engineering (log salary, normalization)
* Data type standardization

---

### 3. Analytics Engine

#### KPI Engine

* Aggregated metrics (mean, sum, count)
* Department-level segmentation
* Controlled metric exposure (whitelist-based system)

#### Risk Engine

* Rule-based scoring model
* Salary, performance, and engagement analysis
* Employee-level risk estimation logic

---

### 4. AI Layer (Groq LLM)

The LLM is used strictly for **high-level summarization**.

* No raw data is sent to the model
* Only aggregated and anonymized metrics are provided
* Generates executive-level summaries

This design improves data privacy and reduces model risk exposure.

---

### 5. Cache Layer (Redis - Optional)

* Used for performance optimization
* Reduces repeated computation overhead
* System is fully functional without Redis (fallback mode enabled)

---

### 6. API Layer (FastAPI)

* RESTful architecture
* Session-based processing
* Input validation with Pydantic
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
* File size enforcement (20MB limit)
* Session isolation (max 500 active sessions)
* Input validation at API level
* Rate limiting for abuse prevention
* Fail-safe architecture (AI/cache independence)

---

## 📄 Documentation

The project includes formal software engineering documentation:

* Software Requirements Specification (SRS)
* Vision & Scope Document
* Risk Analysis
* Requirements Traceability Matrix (RTM)

These documents ensure the system is designed in a requirement-driven and traceable manner.

---

## ⚙️ Deployment

* Frontend: Vercel
* Backend: Render
* Cold start latency: ~20–40 seconds (free tier limitation)

---

## 🧪 Testing & CI/CD

* Pytest unit and integration tests
* Mock API test suite
* GitHub Actions CI pipeline
* Data processing engine coverage tests

---

## 🧠 Design Principles

* Modular and layered architecture
* AI-assisted, not AI-dependent system design
* Fail-safe and resilient processing pipeline
* Testable and observable data flow
* Human-in-the-loop AI usage model

---

## 📌 Data Flow

CSV → API → ETL → KPI/Risk Engine → Aggregation → LLM → Dashboard

---

## 🚀 Project Summary

This project is a modular HR analytics system that integrates data processing, analytical computation, and AI-based summarization into a single pipeline.

It demonstrates an end-to-end system design approach rather than a standalone dashboard implementation.

---

## 📎 Note

This project was developed individually and iteratively, following software engineering practices throughout its evolution.

---


