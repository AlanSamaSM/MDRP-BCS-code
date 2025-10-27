import os
import xgboost as xgb
import numpy as np
import pandas as pd
from geopy.distance import geodesic
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

# AI Model Loading
USE_AI_BUNDLING = os.environ.get('USE_AI_BUNDLING') == '1'
model = None
if USE_AI_BUNDLING:
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bundling_model.xgb'))
    if os.path.exists(model_path):
        model = xgb.XGBRegressor()
        model.load_model(model_path)
        print("AI bundling model loaded successfully.")
    else:
        print("AI bundling model not found at", model_path)
        USE_AI_BUNDLING = False

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
            if USE_AI_BUNDLING and model:
                for pos in range(len(bundle) + 1):
                    candidate_bundle_orders = bundle[:pos] + [order] + bundle[pos:]
                    
                    # Feature Engineering
                    num_orders = len(candidate_bundle_orders)
                    restaurant_loc = (restaurant.location[0], restaurant.location[1])
                    customer_locs = [(o.dropoff_loc[0], o.dropoff_loc[1]) for o in candidate_bundle_orders]
                    
                    distances = [geodesic(restaurant_loc, cl).km for cl in customer_locs]
                    avg_restaurant_to_customer_dist = np.mean(distances)
                    
                    max_customer_age = (current_time - min([o.placement_time for o in candidate_bundle_orders])).total_seconds() / 60
                    waiting_time_since_ready = (current_time - max([o.ready_time for o in candidate_bundle_orders])).total_seconds() / 60

                    features = pd.DataFrame({
                        'num_orders': num_orders,
                        'avg_restaurant_to_customer_dist': avg_restaurant_to_customer_dist,
                        'max_customer_age': max_customer_age,
                        'waiting_time_since_ready': waiting_time_since_ready
                    })
                    
                    predicted_travel_time = model.predict(features)[0]
                    cost = predicted_travel_time

                    # Validate route before considering this bundle
                    dropoff_points = [o.dropoff_loc for o in candidate_bundle_orders]
                    if len(dropoff_points) > 15:
                        continue
                    route = get_route_details(restaurant.location, dropoff_points)
                    if not route:
                        continue

                    if cost < best_cost_increase:
                        best_cost_increase = cost
                        best_bundle = bundle
                        best_position = pos
            else:
                # Original logic if AI model is not used
                if not bundle:
                    route = get_route_details(restaurant.location, [order.dropoff_loc])
                    if route:
                        cost = calculate_cost(route, SERVICE_TIME * 2)
                        if cost < best_cost_increase:
                            best_cost_increase = cost
                            best_bundle = bundle
                            best_position = 0
                else:
                    for pos in range(len(bundle) + 1):
                        if len(bundle) >= target_bundle_size:
                            current_efficiency = calculate_route_efficiency(restaurant.location, bundle)
                            candidate_bundle_for_efficiency = bundle[:pos] + [order] + bundle[pos:]
                            new_efficiency = calculate_route_efficiency(restaurant.location, candidate_bundle_for_efficiency)
                            if new_efficiency >= current_efficiency:
                                continue

                        candidate_bundle = bundle[:pos] + [order] + bundle[pos:]
                        dropoff_points = [o.dropoff_loc for o in candidate_bundle]
                        if len(dropoff_points) > 15:
                            continue
                        route = get_route_details(restaurant.location, dropoff_points)
                        if route:
                            service_delay = SERVICE_TIME + (SERVICE_TIME * len(candidate_bundle))
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
                    for pos in range(len(target_bundle) + 1):
                        candidate_bundle = target_bundle[:pos] + [order] + target_bundle[pos:]
                        
                        dropoff_points = [o.dropoff_loc for o in candidate_bundle]
                        if len(dropoff_points) > 15:
                            continue
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
    return [b for b in bundles if b]

