#!/usr/bin/env python
"""
statistical_analysis.py – Pruebas estadísticas para comparar FCFS vs RH
========================================================================

Aplica el siguiente diseño metodológico para cada escenario de saturación y
cada KPI a nivel de orden, corrigiendo los flancos identificados en la
auditoría adversarial del Cap. 4.5:

PRIMARIA (pareada, intra-instancia):
  - Wilcoxon signed-rank pareado (Wilcoxon 1945) sobre las diferencias
    CtD_FCFS - CtD_RH para órdenes entregadas por AMBAS políticas
  - Diferencia de medias con intervalo de confianza bootstrap (Efron 1993)
  - Matched-pairs rank-biserial como tamaño de efecto pareado

PRIMARIA (entre-instancia, evita pseudo-replicación):
  - Wilcoxon pareado a nivel SEMILLA sobre las medias por seed
    (N_efectivo = #semillas, no #órdenes)
  - Friedman test (sustituye a Kruskal-Wallis) para el efecto del régimen

AUXILIARES (descriptivas):
  - Mann-Whitney U sobre datos no pareados (preservada para comparabilidad
    con la corrida previa; reportada como secundaria)
  - Rank-biserial r de MWU
  - Shapiro-Wilk (informativo, no decisivo)

AGREGACIÓN:
  - Fisher z-transform para promediar correlaciones cross-seed
  - Benjamini-Hochberg FDR para multiplicidad
  - Reporte adicional con Holm-Bonferroni como sanity check

BINARIAS:
  - SLA compliance: test de proporciones (z-test) en lugar de MWU

Uso:
  python scripts/statistical_analysis.py
  python scripts/statistical_analysis.py --run-dir results/experiments/<id>
  python scripts/statistical_analysis.py --scenario S3_media

Salida:
  statistical_tests.csv         — tabla completa (orden, Wilcoxon + MWU + bootstrap)
  statistical_summary.csv       — pivote por escenario
  normality_tests.csv           — Shapiro-Wilk (informativo)
  cross_seed_aggregation.csv    — agregación con Fisher z
  seed_level_tests.csv          — Wilcoxon pareado a nivel semilla (PRIMARIO)
  friedman_omnibus.csv          — Friedman (sustituye a Kruskal-Wallis)
  courier_level_tests.csv       — courier-level (auxiliar)
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import (
    friedmanchisquare,
    kruskal,
    mannwhitneyu,
    norm,
    shapiro,
    wilcoxon,
)

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
# Effect-size helpers
# ──────────────────────────────────────────────────────────────────────
def rank_biserial(u_stat, n1, n2):
    """Rank-biserial r a partir de U (no pareado): r = 1 - 2U/(n1*n2)."""
    return 1.0 - (2.0 * u_stat) / (n1 * n2)


def matched_pairs_rank_biserial(diffs):
    """Matched-pairs rank-biserial r para Wilcoxon signed-rank.

    Definición operativa (Kerby 2014): r = (W+ - W-) / sum(|R_i|),
    donde W+ es la suma de rangos positivos y W- la de rangos negativos.
    Rango [-1, 1]: signo positivo indica que el primer grupo (e.g. FCFS)
    es estocásticamente menor que el segundo (RH).
    """
    diffs = np.asarray(diffs)
    diffs = diffs[diffs != 0]  # Wilcoxon descarta empates en cero
    if len(diffs) == 0:
        return 0.0
    abs_diffs = np.abs(diffs)
    ranks = pd.Series(abs_diffs).rank().values
    w_pos = ranks[diffs > 0].sum()
    w_neg = ranks[diffs < 0].sum()
    total = ranks.sum()
    if total == 0:
        return 0.0
    return float((w_pos - w_neg) / total)


def effect_size_label(r):
    """Clasificación de magnitud (convención Cohen 1988 / Funder-Ozer 2019)."""
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
# Bootstrap CI para diferencia de medias pareada (Efron-Tibshirani 1993)
# ──────────────────────────────────────────────────────────────────────
def bootstrap_mean_diff_ci(x, y, n_boot=10000, alpha=0.05, seed=42):
    """CI bootstrap percentil para la diferencia de medias pareada (x - y).

    Requiere que x[i] y y[i] correspondan a la MISMA unidad (orden); los
    pares se preservan al remuestrear con reemplazo.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) != len(y):
        raise ValueError("bootstrap pareado requiere len(x) == len(y)")
    n = len(x)
    if n < 2:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    diffs = x - y
    mean_diff = float(np.mean(diffs))
    boot_means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = np.mean(diffs[idx])
    ci_low = float(np.percentile(boot_means, 100 * alpha / 2))
    ci_high = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return mean_diff, ci_low, ci_high


