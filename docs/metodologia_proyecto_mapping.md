# Guía de Mapeo: Metodología → Código del Proyecto MDRP

**Documento de referencia para la redacción del Capítulo 7: Metodología**

Este documento mapea cada sección de la Metodología a los archivos de código, scripts y configuraciones correspondientes en el proyecto. Úsalo como guía para identificar qué archivos revisar al documentar cada componente metodológico.

---

## 1. Arquitectura del sistema de simulación

### 1.1 Componentes: simulador, OSRM, orquestación Docker

**Archivos a revisar:**
- `src/main.py` - Core del simulador, bucle principal de eventos
- `src/config.py` - Configuración global del sistema
- `docker-compose.yml` (si existe) - Orquestación de contenedores
- `README.md` - Instrucciones de setup del entorno

**Descripción técnica:**
- **Simulador:** Motor de eventos discretos implementado en Python 3.12
- **OSRM:** Contenedor Docker `osrm/osrm-backend:5.26.0` expuesto en `localhost:5000`
- **Orquestación:** Coordinación entre simulador Python y servidor OSRM vía HTTP

**Flujo de datos:**
1. Simulador genera eventos (orden lista, courier disponible)
2. Módulo de política (FCFS/RH) decide asignaciones
3. Llamadas a OSRM para calcular rutas/tiempos
4. Actualización de estado del sistema

---

### 1.2 Interfaces: API OSRM, formatos de intercambio

**Archivos a revisar:**
- `src/getrouteOSMR.py` - Cliente HTTP para OSRM, cache de consultas
- `cache/*.json` - Ejemplos de respuestas OSRM cacheadas

**Endpoints OSRM utilizados:**
```
GET http://localhost:5000/route/v1/driving/{lon1},{lat1};{lon2},{lat2}
```

**Formato de respuesta OSRM (extracto):**
```json
{
  "routes": [{
    "distance": 1234.5,      // metros
    "duration": 180.2,       // segundos
    "geometry": "encoded_polyline_string"
  }]
}
```

**Transformaciones de datos:**
- Coordenadas WGS84 (lon, lat) → Consulta OSRM → Distancia/Tiempo
- Cache: Tupla `(origen, destino)` → Resultado cacheado para evitar consultas repetidas

---

### 1.3 Modelo de eventos discretos

**Archivos a revisar:**
- `src/main.py` - Función `run_simulation()`, cola de eventos `order_queue`
- `src/synth_loader.py` - Creación de objetos `Order`, `Courier`, `Restaurant`

**Tipos de eventos principales:**
1. **OrderPlaced** (`placement_time`) - Nueva orden ingresa al sistema
2. **OrderReady** (`ready_time = placement_time + prep_time`) - Comida lista para pickup
3. **CourierAvailable** - Courier termina entrega y está libre
4. **OptimizationEpoch** (cada 5 min para RH) - Reoptimización de asignaciones
5. **PickupCompleted** - Courier recoge orden
6. **DeliveryCompleted** - Orden entregada al cliente

**Estructura de la cola de eventos:**
```python
order_queue = deque(sorted(orders, key=lambda o: o.placement_time))
```

**Ciclo de simulación (pseudocódigo):**
```python
current_time = START_TIME
while current_time < END_TIME:
    # Procesar órdenes listas
    ready_orders = [o for o in pending_orders if o.ready_time <= current_time]
    
    if FCFS_POLICY:
        for order in ready_orders:
            assign_to_nearest_courier(order)
    else:  # Rolling Horizon
        if current_time % OPTIMIZATION_FREQUENCY == 0:
            bundles = generate_bundles(ready_orders, lookahead_window)
            matching = solve_bipartite_matching(bundles, available_couriers)
            commit_assignments(matching)
    
    # Avanzar tiempo al siguiente evento
    current_time = next_event_time()
```

---

## 2. Preparación de la infraestructura de ruteo

