#!/usr/bin/env python
"""
plot_results.py – Genera gráficas para el Capítulo 4 (Resultados)
==================================================================

Lee los CSVs generados por run_experiments.py y produce figuras PDF/PNG
listas para inclusión en LaTeX (\\includegraphics).

Uso:
  python scripts/plot_results.py                          # corrida más reciente
  python scripts/plot_results.py --run-dir results/experiments/20260306_143000

Salida (en el mismo directorio de la corrida):
  fig_ctd_boxplot.pdf       — Box plots de CTD por escenario y política
  fig_kpi_vs_ratio.pdf      — KPIs principales vs ratio de saturación
  fig_bundle_distribution.pdf — Distribución de tamaños de bundle
  fig_utilization_cost.pdf  — Utilización vs Costo/Pedido
"""

import argparse
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Backend no interactivo
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BASE_PATH = Path(__file__).resolve().parent.parent

SCENARIO_ORDER = ["S1_baja", "S2_moderada", "S3_media", "S4_alta", "S5_extrema"]
SCENARIO_SHORT = {
    "S1_baja": "S1\n(18:1)",
    "S2_moderada": "S2\n(26:1)",
    "S3_media": "S3\n(35:1)",
    "S4_alta": "S4\n(52:1)",
    "S5_extrema": "S5\n(75:1)",
}
RATIOS = [18, 26, 35, 52, 75]

FCFS_COLOR = "#2196F3"
RH_COLOR = "#FF9800"


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def discover_scenarios(run_path):
    """Devuelve dict {scenario_base_name: [list of (seed, dir)]}."""
    scenarios = {}
    for d in sorted(run_path.iterdir()):
        if not d.is_dir():
            continue
        if not any(f.name.endswith("_fcfs_results.csv") for f in d.iterdir()):
            continue
        # Parse scenario name
        name = d.name
        base = name
        seed = None
        for sn in SCENARIO_ORDER:
            if name.startswith(sn):
                base = sn
                if "_seed" in name:
                    seed = name.split("_seed")[-1]
                break
        scenarios.setdefault(base, []).append((seed, d))
    return scenarios


