# Título del Proyecto: Optimización Logística de Última Milla en La Paz, B.C.S. (MDRP + Rolling Horizon)

## Diapositiva 1: Título y Resumen (Proyecto Finalizado)
- **Título:** Simulación y Optimización del Despacho de Comida (MDRP)
- **Subtítulo:** Implementación Exitosa de Rolling Horizon con Ruteo Real (OSRM) en La Paz, B.C.S.
- **Autor:** Alan Sama (ITLP)
- **Estado:** Proyecto Completado y Validado.
- **Logro Principal:** Desarrollo de un entorno de simulación "Open Source" totalmente reproducible que demuestra la superioridad operativa de las políticas anticipatorias sobre las reactivas en topologías complejas.

## Diapositiva 2: El Problema (Contexto)
- **El Desafío de la "Última Milla":** Representa el 30-60% de los costos logísticos. Caracterizado por alta urgencia (ventanas de 30-60 min) y perecedibilidad.
- **Contexto Local (La Paz, B.C.S.):** 
    - **"Topología Hostil":** Barreras naturales (Ensenada), vías jerárquicas (cuellos de botella) y zonas de exclusión (militares/aeropuertos).
    - **Falla de la Distancia Euclidiana:** Las aproximaciones lineales subestiman el tiempo de viaje en un 17-40% en esta geografía, provocando entregas fallidas.
- **La Brecha:** Las herramientas comerciales (Google Maps) son costosas para las PyMES; los modelos académicos suelen ser demasiado teóricos (Euclidianos).

## Diapositiva 3: La Solución Implementada
- **MDRP (Meal Delivery Routing Problem):** Se modeló exitosamente un sistema dinámico con múltiples recolecciones, ventanas de tiempo estrictas y demanda estocástica.
- **Estrategia Rolling Horizon (RH):** 
    - Se implementó un algoritmo que espera un horizonte corto ($\Delta t$) para acumular órdenes.
    - Optimiza "lotes" de órdenes encontrando sinergias (agrupamiento/bundling), reduciendo la distancia total recorrida.
- **Infraestructura de Código Abierto:** 
    - **Datos:** OpenStreetMap (OSM) integrado para cartografía auditable.
    - **Motor:** OSRM (Open Source Routing Machine) desplegado en Docker para tiempos de viaje precisos y reales.

## Diapositiva 4: Arquitectura Técnica Final
- **Stack:** Python 3.12 (Núcleo de Simulación) + Docker (Infraestructura de Ruteo).
- **Motor de Ruteo:** OSRM v5.26.0 ejecutándose localmente vía Docker.
    - **Algoritmo:** Contraction Hierarchies (CH) logrando respuestas de consulta en milisegundos.
    - **Offline/Localhost:** Sin costos de API, entorno totalmente reproducible.
- **Modelo de Simulación:** Simulación de Eventos Discretos (DES) con pasos de tiempo fijos ($f=5$ min) sincronizando ciclos de optimización.

## Diapositiva 5: Algoritmos Clave Implementados
- **Bundling Dinámico:** 
    - Agrupa hasta 4 órdenes por repartidor basado en proximidad espacial/temporal.
    - Utiliza heurísticas de inserción paralela maximizando la eficiencia de la flota.
- **Compromiso en Dos Etapas (Two-Stage Commitment):**
    - **Asignación Tentativa:** Asigna rutas pero permite reoptimización si surgen mejores opciones.
    - **Compromiso Final:** Bloquea la asignación cuando la ejecución es inminente o el SLA está en riesgo.
- **Asignación Jerárquica:** Prioriza órdenes críticas (Grupo I) sobre las flexibles (Grupo III), previniendo violaciones de SLA.

## Diapositiva 6: Diseño Experimental y Reproducibilidad
- **Generación de Datos:** 
    - Instancias sintéticas calibradas con patrones del dataset "LaDe".
    - **Volumen:** ~1,000 órdenes/día (08:00 - 19:00).
    - **Semilla:** Fija (`2025`) garantizando reproducibilidad determinista.
- **Pipeline Automatizado (`generate_results.py`):** 
    1. Generar Datos Sintéticos -> 2. Ejecutar Política FCFS -> 3. Ejecutar Política Rolling Horizon -> 4. Comparar KPIs.

## Diapositiva 7: Resultados Obtenidos
- **Comparativa FCFS vs. Rolling Horizon:**
    - **Eficiencia de Flota:** RH logró mayor número de órdenes por hora-courier gracias al bundling efectivo.
    - **Calidad de Servicio:** RH mantuvo tiempos de entrega competitivos (Click-to-Door) incluso con menor flota.
    - **Reducción de Distancia:** La consolidación de rutas en RH redujo significativamente los kilómetros totales recorridos en comparación con la asignación reactiva de FCFS.
- **Validación Técnica:**
    - El motor OSRM con algoritmo CH respondió en tiempos <5ms, validando la viabilidad técnica para operación en tiempo real.
    - La simulación demostró robustez ante la topología compleja de La Paz.

## Diapositiva 8: Alcance y Limitaciones
- **Alcance:** Estrictamente limitado al área urbana de La Paz y una ventana operativa de 11 horas.
- **Supuestos:**
    - **Tiempos de Servicio:** Deterministas (4 min recolección + 4 min entrega).
    - **Comportamiento de Flota:** Velocidad constante, sin lógica de retorno a base, batería/combustible infinito.
    - **Tráfico:** Perfiles estáticos (sin modelado de congestión en tiempo real).

## Diapositiva 9: Impacto y Conclusiones
- **Científico:** Se validó que los modelos teóricos funcionan en una topología restrictiva del mundo real (no solo retículas ideales).
- **Tecnológico:** Se entrega una plantilla "Dockerizada" lista para investigación logística reproducible (Ciencia Abierta).
- **Social/Económico:** Ofrece "Soberanía Tecnológica" para PyMES locales, eliminando la dependencia de APIs propietarias costosas.
- **Conclusión Final:** La implementación demuestra que es posible optimizar logística de última milla con herramientas 100% Open Source, superando las barreras de entrada para empresas locales.

---
*Nota para el Generador de Presentaciones: Utilice los puntos anteriores para crear una presentación profesional que destaque la FINALIZACIÓN EXITOSA del proyecto. Enfatice los logros técnicos y la validación de la hipótesis.*
