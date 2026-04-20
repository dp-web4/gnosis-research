#!/usr/bin/env python3
"""Deep analysis of extended S98 ACF: is RAW really an exponential, or a
damped oscillation/beat?

The extended-lag ACF computed in thor_session_103_s98_extended.json shows:
  lag 1:  0.343      lag 50: 0.157
  lag 10: 0.291      lag 60: 0.022
  lag 20: 0.147      lag 70: 0.127
  lag 30: 0.214      lag 80: 0.154
  lag 40: 0.245      lag 99: 0.426  (edge effect?)

This is NOT a clean exponential decay. The |Φ(m)| bounces with minima at
m ≈ 20, 60 and local maxima at m ≈ 40, 95 (before edge-effect explosion).

Suggests either:
 (A) a damped oscillation: Φ(m) ≈ p_∞ + A·exp(-m/τ)·cos(ω m + φ),
     i.e. a beat frequency in the residual phase.
 (B) an edge artifact: with 100 chunks, lag m has (100 − m) pairs per seed,
     so lag 99 has only 1 pair per seed = 8 total. Noise floor is ~1/√8 ≈ 0.35.
 (C) a superposition of two timescales that look like exponential on short
     lags and something else on long lags.

Plus the complex-valued arg(Φ(m)) is NOT small — it drifts from 0° through
−50° by m=40 to ±180° by m=65−70. That's a ROTATION: the residual is
coherently precessing. If the angle drifts linearly in m, there's a
systematic frequency in the residual.
"""
import json
import numpy as np
from scipy.optimize import least_squares

with open('thor_session_103_s98_extended.json') as f:
    D = json.load(f)

T_CHUNK_S = float(D['T_chunk_s'])
raw = np.array(D['raw_abs_acf'])
st = np.array(D['st_abs_acf'])
raw_arg = np.array(D['raw_arg_acf_deg'])
st_arg = np.array(D['st_arg_acf_deg'])

# Complex ACF (reconstruct from abs + arg)
raw_cplx = raw * np.exp(1j * np.deg2rad(raw_arg))
st_cplx = st * np.exp(1j * np.deg2rad(st_arg))
N = len(raw)
M = np.arange(N)

print("EXTENDED S98 ACF — RAW channel deep analysis")
print("=" * 68)
print(f"\nN chunks: {D['n_chunks']}  → effective pairs at lag m: {D['n_seeds']}·(N−m)")
print("Edge-noise floor at lag m = 1/√[8·(100−m)]:")
for m in [1, 30, 60, 90, 99]:
    floor = 1.0 / np.sqrt(8 * (100 - m))
    print(f"  lag m={m}: {floor:.3f}   actual |Φ|={raw[m]:.3f}")

print("\n" + "=" * 68)
print("COMPLEX-PLANE RAW ACF: is the arg-drift LINEAR in m?")
print("=" * 68)
# Unwrap to check for linear phase drift
# BUT: at m>~65 |Φ| < 0.1 so arg is noisy. Limit to where |Φ| > 0.15
mask = (M >= 1) & (raw > 0.15)
mm = M[mask]
arg_unwrap = np.unwrap(np.deg2rad(raw_arg[mask]))
if len(mm) >= 3:
    slope, intercept = np.polyfit(mm, arg_unwrap, 1)
    pred = slope * mm + intercept
    resid = arg_unwrap - pred
    print(f"  Fit region: lags {mm.min()}..{mm.max()} ({mask.sum()} points with |Φ|>0.15)")
    print(f"  Linear-fit slope: {slope:+.4f} rad/lag  ({np.rad2deg(slope):+.2f}°/lag)")
    print(f"  Residual rad RMS: {resid.std():.3f}")
    # Corresponding frequency
    f_beat_Hz = slope / (2 * np.pi * T_CHUNK_S)
    if abs(f_beat_Hz) > 1e-9:
        period = 1.0 / abs(f_beat_Hz)
        print(f"  → Implied residual-beat frequency: {f_beat_Hz:+.2e} Hz")
        print(f"    Period: {period:.0f}s = {period/1000:.0f} ks")
        # relate to ω_spread=0.02 and signal_freq=0.003
        # omega_spread = 0.02 rad/s (in the simulator's internal units; dt=0.1)
        # So ω_spread in Hz = 0.02/(2π) · (1/dt) = 0.00318/dt = 0.0318 Hz??
        # Actually the simulator uses dt=0.1, so omega_base=0.1 rad "per step-time unit"
        # = omega_base/dt rad/s = 1.0 rad/s internal.
        # This is getting confusing — the key is that the OBSERVED residual beat
        # period tells us something empirical.