def load_order_data(scenario_dir):
    """Carga datos de órdenes delivered para FCFS y RH."""
    fcfs_files = list(scenario_dir.glob("*_fcfs_results.csv"))
    rh_files = list(scenario_dir.glob("*_rh_results.csv"))
    if not fcfs_files or not rh_files:
        return None, None

    fcfs = pd.read_csv(fcfs_files[0])
    rh = pd.read_csv(rh_files[0])

    # Filtrar delivered
    fcfs = fcfs[fcfs["status"] == "delivered"].copy()
    rh = rh[rh["status"] == "delivered"].copy()

    # Compute ready_to_door
    for df in [fcfs, rh]:
        for col in ["placement_time", "ready_time", "pickup_time", "delivery_time"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        df["ready_to_door"] = (
            (df["delivery_time"] - df["ready_time"]).dt.total_seconds() / 60.0
        )

    return fcfs, rh


# ──────────────────────────────────────────────────────────────────────
# Fig 1: Box plots de CTD por escenario
# ──────────────────────────────────────────────────────────────────────
def plot_ctd_boxplot(scenarios, out_dir):
    """Box plots de Click-to-Door para FCFS y RH en cada escenario."""
    fig, axes = plt.subplots(1, len(SCENARIO_ORDER), figsize=(14, 5), sharey=True)

    for idx, sn in enumerate(SCENARIO_ORDER):
        ax = axes[idx]
        if sn not in scenarios:
            ax.set_visible(False)
            continue

        # Aggregate all seeds
        fcfs_all, rh_all = [], []
        for seed, sd in scenarios[sn]:
            fcfs, rh = load_order_data(sd)
            if fcfs is not None:
                fcfs_all.append(fcfs["click_to_door"].dropna())
                rh_all.append(rh["click_to_door"].dropna())

        if not fcfs_all:
            continue

        fcfs_vals = pd.concat(fcfs_all)
        rh_vals = pd.concat(rh_all)

        bp = ax.boxplot(
            [fcfs_vals, rh_vals],
            labels=["FCFS", "RH"],
            patch_artist=True,
            widths=0.6,
            showfliers=False,
            medianprops=dict(color="black", linewidth=1.5),
        )
        bp["boxes"][0].set_facecolor(FCFS_COLOR)
        bp["boxes"][0].set_alpha(0.7)
        bp["boxes"][1].set_facecolor(RH_COLOR)
        bp["boxes"][1].set_alpha(0.7)

        ax.set_title(SCENARIO_SHORT[sn], fontsize=10)
        if idx == 0:
            ax.set_ylabel("Click-to-Door (min)")
        ax.axhline(y=40, color="red", linestyle="--", linewidth=0.8, alpha=0.6)

    fig.suptitle("Distribución de Click-to-Door por escenario", fontsize=13, y=1.02)
    plt.tight_layout()

    out_path = out_dir / "fig_ctd_boxplot.pdf"
    fig.savefig(out_path)
    fig.savefig(out_dir / "fig_ctd_boxplot.png")
    plt.close(fig)
    print(f"  Guardado: {out_path}")


# ──────────────────────────────────────────────────────────────────────
# Fig 2: KPIs principales vs ratio de saturación
# ──────────────────────────────────────────────────────────────────────
def plot_kpi_vs_ratio(comparison_df, out_dir):
    """Gráficas de línea: KPIs clave vs ratio de saturación para ambas políticas."""
    # Parse ratio from comparison CSV
    if "Ratio" not in comparison_df.columns:
        print("  Advertencia: columna 'Ratio' no encontrada en comparison CSV")
        return

    # Group by scenario base (average across seeds)
    df = comparison_df.copy()

    # Extract scenario base name for grouping
    df["Scenario_Base"] = df["Scenario"].str.extract(r"(S\d)")
    grouped = df.groupby("Scenario_Base").mean(numeric_only=True).reset_index()
    grouped = grouped.sort_values("Ratio")

    kpis = [
        ("Avg CTD (min)", "Click-to-Door promedio (min)"),
        ("SLA Compliance (%)", "Cumplimiento SLA (%)"),
        ("Utilization (%)", "Utilización courier (%)"),
        ("Cost/Order ($)", "Costo por pedido ($)"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))

    for ax, (kpi, title) in zip(axes.flat, kpis):
        fcfs_col = f"FCFS {kpi}"
        rh_col = f"RH {kpi}"

        if fcfs_col not in grouped.columns or rh_col not in grouped.columns:
            ax.text(0.5, 0.5, f"'{kpi}' no disponible", transform=ax.transAxes,
                    ha="center", va="center")
            continue

        ratios = grouped["Ratio"].values
        ax.plot(ratios, grouped[fcfs_col].values, "o-", color=FCFS_COLOR,
                label="FCFS", linewidth=2, markersize=6)
        ax.plot(ratios, grouped[rh_col].values, "s-", color=RH_COLOR,
                label="RH", linewidth=2, markersize=6)

        ax.set_xlabel("Ratio órdenes/courier ($r$)")
        ax.set_ylabel(title)
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)
        ax.set_xticks(ratios)

    fig.suptitle("KPIs principales vs nivel de saturación", fontsize=13, y=1.01)
    plt.tight_layout()

    out_path = out_dir / "fig_kpi_vs_ratio.pdf"
    fig.savefig(out_path)
    fig.savefig(out_dir / "fig_kpi_vs_ratio.png")
    plt.close(fig)
    print(f"  Guardado: {out_path}")


