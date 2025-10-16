from datetime import timedelta
import numpy as np
from scipy.optimize import linear_sum_assignment

from src.config import (
    OPTIMIZATION_FREQUENCY,
    TARGET_CLICK_TO_DOOR,
    SERVICE_TIME,
)
from src.getrouteOSMR import get_route_details
from src.bundling import calculate_bundle_score

def assign_order_to_nearest_courier(order, couriers, current_time):
    """
    Assigns a single order to the nearest available courier (FCFS logic).
    """
    best_courier = None
    min_dist = float('inf')

    for courier in couriers:
        if courier.current_route is None:
            # Simplified distance calculation (Euclidean)
            dist = np.sqrt((courier.location[0] - order.restaurant.location[0])**2 + 
                         (courier.location[1] - order.restaurant.location[1])**2)
            if dist < min_dist:
                min_dist = dist
                best_courier = courier

    if best_courier:
        route_data = get_route_details(
            best_courier.location,
            [order.restaurant.location, order.dropoff_loc]
        )
        if route_data:
            best_courier.current_route = {
                'orders': [order],
                'route': route_data,
                'start_time': current_time,
                'completion_time': current_time + timedelta(seconds=route_data['duration']),
                'commitment_type': 'final'
            }
            order.status = 'assigned'


###############################################################################
# HELPER: classify_bundle(bundle, couriers, current_time)
#   Returns an integer {1,2,3} for Group I, II, or III.
###############################################################################
def classify_bundle(bundle, couriers, current_time):
    """
    Group I: Orders whose target drop-off time is impossible to achieve
             ( drop-off would exceed earliest_placement + TARGET_CLICK_TO_DOOR ).
    Group II: Not in Group I, but can't be picked up at ready time
              ( i.e. earliest pickup > max(order.ready_time) ) for all couriers.
    Group III: Everything else.
    """
    
    # 1) For each order in the bundle, find earliest_placement_time:
    earliest_placement = min(o.placement_time for o in bundle)
    target_dropoff_time = earliest_placement + TARGET_CLICK_TO_DOOR

    # 2) We'll see if *any* courier can drop off by target_dropoff_time
    #    If none can, => Group I.
    can_meet_deadline = False
    for c in couriers:
        epd = earliest_possible_dropoff(bundle, c, current_time)
        if epd and (epd <= target_dropoff_time):
            can_meet_deadline = True
            break
    if not can_meet_deadline:
        return 1  # Group I

    # 3) Group II: It's not Group I, so next check if for all couriers,
    #    earliest pickup time > max ready_time. We'll do a quick test:
    #    If there's at least one courier who can pick up on time, it's not Group II.
    all_couriers_miss_pickup = True
    bundle_ready_time = max(o.ready_time for o in bundle)
    for c in couriers:
        epd = earliest_possible_dropoff(bundle, c, current_time)
        if epd is None:
            continue
        # earliest pickup time = earliest_possible_dropoff - the travel/ drop segment
        # but let's do a simpler approach: if earliest dropoff is feasible, let's estimate
        # earliest pickup is (earliest_dropoff - the outbound route) ...
        # We can do a simpler approach: just check inbound route feasibility.
        inbound = earliest_pickup_estimate(bundle, c, current_time)
        if inbound <= bundle_ready_time:
            # means we can arrive by the time orders are ready
            all_couriers_miss_pickup = False
            break

    if all_couriers_miss_pickup:
        return 2  # Group II

    # 4) If not Group I or II => Group III
    return 3


# ======================
# Compromiso en dos etapas (2-stage additive commitment)
# ======================

def tentative_assignment(route_data, current_time):
   #Determina si el courier puede llegar al restaurante antes de current_time + OPTIMIZATION_FREQUENCY (Horizonte).
    if not route_data:
        return False
    duracion_min = (route_data['duration'] / 60.0) * 0.5  # mitad del tiempo de viaje por simplificación, se podría mejorar con un modelo de tráfico y ubicando el tiempo exacto desde su ubicación actual al restaurante
    arrival_time = current_time + timedelta(minutes=duracion_min) 
    return arrival_time <= current_time + OPTIMIZATION_FREQUENCY #Bool donde si el tiempo de llegada es menor al horizonte se considera true en el return

