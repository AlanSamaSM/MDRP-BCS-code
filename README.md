# MDRP-BCS Code

This repository contains a basic simulator and heuristics for courier
assignment.  Two loaders are provided:

- **Grubhub benchmark** via `grubhub_loader.py`
- **LaDe (Jilin subset)** via `lade_loader.py`

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
time.

## Metrics for Route Prediction

`lade_metrics.py` implements the performance metrics described in the
LaDe paper: Kendall Rank Correlation, Edit Distance, Location Square
Deviation and Hit Rate@k.  These helpers can be used to evaluate routing
predictions.
