from datetime import timedelta
import numpy as np
from scipy.optimize import linear_sum_assignment

from src.config import (
    OPTIMIZATION_FREQUENCY,
    TARGET_CLICK_TO_DOOR,
    SERVICE_TIME,
    MAX_WAIT_BEFORE_FORCED_COMMIT,
)
from src.getrouteOSMR import get_route_details
from src.bundling import calculate_bundle_score
from src.schedule import plan_route, final_route

def assign_order_to_nearest_courier(order, couriers, current_time):
    """
    Assigns a single order to the nearest available courier (FCFS logic).
    The courier waits at the restaurant if the order is not ready yet.
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
        plan = plan_route(best_courier.location, current_time, [order])
        if plan:
            best_courier.current_route = final_route(plan, [order], current_time)
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

def two_stage_commitment(courier, bundle, current_time):
    """
    Two-stage additive commitment as per Reyes (2018), Section 3.3:
    
    1. Final commitment: Si el repartidor puede llegar al restaurante antes de current_time + OPTIMIZATION_FREQUENCY 
       y todos los pedidos están listos, se hace un compromiso final.
    
    2. Partial commitment: Si el repartidor no puede cumplir la condición anterior, pero termina su última 
       asignación antes de current_time + OPTIMIZATION_FREQUENCY, se hace un compromiso parcial (viajar al restaurante).
    
    3. Ignore: Si el repartidor no puede iniciar antes de current_time + OPTIMIZATION_FREQUENCY, se ignora.
    
    4. Exception: Si alguno de los pedidos lleva listo más de MAX_WAIT_BEFORE_FORCED_COMMIT, se fuerza compromiso final.
    """
    # Excepción: Verificar si alguna orden lleva demasiado tiempo lista (forced commit)
    max_wait_minutes = MAX_WAIT_BEFORE_FORCED_COMMIT.total_seconds() / 60.0
    ready_too_long = any(
        (current_time - o.ready_time).total_seconds() / 60.0 > max_wait_minutes for o in bundle
    )
    
    # ruta y tiempos del bundle (courier -> restaurante -> entregas)
    plan = plan_route(courier.location, current_time, bundle)
    if not plan:
        return False  # no se puede asignar si no hay ruta

    # Built in function all() que revisa si todas las ordenes en el bundle están listas
    all_ready = all(o.ready_time <= current_time + OPTIMIZATION_FREQUENCY for o in bundle)
    # el courier llega al restaurante dentro de la época actual
    reaches_restaurant = plan['arrival_restaurant'] <= current_time + OPTIMIZATION_FREQUENCY

    # Excepción (orden lista hace más de x minutos) o Caso 1: compromiso final
    if ready_too_long or (reaches_restaurant and all_ready):
        courier.current_route = final_route(plan, bundle, current_time)
        for o in bundle:
            o.status = 'assigned'
        return True
    else:
        # Caso 2: Compromiso parcial si el repartidor termina su última asignación antes de current_time + OPTIMIZATION_FREQUENCY
        restaurant_loc = bundle[0].restaurant.location
        inbound_only = get_route_details(courier.location, [restaurant_loc])
        if inbound_only:
            courier.current_route = {
                'orders': bundle,
                'route': inbound_only,
                'waypoints': [restaurant_loc],
                'start_time': current_time,
                'completion_time': current_time + timedelta(seconds=inbound_only['duration']),
                'commitment_type': 'partial'
            }
            # No marcar como 'assigned': partial commit solo desplaza al courier
            # al restaurante; la orden debe ser re-evaluada en el siguiente ciclo.
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

    Uses the same timing rules as the executed route (src/schedule.py):
    the last drop-off of courier -> restaurant -> drop-offs.
    """
    plan = plan_route(courier.location, current_time, bundle)
    if not plan:
        return None  # no route => no feasible assignment
    return max(plan['dropoff_times'])





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

        # Attempt to assign (using config parameter instead of hardcoded value)
        success = two_stage_commitment(courier, bundle, current_time)
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
