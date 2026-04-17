#!/usr/bin/env python3
"""
Thor Session #93 — Part 2: Analytical Lorentzian Fit

S92 Prediction #1: the S86 "SR curve" (response_amp vs sigma at
signal_freq=0.003, A=0.02) is the bistability Lorentzian evaluated at
f_s, not a signal curve. A quantitative fit using the S82-derived
Kramers rate r_K(σ) should match S92's natural-PSD power@signal_freq
sweep (where signal_amp = 0).

Two-state random telegraph PSD (Wiener-Khinchin):
    S(ω) = 2 Δ² · 2r_K / ((2r_K)² + ω²)
Equivalently, S(f) = 4 Δ² r_K / (4r_K² + (2πf)²)

Peak as a function of r_K: ∂/∂r_K [r_K / (4r_K² + (2πf)²)] = 0
yields 4r_K² = (2πf)², i.e., r_K = πf.
At f_s = 0.003 → r_K* = 0.00942.

Using S82 Kramers fit r_K(σ) = r_0 exp(-ΔU/σ²):
    σ* satisfies r_0 exp(-ΔU/σ*²) = r_K*
    σ*² = ΔU / log(r_0/r_K*)

We fit:
  1) Extract r_K(σ) from S82 (direct measurements).
  2) Evaluate S(f_s=0.003, σ) from the two-state Lorentzian.
  3) Compare to S92 experiment_A "power_at_signal_freq" column.
  4) One amplitude scaling parameter Δ² fit via least-squares.

If shape + location match with one scale parameter, Prediction #1 holds.
"""

import json
import numpy as np
import sys

sys.stdout.reconfigure(line_buffering=True)

# ─── Load S82 Kramers rates ───
with open('thor_session_82_potential_results.json') as f:
    s82 = json.load(f)
rates = s82['expC']['rates']
sig82 = np.array([r['noise'] for r in rates])
rk82 = np.array([r['rate'] for r in rates])

# Re-derive Kramers fit
D82 = sig82**2
A_mat = np.vstack([1/D82, np.ones_like(D82)]).T
m, b = np.linalg.lstsq(A_mat, np.log(rk82), rcond=None)[0]
dU_fit = -m
r0_fit = np.exp(b)
print(f"S82 Kramers fit: r_K(σ) = {r0_fit:.4f} · exp(-{dU_fit:.6f}/σ²)")
print(f"  r² = {s82['expC']['r_squared']:.4f}")


def rK(sigma, dU=dU_fit, r0=r0_fit):
    return r0 * np.exp(-dU / sigma**2)


def lorentzian_S_at_f(sigma, f_s, Delta2=1.0):
    """Two-state RTN PSD at frequency f_s, for given sigma.
    S(f) = 4 Δ² r_K / (4 r_K² + (2πf)²)
    """
    r = rK(sigma)
    return 4 * Delta2 * r / (4 * r**2 + (2 * np.pi * f_s)**2)


# ─── Load S92 natural-PSD data ───
with open('thor_session_92_sr_falsifiability_results.json') as f:
    s92 = json.load(f)
npsd = s92['experiment_A_natural_psd']
sig92 = np.array([r['sigma'] for r in npsd])
peakf92 = np.array([r['peak_freq'] for r in npsd])
powsf92 = np.array([r['power_at_signal_freq'] for r in npsd])

print("\nS92 natural PSD:")
print(f"  {'σ':>7} {'peak_freq':>10} {'power@f_s':>10}")
for s, pf, ps in zip(sig92, peakf92, powsf92):
    print(f"  {s:7.4f} {pf:10.5f} {ps:10.2f}")

# ─── Predict S(f_s, σ) using Kramers-Lorentzian ───
f_s = 0.003

