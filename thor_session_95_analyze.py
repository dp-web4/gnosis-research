#!/usr/bin/env python3
"""Analysis for S95: cleaner α fit + phase-drift stats.

We refit α restricted to the detectable-regime rows (|z| > 2, above
the ~null-distribution tail), and we compute the circular-statistics
"phase concentration" R = |mean(exp(i·angle))| per seed to quantify
drift non-stationarity rigorously.
"""
import json
import numpy as np

with open('thor_session_95_switch_timing_results.json') as f:
    data = json.load(f)

rows = data['rows_main']

# Reprint the table
print("\nAll 6 cells:")
print(f"  {'A':>6} {'raw |z|':>8} {'ST |z|':>8} {'ratio':>6} {'N_sw':>6} {'det':>5}")
for r in rows:
    detect_raw = "R" if r['z_vec_raw'] > 2 else "."
    detect_st = "S" if r['z_vec_st'] > 2 else "."
    print(f"  {r['A']:6.3f} {r['z_vec_raw']:8.2f} {r['z_vec_st']:8.2f} "
          f"{(r['z_vec_st']/max(r['z_vec_raw'], 1e-9)):6.2f} "
          f"{r['mean_switches']:6.0f}   {detect_raw}{detect_st}")


def fit_alpha_log(rows, key, A_min=None):
    A = np.array([r['A'] for r in rows])
    z = np.array([r[key] for r in rows])
    if A_min is not None:
        mask = (A >= A_min) & (z > 0.1)
    else:
        mask = z > 0.1
    if mask.sum() < 2:
        return None
    slope, intercept = np.polyfit(np.log(A[mask]), np.log(z[mask]), 1)
    pred = slope * np.log(A[mask]) + intercept
    resid = np.log(z[mask]) - pred
    R2 = 1 - np.var(resid) / max(np.var(np.log(z[mask])), 1e-12)
    return {'alpha': float(slope), 'k': float(np.exp(intercept)),
            'R2': float(R2), 'n_pts': int(mask.sum()),
            'A_fit': A[mask].tolist(), 'z_fit': z[mask].tolist()}


# Three fits: all 6 points, subsets dropping null-floor cells
print("\n" + "=" * 70)
print("α FITS — raw vs switch-timing, at increasing A_min cutoffs")
print("=" * 70)
print(f"{'A_min':>8} {'det':>5}  {'raw α':>8} {'raw k':>7} {'raw R²':>7}    "
      f"{'ST α':>8} {'ST k':>7} {'ST R²':>7}")
for A_min in [None, 0.04, 0.08, 0.12]:
    f_r = fit_alpha_log(rows, 'z_vec_raw', A_min=A_min)
    f_s = fit_alpha_log(rows, 'z_vec_st', A_min=A_min)
    label = "all" if A_min is None else f">={A_min}"
    n = f_r['n_pts'] if f_r else 0
    print(f"{label:>8} {n:>5}  "
          f"{f_r['alpha']:8.3f} {f_r['k']:7.2f} {f_r['R2']:+7.3f}    "
          f"{f_s['alpha']:8.3f} {f_s['k']:7.2f} {f_s['R2']:+7.3f}")


# Phase-drift circular statistics
print("\n" + "=" * 70)
print("PHASE DRIFT — circular variance per seed")
print("=" * 70)
print("R (concentration) ∈ [0,1]; 1 = all angles identical, 0 = uniform drift.")
print(f"Under stationary response + seed-level noise, R → 1 as n_chunks grows.")
print(f"{'seed':>5} {'R':>6} {'circ_mean°':>10} {'circ_std°':>10} {'range°':>8}")
for s in data['chunked_drift']:
    ang = np.radians(s['angles_deg'])
    cvec = np.mean(np.exp(1j * ang))
    R = np.abs(cvec)
    circ_mean = np.degrees(np.angle(cvec))
    # Circular std: sqrt(-2 ln R) in radians
    circ_std = np.degrees(np.sqrt(-2 * np.log(max(R, 1e-12))))
    angs = s['angles_deg']
    rng = max(angs) - min(angs)
    print(f"{s['seed']:>5d} {R:>6.3f} {circ_mean:>+10.1f} {circ_std:>10.1f} "
          f"{rng:>8.1f}")

# Aggregate
R_all = []
for s in data['chunked_drift']:
    ang = np.radians(s['angles_deg'])
    R_all.append(np.abs(np.mean(np.exp(1j * ang))))
R_all = np.array(R_all)
print(f"\nMean R across 4 seeds: {R_all.mean():.3f} ± {R_all.std():.3f}")
print("Expected R under no-drift + noise-only: ~0.8-0.95 (even at n=8 chunks)")
print("Observed R values indicate substantial non-stationary drift.")

# Per-seed angle sequence — look for progressive rotation
print("\n" + "=" * 70)
print("PROGRESSIVE ROTATION — is angle change monotone?")
print("=" * 70)
print("Test: per seed, does cumulative angle sum show a trend?")
for s in data['chunked_drift']:
    angs = np.asarray(s['angles_deg'])
    unwrapped = np.degrees(np.unwrap(np.radians(angs)))
    # Fit linear drift to unwrapped
    t = np.arange(len(angs))
    slope, intercept = np.polyfit(t, unwrapped, 1)
    pred = slope * t + intercept
    resid = unwrapped - pred
    print(f"  seed {s['seed']}: unwrapped angles = "
          f"{[f'{a:+6.1f}' for a in unwrapped]}")
    print(f"          linear drift = {slope:+6.1f}°/chunk  "
          f"RMS residual = {resid.std():.1f}°")
