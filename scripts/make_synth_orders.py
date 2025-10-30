"""Generador de pedidos sintéticos calibrado con LaDe (Wu et al., 2025).

Produce aproximadamente 1,000 pedidos distribuidos entre las 08:00 y las 19:00,
con picos de demanda alrededor de las 09:00 y 17:00 horas. El script reemplaza
las ubicaciones de restaurantes por puntos uniformes dentro del polígono urbano
definido y asigna destinos cercanos para replicar la densidad observada (~1 km).
"""

import argparse
import os
from datetime import datetime, timedelta

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon


DEFAULT_START = datetime(2025, 7, 3, 8, 0, 0)
DEFAULT_SHIFT_MINUTES = 11 * 60  # 08:00 a 19:00
DEFAULT_TARGET_ORDERS = 1000
DEFAULT_SEED = 2025

MORNING_PEAK_HOUR = 9
EVENING_PEAK_HOUR = 17
PEAK_STD_MINUTES = 45
BASE_INTENSITY = 0.6
MORNING_PEAK_WEIGHT = 2.4
EVENING_PEAK_WEIGHT = 2.0

POLYGON_COORDS = [
    (24.124041, -110.311612),
    (24.133011, -110.335855),
    (24.159317, -110.309647),
    (24.147104, -110.292893),
]


def locate_restaurants():
    """Read the restaurants GeoJSON from common locations."""
    possible_paths = [
        os.path.join("data", "la_paz_restaurants.geojson"),
        "la_paz_restaurants.geojson",
    ]
    for candidate in possible_paths:
        if os.path.exists(candidate):
            return gpd.read_file(candidate)
    raise FileNotFoundError(
        "la_paz_restaurants.geojson not found. Expected it under 'data/' or the repository root.\n"
        "Place the file at 'data/la_paz_restaurants.geojson' or adjust the script to point to its location."
    )


def build_intensity_profile(duration_minutes, rng, target_orders):
    """Generate a non-homogeneous Poisson intensity with LaDe-like peaks."""
    minute_axis = np.arange(duration_minutes, dtype=float)
    profile = np.full(duration_minutes, BASE_INTENSITY, dtype=float)

    def gaussian_weight(center_hour, amplitude):
        center_minute = (center_hour - DEFAULT_START.hour) * 60
        return amplitude * np.exp(-0.5 * ((minute_axis - center_minute) / PEAK_STD_MINUTES) ** 2)

    profile += gaussian_weight(MORNING_PEAK_HOUR, MORNING_PEAK_WEIGHT)
    profile += gaussian_weight(EVENING_PEAK_HOUR, EVENING_PEAK_WEIGHT)

    scale = target_orders / profile.sum()
    profile *= scale

    orders_per_minute = rng.poisson(profile)
    return orders_per_minute


def sample_point_in_polygon(polygon, rng, max_tries=1000):
    """Uniformly sample a point inside a (Multi)Polygon using rejection sampling."""
    minx, miny, maxx, maxy = polygon.bounds
    for _ in range(max_tries):
        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)
        candidate = Point(x, y)
        if candidate.within(polygon):
            return candidate
    return polygon.representative_point()


def sample_n_points_in_polygon(polygon, n, rng):
    return [sample_point_in_polygon(polygon, rng) for _ in range(n)]


def generate_orders(rng, target_orders, output_path):
    gdf_rest = locate_restaurants()

    land_poly = Polygon((lon, lat) for lat, lon in POLYGON_COORDS).buffer(0)

    # Time generation (non-homogeneous Poisson)
    orders_per_min = build_intensity_profile(DEFAULT_SHIFT_MINUTES, rng, target_orders)
    minute_offsets = np.repeat(np.arange(DEFAULT_SHIFT_MINUTES), orders_per_min)

    if not len(minute_offsets):
        raise RuntimeError("No orders were generated; adjust intensity parameters or target size.")

    second_offsets = rng.integers(0, 60, size=len(minute_offsets))
    created_ts = [
        DEFAULT_START + timedelta(minutes=int(m), seconds=int(s))
        for m, s in zip(minute_offsets, second_offsets)
    ]

    prep_minutes = np.clip(rng.normal(12, 3, size=len(created_ts)), 5, None)
    ready_ts = [t + timedelta(minutes=float(p)) for t, p in zip(created_ts, prep_minutes)]

    # Spatial sampling
    gdf_rest = gdf_rest.copy()
    gdf_rest.geometry = gpd.GeoSeries(
        sample_n_points_in_polygon(land_poly, len(gdf_rest), rng),
        crs=gdf_rest.crs,
    )

    dest_points = sample_n_points_in_polygon(land_poly, len(created_ts), rng)

    rest_x = gdf_rest.geometry.x.values
    rest_y = gdf_rest.geometry.y.values
    rest_idx = []
    for point in dest_points:
        dx = rest_x - point.x
        dy = rest_y - point.y
        rest_idx.append(int(np.argmin(dx * dx + dy * dy)))

    df = pd.DataFrame(
        {
            "order_id": range(len(created_ts)),
            "restaurant_id": rest_idx,
            "created_at": created_ts,
            "ready_at": ready_ts,
            "rest_lat": gdf_rest.geometry.y.values[rest_idx],
            "rest_lon": gdf_rest.geometry.x.values[rest_idx],
            "dest_lat": [p.y for p in dest_points],
            "dest_lon": [p.x for p in dest_points],
        }
    )

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df.to_csv(output_path, index=False)

    hourly_counts = (
        pd.Series(created_ts)
        .dt.floor("h")
        .value_counts()
        .sort_index()
        .rename("orders")
    )

    print(f"Pedidos sintetizados: {len(df)} -> {output_path}")
    print("Órdenes por hora:")
    for timestamp, count in hourly_counts.items():
        print(f"  {timestamp.strftime('%H:%M')}: {count:4d}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic La Paz orders aligned with LaDe statistics")
    parser.add_argument(
        "--target-orders",
        type=int,
        default=DEFAULT_TARGET_ORDERS,
        help="Approximate number of orders to generate (default: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("data", "synthetic_lapaz_orders_limited.csv"),
        help="Output CSV path",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    generate_orders(rng, args.target_orders, args.output)


if __name__ == "__main__":
    main()
