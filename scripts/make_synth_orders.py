import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points
from datetime import datetime, timedelta
import os

# locate restaurants geojson in common locations
possible_paths = [
    os.path.join("data", "la_paz_restaurants.geojson"),
    "la_paz_restaurants.geojson",
]
gdf_rest = None
for p in possible_paths:
    if os.path.exists(p):
        gdf_rest = gpd.read_file(p)
        break

if gdf_rest is None:
    raise FileNotFoundError(
        "la_paz_restaurants.geojson not found. Expected it under 'data/' or the repository root.\n"
        "Place the file at 'data/la_paz_restaurants.geojson' or adjust the script to point to its location."
    )

# 1. Parámetros de generación
start     = datetime(2025, 7, 3, 11, 0, 0)   # arranque a las 11 am
duration  = 3 * 60                           # 180 min
lam       = 8                                # λ del Poisson

# jitter/sampling configuration
JITTER_SIGMA = 0.005   # degrees (~500m). Reduced to avoid jumping into the sea
LAND_BUFFER  = 0.01    # degrees (~1km) buffer around restaurant convex hull to define valid land area

# 2. Generar llegadas Poisson minuto a minuto
orders_per_min = np.random.poisson(lam, duration)
minutes   = np.repeat(range(duration), orders_per_min).astype(int).tolist()

ts = [start + timedelta(minutes=m) for m in minutes]

# 3. Asignar restaurante y tiempos de preparación
prep = np.clip(np.random.normal(8, 2, len(ts)), 4, None).astype(int).tolist()

# Build a land polygon from user-defined coordinates
# Coordinates provided as (lat, lon) pairs; we'll convert to (lon, lat)
POLYGON_COORDS = [
    (24.124041, -110.311612),
    (24.133011, -110.335855),
    (24.159317, -110.309647),
    (24.147104, -110.292893),
]

# Convert to shapely polygon (lon, lat order)
poly_pts = [(lon, lat) for lat, lon in POLYGON_COORDS]
user_poly = Polygon(poly_pts)

# Use the user polygon as the land polygon (buffer can be applied if needed)
land_poly = user_poly.buffer(0)

# Replace restaurant locations by sampling uniformly inside the user polygon so
# restaurants are spread across the area. Preserve the original number of restaurants.
def sample_point_in_polygon(polygon, max_tries=1000):
    """Uniformly sample a point inside a (Multi)Polygon using rejection sampling."""
    minx, miny, maxx, maxy = polygon.bounds
    for _ in range(max_tries):
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        p = Point(x, y)
        if p.within(polygon):
            return p
    # fallback: return polygon.representative_point()
    return polygon.representative_point()


def sample_n_points_in_polygon(polygon, n):
    pts = []
    for _ in range(n):
        pts.append(sample_point_in_polygon(polygon))
    return pts


new_rest_pts = sample_n_points_in_polygon(land_poly, len(gdf_rest))
# replace geometries in gdf_rest with sampled points
gdf_rest = gdf_rest.copy()
gdf_rest.geometry = gpd.GeoSeries(new_rest_pts, crs=gdf_rest.crs)

# Sample destination points uniformly inside land_poly
dest_pts = [sample_point_in_polygon(land_poly) for _ in range(len(ts))]

# Assign each destination to the nearest restaurant (Euclidean nearest)
rest_x = gdf_rest.geometry.x.values
rest_y = gdf_rest.geometry.y.values
rest_idx = []
for p in dest_pts:
    dx = rest_x - p.x
    dy = rest_y - p.y
    idx = int(np.argmin(dx*dx + dy*dy))
    rest_idx.append(idx)

# 4. Armar DataFrame
df = pd.DataFrame({
    "order_id":      range(len(ts)),
    "restaurant_id": rest_idx,
    "created_at":    ts,
    "ready_at":      [t + timedelta(minutes=int(p)) for t, p in zip(ts, prep)],
    "rest_lat":      gdf_rest.geometry.y.values[rest_idx],
    "rest_lon":      gdf_rest.geometry.x.values[rest_idx],
    "dest_lat":      [p.y for p in dest_pts],
    "dest_lon":      [p.x for p in dest_pts],
})

# Save with a distinct name to indicate coordinates were limited/snapped
out_dir = "data"
os.makedirs(out_dir, exist_ok=True)
out_name = os.path.join(out_dir, "synthetic_lapaz_orders_limited.csv")
df.to_csv(out_name, index=False)
print("Pedidos sintetizados:", len(df), "->", out_name)
