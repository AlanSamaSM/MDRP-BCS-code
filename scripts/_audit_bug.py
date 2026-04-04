"""
Audit script: trace double-assignment bug in RH policy.
Reads raw order-level CSVs and courier-level CSVs to verify the mechanism.
"""
import pandas as pd
import os
import glob
import numpy as np

BASE = "results/experiments/20260323_202838"

print("=" * 72)
print("PART 1: Courier-level orders_delivered inflation per scenario/policy")
print("=" * 72)

rows = []
for scn in ["S1_baja", "S2_moderada", "S3_media", "S4_alta"]:
    for d in sorted(glob.glob(f"{BASE}/{scn}_seed*")):
        seed = d.split("seed")[1]
        for pol in ["fcfs", "rh"]:
            ofile = glob.glob(f"{d}/*_{pol}_results.csv")[0]
            cfile = glob.glob(f"{d}/*_{pol}_couriers.csv")[0]
            odf = pd.read_csv(ofile)
            cdf = pd.read_csv(cfile)
            true_del = len(odf[odf["status"] == "delivered"])
            courier_del = cdf["orders_delivered"].sum()
            total_ord = len(odf)
            drive_min = cdf["driving_time_minutes"].sum()
            dist_km = cdf["total_distance_km"].sum()
            hours = cdf["shift_duration_hours"].sum()
            rows.append({
                "scenario": scn, "seed": seed, "policy": pol,
                "total_orders": total_ord,
                "true_delivered": true_del,
                "courier_reported_del": courier_del,
                "inflation": round(courier_del / true_del, 2) if true_del else 0,
                "driving_min": round(drive_min, 1),
                "dist_km": round(dist_km, 1),
                "shift_hours": round(hours, 1),
                "opc_hr_REPORTED": round(courier_del / hours, 2) if hours else 0,
                "opc_hr_TRUE": round(true_del / hours, 2) if hours else 0,
                "util_pct": round(drive_min / 60 / hours * 100, 1) if hours else 0,
                "dist_per_order_REPORTED": round(dist_km / courier_del, 2) if courier_del else 0,
                "dist_per_order_TRUE": round(dist_km / true_del, 2) if true_del else 0,
            })

df = pd.DataFrame(rows)

# Summary by scenario × policy
print("\n--- Mean inflation factor (courier_del / true_del) ---")
summ = df.groupby(["scenario", "policy"]).agg(
    mean_inflation=("inflation", "mean"),
    mean_opc_hr_REPORTED=("opc_hr_REPORTED", "mean"),
    mean_opc_hr_TRUE=("opc_hr_TRUE", "mean"),
    mean_util=("util_pct", "mean"),
    mean_dpo_REPORTED=("dist_per_order_REPORTED", "mean"),
    mean_dpo_TRUE=("dist_per_order_TRUE", "mean"),
).round(2)
print(summ.to_string())

print("\n" + "=" * 72)
print("PART 2: delivery_time overwrite analysis (S4, seed 2025)")
print("=" * 72)