# Fit Δ² using least-squares on power_at_signal_freq vs σ
# over the range where Kramers theory applies (σ in [0.008, 0.050])
mask = (sig92 >= 0.008) & (sig92 <= 0.050)
sig_fit = sig92[mask]
pow_fit = powsf92[mask]
model_unit = np.array([lorentzian_S_at_f(s, f_s, Delta2=1.0) for s in sig_fit])
# scalar fit: pow ≈ Delta2 · model_unit
Delta2_est = float(np.sum(pow_fit * model_unit) / np.sum(model_unit**2))
print(f"\nFit Δ² = {Delta2_est:.4f}  (using σ ∈ [{sig_fit.min()}, {sig_fit.max()}])")

# Compute predictions on full σ grid
pred_powsf = np.array([lorentzian_S_at_f(s, f_s, Delta2=Delta2_est) for s in sig92])

print(f"\nPrediction vs data:")
print(f"  {'σ':>7} {'data':>8} {'pred':>8} {'ratio':>7} {'resid%':>7}")
for s, d, p in zip(sig92, powsf92, pred_powsf):
    ratio = d / p if p > 0 else float('inf')
    resid_pct = 100 * (d - p) / d if d > 0 else float('inf')
    print(f"  {s:7.4f} {d:8.2f} {p:8.2f} {ratio:7.3f} {resid_pct:+7.1f}")

# R² over fit range
pred_fit = np.array([lorentzian_S_at_f(s, f_s, Delta2=Delta2_est) for s in sig_fit])
ss_res = float(np.sum((pow_fit - pred_fit)**2))
ss_tot = float(np.sum((pow_fit - np.mean(pow_fit))**2))
r2 = 1 - ss_res / ss_tot
print(f"\nR² of Kramers-Lorentzian fit on σ ∈ [0.008, 0.050]: {r2:.3f}")

# Peak location prediction
# r_K* = π f_s → σ*² = dU / log(r0/r_K*)
r_K_target = np.pi * f_s
sig_star = float(np.sqrt(dU_fit / np.log(r0_fit / r_K_target)))
print(f"\nPredicted optimal σ* (where r_K = πf_s = {r_K_target:.5f}): "
      f"σ* = {sig_star:.4f}")
# Where does the data peak?
i_max = int(np.argmax(powsf92))
print(f"Observed peak of power@f_s: σ = {sig92[i_max]:.4f}  "
      f"(value {powsf92[i_max]:.1f})")

# Also predict peak frequency of natural PSD (not at f_s, but ω*_peak):
# For two-state RTN centered at 0 with rate r_K, PSD is monotonically
# decreasing from f=0, so "peak frequency" is 0. BUT the observed
# "peak_freq" in S92 was the argmax of windowed Hann periodogram in
# f > 1e-4, subject to spectral leakage and finite-window artifacts.
# The Lorentzian's HALF-WIDTH (where S drops to S(0)/2) is at
#   f_half = r_K / π
# That's not a peak, but it's a characteristic frequency.

# ─── Save ───
out = {
    'kramers_fit': {'dU': float(dU_fit), 'r0': float(r0_fit),
                    'r2_fit': float(s82['expC']['r_squared'])},
    'Delta2_est': Delta2_est,
    'lorentzian_prediction': [
        {'sigma': float(s), 'r_K': float(rK(s)),
         'pred_S_at_fs': float(lorentzian_S_at_f(s, f_s, Delta2_est))}
        for s in sig92
    ],
    's92_data_comparison': [
        {'sigma': float(s), 'observed': float(d),
         'predicted': float(p),
         'residual_pct': float(100 * (d - p) / d) if d > 0 else None}
        for s, d, p in zip(sig92, powsf92, pred_powsf)
    ],
    'sigma_star_predicted': sig_star,
    'sigma_peak_observed': float(sig92[i_max]),
    'r_squared_fit': float(r2),
}
with open('thor_session_93_lorentzian_fit_results.json', 'w') as f:
    json.dump(out, f, indent=2)
print("\nSaved thor_session_93_lorentzian_fit_results.json")
