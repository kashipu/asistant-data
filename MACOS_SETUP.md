# Guía de Instalación para macOS

Esta guía detalla paso a paso cómo levantar el proyecto **Tablero de Análisis de Chatbot** en una máquina macOS desde cero.

## 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instaladas las siguientes herramientas. Abre tu **Terminal** para verificar.

### Git

Normalmente viene instalado con macOS o Xcode Command Line Tools.

```bash
git --version
# Debería mostrar algo como: git version 2.39.0
```

*Si no lo tienes, al intentar usarlo macOS te pedirá instalar las "Command Line Developer Tools". Acepta la instalación.*

### Python 3

macOS suele traer Python, pero recomendamos usar una versión reciente (3.10+).

```bash
python3 --version
# Debería mostrar Python 3.10.x o superior
```

*Si no lo tienes:* Descárgalo desde [python.org](https://www.python.org/downloads/) o usa Homebrew: `brew install python`.

### Node.js y npm
Necesario para el frontend (React).

```bash
node -v
npm -v
# Node debería ser v16 o superior.
```

*Si no lo tienes:* Descárgalo desde [nodejs.org](https://nodejs.org/) (versión LTS recomendada) o usa Homebrew: `brew install node`.

---

## 2. Clonar el Proyecto

Elige una carpeta donde quieras guardar el proyecto y clónalo.

```bash
# Navega a tu carpeta de proyectos (opcional)
cd ~/Documents

# Clona el repositorio
git clone <URL_DEL_REPOSITORIO>

# Entra en la carpeta del proyecto
cd asistente-tablero
```

---

## 3. Configurar el Backend

El backend usa Python y FastAPI. Configuraremos un entorno virtual para aislar las dependencias.

1.  **Crear entorno virtual:**

    ```bash
    python3 -m venv .venv
    ```

2.  **Activar el entorno:**

    ```bash
    source .venv/bin/activate
    ```

    *Verás que tu terminal ahora muestra `(.venv)` al principio de la línea.*

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar el servidor (Prueba):**

    ```bash
    uvicorn backend.main:app --reload
    ```

    Deberías ver un mensaje indicando que el servidor corre en `http://127.0.0.1:8000`.
    
    🛑 **Para detenerlo:** Presiona `Ctrl + C`.

---

## 4. Configurar el Frontend

El frontend usa React y Vite. Configúralo en una **nueva pestaña** de la terminal (Command + T).

1.  **Navegar a la carpeta frontend:**

    ```bash
    # Asegúrate de estar en la raíz del proyecto primero
    cd frontend
    ```

2.  **Instalar dependencias de Node:**

    ```bash
    npm install
    ```

3.  **Ejecutar el servidor de desarrollo:**

    ```bash
    npm run dev
    ```

    Verás un mensaje indicando que la app corre en `http://localhost:5173`.

---

## 5. Flujo de Trabajo Diario

Cada vez que quieras trabajar en el proyecto, necesitarás dos terminales:

**Terminal 1 (Backend):**

```bash
cd asistente-tablero
source .venv/bin/activate
uvicorn backend.main:app --reload
```

**Terminal 2 (Frontend):**

```bash
cd asistente-tablero/frontend
npm run dev
```

Abre tu navegador en: [http://localhost:5173](http://localhost:5173)

---

## Solución de Problemas Comunes en macOS

-   **Permisos denegados (EACCES):** Si `npm install` falla por permisos, evita usar `sudo`. Intenta reinstalar Node con Homebrew o usa nvm.
-   **Puerto ocupado:** Si el puerto 8000 o 5173 está en uso, busca el proceso con `lsof -i :8000` y mátalo con `kill -9 <PID>`, o cambia el puerto en el comando de inicio.
-   **Python Command not found:** Asegúrate de usar `python3` y `pip3` si `python` apunta a la versión 2.x (obsoleta en macOS nuevos, pero posible en sistemas antiguos).
