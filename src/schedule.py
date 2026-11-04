"""Temporización de rutas según Reyes et al. (2018), Sección 2.1.

Una ruta final recorre: ubicación del courier -> restaurante -> entrega_1 -> ... -> entrega_n.

- Recolección:  pickup = max(ready_time del agrupamiento, llegada al restaurante + s_r/2)
- Salida del restaurante: pickup + s_r/2
- Entrega k:    llegada al cliente k + s_o/2
- Salida del cliente k: entrega k + s_o/2

Con s_r = s_o = SERVICE_TIME (4 min). El courier queda libre al salir del último cliente.
"""
from datetime import timedelta

from src.config import SERVICE_TIME
from src.getrouteOSMR import get_route_details

HALF_SERVICE = SERVICE_TIME / 2


def plan_route(courier_location, start_time, bundle):
    """Calcula ruta y tiempos de una asignación final.

    Retorna un diccionario con la ruta OSRM, los waypoints, la llegada al
    restaurante, el instante de recolección, el instante de entrega de cada
    orden (en el orden de ``bundle``) y el instante en que el courier queda
    libre; o ``None`` si no hay ruta.
    """
    if not bundle:
        return None
    waypoints = [bundle[0].restaurant.location] + [o.dropoff_loc for o in bundle]
    route = get_route_details(courier_location, waypoints)
    if not route or len(route.get('legs') or []) != len(waypoints):
        return None
    legs = route['legs']

    arrival_restaurant = start_time + timedelta(seconds=legs[0]['duration'])
    bundle_ready = max(o.ready_time for o in bundle)
    pickup_time = max(bundle_ready, arrival_restaurant + HALF_SERVICE)

    t = pickup_time + HALF_SERVICE  # salida del restaurante
    dropoff_times = []
    for leg in legs[1:]:
        dropoff = t + timedelta(seconds=leg['duration']) + HALF_SERVICE
        dropoff_times.append(dropoff)
        t = dropoff + HALF_SERVICE  # salida del cliente

    return {
        'route': route,
        'waypoints': waypoints,
        'arrival_restaurant': arrival_restaurant,
        'pickup_time': pickup_time,
        'dropoff_times': dropoff_times,
        'completion_time': t,
    }


def final_route(plan, bundle, start_time):
    """Construye el ``current_route`` de un compromiso final a partir de ``plan_route``."""
    return {
        'orders': list(bundle),
        'route': plan['route'],
        'waypoints': plan['waypoints'],
        'start_time': start_time,
        'pickup_time': plan['pickup_time'],
        'dropoff_times': plan['dropoff_times'],
        'completion_time': plan['completion_time'],
        'commitment_type': 'final',
    }
