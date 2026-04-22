#!/usr/bin/env python3
"""Thor Session #108 analyzer — ridge location comparison: ratio 0.2 vs ratio 0.8.

Reads:
  thor_session_108_ridge_ratio_02_results.json   (4 new cells @ ratio 0.2)
  thor_session_105_kappa_strength_results.json   (r02_k030 @ κ_C=0.15)
  thor_session_106_kappa_c_channel_results.json  (ratio 0.8 κ_p=0.30 sweep — 4 cells)
  thor_session_107_ridge_map_results.json        (κ_p=0.15, 0.50 slices — for cross-ratio context)

Outputs:
  thor_session_108_analysis.json
  human-readable summary table to stdout.
"""
import json
import numpy as np


def per_seed_R_from_z(per_seed_z_list, key):
    """Reconstruct per-seed R_coh list from packed z (list of [re,im] pairs)."""
    out = []
    for s in per_seed_z_list:
        z = np.array([complex(r, i) for r, i in s[key]])
        mu = z.mean()
        dev = z - mu
        sn2 = float(np.mean(np.abs(dev)**2))
        mu2 = float(abs(mu)**2)
        R = mu2 / (mu2 + sn2) if (mu2 + sn2) > 0 else 0.0
        out.append({'R_coh': R, 'mu_abs': float(abs(mu)), 'sigma_n': float(np.sqrt(sn2)),
                    'mu_arg_deg': float(np.degrees(np.angle(mu)))})
    return out


def cell_stats_from_results_file(path, label):
    d = json.load(open(path))
    c = d['cells'][label]
    s = c['summary']
    ps_raw = per_seed_R_from_z(c['per_seed_z'], 'z_raw')
    ps_st = per_seed_R_from_z(c['per_seed_z'], 'z_st')

    n_sw_per_seed = s['n_sw_per_seed']
    return {
        'kappa_phase': c['kappa_phase'],
        'kappa_C': c.get('kappa_C', None),
        'omega': c.get('omega_spread', c.get('omega', None)),
        'ratio': c.get('ratio_omega_over_kappa_phase',
                       c.get('ratio_omega_over_kappa', None)),
        'R_raw': s['raw_R_coh_mean'], 'R_raw_sd': s['raw_R_coh_std'],
        'R_st': s['st_R_coh_mean'], 'R_st_sd': s['st_R_coh_std'],
        'sigma_n_raw': s['raw_sigma_n_mean'],
        'sigma_n_st': s['st_sigma_n_mean'],
        'mu_raw': s['raw_mu_mean'], 'mu_st': s['st_mu_mean'],
        'R_angle_raw': s['cross_seed_R_angle_raw'],
        'R_angle_st': s['cross_seed_R_angle_st'],
        'R_kura': s.get('R_kura_cross_seed_mean', None),
        'R_kura_sd': s.get('R_kura_cross_seed_std', None),
        'N_sw_mean': float(np.mean(n_sw_per_seed)),
        'N_sw_sd': float(np.std(n_sw_per_seed)),
    }


def s105_r02_k030():
    """Recycled S105 cell — add κ_C field (default 0.15 in the S105 sweep)."""
    d = cell_stats_from_results_file('thor_session_105_kappa_strength_results.json', 'r02_k030')
    d['kappa_C'] = 0.15  # S105 simulator used the default κ_C=0.15
    return d


