from datetime import timedelta
# ======================
# MDRP configuración
# ======================
OPTIMIZATION_FREQUENCY = timedelta(minutes=5)  # f Frecuencia de optimización
ASSIGNMENT_HORIZON = timedelta(minutes=20)     # ∆u Horizonte de asignación 
TARGET_CLICK_TO_DOOR = timedelta(minutes=40) #Objetivo en la calidad del servicio
MAX_CLICK_TO_DOOR = timedelta(minutes=90) #Límite en la calidad del servicio
SERVICE_TIME = timedelta(minutes=4)  # minutos (tiempo que incluye pickup + drop-off)


MAX_TARGET_BUNDLE_SIZE = 5  # Evita bundles irreales bajo alta demanda
MAX_BUNDLE_SIZE = 4         # Límite duro para inserciones paralelas
TARGET_ORDERS_PER_COURIER = 18  # Promedio de pedidos por courier por turno

# Penalizaciones para clasificación de grupos 
GROUP_I_PENALTY = 100   
GROUP_II_PENALTY = 50   

# Parámetros de bundling y matching (Reyes 2018)
FRESHNESS_PENALTY_BETA = 0.1  # β: peso del retraso en la frescura de órdenes en pesos de matching
PICKUP_DELAY_THETA = 0.1      # θ: penalizacion por retraso en pickup en matching

# Parámetros de lookahead para Zt 
DELTA_1 = timedelta(minutes=20)  # Δ1: lookahead para ready time de órdenes
DELTA_2 = timedelta(minutes=20)  # Δ2: lookahead para disponibilidad de couriers

MAX_WAIT_BEFORE_FORCED_COMMIT = timedelta(minutes=10)  # x: force commit if order ready >x min

# Pago mínimo garantizado
MIN_PAY_PER_HOUR = 15.0  # p2
PAY_PER_ORDER = 10.0  # p1

