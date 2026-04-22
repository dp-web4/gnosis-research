#!/usr/bin/env python3
"""S110 smoke test: 2 seeds × 2 chunks at the ridge, verify pipeline works."""
import time
import numpy as np
import sys
sys.stdout.reconfigure(line_buffering=True)

from thor_session_110_signal_locked import (
    simulate_signal_locked, signal_phase_binned_lock,
    gate_conditional_lock, signal_phase_binned_switches,
    lock_modulation_at_fs, WARMUP, CHUNK_STEPS, DEC_KURA,
    SIGMA_NOISE, SIGNAL_FREQ, A_SIGNAL, DT, C_THRESHOLD,
)
from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

n_chunks = 2
total_steps = WARMUP + n_chunks * CHUNK_STEPS

t0 = time.time()
res = simulate_signal_locked(
    N=4, noise_std=SIGMA_NOISE, steps=total_steps, seed=110_99_8,
    kappa_phase=0.30, kappa_C=0.30,
    signal_freq=SIGNAL_FREQ, signal_amp=A_SIGNAL,
    omega_spread=0.24, dt=DT)
(Cm, kdec, gdec, Cdec, sdec, spdec, sw_steps, sw_dirs, k_mean) = res
print(f'sim: {time.time()-t0:.2f}s, total_steps={total_steps}')
print(f'kdec={len(kdec)} gdec={len(gdec)} sw_steps={len(sw_steps)}')
print(f'k_mean={k_mean:.3f} att_frac={gdec.mean():.3f}')

# detector outputs
xp = Cm[WARMUP:]
z_st = np.zeros(n_chunks, complex)
n_sw_chunk = np.zeros(n_chunks, int)
for c in range(n_chunks):
    chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
    t_off = WARMUP + c * CHUNK_STEPS
    Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ, t_offset=t_off, threshold=C_THRESHOLD)
    z_st[c] = Is + 1j*Qs
    n_sw_chunk[c] = n

print(f'z_st = {z_st}, |z_st|.mean = {np.abs(z_st).mean():.3f}')
print(f'n_sw per chunk = {n_sw_chunk.tolist()}, total = {n_sw_chunk.sum()}')
print(f'sw_steps from sim = {len(sw_steps)} (should ~match sum)')

# lock analysis
lp, cp, bc = signal_phase_binned_lock(kdec, spdec, n_bins=12)
print(f'lock_per_bin: {[f"{x:.3f}" for x in lp]}')
print(f'cnts: {cp.tolist()}')
gc = gate_conditional_lock(kdec, gdec)
print(f'gate cond: {gc}')
I, Q, mod, arg = lock_modulation_at_fs(kdec, spdec)
print(f'lock mod: I={I:.4f} Q={Q:.4f} amp={mod:.4f} arg={arg:.1f}°')

up_b, dn_b, _, all_b = signal_phase_binned_switches(sw_steps, sw_dirs, SIGNAL_FREQ, DT, n_bins=12)
print(f'switches per bin: {all_b.tolist()}')

# A=0 sanity: no signal-phase structure should emerge
print('\n--- A=0 sanity ---')
res0 = simulate_signal_locked(
    N=4, noise_std=SIGMA_NOISE, steps=total_steps, seed=110_99_9,
    kappa_phase=0.30, kappa_C=0.30,
    signal_freq=SIGNAL_FREQ, signal_amp=0.0,
    omega_spread=0.24, dt=DT)
(Cm0, kdec0, gdec0, _, _, spdec0, _, _, _) = res0
gc0 = gate_conditional_lock(kdec0, gdec0)
print(f'A=0 gate cond: {gc0}')
I0, Q0, mod0, _ = lock_modulation_at_fs(kdec0, spdec0)
print(f'A=0 lock mod amp: {mod0:.4f}')
