#!/usr/bin/env python3
"""S116 analyzer: past-ridge κ_C — signal rescue and aL_arg rotation.

Loads:
  - S116 primary cells (κ_C ∈ {0.50, 0.60, 0.70} × A ∈ {0.30, 0.40, 0.50, 0.60})
    + anchor κ_C=0.40 A=0.60
  - S115 cells (κ_C ∈ {0.05, 0.15, 0.25, 0.40} × A ∈ {0.30, 0.40, 0.50}) for context
  - S113 cells (κ_C=0.30 × A ∈ {0.30, 0.40, 0.50})

Builds a unified κ_C × A table spanning {0.05, 0.15, 0.25, 0.30, 0.40, 0.50,
0.60, 0.70} × {0.30, 0.40, 0.50, 0.60}.

Key tests:
  P1: signal-rescue dR_kura/dA monotone in κ_C
  P2: aL_arg(κ_C) at A=0.40 — extends S115 series, predict κ_C=0.70 ≈ -15°,
      S115-P4 claimed 0° at κ_C ≈ 0.55 (competing prediction κ_C ≈ 0.75)
  P3: ρ_sig recovery with A in over-collapsed regime
       (dρ_sig/dA larger at higher κ_C past saturation)
  P4: lock@sw asymptotes near 1.0 at κ_C ≳ 0.70
  P5: wedge geometry past saturation (maintains ~57°, shrinks, or widens?)
  P6: mod_amp_at_fs vs A across κ_C
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(line_buffering=True)


def load_json(path):
    if not Path(path).exists():
        return None
    with open(path) as f:
        return json.load(f)


def cell_row(cell, source):
    s = cell['summary']
    ca = s['class_agg']
    aL_arg = ca['att_lock']['mu_arg_per_seed_circmean_deg']
    rN_arg = ca['rep_noise']['mu_arg_per_seed_circmean_deg']
    aN_arg = ca['att_noise']['mu_arg_per_seed_circmean_deg']
    rL_arg = ca['rep_lock']['mu_arg_per_seed_circmean_deg']
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
        'R_kura_std':  s.get('kura_mean_std', 0.0),
        'lock_frac':   s['lock_frac_global_mean'],
        'lock_at_sw':  s['lock_at_switch_frac_mean'],
        'lock_at_sw_std': s.get('lock_at_switch_frac_std', 0.0),
        'att_at_sw':   s['gate_att_at_switch_frac_mean'],
        'n_sw':        s['n_sw_total_mean'],
        'mod_amp_lock': s.get('mod_amp_at_fs_lock_mean', 0.0),
        'mod_amp_kura': s.get('mod_amp_at_fs_kura_mean', 0.0),
        'aL_frac':     ca['att_lock']['fraction_of_sw'],
        'aN_frac':     ca['att_noise']['fraction_of_sw'],
        'rL_frac':     ca['rep_lock']['fraction_of_sw'],
        'rN_frac':     ca['rep_noise']['fraction_of_sw'],
        'aL_mu':       ca['att_lock']['mu_abs_per_seed_mean'],
        'aN_mu':       ca['att_noise']['mu_abs_per_seed_mean'],
        'rL_mu':       ca['rep_lock']['mu_abs_per_seed_mean'],
        'rN_mu':       ca['rep_noise']['mu_abs_per_seed_mean'],
        'aL_arg':      aL_arg,
        'aN_arg':      aN_arg,
        'rL_arg':      rL_arg,
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
    return float((rx_dm * ry_dm).sum()
                  / np.sqrt((rx_dm**2).sum() * (ry_dm**2).sum()))


def linfit(x, y):
    """OLS y = a + b·x; return (a, b, r2)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    sx, sy = x.mean(), y.mean()
    Sxx = ((x - sx)**2).sum()
    Sxy = ((x - sx) * (y - sy)).sum()
    Syy = ((y - sy)**2).sum()
    b = Sxy / Sxx if Sxx > 0 else 0.0
    a = sy - b * sx
    r2 = (Sxy**2 / (Sxx * Syy)) if Sxx > 0 and Syy > 0 else 0.0
    return float(a), float(b), float(r2)


