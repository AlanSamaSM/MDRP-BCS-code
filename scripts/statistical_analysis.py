#!/usr/bin/env python
"""
statistical_analysis.py – Pruebas estadísticas para comparar FCFS vs RH
========================================================================

Para cada escenario de saturación y cada KPI a nivel de orden, aplica:
  - Shapiro-Wilk normality pre-test (justifica elección no paramétrica)
  - Mann-Whitney U  (muestras independientes, no paramétrico)
  - Rank-biserial correlation como medida del tamaño del efecto
  - Benjamini-Hochberg FDR correction para pruebas múltiples
  - Agregación cross-seed (media ± std por escenario base)
  - Kruskal-Wallis omnibus test (¿varía la mejora RH entre escenarios?)
  - Métricas adicionales: SLA compliance, P90/P95 CTD, courier-level KPIs

Uso:
  # Analizar la corrida más reciente de run_experiments.py
  python scripts/statistical_analysis.py

  # Analizar una corrida específica
  python scripts/statistical_analysis.py --run-dir results/experiments/20260306_143000

  # Solo un escenario
  python scripts/statistical_analysis.py --scenario S3_media

Salida:
  results/experiments/<run_id>/statistical_tests.csv         — tabla completa
  results/experiments/<run_id>/statistical_summary.csv       — resumen por escenario
  results/experiments/<run_id>/normality_tests.csv           — Shapiro-Wilk pre-tests
  results/experiments/<run_id>/cross_seed_aggregation.csv    — media ± std cross-seed
  results/experiments/<run_id>/kruskal_wallis_omnibus.csv    — omnibus across scenarios
  results/experiments/<run_id>/courier_level_tests.csv       — courier-level comparisons
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, shapiro, kruskal

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

# Métricas adicionales (SLA, percentiles) — computed in prepare_order_data
EXTENDED_ORDER_METRICS = [
    "sla_met",         # binary: 1 if CTD <= 40 min
    "ctd_overage",     # max(0, CTD - 40)
]

METRIC_LABELS = {
    "click_to_door": "Click-to-Door (min)",
    "ready_to_pickup": "Ready-to-Pickup (min)",
    "ready_to_door": "Ready-to-Door (min)",
    "bundle_size": "Bundle Size",
    "sla_met": "SLA Compliance (≤40 min)",
    "ctd_overage": "CTD Overage (min)",
}

# Métricas a nivel de courier
COURIER_METRICS = [
    "orders_per_hour",
    "utilization_pct",
    "dist_per_order",
]

COURIER_METRIC_LABELS = {
    "orders_per_hour": "Orders/Courier/Hr",
    "utilization_pct": "Utilization (%)",
    "dist_per_order": "Distance/Order (km)",
}

SLA_TARGET = 40.0  # minutes


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
# Benjamini-Hochberg FDR correction
# ──────────────────────────────────────────────────────────────────────
def benjamini_hochberg(p_values, alpha=0.05):
    """Apply Benjamini-Hochberg FDR correction.  Returns adjusted p-values."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_idx = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_idx]
    adjusted = np.empty(n)
    cummin = 1.0
    for i in range(n - 1, -1, -1):
        adjusted_p = sorted_p[i] * n / (i + 1)
        cummin = min(cummin, adjusted_p)
        adjusted[sorted_idx[i]] = min(cummin, 1.0)
    return adjusted.tolist()


# ──────────────────────────────────────────────────────────────────────
# Shapiro-Wilk normality test (subsample for large n)
# ──────────────────────────────────────────────────────────────────────
def run_shapiro_wilk(values, max_n=5000):
    """Run Shapiro-Wilk on a subsample (scipy limit ~5000). Returns (W, p)."""
    if len(values) < 3:
        return np.nan, np.nan
    if len(values) > max_n:
        rng = np.random.default_rng(42)
        values = rng.choice(values, size=max_n, replace=False)
    w, p = shapiro(values)
    return round(w, 6), round(p, 6)


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

    # SLA compliance (binary) and CTD overage
    delivered["sla_met"] = (delivered["click_to_door"] <= SLA_TARGET).astype(float)
    delivered["ctd_overage"] = (delivered["click_to_door"] - SLA_TARGET).clip(lower=0)

    return delivered