### 2.1 Descarga y filtrado de red OSM de La Paz

**Archivos a revisar:**
- `data/map.osm` - Red vial de La Paz (extracto OSM)
- `scripts/download_osm.sh` (si existe) - Script de descarga

**Procedimiento documentado:**
1. Descarga desde **Geofabrik** o **Overpass API**:
   ```
   Región: Baja California Sur, México
   Bounding Box: [lon_min, lat_min, lon_max, lat_max] 
   # Coordenadas que cubren La Paz urbana
   ```

2. Filtrado de características:
   - Calles vehiculares (`highway=primary|secondary|tertiary|residential`)
   - Exclusión de senderos peatonales, ciclovías (a menos que courier use bicicleta)

3. Formato: `.osm` (XML) o `.osm.pbf` (binario comprimido)

---

### 2.2 Preprocesamiento en OSRM (extract/partition/customize)

**Archivos a revisar:**
- `osrm_data/*.osrm` - Archivos preprocesados por OSRM
- `scripts/prepare_osrm.sh` - Pipeline de preprocesamiento

**Pipeline OSRM (comandos):**
```bash
# 1. Extract: Parsear OSM y crear grafo
osrm-extract -p car.lua data/map.osm

# 2. Partition: Crear jerarquía de Contraction Hierarchies
osrm-partition data/map.osrm

# 3. Customize: Optimizar estructura para consultas
osrm-customize data/map.osrm
```

**Perfil vehicular (`car.lua`):**
- Velocidades por tipo de vía (ajustadas para motocicletas/bicicletas)
- Restricciones de giro
- Penalizaciones por tipo de superficie

**Salida:**
- Archivos `.osrm`, `.osrm.edges`, `.osrm.nodes`, etc.
- Tamaño típico: 50-200 MB para La Paz

---

### 2.3 Validación de cobertura de la red

**Archivos a revisar:**
- `scripts/validate_osm_coverage.py` (crear si no existe)
- `data/la_paz_restaurants.geojson` - Restaurantes mapeados

**Validación requerida:**
1. **Cobertura geográfica:** Verificar que todos los restaurantes y destinos de clientes caen dentro del polígono cubierto por `map.osm`
2. **Conectividad:** Confirmar que todos los nodos están en el componente conexo más grande
3. **Precisión de snapping:** Validar que coordenadas de restaurantes/clientes se mapean correctamente a nodos de la red

**Métricas de validación:**
- % de restaurantes alcanzables desde cualquier punto
- Distancia promedio de "snapping" (punto real → nodo OSM más cercano)

---

## 3. Generación de instancias sintéticas

### 3.1 Definición del polígono urbano de La Paz

**Archivos a revisar:**
- `scripts/make_synth_orders.py` - Líneas que definen `urban_polygon`

**Definición del polígono:**
```python
# Coordenadas aproximadas del área urbana de La Paz
urban_polygon = Polygon([
    (-110.35, 24.10),  # Noroeste
    (-110.28, 24.10),  # Noreste
    (-110.28, 24.12),  # Sureste
    (-110.35, 24.12),  # Suroeste
])
```

**Justificación:**
- Polígono definido para cubrir zona urbana densa
- Excluye áreas rurales periféricas con baja densidad de restaurantes

---

### 3.2 Calibración temporal inspirada en LaDe (Wu2023)

**Archivos a revisar:**
- `scripts/make_synth_orders.py` - Función `build_intensity_profile()`

**Parámetros LaDe calibrados:**
```python
MORNING_PEAK_HOUR = 9      # Pico de desayuno/almuerzo
EVENING_PEAK_HOUR = 17     # Pico de cena
MORNING_PEAK_INTENSITY = 0.15
EVENING_PEAK_INTENSITY = 0.35
BASELINE_INTENSITY = 0.05
```

**Distribución de arribos:**
- **Proceso de Poisson no homogéneo** con función de intensidad `λ(t)`
- Dos picos gaussianos superpuestos sobre baseline constante