# Load S1 and S4 for detailed analysis
for scn_dir in ["S1_baja_seed2025", "S4_alta_seed2025"]:
    d = f"{BASE}/{scn_dir}"
    seed = scn_dir.split("seed")[1]
    
    fcfs_o = pd.read_csv(glob.glob(f"{d}/*_fcfs_results.csv")[0])
    rh_o = pd.read_csv(glob.glob(f"{d}/*_rh_results.csv")[0])
    
    for c in ["placement_time", "ready_time", "pickup_time", "delivery_time"]:
        fcfs_o[c] = pd.to_datetime(fcfs_o[c], errors="coerce")
        rh_o[c] = pd.to_datetime(rh_o[c], errors="coerce")
    
    fd = fcfs_o[fcfs_o["status"] == "delivered"].copy()
    rd = rh_o[rh_o["status"] == "delivered"].copy()
    
    # Paired comparison on common orders
    common = set(fd["order_id"]) & set(rd["order_id"])
    fc_common = fd[fd["order_id"].isin(common)].set_index("order_id")
    rh_common = rd[rd["order_id"].isin(common)].set_index("order_id")
    
    merged = fc_common[["click_to_door"]].join(
        rh_common[["click_to_door"]], lsuffix="_fcfs", rsuffix="_rh"
    )
    
    fcfs_faster = (merged["click_to_door_fcfs"] < merged["click_to_door_rh"]).sum()
    rh_faster = (merged["click_to_door_fcfs"] > merged["click_to_door_rh"]).sum()
    
    print(f"\n--- {scn_dir} ---")
    print(f"  Common orders: {len(common)}")
    print(f"  FCFS faster: {fcfs_faster} ({fcfs_faster/len(common)*100:.1f}%)")
    print(f"  RH faster:   {rh_faster} ({rh_faster/len(common)*100:.1f}%)")
    print(f"  FCFS-only delivered: {len(fd) - len(common)}")
    print(f"  RH-only delivered:   {len(rd) - len(common)}")
    print(f"  Mean CtD FCFS (common): {merged['click_to_door_fcfs'].mean():.2f}")
    print(f"  Mean CtD RH   (common): {merged['click_to_door_rh'].mean():.2f}")
    print(f"  Median CtD FCFS (common): {merged['click_to_door_fcfs'].median():.2f}")
    print(f"  Median CtD RH   (common): {merged['click_to_door_rh'].median():.2f}")
    
    # Distribution of CtD for RH: the delivery_time is the LAST courier's 
    # completion. Check if there's a pattern.
    print(f"\n  RH CtD percentiles: P10={rd['click_to_door'].quantile(.1):.1f}  "
          f"P50={rd['click_to_door'].median():.1f}  "
          f"P90={rd['click_to_door'].quantile(.9):.1f}  "
          f"P95={rd['click_to_door'].quantile(.95):.1f}")
    print(f"  FCFS CtD percentiles: P10={fd['click_to_door'].quantile(.1):.1f}  "
          f"P50={fd['click_to_door'].median():.1f}  "
          f"P90={fd['click_to_door'].quantile(.9):.1f}  "
          f"P95={fd['click_to_door'].quantile(.95):.1f}")

print("\n" + "=" * 72)
print("PART 3: Driving time and distance inflation analysis")
print("=" * 72)

# Under RH, partial routes also add to driving_time and total_distance
# because the completion handler runs for ALL route types (partial + final)
# Check: if a courier does partial → final, both routes' distance/time are summed.
# This inflates utilization and distance.

for scn_dir in ["S1_baja_seed2025", "S4_alta_seed2025"]:
    d = f"{BASE}/{scn_dir}"
    fc = pd.read_csv(glob.glob(f"{d}/*_fcfs_couriers.csv")[0])
    rc = pd.read_csv(glob.glob(f"{d}/*_rh_couriers.csv")[0])
    
    print(f"\n--- {scn_dir} ---")
    print(f"  FCFS: driving={fc.driving_time_minutes.sum():.0f}min, "
          f"dist={fc.total_distance_km.sum():.0f}km, "
          f"bundles={fc.bundles_picked_up.sum()}")
    print(f"  RH:   driving={rc.driving_time_minutes.sum():.0f}min, "
          f"dist={rc.total_distance_km.sum():.0f}km, "
          f"bundles={rc.bundles_picked_up.sum()}")
    
    # The ratio of RH driving time / FCFS driving time should roughly equal
    # the inflation factor IF the bug is purely from double-assignment
    ratio_drive = rc.driving_time_minutes.sum() / fc.driving_time_minutes.sum()
    ratio_dist = rc.total_distance_km.sum() / fc.total_distance_km.sum()
    print(f"  Ratio driving: {ratio_drive:.2f}x")
    print(f"  Ratio distance: {ratio_dist:.2f}x")

