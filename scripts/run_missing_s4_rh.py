"""Run only the missing S4_alta_seed2026 RH simulation into the existing experiment folder."""
import os, sys, time
from datetime import timedelta

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_PATH)

OUTPUT_DIR = os.path.join(BASE_PATH, "results", "experiments", "20260318_002638", "S4_alta_seed2026")
CSV_PATH = os.path.join(BASE_PATH, "data", "synthetic_lapaz_orders_seed2026.csv")

from src import config
from src.main import run_simulation
from src.synth_loader import load_synth_instance

orders, couriers, restaurants, _ = load_synth_instance(
    CSV_PATH, n_couriers=None, orders_per_courier=52, min_couriers=10
)

os.environ["USE_EUCLIDEAN"] = "0"
os.environ.pop("FCFS_POLICY", None)  # RH mode

sim_start = min(min(c.on_time for c in couriers), min(o.placement_time for o in orders))
sim_end = max(c.off_time for c in couriers) + timedelta(hours=1)

rh_orders = os.path.join(OUTPUT_DIR, "synthetic_lapaz_orders_seed2026_rh_results.csv")
rh_couriers = os.path.join(OUTPUT_DIR, "synthetic_lapaz_orders_seed2026_rh_couriers.csv")

print(f"Running S4_alta_seed2026 RH...")
print(f"  Orders: {len(orders)}, Couriers: {len(couriers)}, Restaurants: {len(restaurants)}")
print(f"  Output: {OUTPUT_DIR}")
t0 = time.time()

run_simulation(
    orders, couriers, restaurants, sim_end,
    start_time=sim_start,
    results_path=rh_orders,
    courier_results_path=rh_couriers,
)

elapsed = time.time() - t0
print(f"Done! Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