def main():
    s116 = load_json('thor_session_116_past_ridge_results.json')
    s115 = load_json('thor_session_115_kc_dip_gate_results.json')
    s113 = load_json('thor_session_113_dip_decomp_results.json')
    if s116 is None:
        print("S116 results not found — has the main run completed?")
        return

    rows = []
    for label, cell in s116['cells'].items():
        rows.append(cell_row(cell, source='S116'))
    if s115 is not None:
        for label, cell in s115['cells'].items():
            rows.append(cell_row(cell, source='S115'))
    if s113 is not None:
        for label, cell in s113['cells'].items():
            A = cell['signal_amp']
            kc = cell.get('kappa_C', 0.30)
            if A in (0.30, 0.40, 0.50) and abs(kc - 0.30) < 1e-6:
                rows.append(cell_row(cell, source='S113'))

    # Sort
    rows_sorted = sorted(rows, key=lambda r: (r['kappa_C'], r['A']))
    kc_vals = sorted(set(r['kappa_C'] for r in rows_sorted))
    A_vals = sorted(set(r['A'] for r in rows_sorted))

    print("\n=== Per-cell summary (sorted by κ_C, A) ===")
    print(f"{'κ_C':>5} {'A':>4} {'ρ_sig':>9} {'sem':>7} {'lock@sw':>8} "
          f"{'wedge°':>7} {'aL_arg':>8} {'R_kura':>7} {'<Nsw>':>6} "
          f"{'mod_lk':>7} {'src':>5}")
    for r in rows_sorted:
        print(f"{r['kappa_C']:5.2f} {r['A']:4.2f} "
              f"{r['rho_sig']:9.4f} {r['rho_sig_sem']:7.4f} "
              f"{r['lock_at_sw']:8.3f} {r['wedge_aL_rN']:7.1f} "
              f"{r['aL_arg']:+8.1f} {r['R_kura']:7.3f} {r['n_sw']:6.0f} "
              f"{r['mod_amp_lock']:7.4f} "
              f"{r['source']:>5}")

    # === P1: signal-rescue dR_kura/dA monotone in κ_C ===
    print("\n=== P1: Signal-rescue dR_kura/dA across κ_C ===")
    print(f"{'κ_C':>5} {'A=0.30':>8} {'A=0.40':>8} {'A=0.50':>8} {'A=0.60':>8} "
          f"{'ΔR(.3→.5)':>10} {'ΔR(.3→.6)':>10} {'slope':>7}")
    rescue_rows = []
    for kc in kc_vals:
        cells_at = {r['A']: r for r in rows_sorted if r['kappa_C'] == kc}
        a_have = sorted(cells_at.keys())
        vals = []
        Avals = []
        for A in [0.30, 0.40, 0.50, 0.60]:
            if A in cells_at:
                vals.append(cells_at[A]['R_kura'])
                Avals.append(A)
            else:
                vals.append(None)
        r30 = vals[0]
        r50 = vals[2]
        r60 = vals[3]
        dR_3_5 = (r50 - r30) if (r30 is not None and r50 is not None) else None
        dR_3_6 = (r60 - r30) if (r30 is not None and r60 is not None) else None
        # slope over what we have
        if len(Avals) >= 2:
            xs = []
            ys = []
            for A, v in zip([0.30, 0.40, 0.50, 0.60], vals):
                if v is not None:
                    xs.append(A); ys.append(v)
            _, slope, _ = linfit(xs, ys)
        else:
            slope = None
        fmt = lambda v: f'{v:8.3f}' if v is not None else '       -'
        fmt2 = lambda v: f'{v:+10.3f}' if v is not None else '         -'
        fmt3 = lambda v: f'{v:+7.3f}' if v is not None else '      -'
        print(f"{kc:5.2f} {fmt(r30)} {fmt(vals[1])} {fmt(r50)} {fmt(r60)} "
              f"{fmt2(dR_3_5)} {fmt2(dR_3_6)} {fmt3(slope)}")
        rescue_rows.append({
            'kappa_C': kc, 'R_kura_by_A': vals, 'A_grid': [0.30, 0.40, 0.50, 0.60],
            'dR_3_5': dR_3_5, 'dR_3_6': dR_3_6, 'slope_R_vs_A': slope,
        })

    # Spearman test on monotonicity
    # Use slope_R_vs_A if available for past-ridge cells (κ_C ≥ 0.30)
    past_ridge = [(rr['kappa_C'], rr['slope_R_vs_A']) for rr in rescue_rows
                  if rr['kappa_C'] >= 0.30 and rr['slope_R_vs_A'] is not None]
    if len(past_ridge) >= 3:
        kc_arr = np.array([p[0] for p in past_ridge])
        sl_arr = np.array([p[1] for p in past_ridge])
        print(f"\n  Spearman ρ(κ_C, dR/dA) for κ_C ≥ 0.30: {spearman(kc_arr, sl_arr):+.3f}")

    # === P2: aL_arg(κ_C) at A=0.40 — does it cross 0°? ===
    print("\n=== P2: aL_arg(κ_C) at A=0.40 (S115-P4 test) ===")
    print(f"{'κ_C':>5} {'aL_arg':>9} {'rN_arg':>9} {'wedge°':>7} {'aL_frac':>8} {'|μ_aL|':>7} {'src':>5}")
    aL_rows = []
    for kc in kc_vals:
        cells_at = {r['A']: r for r in rows_sorted if r['kappa_C'] == kc}
        if 0.40 in cells_at:
            r = cells_at[0.40]
            print(f"{kc:5.2f} {r['aL_arg']:+9.1f} {r['rN_arg']:+9.1f} "
                  f"{r['wedge_aL_rN']:7.1f} {r['aL_frac']:8.3f} {r['aL_mu']:7.1f} "
                  f"{r['source']:>5}")
            aL_rows.append({
                'kappa_C': kc, 'aL_arg': r['aL_arg'], 'rN_arg': r['rN_arg'],
                'wedge': r['wedge_aL_rN'], 'aL_frac': r['aL_frac'],
                'aL_mu': r['aL_mu'], 'rN_mu': r['rN_mu'],
                'source': r['source'],
            })

    # Find sign crossing
    if len(aL_rows) >= 2:
        for i in range(1, len(aL_rows)):
            a0 = aL_rows[i-1]['aL_arg']
            a1 = aL_rows[i]['aL_arg']
            if (a0 < 0) != (a1 < 0):
                # Linear interp crossing
                kc0 = aL_rows[i-1]['kappa_C']
                kc1 = aL_rows[i]['kappa_C']
                frac = -a0 / (a1 - a0)
                kc_cross = kc0 + frac * (kc1 - kc0)
                print(f"\n  *** aL_arg sign-crossing at κ_C ≈ {kc_cross:.3f} ***")
                print(f"      (interpolated between κ_C={kc0:.2f} aL_arg={a0:+.1f}°"
                      f" and κ_C={kc1:.2f} aL_arg={a1:+.1f}°)")
                break
        else:
            # No crossing found
            last = aL_rows[-1]
            print(f"\n  aL_arg has NOT crossed 0° within tested range "
                  f"(max κ_C={last['kappa_C']:.2f} → aL_arg={last['aL_arg']:+.1f}°)")
            # Extrapolate
            if len(aL_rows) >= 3:
                # Use last 3 points
                xs = [r['kappa_C'] for r in aL_rows[-3:]]
                ys = [r['aL_arg'] for r in aL_rows[-3:]]
                _, slope, r2 = linfit(xs, ys)
                if slope > 0:
                    a_last = aL_rows[-1]
                    kc_extrap = a_last['kappa_C'] + (-a_last['aL_arg']) / slope
                    print(f"  Linear extrapolation (last 3): slope={slope:+.1f}°/κ_C, "
                          f"crosses 0° at κ_C ≈ {kc_extrap:.3f}")

    # === P3: ρ_sig recovery with A across κ_C ===
    print("\n=== P3: ρ_sig(A) slope across κ_C ===")
    print(f"{'κ_C':>5} {'ρ(.30)':>8} {'ρ(.40)':>8} {'ρ(.50)':>8} {'ρ(.60)':>8} "
          f"{'slope':>8} {'Δ(.3→.6)':>9} {'frac_gain':>10}")
    rho_rows = []
    for kc in kc_vals:
        cells_at = {r['A']: r for r in rows_sorted if r['kappa_C'] == kc}
        vals = []
        for A in [0.30, 0.40, 0.50, 0.60]:
            vals.append(cells_at[A]['rho_sig'] if A in cells_at else None)
        # slope over what we have
        xs = []; ys = []
        for A, v in zip([0.30, 0.40, 0.50, 0.60], vals):
            if v is not None:
                xs.append(A); ys.append(v)
        slope = None
        if len(xs) >= 2:
            _, slope, _ = linfit(xs, ys)
        gain = None
        frac_gain = None
        if vals[0] is not None and vals[3] is not None:
            gain = vals[3] - vals[0]
            frac_gain = (vals[3] - vals[0]) / vals[0] if vals[0] > 1e-6 else None
        fmt = lambda v: f'{v:8.4f}' if v is not None else '       -'
        fmt2 = lambda v: f'{v:+8.4f}' if v is not None else '       -'
        fmt3 = lambda v: f'{v:+9.4f}' if v is not None else '        -'
        fmt4 = lambda v: f'{v*100:+9.1f}%' if v is not None else '        -'
        print(f"{kc:5.2f} {fmt(vals[0])} {fmt(vals[1])} {fmt(vals[2])} {fmt(vals[3])} "
              f"{fmt2(slope)} {fmt3(gain)} {fmt4(frac_gain)}")
        rho_rows.append({
            'kappa_C': kc, 'rho_by_A': vals, 'A_grid': [0.30, 0.40, 0.50, 0.60],
            'slope_rho_vs_A': slope, 'gain_3_to_6': gain,
            'frac_gain_3_to_6': frac_gain,
        })

    # === P4: lock@sw saturation ===
    print("\n=== P4: lock@sw saturation at A=0.40 ===")
    print(f"{'κ_C':>5} {'lock@sw':>8} {'lock_frac':>9} {'N_sw':>6} {'src':>5}")
    lock_rows = []
    for kc in kc_vals:
        cells_at = {r['A']: r for r in rows_sorted if r['kappa_C'] == kc}
        if 0.40 in cells_at:
            r = cells_at[0.40]
            print(f"{kc:5.2f} {r['lock_at_sw']:8.3f} {r['lock_frac']:9.3f} "
                  f"{r['n_sw']:6.0f} {r['source']:>5}")
            lock_rows.append({
                'kappa_C': kc, 'lock_at_sw': r['lock_at_sw'],
                'lock_frac': r['lock_frac'], 'n_sw': r['n_sw'],
            })

    # === P5: wedge maintenance past saturation ===
    print("\n=== P5: wedge geometry past ridge at A=0.40 ===")
    print(f"{'κ_C':>5} {'wedge°':>7} {'|μ_aL|':>7} {'|μ_rN|':>7} {'aL_frac':>8} {'rN_frac':>8}")
    wedge_rows = []
    for kc in kc_vals:
        cells_at = {r['A']: r for r in rows_sorted if r['kappa_C'] == kc}
        if 0.40 in cells_at:
            r = cells_at[0.40]
            print(f"{kc:5.2f} {r['wedge_aL_rN']:7.1f} {r['aL_mu']:7.1f} "
                  f"{r['rN_mu']:7.1f} {r['aL_frac']:8.3f} {r['rN_frac']:8.3f}")
            wedge_rows.append({
                'kappa_C': kc, 'wedge': r['wedge_aL_rN'],
                'aL_mu': r['aL_mu'], 'rN_mu': r['rN_mu'],
                'aL_frac': r['aL_frac'], 'rN_frac': r['rN_frac'],
            })

    # === P6: mod_amp at f_s vs A across κ_C ===
    print("\n=== P6: mod_amp_at_fs_lock(A) across κ_C ===")
    print(f"{'κ_C':>5} {'A=0.30':>8} {'A=0.40':>8} {'A=0.50':>8} {'A=0.60':>8} {'slope':>8}")
    mod_rows = []
    for kc in kc_vals:
        cells_at = {r['A']: r for r in rows_sorted if r['kappa_C'] == kc}
        vals = []
        xs = []; ys = []
        for A in [0.30, 0.40, 0.50, 0.60]:
            v = cells_at[A]['mod_amp_lock'] if A in cells_at else None
            vals.append(v)
            if v is not None:
                xs.append(A); ys.append(v)
        slope = None
        if len(xs) >= 2:
            _, slope, _ = linfit(xs, ys)
        fmt = lambda v: f'{v:8.4f}' if v is not None else '       -'
        fmt2 = lambda v: f'{v:+8.4f}' if v is not None else '       -'
        print(f"{kc:5.2f} {fmt(vals[0])} {fmt(vals[1])} {fmt(vals[2])} {fmt(vals[3])} "
              f"{fmt2(slope)}")
        mod_rows.append({'kappa_C': kc, 'mod_by_A': vals, 'slope': slope})

    out = {
        'session': 116,
        'analysis_of': ['thor_session_116_past_ridge_results.json',
                        'thor_session_115_kc_dip_gate_results.json',
                        'thor_session_113_dip_decomp_results.json'],
        'kc_vals': kc_vals,
        'A_vals': A_vals,
        'per_cell': rows_sorted,
        'P1_rescue_rows': rescue_rows,
        'P2_aL_arg_rows': aL_rows,
        'P3_rho_rows': rho_rows,
        'P4_lock_rows': lock_rows,
        'P5_wedge_rows': wedge_rows,
        'P6_mod_rows': mod_rows,
    }
    with open('thor_session_116_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nAnalysis → thor_session_116_analysis.json")


if __name__ == '__main__':
    main()