**Generación de tiempos de llegada:**
```python
def sample_order_times(n_orders, start_time, end_time):
    intensities = build_intensity_profile(start_time, end_time)
    arrival_times = np.random.choice(time_bins, size=n_orders, p=intensities)
    return sorted(arrival_times)
```

---

### 3.3 Muestreo geográfico de restaurantes y destinos

**Archivos a revisar:**
- `scripts/make_synth_orders.py` - Función `sample_n_points_in_polygon()`
- `data/restaurants.csv` - Catálogo de 142 restaurantes reales

**Estrategia de muestreo:**

**Restaurantes (origen):**
- Muestreo de catálogo real con pesos proporcionales a popularidad/volumen histórico
- Distribución espacial: Concentración en centro urbano

**Destinos de clientes:**
- Muestreo uniforme dentro de `urban_polygon`
- Validación: Punto debe estar en calles accesibles (snapping a red OSM)

**Código relevante:**
```python
def sample_n_points_in_polygon(polygon, n):
    points = []
    while len(points) < n:
        minx, miny, maxx, maxy = polygon.bounds
        p = Point(np.random.uniform(minx, maxx), 
                  np.random.uniform(miny, maxy))
        if polygon.contains(p):
            points.append(p)
    return points
```

---

### 3.4 Dimensionamiento de la flota de couriers

**Archivos a revisar:**
- `src/synth_loader.py` - Función `load_synth_instance()`, cálculo de `n_couriers`
- `data/couriers.csv` - Definición de 58 couriers

**Lógica de dimensionamiento:**
```python
def compute_fleet_size(total_orders, orders_per_courier=20, min_couriers=10):
    """
    Calcula tamaño de flota basado en carga esperada
    
    Args:
        total_orders: Órdenes totales del día
        orders_per_courier: Productividad target (órdenes/courier/turno)
        min_couriers: Flota mínima para garantizar cobertura
    
    Returns:
        n_couriers: Tamaño de flota óptimo
    """
    computed = math.ceil(total_orders / orders_per_courier)
    return max(min_couriers, computed)
```

**Parámetros del escenario sintético:**
- Total órdenes: 1,038
- `orders_per_courier`: 18 (calibrado a LaDe)
- Resultado: `n_couriers = max(10, ceil(1038/18)) = 58`

**Turnos:**
- Turno matutino: 11:00-17:00 (6h) - 30 couriers
- Turno vespertino: 16:00-23:00 (7h) - 28 couriers
- Overlap: 16:00-17:00 para pico de demanda

---

## 4. Implementación de políticas de despacho

### 4.1 Política base: FCFS

**Archivos a revisar:**
- `src/main.py` - Branch `if FCFS_POLICY == 1`
- `scripts/run_fcfs_instance.py` - Script de ejecución

**Lógica FCFS (pseudocódigo):**
```python
def assign_fcfs(order, available_couriers):
    """
    Asigna orden al courier disponible más cercano al restaurante
    """
    distances = []
    for courier in available_couriers:
        dist = osrm_distance(courier.location, order.restaurant.location)
        distances.append((courier, dist))
    
    # Asignar al courier con menor distancia
    best_courier = min(distances, key=lambda x: x[1])[0]
    
    # Crear ruta individual: restaurante → cliente
    route = create_route([order.restaurant, order.customer])
    assign_route(best_courier, route)
```

**Complejidad:** O(|C|) donde C = couriers disponibles

---

### 4.2 Política avanzada: Rolling Horizon

**Archivos a revisar:**
- `src/main.py` - Branch `else` (RH), llamadas a bundling/matching
- `src/bundling.py` - Generación de bundles consolidados
- `scripts/run_synth_instance.py` - Script de ejecución RH

---

#### 4.2.1 Generación de bundles

**Archivo:** `src/bundling.py`

