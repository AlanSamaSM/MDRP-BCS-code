from datetime import timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import config
from src.main import run_simulation, Restaurant
from src.lade_loader import load_lade_instance


def run_instance(parquet_path):
    orders, couriers, restaurants, _ = load_lade_instance(parquet_path)

    

    os.environ.setdefault('USE_EUCLIDEAN', '0')

    simulation_start = min(min(c.on_time for c in couriers), min(o.placement_time for o in orders))
    simulation_end = max(c.off_time for c in couriers) + timedelta(hours=1)

    run_simulation(orders, couriers, restaurants, simulation_end, start_time=simulation_start)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_lade_instance.py <parquet_file>")
        sys.exit(1)
    run_instance(sys.argv[1])
