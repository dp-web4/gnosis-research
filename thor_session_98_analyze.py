#!/usr/bin/env python3
"""S98 analyzer: reads thor_session_98_phase_drift_results.json and
produces a clear, numerical summary.

Output sections:
  1. Per-channel phase-diffusion fit for the main run.
  2. Variogram analysis (is phase drift Brownian?).
  3. Systematic rotation rate (Δω between detector and simulator clock).
  4. σ-dependence of τ_φ, mean response angle, and mean magnitude.
  5. Cross-check against S95 chunked R=0.59 and S96-P1 angle prediction.
"""

import json
import numpy as np
import sys

sys.stdout.reconfigure(line_buffering=True)

PATH = 'thor_session_98_phase_drift_results.json'


def load():
    with open(PATH) as f:
        return json.load(f)


def _to_complex(arr):
    return np.array([complex(p[0], p[1]) for p in arr])


def fit_phi_with_floor(Phi, lags_time, lag_min=1, R_min=0.05):
    """Fit |Φ(m)| = R_0 · exp(-m Δt / τ_φ) + R_inf model.
    Simple approach: try a 2-parameter log fit excluding lag 0, then
    try a 3-parameter with a floor term if residuals suggest it."""
    absPhi = np.abs(Phi)
    ok = (lags_time > 0) & (absPhi > R_min)
    if ok.sum() < 4:
        return None
    x = lags_time[ok]
    y = absPhi[ok]

    # 2-param exponential: y = a · exp(-x/τ)
    # log y = log a - x/τ
    slope, intercept = np.polyfit(x, np.log(y), 1)
    tau_simple = -1.0 / slope if slope < 0 else float('inf')
    a_simple = float(np.exp(intercept))
    pred_simple = a_simple * np.exp(-x / tau_simple if tau_simple < 1e20 else 1e20)
    ss_simple = float(np.sum((y - pred_simple)**2))

    # 3-param nonlinear: y = a · exp(-x/τ) + c
    #   (model: finite asymptote R_∞ from stationary mean-phase contribution)
    # Coarse grid search over (τ, c) then refine.
    best = None
    for log_tau in np.linspace(np.log(1000), np.log(5_000_000), 80):
        tau = float(np.exp(log_tau))
        for c in np.linspace(0.0, float(y.min()) * 0.95, 15):
            # fit a by closed form: y − c = a exp(−x/τ)
            num = np.sum((y - c) * np.exp(-x / tau))
            den = np.sum(np.exp(-2 * x / tau))
            a = num / den if den > 0 else 0
            pred = a * np.exp(-x / tau) + c
            ss = float(np.sum((y - pred)**2))
            if best is None or ss < best['ss']:
                best = {'tau': tau, 'c': float(c), 'a': float(a),
                        'ss': ss, 'pred': pred}

    R2_simple = 1 - ss_simple / float(np.sum((y - y.mean())**2))
    R2_full = 1 - best['ss'] / float(np.sum((y - y.mean())**2))

    return {
        'simple_exp_fit': {
            'tau_phi_s': float(tau_simple),
            'a': float(a_simple),
            'R2': float(R2_simple),
            'ss': float(ss_simple),
        },
        'exp_plus_floor_fit': {
            'tau_phi_s': float(best['tau']),
            'a': float(best['a']),
            'c_floor': float(best['c']),
            'R2': float(R2_full),
            'ss': float(best['ss']),
        },
        'x_used_s': x.tolist(),
        'y_used': y.tolist(),
        'n_fit': int(ok.sum()),
    }


