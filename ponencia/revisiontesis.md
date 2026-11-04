# Revisión adversarial de la tesis: objetivos, hipótesis y conclusiones

**Tesis revisada:** *Logística de última milla en redes viales reales: un enfoque reproducible para el MDRP en La Paz, B.C.S.* ([docs/tesisss.tex](../docs/tesisss.tex), 3,033 líneas; Caps. 4–5 reescritos con la campaña `20261023_233115_osrm`).

**Fecha:** 2026-10-24. **Lectores:** Alan (autor) y su director de tesis.

**Postura:** la de un sinodal que busca debilidades. Aquí no se discute si la tesis es buena: se buscan los puntos donde una conclusión dice más de lo que el diseño experimental permite.

**Cómo se sustenta cada hallazgo:**
- **[dato]**: verificado con el código o con los CSV crudos en esta revisión. Los fragmentos para reproducirlo están en el Apéndice.
- **[texto]**: contradicción o hueco dentro del propio documento.
- **[fuente]**: contrastado con el texto de la referencia en `docs/ref/*.txt`, o marcado *por verificar* si no hay texto local.

Las referencias "l.NNN" son líneas de `docs/tesisss.tex`.

> **Nota sobre las cifras.** Las cifras de S2–S4 deben considerarse **provisionales** hasta corregir el hallazgo A1 (C22 en [DATACHECKS.md](DATACHECKS.md) §1c), que puede reducir la ventaja de RH.

---

## 0. Estado de atención (2026-10-24)

**Decisión de Alan:** la tesis está en titulación, así que no se cambia el alcance. No se agregan políticas, ablaciones ni otra línea base, y los objetivos y la hipótesis del Cap. 1 se mantienen. Se hacen precisiones de redacción con los datos existentes y tres experimentos pequeños: E1 (robustez del reloj), E3 (control × κ) y E6 (tiempo de cómputo).

| Hallazgo | Estado | Dónde |
|---|---|---|
| A1 (reloj, C22) | Robustez evaluada con E1. El modelo por defecto no cambia: la variante se activa con la bandera `--update-first`, y sin ella se reproduce la campaña de forma idéntica. Los signos y el cruce se mantienen; las magnitudes de S2–S4 son una cota superior | §3.3, §4.6 (Tabla 4.7), limitaciones, Cap. 5 |
| A2 (línea base / ablación) | Redacción: "línea base reactiva", sin atribuir la mejora a un mecanismo; la ablación queda como trabajo futuro | §3.4, Cap. 5 |
| A3 (hipótesis) | Redacción: se rechaza en su forma general y se sostiene condicionalmente; RtD se agregó a la tabla de Wilcoxon; se aclara la productividad | §4.5, §5.2 |
| A4 (topología) | **E3 corrido**: el escalamiento por κ explica 62–84 % del efecto; el resto (p ≤ 0.004) se atribuye a la estructura de la red. Nueva Tabla 4.9 | §3.6, §4.7, contribución 4 |
| A5 (premisa geográfica) | Redacción: dominio de 8.4 km², P99 de κ = 1.90, sin rodeos por la ensenada, 13 pares con *snapping* | §4.7, limitaciones, trabajo futuro |
| A6 (preguntas sin responder) | Se reporta la degradación de RH (+10 % en S1, +29 % en S4) | §4.7 |
| A7 (citas) | Corregidas: Boyacı, Ichoua, Hildebrandt, Figliozzi, Jazemi, LaDe (paquetería), Ec. 2.1, horizontes (variante 7 de Reyes). Bibliografía: LaDe (el DOI anterior apuntaba a otro artículo), Hildebrandt 2022 56(4), Jazemi 13(24):13015 | Caps. 1–4, `biblio.bib` |
| B1–B3 (objetivos) | Redacción de la verificación en el Cap. 5 (hallazgo y dominio; "parametrizadas"; "diferencia" en lugar de "precisión") | §5.1 |
| B4 (fidelidad a Reyes) | Redacción en el OE3; validación con mdrplib como trabajo futuro | §5.1, trabajo futuro |
| B5 (estadística) | RtD, BH (24 pruebas), sin equivalencia formal en S1, nota sobre el piso de p | §4.5 |
| B6–B7 (guía práctica, magnitudes) | "En la configuración evaluada"; encuadre de iso-flota; S4 como ilustración del colapso | §4.5, contribuciones 2–3 |
| B8 (utilización, costo) | Redacción (capacidad ociosa; costo = p1 por construcción) | §4.3, §4.4, limitaciones |
| B9 (agrupamiento por viaje) | Columna Órd./viaje (1.93–2.80) en la Tabla 4.5 y en el texto | §4.2, §4.4, §4.7 |
| B10 (cómputo) | **E6 corrido.** Por día simulado, FCFS tarda 1.8–2.7 s y RH 57–80 s (menos de 0.6 s por época); memoria máxima de 194–221 MB (M1 Pro, 16 GB) | §4.8 (Tabla 4.10) |
| B11 (justificación) | Afirmaciones moderadas | §1.5 |
| B12 (reproducibilidad) | Pendiente de Alan: commit de resultados y fecha de portada | — |
| Marco del problema (los profesores no identificaban qué problema se atacaba) | **2026-10-26.** El §1.2 se reescribió en torno a un solo problema (coordinar o reaccionar según la saturación, en una ciudad media y con red real). Se agregaron la pregunta central y PI1–PI3 (§1.2.4), y su respuesta en el nuevo §5.1. La justificación científica (§1.5.1) se alineó. Objetivos e hipótesis sin cambios | §1.2, §1.5.1, §5.1; `PLAN.md` (marco del artículo) |
| Auditoría de citas (33 fuentes) | **2026-10-26.** Corregidos: metadatos de 9 entradas del .bib y 21 pasajes con atribuciones que las fuentes no sostienen. Se agregó la cita de Benjamini–Hochberg (1995). Detalle en la tabla siguiente | `biblio.bib`; Caps. 1–4 |
| C1 (Resumen/Abstract) | Pendiente: confirmar si el formato del ITLP lo exige | — |
| C2, C3, C7 | Corregidos ("cuatro características", `\ref`, paquetes eliminados) | — |
| C4–C6 | Parcial: CH y horizonte precisados; la tabla del estado del arte queda fuera de alcance | §2.3, §1.6 |

**Resultado de E1 (robustez del reloj, `--update-first`; corrida `20261024_updfirst_osrm`, 80/80 válidas).** El hueco entre viajes baja de un P1 de 8.4–8.9 min a 3.3–5.0 min.

| | S1 | S2 | S3 | S4 |
|---|---|---|---|---|
| ΔCtD principal → variante (min) | −1.38 → −6.77 | 20.64 → 5.40 | 63.13 → 26.27 | 151.24 → 97.52 |
| Cambio rel. del CtD principal → variante | +5.0 → +29.9 % | −36.7 → −14.6 % | −57.9 → −41.4 % | −67.2 → −63.0 % |
| ΔSLA principal → variante (pp) | −1.1 → −14.7 | +31.5 → +19.6 | +50.3 → +34.6 | +36.3 → +45.1 |
| Semillas en que gana RH (variante) | 0/10 | 10/10 | 10/10 | 10/10 |

**Lectura:**
- Los signos y el cruce entre S1 y S2 se mantienen.
- Las magnitudes de S2–S4 bajan, sobre todo en S2, y deben leerse como cota superior.
- En S1, la diferencia de SLA pasa a ser significativa a favor de FCFS (100 % frente a 85.3 %).
- El encuadre de iso-flota se modera: RH en S3 frente a FCFS en S2 da CtD similar (37.0 frente a 36.4 min, p = 0.23) y SLA mayor (+6.2 pp, p = 0.03).

**Resultado de E3 (control euclidiano × κ, 472.1 m/min; 80/80 corridas válidas):**

| | S1 | S2 | S3 | S4 |
|---|---|---|---|---|
| ΔCtD OSRM (min) | −1.38 | 20.64 | 63.13 | 151.24 |
| ΔCtD Euclid. 651 (min) | −4.53 | 11.50 | 37.09 | 123.30 |
| ΔCtD Euclid. × κ (min) | −2.46 | 17.83 | 53.17 | 146.70 |
| Fracción explicada por κ | 66 % | 69 % | 62 % | 84 % |
| p (OSRM vs × κ) | 0.002 | 0.002 | 0.002 | 0.004 |

