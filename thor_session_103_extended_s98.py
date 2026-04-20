#!/usr/bin/env python3
"""Pre-S103 free analysis: extend S98's ACF analysis to full 99-lag window
for A=0.30, ω_spread=0.02, σ=0.022 (8 seeds × 100 chunks).

S102 fit lags 1..30 and got τ ≈ 83ks.  With 100 chunks we can fit out to
lag ~99 (≈ 396 ks), giving 5τ at the S102-reported τ ≈ 80ks. This will
either confirm S102's exponential or reveal another scale beyond it.
"""
import json
import numpy as np
from thor_session_103_omega_spread import (residual_phase_acf,
                                            fit_two_component,
                                            per_seed_from_json)

with open('thor_session_98_phase_drift_results.json') as f:
    s98 = json.load(f)

z_raws = per_seed_from_json(s98['main']['per_seed'], 'z_raw')
z_sts = per_seed_from_json(s98['main']['per_seed'], 'z_st')
print(f"Loaded {len(z_raws)} seeds × {len(z_raws[0])} chunks")

# Extended ACF
T_CHUNK_S = 4000.0
MAX_LAG = 99  # ~396ks lag window

raw_acf = residual_phase_acf(z_raws, MAX_LAG)
st_acf = residual_phase_acf(z_sts, MAX_LAG)

print("\nRAW |Φ(m)| at lags [1, 5, 10, 20, 30, 40, 60, 80, 99]:")
for m in [1, 5, 10, 20, 30, 40, 60, 80, 99]:
    print(f"  m={m:3d}  ({m*T_CHUNK_S/1000:5.0f} ks)  "
          f"{raw_acf['abs_acf'][m]:.3f}")

print("\nST |Φ(m)| at lags [1, 5, 10, 20, 30, 40, 60, 80, 99]:")
for m in [1, 5, 10, 20, 30, 40, 60, 80, 99]:
    print(f"  m={m:3d}  ({m*T_CHUNK_S/1000:5.0f} ks)  "
          f"{st_acf['abs_acf'][m]:.3f}")

# Two-component fits at various lag windows
print("\nRAW two-component fits at varying max_lag:")
print(f"{'max_lag':>8} {'p_inf':>7} {'B':>7} {'τ(s)':>10} {'RMSE':>7}")
for max_lag in [10, 20, 30, 50, 80, 99]:
    rt, _, _ = fit_two_component(raw_acf['abs_acf'], max_lag, T_CHUNK_S)
    print(f"{max_lag:>8d} {rt['p_inf']:>7.3f} {rt['B']:>7.3f} "
          f"{rt['tau_s']:>10.0f} {rt['rmse']:>7.4f}")

print("\nST two-component fits at varying max_lag:")
print(f"{'max_lag':>8} {'p_inf':>7} {'B':>7} {'τ(s)':>10} {'RMSE':>7}")
for max_lag in [10, 20, 30, 50, 80, 99]:
    st_, _, _ = fit_two_component(st_acf['abs_acf'], max_lag, T_CHUNK_S)
    print(f"{max_lag:>8d} {st_['p_inf']:>7.3f} {st_['B']:>7.3f} "
          f"{st_['tau_s']:>10.0f} {st_['rmse']:>7.4f}")

# Save extended ACF
out = {
    'source': 'S98 main, A=0.30, σ=0.022, ω_spread=0.02',
    'n_seeds': len(z_raws),
    'n_chunks': len(z_raws[0]),
    'T_chunk_s': T_CHUNK_S,
    'max_lag': MAX_LAG,
    'raw_abs_acf': raw_acf['abs_acf'],
    'st_abs_acf': st_acf['abs_acf'],
    'raw_arg_acf_deg': raw_acf['arg_acf_deg'],
    'st_arg_acf_deg': st_acf['arg_acf_deg'],
}
with open('thor_session_103_s98_extended.json', 'w') as f:
    json.dump(out, f, indent=2, default=float)
print("\nSaved → thor_session_103_s98_extended.json")