print("\n" + "=" * 68)
print("RAW fit: plateau + damped cosine vs plateau + exponential")
print("=" * 68)

def dampedcos_model(params, m):
    p, B, tau, omega, phi = params
    return p + B * np.exp(-m / tau) * np.cos(omega * m + phi)

def exp_model(params, m):
    p, B, tau = params
    return p + B * np.exp(-m / tau)

# RAW fit on lags 1..80 (exclude noisy edge lags 90-99)
fit_m = M[1:81]
fit_y = raw[1:81]

# Damped-cos initial guess
guess_dc = [0.1, 0.3, 40.0, 2*np.pi/40, 0.0]

def resid_dc(params):
    return dampedcos_model(params, fit_m) - fit_y

def resid_exp(params):
    return exp_model(params, fit_m) - fit_y

res_dc = least_squares(resid_dc, guess_dc,
                        bounds=([-0.1, 0, 5, 0, -np.pi],
                                [0.5, 0.9, 500, np.pi/4, np.pi]))
res_exp = least_squares(resid_exp, [0.15, 0.3, 40.0],
                         bounds=([-0.1, 0, 5], [0.5, 0.9, 500]))

print(f"\nFit window: lags 1..80 (80 points, T=4ks/lag)")

p_dc = res_dc.x
rmse_dc = float(np.sqrt(np.mean(res_dc.fun**2)))
tau_dc_s = p_dc[2] * T_CHUNK_S
omega_dc = p_dc[3]
period_dc_lag = 2*np.pi / omega_dc
period_dc_s = period_dc_lag * T_CHUNK_S
print(f"\nDamped cosine:")
print(f"  Φ(m) = {p_dc[0]:.3f} + {p_dc[1]:.3f}·exp(-m/{p_dc[2]:.1f})·cos({omega_dc:.4f}m + {p_dc[4]:.3f})")
print(f"    p_∞ = {p_dc[0]:.3f}")
print(f"    B   = {p_dc[1]:.3f}")
print(f"    τ   = {p_dc[2]:.1f} lags = {tau_dc_s:.0f}s = {tau_dc_s/1000:.0f} ks")
print(f"    ω   = {omega_dc:.4f} rad/lag  → period {period_dc_lag:.1f} lags = {period_dc_s/1000:.0f} ks")
print(f"    φ   = {p_dc[4]:.3f} rad")
print(f"    RMSE = {rmse_dc:.4f}")

p_exp = res_exp.x
rmse_exp = float(np.sqrt(np.mean(res_exp.fun**2)))
tau_exp_s = p_exp[2] * T_CHUNK_S
print(f"\nPure exponential (for comparison):")
print(f"  Φ(m) = {p_exp[0]:.3f} + {p_exp[1]:.3f}·exp(-m/{p_exp[2]:.1f})")
print(f"    p_∞ = {p_exp[0]:.3f}, τ = {p_exp[2]:.1f} lags = {tau_exp_s/1000:.0f} ks")
print(f"    RMSE = {rmse_exp:.4f}")

improvement = (rmse_exp - rmse_dc) / rmse_exp * 100
print(f"\nDamped cosine beats exp by: {improvement:+.1f}% RMSE reduction")

# Report RMSE by subwindow
print("\nRMSE by subwindow:")
print(f"{'window':>14} {'exp RMSE':>10} {'dcos RMSE':>11} {'%red':>6}")
for (lo, hi) in [(1, 30), (1, 50), (1, 80), (30, 80), (50, 80)]:
    mm = M[lo:hi+1]
    yy = raw[lo:hi+1]
    e_exp = exp_model(p_exp, mm) - yy
    e_dc = dampedcos_model(p_dc, mm) - yy
    rmse_e = np.sqrt(np.mean(e_exp**2))
    rmse_d = np.sqrt(np.mean(e_dc**2))
    red = (rmse_e - rmse_d) / rmse_e * 100
    print(f"  lags {lo:3d}..{hi:3d}   {rmse_e:.4f}      {rmse_d:.4f}     {red:+.1f}%")

# RAW complex-plane variance-decomp: real-part ACF vs imag-part ACF
print("\n" + "=" * 68)
print("Decomposition: real(Φ) vs imag(Φ)")
print("=" * 68)
for m in [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]:
    print(f"  m={m:3d}   Φ = {raw_cplx[m].real:+.3f} + {raw_cplx[m].imag:+.3f}i   |Φ|={raw[m]:.3f}  arg={raw_arg[m]:+.1f}°")

