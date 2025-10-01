"""Validate dataset loaders and run short simulations.

This script attempts to load data using the three loader modules and runs
short simulations to collect basic metrics per dataset.

It is resilient to missing data files: if a dataset file is unavailable the
script will skip that dataset and report which files were missing.
"""
import json
import os
from datetime import datetime, timedelta

# Ensure project root is on sys.path so `from src...` imports work when running
# this file as a script (same approach used in the loaders themselves).
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.synth_loader import load_synth_instance
from src.grubhub_loader import load_instance as load_grubhub_instance
from src.lade_loader import load_lade_instance
from src.main import run_simulation

# Use Euclidean routing during offline validation to avoid external OSRM calls
# (set before any module that imports getrouteOSMR is loaded).
os.environ.setdefault('USE_EUCLIDEAN', '1')
os.environ.setdefault('METERS_PER_MINUTE', '320')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data')
GRUB_DIR = os.path.join(ROOT, 'mdrplib-master', 'public_instances')

REPORT_PATH = os.path.join(ROOT, 'validation_report.json')


def try_synth():
    csv_path = os.path.join(ROOT, 'data', 'synthetic_lapaz_orders.csv')
    if not os.path.exists(csv_path):
        return {'status': 'missing', 'path': csv_path}

    orders, couriers, restaurants, params = load_synth_instance(csv_path, n_couriers=5)
    # run a short simulation window using the existing run_simulation
    start = min(o.placement_time for o in orders) - timedelta(minutes=15)
    end = start + timedelta(hours=2)
    run_simulation(orders, couriers, restaurants, simulation_end=end, start_time=start)
    metrics = {
        'orders_loaded': len(orders),
        'couriers_loaded': len(couriers),
        'restaurants_loaded': len(restaurants),
    }
    return {'status': 'ok', 'metrics': metrics}


def try_grubhub():
    # find any subdirectory in public_instances
    if not os.path.isdir(GRUB_DIR):
        return {'status': 'missing', 'path': GRUB_DIR}

    subdirs = [os.path.join(GRUB_DIR, d) for d in os.listdir(GRUB_DIR) if os.path.isdir(os.path.join(GRUB_DIR, d))]
    if not subdirs:
        return {'status': 'missing', 'path': GRUB_DIR}

    inst_dir = subdirs[0]
    try:
        orders, couriers, restaurants, params = load_grubhub_instance(inst_dir)
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'path': inst_dir}

    start = min(o.placement_time for o in orders) - timedelta(minutes=15)
    end = start + timedelta(hours=2)
    run_simulation(orders, couriers, restaurants, simulation_end=end, start_time=start)
    metrics = {
        'orders_loaded': len(orders),
        'couriers_loaded': len(couriers),
        'restaurants_loaded': len(restaurants),
        'params': params,
    }
    return {'status': 'ok', 'metrics': metrics}


def try_lade():
    parquet_path = os.path.join(ROOT, 'data', 'delivery_jl.parquet')
    if not os.path.exists(parquet_path):
        return {'status': 'missing', 'path': parquet_path}

    orders, couriers, restaurants, params = load_lade_instance(parquet_path)
    start = min(o.placement_time for o in orders) - timedelta(minutes=15)
    end = start + timedelta(hours=2)
    run_simulation(orders, couriers, restaurants, simulation_end=end, start_time=start)
    metrics = {
        'orders_loaded': len(orders),
        'couriers_loaded': len(couriers),
        'restaurants_loaded': len(restaurants),
    }
    return {'status': 'ok', 'metrics': metrics}


def main():
    report = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'results': {}
    }

    report['results']['synth'] = try_synth()
    report['results']['grubhub'] = try_grubhub()
    report['results']['lade'] = try_lade()

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Wrote validation report to {REPORT_PATH}")


if __name__ == '__main__':
    main()