**Algoritmo de bundling (heurística de inserción):**
```python
def generate_bundles(orders, max_bundle_size=4):
    """
    Agrupa órdenes geográficamente cercanas y temporalmente compatibles
    
    Criterios de compatibilidad:
    1. Mismo restaurante o restaurantes cercanos (< 500m)
    2. Tiempos de preparación compatibles (diferencia < 10 min)
    3. SLA no violado por detour adicional
    """
    bundles = []
    remaining_orders = orders.copy()
    
    while remaining_orders:
        seed_order = remaining_orders.pop(0)
        bundle = [seed_order]
        
        # Intentar agregar órdenes compatibles
        for order in remaining_orders[:]:
            if is_compatible(bundle, order):
                bundle.append(order)
                remaining_orders.remove(order)
                if len(bundle) >= max_bundle_size:
                    break
        
        bundles.append(bundle)
    
    return bundles

def is_compatible(bundle, new_order):
    """Verifica compatibilidad geográfica y temporal"""
    # Criterio 1: Distancia entre restaurantes
    if restaurant_distance(bundle[0].restaurant, new_order.restaurant) > 500:
        return False
    
    # Criterio 2: Diferencia en ready_time
    max_ready = max(o.ready_time for o in bundle)
    if abs(new_order.ready_time - max_ready) > 10 * 60:  # 10 min
        return False
    
    # Criterio 3: SLA factible con detour
    test_route = create_route(bundle + [new_order])
    if violates_sla(test_route):
        return False
    
    return True
```

---

#### 4.2.2 Matching bipartito

**Archivo:** `src/bundling.py` (o módulo separado si existe)

**Problema de matching:**
```
Maximizar: Σ w_bc * x_bc
Sujeto a:
  Σ_c x_bc ≤ 1  ∀ bundle b    (cada bundle asignado a lo más un courier)
  Σ_b x_bc ≤ 1  ∀ courier c   (cada courier recibe lo más un bundle)
  x_bc ∈ {0,1}
```

**Pesos de asignación:**
```python
def compute_weight(bundle, courier):
    """
    Calcula peso de asignar bundle a courier
    
    Componentes del peso:
    1. Eficiencia: |bundle| / tiempo_total
    2. Penalización por pickup tardío
    3. Penalización por riesgo de SLA
    """
    n_orders = len(bundle)
    route = create_route_for_bundle(bundle, courier.location)
    total_time = route.total_duration
    
    efficiency = n_orders / (total_time / 3600)  # órdenes/hora
    
    pickup_delay = max(0, route.first_pickup_time - bundle.earliest_ready_time)
    delay_penalty = PICKUP_DELAY_THETA * pickup_delay
    
    sla_risk = compute_sla_risk(bundle, route)
    
    weight = efficiency - delay_penalty - sla_risk
    return weight
```

**Solver:** Algoritmo Húngaro (Hungarian algorithm) - `scipy.optimize.linear_sum_assignment`

---

#### 4.2.3 Estrategia de commitment

**Archivo:** `src/main.py` - Lógica de commitment en bucle RH

**Niveles de commitment:**

1. **Commitment final** (se ejecuta inmediatamente):
   - Todas las órdenes del bundle están listas
   - Courier puede iniciar ruta antes de siguiente epoch

2. **Commitment parcial** (prepositioning):
   - Bundle no completamente listo
   - Se envía courier hacia restaurante sin asignar órdenes específicas aún

3. **Sin commitment** (se pospone):
   - Courier no estará disponible antes de siguiente epoch

4. **Commitment forzado** (excepción por urgencia):
   - Alguna orden lleva >10 min lista sin asignar
   - Se fuerza asignación inmediata para evitar violación de SLA

