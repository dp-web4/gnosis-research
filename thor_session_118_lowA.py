#!/usr/bin/env python3
"""Thor Session #118 — LOW-A extension of the detection-edge run.

The main S118 grid (A ∈ {0.03 … 0.40}) found that the realizable optimal
detector T_cw_loo (whitened-coherent, leave-one-out phase template) is already
saturated at AUC = 1.000 at the grid bottom A = 0.03 for ALL κ_C ∈
{0.30, 0.50, 0.70}. The pre-registered floor-inversion (H1) therefore could not
be resolved — the true floor of the optimal detector sits *below* A = 0.03.

The S118 d′ table shows the over-coupled cell is closest to threshold:
d′(T_cw_loo, A=0.03) = 8.45 (κ_C=0.30) / 5.98 (0.50) / 2.52 (0.70). If a floor
inversion exists at all, κ_C=0.70 should fail first as A → 0.

This driver fills A ∈ {0.005, 0.010, 0.015, 0.020, 0.025} at the same three κ_C
(15 cells, 32 seeds × 25 chunks), reusing the verbatim per-seed body, summarize,
and packing from thor_session_118_parallel. Identical numerics; deterministic in
seed. Output → thor_session_118_lowA_results.json. Analyzed jointly with the
S117 nulls + main S118 grid by thor_session_118_lowA_analyze.py.
"""
import json
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_112_omega_cliff import build_omega
from thor_session_117_class_detector import (
    summarize_cell, pack_per_seed, N_SEEDS, N_CHUNKS,
)
from thor_session_118_parallel import (
    run_one_seed, KAPPA_P, OMEGA_STD, OMEGA_BASE, N_WORKERS,
)

KC_VALS = [0.30, 0.50, 0.70]
A_VALS = [0.005, 0.010, 0.015, 0.020, 0.025]
OUT_PATH = 'thor_session_118_lowA_results.json'


def main():
    start = datetime.now()
    print("Thor Session #118: Detection Edge LOW-A extension")
    print(f"Started: {start.isoformat()}")
    print(f"κ_p={KAPPA_P} ω_std={OMEGA_STD}  {N_SEEDS} seeds × {N_CHUNKS} chunks  "
          f"workers={N_WORKERS}")
    print(f"κ_C ∈ {KC_VALS}  ×  A ∈ {A_VALS}  ({len(KC_VALS)*len(A_VALS)} cells)")

    cells_def = []
    for kc in KC_VALS:
        for A in A_VALS:
            label = f'kc{int(round(kc*100)):03d}_Am{int(round(A*1000)):03d}'
            cells_def.append((label, kc, A))

    omega_vec = build_omega(OMEGA_BASE, OMEGA_STD)
    meta = {
        'session': 118, 'title': 'Detection Edge LOW-A extension',
        'started': start.isoformat(),
        'driver': 'lowA (verbatim run_one_seed from thor_session_118_parallel)',
        'reuses': 'S117 nulls (A=0) + main S118 grid (A≥0.03)',
        'common_params': {
            'kappa_phase': KAPPA_P, 'omega_std': OMEGA_STD, 'omega_base': OMEGA_BASE,
            'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
        },
        'cells_def': cells_def, 'kc_vals': KC_VALS, 'A_vals': A_VALS,
    }

    def checkpoint(cell_results, done):
        m = dict(meta); m['cells_completed'] = done; m['n_cells_total'] = len(cells_def)
        with open(OUT_PATH, 'w') as f:
            json.dump({'meta': m, 'cells': cell_results}, f, indent=2, default=float)

    cell_results = {}
    if os.path.exists(OUT_PATH):
        try:
            cell_results = json.load(open(OUT_PATH)).get('cells', {})
            print(f"[resume] {len(cell_results)} cells: {sorted(cell_results)}")
        except Exception as e:
            print(f"[resume] could not load ({e}); fresh"); cell_results = {}

    with Pool(N_WORKERS) as pool:
        for ci, (label, kc, A) in enumerate(cells_def):
            if label in cell_results:
                print(f"\n>> {label}: already done — skipping"); continue
            seed_base = (210_000_000 + int(round(kc * 100)) * 100_000
                         + int(round(A * 1000)) * 100)
            tasks = [(KAPPA_P, kc, omega_vec.tolist(), A, seed_base + s, N_CHUNKS)
                     for s in range(N_SEEDS)]
            cstart = time.time()
            print(f"\n>> {label}: κ_C={kc:.2f} A={A:.4f} seed_base={seed_base}")
            recs = pool.map(run_one_seed, tasks)
            recs.sort(key=lambda r: r['seed'])
            summary = summarize_cell(recs, A, KAPPA_P, kc, OMEGA_STD)
            print(f"   ⇒ {label}: R_kura={summary['kura_mean_mean']:.3f}  "
                  f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
                  f"wedge={summary['wedge_aL_rN']:.0f}°  "
                  f"<Nsw>={summary['n_sw_total_mean']:.0f}  "
                  f"T_coh={summary['T_coh_mean']:.1f}  ({time.time()-cstart:.0f}s)")
            cell_results[label] = {
                'kappa_phase': KAPPA_P, 'kappa_C': kc, 'omega_std': OMEGA_STD,
                'omega_vec': omega_vec.tolist(), 'signal_amp': A,
                'seed_base': seed_base, 'summary': summary,
                'per_seed': pack_per_seed(recs),
            }
            checkpoint(cell_results, ci + 1)
            print(f"   [checkpoint] {ci+1}/{len(cells_def)} → {OUT_PATH}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)  →  {OUT_PATH}")


if __name__ == '__main__':
    main()
