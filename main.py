# ======================
# En esta sección, se importan librerías y módulos necesarios:
# - requests para hacer solicitudes HTTP (OSRM).
# - folium y polyline para la generación de mapas y decodificación de rutas.
# - restaurants y couriers para manejar listas de restaurantes y repartidores.
# - random, datetime, collections para manejo de datos y fechas.
# ======================
import folium
import polyline
import restaurantsList as rts
import couriersList as crs
from datetime import datetime, timedelta
from bundling import compute_target_bundle_size, generate_bundles_for_restaurant
from asignaciontentativa import assign_bundles_to_couriers
from config import PAY_PER_ORDER, MIN_PAY_PER_HOUR, DELTA_1, DELTA_2
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


# ======================
# simulación
# ======================

def run_simulation(orders, couriers, simulation_end):
    current_time = datetime.min #equivalente a 00:00:00
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
            
            orders_ready = [] #se filtran las ordenes que esten listas segun el horizonte de asignación

            couriers_available_hor =[] #se filtran los repartidores disponibles segun el horizonte de asignación
            
            #se calcula el valor objetivo de Zt, tamaño de los bundles
            target_bundle_size = compute_target_bundle_size(orders_ready, couriers_available_hor)
            
            all_bundles = []

            #se busca en los restaurantes y se generan los bundles, se agregan a la lista de bundles all_bundles
            for rest in rts.restaurantList:
                rst_bundles = generate_bundles_for_restaurant(rest, current_time, target_bundle_size, couriers_available_hor)
                if rst_bundles:
                    all_bundles.extend(rst_bundles)

            #se asignan los bundles a los repartidores disponibles
            assign_bundles_to_couriers(available_couriers, all_bundles, current_time)

            #asignación

            #compensación de repartidores 



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
            location=order.restaurant.location[::-1],
            popup="Restaurant",
            icon=folium.Icon(color='red')
        ).add_to(m)
        
        folium.Marker(
            location=order.dropoff_loc[::-1],
            popup=f"Customer: {order.placement_time.strftime('%H:%M')}",
            icon=folium.Icon(color='green')
        ).add_to(m)
    
    return m

# ======================
# Inicialización
# ======================

if __name__ == "__main__":
    restaurants = rts.restaurantList
    couriers = crs.courierList
    
    test_orders = [] #necesitamos agregar instancias de prueba
    
    run_simulation(
        orders=test_orders,
        couriers=[Courier(*c) for c in couriers], #lista de repartidores almacenados en couriersList.py
        simulation_end=datetime(2025, 1, 1, 12, 0)
    )        
    #cisualizador de rutas de repartidor
    active_courier = next((c for c in couriers if c.current_route), None)
    if active_courier and active_courier.current_route:
        map_ = visualize_route(active_courier.current_route)
        map_.save("mdrp_simulation.html")
    else:
        print("No active courier route found.")
