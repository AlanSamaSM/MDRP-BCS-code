# Simulación y Optimización del Despacho de Órdenes para Entrega de Comida en La Paz, BCS

[![Status](https://img.shields.io/badge/Status-Active%20Development-green)]() 
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()
[![Docker](https://img.shields.io/badge/Docker-Required-important)]()
[![License](https://img.shields.io/badge/License-MIT-blue)]()

Este repositorio contiene la implementación reproducible del Problema de Enrutamiento de Entrega de Comida (MDRP) de Reyes et al. (2018). El proyecto simula y optimiza el despacho de órdenes de comida en La Paz, BCS usando dos políticas:

1. **First-Come, First-Served (FCFS):** Política base donde las órdenes se asignan al repartidor disponible más cercano
2. **Rolling Horizon (RH):** Heurística de optimización que agrupa órdenes y planifica rutas periódicamente


## Requisitos Previos

- **Python 3.8+** (Probado con 3.12)
- **Docker** (Requerido para OSRM - v20.10+)
- **pip** con paquetes de `requirements.txt`

### Paquetes Principales
- pandas, numpy (datos y cálculos)
- folium (mapas interactivos)
- scipy, statsmodels, pingouin (análisis estadístico)
- requests (cliente HTTP para OSRM)
- matplotlib (visualizaciones)

### Servidor OSRM
El proyecto requiere un servidor OSRM local corriendo en `localhost:5000`. Se incluyen datos OSM precompilados para La Paz, BCS.

## Instalación y Setup

### 1. Clonar Repositorio
```bash
git clone https://github.com/AlanSamaSM/MDRP-BCS-code.git
cd MDRP-BCS-code
```

### 2. Instalar Dependencias Python
```bash
pip install -r requirements.txt
pip install statsmodels pingouin  # Análisis estadístico (opcional pero recomendado)
```

### 3. Iniciar Servidor OSRM Local

**Opción A: Con mapa de BCS optimizado (RECOMENDADO)**
```bash
docker run -d -p 5000:5000 \
  -v "${PWD}/osrm_data:/data" \
  osrm/osrm-backend:v5.26.0 \
  osrm-routed --algorithm mld /data/bcs-latest.osrm
```

**Opción B: Con mapa de México completo (más lento)**
```bash
docker run -d -p 5000:5000 \
  -v "${PWD}/osrm_data:/data" \
  osrm/osrm-backend:v5.26.0 \
  osrm-routed --algorithm mld /data/mexico-latest.osrm
```

### 4. Verificar que OSRM está activo
```bash
curl http://localhost:5000/status
# Debería retornar: {"status":0,"message":"OK"}
```

## Reproducción de Resultados

### ⚡ Ejecución Rápida (Pipeline Completo)

```bash
python scripts/generate_results.py
```

Este comando ejecuta automáticamente:
1. ✓ Generación de 1,038 órdenes sintéticas (2-5km, realistas)
2. ✓ Simulación FCFS
3. ✓ Simulación Rolling Horizon con bundling
4. ✓ Cálculo de KPIs (24 métricas)
5. ✓ Análisis estadístico (Mann-Whitney U, Z-test)
6. ✓ Generación de reportes

**Tiempo estimado:** 30-60 minutos (depende de # órdenes)

### 📊 Análisis Estadístico (Ya Completado)

Para ejecutar solo el análisis con datos existentes:
```bash
python scripts/statistical_analysis.py
python scripts/plot_statistical_results.py  # Genera gráficos
```

**Resultados disponibles:**
- `STATISTICAL_REPORT.md` - Reporte detallado
- `ANALYSIS_SUMMARY.md` - Resumen ejecutivo  
- `results/statistical_comparison.png` - Gráficos comparativos
- `results/statistical_report.html` - Dashboard interactivo

### 🗺️ Visualización Interactiva

```bash
# 1. Dashboard de cobertura OSM
python scripts/plot_osm_coverage.py
# Abre: results/maps/osm_coverage_map.html

# 2. Dashboard de rutas en tiempo real
# Abre: osrm_dashboard.html

# 3. Generar índice de bundles completos (DESPUÉS de RH)
python scripts/generate_complete_bundles_index.py
# Abre: results/maps/rh/complete_bundles_index.html
```

#### 🆕 Mapas de Bundles Completos

**Nueva funcionalidad:** Cada vez que se completa un bundling en Rolling Horizon, se genera automáticamente un mapa COMPLETO que incluye:

- ✓ Base del courier (azul - warehouse icon)
- ✓ Ruta completa desde base → restaurantes → clientes → base
- ✓ Restaurantes (rojo - utensils icon)
- ✓ Clientes (verde - pin icon)
- ✓ Información del bundle (# órdenes, distancia, tiempo)

**Ubicación:** `results/maps/rh/complete_bundles/`
- Estructura: `courier_<ID>_bundle_<N>.html`
- Ejemplo: `courier_5_bundle_003.html`

**Acceso rápido:** Abre `results/maps/rh/complete_bundles_index.html` para ver un índice navegable de todos los bundles

### 🔧 Ejecución Manual (Avanzado)

```bash
# 1. Generar datos sintéticos
python scripts/make_synth_orders.py

# 2. Ejecutar FCFS
python scripts/run_fcfs_instance.py data/synthetic_lapaz_orders_limited.csv

# 3. Ejecutar Rolling Horizon
python scripts/run_synth_instance.py data/synthetic_lapaz_orders_limited.csv

# 4. Calcular KPIs
python scripts/generate_results.py --analyze-only
```

## 📈 Resultados Generados

Tras ejecutar el pipeline, encontrarás:

### Datos Crudos (CSV)
```
results/raw/
├── synthetic_lapaz_orders_limited_fcfs_results.csv     (1,038 órdenes)
├── synthetic_lapaz_orders_limited_fcfs_couriers.csv    (58 couriers)
├── synthetic_lapaz_orders_limited_rh_results.csv       (1,038 órdenes)
└── synthetic_lapaz_orders_limited_rh_couriers.csv      (58 couriers)
```

### Reportes y Análisis
```
results/
├── kpi_comparison.csv                  (24 KPIs comparados)
├── statistical_comparison.png          (Gráficos box-plot)
├── statistical_report.html             (Dashboard interactivo)
└── maps/
    ├── osm_coverage_map.html          (Cobertura del OSM)
    │
    ├── 📁 fcfs/                        (Política FCFS)
    │   ├── delivery_01.html → delivery_10.html   (10 primeras rutas)
    │   └── complete_bundles/          (¡Solo si se ejecuta FCFS con bundling)
    │
    ├── 📁 rh/                          (Política Rolling Horizon) ⭐ NUEVO
    │   ├── delivery_01.html → delivery_10.html   (10 primeras rutas)
    │   │
    │   ├── 📁 complete_bundles/        ⭐ NUEVO: Todas las rutas completas
    │   │   ├── courier_1_bundle_001.html
    │   │   ├── courier_1_bundle_002.html
    │   │   ├── courier_2_bundle_001.html
    │   │   ├── ... (TODOS los bundles completados)
    │   │   └── complete_bundles_index.html  ⭐ ÍNDICE NAVEGABLE
    │   │
    │   └── ... (otros mapas)
    │
    └── ... (otros visualizadores)
```

### Reportes Markdown
```
STATISTICAL_REPORT.md                   (Análisis detallado)
ANALYSIS_SUMMARY.md                     (Resumen ejecutivo)
osm_coverage_analysis.md                (Análisis de cobertura)
```

### Métricas Calculadas (24 KPIs)

**Calidad de Servicio:**
| Métrica | FCFS | RH | Mejora |
|---------|------|-----|--------|
| Avg Click-to-Door | 9.5 min | 17.3 min | -6.73% |
| Avg Ready-to-Door | -2.5 min | 4.9 min | -7.37% |
| % Órdenes No Entregadas | Variable | Variable | - |

**Eficiencia Operativa:**
| Métrica | FCFS | RH |
|---------|------|-----|
| Órdenes/Courier-Hora | - | - |
| Bundles/Hora | - | - |
| Avg Bundle Size | - | 1.52 |
| % Multi-Bundles | **0%** | **52.6%** |

**Costos:**
| Métrica | FCFS | RH |
|---------|------|-----|
| Costo por Orden | - | - |
| Distancia Total (km) | - | - |
| Utilización Courier (%) | - | - |

**Significancia Estadística:**
- Click-to-Door: p < 0.0001, Cliff's δ = 0.0673 ✓
- Ready-to-Door: p < 0.0001, Cliff's δ = 0.0737 ✓
- Multi-Bundles: p < 0.0001 ✓

## 📁 Estructura del Proyecto

```
MDRP-BCS-code/
├── 📊 Reportes (Nivel Raíz)
│   ├── STATISTICAL_REPORT.md          ← Análisis estadístico detallado
│   ├── ANALYSIS_SUMMARY.md            ← Resumen ejecutivo de resultados
│   ├── osm_coverage_analysis.md       ← Análisis de cobertura del OSM
│   ├── README.md                      ← Este archivo
│   └── requirements.txt               ← Dependencias Python
│
├── 📁 data/                           # Datos de entrada y sintéticos
│   ├── couriers.csv                   # Definición base de repartidores
│   ├── restaurants.csv                # Restaurantes de referencia
│   ├── la_paz_restaurants.geojson     # Restaurants georeferenciados
│   ├── synthetic_lapaz_orders_limited.csv  # Órdenes sintéticas (1,038)
│   └── delivery_jl.parquet            # Datos de entrega
│
├── 🗺️  osrm_data/                    # Datos geoespaciales
│   ├── bcs-latest.osm.pbf            # Mapa OSM optimizado (14 MB)
│   ├── bcs-latest.osrm                # Archivo compilado OSRM
│   └── bcs-latest.osrm.*              # Índices y recursos OSRM
│
├── 📈 results/                        # Resultados de simulaciones
│   ├── raw/                           # Datos crudos CSV
│   │   ├── *_fcfs_results.csv        # Órdenes FCFS (1,038)
│   │   ├── *_fcfs_couriers.csv       # Couriers FCFS (58)
│   │   ├── *_rh_results.csv          # Órdenes RH (1,038)
│   │   └── *_rh_couriers.csv         # Couriers RH (58)
│   ├── maps/                          # Visualizaciones
│   │   ├── osm_coverage_map.html     # Mapa de cobertura OSM
│   │   ├── courier[1-5]_route[1-6].html  # Rutas individuales (30)
│   │   └── mdrp_simulation.html      # Dashboard principal
│   ├── kpi_comparison.csv             # Tabla de KPIs
│   ├── statistical_comparison.png     # Gráficos comparativos
│   └── statistical_report.html        # Dashboard interactivo
│
├── 🐍 scripts/                        # Scripts de ejecución
│   ├── generate_results.py            # 🔴 MAIN: Orquestador del pipeline
│   ├── make_synth_orders.py           # Generador de órdenes sintéticas
│   ├── run_fcfs_instance.py           # Ejecutor FCFS
│   ├── run_synth_instance.py          # Ejecutor Rolling Horizon
│   ├── run_grubhub_instance.py        # Ejecutor dataset Grubhub (TODO)
│   ├── run_lade_instance.py           # Ejecutor dataset LaDe (TODO)
│   ├── plot_synth_orders.py           # Visualizador de órdenes
│   ├── plot_osm_coverage.py           # Generador mapa cobertura OSM
│   ├── plot_statistical_results.py    # Generador gráficos estadísticos
│   ├── statistical_analysis.py        # Análisis estadístico
│   ├── test_osrm.py                   # Test conexión OSRM
│   └── extraccion_restaurantes.py     # Extractor de datos (setup)
│
├── 💻 src/                            # Código fuente principal
│   ├── main.py                        # Simulador principal
│   ├── bundling.py                    # Algoritmos de bundling
│   ├── asignaciontentativa.py         # Asignación de órdenes
│   ├── getrouteOSMR.py                # Cliente OSRM
│   ├── config.py                      # Parámetros globales
│   ├── parquet.py                     # Utilidades Parquet
│   ├── coord_transform.py             # Transformaciones de coordenadas
│   ├── synth_loader.py                # Cargador datos sintéticos
│   ├── grubhub_loader.py              # Cargador Grubhub (TODO)
│   ├── lade_loader.py                 # Cargador LaDe (TODO)
│   ├── lade_metrics.py                # Métricas LaDe
│   ├── restaurantsList.py             # Gestión de restaurantes
│   └── couriersList.py                # Gestión de couriers
│
├── 🎨 Visualizaciones
│   ├── osrm_dashboard.html            # Dashboard interactivo (Leaflet.js)
│   ├── mdrp_simulation.html           # Simulación visual
│   └── maps/courier*_route*.html      # Rutas individuales
│
├── 📚 Documentación
│   ├── docs/
│   │   ├── osrm_manual.md             # Manual técnico OSRM
│   │   ├── project_pseudocode.txt     # Pseudocódigo del proyecto
│   │   └── DOCKER_EXPLANATION.md      # Arquitectura Docker
│   └── mdrplib-master/                # Biblioteca MDRP referencia
│
└── 🗂️  Otros
    ├── cache/                         # Caché de búsquedas
    ├── __pycache__/                   # Archivos compilados Python
    └── .git/                          # Repositorio Git
```

### Archivos Clave

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `scripts/generate_results.py` | Pipeline completo | ✓ Funcional |
| `src/main.py` | Simulador | ✓ Funcional |
| `src/bundling.py` | Agrupamiento RH | ✓ Funcional |
| `osrm_dashboard.html` | Dashboard interactivo | ✓ Funcional |
| `scripts/statistical_analysis.py` | Análisis estadístico | ✓ Completo |
| `scripts/run_grubhub_instance.py` | Dataset Grubhub | 🟡 Por hacer |
| `scripts/run_lade_instance.py` | Dataset LaDe | 🟡 Por hacer |

## 📚 Documentación

### Guías Disponibles
- **`STATISTICAL_REPORT.md`** - Análisis estadístico completo de resultados
- **`ANALYSIS_SUMMARY.md`** - Resumen ejecutivo con conclusiones
- **`osm_coverage_analysis.md`** - Análisis de cobertura geográfica del OSM
- **`docs/osrm_manual.md`** - Manual técnico del servidor OSRM
- **`docs/project_pseudocode.txt`** - Pseudocódigo del simulador
- **`docs/DOCKER_EXPLANATION.md`** - Explicación de arquitectura Docker

### Paper de Referencia
- **Reyes et al. (2018)** - "The Meal Delivery Routing Problem" (`mdrplib-master/MDRP reyes 2018.pdf`)

### Dashboards Interactivos
- **`osrm_dashboard.html`** - Mapa de La Paz con rutas en tiempo real (Leaflet.js)
- **`results/statistical_report.html`** - Reporte estadístico interactivo (Chart.js)
- **`maps/osm_coverage_map.html`** - Visualización de cobertura del OSM

