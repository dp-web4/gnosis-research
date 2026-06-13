#!/usr/bin/env python3
"""Thor Session #119: The d′ Inverted-U Is a Reproducibility Limit Set by ω-Detuning
=====================================================================================

Context (S118 + S119 Part 1)
----------------------------
S118 found the realizable optimal detector T_cw_loo (whitened-coherent,
LOO phase template) has an *inverted-U* d′(A): d′ rises to a peak near
A≈0.06 then FALLS toward a floor (~3.4 at A=0.40, ridge), while AUC stays
≈1.0. S119 Part 1 (thor_session_119_dprime_decomp.py) decomposed this on
the existing ω_std=0.07 data and found the closed form

    d′ ≈ √2 / CV_sig                                            (var_null ≪ var_sig)

i.e. at the edge the detector's d′ is set by the *seed-to-seed
reproducibility* (coefficient of variation) of its own statistic, NOT by
the signal-to-noise margin. The d′ inverted-U is EXACTLY the U-shape in
CV_sig inverted: CV bottoms at A≈0.06 (0.115 ridge) then rises again at
high A (0.297 at A=0.40). The d′ "fall" is a reproducibility collapse.

The open question: WHAT drives the high-A CV rise? In this simulator ω is
a FIXED 4-element vector (identical across seeds; offsets
{-3,-1,1,3}/√5·ω_std), so the heterogeneity is NOT a seed-draw artifact
(unlike S112's random-ω cliff). It must come from the *within-array
frequency detuning* ω_std interacting with the gate-modulated dynamics:
larger detuning ⇒ more stochastic locking ⇒ more variable per-seed signal
response at high A ⇒ higher CV ⇒ lower d′.

Hypothesis (causal)
-------------------
H1: The d′ fall is ω_std-driven, not intrinsic to the detector. At ω_std=0
    (identical oscillators) the high-A CV rise should be suppressed, so
    d′(A) becomes monotone rise → saturate (no fall, or a much shallower one).
H2: The effect is monotone in ω_std: the high-A d′ (e.g. A=0.40) and the
    inverted-U depth (d′_peak / d′_high) order as ω_std=0.00 < 0.07 < 0.13.
H3: AUC stays ≈1.0 at the edge regardless of ω_std (rank-detectability is a
    margin property, robust to reproducibility) — so AUC and d′ decouple
    MORE as ω_std grows. The closed form d′≈√2/CV_sig holds at every ω_std.

Design
------
3-point ω_std causal series at the ridge (κ_C=0.30, κ_p=0.30):
  ω_std ∈ {0.00, 0.13}  (NEW; ω_std=0.07 reused from S118/S117)
  ×  A ∈ {0.00, 0.02, 0.06, 0.16, 0.40}
  10 NEW cells, 32 seeds × 25 chunks × 1.01M steps. κ_C=0.30 only — the
  ridge has the cleanest inverted-U (d′ span 12→3.4) and best per-channel
  SNR, isolating the ω_std mechanism from the κ_C SNR deficit.

Seed namespace: 300_000_000 + round(ω_std*100)*1_000_000 + round(A*100)*1000,
  disjoint from S117 (117M) and S118 (200M).

The analyzer (thor_session_119_analyze.py) stitches the ω_std=0.07 cells
from S117/S118 and rebuilds the T_cw_loo d′/AUC/CV ladder across all three
ω_std values.

Compute: 10 cells × 32 seeds × ~26 s ≈ 140 min on Thor.
"""
import json
import sys
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_class_detector import (
    run_cell, summarize_cell, pack_per_seed,
)

KAPPA_P = 0.30
KAPPA_C = 0.30
SIGMA_NOISE = 0.022
SIGNAL_FREQ = 0.003
C_THRESHOLD = 0.55
WARMUP = 10_000
CHUNK_STEPS = 40_000
N_SEEDS = 32
N_CHUNKS = 25

OMEGA_STD_VALS = [0.00, 0.13]          # NEW (0.07 reused from S117/S118)
A_VALS = [0.00, 0.02, 0.06, 0.16, 0.40]


def main():
    start = datetime.now()
    print("Thor Session #119: ω-detuning drives the d′ inverted-U")
    print(f"Started: {start.isoformat()}")
    print(f"κ_p={KAPPA_P} κ_C={KAPPA_C}  σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"{N_SEEDS} seeds × {N_CHUNKS} chunks")
    print(f"ω_std ∈ {OMEGA_STD_VALS} (NEW)  ×  A ∈ {A_VALS}  "
          f"({len(OMEGA_STD_VALS)*len(A_VALS)} cells)")

    cells_def = []
    for omstd in OMEGA_STD_VALS:
        for A in A_VALS:
            label = f'om{int(round(omstd*100)):03d}_A{int(round(A*100)):03d}'
            cells_def.append((label, omstd, A))

    meta = {
        'session': 119,
        'title': 'omega-detuning drives the d-prime inverted-U',
        'started': start.isoformat(),
        'reuses': 'S117/S118 ω_std=0.07 κ_C=0.30 cells (A∈{0,0.02..0.40})',
        'common_params': {
            'sigma': SIGMA_NOISE, 'dt': 0.1, 'signal_freq': SIGNAL_FREQ,
            'C_threshold': C_THRESHOLD, 'warmup': WARMUP,
            'chunk_steps': CHUNK_STEPS, 'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
            'kappa_phase': KAPPA_P, 'kappa_C': KAPPA_C, 'omega_base': 0.1,
        },
        'cells_def': cells_def, 'omega_std_vals': OMEGA_STD_VALS, 'A_vals': A_VALS,
    }

    out_path = 'thor_session_119_omega_heterogeneity_results.json'

    def checkpoint(cell_results, done):
        m = dict(meta); m['cells_completed'] = done; m['n_cells_total'] = len(cells_def)
        with open(out_path, 'w') as f:
            json.dump({'meta': m, 'cells': cell_results}, f, indent=2, default=float)

    # Resume: load any cells already completed in a prior (interrupted) run.
    cell_results = {}
    try:
        with open(out_path) as f:
            prev = json.load(f)
        cell_results = {k: v for k, v in prev.get('cells', {}).items()}
        if cell_results:
            print(f"[resume] loaded {len(cell_results)} completed cells: "
                  f"{sorted(cell_results)}")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    for ci, (label, omstd, A) in enumerate(cells_def):
        if label in cell_results:
            print(f"[resume] skip {label} ({ci+1}/{len(cells_def)}) — already done")
            continue
        seed_base = (300_000_000
                     + int(round(omstd * 100)) * 1_000_000
                     + int(round(A * 100)) * 1000)
        seed_records, omega_vec = run_cell(
            label, KAPPA_P, KAPPA_C, omstd, A, seed_base,
            n_chunks=N_CHUNKS, n_seeds=N_SEEDS)
        summary = summarize_cell(seed_records, A, KAPPA_P, KAPPA_C, omstd)
        print(f"\n   ⇒ {label}: ω_std={omstd:.2f} A={A:.2f}  "
              f"R_kura={summary['kura_mean_mean']:.3f}  "
              f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
              f"<Nsw>={summary['n_sw_total_mean']:.0f}")
        cell_results[label] = {
            'kappa_phase': KAPPA_P, 'kappa_C': KAPPA_C, 'omega_std': omstd,
            'omega_vec': omega_vec, 'signal_amp': A, 'seed_base': seed_base,
            'summary': summary, 'per_seed': pack_per_seed(seed_records),
        }
        checkpoint(cell_results, ci + 1)
        print(f"   [checkpoint] {ci+1}/{len(cells_def)} → {out_path}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")


if __name__ == '__main__':
    main()
