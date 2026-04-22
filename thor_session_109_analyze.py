#!/usr/bin/env python3
"""S109 analyzer: phase-ensemble spread vs ρ_sig across cells.

Reports per-cell:
  RAW R_coh, ST R_coh, R_angle
  σ_φ (deg), R_kura_inst, σ_cos, frac_locked
  N_sw, ρ_sig_st

Cross-cell tests:
  P1: σ_φ at ratio 0.2 < at ratio 0.8 for κ_C=0.30 ?  (S108-P6 literal)
  P2: σ_φ at ratio 0.2 > at ratio 0.8 for κ_C=0.30 ?  (R_kura-consistent)
  P3: pairwise |Δφ| bimodal? (fraction in first+last bins vs middle)
  P4: corr(σ_cos, ρ_sig_st) across 6 cells
  P5: σ_φ(kp050, kC=0, r08) < σ_φ(kp030, kC=0, r08) ?

Also compares against S108 R_coh (recomputed with fewer chunks here).
"""
import json
import sys
import numpy as np

sys.stdout.reconfigure(line_buffering=True)


def main():
    with open('thor_session_109_phase_spread_results.json') as f:
        data = json.load(f)

    cells = data['cells']
    meta = data['meta']
    print(f"Session {meta['session']}: {meta['title']}")
    print(f"Per cell: {meta['common_params']['n_seeds']} seeds × "
          f"{meta['common_params']['n_chunks']} chunks × "
          f"{meta['common_params']['chunk_steps']} steps. "
          f"Phase decimate {meta['common_params']['phase_decimate']}.\n")

    # ---- Main results table -----------------------------------------
    hdr = (f"{'label':24s} {'κ_p':>5s} {'κ_C':>5s} {'ratio':>6s} "
           f"{'R_raw':>7s} {'R_st':>7s} {'R_ang_st':>8s} "
           f"{'σ_φ°':>6s} {'R_inst':>7s} {'σ_cos':>7s} "
           f"{'lock%':>6s} {'N_sw':>5s} {'ρ_sig_st':>9s}")
    print(hdr)
    print('-' * len(hdr))

    rows = []
    for name, c in cells.items():
        s = c['summary']
        ratio = c['ratio_omega_over_kappa_phase']
        row = {
            'label': name, 'kp': c['kappa_phase'], 'kC': c['kappa_C'],
            'ratio': ratio,
            'R_raw': s['raw_R_coh_mean'], 'R_raw_sd': s['raw_R_coh_std'],
            'R_st': s['st_R_coh_mean'],  'R_st_sd': s['st_R_coh_std'],
            'R_ang_raw': s['cross_seed_R_angle_raw'],
            'R_ang_st': s['cross_seed_R_angle_st'],
            'sigma_phi_deg': s['sigma_phi_deg_mean'],
            'sigma_phi_sd_rad': s['sigma_phi_rad_std'],
            'R_inst': s['R_inst_mean'], 'R_inst_sd': s['R_inst_std'],
            'sigma_cos': s['sigma_cos_mean'],
            'frac_lock09': s['frac_locked_above_09'],
            'n_sw': s['n_sw_mean'],
            'rho_sig_st': s['rho_sig_st_mean'],
            'rho_sig_sd': s['rho_sig_st_std'],
            'pairwise_dphi_hist': s['pairwise_dphi_hist_mean'],
            'pairwise_dphi_mean_deg': s['pairwise_dphi_mean_deg'],
            'R_kura_stream': s['R_kura_cross_seed_mean'],
        }
        rows.append(row)
        print(f"{name:24s} {c['kappa_phase']:5.2f} {c['kappa_C']:5.2f} "
              f"{ratio:6.2f} "
              f"{row['R_raw']:7.3f} {row['R_st']:7.3f} {row['R_ang_st']:8.3f} "
              f"{row['sigma_phi_deg']:6.1f} {row['R_inst']:7.3f} "
              f"{row['sigma_cos']:7.3f} "
              f"{row['frac_lock09']*100:5.1f}% "
              f"{row['n_sw']:5.0f} {row['rho_sig_st']:9.4f}")

    # ---- Test P1 / P2: σ_φ at ratio 0.2 vs ratio 0.8 at κ_C=0.30 ----
    print()
    rows_by_label = {r['label']: r for r in rows}
    if ('kp030_kC030_r02' in rows_by_label and
            'kp030_kC030_r08' in rows_by_label):
        r02 = rows_by_label['kp030_kC030_r02']
        r08 = rows_by_label['kp030_kC030_r08']
        dsig = r02['sigma_phi_deg'] - r08['sigma_phi_deg']
        print(f"[P1/P2] σ_φ at κ_C=0.30: ratio 0.2 = {r02['sigma_phi_deg']:.1f}°, "
              f"ratio 0.8 = {r08['sigma_phi_deg']:.1f}°   "
              f"Δ(0.2-0.8) = {dsig:+.1f}°")
        if dsig < 0:
            print(f"    → σ_φ smaller at ratio 0.2. S108-P6 SUPPORTED "
                  f"(phase-spread mechanism viable).")
        else:
            print(f"    → σ_φ larger at ratio 0.2. S108-P6 FALSIFIED; "
                  f"P2 (R_kura-consistent) holds.")
        rho_02 = r02['rho_sig_st']
        rho_08 = r08['rho_sig_st']
        print(f"    ρ_sig_st: ratio 0.2 = {rho_02:.4f}, "
              f"ratio 0.8 = {rho_08:.4f}  "
              f"(ratio 0.2/0.8 = {rho_02/rho_08:.2f} — S108 reported 0.39)")

    # ---- Test P3: pairwise |Δφ| bimodality -------------------------
    print("\n[P3] Pairwise |Δφ| histogram (8 bins, 0→π):")
    edges_deg = np.linspace(0, 180, 9)
    headers = ['label'] + [f'{edges_deg[i]:.0f}-{edges_deg[i+1]:.0f}'
                           for i in range(8)] + ['mean°']
    print(' | '.join(f'{h:>10s}' for h in headers))
    for r in rows:
        hist = r['pairwise_dphi_hist']
        bimodal_score = (hist[0] + hist[-1]) - (hist[3] + hist[4])
        vals = [f'{r["label"]:>10s}'] + [f'{h*100:>9.1f}%' for h in hist] \
               + [f'{r["pairwise_dphi_mean_deg"]:>10.1f}']
        print(' | '.join(vals) + f'  [bi={bimodal_score:+.2f}]')

    # ---- Test P4: corr(σ_cos, ρ_sig_st) across cells ---------------
    print()
    sigma_cos_arr = np.array([r['sigma_cos'] for r in rows])
    sigma_phi_arr = np.array([r['sigma_phi_deg'] for r in rows])
    rho_sig_arr = np.array([r['rho_sig_st'] for r in rows])
    n_sw_arr = np.array([r['n_sw'] for r in rows])
    R_inst_arr = np.array([r['R_inst'] for r in rows])
    R_raw_arr = np.array([r['R_raw'] for r in rows])
    R_st_arr = np.array([r['R_st'] for r in rows])
    lock_arr = np.array([r['frac_lock09'] for r in rows])

    def safe_corr(a, b):
        if a.std() == 0 or b.std() == 0:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    print(f"[P4] Cross-cell correlations (N={len(rows)}):")
    print(f"    ρ(σ_cos, ρ_sig_st)   = {safe_corr(sigma_cos_arr, rho_sig_arr):+.3f}")
    print(f"    ρ(σ_φ,   ρ_sig_st)   = {safe_corr(sigma_phi_arr, rho_sig_arr):+.3f}")
    print(f"    ρ(R_inst,ρ_sig_st)   = {safe_corr(R_inst_arr,  rho_sig_arr):+.3f}")
    print(f"    ρ(lock%, ρ_sig_st)   = {safe_corr(lock_arr,     rho_sig_arr):+.3f}")
    print(f"    ρ(σ_cos, R_raw)      = {safe_corr(sigma_cos_arr, R_raw_arr):+.3f}")
    print(f"    ρ(σ_φ,   R_raw)      = {safe_corr(sigma_phi_arr, R_raw_arr):+.3f}")
    print(f"    ρ(σ_cos, R_st)       = {safe_corr(sigma_cos_arr, R_st_arr):+.3f}")
    print(f"    ρ(N_sw,  ρ_sig_st)   = {safe_corr(n_sw_arr,     rho_sig_arr):+.3f}")

    # ---- Test P5: σ_φ at kp=0.5 vs kp=0.3, both kC=0, r08 ---------
    print()
    if ('kp050_kC000_r08' in rows_by_label and
            'kp030_kC000_r08' in rows_by_label):
        r50 = rows_by_label['kp050_kC000_r08']
        r30 = rows_by_label['kp030_kC000_r08']
        dsig = r50['sigma_phi_deg'] - r30['sigma_phi_deg']
        drho = r50['rho_sig_st'] - r30['rho_sig_st']
        print(f"[P5] At κ_C=0, ratio 0.8:")
        print(f"    κ_p=0.30: σ_φ = {r30['sigma_phi_deg']:.1f}°, "
              f"ρ_sig_st = {r30['rho_sig_st']:.4f}")
        print(f"    κ_p=0.50: σ_φ = {r50['sigma_phi_deg']:.1f}°, "
              f"ρ_sig_st = {r50['rho_sig_st']:.4f}")
        print(f"    Δσ_φ = {dsig:+.1f}°   Δρ_sig = {drho:+.4f}")
        print(f"    R_raw: κ_p=0.30 → {r30['R_raw']:.3f}, "
              f"κ_p=0.50 → {r50['R_raw']:.3f}  "
              f"(Δ = {r50['R_raw']-r30['R_raw']:+.3f})")
        if dsig < 0 and drho < 0:
            print(f"    → P5 SUPPORTED: stronger κ_p tightens phase-lock "
                  f"AND drops ρ_sig. Sign-reversal mechanism confirmed.")
        elif dsig < 0 and drho > 0:
            print(f"    → Mixed: phase tightens but ρ_sig INCREASES — "
                  f"phase-spread doesn't explain the sign reversal.")
        else:
            print(f"    → Mixed or opposite direction on σ_φ — revisit.")

    # ---- Save analysis ----------------------------------------------
    analysis = {
        'meta': {'session': 109, 'analyzer': 'thor_session_109_analyze.py'},
        'table': rows,
        'P1_P2_phase_spread_test': {
            'sigma_phi_deg_ratio02_kC030': (
                rows_by_label.get('kp030_kC030_r02', {}).get('sigma_phi_deg')),
            'sigma_phi_deg_ratio08_kC030': (
                rows_by_label.get('kp030_kC030_r08', {}).get('sigma_phi_deg')),
        },
        'P4_cross_cell_corr': {
            'sigma_cos_vs_rho_sig': safe_corr(sigma_cos_arr, rho_sig_arr),
            'sigma_phi_vs_rho_sig': safe_corr(sigma_phi_arr, rho_sig_arr),
            'R_inst_vs_rho_sig':   safe_corr(R_inst_arr, rho_sig_arr),
            'lock_vs_rho_sig':     safe_corr(lock_arr, rho_sig_arr),
            'sigma_cos_vs_R_raw':  safe_corr(sigma_cos_arr, R_raw_arr),
            'sigma_cos_vs_R_st':   safe_corr(sigma_cos_arr, R_st_arr),
            'n_sw_vs_rho_sig':     safe_corr(n_sw_arr, rho_sig_arr),
        },
    }
    with open('thor_session_109_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=float)
    print("\nWrote thor_session_109_analysis.json")


if __name__ == '__main__':
    main()
