#!/usr/bin/env python3
"""Thor Session #100 analysis: assemble τ_φ(σ) and τ_wander(σ) curves
across the full σ range (S98 low-σ sweep + S100 high-σ sweep)."""

import json
import numpy as np


def fit_exp_tau(rho, lags_time_s, floor=0.10):
    """Fit τ from rho(m) = exp(-m/τ) by log-linear regression, using lags
    where rho > floor. Returns (tau_s, R2, n_fit) or None."""
    rho = np.array(rho, dtype=float)
    lags_time_s = np.array(lags_time_s, dtype=float)
    ok = (rho > floor) & (lags_time_s > 0)
    if ok.sum() < 3:
        return None
    y = np.log(rho[ok])
    x = lags_time_s[ok]
    slope, intercept = np.polyfit(x, y, 1)
    if slope >= 0:
        return {'tau_s': float('inf'), 'R2': 0.0, 'n_fit': int(ok.sum()),
                'slope': float(slope)}
    tau = -1.0 / slope
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred)**2))
    ss_tot = float(np.sum((y - y.mean())**2))
    R2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {'tau_s': float(tau), 'R2': float(R2), 'n_fit': int(ok.sum()),
            'slope': float(slope)}


def phi_magnitude(phi_pairs):
    return [abs(complex(a, b)) for (a, b) in phi_pairs]


def analyze_summary(summary, chunk_time_s=4000.0, floor_phi=0.10,
                    floor_rho=0.10):
    """Pull τ_φ (from |Φ|) and τ_mag (from rho_abs) out of a channel summary."""
    abs_phi = np.array(phi_magnitude(summary['Phi']))
    rho_abs = np.array(summary['rho_abs'])
    lags = np.arange(len(abs_phi)) * chunk_time_s
    tau_phi = fit_exp_tau(abs_phi, lags, floor=floor_phi)
    tau_mag = fit_exp_tau(rho_abs, lags, floor=floor_rho)
    per_seed = summary.get('per_seed_stats', [])
    if per_seed:
        ang = np.array([s['mean_angle_deg'] for s in per_seed])
        ang_mean = float(np.degrees(np.angle(np.mean(np.exp(
            1j * np.radians(ang))))))
        R_seeds = float(np.abs(np.mean(np.exp(1j * np.radians(ang)))))
        R_weighted = float(np.mean([s['R_weighted'] for s in per_seed]))
    else:
        ang_mean = float('nan'); R_seeds = float('nan')
        R_weighted = float('nan')
    return {
        'tau_phi': tau_phi,
        'tau_mag': tau_mag,
        'abs_phi_first10': abs_phi[:10].tolist(),
        'rho_abs_first10': rho_abs[:10].tolist(),
        'ang_mean_deg': ang_mean,
        'R_seeds': R_seeds,
        'R_weighted_mean': R_weighted,
        'mean_z2': summary.get('mean_z2'),
    }


def load_s98_s100():
    s98 = json.load(open('thor_session_98_phase_drift_results.json'))
    try:
        s100 = json.load(open('thor_session_100_incoherent_drift_results.json'))
    except FileNotFoundError:
        s100 = None
    return s98, s100


def build_sigma_table(s98, s100):
    """Assemble τ_φ and τ_mag across σ values. Returns list of rows sorted
    by σ."""
    rows = []
    # S98 main (σ=0.022, high-stats) + S98 sigma_sweep (lower-stats)
    m = s98['main']
    rows.append({
        'sigma': s98['meta']['params']['main_sigma'],
        'A': s98['meta']['params']['main_A'],
        'source': 'S98-main',
        'n_seeds': s98['meta']['params']['main_n_seeds'],
        'total_steps': s98['meta']['params']['main_total_steps'],
        'raw': analyze_summary(m['raw']),
        'st': analyze_summary(m['st']),
    })
    for key, res in s98['sigma_sweep'].items():
        rows.append({
            'sigma': res['sigma'],
            'A': res['A'],
            'source': 'S98-sweep',
            'n_seeds': res['n_seeds'],
            'total_steps': res['total_steps'],
            'raw': analyze_summary(res['raw']),
            'st': analyze_summary(res['st']),
        })
    # S100 incoherent sweep + main
    if s100 is not None:
        for key, res in s100['sigma_sweep'].items():
            rows.append({
                'sigma': res['sigma'],
                'A': res['A'],
                'source': 'S100-sweep',
                'n_seeds': res['n_seeds'],
                'total_steps': res['total_steps'],
                'raw': analyze_summary(res['raw']),
                'st': analyze_summary(res['st']),
            })
        mm = s100['main']
        rows.append({
            'sigma': mm['sigma'],
            'A': s100['meta']['params']['main_A'],
            'source': 'S100-main',
            'n_seeds': s100['meta']['params']['main_n_seeds'],
            'total_steps': s100['meta']['params']['main_total_steps'],
            'raw': analyze_summary(mm['raw']),
            'st': analyze_summary(mm['st']),
        })
    rows.sort(key=lambda r: (r['sigma'], r['source']))
    return rows