# ──────────────────────────────────────────────────────────────────────
# Preparar datos a nivel de courier
# ──────────────────────────────────────────────────────────────────────
def prepare_courier_data(df):
    """Prepara DataFrame de couriers con métricas derivadas."""
    c = df.copy()
    c["orders_per_hour"] = c["orders_delivered"] / c["shift_duration_hours"]
    c["utilization_pct"] = (c["driving_time_minutes"] / 60.0) / c["shift_duration_hours"] * 100
    c["dist_per_order"] = c["total_distance_km"] / c["orders_delivered"].replace(0, np.nan)
    return c


# ──────────────────────────────────────────────────────────────────────
# Ejecutar Mann-Whitney U para un par FCFS/RH
# ──────────────────────────────────────────────────────────────────────
def run_statistical_analysis(fcfs_results_path, rh_results_path, scenario_label=""):
    """Aplica Mann-Whitney U a cada métrica de orden.  Devuelve lista de dicts."""
    fcfs_df = pd.read_csv(fcfs_results_path)
    rh_df = pd.read_csv(rh_results_path)
    return compare_policies(fcfs_df, rh_df, scenario_label)


def _mann_whitney_row(x, y, metric_key, scenario_label):
    """Run Mann-Whitney U on two arrays, return result dict or None."""
    if len(x) < 2 or len(y) < 2:
        return None
    u_stat, p_value = mannwhitneyu(x, y, alternative="two-sided")
    r = rank_biserial(u_stat, len(x), len(y))
    label = METRIC_LABELS.get(metric_key, COURIER_METRIC_LABELS.get(metric_key, metric_key))
    return {
        "Scenario": scenario_label,
        "Metric": label,
        "n_FCFS": len(x),
        "n_RH": len(y),
        "Mean_FCFS": round(np.mean(x), 3),
        "Mean_RH": round(np.mean(y), 3),
        "Median_FCFS": round(np.median(x), 3),
        "Median_RH": round(np.median(y), 3),
        "P90_FCFS": round(np.percentile(x, 90), 3),
        "P90_RH": round(np.percentile(y, 90), 3),
        "P95_FCFS": round(np.percentile(x, 95), 3),
        "P95_RH": round(np.percentile(y, 95), 3),
        "U_statistic": round(u_stat, 1),
        "p_value": round(p_value, 6),
        "Rank_Biserial_r": round(r, 4),
        "Effect_Size": effect_size_label(r),
    }


def compare_policies(fcfs_df, rh_df, scenario_label=""):
    """Aplica Mann-Whitney U a cada métrica de orden (original + extended)."""
    fcfs = prepare_order_data(fcfs_df)
    rh = prepare_order_data(rh_df)

    results = []
    all_metrics = ORDER_LEVEL_METRICS + EXTENDED_ORDER_METRICS

    for metric in all_metrics:
        if metric not in fcfs.columns or metric not in rh.columns:
            continue
        x = fcfs[metric].dropna().values
        y = rh[metric].dropna().values
        row = _mann_whitney_row(x, y, metric, scenario_label)
        if row:
            results.append(row)

    return results


def compare_courier_policies(fcfs_courier_df, rh_courier_df, scenario_label=""):
    """Aplica Mann-Whitney U a métricas de courier."""
    fcfs = prepare_courier_data(fcfs_courier_df)
    rh = prepare_courier_data(rh_courier_df)

    results = []
    for metric in COURIER_METRICS:
        if metric not in fcfs.columns or metric not in rh.columns:
            continue
        x = fcfs[metric].dropna().values
        y = rh[metric].dropna().values
        row = _mann_whitney_row(x, y, metric, scenario_label)
        if row:
            results.append(row)
    return results


def run_normality_tests(fcfs_df, rh_df, scenario_label=""):
    """Run Shapiro-Wilk on each metric for both policies."""
    fcfs = prepare_order_data(fcfs_df)
    rh = prepare_order_data(rh_df)
    rows = []
    for metric in ORDER_LEVEL_METRICS:
        if metric not in fcfs.columns:
            continue
        x = fcfs[metric].dropna().values
        y = rh[metric].dropna().values
        w_fcfs, p_fcfs = run_shapiro_wilk(x)
        w_rh, p_rh = run_shapiro_wilk(y)
        label = METRIC_LABELS.get(metric, metric)
        rows.append({
            "Scenario": scenario_label,
            "Metric": label,
            "W_FCFS": w_fcfs, "p_FCFS": p_fcfs,
            "Normal_FCFS (α=0.05)": "Yes" if p_fcfs > 0.05 else "No",
            "W_RH": w_rh, "p_RH": p_rh,
            "Normal_RH (α=0.05)": "Yes" if p_rh > 0.05 else "No",
        })
    return rows


