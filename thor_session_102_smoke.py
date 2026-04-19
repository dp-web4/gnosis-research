#!/usr/bin/env python3
"""Smoke test for S102 — tiny run to verify code paths."""
import numpy as np
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

dt = 0.1
warmup = 10_000
T_CHUNK_S = 4000.0
chunk_steps = int(T_CHUNK_S / dt)

t0 = datetime.now()
x = simulate(N=4, noise_std=0.022, steps=warmup + 5 * chunk_steps,
             seed=102_100, signal_freq=0.003, signal_amp=0.20,
             omega_spread=0.02, dt=dt)
print(f"simulate took {(datetime.now()-t0).total_seconds():.1f}s for "
      f"{warmup + 5 * chunk_steps} steps")

xp = x[warmup:]
n_ch = len(xp) // chunk_steps
for c in range(n_ch):
    chunk = xp[c*chunk_steps:(c+1)*chunk_steps]
    t_off = warmup + c * chunk_steps
    Ir, Qr = phase_coherent_IQ(chunk, dt, 0.003, t_offset=t_off)
    Is, Qs, n = switch_timing_IQ(chunk, dt, 0.003, t_offset=t_off,
                                 threshold=0.55)
    print(f" chunk {c}: z_raw=({Ir:+.4f},{Qr:+.4f})  "
          f"z_st=({Is:+.3f},{Qs:+.3f})  n_sw={n}")
print("OK")