def print_table(rows, channel='st'):
    print(f"\n== τ_φ(σ), channel = {channel} ==")
    print(f"{'σ':>6}  {'source':<11} {'n×T/1e3s':>9} "
          f"{'τ_φ (s)':>12}  {'R²':>5}  {'n':>3}  "
          f"{'|Φ(1)|':>7} {'|Φ(2)|':>7} {'|Φ(5)|':>7} "
          f"{'ang°':>6} {'R_sds':>6}")
    for r in rows:
        ch = r[channel]
        tp = ch['tau_phi']
        tph = (f"{tp['tau_s']:12.0f}" if tp and tp['tau_s'] != float('inf')
               else f"{'inf':>12}")
        r2 = f"{tp['R2']:5.2f}" if tp else " n/a "
        nf = f"{tp['n_fit']:3d}" if tp else "  0"
        a0 = ch['abs_phi_first10']
        phi1 = f"{a0[1]:7.3f}" if len(a0) > 1 else "   -"
        phi2 = f"{a0[2]:7.3f}" if len(a0) > 2 else "   -"
        phi5 = f"{a0[5]:7.3f}" if len(a0) > 5 else "   -"
        nt = r['n_seeds'] * r['total_steps'] * 0.1 / 1e3  # 0.1s/step
        print(f"{r['sigma']:6.3f}  {r['source']:<11} {nt:9.0f} "
              f"{tph}  {r2}  {nf}  {phi1} {phi2} {phi5} "
              f"{ch['ang_mean_deg']:+6.1f} {ch['R_seeds']:6.3f}")


def print_mag_table(rows, channel='st'):
    print(f"\n== τ_mag (|z| wander)(σ), channel = {channel} ==")
    print(f"{'σ':>6}  {'source':<11} "
          f"{'τ_mag (s)':>12}  {'R²':>5}  {'n':>3}  "
          f"{'ρ_abs(1)':>9} {'ρ_abs(2)':>9} {'ρ_abs(5)':>9}")
    for r in rows:
        ch = r[channel]
        tm = ch['tau_mag']
        tph = (f"{tm['tau_s']:12.0f}" if tm and tm['tau_s'] != float('inf')
               else f"{'inf':>12}")
        r2 = f"{tm['R2']:5.2f}" if tm else " n/a "
        nf = f"{tm['n_fit']:3d}" if tm else "  0"
        a0 = ch['rho_abs_first10']
        r1 = f"{a0[1]:9.3f}" if len(a0) > 1 else "   -"
        r2l = f"{a0[2]:9.3f}" if len(a0) > 2 else "   -"
        r5 = f"{a0[5]:9.3f}" if len(a0) > 5 else "   -"
        print(f"{r['sigma']:6.3f}  {r['source']:<11} "
              f"{tph}  {r2}  {nf}  {r1} {r2l} {r5}")