**Auditoría de citas (2026-10-26).**
- Metadatos: los 40 DOI del .bib se contrastaron con Crossref.
- Contenido: cada afirmación citada se contrastó con el texto local de la fuente en `docs/ref/`. Para Steever se usó su resumen publicado; para Psaraftis, el título y los datos verificados en Crossref, porque el PDF está escaneado y no tiene texto.

| Fuente | Problema encontrado | Corrección |
|---|---|---|
| Lin2018 | DOI de otro artículo (TINET, Luo et al.); tercer autor "Zhaodong Xu" | DOI 10.1145/3219819.3219993; Zhe Xu |
| Lenstra1981 | DOI de otro artículo (Bodin y Golden) | DOI 10.1002/net.3230110211 |
| Larsen2000 | Entrada inexistente: "Jesper Larsen", artículo de C&OR con DOI que da 404 | Tesis doctoral de **Allan** Larsen, DTU, IMM-PHD-2000-73. Texto: se quitaron las comillas de una cita que no es textual y "taxonomía fundamental" |
| Boeing2021 | Vol. 53, pp. 482–508 | Vol. 54(3), pp. 519–535, 2022 |
| Psaraftis1980 | Título inexacto ("Approach for") | "A Dynamic Programming Solution to…". Texto: es de **un solo vehículo** |
| Reyes2018 | Tipo `@article` con revista "Optimization Online" | `@misc`, preprint |
| Dantzig1959, Ichoua2006, Muñoz2021 | Sin DOI, guiones Unicode, campo `article-number` que no se imprimía | Corregidos |
| Reyes (β) | "β = 0.1 corresponde al rango recomendado por Reyes": Reyes no publica un valor recomendado; lo muestrean en [0, 1] (Apéndice E) | "dentro del intervalo [0, 1] que exploran" |
| Reyes (4 % del óptimo) | Las soluciones óptimas son de Yildiz y Savelsbergh | Atribución agregada |
| Yildiz / Ulmer (§2.1) | "El simulador incorpora cotas duales (Yildiz) y ready time aleatorio (Ulmer)": falso. No se calculan cotas, y el despachador conoce el ready time al colocarse la orden, como en Reyes | Se explica en qué difieren y que no se adoptan |
| Yildiz (prep.) | Presentado como "estudio empírico"; μ = 12 y σ = 3 "observados" en instancias, sin verificar | Supuesto del generador, no calibrado |
| Muñoz-Villamizar | Citado para sostener que los patrones de consumo son "universales y transferibles"; el artículo dice lo contrario: el tipo de ciudad influye | Se presenta como limitación |
| Pereira (×3) | "Caja negra", "auditoría" y "condición necesaria para la validación científica" no están en el artículo; solo el costo de licencias y los tiempos de cómputo | La cita queda solo en lo que sí dice |
| Cordeau2007 | "Extendieron a Psaraftis y desarrollaron heurísticas": es una **revisión** | "Revisan la literatura del DARP" |
| Steever2019 | "Operadores reales… confirman empíricamente": es simulación inspirada en un servicio; el *virtual food court* es un pedido con varios restaurantes | Descripción corregida |
| Laporte2009 | No documenta *pickup and delivery*, *split delivery* ni tiempos de servicio variables | Esas variantes se citan con Cáceres-Cruz (sí las cubre) |
| Geisberger2008 | "Complejidad empírica O(√V log V)" no está en el artículo | Se quita; queda "<1 ms en Europa occidental (18 M nodos)" |
| Dijkstra1959 | Montículos de Fibonacci atribuidos a Dijkstra | "Mejora posterior al trabajo original" |
| Kuhn1955 / SciPy | SciPy 1.13 usa Jonker–Volgenant, no el Húngaro; el Húngaro original no es O(n³) | Precisado en los Caps. 2 y 3 |
| Jazemi2023 | "El componente más costoso" sin fuente | "Uno de los segmentos más exigentes" |
| Lenstra (TSP) | "NP-duro porque crece factorialmente" (error conceptual) | Reformulado |
| Benjamini–Hochberg | Se usa sin cita; el .bib tenía Benjamini–Yekutieli (2001), que es otro procedimiento | Se agregó BH (1995), verificado en Crossref |

Sin problemas: Boyacı, Ichoua, LaDe, Hildebrandt (ya corregidos el 24-oct), Cáceres-Cruz, Pillac, Figliozzi, Haklay, Ross, Ulmer 2018/2021 (ACA confirmado), Luxen–Vetter, Merkel, Hurlbert, Wilcoxon, Friedman y OSRM.

Pendiente menor:
- La tesis dice que OSRM se despliega con Docker (§1.5, §3.2). Las campañas de octubre usaron el binario nativo `osrm-routed` 5.27.1, misma versión y mismos índices.
- La lista de "tres primitivas" de OSM se cita con Haklay y Boeing, que solo mencionan nodos y vías.

---

## 1. Resumen ejecutivo: los 10 puntos de mayor riesgo en la defensa

| # | Punto débil | Daño potencial | Remedio |
|---|---|---|---|
| 1 | **A1.** El reloj de la simulación deja a cada repartidor 5–10 min parado después de cada viaje. FCFS hace un viaje por orden, así que pierde ≈31 % del turno en S4 y RH ≈18 % | Parte de la ventaja de RH puede ser un artefacto | Corregir el código y repetir la campaña (E1) |
| 2 | **A3.** La hipótesis, tal como está escrita, **se rechaza** (falla en S1), y sus dos métricas (órdenes/hora y RtD) no se probaron formalmente | El Cap. 5 la da por "verificada en S2–S4" | Redacción (§5) y tabla con prueba de RtD |
| 3 | **A4.** El control euclidiano no aísla la topología. Con la misma velocidad media solo cambia la carga, y la propia tesis lo admite (l.2860) | La contribución 4 y la premisa central del Cap. 1 | Control euclidiano × κ (E3) y redacción |
| 4 | **A7.** Boyacı et al. (2021), pilar del planteamiento, concluye que la aproximación euclidiana "da resultados aceptables". El rango 1.2–1.4 que se le atribuye es de Cole y King (1968) | Un sinodal que lea la cita desarma el planteamiento | Reescribir §1.1.10, §1.2.1, §2.3 y §4.6 |
| 5 | **A2.** No hay ablación. RH difiere de FCFS en 6 mecanismos, y FCFS elige repartidor por distancia **en grados**. Además, la tesis llama a FCFS "cota inferior" | No se puede atribuir la mejora al *bundling* ni a la "optimización global". Reyes et al. sí hacen ablaciones (variantes 16–18) | E2, E4 y redacción |
| 6 | **A5.** La "hostilidad topológica" (ensenada, rodeos en U, baja conectividad) no ocurre en los datos. El polígono mide 8.36 km², tiene P99 de κ = 1.90 y solo 0.49 % de pares con κ > 2 | El planteamiento promete algo que el experimento no ejercita | Redacción; medir la conectividad |
| 7 | **B4.** La implementación no se validó contra las **instancias públicas de Reyes** (`github.com/grubhub/mdrplib`, citado en el propio artículo de Reyes), y antes se encontraron 21 errores | "¿Cómo sabe que su RH es el de Reyes?" | Correr un subconjunto de mdrplib |
| 8 | **B1–B3.** El objetivo general y los OE1–OE2 se dan por cumplidos por *actividad* (se corrió, se integró), no por evidencia ("calibradas", "precisión") | Verificación de objetivos débil | Redacción (§5) |
| 9 | **B6–B7.** La "guía práctica" (cruce en ρ ≈ 18–26) depende de esta configuración. El −67 % de S4 viene de un FCFS colapsado (CtD de 225 min, 40 % sin entregar) | Contribuciones 2 y 3 sobredimensionadas | Usar el encuadre de iso-flota (§5) |
| 10 | **C1/B12.** No hay Resumen ni Abstract. La portada dice junio de 2026, pero las corridas son del 23 de octubre de 2026 y no están en git | Observaciones formales inmediatas | Agregar el resumen, corregir la fecha y versionar los resultados |

---

## 2. Matriz de trazabilidad: problema → objetivo → resultado → conclusión

