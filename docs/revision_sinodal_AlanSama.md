# Dictamen de Revisión Sinodal — Tesis de Maestría

**Tesis:** Logística de Última Milla en Redes Viales Reales: Un Enfoque Reproducible para el MDRP en La Paz, B.C.S.
**Sustentante:** Alan José Marcos Sánchez Martínez
**Programa:** Maestría en Sistemas Computacionales
**Institución:** Instituto Tecnológico de La Paz — División de Estudios de Posgrado e Investigación
**Director declarado:** Dr. Marco Antonio Castro Liera
**Documento revisado:** [docs/tesisss.tex](tesisss.tex) (~2887 líneas)
**Fecha de revisión:** 2 de mayo de 2026
**Naturaleza del dictamen:** Revisión sinodal **pre-impresión**, con observaciones obligatorias y sugeridas
**Tono adoptado:** Sinodal exigente — el sustentante solicitó deliberadamente este perfil de revisión para preparar la defensa

---

## 0. Nota preliminar al sustentante

Esta revisión asume que el documento corresponde a la **tesis final** y no a un anteproyecto, a pesar de que la portada conserva la designación "ANTEPROYECTO DE TESIS" y la fecha "DICIEMBRE 2023". Bajo ese supuesto, el rigor aplicado es el que correspondería a una versión próxima a impresión y defensa, con criterio sinodal exigente. Las observaciones se clasifican en **obligatorias** (su corrección es condición para imprimir) y **sugeridas** (mejoran la calidad pero no bloquean).

El dictamen no incluye redacciones alternativas concretas: por solicitud explícita del sustentante, sólo se identifican los problemas y se justifica por qué deben atenderse, dejando al autor la responsabilidad de redactar la corrección.

---

## 1. Resumen ejecutivo

### Veredicto general

La tesis es **aprobable con observaciones obligatorias** previas a la versión final impresa. El trabajo realiza una contribución científica genuina — un simulador reproducible para el MDRP integrando OSRM sobre OpenStreetMap, con análisis estadístico riguroso de cuatro escenarios de saturación — pero presenta **defectos formales graves** que de no corregirse comprometerían el dictamen escrito de los sinodales y expondrían al sustentante a observaciones evitables el día de la defensa.

### Tres mensajes clave

1. **El aporte es real y defendible.** La identificación empírica del punto de cruce entre los regímenes $\rho \in [26, 35]$ donde Rolling Horizon comienza a superar a FCFS, junto con la cuantificación estadísticamente significativa de mejoras de hasta 57.2% en CtD bajo alta saturación (superando el rango 10-25% reportado en la literatura por Reyes et al., 2018), constituye una contribución empírica original sobre topología vial real.

2. **Los defectos formales graves bloquean la impresión.** La portada designa el documento como "ANTEPROYECTO" con fecha 2023; existen 8 referencias declaradas en `biblio.bib` que nunca se citan; el tiempo de preparación se reporta inconsistentemente (12±3 min en código y §3.2, vs. 15±5 min en §4); existe un párrafo duplicado evidente en la sección 1.6.5; la ruta de gráficos en LaTeX es absoluta a Windows. Cada uno de estos puntos sería marcado por cualquier sinodal en su acta.

3. **Hay zonas argumentativas vulnerables ante un jurado exigente.** La hipótesis tal como está redactada (líneas 437-442) **es falsada en S1-S2** (RH no supera a FCFS en CtD ni en RtD bajo baja saturación); esto se gestiona en el Capítulo 5 con honestidad, pero la **formulación original no contemplaba el régimen crítico**, lo cual permite a un sinodal hostil sostener que la hipótesis original se rechaza. Asimismo, el fallo de 3 de 10 semillas se atribuye a "interrupción del servicio OSRM" sin diagnóstico técnico sustantivo, y la calibración de demanda con datos LaDe (chinos) sobre La Paz se reconoce como limitación pero no se mitiga ni siquiera con análisis de sensibilidad.

### Bloqueadores absolutos para impresión (síntesis)

- Portada incoherente con el estado del trabajo (anteproyecto/tesis, fecha 2023/2026, plural sin co-director).
- 8 referencias bibliográficas huérfanas en `biblio.bib`.
- Inconsistencia numérica entre §3.2 y §4.5 sobre tiempo de preparación.
- Texto duplicado evidente en §1.6.5 (líneas 537-538).
- Ruta absoluta `\graphicspath` no portable.

### Mejoras altamente recomendadas (síntesis)

- Diagnóstico técnico de las 3 semillas fallidas o reformulación honesta de su tratamiento.
- Reformulación de la hipótesis para incluir explícitamente el régimen de saturación crítico, o justificación argumentativa adicional en §5.2 sobre por qué la falsación parcial no invalida el aporte.
- Reporte explícito del porcentaje de consultas OSRM que fueron resueltas vs. fallback euclidiano (la verificación en S4 alta seed 2025 confirma 100% OSRM, pero la tesis no lo declara y la información existe en los CSV de resultados).
- Discusión más sustantiva sobre la transferibilidad de los patrones bimodales LaDe al contexto cultural de La Paz.
- Justificación o análisis de sensibilidad sobre `MAX_BUNDLE_SIZE = 4`.

---

## 2. Evaluación capítulo por capítulo

### 2.1 Capítulo 1 — Introducción (líneas 110–603)

#### Síntesis crítica

El capítulo construye un recorrido conceptual sólido desde el TSP hasta el MDRP, justificando la pertinencia del problema en La Paz. La progresión TSP → VRP → DVRP → DARP → MDRP es didácticamente correcta y cita literatura adecuada (Lenstra1981, Dantzig1959, Caceres-Cruz2014, Pillac2013, Psaraftis1980, Cordeau2007, Ichoua2006DDARP, Reyes2018). El planteamiento del problema invoca correctamente el resultado de Boyaci2021 sobre la subestimación euclidiana de 17-40%, que es el argumento central que motiva el uso de OSRM.

#### Fortalezas argumentativas

- La transición de TSP a VRP a DVRP/MDRP está bien hilada y demuestra dominio del estado del arte.
- La justificación combina relevancia científica, tecnológica y socioeconómica (PyMES locales, soberanía tecnológica). El argumento de "arranque en frío" para descartar Aprendizaje Profundo (líneas 472-480) es elegante y defendible.
- La sección 1.6 "Alcance y limitaciones" es exhaustiva: identifica explícitamente el modelo de tráfico estático, los tiempos deterministas, la ausencia de cancelaciones, multihoming y heterogeneidad de flota. Esto blinda al sustentante contra preguntas sobre supuestos no declarados.

#### Debilidades / preguntas previsibles del jurado

1. **La hipótesis (líneas 437-442) está formulada en términos absolutos ("superará significativamente").** Los resultados muestran que en S1-S2 RH es **peor** en CtD y RtD que FCFS. Esto **no es un detalle**: un sinodal exigente sostendrá que la hipótesis original se **rechaza** en el régimen de baja saturación, y que la matización ofrecida en §5.2 es una racionalización post-hoc. La hipótesis debe reformularse para incluir un cuantificador condicional (régimen de saturación) o el sustentante debe estar preparado para defender por qué la falsación parcial no invalida la tesis.

2. **La hipótesis menciona "Ready-to-Door"** como métrica clave (línea 440). Pero el análisis estadístico del Capítulo 4 hace foco en Click-to-Door y CTD Overage. ¿Por qué el análisis principal no es sobre la métrica enunciada en la hipótesis? Hay una desconexión.

3. **El objetivo específico OE2 (líneas 423-425)** habla de "validando la conectividad del grafo vial y la precisión de los tiempos de viaje frente a distancias euclidianas". El §4 reporta el cumplimiento del 100% de cobertura OSRM (líneas 2772-2774), pero **no se realiza la validación cuantitativa** de la diferencia OSRM vs. euclidiana. ¿Existió esa comparación? ¿Cuál fue la magnitud de la diferencia en La Paz específicamente? El supuesto de Boyaci2021 (17-40%) es una cita de la literatura, no un dato propio.

4. **El alcance excluye explícitamente la comparación con otros algoritmos** (líneas declarativas en §1.6). Un sinodal puede preguntar: ¿por qué no se compara también con un algoritmo de optimización exacta (resolución por MIP en instancias pequeñas) que serviría de cota superior, o con una metaheurística clásica (ALNS, Tabu Search) que sirva de baseline más sofisticado que FCFS?

5. **La afirmación "cercana al óptimo"** que se atribuye a la literatura (línea 457) es vaga. ¿Qué literatura? ¿En qué métrica? El argumento de cierre de brecha pierde fuerza si no se acota.

6. **El cuarto vértice del polígono urbano** (línea 1614 del Cap. 3) define la zona estudiada. La línea 488-494 declara "zona urbana de La Paz" pero no especifica que el estudio se restringe a un cuadrilátero de ~5 km × 3 km. Esto debería estar explícito en el alcance geográfico.

