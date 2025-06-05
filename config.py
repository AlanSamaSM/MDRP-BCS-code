from datetime import timedelta
# ======================
# MDRP configuración
# ======================
OPTIMIZATION_FREQUENCY = timedelta(minutes=5)  # f Frecuencia de optimización
ASSIGNMENT_HORIZON = timedelta(minutes=20)     # ∆u Horizonte de asignación 
TARGET_CLICK_TO_DOOR = timedelta(minutes=40) #Objetivo en la calidad del servicio
MAX_CLICK_TO_DOOR = timedelta(minutes=90) #Límite en la calidad del servicio
SERVICE_TIME = timedelta(minutes=4)  # minutos (tiempo que incluye pickup + drop-off)

# penalizaciones:
GROUP_I_PENALTY = 100   
GROUP_II_PENALTY = 50   
FRESHNESS_PENALTY_THETA = 1.5  

# Parámetros de la fórmula Zt
DELTA_1 = timedelta(minutes=20)
DELTA_2 = timedelta(minutes=20)

# Pago mínimo garantizado
MIN_PAY_PER_HOUR = 15.0  # p2
PAY_PER_ORDER = 10.0  # p1

