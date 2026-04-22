#!/usr/bin/env python3
"""S108 smoke test — 1 seed, 2 chunks, verify pipeline works before full run."""
import sys
import time
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_106_kappa_c_channel import simulate_with_kura

WARMUP = 10_000
CHUNK_STEPS = 40_000
N_CHUNKS = 2

t0 = time.time()
x, kura_m, kura_s = simulate_with_kura(
    N=4, noise_std=0.022, steps=WARMUP + N_CHUNKS * CHUNK_STEPS,
    seed=108_030_030,
    kappa_phase=0.30, kappa_C=0.30,
    signal_freq=0.003, signal_amp=0.30,
    omega_spread=0.06, dt=0.1)
xp = x[WARMUP:]

z_raw = np.zeros(N_CHUNKS, dtype=complex)
z_st = np.zeros(N_CHUNKS, dtype=complex)
for c in range(N_CHUNKS):
    chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
    t_off = WARMUP + c * CHUNK_STEPS
    Ir, Qr = phase_coherent_IQ(chunk, 0.1, 0.003, t_offset=t_off)
    Is, Qs, n = switch_timing_IQ(chunk, 0.1, 0.003, t_offset=t_off, threshold=0.55)
    z_raw[c] = Ir + 1j*Qr
    z_st[c]  = Is + 1j*Qs

elapsed = time.time() - t0
print(f"elapsed={elapsed:.1f}s  R_kura={kura_m:.3f}±{kura_s:.3f}")
print(f"|z_raw|={np.abs(z_raw)}  |z_st|={np.abs(z_st)}")
print(f"steps/sec = {(WARMUP+N_CHUNKS*CHUNK_STEPS)/elapsed:.0f}")
print(f"est 8seeds*50chunks = {(WARMUP+50*CHUNK_STEPS)*8/(WARMUP+N_CHUNKS*CHUNK_STEPS)*elapsed/60:.1f} min")
