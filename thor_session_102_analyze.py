#!/usr/bin/env python3
"""S102 secondary analysis:
   - Print full ACF curves (lags 0..30) for all 6 A values
   - Fit two-component model (plateau + exponential slow decay)
   - Per-seed plateau spread
   - Corrected M2 formula (p = exp(-σ_n²/(2|μ|²)) = exp(-1/(2·SNR²)))
     vs empirical
   - Model M3 (Rice-distribution magnitude of ⟨e^(iφ̃)⟩):
     p(ν) = (π/4)·ν²·exp(-ν²/2)·[I₀(ν²/4) + I₁(ν²/4)]²
     where ν = |μ|/σ  (per-component σ, with σ = σ_n/√2)
"""
import json
import numpy as np
from scipy.special import i0, i1

with open('thor_session_102_plateau_scaling_results.json') as f:
    d = json.load(f)

A_vals_sorted = sorted(d['per_A'].keys(), key=float)

print("=" * 72)
print("FULL ACF CURVES, lags 0..30  (plateau profile)")
print("=" * 72)
print("\nRAW channel:")
print(f"{'A':>5} | {'lag 1':>6} {'5':>6} {'10':>6} {'15':>6} "
      f"{'20':>6} {'25':>6} {'30':>6}")
for Ak in A_vals_sorted:
    A = d['per_A'][Ak]['A']
    acf = d['per_A'][Ak]['raw']['abs_acf']
    print(f"{A:>5.2f} | {acf[1]:>6.3f} {acf[5]:>6.3f} {acf[10]:>6.3f} "
          f"{acf[15]:>6.3f} {acf[20]:>6.3f} {acf[25]:>6.3f} {acf[30]:>6.3f}")

print("\nST channel:")
print(f"{'A':>5} | {'lag 1':>6} {'5':>6} {'10':>6} {'15':>6} "
      f"{'20':>6} {'25':>6} {'30':>6}")
for Ak in A_vals_sorted:
    A = d['per_A'][Ak]['A']
    acf = d['per_A'][Ak]['st']['abs_acf']
    print(f"{A:>5.2f} | {acf[1]:>6.3f} {acf[5]:>6.3f} {acf[10]:>6.3f} "
          f"{acf[15]:>6.3f} {acf[20]:>6.3f} {acf[25]:>6.3f} {acf[30]:>6.3f}")


print("\n" + "=" * 72)
print("TWO-COMPONENT FIT: ACF(m) = p_∞ + B·exp(-m·T_chunk/τ)  "
      "for m ≥ 1")
print("=" * 72)
print("Fit only lags 1..30 (skip lag-0 spike).")


def fit_two_component(acf_values, max_lag):
    """Fit ACF(m) = p_inf + B * exp(-m*T/τ) for m ≥ 1.
    Use log-domain linearization: y = acf(m) - p_inf.
    We find p_inf by minimizing residual; grid over p_inf values.
    """
    a = np.array(acf_values[1:max_lag + 1])  # lags 1..max_lag
    m = np.arange(1, max_lag + 1)
    best = None
    for p_inf_try in np.linspace(0, a.min() + 0.0, 101) if a.min() > 0 else np.linspace(-0.02, 0.02, 41):
        # actually let's try a wider grid
        pass
    grid = np.linspace(0.0, max(a.min() - 0.001, 0.001), 100)
    if a.min() < 0.01:
        grid = np.linspace(-0.02, 0.05, 100)
    for p_inf in grid:
        y = a - p_inf
        # only fit where y > floor
        ok = y > 0.005
        if ok.sum() < 4:
            continue
        logy = np.log(y[ok])
        slope, intercept = np.polyfit(m[ok], logy, 1)
        tau_lag = -1.0 / slope if slope < 0 else float('inf')
        B = np.exp(intercept)
        pred = p_inf + B * np.exp(-m/tau_lag) if tau_lag != float('inf') else np.full_like(m, p_inf) + B
        ss_res = float(np.sum((a - pred)**2))
        if best is None or ss_res < best['ss_res']:
            best = {'p_inf': float(p_inf), 'B': float(B),
                    'tau_lag': float(tau_lag), 'ss_res': ss_res,
                    'pred_full': pred.tolist()}
    # also report pure-plateau fit (single constant)
    p_pure = float(a.mean())
    ss_pure = float(np.sum((a - p_pure)**2))
    # pure-exp fit (p_inf = 0)
    ok = a > 0.005
    if ok.sum() >= 4:
        logy = np.log(a[ok])
        slope, intercept = np.polyfit(m[ok], logy, 1)
        tau_pure_exp = -1/slope if slope < 0 else float('inf')
        B_pure = float(np.exp(intercept))
        pred_pure_exp = B_pure * np.exp(-m/tau_pure_exp) if tau_pure_exp != float('inf') else np.zeros_like(m)
        ss_pure_exp = float(np.sum((a - pred_pure_exp)**2))
    else:
        tau_pure_exp = float('inf'); ss_pure_exp = float('inf')
        B_pure = 0.0
    return best, {'p_pure': p_pure, 'ss_pure': ss_pure}, \
           {'tau_pure_exp_lag': tau_pure_exp,
            'B_pure_exp': B_pure, 'ss_pure_exp': ss_pure_exp}


