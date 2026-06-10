#!/usr/bin/env python3
"""Thor Session #118 — PARALLEL driver for the detection-edge run.

Identical experiment and numerics to thor_session_118_detection_edge.py, but
seeds are evaluated across processes. Each seed is fully deterministic in its
seed value (simulate_with_omega calls np.random.seed(seed) at entry and nothing
else touches the global RNG), so process-order is irrelevant — results are
byte-identical to the sequential driver. The per-step Python loop in
simulate_with_omega is single-core-bound (~25.7 s/seed); with N_WORKERS≈12 on
the 14-core box this finishes in ~20 min instead of ~206 min.

The per-seed body below is a verbatim copy of run_cell's loop body
(thor_session_117_class_detector.run_cell). It is verified against the known
sequential output for seed 203003000 (Nsw=8031, R_k=0.298, T_coh=1145.5,
T_incoh=38586.6) before the full run — see --verify.

summarize_cell and pack_per_seed are reused verbatim from S117.
"""
import json
import sys
import time
from datetime import datetime
from multiprocessing import Pool

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_111_dose_response import (
    per_seed_R_coh, lock_modulation_at_fs,
)
from thor_session_112_omega_cliff import build_omega, simulate_with_omega
from thor_session_113_dip_decomposition import per_switch_state, class_decompose
from thor_session_117_class_detector import (
    per_chunk_class_decompose, summarize_cell, pack_per_seed,
    CLASSES, C_THRESHOLD, SIGNAL_FREQ, SIGMA_NOISE, DT, WARMUP,
    CHUNK_STEPS, N_SEEDS, N_CHUNKS, LOCK_THR,
)

KAPPA_P = 0.30
OMEGA_STD = 0.07
OMEGA_BASE = 0.1
KC_VALS = [0.30, 0.50, 0.70]
A_VALS = [0.03, 0.06, 0.10, 0.16, 0.24]
N_WORKERS = 12