def residual_phase_acorr(per_seed_list, channel_key, T_chunk_s, max_lag=30):
    """S99-style per-seed residual-phase autocorrelation: for each seed,
    unwrap angle, subtract a linear trend (absorbs any slope-of-noise
    artifact), lag-autocorrelate the residual, then seed-pool the result."""
    accs = []
    resid_rms = []
    slopes = []
    for ps in per_seed_list:
        z_list = np.array(ps[channel_key])
        z_c = z_list[:, 0] + 1j * z_list[:, 1]
        n = len(z_c)
        phi = np.unwrap(np.angle(z_c))
        t = np.arange(n) * T_chunk_s
        slope, intercept = np.polyfit(t, phi, 1)
        resid = phi - (slope * t + intercept)
        rms = float(np.sqrt((resid ** 2).mean()))
        resid_rms.append(rms)
        slopes.append(float(slope))
        x0 = resid - resid.mean()
        denom = float((x0 * x0).sum())
        ac = np.zeros(max_lag + 1, dtype=float)
        ac[0] = 1.0
        if denom > 0:
            for m in range(1, max_lag + 1):
                if n - m > 0:
                    num = float((x0[:-m] * x0[m:]).sum())
                    ac[m] = num / denom
        accs.append(ac)
    ac_pool = np.mean(accs, axis=0)
    lags_time = np.arange(max_lag + 1) * T_chunk_s
    fit = fit_exp_tau(ac_pool, lags_time, floor=0.10)
    return {
        'pooled_acorr': ac_pool.tolist(),
        'lags_time_s': lags_time.tolist(),
        'fit': fit,
        'per_seed_resid_rms_rad': resid_rms,
        'per_seed_slope_rad_per_s': slopes,
    }


def print_residual_table(rows_with_perseed):
    print("\n== τ_wander (residual phase)(σ) — from per-seed data ==")
    print(f"{'σ':>6}  {'source':<11} {'channel':>6} "
          f"{'τ_res (s)':>10} {'R²':>5} {'n_fit':>5} "
          f"{'ρ(1)':>6} {'ρ(2)':>6} {'ρ(5)':>6} "
          f"{'resid_rms':>10}")
    for r in rows_with_perseed:
        for ch in ('raw', 'st'):
            res = r[f'residual_{ch}']
            if res is None:
                continue
            f = res['fit']
            tau = f"{f['tau_s']:10.0f}" if f and f['tau_s'] != float('inf') \
                else f"{'inf':>10}"
            r2 = f"{f['R2']:5.2f}" if f else " n/a "
            nf = f"{f['n_fit']:5d}" if f else "    0"
            ac = res['pooled_acorr']
            a1 = f"{ac[1]:6.2f}" if len(ac) > 1 else "   -"
            a2 = f"{ac[2]:6.2f}" if len(ac) > 2 else "   -"
            a5 = f"{ac[5]:6.2f}" if len(ac) > 5 else "   -"
            rms = f"{np.mean(res['per_seed_resid_rms_rad']):10.2f}"
            print(f"{r['sigma']:6.3f}  {r['source']:<11} "
                  f"{ch:>6} {tau} {r2} {nf} {a1} {a2} {a5} {rms}")


if __name__ == '__main__':
    s98, s100 = load_s98_s100()
    if s100 is None:
        print("(S100 results not yet written — showing S98 only)")
    rows = build_sigma_table(s98, s100)
    print_table(rows, 'st')
    print_table(rows, 'raw')
    print_mag_table(rows, 'st')
    print_mag_table(rows, 'raw')

    # Per-seed residual-phase autocorr: only where per_seed data is stored
    rows_ps = []
    T98 = s98['meta']['params']['T_chunk_s']
    rows_ps.append({
        'sigma': s98['meta']['params']['main_sigma'],
        'source': 'S98-main',
        'residual_raw': residual_phase_acorr(
            s98['main']['per_seed'], 'z_raw', T98),
        'residual_st': residual_phase_acorr(
            s98['main']['per_seed'], 'z_st', T98),
    })
    if s100 is not None and 'per_seed' in s100.get('main', {}):
        T100 = s100['meta']['params']['T_chunk_s']
        rows_ps.append({
            'sigma': s100['main']['sigma'],
            'source': 'S100-main',
            'residual_raw': residual_phase_acorr(
                s100['main']['per_seed'], 'z_raw', T100),
            'residual_st': residual_phase_acorr(
                s100['main']['per_seed'], 'z_st', T100),
        })
    print_residual_table(rows_ps)

    with open('thor_session_100_analysis.json', 'w') as f:
        json.dump({'rows': rows, 'residual_phase': rows_ps},
                  f, indent=2, default=float)
    print("\nsaved → thor_session_100_analysis.json")