def analyze_channel(summary, label):
    print(f"\n[{label}]")
    Phi = _to_complex(summary['Phi'])
    lags = np.array(summary['lags_time_s'])
    var_dphi = np.array(summary['var_dphi'])
    counts = np.array(summary['count'])
    absPhi = np.abs(Phi)
    argPhi = np.angle(Phi)

    print(f"  n_lags={len(Phi)}  max_lag={lags.max():.0f}s  "
          f"pairs_at_max_lag={counts[-1]}")
    print(f"  |Φ(m)| sampled 1..N:")
    for i, m in enumerate([1, 2, 5, 10, 20, 30, 40, 60]):
        if m < len(Phi):
            print(f"     m={m:3d} ({lags[m]:7.0f}s):  |Φ|={absPhi[m]:.4f}  "
                  f"arg Φ={np.degrees(argPhi[m]):+7.2f}°  "
                  f"var_dφ={var_dphi[m]:.3f}  pairs={counts[m]}")

    fit = fit_phi_with_floor(Phi, lags)
    if fit:
        print("  exponential fit on |Φ(m)|  (m ≥ 1):")
        s = fit['simple_exp_fit']
        print(f"    simple exp:  τ_φ = {s['tau_phi_s']:.0f}s   "
              f"a={s['a']:.3f}  R²={s['R2']:.3f}")
        ff = fit['exp_plus_floor_fit']
        print(f"    exp + floor: τ_φ = {ff['tau_phi_s']:.0f}s  "
              f"a={ff['a']:.3f}  c_floor={ff['c_floor']:.3f}  "
              f"R²={ff['R2']:.3f}")
    else:
        print("  no exponential fit (insufficient data above noise floor)")

    # Variogram: var[Δφ(m)] should be 2 D_φ m Δt (Brownian phase)
    # Fit linear from m=1 onward, check slope and intercept
    m_arr = np.arange(len(var_dphi))
    ok = m_arr >= 1
    if ok.sum() >= 4:
        slope_v, intercept_v = np.polyfit(lags[ok], var_dphi[ok], 1)
        D_from_var = slope_v / 2.0
        tau_from_var = 1.0 / D_from_var if D_from_var > 0 else float('inf')
        print(f"  variogram: slope = {slope_v:.3e} rad²/s  →  "
              f"D_φ = {D_from_var:.3e} /s  τ_φ = {tau_from_var:.0f}s, "
              f"intercept = {intercept_v:.3f} rad² "
              f"(per-chunk phase noise σ²)")

    # Rotation rate
    rot = summary['rotation_rate_fit']
    if rot:
        print(f"  systematic rotation rate: "
              f"Δψ = {rot['rotation_rate_rad_per_s']:.3e} rad/s, "
              f"R²={rot['R2']:.3f}")

    # Per-seed stats
    stats = summary['per_seed_stats']
    angs = np.array([s['mean_angle_deg'] for s in stats])
    mags = np.array([s['mean_mag'] for s in stats])
    R_w = np.array([s['R_weighted'] for s in stats])
    sigma_step = np.array([s['sigma_step_deg'] for s in stats])

    # Circular mean/spread of per-seed mean-angle
    ang_r = np.radians(angs)
    meanvec = np.mean(np.exp(1j * ang_r))
    cmean = float(np.degrees(np.angle(meanvec)))
    R_across = float(np.abs(meanvec))
    print(f"  per-seed mean-angle: mean={cmean:+6.1f}°  R_across_seeds={R_across:.3f} "
          f"(spread {np.degrees(np.sqrt(-2*np.log(max(R_across,1e-6)))):.1f}°-ish)")
    print(f"  per-seed |z̄|: mean={mags.mean():.3e} sd={mags.std():.3e}")
    print(f"  per-seed R_weighted (amp-weighted phase concentration):"
          f" mean={R_w.mean():.3f}  range=[{R_w.min():.3f}, {R_w.max():.3f}]")
    print(f"  per-seed σ_step (lag-1 phase step): mean={sigma_step.mean():.1f}°")
    return fit, cmean, R_across


