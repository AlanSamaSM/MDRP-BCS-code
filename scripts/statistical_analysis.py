import os
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu
import pingouin as pg

def run_statistical_analysis(fcfs_results_path, rh_results_path):
    """ Compara los resultados de dos políticas (FCFS y RH) usando pruebas estadísticas."""
    
   