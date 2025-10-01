import os
import sys
import pandas as pd
from datetime import timedelta
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import config
from src.main import run_simulation
from src.synth_loader import load_synth_instance
from src.grubhub_loader import load_instance as load_grubhub_instance
from src.lade_loader import load_lade_instance

def calculate_kpis(orders, couriers, simulation_start, simulation_end):
    """Calculates a dictionary of KPIs from the simulation results."""
    
    delivered_orders = [o for o in orders if o.status == 'delivered']
    
    if not delivered_orders:
        return {
            "Dataset": "",
            "Total Orders Delivered": 0,
            "Cost Per Order": 0,
            "Avg. Click-to-Door (min)": 0,
            "Avg. Ready-to-Pickup (min)": 0,
            "Orders per Hour": 0,
            "Avg. Courier Utilization (%)": 0,
            "Couriers on Guaranteed Pay (%)": 0,
        }

    total_orders_delivered = len(delivered_orders)
    total_courier_compensation = sum(c.earnings for c in couriers)
    cost_per_order = total_courier_compensation / total_orders_delivered if total_orders_delivered > 0 else 0
    
    avg_click_to_door = np.mean([o.get_click_to_door() for o in delivered_orders if o.get_click_to_door() is not None])
    avg_ready_to_pickup = np.mean([o.get_ready_to_pickup() for o in delivered_orders if o.get_ready_to_pickup() is not None])
    
    sim_duration_hours = (simulation_end - simulation_start).total_seconds() / 3600
    orders_per_hour = total_orders_delivered / sim_duration_hours if sim_duration_hours > 0 else 0
    
    total_shift_seconds = sum((c.off_time - c.on_time).total_seconds() for c in couriers)
    total_work_seconds = sum(
        route['route']['duration'] for c in couriers for route in c.route_history
    )
    avg_courier_utilization = (total_work_seconds / total_shift_seconds) * 100 if total_shift_seconds > 0 else 0
    
    num_on_guaranteed = sum(1 for c in couriers if c.earnings == c.shift_duration_hours() * config.MIN_PAY_PER_HOUR and c.orders_delivered > 0)
    fraction_on_guaranteed = (num_on_guaranteed / len(couriers)) * 100 if couriers else 0

    return {
        "Dataset": "",
        "Total Orders Delivered": total_orders_delivered,
        "Cost Per Order": f"${cost_per_order:.2f}",
        "Avg. Click-to-Door (min)": f"{avg_click_to_door:.2f}",
        "Avg. Ready-to-Pickup (min)": f"{avg_ready_to_pickup:.2f}",
        "Orders per Hour": f"{orders_per_hour:.2f}",
        "Avg. Courier Utilization (%)": f"{avg_courier_utilization:.2f}",
        "Couriers on Guaranteed Pay (%)": f"{fraction_on_guaranteed:.2f}",
    }

def aggregate_kpis(kpi_list):
    """Aggregates a list of KPI dictionaries."""
    if not kpi_list:
        return {}
    
    agg_kpis = {
        "Dataset": kpi_list[0]["Dataset"],
        "Total Orders Delivered": sum(k["Total Orders Delivered"] for k in kpi_list),
        "Cost Per Order": 0,
        "Avg. Click-to-Door (min)": 0,
        "Avg. Ready-to-Pickup (min)": 0,
        "Orders per Hour": 0,
        "Avg. Courier Utilization (%)": 0,
        "Couriers on Guaranteed Pay (%)": 0,
    }

    total_orders = agg_kpis["Total Orders Delivered"]
    if total_orders > 0:
        # Weighted average for cost and time-based metrics
        agg_kpis["Cost Per Order"] = sum(float(k["Cost Per Order"].strip('$')) * k["Total Orders Delivered"] for k in kpi_list) / total_orders
        agg_kpis["Avg. Click-to-Door (min)"] = sum(float(k["Avg. Click-to-Door (min)"]) * k["Total Orders Delivered"] for k in kpi_list) / total_orders
        agg_kpis["Avg. Ready-to-Pickup (min)"] = sum(float(k["Avg. Ready-to-Pickup (min)"]) * k["Total Orders Delivered"] for k in kpi_list) / total_orders
        
        # Average for rates and percentages
        agg_kpis["Orders per Hour"] = np.mean([float(k["Orders per Hour"]) for k in kpi_list])
        agg_kpis["Avg. Courier Utilization (%)"] = np.mean([float(k["Avg. Courier Utilization (%)"]) for k in kpi_list])
        agg_kpis["Couriers on Guaranteed Pay (%)"] = np.mean([float(k["Couriers on Guaranteed Pay (%)"]) for k in kpi_list])

    # Format strings
    agg_kpis["Cost Per Order"] = f"${agg_kpis['Cost Per Order']:.2f}"
    agg_kpis["Avg. Click-to-Door (min)"] = f"{agg_kpis['Avg. Click-to-Door (min)']:.2f}"
    agg_kpis["Avg. Ready-to-Pickup (min)"] = f"{agg_kpis['Avg. Ready-to-Pickup (min)']:.2f}"
    agg_kpis["Orders per Hour"] = f"{agg_kpis['Orders per Hour']:.2f}"
    agg_kpis["Avg. Courier Utilization (%)"] = f"{agg_kpis['Avg. Courier Utilization (%)']:.2f}"
    agg_kpis["Couriers on Guaranteed Pay (%)"] = f"{agg_kpis['Couriers on Guaranteed Pay (%)']:.2f}"

    return agg_kpis

