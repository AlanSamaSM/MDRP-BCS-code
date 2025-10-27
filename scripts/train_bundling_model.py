import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import os
import sys
import random
from itertools import combinations
from geopy.distance import geodesic

# Disable Euclidean fallback to ensure OSRM is used
os.environ['USE_EUCLIDEAN_ON_FAILURE'] = '0'

# Add project root to path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.getrouteOSMR import get_route_details

# Load the synthetic data
df = pd.read_csv('C:/Users/alan_/Documents/GitHub/MDRP-BCS-code/data/synthetic_lapaz_orders.csv')

# Convert to datetime
df['created_at'] = pd.to_datetime(df['created_at'])
df['ready_at'] = pd.to_datetime(df['ready_at'])

# Simulate bundle creation and feature engineering
bundles = []
for restaurant_id, orders in df.groupby('restaurant_id'):
    orders = orders.to_dict('records')
    for bundle_size in range(1, 4): # Bundles of size 1, 2, 3
        all_combinations = list(combinations(orders, bundle_size))
        # Limit the number of combinations to avoid performance issues
        max_combinations = 100 
        if len(all_combinations) > max_combinations:
            all_combinations = random.sample(all_combinations, max_combinations)

        for bundle_orders in all_combinations:
            bundle_orders = list(bundle_orders)
            
            # Features
            num_orders = len(bundle_orders)
            
            # Distances
            restaurant_loc = (bundle_orders[0]['rest_lat'], bundle_orders[0]['rest_lon'])
            customer_locs = [(o['dest_lat'], o['dest_lon']) for o in bundle_orders]
            
            distances = [geodesic(restaurant_loc, cl).km for cl in customer_locs]
            avg_restaurant_to_customer_dist = np.mean(distances)
            
            # Times
            # As a proxy for "current_time", we'll use the ready time of the last order in the bundle
            current_time = max([o['ready_at'] for o in bundle_orders])
            max_customer_age = (current_time - min([o['created_at'] for o in bundle_orders])).total_seconds() / 60
            waiting_time_since_ready = (current_time - max([o['ready_at'] for o in bundle_orders])).total_seconds() / 60

            # Estimated travel time from OSRM
            dropoff_points = [{'lat': o['dest_lat'], 'lon': o['dest_lon']} for o in bundle_orders]
            
            # We need a starting point for the courier. We'll use the restaurant location for this simulation.
            route = get_route_details(restaurant_loc, [(o['dest_lat'], o['dest_lon']) for o in bundle_orders])
            
            if route:
                estimated_travel_time = route['duration'] / 60 # in minutes
                
                bundles.append({
                    'num_orders': num_orders,
                    'avg_restaurant_to_customer_dist': avg_restaurant_to_customer_dist,
                    'max_customer_age': max_customer_age,
                    'waiting_time_since_ready': waiting_time_since_ready,
                    'estimated_travel_time': estimated_travel_time,
                    'target': estimated_travel_time # Using travel time as the target for now
                })

bundle_df = pd.DataFrame(bundles)

# Train the model
X = bundle_df[['num_orders', 'avg_restaurant_to_customer_dist', 'max_customer_age', 'waiting_time_since_ready']]
y = bundle_df['target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"Mean Absolute Error: {mae}")

# Save the model
model.save_model("C:/Users/alan_/Documents/GitHub/MDRP-BCS-code/src/bundling_model.xgb")

print("Model trained and saved as bundling_model.xgb")