# ──────────────────────────────────────────────────────────────────────
# Multiple-comparison corrections
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


def holm_bonferroni(p_values):
    """Holm-Bonferroni step-down correction (más conservadora que BH)."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_idx = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_idx]
    adjusted = np.empty(n)
    cummax = 0.0
    for i in range(n):
        adjusted_p = sorted_p[i] * (n - i)
        cummax = max(cummax, adjusted_p)
        adjusted[sorted_idx[i]] = min(cummax, 1.0)
    return adjusted.tolist()


# ──────────────────────────────────────────────────────────────────────
# Fisher z-transform para promediar correlaciones
# ──────────────────────────────────────────────────────────────────────
def fisher_z_aggregate(r_values):
    """Promedia correlaciones en escala Fisher z y devuelve (r_aggregated, ci_low, ci_high).

    Adecuado para combinar rank-biserial r entre semillas.  Devuelve
    también un intervalo de confianza al 95% retransformado a escala r.
    """
    r_arr = np.asarray(r_values, dtype=float)
    r_arr = r_arr[~np.isnan(r_arr)]
    # Clip para evitar arctanh(±1) = ±∞
    r_arr = np.clip(r_arr, -0.9999, 0.9999)
    if len(r_arr) == 0:
        return float("nan"), float("nan"), float("nan")
    z = np.arctanh(r_arr)
    z_mean = z.mean()
    if len(r_arr) > 1:
        z_se = z.std(ddof=1) / np.sqrt(len(r_arr))
        ci_low = float(np.tanh(z_mean - 1.96 * z_se))
        ci_high = float(np.tanh(z_mean + 1.96 * z_se))
    else:
        ci_low = ci_high = float(np.tanh(z_mean))
    return float(np.tanh(z_mean)), ci_low, ci_high


# ──────────────────────────────────────────────────────────────────────
# Test de proporciones (z-test de dos muestras) para variables binarias
# ──────────────────────────────────────────────────────────────────────
def two_proportion_ztest(x, y):
    """Prueba z de dos proporciones para datos binarios pareados/no pareados.

    Devuelve (p_fcfs, p_rh, diff, z_stat, p_value, ci_low, ci_high).
    Usa aproximación normal con corrección de Wald.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return tuple([float("nan")] * 7)
    p1, p2 = x.mean(), y.mean()
    p_pool = (x.sum() + y.sum()) / (n1 + n2)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se_pool == 0:
        z_stat = 0.0
        p_value = 1.0
    else:
        z_stat = (p1 - p2) / se_pool
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))
    se_diff = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    ci_low = (p1 - p2) - 1.96 * se_diff
    ci_high = (p1 - p2) + 1.96 * se_diff
    return float(p1), float(p2), float(p1 - p2), float(z_stat), float(p_value), float(ci_low), float(ci_high)


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


