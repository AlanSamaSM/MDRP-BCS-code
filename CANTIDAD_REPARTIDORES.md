# 📊 ¿CÓMO SE DETERMINA LA CANTIDAD DE REPARTIDORES?

## Ubicación en el Código

**Archivo:** `src/synth_loader.py`, líneas 19-47

```python
def load_synth_instance(
    csv_path,
    n_couriers=None,                    # ← Parámetro 1: Especificar directo
    orders_per_courier=None,            # ← Parámetro 2: Por ratio
    min_couriers=15,                    # ← Parámetro 3: Mínimo
):
```

---

## 3 FORMAS DE DETERMINAR CANTIDAD DE REPARTIDORES

### **Opción 1: Especificar Directamente (n_couriers)**

```python
# En scripts/run_synth_instance.py o similar:
orders, couriers, restaurants, _ = load_synth_instance(
    csv_path,
    n_couriers=50  # ← Exactamente 50 repartidores
)
```

**Ventaja:** Control exacto  
**Desventaja:** Hardcodeado

---

### **Opción 2: Calcular por Ratio (orders_per_courier)** ⭐ **ESTA ES LA ACTUAL**

```python
# Lógica en src/synth_loader.py, líneas 40-46:

if n_couriers is None:
    if orders_per_courier is None:
        orders_per_courier = TARGET_ORDERS_PER_COURIER  # ← Valor por defecto
    
    computed = math.ceil(len(df) / orders_per_courier)
    n_couriers = max(min_couriers, computed)
```

**Fórmula:**
```
n_couriers = max(
    min_couriers,
    ceil(total_orders / orders_per_courier)
)
```

**Ejemplo con tus datos (1,038 órdenes):**

| Parámetro | Valor | Cálculo | Resultado |
|-----------|-------|---------|-----------|
| **TARGET_ORDERS_PER_COURIER** | 18 | ceil(1038 / 18) | 58 |
| **min_couriers** | 15 | max(15, 58) | **58** |

✅ **Con 1,038 órdenes → 58 repartidores**

---

### **Opción 3: Especificar orders_per_courier Manualmente**

```python
orders, couriers, restaurants, _ = load_synth_instance(
    csv_path,
    orders_per_courier=25  # ← En lugar de 18
)
# Resultado: ceil(1038 / 25) = 42 repartidores
```

---

## Donde se Define TARGET_ORDERS_PER_COURIER

**Archivo:** `src/config.py`, línea 15

```python
TARGET_ORDERS_PER_COURIER = 18  # Promedio de pedidos por courier por turno
```

**Cambiar este valor = cambiar cantidad de repartidores automáticamente**

---

## Flujo Actual (Síntesis)

```
scripts/run_synth_instance.py
│
└─→ load_synth_instance(csv_path)
   │
   ├─ Lee CSV: 1,038 órdenes
   │
   ├─ ¿Se especificó n_couriers? NO
   │  └─ ¿Se especificó orders_per_courier? NO
   │     └─ Usa TARGET_ORDERS_PER_COURIER = 18 (de config.py)
   │
   ├─ Calcula: ceil(1038 / 18) = 58
   │
   ├─ Valida: max(58, min_couriers=15) = 58
   │
   └─ Crea 58 objetos Courier con turno [start, end]
```

**Resultado:** ✅ **58 repartidores por simulación**

---

## ¿Dónde se Usa?

### En scripts/run_fcfs_instance.py

```python
from src.synth_loader import load_synth_instance

orders, couriers, restaurants, _ = load_synth_instance(
    csv_path,
    n_couriers=None  # ← Auto-calcular
)
# Resultado: 58 couriers
```

### En scripts/run_synth_instance.py

```python
orders, couriers, restaurants, _ = load_synth_instance(
    csv_path
    # Sin especificar n_couriers → auto-calcular
)
# Resultado: 58 couriers
```

---

## Tabla de Sensibilidad

¿Cuántos repartidores con diferentes parámetros?

| total_órdenes | orders_per_courier | n_couriers | Utilización |
|---------------|--------------------|-----------|------------|
| 1,038 | 15 | ceil(1038/15) = 69 | 😃 Bien utilizado |
| 1,038 | 18 | ceil(1038/18) = **58** | ✅ **ACTUAL** |
| 1,038 | 20 | ceil(1038/20) = 52 | 😐 Más apretado |
| 1,038 | 25 | ceil(1038/25) = 42 | 😕 Muy cargado |

---

## Código Completo: Cómo se Generan los Couriers

```python
# Líneas 70-76 en src/synth_loader.py

couriers = [
    Courier(
        id=i + 1,                  # IDs 1-58
        on_time=start,             # Inicio turno (08:00)
        off_time=end,              # Fin turno (23:59)
        location=depot             # Ubicación inicial (centro La Paz)
    )
    for i in range(n_couriers)     # Itera 58 veces (si n_couriers=58)
]
```

### Clase Courier (src/main.py)

```python
class Courier:
    def __init__(self, courier_id, on_time, off_time, location):
        self.id = courier_id                    # 1-58
        self.on_time = on_time                  # Entra en turno
        self.off_time = off_time                # Sale de turno
        self.location = location                # Centro La Paz
        self.current_route = None               # Ruta actual
        self.route_history = []                 # Historial
        self.earnings = 0.0                     # Ganancias
        self.orders_delivered = 0               # Órdenes entregadas
        self.total_distance = 0.0               # Distancia total
        # ... más atributos
```

---

## Resumen: Dónde se Determina

```
┌─────────────────────────────────────────┐
│ src/config.py                           │
│ TARGET_ORDERS_PER_COURIER = 18          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ src/synth_loader.py                     │
│ n_couriers = ceil(len(df) / 18)         │
│ n_couriers = max(n_couriers, min=15)    │
│                                         │
│ RESULTADO: 58 repartidores              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ scripts/run_fcfs_instance.py             │
│ scripts/run_synth_instance.py            │
│ load_synth_instance(csv_path)            │
│                                         │
│ SALIDA: couriers = [58 objects]         │
└─────────────────────────────────────────┘
```

---

## Cómo Cambiar la Cantidad

### **Opción A: Cambiar config.py (RECOMENDADO)**

```python
# src/config.py, línea 15
TARGET_ORDERS_PER_COURIER = 15  # ← Cambiar de 18 a 15

# Efecto: 
# n_couriers = ceil(1038 / 15) = 70 repartidores
```

### **Opción B: Especificar en script**

```python
# scripts/run_synth_instance.py
orders, couriers, restaurants, _ = load_synth_instance(
    csv_path,
    n_couriers=100  # ← Exactamente 100
)
```

### **Opción C: Cambiar min_couriers**

```python
# En synth_loader.py
orders, couriers, restaurants, _ = load_synth_instance(
    csv_path,
    min_couriers=50  # ← Mínimo 50, no 15
)
```

---

**Generado:** 5 de noviembre de 2025  
**Proyecto:** MDRP-BCS-code  
**Conclusión:** La cantidad se determina **automáticamente basada en TARGET_ORDERS_PER_COURIER**
