#!/usr/bin/env python3
"""S115 analyzer: lock@sw vs dip presence (S114-P5 direct test).

Loads S115 (4 κ_C × 3 A grid) and S113 (recycled κ_C=0.30 line at
A ∈ {0.30, 0.40, 0.50}) and assembles a 5×3 (κ_C × A) table.

Key tests:
  P1: lock@sw monotone in κ_C at A=0.40 (and at all A).
  P2: dip presence (rho_sig(A=0.40) below mid-point of rho_sig at
      A=0.30 and A=0.50) appears only above some lock@sw threshold.
  P3: wedge angle Δφ_aL,rN at A=0.40 grows with κ_C.
  P4: att_lock class fraction at A=0.40 grows with κ_C.
  P5: total μ_arg at A=0.40 rotates with κ_C.

Reports a per-κ_C row with all key numbers, plus a Spearman ρ between
dip_score and lock@sw across the κ_C axis.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(line_buffering=True)


def load_s115(path='thor_session_115_kc_dip_gate_results.json'):
    if not Path(path).exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_s113(path='thor_session_113_dip_decomp_results.json'):
    """S113 baseline at κ_C=0.30 — A ∈ {0.30, 0.40, 0.50} extracted."""
    if not Path(path).exists():
        return None
    with open(path) as f:
        return json.load(f)


def cell_row(cell, source):
    s = cell['summary']
    ca = s['class_agg']
    aL_arg = ca['att_lock']['mu_arg_per_seed_circmean_deg']
    rN_arg = ca['rep_noise']['mu_arg_per_seed_circmean_deg']
    # Wedge angle (geodesic, in [0,180])
    diff = aL_arg - rN_arg
    wedge = abs(((diff + 180.0) % 360.0) - 180.0)
    n_seeds = s.get('n_seeds', 16)
    rho_std = s['rho_sig_st_std']
    rho_sem = s.get('rho_sig_st_sem', rho_std / np.sqrt(max(1, n_seeds)))
    return {
        'kappa_phase': cell['kappa_phase'],
        'kappa_C':     cell['kappa_C'],
        'omega_std':   cell['omega_std'],
        'A':           cell['signal_amp'],
        'rho_sig':     s['rho_sig_st_mean'],
        'rho_sig_sem': rho_sem,
        'rho_sig_std': rho_std,
        'mu_st':       s['st_mu_mean'],
        'mu_arg_deg':  s['st_mu_arg_circmean_deg'],
        'R_ang':       s['st_mu_arg_R'],
        'R_kura':      s['kura_mean_mean'],
        'lock_frac':   s['lock_frac_global_mean'],
        'lock_at_sw':  s['lock_at_switch_frac_mean'],
        'lock_at_sw_std': s.get('lock_at_switch_frac_std', 0.0),
        'att_at_sw':   s['gate_att_at_switch_frac_mean'],
        'n_sw':        s['n_sw_total_mean'],
        'aL_frac':     ca['att_lock']['fraction_of_sw'],
        'aN_frac':     ca['att_noise']['fraction_of_sw'],
        'rL_frac':     ca['rep_lock']['fraction_of_sw'],
        'rN_frac':     ca['rep_noise']['fraction_of_sw'],
        'aL_mu':       ca['att_lock']['mu_abs_per_seed_mean'],
        'aN_mu':       ca['att_noise']['mu_abs_per_seed_mean'],
        'rL_mu':       ca['rep_lock']['mu_abs_per_seed_mean'],
        'rN_mu':       ca['rep_noise']['mu_abs_per_seed_mean'],
        'aL_arg':      aL_arg,
        'rN_arg':      rN_arg,
        'wedge_aL_rN': wedge,
        'source':      source,
    }


def spearman(xs, ys):
    n = len(xs)
    rx = np.argsort(np.argsort(xs))
    ry = np.argsort(np.argsort(ys))
    rx_dm = rx - rx.mean()
    ry_dm = ry - ry.mean()
    return float((rx_dm * ry_dm).sum() / np.sqrt((rx_dm**2).sum() * (ry_dm**2).sum()))


def main():
    s115 = load_s115()
    s113 = load_s113()
    if s115 is None:
        print("S115 results not found — has the main run completed?")
        return

    # 1. Pull all S115 cells
    rows = []
    for label, cell in s115['cells'].items():
        rows.append(cell_row(cell, source='S115'))

    # 2. Splice S113 cells at κ_C=0.30 for A ∈ {0.30, 0.40, 0.50}
    if s113 is not None:
        for label, cell in s113['cells'].items():
            A = cell['signal_amp']
            if A in (0.30, 0.40, 0.50) and abs(cell.get('kappa_C', 0.30) - 0.30) < 1e-6:
                rows.append(cell_row(cell, source='S113'))

    # 3. Group by κ_C
    rows_sorted = sorted(rows, key=lambda r: (r['kappa_C'], r['A']))
    kc_vals = sorted(set(r['kappa_C'] for r in rows_sorted))
    print("\n=== Per-cell summary (sorted by κ_C, A) ===")
    print(f"{'κ_C':>5} {'A':>4} {'ρ_sig':>9} {'sem':>7} {'lock@sw':>8} "
          f"{'wedge°':>7} {'aL_frac':>7} {'arg_tot':>8} {'src':>5}")
    for r in rows_sorted:
        print(f"{r['kappa_C']:5.2f} {r['A']:4.2f} "
              f"{r['rho_sig']:9.4f} {r['rho_sig_sem']:7.4f} "
              f"{r['lock_at_sw']:8.3f} {r['wedge_aL_rN']:7.1f} "
              f"{r['aL_frac']:7.3f} {r['mu_arg_deg']:+8.1f} "
              f"{r['source']:>5}")

    # 4. Per-κ_C row at A=0.40 with the dip score
    print("\n=== Per-κ_C row at the dip-A (A=0.40) ===")
    print(f"{'κ_C':>5} {'lock@sw':>8} {'wedge°':>7} {'rho(0.30)':>10} "
          f"{'rho(0.40)':>10} {'rho(0.50)':>10} {'mid':>10} "
          f"{'dip_abs':>8} {'dip_pct':>7} {'z_dip':>7}")
    summary_rows = []
    for kc in kc_vals:
        cells_at = {r['A']: r for r in rows_sorted if r['kappa_C'] == kc}
        if not all(A in cells_at for A in (0.30, 0.40, 0.50)):
            continue
        c30, c40, c50 = cells_at[0.30], cells_at[0.40], cells_at[0.50]
        mid = 0.5 * (c30['rho_sig'] + c50['rho_sig'])
        dip_abs = c40['rho_sig'] - mid
        dip_pct = 100.0 * dip_abs / mid if mid > 0 else 0.0
        # Standard error of dip_abs: sqrt(sem_40^2 + 0.25*(sem_30^2+sem_50^2))
        sem_dip = np.sqrt(c40['rho_sig_sem']**2
                           + 0.25 * (c30['rho_sig_sem']**2
                                     + c50['rho_sig_sem']**2))
        z_dip = dip_abs / sem_dip if sem_dip > 0 else 0.0
        print(f"{kc:5.2f} {c40['lock_at_sw']:8.3f} {c40['wedge_aL_rN']:7.1f} "
              f"{c30['rho_sig']:10.4f} {c40['rho_sig']:10.4f} "
              f"{c50['rho_sig']:10.4f} {mid:10.4f} "
              f"{dip_abs:+8.4f} {dip_pct:+7.2f} {z_dip:+7.2f}")
        summary_rows.append({
            'kappa_C': kc,
            'lock_at_sw_A040': c40['lock_at_sw'],
            'wedge_aL_rN_A040': c40['wedge_aL_rN'],
            'rho_A030': c30['rho_sig'],
            'rho_A040': c40['rho_sig'],
            'rho_A050': c50['rho_sig'],
            'rho_mid_30_50': mid,
            'dip_abs': dip_abs,
            'dip_pct': dip_pct,
            'z_dip': z_dip,
            'aL_frac_A040': c40['aL_frac'],
            'mu_arg_A040_deg': c40['mu_arg_deg'],
            'aL_arg_A040_deg': c40['aL_arg'],
            'rN_arg_A040_deg': c40['rN_arg'],
            'R_kura_A040': c40['R_kura'],
            'mu_st_A040': c40['mu_st'],
            'aL_mu_A040': c40['aL_mu'],
            'rN_mu_A040': c40['rN_mu'],
            'rho_A040_sem': c40['rho_sig_sem'],
        })

    # 5. Correlations across κ_C axis
    print("\n=== Cross-κ_C correlations ===")
    if len(summary_rows) >= 3:
        kc_arr = np.array([s['kappa_C']        for s in summary_rows])
        lock_arr = np.array([s['lock_at_sw_A040'] for s in summary_rows])
        wedge_arr = np.array([s['wedge_aL_rN_A040'] for s in summary_rows])
        dip_arr = np.array([s['dip_abs']          for s in summary_rows])
        zdip_arr = np.array([s['z_dip']           for s in summary_rows])
        aL_frac_arr = np.array([s['aL_frac_A040'] for s in summary_rows])
        arg_arr = np.array([s['mu_arg_A040_deg']  for s in summary_rows])
        rho40_arr = np.array([s['rho_A040']       for s in summary_rows])

        # P1
        print(f"P1 (lock@sw monotone in κ_C):")
        print(f"  κ_C: {kc_arr}")
        print(f"  lock@sw: {lock_arr.round(3)}")
        print(f"  Spearman ρ(κ_C, lock@sw) = {spearman(kc_arr, lock_arr):+.3f}")
        # P2
        print(f"\nP2 (dip presence vs lock@sw):")
        print(f"  lock@sw: {lock_arr.round(3)}")
        print(f"  dip_abs: {dip_arr.round(4)}")
        print(f"  z_dip:   {zdip_arr.round(2)}")
        print(f"  Spearman ρ(lock@sw, dip_abs) = {spearman(lock_arr, dip_arr):+.3f}")
        print(f"  (dip_abs < 0 means dip present)")
        # Threshold check
        crossing = "no crossing"
        for i in range(1, len(kc_arr)):
            if (dip_arr[i-1] > 0) != (dip_arr[i] > 0):
                crossing = (f"sign flip between κ_C={kc_arr[i-1]:.2f} "
                            f"(lock@sw={lock_arr[i-1]:.3f}) and "
                            f"κ_C={kc_arr[i]:.2f} (lock@sw={lock_arr[i]:.3f})")
                break
        print(f"  Threshold: {crossing}")
        # P3
        print(f"\nP3 (wedge grows with κ_C):")
        print(f"  wedge°: {wedge_arr.round(1)}")
        print(f"  Spearman ρ(κ_C, wedge°) = {spearman(kc_arr, wedge_arr):+.3f}")
        # P4
        print(f"\nP4 (att_lock fraction grows with κ_C):")
        print(f"  aL_frac: {aL_frac_arr.round(3)}")
        print(f"  Spearman ρ(κ_C, aL_frac) = {spearman(kc_arr, aL_frac_arr):+.3f}")
        # P5
        print(f"\nP5 (μ_arg shifts with κ_C):")
        print(f"  μ_arg_A040: {arg_arr.round(1)}")
        print(f"  range: {arg_arr.max() - arg_arr.min():.1f}°")

        out = {
            'session': 115,
            'analysis_of': ['thor_session_115_kc_dip_gate_results.json',
                            'thor_session_113_analysis.json'],
            'per_cell': rows_sorted,
            'per_kc_at_dipA': summary_rows,
            'correlations': {
                'spearman_kC_lock_at_sw': spearman(kc_arr, lock_arr),
                'spearman_lock_at_sw_dip_abs': spearman(lock_arr, dip_arr),
                'spearman_kC_wedge': spearman(kc_arr, wedge_arr),
                'spearman_kC_aL_frac': spearman(kc_arr, aL_frac_arr),
                'kC_arr': kc_arr.tolist(),
                'lock_at_sw_arr': lock_arr.tolist(),
                'wedge_arr': wedge_arr.tolist(),
                'dip_abs_arr': dip_arr.tolist(),
                'z_dip_arr': zdip_arr.tolist(),
                'aL_frac_arr': aL_frac_arr.tolist(),
                'mu_arg_arr': arg_arr.tolist(),
                'rho_A040_arr': rho40_arr.tolist(),
            },
        }
        with open('thor_session_115_analysis.json', 'w') as f:
            json.dump(out, f, indent=2, default=float)
        print("\nAnalysis → thor_session_115_analysis.json")


if __name__ == '__main__':
    main()
