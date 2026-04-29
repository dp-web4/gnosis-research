#!/usr/bin/env python3
"""S114 analyzer — extract dip-A, peak-A, att_lock saturation across κ_p.

Combines S114 results (κ_p ∈ {0.10, 0.50}) with the S113 ρ_sig(A) curve
(κ_p = 0.30 baseline) to test S113-P1 (linear dip-A scaling),
S113-P4 (att_lock saturation arg κ_p-invariant), and S111-P1 (peak-A
shifts with κ_p).
"""
import json
import os
import sys
from pathlib import Path

import numpy as np


def load_s113_curve(path='thor_session_113_analysis.json'):
    if not os.path.exists(path):
        print(f"  WARN: S113 baseline {path} not found; skipping κ_p=0.30")
        return []
    rows = json.load(open(path))['rows']
    out = []
    for r in rows:
        ca = r.get('class_agg', {})
        out.append({
            'kappa_phase': 0.30,
            'omega_std': 0.07,
            'A': r['A'],
            'rho_sig': r['rho_sig'],
            'rho_sig_std': r.get('rho_sig_std', 0.0),
            'mu_st': r['mu_st'],
            'mu_arg': r['mu_arg'],
            'R_kura': r['R_kura'],
            'lock_at_sw': r['lock_at_sw'],
            'class_arg': {
                k: ca.get(k, {}).get('mu_arg_per_seed_circmean_deg', float('nan'))
                for k in ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
            },
            'class_abs': {
                k: ca.get(k, {}).get('mu_abs_per_seed_mean', float('nan'))
                for k in ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
            },
            'class_frac': {
                k: ca.get(k, {}).get('fraction_of_sw', float('nan'))
                for k in ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
            },
            'source': 'S113',
        })
    return out


def load_s114(path='thor_session_114_dip_kp_scaling_results.json'):
    d = json.load(open(path))
    out = []
    for label, c in d['cells'].items():
        s = c['summary']
        out.append({
            'kappa_phase': c['kappa_phase'],
            'omega_std': c['omega_std'],
            'A': c['signal_amp'],
            'rho_sig': s['rho_sig_st_mean'],
            'rho_sig_std': s['rho_sig_st_std'],
            'rho_sig_sem': s['rho_sig_st_sem'],
            'mu_st': s['st_mu_mean'],
            'mu_arg': s['st_mu_arg_circmean_deg'],
            'R_kura': s['kura_mean_mean'],
            'lock_at_sw': s['lock_at_switch_frac_mean'],
            'n_sw': s['n_sw_total_mean'],
            'class_arg': {
                k: s['class_agg'][k]['mu_arg_per_seed_circmean_deg']
                for k in ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
            },
            'class_abs': {
                k: s['class_agg'][k]['mu_abs_per_seed_mean']
                for k in ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
            },
            'class_frac': {
                k: s['class_agg'][k]['fraction_of_sw']
                for k in ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
            },
            'source': 'S114',
        })
    return out


def quadratic_extremum(xs, ys):
    """Fit ys = a x² + b x + c, return (x*, y*) of vertex.

    Returns (None, None) if fit fails or vertex outside data range."""
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if len(xs) < 3 or np.std(xs) == 0:
        return None, None, None
    coefs = np.polyfit(xs, ys, 2)
    a, b, c = coefs
    if abs(a) < 1e-12:
        return None, None, None
    x_star = -b / (2 * a)
    y_star = c - b * b / (4 * a)
    return float(x_star), float(y_star), float(a)


def find_dip(curve_xs, curve_ys, peak_x=None):
    """Identify a dip A: a strict interior local minimum y[i] with
    y[i-1] > y[i] AND y[i+1] > y[i] (a true valley between two
    higher neighbors).

    Returns (dip_x, dip_y, preceding_peak_x, preceding_peak_y) for the
    deepest such valley relative to its preceding maximum.

    If peak_x is given, prefer dips with A > peak_x; fallback to any
    valid interior valley if none.
    """
    xs = np.asarray(curve_xs, dtype=float)
    ys = np.asarray(curve_ys, dtype=float)
    order = np.argsort(xs)
    xs = xs[order]; ys = ys[order]
    cands = []
    for i in range(1, len(xs) - 1):
        if ys[i] < ys[i - 1] and ys[i] < ys[i + 1]:
            # Find preceding local-or-global peak (max of ys[:i+1])
            j = int(np.argmax(ys[:i+1]))
            preceding_peak_x = float(xs[j]); preceding_peak_y = float(ys[j])
            depth = preceding_peak_y - ys[i]
            cands.append((float(xs[i]), float(ys[i]), preceding_peak_x,
                          preceding_peak_y, depth))
    if not cands:
        return None, None, None, None
    if peak_x is not None:
        post = [c for c in cands if c[0] > peak_x]
        if post:
            cands = post
    # Take the deepest dip relative to its preceding peak
    cands.sort(key=lambda t: -t[4])
    dip_x, dip_y, pp_x, pp_y, _ = cands[0]
    return dip_x, dip_y, pp_x, pp_y


