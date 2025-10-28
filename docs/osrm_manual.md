# Manual OSRM con Docker para MDRP-BCS

Este documento describe la integración de OSRM (Open Source Routing Machine) con Docker como backend de routing para el sistema MDRP-BCS (Meal Delivery Routing Problem - Baja California Sur).

## Índice

1. [Introducción](#introducción)
2. [Requisitos Previos](#requisitos-previos)
3. [Obtención de Datos OSM](#obtención-de-datos-osm)
4. [Preprocesamiento de Datos](#preprocesamiento-de-datos)
5. [Ejecución del Servidor OSRM](#ejecución-del-servidor-osrm)
6. [Endpoints y Uso](#endpoints-y-uso)
7. [Integración con Python](#integración-con-python)
8. [Troubleshooting](#troubleshooting)
9. [Referencias](#referencias)

---

## Introducción

OSRM es un motor de routing de código abierto diseñado para encontrar rutas óptimas en redes de carreteras. En este proyecto, OSRM se ejecuta en un contenedor Docker para:

- **Calcular rutas realistas** entre restaurantes y clientes en La Paz, BCS
- **Obtener tiempos y distancias** precisas basadas en la red vial real
- **Proveer routing escalable** sin depender de APIs comerciales
- **Garantizar reproducibilidad** mediante contenedores

### Ventajas de OSRM con Docker

- ✅ **Independencia**: No requiere APIs externas (Google Maps, Mapbox)
- ✅ **Velocidad**: Respuestas en milisegundos con algoritmos MLD (Multi-Level Dijkstra)
- ✅ **Reproducibilidad**: Mismo código + mismos datos = mismos resultados
- ✅ **Portabilidad**: Corre en Windows, Linux, macOS con Docker
- ✅ **Sin límites de requests**: No hay quotas ni costos por consulta

---

## Requisitos Previos

### Software Necesario

1. **Docker Desktop** (Windows/Mac) o Docker Engine (Linux)
   - Descargar: https://www.docker.com/products/docker-desktop
   - Versión mínima: 20.10+

2. **Imagen OSRM Backend**
   ```powershell
   docker pull osrm/osrm-backend
   ```

### Hardware Recomendado

- **RAM**: Mínimo 4GB (8GB recomendado para ciudades grandes)
- **Disco**: ~500MB por archivo .osm.pbf + ~2-5x para archivos .osrm procesados
- **CPU**: Multi-core recomendado para preprocesamiento rápido

### Verificar Instalación

```powershell
# Verificar Docker
docker --version

# Verificar imagen OSRM
docker images | grep osrm
```

---

## Obtención de Datos OSM

### Opción 1: Descargar desde Geofabrik (Recomendado)

Geofabrik ofrece extracciones regionales actualizadas diariamente:

```powershell
# Descargar México (incluye La Paz, BCS)
# URL: https://download.geofabrik.de/north-america/mexico.html

# Ejemplo con wget (o descarga manual)
wget https://download.geofabrik.de/north-america/mexico-latest.osm.pbf
```

### Opción 2: Exportar área específica con BBBike

Para áreas pequeñas (ciudad), usa [BBBike Extract Service](https://extract.bbbike.org/):

1. Selecciona área en el mapa (La Paz, BCS)
2. Formato: PBF
3. Descarga cuando esté listo

### Opción 3: Overpass API (áreas muy pequeñas)

```bash
# Requiere osmosis o similar
# No recomendado para este proyecto
```

### Archivo Usado en Este Proyecto

- **Archivo**: `mexico-251010.osm.pbf`
- **Fecha de descarga**: 25 de octubre, 2025
- **Fuente**: Geofabrik
- **Tamaño**: ~1.2 GB (comprimido)
- **Región**: Todo México (contiene La Paz, BCS)

**Ubicación en el repositorio:**
```
MDRP-BCS-code/
├── mexico-251010.osm.pbf          # Datos OSM originales
├── mexico-251010.osrm              # Datos procesados (no borrar)
├── mexico-251010.osrm.*            # Archivos auxiliares OSRM
```

---

## Preprocesamiento de Datos

OSRM requiere **preprocesar** los datos OSM antes de usarlos. Este proceso se hace **una sola vez** y genera archivos `.osrm` optimizados.

### Algoritmos Disponibles

1. **CH (Contraction Hierarchies)**: Más rápido de procesar, menos flexible
2. **MLD (Multi-Level Dijkstra)**: Más lento de procesar, más flexible, **RECOMENDADO**

Este proyecto usa **MLD** por su balance entre velocidad y flexibilidad.

### Paso 1: Extract (Convertir OSM a formato OSRM)

```powershell
docker run -t -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/mexico-251010.osm.pbf
```

**Parámetros:**
- `-v`: Monta el directorio local en `/data` dentro del contenedor
- `-p /opt/car.lua`: Perfil de routing (car = automóvil)
- `/data/mexico-251010.osm.pbf`: Archivo de entrada

**Salida:**
- `mexico-251010.osrm` (archivo principal)
- Duración: ~5-15 minutos (según tamaño)

### Paso 2: Partition (para MLD)

```powershell
docker run -t -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-partition /data/mexico-251010.osrm
```

**Salida:**
- `mexico-251010.osrm.partition`
- `mexico-251010.osrm.cells`
- `mexico-251010.osrm.cell_metrics`
- Duración: ~10-30 minutos

### Paso 3: Customize (para MLD)

```powershell
docker run -t -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-customize /data/mexico-251010.osrm
```

**Salida:**
- `mexico-251010.osrm.mldgr`
- Duración: ~5-15 minutos

### ⚠️ IMPORTANTE: No Borrar Archivos .osrm

Los archivos generados **deben mantenerse** para ejecutar el servidor:

```
✅ MANTENER TODOS ESTOS ARCHIVOS:
mexico-251010.osrm
mexico-251010.osrm.cell_metrics
mexico-251010.osrm.cells
mexico-251010.osrm.cnbg
mexico-251010.osrm.cnbg_to_ebg
mexico-251010.osrm.datasource_names
mexico-251010.osrm.ebg
mexico-251010.osrm.ebg_nodes
mexico-251010.osrm.edges
mexico-251010.osrm.enw
mexico-251010.osrm.fileIndex
mexico-251010.osrm.geometry
mexico-251010.osrm.icd
mexico-251010.osrm.maneuver_overrides
mexico-251010.osrm.mldgr          ← Crítico para MLD
mexico-251010.osrm.names
mexico-251010.osrm.nbg_nodes
mexico-251010.osrm.partition       ← Crítico para MLD
mexico-251010.osrm.properties
mexico-251010.osrm.ramIndex
mexico-251010.osrm.restrictions
mexico-251010.osrm.timestamp
mexico-251010.osrm.tld
mexico-251010.osrm.tls
mexico-251010.osrm.turn_duration_penalties
mexico-251010.osrm.turn_penalties_index
mexico-251010.osrm.turn_weight_penalties
```

---

## Ejecución del Servidor OSRM

### Comando Básico

```powershell
docker run -t -i -p 5000:5000 -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm
```

**Parámetros:**
- `-t -i`: Modo interactivo con terminal
- `-p 5000:5000`: Mapea puerto 5000 del contenedor al host
- `--algorithm mld`: Usa Multi-Level Dijkstra
- `/data/mexico-251010.osrm`: Archivo procesado

### Verificar que Funciona

```powershell
# Test simple con curl
curl "http://localhost:5000/route/v1/driving/-110.31,24.14;-110.29,24.16?overview=false"
```

**Respuesta esperada:**
```json
{
  "code": "Ok",
  "routes": [{
    "distance": 4231.5,
    "duration": 305.2
  }],
  "waypoints": [...]
}
```

### Ejecutar en Background (opcional)

```powershell
# Con -d (detached)
docker run -d -p 5000:5000 -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm

# Ver logs
docker logs <container_id>

# Detener
docker stop <container_id>
```

---

## Endpoints y Uso

### 1. `/route` - Calcular Ruta

**Uso principal en el proyecto**: Obtener distancia y duración entre puntos.

```http
GET http://localhost:5000/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false
```

**Ejemplo:**
```powershell
curl "http://localhost:5000/route/v1/driving/-110.31,24.14;-110.29,24.16?overview=false"
```

**Parámetros útiles:**
- `overview=false`: No retorna geometría (más rápido)
- `steps=false`: No retorna instrucciones turn-by-turn
- `alternatives=false`: Solo mejor ruta

**Respuesta:**
```json
{
  "code": "Ok",
  "routes": [{
    "distance": 4231.5,      // metros
    "duration": 305.2,       // segundos
    "legs": [...]
  }]
}
```

### 2. `/nearest` - Punto Más Cercano

Busca el nodo de la red vial más cercano a coordenadas dadas.

```http
GET http://localhost:5000/nearest/v1/driving/{lon},{lat}
```

**Ejemplo:**
```powershell
curl "http://localhost:5000/nearest/v1/driving/-110.31,24.14"
```

**Uso en el proyecto:** Validar que coordenadas estén en la red vial.

### 3. `/table` - Matriz de Distancias

Calcula todas las distancias entre múltiples puntos (many-to-many).

```http
GET http://localhost:5000/table/v1/driving/{coordinates}
```

**Ejemplo:**
```powershell
curl "http://localhost:5000/table/v1/driving/-110.31,24.14;-110.29,24.16;-110.28,24.15"
```

**Respuesta:**
```json
{
  "durations": [
    [0, 305.2, 412.1],
    [305.2, 0, 201.3],
    [412.1, 201.3, 0]
  ]
}
```

**Nota:** En este proyecto usamos principalmente `/route` con llamadas individuales.

---

## Integración con Python

### Módulo Principal: `src/getrouteOSMR.py`

```python
import requests
import polyline

OSRM_URL = "http://localhost:5000"

def get_route_details(origin, waypoints):
    """
    Calcula ruta desde origin hasta waypoints usando OSRM.
    
    Args:
        origin: tuple (lat, lon)
        waypoints: lista de tuples [(lat1, lon1), (lat2, lon2), ...]
    
    Returns:
        dict con 'distance' (m), 'duration' (s), 'geometry', 'legs'
        o None si hay error
    """
    # Convertir a formato lon,lat (OSRM usa lon,lat no lat,lon)
    coords = f"{origin[1]},{origin[0]}"
    for wp in waypoints:
        coords += f";{wp[1]},{wp[0]}"
    
    url = f"{OSRM_URL}/route/v1/driving/{coords}?overview=full&geometries=polyline"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') != 'Ok':
            return None
        
        route = data['routes'][0]
        return {
            'distance': route['distance'],  # metros
            'duration': route['duration'],  # segundos
            'geometry': route['geometry'],  # polyline encoded
            'legs': route['legs']
        }
    except Exception as e:
        print(f"OSRM error: {e}")
        return None
```

### Ejemplo de Uso

```python
from src.getrouteOSMR import get_route_details

# Calcular ruta: restaurante → cliente
restaurant = (24.1440, -110.3115)  # (lat, lon)
customer = (24.1560, -110.2980)

route = get_route_details(restaurant, [customer])

if route:
    print(f"Distancia: {route['distance']/1000:.2f} km")
    print(f"Duración: {route['duration']/60:.1f} min")
else:
    print("No se encontró ruta")
```

### Manejo de Errores

El código implementa fallback estratégico:

```python
# 1. Intentar OSRM
route = get_route_details(origin, waypoints)

# 2. Si falla, usar distancia euclidiana (fallback)
if route is None:
    distance_km = haversine(origin, waypoints[0])
    # Estimar duración: 30 km/h promedio en ciudad
    duration_sec = (distance_km / 30) * 3600
```

**Casos de fallback:**
- Servidor OSRM no disponible
- Coordenadas fuera de la red vial
- Timeout en la request

---

## Troubleshooting

### Problema 1: "Empty reply from server"

**Síntomas:**
```python
curl: (52) Empty reply from server
```

**Causas:**
1. El contenedor Docker no está corriendo
2. Puerto incorrecto
3. Archivos .osrm corruptos

**Soluciones:**
```powershell
# Verificar contenedor
docker ps

# Reiniciar servidor OSRM
docker stop <container_id>
docker run -t -i -p 5000:5000 -v C:\path:/data osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm

# Verificar puerto
netstat -an | findstr 5000
```

### Problema 2: "NoRoute" en respuesta

**Síntomas:**
```json
{"code": "NoRoute"}
```

**Causas:**
- Coordenadas fuera del área cubierta por .osm.pbf
- Coordenadas en el mar o áreas sin carreteras
- Islas o regiones desconectadas

**Soluciones:**
```python
# Validar coordenadas con /nearest
response = requests.get(f"http://localhost:5000/nearest/v1/driving/{lon},{lat}")
# Si la distancia al nodo más cercano es >1km, coordenada problemática

# Usar fallback euclidiano
if route is None:
    use_euclidean_distance()
```

### Problema 3: Servidor lento o timeouts

**Síntomas:**
- Requests tardan >5 segundos
- Timeouts frecuentes

**Causas:**
- Archivo .osm.pbf muy grande (todo México)
- RAM insuficiente
- Algoritmo CH en lugar de MLD

**Soluciones:**
1. Usar extracto regional más pequeño (solo BCS)
2. Aumentar RAM del contenedor Docker
3. Verificar algoritmo: `--algorithm mld`

### Problema 4: Archivos .osrm faltantes

**Síntomas:**
```
[error] Could not open mexico-251010.osrm.partition
```

**Causa:**
- Archivos .osrm borrados accidentalmente
- Preprocesamiento incompleto

**Solución:**
```powershell
# Reprocesar desde cero
docker run -t -v C:\path:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/mexico-251010.osm.pbf
docker run -t -v C:\path:/data osrm/osrm-backend osrm-partition /data/mexico-251010.osrm
docker run -t -v C:\path:/data osrm/osrm-backend osrm-customize /data/mexico-251010.osrm
```

### Problema 5: Docker no encuentra el volumen

**Síntomas:**
```
Error: No such file or directory
```

**Causa:**
- Ruta con espacios o caracteres especiales
- Permisos insuficientes en Windows

**Soluciones:**
```powershell
# Usar comillas dobles
docker run -t -v "C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data" ...

# En Windows, asegurarse de compartir la unidad en Docker Desktop:
# Settings → Resources → File Sharing → Agregar C:\
```

---

## Perfiles de Routing

OSRM soporta diferentes perfiles (`.lua` scripts) que definen velocidades, restricciones y costos.

### Perfiles Incluidos en la Imagen Docker

1. **`car.lua`** (usado en este proyecto)
   - Velocidades típicas de automóviles
   - Respeta sentidos de vialidad
   - Penaliza giros en U

2. **`bicycle.lua`**
   - Velocidades de bicicleta
   - Permite ciclovías

3. **`foot.lua`**
   - Velocidades peatonales
   - Permite aceras y senderos

### Personalizar Perfil (opcional)

Para modificar velocidades o restricciones:

1. Copiar perfil base:
```powershell
docker cp <container_id>:/opt/car.lua ./custom_car.lua
```

2. Editar `custom_car.lua` (cambiar velocidades, etc.)

3. Usar en extract:
```powershell
docker run -t -v C:\path:/data osrm/osrm-backend osrm-extract -p /data/custom_car.lua /data/mexico-251010.osm.pbf
```

**En este proyecto usamos el perfil `car.lua` sin modificaciones.**

---

## Comparación con Otras Opciones

### OSRM vs Google Maps API

| Característica | OSRM (Docker) | Google Maps API |
|----------------|---------------|-----------------|
| Costo | Gratis | Pago después de quota |
| Límite de requests | Sin límite | ~40,000/mes gratis |
| Velocidad | <50ms local | ~200-500ms red |
| Datos | OpenStreetMap | Google propietario |
| Offline | ✅ Sí | ❌ No |
| Reproducibilidad | ✅ Total | ⚠️ Cambia con el tiempo |
| Setup inicial | ⚠️ Complejo | ✅ Simple (API key) |

### OSRM vs Mapbox Directions

Similar a Google Maps pero basado en OSM. OSRM es preferible para investigación por reproducibilidad.

### OSRM vs Graphhopper

Ambos usan OSM, pero Graphhopper requiere Java. OSRM con Docker es más ligero.

---

## Métricas y Performance

### Tiempos de Preprocesamiento (México completo)

- **Extract**: ~12 minutos
- **Partition**: ~25 minutos
- **Customize**: ~8 minutos
- **Total**: ~45 minutos (una sola vez)

### Tiempos de Query

- **Single route**: 10-50 ms
- **Multi-waypoint route** (5 puntos): 50-150 ms
- **Table query** (10x10): 100-300 ms

### Uso de Recursos

- **RAM**: ~2-3 GB con México completo cargado
- **Disco**: ~4 GB (.osm.pbf + .osrm files)
- **CPU**: 1 core suficiente para servidor, 4+ cores recomendado para preprocesamiento

---

## Reproducibilidad y Versionado

### Datos Fijos

Para garantizar reproducibilidad:

1. **Fijar fecha de descarga OSM**: `mexico-251010.osm.pbf`
2. **Versionar archivos .osrm**: Commit hash + fecha
3. **Documentar versión OSRM**: `osrm/osrm-backend:v5.27.1`

### Metadata Recomendada

```yaml
# osrm_metadata.yml
osm_file: mexico-251010.osm.pbf
osm_source: Geofabrik
osm_download_date: 2025-10-25
osrm_version: v5.27.1
algorithm: MLD
profile: car.lua
preprocessing_date: 2025-10-26
total_nodes: ~45M
total_edges: ~95M
```

---

## Referencias

### Documentación Oficial

- OSRM Backend: https://github.com/Project-OSRM/osrm-backend
- OSRM API Documentation: http://project-osrm.org/docs/v5.24.0/api/
- Docker Hub: https://hub.docker.com/r/osrm/osrm-backend

### Papers y Algoritmos

- Geisberger et al. (2008): "Contraction Hierarchies"
- Luxen & Vetter (2011): "Real-time routing with OpenStreetMap data"
- OSRM MLD: https://github.com/Project-OSRM/osrm-backend/wiki/Multi-Level-Dijkstra

### Fuentes de Datos OSM

- Geofabrik: https://download.geofabrik.de/
- BBBike Extract: https://extract.bbbike.org/
- OpenStreetMap: https://www.openstreetmap.org/

---

## Comandos de Referencia Rápida

```powershell
# 1. Preprocesamiento (una sola vez)
docker run -t -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/mexico-251010.osm.pbf
docker run -t -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-partition /data/mexico-251010.osrm
docker run -t -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-customize /data/mexico-251010.osrm

# 2. Servidor OSRM (cada sesión de trabajo)
docker run -t -i -p 5000:5000 -v C:\Users\alan_\Documents\GitHub\MDRP-BCS-code:/data osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm

# 3. Test rápido
curl "http://localhost:5000/route/v1/driving/-110.31,24.14;-110.29,24.16?overview=false"

# 4. Ver logs (si corre en background)
docker logs <container_id>

# 5. Detener servidor
docker stop <container_id>
```

---

**Última actualización:** Octubre 27, 2025  
**Versión del documento:** 1.0  
**Autor:** Alan Sama (MDRP-BCS Project)