def quadratic_peak(x, y):
    """Fit y = a x^2 + b x + c; return (x_peak, y_peak, r2, a)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    coefs = np.polyfit(x, y, 2)
    a, b, c = coefs
    xp = -b / (2 * a) if abs(a) > 1e-12 else np.nan
    yp = a * xp**2 + b * xp + c
    yhat = np.polyval(coefs, x)
    ss_res = float(np.sum((y - yhat)**2))
    ss_tot = float(np.sum((y - y.mean())**2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return float(xp), float(yp), float(r2), float(a)


def rho_sig_from_summary(cell):
    """ρ_sig = |<z_st>|^2 / <N_sw>  — per-event signal density.

    Uses the per-cell mean mu_st (|<z_st>|) and mean N_sw per chunk.
    """
    mu_st = cell['mu_st']
    Nsw = cell['N_sw_mean']
    return mu_st**2 / Nsw if Nsw > 0 else 0.0


def main():
    # Ratio 0.2 slice: 4 new from S108 + 1 recycled from S105.
    r02_labels = [
        ('kp030_kC000_r02', 0.00),
        ('kp030_kC005_r02', 0.05),
        (None,              0.15),  # recycled
        ('kp030_kC030_r02', 0.30),
        ('kp030_kC050_r02', 0.50),
    ]
    ratio02 = []
    for label, kC in r02_labels:
        if label is None:
            cell = s105_r02_k030()
        else:
            cell = cell_stats_from_results_file(
                'thor_session_108_ridge_ratio_02_results.json', label)
        cell['source_label'] = label or 'S105 r02_k030 (recycled)'
        ratio02.append(cell)

    # Ratio 0.8 slice (κ_p=0.30): recycle S106 cells + S105 r08_k030.
    r08_labels = [
        ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC000', 0.00),
        ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC005', 0.05),
        ('thor_session_105_kappa_strength_results.json',  'r08_k030',    0.15),
        ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC030', 0.30),
        ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC050', 0.50),
    ]
    ratio08 = []
    for path, label, kC in r08_labels:
        cell = cell_stats_from_results_file(path, label)
        cell['source_label'] = f"{path.split('_')[2]} {label}"
        cell['kappa_C'] = kC  # force-set for recycled S105 (has no kappa_C field)
        ratio08.append(cell)

    # Quadratic peak fits for ratio 0.2 and ratio 0.8.
    def peaks(slice_cells):
        kC = [c['kappa_C'] for c in slice_cells]
        Rr = [c['R_raw'] for c in slice_cells]
        Rs = [c['R_st'] for c in slice_cells]
        pr = quadratic_peak(kC, Rr)
        ps = quadratic_peak(kC, Rs)
        return {
            'kappa_C_grid': kC,
            'R_raw_grid': Rr, 'R_st_grid': Rs,
            'peak_raw_kC': pr[0], 'peak_raw_R': pr[1], 'r2_raw': pr[2], 'curv_raw': pr[3],
            'peak_st_kC':  ps[0], 'peak_st_R':  ps[1], 'r2_st':  ps[2], 'curv_st':  ps[3],
        }

    fit02 = peaks(ratio02)
    fit08 = peaks(ratio08)

    # σ_n_ST and N_sw across cells.
    def tabulate(slice_cells):
        return [{
            'kC': c['kappa_C'], 'R_raw': c['R_raw'], 'R_st': c['R_st'],
            'sigma_n_raw': c['sigma_n_raw'], 'sigma_n_st': c['sigma_n_st'],
            'mu_raw': c['mu_raw'], 'mu_st': c['mu_st'],
            'N_sw': c['N_sw_mean'], 'R_angle_raw': c['R_angle_raw'],
            'R_angle_st': c['R_angle_st'], 'R_kura': c['R_kura'],
            'rho_sig_st': rho_sig_from_summary(c),
            'source': c.get('source_label', ''),
        } for c in slice_cells]

    tbl02 = tabulate(ratio02)
    tbl08 = tabulate(ratio08)

    # ---- Print tables -----------------------------------------------------
    print("=" * 82)
    print("S108 — Ridge Universality: Ratio 0.2 vs Ratio 0.8 (both at κ_p=0.30)")
    print("=" * 82)

    def print_slice(name, tbl, fit):
        print(f"\n  {name}   (κ_p=0.30, A=0.30, σ=0.022)")
        print(f"  κ_C  |  R_raw  |  R_st  | μ_raw  | μ_st   | σ_n_raw | σ_n_st | N_sw | R_kura  | ρ_sig_st")
        print(f"  -----+--------+--------+--------+--------+---------+--------+------+---------+---------")
        for r in tbl:
            rk = f"{r['R_kura']:.3f}" if r['R_kura'] is not None else "  -  "
            print(f"  {r['kC']:.2f} | {r['R_raw']:.3f}  | {r['R_st']:.3f}  | "
                  f"{r['mu_raw']:.3f}  | {r['mu_st']:5.2f}  | "
                  f"{r['sigma_n_raw']:.3f}   | {r['sigma_n_st']:.2f}   | "
                  f"{r['N_sw']:4.0f} | {rk}   | {r['rho_sig_st']:.4f}")
        print(f"  Quadratic fit:")
        print(f"    RAW: peak κ_C* = {fit['peak_raw_kC']:.3f}   peak R = {fit['peak_raw_R']:.3f}   "
              f"r²={fit['r2_raw']:.3f}   curvature={fit['curv_raw']:.1f}")
        print(f"    ST:  peak κ_C* = {fit['peak_st_kC']:.3f}   peak R = {fit['peak_st_R']:.3f}   "
              f"r²={fit['r2_st']:.3f}   curvature={fit['curv_st']:.1f}")

    print_slice("RATIO 0.2  (ω=0.06, deep-coherent regime)", tbl02, fit02)
    print_slice("RATIO 0.8  (ω=0.24, near-desync)",          tbl08, fit08)

    # ---- Verdict ---------------------------------------------------------
    delta_raw = fit02['peak_raw_kC'] - fit08['peak_raw_kC']
    delta_st = fit02['peak_st_kC'] - fit08['peak_st_kC']

    print("\n" + "=" * 82)
    print("Verdict: ridge location shift across ratio 0.2 → 0.8")
    print("=" * 82)
    print(f"  Δ peak κ_C* (RAW) = {delta_raw:+.3f}   (ratio 0.2: {fit02['peak_raw_kC']:.3f}  vs  ratio 0.8: {fit08['peak_raw_kC']:.3f})")
    print(f"  Δ peak κ_C* (ST)  = {delta_st:+.3f}   (ratio 0.2: {fit02['peak_st_kC']:.3f}  vs  ratio 0.8: {fit08['peak_st_kC']:.3f})")

    if abs(delta_raw) < 0.03 and abs(delta_st) < 0.05:
        verdict = "A: UNIVERSAL RIDGE — peak κ_C* invariant across ratio."
    elif delta_raw < -0.05 or delta_st < -0.08:
        verdict = "B: LEFTWARD SHIFT at ratio 0.2 (deep-locked needs less κ_C)."
    elif delta_raw > 0.05 or delta_st > 0.08:
        verdict = "C: RIGHTWARD SHIFT at ratio 0.2."
    else:
        verdict = "mixed — likely partial universality or ceiling effects."
    print(f"  → {verdict}")

    # ρ_sig separability check (S107-P4 probe).
    print("\n" + "=" * 82)
    print("ρ_sig(κ_C) across ratios — signal density per event:")
    print("=" * 82)
    for i, (r02, r08) in enumerate(zip(tbl02, tbl08)):
        print(f"  κ_C={r02['kC']:.2f}:   ratio-0.2 ρ_sig_st = {r02['rho_sig_st']:.4f}   "
              f"ratio-0.8 ρ_sig_st = {r08['rho_sig_st']:.4f}   "
              f"ratio = {r02['rho_sig_st']/r08['rho_sig_st'] if r08['rho_sig_st']>0 else np.nan:.2f}")

    # N_sw shape comparison.
    print("\n" + "=" * 82)
    print("N_sw(κ_C) — event rate per chunk:")
    print("=" * 82)
    print(f"  κ_C    | ratio 0.2 | ratio 0.8 | ratio 0.2/0.8")
    print(f"  -------+-----------+-----------+---------------")
    for r02, r08 in zip(tbl02, tbl08):
        print(f"  {r02['kC']:.2f}   |  {r02['N_sw']:7.0f} |  {r08['N_sw']:7.0f} |   {r02['N_sw']/r08['N_sw']:.2f}")

    # σ_n_ST flatness check (S107-P5 probe).
    snr_st_r02 = [r['sigma_n_st'] for r in tbl02]
    snr_st_r08 = [r['sigma_n_st'] for r in tbl08]
    print("\n" + "=" * 82)
    print("σ_n_ST flatness (S107-P5 probe):")
    print("=" * 82)
    print(f"  ratio 0.2: min={min(snr_st_r02):.2f}  max={max(snr_st_r02):.2f}  "
          f"mean={np.mean(snr_st_r02):.2f}  cv={np.std(snr_st_r02)/np.mean(snr_st_r02):.3f}")
    print(f"  ratio 0.8: min={min(snr_st_r08):.2f}  max={max(snr_st_r08):.2f}  "
          f"mean={np.mean(snr_st_r08):.2f}  cv={np.std(snr_st_r08)/np.mean(snr_st_r08):.3f}")

    # Save full analysis.
    out = {
        'meta': {
            'session': 108,
            'description': 'Ridge location at ratio 0.2 vs ratio 0.8, κ_p=0.30.',
            'sources': {
                'ratio_0.2_new': 'thor_session_108_ridge_ratio_02_results.json',
                'ratio_0.2_recycled': 'S105 r02_k030',
                'ratio_0.8_kC_sweep': 'S106 kp030_* + S105 r08_k030',
            },
        },
        'ratio_0.2': {'cells': tbl02, 'quadratic_fit': fit02},
        'ratio_0.8': {'cells': tbl08, 'quadratic_fit': fit08},
        'verdict': {
            'delta_peak_kC_raw': delta_raw,
            'delta_peak_kC_st': delta_st,
            'conclusion': verdict,
        },
    }
    with open('thor_session_108_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nWrote thor_session_108_analysis.json")


if __name__ == '__main__':
    main()
