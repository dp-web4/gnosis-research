#!/usr/bin/env python3
"""Thor Session #108: Ridge Universality — Does κ_C* ≈ 0.27 Hold at Ratio 0.2?

Context (S107, S107-P3)
-----------------------
S107 mapped the 2D (κ_phase, κ_C) ridge at ratio ω/κ_phase = 0.80 (near-desync)
and found peak κ_C* = 0.256, 0.274, 0.277 across κ_phase ∈ {0.15, 0.30, 0.50}
— essentially flat at ≈0.27 across a 3× κ_phase range. Peak R rises ~linearly
with κ_phase (+1.02 on the ridge).

Open: **does the ridge location shift with ω/κ_phase ratio?** Ratio 0.80 is
close to the Kuramoto desync cliff (Δ_c/κ = π/4 ≈ 0.785). Ratio 0.20 is
*deep* in the coherent regime where phase oscillators spontaneously lock
(Kuramoto R_kura ≈ 1).

Design
------
Single vertical slice at κ_phase = 0.30, ω_spread = 0.06 (ratio 0.20), with
the same κ_C grid used in S106/S107:

  κ_C ∈ {0.00, 0.05, 0.15, 0.30, 0.50}

Recycle: S105 r02_k030 = (κ_p=0.30, κ_C=0.15, ratio 0.20) — already 8 seeds ×
50 chunks with identical protocol. R_raw=0.495, R_st=0.779.

NEW cells (4):
  kp030_kC000_r02  (κ_C=0.00)
  kp030_kC005_r02  (κ_C=0.05)
  kp030_kC030_r02  (κ_C=0.30)
  kp030_kC050_r02  (κ_C=0.50)

Each: 8 seeds × 50 chunks × 40k steps + 10k warmup = 16M steps.
~6.7 min/cell × 4 = ~27 min.

Observables: per-seed R_coh (RAW/ST), cross-seed R_angle, R_kura, N_sw.

Predictions
-----------
**A (universal ridge):** peak κ_C* ≈ 0.27 at ratio 0.2, within ±0.03 of the
    ratio-0.8 peak. The rate-vs-precision balance that sets the ridge is a
    C-dynamics property, independent of phase-lock regime.

**B (leftward shift):** peak κ_C* < 0.20. Deep phase locking already
    homogenizes the array; less C-coupling force is needed to reach the
    precision optimum. Predicts κ_C* ≈ 0.10–0.15 and a sharper ridge (phases
    already coherent means C-coupling has more leverage per unit).

**C (rightward shift):** peak κ_C* > 0.35. Phase locking removes phase-dof
    randomness that was "helping" switch-timing scatter; more κ_C force
    needed to drive the same rate-vs-precision tradeoff.

**D (no ridge, ceiling regime):** ST R_coh already ≈0.78 at κ_C=0.15 (S105)
    — may be ceiling-limited. RAW has more headroom (0.495 at κ_C=0.15)
    and should show the ridge more cleanly.

My prior: B is most likely. Deep-locked phases should need less κ_C. But
A is a real possibility if the κ_C mechanism is purely about C-dynamics
rate (signal-phase alignment) and not about phase-coupling synergy.

Analysis
--------
Post-run analyzer fits quadratic R(κ_C) per detector and reports κ_C* peak.
Compare directly against S106 κ_p=0.30 ratio-0.8 slice (peak κ_C* = 0.274,
R_peak = 0.610 RAW, 0.795 ST).

Also compute:
  - N_sw(κ_C) curves — same shape as ratio 0.8?
  - σ_n_ST cross-cell variance (S107-P5 probe) — also ~flat at ratio 0.2?
  - R_kura per cell — how close to 1.0 at ratio 0.2?
"""
import json
import sys
import time
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_106_kappa_c_channel import (
    simulate_with_kura, per_seed_R_coh, cross_seed_angle_R,
    summarize_cell, pack_per_seed,
)

C_THRESHOLD = 0.55
SIGNAL_FREQ = 0.003
A_SIGNAL = 0.30
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
T_CHUNK_S = CHUNK_STEPS * DT
N_SEEDS = 8
N_CHUNKS = 50
KURA_DECIMATE = 10


