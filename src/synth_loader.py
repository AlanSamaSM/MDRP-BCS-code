import math
import pandas as pd
from datetime import timedelta
import os
import sys

# Handle both package and direct script imports
try:
    from src.main import Order, Courier, Restaurant
    from src.config import TARGET_ORDERS_PER_COURIER
except ImportError:
    # Add project root to path when running directly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)
    from src.main import Order, Courier, Restaurant
    from src.config import TARGET_ORDERS_PER_COURIER


def load_synth_instance(
    csv_path,
    n_couriers=None,
    orders_per_courier=None,
    min_couriers=15,
):
    """Load the synthetic La Paz orders CSV.

    The file is produced by ``make_synth_orders.py`` and contains restaurant
    and dropoff coordinates as well as order timestamps.  Since the dataset
    does not include couriers, a small fleet is generated automatically.
    """
    print(f"  [synth_loader] Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=["created_at", "ready_at"])
    print(f"  [synth_loader] Loaded {len(df)} orders from CSV")

    if orders_per_courier is None:
        orders_per_courier = TARGET_ORDERS_PER_COURIER

    if n_couriers is None:
        if orders_per_courier <= 0:
            raise ValueError("orders_per_courier must be positive when computing fleet size")
        computed = math.ceil(len(df) / orders_per_courier) if len(df) else min_couriers
        n_couriers = max(min_couriers, computed)
        print(
            f"  [synth_loader] Auto-selected {n_couriers} couriers "
            f"(~{orders_per_courier} orders/courier)"
        )

    restaurants = []
    rest_map = {}
    for rest_id, grp in df.groupby("restaurant_id"):
        lat = grp["rest_lat"].iloc[0]
        lon = grp["rest_lon"].iloc[0]
        r = Restaurant(int(rest_id), (lat, lon))
        restaurants.append(r)
        rest_map[rest_id] = r
    
    print(f"  [synth_loader] Created {len(restaurants)} restaurants")

    orders = []
    for _, row in df.iterrows():
        orders.append(
            Order(
                int(row["order_id"]),
                rest_map[row["restaurant_id"]],
                row["created_at"],
                row["ready_at"],
                (row["dest_lat"], row["dest_lon"]),
            )
        )
    
    print(f"  [synth_loader] Created {len(orders)} order objects")

    start = df["created_at"].min() - timedelta(minutes=15)
    end = df["ready_at"].max() + timedelta(hours=1)
    depot = (df["rest_lat"].mean(), df["rest_lon"].mean())

    couriers = [
        Courier(i + 1, start, end, depot)
        for i in range(n_couriers)
    ]
    
    print(f"  [synth_loader] Created {n_couriers} couriers")
    print(f"  [synth_loader] Courier shift: {start} to {end}")

    params = {}
    return orders, couriers, restaurants, params

if __name__ == "__main__":
    # Find the synthetic orders CSV in the data directory
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "data", "synthetic_lapaz_orders.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: Could not find data file at {csv_path}")
        sys.exit(1)
        
    # Load the synthetic instance
    orders, couriers, restaurants, _ = load_synth_instance(csv_path)
    
    # Print summary statistics
    print(f"Loaded {len(orders)} orders")
    print(f"Created {len(couriers)} couriers")
    print(f"Found {len(restaurants)} restaurants")
    
    # Show sample data
    print("\nFirst 3 orders (sample):")
    for o in orders[:3]:
        print(f"  id={o.id}, restaurant={o.restaurant.id}, "
              f"placement={o.placement_time}, ready={o.ready_time}")
    
    if couriers:
        c = couriers[0]
        print("\nSample courier:")
        print(f"  id={c.id}, on_time={c.on_time}, "
              f"off_time={c.off_time}, location={c.location}")
