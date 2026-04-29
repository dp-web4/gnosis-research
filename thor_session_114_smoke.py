#!/usr/bin/env python3
"""S114 smoke: 1 cell of low-κp setup, 2 seeds, 4 chunks, time it.

Validates simulator timing at κ_p=0.10 / ω_std=0.0233 (matched ratio
to S113 baseline) and confirms switch-rate is sane before committing
to the full sweep.
"""
import time
import numpy as np

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_111_dose_response import (
    per_seed_R_coh, lock_modulation_at_fs,
)
from thor_session_112_omega_cliff import build_omega, simulate_with_omega
from thor_session_113_dip_decomposition import (
    per_switch_state, class_decompose,
)

C_THRESHOLD = 0.55
SIGNAL_FREQ = 0.003
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
N_SEEDS = 2
N_CHUNKS = 4

KAPPA_PHASE = 0.10
KAPPA_C = 0.30
OMEGA_STD = 0.0233       # ratio = ω_std / κ_p = 0.233 (S113 match)
SIGNAL_AMP = 0.13        # near predicted dip-A for κ_p=0.10

omega_vec = build_omega(0.1, OMEGA_STD)
total_steps = WARMUP + N_CHUNKS * CHUNK_STEPS
print(f"S114 smoke: κ_p={KAPPA_PHASE}  κ_C={KAPPA_C}  ω_std={OMEGA_STD}")
print(f"  ω={omega_vec.tolist()}  A={SIGNAL_AMP}  steps={total_steps}")

start = time.time()
for s in range(N_SEEDS):
    t0 = time.time()
    (Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
     sw_steps, sw_dirs, k_mean) = simulate_with_omega(
        N=4, noise_std=SIGMA_NOISE, steps=total_steps,
        seed=114_900_000 + s, omega=omega_vec,
        kappa_phase=KAPPA_PHASE, kappa_C=KAPPA_C,
        signal_freq=SIGNAL_FREQ, signal_amp=SIGNAL_AMP, dt=DT)
    xp = Cm[WARMUP:]
    z_st = np.zeros(N_CHUNKS, dtype=complex)
    for c in range(N_CHUNKS):
        chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
        t_off = WARMUP + c * CHUNK_STEPS
        Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ,
                                      t_offset=t_off, threshold=C_THRESHOLD)
        z_st[c] = Is + 1j * Qs
    st = per_seed_R_coh(z_st)
    kura_at_sw, gate_at_sw, lock_at_sw = per_switch_state(
        sw_steps, sw_dirs, kdec, gdec)
    decomp = class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw)
    cls = decomp['per_class']
    el = time.time() - t0
    print(f"  seed={s} elapsed={el:.1f}s  R_kura={k_mean:.3f}  "
          f"|μ_st|={st['mu_abs']:.2f}  arg={st['mu_arg_deg']:+6.1f}°  "
          f"R_coh={st['R_coh']:.3f}  Nsw={len(sw_steps)}  "
          f"lock@sw={lock_at_sw.mean():.2f}  att@sw={gate_at_sw.mean():.2f}")
    print(f"    |μ_class| aL={cls['att_lock']['mu_abs']:.1f} "
          f"aN={cls['att_noise']['mu_abs']:.1f} "
          f"rL={cls['rep_lock']['mu_abs']:.1f} "
          f"rN={cls['rep_noise']['mu_abs']:.1f}")
    print(f"    arg(μ_class) aL={cls['att_lock']['mu_arg_deg']:+6.1f}° "
          f"aN={cls['att_noise']['mu_arg_deg']:+6.1f}° "
          f"rL={cls['rep_lock']['mu_arg_deg']:+6.1f}° "
          f"rN={cls['rep_noise']['mu_arg_deg']:+6.1f}°")
total = time.time() - start
per_seed = total / N_SEEDS
print(f"\nTotal {total:.1f}s  per_seed {per_seed:.1f}s")
# Extrapolate to 12-cell × 16-seed × 25-chunk full run
sim_steps = WARMUP + 25 * CHUNK_STEPS
factor = sim_steps / total_steps
full_per_seed = per_seed * factor
full_total_min = (12 * 16 * full_per_seed) / 60
print(f"Extrapolated full-run (12 cells × 16 seeds × 25 chunks): "
      f"{full_total_min:.1f} min")
