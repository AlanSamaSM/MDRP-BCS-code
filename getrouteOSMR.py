import requests
import os
import math
import polyline

# ======================
# Funcion de ruteo OSRM
# ======================

def get_route_details(start_coords, waypoints):
    """Return routing information for start_coords -> waypoints.

    If the environment variable ``USE_EUCLIDEAN`` is set to ``1`` the route is
    computed using simple Euclidean distance with constant speed given by the
    ``METERS_PER_MINUTE`` environment variable (default 320).  Otherwise the
    function queries the public OSRM service as before.
    """

    use_euclidean = os.environ.get("USE_EUCLIDEAN", "0") == "1"

    if use_euclidean:
        speed = float(os.environ.get("METERS_PER_MINUTE", 320))
        coords = [start_coords] + waypoints
        distance = 0.0
        legs = []
        for a, b in zip(coords[:-1], coords[1:]):
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            distance += seg
            legs.append({"steps": [{"maneuver": {"location": (b[1], b[0])}}]})
        duration_sec = (distance / speed) * 60.0
        geometry = polyline.encode(coords)
        return {"distance": distance, "duration": duration_sec, "geometry": geometry, "legs": legs}

    coordinates = ";".join([f"{lon},{lat}" for lat, lon in [start_coords] + waypoints])
    url = f"http://router.project-osrm.org/route/v1/driving/{coordinates}"
    params = {"overview": "full", "steps": "true", "annotations": "true"}

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if data.get("code") == "Ok":
            return data["routes"][0]
    except Exception as e:
        print(f"Routing error: {e}")
    return None


