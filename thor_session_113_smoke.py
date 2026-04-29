#!/usr/bin/env python3
"""Smoke test for S113: short steps, 2 seeds, verify class-decomposition arithmetic
matches first-principles z_total to floating-point precision.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)
import numpy as np

from thor_session_111_dose_response import first_principles_z_st
from thor_session_112_omega_cliff import build_omega, simulate_with_omega
from thor_session_113_dip_decomposition import (
    per_switch_state, class_decompose,
    SIGMA_NOISE, SIGNAL_FREQ, DT, WARMUP, DEC_KURA,
)

# Tiny: 2 seeds, 2 chunks of 40k = 90k steps total
omega_vec = build_omega(0.1, 0.07)
total_steps = WARMUP + 2 * 40_000
print(f"smoke: ω={omega_vec}, total_steps={total_steps}")

for s in range(2):
    (Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
     sw_steps, sw_dirs, k_mean) = simulate_with_omega(
        N=4, noise_std=SIGMA_NOISE, steps=total_steps,
        seed=113_999_000 + s, omega=omega_vec,
        kappa_phase=0.30, kappa_C=0.30,
        signal_freq=SIGNAL_FREQ, signal_amp=0.30, dt=DT)
    Ip, Qp, fp_z_total = first_principles_z_st(
        sw_steps, sw_dirs, SIGNAL_FREQ, DT)
    fp_complex = complex(Ip, Qp)
    kura_at_sw, gate_at_sw, lock_at_sw = per_switch_state(
        sw_steps, sw_dirs, kdec, gdec)
    decomp = class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw)
    z_class_total = complex(decomp['z_total_re'], decomp['z_total_im'])
    diff = abs(z_class_total - fp_complex)
    cls = decomp['per_class']
    print(f"\nseed {s}: Nsw={len(sw_steps)}  R_kura={k_mean:.3f}  "
          f"|fp|={abs(fp_complex):.3f}  |class_sum|={abs(z_class_total):.3f}  "
          f"diff={diff:.2e}  (must be < 1e-9)")
    print(f"  classes: aL={cls['att_lock']['count']} aN={cls['att_noise']['count']} "
          f"rL={cls['rep_lock']['count']} rN={cls['rep_noise']['count']}  "
          f"sum={sum(cls[k]['count'] for k in cls)}  Nsw={len(sw_steps)}")
    print(f"  |μ|² check: |z|²={decomp['z_total_abs2']:.4f}  "
          f"sum_sq+cross={decomp['sum_class_sq']+decomp['cross_total']:.4f}  "
          f"residual={decomp['class_sum_check']:.2e}")
    print(f"  lock@sw frac={float(lock_at_sw.mean()) if len(sw_steps)>0 else 0:.3f}, "
          f"att@sw={float(gate_at_sw.mean()) if len(sw_steps)>0 else 0:.3f}")

print("\n✓ smoke OK if both diff < 1e-9 and class counts sum to Nsw.")
