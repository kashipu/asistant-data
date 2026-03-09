# Setup — Asistente Tablero

Dashboard de analytics para chatbot bancario. Backend en FastAPI + Pandas, frontend en React + Vite + Tailwind.

## Requisitos

| Herramienta | Version | Notas |
|---|---|---|
| Python | 3.13 (o >=3.9) | Backend FastAPI + Pandas |
| Node.js | 18+ | Frontend React/Vite |
| npm | viene con Node | Dependencias frontend |
| Git | cualquiera | Clonar repo |
| ~2GB RAM libre | | pysentimiento carga modelos en memoria |

## Instalacion en macOS

### 1. Herramientas base

```bash
# Homebrew (si no lo tienes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.13 + Node.js
brew install python@3.13 node git
```

### 2. Clonar y configurar backend

```bash
git clone https://github.com/kashipu/asistant-data.git asistente-tablero
cd asistente-tablero

# Crear virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt
```

> **Nota Apple Silicon (M1/M2/M3/M4):** `pysentimiento` depende de PyTorch. Si falla la instalacion:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements.txt
> ```

### 3. Configurar frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Datos

Los archivos de datos estan en `.gitignore` y no vienen con el repo. Necesitas el CSV fuente:

```bash
mkdir -p data
# Copiar data-asistente.csv (~165MB) al directorio data/
# Puedes usar SCP, USB, o cloud storage
```

Al iniciar el backend por primera vez, si no existe `data/chat_data.db`, el ETL se ejecuta automaticamente desde el CSV. Esto tarda ~2 minutos en la primera ejecucion.

### 5. Variables de entorno

```bash
cp .env.example .env
# Editar .env si necesitas configurar API keys o modelo local
```

Opciones disponibles en `.env`:
- `USE_LOCAL_MODEL=true` — Usar modelo local (Ollama) en vez de API externa
- `LOCAL_MODEL_NAME` — Nombre del modelo (ej: `phi3:mini`)
- `LOCAL_MODEL_URL` — URL del servidor local

### 6. Ejecutar

```bash
# Terminal 1 — Backend
source .venv/bin/activate
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Abrir `http://localhost:5173` en el navegador.

## Instalacion en Windows

```bash
# Usar Git Bash o WSL
git clone https://github.com/kashipu/asistant-data.git asistente-tablero
cd asistente-tablero

# Backend
python -m venv .venv
source .venv/Scripts/activate   # Git Bash
# .venv\Scripts\Activate.ps1    # PowerShell
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..

# Datos
mkdir data
# Copiar data-asistente.csv al directorio data/

# Ejecutar
cp .env.example .env
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
# En otra terminal:
cd frontend && npm run dev
```

## Estructura del proyecto

```
asistente-tablero/
  backend/
    main.py              # FastAPI endpoints (20+)
    engine.py            # DataEngine singleton (cache en memoria)
    ingest.py            # ETL pipeline (7 pasos)
    loader.py            # Carga SQLite, auto-ingest si no hay DB
    dashboard_metrics.py # Metricas del dashboard (14 metricas)
    reports_deep.py      # KPIs, categorias, productos, fallos detallados
    referrals.py         # Deteccion de redirecciones
    failures.py          # Deteccion de fallos de IA
  frontend/
    src/
      App.tsx            # Routing de tabs, control ETL, periodo de datos
      services/api.ts    # Todas las llamadas API centralizadas
      components/        # Componentes React (Charts, KPIs, Deep panels...)
      components/ui/     # Componentes base (Card, Badge, Progress, Accordion)
  categorias.yml         # Taxonomia de categorias (fuente de verdad)
  productos.yml          # Catalogo de productos bancarios
  data/                  # (gitignored) CSV fuente + SQLite generado
```

## Reprocesar datos

Si cambias `categorias.yml` o `productos.yml`, reprocesa datos desde la UI:
1. Abrir el dashboard
2. Click en "Reprocesar datos" (boton en la barra superior)
3. Esperar a que el ETL termine (~2 min)

O desde la API:
```bash
curl -X POST http://localhost:8000/api/etl/run
```

## Troubleshooting

**El backend no inicia / import error:**
- Verificar que el venv esta activado: `which python` debe apuntar a `.venv/`
- Reinstalar: `pip install -r requirements.txt`

**Frontend no compila:**
- `cd frontend && rm -rf node_modules && npm install`

**Datos vacios / "Cargando..." permanente:**
- Verificar que `data/data-asistente.csv` existe
- Revisar logs del backend por errores de ETL

**pysentimiento falla en Apple Silicon:**
- Instalar torch primero: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