T_CHUNK_S = d['meta']['params']['T_chunk_s']
MAX = d['meta']['params']['max_lag']
print(f"\nT_chunk = {T_CHUNK_S}s, max_lag = {MAX}\n")
print("RAW channel:")
print(f"{'A':>5} | {'p_inf':>6} {'B':>6} {'τ(s)':>10} | "
      f"{'pure p':>6} | {'RMS 2c':>7} {'RMS pure':>8}")
for Ak in A_vals_sorted:
    A = d['per_A'][Ak]['A']
    acf = d['per_A'][Ak]['raw']['abs_acf']
    two, pure, pex = fit_two_component(acf, MAX)
    tau_s = two['tau_lag'] * T_CHUNK_S if two and np.isfinite(two['tau_lag']) else float('inf')
    rms2 = np.sqrt(two['ss_res']/MAX) if two else float('inf')
    rmsp = np.sqrt(pure['ss_pure']/MAX)
    print(f"{A:>5.2f} | {two['p_inf']:>6.3f} {two['B']:>6.3f} "
          f"{tau_s:>10.0f} | {pure['p_pure']:>6.3f} | "
          f"{rms2:>7.4f} {rmsp:>8.4f}")

print("\nST channel:")
print(f"{'A':>5} | {'p_inf':>6} {'B':>6} {'τ(s)':>10} | "
      f"{'pure p':>6} | {'RMS 2c':>7} {'RMS pure':>8}")
for Ak in A_vals_sorted:
    A = d['per_A'][Ak]['A']
    acf = d['per_A'][Ak]['st']['abs_acf']
    two, pure, pex = fit_two_component(acf, MAX)
    tau_s = two['tau_lag'] * T_CHUNK_S if two and np.isfinite(two['tau_lag']) else float('inf')
    rms2 = np.sqrt(two['ss_res']/MAX) if two else float('inf')
    rmsp = np.sqrt(pure['ss_pure']/MAX)
    print(f"{A:>5.2f} | {two['p_inf']:>6.3f} {two['B']:>6.3f} "
          f"{tau_s:>10.0f} | {pure['p_pure']:>6.3f} | "
          f"{rms2:>7.4f} {rmsp:>8.4f}")


print("\n" + "=" * 72)
print("CORRECTED M2 + M3 (Rice) vs measured plateau")
print("=" * 72)
print("M2_corr: p = exp(-σ_n²/(2|μ|²)) = exp(-1/(2·SNR²))")
print("         where SNR² = 2·|μ|²/σ_n² = |μ|²/σ² (per-component σ)")
print("M3 (Rice): p(ν) = ⟨cos(φ̃)⟩² + ⟨sin(φ̃)⟩² for z = μ + N(0,σ²I₂)")
print("         Closed form (|μ|/σ = ν):")
print("         ⟨e^(iφ̃)⟩ = √(π/2)·(ν/2)·exp(-ν²/4)·[I₀(ν²/4)+I₁(ν²/4)]")
print()