def _paired_test_row(x_paired, y_paired, x_all, y_all, metric_key, scenario_label):
    """Compone una fila combinando Wilcoxon pareado (primario), Mann-Whitney U
    (auxiliar), bootstrap CI de Δ media, y métricas descriptivas.

    Argumentos:
      x_paired, y_paired: vectores PAREADOS (mismo order_id), igual longitud.
      x_all, y_all: vectores sin pareamiento (incluyen órdenes no compartidas).
                    Se usan para Mann-Whitney U auxiliar y estadísticos
                    descriptivos.
    """
    if len(x_paired) < 2 or len(y_paired) < 2 or len(x_all) < 2 or len(y_all) < 2:
        return None

    diffs = x_paired - y_paired
    # Para Wilcoxon: si todas las diferencias son cero (e.g. bundle_size en FCFS=1
    # vs FCFS=1) la prueba degenera; manejamos con NaN explícito.
    nonzero = diffs[diffs != 0]
    if len(nonzero) == 0:
        w_stat = 0.0
        p_wilcoxon = 1.0
        r_paired = 0.0
    else:
        try:
            w_stat, p_wilcoxon = wilcoxon(x_paired, y_paired, alternative="two-sided", zero_method="wilcox")
        except ValueError:
            w_stat, p_wilcoxon = float("nan"), float("nan")
        r_paired = matched_pairs_rank_biserial(diffs)

    # Mann-Whitney U (auxiliar) sobre datos sin pareamiento
    try:
        u_stat, p_mwu = mannwhitneyu(x_all, y_all, alternative="two-sided")
        r_unpaired = rank_biserial(u_stat, len(x_all), len(y_all))
    except ValueError:
        u_stat, p_mwu, r_unpaired = float("nan"), float("nan"), float("nan")

    # Bootstrap CI para diferencia de medias pareada
    mean_diff, ci_low, ci_high = bootstrap_mean_diff_ci(x_paired, y_paired, n_boot=2000)

    label = METRIC_LABELS.get(metric_key, COURIER_METRIC_LABELS.get(metric_key, metric_key))
    return {
        "Scenario": scenario_label,
        "Metric": label,
        "n_paired": len(x_paired),
        "n_FCFS_all": len(x_all),
        "n_RH_all": len(y_all),
        "Mean_FCFS": round(float(np.mean(x_all)), 3),
        "Mean_RH": round(float(np.mean(y_all)), 3),
        "Median_FCFS": round(float(np.median(x_all)), 3),
        "Median_RH": round(float(np.median(y_all)), 3),
        "P90_FCFS": round(float(np.percentile(x_all, 90)), 3),
        "P90_RH": round(float(np.percentile(y_all, 90)), 3),
        "P95_FCFS": round(float(np.percentile(x_all, 95)), 3),
        "P95_RH": round(float(np.percentile(y_all, 95)), 3),
        # Prueba PRIMARIA: Wilcoxon pareado
        "W_statistic": round(float(w_stat), 2) if not np.isnan(w_stat) else float("nan"),
        "p_wilcoxon_paired": round(float(p_wilcoxon), 6) if not np.isnan(p_wilcoxon) else float("nan"),
        "Rank_Biserial_r_paired": round(float(r_paired), 4),
        "Effect_Size_paired": effect_size_label(r_paired),
        # Diferencia de medias con CI bootstrap (interpretación operativa)
        "Mean_Diff_FCFS_minus_RH": round(float(mean_diff), 3) if not np.isnan(mean_diff) else float("nan"),
        "Mean_Diff_CI_low": round(float(ci_low), 3) if not np.isnan(ci_low) else float("nan"),
        "Mean_Diff_CI_high": round(float(ci_high), 3) if not np.isnan(ci_high) else float("nan"),
        # Auxiliar: Mann-Whitney U (sin pareamiento) para comparabilidad histórica
        "U_statistic_aux": round(float(u_stat), 1) if not np.isnan(u_stat) else float("nan"),
        "p_mannwhitney_aux": round(float(p_mwu), 6) if not np.isnan(p_mwu) else float("nan"),
        "Rank_Biserial_r_unpaired": round(float(r_unpaired), 4) if not np.isnan(r_unpaired) else float("nan"),
        # p_value canónico = Wilcoxon pareado (para BH-FDR sobre la prueba primaria)
        "p_value": round(float(p_wilcoxon), 6) if not np.isnan(p_wilcoxon) else 1.0,
    }


def _proportion_test_row(x_paired, y_paired, x_all, y_all, metric_key, scenario_label):
    """Test específico para variables binarias (sla_met): z-test de proporciones."""
    p1, p2, diff, z_stat, p_value, ci_low, ci_high = two_proportion_ztest(x_all, y_all)
    label = METRIC_LABELS.get(metric_key, metric_key)
    # También computamos Wilcoxon pareado por consistencia de tabla
    paired_row = _paired_test_row(x_paired, y_paired, x_all, y_all, metric_key, scenario_label)
    if paired_row is None:
        return None
    paired_row.update({
        "Proportion_FCFS": round(float(p1), 6),
        "Proportion_RH": round(float(p2), 6),
        "Prop_Diff_FCFS_minus_RH": round(float(diff), 6),
        "z_statistic_prop": round(float(z_stat), 4),
        "p_proportion_ztest": round(float(p_value), 6),
        "Prop_Diff_CI_low": round(float(ci_low), 6),
        "Prop_Diff_CI_high": round(float(ci_high), 6),
        # Para datos binarios, p_value primario = proportion z-test
        "p_value": round(float(p_value), 6),
    })
    return paired_row


