# PLAN — RIIM journal article from the thesis

The article will be written in LaTeX and compiled to the PDF uploaded to RIIM. It is derived from the thesis `docs/tesisss.tex`.

## 1. Target

| Item | Value |
|---|---|
| Journal | Revista Internacional de Investigación Multidisciplinaria (RIIM), TecNM / IT Orizaba, ISSN 3122-4806 |
| Issue | Vol. 3, No. 2, 2026 |
| Submission | OJS: http://orizaba.tecnm.mx/revistaojs — **Oct 12 → Nov 8, 2026** (closes Sunday) |
| Review results | Fri Nov 20, 2026 (Aceptado / Susceptible de aceptación / Rechazado) |
| Fee | $2,500 MXN, paid only if accepted |
| Rules | Original, not submitted elsewhere; plagiarism software; double-blind review; author list frozen after acceptance |

The thesis and this article are the only documents about this work. The ECTI 2026 draft was dropped, and its `.docx` is already deleted in the working tree.

## 2. Confirmed decisions

- **Área de participación:** Sistemas Computacionales.
- **Author:** Sánchez Martínez, Alan José Marcos¹* — ¹Tecnológico Nacional de México / Instituto Tecnológico de La Paz, alansama2906@gmail.com.
- **Title** (13 words; the limit is 15): *Logística de última milla en redes viales reales: MDRP reproducible en La Paz, B.C.S.*
- **Keywords** (4): enrutamiento dinámico, horizonte rodante, OpenStreetMap, simulación. **Key words:** dynamic routing, rolling horizon, OpenStreetMap, simulation.

## 3. Template specification

Extracted from `producto_academico/Template_artículo_RIIM.docx` (`word/styles.xml`, `document.xml`, `header1.xml`, `footer1.xml`).

| Element | Spec |
|---|---|
| Page | Letter; margins L/R 2.0 cm, top 3.5 cm, bottom 2.25 cm; header and footer 1.25 cm from the edge |
| Body | Montserrat 10 pt, single spacing, justified, no indent, 8 pt after each paragraph |
| Title | Montserrat SemiBold 16 pt, ALL CAPS, centered, 6 pt before / 18 pt after |
| Authors / affiliation | Italic 9 pt, centered; superscript numbers and `*` |
| Área line | 9 pt centered, label "Área de participación:" |
| Section heading | Montserrat SemiBold 12 pt, color `#003D7C`, left-aligned, unnumbered |
| Subheading | Montserrat SemiBold *italic* 11 pt, slight letter spacing |
| Keywords line | "Palabras clave:" in regular weight, terms in *italic* (same for "Key words:") |
| Figures | Caption below, 9 pt centered: "Figura N. …" (add "Tomado/Adaptado de [n]" only for borrowed figures) |
| Tables | Caption above, 9 pt centered: "Tabla N. …" |
| References | IEEE, numbered `[n]` in order of first citation; Arial 10 pt, 1.27 cm hanging indent; ≥6, all cited, **most ≤5 years old (2021+)** |
| Header | RIIM logo (template `image4.png`, left 59.3%) + "RIIM, Vol 3, Num 2, 2026" in Arial 8 pt |
| Footer | Page number centered; next line "ISSN 3122-4806" (left) and "http://orizaba.tecnm.mx/revistaojs" (right), 9 pt |
| Length | 7–10 pages |
| Section order | Resumen (≤150 words) → Palabras clave → Abstract (≤150) → Key words → Introducción → Metodología → Resultados y discusión → Trabajo a futuro → Conclusiones → [Agradecimientos] → Referencias |

## 4. Phases

### Phase 0 — Fix the data (BLOCKING)
The current results are invalid; see **`DATACHECKS.md`**. Before any number is written:
1. Fix in `src/` the following:
   - C1: wait for food plus service time in the route timing;
   - C2: dispatch trigger based on elapsed time;
   - C3: RH double delivery;
   - C4: decide what the FCFS baseline is.
2. Re-run all 10 seeds × 4 scenarios × 2 policies, then run the statistical analysis.
3. Pass checks DC1–DC5 with the script in `DATACHECKS.md` §2.
4. Optional, needed only to keep the "real topology" claim: a Euclidean control run plus a circuity measurement (C5).

Time budget: the deadline is Nov 8. Allow ~3–4 days for the fix, the re-run and the checks, then ~1 week for writing.

### Phase 1 — LaTeX scaffold (independent of the numbers; can start in parallel)
Files under `producto_academico/`:
- `articulo_RIIM.tex`: a single file with an inline bibliography.
- `fonts/Montserrat-{Regular,Italic,Bold,BoldItalic,SemiBold,SemiBoldItalic}.ttf` from github.com/JulietaUla/Montserrat (SIL OFL). Montserrat is not installed locally.
- `img/riim_header.png`: `sips -c 388 2040 --cropOffset 0 0 <template image4.png> --out img/riim_header.png`.
- `img/`: figures copied from the **new** run directory.

Technical choices:
- **XeLaTeX** + `fontspec`.
  - `\setmainfont{Montserrat}[Path=fonts/]`; a `\semibold` family for headings; Arial (a macOS system font) for the header and references.
  - Fallback via `\IfFileExists`: if `fonts/` is missing, use Arial.
