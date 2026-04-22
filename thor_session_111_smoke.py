#!/usr/bin/env python3
"""Smoke test for S111: 1 cell × 1 seed × 2 chunks."""
import sys
import time
sys.stdout.reconfigure(line_buffering=True)
import numpy as np

from thor_session_111_dose_response import (
    simulate_dose_response, per_seed_R_coh,
    signal_phase_binned_lock, gate_conditional_lock,
    signal_phase_binned_switches, lock_modulation_at_fs,
    kura_modulation_at_fs, first_principles_z_st,
    WARMUP, CHUNK_STEPS, DT, SIGMA_NOISE, SIGNAL_FREQ, C_THRESHOLD,
)
from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

t0 = time.time()
n_chunks = 2
total = WARMUP + n_chunks * CHUNK_STEPS
(Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
 sw_steps, sw_dirs, k_mean) = simulate_dose_response(
    N=4, noise_std=SIGMA_NOISE, steps=total,
    seed=11130800,
    kappa_phase=0.30, kappa_C=0.30,
    signal_freq=SIGNAL_FREQ, signal_amp=0.30,
    omega_spread=0.24, dt=DT)

print(f"Sim {time.time()-t0:.1f}s")
print(f"  C_mean_hist len {len(Cm)}  expected {total}")
print(f"  kura_dec len {len(kdec)}  expected ~{n_chunks*CHUNK_STEPS//10}")
print(f"  mean_phase_dec len {len(mphdec)}  range [{mphdec.min():.2f}, {mphdec.max():.2f}] rad")
print(f"  gate_dec sum {gdec.sum()} of {len(gdec)}")
print(f"  switch_steps {len(sw_steps)} events")
print(f"  R_kura mean {k_mean:.3f}")

xp = Cm[WARMUP:]
z_st_chunks = []
n_sw_chunks = []
for c in range(n_chunks):
    chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
    t_off = WARMUP + c * CHUNK_STEPS
    Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ, t_offset=t_off,
                                   threshold=C_THRESHOLD)
    z_st_chunks.append(Is + 1j*Qs)
    n_sw_chunks.append(n)
z_st_arr = np.array(z_st_chunks)
print(f"  per-chunk z_st: |⟨z⟩|={abs(z_st_arr.mean()):.3f}  N_sw_per={n_sw_chunks}")
sum_meas = abs(z_st_arr.sum())
Ip, Qp, fp = first_principles_z_st(sw_steps, sw_dirs, SIGNAL_FREQ, DT)
print(f"  fp_z_total={fp:.3f}  meas_z_total={sum_meas:.3f}  ratio={fp/sum_meas:.4f}")

lpb, cpb, bc = signal_phase_binned_lock(kdec, spdec)
print(f"  lock_per_bin: min={lpb.min():.3f} max={lpb.max():.3f} mean={lpb.mean():.3f}")

gc = gate_conditional_lock(kdec, gdec)
print(f"  P(L|att)={gc['P_lock_given_attractive']:.3f}  P(L|rep)={gc['P_lock_given_repulsive']:.3f}")

I, Q, m, ag = lock_modulation_at_fs(kdec, spdec)
print(f"  mod_amp_lock={m:.4f} arg={ag:.1f}°")
I, Q, m, ag = kura_modulation_at_fs(kdec, spdec)
print(f"  mod_amp_kura={m:.5f} arg={ag:.1f}°")

import numpy as np_
cphi = np_.cos(mphdec)
cphi_dm = cphi - cphi.mean()
I_cp = float(np_.mean(cphi_dm * np_.sin(spdec)))
Q_cp = float(np_.mean(cphi_dm * np_.cos(spdec)))
print(f"  mod_amp_cosphi={(I_cp**2+Q_cp**2)**0.5:.4f}")

print(f"\nSmoke OK in {time.time()-t0:.1f}s")
