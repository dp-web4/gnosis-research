#!/usr/bin/env python3
"""S109 smoke test — 1 seed, 2 chunks, verify pipeline + phase trace work."""
import sys
import time
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_109_phase_spread import (
    simulate_with_phase_trace, phase_ensemble_stats,
)

WARMUP = 10_000
CHUNK_STEPS = 40_000
N_CHUNKS = 2

t0 = time.time()
x, kura_m, kura_s, phases = simulate_with_phase_trace(
    N=4, noise_std=0.022, steps=WARMUP + N_CHUNKS * CHUNK_STEPS,
    seed=9_030_30_2,
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

ps = phase_ensemble_stats(phases)
elapsed = time.time() - t0
print(f"elapsed={elapsed:.1f}s")
print(f"phase_samples shape = {phases.shape}")
print(f"R_kura_mean (stream, decimate=10) = {kura_m:.3f}±{kura_s:.3f}")
print(f"R_inst_mean (from trace, decimate=100) = {ps['R_kura_inst_mean']:.3f}")
print(f"sigma_phi_rad = {ps['sigma_phi_rad']:.3f}  (σ_φ = {ps['sigma_phi_deg']:.1f}°)")
print(f"sigma_cos_mean = {ps['sigma_cos_mean']:.3f}")
print(f"pairwise_dphi_mean (deg) = {np.degrees(ps['pairwise_dphi_mean']):.1f}")
print(f"pairwise_dphi_hist = {['%.3f'%h for h in ps['pairwise_dphi_hist']]}")
print(f"frac_locked_above_09 = {ps['frac_locked_above_09']:.3f}")
print(f"|z_raw|={np.abs(z_raw)}  |z_st|={np.abs(z_st)}")
print(f"steps/sec = {(WARMUP+N_CHUNKS*CHUNK_STEPS)/elapsed:.0f}")
print(f"est 8seeds*30chunks = {(WARMUP+30*CHUNK_STEPS)*8/(WARMUP+N_CHUNKS*CHUNK_STEPS)*elapsed/60:.1f} min")