def run_one_seed(task):
    """Verbatim per-seed body of run_cell. task = (kappa_phase, kappa_C,
    omega_vec(list), signal_amp, seed, n_chunks). Returns the seed record dict."""
    kappa_phase, kappa_C, omega_vec, signal_amp, seed, n_chunks = task
    omega_vec = np.asarray(omega_vec, dtype=float)
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    t0 = time.time()
    (Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
     sw_steps, sw_dirs, k_mean) = simulate_with_omega(
        N=4, noise_std=SIGMA_NOISE, steps=total_steps,
        seed=seed, omega=omega_vec,
        kappa_phase=kappa_phase, kappa_C=kappa_C,
        signal_freq=SIGNAL_FREQ, signal_amp=signal_amp, dt=DT)
    xp = Cm[WARMUP:]
    z_raw = np.zeros(n_chunks, dtype=complex)
    z_st = np.zeros(n_chunks, dtype=complex)
    n_sw_chunks = np.zeros(n_chunks, dtype=int)
    for c in range(n_chunks):
        chunk = xp[c * CHUNK_STEPS:(c + 1) * CHUNK_STEPS]
        t_off = WARMUP + c * CHUNK_STEPS
        Ir, Qr = phase_coherent_IQ(chunk, DT, SIGNAL_FREQ, t_offset=t_off)
        Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ,
                                     t_offset=t_off, threshold=C_THRESHOLD)
        z_raw[c] = Ir + 1j * Qr
        z_st[c] = Is + 1j * Qs
        n_sw_chunks[c] = n
    raw_st = per_seed_R_coh(z_raw)
    st_st = per_seed_R_coh(z_st)
    I_lock, Q_lock, mod_amp_lock, mod_arg_lock = lock_modulation_at_fs(kdec, spdec)
    kura_at_sw, gate_at_sw, lock_at_sw = per_switch_state(sw_steps, sw_dirs, kdec, gdec)
    decomp = class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw)
    mu_kc, cnt_kc = per_chunk_class_decompose(
        sw_steps, sw_dirs, gate_at_sw, lock_at_sw, n_chunks=n_chunks)
    chk = 0.0
    for k in CLASSES:
        mu_seed_k = mu_kc[k].sum()
        ref = complex(decomp['per_class'][k]['mu_re'],
                      decomp['per_class'][k]['mu_im'])
        chk = max(chk, abs(mu_seed_k - ref))
    rec = {
        'seed': seed,
        'z_st': z_st, 'n_sw_chunks': n_sw_chunks,
        'raw_per_seed': raw_st, 'st_per_seed': st_st,
        'kura_mean': k_mean,
        'lock_frac_global': float((kdec > LOCK_THR).mean()),
        'mod_amp_at_fs_lock': mod_amp_lock,
        'switch_total': int(len(sw_steps)),
        'lock_at_switch_frac': float(lock_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
        'gate_att_at_switch_frac': float(gate_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
        'class_decomp': decomp,
        'mu_kc': mu_kc, 'cnt_kc': cnt_kc,
        'per_chunk_chk': float(chk),
        '_elapsed': time.time() - t0,
    }
    return rec


def verify():
    """Reproduce sequential ground-truth for seed 203003000 (kc=0.30, A=0.03)."""
    omega_vec = build_omega(OMEGA_BASE, OMEGA_STD)
    rec = run_one_seed((KAPPA_P, 0.30, omega_vec.tolist(), 0.03, 203003000, N_CHUNKS))
    T_coh = rec['class_decomp']['z_total_abs2']
    T_incoh = rec['class_decomp']['sum_class_sq']
    print(f"seed=203003000  Nsw={rec['switch_total']}  R_k={rec['kura_mean']:.3f}  "
          f"T_coh={T_coh:.1f}  T_incoh={T_incoh:.1f}  chk={rec['per_chunk_chk']:.1e}")
    ok = (rec['switch_total'] == 8031
          and abs(rec['kura_mean'] - 0.298) < 5e-4
          and abs(T_coh - 1145.5) < 0.1
          and abs(T_incoh - 38586.6) < 0.1)
    print("VERIFY:", "PASS — identical to sequential" if ok else "FAIL — numerics differ!")
    return ok


def main():
    start = datetime.now()
    print("Thor Session #118: The Detection Edge (PARALLEL)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  chunk={CHUNK_STEPS}  "
          f"warmup={WARMUP}  {N_SEEDS} seeds × {N_CHUNKS} chunks  "
          f"κ_p={KAPPA_P} ω_std={OMEGA_STD}  workers={N_WORKERS}")
    print(f"κ_C ∈ {KC_VALS}  ×  A ∈ {A_VALS}  ({len(KC_VALS)*len(A_VALS)} cells)")

    cells_def = []
    for kc in KC_VALS:
        for A in A_VALS:
            label = f'kc{int(round(kc*100)):03d}_A{int(round(A*100)):03d}'
            cells_def.append((label, kc, A))

    omega_vec_default = build_omega(OMEGA_BASE, OMEGA_STD)
    meta = {
        'session': 118, 'title': 'The Detection Edge', 'started': start.isoformat(),
        'driver': 'parallel (identical numerics to thor_session_118_detection_edge.py)',
        'reuses': 'thor_session_117_class_detector_results.json (A=0 nulls + A=0.40 anchors, κ_C∈{0.30,0.50,0.70})',
        'common_params': {
            'sigma': SIGMA_NOISE, 'dt': DT, 'signal_freq': SIGNAL_FREQ,
            'C_threshold': C_THRESHOLD, 'warmup': WARMUP,
            'chunk_steps': CHUNK_STEPS, 'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
            'kappa_phase': KAPPA_P, 'omega_std': OMEGA_STD, 'omega_base': OMEGA_BASE,
        },
        'cells_def': cells_def, 'kc_vals': KC_VALS, 'A_vals': A_VALS,
    }
    out_path = 'thor_session_118_detection_edge_results.json'

    def checkpoint(cell_results, done):
        m = dict(meta); m['cells_completed'] = done; m['n_cells_total'] = len(cells_def)
        with open(out_path, 'w') as f:
            json.dump({'meta': m, 'cells': cell_results}, f, indent=2, default=float)

    # Resume: load completed cells from an existing checkpoint and skip them.
    # Cells are byte-deterministic in their seeds, so resumed + fresh cells form
    # one consistent result set.
    cell_results = {}
    import os
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
        for ci, (label, kc, A) in enumerate(cells_def):
            if label in cell_results:
                print(f"\n>> {label}: already done (resumed) — skipping")
                continue
            seed_base = (200_000_000
                         + int(round(kc * 100)) * 100_000
                         + int(round(A * 100)) * 1000)
            tasks = [(KAPPA_P, kc, omega_vec_default.tolist(), A,
                      seed_base + s, N_CHUNKS) for s in range(N_SEEDS)]
            cstart = time.time()
            print(f"\n>> {label}: κ_C={kc:.2f} A={A:.3f} seed_base={seed_base} "
                  f"({N_SEEDS} seeds × {N_WORKERS} workers)")
            recs = pool.map(run_one_seed, tasks)
            recs.sort(key=lambda r: r['seed'])   # deterministic order
            summary = summarize_cell(recs, A, KAPPA_P, kc, OMEGA_STD)
            print(f"   ⇒ {label}: R_kura={summary['kura_mean_mean']:.3f}  "
                  f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
                  f"wedge={summary['wedge_aL_rN']:.0f}°  "
                  f"<Nsw>={summary['n_sw_total_mean']:.0f}  "
                  f"T_coh={summary['T_coh_mean']:.1f}  "
                  f"({time.time()-cstart:.0f}s, max chk="
                  f"{max(r['per_chunk_chk'] for r in recs):.1e})")
            cell_results[label] = {
                'kappa_phase': KAPPA_P, 'kappa_C': kc, 'omega_std': OMEGA_STD,
                'omega_vec': omega_vec_default.tolist(), 'signal_amp': A,
                'seed_base': seed_base, 'summary': summary,
                'per_seed': pack_per_seed(recs),
            }
            checkpoint(cell_results, ci + 1)
            print(f"   [checkpoint] {ci+1}/{len(cells_def)} → {out_path}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)  →  {out_path}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        sys.exit(0 if verify() else 1)
    main()
