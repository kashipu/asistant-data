# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Always activate the Python virtual environment before running backend commands:

```bash
# Windows (bash/Git Bash)
source .venv/Scripts/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

## Commands

### Backend
```bash
# Run development server (from repo root, venv active)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Interactive API docs
http://localhost:8000/docs

# Install dependencies
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # http://localhost:5173
npm run build
npm run lint
```

## Architecture

**Asistente Tablero** is a banking chatbot analytics dashboard. CSV conversation data flows through a 7-step ETL pipeline into SQLite, served via FastAPI, visualized in React.

```
data/data-asistente.csv  (118 MB)
    ↓ ingest.py (7-step ETL)
data/chat_data.db        (154 MB SQLite)
    ↓ engine.py (DataEngine singleton, in-memory cache)
backend/main.py          (20+ FastAPI endpoints at /api/*)
    ↓ HTTP (Axios)
frontend/src/services/api.ts
    ↓
frontend/src/App.tsx + components/
```

### ETL Pipeline (`backend/ingest.py`)
7 steps run sequentially:
1. Load & clean CSV, normalize dates
2. Deduplication by ID and content
3. Product homologation: CSV value → canonical name from `productos.yml`
4. Category matching: CSV intention → category from `categorias.yml`
5. Keyword NLP fallback for uncategorized messages (substring + regex against `palabras_clave`)
6. Sentiment propagation: propagate AI sentiment to human messages within a thread (by mode)
7. Servilínea detection: flag support referrals by keyword

### DataEngine (`backend/engine.py`)
Singleton that loads SQLite into Pandas DataFrames on startup. Pre-computes thread metadata, failures, and referrals caches. Reload is triggered after ETL via `engine.reload()`.

### YAML Configuration
- **`categorias.yml`**: 80+ categories with `nombre`, `macro`, `palabras_clave` (supports regex with `^...$`). This is the source of truth for category taxonomy. HITL feedback appends new `palabras_clave` entries here automatically.
- **`productos.yml`**: 20+ banking products with canonical names, macros, and aliases.

Changes to either YAML take effect on next ETL run (`POST /api/etl/run`).

### HITL Learning Loop
Uncategorized messages → `ReviewPanel` → `POST /api/feedbacks/categorize` → updates DB + appends to `categorias.yml` → next ETL improves auto-categorization.

### ETL Background Task
`POST /api/etl/run` launches ETL as a FastAPI `BackgroundTask`. Frontend polls `GET /api/etl/status` every 3 seconds and auto-reloads on completion.

### Database Schema (`messages` table)
Key columns: `id`, `thread_id`, `text`, `fecha` (YYYY-MM-DD), `hora` (0-23), `type` (human/ai/tool), `sentiment`, `categoria_yaml`, `macro_yaml`, `product_yaml`, `product_macro_yaml`, `is_servilinea`, `requires_review`, `input_tokens`, `output_tokens`.

### CORS
Backend allows: `localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, `127.0.0.1:3000`.

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | All FastAPI endpoints (20+) |
| `backend/engine.py` | DataEngine singleton |
| `backend/ingest.py` | ETL pipeline (~700 lines) |
| `backend/loader.py` | SQLite loading, auto-ingest if DB missing |
| `categorias.yml` | Category taxonomy (source of truth) |
| `productos.yml` | Product catalog |
| `frontend/src/App.tsx` | Tab routing, ETL control, data period |
| `frontend/src/services/api.ts` | All API calls centralized here |
