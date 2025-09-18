# MDRP-BCS Code

This repository contains a basic simulator and heuristics for courier
assignment.  Three loaders are provided:

- **Grubhub benchmark** via `grubhub_loader.py`
- **LaDe (Jilin subset)** via `lade_loader.py`
- **Synthetic La Paz** via `synth_loader.py`

## Running with LaDe

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Execute the simulation

```bash
python run_lade_instance.py delivery_jl.parquet
```

The loader approximates each depot using the courier GPS when the order
was accepted.  Acceptance time is treated as both placement and ready
time.  The ``ds`` column stores the month and day for each order, which
the loader merges with the ``accept_time`` and ``delivery_time`` strings
to build full datetimes.

## Running the Synthetic Example

1. Generate or obtain ``synthetic_lapaz_orders.csv`` using
   ``make_synth_orders.py``.

2. Execute the simulation:

```bash
python run_synth_instance.py synthetic_lapaz_orders.csv
```

If the online OSRM service is slow or unreachable, set `USE_EUCLIDEAN=1`
to compute straight‑line distances instead of requesting routes:

```bash
USE_EUCLIDEAN=1 python run_synth_instance.py synthetic_lapaz_orders.csv
``` v

## Metrics for Route Prediction

`lade_metrics.py` implements the performance metrics described in the
LaDe paper: Kendall Rank Correlation, Edit Distance, Location Square
Deviation and Hit Rate@k.  These helpers can be used to evaluate routing
predictions.
