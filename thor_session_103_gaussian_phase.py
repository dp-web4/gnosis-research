#!/usr/bin/env python3
"""Verify the Gaussian-phase interpretation: within a single seed,
    plateau = mean(|Φ(m)|) = exp(-σ_Δresid² / 2)
for iid Gaussian residual-phase differences.

If the residual phase within a seed is iid white with std σ_resid, then
Δresid = resid(k) − resid(k+m) is zero-mean Gaussian with variance 2σ_resid²,
and E[exp(i·Δresid)] = exp(-σ_resid²).

So the per-seed plateau level should be:
    RAW:  0.35 ≈ exp(-σ_RAW_resid²)    →    σ_RAW ≈ 1.02 rad
    ST:   0.76 ≈ exp(-σ_ST_resid²)     →    σ_ST  ≈ 0.52 rad

Compared to direct measurement of σ_resid per seed (after linear detrend).
"""
import json
import numpy as np

with open('thor_session_98_phase_drift_results.json') as f:
    s98 = json.load(f)


def per_seed_cplx(records, key):
    return [np.array([complex(p[0], p[1]) for p in s[key]]) for s in records]


def seed_residual_stats(z):
    phi = np.unwrap(np.angle(z))
    k = np.arange(len(phi))
    slope, intercept = np.polyfit(k, phi, 1)
    resid = phi - slope * k - intercept
    # Check normality loosely: skewness and kurtosis
    return {
        'sigma_resid_rad': float(np.std(resid)),
        'mean_resid_rad': float(np.mean(resid)),
        'skew': float(((resid - resid.mean())**3).mean() / (resid.std()**3 + 1e-12)),
        'excess_kurt': float(((resid - resid.mean())**4).mean() / (resid.std()**4 + 1e-12) - 3.0),
        'slope_per_chunk': float(slope),
    }

def acf_plateau(z, lag_range=(1, 60)):
    phi = np.unwrap(np.angle(z))
    k = np.arange(len(phi))
    slope, intercept = np.polyfit(k, phi, 1)
    resid = phi - slope * k - intercept
    u = np.exp(1j * resid)
    vals = []
    for m in range(lag_range[0], lag_range[1] + 1):
        if len(u) - m <= 0: break
        vals.append(abs(np.mean(u[:-m] * np.conj(u[m:]))))
    return float(np.mean(vals))


print("Gaussian-phase calibration test (S98 main, 8 seeds × 100 chunks)")
print("=" * 78)
for ch, key in [('RAW', 'z_raw'), ('ST', 'z_st')]:
    zs = per_seed_cplx(s98['main']['per_seed'], key)
    print(f"\n{ch} channel:")
    print(f"{'seed':>4}  {'σ_resid':>9}  {'exp(-σ²)':>10}  {'measured':>10}  {'skew':>7}  {'ex_kurt':>8}")
    gauss_preds = []
    measured = []
    for i, z in enumerate(zs):
        st = seed_residual_stats(z)
        pred = float(np.exp(-st['sigma_resid_rad']**2))
        meas = acf_plateau(z, (1, 60))
        gauss_preds.append(pred)
        measured.append(meas)
        print(f"{i:>4}   {st['sigma_resid_rad']:>7.3f}r  "
              f"{pred:>10.3f}  {meas:>10.3f}  "
              f"{st['skew']:>+7.2f}  {st['excess_kurt']:>+8.2f}")
    print(f"  mean pred:  {np.mean(gauss_preds):.3f}")
    print(f"  mean meas:  {np.mean(measured):.3f}")
    print(f"  bias: {np.mean(measured) - np.mean(gauss_preds):+.3f}")

print("\n" + "=" * 78)
print("Interpretation:")
print("=" * 78)
print("""
If per-seed residual phase is iid zero-mean Gaussian with std σ_resid, then:
    Φ(m≥1) = E[exp(i·(resid_k − resid_{k+m}))] = exp(-σ_resid²)
regardless of m. The measured per-seed plateau matching this prediction
confirms the residual is (approximately) iid white.

If the plateau were FROM a slow dynamical timescale, we'd expect it to
diverge from exp(-σ_resid²) — e.g., a decay vs. constant value — and
skew/kurt would be detectable.

Implications:
 - S99's "τ_res ≈ 22ks" (10-lag exp fit) = projection of cross-seed
   angle-drift differences onto a simple 1-τ exp. Not a true timescale.
 - S101's "plateau + white" decomposition at per-seed scale = exactly
   Gaussian-phase autocorr with constant = exp(-σ²). Correct shape but
   "plateau" is a calibration constant, not a dynamical phenomenon.
 - S102's "τ≈80ks exponential" (30-lag fit on pooled) = same artifact
   with longer lag window picking up more of the inter-seed decoherence.
 - The REAL physical quantity is σ_resid per seed (which varies with A,
   σ, ω_spread via SNR).
""")
