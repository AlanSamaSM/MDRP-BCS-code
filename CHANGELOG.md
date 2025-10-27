# Changelog - MDRP-BCS-code

## [Versión Final - Octubre 2025] - Implementación completa del pipeline

### ✅ Completado

#### 1. Orquestador Completo (`scripts/generate_results.py`)
- **Función `run_full_pipeline()`**: Ejecuta automáticamente todo el pipeline experimental
  - Generación de datos sintéticos
  - Simulación FCFS
  - Simulación Rolling Horizon
  - Análisis y comparación de KPIs
- **Modo `--analyze-only`**: Permite recalcular métricas sin reejecutar simulaciones
- **Parámetro `--csv`**: Permite especificar archivo de órdenes personalizado

#### 2. Métricas Expandidas (Paridad con Reyes 2018)
Todas las métricas ahora incluyen percentiles y estadísticos detallados:

**Calidad de Servicio:**
- ✅ Click-to-Door: promedio, P10, P50, P90, P95
- ✅ Ready-to-Pickup: promedio, P10, P50, P90
- ✅ Ready-to-Door: promedio, P10, P50, P90
- ✅ Click-to-Door Overage (sobretiempo vs. target 40 min)
- ✅ % Órdenes no entregadas

**Eficiencia Operativa:**
- ✅ Órdenes por courier-hora
- ✅ Bundles por hora (ahora calculado correctamente)
- ✅ Tamaño promedio de bundle
- ✅ Distancia total (km)
- ✅ Utilización de couriers (% tiempo conduciendo)

**Costos:**
- ✅ Compensación total de couriers
- ✅ Costo por orden
- ✅ Ganancias por entregas
- ✅ Fracción de couriers con compensación mínima

#### 3. Captura de Métricas en Simulación (`src/main.py`)
- **Clase `Courier`** actualizada con:
  - `bundles_picked_up`: contador de bundles recogidos
  - `driving_time`: tiempo total conduciendo (minutos)
- **Loop de simulación** actualizado para:
  - Incrementar `bundles_picked_up` al completar cada ruta final
  - Acumular `driving_time` usando duration de OSRM
  - Guardar métricas adicionales en CSVs de couriers

#### 4. Documentación
- ✅ `docs/project_pseudocode.txt`: Pseudocódigo completo en español
- ✅ `README.md`: Actualizado con instrucciones completas de uso
- ✅ `CHANGELOG.md`: Este archivo de cambios

#### 5. Generación de Datos Sintéticos Mejorada
- ✅ Restricción a polígono definido por usuario
- ✅ Distribución uniforme de restaurantes y destinos
- ✅ Snapping a tierra para evitar coordenadas en el mar

### 🎯 Uso del Pipeline

**Ejecución completa (recomendado):**
```bash
python scripts/generate_results.py
```

**Solo análisis (con resultados existentes):**
```bash
python scripts/generate_results.py --analyze-only
```

**Con CSV personalizado:**
```bash
python scripts/generate_results.py --csv data/mi_dataset.csv
```

### 📊 Salidas Generadas

```
results/
├── raw/
│   ├── synthetic_lapaz_orders_limited_fcfs_results.csv
│   ├── synthetic_lapaz_orders_limited_fcfs_couriers.csv
│   ├── synthetic_lapaz_orders_limited_rh_results.csv
│   └── synthetic_lapaz_orders_limited_rh_couriers.csv
└── kpi_comparison.csv  # Tabla comparativa completa
```

### 🔍 Verificaciones

- ✅ Pipeline ejecuta sin errores
- ✅ Todas las métricas se calculan correctamente
- ✅ Paridad completa con métricas de Reyes (2018)
- ✅ Documentación actualizada
- ✅ Ayuda del CLI funcional (`--help`)

### 📝 Notas Técnicas

**Cálculo de Utilización de Couriers:**
- Formula: `(total_driving_time_hours / total_shift_hours) * 100`
- Usa tiempos reales de OSRM convertidos de segundos a horas
- Se acumula solo en rutas completadas

**Bundles por Hora:**
- Formula: `total_bundles_picked_up / total_shift_hours`
- Se incrementa solo al completar rutas con `commitment_type == 'final'`

**Percentiles:**
- P10, P50 (mediana), P90, P95 calculados con pandas `.quantile()`
- Aplicados a Click-to-Door, Ready-to-Pickup, Ready-to-Door

### 🚀 Próximos Pasos Sugeridos

1. Ejecutar experimentos con diferentes parámetros (λ, DELTA_1, DELTA_2)
2. Comparar con benchmarks Grubhub/LaDe si es necesario
3. Generar visualizaciones de mapas de calor de métricas
4. Análisis estadístico de significancia de mejoras

---

**Fecha de implementación:** Octubre 26, 2025
**Autor:** Alan Sama (con asistencia de GitHub Copilot)
