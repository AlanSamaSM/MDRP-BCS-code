import requests

# ======================
# Funcion de ruteo OSRM
# ======================

def get_route_details(start_coords, waypoints):
    """
    Llama a OSRM para obtener la ruta y duración entre un punto inicial y varios 'waypoints'.
    Retorna la primera ruta en caso de éxito, o None si falla.
    """
    coordinates = ";".join([f"{lon},{lat}" for lat, lon in [start_coords] + waypoints])
    url = f"http://router.project-osrm.org/route/v1/driving/{coordinates}"
    params = {"overview": "full", "steps": "true", "annotations": "true"}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if data["code"] == "Ok":
            return data["routes"][0]
    except Exception as e:
        print(f"Routing error: {e}")
    return None

