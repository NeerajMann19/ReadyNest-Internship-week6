# Analytics Studio

**Analytics Studio** is a Decision Intelligence Platform that turns raw business data into structured insights, recommendations, and executive reports.

---

## 🚀 Live Deployments

- 🌐 **Live Web Application**: [https://analytics-studio-mu.vercel.app](https://analytics-studio-mu.vercel.app)
- ⚙️ **Backend REST API**: [https://analytics-studio-backend.onrender.com](https://analytics-studio-backend.onrender.com)

> 💡 **Notice on Backend Performance**: The backend is hosted on Render's Free Tier. The first request after a period of inactivity may take 30–60 seconds while the server cold-starts.

---

## ⚡ What It Does

- 📊 **Automated CSV Cleaning & Quality Scoring**: Upload raw CSV files for instant validation, duplicate/missing value handling, and quality scoring (0–100%).
- 📈 **Quantitative Analytics & Correlation**: Computes descriptive statistics, frequency distributions, IQR outlier detection, and pairwise correlation matrices.
- 🔮 **Machine Learning Predictive Modeling**: Automated Scikit-learn regression and classification modeling with standard evaluation metrics.
- 💡 **AI Business Insight Engine**: Generates 4–6 grounded, empirical business insights categorized by severity and impact using Google Gemini 2.0 Flash with deterministic fallback.
- 🎯 **Decision Simulator & Counter-Analysis**: Simulates percentage price adjustments, projecting revenue/volume impact while conducting AI counter-analysis for risks and mitigations.
- 📄 **Executive PDF Report Export**: Assembles all domain analytics into a styled, presentation-ready executive PDF report rendered cleanly via Jinja2 & WeasyPrint.
- 🧠 **Contextual Executive Advisor**: One-click contextual explanation engine providing 2–3 sentence plain-language executive briefs on specific business findings.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python FastAPI
- **Data & Scientific Stack**: Pandas, NumPy, Scikit-Learn
- **Validation**: Pydantic v2 (Canonical domain models as single source of truth)
- **PDF Engine**: Jinja2 + WeasyPrint (HTML/CSS to PDF compilation)
- **AI & LLM Layer**: Google Gemini API (`gemini-2.0-flash` with locked deterministic parameters: `temperature=0.2`, `top_p=0.9`, `top_k=40`)
- **Deployment**: Docker container on Render (`python:3.11-slim-bookworm`)

### Frontend
- **Framework**: React 19 + Vite + TypeScript
- **Styling**: Tailwind CSS + custom dark-mode design system
- **Icons & Visuals**: Lucide React, Recharts
- **Deployment**: Vercel

---

## 📐 Architecture Overview

Analytics Studio operates on a strictly modular pipeline. Every phase processes and mutates a set of **canonical Pydantic domain objects** (`Dataset`, `Analytics`, `Prediction`, `Insight`, `Decision`, `Report`, `AdvisorResponse`) stored in the in-memory session layer:

```
[ Raw CSV Upload ]
       │
       ▼
[ Dataset Module ] ──► Computes Column Schema & QualityReport (Score 0-100%)
       │
       ▼
[ Analytics Engine ] ──► Calculates Numeric Summaries, Correlations & Outliers
       │
       ▼
[ Prediction Engine ] ──► Fits Scikit-learn Model & Evaluates Metrics
       │
       ▼
[ Insight Engine ] ──► Generates 4-6 Grounded Business Insights via Gemini 2.0
       │
       ▼
[ Decision Simulator ] ──► Simulates Price Changes & Counter-Analysis
       │
       ▼
[ Executive Report ] ──► Renders Styled Executive PDF (Jinja2 + WeasyPrint)
       │
       ▼
[ Executive Advisor ] ──► Contextual 2-3 Sentence Plain-Language Explanations
```

---

## 💻 Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Backend Setup

```bash
# Navigate to project root
cd Analytics-Studio

# Create and activate Python virtual environment
python -m venv backend/venv

# Windows PowerShell:
.\backend\venv\Scripts\Activate.ps1
# macOS/Linux:
source backend/venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure Environment Variables (Create backend/.env)
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```env
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Start backend development server:
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health check:
```bash
curl http://localhost:8000/health
# Response: {"status":"ok"}
```

### 2. Frontend Setup

In a new terminal window:
```bash
cd Analytics-Studio/frontend

# Install dependencies
npm install

# Configure Environment Variables (Create frontend/.env)
cp .env.example .env
```

Edit `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

Start frontend development server:
```bash
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 🔑 Environment Variables

| Variable | Scope | Location | Required | Example / Default Value | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `GEMINI_API_KEY` | Backend | `.env` / Render Dashboard | **Yes** | `AIzaSy...` | Google Gemini API key for Insights, Decisions & Advisor |
| `CORS_ORIGINS` | Backend | `.env` / Render Dashboard | **Yes** | `http://localhost:5173,https://analytics-studio-mu.vercel.app` | Allowed CORS origins for API requests |
| `PORT` | Backend | `.env` / Render Dashboard | No | `8000` | Port for ASGI web server (injected by Render) |
| `VITE_API_BASE_URL` | Frontend | `.env` / Vercel Dashboard | **Yes** | `https://analytics-studio-backend.onrender.com` | Base REST API URL for Axios client |

---

## 🚧 Known Limitations

- **In-Memory Session Storage**: All session state (`_SESSIONS`, `_REPORT_CACHE`, `_DECISION_CACHE`) is stored in-memory. Sessions do not persist across backend server restarts or Render free-tier cold starts. This is an intentional MVP scope design decision.
- **Single Scenario Type in Decision Simulator**: The simulator currently models percentage price adjustments (`scenario_input`). Expanding to multi-variable scenario modeling is planned for future releases.
- **Single-User Session Scope**: No multi-user authentication or RBAC is implemented in this version, keeping the architecture focused on core decision intelligence capabilities.

---

## 🎓 Project Context

Analytics Studio was developed as the **Week 6 Capstone Project for the ReadyNest Internship**. It synthesizes prior internship modules (EDA, customer analytics, geographic data analysis, predictive modeling, and ETL pipelines) into a unified, executive-grade decision intelligence platform.

---

## 🗺️ Future Roadmap

- 🔁 **Multi-Scenario Decision Builder**: Expand simulator to support cost restructuring, marketing budget re-allocation, and churn mitigation modeling.
- 💾 **Persistent Storage Layer**: Integrate PostgreSQL (via SQLAlchemy async + Supabase) and Redis for session memory persistence across restarts.
- 🔐 **Multi-Tenant Authentication**: Add JWT-based user authentication, role-based access control, and workspace sharing.
- 📅 **Time-Series Forecasting**: Incorporate Prophet / ARIMA modules for seasonal trend projections.
- 📊 **Additional Export Formats**: Support CSV, Excel, and PowerPoint presentation deck exports.
