#!/usr/bin/env python3
"""Thor Session #119 — PARALLEL driver for the ω-heterogeneity run.

Identical experiment and numerics to thor_session_119_omega_heterogeneity.py
(see that file's docstring for hypotheses H1–H3), but seeds are evaluated
across processes using the verified per-seed body from S118's parallel
driver (run_one_seed). Each seed is fully deterministic in its seed value,
so results are byte-identical to the sequential driver.

Per-cell checkpointing with resume: rerunning after an interruption skips
completed cells.
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
    summarize_cell, pack_per_seed,
    SIGMA_NOISE, SIGNAL_FREQ, C_THRESHOLD, WARMUP, CHUNK_STEPS,
    N_SEEDS, N_CHUNKS,
)
from thor_session_118_parallel import run_one_seed

KAPPA_P = 0.30
KAPPA_C = 0.30
OMEGA_BASE = 0.1
OMEGA_STD_VALS = [0.00, 0.13]          # NEW (0.07 reused from S117/S118)
A_VALS = [0.00, 0.02, 0.06, 0.16, 0.40]
N_WORKERS = 12


def main():
    start = datetime.now()
    print("Thor Session #119: ω-detuning drives the d′ inverted-U (PARALLEL)")
    print(f"Started: {start.isoformat()}")
    print(f"κ_p={KAPPA_P} κ_C={KAPPA_C}  σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"{N_SEEDS} seeds × {N_CHUNKS} chunks  workers={N_WORKERS}")
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
        'driver': 'parallel (identical numerics to thor_session_119_omega_heterogeneity.py)',
        'reuses': 'S117/S118 ω_std=0.07 κ_C=0.30 cells (A∈{0,0.02..0.40})',
        'common_params': {
            'sigma': SIGMA_NOISE, 'dt': 0.1, 'signal_freq': SIGNAL_FREQ,
            'C_threshold': C_THRESHOLD, 'warmup': WARMUP,
            'chunk_steps': CHUNK_STEPS, 'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
            'kappa_phase': KAPPA_P, 'kappa_C': KAPPA_C, 'omega_base': OMEGA_BASE,
        },
        'cells_def': cells_def, 'omega_std_vals': OMEGA_STD_VALS, 'A_vals': A_VALS,
    }
    out_path = 'thor_session_119_omega_heterogeneity_results.json'

    def checkpoint(cell_results, done):
        m = dict(meta); m['cells_completed'] = done; m['n_cells_total'] = len(cells_def)
        with open(out_path, 'w') as f:
            json.dump({'meta': m, 'cells': cell_results}, f, indent=2, default=float)

    cell_results = {}
    if os.path.exists(out_path):
        try:
            prev = json.load(open(out_path))
            cell_results = prev.get('cells', {})
            print(f"[resume] found {len(cell_results)} completed cells: "
                  f"{sorted(cell_results)}")
        except Exception as e:
            print(f"[resume] could not load checkpoint ({e}); starting fresh")
            cell_results = {}

    with Pool(N_WORKERS) as pool:
        for ci, (label, omstd, A) in enumerate(cells_def):
            if label in cell_results:
                print(f"\n>> {label}: already done (resumed) — skipping")
                continue
            omega_vec = build_omega(OMEGA_BASE, omstd)
            seed_base = (300_000_000
                         + int(round(omstd * 100)) * 1_000_000
                         + int(round(A * 100)) * 1000)
            tasks = [(KAPPA_P, KAPPA_C, omega_vec.tolist(), A,
                      seed_base + s, N_CHUNKS) for s in range(N_SEEDS)]
            cstart = time.time()
            print(f"\n>> {label}: ω_std={omstd:.2f} A={A:.3f} seed_base={seed_base} "
                  f"({N_SEEDS} seeds × {N_WORKERS} workers)")
            recs = pool.map(run_one_seed, tasks)
            recs.sort(key=lambda r: r['seed'])
            summary = summarize_cell(recs, A, KAPPA_P, KAPPA_C, omstd)
            print(f"   ⇒ {label}: R_kura={summary['kura_mean_mean']:.3f}  "
                  f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
                  f"<Nsw>={summary['n_sw_total_mean']:.0f}  "
                  f"T_coh={summary['T_coh_mean']:.1f}  "
                  f"({time.time()-cstart:.0f}s, max chk="
                  f"{max(r['per_chunk_chk'] for r in recs):.1e})")
            cell_results[label] = {
                'kappa_phase': KAPPA_P, 'kappa_C': KAPPA_C, 'omega_std': omstd,
                'omega_vec': omega_vec.tolist(), 'signal_amp': A,
                'seed_base': seed_base, 'summary': summary,
                'per_seed': pack_per_seed(recs),
            }
            checkpoint(cell_results, ci + 1)
            print(f"   [checkpoint] {ci+1}/{len(cells_def)} → {out_path}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)  →  {out_path}")


if __name__ == '__main__':
    main()