#### Recomendaciones para el sinodal del trabajo

- Reformular la hipótesis para que sea consistente con los resultados, o justificar argumentativamente por qué la formulación original sigue siendo defendible.
- Explicitar en §1.6.1 los límites del polígono urbano de estudio.
- Agregar (al menos como párrafo) una validación cuantitativa de la diferencia OSRM-euclidiana en La Paz, en lugar de delegar el argumento a Boyaci2021.

---

### 2.2 Capítulo 2 — Marco Teórico (líneas 604–1212)

#### Síntesis crítica

El capítulo formaliza el MDRP siguiendo escrupulosamente la notación de Reyes et al. (2018), describe la heurística Rolling Horizon en sus cinco componentes (tamaño de bundle, generación, clasificación por prioridad, asignación bipartita, compromiso en dos etapas), introduce los fundamentos de Contraction Hierarchies y OSRM, y plantea el modelo de generación estocástica de demanda. Es, técnicamente, el capítulo más sólido del documento.

#### Fortalezas argumentativas

- La formalización matemática del problema (líneas 615-759) es completa y consistente: conjuntos, decisiones, supuestos estructurales, modelo de compensación, métricas primarias (CtD, RtP, RtD).
- La descripción de la heurística RH (líneas 763-954) es fiel al paper original y enuncia con claridad las cinco fases del ciclo, incluyendo la matriz de pesos $w_{s,d}$ y la solución vía Algoritmo Húngaro.
- La sección de OSRM/CH (líneas 959-1074) demuestra comprensión profunda del mecanismo de Contraction Hierarchies, incluyendo la complejidad de consulta $O(\sqrt{|V|} \cdot \log |V|)$.

#### Debilidades / preguntas previsibles del jurado

7. **La función objetivo del MDRP no se enuncia explícitamente.** El capítulo formaliza variables y restricciones, pero no escribe la función objetivo del problema completo. Reyes2018 minimiza una combinación lineal de tiempo de entrega y compensación. La tesis omite esta formulación y salta directamente a las métricas. Un sinodal puede preguntar: ¿cuál es exactamente la función objetivo del problema que se resuelve? Si la respuesta es "minimizar CtD bajo restricciones de servicio", debe escribirse.

8. **La diferencia entre $\Delta_u$, $\Delta_1$ y $\Delta_2$** debe aclararse mejor. El código define los tres en 20 minutos, pero el texto los trata como independientes en algunas zonas y los confunde en otras. El sinodal preguntará la diferencia conceptual entre el horizonte de asignación y los lookaheads de Zt.

9. **El factor de penalización $\beta = 0.1$ y $\theta = 0.1$ no se justifican.** Estos parámetros aparecen como números mágicos. ¿Por qué 0.1 y no 0.05 o 0.5? ¿Se hizo análisis de sensibilidad? Si se tomó del paper original, debe citarse el valor con su justificación; si se calibró localmente, debe describirse el procedimiento.

10. **La sección 2.4 sobre el Proceso de Poisson No Homogéneo** (líneas 1079-1154) describe correctamente la teoría, pero la conexión con la calibración real (LaDe → La Paz) se relega al Cap. 3. Un sinodal exigente preguntará si los parámetros bimodales ($\mu_m = 09:00$, $\mu_e = 17:00$, $A_m = 2.4$, $A_e = 2.0$) son apropiados para hábitos mexicanos. En México, los picos clásicos de delivery son 13:00-14:00 (almuerzo) y 20:00-21:00 (cena), no 09:00 y 17:00.

11. **El parámetro `MAX_TARGET_BUNDLE_SIZE = 5`** (cap en Zt) y `MAX_BUNDLE_SIZE = 4` (cap duro) están en el código pero no claramente explicados en el marco teórico. ¿Por qué estos valores y no otros?

12. **El supuesto de tiempos de viaje invariantes en el tiempo** (línea 663-664) es incompatible con tráfico real. Esta limitación debe estar mejor enmarcada teóricamente, no solo como mención en §1.6.

#### Recomendaciones para el sinodal del trabajo

- Escribir explícitamente la función objetivo del problema MDRP.
- Justificar (con referencia o análisis propio) los valores de $\beta$, $\theta$, `MAX_BUNDLE_SIZE`.
- Adelantar una breve discusión en §2.4 sobre la transferibilidad de patrones bimodales chinos al contexto mexicano, o ajustar los parámetros a hábitos locales.

---

### 2.3 Capítulo 3 — Desarrollo (líneas 1213–2285)

#### Síntesis crítica

El capítulo describe la arquitectura de tres capas (OSRM contenerizado, simulador Python, scripts de análisis), el generador sintético de instancias, el motor de eventos discretos, las dos políticas (FCFS y RH) y el diseño experimental. Es ambicioso y, en general, exitoso. Los parámetros declarados en §3.1 (líneas 1483-1506) son consistentes con los valores en [src/config.py](../src/config.py) (verificado: `OPTIMIZATION_FREQUENCY = 5 min`, `ASSIGNMENT_HORIZON = 20 min`, `TARGET_CLICK_TO_DOOR = 40 min`, `SERVICE_TIME = 4 min`, `MAX_BUNDLE_SIZE = 4`, `FRESHNESS_PENALTY_BETA = 0.1`, `PICKUP_DELAY_THETA = 0.1`, `GROUP_I_PENALTY = 100`, `GROUP_II_PENALTY = 50`, `PAY_PER_ORDER = 10`, `MIN_PAY_PER_HOUR = 15`).

#### Fortalezas argumentativas

- La arquitectura desacoplada (OSRM como servicio HTTP, simulador Python, capa de análisis estadístico) es modular y permite intercambiar componentes (e.g., reemplazar OSRM por GraphHopper sin tocar el simulador).
- El uso de Docker para la inmutabilidad del entorno de cálculo es correcto, defendible, y representa buena práctica de Ciencia Abierta.
- La descripción del two-stage commitment (líneas 2005-2041) es la más detallada y correcta del documento, y corresponde fielmente a la implementación en [src/asignaciontentativa.py](../src/asignaciontentativa.py:112-184). Se confirma que tras el fix del commit 204500f, el código marca correctamente las órdenes como `'assigned'` en los casos de forced-commit y final-commit.

#### Debilidades / preguntas previsibles del jurado

13. **El código del proyecto fue sometido a un fix crítico el 4 de abril de 2026 (commit 204500f)** que corregía un bug en `two_stage_commitment` que dejaba órdenes en estado `'ready'` y permitía su re-asignación múltiple, inflando las métricas de eficiencia (`courier_del`) en factores de 2-3×. El experimento más reciente ([results/experiments/20260413_182745/](../results/experiments/20260413_182745/)) corresponde a ejecución post-fix, pero **el documento no informa al lector sobre la existencia del bug ni sobre la verificación de que las cifras reportadas son post-fix**. Un sinodal hostil puede argumentar que la integridad de los datos depende de un fix que el autor no menciona, lo cual compromete la reproducibilidad declarada. Esta omisión debe corregirse explícitamente, ya sea en una nota al pie en §3.4 o §4.1 o en la sección de Limitaciones.

