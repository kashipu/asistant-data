# Contexto del Proyecto: Asistente Tablero

Este documento proporciona una visión general de la arquitectura, tecnologías, lenguajes y estructura del proyecto "Asistente Tablero", diseñado para analizar datos de conversaciones de chatbots bancarios. Este archivo sirve como memoria principal e introducción rápida al entorno de desarrollo.

---

## 1. Arquitectura General y Flujo de Datos
El proyecto sigue una arquitectura clásica de **Cliente-Servidor**, dividiendo la responsabilidad de la interfaz gráfica y la lógica analítica de la siguiente manera:

1. **El Usuario (Cliente)** navega en el Frontend interactuando con los dashboards.
2. **El Frontend (React)** renderiza los gráficos (usando Recharts) y recopila filtros. Envía peticiones HTTP mediante `axios` hacia el puerto `8000`.
3. **El Backend (FastAPI)** recibe la petición REST, se comunica con el motor de datos (`DataEngine` en `engine.py`) y hace consultas sobre la base de datos `SQLite` (`data/chat_data.db`).
4. **Procesamiento Analítico:** Con ayuda de `pandas`, el backend filtra fechas, analiza longitudes, genera nubes de palabras (`wordcloud`) y prepara tablas resumen.
5. **Respuesta:** La API devuelve el resultado procesado en formato JSON, el cual actualiza el estado del React y la vista del usuario en tiempo real.

---

## 2. Pila Tecnológica (Tech Stack)

### 🎨 Frontend (Interfaz Visual)
- **Lenguaje Principal:** TypeScript (`.tsx`, `.ts`)
- **Framework Core:** React (v18.2.0)
- **Herramienta de Construcción:** Vite (Entorno de desarrollo super-rápido)
- **Estilos y Componentes:** 
  - Tailwind CSS (Gestión de estilos utilitarios)
  - `tailwind-merge` y `clsx` (Para la combinación y renderización dinámica de clases)
- **Visualización de Datos:** Recharts (Gráficos estadísticos y de tiempo)
- **Iconografía:** Lucide React
- **Peticiones HTTP:** Axios

### ⚙️ Backend (API de Procesamiento y Análisis)
- **Lenguaje Principal:** Python (v3.9+, Recomendado 3.10+)
- **Framework Web:** FastAPI (Robusto y asíncrono, basado en tipos)
- **Servidor ASGI:** Uvicorn
- **Procesamiento de Datos y NLP:**
  - `pandas`: Filtrado y agregaciones de DataFrames en memoria.
  - `openpyxl`: Soporte para lectura de archivos excel si es aplicable.
  - `nltk`, `wordcloud`, `ftfy`: Analítica de texto, limpieza unicode y nubes de palabras.
- **Base de Datos:** SQLite. Los datos de las conversaciones están almacenados de forma local en `data/chat_data.db`.

---

## 3. Estructura de Carpetas

```text
asistente-tablero/
├── backend/                # Lógica del servidor y analítica de datos
│   ├── main.py             # Punto de entrada de la API y declaración de Endpoints de FastAPI
│   ├── engine.py           # Motor de manejo de datos base (DataEngine implementado como Singleton)
│   ├── summary.py          # Agregación y resumen estadístico de datos generales
│   ├── failures.py         # Módulo para detección de fallos o frustraciones del usuario
│   ├── categorical.py      # Análisis de frecuencias por intenciones y categorías
│   ├── text_analysis.py    # Generación de WordClouds basados en texto de usuarios
│   └── ...                 # Otros servicios analíticos (conversations, temporal, insights, referrals)
│
├── frontend/               # Aplicación Single-Page
│   ├── package.json        # Dependencias NPM y scripts (dev, build, lint)
│   ├── vite.config.ts      # Configuración del compilador frontend
│   ├── tailwind.config.js  # Reglas, temas y colores definidos para Tailwind
│   └── src/                # Código fuente interactivo
│       ├── components/     # Paneles reutilizables de React (Ej. Gráficos, Tablas, Modales)
│       └── services/       # Conectores cliente Axios mapeados a los endpoints de FastAPI
│
├── data/                   # Almacenamiento local Data Lake / BBDD
│   └── chat_data.db        # Archivo SQLite con la base de datos principal
│
├── pyproject.toml          # Meta-información del paquete Python y dependencias
├── requirements.txt        # Manejo de requisitos básicos Python (Pip)
└── README.md               # Instrucciones de setup y quickstart general
```

---

## 4. Temas y Entidades Clave del Negocio

### Vista de Frontend 
- **Dashboard de KPIs:** Permite la vista consolidada de volumen (mensajes, conversaciones), incluyendo un análisis temporal (día/fecha).
- **Control de Tableros (Paneles):** 
  - Panel de Encuestas (`surveys`): Rastreo de si la IA fue útil (Ej: `[survey] útil` vs `No útil`).
  - Panel "Sin Categoría" (`UncategorizedPanel`): Ayuda a identificar flujos o intenciones que la IA no pudo manejar (Mensajes vacíos, traslados a Servilínea).
- **Navegación Intuitiva:** El frontend soporta paginaciones completas manejadas enteramente por el backend a través de queries (ej: `?page=1&limit=20`).

### Dominio desde el Backend
- **DataEngine (Singleton):** Carga perezosa (lazy-load) conectándose a SQLite para evitar lecturas constantes del disco. Genera la metadata de "longitud de conversación" y pre-calcula flujos (como referencias a asesores `Servilínea`).
- **Análisis de Texto:** Procesador para agrupar términos clave mediante NLP, logrando visualizaciones (WordClouds) segmentables por intención de los clientes.
- **Endpoints Flexibles:** `main.py` expone múltiples rutas (`/api/messages`, `/api/failures`, `/api/referrals`, `/api/summary`) capaces de filtrar granularmente por Rango de Fechas, Producto, o Sentimiento.

---

## 5. Accesos de Desarrollo

- **Frontend:** 
  ```bash
  cd frontend
  npm run dev
  ```
  *Disponible en: http://localhost:5173* (O puerto indicado en consola).

- **Backend:** 
  ```bash
  # Activar entorno virtual
  uvicorn backend.main:app --reload
  ```
  *Disponible en: http://localhost:8000*
  *Documentación Swagger: http://localhost:8000/docs* (Excelente para probar queries rápidos).

> **Nota para IAs / Agentes (`Global Rule`)**: Revisar siempre este archivo `GEMINI.md` y `README.md` antes de ejecutar mutaciones estructurales o adición de dependencias en el proyecto para asegurar el cumplimiento del Stack tecnológico actual (FastAPI + React).
