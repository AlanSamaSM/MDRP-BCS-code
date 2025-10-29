import argparse
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import config
from src.main import run_simulation, Restaurant
from src.synth_loader import load_synth_instance


def run_instance(csv_path, orders_per_courier=None, min_couriers=25):
    if orders_per_courier is None:
        orders_per_courier = config.TARGET_ORDERS_PER_COURIER

    print(f"Loading instance from {csv_path}...")
    orders, couriers, restaurants, _ = load_synth_instance(
        csv_path,
        n_couriers=None,
        orders_per_courier=orders_per_courier,
        min_couriers=min_couriers,
    )
    print(f"Loaded: {len(orders)} orders, {len(couriers)} couriers, {len(restaurants)} restaurants")

    os.environ['USE_EUCLIDEAN'] = '0'

    simulation_start = min(
        min(c.on_time for c in couriers),
        min(o.placement_time for o in orders),
    )
    simulation_end = max(c.off_time for c in couriers) + timedelta(hours=1)
    
    print(f"Simulation window: {simulation_start} to {simulation_end}")

    results_dir = os.path.join(os.path.dirname(__file__), '..\\', 'results', 'raw')
    os.makedirs(results_dir, exist_ok=True)
    base_filename = os.path.basename(csv_path).replace('.csv', '')
    results_path = os.path.join(results_dir, f'{base_filename}_rh_results.csv')
    courier_results_path = os.path.join(results_dir, f'{base_filename}_rh_couriers.csv')
    
    print(f"Starting Rolling Horizon simulation...")

    run_simulation(orders, couriers, restaurants, simulation_end, start_time=simulation_start, results_path=results_path, courier_results_path=courier_results_path)
    
    print(f"Simulation complete. Results saved to {results_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Rolling Horizon simulation on synthetic data")
    parser.add_argument("csv_path", help="Path to the synthetic orders CSV")
    parser.add_argument(
        "--orders-per-courier",
        type=float,
        default=None,
        help="Target number of orders per courier shift (defaults to config.TARGET_ORDERS_PER_COURIER)",
    )
    parser.add_argument(
        "--min-couriers",
        type=int,
        default=25,
        help="Minimum fleet size to instantiate",
    )
    args = parser.parse_args()

    run_instance(
        args.csv_path,
        orders_per_courier=args.orders_per_courier,
        min_couriers=args.min_couriers,
    )
