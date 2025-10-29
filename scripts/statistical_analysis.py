import os
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import proportions_ztest
import pingouin as pg

def run_statistical_analysis(fcfs_results_path, rh_results_path):
    """
    Compara los resultados de dos políticas (FCFS y RH) usando pruebas estadísticas.
    - Test de Mann-Whitney U para distribuciones de tiempos (CTD, RTP, RTD).
    - Test de proporciones Z para comparar el porcentaje de órdenes en bundles.
    - Calcula el tamaño del efecto (Cliff's Delta) para las métricas de tiempo.
    """
    print("="*60)
    print("ANÁLISIS ESTADÍSTICO DE RESULTADOS")
    print("="*60)

    # Cargar datos
    try:
        fcfs_df = pd.read_csv(fcfs_results_path)
        rh_df = pd.read_csv(rh_results_path)
        print(f"✓ Datos cargados: {os.path.basename(fcfs_results_path)}, {os.path.basename(rh_results_path)}")
    except FileNotFoundError as e:
        print(f"✗ Error: No se encontró el archivo de resultados: {e.filename}")
        return

    # Filtrar solo órdenes entregadas para el análisis
    fcfs_delivered = fcfs_df[fcfs_df['status'] == 'delivered'].copy()
    rh_delivered = rh_df[rh_df['status'] == 'delivered'].copy()

    if fcfs_delivered.empty or rh_delivered.empty:
        print("✗ No hay suficientes datos de órdenes entregadas para realizar el análisis.")
        return

    # Calcular métricas que no están en el CSV crudo
    for df in [fcfs_delivered, rh_delivered]:
        for col in ['placement_time', 'ready_time', 'pickup_time', 'delivery_time']:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        df['ready_to_door'] = (df['delivery_time'] - df['ready_time']).dt.total_seconds() / 60

    print("\n--- 1. Comparación de Métricas de Tiempo (Mann-Whitney U) ---")
    
    metrics_to_test = {
        'click_to_door': 'Click-to-Door Time',
        'ready_to_pickup': 'Ready-to-Pickup Time',
        'ready_to_door': 'Ready-to-Door Time'
    }

    for key, name in metrics_to_test.items():
        print(f"\nAnálisis para: {name}")
        
        stat, p_value = mannwhitneyu(fcfs_delivered[key], rh_delivered[key], alternative='two-sided')
        
        # Calcular Cliff's Delta
        cliff_delta = pg.compute_effsize(fcfs_delivered[key], rh_delivered[key], eftype='cles')

        print(f"  - P-valor (Mann-Whitney U): {p_value:.4f}")
        print(f"  - Cliff's Delta (Tamaño del Efecto): {cliff_delta:.4f}")

        if p_value < 0.05:
            print("  - Conclusión: La diferencia es estadísticamente significativa.")
            if cliff_delta > 0.2:
                print("    (Efecto: FCFS tiende a tener valores más altos que RH)")
            elif cliff_delta < -0.2:
                 print("    (Efecto: RH tiende a tener valores más altos que FCFS)")
        else:
            print("  - Conclusión: La diferencia no es estadísticamente significativa.")

    print("\n--- 2. Comparación de Proporción de Multi-Bundles (Z-test) ---")

    # Contar órdenes en multi-bundles
    fcfs_multi_bundle_count = fcfs_delivered[fcfs_delivered['bundle_size'] > 1].shape[0]
    rh_multi_bundle_count = rh_delivered[rh_delivered['bundle_size'] > 1].shape[0]

    # Total de órdenes entregadas
    fcfs_total_delivered = fcfs_delivered.shape[0]
    rh_total_delivered = rh_delivered.shape[0]

    count = np.array([fcfs_multi_bundle_count, rh_multi_bundle_count])
    nobs = np.array([fcfs_total_delivered, rh_total_delivered])

    if nobs.all() > 0:
        stat, p_value = proportions_ztest(count, nobs)
        
        prop_fcfs = (fcfs_multi_bundle_count / fcfs_total_delivered) * 100
        prop_rh = (rh_multi_bundle_count / rh_total_delivered) * 100

        print(f"  - Proporción FCFS: {prop_fcfs:.2f}% ({fcfs_multi_bundle_count}/{fcfs_total_delivered})")
        print(f"  - Proporción RH: {prop_rh:.2f}% ({rh_multi_bundle_count}/{rh_total_delivered})")
        print(f"  - P-valor (Z-test): {p_value:.4f}")

        if p_value < 0.05:
            print("  - Conclusión: La diferencia en la proporción de multi-bundles es estadísticamente significativa.")
        else:
            print("  - Conclusión: La diferencia no es estadísticamente significativa.")
    else:
        print("  - No hay suficientes datos para la prueba de proporciones.")

    print("\n" + "="*60)
    print("ANÁLISIS ESTADÍSTICO COMPLETADO")
    print("="*60)


if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(__file__))
    raw_results_path = os.path.join(base_path, 'results', 'raw')

    fcfs_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_limited_fcfs_results.csv')
    rh_path = os.path.join(raw_results_path, 'synthetic_lapaz_orders_limited_rh_results.csv')
    
    run_statistical_analysis(fcfs_path, rh_path)