def main():
    """Runs simulations for all datasets and generates a KPI comparison table."""
    
    # Define paths to data files
    base_path = os.path.dirname(os.path.dirname(__file__))
    synth_path = os.path.join(base_path, "data", "synthetic_lapaz_orders.csv")
    lade_path = os.path.join(base_path, "data", "delivery_jl.parquet")
    # For Grubhub, we pick a representative instance
    grubhub_path = os.path.join(base_path, "mdrplib-master", "public_instances", "0o100t100s1p100")
    
    datasets = {
        "Synthetic": (load_synth_instance, synth_path),
        "LaDe": (load_lade_instance, lade_path),
        "Grubhub": (load_grubhub_instance, grubhub_path),
    }
    
    all_results = []

    for name, (loader_func, path) in datasets.items():
        print(f"--- Running simulation for {name} dataset ---")
        
        if name == "LaDe":
            daily_data = loader_func(path)
            daily_kpis = []
            for i, (orders, couriers, restaurants, _) in enumerate(daily_data):
                print(f"  - Simulating day {i+1}/{len(daily_data)}...")
                if not orders:
                    continue
                
                simulation_start = min(min(c.on_time for c in couriers if c.on_time), min(o.placement_time for o in orders if o.placement_time))
                simulation_end = max(max(c.off_time for c in couriers if c.off_time), max(o.placement_time for o in orders if o.placement_time)) + timedelta(hours=1)

                run_simulation(orders, couriers, restaurants, simulation_end, start_time=simulation_start)
                
                kpis = calculate_kpis(orders, couriers, simulation_start, simulation_end)
                kpis["Dataset"] = name
                daily_kpis.append(kpis)
            
            if daily_kpis:
                agg_kpis = aggregate_kpis(daily_kpis)
                all_results.append(agg_kpis)
        else:
            # Load data
            print(f"Loading data for {name}...")
            orders, couriers, restaurants, _ = loader_func(path)
            print(f"Data loaded for {name}.")
            
            # Determine simulation start and end times
            simulation_start = min(min(c.on_time for c in couriers), min(o.placement_time for o in orders))
            simulation_end = max(c.off_time for c in couriers) + timedelta(hours=1)
            
            # Run simulation
            print(f"Running simulation for {name}...")
            run_simulation(orders, couriers, restaurants, simulation_end, start_time=simulation_start)
            print(f"Simulation finished for {name}.")
            
            # Calculate KPIs
            kpis = calculate_kpis(orders, couriers, simulation_start, simulation_end)
            kpis["Dataset"] = name
            all_results.append(kpis)
        
        print(f"--- Finished {name} ---")

    # Create and display results
    df = pd.DataFrame(all_results)
    df = df.set_index("Dataset")
    
    print("\n\n--- KPI Comparison ---")
    print(df.to_markdown())
    
    # Save to CSV
    results_dir = os.path.join(base_path, "results")
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(results_dir, "kpi_comparison.csv")
    df.to_csv(csv_path)
    
    print(f"\nResults saved to {csv_path}")

if __name__ == "__main__":
    main()
