# Guía de Migración: MDRP-BCS en Windows 11

Pasos para poner en marcha el proyecto en una máquina nueva con Windows 11.

---

## 1. Instalar prerrequisitos

### 1.1 Git

1. Descarga Git desde https://git-scm.com/download/win
2. Instala con las opciones por defecto (asegúrate de que "Git from the command line" quede habilitado).
3. Verifica en una terminal nueva:
   ```powershell
   git --version
   ```

### 1.2 Python 3.8+

1. Descarga Python desde https://www.python.org/downloads/
2. **Importante:** marca la casilla **"Add Python to PATH"** durante la instalación.
3. Verifica:
   ```powershell
   python --version
   pip --version
   ```

### 1.3 Docker Desktop

1. Descarga Docker Desktop para Windows desde https://www.docker.com/products/docker-desktop/
2. Ejecuta el instalador. Si te pide habilitar **WSL 2**, acepta (es el backend recomendado).
   - Si WSL 2 no está instalado, el instalador de Docker te guiará. También puedes hacerlo manualmente:
     ```powershell
     wsl --install
     ```
     Reinicia la PC después de esto.
3. Abre Docker Desktop y espera a que el ícono en la barra de tareas muestre "Docker Desktop is running".
4. Verifica en la terminal:
   ```powershell
   docker --version
   docker compose version
   ```

---

## 2. Clonar el repositorio

```powershell
git clone https://github.com/AlanSamaSM/MDRP-BCS-code.git
cd MDRP-BCS-code
```

> El repositorio ya incluye los archivos OSRM precompilados para La Paz/BCS en `osrm_data/` (~160 MB), por lo que la clonación puede tardar un poco.

---

## 3. Instalar dependencias de Python

Se recomienda usar un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Si PowerShell bloquea la activación del venv, ejecuta primero:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

---

## 4. Levantar el servidor OSRM con Docker

El proyecto usa un servidor OSRM local para calcular rutas reales. Se levanta con Docker Compose:

```powershell
docker compose up -d
```

Esto descarga la imagen `osrm/osrm-backend:5.26.0` (~200 MB, solo la primera vez) y arranca el contenedor `mdrp-osrm` en el puerto **5000**.

### Verificar que OSRM está funcionando

```powershell
curl http://localhost:5000/route/v1/driving/-110.31,24.14;-110.30,24.15
```

Deberías recibir una respuesta JSON con `"code":"Ok"`. Si `curl` no está disponible, abre esa URL en el navegador.

### Comandos útiles de Docker

| Acción | Comando |
|---|---|
| Ver contenedores activos | `docker ps` |
| Ver logs del contenedor | `docker logs mdrp-osrm` |
| Detener el servidor | `docker compose down` |
| Reiniciar | `docker compose restart` |

---

## 5. Ejecutar el proyecto

### Pipeline completo (genera datos, corre ambas políticas, compara KPIs)

```powershell
python scripts/generate_results.py
```

### Ejecución manual paso a paso

```powershell
# 1. Generar datos sintéticos
python scripts/make_synth_orders.py

# 2. Ejecutar política FCFS
python scripts/run_fcfs_instance.py data/synthetic_lapaz_orders_limited.csv

# 3. Ejecutar política Rolling Horizon
python scripts/run_synth_instance.py data/synthetic_lapaz_orders_limited.csv

# 4. Solo análisis de resultados
python scripts/generate_results.py --analyze-only
```

### Experimentos con múltiples escenarios y semillas

```powershell
python scripts/run_experiments.py
```

---

## 6. Solución de problemas

### Docker no arranca / error de WSL

```powershell
wsl --update
wsl --set-default-version 2
```
Reinicia Docker Desktop después.

### Error "Cannot connect to the Docker daemon"

Asegúrate de que Docker Desktop está abierto y corriendo (ícono verde en la barra de tareas).

### OSRM no responde en localhost:5000

1. Verifica que el contenedor está activo: `docker ps`
2. Si no aparece, revisa los logs: `docker compose logs osrm`
3. Asegúrate de que el puerto 5000 no esté ocupado por otra aplicación.

### Error de permisos en PowerShell con venv

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### pip install falla con geopandas/shapely

Estas librerías requieren compilación nativa. Si hay errores, instala las build tools:
```powershell
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
Si persiste, usa los binarios precompilados de Christoph Gohlke o instala via conda:
```powershell
conda install geopandas shapely
```
