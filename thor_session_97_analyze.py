#!/usr/bin/env python3
"""S97 analysis: compare ST vs ML Kramers vs 2f_s detectors on same trajectories."""
import json
import sys
import numpy as np
from scipy.stats import chi2, spearmanr

sys.stdout.reconfigure(line_buffering=True)

with open('thor_session_97_ml_kramers_results.json') as f:
    D = json.load(f)

amps = D['meta']['params']['amplitudes']
null_rows = D['results']['null']
N_NULL = len(null_rows)


def arr(rows, key):
    return np.array([r[key] for r in rows])


# ─── Null distributions ───
print("=" * 78)
print("NULL DISTRIBUTIONS (n = %d)" % N_NULL)
print("=" * 78)

lam_null = arr(null_rows, 'lam')
I_st_null = arr(null_rows, 'I_st')
Q_st_null = arr(null_rows, 'Q_st')
I_raw_null = arr(null_rows, 'I_raw')
Q_raw_null = arr(null_rows, 'Q_raw')
I_st2_null = arr(null_rows, 'I_st2')
Q_st2_null = arr(null_rows, 'Q_st2')

# T²_ST per-seed = (I² + Q²) / Var_null  (normalized by null variance)
var_I_null = I_st_null.var(ddof=1)
var_Q_null = Q_st_null.var(ddof=1)

def per_seed_T2(I_arr, Q_arr, vI, vQ):
    return I_arr**2 / vI + Q_arr**2 / vQ

T2_st_null = per_seed_T2(I_st_null, Q_st_null, var_I_null, var_Q_null)
T2_raw_null = per_seed_T2(I_raw_null, Q_raw_null,
                          I_raw_null.var(ddof=1), Q_raw_null.var(ddof=1))
T2_st2_null = per_seed_T2(I_st2_null, Q_st2_null,
                          I_st2_null.var(ddof=1), Q_st2_null.var(ddof=1))

print(f"\nΛ_ML:        mean={lam_null.mean():6.2f}  med={np.median(lam_null):6.2f}  "
      f"95%={np.percentile(lam_null, 95):6.2f}  max={lam_null.max():6.2f}")
print(f"T²_ST:       mean={T2_st_null.mean():6.2f}  med={np.median(T2_st_null):6.2f}  "
      f"95%={np.percentile(T2_st_null, 95):6.2f}  max={T2_st_null.max():6.2f}")
print(f"T²_raw:      mean={T2_raw_null.mean():6.2f}  med={np.median(T2_raw_null):6.2f}  "
      f"95%={np.percentile(T2_raw_null, 95):6.2f}  max={T2_raw_null.max():6.2f}")
print(f"T²_2f_s:     mean={T2_st2_null.mean():6.2f}  med={np.median(T2_st2_null):6.2f}  "
      f"95%={np.percentile(T2_st2_null, 95):6.2f}  max={T2_st2_null.max():6.2f}")
print(f"\nχ²(2) theoretical: mean=2.00, 95%={chi2.ppf(0.95, 2):.2f}")

# Empirical thresholds
thr_lam_95 = np.percentile(lam_null, 95)
thr_st_95 = np.percentile(T2_st_null, 95)
thr_raw_95 = np.percentile(T2_raw_null, 95)
thr_st2_95 = np.percentile(T2_st2_null, 95)

print(f"\nEmpirical 95% thresholds (single-seed detection):")
print(f"  Λ_ML : {thr_lam_95:6.2f}")
print(f"  T²_ST: {thr_st_95:6.2f}   (χ² 5.99)")
print(f"  T²_raw:{thr_raw_95:6.2f}   (χ² 5.99)")
print(f"  T²_2f:{thr_st2_95:6.2f}    (χ² 5.99)")

# ─── Detection power per A ───
print("\n" + "=" * 78)
print("DETECTION POWER (fraction of signal seeds exceeding null 95%)")
print("=" * 78)
print(f"{'A':>6} {'ΛML_mean':>10} {'P(ΛML>)':>9} {'T²st_mean':>10} "
      f"{'P(T²st>)':>9} {'T²2f_mean':>10} {'P(T²2f>)':>9} "
      f"{'k̂_mean':>8}")

det_table = []
for A in amps:
    key = f"A={A}"
    rw = D['results'][key]['with']
    lam_w = arr(rw, 'lam')
    I_st_w = arr(rw, 'I_st')
    Q_st_w = arr(rw, 'Q_st')
    I_raw_w = arr(rw, 'I_raw')
    Q_raw_w = arr(rw, 'Q_raw')
    I_st2_w = arr(rw, 'I_st2')
    Q_st2_w = arr(rw, 'Q_st2')
    k_hat_w = arr(rw, 'k_hat')

    T2_st_w = per_seed_T2(I_st_w, Q_st_w, var_I_null, var_Q_null)
    T2_raw_w = per_seed_T2(I_raw_w, Q_raw_w,
                           I_raw_null.var(ddof=1), Q_raw_null.var(ddof=1))
    T2_st2_w = per_seed_T2(I_st2_w, Q_st2_w,
                           I_st2_null.var(ddof=1), Q_st2_null.var(ddof=1))

    p_lam = np.mean(lam_w > thr_lam_95)
    p_st = np.mean(T2_st_w > thr_st_95)
    p_st2 = np.mean(T2_st2_w > thr_st2_95)

    print(f"{A:6.3f} {lam_w.mean():10.2f} {p_lam:9.2%} "
          f"{T2_st_w.mean():10.2f} {p_st:9.2%} "
          f"{T2_st2_w.mean():10.2f} {p_st2:9.2%} "
          f"{np.abs(k_hat_w).mean():+8.3f}")
    det_table.append({
        'A': A,
        'lam_mean': float(lam_w.mean()),
        'lam_p_detect': float(p_lam),
        'T2_st_mean': float(T2_st_w.mean()),
        'T2_st_p_detect': float(p_st),
        'T2_st2_mean': float(T2_st2_w.mean()),
        'T2_st2_p_detect': float(p_st2),
        'abs_k_hat_mean': float(np.abs(k_hat_w).mean()),
        'k_hat_std': float(k_hat_w.std(ddof=1)),
    })


