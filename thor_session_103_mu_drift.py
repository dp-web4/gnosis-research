#!/usr/bin/env python3
"""Is there slow drift of μ(t) over a single seed's trajectory?

If z(k) = μ(k) + ε(k) with μ slowly varying (not strictly constant),
that WOULD be a dynamical timescale — not an SNR-floor artifact.

Test: split each seed's 100 chunks into N_win = 10 windows of 10 chunks
each. Compute |μ_win| per window. If constant, μ is stationary.
If μ varies window-to-window, the variance of |μ_win| tells us the drift.

Reference: σ_Mc noise per window is √(var(z)/10) ≈ σ_n/√10, so
var(|μ_win|) from pure-white-noise-baseline = σ_n²/(10·|μ|) (via
|μ+ε| ≈ |μ| + Re(ε·exp(-iφμ))/|μ| for small ε).

Null expected std(|μ_win|) ≈ σ_n/(√10) if |μ|≫σ_n, or ~ σ_n/√10 in
general. Compare measured vs this null.
"""
import json
import numpy as np

with open('thor_session_98_phase_drift_results.json') as f:
    s98 = json.load(f)


def per_seed_cplx(records, key):
    return [np.array([complex(p[0], p[1]) for p in s[key]]) for s in records]


def window_mu_drift(z, n_windows=10):
    N = len(z)
    w = N // n_windows
    mus = []
    sigs = []
    for i in range(n_windows):
        chunk = z[i*w:(i+1)*w]
        mu = chunk.mean()
        sig = np.sqrt(np.mean(np.abs(chunk - mu)**2))
        mus.append(mu)
        sigs.append(sig)
    return np.array(mus), np.array(sigs)


for ch, key in [('RAW', 'z_raw'), ('ST', 'z_st')]:
    print(f"\n{ch} channel — per-seed μ-drift over 10 windows of 10 chunks")
    print("=" * 80)
    print(f"{'seed':>4}  {'|μ|_global':>12}  {'|μ_win|_mean':>12}  "
          f"{'|μ_win|_std':>12}  {'null_sd':>10}  {'ratio':>6}")
    zs = per_seed_cplx(s98['main']['per_seed'], key)
    ratios = []
    for i, z in enumerate(zs):
        mus, sigs = window_mu_drift(z, 10)
        mu_global = abs(z.mean())
        sig_global = np.sqrt(np.mean(np.abs(z - z.mean())**2))
        mu_win_abs = np.abs(mus)
        measured_sd = np.std(mu_win_abs)
        null_sd = sig_global / np.sqrt(10)
        ratio = measured_sd / null_sd if null_sd > 0 else 0
        ratios.append(ratio)
        print(f"{i:>4}  {mu_global:>12.4e}  {mu_win_abs.mean():>12.4e}  "
              f"{measured_sd:>12.4e}  {null_sd:>10.4e}  {ratio:>6.2f}")
    print(f"  ratio = measured SD / null SD (expected ≈ 1 if μ stationary)")
    print(f"  mean ratio across 8 seeds: {np.mean(ratios):.2f}")
    print(f"  std  ratio: {np.std(ratios):.2f}")
    if np.mean(ratios) > 1.3:
        print("  → SLOW drift of μ detected (ratio > 1.3)")
    elif np.mean(ratios) < 0.7:
        print("  → Sub-null SD: μ oscillates coherently (unlikely, verify)")
    else:
        print("  → Consistent with stationary μ + white noise ε (within ±30%)")

# Cross-seed: angular coherence of μ_win across seeds WITHIN each window
print("\n" + "=" * 80)
print("Cross-seed angular coherence of μ_win per window")
print("=" * 80)
for ch, key in [('RAW', 'z_raw'), ('ST', 'z_st')]:
    zs = per_seed_cplx(s98['main']['per_seed'], key)
    print(f"\n{ch}: R_angle(seeds) per window")
    print(f"{'window':>7}", end='')
    for w_i in range(10):
        print(f"  w{w_i}", end='')
    print()
    # For each window, compute angles of μ_win across seeds, then R_angle
    all_R = []
    for w_i in range(10):
        angles = []
        for z in zs:
            mu_win, _ = window_mu_drift(z, 10)
            angles.append(np.angle(mu_win[w_i]))
        R = abs(np.mean(np.exp(1j * np.array(angles))))
        all_R.append(R)
    print(f"  R_angle", end='')
    for R in all_R:
        print(f"  {R:.2f}", end='')
    print()
    print(f"  mean R_angle across windows: {np.mean(all_R):.3f}")