- Only packages present in the local TeX Live *basic* install:
  - used: `geometry`, `fancyhdr`, `caption`, `booktabs`, `tabularx`, `graphicx`, `amsmath`, `amssymb`, `xcolor`, `tikz`, `float`, `hyperref`, `babel[spanish,mexico,es-tabla,es-nodecimaldot]`;
  - not available: `titlesec`, `enumitem`, `IEEEtran`, `multirow`, `siunitx`, `biber`.
- Headings via `\@startsection` with `secnumdepth=0`. Paragraphs: `\parindent=0pt`, `\parskip=8pt`.
- **Blind switch:** `\newif\ifblind`.
  - `\blindtrue` produces the version uploaded to OJS: no author or affiliation lines, empty PDF author metadata, and no Agradecimientos.
  - `\blindfalse` produces the camera-ready version.
- Bibliography: a hand-written `thebibliography` in IEEE style. No BibTeX step is needed, since no IEEE `.bst` is installed.

### Phase 2 — Content (fresh Spanish prose, ~4,000–4,500 words)
Write new text rather than pasting from the thesis, so the plagiarism check stays clean. Avoid self-identifying wording ("esta tesis", institute name, repo URL).

1. **Resumen / Abstract** (≤150 words each).
2. **Introducción:**
   - last-mile cost [Jazemi2023];
   - the MDRP [Reyes2018, Yildiz2019, Ulmer2021RMDP];
   - the Euclidean approximation underestimates by 17–40% [Boyaci2021] and is a reproducibility problem [Pereira2021];
   - La Paz's topology;
   - cost barrier for SMEs [MunozVillamizar2021];
   - data-hungry ML alternatives [Hildebrandt2021];
   - objective, hypothesis, contributions.
3. **Metodología:**
   - *Formulación del MDRP y métricas:* sets; CtD / RtP / RtD; compensation equation.
   - *Heurística de horizonte rodante:* the Z_t equation, insertion cost, priority groups, the w_{s,d} equation, the Hungarian algorithm [Kuhn1955], two-stage commitment.
   - *Entorno reproducible:* OSM → OSRM (CH) [Boeing2021, Geisberger2008] in Docker; epochs of f = 5 min; cache and Haversine fallback. **Figura 1:** a compact TikZ version of the thesis's three-layer architecture diagram.
   - *Generación de instancias:* the λ(t) equation for the bimodal NHPP [Wu2023LaDe], prep time, uniform spatial sampling (described honestly; C9), the fleet-sizing equation.
   - *Política base FCFS:* described exactly as implemented after the C4 decision.
   - *Diseño experimental:* **Tabla 1** (parameters), **Tabla 2** (scenarios, with actual fleet ranges), paired design, seed-level Wilcoxon [Wilcoxon1945] and Friedman [Friedman1937], n = 10.
4. **Resultados y discusión:**
   - **Tabla 3:** CtD, P90, SLA in pp, coverage.
   - **Figura 2:** CtD boxplot.
   - RtP and overage.
   - **Tabla 4:** efficiency, bundles, cost, using unique deliveries.
   - **Figura 3:** bundle distribution. Drop it first if the article runs over 10 pages.
   - **Tabla 5:** Wilcoxon.
   - **Figura 4:** KPIs vs saturation.
   - Comparison with the literature, without the C5/C6 claims unless the control run exists.
   - Limitations.
5. **Trabajo a futuro.**
6. **Conclusiones:** whatever the corrected data support, even if the headline changes.
7. **Agradecimientos:** optional, camera-ready only.

### Phase 3 — References (14; 8 are 2021+)
In order of likely first citation:
1. Jazemi 2023
2. Reyes 2018
3. Yıldız & Savelsbergh 2019
4. Ulmer et al. 2021
5. Boyacı et al. 2021
6. Pereira et al. 2021
7. Muñoz-Villamizar et al. 2021
8. Hildebrandt & Ulmer 2022
9. Kuhn 1955
10. Boeing 2021
11. Geisberger et al. 2008
12. Wu et al. 2023 (LaDe)
13. Wilcoxon 1945
14. Friedman 1937

Verify every entry against Crossref before writing. Known `biblio.bib` errors are listed in `DATACHECKS.md` §4.

### Phase 4 — Verification
- [ ] `cd producto_academico && xelatex articulo_RIIM.tex` (×2): no undefined references or citations; no missing font or file warnings.
- [ ] Page count is between 7 and 10 (from "Output written … (N pages)" in the log).
- [ ] Script check:
  - title ≤15 words;
  - Resumen ≤150 and Abstract ≤150 words;
  - ≤4 keywords;
  - every `\bibitem` is cited and every `\cite` resolves;
  - ≥8 of 14 references are from 2021+.
- [ ] Visual check of every PDF page:
  - header logo and text; footer ISSN and URL;
  - fonts; heading color; caption positions;
  - no overfull tables or figures.
- [ ] Blind build contains no name, email or institute. Camera-ready build shows the author block.
- [ ] Every number in the article traces to a CSV cell from the new run (`DATACHECKS.md` §3).

## 5. Risks

- **The headline may change.** C1 favors FCFS, so after the fix the "FCFS wins at low saturation" regime and the 26–35 crossover may disappear or move. The article must report the corrected result.
- **Thesis/article mismatch.** If the thesis is deposited with the old numbers, prepare an erratum or corrected version. Reviewers or the plagiarism tool may compare the two.
- **Deadline.** If Phase 0 slips past ~Nov 1, consider submitting to a later RIIM issue instead of rushing.
