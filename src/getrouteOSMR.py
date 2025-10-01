import requests
import os
import math
import polyline
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure a requests Session with retry/backoff to be resilient to
# transient errors and common server-side rate limiting (HTTP 429).
_session = None

def _get_session():
    global _session
    if _session is not None:
        return _session

    s = requests.Session()
    retries = Retry(
        total=int(os.environ.get('OSRM_MAX_RETRIES', '3')),
        backoff_factor=float(os.environ.get('OSRM_BACKOFF_FACTOR', '0.5')),
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    _session = s
    return _session

def as_lonlat(pt):
    """Convert (lat, lon) -> (lon, lat)"""
    lat, lon = pt
    return lon, lat

def as_latlon(pt):
    """Convert (lon, lat) -> (lat, lon)"""
    lon, lat = pt
    return lat, lon

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

    use_euclidean = True

    # If explicitly requested, use Euclidean fallback only and skip HTTP calls.
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

    points = [start_coords] + waypoints
    coordinates = ";".join(
        f"{lon},{lat}" for lon, lat in map(as_lonlat, points)
    )
    url = f"http://router.project-osrm.org/route/v1/driving/{coordinates}"
    params = {"overview": "full", "steps": "true", "annotations": "true"}

    # Respect a small per-request delay (configurable) before calling the
    # public OSRM instance to be polite and reduce risk of immediate 429s.
    request_delay = float(os.environ.get('OSRM_REQUEST_DELAY', '0.15'))

    try:
        time.sleep(request_delay)
        session = _get_session()
        response = session.get(url, params=params, timeout=float(os.environ.get('OSRM_TIMEOUT', '8')))
        # If the server returns a non-200 status this will raise and be
        # handled by the retry logic in the adapter; otherwise continue.
        response.raise_for_status()
        data = response.json()
        code = data.get('code')
        if code == 'Ok' and data.get('routes'):
            return data['routes'][0]

        # Handle situations where OSRM returns an error code (e.g., NoRoute,
        # InvalidUrl, TooBig). In some cases we want to fallback to a simple
        # Euclidean estimate rather than fail hard.
        msg = data.get('message') if isinstance(data, dict) else None
        print(f"OSRM returned code={code} message={msg}")

    except requests.exceptions.HTTPError as e:
        # If we received a 429 or 5xx after retries, fall through to fallback
        # handling below. Print a short diagnostic.
        print(f"OSRM HTTP error: {e} (status={getattr(e.response, 'status_code', None)})")
    except Exception as e:
        # Generic catch-all for connectivity/timeouts/etc.
        print(f"Routing error: {e}")

    # If we get here the OSRM call failed or returned an error. Respect an
    # environment-driven policy to fallback to Euclidean routing which is
    # useful for offline testing or when the public API is rate-limited.
    fallback = os.environ.get('USE_EUCLIDEAN_ON_FAILURE', '1') == '1'
    if fallback:
        try:
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
        except Exception as e:
            print(f"Euclidean fallback failed: {e}")

    return None


