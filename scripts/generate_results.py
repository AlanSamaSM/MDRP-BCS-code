import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def calculate_kpis(df, policy_name, total_orders, courier_df):
    """Calcula KPIs completos según Reyes (2018) y métricas adicionales."""
    if df.empty:
        return {
            'Policy': policy_name,
            'Avg. Click-to-Door (min)': 0,
            'P10 Click-to-Door (min)': 0,
            'P50 Click-to-Door (min)': 0,
            'P90 Click-to-Door (min)': 0,
            'P95 Click-to-Door (min)': 0,
            'Avg. Ready-to-Pickup (min)': 0,
            'P10 Ready-to-Pickup (min)': 0,
            'P50 Ready-to-Pickup (min)': 0,
            'P90 Ready-to-Pickup (min)': 0,
            'Avg. Ready-to-Door (min)': 0,
            'P10 Ready-to-Door (min)': 0,
            'P50 Ready-to-Door (min)': 0,
            'P90 Ready-to-Door (min)': 0,
            '% Undelivered Orders': 100,
            'Total Distance (km)': 0,
            'Distance per Order (km)': 0,
            'Orders per Courier per Hour': 0,
            'Bundles per Hour': 0,
            'Avg. Bundle Size': 0,
            '% Orders in Multi-Bundles': 0,
            'Total Courier Compensation': 0,
            'Cost per Order': 0,
            'Fraction of Couriers with Minimum Compensation': 0,
            'Click-to-Door Overage (min)': 0,
            'Courier Utilization (%)': 0,
            'Courier Delivery Earnings': 0,
        }

    # Convert time columns to datetime
    for col in ['placement_time', 'ready_time', 'pickup_time', 'delivery_time']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    delivered_df = df[df['status'] == 'delivered'].copy()

    # Calculate Click-to-Door metrics (percentiles)
    avg_ctd = delivered_df['click_to_door'].mean()
    p10_ctd = delivered_df['click_to_door'].quantile(0.10)
    p50_ctd = delivered_df['click_to_door'].quantile(0.50)
    p90_ctd = delivered_df['click_to_door'].quantile(0.90)
    p95_ctd = delivered_df['click_to_door'].quantile(0.95)
    
    # Calculate Ready-to-Pickup metrics
    avg_rtp = delivered_df['ready_to_pickup'].mean()
    p10_rtp = delivered_df['ready_to_pickup'].quantile(0.10)
    p50_rtp = delivered_df['ready_to_pickup'].quantile(0.50)
    p90_rtp = delivered_df['ready_to_pickup'].quantile(0.90)
    
    # Calculate Ready-to-Door metrics
    delivered_df['ready_to_door'] = (delivered_df['delivery_time'] - delivered_df['ready_time']).dt.total_seconds() / 60
    avg_rtd = delivered_df['ready_to_door'].mean()
    p10_rtd = delivered_df['ready_to_door'].quantile(0.10)
    p50_rtd = delivered_df['ready_to_door'].quantile(0.50)
    p90_rtd = delivered_df['ready_to_door'].quantile(0.90)
    
    undelivered_orders = total_orders - len(delivered_df)
    undelivered_orders_percentage = (undelivered_orders / total_orders) * 100 if total_orders > 0 else 0

    avg_bundle_size = delivered_df['bundle_size'].mean()

    # Calculate metrics from courier data
    total_distance = courier_df['total_distance_km'].sum()
    total_hours = courier_df['shift_duration_hours'].sum()
    total_delivered_orders = courier_df['orders_delivered'].sum()
    total_bundles = courier_df['bundles_picked_up'].sum()
    total_driving_time_hours = courier_df['driving_time_minutes'].sum() / 60.0
    
    if total_hours > 0:
        orders_per_courier_hour = total_delivered_orders / total_hours
        bundles_per_hour = total_bundles / total_hours
        courier_utilization = (total_driving_time_hours / total_hours) * 100
    else:
        orders_per_courier_hour = 0
        bundles_per_hour = 0
        courier_utilization = 0

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
    
    total_delivery_earnings = courier_df['delivery_earnings'].sum()

    # Nuevas métricas solicitadas
    distance_per_order = total_distance / total_delivered_orders if total_delivered_orders > 0 else 0
    
    multi_bundle_orders = delivered_df[delivered_df['bundle_size'] > 1]
    percentage_multi_bundle = (len(multi_bundle_orders) / len(delivered_df)) * 100 if len(delivered_df) > 0 else 0

    return {
        'Policy': policy_name,
        'Avg. Click-to-Door (min)': f'{avg_ctd:.2f}',
        'P10 Click-to-Door (min)': f'{p10_ctd:.2f}',
        'P50 Click-to-Door (min)': f'{p50_ctd:.2f}',
        'P90 Click-to-Door (min)': f'{p90_ctd:.2f}',
        'P95 Click-to-Door (min)': f'{p95_ctd:.2f}',
        'Avg. Ready-to-Pickup (min)': f'{avg_rtp:.2f}',
        'P10 Ready-to-Pickup (min)': f'{p10_rtp:.2f}',
        'P50 Ready-to-Pickup (min)': f'{p50_rtp:.2f}',
        'P90 Ready-to-Pickup (min)': f'{p90_rtp:.2f}',
        'Avg. Ready-to-Door (min)': f'{avg_rtd:.2f}',
        'P10 Ready-to-Door (min)': f'{p10_rtd:.2f}',
        'P50 Ready-to-Door (min)': f'{p50_rtd:.2f}',
        'P90 Ready-to-Door (min)': f'{p90_rtd:.2f}',
        '% Undelivered Orders': f'{undelivered_orders_percentage:.2f}',
        'Total Distance (km)': f'{total_distance:.2f}',
        'Distance per Order (km)': f'{distance_per_order:.2f}',
        'Orders per Courier per Hour': f'{orders_per_courier_hour:.2f}',
        'Bundles per Hour': f'{bundles_per_hour:.2f}',
        'Avg. Bundle Size': f'{avg_bundle_size:.2f}',
        '% Orders in Multi-Bundles': f'{percentage_multi_bundle:.2f}',
        'Total Courier Compensation': f'{total_compensation:.2f}',
        'Cost per Order': f'{cost_per_order:.2f}',
        'Fraction of Couriers with Minimum Compensation': f'{fraction_min_comp:.2f}',
        'Click-to-Door Overage (min)': f'{avg_ctd_overage:.2f}',
        'Courier Utilization (%)': f'{courier_utilization:.2f}',
        'Courier Delivery Earnings': f'{total_delivery_earnings:.2f}',
    }

