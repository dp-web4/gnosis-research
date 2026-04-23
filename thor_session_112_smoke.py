#!/usr/bin/env python3
"""S112 smoke: 1 seed, 2 chunks, two ω_std levels to verify the plumbing."""
import numpy as np
import time, sys
sys.stdout.reconfigure(line_buffering=True)

from thor_session_112_omega_cliff import (
    simulate_with_omega, build_omega, WARMUP, CHUNK_STEPS, DT, SIGNAL_FREQ,
    SIGMA_NOISE, C_THRESHOLD, DEC_KURA
)
from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

N_CHUNKS = 2
total_steps = WARMUP + N_CHUNKS * CHUNK_STEPS

for om_std in [0.03, 0.23]:
    omega = build_omega(0.1, om_std)
    print(f"\nω_std={om_std}, ω={np.round(omega,3).tolist()} std_check={omega.std():.4f}")
    t0 = time.time()
    (Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
     sw_steps, sw_dirs, k_mean) = simulate_with_omega(
        N=4, noise_std=SIGMA_NOISE, steps=total_steps,
        seed=112_000_001, omega=omega,
        kappa_phase=0.30, kappa_C=0.30,
        signal_freq=SIGNAL_FREQ, signal_amp=0.50, dt=DT)
    xp = Cm[WARMUP:]
    z_raw_I, z_raw_Q = phase_coherent_IQ(xp, DT, SIGNAL_FREQ, t_offset=WARMUP)
    z_st_I, z_st_Q, n_sw = switch_timing_IQ(xp, DT, SIGNAL_FREQ, t_offset=WARMUP,
                                             threshold=C_THRESHOLD)
    lock_frac = float((kdec > 0.9).mean())
    print(f"  {time.time()-t0:.1f}s  R_kura={k_mean:.3f}  lock_frac={lock_frac:.3f}  "
          f"|z_st|={np.sqrt(z_st_I**2+z_st_Q**2):.2f}  Nsw_per_chunk={len(sw_steps)/N_CHUNKS:.0f}")
