# DATACHECKS — data consistency checks before writing the RIIM article

> **Status: BLOCKED.** The results in `results/experiments/20260413_182745/`, which are the source of every number in thesis Chapter 4, are **not valid for publication**. Do not copy any number from the thesis into the article until checks **DC1–DC5** pass on a fresh run.

Audit date: 2026-10-23. Sources audited: `docs/tesisss.tex` (the `.tex`, which is newer than `docs/tesisss.pdf`), `src/`, `scripts/run_experiments.py`, and the raw per-seed CSVs.

---

## 1. Critical errors in the thesis

Severity levels:
- **Critical**: invalidates the reported results.
- **Major**: an unsupported or incorrect claim.
- **Moderate**: a methodological inaccuracy.

### C1 — Delivery time ignores the wait for food and the service time (Critical)

**Evidence.** Two pieces of code interact.

[`src/asignaciontentativa.py:40`](../src/asignaciontentativa.py#L40) (FCFS) and [`:149`](../src/asignaciontentativa.py#L149) / [`:162`](../src/asignaciontentativa.py#L162) (RH final commitment) compute:
```python
'completion_time': current_time + timedelta(seconds=route_data['duration'])
```
The OSRM duration is pure driving time: courier → restaurant → customers.

[`src/main.py:173-181`](../src/main.py#L173-L181) then computes
`pickup = max(bundle_ready, arrival + SERVICE_TIME/2)`, but stores `delivery_time = completion_time`. So:
- the courier never waits at the restaurant for the food to be ready;
- the service time `SERVICE_TIME = 4 min` ([`src/config.py:9`](../src/config.py#L9)) is never added to the delivery time.

Orders delivered *before* they were ready (and before their own pickup), from the raw CSVs (7 valid seeds):

| Scenario | FCFS deliveries | FCFS delivered < ready | RH deliveries | RH delivered < ready | RH delivered < pickup |
|---|---|---|---|---|---|
| S1 | 7,185 | **5,008 (69.7%)** | 7,185 | 160 (2.2%) | 390 (5.4%) |
| S2 | 7,185 | **4,074 (56.7%)** | 7,185 | 160 (2.2%) | 447 (6.2%) |
| S3 | 7,185 | **3,208 (44.6%)** | 7,185 | 169 (2.4%) | 490 (6.8%) |
| S4 | 6,361 | **1,998 (31.4%)** | 7,185 | 132 (1.8%) | 412 (5.7%) |

Concrete rows from `S1_baja_seed2025/synthetic_lapaz_orders_seed2025_fcfs_results.csv`:
- order 1: ready 08:13:38, pickup 08:13:38, **delivered 08:13:05**;
- order 1037: placed 18:58:29, ready 19:13:18, **delivered 19:05:54** (CtD 7.4 min).

The aggregate statistics show the same problem: in `seed_level_tests.csv`, the mean FCFS **Ready-to-Door in S1 is −1.89 min**. FCFS's mean CtD in S1 (10.1 min) is below the mean preparation time (12 min) alone.

**Impact.**
- Every service-quality number in the thesis is wrong: CtD (mean, P50, P90, P95), RtD, SLA, CTD Overage.
  - Tables: `tab:res_ctd`, `tab:res_rtp`, `tab:wilcoxon_seed`.
  - Figures: `fig_ctd_boxplot`, `fig_kpi_vs_ratio`.
- The error strongly favors FCFS, most of all at low saturation.
- The headline conclusions are therefore probably artifacts: "FCFS is faster in S1–S2", the two-regime story, and the "crossover between 26 and 35 orders/courier".
- The thesis says the service time is applied ([tesisss.tex:567-570](../docs/tesisss.tex#L567-L570), [:1582](../docs/tesisss.tex#L1582)); the code does not do this.
- RtD is defined and named in the hypothesis but never reported, which is why the negative values went unnoticed.

**Fix.**
1. Simulate the route in sequence: `arrive_r = t + leg0`; `pickup = max(arrive_r, ready_bundle) + s_r`; then for each drop `k`, `deliver_k = deliver_{k-1} + leg_k + s_o`.
2. Use the final `deliver_k` as the courier's release time, and give each order in a bundle its own delivery time. Today every order in a bundle gets the bundle's completion time.

### C2 — The three "failed" seeds come from a code bug, not an OSRM outage (Critical)

**Evidence.**
- Dispatch runs only when `current_time.minute % 5 == 0` ([`src/main.py:120`](../src/main.py#L120)).
- The clock starts at the first order minus 15 min ([`src/synth_loader.py:73`](../src/synth_loader.py#L73)) and advances in 5-min steps.
- If the first order is placed at 08:01:xx, the clock reads :46, :51, :56, … and dispatch **never** runs.

| Seed | First order | Start | Dispatch ever runs? | Result |
|---|---|---|---|---|
| 2025, 2026, 2028–2032 | 08:00:xx | 07:45:xx | yes | valid |
| **2027** | 08:01:54 | 07:46:54 | **no** | all 1,014 orders stuck in `ready` |
| **2033** | 08:01:06 | 07:46:06 | **no** | all 991 orders stuck in `ready` |
| **2034** | 08:01:26 | 07:46:26 | **no** | all 994 orders stuck in `ready` |

The failure repeats identically in all 8 runs of each bad seed (4 scenarios × 2 policies). Every valid run reports 100% `routing_source = osrm`.

**Impact.** The thesis attributes the failures to "una interrupción del servicio OSRM" in several places:
- [tesisss.tex:2413](../docs/tesisss.tex#L2413) (Ch. 4 intro);
- [:2784-2788](../docs/tesisss.tex#L2784-L2788) (limitations);
- OE1 ([:2834](../docs/tesisss.tex#L2834));
- future work ([:2933-2938](../docs/tesisss.tex#L2933-L2938)).

That explanation is wrong. Also, n = 7 instead of 10.

**Fix.**
- Trigger dispatch on elapsed time: `(current_time - start_time) % OPTIMIZATION_FREQUENCY == 0`. Since the loop already steps by `f`, simply dispatching on every iteration is enough.
- Alternatively, floor `start` to a 5-minute boundary.
- Then re-run all 10 seeds.

### C3 — RH delivers some orders twice (Critical)

**Evidence.** The courier CSVs sum to more deliveries than there are orders:

| Run | Orders | Σ `orders_delivered` (courier CSV) | Delivered (order CSV) |
|---|---|---|---|
| S1 seed 2025 RH | 1,038 | **1,089** | 1,038 |
| S1 seed 2026 RH | 1,042 | **1,093** | 1,042 |
| S4 seed 2025 RH | 1,038 | **1,079** | 1,038 |
| S4 seed 2026 RH | 1,042 | **1,075** | 1,042 |
| FCFS (all checked) | — | equal | equal |

Across the 7 valid seeds, the RH duplicates per scenario are **314 / 269 / 321 / 306** (S1–S4), about 4% of RH deliveries. FCFS has 0. The same order ends up in more than one final route. Each delivery increments `c.orders_delivered`, while the order row is simply overwritten (last write wins).

An earlier fix for this, commit `204500f` (2026-04-04, "mark orders as assigned in two_stage_commitment"), **predates** this run (2026-04-13). Duplicates therefore still enter through another path. Its root cause has not been located yet. `scripts/_audit_bug.py` already traces this mechanism, but it points at the older run `20260323_202838`; set its `BASE` to the new run.

**Impact.**
- KPIs computed from the courier CSV are inflated for RH ([`scripts/run_experiments.py:129-154`](../scripts/run_experiments.py#L129-L154)): Orders/Courier/Hr, Cost/Order, Dist/Order and Frac. Mín.
  - The "RH +4.9% throughput in S1" is **exactly** 1089/1038.
  - Bundle sizes are probably affected as well.
- The integrity check claimed at [tesisss.tex:2450-2452](../docs/tesisss.tex#L2450-L2452) ("cada `order_id` aparece exactamente una vez") cannot detect this. The order CSV has one row per `Order` object by construction.

**Fix.**
- Find the second duplication path. Candidates: the same order appearing in bundles of more than one priority group; a courier being re-used across the sequential group rounds of `assign_bundles_to_couriers`; a partial-commit courier and a new final-commit courier holding the same orders. Only orders with status `ready` may enter `generate_bundles_for_restaurant`.
- Add an assertion in `main.py` that an order is never delivered twice.

### C4 — The FCFS baseline is not purely reactive (Critical for interpretation)

**Evidence.**
- [`src/main.py:124`](../src/main.py#L124) builds `orders_ready` with `o.ready_time <= current_time + ASSIGNMENT_HORIZON` (20 min) for **both** policies.
- FCFS then dispatches each of these orders immediately ([`src/main.py:126-130`](../src/main.py#L126-L130)).
- The thesis describes FCFS as acting on orders "con estado `ready`" ([tesisss.tex:1908](../docs/tesisss.tex#L1908)) and as purely reactive.

**Impact.** FCFS sends couriers up to 20 min before the food is ready. Combined with C1 (no waiting), this is what produces "deliveries before ready".

**Fix.** Choose one:
- FCFS uses only `ready_time <= current_time` (a truly reactive baseline);
- or document FCFS as "nearest courier with 20-min lookahead".

Either way, C1 must be fixed.

### C5 — "Real topology amplifies RH's advantage" is not supported (Major)

**Evidence.**
- No Euclidean-vs-OSRM run exists. Both policies always use OSRM (`routing_source = osrm` in 100% of rows).
- Scope promised a control scenario ([tesisss.tex:525-528](../docs/tesisss.tex#L525-L528)), and OE2 promised validation "frente a distancias euclidianas" ([:429-430](../docs/tesisss.tex#L429-L430)). Neither was done.
- No topology metric for La Paz was computed (circuity, detour factor).

**Impact.** The following claims have no supporting experiment:
- Ch. 4 "Comparación con la literatura" ([:2770-2778](../docs/tesisss.tex#L2770-L2778));
- contribution 4 ([:2918-2922](../docs/tesisss.tex#L2918-L2922));
- the hypothesis wording "FCFS con estimación euclidiana" ([:443-447](../docs/tesisss.tex#L443-L447)).

**Fix.** Either:
- run the control (RH and FCFS with Haversine at 320 m/min vs OSRM) and report circuity (OSRM km / Haversine km) for the sampled pairs;
- or drop these claims.

### C6 — Misread citation of Reyes et al. (2018) (Major)

**Evidence.**
- The thesis says "Reyes2018 reportan mejoras de CtD de 10–25% al pasar de asignación greedy a horizonte rodante" ([:2772](../docs/tesisss.tex#L2772), [:2916](../docs/tesisss.tex#L2916)).
- In `docs/ref/reyes2018.txt:1057-1058`, the 10% CtD improvement comes from instances where **travel times are 25% faster**. That is a sensitivity analysis, not a greedy-vs-RH comparison.
- The thesis also says "eficiencias cercanas al 96% respecto al óptimo" ([:406](../docs/tesisss.tex#L406)). The source says mean CtD is "on average only 4% above the optimal value" on small instances (`reyes2018.txt:1005`).

**Fix.**
- Remove the "10–25%" comparison.
- Rephrase the 96% claim as "≈4% above optimal mean CtD on small instances".

### C7 — SLA reported in mixed units (Major)

**Evidence.**
- In Table `tab:res_ctd` ([:2473-2476](../docs/tesisss.tex#L2473-L2476)), the SLA "Δ%" column is a *relative* change (+5.8 / +18.2 / +27.9).
- The text and conclusions call these values percentage points: "+5.8 pp" at [:2494](../docs/tesisss.tex#L2494), "mejora el SLA en 27.9 pp" at [:2888](../docs/tesisss.tex#L2888).
- The actual paired differences (`seed_level_tests.csv`) are **5.4 / 14.0 / 17.1 pp** (S2 / S3 / S4).
- S2 RH SLA appears as 97.0 at [:2494](../docs/tesisss.tex#L2494) and [:2877](../docs/tesisss.tex#L2877), but as 97.1 at [:2726](../docs/tesisss.tex#L2726) and [:2755](../docs/tesisss.tex#L2755). The seed mean is 97.05.

**Fix.** Report SLA differences in pp everywhere, and use one rounding rule (1 decimal, half-up).

### C8 — Throughput and utilization are misread (Major)

**Evidence.**
- Orders/Courier/Hr = Σ delivered / Σ shift hours.
- Both policies use the **same fleet and the same shifts**, so the denominator is identical. Any difference comes only from:
  - FCFS undelivered orders (S4);
  - RH duplicates (C3).
- "Utilization" counts driving minutes only (no service, no waiting), so "lower utilization = more efficiency" ([:2603-2609](../docs/tesisss.tex#L2603-L2609)) is not supported.

**Fix.**
- Report coverage (% delivered) directly.
- Compare distance per *unique* delivered order.
- Define utilization as (driving + service + waiting) / shift once C1 is fixed.

### C9 — "Real demographic structure" is not implemented (Moderate)

The thesis claims a demographic projection in OE1 ([:425](../docs/tesisss.tex#L425)) and its verification ([:2831](../docs/tesisss.tex#L2831)). In fact:
- restaurant coordinates from OSM are discarded ([:1724-1730](../docs/tesisss.tex#L1724-L1730));
- all points are drawn uniformly inside a 4-vertex polygon ([:1693-1700](../docs/tesisss.tex#L1693-L1700)).

This polygon may also exclude the bay detours that motivate the problem (§1.2.2). Describe it as uniform spatial sampling, or use population-weighted sampling.

### C10 — Meal peaks at 09:00 and 17:00 are called "local hours" (Moderate)

The peaks are set at [:1644](../docs/tesisss.tex#L1644), and [:1256](../docs/tesisss.tex#L1256) says they are adjusted to local hours. Typical Mexican lunch and dinner peaks are around 14:00 and 20:00. Either justify the choice (e.g., LaDe hours mapped to the window) or move the peaks.

### C11 — Fleet sizes are not fixed per scenario (Moderate)

Tables `tab:scenarios` and `tab:escenarios` give |C| = 58/40/30/20. The real per-seed values differ, e.g. 41 couriers in S2 and 21 in S4 for seed 2026 (`experiment_summary.csv`). Report the range, or fix |C| per scenario.

### C12 — Distance formula without cos(latitude) (Moderate)

[:1714](../docs/tesisss.tex#L1714) uses 111 km/degree for longitude too. At 24° N, one degree of longitude is about 101 km, so the 2–5 km rule is off by up to about 9%. Use Haversine (it is already in `getrouteOSMR.py`).

### C13 — `docs/tesisss.pdf` is stale (Minor)

`tesisss.tex` was modified 2026-08-05 03:36, but the PDF was built at 01:50. Recompile the thesis before quoting it.

---

## 2. Blocking checks (must pass on the new run before any number goes into the article)

| ID | Check | Pass criterion |
|---|---|---|
| DC1 | No delivery before ready time or before pickup | 0 rows with `delivery_time < ready_time` or `delivery_time < pickup_time`, in every run |
| DC2 | Every seed dispatches | 10/10 seeds × 4 scenarios × 2 policies have delivered orders > 0 |
| DC3 | No double delivery | Σ courier `orders_delivered` == number of delivered rows in the order CSV, in every run |
| DC4 | FCFS baseline as described | FCFS assigns only orders with `ready_time <= t` (or the text explicitly documents the 20-min lookahead) |
| DC5 | Physically plausible CtD | for every delivered order: `CtD >= prep_time + s` (RtD ≥ service time) |

### Reproduction script (read-only; run from the repo root)

```bash
python3 - <<'EOF'
import csv, glob, collections
from datetime import datetime, timedelta
RUN = 'results/experiments/20260413_182745'   # change to the new run id
P = lambda s: datetime.fromisoformat(s) if s else None

# DC1 / DC2 / DC3
for sc in ['S1_baja', 'S2_moderada', 'S3_media', 'S4_alta']:
    for pol in ['fcfs', 'rh']:
        tot = bad_ready = bad_pick = 0; failed = []; dup = 0
        for f in sorted(glob.glob(f'{RUN}/{sc}_seed*/*_{pol}_results.csv')):
            rows = list(csv.DictReader(open(f)))
            deliv = [r for r in rows if r['status'] == 'delivered']
            if not deliv: failed.append(f.split('seed')[1][:4]); continue
            for r in deliv:
                d, rd, pk = P(r['delivery_time']), P(r['ready_time']), P(r['pickup_time'])
                tot += 1; bad_ready += d < rd; bad_pick += d < pk
            cfile = f.replace('_results.csv', '_couriers.csv')
            dup += sum(int(c['orders_delivered']) for c in csv.DictReader(open(cfile))) - len(deliv)
        print(f'{sc:12s} {pol:4s} delivered={tot} deliv<ready={bad_ready} '
              f'deliv<pickup={bad_pick} duplicates={dup} failed_seeds={failed}')

# C2: seeds whose clock never hits minute % 5 == 0
for f in sorted(glob.glob('data/synthetic_lapaz_orders_seed*.csv')):
    rows = list(csv.DictReader(open(f)))
    t0 = min(datetime.fromisoformat(r['created_at']) for r in rows)
    st = t0 - timedelta(minutes=15)
    print(f[-8:-4], 'start', st.time(), 'dispatch runs:', st.minute % 5 == 0)
EOF
```

Expected output on the **current** (invalid) run:
- `deliv<ready` FCFS = 5008 / 4074 / 3208 / 1998;
- RH duplicates > 0;
- failed seeds = 2027, 2033, 2034.

---

## 3. Reporting-consistency checks (after DC1–DC5 pass)

- [ ] SLA differences in **percentage points** in every table and every sentence. Relative % is used only for continuous metrics (CtD, distance).
- [ ] One rounding rule (1 decimal, half-up) applied to every number, in both tables and prose.
- [ ] Actual fleet size per seed reported (range per scenario), not the nominal 58/40/30/20.
- [ ] Coverage reported explicitly: % undelivered per policy and scenario.
- [ ] SLA computed both **over delivered orders** and **over all generated orders** (FCFS survivorship bias; the old draft had 61.2% → 54.1% in S4).
- [ ] Bundle-share figures recomputed from the new run (old draft: 54.2% single orders in S1, 70.3% in bundles of 3–4 in S4).
- [ ] Wilcoxon and Friedman recomputed with **n = 10** seeds. The minimum two-sided Wilcoxon p for n = 10 is 0.00195; for n = 7 it was 0.0156.
- [ ] Crossover point (if it still exists) re-derived from the new `fig_kpi_vs_ratio`.
- [ ] Figures regenerated from the new run and copied to `ponencia/producto_academico/img/`.
- [ ] Each number in the article traced to a CSV cell. Keep a small mapping table in `PLAN.md` or a comment block in the `.tex`.

## 4. Literature checks

- [ ] C6: remove the "10–25%" Reyes claim; rephrase "96%" as "≈4% above optimal mean CtD on small instances".
- [ ] Verify each reference against Crossref (`curl -s https://api.crossref.org/works/<DOI>`) for authors, title, venue, volume, issue, pages and year.
  - Known errors in `docs/ref/biblio.bib`:
    - `Jazemi2023`: the `number` field holds `2413015`; the correct citation is *Applied Sciences* **13**(24), 13015.
    - `Hildebrandt2021`: published in *Transportation Science* **56**(4), 2022 (pages to confirm).
    - `Reyes2018`: Optimization Online preprint. Cite it as such (there is no journal version with this exact title).
- [ ] RIIM rule: most references ≤5 years old (2021+). Plan: 8 of 14.

## 5. Re-run checklist (Phase 0 in `PLAN.md`)

1. Fix C1: sequential route timing with waiting and service time; per-order delivery times inside bundles.
2. Fix C2: dispatch on elapsed time (or align `start` to 5 min).
3. Fix C3: find the remaining duplication path (the 2026-04-04 fix was not enough); add an assertion that an order is delivered at most once.
4. Decide on C4 (purely reactive FCFS vs documented lookahead) and make code and text agree.
5. Optional, needed to keep claim C5: Euclidean control run plus a circuity measurement.
6. Run `python scripts/run_experiments.py --seeds 2025,2026,2027,2028,2029,2030,2031,2032,2033,2034`, then `python scripts/statistical_analysis.py --run-dir results/experiments/<new_run_id>`.
7. Run the script in §2 on the new run. All of DC1–DC5 must pass.
8. Update the thesis (erratum or corrected version) so that thesis and article agree.
