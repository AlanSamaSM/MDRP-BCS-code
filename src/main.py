# ======================
# En esta sección, se importan librerías y módulos necesarios:
# - requests para hacer solicitudes HTTP (OSRM).
# - folium y polyline para la generación de mapas y decodificación de rutas.
# - restaurants y couriers para manejar listas de restaurantes y repartidores.

import folium
import polyline
import os
import restaurantsList as rts
import couriersList as crs

from datetime import datetime
from bundling import compute_target_bundle_size, generate_bundles_for_restaurant
from asignaciontentativa import assign_bundles_to_couriers
from config import PAY_PER_ORDER, MIN_PAY_PER_HOUR, ASSIGNMENT_HORIZON, OPTIMIZATION_FREQUENCY
from collections import deque


class Order:
    def __init__(self, order_id, restaurant, placement_time, ready_time, dropoff_loc):
        self.restaurant = restaurant 
        self.placement_time = placement_time
        self.ready_time = ready_time
        self.dropoff_loc = dropoff_loc
        self.status = "pending"
        # Para las métricas:
        self.pickup_time = None
        self.delivery_time = None
        self.id = order_id

    def get_click_to_door(self):
        #calcula el click to door en minutos, que es la diferencia entre delivery_time y placement_time
        if self.delivery_time:
            return (self.delivery_time - self.placement_time).total_seconds() / 60.0
        return None

    def get_ready_to_pickup(self):
        #calcula el tiempo de espera en minutos, que es la diferencia entre pickup_time y ready_time
        if self.pickup_time:
            return (self.pickup_time - self.ready_time).total_seconds() / 60.0
        return None

class Courier:
    def __init__(self, courier_id, on_time, off_time, location):
        self.id = courier_id
        self.on_time = on_time
        self.off_time = off_time
        self.location = location
        self.current_route = None
        # historial de rutas completadas para visualizar despues
        self.route_history = []
        self.earnings = 0.0
        self.orders_delivered = 0
        self.shift_started = False  # Para controlar el cálculo del tiempo de turno

    def shift_duration_hours(self):
        #aqui se calcula la duracion del turno del repartidor en HORAS
        diff = (self.off_time - self.on_time).total_seconds() / 3600.0
        return diff if diff > 0 else 0 # solo para no tener valores negativos

    def final_compensation(self):
        #para decidor si se paga por hora o por ordenes

        pay_by_orders = self.orders_delivered * PAY_PER_ORDER
        pay_by_minimum = self.shift_duration_hours() * MIN_PAY_PER_HOUR
        if pay_by_orders < pay_by_minimum:
            self.earnings = pay_by_minimum
        else:
            self.earnings = pay_by_orders



# ======================
# simulación
# ======================