# ─── Aggregate z-scores (cross-seed test) ───
print("\n" + "=" * 78)
print("CROSS-SEED Z-TEST (signed differences, ST-style aggregation)")
print("=" * 78)
print(f"{'A':>6} {'z_I_st':>8} {'z_Q_st':>8} {'T²_ST':>8} "
      f"{'z_I_2f':>8} {'z_Q_2f':>8} {'T²_2f':>8} "
      f"{'z_Λ':>8}")

agg_table = []
for A in amps:
    key = f"A={A}"
    rw = D['results'][key]['with']

    def z2diff(w_arr, wo_arr):
        m = w_arr.mean() - wo_arr.mean()
        se = np.sqrt(w_arr.var(ddof=1)/len(w_arr) + wo_arr.var(ddof=1)/len(wo_arr))
        return float(m/se) if se > 0 else 0.0

    z_I_st = z2diff(arr(rw, 'I_st'), I_st_null)
    z_Q_st = z2diff(arr(rw, 'Q_st'), Q_st_null)
    T2_ST_cross = z_I_st**2 + z_Q_st**2

    z_I_2f = z2diff(arr(rw, 'I_st2'), I_st2_null)
    z_Q_2f = z2diff(arr(rw, 'Q_st2'), Q_st2_null)
    T2_2f_cross = z_I_2f**2 + z_Q_2f**2

    z_lam = z2diff(arr(rw, 'lam'), lam_null)

    print(f"{A:6.3f} {z_I_st:+8.2f} {z_Q_st:+8.2f} {T2_ST_cross:8.2f} "
          f"{z_I_2f:+8.2f} {z_Q_2f:+8.2f} {T2_2f_cross:8.2f} "
          f"{z_lam:+8.2f}")

    agg_table.append({
        'A': A,
        'z_I_st': z_I_st, 'z_Q_st': z_Q_st, 'T2_ST': T2_ST_cross,
        'z_I_2f': z_I_2f, 'z_Q_2f': z_Q_2f, 'T2_2f': T2_2f_cross,
        'z_lam': z_lam,
    })


# ─── Correlation: is Λ_ML just ST + noise? ───
print("\n" + "=" * 78)
print("ORTHOGONALITY CHECK: ρ(Λ_ML, T²_ST) per A")
print("=" * 78)
for A in amps:
    key = f"A={A}"
    rw = D['results'][key]['with']
    lam_w = arr(rw, 'lam')
    T2_w = per_seed_T2(arr(rw, 'I_st'), arr(rw, 'Q_st'),
                       var_I_null, var_Q_null)
    T2_2f_w = per_seed_T2(arr(rw, 'I_st2'), arr(rw, 'Q_st2'),
                          I_st2_null.var(ddof=1), Q_st2_null.var(ddof=1))
    rho_lam_st, _ = spearmanr(lam_w, T2_w)
    rho_2f_st, _ = spearmanr(T2_2f_w, T2_w)
    print(f"  A={A:.2f}  ρ(Λ, T²_ST) = {rho_lam_st:+.3f}   "
          f"ρ(T²_2f, T²_ST) = {rho_2f_st:+.3f}")


# ─── k̂ scaling: does k̂ ∝ A? ───
print("\n" + "=" * 78)
print("MLE k̂ SCALING (Kramers predicts k̂ ∝ A)")
print("=" * 78)
abs_k = []
for A in amps:
    rw = D['results'][f"A={A}"]['with']
    k_w = arr(rw, 'k_hat')
    # Mean |k| is a natural scale-invariant measure (sign ambiguity k↔-k, φ↔φ+π)
    abs_k.append(np.abs(k_w).mean())
print("  A       ⟨|k̂|⟩   expected ∝ A?")
for A, mk in zip(amps, abs_k):
    print(f"  {A:5.3f}   {mk:6.4f}")

# Linear fit of |k| vs A (excluding A=0)
amps_pos = np.array([a for a in amps if a > 0])
abs_k_pos = np.array(abs_k[1:])
if len(amps_pos) >= 2:
    slope, intercept = np.polyfit(amps_pos, abs_k_pos, 1)
    print(f"\n  Linear fit (A>0): |k̂| = {slope:.3f} * A + {intercept:+.3f}")
    # Also log-log
    log_A = np.log(amps_pos)
    log_k = np.log(np.maximum(abs_k_pos, 1e-4))
    alpha_k, _ = np.polyfit(log_A, log_k, 1)
    print(f"  Log-log slope α (|k̂|~A^α): {alpha_k:.3f}")


# Save analysis table
with open('thor_session_97_analysis.json', 'w') as f:
    json.dump({
        'null_thresholds': {
            'lam_95': float(thr_lam_95),
            'T2_st_95': float(thr_st_95),
            'T2_raw_95': float(thr_raw_95),
            'T2_st2_95': float(thr_st2_95),
        },
        'null_stats': {
            'lam_mean': float(lam_null.mean()),
            'lam_median': float(np.median(lam_null)),
            'lam_max': float(lam_null.max()),
            'T2_st_mean': float(T2_st_null.mean()),
            'T2_st_95': float(np.percentile(T2_st_null, 95)),
        },
        'detection_per_seed': det_table,
        'aggregate_z': agg_table,
    }, f, indent=2)

print("\n\nSaved thor_session_97_analysis.json")