```python
MAX_WAIT_BEFORE_FORCED_COMMIT = 10 * 60  # 10 minutos

def evaluate_commitment(bundle, courier, current_time, next_epoch):
    all_ready = all(o.ready_time <= current_time for o in bundle)
    courier_available = courier.available_time <= next_epoch
    
    if all_ready and courier_available:
        return "FINAL"
    
    # Verificar si hay órdenes en riesgo
    for order in bundle:
        wait_time = current_time - order.ready_time
        if wait_time > MAX_WAIT_BEFORE_FORCED_COMMIT:
            return "FORCED"
    
    if courier_available:
        return "PARTIAL"
    
    return "NONE"
```

---

## 5. Diseño experimental

### 5.1 Definición de escenarios de prueba

**Escenario sintético base:**
- Nombre: `synthetic_lapaz_1038orders`
- Órdenes: 1,038
- Couriers: 58
- Restaurantes: 142
- Horizonte: 11:00 - 23:00 (12 horas)
- Seed: 2025

**Variaciones experimentales (futuras):**
- Escala de demanda: 500, 1000, 1500 órdenes
- Tamaño de flota: 30, 58, 80 couriers
- Patrones temporales: Peak único, doble peak, demanda plana

---

### 5.2 Parámetros de configuración

**Archivo:** `src/config.py`

**Parámetros RH:**
```python
OPTIMIZATION_FREQUENCY = 5 * 60        # 5 minutos
ASSIGNMENT_HORIZON_DELTA_U = 20 * 60  # 20 minutos
LOOKAHEAD_DELTA_1 = 15 * 60           # 15 minutos
LOOKAHEAD_DELTA_2 = 10 * 60           # 10 minutos
PICKUP_DELAY_THETA = 0.5              # Penalización pickup tardío
MAX_BUNDLE_SIZE = 4                    # Máximo órdenes por bundle
```

**Parámetros OSRM:**
```python
OSRM_URL = "http://localhost:5000"
OSRM_PROFILE = "driving"
```

**Parámetros SLA:**
```python
CLICK_TO_DOOR_SLA = 60 * 60  # 60 minutos
```

---

### 5.3 Control de aleatoriedad y semillas

**Archivos a revisar:**
- `scripts/make_synth_orders.py` - `np.random.seed(2025)`
- `src/main.py` - Inicialización de RNG

**Control de reproducibilidad:**
```python
# Generación de instancia sintética
INSTANCE_SEED = 2025
np.random.seed(INSTANCE_SEED)
random.seed(INSTANCE_SEED)

# Ejecución de simulación (réplicas independientes)
SIMULATION_SEEDS = [3001, 3002, 3003, ...]  # 30 réplicas

for seed in SIMULATION_SEEDS:
    np.random.seed(seed)
    run_simulation(instance, policy="RH", seed=seed)
```

**Componentes estocásticos controlados:**
1. Tiempos de preparación (log-normal)
2. Tiempos de llegada de órdenes (Poisson no homogéneo)
3. Posiciones iniciales de couriers
4. Desempates en algoritmos (e.g., matching con pesos idénticos)

---

## 6. Métricas de evaluación

### 6.1 Métricas de calidad de servicio (Reyes2018)

**Archivo:** `src/lade_metrics.py` (o similar)

**Métricas Click-to-Door:**
```python
def compute_click_to_door(order):
    """
    Tiempo total desde colocación hasta entrega
    """
    return order.delivery_time - order.placement_time

# Estadísticos
click_to_door_times = [compute_click_to_door(o) for o in delivered_orders]
mean_ctd = np.mean(click_to_door_times)
p50_ctd = np.percentile(click_to_door_times, 50)
p95_ctd = np.percentile(click_to_door_times, 95)
```

**Descomposición temporal:**
```python
prep_time = order.ready_time - order.placement_time
ready_to_pickup = order.pickup_time - order.ready_time
pickup_to_door = order.delivery_time - order.pickup_time
```

**Cumplimiento SLA:**
```python
sla_compliance = sum(1 for o in orders if compute_click_to_door(o) <= SLA) / len(orders)
```

---

### 6.2 Métricas de eficiencia operacional

