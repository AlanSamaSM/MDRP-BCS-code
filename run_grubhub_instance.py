from datetime import timedelta
import config
import restaurantsList as rts
from main import run_simulation
from grubhub_loader import load_instance
import os

def run_instance(instance_path):
    orders, couriers, restaurants, params = load_instance(instance_path)

    # Replace global restaurant list with loaded instance restaurants
    rts.restaurantList = restaurants

    # Override configuration parameters with instance values
    config.PAY_PER_ORDER = params.get('pay per order', config.PAY_PER_ORDER)
    config.MIN_PAY_PER_HOUR = params.get('guaranteed pay per hour', config.MIN_PAY_PER_HOUR)
    config.SERVICE_TIME = timedelta(minutes=params.get('pickup service minutes', 4))
    config.TARGET_CLICK_TO_DOOR = timedelta(minutes=params.get('target click-to-door', 40))
    config.MAX_CLICK_TO_DOOR = timedelta(minutes=params.get('maximum click-to-door', 90))

    # Use the Euclidean router with the given speed
    os.environ['USE_EUCLIDEAN'] = '1'
    os.environ['METERS_PER_MINUTE'] = str(params.get('meters_per_minute', 320))

    simulation_start = min(
        min(c.on_time for c in couriers),
        min(o.placement_time for o in orders),
    )
    simulation_end = max(c.off_time for c in couriers) + timedelta(hours=1)
    run_simulation(orders, couriers, simulation_end, start_time=simulation_start)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_grubhub_instance.py <instance_path>")
        sys.exit(1)
    run_instance(sys.argv[1])