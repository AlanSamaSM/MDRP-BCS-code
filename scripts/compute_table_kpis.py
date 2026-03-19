"""Compute KPIs from experiment CSVs for thesis tables (2 seeds)."""
import pandas as pd, numpy as np, os
from scipy.stats import mannwhitneyu

base = os.path.join('results', 'experiments', '20260318_002638')
scenarios = {
    'S1': ['S1_baja_seed2025', 'S1_baja_seed2026'],
    'S2': ['S2_moderada_seed2025', 'S2_moderada_seed2026'],
    'S3': ['S3_media_seed2025', 'S3_media_seed2026'],
    'S4': ['S4_alta_seed2025', 'S4_alta_seed2026'],
}

p1, p2, shift, sla = 10.0, 15.0, 11.0, 40.0

def dpct(f, r):
    if f == 0: return '--'
    return f'{((r-f)/abs(f))*100:+.1f}'

for sid, folders in scenarios.items():
    fa, ra, fca, rca = [], [], [], []
    for f in folders:
        fp = os.path.join(base, f)
        fls = os.listdir(fp)
        fa.append(pd.read_csv(os.path.join(fp, [x for x in fls if 'fcfs_results' in x][0])))
        ra.append(pd.read_csv(os.path.join(fp, [x for x in fls if 'rh_results' in x][0])))
        fca.append(pd.read_csv(os.path.join(fp, [x for x in fls if 'fcfs_couriers' in x][0])))
        rca.append(pd.read_csv(os.path.join(fp, [x for x in fls if 'rh_couriers' in x][0])))
    ns = len(folders)
    fcfs = pd.concat(fa); rh = pd.concat(ra)
    fc = pd.concat(fca); rc = pd.concat(rca)
    nc = len(fca[0])  # couriers per seed
    fd = fcfs[fcfs.status=='delivered']; rd = rh[rh.status=='delivered']
    fn = len(fd)/ns; rn = len(rd)/ns  # avg delivered per seed

    # CtD
    f_avg = fd.click_to_door.mean(); r_avg = rd.click_to_door.mean()
    f_p90 = fd.click_to_door.quantile(.9); r_p90 = rd.click_to_door.quantile(.9)
    f_sla = (fd.click_to_door<=sla).mean()*100; r_sla = (rd.click_to_door<=sla).mean()*100
    # RtP
    f_rtp = fd.ready_to_pickup.mean(); r_rtp = rd.ready_to_pickup.mean()
    # Overage
    f_ov = np.maximum(fd.click_to_door-sla, 0).mean()
    r_ov = np.maximum(rd.click_to_door-sla, 0).mean()
    # Undelivered
    f_up = (fcfs.status!='delivered').mean()*100; r_up = (rh.status!='delivered').mean()*100
    # Efficiency
    ftk = fc.total_distance_km.sum()/ns; rtk = rc.total_distance_km.sum()/ns
    f_dpo = ftk/fn if fn else 0; r_dpo = rtk/rn if rn else 0
    f_ochr = fn/nc/shift; r_ochr = rn/nc/shift
    f_ut = fc.driving_time_minutes.sum()/ns/(nc*shift*60)*100
    r_ut = rc.driving_time_minutes.sum()/ns/(nc*shift*60)*100
    # Bundle
    f_bs = fd.bundle_size.mean(); r_bs = rd.bundle_size.mean()
    f_pm = (fd.bundle_size>1).mean()*100; r_pm = (rd.bundle_size>1).mean()*100
    # Cost (from results, not inflated courier CSV)
    f_opc = fd.groupby('courier_id').size()
    r_opc = rd.groupby('courier_id').size()
    f_comp = sum(max(n/ns*p1, p2*shift) for n in f_opc) + (nc - f_opc.index.nunique())*p2*shift
    r_comp = sum(max(n/ns*p1, p2*shift) for n in r_opc) + (nc - r_opc.index.nunique())*p2*shift
    f_cpo = f_comp/fn if fn else 0; r_cpo = r_comp/rn if rn else 0
    # Mann-Whitney
    u, p = mannwhitneyu(fd.click_to_door, rd.click_to_door, alternative='two-sided')
    rb = 1 - 2*u/(len(fd)*len(rd))
    eff = 'Neg.' if abs(rb)<.1 else 'Peq.' if abs(rb)<.3 else 'Med.' if abs(rb)<.5 else 'Grande'

    print(f'=== {sid} (nc={nc}, seeds={ns}, delivered F={fn:.0f} R={rn:.0f}) ===')
    print(f'  AvgCtD:  F={f_avg:.2f}  R={r_avg:.2f}  D={dpct(f_avg,r_avg)}')
    print(f'  P90CtD:  F={f_p90:.2f}  R={r_p90:.2f}  D={dpct(f_p90,r_p90)}')
    print(f'  SLA%:    F={f_sla:.1f}  R={r_sla:.1f}  D={dpct(f_sla,r_sla)}')
    print(f'  AvgRtP:  F={f_rtp:.2f}  R={r_rtp:.2f}  D={dpct(f_rtp,r_rtp)}')
    print(f'  Overage: F={f_ov:.2f}  R={r_ov:.2f}  D={dpct(f_ov,r_ov)}')
    print(f'  Undel%:  F={f_up:.1f}  R={r_up:.1f}')
    print(f'  Ord/C/H: F={f_ochr:.2f}  R={r_ochr:.2f}  D={dpct(f_ochr,r_ochr)}')
    print(f'  Util%:   F={f_ut:.1f}  R={r_ut:.1f}  D={dpct(f_ut,r_ut)}')
    print(f'  Dist/O:  F={f_dpo:.2f}  R={r_dpo:.2f}  D={dpct(f_dpo,r_dpo)}')
    print(f'  AvgBS:   F={f_bs:.2f}  R={r_bs:.2f}  D={dpct(f_bs,r_bs)}')
    print(f'  %Multi:  F={f_pm:.1f}  R={r_pm:.1f}  Dp={r_pm-f_pm:.1f}')
    print(f'  Cost/O:  F={f_cpo:.2f}  R={r_cpo:.2f}  D={dpct(f_cpo,r_cpo)}')
    print(f'  MW: U={u:.0f} p={p:.2e} r={rb:.3f} {eff}')
    print()