def run_simulation(orders, couriers, simulation_end, start_time=None):
    if start_time is None:
        start_time = datetime(2025, 1, 1, 8, 0)
    current_time = start_time  # punto de inicio de la simulación
    order_queue = deque(sorted(orders, key=lambda o: o.placement_time)) #se ordenan las ordenes por tiempo de colocación
    active_couriers = [] #se inicializa una lista que contendrá los repartidores activos
    
    while current_time < simulation_end:
        for c in couriers:  #loop para revisar si un repartidor está disponible
            if c.on_time <= current_time and c not in active_couriers:
                active_couriers.append(c)
                c.shift_started = True
        
        while order_queue and order_queue[0].placement_time <= current_time: #mientras aun haya ordenes en la cola y la orden en la posicion 0 sea menor o igual al tiempo actual
            new_order = order_queue.popleft() #se saca la orden de la cola
            new_order.status = 'ready' #se cambia el estado de la orden a lista
            new_order.restaurant.orders.append(new_order) #se agrega la orden a la lista de ordenes del restaurante
         
        if (current_time.minute % 5) == 0: #cada que el tiempo actual sea multiplo de 5 minutos
            available_couriers = [c for c in active_couriers if not c.current_route and c.off_time > current_time] # se filtra la lista de repartidores activos para obtener los que no tienen rutas asignadas y que su tiempo de salida sea mayor al tiempo actual
            
            orders_ready = [o for rest in rts.restaurantList for o in rest.orders if o.status == "ready" and o.ready_time <= current_time + ASSIGNMENT_HORIZON] #se filtran las ordenes que esten listas segun el horizonte de asignación

            couriers_available_hor = [c for c in available_couriers if c.off_time >= current_time + ASSIGNMENT_HORIZON] #se filtran los repartidores disponibles segun el horizonte de asignación
            
            #se calcula el valor objetivo de Zt, tamaño de los bundles

            target_bundle_size = compute_target_bundle_size(
                current_time,
                orders_ready,
                couriers_available_hor,
            )

            
            all_bundles = []

            #se busca en los restaurantes y se generan los bundles, se agregan a la lista de bundles all_bundles
            for rest in rts.restaurantList:
                rst_bundles = generate_bundles_for_restaurant(
                    rest,
                    current_time,
                    target_bundle_size,
                    len(couriers_available_hor),
                )
                if rst_bundles:
                    all_bundles.extend(rst_bundles)

            #se asignan los bundles a los repartidores disponibles

            assign_bundles_to_couriers(available_couriers, all_bundles, current_time)

        # actualizar progreso de rutas
        for c in active_couriers:
            if c.current_route and current_time >= c.current_route['completion_time']:
                if c.current_route['commitment_type'] == 'final':
                    for o in c.current_route['orders']:
                        o.status = 'delivered'
                        o.pickup_time = c.current_route['start_time']
                        o.delivery_time = c.current_route['completion_time']
                        c.orders_delivered += 1
                # actualizar ubicación al último punto de la ruta
                if c.current_route['route']['legs']:
                    last = c.current_route['route']['legs'][-1]['steps'][-1]['maneuver']['location']
                    from getrouteOSMR import as_latlon
                    c.location = as_latlon(last)
                # almacenar la ruta completada antes de limpiarla y guardar mapa
                c.route_history.append(c.current_route)
                filename = f"courier{c.id}_route{len(c.route_history)}.html"
                save_route_map(c.current_route, filename)
                c.current_route = None

        current_time += OPTIMIZATION_FREQUENCY

    # calcular compensación final al terminar la simulación
    for c in couriers:
        c.final_compensation()

    # imprimir métricas simples
    for c in couriers:
        print(f"Courier {c.id}: orders={c.orders_delivered}, earnings=${c.earnings:.2f}")

# ======================
# Visualización de la ruta
# ======================

def visualize_route(courier_route):
    """Genera un mapa con la ruta del courier seleccionado."""
    route = courier_route['route']
    coords = polyline.decode(route['geometry'])
    
    m = folium.Map(location=coords[0], zoom_start=13)
    folium.PolyLine(coords, color='blue', weight=2.5, opacity=1).add_to(m)

    for order in courier_route['orders']:
        folium.Marker(
            location=order.restaurant.location,
            popup="Restaurant",
            icon=folium.Icon(color='red')
        ).add_to(m)

        folium.Marker(
            location=order.dropoff_loc,
            popup=f"Customer: {order.placement_time.strftime('%H:%M')}",
            icon=folium.Icon(color='green')
        ).add_to(m)
    
    return m

def save_route_map(courier_route, filename):
    """Save a route visualization to the maps folder."""
    m = visualize_route(courier_route)
    os.makedirs("maps", exist_ok=True)
    filepath = os.path.join("maps", filename)
    m.save(filepath)
    return filepath

# ======================
# Inicialización
# ======================

if __name__ == "__main__":
    restaurants = rts.restaurantList

    couriers = [Courier(*c) for c in crs.courierList]
    
    test_orders = [
        Order(1, restaurants[0], datetime(2025,1,1,8,5), datetime(2025,1,1,8,15), (19.4360,-99.1320)),
        Order(2, restaurants[1], datetime(2025,1,1,8,10), datetime(2025,1,1,8,20), (19.4370,-99.1310)),
        Order(3, restaurants[2], datetime(2025,1,1,8,15), datetime(2025,1,1,8,25), (19.4380,-99.1300)),
    ] #necesitamos agregar instancias de prueba
    
    run_simulation(
        orders=test_orders,
        couriers=couriers,
        simulation_end=datetime(2025, 1, 1, 12, 0)
    )
    # Visualizar la ultima ruta ejecutada
    active_courier = next((c for c in couriers if c.current_route), None)
    route_to_show = None
    if active_courier and active_courier.current_route:
        route_to_show = active_courier.current_route
    else:
        # si no hay ruta activa, tomar la ultima completada de cualquier courier
        for c in couriers:
            if c.route_history:
                route_to_show = c.route_history[-1]
                break
    if route_to_show:
        map_ = visualize_route(route_to_show)
        map_.save("mdrp_simulation.html")
    else:
        print("No courier route found to visualize.")