def linear_fit(xs, ys, sigmas=None):
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if sigmas is not None:
        w = 1.0 / np.asarray(sigmas, dtype=float)**2
        S = np.sum(w); Sx = np.sum(w * xs); Sy = np.sum(w * ys)
        Sxx = np.sum(w * xs * xs); Sxy = np.sum(w * xs * ys)
        D = S * Sxx - Sx * Sx
        slope = (S * Sxy - Sx * Sy) / D
        intercept = (Sxx * Sy - Sx * Sxy) / D
        slope_se = float(np.sqrt(S / D))
        return float(slope), float(intercept), slope_se
    else:
        n = len(xs)
        mx, my = xs.mean(), ys.mean()
        ssx = np.sum((xs - mx)**2)
        sxy = np.sum((xs - mx) * (ys - my))
        if ssx == 0:
            return float('nan'), float(my), float('nan')
        slope = sxy / ssx
        intercept = my - slope * mx
        resid = ys - (slope * xs + intercept)
        s2 = np.sum(resid**2) / max(1, n - 2)
        slope_se = float(np.sqrt(s2 / ssx))
        return float(slope), float(intercept), slope_se


def att_lock_saturation_arg(curve, plateau_window=2):
    """Mean att_lock arg over the top-A plateau.

    Take the last `plateau_window+1` points sorted by A; compute the
    circular mean of arg(μ_aL).
    """
    sorted_curve = sorted(curve, key=lambda r: r['A'])
    tail = sorted_curve[-min(len(sorted_curve), plateau_window + 1):]
    args = np.array([r['class_arg']['att_lock'] for r in tail])
    z = np.exp(1j * np.deg2rad(args))
    return float(np.degrees(np.angle(z.mean()))), float(abs(z.mean())), len(tail)


