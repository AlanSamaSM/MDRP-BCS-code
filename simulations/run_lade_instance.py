from datetime import timedelta
import os
import restaurantsList as rts
from main import run_simulation
from lade_loader import load_lade_instance


def run_instance(parquet_path):
    orders, couriers, restaurants, _ = load_lade_instance(parquet_path)

    rts.restaurantList = restaurants

    os.environ.setdefault('USE_EUCLIDEAN', '0')

    simulation_start = min(min(c.on_time for c in couriers), min(o.placement_time for o in orders))
    simulation_end = max(c.off_time for c in couriers) + timedelta(hours=1)

    run_simulation(orders, couriers, simulation_end, start_time=simulation_start)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_lade_instance.py <parquet_file>")
        sys.exit(1)
    run_instance(sys.argv[1])
