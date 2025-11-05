# ======================
# En esta sección, se importan librerías y módulos necesarios:
# - requests para hacer solicitudes HTTP (OSRM).
# - folium y polyline para la generación de mapas y decodificación de rutas.
# - restaurants y couriers para manejar listas de restaurantes y repartidores.

import folium
import polyline
import os
import pandas as pd
from datetime import datetime
from src.bundling import compute_target_bundle_size, generate_bundles_for_restaurant
from src.asignaciontentativa import assign_bundles_to_couriers, assign_order_to_nearest_courier
from src.config import PAY_PER_ORDER, MIN_PAY_PER_HOUR, ASSIGNMENT_HORIZON, OPTIMIZATION_FREQUENCY
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
        self.courier_id = None
        self.bundle_size = 1

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
        # current location (updates during simulation)
        self.location = location
        # base / start location (depot) — preserved for map visualizations
        self.start_location = location
        self.current_route = None
        # historial de rutas completadas para visualizar despues
        self.route_history = []
        self.earnings = 0.0
        self.orders_delivered = 0
        self.total_distance = 0.0
        self.shift_started = False  # Para controlar el cálculo del tiempo de turno
        self.bundles_picked_up = 0  # Número de bundles recogidos
        self.driving_time = 0.0  # Tiempo total conduciendo en minutos

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