def two_stage_commitment(courier, bundle, current_time, X_COMMITMENT=15):
    """
    Compromiso final: Si el repartidor puede llegar al restaurante antes de current_time + OPTIMIZATION_FREQUENCY 
    y todos los pedidos están listos, se hace un compromiso final (el repartidor recibe instrucciones para viajar al restaurante, recoger y entregar los pedidos).

    Compromiso parcial:
    Si el repartidor no puede cumplir la condición anterior, pero termina su última asignación antes 
    de current_time + OPTIMIZATION_FREQUENCY, entonces se hace un compromiso parcial (se instruye al 
    repartidor a viajar al restaurante y esperar allí una asignación definitiva).

    Ignorar la asignación:
    Si el repartidor no puede iniciar una nueva asignación antes de current_time + OPTIMIZATION_FREQUENCY
    la asignación se ignora.

    Excepción:
    Si alguno de los pedidos en el paquete lleva listo más de 15 minutos (X_COMMITMENT), se omiten las reglas anteriores y se fuerza un compromiso final.
    """
    # variable que revisa si alguna orden lleva lista más de 15 minutos
    ready_too_long = any(
        (current_time - o.ready_time).total_seconds() / 60.0 > X_COMMITMENT for o in bundle
    )
    
    # obtener la ruta del buldle
    route_data = get_route_details(
        courier.location,
        [o.restaurant.location for o in bundle] + [o.dropoff_loc for o in bundle]
    )
    if not route_data:
        return False  # no se puede asignar si no hay ruta

    # Built in function all() que revisa si todas las ordenes en el bundle están listas
    all_ready = all(o.ready_time <= current_time + OPTIMIZATION_FREQUENCY for o in bundle)
    
    # Excepción: si alguna orden lleva lista más de 15 minutos, se fuerza un compromiso final
    if ready_too_long:
        courier.current_route = {
            'orders': bundle,
            'route': route_data,
            'start_time': current_time,
            'completion_time': current_time + timedelta(seconds=route_data['duration']),
            'commitment_type': 'final'
        }
        return True

    # Caso 1: Compromiso final si las ordenes están listas y el repartidor puede llegar al restaurante antes de current_time + OPTIMIZATION_FREQUENCY
    if tentative_assignment(route_data, current_time) and all_ready:
        courier.current_route = {
            'orders': bundle,
            'route': route_data,
            'start_time': current_time,
            'completion_time': current_time + timedelta(seconds=route_data['duration']),
            'commitment_type': 'final'
        }
        return True
    else:
        # Caso 2: Compromiso parcial si el repartidor termina su última asignación antes de current_time + OPTIMIZATION_FREQUENCY
        inbound_only = get_route_details(courier.location, [bundle[0].restaurant.location])
        if inbound_only:
            courier.current_route = {
                'orders': bundle,
                'route': inbound_only,
                'start_time': current_time,
                'completion_time': current_time + timedelta(seconds=inbound_only['duration']),
                'commitment_type': 'partial'
            }
            return True

    # Caso 3: Ignorar la asignación si no se cumple ninguna de las condiciones anteriores
    return False

#def assign_bundles_to_couriers(couriers, bundles, current_time):

###############################################################################
# HELPER: earliest_possible_dropoff(bundle, courier, current_time)
###############################################################################
def earliest_possible_dropoff(bundle, courier, current_time):
    """
    Returns the earliest drop-off time if 'courier' starts delivering 'bundle' NOW
    (i.e., from courier.location at current_time).

    Simplistic approach:
      1) Compute inbound route to restaurant (time_inbound).
      2) Earliest pickup time = max{ bundle_ready_time, current_time + time_inbound + SERVICE_TIME}.
      3) After picking up, compute time from restaurant to all drop-offs in bundle.
      4) The final drop-off time is that earliest pickup + travel_to_customers + SERVICE_TIME * #orders).
    """
    if not bundle:
        return None

    # Step 1: inbound route from courier.location -> bundle[0].restaurant
    r_loc = bundle[0].restaurant.location
    inbound = get_route_details(courier.location, [r_loc])
    if not inbound:
        return None  # no route => no feasible assignment

    time_inbound_min = inbound["duration"] / 60.0

    # Step 2: earliest pickup
    bundle_ready_time = max(o.ready_time for o in bundle)
    service_min = SERVICE_TIME.total_seconds() / 60.0
    earliest_pickup = max(
        bundle_ready_time,
        current_time + timedelta(minutes=time_inbound_min + service_min)
    )

    # Step 3: route from restaurant to each drop-off (in the order they appear).
    #   We'll do a naive approach: restaurant -> dropoff1 -> dropoff2 -> ... -> dropoffN
    dropoff_points = [o.dropoff_loc for o in bundle] 
    route_outbound = get_route_details(r_loc, dropoff_points)
    if not route_outbound:
        return None
    time_outbound_min = route_outbound["duration"] / 60.0

    # Step 4: final drop-off time
    #   After picking up, we add time_outbound_min + half-service per order
    total_drop_service_min = service_min * len(bundle)
    final_dropoff = earliest_pickup + timedelta(minutes=time_outbound_min + total_drop_service_min)
    return final_dropoff





