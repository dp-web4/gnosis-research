#!/usr/bin/env python3
"""Per-seed ACF analysis on S98 main data (ω_spread=0.02, A=0.30, σ=0.022,
8 seeds × 100 chunks).

Goal: Is the damped oscillation (T_osc ≈ 150 ks, |B|≈0.12, τ≈390ks) visible
per-seed, or does it only emerge from cross-seed pooling?

Per-seed has 8·99 = 792 pair-lag samples vs cross-seed 64·99 = wait:
per-seed has (100 − m) pairs at lag m in ONE seed = max 99 pairs at m=1.
Cross-seed pool has 8·(100 − m) = 792 max pairs at m=1.
So per-seed noise ~ 3× cross-seed.

We need to ask: (a) is each seed showing the same beat period? Would imply
a deterministic dynamical origin (collective mode). (b) Or does each seed
show a different beat period that averages out in the pooled magnitude?
"""
import json
import numpy as np
from scipy.optimize import least_squares

with open('thor_session_98_phase_drift_results.json') as f:
    s98 = json.load(f)

T_CHUNK_S = 4000.0


def per_seed_complex(records, key):
    out = []
    for s in records:
        out.append(np.array([complex(p[0], p[1]) for p in s[key]]))
    return out


def single_seed_acf(z, max_lag):
    phi = np.unwrap(np.angle(z))
    k = np.arange(len(phi))
    slope, _ = np.polyfit(k, phi, 1)
    resid = phi - slope * k - phi[0]
    u = np.exp(1j * resid)
    acf = np.zeros(max_lag + 1, dtype=complex)
    acf[0] = 1.0
    for m in range(1, max_lag + 1):
        if len(u) - m <= 0: continue
        acf[m] = np.mean(u[:-m] * np.conj(u[m:]))
    return acf


def fit_dcos(y_abs, max_lag):
    m = np.arange(1, max_lag + 1)
    y = np.array(y_abs[1:max_lag + 1])
    def dcos(p): return p[0] + p[1]*np.exp(-m/p[2])*np.cos(p[3]*m + p[4])
    best = None
    for om_init in np.linspace(0.05, 0.5, 15):
        for tau_init in [30, 80, 200]:
            try:
                r = least_squares(lambda p: dcos(p) - y,
                    [0.1, 0.3, tau_init, om_init, 0.0],
                    bounds=([-0.2, 0, 5, 0.001, -np.pi],
                            [0.8, 1.0, 2000, np.pi, np.pi]))
                ss = float(np.sum(r.fun**2))
                if best is None or ss < best['ss']:
                    best = {'params': r.x.tolist(), 'ss': ss,
                            'rmse': float(np.sqrt(ss/max_lag))}
            except Exception:
                pass
    return best

z_raws = per_seed_complex(s98['main']['per_seed'], 'z_raw')
z_sts = per_seed_complex(s98['main']['per_seed'], 'z_st')

print("Per-seed complex ACF fits (RAW, S98 main, ω_spread=0.02)")
print("=" * 72)
print(f"{'seed':>4} {'|<z>|':>10} {'σ_n':>10} {'|Φ(1)|':>8} {'|Φ(20)|':>8} {'|Φ(40)|':>8} {'|Φ(60)|':>8}")
seed_acfs = []
for i, z in enumerate(z_raws):
    mu = z.mean()
    sig = np.sqrt(np.mean(np.abs(z - mu)**2))
    acf = single_seed_acf(z, 80)
    seed_acfs.append(acf)
    print(f"{i:>4} {abs(mu):>10.4e} {sig:>10.4e}  "
          f"{abs(acf[1]):>7.3f}  {abs(acf[20]):>7.3f}  "
          f"{abs(acf[40]):>7.3f}  {abs(acf[60]):>7.3f}")

# Pool acf by taking |mean(complex ACF)| vs mean(|complex ACF|)
stacked = np.array(seed_acfs)
pooled_cplx = np.mean(stacked, axis=0)
pooled_abs_mean = np.mean(np.abs(stacked), axis=0)
print("\nComparison of pooling methods:")
print(f"{'lag':>5} {'|mean(Φ)|':>10} {'mean(|Φ|)':>10}   {'diff':>8}")
for m in [1, 10, 20, 30, 40, 50, 60, 70, 80]:
    a = abs(pooled_cplx[m])
    b = pooled_abs_mean[m]
    print(f"{m:>5} {a:>10.3f} {b:>10.3f}   {a-b:+.3f}")

# Per-seed damped-cos fit
print("\nPer-seed damped-cos fits (RAW):")
print(f"{'seed':>4} {'p_∞':>7} {'B':>7} {'τ_lag':>7} {'ω':>8} {'T_osc':>8} {'RMSE':>7}")
seed_fits = []
for i, acf in enumerate(seed_acfs):
    f = fit_dcos(np.abs(acf).tolist(), 80)
    seed_fits.append(f)
    if f:
        p = f['params']
        t_osc = 2*np.pi/p[3] if p[3] > 0 else float('inf')
        print(f"{i:>4} {p[0]:>7.3f} {p[1]:>7.3f} {p[2]:>7.1f} "
              f"{p[3]:>8.4f} {t_osc:>8.1f} {f['rmse']:>7.4f}")

# Aggregate the periods
periods = [2*np.pi/f['params'][3] for f in seed_fits if f]
omegas = [f['params'][3] for f in seed_fits if f]
print(f"\nPer-seed T_osc statistics (lags): mean={np.mean(periods):.1f} ± {np.std(periods):.1f}")
print(f"Per-seed ω statistics: mean={np.mean(omegas):.4f} ± {np.std(omegas):.4f} rad/lag")

# If each seed had DIFFERENT ω, the pooled |Φ| would decay faster than
# individual |Φ| (due to dephasing). If all seeds share the same ω, the
# pooled |Φ| would track individual |Φ| closely. Check this.
print("\n|Φ(m)| @ key lags — individual seeds vs pool:")
for m in [1, 20, 40, 60]:
    per_seed_abs = [abs(a[m]) for a in seed_acfs]
    print(f"  lag {m}: seeds range {min(per_seed_abs):.3f}–{max(per_seed_abs):.3f}  "
          f"mean_of_abs {np.mean(per_seed_abs):.3f}  "
          f"abs_of_mean_cplx {abs(pooled_cplx[m]):.3f}")

out = {
    'source': 'S98 main (ω_spread=0.02, A=0.30, σ=0.022), 8 seeds × 100 chunks',
    'T_chunk_s': T_CHUNK_S,
    'per_seed_fits_raw': [
        {'seed': i, 'params': f['params'] if f else None,
         'rmse': f['rmse'] if f else None,
         'T_osc_lag': float(2*np.pi/f['params'][3]) if (f and f['params'][3] > 0) else None}
        for i, f in enumerate(seed_fits)
    ],
    'per_seed_abs_acf_raw': [np.abs(a).tolist() for a in seed_acfs],
    'pooled_cplx_mean_abs': [float(abs(z)) for z in pooled_cplx.tolist()],
    'pooled_absmean': pooled_abs_mean.tolist(),
    'period_stats': {
        'mean_lag': float(np.mean(periods)),
        'std_lag': float(np.std(periods)),
        'mean_omega': float(np.mean(omegas)),
        'std_omega': float(np.std(omegas)),
    },
}
with open('thor_session_103_per_seed_s98.json', 'w') as f:
    json.dump(out, f, indent=2, default=float)
print("\nSaved → thor_session_103_per_seed_s98.json")