# ──────────────────────────────────────────────────────────────────────
# Descubrir y analizar todos los escenarios de una corrida
# ──────────────────────────────────────────────────────────────────────
SCENARIO_MAP = [
    ("S1_baja", "S1 – Baja (18:1)"),
    ("S2_moderada", "S2 – Moderada (26:1)"),
    ("S3_media", "S3 – Media (35:1)"),
    ("S4_alta", "S4 – Alta (52:1)"),
    ("S5_extrema", "S5 – Extrema (75:1)"),
]


def _scenario_label(scenario_name):
    """Extract human-readable label and base scenario from directory name."""
    label = scenario_name
    base = scenario_name
    for key, readable in SCENARIO_MAP:
        if key in scenario_name:
            label = readable
            base = key
            if "_seed" in scenario_name:
                seed_part = scenario_name.split("_seed")[-1]
                label += f" (seed {seed_part})"
            break
    return label, base


def analyze_run(run_dir, scenario_filter=None):
    """Analiza todos los escenarios en un directorio de experimentos."""
    run_path = Path(run_dir)
    all_order_results = []
    all_courier_results = []
    all_normality = []
    # Track per-order deltas for Kruskal-Wallis omnibus
    kw_data = {}  # base_scenario -> list of (ctd_fcfs - ctd_rh) per order

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
        fcfs_courier_files = list(sd.glob("*_fcfs_couriers.csv"))
        rh_courier_files = list(sd.glob("*_rh_couriers.csv"))

        if not fcfs_files or not rh_files:
            continue

        fcfs_df = pd.read_csv(fcfs_files[0])
        rh_df = pd.read_csv(rh_files[0])

        label, base = _scenario_label(scenario_name)

        print(f"  Analizando: {scenario_name} → {label}")

        # Order-level Mann-Whitney tests
        results = compare_policies(fcfs_df, rh_df, label)
        all_order_results.extend(results)

        # Normality pre-tests
        norm_rows = run_normality_tests(fcfs_df, rh_df, label)
        all_normality.extend(norm_rows)

        # Courier-level tests
        if fcfs_courier_files and rh_courier_files:
            fc_df = pd.read_csv(fcfs_courier_files[0])
            rc_df = pd.read_csv(rh_courier_files[0])
            courier_results = compare_courier_policies(fc_df, rc_df, label)
            all_courier_results.extend(courier_results)

        # Collect CTD deltas for Kruskal-Wallis (match by order_id)
        fcfs_prep = prepare_order_data(fcfs_df)
        rh_prep = prepare_order_data(rh_df)
        if "click_to_door" in fcfs_prep.columns and "click_to_door" in rh_prep.columns:
            # Per-order difference where both policies delivered the same order
            merged = fcfs_prep[["order_id", "click_to_door"]].merge(
                rh_prep[["order_id", "click_to_door"]],
                on="order_id", suffixes=("_fcfs", "_rh"),
            )
            delta = (merged["click_to_door_fcfs"] - merged["click_to_door_rh"]).dropna().values
            if len(delta) > 0:
                kw_data.setdefault(base, []).append(delta)

    if not all_order_results:
        print("  Sin resultados para analizar.")
        return pd.DataFrame()

    # ── Build main results DataFrame ──────────────────────────────────
    df = pd.DataFrame(all_order_results)

    # ── Apply Benjamini-Hochberg FDR correction ──────────────────────
    raw_p = df["p_value"].tolist()
    adjusted_p = benjamini_hochberg(raw_p)
    df["p_adjusted_BH"] = [round(p, 6) for p in adjusted_p]
    df["Significant (α=0.05)"] = df["p_value"].apply(lambda p: "Yes" if p < 0.05 else "No")
    df["Significant_BH (α=0.05)"] = df["p_adjusted_BH"].apply(lambda p: "Yes" if p < 0.05 else "No")

    # Save order-level tests
    out_path = run_path / "statistical_tests.csv"
    df.to_csv(out_path, index=False)
    print(f"\n  Tests guardados en: {out_path}")

    # ── Normality tests ──────────────────────────────────────────────
    if all_normality:
        norm_df = pd.DataFrame(all_normality)
        norm_path = run_path / "normality_tests.csv"
        norm_df.to_csv(norm_path, index=False)
        print(f"  Normality tests guardados en: {norm_path}")
        n_non_normal = len(norm_df[
            (norm_df["Normal_FCFS (α=0.05)"] == "No") | (norm_df["Normal_RH (α=0.05)"] == "No")
        ])
        print(f"  → {n_non_normal}/{len(norm_df)} distribuciones NO normales"
              f" → Mann-Whitney U justificado")

    # ── Courier-level tests ──────────────────────────────────────────
    if all_courier_results:
        c_df = pd.DataFrame(all_courier_results)
        c_raw_p = c_df["p_value"].tolist()
        c_adj_p = benjamini_hochberg(c_raw_p)
        c_df["p_adjusted_BH"] = [round(p, 6) for p in c_adj_p]
        c_df["Significant (α=0.05)"] = c_df["p_value"].apply(lambda p: "Yes" if p < 0.05 else "No")
        c_df["Significant_BH (α=0.05)"] = c_df["p_adjusted_BH"].apply(lambda p: "Yes" if p < 0.05 else "No")
        courier_path = run_path / "courier_level_tests.csv"
        c_df.to_csv(courier_path, index=False)
        print(f"  Courier-level tests guardados en: {courier_path}")

    # ── Cross-seed aggregation ───────────────────────────────────────
    _generate_cross_seed_aggregation(df, run_path)
    if all_courier_results:
        _generate_cross_seed_aggregation(
            pd.DataFrame(all_courier_results), run_path,
            filename="cross_seed_courier_aggregation.csv",
            label="Courier",
        )

    # ── Kruskal-Wallis omnibus test ──────────────────────────────────
    _run_kruskal_wallis(kw_data, run_path)

    # ── Summary pivot ────────────────────────────────────────────────
    if len(df) > 0:
        summary = df.pivot_table(
            index="Scenario",
            columns="Metric",
            values=["p_value", "p_adjusted_BH", "Rank_Biserial_r", "Mean_FCFS", "Mean_RH"],
            aggfunc="first",
        )
        summary_path = run_path / "statistical_summary.csv"
        summary.to_csv(summary_path)
        print(f"  Resumen guardado en: {summary_path}")

    # ── Console output ───────────────────────────────────────────────
    _print_results(df)
    if all_courier_results:
        _print_results(pd.DataFrame(all_courier_results), title="COURIER-LEVEL")

    return df