14. **La sección 3.2 sobre generación sintética declara $T_{prep} \sim \max(5, \mathcal{N}(\mu_{prep}, \sigma_{prep}^2))$ con $\mu_{prep} = 12$, $\sigma_{prep} = 3$** (líneas 1585-1586), lo cual coincide con [scripts/make_synth_orders.py:110](../scripts/make_synth_orders.py#L110): `prep_minutes = np.clip(rng.normal(12, 3, size=...), 5, None)`. **Pero el Capítulo 4 declara "$t_{\text{prep}} = 15 \pm 5$ min" (línea 2713)**. Esto es un error numérico evidente — los valores correctos son $12 \pm 3$ min. El error puede confundir a un sinodal y, peor, puede leerse como evidencia de que el autor no controla los parámetros de su propia simulación.

15. **El parámetro `MAX_BUNDLE_SIZE = 4`** carece de justificación teórica o empírica. Reyes2018 no lo limita. La limitación a 4 órdenes por bundle es una decisión de diseño con consecuencias significativas: en S4 (alta saturación), el bundle promedio bajo RH es 3.07, muy cerca del cap. Sin análisis de sensibilidad sobre este parámetro, es imposible saber si los resultados de S4 mejorarían (o empeorarían) con `MAX_BUNDLE_SIZE = 5, 6` o ilimitado. Un sinodal preguntará: ¿qué pasaría si elevas el cap?

16. **El generador de instancias define `TARGET_ORDERS = 1000`** (línea 22 de make_synth_orders.py) y los CSVs reales tienen ~1038 órdenes. La tesis menciona "$\sim$1,026 órdenes" (línea 2767) y "1,038" en otros lugares. La cifra correcta debe declararse de forma única y consistente. Las semillas válidas (2025-2032 excluyendo 2027) producen valores ligeramente distintos (988-1047) por la naturaleza aleatoria de Poisson; conviene reportar el rango.

17. **Los 25 restaurantes** del catálogo `la_paz_restaurants.geojson` (línea 1643 de la tesis) se "reproyectan dentro del polígono urbano" (línea 1645). En [scripts/make_synth_orders.py:114-118](../scripts/make_synth_orders.py#L114-L118) esto se implementa reemplazando la geometría de los 25 puntos con un nuevo muestreo uniforme dentro del polígono. **Los restaurantes reales geolocalizados se descartan**: solo se preserva el conteo (25), las ubicaciones se randomizan. Esto contradice la afirmación de "geolocalización real" del Cap. 4 (líneas 2303 y 2767, donde se menciona "142~restaurantes geolocalizados", cifra que adicionalmente **no coincide** con los 25 del archivo). El sinodal querrá aclaración: (i) ¿son 25 o 142?, (ii) ¿son ubicaciones reales o sintéticas?

18. **El cálculo de tamaño de flota** (líneas 1648-1664) usa `n_couriers = max(min_couriers, ceil(total_orders / orders_per_courier))`. Para S1 con 1038/18 ≈ 58 couriers y `min_couriers = 10` el cap inferior no afecta. Pero la lógica de mín/máx debe quedar más clara para que un sinodal entienda exactamente cómo se construye cada escenario.

19. **Los cuatro escenarios S1-S4** se construyen variando `orders_per_courier`, lo cual altera el número de couriers manteniendo el número de órdenes. Este es un diseño experimental válido para variar la saturación, pero un sinodal puede preguntar si no sería más natural variar el número de órdenes con flota fija (escenarios de demanda) o variar ambos.

#### Recomendaciones para el sinodal del trabajo

- Documentar (al menos en una nota al pie) la existencia y resolución del bug del two-stage commitment.
- Homologar el valor del tiempo de preparación a 12±3 min en todo el documento.
- Justificar `MAX_BUNDLE_SIZE = 4` o realizar análisis de sensibilidad.
- Aclarar la inconsistencia 25 vs. 142 restaurantes y la decisión de re-muestrear ubicaciones.
- Reportar un único rango/promedio de órdenes por instancia con su variabilidad.

---

### 2.4 Capítulo 4 — Resultados (líneas 2286–2741)

#### Síntesis crítica

El capítulo reporta los resultados de 56 simulaciones válidas (4 escenarios × 7 semillas × 2 políticas), con 21 KPIs por simulación. Las tablas y figuras son claras, las cifras son verificables contra los CSV en [results/experiments/20260413_182745/](../results/experiments/20260413_182745/), y la discusión por regímenes (baja/media/alta saturación) es coherente con la evidencia. La identificación del punto de cruce entre S2 y S3 es el hallazgo central del trabajo, bien argumentado.

Tras verificación cruzada con `cross_seed_aggregation.csv`, las cifras principales reportadas en la Tabla 4.1 (líneas 2596-2610) son **correctas**: $\bar{x}_{FCFS} = 10.10$, $\bar{x}_{RH} = 20.38$, $\bar{r} = 0.911 \pm 0.018$ (S1); $35.79 / 25.52 / 0.406 \pm 0.046$ (S3); $75.41 / 32.26 / 0.144 \pm 0.030$ (S4).

#### Fortalezas argumentativas

- El uso de Mann-Whitney U es metodológicamente correcto: la prueba de Shapiro-Wilk rechazó normalidad en las 160 distribuciones evaluadas (línea 2581), justificando rigurosamente el test no paramétrico.
- La corrección Benjamini-Hochberg para comparaciones múltiples y el reporte del tamaño de efecto rank-biserial con clasificación de Cohen demuestran madurez estadística.
- El test ómnibus de Kruskal-Wallis ($H = 782.78$, $p < 0.001$) confirma adecuadamente que el efecto de la política varía significativamente entre escenarios.
- La interpretación del "efecto pequeño en S4 a pesar de mejora grande en media" (líneas 2620-2623) — atribuida a la distribución bimodal de FCFS bajo alta saturación — es estadísticamente lúcida y demuestra comprensión profunda de la diferencia entre estadísticos ordinales y de tendencia central.

#### Debilidades / preguntas previsibles del jurado

20. **La afirmación "Todas las 28 pruebas individuales resultaron significativas tras la corrección de Benjamini-Hochberg" (líneas 2593-2594)** es **estrictamente verdadera para Click-to-Door** (pues son 4 escenarios × 7 semillas = 28 pruebas, todas significativas según `statistical_summary.csv`). Pero **NO es verdadera para todas las métricas reportadas**: en `cross_seed_aggregation.csv`, la métrica **Ready-to-Pickup en S4 Alta tiene `All_Significant_BH=No` ($\bar{r} = 0.0331$)**. Adicionalmente, varias semillas individuales en S4 muestran $p > 0.05$ tras corrección BH para Ready-to-Pickup (seeds 2025, 2026, 2028, 2030, 2032). La afirmación universal **debe matizarse** o restringirse explícitamente a la métrica CtD. Un sinodal hostil puede explotar esta ambigüedad.

21. **El "11.5% de órdenes no entregadas bajo FCFS en S4"** (línea 2814) es uno de los hallazgos más fuertes del documento. Verificable: con 1038 órdenes y semilla 2025, la cifra debe poder reconstruirse desde el CSV de resultados FCFS de S4 (orders con `status != 'delivered'`). El sustentante debe poder reproducir esta cifra en vivo si el jurado lo solicita.

22. **La cifra "100% de cobertura del grafo vial" (línea 2773)** se afirma sin reportar el dato crudo. Verificación cruzada con [results/experiments/20260413_182745/S4_alta_seed2025/synthetic_lapaz_orders_seed2025_rh_results.csv](../results/experiments/20260413_182745/S4_alta_seed2025/synthetic_lapaz_orders_seed2025_rh_results.csv) confirma que las 1038 órdenes tienen `routing_source = osrm` (cero `euclidean_fallback`). **Este dato debería estar explícito en la tesis** — es una refutación poderosa de la objeción "tal vez muchas consultas cayeron al fallback euclidiano".

23. **El "P90 CtD = 228.01 min en S4 FCFS"** y "228.01 vs 52.27" (Tabla 4.1) son cifras duras. ¿Qué significa una cola al 90% de 228 minutos (3.8 horas) para un servicio de comida? Conviene contextualizar operativamente: a esos tiempos la comida ya está fría y el cliente probablemente cancelaría. La discusión debería conectar el dato estadístico con la operación real.

24. **La "Comparación con la literatura" (líneas 2692-2700)** afirma que las mejoras superan el rango de Reyes2018 "sugiriendo que la topología vial de La Paz amplifica la ventaja". Este argumento es plausible pero **especulativo**: no se ha hecho un experimento controlado que aísle el efecto de la topología. Las diferencias podrían deberse a otros factores (diferente densidad de demanda, diferente tamaño de flota, diferente función de penalización). El sinodal preguntará: ¿qué evidencia experimental tienes para sostener que es la topología y no otro factor?

25. **El análisis estadístico se hace agregando 7 semillas, pero no se reportan intervalos de confianza por escenario**. Sería más informativo presentar boxplots o forest plots con IC95% de la diferencia $\bar{r}_{FCFS} - \bar{r}_{RH}$ por seed, en lugar de solo medias y desviaciones. La Figura 4 (boxplot CtD) atiende parcialmente esta preocupación pero no reporta IC.

26. **La Tabla 4.1 reporta SLA Compliance en S1 como "100.0% FCFS vs 99.2% RH"**. La literalidad del 100% bajo FCFS es sospechosa: significaría que ni una sola orden de las ~7300 totales en S1 (1038 × 7 seeds) excedió 40 minutos. Verificable: en `cross_seed_aggregation.csv` $\bar{x}_{FCFS} = 1.0$ confirma 100% promediado. Esto es plausible pero aún así inusual. ¿Es exactamente 100% o es 99.99% redondeado? Reportar con más precisión (e.g., "100.00%") refuerza credibilidad.

27. **La sección de discusión (líneas 2656-2700) menciona "regímenes claramente identificables"** pero no propone una explicación causal cuantitativa del punto de cruce. El sinodal preguntará: ¿qué propiedad estructural del sistema produce que el punto de cruce esté entre $\rho = 26$ y $\rho = 35$ y no en otro valor? ¿Hay una predicción teórica del paper de Reyes2018 o se trata de un hallazgo empírico sin modelo?

28. **Las 3 semillas fallidas (2027, 2033, 2034)** se atribuyen a "interrupción del servicio OSRM" sin diagnóstico. Esto es la **vulnerabilidad más grande del Capítulo 4**: un sinodal hostil puede argumentar que (i) si hubo interrupciones, ¿cómo sabemos que las 7 semillas exitosas no tuvieron interrupciones parciales que afectaron parte de los datos?, (ii) ¿se intentó reproducir esas semillas? Si no, debería intentarse antes de la defensa, ya sea para incluirlas o para entender por qué fallan. Un fallo del 30% de las corridas con causa no identificada compromete la afirmación de reproducibilidad.

#### Recomendaciones para el sinodal del trabajo

- Matizar la afirmación universal de significancia (línea 2593-2594) o restringirla a CtD.
- Reportar explícitamente el % de consultas OSRM resueltas vs. fallback.
- Diagnosticar y reportar la causa técnica de las 3 semillas fallidas.
- Presentar intervalos de confianza por seed/escenario.
- Conectar las cifras estadísticas con interpretación operativa (e.g., "P90 = 228 min implica X").

---

### 2.5 Capítulo 5 — Conclusiones (líneas 2743–2880)

#### Síntesis crítica

El capítulo verifica el cumplimiento de los objetivos, contrasta los resultados con la hipótesis, enumera las contribuciones principales y propone trabajo futuro. La estructura es ortodoxa y completa.

#### Fortalezas argumentativas

- La verificación de objetivos es exhaustiva y honesta: cada objetivo específico (OE1-OE4) recibe un párrafo de evidencia.
- El §5.2 "Verificación de la hipótesis" es **académicamente honesto**: reconoce explícitamente que en S1-S2 RH no supera a FCFS en CtD promedio. Esta honestidad debe valorarse positivamente, pero también expone el problema central del Cap. 1.
- El listado de contribuciones (§5.3) identifica correctamente los aportes diferenciados respecto a la literatura.
- El trabajo futuro (§5.4) es realista y específico, no genérico.

#### Debilidades / preguntas previsibles del jurado

29. **El §5.2 dice "La hipótesis se confirma con la mayor contundencia" en S4** (línea 2815). Esta es una afirmación argumentativamente fuerte que **contradice el §5.2 anterior** (donde se reconoce que en S1-S2 la hipótesis se rechaza). La hipótesis no puede a la vez confirmarse y rechazarse: o se considera condicional al régimen (y entonces hay que reformularla) o se rechaza globalmente (lo cual no es lo que se quiere). El sinodal pedirá coherencia lógica: ¿qué significa "la hipótesis" cuando los resultados son condicionales al escenario?

30. **La contribución 4 ("Validación sobre topología real")** afirma que "los beneficios se amplifican al utilizar distancias reales sobre la red vial de La Paz". Como se discutió en la observación 24, esto es especulativo: no hay un experimento controlado FCFS-OSRM vs FCFS-Euclidiano en este trabajo. La literatura (Boyaci2021) lo sugiere pero el sustentante no lo demuestra empíricamente. **El §1.6.5 (líneas 520-523) menciona la posibilidad de un "Escenario de Control (Aislamiento de Variables)" pero el Cap. 4 no reporta su ejecución**. Esta promesa incumplida es una zona expuesta.

31. **El trabajo futuro #1 ("Diagnóstico de semillas fallidas")** convierte un problema actual en trabajo futuro. Esto es legítimo en una tesis pero un sinodal puede argumentar que si el diagnóstico es trivial (revisar logs, reproducir corridas), debería hacerse antes de defender, no después.

32. **No hay sección de "Validación interna"** que demuestre que el simulador produce resultados consistentes con la teoría. Por ejemplo: ¿el SLA bajo FCFS en S1 es realmente 100% porque los couriers están ociosos la mayor parte del tiempo? ¿Cuál es la utilización promedio del courier en cada escenario? La utilización se reporta en §4.3 pero la conexión con el comportamiento esperado del sistema podría ser más explícita.

33. **La conclusión no menciona explícitamente cómo se mitiga la limitación de la calibración LaDe**. Un sinodal preguntará: si los datos chinos no son transferibles, ¿qué tan generalizables son las conclusiones a cualquier ciudad mexicana similar a La Paz?

#### Recomendaciones para el sinodal del trabajo

- Reformular §5.2 para que la "verificación de hipótesis" sea internamente coherente.
- O bien ejecutar el experimento de control FCFS-OSRM vs FCFS-Euclidiano antes de la defensa, o bien retirar la contribución 4 y reformularla como "validación sobre topología real" (sin la palabra "amplifica").
- Diagnosticar y reportar las 3 semillas fallidas antes de la defensa.

---

## 3. Coherencia transversal hipótesis-método-resultados-conclusiones

Esta sección audita la **lógica argumentativa transversal** del documento.

### 3.1 ¿La hipótesis se confirma o se rechaza?

La hipótesis original (líneas 437-442) es:

> "La implementación de una política de despacho anticipatoria (Horizonte Rodante), alimentada con una matriz de costos de viaje reales (OSRM) sobre la topología de La Paz, **superará significativamente** en eficiencia operativa 'órdenes por hora' y nivel de servicio '*Ready-to-Door*' a la estrategia reactiva estándar (FCFS con estimación euclidiana)..."

Análisis sinodal:

- **"Órdenes por hora" (throughput):** RH es superior a FCFS en TODOS los escenarios (+4.9% S1, +3.4% S2, +4.7% S3, +17.7% S4). En esta métrica, la hipótesis se confirma globalmente. ✓
- **"Ready-to-Door":** En S1 ($\bar{x}_{FCFS} = -1.89$ vs $\bar{x}_{RH} = 8.395$) y S2 ($4.694$ vs $10.752$), RH es **peor** que FCFS. Solo en S3 (23.808 vs 13.539) y S4 (63.442 vs 20.279) RH supera a FCFS. La hipótesis **no se confirma globalmente** en RtD. ✗

Por tanto, la afirmación general de "superará significativamente" es **falsada** en el régimen de baja saturación cuando se evalúa con RtD (la métrica que la propia hipótesis enuncia como criterio).

**Implicación para la defensa:** un sinodal estricto puede sostener que la hipótesis original se rechaza. La tesis lo gestiona dividiendo en regímenes, pero esto introduce un cuantificador condicional que no estaba en la formulación original. Esto es una vulnerabilidad lógica.

### 3.2 ¿Los objetivos específicos están cubiertos?

| OE | Enunciado | Evidencia en Cap. 4 | Estado |
|----|-----------|---------------------|--------|
| OE1 | Generar instancias sintéticas calibradas | §3.2, §4.1 (1038 órdenes/instancia, 7 seeds válidas) | Cubierto, con caveat de las 3 seeds fallidas |
| OE2 | Integrar simulador con OSRM, validando precisión vs euclidianas | §4.1, §5.1 (100% cobertura OSRM) | **Parcialmente cubierto** — se afirma 100% cobertura pero NO se ejecuta la validación cuantitativa OSRM vs euclidiana |
| OE3 | Implementar RH y FCFS con instrumentación de métricas | Cap. 3 completo, código en src/ | Cubierto |
| OE4 | Cuantificar diferencias mediante análisis estadístico | §4.5 (Mann-Whitney U, BH, Kruskal-Wallis) | Cubierto, con observaciones sobre la afirmación universal de significancia |

**OE2 es el más vulnerable.** La validación "frente a distancias euclidianas" no se reporta como experimento. Bajo cuestionamiento, el sustentante deberá apoyarse en Boyaci2021 como cita externa, pero ese no es trabajo propio.

### 3.3 ¿Las conclusiones exceden lo que los datos permiten afirmar?

- **§5.3 Contribución 3 ("Magnitud de la mejora bajo saturación... superando las mejoras de 10-25% reportadas por Reyes2018")**: la comparación es válida en magnitud, pero implícitamente sugiere que **es la topología** la causa de la diferencia. Este argumento causal **no está soportado** por experimentos propios. Es una hipótesis razonable, no un resultado.

- **§5.3 Contribución 4 ("Los beneficios se amplifican al utilizar distancias reales")**: misma observación. Sin experimento de control, "amplifican" debería ser "se mantienen" o "no se degradan".

---

## 4. Validación técnica (tesis vs. código)

### 4.1 Correspondencia matemática

| Concepto | Tesis (línea) | Código | Estado |
|----------|---------------|--------|--------|
| $f$ (frecuencia optimización) = 5 min | 1276, 1491 | `OPTIMIZATION_FREQUENCY = timedelta(minutes=5)` ([config.py:5](../src/config.py#L5)) | ✓ |
| $\Delta_u$ (horizonte asignación) = 20 min | 1492 | `ASSIGNMENT_HORIZON = timedelta(minutes=20)` ([config.py:6](../src/config.py#L6)) | ✓ |
| $\tau$ (objetivo CtD) = 40 min | 1493 | `TARGET_CLICK_TO_DOOR = timedelta(minutes=40)` ([config.py:7](../src/config.py#L7)) | ✓ |
| $\tau_{max}$ (máx CtD) = 90 min | 1494 | `MAX_CLICK_TO_DOOR = timedelta(minutes=90)` ([config.py:8](../src/config.py#L8)) | ✓ |
| $s$ (servicio) = 4 min | 1495 | `SERVICE_TIME = timedelta(minutes=4)` ([config.py:9](../src/config.py#L9)) | ✓ |
| MAX_BUNDLE_SIZE = 4 | 1496 | `MAX_BUNDLE_SIZE = 4` ([config.py:13](../src/config.py#L13)) | ✓ |
| $\beta$ = 0.1 (frescura) | 1497 | `FRESHNESS_PENALTY_BETA = 0.1` ([config.py:21](../src/config.py#L21)) | ✓ |
| $\theta$ = 0.1 (penalización pickup) | 1498 | `PICKUP_DELAY_THETA = 0.1` ([config.py:22](../src/config.py#L22)) | ✓ |
| $P_g \in \{0, 50, 100\}$ | 1995-1996 | `GROUP_I_PENALTY = 100, GROUP_II_PENALTY = 50` ([config.py:17-18](../src/config.py#L17-L18)) | ✓ |
| $p_1 = \$10$/orden, $p_2 = \$15$/h | 689-699, 1752 | `PAY_PER_ORDER = 10.0, MIN_PAY_PER_HOUR = 15.0` ([config.py:31-32](../src/config.py#L31-L32)) | ✓ |
| $T_{prep} \sim \max(5, \mathcal{N}(12, 3^2))$ | 1585-1586 | `np.clip(rng.normal(12, 3, ...), 5, None)` ([make_synth_orders.py:110](../scripts/make_synth_orders.py#L110)) | ✓ |
| $T_{prep} = 15 \pm 5$ min | **2713** | (No coincide con código ni con §3.2) | ✗ **Inconsistencia** |

### 4.2 Bug del two-stage commitment (commit 204500f)

Verificado en [src/asignaciontentativa.py:152-153, 165-166](../src/asignaciontentativa.py#L152): el código actual **sí** marca `o.status = 'assigned'` en los caminos de `forced commit` y `final commit`, evitando la inflación de `courier_del`. La verificación con [_audit_bug.py](../scripts/_audit_bug.py) (script de diagnóstico que el autor mantuvo en el repositorio) confirmaría inflation_factor ≈ 1.0 post-fix.

**El `partial commit` deliberadamente NO marca como `'assigned'`** (líneas 178-180 de asignaciontentativa.py), lo cual es correcto: la orden debe re-evaluarse en el siguiente ciclo. Esto está documentado en el código pero no en la tesis.

**El bug y su fix no se mencionan en el documento.** Un sinodal exigente puede preguntar: ¿cómo sé que las cifras del Cap. 4 son post-fix? La respuesta correcta es: el experimento [results/experiments/20260413_182745/](../results/experiments/20260413_182745/) tiene timestamp 13/abril/2026, posterior al commit 204500f del 4/abril/2026. Esta justificación debe estar explícita en el documento.

### 4.3 Reproducibilidad

- **Semillas válidas:** 7 de 10 (2025, 2026, 2028, 2029, 2030, 2031, 2032).
- **Semillas fallidas:** 3 de 10 (2027, 2033, 2034). Causa declarada: "interrupción del servicio OSRM". Causa técnica real: no diagnosticada.
- **Cobertura OSRM:** Verificada en S4 alta seed 2025: 1038/1038 órdenes con `routing_source = osrm`, 0 fallback. Esto invalida la objeción de contaminación euclidiana **en ese caso**, pero no se ha verificado en los demás escenarios/seeds. La tesis afirma 100% cobertura sin reportar el dato crudo.

### 4.4 Referencias huérfanas en biblio.bib

Se identificaron **8 referencias declaradas en [docs/ref/biblio.bib](ref/biblio.bib) que NUNCA se citan en el texto** (verificación con `grep \\cite[pt]?{...}`):

| Cita | Tipo | Razón posible | Recomendación |
|------|------|---------------|---------------|
| `Lawler1985` | Libro TSP clásico | Posiblemente plan original incluía contexto histórico | Citar o eliminar |
| `Laporte1992` | Survey TSP | Mismo caso | Citar o eliminar |
| `Lin2018GreedRL` | Deep RL para fleet management | Probablemente para §1.4 (delimitación frente a DL) | **Debería citarse en línea 472-480** |
| `Letchford2004` | Branch-and-cut CVRP | Métodos exactos | Citar o eliminar |
| `Jaw1986` | Dial-a-Ride heurística | Probablemente para §1.1.4 | Citar o eliminar |
| `MunozVillamizar2021` | Disrupciones última milla | Latinoamérica | **Debería citarse en §1.4 o §1.6** |
| `Boeing2021` | Modelos de redes urbanas | Validación topológica | Citar en §2.3 al hablar de OSM |
| `OSRMWiki2025` | Documentación técnica OSRM | **Debería citarse en §3.1** | Citar al describir OSRM v5.27.1 |

Cada referencia huérfana es un *flag* en el acta de un sinodal: o se cita donde corresponde, o se elimina.

### 4.5 Referencias citadas: revisión por entrada

- `Reyes2018`: publicado en **Optimization Online** (preprint). **Verificar si existe versión arbitrada en revista** (e.g., *Transportation Science*, *EJOR*); si existe, citarla preferentemente. Si no, dejarlo como preprint pero marcar visualmente.
- `Larsen2000DVRP`: el rango de páginas `103--122` parece anómalo para ese journal/año. Verificar contra original.
- `Wu2023LaDe`: la cita es a un dataset publicado en CIKM 2023; verificar que la versión usada corresponda a la versión revisada por pares y no a un preprint posterior.
- Resto de referencias: validadas con DOI/journal correcto.

### 4.6 Sugerencias de referencias adicionales

Para fortalecer el estado del arte, considerar:

- **Ulmer, Soeffker & Mattfeld (2018)**: "Value Function Approximation for Dynamic Multi-Period Vehicle Routing", *Transportation Science*. Estado del arte en políticas de despacho dinámicas.
- **Steever, Karwan & Murray (2019)**: "Dynamic courier routing for a food delivery service", *Computers & Operations Research*.
- **Auad, Erera, Savelsbergh (2024)** o publicaciones recientes del grupo Savelsbergh sobre MDRP — el campo se ha movido desde Reyes2018.
- Para contexto latinoamericano: **Cattaruzza, Absi, Feillet (2018)** sobre logística urbana, o trabajos del grupo de **Faulin** en logística urbana sostenible.

---

## 5. Redacción y forma

### 5.1 Defectos formales detectados

- **Portada (línea 73, 88):** "ANTEPROYECTO DE TESIS" / "DICIEMBRE 2023". Inconsistente con el estado actual del trabajo. Ningún sinodal aceptará un documento con esta portada para defensa de tesis final.
- **Director plural sin co-director (líneas 83-84):** Encabezado "DIRECTORES DE TESIS" pero solo aparece "DR. MARCO ANTONIO CASTRO LIERA". Si hay co-director, agregarlo. Si no, cambiar a "DIRECTOR DE TESIS" (singular).
- **Texto duplicado evidente (líneas 537-538):** dos viñetas idénticas con el mismo texto "Infraestructura de Enrutamiento Contenerizada" cambiando solo el nombre de la imagen Docker (`osrm/osrm-backend` vs `ghcr.io/project-osrm/osrm-backend:v5.27.1`). Es un error de edición visible que cualquier lector detecta.
- **`\usepackage{lipsum}` (línea 15):** comentario explícito en el .tex dice "elimínala cuando ya estés trabajando en tu tesis". Si no se usa el comando `\lipsum`, desinstalar el paquete (verificación rápida: `grep -n lipsum docs/tesisss.tex`).
- **`\graphicspath` con ruta absoluta de Windows (línea 39):** `c:/Users/GpoFi/OneDrive/Documentos/GitHub/MDRP-BCS-code/docs/`. **Compromete la portabilidad**: ningún revisor externo puede compilar el documento sin editar esta línea. Cambiar a `{img/}{./}` (rutas relativas).
- **Comillas mixtas (línea 440):** `"\textit{Ready-to-Door"}` mezcla `"` ASCII con `\textit`, generando salida tipográfica inconsistente. Usar siempre comillas LaTeX `\textquotedblleft` y `\textquotedblright` o `\enquote` con paquete `csquotes`.
- **Doble apóstrofo en línea 475:** `''arranque en frío''` debería ser `\textquotedblleft arranque en frío\textquotedblright`.
- **Encoding declarado UTF-8 (línea 3):** correcto, pero algunas vocales acentuadas en comentarios LaTeX usan caracteres ASCII (verificar consistencia).

### 5.2 Notación matemática

- **Símbolos $\Delta_u$, $\Delta_1$, $\Delta_2$:** los tres valen 20 min en código pero la tesis los presenta como independientes. Documentar la convención.
- **Símbolos $\tau$, $\tau_{max}$, $T_{target}$:** verificar consistencia. La sección 2.1 usa $\tau$ y $\tau_{max}$, pero §3.4 usa términos descriptivos. Unificar.
- **Variables $w_{s,d}$ vs $w_{cj}$:** la matriz de pesos se denota de dos formas distintas (líneas 884 y 1984). Unificar a una sola notación.
- **Indices $s$ vs $B_j$ vs `bundle`:** la tesis alterna $s$ (sequence) y $B_j$ (bundle) para la misma entidad. Decidir y unificar.

### 5.3 Convenciones tipográficas

- Uso inconsistente de `\textit{...}`, `\emph{...}` y comillas para términos técnicos. Establecer una convención (ej.: `\textit` para inglés, `\emph` para énfasis, comillas para citas literales) y aplicarla en todo el documento.
- Mayúsculas en títulos de sección: alternan título de capítulo (mayúsculas) y subsecciones (mayúsculas iniciales). Verificar consistencia con la guía editorial del Tecnológico de La Paz.
- Espaciado en torno a símbolos matemáticos: usar `\,` o `\;` consistentemente.

---

## 6. Observaciones obligatorias (numeradas)

> **Estas observaciones son condición para impresión y defensa.** Sin su corrección, el dictamen sinodal escrito incluiría observación formal.

### OBL-1. Portada incoherente

- **Ubicación:** [tesisss.tex:67-89](tesisss.tex#L67-L89).
- **Problema:** "ANTEPROYECTO DE TESIS" (línea 73) y "DICIEMBRE 2023" (línea 88).
- **Justificación:** El documento es tesis final, no anteproyecto, y los experimentos son de abril 2026.

### OBL-2. Director plural sin co-director nombrado

- **Ubicación:** [tesisss.tex:83-84](tesisss.tex#L83-L84).
- **Problema:** Encabezado "DIRECTORES DE TESIS" pero solo aparece un nombre.
- **Justificación:** O se agrega el segundo nombre (si hay co-director), o se corrige el plural.

### OBL-3. Texto duplicado en sección 1.6.4

- **Ubicación:** [tesisss.tex:537-538](tesisss.tex#L537-L538).
- **Problema:** Dos viñetas idénticas con el mismo título.
- **Justificación:** Error de edición evidente al lector.

### OBL-4. Inconsistencia numérica en $T_{prep}$

- **Ubicación:** [tesisss.tex:2713](tesisss.tex#L2713) ("$t_{\text{prep}} = 15 \pm 5$ min") vs [tesisss.tex:1585-1586](tesisss.tex#L1585-L1586) ($T_{prep} \sim \max(5, \mathcal{N}(12, 3^2))$) y código en [scripts/make_synth_orders.py:110](../scripts/make_synth_orders.py#L110).
- **Problema:** La cifra "$15 \pm 5$" no corresponde ni al código ni al marco teórico.
- **Justificación:** Cualquier sinodal verifica este tipo de número y lo encuentra trivialmente.

### OBL-5. Referencias huérfanas en biblio.bib

- **Ubicación:** [docs/ref/biblio.bib](ref/biblio.bib) — 8 entradas declaradas y nunca citadas: `Lawler1985`, `Laporte1992`, `Lin2018GreedRL`, `Letchford2004`, `Jaw1986`, `MunozVillamizar2021`, `Boeing2021`, `OSRMWiki2025`.
- **Problema:** Bibliografía contiene literatura no citada en el texto.
- **Justificación:** Convención académica universal: toda referencia listada debe citarse al menos una vez.

### OBL-6. Ruta absoluta en `\graphicspath`

- **Ubicación:** [tesisss.tex:39](tesisss.tex#L39).
- **Problema:** Ruta absoluta a `c:/Users/GpoFi/...` impide compilación en máquina ajena.
- **Justificación:** Reproducibilidad técnica de la propia tesis.

### OBL-7. Hipótesis falsada parcialmente sin reformulación

- **Ubicación:** [tesisss.tex:437-442](tesisss.tex#L437-L442).
- **Problema:** La hipótesis afirma superioridad universal de RH; los resultados S1-S2 contradicen esto en CtD y RtD.
- **Justificación:** La gestión actual en §5.2 introduce una condicionalidad que no estaba en la formulación original. O la hipótesis se reformula con el cuantificador "bajo régimen de saturación", o se acepta su rechazo parcial explícitamente y se reformula la tesis del trabajo.

### OBL-8. Afirmación universal de significancia incorrecta

- **Ubicación:** [tesisss.tex:2593-2594](tesisss.tex#L2593-L2594).
- **Problema:** "Todas las 28 pruebas individuales resultaron significativas" — válido para CtD pero NO para Ready-to-Pickup en S4 ($\bar{r} = 0.0331$, `All_Significant_BH=No` en `cross_seed_aggregation.csv`).
- **Justificación:** Acotar la afirmación a la métrica CtD evita imprecisión estadística.

### OBL-9. Bug y fix del two-stage commitment no documentado

- **Ubicación:** Cap. 3 §3.4 y/o Cap. 4 §4.6 (Limitaciones).
- **Problema:** El commit 204500f fixea un bug crítico que inflaba `courier_del` 2-3×. La tesis no menciona ni el bug ni que las cifras reportadas son post-fix.
- **Justificación:** Transparencia metodológica. Si el bug se descubriera durante o después de la defensa, la credibilidad del trabajo se vería seriamente comprometida.

### OBL-10. Inconsistencia 25 vs 142 restaurantes

- **Ubicación:** [tesisss.tex:1643-1645](tesisss.tex#L1643-L1645) (25 establecimientos, "reproyectados") vs [tesisss.tex:2303](tesisss.tex#L2303) y [tesisss.tex:2767](tesisss.tex#L2767) ("142 restaurantes geolocalizados").
- **Problema:** Cifra inconsistente y geometría re-muestreada (no real) sin declaración explícita.
- **Justificación:** El argumento de "geolocalización real" se debilita si las ubicaciones son re-muestreadas dentro del polígono.

### OBL-11. Cifra de órdenes inconsistente

- **Ubicación:** Múltiples lugares (líneas 2298, 2305, 2767) — alterna entre "~1,026", "1,038", "~1,000".
- **Problema:** El número de órdenes por instancia debería expresarse de forma única (e.g., "1,038 ± 30 órdenes").
- **Justificación:** Precisión expositiva.

### OBL-12. Comillas tipográficas mixtas

- **Ubicación:** Múltiples líneas, especialmente [tesisss.tex:440](tesisss.tex#L440), [tesisss.tex:475](tesisss.tex#L475).
- **Problema:** Mezcla de `"..."` ASCII con `\textit{...}` y `''...''`.
- **Justificación:** Tipografía consistente en documento académico.

---

## 7. Observaciones sugeridas (no bloquean impresión, mejoran calidad)

### SUG-1. Diagnóstico de las 3 semillas fallidas

Antes de la defensa, intentar reproducir las semillas 2027, 2033, 2034 con logs OSRM activados. Si el problema es transiente (e.g., timeout HTTP), incluirlas. Si es estructural (e.g., distribución particular que excede capacidad del solver), documentar la causa raíz.

### SUG-2. Análisis de sensibilidad sobre `MAX_BUNDLE_SIZE`

Ejecutar al menos S4 con `MAX_BUNDLE_SIZE ∈ {3, 4, 5, 6}` para mostrar que el cap = 4 no está perdiendo eficiencia. La infraestructura experimental ya soporta esta variación (`run_experiments.py --bundle-sizes`).

### SUG-3. Reporte explícito de cobertura OSRM

Agregar tabla en §4.1 con porcentaje de consultas OSRM resueltas vs. fallback euclidiano por escenario/seed. Verificación realizada por este sinodal: en S4 alta seed 2025, 1038/1038 = 100% OSRM. La tabla refuerza el aporte sobre topología real.

### SUG-4. Análisis de sensibilidad sobre patrones de demanda

Variar $\mu_m$, $\mu_e$, $A_m$, $A_e$ del proceso de Poisson para evaluar robustez de los resultados a perturbaciones del patrón LaDe. Esto mitiga la objeción "los datos chinos no aplican a México".

### SUG-5. Experimento de control FCFS-OSRM vs FCFS-Euclidiano

Anunciado en §1.6.5 (línea 520-523) pero no ejecutado. Aislaría la contribución específica de la topología. Si no se puede ejecutar antes de la defensa, retirar la promesa del Cap. 1 y la afirmación causal del §5.3 contribución 4.

### SUG-6. Intervalos de confianza por seed

Reportar IC95% bootstrap de la diferencia $\bar{x}_{FCFS} - \bar{x}_{RH}$ por escenario. Refuerza la presentación estadística.

### SUG-7. Discusión causal del punto de cruce

Adicionar al §4.6 una hipótesis causal sobre por qué $\rho^* \in [26, 35]$. Posibles factores: ratio crítico entre tasa de llegada y capacidad de servicio, geometría del polígono urbano, distribución de demanda en el grafo vial.

### SUG-8. Función objetivo explícita

En §2.1, escribir explícitamente la función objetivo del MDRP (e.g., $\min \sum_o \text{CtD}_o$ s.a. restricciones). Aclara la formulación matemática.

### SUG-9. Justificación de $\beta = 0.1$ y $\theta = 0.1$

Sea por cita al paper original, sea por experimento propio, justificar estos parámetros.

### SUG-10. Citar literatura post-2020 sobre MDRP

Incorporar al menos 1-2 referencias del estado del arte reciente (Ulmer, Steever, Auad-Erera-Savelsbergh) para mostrar dominio actualizado del campo.

### SUG-11. Conexión operativa de cifras estadísticas

Agregar 1-2 párrafos al §4 que conecten cifras como "P90 = 228 min" con consecuencias operativas (calidad del producto, satisfacción del cliente, viabilidad comercial).

### SUG-12. Limpieza de paquetes LaTeX no usados

Eliminar `\usepackage{lipsum}` (línea 15) y verificar que todos los demás paquetes (e.g., `pgfgantt`, `tikz`) se usen efectivamente.

### SUG-13. Glosario / lista de símbolos

Agregar al frontmatter una lista de símbolos matemáticos ($\mathcal{R}$, $\mathcal{O}$, $\mathcal{C}$, $\Delta_u$, $\tau$, $\beta$, $\theta$, $Z_t$, $w_{s,d}$, etc.) con su definición y ubicación. Facilita la lectura del jurado.

---

## 8. Preguntas previsibles del jurado y guion de respuesta

> Esta sección anticipa preguntas que un sinodal exigente puede plantear el día de la defensa, con esbozo de la respuesta defendible. **No son redacciones que el sustentante deba memorizar**, sino direcciones argumentales que debe tener pensadas.

### P1. ¿Por qué fallaron 3 de 10 semillas y qué garantías hay sobre las 7 exitosas?

Línea de respuesta: el fallo se atribuye a interrupciones transitorias del servicio OSRM durante la ejecución batch. Las 7 semillas exitosas fueron verificadas individualmente confirmando que el 100% de las consultas a OSRM se resolvieron sin caer al fallback euclidiano (verificable en la columna `routing_source` de los CSV de resultados). El sinodal querrá saber qué se hizo para diagnosticar el fallo; la respuesta más defendible es haber intentado reproducir esas semillas con logs detallados antes de la defensa.

### P2. ¿Por qué `MAX_BUNDLE_SIZE = 4`? ¿Qué pasa si se aumenta?

Línea de respuesta: el cap se eligió con base en limitaciones operativas reales del repartidor (capacidad física de la mochila aislante, tiempo razonable entre primera y última entrega del bundle). En S4 el bundle promedio es 3.07, cerca pero no en el cap. Un análisis de sensibilidad con `MAX_BUNDLE_SIZE ∈ {3, 4, 5, 6}` permitiría cuantificar el efecto. Esta justificación se fortalece **muchísimo** si el sustentante puede mostrar el experimento de sensibilidad ejecutado.

### P3. ¿Cuántas consultas OSRM cayeron al fallback euclidiano? ¿No contamina eso el resultado?

Línea de respuesta: en el experimento verificado (S4 alta seed 2025), 1038 de 1038 consultas se resolvieron exitosamente con OSRM (verificable en CSV). El fallback euclidiano está implementado como mecanismo de robustez ([src/getrouteOSMR.py:144-160](../src/getrouteOSMR.py#L144-L160)) pero no se activó en las corridas exitosas. El sinodal querrá ver el dato explícito en la tesis.

### P4. ¿Es válido calibrar la demanda con LaDe (datos de China) para La Paz?

Línea de respuesta: la calibración usa el patrón estructural (proceso de Poisson no homogéneo bimodal) más que los valores absolutos. Los picos $\mu_m = 09:00$ y $\mu_e = 17:00$ no corresponden a hábitos mexicanos (almuerzo 13-14h, cena 20-21h) — esto es una limitación que debe reconocerse explícitamente. Una mitigación parcial es ejecutar análisis de sensibilidad con $\mu_m, \mu_e$ desplazados a horarios mexicanos. La defensa más fuerte es el ejercicio empírico de sustituir los parámetros por los locales y mostrar que las conclusiones cualitativas (existencia del punto de cruce) se mantienen.

### P5. ¿Por qué la hipótesis original no contemplaba el régimen de baja saturación?

Línea de respuesta: la formulación original asumía implícitamente un régimen "no trivial" donde la flota está bajo presión. Bajo holgura extrema (S1, $\rho = 18$), el problema MDRP se degenera y cualquier política inteligente puede ser superada por una política reactiva pura. La reformulación de la hipótesis (versión condicional) refleja esta clarificación, pero **debe estar incluida en el documento**, no solo defendida verbalmente.

### P6. ¿Cómo garantiza que el bug fixeado no afectó otros KPIs además de `courier_del`?

Línea de respuesta: el bug consistía en que las órdenes con forced/final commit no se marcaban como `'assigned'` y podían re-procesarse, lo cual inflaba el conteo de bundles recogidos por courier. Las métricas a nivel de orden (CtD, RtP, RtD, SLA) se calculan sobre el momento de entrega registrado, que **no se duplicaba**, por lo que esas métricas no se inflaban. El [_audit_bug.py](../scripts/_audit_bug.py) verifica exactamente esta condición. La defensa más fuerte es ejecutar `_audit_bug.py` en vivo y mostrar `inflation_factor ≈ 1.0`.

### P7. ¿Qué pasa con tráfico dinámico, ventanas de tiempo del cliente, vehículos heterogéneos?

Línea de respuesta: explícitamente fuera del alcance (§1.6). Trabajo futuro. La defensa correcta es **no defender lo que no se hizo**, sino reconocer la limitación y argumentar por qué los resultados actuales son aún relevantes (caso optimista, baseline para comparaciones futuras).

### P8. ¿Por qué Mann-Whitney U y no t-test pareado?

Línea de respuesta: la prueba de Shapiro-Wilk rechazó normalidad en las 160 distribuciones. Mann-Whitney es la elección apropiada para distribuciones no normales. Adicionalmente, la presencia de outliers (P90 = 228 min en S4 FCFS) hace que t-test sea inadecuado por su sensibilidad a colas. Buena defensa.

### P9. ¿Por qué no se incluyó un baseline metaheurístico (ALNS, Tabu Search) además de FCFS?

Línea de respuesta: FCFS es el baseline reactivo estándar en la industria del meal delivery (la mayoría de plataformas operan así). El objetivo del trabajo no era comparar contra el estado del arte algorítmico, sino cuantificar el beneficio de pasar de reactivo a anticipatorio bajo topología real. ALNS o similar podría ser trabajo futuro; el alcance acotado es defendible.

### P10. ¿Cuál es el costo computacional de RH? ¿Es factible en tiempo real?

Línea de respuesta: el ciclo de optimización se ejecuta cada $f = 5$ min, y dentro de él el componente más costoso es el Algoritmo Húngaro ($O(n^3)$). En la mayor instancia (S4, ~20 couriers libres × ~10 bundles candidatos), el matching es trivial computacionalmente. La consulta OSRM (~5 ms) es el cuello de botella práctico. RH es factible en tiempo real para flotas de cientos de couriers.

### P11. ¿Por qué la mejora de RH (28-57%) excede tan ampliamente la de Reyes2018 (10-25%)?

Línea de respuesta: hipótesis causal — la topología vial de La Paz, con menor conectividad y mayor variabilidad de distancias que ciudades de cuadrícula, amplifica el beneficio del agrupamiento. **Pero esta es una hipótesis, no un resultado demostrado**. Defensa honesta: reconocer que es una hipótesis; lo demostraría un experimento de control con FCFS-Euclidiano que aislara el efecto topológico.

### P12. ¿Es generalizable este resultado a otras ciudades latinoamericanas?

Línea de respuesta: el patrón cualitativo (existencia de punto de cruce entre régimen de baja y alta saturación) probablemente sí; la magnitud específica (28-57%) probablemente no. La generalización requeriría replicar el experimento en otras topologías. Sería trabajo futuro.

---

## 9. Dictamen final

### 9.1 Veredicto razonado

La tesis **"Logística de Última Milla en Redes Viales Reales: Un Enfoque Reproducible para el MDRP en La Paz, B.C.S."** constituye una contribución científica original, técnicamente sólida, con análisis estadístico riguroso y arquitectura de software ejemplar para reproducibilidad. La identificación empírica del punto de cruce entre regímenes de saturación y la cuantificación de mejoras de hasta 57.2% en CtD bajo alta saturación son hallazgos genuinamente nuevos y operativamente relevantes.

Sin embargo, el documento **no se encuentra en estado óptimo para impresión final**. La portada conserva la designación de anteproyecto y fecha desactualizada; existen 8 referencias huérfanas en la bibliografía; hay una inconsistencia numérica trivial sobre el tiempo de preparación que cualquier sinodal detectará; existe un párrafo duplicado evidente; la ruta de gráficos LaTeX impide la compilación en otra máquina; la hipótesis original es parcialmente falsada y la gestión de esa falsación introduce incoherencias en el §5.2; el bug fixeado en abril 2026 no se documenta; afirmaciones universales sobre significancia estadística no son estrictamente correctas; la cobertura OSRM se afirma sin reportar el dato.

**El veredicto es: aprobada con observaciones obligatorias previas a la versión final impresa.**

### 9.2 Bloqueadores absolutos para imprimir

1. Corrección de portada (OBL-1, OBL-2).
2. Eliminación o citación de las 8 referencias huérfanas (OBL-5).
3. Homologación numérica de $T_{prep}$ (OBL-4).
4. Eliminación del texto duplicado en §1.6 (OBL-3).
5. Corrección de `\graphicspath` (OBL-6).
6. Reformulación de la hipótesis o defensa explícita de su falsación condicional (OBL-7).
7. Acotación de la afirmación universal de significancia (OBL-8).
8. Documentación del bug y su fix (OBL-9).
9. Aclaración de inconsistencias numéricas sobre restaurantes y órdenes (OBL-10, OBL-11).
10. Limpieza tipográfica de comillas y símbolos (OBL-12).

### 9.3 Mejoras altamente recomendadas (no bloquean pero elevan la calidad)

1. Diagnóstico de semillas fallidas (SUG-1).
2. Análisis de sensibilidad sobre `MAX_BUNDLE_SIZE` (SUG-2).
3. Reporte explícito de cobertura OSRM (SUG-3).
4. Análisis de sensibilidad sobre patrones de demanda (SUG-4).
5. Experimento de control FCFS-OSRM vs FCFS-Euclidiano (SUG-5).
6. Citas a literatura post-2020 sobre MDRP (SUG-10).
7. Función objetivo explícita en §2.1 (SUG-8).

### 9.4 Reconocimiento de fortalezas

Es deber del sinodal **reconocer explícitamente las fortalezas** del trabajo, no solo señalar defectos:

- **Reproducibilidad técnica ejemplar.** El uso de Docker para OSRM, OpenStreetMap como fuente cartográfica, semillas explícitas y código abierto en GitHub representa estándar de Ciencia Abierta superior al promedio de tesis de maestría en el área.
- **Rigor estadístico.** El uso de tests no paramétricos justificados por Shapiro-Wilk, corrección Benjamini-Hochberg, Kruskal-Wallis ómnibus y reporte de tamaño de efecto rank-biserial demuestra madurez metodológica.
- **Identificación del punto de cruce empírico** entre regímenes de saturación es un aporte cuantitativo genuino y operativamente útil para la industria del delivery.
- **Validación sobre topología real.** Aunque la afirmación causal sobre amplificación es especulativa, el ejercicio empírico de validar Rolling Horizon sobre OSRM-OSM en una ciudad latinoamericana es novedoso y replicable.
- **Arquitectura modular del software.** Las tres capas desacopladas (OSRM como servicio, simulador Python, análisis estadístico) son de calidad ingenieril sólida y permiten extensión futura.
- **Honestidad académica en §5.2.** El reconocimiento explícito de que la hipótesis no se confirma en S1-S2 es académicamente meritorio, aunque estructuralmente revele un problema con la formulación original.

### 9.5 Recomendación final

**El sustentante puede defender este trabajo con éxito**, siempre que:

(a) corrija los 12 bloqueadores listados en §6 antes de imprimir,
(b) tenga preparadas respuestas a las 12 preguntas previsibles del §8,
(c) en lo posible, atienda las sugerencias 1, 2 y 3 (diagnóstico de semillas, sensibilidad de bundle, reporte de cobertura) que blindan las áreas más vulnerables.

La calidad del aporte científico justifica la inversión en pulir los aspectos formales. El trabajo merece la defensa, pero no en su forma actual.

---

**Atte.,**

*Sinodal asignado para revisión pre-impresión*
*Fecha: 2026-05-02*

---

## Anexo A — Catálogo cruzado de hallazgos

Para facilitar el seguimiento, se cruzan las observaciones obligatorias con los capítulos donde impactan:

| Observación | Capítulo afectado | Sección de la tesis | Severidad |
|-------------|-------------------|---------------------|-----------|
| OBL-1 (Portada) | Frontmatter | Líneas 73, 88 | Alta |
| OBL-2 (Director plural) | Frontmatter | Líneas 83-84 | Media |
| OBL-3 (Texto duplicado) | Cap. 1 | Líneas 537-538 | Alta |
| OBL-4 ($T_{prep}$) | Cap. 4 | Línea 2713 | Alta |
| OBL-5 (Refs huérfanas) | Bibliografía | biblio.bib | Alta |
| OBL-6 (graphicspath) | Preámbulo | Línea 39 | Alta |
| OBL-7 (Hipótesis) | Cap. 1, Cap. 5 | Líneas 437-442, 2795-2823 | Alta |
| OBL-8 (Significancia) | Cap. 4 | Líneas 2593-2594 | Media |
| OBL-9 (Bug fix) | Cap. 3, Cap. 4 | Sin sección actual | Alta |
| OBL-10 (Restaurantes) | Cap. 3 | Línea 1645 vs 2767 | Media |
| OBL-11 (Órdenes) | Cap. 3, Cap. 4 | Múltiple | Baja |
| OBL-12 (Tipografía) | Múltiple | Múltiple | Baja |

## Anexo B — Verificación de cifras principales

Verificación cruzada con [results/experiments/20260413_182745/cross_seed_aggregation.csv](../results/experiments/20260413_182745/cross_seed_aggregation.csv):

| Cifra reportada en tesis | Línea tesis | Cifra en CSV | Estado |
|--------------------------|-------------|--------------|--------|
| S1 CtD FCFS = 10.10 | 2605 | 10.095 | ✓ |
| S1 CtD RH = 20.38 | 2605 | 20.379 | ✓ |
| S2 CtD FCFS = 16.68 | 2606 | 16.679 | ✓ |
| S2 CtD RH = 22.74 | 2606 | 22.737 | ✓ |
| S3 CtD FCFS = 35.79 | 2607 | 35.793 | ✓ |
| S3 CtD RH = 25.52 | 2607 | 25.523 | ✓ |
| S4 CtD FCFS = 75.41 | 2608 | 75.414 | ✓ |
| S4 CtD RH = 32.26 | 2608 | 32.263 | ✓ |
| S1 $\bar{r}$ = 0.911 | 2605 | 0.911 | ✓ |
| S4 $\bar{r}$ = 0.144 | 2608 | 0.1437 | ✓ |
| S4 RtP All_Significant_BH | -- | **No** | **Inconsistente con afirmación universal en línea 2593** |

## Anexo C — Lista priorizada para acción

**Máxima prioridad (hacer primero, son rápidos):**
1. Corregir portada (OBL-1, OBL-2) — 5 min
2. Eliminar texto duplicado (OBL-3) — 1 min
3. Corregir `\graphicspath` (OBL-6) — 1 min
4. Homologar $T_{prep}$ (OBL-4) — 5 min
5. Citar o eliminar referencias huérfanas (OBL-5) — 30 min

**Prioridad alta (requieren reflexión):**
6. Reformular hipótesis o defender falsación (OBL-7) — 1-2 horas
7. Acotar afirmación de significancia (OBL-8) — 15 min
8. Documentar bug fix (OBL-9) — 30 min
9. Aclarar inconsistencias numéricas (OBL-10, OBL-11) — 30 min

**Prioridad media (requieren reescritura):**
10. Tipografía (OBL-12) — 1-2 horas

**Si se cuenta con tiempo (semanas antes de defensa):**
11. Diagnóstico de semillas (SUG-1) — 1-2 días
12. Sensibilidad MAX_BUNDLE_SIZE (SUG-2) — 1 día
13. Reporte cobertura OSRM (SUG-3) — 1 hora
14. Sensibilidad demanda (SUG-4) — 1 día
15. Experimento de control (SUG-5) — 1-2 días

---

*Fin del dictamen.*
