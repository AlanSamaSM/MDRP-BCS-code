from datetime import timedelta
import math
import numpy as np
from src.config import (
    ASSIGNMENT_HORIZON,
    MAX_CLICK_TO_DOOR,
    SERVICE_TIME,
    DELTA_1,
    DELTA_2,
    FRESHNESS_PENALTY_BETA,
    PICKUP_DELAY_THETA,
)
from src.getrouteOSMR import get_route_details
from src.schedule import plan_route
from src.config import (
    GROUP_I_PENALTY,
    GROUP_II_PENALTY,
    MAX_TARGET_BUNDLE_SIZE,
    MAX_BUNDLE_SIZE,
)
# ======================
# Bundling
# =====================

#Aquí se define Zt, que es el tamaño objetivo de los bundles
def compute_target_bundle_size(current_time, orders, couriers):
    """
    Compute Zt as per Reyes et al. (2018), Section 3.1:
    
    Zt = ⌈ |{o ∈ Ot : eo ≤ t + Δ1}| / |{d ∈ Dt : ed ≤ t + Δ2}| ⌉
    
    where eo is order ready time and ed is courier available time.
    """
    # Órdenes que estarán listas en los próximos Δ1 minutos
    orders_ready = [
        o for o in orders 
        if o.ready_time <= current_time + DELTA_1
    ]
    
    # Couriers que estarán disponibles (terminarán su asignación actual) en los próximos Δ2 minutos
    # available_time es cuando el courier termina su ruta actual, o current_time si está libre
    def get_available_time(courier):
        if courier.current_route is None:
            return current_time
        return courier.current_route.get('completion_time', current_time)
    
    couriers_soon_available = [
        c for c in couriers 
        if get_available_time(c) <= current_time + DELTA_2
    ]
    
    if not couriers_soon_available:
        # Si ningún courier estará disponible pronto, usar cualquier courier activo en turno
        couriers_soon_available = [
            c for c in couriers 
            if c.off_time >= current_time  # aún en turno
        ]
    
    if not couriers_soon_available:
        return 1  # Fallback: no hay couriers disponibles
    
    # Cálculo según paper (con ceiling)
    ratio = len(orders_ready) / len(couriers_soon_available)
    target = max(int(np.ceil(ratio)), 1)
    if MAX_TARGET_BUNDLE_SIZE:
        target = min(target, MAX_TARGET_BUNDLE_SIZE)
    
    return target

def calculate_bundle_score(bundle, courier, current_time):
    """
    Calculate matching weight as per Reyes (2018), Equation (1a):
    
    weight = Ns / (max_dropoff - courier_available) - θ × (pickup_time - bundle_ready)
    
    where θ (PICKUP_DELAY_THETA) penalizes pickup delay.
    """

    # Determinar cuando el courier está disponible para empezar nueva asignación
    if courier.current_route is None:
        courier_available_time = current_time
    else:
        courier_available_time = courier.current_route.get('completion_time', current_time)

    # Ruta courier -> restaurante -> entregas con los tiempos de Reyes (2018):
    # pickup = max(e_o, llegada + s_r/2); entrega = llegada al cliente + s_o/2
    plan = plan_route(courier.location, courier_available_time, bundle)
    if not plan:
        return float('-inf')

    bundle_ready_time = max(o.ready_time for o in bundle)
    pickup_time = plan['pickup_time']
    delivery_finish_time = max(plan['dropoff_times'])  # max_o delta_{o,d}

    # 2) Penalizaciones de Prioridad (grupos I, II, III) - para clasificación solamente
    earliest_placement = min(o.placement_time for o in bundle)
    if delivery_finish_time > earliest_placement + MAX_CLICK_TO_DOOR:
        priority_penalty = GROUP_I_PENALTY  # No se puede cumplir entrega a tiempo
    elif pickup_time > max(o.ready_time for o in bundle):
        priority_penalty = GROUP_II_PENALTY  # Retraso en la recogida
    else:
        priority_penalty = 0  # Grupo III

    # 3) Throughput component (Ns / delivery_time)
    delivery_time_hours = (delivery_finish_time - courier_available_time).total_seconds() / 3600.0
    throughput = len(bundle) / max(delivery_time_hours, 0.01)
    
    # 4) Pickup delay penalty (θ term from Equation 1a)
    pickup_delay_min = max(0, (pickup_time - bundle_ready_time).total_seconds() / 60.0)
    pickup_penalty = PICKUP_DELAY_THETA * pickup_delay_min

    # Score final (matching weight)
    score = throughput - pickup_penalty - priority_penalty

    return score

def calculate_cost(route_details, service_delay):
    """
    Calculate route cost as per Reyes (2018) Procedure 1:
    
    cost = travel_time + β × service_delay
    
    where β (FRESHNESS_PENALTY_BETA) is the weight for service delay in bundle construction.
    """
    travel_time = route_details['duration'] / 60.0  # seconds -> minutes

    if isinstance(service_delay, timedelta):
        delay_minutes = service_delay.total_seconds() / 60.0
    else:
        delay_minutes = float(service_delay)

    return travel_time + FRESHNESS_PENALTY_BETA * delay_minutes

def calculate_route_efficiency(restaurant_location, bundle):
    """Calculates the efficiency (average time per order) of a bundle."""
    if not bundle:
        return float('inf')
    
    dropoff_points = [o.dropoff_loc for o in bundle]
    route = get_route_details(restaurant_location, dropoff_points)
    if not route:
        return float('inf')

    travel_time_min = route['duration'] / 60.0
    total_service_time_min = (SERVICE_TIME.total_seconds() / 60.0) * len(bundle)
    total_time = travel_time_min + total_service_time_min
    
    return total_time / len(bundle)


