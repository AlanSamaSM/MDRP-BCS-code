# Simulación y Optimización del Despacho de Órdenes para Entrega de Comida en La Paz, BCS

Este repositorio contiene el código fuente y los experimentos para la tesis de optimización de despacho de órdenes en sistemas de entrega de comida. El proyecto implementa un simulador para el Problema de Enrutamiento de Entrega de Comida (MDRP) y compara dos políticas de asignación de repartidores:

1.  **First-Come, First-Served (FCFS):** Una política base simple donde las órdenes se asignan al repartidor disponible más cercano a medida que están listas.
2.  **Rolling Horizon (RH):** Una heurística de optimización que agrupa (bundle) órdenes y planifica rutas en intervalos de tiempo periódicos para mejorar la eficiencia.

El objetivo es demostrar la mejora en la calidad del servicio y la eficiencia operativa del enfoque RH sobre FCFS utilizando un conjunto de datos sintético basado en la ciudad de La Paz, BCS.

## Requisitos Previos

*   Python 3.8 o superior
*   Docker (para ejecutar servidor OSRM local)
*   Un servidor OSRM local corriendo en `localhost:5000`. El proyecto incluye archivos `.osrm` precompilados para La Paz.

## Instalación

1.  Clona este repositorio:
    ```bash
    git clone https://github.com/AlanSamaSM/MDRP-BCS-code.git
    cd MDRP-BCS-code
    ```

2.  Instala las dependencias de Python:
    ```bash
    pip install -r requirements.txt
    ```

3.  Inicia el servidor OSRM local (requerido para ruteo):
    ```bash
    docker run -d -p 5000:5000 -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm
    ```
    
    Para Windows PowerShell:
    ```powershell
    docker run -d -p 5000:5000 -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/mexico-251010.osrm
    ```

## Reproducción de Resultados

### Pipeline Completo (Recomendado)

Para generar los resultados comparativos presentados en la tesis, ejecuta el pipeline completo:

```bash
python scripts/generate_results.py
```

Este script realizará automáticamente los siguientes pasos:
1.  Generará el conjunto de datos de órdenes sintéticas (`data/synthetic_lapaz_orders_limited.csv`).
2.  Ejecutará la simulación para la política **FCFS**.
3.  Ejecutará la simulación para la política **Rolling Horizon (RH)**.
4.  Calculará y comparará los KPIs de ambas políticas.
5.  Generará los archivos de resultados en la carpeta `results/`.

### Solo Análisis (sin ejecutar simulaciones)

Si ya ejecutaste las simulaciones y solo quieres recalcular los KPIs:

```bash
python scripts/generate_results.py --analyze-only
```

### Ejecución Manual de Políticas

También puedes ejecutar cada política individualmente:

```bash
# Generar datos sintéticos
python scripts/make_synth_orders.py

# Ejecutar FCFS
python scripts/run_fcfs_instance.py data/synthetic_lapaz_orders_limited.csv

# Ejecutar Rolling Horizon
python scripts/run_synth_instance.py data/synthetic_lapaz_orders_limited.csv

# Analizar resultados
python scripts/generate_results.py --analyze-only
```

## Resultados Generados

Tras ejecutar el pipeline, encontrarás los siguientes archivos en la carpeta `results/`:

*   `raw/synthetic_lapaz_orders_limited_fcfs_results.csv`: Resultados detallados de órdenes (FCFS)
*   `raw/synthetic_lapaz_orders_limited_fcfs_couriers.csv`: Métricas de repartidores (FCFS)
*   `raw/synthetic_lapaz_orders_limited_rh_results.csv`: Resultados detallados de órdenes (RH)
*   `raw/synthetic_lapaz_orders_limited_rh_couriers.csv`: Métricas de repartidores (RH)
*   `kpi_comparison.csv`: Tabla comparativa con todas las métricas clave de rendimiento

### Métricas Calculadas

El sistema calcula las siguientes métricas según Reyes et al. (2018):

