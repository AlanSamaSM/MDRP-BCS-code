from datetime import timedelta
from src.config import (
    ASSIGNMENT_HORIZON,
    MAX_CLICK_TO_DOOR,
    SERVICE_TIME,
    DELTA_1,
    DELTA_2,
)
from src.getrouteOSMR import get_route_details
from src.config import GROUP_I_PENALTY, GROUP_II_PENALTY, FRESHNESS_PENALTY_THETA
# ======================
# Bundling
# =====================

#Aquí se define Zt, que es el tamaño objetivo de los bundles
def compute_target_bundle_size(current_time, orders, couriers):
    """Compute dynamic target bundle size using DELTA_1 and DELTA_2."""

    orders_ready = [o for o in orders if o.ready_time <= current_time + DELTA_1]
    couriers_available = [c for c in couriers if c.off_time >= current_time + DELTA_2]

    if not couriers_available:
        return 1

    ratio = len(orders_ready) / len(couriers_available)
    return max(int(ratio), 1)

def calculate_bundle_score(bundle, courier, current_time):
    """
    Calcula el score para asignar un bundle a un courier específico.
    Considera ventanas exactas para pickup y drop-off según Reyes (2018).
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
    courier_arrival_at_restaurant = current_time + timedelta(minutes=inbound_duration_min)

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

    # 2) Calcular pérdidas de frescura
    # Frescura se penaliza sólo si pickup_time > ready_time

    # 2) Penalizaciones de Prioridad (grupos I, II, III)
    earliest_placement = min(o.placement_time for o in bundle)
    if delivery_finish_time > earliest_placement + MAX_CLICK_TO_DOOR:
        priority_penalty = GROUP_I_PENALTY  # No se puede cumplir entrega a tiempo
    elif pickup_time > max(o.ready_time for o in bundle):
        priority_penalty = GROUP_II_PENALTY  # Retraso en la recogida
    else:
        priority_penalty = 0  # Grupo III

    # 3) Throughput: Número de órdenes dividido entre tiempo total
    total_service_time_min = SERVICE_TIME.total_seconds() / 60.0
    total_time = total_travel_time_min + total_service_time_min
    throughput = len(bundle) / total_time if total_time > 0 else len(bundle)
    
    # 4) Frescura (considerando la orden con mayor espera)
    freshness_penalty = FRESHNESS_PENALTY_THETA * max(
        max((pickup_time - o.ready_time).total_seconds() / 60.0, 0.0) for o in bundle
    )

    # 3) Score Final
    score = throughput - freshness_penalty - priority_penalty

    return score

def calculate_cost(route_details, service_delay):
    """Calculate the cost of a candidate route.

    ``service_delay`` may be provided as a ``timedelta``.  Convert it to minutes
    before applying the freshness penalty so arithmetic with the travel time
    (float) works correctly.
    """
    travel_time = route_details['duration'] / 60.0  # seconds -> minutes

    if isinstance(service_delay, timedelta):
        delay_minutes = service_delay.total_seconds() / 60.0
    else:
        delay_minutes = float(service_delay)

    return travel_time + FRESHNESS_PENALTY_THETA * delay_minutes

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
    
    # 2. Ordenar las órdenes por su ready_time (de menor a mayor)
    restaurant_orders.sort(key=lambda o: o.ready_time)
    
    # 3. Calcular el número objetivo de bundles a crear para este restaurante.
    target_bundles = max(len(restaurant_orders) // target_bundle_size, couriers_available)
    
    # 4. Inicializar mr bundles vacíos.
    bundles = [[] for _ in range(target_bundles)]
    
    # 5. Para cada orden, buscar el bundle y la posición de inserción que minimicen el incremento del costo.
    for order in restaurant_orders:
        best_bundle = None
        best_cost_increase = float('inf')
        best_position = None
        
        # Para cada bundle existente, evaluar todas las posiciones de inserción
        for bundle in bundles:
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
                    candidate_bundle = bundle[:pos] + [order] + bundle[pos:] #concatenación de listas
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

    # Remove any empty bundles that may have been preallocated but not filled
    return [b for b in bundles if b]

