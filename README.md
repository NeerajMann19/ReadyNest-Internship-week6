# Analytics Studio

Analytics Studio is a Decision Intelligence Platform designed to transform raw business data into actionable business decisions through structured insights, executive reporting, contextual explanations, and decision simulation.

> **Note on Session Persistence**: All user session state is stored strictly in-memory and will reset upon backend application restart or Render free-tier cold start. This is an accepted and intentional design limitation for this project's scope.

## Project Structure

```
Analytics-Studio/
├── docs/                      # Product, Technical & Design Specifications
├── backend/                   # FastAPI Backend Monolith
│   ├── main.py                # ASGI Application Entrypoint
│   ├── models.py              # Canonical Pydantic v2 Domain Models
│   ├── storage.py             # In-Memory Session Store
│   ├── config.py              # Application & Environment Settings
│   ├── requirements.txt       # Backend Dependencies
│   ├── .env.example           # Deployment Environment Template
│   ├── .gitignore             # Backend Git Ignore Patterns
│   ├── modules/               # Core Business Modules (Stubs in Phase 1A)
│   │   ├── dataset.py
│   │   ├── analytics.py
│   │   ├── prediction.py
│   │   ├── insight.py
│   │   ├── decision.py
│   │   ├── report.py
│   │   └── advisor.py
│   └── api/                   # API Routers
│       └── routes.py          # GET /health Endpoint
└── frontend/                  # React Desktop Web Application (Phase 9)
```

## Running the Backend Locally

1. Create and activate a Python 3.12 virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run the backend dev server:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Verify health check:
   ```bash
   curl http://localhost:8000/health
   ```