print("\n" + "=" * 68)
print("ST channel — is ST truly plateau-dominated?")
print("=" * 68)
# ST fit
st_fit_y = st[1:81]
res_st_dc = least_squares(resid_dc, [0.7, 0.05, 80.0, 0.02, 0.0],
                           bounds=([0, 0, 5, 0, -np.pi],
                                   [1.0, 0.3, 500, np.pi/4, np.pi]),
                           args=(), kwargs={})
# Need to redefine with st_fit_y
def resid_st_dc(params):
    return dampedcos_model(params, fit_m) - st_fit_y
def resid_st_exp(params):
    return exp_model(params, fit_m) - st_fit_y

res_st_dc = least_squares(resid_st_dc, [0.7, 0.05, 80.0, 0.02, 0.0],
                           bounds=([0, 0, 5, 0, -np.pi],
                                   [1.0, 0.3, 500, np.pi/4, np.pi]))
res_st_exp = least_squares(resid_st_exp, [0.7, 0.1, 80.0],
                            bounds=([0, 0, 5], [1.0, 0.5, 500]))
p_st_dc = res_st_dc.x
p_st_exp = res_st_exp.x
print(f"\nST damped-cos: p_∞={p_st_dc[0]:.3f} B={p_st_dc[1]:.3f} "
      f"τ={p_st_dc[2]*T_CHUNK_S/1000:.0f}ks  ω={p_st_dc[3]:.4f}rad/lag   "
      f"RMSE={np.sqrt(np.mean(res_st_dc.fun**2)):.4f}")
print(f"ST pure-exp:   p_∞={p_st_exp[0]:.3f} B={p_st_exp[1]:.3f} "
      f"τ={p_st_exp[2]*T_CHUNK_S/1000:.0f}ks   "
      f"RMSE={np.sqrt(np.mean(res_st_exp.fun**2)):.4f}")
print(f"ST pure-plateau RMSE (lags 1..80): "
      f"{np.sqrt(np.mean((st[1:81] - st[1:81].mean())**2)):.4f}")
print(f"ST mean over lags 1..80: {st[1:81].mean():.3f}")

# Save
out = {
    'source': 'Extended S98 A=0.30 σ=0.022 ω_spread=0.02, 8×100 chunks',
    'T_chunk_s': T_CHUNK_S,
    'raw_damped_cos': {
        'p_inf': float(p_dc[0]), 'B': float(p_dc[1]),
        'tau_lag': float(p_dc[2]), 'tau_s': float(tau_dc_s),
        'omega_rad_per_lag': float(omega_dc),
        'period_lag': float(period_dc_lag),
        'period_s': float(period_dc_s),
        'phi': float(p_dc[4]),
        'rmse_1_80': float(rmse_dc),
    },
    'raw_pure_exp': {
        'p_inf': float(p_exp[0]), 'B': float(p_exp[1]),
        'tau_lag': float(p_exp[2]), 'tau_s': float(tau_exp_s),
        'rmse_1_80': float(rmse_exp),
    },
    'raw_rmse_reduction_percent': float(improvement),
    'st_damped_cos': {
        'p_inf': float(p_st_dc[0]), 'B': float(p_st_dc[1]),
        'tau_lag': float(p_st_dc[2]),
        'tau_s': float(p_st_dc[2] * T_CHUNK_S),
        'omega_rad_per_lag': float(p_st_dc[3]),
        'period_s': float((2*np.pi/p_st_dc[3]) * T_CHUNK_S) if p_st_dc[3] > 0 else float('inf'),
        'phi': float(p_st_dc[4]),
        'rmse_1_80': float(np.sqrt(np.mean(res_st_dc.fun**2))),
    },
    'st_pure_exp': {
        'p_inf': float(p_st_exp[0]), 'B': float(p_st_exp[1]),
        'tau_lag': float(p_st_exp[2]),
        'rmse_1_80': float(np.sqrt(np.mean(res_st_exp.fun**2))),
    },
    'arg_linear_slope_rad_per_lag': float(slope) if len(mm) >= 3 else None,
    'raw_cplx_real': [float(z.real) for z in raw_cplx.tolist()],
    'raw_cplx_imag': [float(z.imag) for z in raw_cplx.tolist()],
    'st_cplx_real': [float(z.real) for z in st_cplx.tolist()],
    'st_cplx_imag': [float(z.imag) for z in st_cplx.tolist()],
}
with open('thor_session_103_s98_dampedcos_fit.json', 'w') as f:
    json.dump(out, f, indent=2)
print("\nSaved → thor_session_103_s98_dampedcos_fit.json")
