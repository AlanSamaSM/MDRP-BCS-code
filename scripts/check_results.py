#!/usr/bin/env python
"""
check_results.py – Verificaciones de integridad de una corrida (ponencia/DATACHECKS.md §2)
==========================================================================================

DC1  ninguna orden se entrega antes de estar lista ni antes de su recolección
DC2  toda semilla, escenario y política entrega órdenes
DC3  Σ orders_delivered de repartidores == órdenes entregadas (sin entregas dobles)
DC5  CtD >= tiempo de preparación + s_o/2 (entrega físicamente posible)
     Además se reporta cuántas entregas usaron el respaldo euclidiano en una corrida OSRM.

(DC4 —la política FCFS despacha al colocarse la orden— se verifica en el código.)

Uso:
  python scripts/check_results.py results/experiments/<run_id>
"""
import glob
import os
import sys

import pandas as pd

HALF_SERVICE_MIN = 2.0  # s_o / 2


def check_run(run_dir):
    failures = 0
    rows = []
    for f in sorted(glob.glob(os.path.join(run_dir, "*", "*_results.csv"))):
        run = os.path.basename(os.path.dirname(f))
        policy = "fcfs" if f.endswith("_fcfs_results.csv") else "rh"
        df = pd.read_csv(f, parse_dates=["placement_time", "ready_time", "pickup_time", "delivery_time"])
        couriers = pd.read_csv(f.replace("_results.csv", "_couriers.csv"))
        d = df[df["status"] == "delivered"]

        dc1 = int(((d["delivery_time"] < d["ready_time"])
                   | (d["delivery_time"] < d["pickup_time"])
                   | (d["pickup_time"] < d["ready_time"])).sum())
        dc2 = len(d) > 0
        dc3 = int(couriers["orders_delivered"].sum()) - len(d)
        prep = (d["ready_time"] - d["placement_time"]).dt.total_seconds() / 60
        dc5 = int((d["click_to_door"] < prep + HALF_SERVICE_MIN - 1e-6).sum())
        fallback = int((d["routing_source"] == "euclidean_fallback").sum())
        ok = dc1 == 0 and dc2 and dc3 == 0 and dc5 == 0 and fallback == 0
        failures += not ok
        rows.append({
            "run": run, "policy": policy, "delivered": len(d), "orders": len(df),
            "DC1": dc1, "DC2": "ok" if dc2 else "FAIL", "DC3": dc3, "DC5": dc5,
            "fallback": fallback,
            "status": "ok" if ok else "FAIL",
        })

    if not rows:
        print(f"No se encontraron resultados en {run_dir}")
        return 1
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"\n{len(rows) - failures}/{len(rows)} corridas pasan DC1, DC2, DC3, DC5 y sin respaldo euclidiano")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(check_run(sys.argv[1]))
