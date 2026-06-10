#!/usr/bin/env python3
"""Thor Session #118: The Detection Edge — Where Detectors Actually Compete
==========================================================================

Context (S117)
--------------
S117 ran paired (A=0 null, A=0.40 signal) cells across κ_C and built a
full detection ladder (T_coh, T_white, T_cw_loo, N_sw, LDA) with AUC vs
a paired independent null. The decisive finding: **at A=0.40 every
detector is at AUC≈1.0**. The coherent matched filter T_coh never loses
rank separation even in the over-coupled regime (wedge=120°), because
the destructive cross-term cancels the NULL floor in lockstep. The
"ρ_sig collapse" of S116 was an effect-size collapse, not a detection
collapse. Past the ridge, raw switch COUNT N_sw alone gives AUC=1.0.

The problem this leaves
-----------------------
A=0.40 is *trivially* detectable. When every detector scores AUC=1.0,
the ladder is uninformative — you cannot rank detectors, and you cannot
see whether the over-coupled regime is genuinely "easier" or merely
"easy enough that the ceiling hides the differences". To rank detectors
and to measure a *detection floor*, you must drive A down to where AUC
lives in (0.5, 1.0). That is the detection edge.

S117-P1 (this session)
----------------------
Re-run the ladder at the true detection edge: A ∈ {0.03, 0.06, 0.10,
0.16, 0.24} at κ_C ∈ {0.30 (ridge), 0.50 (transition), 0.70
(over-coupled)}. Combined with the reused S117 anchors (A=0 null,
A=0.40 saturated) this gives a 7-point A curve per κ_C.

Sharp hypotheses
----------------
H1 (floor is κ_C-dependent, INVERTED vs A=0.40): although κ_C=0.70 is
   *easiest* at A=0.40 (N_sw AUC=1 via signal-rescue), near threshold it
   should be *hardest*. Its detection channels — N_sw rate-rescue and
   signal-following R_kura — are higher-order in A and vanish faster as
   A→0 than the ridge's clean coherent matched filter. Predict
   A_min(κ_C=0.30) < A_min(κ_C=0.70).
H2 (ordering inverts at threshold): at A=0.40, raw T_coh = best (=1.0).
   Near threshold the realizable whitened-coherent LOO template
   T_cw_loo should finally *beat* T_coh, because template precision and
   per-class null-whitening matter when the margin is thin (S117-P1).
H3 (N_sw channel switches sign of usefulness): at the ridge N_sw is
   anti-informative (signal reduces switches, AUC<0.5) at all A; in the
   over-coupled regime N_sw is the dominant channel at A=0.40 but should
   need a threshold A* > floor to engage. Below A*, even κ_C=0.70 must
   detect through the coherent/whitened channel, not N_sw.
H4 (fusion is floor-robust, S117-P3): a 2-feature detector
   (log N_sw, T_coh) has the lowest floor at every κ_C because rate and
   timing channels are near-orthogonal — at the ridge T_coh carries it,
   in the over-coupled regime N_sw carries it, and the LDA picks whoever
   is informative.

Design
------
NEW cells (this script): κ_C ∈ {0.30, 0.50, 0.70} × A ∈ {0.03, 0.06,
  0.10, 0.16, 0.24}. 15 cells, 32 seeds × 25 chunks × 1.01M steps.
  κ_p=0.30, ω_std=0.07 fixed (= S113/S115/S116/S117 protocol).
REUSED (from thor_session_117_class_detector_results.json): the A=0 null
  and A=0.40 anchor cells at κ_C ∈ {0.30, 0.50, 0.70} (32 seeds each,
  identical params). The analyzer stitches them in.

Seed namespace: base 200_000_000 + round(κ_C*100)*100_000 +
  round(A*100)*1000, fully disjoint from S117's ~120-125M range.

Compute: 15 cells × 32 seeds × 1.01M steps × ~25.8 µs/step ≈ 206 min.
"""
import json
import sys
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

