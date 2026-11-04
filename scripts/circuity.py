#!/usr/bin/env python
"""
circuity.py – Rodeo de la red vial de La Paz frente a la línea recta
====================================================================

Para cada par restaurante -> cliente de las instancias sintéticas consulta OSRM
y compara la distancia por la red con la distancia en línea recta (Haversine):

  circuity = distancia OSRM / distancia Haversine

También estima la velocidad media de la red (Σ distancia OSRM / Σ duración OSRM),
que es la velocidad con la que se ejecuta el escenario de control euclidiano
(`run_experiments.py --euclidean --speed <m/min>`).

Requiere el servidor OSRM activo en localhost:5000 (docker-compose up -d).

Uso:
  python scripts/circuity.py                       # semillas 2025-2034
  python scripts/circuity.py --seeds 2025,2026
"""
import argparse
import json
import os
import sys

import pandas as pd

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_PATH)

# Sin respaldo euclidiano: si OSRM falla, la medición no es válida.
os.environ["USE_EUCLIDEAN"] = "0"
os.environ["USE_EUCLIDEAN_ON_FAILURE"] = "0"

from src.getrouteOSMR import get_route_details, haversine_distance  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", default="2025,2026,2027,2028,2029,2030,2031,2032,2033,2034")
    args = parser.parse_args()

    rows = []
    for seed in [int(s) for s in args.seeds.split(",")]:
        csv_path = os.path.join(BASE_PATH, "data", f"synthetic_lapaz_orders_seed{seed}.csv")
        df = pd.read_csv(csv_path)
        print(f"  seed {seed}: {len(df)} pares restaurante -> cliente")
        for _, r in df.iterrows():
            origin = (r["rest_lat"], r["rest_lon"])
            dest = (r["dest_lat"], r["dest_lon"])
            route = get_route_details(origin, [dest])
            if not route or route.get("routing_source") != "osrm":
                sys.exit(f"OSRM no respondió para {origin} -> {dest}; ¿está activo el contenedor?")
            rows.append({
                "seed": seed,
                "order_id": r["order_id"],
                "haversine_m": haversine_distance(origin, dest),
                "osrm_m": route["distance"],
                "osrm_s": route["duration"],
            })

    pairs = pd.DataFrame(rows)
    pairs = pairs[pairs["haversine_m"] > 0]
    pairs["circuity"] = pairs["osrm_m"] / pairs["haversine_m"]

    speed_m_per_min = pairs["osrm_m"].sum() / (pairs["osrm_s"].sum() / 60.0)
    summary = {
        "pairs": int(len(pairs)),
        "circuity_aggregate": round(pairs["osrm_m"].sum() / pairs["haversine_m"].sum(), 4),
        "circuity_mean": round(pairs["circuity"].mean(), 4),
        "circuity_p10": round(pairs["circuity"].quantile(0.10), 4),
        "circuity_median": round(pairs["circuity"].median(), 4),
        "circuity_p90": round(pairs["circuity"].quantile(0.90), 4),
        "haversine_km_mean": round(pairs["haversine_m"].mean() / 1000, 3),
        "osrm_km_mean": round(pairs["osrm_m"].mean() / 1000, 3),
        "osrm_speed_m_per_min": round(speed_m_per_min, 1),
        "osrm_speed_km_h": round(speed_m_per_min * 60 / 1000, 1),
    }

    out_dir = os.path.join(BASE_PATH, "results", "circuity")
    os.makedirs(out_dir, exist_ok=True)
    pairs.to_csv(os.path.join(out_dir, "circuity_pairs.csv"), index=False)
    with open(os.path.join(out_dir, "circuity_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"\n  Resultados en {out_dir}")


if __name__ == "__main__":
    main()