# ──────────────────────────────────────────────────────────────────────
# Cross-seed aggregation (mean ± std per base scenario)
# ──────────────────────────────────────────────────────────────────────
def _generate_cross_seed_aggregation(df, run_path, filename="cross_seed_aggregation.csv",
                                     label="Order"):
    """Aggregate results across seeds for each base scenario."""
    # Extract base scenario (e.g., "S1 – Baja (18:1)" without seed suffix)
    df = df.copy()
    df["Base_Scenario"] = df["Scenario"].str.replace(r"\s*\(seed \d+\)", "", regex=True)

    agg_rows = []
    for (base, metric), g in df.groupby(["Base_Scenario", "Metric"]):
        if len(g) < 2:
            continue
        agg_rows.append({
            "Base_Scenario": base,
            "Metric": metric,
            "n_seeds": len(g),
            "Mean_FCFS_avg": round(g["Mean_FCFS"].mean(), 3),
            "Mean_FCFS_std": round(g["Mean_FCFS"].std(), 3),
            "Mean_RH_avg": round(g["Mean_RH"].mean(), 3),
            "Mean_RH_std": round(g["Mean_RH"].std(), 3),
            "Median_FCFS_avg": round(g["Median_FCFS"].mean(), 3),
            "Median_RH_avg": round(g["Median_RH"].mean(), 3),
            "Rank_Biserial_r_avg": round(g["Rank_Biserial_r"].mean(), 4),
            "Rank_Biserial_r_std": round(g["Rank_Biserial_r"].std(), 4),
            "All_Significant_BH": "Yes" if (
                "Significant_BH (α=0.05)" in g.columns
                and (g["Significant_BH (α=0.05)"] == "Yes").all()
            ) else (
                "Yes" if all(g["p_value"] < 0.05) else "No"
            ),
        })

    if agg_rows:
        agg_df = pd.DataFrame(agg_rows)
        agg_path = run_path / filename
        agg_df.to_csv(agg_path, index=False)
        print(f"  {label} cross-seed aggregation guardada en: {agg_path}")

        # Print summary
        print(f"\n  {'─' * 80}")
        print(f"  AGREGACIÓN CROSS-SEED ({label}-level): media ± std")
        print(f"  {'─' * 80}")
        for base in agg_df["Base_Scenario"].unique():
            print(f"\n  {base}  ({agg_df[agg_df['Base_Scenario']==base]['n_seeds'].iloc[0]} seeds)")
            sub = agg_df[agg_df["Base_Scenario"] == base]
            for _, row in sub.iterrows():
                print(
                    f"    {row['Metric']:<30s} "
                    f"FCFS={row['Mean_FCFS_avg']:>8.2f}±{row['Mean_FCFS_std']:<6.2f} "
                    f"RH={row['Mean_RH_avg']:>8.2f}±{row['Mean_RH_std']:<6.2f} "
                    f"r={row['Rank_Biserial_r_avg']:>7.4f}±{row['Rank_Biserial_r_std']:<6.4f}"
                )


