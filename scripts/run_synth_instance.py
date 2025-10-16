import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import config
from src.main import run_simulation, Restaurant
from src.synth_loader import load_synth_instance


def run_instance(csv_path):
    orders, couriers, restaurants, _ = load_synth_instance(csv_path)

    

    os.environ['USE_EUCLIDEAN'] = '0'

    simulation_start = min(
        min(c.on_time for c in couriers),
        min(o.placement_time for o in orders),
    )
    simulation_end = max(c.off_time for c in couriers) + timedelta(hours=1)

    results_dir = os.path.join(os.path.dirname(__file__), '..\\', 'results', 'raw')
    os.makedirs(results_dir, exist_ok=True)
    base_filename = os.path.basename(csv_path).replace('.csv', '')
    results_path = os.path.join(results_dir, f'{base_filename}_rh_results.csv')
    courier_results_path = os.path.join(results_dir, f'{base_filename}_rh_couriers.csv')

    run_simulation(orders, couriers, restaurants, simulation_end, start_time=simulation_start, results_path=results_path, courier_results_path=courier_results_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_synth_instance.py <orders.csv>")
        sys.exit(1)
    run_instance(sys.argv[1])