**Órdenes por courier-hora:**
```python
def compute_orders_per_courier_hour(simulation_results):
    total_deliveries = len(simulation_results.delivered_orders)
    total_courier_hours = sum(c.shift_duration_hours for c in simulation_results.couriers)
    return total_deliveries / total_courier_hours
```

**Utilización de couriers:**
```python
def compute_utilization(courier):
    """
    % del turno activamente sirviendo órdenes
    """
    active_time = sum(route.duration for route in courier.completed_routes)
    total_shift = courier.shift_end - courier.shift_start
    return active_time / total_shift
```

**Distancia total recorrida:**
```python
total_distance = sum(route.distance for c in couriers for route in c.routes)
```

---

### 6.3 Procedimiento de cálculo

**Archivo de salida:** CSV/Parquet con métricas por orden y por courier

**Formato de resultados:**
```python
# metrics_per_order.csv
order_id, placement_time, ready_time, pickup_time, delivery_time, 
click_to_door, prep_time, ready_to_pickup, pickup_to_door, 
sla_met, courier_id, bundle_size

# metrics_per_courier.csv
courier_id, shift_start, shift_end, total_deliveries, total_distance,
total_active_time, utilization, orders_per_hour
```

---

## 7. Validación y verificación

### 7.1 Validación del simulador

**Pruebas de validación:**

1. **Conservación de órdenes:** Todas las órdenes ingresadas son eventualmente asignadas
2. **Consistencia temporal:** `placement_time ≤ ready_time ≤ pickup_time ≤ delivery_time`
3. **Capacidad de couriers:** Nunca se excede `max_capacity` simultáneo
4. **Precedencia pickup-delivery:** Pickup siempre precede a delivery para cada orden

**Archivo de tests:** `tests/test_simulator_validation.py` (crear)

---

### 7.2 Verificación de consistencia de resultados

**Tests de regresión:**
- Ejecutar instancia con `seed=2025` debe producir resultados idénticos
- Hash de dataset sintético debe coincidir: `sha256(synthetic_lapaz_orders.csv)`

---

## 8. Protocolo de análisis estadístico

### 8.1 Estadísticos descriptivos y percentiles

**Análisis por política:**
```python
# Para cada métrica (e.g., Click-to-Door)
for policy in ["FCFS", "RH"]:
    results = load_results(policy)
    print(f"{policy}:")
    print(f"  Mean: {np.mean(results.click_to_door):.2f}")
    print(f"  Median (P50): {np.percentile(results.click_to_door, 50):.2f}")
    print(f"  P95: {np.percentile(results.click_to_door, 95):.2f}")
    print(f"  Std Dev: {np.std(results.click_to_door):.2f}")
```

---

### 8.2 Pruebas de comparación pareada

**Test de Wilcoxon (no paramétrico):**
```python
from scipy.stats import wilcoxon

fcfs_ctd = load_metric("FCFS", "click_to_door")
rh_ctd = load_metric("RH", "click_to_door")

# Comparación pareada (mismas órdenes)
statistic, p_value = wilcoxon(fcfs_ctd, rh_ctd)

if p_value < 0.05:
    print(f"Diferencia estadísticamente significativa (p={p_value:.4f})")
```

---

### 8.3 Análisis de tamaño de efecto

**Cohen's d:**
```python
def cohens_d(group1, group2):
    mean_diff = np.mean(group1) - np.mean(group2)
    pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)
    return mean_diff / pooled_std

effect_size = cohens_d(fcfs_ctd, rh_ctd)
# |d| > 0.8: efecto grande
# |d| 0.5-0.8: efecto medio
# |d| 0.2-0.5: efecto pequeño
```

---

## 9. Pipeline reproducible

### 9.1 Orquestación con Docker

**Archivos a revisar:**
- `docker-compose.yml` - Definición de servicios
- `Dockerfile` (simulador) - Imagen Python del simulador

