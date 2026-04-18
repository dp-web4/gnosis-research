#!/usr/bin/env python3
"""Smoke test for S98 autocorrelation code. Small trajectory to check
for bugs before the full 25-minute run."""

import numpy as np
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_98_phase_drift import (
    run_long_chunked, summarize_channel, autocorr_channel,
    fit_phase_diffusion, fit_rotation_rate,
)

dt = 0.1
signal_freq = 0.003
warmup = 10_000
T_CHUNK_S = 2000.0
chunk_steps = int(T_CHUNK_S / dt)  # 20_000

# Tiny: 3 seeds × 40 chunks × 2000s = 240,000s total compute
total_steps = warmup + 40 * chunk_steps   # 810,000 steps ≈ 20s

print(f"Smoke: warmup={warmup}, chunk_steps={chunk_steps}, "
      f"total_steps={total_steps}, n_chunks_expected=40")

t0 = datetime.now()
per_seed = run_long_chunked(
    sigma=0.022, A=0.30, n_seeds=3,
    total_steps=total_steps, warmup=warmup,
    chunk_steps=chunk_steps, dt=dt, signal_freq=signal_freq,
    seed_base=99_000,
)
print(f"sim done in {(datetime.now()-t0).total_seconds():.1f}s")

raw = summarize_channel('z_raw', per_seed, max_lag=20,
                        chunk_time_s=T_CHUNK_S)
st = summarize_channel('z_st', per_seed, max_lag=20,
                       chunk_time_s=T_CHUNK_S)

for summ in (raw, st):
    print(f"\n{summ['channel']}:")
    Phi = [complex(x[0], x[1]) for x in summ['Phi']]
    absPhi = [abs(p) for p in Phi]
    print(f"  |Φ(m)| lags 0..10: {[f'{v:.3f}' for v in absPhi[:11]]}")
    print(f"  var_dphi lags 0..10: {[f'{v:.3f}' for v in summ['var_dphi'][:11]]}")
    f = summ['phase_diffusion_fit']
    r = summ['rotation_rate_fit']
    print(f"  phase fit: {f}")
    print(f"  rot fit: {r}")
    angs = [s['mean_angle_deg'] for s in summ['per_seed_stats']]
    print(f"  per-seed mean angles: {[f'{a:+.1f}' for a in angs]}")

print("\nSmoke passed.")