def rice_phase_concentration(nu):
    """⟨e^(i·(arg(z)-arg(μ)))⟩ for z = μ·1 + (X + iY), X,Y~N(0,σ²).
    Use the exact Rice-distribution formula with ν = |μ|/σ.
    For ν large: ~ 1 - 1/(4ν²)
    For ν small: ~ √(π/2)·(ν/2)
    """
    nu = np.atleast_1d(nu)
    nu2 = nu**2
    # Exact: ⟨e^iφ̃⟩ = ⟨cos φ̃⟩ + i⟨sin φ̃⟩.
    # For Rice with mean real (μ>0, real), ⟨sin φ̃⟩=0.
    # ⟨cos φ̃⟩ = √(π/8)·ν·exp(-ν²/4)·[(1+ν²/2)·I₀(ν²/4) + (ν²/2)·I₁(ν²/4)]
    # ... this is the form from Abramowitz; let me use Marsaglia/Rice form:
    # E[e^iφ] = √(π/2)·(ν/2)·exp(-ν²/4)·(I₀(ν²/4) + I₁(ν²/4))
    arg = nu2 / 4
    c = np.sqrt(np.pi / 2) * (nu / 2) * np.exp(-arg) * (i0(arg) + i1(arg))
    return c


def p_from_phase_concentration(Ce):
    """For iid phases drawn from Rice-phase-dist with concentration ⟨e^iφ̃⟩ = Ce,
    p(m≥1) = |Ce|²."""
    return np.abs(Ce)**2


fits = d['fits']
mu_raw = fits['mu_raw']
sig_raw = fits['sig_raw']
mu_st = fits['mu_st']
sig_st = fits['sig_st']
A_vals = fits['A_vals']
p_raw = fits['p_raw']
p_st = fits['p_st']

print("RAW channel:")
print(f"{'A':>5} | {'|μ|':>10} {'σ_n':>10} {'ν=√2|μ|/σ_n':>13} | "
      f"{'M2_corr':>8} {'M3 Rice':>8} | {'measured':>9}")
for i, Ak in enumerate(A_vals):
    mu = mu_raw[i]; sig = sig_raw[i]
    nu = np.sqrt(2) * mu / sig if sig > 0 else 0.0  # per-component σ = σ_n/√2
    snr2 = nu**2  # SNR² for complex signal (|μ|²/σ²) with σ per-component
    m2_corr = np.exp(-1/(2*snr2)) if snr2 > 1e-10 else 0.0
    # Actually: M2_corr as I defined = exp(-σ_n²/(2|μ|²)) = exp(-1/ν²) since ν²=2|μ|²/σ_n²
    # Wait let me redo: σ_n² = 2σ² (total complex noise power), so σ_n²/(2|μ|²) = σ²/|μ|² = 1/ν².
    m2_corr = np.exp(-1/nu**2) if nu > 1e-5 else 0.0
    rice_c = float(rice_phase_concentration(nu))
    m3 = rice_c**2
    print(f"{Ak:>5.2f} | {mu:>10.4e} {sig:>10.4e} {nu:>13.3f} | "
          f"{m2_corr:>8.3f} {m3:>8.3f} | {p_raw[i]:>9.3f}")

print("\nST channel:")
print(f"{'A':>5} | {'|μ|':>10} {'σ_n':>10} {'ν=√2|μ|/σ_n':>13} | "
      f"{'M2_corr':>8} {'M3 Rice':>8} | {'measured':>9}")
for i, Ak in enumerate(A_vals):
    mu = mu_st[i]; sig = sig_st[i]
    nu = np.sqrt(2) * mu / sig if sig > 0 else 0.0
    m2_corr = np.exp(-1/nu**2) if nu > 1e-5 else 0.0
    rice_c = float(rice_phase_concentration(nu))
    m3 = rice_c**2
    print(f"{Ak:>5.2f} | {mu:>10.4f} {sig:>10.4f} {nu:>13.3f} | "
          f"{m2_corr:>8.3f} {m3:>8.3f} | {p_st[i]:>9.3f}")

