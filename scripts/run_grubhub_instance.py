from datetime import timedelta
from src import config
from src.main import run_simulation, Restaurant
from src.grubhub_loader import load_instance
import os

def run_instance(instance_path):
    orders, couriers, restaurants, params = load_instance(instance_path)

    

    # Override configuration parameters with instance values
    config.PAY_PER_ORDER = params.get('pay per order', config.PAY_PER_ORDER)
    config.MIN_PAY_PER_HOUR = params.get('guaranteed pay per hour', config.MIN_PAY_PER_HOUR)
    config.SERVICE_TIME = timedelta(minutes=params.get('pickup service minutes', 4))
    config.TARGET_CLICK_TO_DOOR = timedelta(minutes=params.get('target click-to-door', 40))
    config.MAX_CLICK_TO_DOOR = timedelta(minutes=params.get('maximum click-to-door', 90))

    # Enable OSRM routing by default
    os.environ['USE_EUCLIDEAN'] = '0'

    simulation_start = min(
        min(c.on_time for c in couriers),
        min(o.placement_time for o in orders),
    )
    simulation_end = max(c.off_time for c in couriers) + timedelta(hours=1)
    run_simulation(orders, couriers, restaurants, simulation_end, start_time=simulation_start)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_grubhub_instance.py <instance_path>")
        sys.exit(1)
    run_instance(sys.argv[1])