| Planteamiento (Cap. 1) | Objetivo | Resultado (Cap. 4) | Conclusión (Cap. 5) | ¿Cierra? |
|---|---|---|---|---|
| §1.2.1: las distancias euclidianas subestiman 17–40 % y producen rutas infactibles (Boyacı) | OE2: precisión frente a euclidiana | κ = 1.38; control euclidiano | "La ventaja de RH en minutos es mayor con la red real" | ✗ La cita no dice eso (A7). κ mide diferencia, no precisión (B3). El control no aísla la topología (A4) |
| §1.2.2: la ensenada obliga a rodeos en U; arterias que hacen de cuello de botella | — | Polígono de 8.36 km² junto a la costa; P99 de κ = 1.90 | No se retoma | ✗ Premisa no ejercitada ni medida (A5) |
| §1.2.3: "se desconoce el grado de degradación" de RH en una topología hostil | Objetivo general | La degradación de RH existe en los datos (S1 27.55→30.31; S4 56.96→73.63 min) pero no se reporta | No se responde | ✗ (A6) |
| §1.5.1: ¿se sostiene la cercanía al óptimo de Reyes? | — | Sin cota ni óptimo | No se responde | ✗ (A6) |
| Demanda "calibrada" con LaDe | OE1 | Picos a las 09:00 y 17:00; 1,000 órdenes; 25 restaurantes; muestreo uniforme | "Todas generaron resultados válidos" | ✗ Calibración sin objetivo de referencia (B2) |
| Implementar RH (Reyes) y FCFS | OE3 | DC1–DC5 pasan | "Se verificó la integridad" | ◐ Hay consistencia, pero no fidelidad a Reyes (B4) |
| Significancia de las mejoras | OE4 | Wilcoxon, IC, r, Friedman | p = 0.002 en S2–S4 | ◐ Solo se prueban CtD y SLA, no RtD; S1 se declara "equivalente" sin margen (B5) |
| Hipótesis: RH supera en órdenes/hora y RtD | — | Órdenes/hora iguales en S1–S2; RtD sin tabla | "Se verifica en S2–S4" | ✗ (A3) |

---

## 3. Fichas de hallazgos

Cada ficha incluye la afirmación, por qué es débil, la pregunta probable del sinodal, la respuesta defendible **hoy** y el remedio.

### A. Críticos: amenazan las conclusiones centrales

#### A1. Artefacto del reloj que penaliza a FCFS (C22) [dato]

**Afirmación (l.2894–2896):** "un repartidor que termina su ruta queda disponible en la época siguiente".