print("\n" + "=" * 72)
print("M3 (Rice) fit — should be EXACT under Gaussian-chunk-noise-around-μ")
print("if μ is seed-seed coherent and chunks are iid around it.")
print("=" * 72)
m3_raw_pred = []
m3_st_pred = []
for i in range(len(A_vals)):
    nu_r = np.sqrt(2) * mu_raw[i] / sig_raw[i] if sig_raw[i] > 0 else 0
    nu_s = np.sqrt(2) * mu_st[i] / sig_st[i] if sig_st[i] > 0 else 0
    m3_raw_pred.append(float(rice_phase_concentration(nu_r))**2)
    m3_st_pred.append(float(rice_phase_concentration(nu_s))**2)

rmse_raw = np.sqrt(np.mean((np.array(p_raw) - np.array(m3_raw_pred))**2))
rmse_st = np.sqrt(np.mean((np.array(p_st) - np.array(m3_st_pred))**2))
print(f"  RAW M3 RMSE: {rmse_raw:.4f}  "
      f"(M1 RMSE was {fits['raw']['M1']['rmse']:.4f})")
print(f"  ST  M3 RMSE: {rmse_st:.4f}  "
      f"(M1 RMSE was {fits['st']['M1']['rmse']:.4f})")

print("\n" + "=" * 72)
print("PER-SEED PLATEAU SPREAD  (lags 1..30 mean per seed)")
print("=" * 72)
for Ak in A_vals_sorted:
    A = d['per_A'][Ak]['A']
    # seed-level ACF was not stored (we aggregated into per-seed acf_abs).
    # Check: 'raw': {'per_seed_dw': ..., 'per_seed_resid_rms': ...}
    rrms = d['per_A'][Ak]['raw']['per_seed_resid_rms']
    srms = d['per_A'][Ak]['st']['per_seed_resid_rms']
    print(f"A={A:>5.2f}  RAW resid_rms (rad): "
          f"min={min(rrms):.2f} max={max(rrms):.2f} "
          f"mean={np.mean(rrms):.2f} ± {np.std(rrms):.2f}")
    print(f"         ST  resid_rms (rad): "
          f"min={min(srms):.2f} max={max(srms):.2f} "
          f"mean={np.mean(srms):.2f} ± {np.std(srms):.2f}")

# Save compact summary
out = {
    'per_A_summary': {Ak: {
        'A': d['per_A'][Ak]['A'],
        'raw_plateau': d['per_A'][Ak]['raw']['plateau']['plateau_mean'],
        'raw_slope_per_lag': d['per_A'][Ak]['raw']['plateau']['slope_per_lag'],
        'raw_acf': d['per_A'][Ak]['raw']['abs_acf'],
        'st_plateau': d['per_A'][Ak]['st']['plateau']['plateau_mean'],
        'st_slope_per_lag': d['per_A'][Ak]['st']['plateau']['slope_per_lag'],
        'st_acf': d['per_A'][Ak]['st']['abs_acf'],
        'mu_raw': d['per_A'][Ak]['raw']['seeds']['mean_mu_abs'],
        'mu_st': d['per_A'][Ak]['st']['seeds']['mean_mu_abs'],
        'sig_raw': d['per_A'][Ak]['raw']['seeds']['mean_sigma_n'],
        'sig_st': d['per_A'][Ak]['st']['seeds']['mean_sigma_n'],
    } for Ak in A_vals_sorted},
    'M1_RAW_sigA2': fits['raw']['M1']['sigA2_LS'],
    'M1_ST_sigA2': fits['st']['M1']['sigA2_LS'],
    'M3_raw_pred': m3_raw_pred,
    'M3_st_pred': m3_st_pred,
    'M3_raw_rmse': float(rmse_raw),
    'M3_st_rmse': float(rmse_st),
}
with open('thor_session_102_analysis.json', 'w') as f:
    json.dump(out, f, indent=2, default=float)
print("\nSaved → thor_session_102_analysis.json")
