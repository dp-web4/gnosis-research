#!/usr/bin/env python3
"""Thor Session #107: 2D Coupling Surface — the (κ_phase, κ_C) Ridge Map.

Context (S106, S106-P1)
-----------------------
S106 discovered that at κ_phase=0.30, ω=0.24 (ratio 0.8), R_coh peaks at
κ_C ≈ 0.30 (RAW 0.610) and collapses at κ_C=0.50 (RAW 0.269). This
identifies a 2D ridge in (κ_phase, κ_C) space that prior S105 work (κ_phase
sweeps at fixed κ_C=0.15) could not see. S106 was a single vertical slice
at κ_phase=0.30.

S107 adds two more vertical slices (κ_phase=0.15 weak, κ_phase=0.50 strong)
to answer:

1. **Does the κ_C peak position shift with κ_phase?**
   Predict (S106-P3 line): approximate invariance at κ_C ≈ 0.25–0.35, since
   the peak emerges from an internal oscillator-coupling balance, not
   signal-coupling strength. If peak DOES shift significantly, the story
   gets richer: κ_C optimum depends on κ_phase via indirect channels.

2. **How does the ridge height scale with κ_phase?**
   Predict (S106-P1 line): R_peak grows with κ_phase. Magnitude of the
   κ_C sweep (0.091 → 0.610, 6.7× range at κ_phase=0.30) should hold or
   widen at κ_phase=0.50.

3. **Is there κ_phase saturation at the ridge?** (S105-P3 now at κ_C=ridge)
   S105 showed dR/dκ_phase=+0.94 at κ_C=0.15 between κ_phase=0.05 and 0.50.
   Does that same slope hold on the ridge (κ_C=0.30)? If slope is SMALLER
   on the ridge, κ_phase + ridge-κ_C are closer to separate additive
   channels. If LARGER, they interact multiplicatively.

Design
------
Grid at ratio ω/κ_phase = 0.80:
  κ_phase ∈ {0.15, 0.30, 0.50}
  κ_C     ∈ {0.00, 0.05, 0.15, 0.30, 0.50}

Already run (reuse via recycling):
  κ_phase = 0.30 × all 5 κ_C points (S106)
  κ_phase = 0.15, κ_C = 0.15  (S105 r08_k015)
  κ_phase = 0.50, κ_C = 0.15  (S105 r08_k050)

NEW cells (this session):
  κ_phase = 0.15, κ_C ∈ {0.00, 0.05, 0.30, 0.50}  — 4 cells
  κ_phase = 0.50, κ_C ∈ {0.00, 0.05, 0.30, 0.50}  — 4 cells

Each cell: 8 seeds × 50 chunks × 40k steps + 10k warmup = 16M steps.
~6.7 min/cell × 8 cells ≈ 54 min wall time.

Observables per cell (matches S105/S106):
  - per-seed R_coh_raw, R_coh_st
  - cross-seed angular coherence R_angle
  - Kuramoto order R_kura (decimated by 10, post-warmup)
  - switch count per chunk N_sw

Predictions (what we'd learn from each)
----------------------------------------
A: κ_C peak stable across κ_phase → ridge is a flat line at κ_C ≈ 0.30
   with height monotone in κ_phase. Confirms S106-P3.
B: κ_C peak shifts lower (κ_C ≈ 0.15) at κ_phase=0.50 → stronger κ_phase
   compensates for less C-coupling. Ridge has negative slope.
C: κ_C peak shifts higher (κ_C ≈ 0.40+) at κ_phase=0.50 → more phase
   coupling needs more C-coupling to balance. Ridge has positive slope.
D: Peak disappears at κ_phase=0.15 (monotone curve) → the peak is a
   strong-coupling phenomenon, not a universal ridge. S106 would be a
   special case, not a general feature.

My prior: between A and C. Peak exists at all three κ_phase slices, but
shifts slightly positive at higher κ_phase because the C-coupling
homogenization effect needs more force to flatten an oscillator array
that's already tightly phase-locked.
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
    print("Thor Session #107: 2D Coupling Surface — Ridge Map (S106-P1)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: A={A_SIGNAL}  σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks × {CHUNK_STEPS} steps")
    print(f"Grid: ratio ω/κ_p = 0.80, κ_p ∈ {{0.15, 0.30, 0.50}}, "
          f"κ_C ∈ {{0.00, 0.05, 0.15, 0.30, 0.50}}")

    # 8 NEW cells. Seeds are disjoint from S105/S106 (prefix 107_).
    # Format: (κ_p, κ_C, ω_spread, seed_base, label)
    cells = [
        # κ_p = 0.15 slice (ω = 0.12, ratio 0.8)
        (0.15, 0.00, 0.120, 107_015_000, 'kp015_kC000'),
        (0.15, 0.05, 0.120, 107_015_005, 'kp015_kC005'),
        (0.15, 0.30, 0.120, 107_015_030, 'kp015_kC030'),
        (0.15, 0.50, 0.120, 107_015_050, 'kp015_kC050'),
        # κ_p = 0.50 slice (ω = 0.40, ratio 0.8)
        (0.50, 0.00, 0.400, 107_050_000, 'kp050_kC000'),
        (0.50, 0.05, 0.400, 107_050_005, 'kp050_kC005'),
        (0.50, 0.30, 0.400, 107_050_030, 'kp050_kC030'),
        (0.50, 0.50, 0.400, 107_050_050, 'kp050_kC050'),
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
            'session': 107,
            'title': '2D Coupling Surface — (κ_phase, κ_C) Ridge Map',
            'started': start.isoformat(),
            'common_params': {
                'A': A_SIGNAL, 'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'kura_decimate': KURA_DECIMATE,
                'ratio_omega_over_kappa_phase': 0.80,
            },
            'design_notes': {
                'purpose': 'Map the (κ_p, κ_C) ridge first identified in S106.',
                'hypothesis_A': 'κ_C peak stable at ~0.30 across κ_phase.',
                'hypothesis_B': 'κ_C peak shifts lower at larger κ_phase.',
                'hypothesis_C': 'κ_C peak shifts higher at larger κ_phase.',
                'hypothesis_D': 'No peak at weak κ_phase=0.15 (monotone curve).',
                'recycle_source': 'S106 provides full κ_phase=0.30 slice; S105 provides κ_C=0.15 at all three κ_phase values.',
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_107_ridge_map_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_107_ridge_map_results.json")


if __name__ == '__main__':
    main()
