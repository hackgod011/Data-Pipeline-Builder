# PipeForge — Intelligent NL-to-ETL Pipeline Builder

Type plain English → get a working data pipeline. PipeForge turns natural language descriptions into executable Python/Pandas ETL code, runs it safely in a sandbox, and streams live execution logs with a data quality report.

## Architecture

```
┌─────────────────────┐      ┌──────────────────────────────────┐
│   React Frontend    │      │        FastAPI Backend            │
│                     │      │                                   │
│  Dashboard          │ HTTP │  POST /api/v1/sources/upload      │
│  Pipeline Builder   │─────▶│  POST /api/v1/pipelines/generate  │
│  Execution Monitor  │      │  POST /api/v1/pipelines/{id}/execute│
│  Pipeline History   │◀─────│  WS   /ws/execution/{id}         │
│                     │  WS  │  GET  /api/v1/executions/{id}     │
└─────────────────────┘      └──────────────────────────────────┘
         │                                   │
         │                          ┌────────┴───────┐
         │                          │  LiteLLM       │
         │                          │  (Groq/Gemini) │
         │                          └────────────────┘
         │
    React Flow DAG
    Monaco Editor
    Recharts
```

**Flow:**
1. Upload CSV / Excel / JSON / Parquet on the Dashboard
2. Select sources → describe your pipeline in plain English
3. PipeForge calls the LLM (via LiteLLM — Groq, Gemini, or Anthropic) to produce a structured DAG plan + Pandas/SQL code
4. Click **Run** → sandbox executes the code → WebSocket streams live logs
5. DAG nodes light up per step; data quality report auto-appears on success

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| DAG Visualization | React Flow |
| Charts | Recharts |
| Code Editor | Monaco Editor |
| State | Zustand + TanStack Query |
| Backend | FastAPI, Python 3.11, SQLAlchemy async |
| LLM | LiteLLM (Groq / Gemini / Anthropic — provider-agnostic) |
| Data | Pandas 2, DuckDB (large files), PyArrow |
| Sandboxing | AST validator + subprocess with 60s timeout |
| Database | SQLite (dev) |
| CI/CD | GitHub Actions |
| Deployment | Docker + Docker Compose |

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- An LLM API key — **Groq is free and recommended**: get a key at [console.groq.com](https://console.groq.com).
  Alternatively use [Gemini](https://aistudio.google.com/apikey) or Anthropic Claude.

### 1. Environment

```bash
cp .env.example .env
# Edit .env — set your LLM provider key (e.g. GROQ_API_KEY=gsk_...)
# Generate SECRET_KEY and ENCRYPTION_KEY per the comments in .env.example
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Docker (Production)

```bash
# Copy and fill in your API key
cp .env.example .env

docker compose up --build
```

Frontend at [http://localhost:80](http://localhost:80), backend at [http://localhost:8000](http://localhost:8000).

To override the Gemini model or other settings, add them to `.env`:

```env
GEMINI_API_KEY=your-key-here
LLM_MODEL=gemini-2.0-flash-lite
CORS_ORIGINS=https://yourapp.com
```

## Running Tests

```bash
cd backend
pytest tests/ -v
```

62 tests covering all API endpoints, services (profiler, executor, NL parser, code generator, schema detector), and the AST sandbox.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI entry point
│   │   ├── core/
│   │   │   ├── config.py        Settings (reads .env)
│   │   │   ├── database.py      SQLite async engine
│   │   │   └── sandbox.py       AST-based code validator
│   │   ├── models/              SQLAlchemy ORM models
│   │   ├── schemas/             Pydantic request/response shapes
│   │   ├── services/
│   │   │   ├── nl_parser.py     LiteLLM → structured pipeline plan (provider-agnostic)
│   │   │   ├── code_generator.py  Plan → executable Pandas code
│   │   │   ├── executor.py      Sandboxed subprocess runner
│   │   │   ├── schema_detector.py  Pandas / DuckDB schema analysis
│   │   │   └── profiler.py      Post-execution data quality scoring
│   │   └── api/routes/          FastAPI route handlers
│   ├── tests/                   62 pytest tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               Dashboard, PipelineBuilder, ExecutionMonitor, PipelineHistory
│   │   ├── components/          DAGCanvas, PipelineNode, LogStream, QualityReport, …
│   │   ├── hooks/               useWebSocket (auto-reconnect, exponential backoff)
│   │   ├── api/client.ts        Axios + all TypeScript interfaces
│   │   └── stores/              Zustand pipeline store
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .github/workflows/ci.yml     lint + test + type-check + Docker build
└── .env.example
```

## CI/CD

GitHub Actions runs on every push to `main` / `dev` and on pull requests:

1. **Backend** — `ruff` lint + `pytest` (62 tests)
2. **Frontend** — `eslint` + TypeScript type-check + `vite build`
3. **Docker** — builds both images to catch Dockerfile regressions