def main():
    s114 = load_s114()
    s113 = load_s113_curve()
    all_rows = s114 + s113

    by_kp = {}
    for r in all_rows:
        by_kp.setdefault(round(r['kappa_phase'], 4), []).append(r)
    for kp in by_kp:
        by_kp[kp].sort(key=lambda r: r['A'])

    PEAK_HINT = {0.10: 0.10, 0.30: 0.35, 0.50: 0.65}

    print(f"{'='*74}")
    print(f"S114 ANALYSIS: dip-A vs κ_p (S113-P1, P4 + S111-P1)")
    print(f"{'='*74}\n")

    per_kp = {}
    for kp in sorted(by_kp.keys()):
        curve = by_kp[kp]
        xs = np.array([r['A'] for r in curve])
        ys = np.array([r['rho_sig'] for r in curve])
        print(f"--- κ_p = {kp:.2f}  (n_cells={len(curve)})  ---")
        print(f"{'A':>6}  {'ρ_sig':>8}  {'|μ_st|':>8}  {'arg':>7}  {'R_k':>6}  "
              f"{'Lk@sw':>6}  {'aL_arg':>7}  {'aL_|μ|':>8}  {'rN_arg':>7}  {'rN_|μ|':>8}  src")
        for r in curve:
            print(f"{r['A']:>6.2f}  {r['rho_sig']:>8.4f}  {r['mu_st']:>8.3f}  "
                  f"{r['mu_arg']:>+7.1f}  {r['R_kura']:>6.3f}  "
                  f"{r['lock_at_sw']:>6.3f}  "
                  f"{r['class_arg']['att_lock']:>+7.1f}  "
                  f"{r['class_abs']['att_lock']:>8.2f}  "
                  f"{r['class_arg']['rep_noise']:>+7.1f}  "
                  f"{r['class_abs']['rep_noise']:>8.2f}  {r['source']}")
        peak_x, peak_y, _ = quadratic_extremum(xs, ys)
        # Identify nearest-data peak as cross-check
        peak_idx = int(np.argmax(ys))
        peak_data_x = float(xs[peak_idx])
        peak_data_y = float(ys[peak_idx])
        # Wedge between att_lock and rep_noise (S113 mechanism observable)
        wedge_deg = []
        for r in curve:
            aL = r['class_arg']['att_lock']
            rN = r['class_arg']['rep_noise']
            d = (rN - aL + 540.0) % 360.0 - 180.0   # signed in [-180, 180]
            wedge_deg.append(abs(d))
        wedge_deg = np.array(wedge_deg)
        wedge_max_idx = int(np.argmax(wedge_deg))
        wedge_max_A = float(xs[wedge_max_idx])
        wedge_max_val = float(wedge_deg[wedge_max_idx])
        print(f"  wedge |arg(μ_rN) - arg(μ_aL)|: max {wedge_max_val:.1f}° at A={wedge_max_A:.3f}")
        # Find dip (strict interior local minimum)
        dip_x, dip_y, pp_x, pp_y = find_dip(xs, ys)
        print(f"\n  peak_quad(x*={peak_x},  y*={peak_y})")
        print(f"  peak_data: A={peak_data_x:.3f}, ρ_sig={peak_data_y:.4f}")
        if dip_x is not None:
            print(f"  dip_data: A={dip_x:.3f}, ρ_sig={dip_y:.4f}  "
                  f"(preceding peak: A={pp_x:.3f}, ρ_sig={pp_y:.4f}; "
                  f"drop_pct={(pp_y-dip_y)/pp_y*100:.1f}%)")
        else:
            print("  dip_data: NONE (no strict interior valley in sampled grid)")
        sat_arg, sat_R, sat_n = att_lock_saturation_arg(curve)
        print(f"  att_lock plateau arg (top-{sat_n} A): {sat_arg:+.1f}°  R={sat_R:.3f}")
        # rep_noise rotation rate (deg/A) — fit linear over the swept range
        rN_args = np.array([r['class_arg']['rep_noise'] for r in curve])
        # Unwrap rep_noise (it rotates monotonically through ±180)
        rN_unw = np.unwrap(np.deg2rad(rN_args))
        rN_unw_deg = np.rad2deg(rN_unw)
        rN_slope, rN_intercept, rN_se = linear_fit(xs, rN_unw_deg)
        print(f"  rep_noise rotation rate: {rN_slope:+.1f} ± {rN_se:.1f} deg/A "
              f"(unwrapped, n={len(xs)})")
        # att_lock rotation early-A (only data with A < peak_data_x)
        early = xs < peak_data_x
        if early.sum() >= 2:
            aL_args = np.array([r['class_arg']['att_lock'] for r in curve])
            aL_unw = np.rad2deg(np.unwrap(np.deg2rad(aL_args)))
            aL_slope, aL_int, aL_se = linear_fit(xs[early], aL_unw[early])
            print(f"  att_lock rotation rate (A<peak): "
                  f"{aL_slope:+.1f} ± {aL_se:.1f} deg/A")
        else:
            aL_slope = float('nan')
            aL_se = float('nan')
        per_kp[kp] = {
            'kappa_phase': kp,
            'n_cells': len(curve),
            'peak_data_A': peak_data_x,
            'peak_data_rho': peak_data_y,
            'peak_quad_A': peak_x,
            'peak_quad_rho': peak_y,
            'dip_A': dip_x,
            'dip_rho': dip_y,
            'dip_preceding_peak_A': pp_x,
            'dip_preceding_peak_rho': pp_y,
            'dip_drop_pct': ((pp_y - dip_y) / pp_y * 100.0)
                if dip_x is not None else None,
            'att_lock_sat_arg_deg': sat_arg,
            'att_lock_sat_R': sat_R,
            'rep_noise_rotation_rate_deg_per_A': rN_slope,
            'rep_noise_rotation_rate_se': rN_se,
            'att_lock_rotation_rate_deg_per_A': aL_slope,
            'wedge_max_A': wedge_max_A,
            'wedge_max_deg': wedge_max_val,
            'wedge_per_A': dict(zip([float(x) for x in xs],
                                    [float(w) for w in wedge_deg])),
            'curve': curve,
        }
        print()

    # ----------------- cross-κ_p test of P1 (dip-A scaling) ---------------
    print(f"{'='*74}")
    print(f"CROSS-κ_p ANALYSIS")
    print(f"{'='*74}\n")
    valid_dip = [(kp, per_kp[kp]['dip_A']) for kp in sorted(per_kp.keys())
                 if per_kp[kp]['dip_A'] is not None]
    print("--- P1: dip-A ∝ κ_p ---")
    for kp, d in valid_dip:
        pred = 0.40 * (kp / 0.30)
        print(f"  κ_p={kp:.2f}  dip-A_obs={d:.3f}  dip-A_pred={pred:.3f}  "
              f"obs/pred={d/pred:.2f}")
    if len(valid_dip) >= 2:
        kps = np.array([t[0] for t in valid_dip])
        dipAs = np.array([t[1] for t in valid_dip])
        slope, intercept, se = linear_fit(kps, dipAs)
        print(f"\n  Linear fit: dip-A = {slope:.3f} · κ_p + {intercept:+.3f}")
        print(f"  Predicted slope (= dip-A(0.30)/0.30 = 4/3): 1.33")
        print(f"  Predicted intercept: 0.0")
        # r²
        pred = slope * kps + intercept
        ss_res = float(np.sum((dipAs - pred)**2))
        ss_tot = float(np.sum((dipAs - dipAs.mean())**2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
        print(f"  r² = {r2:.3f}")
    else:
        print("  Insufficient valid dips for cross-κ_p fit.")

    # P4 invariance of att_lock saturation arg
    print("\n--- P4: att_lock saturation arg κ_p-invariant ---")
    sat_args = [per_kp[kp]['att_lock_sat_arg_deg'] for kp in sorted(per_kp.keys())]
    for kp, sa in zip(sorted(per_kp.keys()), sat_args):
        print(f"  κ_p={kp:.2f}  att_lock_sat_arg = {sa:+.1f}°")
    z = np.exp(1j * np.deg2rad(sat_args))
    sa_mean = float(np.degrees(np.angle(z.mean())))
    sa_R = float(abs(z.mean()))
    print(f"  Circular mean across κ_p: {sa_mean:+.1f}°   R={sa_R:.3f}")
    print(f"  S113 reference: −96° at κ_p=0.30, A≥0.35")

    # P5b: wedge max location vs dip location — should track
    print("\n--- P5b: wedge max A ≈ dip A ---")
    for kp in sorted(per_kp.keys()):
        d = per_kp[kp]
        wmA = d.get('wedge_max_A')
        wmV = d.get('wedge_max_deg')
        dipA = d.get('dip_A')
        print(f"  κ_p={kp:.2f}  wedge_max @ A={wmA:.3f} ({wmV:.1f}°)  "
              f"dip_A={dipA if dipA is not None else 'NONE'}")

    # P3 rep_noise rotation rate ∝ 1/κ_p
    print("\n--- P3: rep_noise rotation rate ∝ 1/κ_p ---")
    rN_rates = []
    for kp in sorted(per_kp.keys()):
        rate = per_kp[kp]['rep_noise_rotation_rate_deg_per_A']
        rN_rates.append((kp, rate))
        print(f"  κ_p={kp:.2f}  rate = {rate:+7.1f} deg/A    "
              f"product κ_p · rate = {kp * rate:+7.2f}")

    # Save analysis
    out = {
        'session': 114,
        'analysis_of': ['thor_session_114_dip_kp_scaling_results.json',
                        'thor_session_113_analysis.json'],
        'per_kp': per_kp,
        'p1_linear_fit': {
            'valid_dips': valid_dip,
            'slope': slope if len(valid_dip) >= 2 else None,
            'intercept': intercept if len(valid_dip) >= 2 else None,
            'r2': r2 if len(valid_dip) >= 2 else None,
            'predicted_slope': 1.333,
            'predicted_intercept': 0.0,
        },
        'p4_sat_arg_invariance': {
            'per_kp_sat_arg_deg': dict(zip(sorted(per_kp.keys()), sat_args)),
            'circular_mean_deg': sa_mean,
            'circular_R': sa_R,
            's113_reference': -96.0,
        },
        'p3_rN_rotation_rates': dict(rN_rates),
    }
    with open('thor_session_114_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print(f"\nWrote thor_session_114_analysis.json")


if __name__ == '__main__':
    main()
