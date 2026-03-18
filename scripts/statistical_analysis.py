#!/usr/bin/env python
"""
statistical_analysis.py – Pruebas estadísticas para comparar FCFS vs RH
========================================================================

Para cada escenario de saturación y cada KPI a nivel de orden, aplica:
  - Mann-Whitney U  (muestras independientes, no paramétrico)
  - Rank-biserial correlation como medida del tamaño del efecto

Uso:
  # Analizar la corrida más reciente de run_experiments.py
  python scripts/statistical_analysis.py

  # Analizar una corrida específica
  python scripts/statistical_analysis.py --run-dir results/experiments/20260306_143000

  # Solo un escenario
  python scripts/statistical_analysis.py --scenario S3_media

Salida:
  results/experiments/<run_id>/statistical_tests.csv    — tabla completa
  results/experiments/<run_id>/statistical_summary.csv  — resumen por escenario
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

BASE_PATH = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────────────────────────────
# Métricas a nivel de orden sobre las cuales se aplica Mann-Whitney U
# ──────────────────────────────────────────────────────────────────────
ORDER_LEVEL_METRICS = [
    "click_to_door",
    "ready_to_pickup",
    "ready_to_door",
    "bundle_size",
]

METRIC_LABELS = {
    "click_to_door": "Click-to-Door (min)",
    "ready_to_pickup": "Ready-to-Pickup (min)",
    "ready_to_door": "Ready-to-Door (min)",
    "bundle_size": "Bundle Size",
}


# ──────────────────────────────────────────────────────────────────────
# Rank-biserial correlation  r = 1 - 2U/(n1*n2)
# ──────────────────────────────────────────────────────────────────────
def rank_biserial(u_stat, n1, n2):
    """Calcula la correlación rank-biserial a partir de U y tamaños de muestra."""
    return 1.0 - (2.0 * u_stat) / (n1 * n2)


def effect_size_label(r):
    """Clasifica el tamaño del efecto según Cohen (1988)."""
    ar = abs(r)
    if ar < 0.1:
        return "negligible"
    elif ar < 0.3:
        return "small"
    elif ar < 0.5:
        return "medium"
    else:
        return "large"


# ──────────────────────────────────────────────────────────────────────
# Preparar datos a nivel de orden
# ──────────────────────────────────────────────────────────────────────
def prepare_order_data(df):
    """Prepara DataFrame de órdenes para análisis estadístico."""
    for col in ["placement_time", "ready_time", "pickup_time", "delivery_time"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    delivered = df[df["status"] == "delivered"].copy()

    # Calcular ready_to_door si no existe
    if "ready_to_door" not in delivered.columns:
        delivered["ready_to_door"] = (
            (delivered["delivery_time"] - delivered["ready_time"]).dt.total_seconds() / 60.0
        )

    return delivered


# ──────────────────────────────────────────────────────────────────────
# Ejecutar Mann-Whitney U para un par FCFS/RH
# ──────────────────────────────────────────────────────────────────────
def run_statistical_analysis(fcfs_results_path, rh_results_path, scenario_label=""):
    """Aplica Mann-Whitney U a cada métrica de orden.  Devuelve lista de dicts."""
    fcfs_df = pd.read_csv(fcfs_results_path)
    rh_df = pd.read_csv(rh_results_path)
    return compare_policies(fcfs_df, rh_df, scenario_label)


def compare_policies(fcfs_df, rh_df, scenario_label=""):
    """Aplica Mann-Whitney U a cada métrica de orden.  Devuelve lista de dicts."""
    fcfs = prepare_order_data(fcfs_df)
    rh = prepare_order_data(rh_df)

    results = []

    for metric in ORDER_LEVEL_METRICS:
        if metric not in fcfs.columns or metric not in rh.columns:
            continue

        x = fcfs[metric].dropna().values
        y = rh[metric].dropna().values

        if len(x) < 2 or len(y) < 2:
            continue

        # Mann-Whitney U (two-sided)
        u_stat, p_value = mannwhitneyu(x, y, alternative="two-sided")

        # Tamaño del efecto
        r = rank_biserial(u_stat, len(x), len(y))

        results.append({
            "Scenario": scenario_label,
            "Metric": METRIC_LABELS.get(metric, metric),
            "n_FCFS": len(x),
            "n_RH": len(y),
            "Mean_FCFS": round(np.mean(x), 3),
            "Mean_RH": round(np.mean(y), 3),
            "Median_FCFS": round(np.median(x), 3),
            "Median_RH": round(np.median(y), 3),
            "U_statistic": round(u_stat, 1),
            "p_value": round(p_value, 6),
            "Significant (α=0.05)": "Yes" if p_value < 0.05 else "No",
            "Rank_Biserial_r": round(r, 4),
            "Effect_Size": effect_size_label(r),
        })

    return results


# ──────────────────────────────────────────────────────────────────────
# Descubrir y analizar todos los escenarios de una corrida
# ──────────────────────────────────────────────────────────────────────
def analyze_run(run_dir, scenario_filter=None):
    """Analiza todos los escenarios en un directorio de experimentos."""
    run_path = Path(run_dir)
    all_results = []

    # Descubrir escenarios (subdirectorios con CSVs)
    scenario_dirs = sorted([
        d for d in run_path.iterdir()
        if d.is_dir() and any(f.name.endswith("_fcfs_results.csv") for f in d.iterdir())
    ])

    if not scenario_dirs:
        print(f"  No se encontraron escenarios en {run_dir}")
        return pd.DataFrame()

    for sd in scenario_dirs:
        scenario_name = sd.name

        if scenario_filter and scenario_filter not in scenario_name:
            continue

        # Buscar archivos FCFS y RH
        fcfs_files = list(sd.glob("*_fcfs_results.csv"))
        rh_files = list(sd.glob("*_rh_results.csv"))

        if not fcfs_files or not rh_files:
            continue

        fcfs_df = pd.read_csv(fcfs_files[0])
        rh_df = pd.read_csv(rh_files[0])

        # Extraer label legible
        label = scenario_name
        for s in [
            ("S1_baja", "S1 – Baja (18:1)"),
            ("S2_moderada", "S2 – Moderada (26:1)"),
            ("S3_media", "S3 – Media (35:1)"),
            ("S4_alta", "S4 – Alta (52:1)"),
            ("S5_extrema", "S5 – Extrema (75:1)"),
        ]:
            if s[0] in scenario_name:
                label = s[1]
                # Append seed info if present
                if "_seed" in scenario_name:
                    seed_part = scenario_name.split("_seed")[-1]
                    label += f" (seed {seed_part})"
                break

        print(f"  Analizando: {scenario_name} → {label}")
        results = compare_policies(fcfs_df, rh_df, label)
        all_results.extend(results)

    if not all_results:
        print("  Sin resultados para analizar.")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)

    # Guardar tabla completa
    out_path = run_path / "statistical_tests.csv"
    df.to_csv(out_path, index=False)
    print(f"\n  Tests guardados en: {out_path}")

    # Resumen: pivot por escenario y métrica
    if len(df) > 0:
        summary = df.pivot_table(
            index="Scenario",
            columns="Metric",
            values=["p_value", "Rank_Biserial_r", "Mean_FCFS", "Mean_RH"],
            aggfunc="first",
        )
        summary_path = run_path / "statistical_summary.csv"
        summary.to_csv(summary_path)
        print(f"  Resumen guardado en: {summary_path}")

    # Imprimir resultados
    print("\n" + "=" * 90)
    print("RESULTADOS DE PRUEBAS ESTADÍSTICAS (Mann-Whitney U)")
    print("=" * 90)
    for scenario in df["Scenario"].unique():
        sdf = df[df["Scenario"] == scenario]
        print(f"\n  {scenario}")
        print(f"  {'─' * 80}")
        for _, row in sdf.iterrows():
            sig = "***" if row["p_value"] < 0.001 else (
                "**" if row["p_value"] < 0.01 else (
                    "*" if row["p_value"] < 0.05 else "ns"
                )
            )
            print(
                f"    {row['Metric']:<25s} "
                f"FCFS={row['Mean_FCFS']:>8.2f}  RH={row['Mean_RH']:>8.2f}  "
                f"U={row['U_statistic']:>10.0f}  p={row['p_value']:<10.6f} {sig:>4s}  "
                f"r={row['Rank_Biserial_r']:>7.4f} ({row['Effect_Size']})"
            )

    return df


# ──────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Análisis estadístico FCFS vs RH (Mann-Whitney U)",
    )
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Directorio de la corrida a analizar (default: más reciente)",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Filtrar por nombre de escenario (ej: S3_media)",
    )
    args = parser.parse_args()

    # Encontrar directorio de corrida
    if args.run_dir:
        run_dir = args.run_dir
    else:
        exp_root = BASE_PATH / "results" / "experiments"
        if not exp_root.exists():
            print("No se encontraron resultados de experimentos.")
            sys.exit(1)
        runs = sorted([d for d in exp_root.iterdir() if d.is_dir()])
        if not runs:
            print("No se encontraron corridas de experimentos.")
            sys.exit(1)
        run_dir = runs[-1]
        print(f"  Usando corrida más reciente: {run_dir}")

    df = analyze_run(run_dir, args.scenario)

    if len(df) > 0:
        # Resumen final
        n_sig = len(df[df["p_value"] < 0.05])
        n_total = len(df)
        print(f"\n  Resumen: {n_sig}/{n_total} pruebas significativas (α=0.05)")


if __name__ == "__main__":
    main()