def run_simulation(orders, couriers, restaurants, simulation_end, start_time=None, results_path="results/simulation_results.csv", courier_results_path=None):
    print(f"=== ENTERING run_simulation ===")
    print(f"  Orders: {len(orders)}, Couriers: {len(couriers)}, Restaurants: {len(restaurants)}")
    
    if start_time is None:
        start_time = datetime(2025, 1, 1, 8, 0)
    current_time = start_time  # punto de inicio de la simulación
    
    print(f"  Start time: {start_time}, End time: {simulation_end}")
    
    order_queue = deque(sorted(orders, key=lambda o: o.placement_time)) #se ordenan las ordenes por tiempo de colocación
    active_couriers = [] #se inicializa una lista que contendrá los repartidores activos
    
    use_fcfs = os.environ.get('FCFS_POLICY') == '1'
    policy_label = 'fcfs' if use_fcfs else 'rh'
    print(f"  Policy: {'FCFS' if use_fcfs else 'Rolling Horizon'}")

    delivered_orders = []

    visualized_deliveries_count = 0
    
    print(f"=== STARTING SIMULATION LOOP ===")
    
    iteration_count = 0

    while current_time < simulation_end:
        iteration_count += 1
        if iteration_count % 10 == 0:  # Print every 10 iterations to reduce noise
            print(f"\n--- Simulation time: {current_time} (iteration {iteration_count}) ---")

        for c in couriers:  #loop para revisar si un repartidor está disponible
            if c.on_time <= current_time and c not in active_couriers:
                active_couriers.append(c)
                c.shift_started = True
        
        while order_queue and order_queue[0].placement_time <= current_time: #mientras aun haya ordenes en la cola y la orden en la posicion 0 sea menor o igual al tiempo actual
            new_order = order_queue.popleft() #se saca la orden de la cola
            new_order.status = 'ready' #se cambia el estado de la orden a lista
            new_order.restaurant.orders.append(new_order) #se agrega la orden a la lista de ordenes del restaurante
         
        if (current_time.minute % 5) == 0: #cada que el tiempo actual sea multiplo de 5 minutos
            print(f"[{current_time}] Running assignment logic...")
            available_couriers = [c for c in active_couriers if not c.current_route and c.off_time > current_time] # se filtra la lista de repartidores activos para obtener los que no tienen rutas asignadas y que su tiempo de salida sea mayor al tiempo actual
            
            orders_ready = [o for rest in restaurants for o in rest.orders if o.status == "ready" and o.ready_time <= current_time + ASSIGNMENT_HORIZON] #se filtran las ordenes que esten listas segun el horizonte de asignación

            if use_fcfs:
                # Lógica FCFS: Asignar órdenes una por una al repartidor más cercano
                for order in orders_ready:
                    if order.status == 'ready':
                        assign_order_to_nearest_courier(order, available_couriers, current_time)
            else:
                # Lógica de Rolling Horizon (la que ya existía)
                couriers_available_hor = [c for c in available_couriers if c.off_time >= current_time + ASSIGNMENT_HORIZON] #se filtran los repartidores disponibles segun el horizonte de asignación
                
                print(f"  RH: {len(orders_ready)} orders ready, {len(couriers_available_hor)} couriers in horizon")
                
                target_bundle_size = compute_target_bundle_size(
                    current_time,
                    orders_ready,
                    couriers_available_hor,
                )
                print(f"  RH: target_bundle_size = {target_bundle_size}")

                all_bundles = []
                for rest in restaurants:
                    rst_bundles = generate_bundles_for_restaurant(
                        rest,
                        current_time,
                        target_bundle_size,
                        len(couriers_available_hor),
                    )
                    if rst_bundles:
                        all_bundles.extend(rst_bundles)
                
                print(f"  RH: Generated {len(all_bundles)} bundles from {len(restaurants)} restaurants")

                assign_bundles_to_couriers(available_couriers, all_bundles, current_time)
                print(f"  RH: Bundle assignment complete")
            print(f"[{current_time}] Assignment logic finished.")

        # actualizar progreso de rutas
        for c in active_couriers:
            if c.current_route and current_time >= c.current_route['completion_time']:
                if c.current_route['commitment_type'] == 'final':
                    for o in c.current_route['orders']:
                        o.status = 'delivered'
                        o.pickup_time = c.current_route['start_time']
                        o.delivery_time = c.current_route['completion_time']
                        o.courier_id = c.id
                        o.bundle_size = len(c.current_route['orders'])
                        c.orders_delivered += 1
                        delivered_orders.append(o)
                        print(f"Order {o.id} delivered.")
                    # Incrementar bundles recogidos (una ruta = un bundle)
                    c.bundles_picked_up += 1
                # actualizar ubicación al último punto de la ruta
                if c.current_route['route']['legs']:
                    last = c.current_route['route']['legs'][-1]['steps'][-1]['maneuver']['location']
                    from src.getrouteOSMR import as_latlon
                    c.location = as_latlon(last)
                    c.total_distance += c.current_route['route']['distance'] / 1000 # convert to km
                    # Sumar tiempo de conducción (duration en segundos -> minutos)
                    c.driving_time += c.current_route['route']['duration'] / 60.0
                # almacenar la ruta completada antes de limpiarla y guardar mapa
                c.route_history.append(c.current_route)
                if visualized_deliveries_count < 10 and c.current_route['commitment_type'] == 'final':
                    visualized_deliveries_count += 1
                    save_route_map(
                        c.current_route,
                        policy_label,
                        visualized_deliveries_count,
                    )
                
                # NUEVO: Guardar mapa COMPLETO con base del courier para TODOS los bundlings
                # (Se filtrarán después con generate_complete_bundles_index.py)
                if c.current_route['commitment_type'] == 'final':
                    save_complete_route_map(
                        c.current_route,
                        courier_base=c.start_location,
                        courier_id=c.id,
                        policy_label=policy_label,
                        bundling_number=c.bundles_picked_up  # número secuencial del bundle para este courier
                    )
                
                c.current_route = None

        current_time += OPTIMIZATION_FREQUENCY
    # calcular compensación final al terminar la simulación
    for c in couriers:
        c.final_compensation()

    # Guardar resumen de repartidores
    courier_summary_df = pd.DataFrame.from_records([
        {
            'courier_id': c.id,
            'orders_delivered': c.orders_delivered,
            'total_distance_km': c.total_distance,
            'shift_duration_hours': c.shift_duration_hours(),
            'bundles_picked_up': c.bundles_picked_up,
            'driving_time_minutes': c.driving_time,
        } for c in couriers
    ])
    if courier_results_path:
        courier_summary_df.to_csv(courier_results_path, index=False)

    # imprimir métricas simples
    for c in couriers:
        print(f"Courier {c.id}: orders={c.orders_delivered}, earnings=${c.earnings:.2f}, distance={c.total_distance:.2f}km")

    # Guardar resultados detallados
    all_orders_df = pd.DataFrame.from_records([
        {
            'order_id': o.id,
            'status': o.status,
            'placement_time': o.placement_time,
            'ready_time': o.ready_time,
            'pickup_time': o.pickup_time,
            'delivery_time': o.delivery_time,
            'click_to_door': o.get_click_to_door(),
            'ready_to_pickup': o.get_ready_to_pickup(),
            'courier_id': o.courier_id,
            'bundle_size': o.bundle_size
        } for o in orders
    ])
    all_orders_df.to_csv(results_path, index=False)

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