def run():
    d = load()
    meta = d['meta']['params']
    print("=" * 72)
    print("THOR SESSION 98 — Phase-Drift Timescale τ_φ")
    print("=" * 72)
    print(f"  T_chunk = {meta['T_chunk_s']:.0f}s, warmup={meta['warmup']}, "
          f"dt={meta['dt']}, f_s={meta['signal_freq']}")

    print(f"\n── MAIN: σ={meta['main_sigma']}, A={meta['main_A']}, "
          f"n_seeds={meta['main_n_seeds']}, "
          f"T_total={(meta['main_total_steps']-meta['warmup'])*meta['dt']:.0f}s, "
          f"max_lag_s={meta['main_max_lag']*meta['T_chunk_s']:.0f}s ──")
    raw_fit, raw_ang, raw_R = analyze_channel(d['main']['raw'], 'z_raw (raw-signal MF)')
    st_fit, st_ang, st_R = analyze_channel(d['main']['st'], 'z_st (switch-timing MF)')

    # Comparison: raw/ST angle separation
    ang_sep = abs(((raw_ang - st_ang + 180) % 360) - 180)
    print(f"\n  ── raw ↔ ST angular separation: {ang_sep:.1f}° "
          f"(S95 predicted ≈ 90° from π/2 matched-filter geometry)")

    # σ-sweep
    print("\n" + "=" * 72)
    print("── σ-SWEEP ──")
    print("=" * 72)
    sweep = d['sigma_sweep']
    print(f"  {'σ':>6} {'chan':>6}  {'τ_φ (exp)':>12} {'τ_φ (exp+floor)':>18} "
          f"{'mean_angle':>12} {'R_across':>10} {'|z̄|':>10}")
    sweep_rows = []
    for sig_key in sorted(sweep.keys()):
        s = sweep[sig_key]
        for channel_key, channel in (('raw', s['raw']), ('st', s['st'])):
            Phi = _to_complex(channel['Phi'])
            lags = np.array(channel['lags_time_s'])
            fit = fit_phi_with_floor(Phi, lags)
            stats = channel['per_seed_stats']
            angs = np.array([x['mean_angle_deg'] for x in stats])
            mags = np.array([x['mean_mag'] for x in stats])
            meanvec = np.mean(np.exp(1j * np.radians(angs)))
            cmean = float(np.degrees(np.angle(meanvec)))
            R_across = float(np.abs(meanvec))
            tau_s = fit['simple_exp_fit']['tau_phi_s'] if fit else np.nan
            tau_f = fit['exp_plus_floor_fit']['tau_phi_s'] if fit else np.nan
            print(f"  {s['sigma']:6.3f} {channel_key:>6}  "
                  f"{tau_s:12.0f} {tau_f:18.0f} "
                  f"{cmean:+12.1f} {R_across:10.3f} {mags.mean():10.3e}")
            sweep_rows.append({
                'sigma': s['sigma'], 'channel': channel_key,
                'tau_simple': tau_s, 'tau_floor': tau_f,
                'mean_angle_deg': cmean, 'R_across': R_across,
                'mean_mag': float(mags.mean()),
            })

    # S96-P1 prediction: at σ=0.015 (smaller r₀), ST response angle rotates
    # toward Q_st axis vs σ=0.022. Check by comparing angles across σ.
    print("\n  ── S96-P1 check: ST mean_angle rotation with σ ──")
    st_by_sig = {r['sigma']: r for r in sweep_rows if r['channel'] == 'st'}
    if 0.015 in st_by_sig and 0.022 in st_by_sig and 0.030 in st_by_sig:
        a15 = st_by_sig[0.015]['mean_angle_deg']
        a22 = st_by_sig[0.022]['mean_angle_deg']
        a30 = st_by_sig[0.030]['mean_angle_deg']
        d15 = ((a15 - a22 + 180) % 360) - 180
        d30 = ((a30 - a22 + 180) % 360) - 180
        print(f"     ST angle σ=0.015: {a15:+.1f}°")
        print(f"     ST angle σ=0.022: {a22:+.1f}°  (reference)")
        print(f"     ST angle σ=0.030: {a30:+.1f}°")
        print(f"     Δ(0.015 − 0.022) = {d15:+.1f}°  "
              f"Δ(0.030 − 0.022) = {d30:+.1f}°")
        print(f"     S96-P1 predicts: smaller σ → angle rotates toward Q_st "
              f"(| tan(angle − 90°)| decreases in σ)")

    out_summary = {
        'main_raw_fit': raw_fit, 'main_st_fit': st_fit,
        'main_raw_angle_deg': raw_ang, 'main_st_angle_deg': st_ang,
        'raw_st_angular_separation_deg': ang_sep,
        'sweep_rows': sweep_rows,
    }
    with open('thor_session_98_analysis.json', 'w') as f:
        json.dump(out_summary, f, indent=2, default=float)
    print("\nAnalysis JSON → thor_session_98_analysis.json")


if __name__ == '__main__':
    run()