**Arquitectura Docker:**
```yaml
services:
  osrm:
    image: osrm/osrm-backend:5.26.0
    volumes:
      - ./osrm_data:/data
    ports:
      - "5000:5000"
    command: osrm-routed --algorithm mld /data/map.osrm
  
  simulator:
    build: .
    depends_on:
      - osrm
    environment:
      - OSRM_URL=http://osrm:5000
      - SIM_SEED=2025
    volumes:
      - ./data:/app/data
      - ./results:/app/results
```

---

### 9.2 Ejecución automatizada

**Archivos a revisar:**
- `scripts/generate_results.py` - Script maestro de ejecución
- `scripts/run_fcfs_instance.py` - Ejecución FCFS
- `scripts/run_synth_instance.py` - Ejecución RH

**Pipeline completo:**
```bash
# 1. Generar instancia sintética
python scripts/make_synth_orders.py --seed 2025 --n_orders 1038

# 2. Ejecutar FCFS
python scripts/run_fcfs_instance.py --instance synthetic_lapaz_1038orders

# 3. Ejecutar RH
python scripts/run_synth_instance.py --instance synthetic_lapaz_1038orders

# 4. Comparar resultados
python scripts/compare_policies.py --fcfs results/fcfs/ --rh results/rh/
```

---

### 9.3 Trazabilidad de experimentos

**Manifest de experimento (JSON):**
```json
{
  "experiment_id": "exp_2025_fcfs_lapaz_1038",
  "timestamp": "2025-01-15T10:30:00Z",
  "git_commit": "a3f2b9c",
  "instance": {
    "file": "data/synthetic_lapaz_orders.csv",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "seed": 2025,
    "n_orders": 1038,
    "n_couriers": 58
  },
  "policy": "FCFS",
  "parameters": {
    "osrm_version": "5.26.0",
    "sla_minutes": 60
  },
  "results": {
    "output_dir": "results/fcfs/exp_2025_fcfs_lapaz_1038/",
    "metrics_file": "metrics_summary.csv",
    "routes_file": "routes.json"
  }
}
```

---

## Resumen de archivos clave por sección

| Sección Metodología | Archivos principales |
|---------------------|----------------------|
| 1.1 Arquitectura | `src/main.py`, `src/config.py` |
| 1.2 Interfaces OSRM | `src/getrouteOSMR.py` |
| 1.3 Eventos discretos | `src/main.py`, `src/synth_loader.py` |
| 2.1 Red OSM | `data/map.osm`, `scripts/download_osm.sh` |
| 2.2 OSRM preprocessing | `scripts/prepare_osrm.sh`, `osrm_data/` |
| 3.1 Polígono urbano | `scripts/make_synth_orders.py` (línea ~50) |
| 3.2 Calibración LaDe | `scripts/make_synth_orders.py` (`build_intensity_profile`) |
| 3.3 Muestreo geográfico | `scripts/make_synth_orders.py` (`sample_n_points_in_polygon`) |
| 3.4 Dimensionamiento flota | `src/synth_loader.py` (línea ~80) |
| 4.1 FCFS | `src/main.py` (branch FCFS) |
| 4.2 Rolling Horizon | `src/main.py`, `src/bundling.py` |
| 5.2 Parámetros | `src/config.py` |
| 5.3 Semillas | `scripts/make_synth_orders.py` (línea 1) |
| 6.1-6.2 Métricas | `src/lade_metrics.py` |
| 9.1 Docker | `docker-compose.yml`, `Dockerfile` |
| 9.2 Ejecución | `scripts/run_*.py` |

---

## Notas finales

- Este documento debe actualizarse conforme se desarrolla el código
- Cada sección de la Metodología debe citar números de línea específicos
- Incluir diagramas de flujo para bucles principales (simulador, RH)
- Documentar valores por defecto de todos los parámetros configurables
- Validar que todos los scripts mencionados existen y están funcionales

**Versión:** 1.0 (Noviembre 2025)