def earliest_pickup_estimate(bundle, courier, current_time):
    """
    Returns the earliest possible pickup time ignoring outbound deliveries.
    Just focuses on inbound route + half the pickup service time.
    """
    from src.getrouteOSMR import get_route_details
    r_loc = bundle[0].restaurant.location
    inbound = get_route_details(courier.location, [r_loc])
    if not inbound:
        return current_time + timedelta(days=999999)  # effectively infinite
    time_inbound_min = inbound["duration"] / 60.0
    half_sr = (SERVICE_TIME.total_seconds()/60.0)/2
    return current_time + timedelta(minutes=time_inbound_min + half_sr)


###############################################################################
# HELPER: do_linear_assignment(couriers, candidate_bundles, current_time)
#   Builds the cost matrix and solves bipartite matching for courier-bundle.
###############################################################################
def do_linear_assignment(couriers, candidate_bundles, current_time):
    """
    1) For each (courier,bundle), get a "score" from your code (calculate_bundle_score).
    2) Convert to a cost = -score (Hungarian is min-cost).
    3) Solve. Then two_stage_commitment for each matched pair.
    """
    if not couriers or not candidate_bundles:
        return

    # Filter out couriers who are already busy or off-duty
    free_couriers = [c for c in couriers if c.current_route is None and c.off_time > current_time]
    if not free_couriers:
        return

    num_couriers = len(free_couriers)
    num_bundles = len(candidate_bundles)
    print(f"      Building cost matrix for {num_couriers} couriers and {num_bundles} bundles...")

    cost_matrix = np.zeros((num_couriers, num_bundles), dtype=float)

    for i, courier in enumerate(free_couriers):
        for j, bundle in enumerate(candidate_bundles):
            score = calculate_bundle_score(bundle, courier, current_time)
            if score == float('-inf'):
                # infeasible => set cost high so it won't be chosen
                cost_matrix[i, j] = 1e9
            else:
                # cost is negative of the 'score' so we can minimize
                cost_matrix[i, j] = -score

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # For each matched pair, attempt two_stage_commitment
    for r, c in zip(row_ind, col_ind):
        if cost_matrix[r, c] >= 1e9:
            continue  # means it was infeasible

        courier = free_couriers[r]
        bundle  = candidate_bundles[c]

        # Double-check the courier is still free
        if courier.current_route is not None:
            continue

        # Attempt to assign
        success = two_stage_commitment(courier, bundle, current_time, X_COMMITMENT=15)
        if success:
            # The courier now has current_route set (partial or final).
            # If partial, the route can be updated in next optimization iteration.
            pass


###############################################################################
# MAIN ASSIGN FUNCTION: assign_bundles_to_couriers(couriers, bundles, current_time)
###############################################################################
def assign_bundles_to_couriers(couriers, bundles, current_time):
    """
    Implements the 3-priority scheme from Section 3.2:
      Group I  -> "already late" for target click-to-door
      Group II -> "can't be picked up at ready time"
      Group III -> all else

    Then runs a bipartite matching for each group in ascending order of group number,
    so that Group I (most urgent) is matched first, then II, then III.
    """
    if not couriers or not bundles:
        return

    # 1) Classify each bundle
    print(f"    Classifying {len(bundles)} bundles...")
    groupI, groupII, groupIII = [], [], []
    for b in bundles:
        g = classify_bundle(b, couriers, current_time)
        if g == 1:
            groupI.append(b)
        elif g == 2:
            groupII.append(b)
        else:
            groupIII.append(b)
    
    print(f"    Group I: {len(groupI)}, Group II: {len(groupII)}, Group III: {len(groupIII)}")

    # 2) Solve assignment in that order:
    #    Group I first => then Group II => then Group III
    if groupI:
        print("    Assigning Group I bundles...")
        do_linear_assignment(couriers, groupI, current_time)
    if groupII:
        print("    Assigning Group II bundles...")
        do_linear_assignment(couriers, groupII, current_time)
    if groupIII:
        print("    Assigning Group III bundles...")
        do_linear_assignment(couriers, groupIII, current_time)