def _extract_paired_arrays(fcfs_prep, rh_prep, metric):
    """Devuelve (x_paired, y_paired, x_all, y_all) para una métrica.

    Inner-merge por order_id para construir los pares; preserva los arrays
    completos para descripción y MWU auxiliar.
    """
    if metric not in fcfs_prep.columns or metric not in rh_prep.columns:
        return None, None, None, None
    if "order_id" not in fcfs_prep.columns or "order_id" not in rh_prep.columns:
        # Fallback: sin order_id no podemos parear; devolvemos solo no-pareados
        x_all = fcfs_prep[metric].dropna().values
        y_all = rh_prep[metric].dropna().values
        return x_all, y_all, x_all, y_all
    paired = fcfs_prep[["order_id", metric]].merge(
        rh_prep[["order_id", metric]],
        on="order_id",
        suffixes=("_fcfs", "_rh"),
    ).dropna()
    x_paired = paired[f"{metric}_fcfs"].values
    y_paired = paired[f"{metric}_rh"].values
    x_all = fcfs_prep[metric].dropna().values
    y_all = rh_prep[metric].dropna().values
    return x_paired, y_paired, x_all, y_all


def compare_policies(fcfs_df, rh_df, scenario_label=""):
    """Aplica Wilcoxon pareado (primario) + MWU (auxiliar) + bootstrap CI
    a cada métrica de orden.  La métrica `sla_met` usa test de proporciones.
    """
    fcfs = prepare_order_data(fcfs_df)
    rh = prepare_order_data(rh_df)

    results = []
    all_metrics = ORDER_LEVEL_METRICS + EXTENDED_ORDER_METRICS

    for metric in all_metrics:
        x_paired, y_paired, x_all, y_all = _extract_paired_arrays(fcfs, rh, metric)
        if x_paired is None:
            continue
        if metric == "sla_met":
            row = _proportion_test_row(x_paired, y_paired, x_all, y_all, metric, scenario_label)
        else:
            row = _paired_test_row(x_paired, y_paired, x_all, y_all, metric, scenario_label)
        if row:
            results.append(row)

    return results


