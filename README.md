# end-to-end-project

# 🎯 Nexus HR: AI-Augmented HR Analytics MVP

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![React](https://img.shields.io/badge/React-18.0-61DAFB.svg)
![AI](https://img.shields.io/badge/AI-Groq%20Llama%203.3-FF9900.svg)
![Deployed](https://img.shields.io/badge/Deployed-Vercel%20%7C%20Railway-success.svg)



🔗 **Live Demo:** [Nexus HR Dashboard'u İncele] https://nexus-hr-ai.vercel.app
                                                       Not: Backend ücretsiz Railway sunucusunda çalıştığı için ilk isteklerde uyanması 30-40 saniye sürebilir.

## 📌 Project Context & Overview
...

## 📌 Project Context & Overview
Nexus HR is an end-to-end Minimum Viable Product (MVP) designed to bridge the gap between raw HR datasets and actionable decision-making. 

**The Origin Story:** This project was initially conceptualized for a Software Requirements Analysis course where 90% of the evaluation was based purely on documentation. However, to demonstrate true full-stack capability, I took the initiative to build and deploy the complete system solo. It combines **Data Engineering, Rule-Based Risk Scoring,** and **Generative AI** into a live, functional dashboard.

### 🛠️ Strategic Engineering Choice: Prototyping & Data Focus
During this development phase, a **CSV-based Data Engine** was intentionally chosen over a traditional SQL/PostgreSQL database. 
* **Rapid Prototyping:** To iterate quickly on the core **Data Analysis Problem** and AI logic without database overhead.
* **Analytical Focus:** The project prioritizes complex data transformations (ETL, log normalization) and predictive modeling over standard CRUD operations.
* **Future Roadmap:** Migrating to a persistent PostgreSQL layer is planned for the next iteration to support multi-user concurrency.

## 🚀 Core Features

* **🧠 AI-Driven Insights:** Integrates with `Llama-3.3-70b-versatile` (via Groq API) to analyze current data states and produce actionable executive summaries.
* **⚠️ Rule-Based Flight Risk (Churn) Scoring:** A deterministic algorithm identifying high-risk employees using engagement scores, tenure, and project involvement metrics.
* **📊 Dynamic KPI Engine:** Calculates real-time metrics across departments with strict whitelist validation to ensure data integrity.
* **🛡️ API Security & Validation:** Implements `SlowAPI` for DDoS protection/rate limiting and `Pydantic` for robust payload validation.

## 📂 Engineering Documentation
A functional prototype is only as good as its architecture. Moving beyond just code, this MVP is backed by **9 comprehensive Software Engineering reports** created during the design phase:
1. **Vision & Scope**
2. **Stakeholder Analysis**
3. **SRS (Software Requirements Specification)**
4. **Requirements Classification**
5. **Analysis Models**
6. **RTM (Requirements Traceability Matrix)**
7. **Risk Analysis**
8. **Prototype Evolution Report**
9. **Validation & Change Management**

## 🛠️ Technology Stack & Architecture

### Backend (Data Engine & AI)
* **Framework:** FastAPI (Python)
* **Data Processing:** Pandas, NumPy (Includes ETL pipelines and `log1p` salary normalization)
* **AI Integration:** Groq API (Prompt Engineering with a C-level executive persona)
* **Testing:** Pytest (Unit & Integration tests)

### Frontend (Client)
* **Library:** React.js (Vite)
* **Visuals:** Recharts & Lucide React Icons

## ⚙️ Local Installation
```bash
# Clone the repository
git clone [https://github.com/nuraylaraacar-Seng/Nexus-HR-AI.git](https://github.com/nuraylaraacar-Seng/Nexus-HR-AI.git)

# Setup Backend
cd Backend
pip install -r requirements.txt
uvicorn main:app --reload

# Setup Frontend
cd ../frontend
npm install
npm run dev
