# Setup de OSRM en Nueva Computadora

Este archivo explica cómo transferir los datos de OSRM a otra computadora y ejecutar el proyecto.

## Opción 1: Transferencia via USB (Recomendado)

### Paso 1: Preparar los archivos en la computadora original

Los archivos `.osrm` ya están en la carpeta `osrm_data/`. Solo cópialo completo a tu USB:

```powershell
# En la computadora original:
Copy-Item -Path "C:\Users\alan_\Documents\GitHub\MDRP-BCS-code\osrm_data" -Destination "X:\osrm_data" -Recurse
```

### Paso 2: Transferir a la nueva computadora

```powershell
# En la nueva computadora:
# Copia la carpeta osrm_data desde el USB al repositorio
Copy-Item -Path "X:\osrm_data" -Destination "C:\Users\<tu_usuario>\Documents\GitHub\MDRP-BCS-code\" -Recurse
```

### Paso 3: Verificar que los archivos estén presentes

```powershell
Get-ChildItem "C:\Users\<tu_usuario>\Documents\GitHub\MDRP-BCS-code\osrm_data" | Select-Object Name
```

Deberías ver archivos como:
- `mexico-251010.osm.pbf`
- `mexico-251010.osrm`
- `mexico-251010.osrm.fileIndex`
- etc.

## Opción 2: NO Transferir (Solo ejecutar ruteo remoto)

Si la segunda computadora es débil, puedes dejar OSRM corriendo en la computadora más potente y acceder remotamente:

### En la computadora potente (servidora):

```powershell
# Iniciar OSRM sin restricción de puerto local (escucha en 0.0.0.0)
docker run -d -p 5000:5000 \
  -v "C:\Users\alan_\Documents\GitHub\MDRP-BCS-code\osrm_data:/data" \
  osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm
```

### En la computadora débil (cliente):

1. Edita `src/config.py` y cambia:

```python
# config.py
OSRM_URL = "http://<IP_computadora_potente>:5000"
# Ejemplo:
# OSRM_URL = "http://192.168.1.100:5000"
```

2. Ejecuta los scripts normalmente:

```powershell
python scripts/generate_results.py
```

## Opción 3: Descargar y procesar desde cero

Si prefieres no transferir los archivos, puedes descargarlos y procesarlos en la nueva computadora:

### Paso 1: Descargar el mapa de OSM

```powershell
# Descarga desde Geofabrik (el archivo mexico-latest.osm.pbf)
# URL: https://download.geofabrik.de/north-america/mexico.html
# Guarda en: osrm_data/mexico-251010.osm.pbf
```

### Paso 2: Procesar el mapa con OSRM

Sigue los pasos en `docs/osrm_manual.md`:

```powershell
# Extract
docker run -t -v "C:\...\osrm_data:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/mexico-251010.osm.pbf

# Partition
docker run -t -v "C:\...\osrm_data:/data" osrm/osrm-backend osrm-partition /data/mexico-251010.osrm

# Customize
docker run -t -v "C:\...\osrm_data:/data" osrm/osrm-backend osrm-customize /data/mexico-251010.osrm
```

## Ejecución del Servidor OSRM

Una vez que los archivos estén en su lugar, ejecuta el servidor:

```powershell
# Forma 1: Interactivo (ves logs en pantalla)
docker run -t -i -p 5000:5000 \
  -v "C:\Users\<tu_usuario>\Documents\GitHub\MDRP-BCS-code\osrm_data:/data" \
  osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm

# Forma 2: Background (se ejecuta en segundo plano)
docker run -d -p 5000:5000 \
  -v "C:\Users\<tu_usuario>\Documents\GitHub\MDRP-BCS-code\osrm_data:/data" \
  osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm
```

## Verificar que todo funciona

```powershell
# Prueba rápida con curl
curl "http://localhost:5000/route/v1/driving/-110.31,24.14;-110.29,24.16?overview=false"

# Deberías ver una respuesta JSON con "code": "Ok"
```

## Si algo no funciona

Revisa `docs/osrm_manual.md` en la sección "Troubleshooting" para diagnosticar problemas comunes.
