# Arquitectura — Asistente Tablero

**Stack**: FastAPI + SQLite + Pandas (backend) / React + TypeScript + Recharts (frontend)
**Propósito**: Dashboard analítico para conversaciones de chatbot bancario con pipeline ETL, detección automática de fallos/derivaciones y revisión humana (HITL).

---

## Índice

1. [Visión General](#1-visión-general)
2. [Flujo de Datos](#2-flujo-de-datos)
3. [Pipeline ETL (`ingest.py`)](#3-pipeline-etl-ingestpy)
4. [Módulos Backend](#4-módulos-backend)
5. [Endpoints REST](#5-endpoints-rest)
6. [Capa de Datos (SQLite)](#6-capa-de-datos-sqlite)
7. [Archivos de Configuración YAML](#7-archivos-de-configuración-yaml)
8. [Componentes Frontend](#8-componentes-frontend)
9. [Servicio API (`api.ts`)](#9-servicio-api-apits)
10. [Flujos Clave](#10-flujos-clave)
11. [Configuración y Despliegue](#11-configuración-y-despliegue)

---

## 1. Visión General

```
CSV Input
  └─► ETL (ingest.py)
        └─► SQLite (chat_data.db)
              └─► DataEngine (singleton en memoria)
                    └─► FastAPI Endpoints (/api/*)
                          └─► React Frontend (localhost:5173)
```

El backend expone **20 endpoints REST** bajo `http://127.0.0.1:8000/api`.
El frontend consume esos endpoints mediante axios y los renderiza en **12 tabs** independientes.

---

## 2. Flujo de Datos

```
data/data-asistente.csv
    │
    ▼  [ingest.py]
    ├── Deduplicación
    ├── Propagación de sentimiento (AI → human por thread)
    ├── Homologación de producto  (aliases CSV → nombre canónico)
    ├── Propagación de producto   (AI → human por thread)
    ├── Homologación de categoría (CSV intencion → YAML)
    ├── NLP por palabras clave    (categorias.yml)
    ├── Preservación de correcciones HITL
    └── Detección Servilínea
    │
    ▼  data/chat_data.db  (tabla messages)
    │
    ▼  [engine.py — DataEngine singleton]
    │   Caches: df, thread_lengths, servilinea_threads,
    │           referrals_df, failures_df
    │
    ▼  FastAPI  →  React
```

---

## 3. Pipeline ETL (`ingest.py`)

El ETL se ejecuta al iniciar el servidor y también bajo demanda via `POST /api/etl/run` (tarea en background).

| Paso | Descripción | Salida |
|------|-------------|--------|
| **0 — Carga y limpieza** | Lee CSV, normaliza texto, parsea fechas, rellena NaN en columnas críticas | DataFrame base |
| **1 — Deduplicación** | Por `id` (primero), luego por `(thread_id, text, type, fecha, hora)` | Sin duplicados |
| **2 — Sentimiento** | Propaga `sentiment` de filas `type=ai` al resto del thread (moda). Rellena restantes con `neutral` | `sentiment` en todas las filas |
| **3 — Producto** | Homologa `product_type` del CSV con `aliases` de `productos.yml`. Propaga AI→human por thread. NLP de respaldo si no hay alias. | `product_yaml`, `product_macro_yaml` |
| **4 — Categoría** | Homologa `intencion` del CSV con mapping a YAML. Propaga AI→human por thread. | `categoria_yaml`, `macro_yaml` |
| **5 — NLP por keywords** | Para mensajes humanos sin `categoria_yaml`: busca `palabras_clave` de `categorias.yml` (substring + regex `^$`). Sin match → `requires_review=1`. Preserva correcciones HITL previas. | `categoria_yaml`, `requires_review` |
| **6 — Servilínea** | Detecta mensajes AI con "servilínea" / "línea de atención" / `tel:`. Marca todo el thread con `is_servilinea=1`. | `is_servilinea` |
| **7 — Persistencia** | Guarda en SQLite con 6 índices. | `data/chat_data.db` |

**Índices creados**: `idx_thread_id`, `idx_fecha`, `idx_type`, `idx_requires_review`, `idx_is_servilinea`, `idx_product_yaml`

---

## 4. Módulos Backend

| Módulo | Responsabilidad |
|--------|----------------|
| `main.py` | App FastAPI, definición de todos los endpoints, middleware CORS, orquestación del ETL background |
| `engine.py` | Singleton `DataEngine` — carga la DB en memoria, precalcula metadatos de threads (longitudes, servilínea, fallos, derivaciones) |
| `ingest.py` | Pipeline ETL completo (ver §3) |
| `metrics.py` | KPIs: totales de conversaciones, mensajes, usuarios, tokens |
| `categorical.py` | Distribución por intención, producto y sentimiento |
| `temporal.py` | Series temporales: volumen diario, por hora, por día de semana |
| `conversations.py` | Análisis a nivel de hilo: distribución de longitud, hilos más largos, detalle de conversación |
| `text_analysis.py` | Genera imagen de nube de palabras (NLTK + WordCloud) en base64 |
| `summary.py` | Tabla resumen agrupada por categoría × intención; hilos sin categorizar; estadísticas de encuestas |
| `failures.py` | Detecta conversaciones con fallo del bot (frases de error, usuario repite, > 50% negativo) |
| `referrals.py` | Detecta derivaciones a Servilínea (keywords + `tel:`) |
| `advisors.py` | Detecta solicitudes de asesor humano; clasifica en "Inmediato" o "Luego de intentar" |
| `insights.py` | Agrega KPIs + top categorías + derivaciones para la vista resumen |
| `feedback.py` | HITL: obtiene mensajes pendientes, procesa correcciones, actualiza YAML |
| `faqs.py` | Top frases exactas por subcategoría (test cases) |

---

## 5. Endpoints REST

Base URL: `http://127.0.0.1:8000/api`

### 5.1 Métricas y KPIs

| Método | Path | Parámetros | Retorna |
|--------|------|------------|---------|
| GET | `/kpis` | — | `total_conversations`, `total_messages`, `messages_by_type`, `avg_messages_per_thread`, `total_users`, `total_input_tokens`, `total_output_tokens` |
| GET | `/insights` | — | KPIs + top intenciones + distribución sentimientos + estadísticas de derivaciones (totales, razones frecuentes, recientes) |

### 5.2 Análisis

| Método | Path | Parámetros | Retorna |
|--------|------|------------|---------|
| GET | `/analysis/categorical` | — | `top_intents`, `top_macros`, `top_products`, `sentiment_distribution`, `sentiment_by_intent` |
| GET | `/analysis/temporal` | — | `daily_volume`, `hourly_volume`, `day_of_week_volume` |
| GET | `/analysis/conversations` | `thread_id?` | Sin thread_id: distribución de longitudes + hilos más largos. Con thread_id: mensajes del hilo + resumen |
| GET | `/analysis/wordcloud` | `intencion?` | `{ "image": "<base64 PNG>" }` |

### 5.3 Resumen y Paneles

| Método | Path | Parámetros | Retorna |
|--------|------|------------|---------|
| GET | `/summary` | `start_date?`, `end_date?` | Array de filas `{ category, intention, unique_conversations, total_interactions, human_msgs, ai_msgs, tool_msgs, positive, neutral, negative, servilinea_referrals }` |
| GET | `/analysis/uncategorized` | `page`, `limit`, `start_date?`, `end_date?` | `{ data: [{ thread_id, date, msg_count, sample_text, is_servilinea, has_empty_msg }], total, stats }` |
| GET | `/analysis/surveys` | `start_date?`, `end_date?` | `{ stats: { total, useful, not_useful }, conversations: [...] }` |
| GET | `/advisors` | `start_date?`, `end_date?` | `{ stats: { total, immediate, after_effort }, data: [{ thread_id, date, sample_text, msg_count, request_type }] }` |

### 5.4 Detección de Fallos y Derivaciones

| Método | Path | Parámetros | Retorna |
|--------|------|------------|---------|
| GET | `/failures` | `page`, `limit`, `start_date?`, `end_date?` | `{ data: [{ thread_id, fecha, intencion, product_type, msg_count, last_user_message, sentiment, criteria }], total, page, limit }` |
| GET | `/referrals` | `page`, `limit`, `start_date?`, `end_date?` | `{ data: [{ thread_id, intencion, product_type, fecha, customer_request, referral_response, msg_count, sentiment }], total, page, limit }` |

### 5.5 Explorador de Mensajes

| Método | Path | Parámetros | Retorna |
|--------|------|------------|---------|
| GET | `/messages` | `page`, `limit`, `search?`, `intencion?`, `sentiment?`, `product?`, `sender_type?`, `thread_id?`, `exclude_empty?`, `sort_by?`, `start_date?`, `end_date?` | `{ data: [{ id, thread_id, text, fecha, hora, type, sentiment, intencion, product_type, categoria_yaml, macro_yaml, is_servilinea, thread_length, input_tokens, output_tokens }], total, page, limit }` |
| GET | `/options` | — | `{ intenciones: [...], productos: [...], sentimientos: [...] }` |

> **Default:** Si no se pasa `sender_type`, `thread_id`, `search`, `intencion`, `sentiment` ni `product`, muestra solo mensajes humanos.

### 5.6 HITL — Revisión Manual

| Método | Path | Parámetros | Retorna |
|--------|------|------------|---------|
| GET | `/feedbacks` | `page`, `limit` | `{ data: [{ id, thread_id, text, fecha, sentiment, categoria_yaml, macro_yaml, product_yaml, product_macro_yaml, requires_review }], total, page, limit }` |
| GET | `/feedbacks/options` | — | `{ categories: [...], products: [...], sentiments: [...] }` |
| POST | `/feedbacks/categorize` | Body: `{ message_id, new_category, new_sentiment?, new_product?, original_text }` | `{ success: bool, yaml_updated: bool }` — Actualiza DB + aprende en YAML |

### 5.7 FAQs y ETL

| Método | Path | Parámetros | Retorna |
|--------|------|------------|---------|
| GET | `/faqs` | `top_n?` (default 5) | `{ "Macro": { "Subcategoría": [{ phrase, count }] } }` |
| POST | `/etl/run` | — | Inicia pipeline en background. `{ "message": "ETL process started..." }` |
| GET | `/etl/status` | — | `{ is_running: bool, elapsed_seconds: int, last_status: "success"\|"error"\|null }` |

---

## 6. Capa de Datos (SQLite)

**Archivo**: `data/chat_data.db` — tabla `messages`

| Columna | Tipo | Origen | Descripción |
|---------|------|--------|-------------|
| `id` | TEXT | CSV | ID único del mensaje |
| `thread_id` | TEXT | CSV | ID de la conversación |
| `text` | TEXT | CSV | Contenido del mensaje |
| `fecha` | TEXT | CSV | Fecha `YYYY-MM-DD` |
| `hora` | INTEGER | CSV | Hora del día (0–23) |
| `type` | TEXT | CSV | `human` / `ai` / `tool` |
| `sentiment` | TEXT | ETL-2 | `positivo` / `neutral` / `negativo` |
| `intencion` | TEXT | CSV | Intención original (cruda) |
| `product_type` | TEXT | CSV | Producto original (crudo) |
| `product_detail` | TEXT | CSV | Detalle de producto (crudo) |
| `client_ip` | TEXT | CSV | IP del cliente (para contar usuarios únicos) |
| `input_tokens` | INTEGER | CSV | Tokens de entrada del LLM |
| `output_tokens` | INTEGER | CSV | Tokens de salida del LLM |
| `rowid` | INTEGER | CSV | Índice de fila original |
| `categoria_yaml` | TEXT | ETL-4/5 | Subcategoría del YAML (fuente de verdad) |
| `macro_yaml` | TEXT | ETL-4/5 | Macro del YAML |
| `product_yaml` | TEXT | ETL-3 | Producto canónico del YAML |
| `product_macro_yaml` | TEXT | ETL-3 | Macro de producto del YAML |
| `is_servilinea` | INTEGER | ETL-6 | `1` si el hilo fue derivado a Servilínea |
| `requires_review` | INTEGER | ETL-5 | `1` si requiere revisión HITL |

---

## 7. Archivos de Configuración YAML

### `categorias.yml`

Define las categorías de intención con reglas de matching por palabras clave.

```yaml
version: v12-20260226-macro-subcategoria
categorias:
  - nombre: "Envío de Dinero"      # Subcategoría (fuente de verdad en DB)
    macro: "Transferencias"         # Grupo macro para aggregación
    descripcion: "..."
    min_len: 1                      # Longitud mínima del texto para aplicar
    palabras_clave:
      - "enviar dinero"             # Substring match (case-insensitive)
      - "^transferir$"              # Regex: match exacto
      - "cel2cel"
```

**Usos**:
- ETL paso 5: NLP de categorización automática
- `feedback.py`: Opciones para el selector de categoría en HITL
- `feedback.py`: Aprende — al guardar una corrección HITL, el texto original se agrega a `palabras_clave`
- `categorias_v1_backup.yml`: Copia de seguridad creada automáticamente la primera vez que HITL modifica el archivo

### `productos.yml`

Define los productos bancarios canónicos con aliases para homologación del CSV.

```yaml
version: v1-20260226
productos:
  - nombre: "Tarjeta de Crédito"         # Nombre canónico (guardado en DB)
    macro: "Tarjetas"                     # Grupo de productos
    aliases:
      - "tarjeta de credito"              # Variantes del CSV (product_type / product_detail)
      - "tc"
      - "[tarjeta de credito] latam"
    palabras_clave:
      - "tarjeta de crédito"              # NLP de respaldo si el CSV no trae product_type
      - "cupo disponible"
```

**Usos**:
- ETL paso 3: Homologación y NLP de producto
- `feedback.py`: Opciones para el selector de producto en HITL

---

## 8. Componentes Frontend

Todos los componentes importan `api` de `../services/api`.

| Componente | Tab | Endpoints consumidos | Descripción |
|------------|-----|---------------------|-------------|
| `Insights.tsx` | Dashboard | `/insights` | KPIs, top categorías (barras horizontales), razones de derivación, derivaciones recientes |
| `Charts.tsx` | Análisis | `/analysis/temporal`, `/analysis/categorical` | Volumen diario (línea), por hora (barras), top intenciones (barras), distribución sentimiento (torta) |
| `SummaryTable.tsx` | Resumen | `/summary` | Tabla agrupada Macro × Subcategoría con conteos y sentimientos. Columna total sticky. Ordenable. |
| `MessageExplorer.tsx` | Mensajes | `/messages`, `/options` | Tabla con 10 filtros (búsqueda, intención, sentimiento, producto, tipo, thread, vacíos, orden). Paginación. Navega a hilo completo. |
| `Failures.tsx` | Fallos | `/failures` | Tabla de conversaciones con fallo detectado. Muestra criterio de fallo y último mensaje del usuario. |
| `Referrals.tsx` | Derivaciones | `/referrals` | Tabla de derivaciones a Servilínea. Muestra petición del cliente y respuesta del bot. |
| `AdvisorPanel.tsx` | Asesores | `/advisors` | Cards con totales + tabla con tipo de solicitud (Inmediato / Luego de intentar). |
| `UncategorizedPanel.tsx` | Sin categoría | `/analysis/uncategorized` | Cards estadísticas + tabla de hilos sin categorizar. Muestra texto de muestra. |
| `SurveyPanel.tsx` | Encuestas | `/analysis/surveys` | Cards con % útil/no útil + tabla de respuestas individuales. |
| `ReviewPanel.tsx` | HITL | `/feedbacks`, `/feedbacks/options`, `/feedbacks/categorize` | Formulario de revisión manual. Datalist para categoría, selects para producto y sentimiento. Aprende al guardar. |
| `FaqsPanel.tsx` | FAQs | `/faqs` | Jerarquía colapsable Macro → Subcategoría → Frases. Botones de copiar y exportar a Excel. |
| `KPIs.tsx` | (embebido) | (prop del padre) | 4 tarjetas de KPI: Conversaciones, Mensajes, Usuarios únicos, Promedio mensajes/conv. |

---

## 9. Servicio API (`api.ts`)

**Archivo**: `frontend/src/services/api.ts`
**Base URL**: `http://127.0.0.1:8000/api`

```typescript
export const api = {
  // Métricas
  getKpis()
  getInsights()

  // Análisis
  getCategoricalAnalysis()
  getTemporalAnalysis()
  getConversationAnalysis(threadId?)
  getWordCloud(intencion?)

  // Resumen y paneles
  getSummary(start_date?, end_date?)
  getUncategorized(page, limit, start_date?, end_date?)
  getSurveys(start_date?, end_date?)
  getAdvisors(start_date?, end_date?)

  // Detección
  getFailures({ page, limit, start_date?, end_date? })
  getReferrals({ page, limit, start_date?, end_date? })

  // Explorador
  getMessages({ page, limit, search?, intencion?, sentiment?, product?,
                sender_type?, thread_id?, exclude_empty?, sort_by?,
                start_date?, end_date? })
  getOptions()

  // HITL
  getFeedbacks(page, limit)
  getFeedbackOptions()
  categorizeFeedback({ message_id, new_category, new_sentiment?,
                       new_product?, original_text })

  // FAQs y ETL
  getFaqs(top_n?)
  runEtl()
  getEtlStatus()
}
```

---

## 10. Flujos Clave

### 10.1 HITL — Aprendizaje Continuo

```
ETL → mensajes sin match → requires_review=1
         │
         ▼
ReviewPanel muestra mensajes pendientes
         │
Usuario selecciona categoría / producto / sentimiento
         │
         ▼
POST /api/feedbacks/categorize
  ├── DB: categoria_yaml, macro_yaml, product_yaml, requires_review=0
  └── YAML: agrega original_text a palabras_clave de la categoría
         │
         ▼
Próxima ETL → mayor precisión automática
```

### 10.2 Re-procesamiento (ETL On-Demand)

```
Usuario → "Re-procesar Datos" (App.tsx)
       → POST /api/etl/run
       → Poll GET /api/etl/status cada 3 seg
       → is_running=false → last_status="success"
       → Recarga la página
```

### 10.3 Detección de Fallos

```
failures.py analiza cada thread:
  ├── Bot usa frases de error ("no puedo", "lo siento", "no tengo información")
  ├── Usuario repite la misma pregunta (frustración)
  └── > 50% mensajes con sentimiento negativo

→ Failures.tsx muestra tabla con criterio + último mensaje
→ "Ver conversación" → MessageExplorer filtrado por thread_id
```

### 10.4 Navegación a Hilo Completo

Todos los paneles de lista (Failures, Referrals, HITL, Uncategorized, Advisors) tienen un botón "Ver conversación" que navega a `MessageExplorer` con `thread_id` pre-filtrado, mostrando todos los mensajes ordenados por `rowid`.

---

## 11. Configuración y Despliegue

### Puertos
| Servicio | Host | Puerto |
|----------|------|--------|
| Backend (uvicorn) | 127.0.0.1 | 8000 |
| Frontend (Vite dev) | localhost | 5173 |

### CORS permitidos
```
http://localhost:5173
http://127.0.0.1:5173
http://localhost:3000
http://127.0.0.1:3000
```

### Rutas de archivos (relativas a la raíz del proyecto)
```
data/data-asistente.csv       ← Input del ETL
data/chat_data.db             ← Base de datos SQLite
categorias.yml                ← Categorías e intenciones
productos.yml                 ← Catálogo de productos
categorias_v1_backup.yml      ← Backup automático (creado en 1er HITL update)
```

### Comandos de inicio
```bash
# Backend (con venv activado)
uvicorn backend.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8000

# Frontend
cd frontend && npm run dev
```

### Dependencias principales
| Backend | Frontend |
|---------|----------|
| FastAPI 0.128 | React 18 + TypeScript |
| Starlette 0.52 | Recharts |
| Pandas | Tailwind CSS |
| SQLite3 (stdlib) | Lucide React |
| NLTK | Axios |
| PyYAML | XLSX (exportar Excel) |
| WordCloud + Matplotlib | Vite |

---

*Generado el 2026-02-26*