def _bundle_cost(restaurant_location, bundle):
    """Costo de la ruta restaurante -> entregas de un bundle (0 si está vacío)."""
    if not bundle:
        return 0.0
    route = get_route_details(restaurant_location, [o.dropoff_loc for o in bundle])
    if not route:
        return float('inf')
    # Total Service Time = Pickup (once per bundle) + Drop-offs (once per order)
    service_delay = SERVICE_TIME + (SERVICE_TIME * len(bundle))
    return calculate_cost(route, service_delay)


def _best_insertion(restaurant_location, bundles, order, target_bundle_size=None):
    """Bundle y posición que minimizan el incremento de costo al insertar ``order``.

    Si se indica ``target_bundle_size`` y un bundle ya lo alcanzó, solo se
    permite insertar si mejora su eficiencia (tiempo promedio por orden).
    Retorna ``(None, None)`` si ningún bundle admite la orden.
    """
    best_bundle, best_position = None, None
    best_increase = float('inf')
    for bundle in bundles:
        if MAX_BUNDLE_SIZE and len(bundle) >= MAX_BUNDLE_SIZE:
            continue
        base_cost = _bundle_cost(restaurant_location, bundle)
        for pos in range(len(bundle) + 1):
            candidate = bundle[:pos] + [order] + bundle[pos:]
            if target_bundle_size and bundle and len(bundle) >= target_bundle_size:
                if (calculate_route_efficiency(restaurant_location, candidate)
                        >= calculate_route_efficiency(restaurant_location, bundle)):
                    continue
            increase = _bundle_cost(restaurant_location, candidate) - base_cost
            if increase < best_increase:
                best_increase = increase
                best_bundle, best_position = bundle, pos
    return best_bundle, best_position


def generate_bundles_for_restaurant(restaurant, current_time, target_bundle_size, couriers_available):
    """
    Genera bundles (rutas) de órdenes para un restaurante, siguiendo la lógica de inserción paralela.
    
    Parámetros:
      - restaurant: objeto que contiene la lista de órdenes (restaurant.orders).
      - current_time: tiempo actual.
      - target_bundle_size: tamaño objetivo Zt, obtenido a partir de orders_ready y couriers_available.
      - couriers_available: número de repartidores disponibles
      
    Retorna:
      - Una lista de bundles (cada bundle es una lista de órdenes) para ser asignados a repartidores.
    """
    # 1. Filtrar órdenes pendientes que estén listas dentro del horizonte de asignación (por ejemplo, ASSIGNMENT_HORIZON)
    restaurant_orders = [
        order for order in restaurant.orders
        if order.status == 'ready' and order.ready_time <= current_time + ASSIGNMENT_HORIZON
    ]
    
    # Si no hay órdenes, retorna una lista vacía
    if not restaurant_orders:
        return []
    
    print(f"    Bundling: Restaurant has {len(restaurant_orders)} ready orders")
    
    # 2. Ordenar las órdenes por su ready_time (de menor a mayor)
    restaurant_orders.sort(key=lambda o: o.ready_time)
    
    # 3. Calcular el número objetivo de bundles a crear para este restaurante.
    safe_bundle_size = max(target_bundle_size, 1)
    if safe_bundle_size <= 0:
        safe_bundle_size = 1

    desired_bundle_count = max(1, math.ceil(len(restaurant_orders) / safe_bundle_size))
    if couriers_available:
        desired_bundle_count = min(desired_bundle_count, couriers_available)

    target_bundles = max(1, desired_bundle_count)
    
    # 4. Inicializar mr bundles vacíos.
    bundles = [[] for _ in range(target_bundles)]

    # 5. Inserción paralela: cada orden va al bundle y posición con el menor
    #    INCREMENTO de costo (Reyes et al., 2018, Procedimiento 1).
    for order in restaurant_orders:
        best_bundle, best_position = _best_insertion(
            restaurant.location, bundles, order, target_bundle_size
        )
        if best_bundle is not None:
            best_bundle.insert(best_position, order)
        else:
            # Todos los bundles están llenos (MAX_BUNDLE_SIZE): se abre uno nuevo.
            bundles.append([order])

    # 6. Mejora local "remove-reinsert": se extrae cada orden de su bundle actual
    #    y se reinserta en la mejor posición de cualquier bundle (incluido el suyo).
    for _ in range(2):  # Se puede iterar varias veces para una mejor solución
        for order in [o for b in bundles for o in b]:
            source = next(b for b in bundles if any(x is order for x in b))
            source.remove(order)
            target, pos = _best_insertion(restaurant.location, bundles, order)
            if target is None:
                source.append(order)
            else:
                target.insert(pos, order)

    # Remove any empty bundles that may have been preallocated but not filled
    final_bundles = [b for b in bundles if b]

    # Cada orden debe aparecer exactamente una vez entre los bundles
    bundled_ids = [o.id for b in final_bundles for o in b]
    assert sorted(bundled_ids) == sorted(o.id for o in restaurant_orders), \
        f"Bundling duplicó o perdió órdenes en el restaurante {restaurant.id}"

    print(f"    Bundling: Returning {len(final_bundles)} bundles after optimization")
    return final_bundles

