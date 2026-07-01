# Plan de implementación de observaciones ICL

**Documento revisado:** `tesis revisión 29.05.2026_revICL (2).pdf`  
**Fuente que se modificará posteriormente:** `docs/tesisss.tex`  
**Revisora:** Iliana Castro Liera  
**Estado:** implementado y verificado el 9 de junio de 2026.  
**Alcance de este archivo:** plan, trazabilidad de las 32 anotaciones y registro de implementación.

## Resumen

El PDF contiene 32 anotaciones en 11 páginas: 21 resaltados y 11 notas de texto.
Las anotaciones se consolidan en nueve paquetes de cambio:

| ID | Cambio | Prioridad | Dependencia |
|---|---|---:|---|
| ICL-01 | Actualizar el logotipo de portada | Alta | Recibir el archivo por WhatsApp |
| ICL-02 | Actualizar el mes y año de portada | Alta | Confirmar junio o agosto de 2026 |
| ICL-03 | Poner *Click-to-Door* en cursiva en la lista de figuras | Baja | Ninguna |
| ICL-04 | Homologar las citas narrativas al estilo numérico | Alta | Ninguna |
| ICL-05 | Revisar la pregunta retórica del apartado DARP | Media | Intención inferida; coordinar con ICL-04 |
| ICL-06 | Revisar la pregunta retórica previa a Ichoua | Media | Intención inferida; coordinar con ICL-04 |
| ICL-07 | Poner en negrita el encabezado “Agrupamiento” | Baja | Ninguna |
| ICL-08 | Poner en negrita los nombres de tres métricas | Baja | Ninguna |
| ICL-09 | Fijar la Tabla 3.4 junto a su texto introductorio | Media | Compilar e inspeccionar el PDF |

## Estado de implementación

| ID | Estado | Fuente actual | Evidencia en el PDF generado |
|---|---|---|---|
| ICL-01 | Completado | `tesisss.tex:52`; activos en `docs/img/` | Portada, PDF p. 1 |
| ICL-02 | Completado con `JUNIO 2026` | `tesisss.tex:90` | Portada, PDF p. 1 |
| ICL-03 | Completado | `tesisss.tex:2520` | Lista de figuras, PDF p. 8 |
| ICL-04 | Completado | `tesisss.tex:182–374` | Citas numéricas en PDF pp. 12–17 |
| ICL-05 | Completado | `tesisss.tex:243–251` | Redacción declarativa en PDF p. 14 |
| ICL-06 | Completado | `tesisss.tex:288–297` | Redacción declarativa en PDF p. 15 |
| ICL-07 | Completado | `tesisss.tex:705` | Negrita en PDF p. 28 |
| ICL-08 | Completado | `tesisss.tex:750`, `754`, `757` | Negrita-cursiva en PDF p. 29 |
| ICL-09 | Completado | `tesisss.tex:23`, `2364–2402` | Tabla completa en PDF p. 66, página interna 57 |