**Por qué es débil:**
- En [src/main.py:124-166](../src/main.py#L124-L166) la asignación ocurre **antes** de la actualización de rutas ([src/main.py:170-211](../src/main.py#L170-L211)).
- Un repartidor que termina en c ∈ (t−5, t] se libera en la actualización de t y recibe ruta hasta t+5. El tiempo muerto es de 5 a 10 min por viaje, unos 7.5 min en promedio.
- **Evidencia:** el percentil 1 del hueco entre el fin de un viaje (última entrega + s_o/2) y la siguiente recolección es 8.35–8.90 min en *todos* los escenarios y políticas. Eso equivale a ≥ 5 min muertos + s_r/2 + el traslado.
- **Asimetría.** FCFS hace un viaje por orden; RH, 1.93–2.80 órdenes por viaje. Tiempo muerto estimado como porcentaje del turno (contando solo los viajes finales):

  | | S1 | S2 | S3 | S4 |
  |---|---|---|---|---|
  | FCFS | 17.9 % | 25.8 % | 30.7 % | 30.6 % |
  | RH | 9.3 % | 11.9 % | 14.4 % | 18.2 % |

- En S4, FCFS tiene 67.3 % de utilización más ≈31 % de tiempo muerto: el sistema queda saturado *en parte por el reloj*.

**Pregunta del sinodal:** "¿Cuánto de la ventaja de RH es del algoritmo y cuánto de la discretización?"

**Respuesta defendible hoy:** "La discretización afecta a ambas políticas, pero más a la que hace más viajes. En S1, aun con esta desventaja, FCFS gana por 1.4 min, así que el régimen de baja saturación no cambia. Las magnitudes de S2–S4 son una cota superior de la ventaja de RH y estoy repitiendo la campaña con la corrección."

**Remedio:** E1, la corrección y repetición de la campaña, y luego la actualización de las Tablas 4.2–4.7.

#### A2. Línea base débil y sin ablación [texto/dato]

**Afirmación (l.2012–2014):** "Estas simplificaciones hacen de FCFS una **cota inferior práctica**: cualquier mejora que la política RH logre sobre FCFS puede atribuirse directamente a los mecanismos de agrupamiento y optimización global."

**Por qué es débil:**
- "Cota inferior" tiene un significado matemático preciso y FCFS no lo es: es una línea base, nada más.
- RH difiere de FCFS en al menos 6 mecanismos a la vez:
  1. *bundling*;
  2. *matching* global con el algoritmo Húngaro;
  3. elección del repartidor con tiempos OSRM, cuando FCFS usa distancia euclidiana **en grados** (l.1963–1972);
  4. horizonte Δu;
  5. compromiso parcial o preposicionamiento;
  6. grupos de prioridad.
- Sin ablación, ninguna mejora se puede atribuir a un mecanismo concreto.
- Reyes et al. (2018) sí aíslan componentes: en su Tabla 3, las variantes 16 (compromiso de una etapa), 17 (sin grupos de prioridad) y 18 (sin *bundling*) (`docs/ref/reyes2018.txt` l.983–985). La tesis no lo replica.

**Pregunta del sinodal:** "Si le quito el *bundling* a RH, ¿sigue ganando? ¿Y si FCFS eligiera al repartidor con tiempos OSRM?"

**Respuesta defendible hoy:** "La comparación es entre políticas completas, no entre mecanismos. No atribuyo la mejora a un componente específico." Para poder decir esto hay que retirar la frase de la l.2012–2014.

**Remedio:**
- Texto: sustituir "cota inferior" por "línea base reactiva" y quitar la atribución.
- Experimentos: E2 (RH con B_max = 1) y E4 (FCFS que elige repartidor por tiempo OSRM).

#### A3. La hipótesis se rechaza en su forma general y sus métricas no se probaron [texto/dato]

**Hipótesis (l.443–446):** RH "superará significativamente en eficiencia operativa 'órdenes por hora' y nivel de servicio 'Ready-to-Door' a […] FCFS, demostrando la viabilidad de soluciones […] basadas exclusivamente en software de código abierto".

**Por qué es débil:**
1. **Es incondicional** y falla en S1, que es el escenario por defecto (`TARGET_ORDERS_PER_COURIER = 18`): FCFS es 1.38 min mejor en CtD (p = 0.0137) y también mejor en RtD (16.95 frente a 18.32 min). Partir la verificación en "regímenes" después de ver los datos es HARKing.
2. **"Órdenes por hora" no puede variar por diseño.** La tesis misma lo reconoce: con la misma flota y los mismos turnos, solo difiere por cobertura (l.2390–2392 y l.2654). Es idéntica en S1–S2, y el +66 % de S4 son las órdenes que FCFS **no entrega**, no productividad. La hipótesis eligió una métrica que el experimento no puede mover.
3. **RtD no está en ninguna tabla del Cap. 4 ni tiene prueba estadística.** Las cifras (−46.8 % a −71.0 %) aparecen solo en el Cap. 5 (l.2965–2966). Coinciden con `experiment_comparison.csv`, pero el lector no puede verificarlas en la tesis.
4. "Demostrando la viabilidad… código abierto" no es contrastable: ningún resultado podría refutarlo.

**Pregunta del sinodal:** "Su hipótesis dice 'superará'. En S1 no supera. ¿Se verifica o no?"

**Respuesta defendible hoy:** "En su forma general, no: se rechaza. Los datos sostienen una versión condicional: a partir de una saturación moderada, RH reduce significativamente el CtD y el RtD. La productividad por hora no discrimina entre políticas con este diseño, así que ese componente de la hipótesis no se pudo contrastar." Ver la redacción sugerida en §5.

**Remedio:**
- Agregar RtD (media y P90) a la Tabla 4.2 y a la Tabla 4.7 (Wilcoxon).
- Reescribir §5.2 (ver §5).

#### A4. La contribución 4 (topología) no aísla la topología [dato]

**Afirmación (l.2853–2865 y l.2993–2996):** "con la red real, la ventaja de RH en minutos es mayor que con distancias euclidianas en todos los escenarios".

**Por qué es débil:**
- El control usa la **misma velocidad media** (651 m/min). Como la red alarga los viajes un 38 %, el control es simplemente un sistema **menos cargado**. La tesis lo reconoce: "El mecanismo es la carga efectiva" (l.2860).
- Entonces el resultado se reproduciría con distancia euclidiana × κ, que es exactamente el factor de conversión γ de Reyes que la tesis dice eliminar (l.1162–1164). El experimento no demuestra que la *estructura* de la red (sentidos, barreras, asimetría) importe más allá de un escalar.
- Boyacı et al. sugieren justamente multiplicar la distancia euclidiana por ≈1.3 (`Boyaci2021.txt` l.564–566).
- **Agravante:** en ambos brazos FCFS elige repartidor por distancia en grados, mientras RH pondera con tiempos de ruta. Con OSRM, la elección de FCFS ignora la red y la de RH no.
- Los resultados son mixtos: en S4 el cambio relativo es igual (p = 0.084) y en SLA hay signos mixtos.

**Pregunta del sinodal:** "Si multiplico la distancia euclidiana por 1.38, ¿obtengo lo mismo? Si sí, ¿para qué OSRM?"

**Respuesta defendible hoy:** "El control mide el efecto de la longitud real de los viajes, que es la principal consecuencia de la red. Separar la longitud de la estructura requiere un control euclidiano escalado por κ, y lo reporto como trabajo pendiente." OSRM sigue siendo valioso: da κ medido, no supuesto, y tiempos por par, no un promedio.

**Remedio:**
- E3: control euclidiano a 651/1.38 ≈ 472 m/min.
- E4: FCFS con tiempos OSRM.
- Reescribir la contribución 4 como "se cuantificó κ = 1.38 y se mostró que ignorarlo subestima la carga y los tiempos de ambas políticas".

#### A5. La premisa geográfica no se ejercita ni se mide [dato]

**Afirmación (l.387–402):** la ensenada obliga a "rodeos extensos (en forma de U)"; dependencia de pocas arterias; "baja conectividad" (l.410).

**Por qué es débil:**
- El polígono de muestreo es un cuadrilátero de **8.36 km²** cuyo lado noroeste sigue la costa (`scripts/make_synth_orders.py` l.34–38). Ningún par cruza la ensenada.
- Los datos de κ no muestran rodeos en U: P99 = 1.90, solo 0.49 % de pares con κ > 2 y 2.1 % con κ > 1.8.
- κ = 1.38 queda *dentro* del rango típico de 1.2–1.4. No demuestra que La Paz sea atípica.
- La "baja conectividad" nunca se mide: ni densidad de intersecciones, ni grado medio de los nodos, ni centralidad. La tesis ya cita a Boeing (2021, OSMnx), que permite medirlas.
- **Calidad del grafo:** 13 pares tienen κ < 1 (mínimo 0.13), lo cual es imposible físicamente. Indica puntos ajustados (*snapped*) lejos de la vía. El OE2 prometía "validar la conectividad del grafo vial" y no se hizo.

**Pregunta del sinodal:** "Muéstreme un pedido de su experimento que rodee la ensenada."

**Respuesta defendible hoy:** "El dominio experimental es el centro urbano. La ensenada motiva el uso de redes reales, pero no se ejercita en estas instancias."

**Remedio:**
- Moderar el §1.2.2.
- Reportar métricas de conectividad del grafo (OSMnx) y la distancia de *snapping* que devuelve OSRM (`waypoints[].distance`).
- Excluir o explicar los 13 pares con κ < 1.
- Trabajo futuro: un polígono que incluya El Centenario y Chametla, o el área urbana completa.

#### A6. Las preguntas de investigación del Cap. 1 no se responden [texto]

**Afirmaciones:**
- l.409–410: "se desconoce el grado de degradación que sufren estas políticas".
- l.461–463: "validar si las eficiencias reportadas en la literatura (cercanas al óptimo) se sostienen".

**Por qué es débil:**
- No se calcula ninguna cota ni brecha de optimalidad.
- La degradación de RH al pasar de euclidiano a OSRM está en los datos pero no se reporta: CtD de RH 27.55→30.31 min en S1 y 56.96→73.63 min en S4.

**Pregunta del sinodal:** "Usted preguntó cuánto se degrada RH. ¿Cuánto?"

**Respuesta defendible hoy:** reportar esa degradación (+10 % en S1 y +29 % en S4 en el CtD medio de RH) y reconocer que la cercanía al óptimo no se evaluó.

**Remedio:** agregar un párrafo en §4.6 y en §5.1. La cota de Yıldız y Savelsbergh (2019), ya citada, queda como trabajo futuro.

#### A7. Citas que no dicen lo que la tesis afirma [fuente, verificado en `docs/ref/`]

| Cita en la tesis | Lo que dice la fuente | Gravedad |
|---|---|---|
| **Boyacı 2021** (l.367–375, 383–385, 1047–1049, 2822): "tras analizar 96 instancias en 12 ciudades, determinaron que las rutas son entre un 17 % y un 40 % más largas"; "advierten que […] resulta frecuentemente en rutas operativamente infactibles" | Las 96 instancias y 12 ciudades son correctas. El rango **1.2–1.4 es de Cole y King (1968)**, citado en sus antecedentes (l.157–159), no un hallazgo propio, y el "17 %" no aparece. **Su conclusión es la contraria:** "on the whole, using Euclidean distances instead of real road distances gives acceptable results" (l.511–514). La infactibilidad solo se advierte para **problemas con ventanas de tiempo estrechas** (l.521–568) | **Crítica.** Es el pilar del planteamiento. Se puede rescatar: el MDRP sí tiene urgencia y ventanas de tiempo, que es justo el caso donde Boyacı advierte riesgo. Pero la cita debe decir eso |
| **Ichoua 2006** (l.291–297): "dial-a-ride dinámico"; "mejoras de hasta el 29 % […] y entre 4–16 %" | Es un problema de **despacho de vehículos en tiempo real**, no *dial-a-ride*. Las reducciones van de 3.4 % a 29.0 % (no servidos) y de **2.0 % a 16.0 %** (tiempo + retraso), con **promedios de 9.0 % y 4.2 %** (l.1409–1413) | Media: el rango está mal y se omiten los promedios. La clave `Ichoua2006DDARP` también es engañosa |
| **Hildebrandt** (l.1272–1274): "demuestran que la estimación precisa del ETA es un predictor más fuerte de la satisfacción" | Lo **citan** de Thompson et al. (1996) y Davis y Heineke (1998) (l.34–36); no lo demuestran | Media: cambiar "demuestran" por "señalan, citando a…". El año en la bibliografía es 2021, pero la versión publicada es Transp. Sci. 56(4), 2022 |
| **Figliozzi 2007** (l.459–460): "advierte que las aproximaciones lineales distorsionan significativamente los costos de viaje" | Trata sobre la eficiencia de *tours* comerciales urbanos con **aproximaciones continuas** (Daganzo), no sobre el error euclidiano | Media: la cita no sostiene la frase |
| **Jazemi 2023** (l.182–185): "la última milla puede representar entre el 30 % y el 60 % del costo" | No encontré "30 %" ni "60 %" en el texto local | *Por verificar.* Si no aparece, citar la fuente primaria |
| **Ec. 2.1** (l.681–700): objetivo ponderado α₁·CtD + α₂·Pago + α₃·no entregadas, atribuido a Reyes y Ulmer | Reyes usa un **objetivo de servicio jerárquico**: primero entregar casi todo y luego minimizar el CtD (l.963 y l.989–990). No aparece ninguna suma ponderada | Media: presentarla como formulación propia "inspirada en" |
| **Parámetros "por calibración empírica"** (l.874): f = 5 y Δu = Δ1 = Δ2 = 20 | Coinciden con la **variante 7 de la malla de Reyes** (l.974). Su configuración por defecto es f = 5 y Δ = 10 (Tabla 3, l.966) | Media: decir de dónde salen. "Calibración" implica un proceso que no se documenta |
| **LaDe** (l.1221 y l.1718): picos de "almuerzo y cena" y rango de 2–5 km | LaDe (Wu et al., CIKM'23) es un conjunto de datos de **paquetería** de última milla (Cainiao), no de comida | *Por verificar* el contenido exacto (sin texto local). Si se confirma, los picos y distancias "de comida" no tienen respaldo |
| **Lin2018GreedRL** (l.478): métodos de aprendizaje profundo para entrega | Lin et al. (KDD'18) trata de gestión de flotas de *ride-hailing* (DiDi) con aprendizaje por refuerzo multiagente. "GreedRL" es otro trabajo | Baja-media: la delimitación frente a aprendizaje profundo descansa en una sola cita, de 2018 y de otro dominio |

---

### B. Mayores: objetivos verificados por actividad, no por evidencia

#### B1. Objetivo general [texto]
- **Verificación actual (l.2912–2917):** se cumple porque "se ejecutaron 80 corridas válidas […] y se cuantificaron las diferencias en 21 KPIs".
- **Debilidad:** "evaluar" es un verbo autocumplido; cualquier ejecución lo satisface.
- **Pregunta:** "¿Qué *resultado* demuestra que cumplió el objetivo?"
- **Remedio:** enunciar el hallazgo y su dominio de validez (ver §5).

#### B2. OE1: "instancias sintéticas **calibradas** […] garantizando la validez geoespacial" [texto/fuente]
- **Debilidades:**
  - No hay objetivo de calibración porque no existen datos de La Paz; los parámetros están fijados, no calibrados.
  - LaDe probablemente sea de paquetería (A7).
  - Los picos a las 09:00 y 17:00 no son horarios locales; la tesis ya lo reconoce.
  - El volumen de 1,000 órdenes al día y los 25 restaurantes no se justifican, y las coordenadas reales de los restaurantes se descartan (l.1739–1745).
  - La "validez geoespacial" se reduce a caer dentro de un polígono de 8 km², y hay 13 pares anómalos.
  - La conclusión del OE1 (l.2921–2925) habla de corridas válidas, no de calibración.
- **Pregunta:** "¿Contra qué calibró?"
- **Remedio:** cambiar "calibradas" por "parametrizadas con valores de la literatura", y documentar el origen de cada parámetro. Como experimento opcional, sensibilidad a 50 y 100 restaurantes y a volúmenes de ±30 %, porque el *bundling* depende de cuántas órdenes por restaurante caen en 20 min.

#### B3. OE2: "validando la conectividad del grafo vial y la **precisión** de los tiempos de viaje frente a distancias euclidianas" [texto]
- **Debilidades:**
  - La precisión exige una verdad de referencia, como trazas GPS o una muestra de Google o HERE. κ mide la *diferencia* entre dos modelos, no la exactitud de ninguno.
  - El perfil es `car.lua` (automóvil), mientras que los repartidores van en moto o bicicleta.
  - 39.1 km/h a flujo libre y sin congestión es optimista para el centro de La Paz.
  - La conectividad no se validó (A5).
- **Remedio:** cambiar "precisión" por "diferencia". Opcional: comparar ≈50 pares contra una fuente externa y reportar el error.

#### B4. OE3: fidelidad a Reyes sin validación externa [dato/fuente]
- **Debilidades:**
  - Reyes publica sus instancias y un script de evaluación en **`github.com/grubhub/mdrplib`** (`reyes2018.txt` l.734–736). La tesis no reproduce ningún resultado publicado.
  - Desviaciones documentadas o encontradas respecto a Reyes:
    - m_r usa `min` en lugar de `max` (nota en l.895–898);
    - penalizaciones P_g = 100 y 50 que no están en Reyes;
    - θ resta minutos a un término en órdenes por hora ([src/bundling.py:105-113](../src/bundling.py#L105-L113)), así que su escala es arbitraria;
    - Z_t con techo;
    - `MAX_TARGET_BUNDLE_SIZE = 5` es mayor que B_max = 4;
    - el *matching* solo considera repartidores ociosos.
  - La auditoría previa encontró 21 errores (C1–C21). DC1–DC5 comprueban **consistencia** (nada se entrega antes de estar listo), no **corrección** (que RH sea el de Reyes).
- **Pregunta:** "¿Cómo sabe que no quedan errores?"
- **Respuesta defendible hoy:** "Por las verificaciones automáticas, la temporización compartida (`schedule.py`) y la auditoría documentada en DATACHECKS.md. La validación contra mdrplib es el siguiente paso."
- **Remedio:** correr 2–3 instancias de mdrplib con su script de factibilidad y agregar pruebas unitarias de `schedule.py`.

#### B5. OE4: estadística [dato/texto]
- Con n = 10, p = 0.002 es el **piso** de Wilcoxon y r = ±1 solo indica que todas las semillas tienen el mismo signo. El p-valor no aporta más que eso; la evidencia real está en el IC y en la magnitud.
- No se justifica por qué n = 10, por ejemplo con un objetivo de ancho de IC.
- **S1 "prácticamente equivalentes"** (l.2559 y l.2794) con una diferencia significativa (p = 0.0137). Afirmar equivalencia requiere un margen definido de antemano y una prueba TOST.
- La corrección de Benjamini–Hochberg "se mantiene" (l.2786–2787), pero no se dice sobre qué familia de pruebas ni se muestran los p ajustados.
- Friedman entre escenarios es trivialmente esperable, porque el escenario es el factor de diseño.
- Solo se prueban 2 de los 21 KPI, y RtD (de la hipótesis) no está entre ellos.
- **Dos "cambios relativos" para lo mismo:** S1 +4.8 % en la Tabla 4.2 frente a +5.0 % en la Tabla 4.8 (razón de medias frente a media de razones), sin explicación.
- **Censura:** el CtD se promedia solo sobre las órdenes entregadas, y FCFS deja 39.9 % sin entregar en S4. El sesgo se corrige para el SLA, no para el CtD.

#### B6. Contribución 2: la "guía práctica" no es transferible [texto]
- **Afirmación (l.2984–2988):** "con flotas holgadas basta un despacho reactivo, y por encima de ese umbral conviene coordinar".
- **Debilidades:**
  - El cruce ρ ≈ 18–26 depende de la forma de la demanda, del turno único de 12.5 h para toda la flota, del polígono de 8 km², de los 25 restaurantes, de s_r y s_o, de f y del artefacto A1.
  - La propia tesis atribuye la derrota de RH en S1 a su **redondeo hacia arriba de Z_t** (l.2710–2712 y l.2878–2880). Es una propiedad de esta implementación, no de la política.
- **Remedio:** acotar con "en esta configuración"; E5 (Z_t redondeado al entero más cercano en S1).

#### B7. Contribución 3: magnitudes en un régimen colapsado [dato]
- −67.3 % de CtD en S4 con FCFS en 224.9 min de media y 39.9 % sin entregar: ningún operador trabaja ahí. La magnitud refleja que la cola de FCFS es inestable (más el efecto de A1).
- **Encuadre más fuerte que la tesis no usa: comparación a igual flota.** RH con 29–30 repartidores (S3: CtD 45.4 min, SLA 57.6 %) es mejor que FCFS con 38–41 (S2: CtD 56.1 min, SLA 38.1 %). Es decir, **mejor servicio con ≈25 % menos repartidores**, que es la pregunta que le importa a un operador.
- **Remedio:** destacar S2 (2.06 órdenes por repartidor por hora, el régimen más realista) y el encuadre de igual flota. Esta cifra también debe recalcularse después de E1.

#### B8. Eficiencia y costo [dato/texto]
- **Utilización:** "menor utilización ⇒ atiende la misma demanda con menos tiempo" (l.2662 y l.2972–2974). Con la flota fija eso es **capacidad ociosa**, no ahorro. Solo se vuelve ahorro si se reduce la flota, que es justo el encuadre de B7.
- **Costo degenerado:** p1 = $10 por orden y p2 = $15/h, muy por debajo del salario mínimo en México. El piso solo actúa en S1 (≈60 % de los repartidores), y en S2–S4 el costo por pedido es igual a p1 por construcción. La familia de KPI de costo no aporta información.
- **Remedio:** usar parámetros de pago realistas y justificados, o declarar el costo fuera de alcance.

#### B9. Tamaño de agrupamiento mal reportado [dato]
- l.2564: "consolida en promedio 2.54 órdenes **por viaje**". El 2.54 es una media **ponderada por orden**, el campo `bundle_size` de las órdenes entregadas.
- La media por viaje es **1.93 / 2.17 / 2.42 / 2.80** en S1–S4.
- **Remedio:** reportar ambas medidas en la Tabla 4.5 y corregir las l.2564 y 2878.

#### B10. "Computacionalmente ligero / servidores económicos / 8 GB de RAM" [dato]
- **Afirmación (l.482 y l.550):** el sistema es ligero y corre en hardware de consumo.
- **Debilidades:**
  - La tesis no reporta ningún tiempo de cómputo.
  - Las columnas `FCFS/RH Time (s)` valen 0.00 en la corrida OSRM (C23).
  - El control euclidiano sí registra 6.5–16.7 s por día simulado para RH, pero ese dato no aparece en la tesis.
  - En una Maestría en Sistemas Computacionales el sinodal preguntará por el tiempo por época, la escalabilidad y la memoria.
- **Remedio:** E6, que registra el tiempo por corrida y por época, y una tabla de desempeño computacional.

#### B11. Justificación sin sustento [texto]
- Afirmaciones sin cuantificar ni evidencia (l.470–474):
  - el ahorro frente a Google Maps o Mapbox;
  - la "soberanía tecnológica";
  - "competir con plataformas transnacionales";
  - "generar datos para entrenar IA" (l.483–484).
- **"En La Paz no existen registros previos de rutas y pedidos"** (l.478–479): en La Paz operan plataformas de entrega. El problema es que el investigador no tiene **acceso** a sus datos, no que no existan.
- **Remedio:** moderar estas frases o cuantificar el costo de la API comercial para el volumen simulado.

#### B12. Reproducibilidad, que está en el título [dato]
- Las corridas citadas (`20261023_233115_osrm` y `20261023_232220_euclid`) **no están versionadas** en git.
- La campaña final usó `osrm-routed` nativo (macOS ARM), no la imagen Docker sobre la que descansa el argumento de reproducibilidad (§1.6.3 y §3.1). El Cap. 4 lo aclara, pero no hay prueba de equivalencia, como comparar una muestra de rutas entre ambos.
- La portada dice **junio de 2026** y los identificadores de corrida dicen 23 de octubre de 2026.
- **Remedio:**
  - versionar los resultados, con una etiqueta de git o un DOI de Zenodo;
  - crear un script que reproduzca todo con un solo comando;
  - comparar una muestra de rutas entre Docker y la versión nativa;
  - corregir la fecha.

### C. Formales y moderados

- **C1.** No hay **Resumen ni Abstract**, agradecimientos ni dedicatoria. Revisar los lineamientos de titulación del posgrado del TecNM.
- **C2.** "Integra **cinco** características estructurales" (l.327), pero la lista tiene 4 (l.336–352).
- **C3.** "Sección 2.1.5" (l.1031) debería ser 2.1.6, *Variantes del entorno operativo*. Hay muchas referencias numéricas escritas a mano ("Sección 3.5", "§2.4.1"): conviene sustituirlas por `\ref`.
- **C4.** **Vigencia de la literatura.** De unas 42 referencias, solo 9 son de 2021 en adelante y ninguna de 2022, 2024 o 2026. Falta una **tabla comparativa del estado del arte** (método, red vial, datos, línea base). *Por verificar:* trabajos previos que ya usan redes viales reales en entrega de comida, como Ulmer et al. (2021) en Iowa City, debilitarían la "brecha" declarada.
- **C5.** La justificación de *Contraction Hierarchies* habla de "grafos con millones de nodos" (l.1088–1095), pero el área urbana tiene unos 10⁴ nodos y Dijkstra bastaría a esa escala. El sinodal puede preguntar por qué CH es necesario. Hay una buena respuesta: el número de consultas por época, que es O(|C|·|S|), más el uso de la caché.
- **C6.** Diseño experimental:
  - turno único de ≈12.5 h para toda la flota, cuando Reyes usa turnos escalonados;
  - "horizonte configurable (10–20 min)" (l.521), aunque se fijó en 20;
  - el eje de sensibilidad |B| que se anuncia en §3.6.6 no se ejecutó.
- **C7.** Quedan restos de la plantilla: `lipsum` ("recuerda eliminarla") y `pgfgantt` en el preámbulo.

---

## 4. Lo que sí está bien

Esto también conviene decirlo en la defensa, con estos argumentos:

1. **Diseño pareado bien hecho:** misma instancia, misma flota y misma semilla. La inferencia se hace a nivel semilla, evitando la pseudorreplicación, y se citan las fuentes (Hurlbert, 1984).
2. **Se reportan IC y tamaño de efecto**, no solo p-valores.
3. **Hay un experimento de control** y **circuidad medida**, no supuesta.
4. **Verificaciones automáticas de integridad** (`check_results.py`): nada se entrega antes de estar listo, no hay entregas dobles y no se usa el respaldo euclidiano.
5. **La auditoría está documentada.** Se encontraron y corrigieron 21 errores, con su evidencia (DATACHECKS.md). Pocas tesis se auditan hasta el código.
6. **Las limitaciones se declaran:** picos de LaDe, muestreo uniforme, red estática y SLA calculado también sobre todas las órdenes.
7. **Código y red vial abiertos**, con la versión de OSRM fijada.

---

## 5. Redacción sugerida para el Cap. 5

> Las cifras de S2–S4 deben actualizarse después de E1.

**§5.1, objetivo general (en lugar de l.2912–2917):**

> El objetivo general se cumplió: se construyó un entorno reproducible sobre la red vial de La Paz y con él se evaluaron ambas políticas en 80 corridas pareadas. La evaluación muestra que la ventaja de RH depende de la saturación de la flota. Con 18 pedidos por repartidor, FCFS entrega 1.4 min antes. A partir de 26 pedidos por repartidor, RH reduce el CtD medio entre 37 % y 67 % y entrega prácticamente todos los pedidos. Estos resultados son válidos para instancias sintéticas del centro urbano (8.4 km²), con 25 restaurantes, turno único y red sin congestión.

**§5.2, verificación de la hipótesis (en lugar de l.2954–2974):**

> La hipótesis, formulada de manera general, **no se verifica**. En baja saturación (S1), RH no supera a FCFS: su CtD es 1.38 min mayor (IC 95 % [0.41, 2.35], p = 0.014) y su RtD también es ligeramente mayor. El componente de productividad (órdenes por repartidor por hora) no permite contrastarla con este diseño, porque ambas políticas operan con la misma flota y los mismos turnos y solo difieren en cobertura. Los datos sí sostienen una **versión condicional**: a partir de una saturación moderada (S2–S4), RH reduce el CtD medio entre 36.8 % y 67.3 %, el RtD entre 46.8 % y 71.0 % y mejora el cumplimiento SLA entre 31.5 y 50.3 pp, en las diez semillas de cada escenario (p = 0.002, el mínimo alcanzable con n = 10). Esta forma condicional es un hallazgo del estudio y no la hipótesis original.

**Contribución 2 (en lugar de l.2984–2988):**

> […] en esta configuración, el punto de cruce se ubica entre 18 y 26 pedidos por repartidor. La desventaja de RH en S1 se asocia con el redondeo hacia arriba del tamaño objetivo de agrupamiento, por lo que el umbral es una propiedad de la implementación evaluada y no una regla general para operadores.

**Contribución 3, con el encuadre de igual flota (nuevo):**

> RH con 29–30 repartidores (S3) obtiene un CtD medio de 45.4 min y un SLA de 57.6 %, mejores que los de FCFS con 38–41 repartidores (S2): 56.1 min y 38.1 %. Es decir, RH ofrece mejor servicio con alrededor de 25 % menos flota.

**Contribución 4 (en lugar de l.2993–2996):**

> Se midió que los trayectos por la red vial del centro de La Paz son 38 % más largos que en línea recta (κ = 1.38), y que ignorar esta diferencia subestima tanto los tiempos de entrega de ambas políticas como la carga efectiva de la flota. Separar el efecto de la estructura de la red del de la longitud de los viajes requiere un control euclidiano escalado por κ, que se propone como trabajo futuro.

---

## 6. Banco de preguntas de defensa

| # | Pregunta probable | Respuesta sugerida (con los datos actuales) |
|---|---|---|
| 1 | ¿Se verifica su hipótesis? | En su forma general, no: falla en S1. Se sostiene en forma condicional en S2–S4 (§5). |
| 2 | ¿Por qué eligió "órdenes por hora" si no puede variar? | Fue un error de operacionalización. Con flota y turnos fijos, esa métrica solo refleja cobertura. La métrica correcta de eficiencia es la flota necesaria para un SLA dado (B7). |
| 3 | ¿Cuánto de la ventaja es del reloj de 5 min? | Hay un tiempo muerto de 5–10 min por viaje que penaliza más a FCFS. La corrección está en curso (E1); S1 no cambia de signo. |
| 4 | ¿Qué parte de la mejora es del *bundling*? | No se aisló; la comparación es entre políticas completas. E2 (RH sin *bundling*) responde esa pregunta. |
| 5 | ¿Por qué FCFS elige por distancia en grados? | Se usa solo para ordenar a los repartidores por cercanía. Reconozco que, con la red real, eso pone a FCFS en desventaja (E4). |
| 6 | Si multiplico la distancia euclidiana por 1.38, ¿obtengo lo mismo? | Probablemente sí en buena medida, porque el mecanismo es la carga. Por eso la contribución se replantea como "medir κ" (§5) y se propone E3. |
| 7 | Boyacı dice que la aproximación euclidiana funciona bien. ¿Por qué lo cita en sentido contrario? | Su conclusión aplica a problemas sin ventanas de tiempo. Ellos mismos advierten el riesgo con ventanas estrechas, que es el caso del MDRP. La cita se corrige en ese sentido. |
| 8 | ¿Dónde están los rodeos por la ensenada en sus datos? | No están: el dominio es el centro urbano. La ensenada motiva el trabajo, pero no se ejercita (A5). |
| 9 | ¿Contra qué calibró las instancias? | No se calibraron: se parametrizaron con valores de la literatura, porque no existen datos locales accesibles. |
| 10 | LaDe es de paquetería. ¿Por qué la usa para comida? | (Verificar antes de la defensa.) Se usó por la forma bimodal y la escala de distancias. Es un supuesto declarado, y su sustitución por datos locales es trabajo futuro. |
| 11 | ¿Cómo sabe que su RH es el de Reyes? | Sigue la temporización y la estructura del artículo, con desviaciones documentadas (B4). Correr las instancias de mdrplib es el paso de validación pendiente. |
| 12 | Encontró 21 errores. ¿Por qué no habría más? | Las verificaciones automáticas cubren la consistencia temporal y de entregas, pero no prueban la fidelidad. Lo reconozco, y la validación contra mdrplib atiende ese punto. |
| 13 | En S1 dice "equivalentes", pero p = 0.014. | Es una diferencia estadísticamente significativa de 1.4 min, de poca relevancia práctica. No afirmo equivalencia formal porque no definí un margen de antemano. |
| 14 | ¿Por qué 10 semillas? | En S2–S4 el semiancho de los IC es ≤ 11 % del efecto. En S1 el IC es [0.41, 2.35] min, suficiente para el signo. (Idealmente, justificar n a priori.) |
| 15 | ¿Cuánto tarda RH por época? ¿Escala? | Con el control euclidiano, RH simula un día en 6.5–16.7 s. La medición con OSRM está pendiente (E6). |
| 16 | El costo por pedido es siempre $10. ¿Qué mide? | Con estos parámetros de pago, el piso solo actúa en S1. El modelo de costo no discrimina, y se declara como limitación. |
| 17 | ¿Por qué un solo turno de 12.5 h para toda la flota? | Por simplicidad. Turnos escalonados (como en Reyes) cambiarían la saturación en los picos; es trabajo futuro. |
| 18 | ¿Su trabajo es reproducible? ¿Dónde están los resultados? | El código, la red y las semillas están fijados. Los resultados se publican con etiqueta y DOI (pendiente, B12). |
| 19 | ¿Qué aporta frente a Reyes et al.? | Una implementación abierta sobre una red vial real de una ciudad media, κ medido, la comparación contra una línea base reactiva por régimen de saturación y un conjunto de verificaciones de integridad. |
| 20 | ¿Qué haría distinto? | Formular una hipótesis condicional y comparable, incluir ablaciones y un control escalado por κ desde el diseño, y validar contra mdrplib antes de experimentar. |

---

## 7. Experimentos recomendados (ordenados por valor/costo)

Los comandos asumen OSRM levantado en `localhost:5000`, con Docker (`docker-compose up -d`) o con el binario nativo:

```
scratchpad/osrm_dl/binding/osrm-routed --algorithm ch --ip 127.0.0.1 --port 5000 osrm_data/bcs-latest.osrm
```

Las semillas son `--seeds 2025,2026,2027,2028,2029,2030,2031,2032,2033,2034`. Se pueden repartir entre varios procesos con `--scenario S1_baja` (y los demás), el mismo `--run-id` y `--no-analysis`, y analizar después con `--analyze-only --run-id <id>`.

| ID | Experimento | Cambio | Comando base | Qué responde | Impacto si sale mal para RH |
|---|---|---|---|---|---|
| **E1** | Corregir el reloj (C22) | En [src/main.py](../src/main.py), mover la actualización de rutas (l.170–211) **antes** de la asignación (l.123), o liberar al repartidor en su instante exacto de término | `run_experiments.py --seeds … --run-id <id>_osrm` y `--euclidean --run-id <id>_euclid`; luego `check_results.py` | A1: magnitud real de la ventaja y del cruce | Las magnitudes de S2–S4 bajan y el cruce puede moverse. Reescribir los Caps. 4–5 |
| **E2** | Ablación del *bundling* | Ninguno | `--bundle-sizes 1` (RH sin *bundling*) | A2: cuánto aporta el *matching* frente al *bundling* | Si RH con B = 1 ≈ FCFS, la ventaja es del *bundling* |
| **E3** | Control euclidiano escalado por κ | Ninguno | `--euclidean --speed 472` (651.1 / 1.3793 ≈ 472) | A4: ¿importa la estructura de la red o solo la longitud? | Si coincide con OSRM, la contribución 4 se reduce a "medir κ" |
| **E4** | FCFS con tiempos OSRM | En `assign_order_to_nearest_courier`, elegir por `plan_route(...)['arrival_restaurant']` en lugar de la distancia en grados | Igual que E1 | A2 y A4: línea base más justa | La ventaja de RH baja con OSRM |
| **E5** | Z_t redondeado en S1 | En `compute_target_bundle_size`, usar `round` (o `floor`, con mínimo 1) en lugar de `ceil` | `--scenario S1_baja --seeds …` | B6: ¿la derrota en S1 es de la implementación? | Si RH gana en S1, la hipótesis general se sostiene mejor |
| **E6** | Tiempo de cómputo | Registrar el tiempo real por corrida y por época también con `--run-id` y `--no-analysis` (C23) | Cualquier corrida | B10: "ligero" con datos | Ninguno; solo agrega evidencia |

**Orden sugerido:**
1. E1 y E6 juntos, porque son la base de las cifras.
2. E2 y E3, porque solo requieren correr comandos.
3. E4 y E5, que requieren pequeños cambios de código.

---

## 8. Comparación con otras maestrías del TecNM

**Fuente:** Repositorio Institucional del TecNM (RI-TecNM), consultado el 2026-10-24.

**Advertencia de asimetría:** de las otras tesis solo leí títulos y resúmenes, no los PDF. "No se menciona" significa "no aparece en el resumen". Esta tesis, en cambio, se revisó hasta el código. Si a cualquier otra tesis se le aplicara la misma auditoría, muy probablemente aparecerían problemas de la misma naturaleza.

| Programa | Muestra | Tipo de trabajo predominante | Rigor experimental visible en el resumen |
|---|---|---|---|
| **IT La Paz, Maestría en Sistemas Computacionales** (el mismo programa) | 10 tesis (2022–2026); 6 resúmenes leídos | Aprendizaje automático aplicado, visión por computadora, control y prototipos: detección de armas con YOLO, huellas dactilares, perfiles hidrográficos, señales sísmicas, robot recolector | Una métrica puntual por trabajo (precisión de 88–96.7 %, R² de 0.99). Ninguno menciona una línea base externa, réplicas con dispersión ni pruebas estadísticas. En una, el "mejor de 10 entrenamientos" se eligió usando los datos de prueba |
| **ITS Teziutlán, Maestría en Sistemas Computacionales** | 39 tesis (2020–2023) | Sistemas y aplicaciones (web, móvil, sistemas expertos y tutores) | Una usa una prueba t pareada contra el proceso manual (n = 3); otra, una RNN sin cifras en el resumen |
| **IT Cd. Madero, Maestría en Ciencias de la Computación** (orientada a investigación en optimización) | 4 resúmenes de 2021–2022 | Metaheurísticas y optimización multiobjetivo | El estándar alto. Por ejemplo, un algoritmo memético comparado contra el mejor algoritmo publicado, en instancias del estado del arte, con Wilcoxon (2997), y el *benchmark* DTLZ (3033) |

**Lectura objetiva:**
- En **diseño experimental** (pareado, 10 réplicas, IC, tamaño de efecto, control, verificaciones de integridad, código y red abiertos), esta tesis está **por encima de lo típico de su propio programa**, a juzgar por los resúmenes.
- El **problema** (MDRP dinámico sobre red vial real) es de investigación de frontera, con literatura reciente en *Transportation Science*, y casi no tiene presencia en el TecNM.
- Frente al **estándar de un programa orientado a investigación** (Madero) le faltan dos elementos que allí son norma:
  1. una línea base del estado del arte, no solo una política reactiva;
  2. instancias de referencia (aquí existen: mdrplib de Reyes).
- La debilidad real no es el tema ni el esfuerzo: tres afirmaciones (A1, A3 y A4) dicen más de lo que el diseño permite. Se corrigen con redacción honesta y 2–3 experimentos baratos (E1–E3).

**Fuentes:**
- [RI-TecNM: IT La Paz, Maestría en Sistemas Computacionales](https://rinacional.tecnm.mx/handle/TecNM/5298)
- [RI-TecNM: ITS Teziutlán, Maestría en Sistemas Computacionales](https://rinacional.tecnm.mx/handle/TecNM/1272)
- [RI-TecNM: IT Cd. Madero, Tesis de Maestría](https://rinacional.tecnm.mx/handle/TecNM/1509)
- Fichas: [5373](https://rinacional.tecnm.mx/handle/TecNM/5373), [6088](https://rinacional.tecnm.mx/handle/TecNM/6088), [6089](https://rinacional.tecnm.mx/handle/TecNM/6089), [7596](https://rinacional.tecnm.mx/handle/TecNM/7596), [8230](https://rinacional.tecnm.mx/handle/TecNM/8230), [10901](https://rinacional.tecnm.mx/handle/TecNM/10901), [2685](https://rinacional.tecnm.mx/handle/TecNM/2685), [7426](https://rinacional.tecnm.mx/handle/TecNM/7426), [2997](https://rinacional.tecnm.mx/handle/TecNM/2997), [3033](https://rinacional.tecnm.mx/handle/TecNM/3033), [5368](https://rinacional.tecnm.mx/handle/TecNM/5368), [3609](https://rinacional.tecnm.mx/handle/TecNM/3609)
- Ficha del programa de posgrado del IT La Paz: [gob.mx](https://www.gob.mx/cms/uploads/attachment/file/476425/Instituto_Tecnolgico_de_La_Paz.pdf)

---

## Apéndice: reproducir las cifras de esta revisión

Todos los fragmentos son de **solo lectura**. Se ejecutan desde la raíz del repositorio con el entorno virtual del proyecto (`python` con pandas y numpy).

**A1/B9: huecos entre viajes y tamaño de agrupamiento por viaje**

```python
import glob, pandas as pd, numpy as np
base = "results/experiments/20261023_233115_osrm"
for sc in ["S1", "S2", "S3", "S4"]:
    for pol in ["fcfs", "rh"]:
        per_trip, gap_p1 = [], []
        for f in sorted(glob.glob(f"{base}/{sc}_*/*_{pol}_results.csv")):
            d = pd.read_csv(f, parse_dates=["pickup_time", "delivery_time"])
            d = d[d.status == "delivered"]
            per_trip.append(d.groupby(["courier_id", "pickup_time"]).size().mean())
            g = []
            for _, dd in d.groupby("courier_id"):
                t = dd.groupby("pickup_time").delivery_time.max().sort_index()
                ends = t.values[:-1] + np.timedelta64(120, "s")      # + s_o/2
                g += list((t.index.values[1:] - ends) / np.timedelta64(1, "m"))
            gap_p1.append(np.percentile(g, 1))
        print(sc, pol, "orders/trip", round(np.mean(per_trip), 2),
              "P1 gap (min)", round(np.mean(gap_p1), 2))
```

Resultado esperado: P1 de 8.35–8.90 min; órdenes por viaje de RH: 1.93 / 2.17 / 2.42 / 2.80.

**A1: tiempo muerto estimado como porcentaje del turno**

```python
for sc in ["S1", "S2", "S3", "S4"]:
    for pol in ["fcfs", "rh"]:
        fr = []
        for f in sorted(glob.glob(f"{base}/{sc}_*/*_{pol}_couriers.csv")):
            c = pd.read_csv(f)
            fr.append(c.bundles_picked_up.sum() * 7.5 / (c.shift_duration_hours * 60).sum() * 100)
        print(sc, pol, round(np.mean(fr), 1), "%")
```

Resultado esperado: FCFS 17.9 / 25.8 / 30.7 / 30.6 %; RH 9.3 / 11.9 / 14.4 / 18.2 %.

**A5: cola de κ y área del polígono**

```python
import math
d = pd.read_csv("results/circuity/circuity_pairs.csv")
print(d.circuity.describe(percentiles=[.5, .9, .95, .99]))
print("κ>2:", (d.circuity > 2).mean(), " κ<1:", (d.circuity < 1).sum())
P = [(24.124041, -110.311612), (24.133011, -110.335855),
     (24.159317, -110.309647), (24.147104, -110.292893)]
kx, ky = 111.32 * math.cos(math.radians(24.14)), 110.57
xy = [(lon * kx, lat * ky) for lat, lon in P]
print("área km²:", 0.5 * abs(sum(xy[i][0] * xy[(i + 1) % 4][1] - xy[(i + 1) % 4][0] * xy[i][1] for i in range(4))))
```

Resultado esperado: P99 = 1.90; κ > 2 en 0.49 %; 13 pares con κ < 1; área de 8.36 km².

**A3/A6/B10: RtD, degradación de RH y tiempos de cómputo**

```python
for run in ["20261023_233115_osrm", "20261023_232220_euclid"]:
    d = pd.read_csv(f"results/experiments/{run}/experiment_comparison.csv")
    d["sc"] = d.Scenario.str[:2]
    print(run)
    print(d.groupby("sc")[["FCFS Avg RTD (min)", "RH Avg RTD (min)", "RH Avg CTD (min)",
                           "FCFS Time (s)", "RH Time (s)"]].mean().round(2))
```

Resultado esperado:
- RtD OSRM: FCFS 16.95 / 44.08 / 96.52 / 212.92 y RH 18.32 / 23.44 / 33.37 / 61.65 min (Δ +8.1 / −46.8 / −65.4 / −71.0 %).
- CtD de RH: euclidiano 27.55 → OSRM 30.31 (S1) y 56.96 → 73.63 (S4).
- Tiempos: 0.00 s en OSRM; RH 6.5–16.7 s en el control euclidiano.

**A7: citas** (texto local en `docs/ref/`)

```
grep -n "acceptable results" docs/ref/Boyaci2021.txt                 # l.511–514
grep -n "deviation factor ranges" docs/ref/Boyaci2021.txt            # l.159 (Cole y King, 1968)
grep -n "ranges from 3.4% to 29.0%" docs/ref/Ichoua2006.txt          # l.1409
grep -n "better predictor of customer satisfaction" docs/ref/Hildebrandt2021.txt
grep -n "mdrplib" docs/ref/reyes2018.txt                             # l.736
grep -n "no bundling" docs/ref/reyes2018.txt                         # l.985
```