# ──────────────────────────────────────────────────────────────────────
# Fig 3: Distribución de tamaños de bundle por escenario (solo RH)
# ──────────────────────────────────────────────────────────────────────
def plot_bundle_distribution(scenarios, out_dir):
    """Barras agrupadas: distribución de bundle sizes por escenario (RH only)."""
    fig, ax = plt.subplots(figsize=(10, 5))

    bundle_sizes_range = [1, 2, 3, 4]
    x = np.arange(len(SCENARIO_ORDER))
    width = 0.18
    offsets = np.arange(len(bundle_sizes_range)) - (len(bundle_sizes_range) - 1) / 2

    colors = ["#66BB6A", "#42A5F5", "#FFA726", "#EF5350"]

    for i, bs in enumerate(bundle_sizes_range):
        pcts = []
        for sn in SCENARIO_ORDER:
            if sn not in scenarios:
                pcts.append(0)
                continue
            rh_all = []
            for seed, sd in scenarios[sn]:
                _, rh = load_order_data(sd)
                if rh is not None:
                    rh_all.append(rh)
            if not rh_all:
                pcts.append(0)
                continue
            rh_concat = pd.concat(rh_all)
            n_total = len(rh_concat)
            n_bs = len(rh_concat[rh_concat["bundle_size"] == bs])
            pcts.append(100.0 * n_bs / n_total if n_total > 0 else 0)

        ax.bar(x + offsets[i] * width, pcts, width, label=f"Bundle = {bs}",
               color=colors[i], alpha=0.85, edgecolor="white")

    ax.set_xlabel("Escenario")
    ax.set_ylabel("% de órdenes")
    ax.set_title("Distribución de tamaños de agrupamiento (Rolling Horizon)")
    ax.set_xticks(x)
    ax.set_xticklabels([SCENARIO_SHORT[s] for s in SCENARIO_ORDER])
    ax.legend(title="Tamaño de bundle")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    out_path = out_dir / "fig_bundle_distribution.pdf"
    fig.savefig(out_path)
    fig.savefig(out_dir / "fig_bundle_distribution.png")
    plt.close(fig)
    print(f"  Guardado: {out_path}")


# ──────────────────────────────────────────────────────────────────────
# Fig 4: Utilización vs Costo/Pedido (scatter)
# ──────────────────────────────────────────────────────────────────────
def plot_utilization_cost(comparison_df, out_dir):
    """Scatter: Utilización de courier vs Costo por pedido, por política."""
    fig, ax = plt.subplots(figsize=(8, 5))

    df = comparison_df.copy()

    for policy, color, marker in [("FCFS", FCFS_COLOR, "o"), ("RH", RH_COLOR, "s")]:
        util_col = f"{policy} Utilization (%)"
        cost_col = f"{policy} Cost/Order ($)"
        if util_col not in df.columns or cost_col not in df.columns:
            continue
        ax.scatter(df[util_col], df[cost_col], c=color, marker=marker,
                   s=80, label=policy, alpha=0.8, edgecolors="white", linewidth=0.5)

        # Anotar con scenario label
        for _, row in df.iterrows():
            lbl = row.get("Scenario", "")
            if isinstance(lbl, str):
                short = lbl.split("–")[0].strip() if "–" in lbl else lbl[:2]
            else:
                short = ""
            ax.annotate(short, (row[util_col], row[cost_col]),
                        textcoords="offset points", xytext=(5, 5), fontsize=8)

    ax.set_xlabel("Utilización de courier (%)")
    ax.set_ylabel("Costo por pedido ($)")
    ax.set_title("Trade-off: Utilización vs Costo")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = out_dir / "fig_utilization_cost.pdf"
    fig.savefig(out_path)
    fig.savefig(out_dir / "fig_utilization_cost.png")
    plt.close(fig)
    print(f"  Guardado: {out_path}")


# ──────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generación de gráficas Cap. 4")
    parser.add_argument("--run-dir", default=None, help="Directorio de corrida")
    args = parser.parse_args()

    if args.run_dir:
        run_path = Path(args.run_dir)
    else:
        exp_root = BASE_PATH / "results" / "experiments"
        if not exp_root.exists():
            print("No se encontraron resultados de experimentos.")
            sys.exit(1)
        runs = sorted([d for d in exp_root.iterdir() if d.is_dir()])
        if not runs:
            print("No se encontraron corridas.")
            sys.exit(1)
        run_path = runs[-1]

    print(f"  Directorio de corrida: {run_path}")

    # Descubrir escenarios
    scenarios = discover_scenarios(run_path)
    print(f"  Escenarios encontrados: {list(scenarios.keys())}")

    # Cargar comparison CSV si existe
    comparison_path = run_path / "experiment_comparison.csv"
    comparison_df = None
    if comparison_path.exists():
        comparison_df = pd.read_csv(comparison_path)
        print(f"  Comparison CSV: {len(comparison_df)} filas")

    # Generar gráficas
    print("\n  Generando gráficas...")
    plot_ctd_boxplot(scenarios, run_path)
    plot_bundle_distribution(scenarios, run_path)

    if comparison_df is not None:
        plot_kpi_vs_ratio(comparison_df, run_path)
        plot_utilization_cost(comparison_df, run_path)

    print("\n  Todas las gráficas generadas.")


if __name__ == "__main__":
    main()