def visualize_complete_route(courier_route, courier_base):
    """Genera un mapa COMPLETO incluyendo la base del courier y la ruta completa.
    
    Mostrará:
    - Base del courier (azul)
    - Ruta completa desde base → restaurantes → clientes → base
    - Restaurantes (rojo)
    - Clientes (verde)
    """
    route = courier_route['route']
    coords = polyline.decode(route['geometry'])
    
    # Centro del mapa en la primera coordenada
    m = folium.Map(location=coords[0], zoom_start=13)
    
    # Dibujar ruta principal (azul)
    folium.PolyLine(coords, color='blue', weight=3, opacity=0.8, popup='Ruta del Bundle').add_to(m)
    
    # Marcador de la base del courier (azul)
    folium.Marker(
        location=courier_base,
        popup="Courier Base",
        icon=folium.Icon(color='blue', prefix='fa', icon='warehouse')
    ).add_to(m)
    
    # Marcadores de órdenes
    for i, order in enumerate(courier_route['orders'], 1):
        # Restaurante (rojo)
        folium.Marker(
            location=order.restaurant.location,
            popup=f"Restaurant #{i}",
            icon=folium.Icon(color='red', prefix='fa', icon='utensils')
        ).add_to(m)
        
        # Cliente (verde)
        folium.Marker(
            location=order.dropoff_loc,
            popup=f"Customer #{i}: {order.placement_time.strftime('%H:%M')}",
            icon=folium.Icon(color='green', prefix='fa', icon='map-pin')
        ).add_to(m)
    
    # Línea conectando base al primer punto de la ruta
    if coords and courier_base:
        folium.PolyLine(
            [courier_base, coords[0]], 
            color='gray', 
            weight=2, 
            opacity=0.5, 
            dash_array='5, 5',
            popup='Salida de base'
        ).add_to(m)
    
    return m

def save_route_map(courier_route, policy_label, delivery_number):
    """Save a route visualization to results/maps/<policy>/delivery_<n>.html."""
    m = visualize_route(courier_route)
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'maps', policy_label)
    os.makedirs(base_dir, exist_ok=True)
    filename = f"delivery_{delivery_number:02d}.html"
    filepath = os.path.join(base_dir, filename)
    m.save(filepath)
    rel_path = os.path.join('results', 'maps', policy_label, filename)
    print(f"    Saved route map: {rel_path}")
    return filepath

def save_complete_route_map(courier_route, courier_base, courier_id, policy_label, bundling_number):
    """Guarda un mapa COMPLETO del bundling incluyendo base del courier.
    
    Se guarda en: results/maps/<policy>/complete_bundles/courier_<id>_bundle_<n>.html
    """
    m = visualize_complete_route(courier_route, courier_base)
    base_dir = os.path.join(
        os.path.dirname(__file__), '..', 'results', 'maps', 
        policy_label, 'complete_bundles'
    )
    os.makedirs(base_dir, exist_ok=True)
    
    # Información del bundling
    num_orders = len(courier_route['orders'])
    total_distance = courier_route['route']['distance'] / 1000  # convertir a km
    total_time = courier_route['route']['duration'] / 60  # convertir a minutos
    
    filename = f"courier_{courier_id}_bundle_{bundling_number:03d}.html"
    filepath = os.path.join(base_dir, filename)
    
    # Agregar información en el título
    m.get_root().html.add_child(folium.Element(f"""
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size: 12px; padding: 10px; border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <b>Bundle #{bundling_number}</b><br>
        Courier ID: {courier_id}<br>
        Órdenes: {num_orders}<br>
        Distancia: {total_distance:.2f} km<br>
        Tiempo: {total_time:.1f} min<br>
        <i style="color: #666; font-size: 10px;">Ruta completa desde base</i>
    </div>
    """))
    
    m.save(filepath)
    rel_path = os.path.join('results', 'maps', policy_label, 'complete_bundles', filename)
    print(f"    💾 Saved complete bundle map: {rel_path}")
    return filepath

# ======================
# Inicialización
# ======================

class Restaurant:
    def __init__(self, rest_id, location):
        self.id = rest_id
        self.location = location  # (lat, lon)
        self.orders = []

if __name__ == "__main__":
    restaurants_df = pd.read_csv("data/restaurants.csv")
    restaurants = [
        Restaurant(row['id'], (row['latitude'], row['longitude']))
        for _, row in restaurants_df.iterrows()
    ]

    couriers_df = pd.read_csv("data/couriers.csv", parse_dates=["on_time", "off_time"])
    couriers = [
        Courier(row['id'], row['on_time'], row['off_time'], (row['start_latitude'], row['start_longitude']))
        for _, row in couriers_df.iterrows()
    ]
    
    test_orders = [
        Order(1, restaurants[0], datetime(2025,1,1,8,5), datetime(2025,1,1,8,15), (19.4360,-99.1320)),
        Order(2, restaurants[1], datetime(2025,1,1,8,10), datetime(2025,1,1,8,20), (19.4370,-99.1310)),
        Order(3, restaurants[2], datetime(2025,1,1,8,15), datetime(2025,1,1,8,25), (19.4380,-99.1300)),
    ] #necesitamos agregar instancias de prueba
    
    run_simulation(
        orders=test_orders,
        couriers=couriers,
        restaurants=restaurants,
        simulation_end=datetime(2025, 1, 1, 12, 0),
        results_path="results/test_results.csv",
        courier_results_path="results/test_couriers.csv"
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
