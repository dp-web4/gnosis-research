#!/usr/bin/env python3
"""S115 smoke: 1 seed × 5 chunks at one (κ_C, A) cell to validate plumbing."""
import sys
import time
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_111_dose_response import (
    per_seed_R_coh, lock_modulation_at_fs,
)
from thor_session_112_omega_cliff import build_omega, simulate_with_omega
from thor_session_113_dip_decomposition import per_switch_state, class_decompose

DT = 0.1
WARMUP = 10_000
CHUNK = 40_000
N_CHUNKS = 5
SEED = 115_999_000

t0 = time.time()
omega = build_omega(0.1, 0.07)
total = WARMUP + N_CHUNKS * CHUNK
print(f"smoke: kp=0.30 kC=0.15 ω_std=0.07 A=0.40 chunks={N_CHUNKS} steps={total}")
(Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
 sw_steps, sw_dirs, k_mean) = simulate_with_omega(
    N=4, noise_std=0.022, steps=total, seed=SEED, omega=omega,
    kappa_phase=0.30, kappa_C=0.15,
    signal_freq=0.003, signal_amp=0.40, dt=DT)
print(f"sim done in {time.time()-t0:.1f}s")
xp = Cm[WARMUP:]
z_st = np.zeros(N_CHUNKS, dtype=complex)
for c in range(N_CHUNKS):
    chunk = xp[c*CHUNK:(c+1)*CHUNK]
    Is, Qs, n = switch_timing_IQ(chunk, DT, 0.003, t_offset=WARMUP+c*CHUNK,
                                  threshold=0.55)
    z_st[c] = Is + 1j * Qs
print(f"|<z_st>|={abs(z_st.mean()):.3f}  arg={np.degrees(np.angle(z_st.mean())):+.1f}°")
print(f"R_kura={k_mean:.3f}  lock_frac={(kdec>0.9).mean():.3f}  Nsw={len(sw_steps)}")
mod_amp_lock = lock_modulation_at_fs(kdec, spdec)
print(f"mod_amp_at_fs_lock={mod_amp_lock[2]:.4f}")
kura_at_sw, gate_at_sw, lock_at_sw = per_switch_state(sw_steps, sw_dirs, kdec, gdec)
print(f"lock@sw={lock_at_sw.mean():.3f}  att@sw={gate_at_sw.mean():.3f}")
decomp = class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw)
for k, v in decomp['per_class'].items():
    print(f"  {k}: count={v['count']} |μ|={v['mu_abs']:.2f} arg={v['mu_arg_deg']:+.1f}°")
print(f"class_sum residual={decomp['class_sum_check']:.2e}")
