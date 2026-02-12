# Tablero de Análisis de Chatbot

Este proyecto es un sistema integral para analizar datos de conversaciones de chatbots. Consta de un backend en Python (FastAPI) para el procesamiento de datos y un frontend en React (Vite + Tailwind CSS) para la visualización.

## Características Principales

### 📊 Dashboard General
- **KPIs**: Total de conversaciones, mensajes, usuarios únicos y métricas de uso.
- **Gráficos**: Análisis temporal (volumen por día/hora) y distribución por categoría/sentimiento.

### 🔍 Herramientas de Análisis
- **Explorador de Mensajes**: Buscador avanzado con filtros por intención, sentimiento, producto, remitente y texto.
  - *Nuevo*: Filtro de mensajes vacíos y ordenamiento por longitud de conversación.
- **Resumen Detallado**: Tabla clasificatoria por Categoría e Intención.
- **Análisis de "Sin Categoría"**: Panel con estadísticas (Servilínea, Vacíos) y paginación.
- **Análisis de Encuestas**: Seguimiento de feedback `[survey]` (Útil vs No Útil).

### 🚨 Detección de Problemas
- **Fallos**: Identifica conversaciones con errores técnicos o frustración del usuario.
- **Servilínea**: Rastreo automático de derivaciones a soporte humano.

---

## Requisitos Previos

- **Python 3.10+**
- **Node.js 16+**
- **SQLite** (Base de datos incluida en `data/chat_data.db`)

---

## Instrucciones de Ejecución

### 1. Configurar Backend (Python/FastAPI)

El backend procesa los datos y sirve la API en el puerto `8000`.

1.  **Navega a la carpeta raíz:**
    > 📂 Ejecutar en: `asistente-tablero/`
    ```bash
    cd asistente-tablero
    ```

2.  **Crea un entorno virtual e instala dependencias:**
    > 📂 Ejecutar en: `asistente-tablero/`

    **MacOS / Linux:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

    **Windows:**
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Inicia el servidor:**
    > 📂 Ejecutar en: `asistente-tablero/`
    ```bash
    # Asegúrate de que el entorno virtual esté activo (.venv)
    uvicorn backend.main:app --reload
    ```
    
    *API disponible en:* `http://localhost:8000`  
    *Documentación interactiva:* `http://localhost:8000/docs`

### 2. Configurar Frontend (React/Vite)

El dashboard visual se ejecuta en el puerto `5173`.

1.  **Navega a la carpeta frontend:**
    > 📂 Ejecutar en: `asistente-tablero/`
    ```bash
    cd frontend
    ```

2.  **Instala dependencias:**
    > 📂 Ejecutar en: `asistente-tablero/frontend/`
    ```bash
    npm install
    ```

3.  **Inicia el servidor de desarrollo:**
    > 📂 Ejecutar en: `asistente-tablero/frontend/`
    ```bash
    npm run dev
    ```

    *Dashboard disponible en:* `http://localhost:5173`

---

## Estructura del Proyecto

- `backend/`: Código fuente de la API.
  - `main.py`: Punto de entrada y endpoints.
  - `summary.py`: Lógica de agregación y estadísticas.
  - `ingest.py`: Script de importación de datos (CSV -> SQLite).
- `frontend/`: Aplicación React.
  - `src/components/`: Paneles (Charts, SummaryTable, UncategorizedPanel, SurveyPanel).
  - `src/services/`: Conexión con API.
- `data/`: Base de datos SQLite y archivos fuente.
