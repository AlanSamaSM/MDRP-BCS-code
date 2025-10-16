# Simulación y Optimización del Despacho de Órdenes para Entrega de Comida en La Paz, BCS

Este repositorio contiene el código fuente y los experimentos para la tesis [**TU TÍTULO DE TESIS AQUÍ**]. El proyecto implementa un simulador para el Problema de Enrutamiento de Entrega de Comida (MDRP) y compara dos políticas de asignación de repartidores:

1.  **First-Come, First-Served (FCFS):** Una política base simple donde las órdenes se asignan al repartidor disponible más cercano a medida que están listas.
2.  **Rolling Horizon (RH):** Una heurística de optimización que agrupa (bundle) órdenes y planifica rutas en intervalos de tiempo periódicos para mejorar la eficiencia.

El objetivo es demostrar la mejora en la calidad del servicio y la eficiencia operativa del enfoque RH sobre FCFS utilizando un conjunto de datos sintético basado en la ciudad de La Paz, BCS.

## Requisitos Previos

*   Python 3.8 o superior
*   Un servidor OSRM local o acceso a uno. El proyecto está configurado para usar el servidor público de OSRM, pero se recomienda uno local para un rendimiento estable. Las instrucciones de configuración de OSRM se pueden encontrar [aquí](http://project-osrm.org/).

## Instalación

1.  Clona este repositorio:
    ```bash
    git clone [URL-DE-TU-REPOSITORIO]
    cd MDRP-BCS-code
    ```

2.  Instala las dependencias de Python:
    ```bash
    pip install -r requirements.txt
    ```

## Reproducción de Resultados

Para generar los resultados comparativos presentados en la tesis, ejecuta el siguiente script:

```bash
python scripts/generate_results.py
```

Este script realizará los siguientes pasos:
1.  Generará el conjunto de datos de órdenes sintéticas (`synthetic_lapaz_orders.csv`) si no existe.
2.  Ejecutará la simulación para la política **FCFS**.
3.  Ejecutará la simulación para la política **Rolling Horizon (RH)**.
4.  Generará los archivos de resultados en la carpeta `/results`, incluyendo:
    *   `fcfs_results.txt`: Tiempos de entrega detallados para FCFS.
    *   `rh_results.txt`: Tiempos de entrega detallados para RH.
    *   `kpi_comparison.csv`: Una tabla comparativa con las métricas clave de rendimiento (KPIs) de ambas políticas.

## Estructura del Proyecto

```
MDRP-BCS-code/
├── data/                 # Datos de entrada (restaurantes, repartidores, etc.)
├── results/              # Resultados generados por las simulaciones
├── scripts/              # Scripts para ejecutar experimentos y generar datos
│   ├── generate_results.py # Script principal para reproducir los resultados de la tesis
│   └── make_synth_orders.py  # Generador de órdenes sintéticas
├── src/                  # Código fuente principal de la simulación y algoritmos
│   ├── bundling.py       # Lógica para la agrupación de órdenes (bundling)
│   ├── getrouteOSMR.py   # Cliente para interactuar con el servidor OSRM
│   └── main.py           # Lógica central de la simulación
├── tests/                # Pruebas unitarias
├── README.md             # Este archivo
└── requirements.txt      # Dependencias de Python
```

## Scripts y Módulos Adicionales

*   `run_fcfs_instance.py`: Ejecuta una simulación solo con la política FCFS.
*   `run_synth_instance.py`: Ejecuta una simulación solo con la política RH.
*   `grubhub_loader.py` / `lade_loader.py`: Módulos para cargar datos de otros benchmarks (Grubhub, LaDe), no utilizados en el experimento principal de la tesis.