# ──────────────────────────────────────────────────────────────────────
# Kruskal-Wallis omnibus test across scenarios
# ──────────────────────────────────────────────────────────────────────
def _run_kruskal_wallis(kw_data, run_path):
    """Test whether the CTD improvement (FCFS−RH) varies across scenarios."""
    if len(kw_data) < 2:
        return

    # Flatten seeds within each base scenario
    groups = {}
    for base, delta_lists in sorted(kw_data.items()):
        groups[base] = np.concatenate(delta_lists)

    group_arrays = list(groups.values())
    group_names = list(groups.keys())

    if any(len(g) < 2 for g in group_arrays):
        return

    h_stat, p_value = kruskal(*group_arrays)

    kw_rows = []
    for name, arr in zip(group_names, group_arrays):
        kw_rows.append({
            "Scenario": name,
            "n": len(arr),
            "Mean_Delta_CTD": round(np.mean(arr), 3),
            "Median_Delta_CTD": round(np.median(arr), 3),
            "Std_Delta_CTD": round(np.std(arr), 3),
        })

    kw_df = pd.DataFrame(kw_rows)
    kw_df["Kruskal_Wallis_H"] = round(h_stat, 4)
    kw_df["p_value"] = round(p_value, 6)
    kw_df["Significant (α=0.05)"] = "Yes" if p_value < 0.05 else "No"

    kw_path = run_path / "kruskal_wallis_omnibus.csv"
    kw_df.to_csv(kw_path, index=False)
    print(f"\n  Kruskal-Wallis omnibus guardado en: {kw_path}")
    print(f"  → H={h_stat:.4f}, p={p_value:.6f}"
          f"  {'***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")
    print(f"  → La mejora de RH sobre FCFS"
          f" {'SÍ' if p_value < 0.05 else 'NO'}"
          f" varía significativamente entre escenarios de saturación.")


# ──────────────────────────────────────────────────────────────────────
# Console pretty printer
# ──────────────────────────────────────────────────────────────────────
def _print_results(df, title="ORDER-LEVEL"):
    """Print formatted results table to console."""
    print(f"\n{'=' * 90}")
    print(f"RESULTADOS DE PRUEBAS ESTADÍSTICAS — {title} (Mann-Whitney U + BH FDR)")
    print("=" * 90)
    for scenario in df["Scenario"].unique():
        sdf = df[df["Scenario"] == scenario]
        print(f"\n  {scenario}")
        print(f"  {'─' * 80}")
        for _, row in sdf.iterrows():
            p = row["p_value"]
            sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
            bh_note = ""
            if "p_adjusted_BH" in row.index and row["p_adjusted_BH"] >= 0.05 and p < 0.05:
                bh_note = " [ns after BH]"
            print(
                f"    {row['Metric']:<30s} "
                f"FCFS={row['Mean_FCFS']:>8.2f}  RH={row['Mean_RH']:>8.2f}  "
                f"U={row['U_statistic']:>10.0f}  p={p:<10.6f} {sig:>4s}{bh_note}  "
                f"r={row['Rank_Biserial_r']:>7.4f} ({row['Effect_Size']})"
            )


# ──────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Análisis estadístico FCFS vs RH (Mann-Whitney U + BH FDR + cross-seed)",
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
        n_sig_bh = len(df[df["p_adjusted_BH"] < 0.05]) if "p_adjusted_BH" in df.columns else n_sig
        n_total = len(df)
        print(f"\n  Resumen: {n_sig}/{n_total} pruebas significativas (α=0.05 sin corregir)")
        print(f"           {n_sig_bh}/{n_total} pruebas significativas (α=0.05 con BH FDR)")


if __name__ == "__main__":
    main()