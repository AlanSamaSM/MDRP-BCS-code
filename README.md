# Simulación y Optimización del Despacho de Órdenes para Entrega de Comida - Enfoque Rolling Horizon

Este repositorio contiene la implementación del **algoritmo Rolling Horizon (RH)** para el Problema de Enrutamiento de Entregas de Comida (MDRP - Meal Delivery Routing Problem) en La Paz, Baja California Sur, basado en la investigación de Reyes et al. (2018).

## Descripción del Proyecto

El proyecto implementa un **simulador multi-agente basado en eventos** que modela dinámicamente el sistema de entrega de comida utilizando:

- **Bundling de órdenes:** Agrupación inteligente de múltiples órdenes por restaurante según su disponibilidad y geometría espacial
- **Asignación de dos fases:** Asignación tentativa seguida de un compromiso finalizador (two-stage commitment)
- **Optimización de rutas:** Integración con servidor OSRM para cálculo de distancias y tiempos reales
- **Horizonte rodante:** Replaneamiento periódico de bundles y asignaciones de couriers

El objetivo es maximizar la eficiencia operativa mientras se mantiene la calidad del servicio a través de métricas de experiencia de cliente según Reyes et al. (2018).

## Requisitos Previos

*   Python 3.8 o superior
*   Docker (para ejecutar servidor OSRM local)
*   Un servidor OSRM local corriendo en `localhost:5000`. El proyecto incluye archivos `.osrm` precompilados para La Paz/BCS.

## Instalación

1.  Clona este repositorio:
    
    git clone https://github.com/AlanSamaSM/MDRP-BCS-code.git
    cd MDRP-BCS-code
    

2.  Instala las dependencias de Python:
    
    pip install -r requirements.txt


3.  Inicia el servidor OSRM local (requerido para ruteo):
    
    docker run -d -p 5000:5000 -v "${PWD}/osrm_data:/data" osrm/osrm-backend osrm-routed --algorithm ch /data/bcs-latest.osrm
    

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

Si solo quieres recalcular los KPIs:

python scripts/generate_results.py --analyze-only


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

## Visualización de Resultados

Los resultados de las simulaciones incluyen:

- **Mapas interactivos de rutas:** Visualización de cada entrega con rutas detalladas en `results/maps/{policy_name}/delivery_XX.html`
- **Índice de bundles completos:** Vista general de todos los bundles en `results/maps/{policy_name}/complete_bundles_index.html`
- **Comparación de KPIs:** Tabla comparativa en `results/kpi_comparison.csv`

Para visualizar un mapa específico, abre el archivo HTML en tu navegador web.

## Algoritmo de Rolling Horizon - Resumen Técnico

### Proceso de Simulación

1. **Horizonte de asignación (Δt):** Se procesan eventos cada cierto intervalo de tiempo
2. **Generación de bundles:** Para cada restaurante se crean bundles de órdenes listas
3. **Asignación tentativa:** Se asignan bundles a couriers según scoring
4. **Compromiso finalizador:** Se valida viabilidad y se confirman asignaciones
5. **Optimización de rutas:** Se calculan rutas reales usando OSRM

### Parámetros Configurables

Todos los parámetros se definen en `src/config.py`:

- `ASSIGNMENT_HORIZON`: Intervalo de replaneamiento (minutos)
- `MAX_CLICK_TO_DOOR`: Objetivo máximo de click-to-door (minutos)
- `SERVICE_TIME`: Tiempo de servicio en restaurante (segundos)
- `PAY_PER_ORDER`: Compensación por orden entregada
- `MIN_PAY_PER_HOUR`: Compensación mínima por hora

## Documentación Adicional

- **Manual técnico de OSRM:** Ver `docs/osrm_manual.md` para detalles de preprocesamiento, endpoints y troubleshooting.
- **Paper de referencia:** Reyes et al. (2018) - "The Meal Delivery Routing Problem"
- **Dashboard OSRM:** Ver `docs/osrm_dashboard.html` para visualizar el estado del servidor

## Contribuciones

Este proyecto es parte de una investigación académica. Para preguntas o sugerencias, contacta al autor.

## Licencia

[Especificar licencia]

## Autor

Alan Sama
Instituto Tecnológico de La Paz (ITLP)