#!/usr/bin/env python
"""
run_experiments.py – Análisis de sensibilidad multi-escenario para MDRP-BCS
============================================================================

Ejecuta la simulación FCFS y Rolling Horizon bajo múltiples escenarios de
saturación de flota, recopila KPIs y genera una tabla consolidada.

Escenarios de saturación:
  Se varían los parámetros --orders-per-courier y --min-couriers para generar
  distintos ratios órdenes/courier (desde baja hasta alta saturación).

Uso:
  # Ejecutar todos los escenarios predefinidos
  python scripts/run_experiments.py

  # Solo analizar resultados existentes (sin re-correr simulaciones)
  python scripts/run_experiments.py --analyze-only

  # Datos sintéticos personalizados
  python scripts/run_experiments.py --csv data/my_orders.csv

  # Ejecutar un solo escenario por nombre
  python scripts/run_experiments.py --scenario S3_media

  # Agregar variación algorítmica (ej. distintos MAX_BUNDLE_SIZE)
  python scripts/run_experiments.py --bundle-sizes 2,3,4

  # Múltiples semillas para robustez estadística
  python scripts/run_experiments.py --seeds 2025,2026,2027
"""

import argparse
import copy
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime

import pandas as pd

# ──────────────────────────────────────────────────────────────────────
# Ruta base del proyecto
# ──────────────────────────────────────────────────────────────────────
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_PATH)

# ──────────────────────────────────────────────────────────────────────
# Escenarios de saturación
# ──────────────────────────────────────────────────────────────────────
# Cada escenario define:
#   label:              nombre legible para tablas/gráficas
#   orders_per_courier: ratio para auto-dimensionado de flota
#   min_couriers:       piso de tamaño de flota
#
# Con ~1 038 órdenes, la flota resultante es:
#   S1: ceil(1038/18)=58 couriers  →  ~17.9 órd/courier  (baseline)
#   S2: ceil(1038/26)=40 couriers  →  ~25.9 órd/courier
#   S3: ceil(1038/35)=30 couriers  →  ~34.6 órd/courier
#   S4: ceil(1038/52)=20 couriers  →  ~51.9 órd/courier

SCENARIOS = [
    {
        "name": "S1_baja",
        "label": "S1 – Baja (18:1)",
        "orders_per_courier": 18,
        "min_couriers": 10,
    },
    {
        "name": "S2_moderada",
        "label": "S2 – Moderada (26:1)",
        "orders_per_courier": 26,
        "min_couriers": 10,
    },
    {
        "name": "S3_media",
        "label": "S3 – Media (35:1)",
        "orders_per_courier": 35,
        "min_couriers": 10,
    },
    {
        "name": "S4_alta",
        "label": "S4 – Alta (52:1)",
        "orders_per_courier": 52,
        "min_couriers": 10,
    },
]


