import pandas as pd

from restaurantsList import Restaurant
from main import Order, Courier

def load_lade_instance(parquet_path):
    """Load a LaDe delivery parquet file.

    Because the public dataset only records acceptance and delivery
    events, we approximate restaurant locations using the courier's
    GPS position when accepting the order. ``accept_time`` is used as
    both placement_time and ready_time.
    """
    df = pd.read_parquet(parquet_path)

    # parse timestamps using ds (month/day) combined with time fields
    ds_str = df['ds'].astype(int).astype(str).str.zfill(4)
    accept_time_str = df['accept_time'].astype(str).str.extract(r'(\d{2}:\d{2}:\d{2})')[0]
    delivery_time_str = df['delivery_time'].astype(str).str.extract(r'(\d{2}:\d{2}:\d{2})')[0]

    df['accept_time'] = pd.to_datetime(
        ds_str + ' ' + accept_time_str, format='%m%d %H:%M:%S'
    ).apply(lambda d: d.replace(year=2025))
    df['delivery_time'] = pd.to_datetime(
        ds_str + ' ' + delivery_time_str, format='%m%d %H:%M:%S'
    ).apply(lambda d: d.replace(year=2025))

    restaurants = []
    rest_map = {}
    for region, grp in df.groupby('region_id'):
        # Pick first available accept GPS as the depot/restaurant location
        row = grp.dropna(subset=['accept_gps_lat', 'accept_gps_lng']).head(1)
        if len(row) == 0:
            lat = grp['lat'].iloc[0]
            lng = grp['lng'].iloc[0]
        else:
            lat = row['accept_gps_lat'].iloc[0]
            lng = row['accept_gps_lng'].iloc[0]
        r = Restaurant(int(region), (lat, lng))
        restaurants.append(r)
        rest_map[region] = r

    orders = []
    for _, row in df.iterrows():
        rest = rest_map[row['region_id']]
        placement_time = row['accept_time']
        ready_time = placement_time
        drop_loc = (row['lat'], row['lng'])
        orders.append(Order(int(row['order_id']), rest, placement_time, ready_time, drop_loc))

    couriers = []
    for cid, grp in df.groupby('courier_id'):
        on_time = grp['accept_time'].min()
        off_time = grp['delivery_time'].max()
        # start location as first accept GPS or first dropoff if missing
        row = grp.dropna(subset=['accept_gps_lat', 'accept_gps_lng']).head(1)
        if len(row) == 0:
            lat = grp['lat'].iloc[0]
            lng = grp['lng'].iloc[0]
        else:
            lat = row['accept_gps_lat'].iloc[0]
            lng = row['accept_gps_lng'].iloc[0]
        couriers.append(Courier(int(cid), on_time, off_time, (lat, lng)))

    params = {}
    return orders, couriers, restaurants, params
