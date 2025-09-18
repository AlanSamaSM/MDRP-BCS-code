import os
import pandas as pd
from datetime import datetime, timedelta
from restaurantsList import Restaurant
from main import Order, Courier
from coord_transform import xy_to_latlon

START_TIME = datetime(2025, 1, 1)

def load_instance(path):
    """Load a Grubhub benchmark instance from ``path``.

    Returns a tuple ``(orders, couriers, restaurants, params)``.
    """
    orders_df = pd.read_table(os.path.join(path, 'orders.txt'))
    rest_df = pd.read_table(os.path.join(path, 'restaurants.txt'))
    cour_df = pd.read_table(os.path.join(path, 'couriers.txt'))
    params_df = pd.read_table(os.path.join(path, 'instance_parameters.txt'))

    restaurants = []
    rest_map = {}
    for _, row in rest_df.iterrows():
        r = Restaurant(row['restaurant'], xy_to_latlon(row['x'], row['y']))
        restaurants.append(r)
        rest_map[row['restaurant']] = r

    orders = []
    for _, row in orders_df.iterrows():
        orders.append(
            Order(
                row['order'],
                rest_map[row['restaurant']],
                START_TIME + timedelta(minutes=int(row['placement_time'])),
                START_TIME + timedelta(minutes=int(row['ready_time'])),
                xy_to_latlon(row['x'], row['y'])
            )
        )

    couriers = []
    for _, row in cour_df.iterrows():
        couriers.append(
            Courier(
                row['courier'],
                START_TIME + timedelta(minutes=int(row['on_time'])),
                START_TIME + timedelta(minutes=int(row['off_time'])),
                xy_to_latlon(row['x'], row['y'])
            )
        )

    params = params_df.iloc[0].to_dict()
    return orders, couriers, restaurants, params
