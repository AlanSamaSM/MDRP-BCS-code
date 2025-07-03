import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timedelta

gdf_rest = gpd.read_file("la_paz_restaurants.geojson")

# 1. Parámetros de generación
start     = datetime(2025, 7, 3, 11, 0, 0)   # arranque a las 11 am
duration  = 3 * 60                           # 180 min
lam       = 8                                # λ del Poisson

# 2. Generar llegadas Poisson minuto a minuto
orders_per_min = np.random.poisson(lam, duration)
minutes   = np.repeat(range(duration), orders_per_min).astype(int).tolist()

ts = [start + timedelta(minutes=m) for m in minutes]

# 3. Asignar restaurante y tiempos de preparación
rest_idx = np.random.choice(len(gdf_rest), size=len(ts))
prep = np.clip(np.random.normal(8, 2, len(ts)), 4, None).astype(int).tolist()
def jitter(pt, σ=0.015):
    return Point(pt.x + np.random.normal(scale=σ),
                 pt.y + np.random.normal(scale=σ))

dest_pts = [jitter(gdf_rest.geometry[i]) for i in rest_idx]

# 4. Armar DataFrame
df = pd.DataFrame({
    "order_id":      range(len(ts)),
    "restaurant_id": rest_idx,
    "created_at":    ts,
    "ready_at":      [t + timedelta(minutes=int(p)) for t, p in zip(ts, prep)],
    "rest_lat":      gdf_rest.geometry.y.values[rest_idx        º],
    "rest_lon":      gdf_rest.geometry.x.values[rest_idx],
    "dest_lat":      [p.y for p in dest_pts],
    "dest_lon":      [p.x for p in dest_pts],
})

df.to_csv("synthetic_lapaz_orders.csv", index=False)
print("Pedidos sintetizados:", len(df))
