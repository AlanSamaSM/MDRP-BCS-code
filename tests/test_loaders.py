import os
import pytest
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def test_synth_loader_imports():
    try:
        from src.synth_loader import load_synth_instance
    except Exception as e:
        pytest.skip(f"Cannot import synth_loader: {e}")

    csv_path = os.path.join(ROOT, 'data', 'synthetic_lapaz_orders.csv')
    if not os.path.exists(csv_path):
        pytest.skip("Synthetic CSV not present")

    orders, couriers, restaurants, params = load_synth_instance(csv_path, n_couriers=2)
    assert isinstance(orders, list)
    assert isinstance(couriers, list)
    assert isinstance(restaurants, list)


def test_grubhub_loader_imports():
    try:
        from src.grubhub_loader import load_instance
    except Exception as e:
        pytest.skip(f"Cannot import grubhub_loader: {e}")

    inst_root = os.path.join(ROOT, 'mdrplib-master', 'public_instances')
    if not os.path.isdir(inst_root):
        pytest.skip("Grubhub public_instances not present")

    # pick one subdir
    subdirs = [d for d in os.listdir(inst_root) if os.path.isdir(os.path.join(inst_root, d))]
    if not subdirs:
        pytest.skip("No grubhub instance directories")

    orders, couriers, restaurants, params = load_instance(os.path.join(inst_root, subdirs[0]))
    assert isinstance(orders, list)
    assert isinstance(couriers, list)
    assert isinstance(restaurants, list)


def test_lade_loader_imports():
    try:
        from src.lade_loader import load_lade_instance
    except Exception as e:
        pytest.skip(f"Cannot import lade_loader: {e}")

    parquet_path = os.path.join(ROOT, 'data', 'delivery_jl.parquet')
    if not os.path.exists(parquet_path):
        pytest.skip("LaDe parquet not present")

    orders, couriers, restaurants, params = load_lade_instance(parquet_path)
    assert isinstance(orders, list)
    assert isinstance(couriers, list)
    assert isinstance(restaurants, list)