def compare_courier_policies(fcfs_courier_df, rh_courier_df, scenario_label=""):
    """Aplica Wilcoxon pareado a métricas de courier (pareando por courier_id)."""
    fcfs = prepare_courier_data(fcfs_courier_df)
    rh = prepare_courier_data(rh_courier_df)

    results = []
    for metric in COURIER_METRICS:
        if metric not in fcfs.columns or metric not in rh.columns:
            continue
        # Pareamiento por courier_id si existe; si no, fallback a no pareado
        if "courier_id" in fcfs.columns and "courier_id" in rh.columns:
            paired = fcfs[["courier_id", metric]].merge(
                rh[["courier_id", metric]],
                on="courier_id",
                suffixes=("_fcfs", "_rh"),
            ).dropna()
            x_paired = paired[f"{metric}_fcfs"].values
            y_paired = paired[f"{metric}_rh"].values
        else:
            x_paired = fcfs[metric].dropna().values
            y_paired = rh[metric].dropna().values
            # Recorte para igualar tamaños (solución barata cuando no hay id)
            min_n = min(len(x_paired), len(y_paired))
            x_paired = x_paired[:min_n]
            y_paired = y_paired[:min_n]
        x_all = fcfs[metric].dropna().values
        y_all = rh[metric].dropna().values
        row = _paired_test_row(x_paired, y_paired, x_all, y_all, metric, scenario_label)
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
    # Diccionario para agregación a nivel SEMILLA: (base, metric) -> list of (mean_fcfs, mean_rh, seed)
    seed_level_data = {}
    # Friedman omnibus: necesitamos vector (seed, scenario) -> mean CtD para cada política
    friedman_data = {"fcfs": {}, "rh": {}}  # política -> {seed -> {scenario: mean_ctd}}

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
        seed = scenario_name.split("_seed")[-1] if "_seed" in scenario_name else "unknown"

        print(f"  Analizando: {scenario_name} → {label}")

        # Order-level paired tests (Wilcoxon + bootstrap + MWU auxiliar)
        results = compare_policies(fcfs_df, rh_df, label)
        all_order_results.extend(results)

        # Normality pre-tests (informativo, no decisivo)
        norm_rows = run_normality_tests(fcfs_df, rh_df, label)
        all_normality.extend(norm_rows)

        # Courier-level tests
        if fcfs_courier_files and rh_courier_files:
            fc_df = pd.read_csv(fcfs_courier_files[0])
            rc_df = pd.read_csv(rh_courier_files[0])
            courier_results = compare_courier_policies(fc_df, rc_df, label)
            all_courier_results.extend(courier_results)

        # Recolectar datos a nivel SEMILLA (Fase B): media por seed × escenario × métrica
        fcfs_prep = prepare_order_data(fcfs_df)
        rh_prep = prepare_order_data(rh_df)
        for metric in ORDER_LEVEL_METRICS + EXTENDED_ORDER_METRICS:
            if metric not in fcfs_prep.columns or metric not in rh_prep.columns:
                continue
            mean_fcfs = float(fcfs_prep[metric].dropna().mean()) if len(fcfs_prep[metric].dropna()) else float("nan")
            mean_rh = float(rh_prep[metric].dropna().mean()) if len(rh_prep[metric].dropna()) else float("nan")
            seed_level_data.setdefault((base, metric), []).append({
                "seed": seed,
                "mean_fcfs": mean_fcfs,
                "mean_rh": mean_rh,
            })

        # Friedman omnibus: media de CtD por (seed, scenario) para cada política
        if "click_to_door" in fcfs_prep.columns and "click_to_door" in rh_prep.columns:
            mean_ctd_fcfs = float(fcfs_prep["click_to_door"].dropna().mean())
            mean_ctd_rh = float(rh_prep["click_to_door"].dropna().mean())
            friedman_data["fcfs"].setdefault(seed, {})[base] = mean_ctd_fcfs
            friedman_data["rh"].setdefault(seed, {})[base] = mean_ctd_rh

    if not all_order_results:
        print("  Sin resultados para analizar.")
        return pd.DataFrame()

    # ── Build main results DataFrame ──────────────────────────────────
    df = pd.DataFrame(all_order_results)

    # ── Apply Benjamini-Hochberg AND Holm-Bonferroni FDR corrections ─
    raw_p = df["p_value"].tolist()
    adjusted_bh = benjamini_hochberg(raw_p)
    adjusted_holm = holm_bonferroni(raw_p)
    df["p_adjusted_BH"] = [round(p, 6) for p in adjusted_bh]
    df["p_adjusted_Holm"] = [round(p, 6) for p in adjusted_holm]
    df["Significant (α=0.05)"] = df["p_value"].apply(lambda p: "Yes" if p < 0.05 else "No")
    df["Significant_BH (α=0.05)"] = df["p_adjusted_BH"].apply(lambda p: "Yes" if p < 0.05 else "No")
    df["Significant_Holm (α=0.05)"] = df["p_adjusted_Holm"].apply(lambda p: "Yes" if p < 0.05 else "No")

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

    # ── Análisis a nivel SEMILLA (PRIMARIO, evita pseudo-replicación) ─
    _run_seed_level_tests(seed_level_data, run_path)

    # ── Friedman omnibus (sustituye a Kruskal-Wallis) ────────────────
    _run_friedman(friedman_data, run_path)

    # ── Summary pivot ────────────────────────────────────────────────
    if len(df) > 0:
        summary = df.pivot_table(
            index="Scenario",
            columns="Metric",
            values=["p_value", "p_adjusted_BH", "Rank_Biserial_r_paired", "Mean_FCFS", "Mean_RH"],
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
# Cross-seed aggregation con Fisher z-transform (Fase D)
# ──────────────────────────────────────────────────────────────────────
def _generate_cross_seed_aggregation(df, run_path, filename="cross_seed_aggregation.csv",
                                     label="Order"):
    """Agrega resultados cross-seed usando Fisher z para correlaciones."""
    df = df.copy()
    df["Base_Scenario"] = df["Scenario"].str.replace(r"\s*\(seed \d+\)", "", regex=True)

    # Detectar columna de correlación (pareada si existe, caer a no pareada)
    r_col = "Rank_Biserial_r_paired" if "Rank_Biserial_r_paired" in df.columns else "Rank_Biserial_r_unpaired"
    if r_col not in df.columns:
        r_col = None

    agg_rows = []
    for (base, metric), g in df.groupby(["Base_Scenario", "Metric"]):
        if len(g) < 2:
            continue
        row = {
            "Base_Scenario": base,
            "Metric": metric,
            "n_seeds": len(g),
            "Mean_FCFS_avg": round(g["Mean_FCFS"].mean(), 3),
            "Mean_FCFS_std": round(g["Mean_FCFS"].std(), 3),
            "Mean_RH_avg": round(g["Mean_RH"].mean(), 3),
            "Mean_RH_std": round(g["Mean_RH"].std(), 3),
            "Median_FCFS_avg": round(g["Median_FCFS"].mean(), 3),
            "Median_RH_avg": round(g["Median_RH"].mean(), 3),
        }
        if r_col is not None:
            r_pooled, r_ci_low, r_ci_high = fisher_z_aggregate(g[r_col].values)
            row.update({
                "r_pooled_FisherZ": round(r_pooled, 4),
                "r_CI_low_FisherZ": round(r_ci_low, 4),
                "r_CI_high_FisherZ": round(r_ci_high, 4),
                # Mantener el promedio aritmético etiquetado como ingenuo
                "r_arithmetic_mean": round(g[r_col].mean(), 4),
            })
        row["All_Significant_BH"] = "Yes" if (
            "Significant_BH (α=0.05)" in g.columns
            and (g["Significant_BH (α=0.05)"] == "Yes").all()
        ) else (
            "Yes" if all(g["p_value"] < 0.05) else "No"
        )
        agg_rows.append(row)

    if agg_rows:
        agg_df = pd.DataFrame(agg_rows)
        agg_path = run_path / filename
        agg_df.to_csv(agg_path, index=False)
        print(f"  {label} cross-seed aggregation (Fisher z) guardada en: {agg_path}")

        # Print summary
        print(f"\n  {'─' * 80}")
        print(f"  AGREGACIÓN CROSS-SEED ({label}-level): Fisher z [CI 95%]")
        print(f"  {'─' * 80}")
        for base in agg_df["Base_Scenario"].unique():
            n_s = agg_df[agg_df['Base_Scenario'] == base]['n_seeds'].iloc[0]
            print(f"\n  {base}  ({n_s} seeds)")
            sub = agg_df[agg_df["Base_Scenario"] == base]
            for _, row in sub.iterrows():
                r_pooled = row.get("r_pooled_FisherZ", float("nan"))
                ci_low = row.get("r_CI_low_FisherZ", float("nan"))
                ci_high = row.get("r_CI_high_FisherZ", float("nan"))
                print(
                    f"    {row['Metric']:<30s} "
                    f"FCFS={row['Mean_FCFS_avg']:>8.2f}±{row['Mean_FCFS_std']:<6.2f} "
                    f"RH={row['Mean_RH_avg']:>8.2f}±{row['Mean_RH_std']:<6.2f} "
                    f"r={r_pooled:>7.4f} [{ci_low:>6.3f}, {ci_high:>6.3f}]"
                )


# ──────────────────────────────────────────────────────────────────────
# Análisis a nivel SEMILLA (Fase B) — la prueba primaria
# ──────────────────────────────────────────────────────────────────────
def _run_seed_level_tests(seed_level_data, run_path):
    """Wilcoxon pareado sobre las MEDIAS por semilla (N efectivo = #semillas).

    Esto evita la pseudo-replicación: cada semilla aporta una observación
    independiente al test, no las miles de órdenes que contiene.
    """
    if not seed_level_data:
        return

    rows = []
    for (base, metric), records in sorted(seed_level_data.items()):
        if len(records) < 2:
            continue
        # Filtrar semillas fallidas (means NaN o ambos 0 que indica corrida vacía)
        valid = [
            r for r in records
            if not (np.isnan(r["mean_fcfs"]) or np.isnan(r["mean_rh"]))
            and not (r["mean_fcfs"] == 0.0 and r["mean_rh"] == 0.0 and metric != "sla_met")
        ]
        if len(valid) < 2:
            continue
        fcfs_vec = np.array([r["mean_fcfs"] for r in valid])
        rh_vec = np.array([r["mean_rh"] for r in valid])
        diffs = fcfs_vec - rh_vec
        nonzero = diffs[diffs != 0]
        if len(nonzero) < 2:
            w_stat, p_value = float("nan"), 1.0
        else:
            try:
                w_stat, p_value = wilcoxon(fcfs_vec, rh_vec, alternative="two-sided", zero_method="wilcox")
            except ValueError:
                w_stat, p_value = float("nan"), float("nan")
        r_paired = matched_pairs_rank_biserial(diffs)
        # CI t-Student de muestra pequeña (más apropiado que bootstrap para n=7)
        mean_diff = float(np.mean(diffs))
        if len(diffs) >= 2:
            se = float(np.std(diffs, ddof=1) / np.sqrt(len(diffs)))
            from scipy.stats import t as t_dist
            t_crit = t_dist.ppf(0.975, df=len(diffs) - 1)
            ci_low = mean_diff - t_crit * se
            ci_high = mean_diff + t_crit * se
        else:
            ci_low = ci_high = float("nan")

        label = METRIC_LABELS.get(metric, metric)
        rows.append({
            "Base_Scenario": base,
            "Metric": label,
            "n_seeds_valid": len(valid),
            "n_seeds_total": len(records),
            "Mean_FCFS": round(float(np.mean(fcfs_vec)), 4),
            "Mean_RH": round(float(np.mean(rh_vec)), 4),
            "Mean_Diff_FCFS_minus_RH": round(mean_diff, 4),
            "CI_low_95": round(float(ci_low), 4),
            "CI_high_95": round(float(ci_high), 4),
            "W_statistic_seed": round(float(w_stat), 2) if not np.isnan(w_stat) else float("nan"),
            "p_value_seed": round(float(p_value), 6) if not np.isnan(p_value) else float("nan"),
            "Rank_Biserial_r_seed": round(float(r_paired), 4),
            "Effect_Size_seed": effect_size_label(r_paired),
            "Significant_seed (α=0.05)": "Yes" if (not np.isnan(p_value) and p_value < 0.05) else "No",
        })

    if not rows:
        return

    seed_df = pd.DataFrame(rows)
    # Aplicar BH-FDR sobre los p-valores a nivel semilla
    p_vec = seed_df["p_value_seed"].fillna(1.0).tolist()
    seed_df["p_seed_BH"] = [round(p, 6) for p in benjamini_hochberg(p_vec)]
    seed_df["Significant_seed_BH (α=0.05)"] = seed_df["p_seed_BH"].apply(
        lambda p: "Yes" if p < 0.05 else "No"
    )

    out_path = run_path / "seed_level_tests.csv"
    seed_df.to_csv(out_path, index=False)
    print(f"\n  ★ Seed-level tests (PRIMARIO, n_efectivo = #semillas) guardado en: {out_path}")
    print(f"  {'─' * 80}")
    for base in seed_df["Base_Scenario"].unique():
        print(f"\n  {base}")
        sub = seed_df[seed_df["Base_Scenario"] == base]
        for _, row in sub.iterrows():
            sig = "***" if row["p_value_seed"] < 0.001 else (
                "**" if row["p_value_seed"] < 0.01 else (
                    "*" if row["p_value_seed"] < 0.05 else "ns"))
            print(
                f"    {row['Metric']:<28s} "
                f"Δ̄={row['Mean_Diff_FCFS_minus_RH']:>+8.3f} "
                f"[{row['CI_low_95']:>+7.3f}, {row['CI_high_95']:>+7.3f}]  "
                f"W={row['W_statistic_seed']:>6.1f}  p={row['p_value_seed']:<10.6f} {sig:>3s}  "
                f"r={row['Rank_Biserial_r_seed']:>+6.3f} ({row['Effect_Size_seed']})"
            )


# ──────────────────────────────────────────────────────────────────────
# Friedman omnibus (sustituye a Kruskal-Wallis, Fase E)
# ──────────────────────────────────────────────────────────────────────
def _run_friedman(friedman_data, run_path):
    """Friedman test sobre Δ CtD = CtD_FCFS − CtD_RH a nivel seed × escenario.

    Para cada semilla disponible en TODOS los escenarios, calcula Δ
    en cada escenario, y aplica Friedman para detectar si la mejora
    de RH varía significativamente entre regímenes de saturación.
    Requiere ≥ 3 escenarios y ≥ 2 semillas comunes.
    """
    fcfs_seed = friedman_data.get("fcfs", {})
    rh_seed = friedman_data.get("rh", {})
    if not fcfs_seed or not rh_seed:
        return

    # Encontrar semillas comunes y escenarios comunes
    common_seeds = sorted(set(fcfs_seed.keys()) & set(rh_seed.keys()))
    if len(common_seeds) < 2:
        return

    # Para cada semilla, determinar escenarios donde tiene datos en AMBAS políticas
    scenario_set = None
    for s in common_seeds:
        s_scenarios = set(fcfs_seed[s].keys()) & set(rh_seed[s].keys())
        scenario_set = s_scenarios if scenario_set is None else scenario_set & s_scenarios
    if not scenario_set or len(scenario_set) < 3:
        return

    scenarios = sorted(scenario_set)

    # Construir matriz seed × scenario de Δ = FCFS − RH
    matrix = []
    valid_seeds = []
    for s in common_seeds:
        row = [fcfs_seed[s][sc] - rh_seed[s][sc] for sc in scenarios]
        if all(not np.isnan(v) for v in row):
            matrix.append(row)
            valid_seeds.append(s)

    if len(matrix) < 2:
        return

    matrix = np.array(matrix)  # shape: (seeds, scenarios)
    # Friedman compara las COLUMNAS (escenarios), bloques = filas (semillas)
    f_stat, p_value = friedmanchisquare(*[matrix[:, j] for j in range(matrix.shape[1])])

    rows = []
    for j, sc in enumerate(scenarios):
        rows.append({
            "Scenario": sc,
            "n_seeds": len(valid_seeds),
            "Mean_Delta_CtD": round(float(matrix[:, j].mean()), 3),
            "Median_Delta_CtD": round(float(np.median(matrix[:, j])), 3),
            "Std_Delta_CtD": round(float(matrix[:, j].std(ddof=1)), 3),
        })
    fr_df = pd.DataFrame(rows)
    fr_df["Friedman_statistic"] = round(float(f_stat), 4)
    fr_df["p_value"] = round(float(p_value), 6)
    fr_df["Significant (α=0.05)"] = "Yes" if p_value < 0.05 else "No"

    fr_path = run_path / "friedman_omnibus.csv"
    fr_df.to_csv(fr_path, index=False)
    print(f"\n  Friedman omnibus guardado en: {fr_path}")
    sig = "***" if p_value < 0.001 else ("**" if p_value < 0.01 else ("*" if p_value < 0.05 else "ns"))
    print(f"  → χ²_Friedman = {f_stat:.4f}, p = {p_value:.6f}  {sig}")
    print(f"  → La mejora de RH sobre FCFS"
          f" {'SÍ' if p_value < 0.05 else 'NO'}"
          f" varía significativamente entre escenarios (n_seeds = {len(valid_seeds)}).")


# ──────────────────────────────────────────────────────────────────────
# Console pretty printer
# ──────────────────────────────────────────────────────────────────────
def _print_results(df, title="ORDER-LEVEL"):
    """Print formatted results table to console."""
    print(f"\n{'=' * 100}")
    print(f"RESULTADOS DE PRUEBAS ESTADÍSTICAS — {title} (Wilcoxon pareado primario + MWU auxiliar + BH/Holm)")
    print("=" * 100)
    # Detectar qué columnas usar (paired vs unpaired backward-compat)
    r_col = "Rank_Biserial_r_paired" if "Rank_Biserial_r_paired" in df.columns else "Rank_Biserial_r"
    eff_col = "Effect_Size_paired" if "Effect_Size_paired" in df.columns else "Effect_Size"
    stat_col = "W_statistic" if "W_statistic" in df.columns else "U_statistic"
    diff_col = "Mean_Diff_FCFS_minus_RH" if "Mean_Diff_FCFS_minus_RH" in df.columns else None

    for scenario in df["Scenario"].unique():
        sdf = df[df["Scenario"] == scenario]
        print(f"\n  {scenario}")
        print(f"  {'─' * 95}")
        for _, row in sdf.iterrows():
            p = row["p_value"]
            sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
            bh_note = ""
            if "p_adjusted_BH" in row.index and row["p_adjusted_BH"] >= 0.05 and p < 0.05:
                bh_note = " [ns/BH]"
            holm_note = ""
            if "p_adjusted_Holm" in row.index and row["p_adjusted_Holm"] >= 0.05 and p < 0.05:
                holm_note = " [ns/Holm]"
            stat_val = row.get(stat_col, float("nan"))
            r_val = row.get(r_col, float("nan"))
            eff_lbl = row.get(eff_col, "?")
            diff_str = ""
            if diff_col and not pd.isna(row.get(diff_col)):
                ci_low = row.get("Mean_Diff_CI_low", float("nan"))
                ci_high = row.get("Mean_Diff_CI_high", float("nan"))
                diff_str = f"Δμ={row[diff_col]:>+7.2f} [{ci_low:>+6.2f},{ci_high:>+6.2f}]  "
            print(
                f"    {row['Metric']:<28s} "
                f"FCFS={row['Mean_FCFS']:>8.2f}  RH={row['Mean_RH']:>8.2f}  "
                f"{diff_str}"
                f"W={stat_val:>10.0f}  p={p:<10.6f} {sig:>4s}{bh_note}{holm_note}  "
                f"r={r_val:>+6.3f} ({eff_lbl})"
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