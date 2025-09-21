import pandas as pd
from datetime import timedelta

from src.main import Order, Courier, Restaurant


def load_synth_instance(csv_path, n_couriers=5):
    """Load the synthetic La Paz orders CSV.

    The file is produced by ``make_synth_orders.py`` and contains restaurant
    and dropoff coordinates as well as order timestamps.  Since the dataset
    does not include couriers, a small fleet is generated automatically.
    """
    df = pd.read_csv(csv_path, parse_dates=["created_at", "ready_at"])

    restaurants = []
    rest_map = {}
    for rest_id, grp in df.groupby("restaurant_id"):
        lat = grp["rest_lat"].iloc[0]
        lon = grp["rest_lon"].iloc[0]
        r = Restaurant(int(rest_id), (lat, lon))
        restaurants.append(r)
        rest_map[rest_id] = r

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

    start = df["created_at"].min() - timedelta(minutes=15)
    end = df["ready_at"].max() + timedelta(hours=1)
    depot = (df["rest_lat"].mean(), df["rest_lon"].mean())

    couriers = [
        Courier(i + 1, start, end, depot)
        for i in range(n_couriers)
    ]

    params = {}
    return orders, couriers, restaurants, params