# Reuse S117 machinery verbatim — identical simulator path & decomposition.
from thor_session_117_class_detector import (
    run_cell,
    summarize_cell,
    pack_per_seed,
)

# S117 constants (kept identical for cross-session comparability)
KAPPA_P = 0.30
OMEGA_STD = 0.07
SIGMA_NOISE = 0.022
SIGNAL_FREQ = 0.003
C_THRESHOLD = 0.55
WARMUP = 10_000
CHUNK_STEPS = 40_000
N_SEEDS = 32
N_CHUNKS = 25

KC_VALS = [0.30, 0.50, 0.70]
A_VALS = [0.03, 0.06, 0.10, 0.16, 0.24]


def main():
    start = datetime.now()
    print("Thor Session #118: The Detection Edge")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  chunk={CHUNK_STEPS}  "
          f"warmup={WARMUP}  {N_SEEDS} seeds × {N_CHUNKS} chunks  "
          f"κ_p={KAPPA_P} ω_std={OMEGA_STD}")
    print(f"κ_C ∈ {KC_VALS}  ×  A ∈ {A_VALS}  ({len(KC_VALS)*len(A_VALS)} cells)")

    cells_def = []
    for kc in KC_VALS:
        for A in A_VALS:
            label = f'kc{int(round(kc*100)):03d}_A{int(round(A*100)):03d}'
            cells_def.append((label, kc, A))

    meta = {
        'session': 118,
        'title': 'The Detection Edge',
        'started': start.isoformat(),
        'reuses': 'thor_session_117_class_detector_results.json (A=0 nulls + A=0.40 anchors, κ_C∈{0.30,0.50,0.70})',
        'common_params': {
            'sigma': SIGMA_NOISE, 'dt': 0.1, 'signal_freq': SIGNAL_FREQ,
            'C_threshold': C_THRESHOLD, 'warmup': WARMUP,
            'chunk_steps': CHUNK_STEPS, 'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
            'kappa_phase': KAPPA_P, 'omega_std': OMEGA_STD, 'omega_base': 0.1,
        },
        'cells_def': cells_def, 'kc_vals': KC_VALS, 'A_vals': A_VALS,
    }

    out_path = 'thor_session_118_detection_edge_results.json'

    def checkpoint(cell_results, done):
        meta_now = dict(meta)
        meta_now['cells_completed'] = done
        meta_now['n_cells_total'] = len(cells_def)
        with open(out_path, 'w') as f:
            json.dump({'meta': meta_now, 'cells': cell_results}, f,
                      indent=2, default=float)

    cell_results = {}
    for ci, (label, kc, A) in enumerate(cells_def):
        seed_base = (200_000_000
                     + int(round(kc * 100)) * 100_000
                     + int(round(A * 100)) * 1000)
        seed_records, omega_vec = run_cell(
            label, KAPPA_P, kc, OMEGA_STD, A, seed_base,
            n_chunks=N_CHUNKS, n_seeds=N_SEEDS)
        summary = summarize_cell(seed_records, A, KAPPA_P, kc, OMEGA_STD)
        print(f"\n   ⇒ {label}: κ_C={kc:.2f} A={A:.2f}  "
              f"R_kura={summary['kura_mean_mean']:.3f}  "
              f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
              f"wedge={summary['wedge_aL_rN']:.0f}°  "
              f"<Nsw>={summary['n_sw_total_mean']:.0f}")
        cell_results[label] = {
            'kappa_phase': KAPPA_P, 'kappa_C': kc, 'omega_std': OMEGA_STD,
            'omega_vec': omega_vec, 'signal_amp': A, 'seed_base': seed_base,
            'summary': summary, 'per_seed': pack_per_seed(seed_records),
        }
        checkpoint(cell_results, ci + 1)
        print(f"   [checkpoint] {ci+1}/{len(cells_def)} cells → {out_path}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"Results → {out_path}")


if __name__ == '__main__':
    main()