# ──────────────────────────────────────────────────────────────────────
# Cálculo de KPIs  (misma lógica que generate_results.py)
# ──────────────────────────────────────────────────────────────────────
def calculate_kpis(df, courier_df, total_orders):
    """Calcula KPIs a partir de CSVs de resultados."""
    for col in ["placement_time", "ready_time", "pickup_time", "delivery_time"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    delivered = df[df["status"] == "delivered"].copy()
    n_delivered = len(delivered)

    if n_delivered == 0:
        return {k: 0.0 for k in _kpi_keys()}

    # Click-to-Door
    avg_ctd = delivered["click_to_door"].mean()
    p50_ctd = delivered["click_to_door"].quantile(0.50)
    p90_ctd = delivered["click_to_door"].quantile(0.90)
    p95_ctd = delivered["click_to_door"].quantile(0.95)

    # Ready-to-Pickup
    avg_rtp = delivered["ready_to_pickup"].mean()
    p90_rtp = delivered["ready_to_pickup"].quantile(0.90)

    # Ready-to-Door
    delivered["ready_to_door"] = (
        (delivered["delivery_time"] - delivered["ready_time"]).dt.total_seconds() / 60
    )
    avg_rtd = delivered["ready_to_door"].mean()
    p90_rtd = delivered["ready_to_door"].quantile(0.90)

    # Undelivered
    pct_undelivered = ((total_orders - n_delivered) / total_orders) * 100

    # Courier metrics
    total_dist = courier_df["total_distance_km"].sum()
    total_hours = courier_df["shift_duration_hours"].sum()
    total_del = courier_df["orders_delivered"].sum()
    total_bundles = courier_df["bundles_picked_up"].sum()
    driving_hrs = courier_df["driving_time_minutes"].sum() / 60.0

    opc_hr = total_del / total_hours if total_hours > 0 else 0
    bph = total_bundles / total_hours if total_hours > 0 else 0
    utilization = (driving_hrs / total_hours) * 100 if total_hours > 0 else 0
    dist_per_order = total_dist / total_del if total_del > 0 else 0

    avg_bundle = delivered["bundle_size"].mean()
    pct_multi = (len(delivered[delivered["bundle_size"] > 1]) / n_delivered) * 100

    # Compensación
    PAY_PER_ORDER = 10.0
    MIN_PAY_PER_HOUR = 15.0
    TARGET_CTD = 40.0

    c = courier_df.copy()
    c["del_earn"] = c["orders_delivered"] * PAY_PER_ORDER
    c["min_earn"] = c["shift_duration_hours"] * MIN_PAY_PER_HOUR
    c["comp"] = c[["del_earn", "min_earn"]].max(axis=1)

    total_comp = c["comp"].sum()
    cost_per_order = total_comp / total_del if total_del > 0 else 0
    frac_min = len(c[c["comp"] == c["min_earn"]]) / len(c) if len(c) > 0 else 0

    delivered["overage"] = (delivered["click_to_door"] - TARGET_CTD).clip(lower=0)
    avg_overage = delivered["overage"].mean()

    # SLA compliance (% orders within 40 min CTD)
    sla_pct = (len(delivered[delivered["click_to_door"] <= TARGET_CTD]) / n_delivered) * 100

    return {
        "Avg CTD (min)": round(avg_ctd, 2),
        "P50 CTD (min)": round(p50_ctd, 2),
        "P90 CTD (min)": round(p90_ctd, 2),
        "P95 CTD (min)": round(p95_ctd, 2),
        "Avg RTP (min)": round(avg_rtp, 2),
        "P90 RTP (min)": round(p90_rtp, 2),
        "Avg RTD (min)": round(avg_rtd, 2),
        "P90 RTD (min)": round(p90_rtd, 2),
        "% Undelivered": round(pct_undelivered, 2),
        "SLA Compliance (%)": round(sla_pct, 2),
        "Avg Bundle Size": round(avg_bundle, 2),
        "% Multi-Bundle": round(pct_multi, 2),
        "Total Distance (km)": round(total_dist, 2),
        "Dist/Order (km)": round(dist_per_order, 2),
        "Orders/Courier/Hr": round(opc_hr, 2),
        "Bundles/Hr": round(bph, 2),
        "Utilization (%)": round(utilization, 2),
        "Total Compensation ($)": round(total_comp, 2),
        "Cost/Order ($)": round(cost_per_order, 2),
        "Frac. Min Comp": round(frac_min, 2),
        "CTD Overage (min)": round(avg_overage, 2),
    }


def _kpi_keys():
    return [
        "Avg CTD (min)", "P50 CTD (min)", "P90 CTD (min)", "P95 CTD (min)",
        "Avg RTP (min)", "P90 RTP (min)", "Avg RTD (min)", "P90 RTD (min)",
        "% Undelivered", "SLA Compliance (%)", "Avg Bundle Size", "% Multi-Bundle",
        "Total Distance (km)", "Dist/Order (km)", "Orders/Courier/Hr", "Bundles/Hr",
        "Utilization (%)", "Total Compensation ($)", "Cost/Order ($)",
        "Frac. Min Comp", "CTD Overage (min)",
    ]


# ──────────────────────────────────────────────────────────────────────
# Ejecución de un escenario individual
# ──────────────────────────────────────────────────────────────────────
def run_scenario(scenario, csv_path, results_base, seed_suffix=""):
    """Ejecuta FCFS y RH para un escenario dado.  Devuelve dict con rutas de resultados."""
    name = scenario["name"] + seed_suffix
    opc = scenario["orders_per_courier"]
    mc = scenario["min_couriers"]
    label = scenario["label"]

    scenario_dir = os.path.join(results_base, name)
    os.makedirs(scenario_dir, exist_ok=True)

    base_csv_name = os.path.basename(csv_path).replace(".csv", "")

    # Paths de salida
    fcfs_orders = os.path.join(scenario_dir, f"{base_csv_name}_fcfs_results.csv")
    fcfs_couriers = os.path.join(scenario_dir, f"{base_csv_name}_fcfs_couriers.csv")
    rh_orders = os.path.join(scenario_dir, f"{base_csv_name}_rh_results.csv")
    rh_couriers = os.path.join(scenario_dir, f"{base_csv_name}_rh_couriers.csv")

    # ── FCFS ──
    print(f"\n  [{name}] Ejecutando FCFS (opc={opc}, min_c={mc})...")
    t0 = time.time()
    _run_policy(
        csv_path, opc, mc,
        results_path=fcfs_orders,
        courier_results_path=fcfs_couriers,
        policy="fcfs",
    )
    t_fcfs = time.time() - t0
    print(f"  [{name}] FCFS completado en {t_fcfs:.1f}s")

    # ── Rolling Horizon ──
    print(f"  [{name}] Ejecutando Rolling Horizon (opc={opc}, min_c={mc})...")
    t0 = time.time()
    _run_policy(
        csv_path, opc, mc,
        results_path=rh_orders,
        courier_results_path=rh_couriers,
        policy="rh",
    )
    t_rh = time.time() - t0
    print(f"  [{name}] RH completado en {t_rh:.1f}s")

    return {
        "name": name,
        "label": label,
        "opc": opc,
        "min_couriers": mc,
        "fcfs_orders": fcfs_orders,
        "fcfs_couriers": fcfs_couriers,
        "rh_orders": rh_orders,
        "rh_couriers": rh_couriers,
        "t_fcfs": t_fcfs,
        "t_rh": t_rh,
    }


def _run_policy(csv_path, opc, mc, results_path, courier_results_path, policy):
    """Invoca la simulación en-proceso (sin subprocess) para mayor eficiencia."""
    # Imports dinámicos para evitar contaminación de env antes de tiempo
    from src import config
    from src.main import run_simulation
    from src.synth_loader import load_synth_instance
    from datetime import timedelta

    orders, couriers, restaurants, _ = load_synth_instance(
        csv_path,
        n_couriers=None,
        orders_per_courier=opc,
        min_couriers=mc,
    )

    os.environ["USE_EUCLIDEAN"] = "0"

    if policy == "fcfs":
        os.environ["FCFS_POLICY"] = "1"
    else:
        os.environ.pop("FCFS_POLICY", None)

    sim_start = min(
        min(c.on_time for c in couriers),
        min(o.placement_time for o in orders),
    )
    sim_end = max(c.off_time for c in couriers) + timedelta(hours=1)

    run_simulation(
        orders, couriers, restaurants, sim_end,
        start_time=sim_start,
        results_path=results_path,
        courier_results_path=courier_results_path,
    )


# ──────────────────────────────────────────────────────────────────────
# Análisis consolidado multi-escenario
# ──────────────────────────────────────────────────────────────────────
def analyze_all(results_base, scenarios_run):
    """Lee resultados de todos los escenarios y genera tabla consolidada."""
    rows = []

    for sr in scenarios_run:
        fcfs_df = pd.read_csv(sr["fcfs_orders"])
        rh_df = pd.read_csv(sr["rh_orders"])
        fcfs_c = pd.read_csv(sr["fcfs_couriers"])
        rh_c = pd.read_csv(sr["rh_couriers"])

        total_orders = len(fcfs_df)
        n_couriers = len(fcfs_c)

        fcfs_kpis = calculate_kpis(fcfs_df, fcfs_c, total_orders)
        rh_kpis = calculate_kpis(rh_df, rh_c, total_orders)

        # Calcular mejoras porcentuales
        improvements = {}
        for k in fcfs_kpis:
            fv, rv = fcfs_kpis[k], rh_kpis[k]
            if fv != 0:
                improvements[k] = round(((rv - fv) / abs(fv)) * 100, 2)
            else:
                improvements[k] = 0.0

        row = {
            "Scenario": sr["label"],
            "Orders": total_orders,
            "Couriers": n_couriers,
            "Ratio": round(total_orders / n_couriers, 1),
        }

        # KPIs FCFS
        for k, v in fcfs_kpis.items():
            row[f"FCFS {k}"] = v
        # KPIs RH
        for k, v in rh_kpis.items():
            row[f"RH {k}"] = v
        # Mejoras
        for k, v in improvements.items():
            row[f"Δ% {k}"] = v

        # Tiempos de ejecución
        row["FCFS Time (s)"] = round(sr.get("t_fcfs", 0), 1)
        row["RH Time (s)"] = round(sr.get("t_rh", 0), 1)

        rows.append(row)

    df = pd.DataFrame(rows)

    # Guardar tabla completa
    out_path = os.path.join(results_base, "experiment_comparison.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  Tabla completa guardada en: {out_path}")

    # ── Tabla resumen con KPIs clave ──
    summary_cols = [
        "Scenario", "Orders", "Couriers", "Ratio",
        "FCFS Avg CTD (min)", "RH Avg CTD (min)", "Δ% Avg CTD (min)",
        "FCFS Cost/Order ($)", "RH Cost/Order ($)", "Δ% Cost/Order ($)",
        "FCFS Orders/Courier/Hr", "RH Orders/Courier/Hr", "Δ% Orders/Courier/Hr",
        "FCFS Utilization (%)", "RH Utilization (%)", "Δ% Utilization (%)",
        "FCFS SLA Compliance (%)", "RH SLA Compliance (%)", "Δ% SLA Compliance (%)",
        "FCFS Dist/Order (km)", "RH Dist/Order (km)", "Δ% Dist/Order (km)",
    ]
    existing_cols = [c for c in summary_cols if c in df.columns]
    summary_df = df[existing_cols]

    summary_path = os.path.join(results_base, "experiment_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"  Resumen guardado en: {summary_path}")

    # ── Imprimir resumen en consola ──
    print("\n" + "=" * 80)
    print("RESUMEN DE EXPERIMENTOS")
    print("=" * 80)
    try:
        print(summary_df.to_markdown(index=False))
    except ImportError:
        print(summary_df.to_string(index=False))

    return df


# ──────────────────────────────────────────────────────────────────────
# Generación de datos con distintas semillas
# ──────────────────────────────────────────────────────────────────────
def generate_synthetic_data(seed, target_orders=1000):
    """Genera un CSV de órdenes sintéticas con la semilla indicada."""
    output_path = os.path.join(
        BASE_PATH, "data", f"synthetic_lapaz_orders_seed{seed}.csv"
    )
    if os.path.exists(output_path):
        print(f"  Datos ya existen para seed={seed}: {output_path}")
        return output_path

    print(f"  Generando datos sintéticos (seed={seed}, target={target_orders})...")
    cmd = [
        sys.executable,
        os.path.join(BASE_PATH, "scripts", "make_synth_orders.py"),
        "--seed", str(seed),
        "--target-orders", str(target_orders),
        "--output", output_path,
    ]
    result = subprocess.run(cmd, cwd=BASE_PATH, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR generando datos: {result.stderr}")
        raise RuntimeError(f"make_synth_orders.py falló con seed={seed}")
    print(f"  Datos generados: {output_path}")
    return output_path


# ──────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Análisis de sensibilidad multi-escenario MDRP-BCS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/run_experiments.py
  python scripts/run_experiments.py --scenario S3_media
  python scripts/run_experiments.py --seeds 2025,2026,2027
  python scripts/run_experiments.py --analyze-only
  python scripts/run_experiments.py --bundle-sizes 2,3,4
        """,
    )
    parser.add_argument(
        "--csv",
        default="data/synthetic_lapaz_orders_limited.csv",
        help="CSV de órdenes sintéticas (default: %(default)s)",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Ejecutar solo un escenario por nombre (ej: S3_media)",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Solo analizar resultados existentes sin ejecutar simulaciones",
    )
    parser.add_argument(
        "--seeds",
        default=None,
        help="Semillas separadas por coma para robustez estadística (ej: 2025,2026,2027)",
    )
    parser.add_argument(
        "--target-orders",
        type=int,
        default=1000,
        help="Número objetivo de órdenes por instancia (default: 1000)",
    )
    parser.add_argument(
        "--bundle-sizes",
        default=None,
        help="Valores de MAX_BUNDLE_SIZE a probar, separados por coma (ej: 2,3,4)",
    )
    args = parser.parse_args()

    # Timestamp para identificar esta corrida
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_base = os.path.join(BASE_PATH, "results", "experiments", run_id)
    os.makedirs(results_base, exist_ok=True)

    # Filtrar escenarios si se pide uno específico
    scenarios_to_run = SCENARIOS
    if args.scenario:
        scenarios_to_run = [s for s in SCENARIOS if s["name"] == args.scenario]
        if not scenarios_to_run:
            valid = [s["name"] for s in SCENARIOS]
            print(f"Escenario '{args.scenario}' no encontrado. Válidos: {valid}")
            sys.exit(1)

    # Determinar semillas
    seeds = [None]  # None = usar CSV existente sin regenerar
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]

    # Determinar bundle sizes
    bundle_sizes = [None]  # None = usar config default
    if args.bundle_sizes:
        bundle_sizes = [int(b) for b in args.bundle_sizes.split(",")]

    print("=" * 70)
    print(f"MDRP-BCS – ANÁLISIS DE SENSIBILIDAD")
    print(f"  Run ID:       {run_id}")
    print(f"  Escenarios:   {len(scenarios_to_run)}")
    print(f"  Semillas:     {seeds}")
    print(f"  Bundle sizes: {bundle_sizes}")
    print(f"  Resultados:   {results_base}")
    print("=" * 70)

    if args.analyze_only:
        # Buscar la corrida más reciente para analizar
        exp_root = os.path.join(BASE_PATH, "results", "experiments")
        if not os.path.exists(exp_root):
            print("No se encontraron resultados de experimentos anteriores.")
            sys.exit(1)
        runs = sorted(os.listdir(exp_root))
        if not runs:
            print("No se encontraron resultados de experimentos anteriores.")
            sys.exit(1)
        latest = os.path.join(exp_root, runs[-1])
        print(f"  Analizando corrida más reciente: {latest}")

        # Reconstruir scenarios_run a partir de los directorios existentes
        scenarios_run = _discover_scenarios(latest)
        if not scenarios_run:
            print("  No se encontraron resultados de escenarios.")
            sys.exit(1)
        analyze_all(latest, scenarios_run)
        return

    # ── Ejecutar experimentos ──
    all_scenarios_run = []
    total = len(scenarios_to_run) * len(seeds) * len(bundle_sizes)
    idx = 0

    for seed in seeds:
        # Generar datos si se especificó semilla
        if seed is not None:
            csv_path = generate_synthetic_data(seed, args.target_orders)
            seed_suffix = f"_seed{seed}"
        else:
            csv_path = os.path.join(BASE_PATH, args.csv)
            seed_suffix = ""

        for bs in bundle_sizes:
            if bs is not None:
                # Override dinámico de config
                from src import config
                original_bs = config.MAX_BUNDLE_SIZE
                config.MAX_BUNDLE_SIZE = bs
                bs_suffix = f"_bs{bs}"
                print(f"\n  >> MAX_BUNDLE_SIZE override: {original_bs} → {bs}")
            else:
                bs_suffix = ""

            for scenario in scenarios_to_run:
                idx += 1
                combo_suffix = seed_suffix + bs_suffix
                print(f"\n{'─' * 60}")
                print(f"  [{idx}/{total}] {scenario['label']}{combo_suffix}")
                print(f"{'─' * 60}")

                sr = run_scenario(scenario, csv_path, results_base, combo_suffix)
                all_scenarios_run.append(sr)

            # Restaurar config si fue modificado
            if bs is not None:
                config.MAX_BUNDLE_SIZE = original_bs

    # ── Guardar metadata ──
    meta = {
        "run_id": run_id,
        "csv": args.csv,
        "seeds": seeds,
        "bundle_sizes": bundle_sizes,
        "scenarios": [s["name"] for s in scenarios_to_run],
        "n_experiments": total,
        "timestamp": datetime.now().isoformat(),
    }
    meta_path = os.path.join(results_base, "experiment_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, default=str)

    # ── Análisis consolidado ──
    print("\n\n" + "=" * 70)
    print("ANÁLISIS DE RESULTADOS")
    print("=" * 70)
    analyze_all(results_base, all_scenarios_run)

    print(f"\n  Metadata: {meta_path}")
    print(f"\n{'=' * 70}")
    print("EXPERIMENTOS COMPLETADOS")
    print(f"{'=' * 70}")


def _discover_scenarios(results_dir):
    """Descubre escenarios a partir de la estructura de directorios."""
    scenarios_run = []
    base_name = "synthetic_lapaz_orders_limited"  # fallback

    for entry in sorted(os.listdir(results_dir)):
        entry_path = os.path.join(results_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        # Buscar CSVs dentro del directorio
        files = os.listdir(entry_path)
        fcfs_orders = [f for f in files if f.endswith("_fcfs_results.csv")]
        rh_orders = [f for f in files if f.endswith("_rh_results.csv")]

        if fcfs_orders and rh_orders:
            scenarios_run.append({
                "name": entry,
                "label": entry,
                "opc": 0,
                "min_couriers": 0,
                "fcfs_orders": os.path.join(entry_path, fcfs_orders[0]),
                "fcfs_couriers": os.path.join(
                    entry_path,
                    fcfs_orders[0].replace("_results.csv", "_couriers.csv"),
                ),
                "rh_orders": os.path.join(entry_path, rh_orders[0]),
                "rh_couriers": os.path.join(
                    entry_path,
                    rh_orders[0].replace("_results.csv", "_couriers.csv"),
                ),
                "t_fcfs": 0,
                "t_rh": 0,
            })

    return scenarios_run


if __name__ == "__main__":
    main()
