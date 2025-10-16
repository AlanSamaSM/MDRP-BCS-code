import geopandas as gpd
import random

# ---------- 1. Cargar restaurantes desde el OSM ya filtrado ----------
gdf_restaurants = gpd.read_file("map.osm")  # o map.osm si lo parseas directo

# ---------- 2. Ordenar por cercanía al “centro” y elegir 25 ----------
punto_centro = gdf_restaurants.unary_union.centroid          # calcula centroide global
gdf_restaurants["dist_to_center"] = gdf_restaurants.distance(punto_centro)

gdf_sample = (
    gdf_restaurants
    .sort_values("dist_to_center")
    .head(30)              # los 30 más cercanos
    .reset_index(drop=True)
)

# ---------- 3. Guardar resultado ----------
gdf_sample[["name", "geometry"]].to_file(
    "la_paz_restaurants.geojson",
    driver="GeoJSON"
)
print("Hecho: se guardó la muestra ‘la_paz_restaurants.geojson’")
