import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def calculate_kpis(df, policy_name, total_orders, courier_df):
    if df.empty:
        return {
            'Policy': policy_name,
            'Avg. Click-to-Door (min)': 0,
            'P95 Click-to-Door (min)': 0,
            'Avg. Ready-to-Pickup (min)': 0,
            '% Undelivered Orders': 100,
            'Total Distance (km)': 0,
            'Orders per Courier per Hour': 0,
            'Avg. Bundle Size': 0,
            'Total Courier Compensation': 0,
            'Cost per Order': 0,
            'Fraction of Couriers with Minimum Compensation': 0,
            'Click-to-Door Overage': 0,
            'Ready-to-Door Time': 0,
            'Courier Utilization': 0,
            'Courier Delivery Earnings': 0,
            'Bundles picked up per Hour': 0,
        }

    # Convert time columns to datetime
    for col in ['placement_time', 'ready_time', 'pickup_time', 'delivery_time']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    delivered_df = df[df['status'] == 'delivered'].copy()

    # Calculate metrics
    avg_ctd = delivered_df['click_to_door'].mean()
    p95_ctd = delivered_df['click_to_door'].quantile(0.95)
    avg_rtp = delivered_df['ready_to_pickup'].mean()
    
    undelivered_orders = total_orders - len(delivered_df)
    undelivered_orders_percentage = (undelivered_orders / total_orders) * 100 if total_orders > 0 else 0

    avg_bundle_size = delivered_df['bundle_size'].mean()

    # Calculate metrics from courier data
    total_distance = courier_df['total_distance_km'].sum()
    total_hours = courier_df['shift_duration_hours'].sum()
    total_delivered_orders = courier_df['orders_delivered'].sum()
    
    if total_hours > 0:
        orders_per_courier_hour = total_delivered_orders / total_hours
    else:
        orders_per_courier_hour = 0

    # New metrics from reyes2018.txt
    PAY_PER_ORDER = 10
    MIN_PAY_PER_HOUR = 15
    TARGET_CLICK_TO_DOOR = 40

    courier_df['delivery_earnings'] = courier_df['orders_delivered'] * PAY_PER_ORDER
    courier_df['minimum_earnings'] = courier_df['shift_duration_hours'] * MIN_PAY_PER_HOUR
    courier_df['compensation'] = courier_df[['delivery_earnings', 'minimum_earnings']].max(axis=1)
    
    total_compensation = courier_df['compensation'].sum()
    cost_per_order = total_compensation / total_delivered_orders if total_delivered_orders > 0 else 0
    
    min_comp_couriers = courier_df[courier_df['compensation'] == courier_df['minimum_earnings']]
    fraction_min_comp = len(min_comp_couriers) / len(courier_df) if len(courier_df) > 0 else 0
    
    delivered_df['click_to_door_overage'] = (delivered_df['click_to_door'] - TARGET_CLICK_TO_DOOR).clip(lower=0)
    avg_ctd_overage = delivered_df['click_to_door_overage'].mean()
    
    delivered_df['ready_to_door'] = (delivered_df['delivery_time'] - delivered_df['ready_time']).dt.total_seconds() / 60
    avg_rtd = delivered_df['ready_to_door'].mean()
    
    # Courier utilization is not directly available, so we need to estimate it.
    # For now, we'll use a placeholder value.
    courier_utilization = 0 

    total_delivery_earnings = courier_df['delivery_earnings'].sum()
    
    # Bundles picked up per hour requires information not present in the current dataframes.
    # We will use a placeholder for now.
    bundles_per_hour = 0

    return {
        'Policy': policy_name,
        'Avg. Click-to-Door (min)': f'{avg_ctd:.2f}',
        'P95 Click-to-Door (min)': f'{p95_ctd:.2f}',
        'Avg. Ready-to-Pickup (min)': f'{avg_rtp:.2f}',
        '% Undelivered Orders': f'{undelivered_orders_percentage:.2f}',
        'Total Distance (km)': f'{total_distance:.2f}',
        'Orders per Courier per Hour': f'{orders_per_courier_hour:.2f}',
        'Avg. Bundle Size': f'{avg_bundle_size:.2f}',
        'Total Courier Compensation': f'{total_compensation:.2f}',
        'Cost per Order': f'{cost_per_order:.2f}',
        'Fraction of Couriers with Minimum Compensation': f'{fraction_min_comp:.2f}',
        'Click-to-Door Overage': f'{avg_ctd_overage:.2f}',
        'Ready-to-Door Time': f'{avg_rtd:.2f}',
        'Courier Utilization': f'{courier_utilization:.2f}',
        'Courier Delivery Earnings': f'{total_delivery_earnings:.2f}',
        'Bundles picked up per Hour': f'{bundles_per_hour:.2f}',
    }

def main():
    base_path = os.path.dirname(os.path.dirname(__file__))
    raw_results_path = os.path.join(base_path, 'results', 'raw')

    # Define paths for order results
    fcfs_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_fcfs_results.csv')
    rh_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_rh_results.csv')

    # Define paths for courier summaries
    fcfs_courier_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_fcfs_couriers.csv')
    rh_courier_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_rh_couriers.csv')

    # Load dataframes
    fcfs_df = pd.read_csv(fcfs_path)
    rh_df = pd.read_csv(rh_path)
    fcfs_courier_df = pd.read_csv(fcfs_courier_path)
    rh_courier_df = pd.read_csv(rh_courier_path)

    total_orders = len(fcfs_df) # Assuming both policies run on the same set of orders

    fcfs_kpis = calculate_kpis(fcfs_df, 'FCFS', total_orders, fcfs_courier_df)
    rh_kpis = calculate_kpis(rh_df, 'Rolling Horizon', total_orders, rh_courier_df)

    comparison_df = pd.DataFrame([fcfs_kpis, rh_kpis])
    comparison_df = comparison_df.set_index('Policy')

    # Calculate improvement
    rh_metrics = rh_kpis.copy()
    fcfs_metrics = fcfs_kpis.copy()
    
    # Convert to numeric for calculation
    for k in rh_metrics:
        if k != 'Policy':
            rh_metrics[k] = float(rh_metrics[k])
            fcfs_metrics[k] = float(fcfs_metrics[k])

    improvement = {}
    for key in rh_metrics:
        if key != 'Policy':
            if fcfs_metrics[key] > 0:
                imp = ((rh_metrics[key] - fcfs_metrics[key]) / fcfs_metrics[key]) * 100
                improvement[key] = f'{imp:.2f}%'
            else:
                improvement[key] = 'N/A'
    improvement['Policy'] = 'Improvement (%)'
    
    # Transpose for the final table format
    comparison_df = comparison_df.T
    comparison_df['Improvement (%)'] = pd.Series(improvement)

    print("--- KPI Comparison ---")
    print(comparison_df.to_markdown())

    # Save to CSV
    results_dir = os.path.join(base_path, "results")
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(results_dir, "kpi_comparison.csv")
    comparison_df.to_csv(csv_path)
    
    print(f"\nResults saved to {csv_path}")

if __name__ == "__main__":
    main()