La compilación final se realizó con:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error tesisss.tex
```

Resultado: `docs/tesisss.pdf`, 85 páginas, sin citas o referencias indefinidas y
sin archivos gráficos faltantes.

## Convención para las citas

La revisora señaló como modelo la forma “Boyacı et al. [12]”. La implementación debe:

1. Eliminar años escritos manualmente como `(2018)` cuando la referencia ya es numérica.
2. Usar `\citet{clave}` cuando produzca correctamente `Autor et al. [n]`.
3. Usar texto de autor más `\cite{clave}` cuando se necesite conservar una conjunción en español o colocar primero el número, por ejemplo `En~\cite{Larsen2000DVRP}, Larsen...`.
4. Eliminar la cita duplicada al final de una oración cuando se incorpore al inicio.
5. No modificar el ejemplo ya correcto `\citet{Boyaci2021}`.

## Cotejo exacto de las 32 anotaciones

Las líneas de esta tabla corresponden al estado de `docs/tesisss.tex` cotejado el
9 de junio de 2026 **antes de aplicar las modificaciones**. Se conservan como
trazabilidad entre cada marca del PDF comentado y el texto fuente original. Las
ubicaciones posteriores a la implementación aparecen en la tabla de estado anterior.

| ID | PDF | Tipo | Texto de la anotación o selección | Línea(s) exacta(s) en `tesisss.tex` | Correspondencia comprobada |
|---|---:|---|---|---:|---|
| A01 | 1 | Nota | “Actualizar logotipo (te lo mando al WA)” | 51 | La nota está junto al logotipo izquierdo; corresponde a `img/sep2021.png`. |
| A02 | 1 | Nota | “será junio 2026 ó agosto...” | 89 | Sustituir `MARZO 2026` cuando se confirme el mes oficial. |
| A03 | 8 | Resaltado | `Click-to-Door` | 2514 | Es el texto del pie que alimenta automáticamente la lista de figuras. |
| A04 | 8 | Nota | “itálica” | 2514 | Confirma que A03 debe quedar como `\textit{Click-to-Door}`. |
| A05 | 12 | Resaltado | `Jazemi et al. (2023)` | 181; cita actual en 184 | Convertir la mención narrativa al estilo numérico y retirar la cita final duplicada. |
| A06 | 12 | Nota | “ver nota en la página 4, (Larsen)” | 181–184 | Remite al criterio explícito de A08; se aplica a la mención de Jazemi de A05. |
| A07 | 13 | Resaltado | `Larsen (2000)` | 213; cita actual en 216 | Mención que la revisora usa para explicar el formato deseado. |
| A08 | 13 | Nota | “esta cita no es consistente... En [9] Larsen proporciona...” | 213–216 | Reescribir el inicio con la referencia numérica y eliminar `\cite{Larsen2000DVRP}` del final. |
| A09 | 13 | Resaltado | `Pillac et al. (2013)` | 231 | Sustituir autor-año por cita narrativa numérica. |
| A10 | 13 | Nota | “igual que la nota anterior” | 231 | Aplica a A09 el mismo criterio de A08. |
| A11 | 14 | Resaltado | `Psaraftis (1980)` — primera mención | 243 | Primera aparición del autor en el apartado DARP. |
| A12 | 14 | Nota | “cita” | 243; cita actual en 247 | La primera afirmación debe quedar respaldada allí, sin esperar hasta el final de la pregunta. |
| A13 | 14 | Resaltado | `Psaraftis (1980) abordó` — segunda mención | 246–247 | Homologar o fusionar esta segunda mención al reescribir el pasaje. |
| A14 | 14 | Resaltado | `inmediato?` | 247 | Marca sin nota asociada. El plan infiere que debe evitarse la pregunta retórica; confirmar al implementar si solo se pretendía revisar puntuación/estilo. |
| A15 | 14 | Resaltado | `Cordeau y Laporte (2007)` | 249; cita actual en 250 | Integrar la referencia numérica en la mención narrativa y quitar la duplicación final. |
| A16 | 15 | Resaltado | `Ichoua et al. (2006)` | 290; cita actual en 296 | Convertir la mención narrativa al estilo numérico y retirar la cita final. |
| A17 | 15 | Resaltado | `anticipatorias?` | 287–288 | Marca sin nota asociada. El plan infiere una conversión a enunciado; la misma oración contiene `reacitvas` en la línea 287. |
| A18 | 16 | Resaltado | `Reyes et al. (2018)` — introducción del MDRP | 306 | Reemplazar la escritura manual por `\citet{Reyes2018}`. |
| A19 | 16 | Resaltado | `Reyes et al. (2018)` — brecha del MDRP | 320 | Reemplazar la escritura manual por `\citet{Reyes2018}`. |
| A20 | 16 | Resaltado | `Reyes et al. (2018)` — definición del MDRP | 326 | Reemplazar la escritura manual por `\citet{Reyes2018}`. |
| A21 | 17 | Resaltado | `Reyes et al. (2018)` — *ready time* | 336 | Reemplazar la escritura manual por `\citet{Reyes2018}`. |
| A22 | 17 | Resaltado | `Reyes et al. (2018)` — urgencia | 340 | Reemplazar la escritura manual por `\citet{Reyes2018}`. |
| A23 | 17 | Resaltado | `Reyes et al. (2018)` — capacidad de agrupamiento | 344 | Reemplazar la escritura manual por `\citet{Reyes2018}`. |
| A24 | 17 | Resaltado | `Boyacı et al. [12]` | 363 | Es el ejemplo correcto producido por `\citet{Boyaci2021}`; no requiere cambio. |
| A25 | 17 | Nota | “así puedes citar las demás” | Anclaje: 363; alcance: 181–344 | Confirma que A24 es el modelo para A05, A07, A09, A11, A13, A15, A16 y A18–A23. |
| A26 | 28 | Resaltado | `Agrupamiento (bundling):` | 700 | Primer encabezado de la lista de suposiciones; es el único sin negrita. |
| A27 | 28 | Nota | “¿porqué no está en negrita?” | 700 | Confirma que debe envolverse el encabezado con `\textbf{...}`. |
| A28 | 29 | Resaltado | `Click-to-Door (CtD):` | 745 | Primer nombre de métrica que debe ponerse en negrita. |
| A29 | 29 | Resaltado | `Ready-to-Pickup` | 749 | Segundo nombre de métrica que debe ponerse en negrita. |
| A30 | 29 | Resaltado | `Ready-to-Door (RtD):` | 752 | Tercer nombre de métrica que debe ponerse en negrita. |
| A31 | 29 | Nota | “negrita en los 3” | 745, 749 y 752 | Confirma el cambio conjunto de A28–A30. |
| A32 | 66 | Nota | “¿no puede ir aquí la tabla?” | Anclaje: 2359–2362; tabla: 2364–2396 | La tabla 3.4 debe colocarse inmediatamente después de su introducción. Si se usa `[H]`, añadir `float` después de la línea 22 del preámbulo. |

### Resultado del cotejo

- Las 32 anotaciones tienen una correspondencia concreta en la fuente.
- A14 y A17 son las únicas marcas cuyo cambio editorial es inferido porque no tienen
  una nota explicativa asociada.
- A24 es una referencia de formato, no una solicitud de modificación.
- A06, A08, A10, A12, A25, A27 y A31 son notas que explican uno o varios
  resaltados; no representan necesariamente una línea adicional que deba modificarse.
- A32 afecta tanto el punto de inserción visual (líneas 2359–2362) como el entorno
  flotante de la tabla (líneas 2364–2396).

## ICL-01 — Logotipo de portada

**Anotación:** PDF p. 1, “Actualizar logotipo (te lo mando al WA)”.  
**Ubicación comprobada:** `docs/tesisss.tex:51`, actualmente `img/sep2021.png`.

### Implementación prevista

1. Recibir el logotipo actualizado y confirmar cuál de los tres logotipos de la portada reemplaza. La posición de la anotación corresponde al logotipo izquierdo, actualmente `sep2021.png`.
2. Guardar el activo dentro de `docs/img/` con un nombre descriptivo y estable.
3. Actualizar la ruta del `\includegraphics` sin sobrescribir el archivo anterior hasta comprobar el resultado.
4. Conservar `keepaspectratio` o ajustar únicamente el ancho para evitar deformación.

**Implementado:** el logotipo recibido por WhatsApp se incorporó como
`docs/img/sep2026.jpeg`. Los logotipos `TecNM.png` y `logotec.jpeg` se recuperaron
sin recomprimir desde el PDF revisado. Se conserva `sep_previous.png` como respaldo
del logotipo anterior.

### Verificación

- El logotipo correcto aparece en la esquina superior izquierda.
- No se pixela ni se deforma.
- Los tres logotipos mantienen alineación y separación uniformes.
- La compilación no reporta archivos gráficos faltantes.

## ICL-02 — Fecha de portada

**Anotación:** PDF p. 1, “será junio 2026 ó agosto”.  
**Fuente comprobada:** `docs/tesisss.tex:89`.

### Implementación prevista

1. Se adoptó `JUNIO 2026`, por corresponder al periodo actual de implementación.
2. Se reemplazó `MARZO 2026` una sola vez en la portada.
3. Se comprobó que el PDF recompilado ya no contiene la fecha anterior.

### Verificación

- La portada muestra exactamente el mes aprobado y `2026`.
- El PDF recompilado ya no contiene `MARZO 2026`.

## ICL-03 — Cursiva en *Click-to-Door*

**Anotaciones:** PDF p. 8, resaltado de “Click-to-Door” y nota “itálica”.  
**Fuente comprobada:** pie de la Figura 4.1 en `docs/tesisss.tex:2514`.

### Implementación prevista

Cambiar:

```tex
\caption{Distribución del Click-to-Door por escenario y política...
```

por:

```tex
\caption{Distribución del \textit{Click-to-Door} por escenario y política...
```

La lista de figuras se genera a partir del pie, por lo que no debe editarse `tesisss.lof`
manualmente.

### Verificación

- *Click-to-Door* aparece en cursiva tanto en el pie de la Figura 4.1 como en la lista de figuras.
- La lista de figuras se regenera compilando al menos dos veces.

## ICL-04 — Homologación de citas narrativas

**Anotaciones:** PDF pp. 12–17.  
**Fuente comprobada:** `docs/tesisss.tex:181–344`; el ejemplo correcto está en la
línea 363.

| PDF | Texto marcado | Línea(s) exacta(s) | Acción prevista |
|---:|---|---:|---|
| 12 | `Jazemi et al. (2023)` | 181; cita en 184 | Usar `\citet{Jazemi2023}` y retirar la cita repetida al final del párrafo. |
| 13 | `Larsen (2000)` | 213; cita en 216 | Seguir la propuesta explícita: `En~\cite{Larsen2000DVRP}, Larsen proporciona...`; retirar la cita final duplicada. |
| 13 | `Pillac et al. (2013)` | 231 | Usar `\citet{Pillac2013}` y retirar la cita al final de la oración. |
| 14 | Primera mención de `Psaraftis (1980)` | 243; cita actual en 247 | Introducir la referencia numérica en la primera mención. |
| 14 | Segunda mención de `Psaraftis (1980)` | 246–247 | Integrarla en la reescritura ICL-05 y eliminar la cita aislada posterior a la pregunta. |
| 14 | `Cordeau y Laporte (2007)` | 249; cita en 250 | Usar `Cordeau y Laporte~\cite{Cordeau2007}` y retirar la cita final duplicada. |
| 15 | `Ichoua et al. (2006)` | 290; cita en 296 | Usar `\citet{Ichoua2006DDARP}` y retirar la cita al final del párrafo. |
| 16 | `Reyes et al. (2018)` — introducción del MDRP | 306 | Sustituir por `\citet{Reyes2018}`. |
| 16 | `Reyes et al. (2018)` — brecha del MDRP | 320 | Sustituir por `\citet{Reyes2018}`. |
| 16 | `Reyes et al. (2018)` — definición del MDRP | 326 | Sustituir por `\citet{Reyes2018}`. |
| 17 | `Reyes et al. (2018)` — *ready time* | 336 | Sustituir por `\citet{Reyes2018}`. |
| 17 | `Reyes et al. (2018)` — urgencia y dinamismo | 340 | Sustituir por `\citet{Reyes2018}`. |
| 17 | `Reyes et al. (2018)` — capacidad de agrupamiento | 344 | Sustituir por `\citet{Reyes2018}`. |

El resaltado `Boyacı et al. [12]` de la página 17 es el ejemplo de formato correcto, no
un texto que deba cambiarse.

### Verificación

- Buscar patrones de autor-año manuales; la búsqueda no debe devolver las 13 ocurrencias anteriores.
- Todas las referencias conservan su número correcto después de recompilar.
- No aparecen citas duplicadas como `Autor [n] ... [n]`.
- Las entradas [5]–[13] siguen presentes y ordenadas de acuerdo con `unsrtnat`.
- Revisar visualmente las páginas afectadas para detectar saltos de línea poco naturales.

## ICL-05 — Pregunta retórica en DARP

**Anotación inferida:** PDF p. 14, resaltado del signo de interrogación en la pregunta atribuida a Psaraftis.  
**Fuente comprobada:** `docs/tesisss.tex:243–247`; el signo resaltado está en la
línea 247.

### Implementación prevista

Reescribir las dos oraciones como una exposición declarativa. Una redacción base para la
implementación es:

> En [6], Psaraftis formuló el primer modelo dinámico de *dial-a-ride* y abordó la
> asignación dinámica de pasajeros a vehículos y la secuenciación óptima de sus viajes
> bajo políticas de despacho inmediato.

La versión final debe conservar la explicación de solicitudes en tiempo real y coordinarse
con el cambio de cita de ICL-04.

### Verificación

- Se elimina la pregunta retórica.
- La referencia [6] queda asociada claramente con toda la afirmación.
- No se pierde la definición operativa del DARP.

## ICL-06 — Disyuntiva reactiva/anticipatoria

**Anotación inferida:** PDF p. 15, resaltado del signo de interrogación al final de “anticipatorias?”.  
**Fuente comprobada:** `docs/tesisss.tex:287–288`; la mención posterior de Ichoua
está en la línea 290 y su cita actual en la 296.

### Implementación prevista

Reemplazar la pregunta por una afirmación, por ejemplo:

> A pesar de sus diferencias, DVRP y DARP comparten la disyuntiva fundamental entre
> decisiones reactivas (FCFS) y decisiones anticipatorias.

En el mismo cambio:

- Corregir `reacitvas` por `reactivas`.
- Iniciar el párrafo siguiente con la cita numérica de Ichoua definida en ICL-04.

### Verificación

- No permanece `reacitvas`.
- La transición hacia el trabajo de Ichoua es declarativa y fluida.
- No queda una pregunta retórica aislada.

## ICL-07 — Negrita en “Agrupamiento”

**Anotaciones:** PDF p. 28, resaltado y nota “¿porqué no está en negrita?”.  
**Fuente comprobada:** `docs/tesisss.tex:700`.

### Implementación prevista

Cambiar el primer elemento de “Suposiciones estructurales” a:

```tex
\item \textbf{Agrupamiento (\textit{bundling}):} Órdenes del mismo...
```

### Verificación

- Los cinco encabezados de la lista tienen el mismo peso tipográfico.
- *bundling* conserva la cursiva dentro de la negrita.

## ICL-08 — Negrita en las tres métricas

**Anotaciones:** PDF p. 29, tres resaltados y nota “negrita en los 3”.  
**Fuente comprobada:** `docs/tesisss.tex:745`, `docs/tesisss.tex:749` y
`docs/tesisss.tex:752`.

### Implementación prevista

Aplicar negrita al nombre completo, acrónimo y dos puntos, conservando la cursiva del
término inglés:

```tex
\item \textbf{\textit{Click-to-Door} (CtD):} ...
\item \textbf{\textit{Ready-to-Pickup} (RtP):} ...
\item \textbf{\textit{Ready-to-Door} (RtD):} ...
```

### Verificación

- Las cinco métricas de la lista comienzan con un encabezado en negrita.
- Los tres términos ingleses siguen en cursiva.
- Las ecuaciones y definiciones no cambian.

## ICL-09 — Ubicación de la Tabla 3.4

**Anotación:** PDF p. 66, “¿no puede ir aquí la tabla?”.  
**Fuente comprobada:** introducción en `docs/tesisss.tex:2359–2362` y entorno de la
tabla en `docs/tesisss.tex:2364–2396`.

### Implementación prevista

1. Agregar `\usepackage{float}` después de `docs/tesisss.tex:22` si se decide usar
   posicionamiento estricto.
2. Cambiar únicamente la Tabla 3.4 en `docs/tesisss.tex:2364` de
   `\begin{table}[htbp]` a `\begin{table}[H]`.
3. Compilar e inspeccionar si la tabla completa cabe debajo del texto introductorio.
4. Si no cabe, reducir localmente el tamaño a `\footnotesize` y, solo si es necesario,
   ajustar `\arraystretch` o el ancho de la columna de definición.
5. Mantener los 21 indicadores y la leyenda; no dividir ni eliminar filas solo para forzar
   el acomodo.

### Verificación

- La Tabla 3.4 comienza en la misma página que “3.7.6 Resumen de indicadores”.
- No invade el margen inferior ni queda partida de manera ilegible.
- El Capítulo 4 conserva un inicio limpio.
- La lista de tablas registra la página nueva después de dos compilaciones.

## Orden recomendado de implementación

1. Obtener el logotipo y confirmar el mes de portada.
2. Aplicar ICL-01, ICL-02 e ICL-03.
3. Aplicar ICL-04, ICL-05 e ICL-06 en una sola revisión de estilo para evitar citas duplicadas.
4. Aplicar ICL-07 e ICL-08.
5. Aplicar ICL-09 y ajustar el diseño únicamente después de compilar.
6. Limpiar auxiliares de LaTeX si la lista de figuras o tablas conserva datos anteriores.
7. Compilar al menos dos veces y revisar visualmente las páginas 1, 8, 12–17, 28–29 y 66–67.

## Cobertura de las 32 anotaciones

| Página PDF | Anotaciones | Cantidad | Cubiertas por |
|---:|---|---:|---|
| 1 | 2 notas de texto | 2 | ICL-01, ICL-02 |
| 8 | 1 resaltado + 1 nota | 2 | ICL-03 |
| 12 | 1 resaltado + 1 nota | 2 | ICL-04 |
| 13 | 2 resaltados + 2 notas | 4 | ICL-04 |
| 14 | 4 resaltados + 1 nota | 5 | ICL-04, ICL-05 |
| 15 | 2 resaltados | 2 | ICL-04, ICL-06 |
| 16 | 3 resaltados | 3 | ICL-04 |
| 17 | 4 resaltados + 1 nota | 5 | ICL-04 |
| 28 | 1 resaltado + 1 nota | 2 | ICL-07 |
| 29 | 3 resaltados + 1 nota | 4 | ICL-08 |
| 66 | 1 nota de texto | 1 | ICL-09 |
| **Total** |  | **32** | **32 cubiertas** |

## Criterio de cierre para la implementación futura

La revisión podrá considerarse implementada solamente cuando:

- estén resueltas las dos dependencias de portada;
- los nueve paquetes ICL hayan sido aplicados;
- el documento compile sin errores;
- las citas y referencias se hayan regenerado correctamente;
- las listas de figuras y tablas estén actualizadas;
- y una inspección visual confirme cada cambio en las páginas señaladas.

**Cierre:** todos los criterios anteriores se cumplieron. La inspección visual incluyó
la portada, la lista de figuras, las páginas de citas, las listas tipográficas y la
Tabla 3.4. La numeración original se preservó como Pereira [11], Boyacı [12] y
Reyes [13].