def run_cell(kappa_phase, kappa_C, omega_spread, seed_base,
             n_chunks=N_CHUNKS, n_seeds=N_SEEDS):
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> κ_p={kappa_phase:.3f}  κ_C={kappa_C:.3f}  "
          f"ω_spread={omega_spread:.4f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  "
          f"steps={total_steps}  seed_base={seed_base}")
    per_seed = []
    cell_start = time.time()
    for s in range(n_seeds):
        t0 = time.time()
        x, kura_mean, kura_std = simulate_with_kura(
            N=4, noise_std=SIGMA_NOISE, steps=total_steps,
            seed=seed_base + s,
            kappa_phase=kappa_phase, kappa_C=kappa_C,
            signal_freq=SIGNAL_FREQ, signal_amp=A_SIGNAL,
            omega_spread=omega_spread, dt=DT)
        xp = x[WARMUP:]
        z_raw = np.zeros(n_chunks, dtype=complex)
        z_st = np.zeros(n_chunks, dtype=complex)
        n_sw = np.zeros(n_chunks, dtype=int)
        for c in range(n_chunks):
            chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
            t_off = WARMUP + c * CHUNK_STEPS
            Ir, Qr = phase_coherent_IQ(chunk, DT, SIGNAL_FREQ, t_offset=t_off)
            Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ,
                                          t_offset=t_off,
                                          threshold=C_THRESHOLD)
            z_raw[c] = Ir + 1j * Qr
            z_st[c] = Is + 1j * Qs
            n_sw[c] = n
        per_seed.append({
            'seed': seed_base + s,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw': n_sw,
            'kura_mean': kura_mean, 'kura_std': kura_std,
        })
        elapsed = time.time() - t0
        print(f"   seed={seed_base+s:7d}  {elapsed:5.1f}s   "
              f"|<z_raw>|={abs(z_raw.mean()):.3e}   "
              f"|<z_st>|={abs(z_st.mean()):.3f}   "
              f"<R_kura>={kura_mean:.3f} ± {kura_std:.3f}   "
              f"N_sw/chunk={n_sw.mean():.0f}")
    print(f"   total {time.time()-cell_start:.0f}s")
    return per_seed


def main():
    start = datetime.now()
    print("Thor Session #108: Ridge Universality at Ratio 0.2 (S107-P3)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: A={A_SIGNAL}  σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks × {CHUNK_STEPS} steps")
    print(f"Slice: κ_p=0.30, ω=0.06 (ratio 0.2), κ_C ∈ {{0.00, 0.05, 0.30, 0.50}}")
    print(f"Recycled from S105: r02_k030 (κ_C=0.15) — not re-run.")

    # Seeds are disjoint from all prior sessions (prefix 108_).
    # Format: (κ_p, κ_C, ω_spread, seed_base, label)
    cells = [
        (0.30, 0.00, 0.060, 108_030_000, 'kp030_kC000_r02'),
        (0.30, 0.05, 0.060, 108_030_005, 'kp030_kC005_r02'),
        (0.30, 0.30, 0.060, 108_030_030, 'kp030_kC030_r02'),
        (0.30, 0.50, 0.060, 108_030_050, 'kp030_kC050_r02'),
    ]

    cell_results = {}
    for kp, kC, omega, sb, label in cells:
        ps = run_cell(kappa_phase=kp, kappa_C=kC,
                      omega_spread=omega, seed_base=sb)
        summary = summarize_cell(ps)
        print(f"   ⇒ {label}: "
              f"RAW R_coh={summary['raw_R_coh_mean']:.3f} ± {summary['raw_R_coh_std']:.3f}   "
              f"ST R_coh={summary['st_R_coh_mean']:.3f} ± {summary['st_R_coh_std']:.3f}   "
              f"R_angle RAW/ST = {summary['cross_seed_R_angle_raw']:.3f} / {summary['cross_seed_R_angle_st']:.3f}   "
              f"<R_kura>={summary['R_kura_cross_seed_mean']:.3f} ± {summary['R_kura_cross_seed_std']:.3f}")
        cell_results[label] = {
            'kappa_phase': kp, 'kappa_C': kC, 'omega_spread': omega,
            'ratio_omega_over_kappa_phase': omega / kp if kp > 0 else float('inf'),
            'seed_base': sb,
            'summary': summary,
            'per_seed_z': pack_per_seed(ps),
        }

    out = {
        'meta': {
            'session': 108,
            'title': 'Ridge Universality at Ratio 0.2 (S107-P3)',
            'started': start.isoformat(),
            'common_params': {
                'A': A_SIGNAL, 'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'kura_decimate': KURA_DECIMATE,
                'ratio_omega_over_kappa_phase': 0.20,
            },
            'design_notes': {
                'purpose': 'Test ridge universality across ω/κ_phase ratio.',
                'hypothesis_A': 'κ_C peak stable at ~0.27 across ratios (universal ridge).',
                'hypothesis_B': 'κ_C peak shifts LOWER at ratio 0.2 (phase-locked regime).',
                'hypothesis_C': 'κ_C peak shifts HIGHER at ratio 0.2.',
                'hypothesis_D': 'R(κ_C) ceiling-limited; ST especially near 1.0.',
                'recycle_source': 'S105 r02_k030 (κ_C=0.15) — 8 seeds × 50 chunks, identical protocol.',
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_108_ridge_ratio_02_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_108_ridge_ratio_02_results.json")


if __name__ == '__main__':
    main()
