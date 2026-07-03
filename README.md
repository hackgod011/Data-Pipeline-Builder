<h1 align="center">⚡ PipeForge — Intelligent NL-to-ETL Pipeline Builder</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react">
  <img src="https://img.shields.io/badge/LiteLLM-Groq%20%7C%20Gemini%20%7C%20Anthropic-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker">
  <img src="https://img.shields.io/badge/CI-GitHub%20Actions-success?style=for-the-badge&logo=githubactions">
</p>

<p align="center">
  🚀 <b>Type plain English → get a working data pipeline.</b><br>
  PipeForge turns natural language descriptions into executable Python/Pandas ETL code,<br>
  runs it safely in a sandbox, and streams live execution logs with a data quality report.
</p>

---

## 📋 Table of Contents

- 🔥 [Problem Statement](#-problem-statement)
- ✨ [Features](#-features)
- 🧠 [System Architecture](#-system-architecture)
- 🛠 [Tech Stack](#-tech-stack)
- ⚡ [Local Setup](#-local-setup)
- 🐳 [Docker (Production)](#-docker-production)
- 🧪 [Running Tests](#-running-tests)
- 📁 [Project Structure](#-project-structure)
- 🔄 [CI/CD](#-cicd)
- 🌍 [Free Deployment](DEPLOYMENT.md)

---

<h2 align="center">🔥 Problem Statement</h2>

<p align="center">
Data engineers spend hours writing boilerplate ETL scripts for every new pipeline.<br>
Non-technical analysts can't build pipelines at all — they depend entirely on engineering backlogs.<br>
And even when pipelines are built, there's no easy way to monitor their quality in real time.
</p>

**PipeForge solves this by:**

✅ _Translating_ plain English descriptions into executable, production-ready Pandas code  
✅ _Executing_ pipelines safely inside an AST-validated sandbox — no arbitrary code risk  
✅ _Streaming_ live execution logs over WebSocket so you watch every step in real time  
✅ _Visualizing_ your pipeline as an animated DAG where nodes light up as steps complete  
✅ _Reporting_ data quality automatically — null rates, type coverage, row counts, and more  

---

## ✨ Features

- 🗣 **Natural Language to ETL** — Describe your pipeline in plain English; get clean Pandas code instantly
- 🔀 **Live DAG Visualization** — React Flow canvas shows your pipeline graph; nodes animate during execution
- 📡 **Real-Time Log Streaming** — WebSocket pushes execution logs live as each step runs
- 🛡 **AST Sandbox** — Code is validated at the AST level before execution; 60-second subprocess timeout
- 📊 **Automatic Data Quality Report** — Post-execution report with null rates, schema coverage, row counts
- 🤖 **Provider-Agnostic LLM** — Works with Groq (free), Gemini, or Anthropic via LiteLLM — swap with one env var
- 📂 **Multi-Format Ingestion** — Upload CSV, Excel, JSON, or Parquet
- 🕒 **Pipeline History** — Full execution history with re-run and code inspection
- 🐳 **Docker-Ready** — Single `docker compose up` for a full production stack

---

## 🧠 System Architecture

```
┌─────────────────────┐      ┌──────────────────────────────────────┐
│   React Frontend    │      │          FastAPI Backend              │
│                     │      │                                       │
│  Dashboard          │ HTTP │  POST /api/v1/sources/upload          │
│  Pipeline Builder   │─────▶│  POST /api/v1/pipelines/generate      │
│  Execution Monitor  │      │  POST /api/v1/pipelines/{id}/execute  │
│  Pipeline History   │◀─────│  WS   /ws/execution/{id}             │
│                     │  WS  │  GET  /api/v1/executions/{id}         │
└─────────────────────┘      └──────────────────────────────────────┘
         │                                      │
         │                           ┌──────────┴──────────┐
         │                           │      LiteLLM         │
         │                           │  Groq / Gemini /     │
         │                           │  Anthropic           │
         │                           └─────────────────────┘
    React Flow DAG
    Monaco Editor
    Recharts
```

**Execution Flow:**

```
1. Upload CSV / Excel / JSON / Parquet
        ↓
2. Select sources → describe your pipeline in plain English
        ↓
3. LLM (via LiteLLM) produces a structured DAG plan + Pandas/SQL code
        ↓
4. Click Run → AST validator checks the code → subprocess executes in sandbox
        ↓
5. WebSocket streams live logs → DAG nodes light up step-by-step
        ↓
6. Data quality report auto-appears on success
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| DAG Visualization | React Flow |
| Charts | Recharts |
| Code Editor | Monaco Editor |
| State Management | Zustand + TanStack Query |
| Backend | FastAPI, Python 3.11, SQLAlchemy async |
| LLM | LiteLLM — Groq / Gemini / Anthropic (provider-agnostic) |
| Data Processing | Pandas 2, DuckDB (large files), PyArrow |
| Sandboxing | AST validator + subprocess with 60s timeout |
| Database | SQLite (dev) |
| CI/CD | GitHub Actions |
| Deployment | Docker + Docker Compose |

---

## ⚡ Local Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- An LLM API key — **Groq is free and recommended**: get a key at [console.groq.com](https://console.groq.com).  
  Alternatively use [Gemini](https://aistudio.google.com/apikey) or Anthropic Claude.

### 1️⃣ Environment

```bash
cp .env.example .env
# Edit .env — set your LLM provider key (e.g. GROQ_API_KEY=gsk_...)
# Generate SECRET_KEY and ENCRYPTION_KEY per the comments in .env.example
```

### 2️⃣ Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3️⃣ Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🐳 Docker (Production)

```bash
# Copy and fill in your API key
cp .env.example .env

docker compose up --build
```

Frontend → [http://localhost:80](http://localhost:80) | Backend → [http://localhost:8000](http://localhost:8000)

To override the model or CORS settings, add them to `.env`:

```env
GEMINI_API_KEY=your-key-here
LLM_MODEL=gemini-2.0-flash-lite
CORS_ORIGINS=https://yourapp.com
```

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

**62 tests** covering all API endpoints, services (profiler, executor, NL parser, code generator, schema detector), and the AST sandbox.

---

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                  FastAPI entry point
│   │   ├── core/
│   │   │   ├── config.py            Settings (reads .env)
│   │   │   ├── database.py          SQLite async engine
│   │   │   └── sandbox.py           AST-based code validator
│   │   ├── models/                  SQLAlchemy ORM models
│   │   ├── schemas/                 Pydantic request/response shapes
│   │   ├── services/
│   │   │   ├── nl_parser.py         LiteLLM → structured pipeline plan
│   │   │   ├── code_generator.py    Plan → executable Pandas code
│   │   │   ├── executor.py          Sandboxed subprocess runner
│   │   │   ├── schema_detector.py   Pandas / DuckDB schema analysis
│   │   │   └── profiler.py          Post-execution data quality scoring
│   │   └── api/routes/              FastAPI route handlers
│   ├── tests/                       62 pytest tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                   Dashboard, PipelineBuilder, ExecutionMonitor, PipelineHistory
│   │   ├── components/              DAGCanvas, PipelineNode, LogStream, QualityReport, …
│   │   ├── hooks/                   useWebSocket (auto-reconnect, exponential backoff)
│   │   ├── api/client.ts            Axios + all TypeScript interfaces
│   │   └── stores/                  Zustand pipeline store
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .github/workflows/ci.yml         lint + test + type-check + Docker build
└── .env.example
```

---

## 🔄 CI/CD

GitHub Actions runs on every push to `main` / `dev` and on all pull requests:

| Step | Check |
|---|---|
| Backend | `ruff` lint + `pytest` (62 tests) |
| Frontend | `eslint` + TypeScript type-check + `vite build` |
| Docker | Builds both images to catch Dockerfile regressions |

---

## 🤝 Contributing

Contributions are welcome! Fork the repo, make your changes, and open a pull request.  
For major changes, open an issue first to discuss what you'd like to change.

---

## 📚 References

- [LiteLLM](https://github.com/BerriAI/litellm) — Provider-agnostic LLM gateway
- [Groq Console](https://console.groq.com) — Free LLM API (recommended)
- [React Flow](https://reactflow.dev) — DAG visualization
- [FastAPI](https://fastapi.tiangolo.com) — Async Python backend
- [Pandas Documentation](https://pandas.pydata.org/docs/)