def run_full_pipeline(synthetic_csv_path='data/synthetic_lapaz_orders_limited.csv', skip_data_generation=False):
    """
    Orquestador completo del pipeline de experimentación:
    1. Genera datos sintéticos (opcional)
    2. Ejecuta simulación FCFS
    3. Ejecuta simulación Rolling Horizon
    4. Calcula y compara KPIs
    """
    base_path = os.path.dirname(os.path.dirname(__file__))
    
    print("="*60)
    print("PIPELINE DE EXPERIMENTACIÓN MDRP-BCS")
    print("="*60)
    
    # Paso 1: Generar datos sintéticos
    if not skip_data_generation:
        print("\n[1/4] Generando datos sintéticos...")
        import subprocess
        synth_script = os.path.join(base_path, 'scripts', 'make_synth_orders.py')
        result = subprocess.run([sys.executable, synth_script], cwd=base_path, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Datos sintéticos generados: {result.stdout.strip()}")
        else:
            print(f"✗ Error generando datos: {result.stderr}")
            return
    else:
        print(f"\n[1/4] Saltando generación de datos (usando: {synthetic_csv_path})")
    
    # Paso 2: Ejecutar FCFS
    print("\n[2/4] Ejecutando simulación FCFS...")
    fcfs_script = os.path.join(base_path, 'scripts', 'run_fcfs_instance.py')
    result = subprocess.run([sys.executable, fcfs_script, synthetic_csv_path], cwd=base_path, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Simulación FCFS completada")
    else:
        print(f"✗ Error en simulación FCFS: {result.stderr}")
        return
    
    # Paso 3: Ejecutar Rolling Horizon
    print("\n[3/4] Ejecutando simulación Rolling Horizon...")
    rh_script = os.path.join(base_path, 'scripts', 'run_synth_instance.py')
    # No capturar output para ver los prints en tiempo real
    result = subprocess.run([sys.executable, rh_script, synthetic_csv_path], cwd=base_path)
    if result.returncode == 0:
        print("✓ Simulación Rolling Horizon completada")
    else:
        print(f"✗ Error en simulación RH (returncode: {result.returncode})")
        return
    
    # Paso 4: Calcular y comparar KPIs
    print("\n[4/4] Calculando KPIs y generando comparación...")
    analyze_results()
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETADO")
    print("="*60)

def analyze_results():
    """Analiza los resultados de las simulaciones y genera comparación de KPIs."""
    base_path = os.path.dirname(os.path.dirname(__file__))
    raw_results_path = os.path.join(base_path, 'results', 'raw')

    # Define paths for order results
    fcfs_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_limited_fcfs_results.csv')
    rh_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_limited_rh_results.csv')

    # Define paths for courier summaries
    fcfs_courier_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_limited_fcfs_couriers.csv')
    rh_courier_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_limited_rh_couriers.csv')

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
            fcfs_val = fcfs_metrics[key]
            rh_val = rh_metrics[key]
            
            # Handle negative values (invalid timestamps or data quality issues)
            if fcfs_val < 0 or rh_val < 0:
                improvement[key] = 'INVALID'
            # Both values are zero - no improvement but both optimal
            elif fcfs_val == 0 and rh_val == 0:
                improvement[key] = '✓ Both 0%'
            # Only FCFS is zero - show absolute difference instead of percentage
            elif fcfs_val == 0 and rh_val > 0:
                improvement[key] = f'Δ={rh_val:.2f}'
            # Normal case - calculate percentage improvement
            elif fcfs_val > 0:
                imp = ((rh_val - fcfs_val) / fcfs_val) * 100
                improvement[key] = f'{imp:.2f}%'
            # Fallback for edge cases
            else:
                improvement[key] = 'N/A'
    improvement['Policy'] = 'Improvement (%)'
    
    # Transpose for the final table format
    comparison_df = comparison_df.T
    comparison_df['Improvement (%)'] = pd.Series(improvement)

    print("\n--- KPI Comparison ---")
    print(comparison_df.to_markdown())

    # Save to CSV
    results_dir = os.path.join(base_path, "results")
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(results_dir, "kpi_comparison.csv")
    comparison_df.to_csv(csv_path)
    

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Execute full MDRP experimentation pipeline or analyze existing results')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze existing results without running simulations')
    parser.add_argument('--csv', default='data/synthetic_lapaz_orders_limited.csv', help='Path to synthetic orders CSV')
    args = parser.parse_args()
    
    if args.analyze_only:
        print("Analyzing existing results...")
        analyze_results()
    else:
        run_full_pipeline(synthetic_csv_path=args.csv)