**Calidad de Servicio:**
- Click-to-Door: promedio, P10, P50, P90, P95
- Ready-to-Pickup: promedio, P10, P50, P90
- Ready-to-Door: promedio, P10, P50, P90
- Click-to-Door Overage (sobretiempo respecto a target de 40 min)
- Porcentaje de órdenes no entregadas

**Eficiencia Operativa:**
- Órdenes por courier-hora
- Bundles por hora
- Tamaño promedio de bundle
- Distancia total recorrida (km)
- Utilización de couriers (% tiempo conduciendo)

**Costos:**
- Compensación total de couriers
- Costo por orden
- Ganancias de couriers por entregas
- Fracción de couriers con compensación mínima

## Estructura del Proyecto

```
MDRP-BCS-code/
├── data/                 # Datos de entrada
│   ├── couriers.csv                        # Definición de repartidores
│   ├── restaurants.csv                     # Restaurantes base
│   ├── la_paz_restaurants.geojson         # Restaurantes de La Paz
│   └── synthetic_lapaz_orders_limited.csv # Órdenes sintéticas generadas
├── osrm_data/            # Datos geoespaciales y OSRM
│   ├── mexico-251010.osm.pbf    # Mapa base de México (OpenStreetMap)
│   ├── mexico-251010.osrm       # Archivo OSRM principal
│   └── mexico-251010.osrm.*     # Archivos de índice y recursos OSRM
├── results/              # Resultados de simulaciones
│   ├── raw/              # Resultados detallados por política
│   ├── maps/             # Mapas de visualización de rutas
│   └── kpi_comparison.csv # Comparación final de métricas
├── scripts/              # Scripts de ejecución
│   ├── generate_results.py    # Orquestador principal del pipeline
│   ├── make_synth_orders.py   # Generador de órdenes sintéticas
│   ├── run_fcfs_instance.py   # Ejecutor de política FCFS
│   ├── run_synth_instance.py  # Ejecutor de política Rolling Horizon
│   ├── plot_synth_on_map.py   # Visualizador de órdenes en mapa
│   └── validate_datasets.py   # Validador de conjuntos de datos
├── src/                  # Código fuente principal
│   ├── main.py           # Simulador principal y clases de dominio
│   ├── bundling.py       # Algoritmos de agrupación de órdenes
│   ├── asignaciontentativa.py # Algoritmos de asignación
│   ├── getrouteOSMR.py   # Cliente OSRM y cálculo de rutas
│   ├── config.py         # Parámetros de configuración global
│   ├── synth_loader.py   # Cargador de datos sintéticos
│   ├── grubhub_loader.py # Cargador de benchmark Grubhub
│   └── lade_loader.py    # Cargador de benchmark LaDe
├── docs/                 # Documentación
│   └── project_pseudocode.txt # Pseudocódigo del proyecto
├── tests/                # Pruebas unitarias
├── README.md             # Este archivo
└── requirements.txt      # Dependencias de Python
```

## Visualización

Para visualizar las órdenes sintéticas generadas en un mapa interactivo:

```bash
python scripts/plot_synth_on_map.py data/synthetic_lapaz_orders_limited.csv
```

Esto generará un archivo HTML en `results/maps/` que puedes abrir en tu navegador.

## Documentación Adicional

- **Pseudocódigo del proyecto:** Ver `docs/project_pseudocode.txt` para una descripción detallada de la arquitectura y flujo del sistema.
- **Setup de OSRM en otra computadora:** Ver `README_OSRM_SETUP.md` para instrucciones de transferencia de archivos `.osrm` via USB u otras opciones.
- **Manual técnico de OSRM:** Ver `docs/osrm_manual.md` para detalles de preprocesamiento, endpoints y troubleshooting.
- **Paper de referencia:** Reyes et al. (2018) - "The Meal Delivery Routing Problem"

## Contribuciones

Este proyecto es parte de una tesis de maestría. Para preguntas o sugerencias, contacta al autor.

## Licencia

[Especificar licencia]

## Autor

Alan Sama
ITLP