# 🛠️ Utilidades de Entorno

Este documento contiene comandos útiles para la gestión del entorno de desarrollo del proyecto.

## 🛑 Apagar procesos (Kill Dev Servers)

Para liberar los puertos `8000` (Backend) y `5173` (Frontend) en Windows, ejecuta el siguiente comando en PowerShell o CMD con permisos de administrador si es necesario:

```powershell
taskkill /F /IM uvicorn.exe /IM node.exe /T
```

### Explicación del comando
*   `taskkill`: Utilidad de Windows para finalizar procesos.
*   `/F`: Fuerza la terminación del proceso (**F**orce).
*   `/IM`: Busca por el nombre de la imagen (**I**mage **M**ame). Detiene `uvicorn.exe` (FastAPI) y `node.exe` (Vite/React).
*   `/T`: Termina los procesos en **árbol** (incluye procesos hijos).

---

## 🔍 Buscar procesos por puerto

Si un puerto específico está bloqueado y no sabes qué proceso lo usa:

1. **Encontrar el PID (Process ID):**
   ```powershell
   netstat -ano | findstr :8000
   ```
2. **Matar el proceso por su PID:**
   ```powershell
   taskkill /F /PID <NÚMERO_DE_PID> /T
   ```