print("\n" + "=" * 72)
print("PART 4: Impact on CtD metrics (order-level CSV — not affected by courier inflation)")
print("=" * 72)

# The order-level CSV has the LAST delivery_time written. 
# With the bug, if Order O is assigned to Courier A (fast, completes T=10)
# then re-assigned to Courier B (slow, completes T=25), the CSV records T=25.
# But if A completes AFTER B, the CSV records A's time.
# The direction depends on which courier finishes last.

# To understand: under normal RH (without bug), only ONE courier would deliver O.
# With the bug, the LAST courier to finish overwrites delivery_time.
# This means: if the first courier is fast and finishes first, and then a second 
# courier is assigned (redundantly) and finishes later, the CtD is INFLATED.
# Conversely, if the second courier happens to be faster (unlikely), CtD deflates.

# Net effect: since the first courier was assigned first (presumably a good match),
# and the second courier is assigned from a later optimization cycle, 
# the second courier likely finishes LATER → CtD is INFLATED on average.

# Let's verify by comparing RH CtD percentiles before and after the theoretical impact
for scn in ["S1_baja", "S4_alta"]:
    fcfs_ctds = []
    rh_ctds = []
    for d in sorted(glob.glob(f"{BASE}/{scn}_seed*")):
        seed = d.split("seed")[1]
        if seed in ["2027", "2033", "2034"]:
            continue
        fo = pd.read_csv(glob.glob(f"{d}/*_fcfs_results.csv")[0])
        ro = pd.read_csv(glob.glob(f"{d}/*_rh_results.csv")[0])
        fcfs_ctds.extend(fo[fo["status"]=="delivered"]["click_to_door"].dropna().tolist())
        rh_ctds.extend(ro[ro["status"]=="delivered"]["click_to_door"].dropna().tolist())
    
    fc = np.array(fcfs_ctds)
    rc = np.array(rh_ctds)
    print(f"\n--- {scn} (all valid seeds pooled) ---")
    print(f"  FCFS: n={len(fc)}, mean={fc.mean():.2f}, median={np.median(fc):.2f}, "
          f"P90={np.percentile(fc,90):.2f}, P95={np.percentile(fc,95):.2f}")
    print(f"  RH:   n={len(rc)}, mean={rc.mean():.2f}, median={np.median(rc):.2f}, "
          f"P90={np.percentile(rc,90):.2f}, P95={np.percentile(rc,95):.2f}")
    
    # Mann-Whitney direction check
    from scipy.stats import mannwhitneyu
    U, p = mannwhitneyu(fc, rc, alternative='two-sided')
    n1, n2 = len(fc), len(rc)
    r = 1 - 2*U/(n1*n2)
    print(f"  Mann-Whitney U={U:.0f}, p={p:.2e}, r={r:.4f} "
          f"({'FCFS<RH (r>0)' if r>0 else 'RH<FCFS (r<0)'})")

print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)
print("""
BUG: two_stage_commitment() in asignaciontentativa.py never sets order.status = 'assigned'
for RH (FCFS does set it on line 42). This causes orders to remain 'ready' after being
assigned to a courier, allowing them to be re-bundled and re-assigned in subsequent
optimization cycles.

AFFECTED METRICS (from courier_summary CSV):
  - orders_delivered: inflated ~2-3x under RH
  - driving_time_minutes: inflated (includes redundant route segments)  
  - total_distance_km: inflated (includes redundant route segments)
  - All derived metrics: opc_hr, utilization, dist/order

PARTIALLY AFFECTED (from order-level CSV):
  - delivery_time: overwritten by LAST completing courier (not first)
  - click_to_door: derived from delivery_time → potentially inflated
  - pickup_time: overwritten by LAST courier
  - courier_id: overwritten by LAST courier
  - bundle_size: overwritten by LAST courier's bundle size

NOT AFFECTED:
  - order count (unique order_ids in CSV)
  - status distribution (each order appears once in CSV)
  - % Undelivered (based on order count)
""")
