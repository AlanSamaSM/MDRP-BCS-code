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

    # 1. Obtener la ruta completa (inbound a restaurante + entregas)
    full_route = get_route_details(
        courier.location,
        [bundle[0].restaurant.location] + [o.dropoff_loc for o in bundle]
    )
    if not full_route:
        return float('-inf')

    total_travel_time_min = full_route['duration'] / 60.0

    # 1) Calcular tiempo de llegada al restaurante (inbound)
    inbound_route = get_route_details(courier.location, [bundle[0].restaurant.location])
    if not inbound_route:
        return float('-inf')

    inbound_duration_min = inbound_route['duration'] / 60.0
    
    # Determinar cuando el courier está disponible para empezar nueva asignación
    if courier.current_route is None:
        courier_available_time = current_time
    else:
        courier_available_time = courier.current_route.get('completion_time', current_time)
    
    courier_arrival_at_restaurant = courier_available_time + timedelta(minutes=inbound_duration_min)

    # Según Reyes (2018), la hora exacta del pickup es:
    # max(e_o, llegada_repartidor + s_r/2)
    service_half_min = SERVICE_TIME.total_seconds() / 60.0 / 2
    bundle_ready_time = max(o.ready_time for o in bundle)
    pickup_time = max(
        bundle_ready_time,
        courier_arrival_at_restaurant + timedelta(minutes=service_half_min)
    )
    departure_from_restaurant_time = pickup_time + timedelta(minutes=service_half_min)
    
    # Tiempo de entrega (drop-off)
    # Tiempo al cliente + s_o/2 por orden entregada
    customer_half_min = SERVICE_TIME.total_seconds() / 60.0 / 2
    delivery_finish_time = departure_from_restaurant_time + timedelta(
        minutes=total_travel_time_min + customer_half_min * len(bundle)
    )

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
    
    # 5. Para cada orden, buscar el bundle y la posición de inserción que minimicen el incremento del costo.
    for order in restaurant_orders:
        best_bundle = None
        best_cost_increase = float('inf')
        best_position = None
        
        # Para cada bundle existente, evaluar todas las posiciones de inserción
        for bundle in bundles:
            if MAX_BUNDLE_SIZE and len(bundle) >= MAX_BUNDLE_SIZE:
                continue
            # Si el bundle está vacío, la única opción es insertarla en la posición 0.
            if not bundle: #evalua si el bundle esta vacio
                # Coste base: calcular ruta desde la ubicación del restaurante del objeto restaurant (o se podría usar restaurant_orders[0].restaurant.location)
                route = get_route_details(restaurant.location, [order.dropoff_loc])
                if route!=None:
                    cost = calculate_cost(route, SERVICE_TIME*2)
                    if cost < best_cost_increase:
                        best_cost_increase = cost
                        best_bundle = bundle
                        best_position = 0
            else:
                # Probar todas las posiciones posibles (de 0 a len(bundle))
                for pos in range(len(bundle) + 1):
                    # --- INICIO DE LA MODIFICACIÓN: Verificación de eficiencia ---
                    # Si el bundle ya alcanzó el tamaño objetivo, solo se inserta si mejora la eficiencia.
                    if len(bundle) >= target_bundle_size:
                        current_efficiency = calculate_route_efficiency(restaurant.location, bundle)
                        candidate_bundle_for_efficiency = bundle[:pos] + [order] + bundle[pos:]
                        new_efficiency = calculate_route_efficiency(restaurant.location, candidate_bundle_for_efficiency)
                        
                        # Si la nueva eficiencia no es mejor (menor), se ignora esta inserción.
                        if new_efficiency >= current_efficiency:
                            continue
                    # --- FIN DE LA MODIFICACIÓN ---

                    candidate_bundle = bundle[:pos] + [order] + bundle[pos:] #concatenación de listas
                    if MAX_BUNDLE_SIZE and len(candidate_bundle) > MAX_BUNDLE_SIZE:
                        continue
                    # Calcular la ruta completa para este candidate_bundle.
                    # Suponemos que la ruta inicia en la ubicación del restaurante.
                    dropoff_points = [o.dropoff_loc for o in candidate_bundle]  #asignamos a dropoff_points la ubicacion de entrega del bundle completo con la configuración iterandose
                    route = get_route_details(restaurant.location, dropoff_points) #se calcula la ruta con la configuración tentativa 
                    if route:
                        service_delay = SERVICE_TIME + (SERVICE_TIME * len(candidate_bundle)) #Total Service Time=Pickup (once per bundle)+Drop-offs (once per order)=SERVICE_TIME+(SERVICE_TIME×number of orders)
                        cost = calculate_cost(route, service_delay)
                        if cost < best_cost_increase:
                            best_cost_increase = cost
                            best_bundle = bundle
                            best_position = pos
        
        # Si se encontró un bundle adecuado, inserta la orden en la posición óptima.
        if best_bundle is not None and best_position is not None:
            best_bundle.insert(best_position, order)
        else:
            # Si no se encontró un bundle (caso raro), se podría crear un nuevo bundle.
            bundles.append([order])

    # --- INICIO DE LA MODIFICACIÓN: Fase de mejora con "remove-reinsert" ---
    for _ in range(2): # Se puede iterar varias veces para una mejor solución
        for bundle_idx, bundle in enumerate(list(bundles)):
            for order_idx, order in enumerate(list(bundle)):
                # 1. Extraer la orden del bundle actual
                original_bundle = list(bundle)
                del original_bundle[order_idx]
                bundles[bundle_idx] = original_bundle

                # 2. Encontrar la mejor posición para re-insertar la orden en CUALQUIER bundle
                best_new_bundle_idx = -1
                best_new_pos = -1
                min_cost = float('inf')

                for target_bundle_idx, target_bundle in enumerate(bundles):
                    if MAX_BUNDLE_SIZE and len(target_bundle) >= MAX_BUNDLE_SIZE:
                        continue
                    for pos in range(len(target_bundle) + 1):
                        candidate_bundle = target_bundle[:pos] + [order] + target_bundle[pos:]
                        if MAX_BUNDLE_SIZE and len(candidate_bundle) > MAX_BUNDLE_SIZE:
                            continue
                        
                        dropoff_points = [o.dropoff_loc for o in candidate_bundle]
                        route = get_route_details(restaurant.location, dropoff_points)
                        
                        if route:
                            service_delay = SERVICE_TIME + (SERVICE_TIME * len(candidate_bundle))
                            cost = calculate_cost(route, service_delay)
                            
                            if cost < min_cost:
                                min_cost = cost
                                best_new_bundle_idx = target_bundle_idx
                                best_new_pos = pos
                
                # 3. Si se encontró una mejor posición, realizar el cambio
                if best_new_bundle_idx != -1:
                    bundles[best_new_bundle_idx].insert(best_new_pos, order)
    # --- FIN DE LA MODIFICACIÓN ---

    # Remove any empty bundles that may have been preallocated but not filled
    final_bundles = [b for b in bundles if b]
    print(f"    Bundling: Returning {len(final_bundles)} bundles after optimization")
    return final_bundles

