#!/usr/bin/env python3
"""S107 smoke test — 2 seeds × 3 chunks, one cell from the planned grid.

Goal: confirm per-seed wall time and that R_coh numbers are in the
sane range vs. S106's kp030_kC030 reference (RAW=0.610, ST=0.795).
Use kp=0.30 kC=0.30 ω=0.24 (S106 peak) with reduced N_chunks=3 to
match S106 chunk structure while cutting total steps ~16×.
"""
import time
import numpy as np
import sys
sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_106_kappa_c_channel import simulate_with_kura

C_THR = 0.55; F = 0.003; A = 0.30; SIG = 0.022
DT = 0.1; WARM = 10_000; CHUNK = 40_000

for (kp, kC, omega) in [(0.30, 0.30, 0.24)]:
    print(f"\nSmoke cell: kp={kp} kC={kC} ω={omega}")
    for s in range(2):
        t0 = time.time()
        total_steps = WARM + 3 * CHUNK
        x, km, ks = simulate_with_kura(
            N=4, noise_std=SIG, steps=total_steps, seed=107_0 + s,
            kappa_phase=kp, kappa_C=kC,
            signal_freq=F, signal_amp=A,
            omega_spread=omega, dt=DT)
        xp = x[WARM:]
        zr = np.zeros(3, complex); zs = np.zeros(3, complex); nsw = 0
        for c in range(3):
            chunk = xp[c*CHUNK:(c+1)*CHUNK]
            t_off = WARM + c*CHUNK
            Ir, Qr = phase_coherent_IQ(chunk, DT, F, t_offset=t_off)
            Is, Qs, n = switch_timing_IQ(chunk, DT, F, t_offset=t_off, threshold=C_THR)
            zr[c] = Ir + 1j*Qr; zs[c] = Is + 1j*Qs; nsw += n
        dt_sec = time.time() - t0
        print(f"  seed={107_0+s}  {dt_sec:.2f}s  |<z_raw>|={abs(zr.mean()):.3e}  |<z_st>|={abs(zs.mean()):.3f}  kura={km:.3f}  N_sw={nsw//3}")
    # Extrapolate to 50-chunk full cell
    scale_factor = (WARM + 50 * CHUNK) / (WARM + 3 * CHUNK)
    est_seed = dt_sec * scale_factor
    print(f"  Est per-seed (50 chunks): {est_seed:.0f}s  ({est_seed/60:.2f} min)")
    print(f"  Est cell (8 seeds): {est_seed * 8 / 60:.1f} min")
