#!/usr/bin/env python3
"""Tiny-budget smoke for S101: verify imports, A=0 MF behavior,
ω_spread=0 works, and ACF fits don't crash."""

import numpy as np
import sys
sys.stdout.reconfigure(line_buffering=True)

from thor_session_101_intrinsic_wander import (
    run_long_chunked_omega,
    summarize_channel_null,
    print_summary_row,
    fit_tau_from_rho,
)

dt = 0.1
warmup = 10_000
T_chunk_s = 4000.0
chunk_steps = int(T_chunk_s / dt)
total_steps = warmup + 10 * chunk_steps  # 40,000s trajectory

for omega_spread in (0.0, 0.02):
    print(f"\n--- smoke: A=0, ω_spread={omega_spread} ---")
    ps = run_long_chunked_omega(
        sigma=0.022, A=0.0, n_seeds=2,
        total_steps=total_steps, warmup=warmup,
        chunk_steps=chunk_steps, omega_spread=omega_spread,
        dt=dt, signal_freq=0.003, seed_base=101_999)
    raw = summarize_channel_null('z_raw', ps, 5, T_chunk_s)
    st = summarize_channel_null('z_st', ps, 5, T_chunk_s)
    for s in (raw, st):
        print_summary_row(0.022, 0.0, omega_spread, s)

# Signal sanity: with A=0.30, |Φ(1)| should be high (≈0.7 at σ=0.022).
print("\n--- sanity: A=0.30, ω_spread=0.02 ---")
ps = run_long_chunked_omega(
    sigma=0.022, A=0.30, n_seeds=2,
    total_steps=total_steps, warmup=warmup,
    chunk_steps=chunk_steps, omega_spread=0.02,
    dt=dt, signal_freq=0.003, seed_base=101_998)
raw = summarize_channel_null('z_raw', ps, 5, T_chunk_s)
st = summarize_channel_null('z_st', ps, 5, T_chunk_s)
for s in (raw, st):
    print_summary_row(0.022, 0.30, 0.02, s)
print("\nSmoke OK.")
