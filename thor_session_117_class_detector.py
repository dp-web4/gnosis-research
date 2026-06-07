#!/usr/bin/env python3
"""Thor Session #117: Coherent vs Incoherent Class Combining
============================================================

Context (S116-P8)
-----------------
S116 found that past the κ_C ridge (κ_C ≥ 0.50, the "signal-following
oscillator" regime) the att_lock and rep_noise switch-classes rotate
toward near-anti-phase (wedge → 153° at κ_C=0.70 A=0.30). The two
dominant per-class phasors do NOT vanish (|μ_aL|≈28, |μ_rN|≈25) but
their coherent sum cancels: |Σ_k μ_k|² = 879 while Σ_k |μ_k|² = 1358.
The standard detector ρ_sig = |Σ_k μ_k|² / N_sw is a *naive coherent
combine* of the classes and collapses (ρ_sig 0.13 ridge → 0.01).

S116-P8 asked: would an alternative detector that operates on per-class
phasors directly — sum of |μ_class|² instead of |Σμ_class|² — recover
the per-class detection power in the over-coupled regime?

Detection-theory framing
-------------------------
The class partition (gate × R_kura>0.9 at switch time) is signal-BLIND
(uses only internal C-gate and Kuramoto order), so a real detector can
compute it. Two ways to combine the 4 class matched-filter phasors:

  T_coh   = |Σ_k μ_k|²       naive coherent  (= current ρ_sig·N_sw)
  T_incoh = Σ_k |μ_k|²       incoherent / energy (phase-blind)

Coherent is optimal IFF the per-class relative phase (wedge) is known
and the classes are aligned. When the wedge is large (over-coupled
regime) and treated as a nuisance, the naive coherent combine suffers
the destructive cross-term while the incoherent combine is robust.

A third, fully-informed detector uses the per-class phase as a known
(ensemble-stable) parameter and combines coherently after de-rotation:

  T_wedge = |Σ_k μ_k · e^{-i φ̂_k}|²   wedge-corrected coherent (oracle/GLRT)

φ̂_k is the ensemble per-class mean angle (estimated from training seeds;
here measured for an upper bound / oracle).

THE MISSING INGREDIENT is matched A=0 NULL cells. The random-phase
null E[|μ_k|²]=n_k is badly violated — switch events are strongly
phase-anti-correlated (per-seed |z_total|²=879 ≪ N_sw=2931), so the
true null floor must be measured empirically. S117 runs paired
(A=0.40 signal, A=0.00 null) cells across κ_C to calibrate both
detectors and compute their ROC/d′ across the ridge → over-coupled
transition.

Design
------
Grid: κ_C ∈ {0.30, 0.40, 0.50, 0.60, 0.70} × A ∈ {0.00, 0.40}
  κ_p = 0.30, ω_std = 0.07 fixed (= S113/S115/S116 protocol).
  32 seeds × 25 chunks × 1.01M steps per cell (10 cells).
  Independent seed namespaces for null vs signal (S103 rule:
  independent seeds for with/without conditions).

Each seed records the full per-chunk per-class decomposition:
  μ_k,chunk for k ∈ {att_lock, att_noise, rep_lock, rep_noise},
  c ∈ 0..24. The per-seed phasor μ_k = Σ_c μ_k,chunk; the per-chunk
  scatter calibrates the noise. Stored so the analyzer can build:
    - per-seed T_coh, T_incoh, T_wedge
    - null distributions from A=0 cells
    - ROC / AUC / d′ for each detector vs κ_C

Predictions
-----------
P1 (incoherent recovers over-coupled detection): d′(T_incoh) > d′(T_coh)
   for κ_C ≥ 0.50; the crossover sits near the ridge (κ_C ≈ 0.35-0.45).
P2 (coherent wins at ridge): at κ_C=0.30 the classes are mildly
   constructive (wedge ≈ 49°, cos>0) so d′(T_coh) ≥ d′(T_incoh).
P3 (wedge-corrected is the envelope): T_wedge ≥ max(T_coh, T_incoh)
   at every κ_C — coherent combine with known per-class phase is the
   matched-filter optimum; it should dominate both naive variants.
P4 (incoherent null penalty): the null mean of T_incoh exceeds the
   null mean of T_coh (4 noise floors vs 1) — the incoherent detector
   pays a noise tax that the over-coupled signal gain must overcome.
P5 (small-class contribution): att_noise + rep_lock fractions are
   small (~0.02 each past ridge); test whether dropping them
   (2-class incoherent: aL + rN only) matches or beats the 4-class
   incoherent — i.e., are the small classes pure noise tax?

Compute
-------
10 cells × 32 seeds × 1.01M steps × 25.7 µs ≈ 137 min on Thor.
"""
import json
import sys
import time
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_111_dose_response import (
    per_seed_R_coh,
    lock_modulation_at_fs,
    kura_modulation_at_fs,
)
from thor_session_112_omega_cliff import (
    OMEGA_OFFSETS_UNIT,
    build_omega,
    simulate_with_omega,
)
from thor_session_113_dip_decomposition import (
    per_switch_state,
    class_decompose,
)

C_THRESHOLD = 0.55
SIGNAL_FREQ = 0.003
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
T_CHUNK_S = CHUNK_STEPS * DT
N_SEEDS = 32
N_CHUNKS = 25
DEC_KURA = 10
LOCK_THR = 0.9

CLASSES = ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']


def per_chunk_class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw,
                              n_chunks=N_CHUNKS, chunk_steps=CHUNK_STEPS,
                              signal_freq=SIGNAL_FREQ, dt=DT, warmup=WARMUP):
    """Per-class, per-chunk complex matched-filter sums.

    sw_steps are post-warmup step indices. The signal phase uses the
    absolute time (sw_steps + warmup)·dt — same convention as
    class_decompose / switch_timing_IQ.

    Returns mu_kc: dict class -> complex array length n_chunks, plus
    cnt_kc: dict class -> int array length n_chunks (events per chunk).
    Summing over chunks reproduces the per-seed class_decompose μ_k.
    """
    masks = {
        'att_lock':  gate_at_sw & lock_at_sw,
        'att_noise': gate_at_sw & ~lock_at_sw,
        'rep_lock':  ~gate_at_sw & lock_at_sw,
        'rep_noise': ~gate_at_sw & ~lock_at_sw,
    }
    mu_kc = {k: np.zeros(n_chunks, dtype=complex) for k in CLASSES}
    cnt_kc = {k: np.zeros(n_chunks, dtype=int) for k in CLASSES}
    if len(sw_steps) == 0:
        return mu_kc, cnt_kc
    chunk_idx = np.minimum(sw_steps // chunk_steps, n_chunks - 1)
    abs_t = (sw_steps + warmup) * dt
    arg = 2.0 * np.pi * signal_freq * abs_t
    contrib = sw_dirs.astype(float) * (np.sin(arg) + 1j * np.cos(arg))
    for k in CLASSES:
        m = masks[k]
        if not m.any():
            continue
        ci = chunk_idx[m]
        co = contrib[m]
        # accumulate complex sums per chunk
        np.add.at(mu_kc[k], ci, co)
        np.add.at(cnt_kc[k], ci, 1)
    return mu_kc, cnt_kc


def run_cell(label, kappa_phase, kappa_C, omega_std, signal_amp, seed_base,
             n_chunks=N_CHUNKS, n_seeds=N_SEEDS, omega_base=0.1):
    omega_vec = build_omega(omega_base, omega_std)
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> {label}: κ_p={kappa_phase:.3f}  κ_C={kappa_C:.3f}  "
          f"ω_std={omega_std:.4f}  A={signal_amp:.4f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  steps={total_steps}  "
          f"seed_base={seed_base}")
    cell_start = time.time()
    seed_records = []
    for s in range(n_seeds):
        t0 = time.time()
        (Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
         sw_steps, sw_dirs, k_mean) = simulate_with_omega(
            N=4, noise_std=SIGMA_NOISE, steps=total_steps,
            seed=seed_base + s, omega=omega_vec,
            kappa_phase=kappa_phase, kappa_C=kappa_C,
            signal_freq=SIGNAL_FREQ, signal_amp=signal_amp, dt=DT)
        xp = Cm[WARMUP:]
        z_raw = np.zeros(n_chunks, dtype=complex)
        z_st = np.zeros(n_chunks, dtype=complex)
        n_sw_chunks = np.zeros(n_chunks, dtype=int)
        for c in range(n_chunks):
            chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
            t_off = WARMUP + c * CHUNK_STEPS
            Ir, Qr = phase_coherent_IQ(chunk, DT, SIGNAL_FREQ, t_offset=t_off)
            Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ,
                                          t_offset=t_off,
                                          threshold=C_THRESHOLD)
            z_raw[c] = Ir + 1j * Qr
            z_st[c] = Is + 1j * Qs
            n_sw_chunks[c] = n
        raw_st = per_seed_R_coh(z_raw)
        st_st = per_seed_R_coh(z_st)
        I_lock, Q_lock, mod_amp_lock, mod_arg_lock = lock_modulation_at_fs(
            kdec, spdec)
        kura_at_sw, gate_at_sw, lock_at_sw = per_switch_state(
            sw_steps, sw_dirs, kdec, gdec)
        decomp = class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw)
        mu_kc, cnt_kc = per_chunk_class_decompose(
            sw_steps, sw_dirs, gate_at_sw, lock_at_sw, n_chunks=n_chunks)
        # consistency: per-chunk sum == per-seed class μ
        chk = 0.0
        for k in CLASSES:
            mu_seed_k = mu_kc[k].sum()
            ref = complex(decomp['per_class'][k]['mu_re'],
                          decomp['per_class'][k]['mu_im'])
            chk = max(chk, abs(mu_seed_k - ref))
        rec = {
            'seed': seed_base + s,
            'z_st': z_st, 'n_sw_chunks': n_sw_chunks,
            'raw_per_seed': raw_st, 'st_per_seed': st_st,
            'kura_mean': k_mean,
            'lock_frac_global': float((kdec > LOCK_THR).mean()),
            'mod_amp_at_fs_lock': mod_amp_lock,
            'switch_total': int(len(sw_steps)),
            'lock_at_switch_frac': float(lock_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'gate_att_at_switch_frac': float(gate_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'class_decomp': decomp,
            'mu_kc': mu_kc,         # dict class -> complex[n_chunks]
            'cnt_kc': cnt_kc,       # dict class -> int[n_chunks]
            'per_chunk_chk': float(chk),
        }
        seed_records.append(rec)
        elapsed = time.time() - t0
        cls = decomp['per_class']
        T_coh = decomp['z_total_abs2']
        T_incoh = decomp['sum_class_sq']
        print(f"   seed={seed_base+s:9d} {elapsed:5.1f}s   "
              f"Nsw={len(sw_steps):5d}  R_k={k_mean:.3f}  "
              f"T_coh={T_coh:8.1f}  T_incoh={T_incoh:8.1f}  "
              f"ratio={T_incoh/T_coh if T_coh>0 else 0:5.2f}  chk={chk:.1e}")
    print(f"   total {time.time()-cell_start:.0f}s")
    return seed_records, omega_vec.tolist()


def summarize_cell(seed_records, signal_amp, kappa_phase, kappa_C, omega_std):
    n = len(seed_records)
    st_R = np.array([s['st_per_seed']['R_coh'] for s in seed_records])
    st_mu = np.array([s['st_per_seed']['mu_abs'] for s in seed_records])
    st_mu_arg = np.array([s['st_per_seed']['mu_arg_deg'] for s in seed_records])
    kura_mean_arr = np.array([s['kura_mean'] for s in seed_records])
    n_sw_total = np.array([s['switch_total'] for s in seed_records])
    lock_at_sw = np.array([s['lock_at_switch_frac'] for s in seed_records])

    T_coh = np.array([s['class_decomp']['z_total_abs2'] for s in seed_records])
    T_incoh = np.array([s['class_decomp']['sum_class_sq'] for s in seed_records])

    z_arg = np.exp(1j * np.deg2rad(st_mu_arg))
    R_ang = float(abs(z_arg.mean()))
    mean_arg = float(np.degrees(np.angle(z_arg.mean())))

    rho_sig = np.array([
        (abs(s['z_st'].mean())**2 / float(np.mean(s['n_sw_chunks'])))
        if np.mean(s['n_sw_chunks']) > 0 else 0.0
        for s in seed_records])

    class_agg = {}
    for k in CLASSES:
        mu_re = np.array([s['class_decomp']['per_class'][k]['mu_re'] for s in seed_records])
        mu_im = np.array([s['class_decomp']['per_class'][k]['mu_im'] for s in seed_records])
        cnt = np.array([s['class_decomp']['per_class'][k]['count'] for s in seed_records], float)
        mu_abs = np.sqrt(mu_re**2 + mu_im**2)
        mu_arg = np.degrees(np.arctan2(mu_im, mu_re))
        zc = np.exp(1j * np.deg2rad(mu_arg)).mean()
        sw_total = np.array([s['switch_total'] for s in seed_records], float)
        class_agg[k] = {
            'mu_abs_per_seed_mean': float(mu_abs.mean()),
            'mu_arg_per_seed_circmean_deg': float(np.degrees(np.angle(zc))),
            'mu_arg_R_seedpair': float(abs(zc)),
            'count_per_seed_mean': float(cnt.mean()),
            'fraction_of_sw': float(cnt.sum() / max(1, sw_total.sum())),
        }
    aL = class_agg['att_lock']['mu_arg_per_seed_circmean_deg']
    rN = class_agg['rep_noise']['mu_arg_per_seed_circmean_deg']
    wedge = abs(((aL - rN + 180.0) % 360.0) - 180.0)

    return {
        'signal_amp': signal_amp, 'kappa_phase': kappa_phase,
        'kappa_C': kappa_C, 'omega_std': omega_std, 'n_seeds': n,
        'st_R_coh_mean': float(st_R.mean()), 'st_R_coh_std': float(st_R.std()),
        'st_mu_mean': float(st_mu.mean()),
        'st_mu_arg_circmean_deg': mean_arg, 'st_mu_arg_R': R_ang,
        'kura_mean_mean': float(kura_mean_arr.mean()),
        'kura_mean_std': float(kura_mean_arr.std()),
        'rho_sig_st_mean': float(rho_sig.mean()), 'rho_sig_st_std': float(rho_sig.std()),
        'n_sw_total_mean': float(n_sw_total.mean()),
        'lock_at_switch_frac_mean': float(lock_at_sw.mean()),
        'T_coh_mean': float(T_coh.mean()), 'T_coh_std': float(T_coh.std()),
        'T_incoh_mean': float(T_incoh.mean()), 'T_incoh_std': float(T_incoh.std()),
        'wedge_aL_rN': float(wedge),
        'class_agg': class_agg,
    }


def pack_per_seed(seed_records):
    packed = []
    for s in seed_records:
        rec = {
            'seed': s['seed'],
            'z_st': [[float(z.real), float(z.imag)] for z in s['z_st']],
            'n_sw_chunks': s['n_sw_chunks'].tolist(),
            'raw_per_seed': s['raw_per_seed'], 'st_per_seed': s['st_per_seed'],
            'kura_mean': s['kura_mean'],
            'lock_frac_global': s['lock_frac_global'],
            'mod_amp_at_fs_lock': s['mod_amp_at_fs_lock'],
            'switch_total': s['switch_total'],
            'lock_at_switch_frac': s['lock_at_switch_frac'],
            'gate_att_at_switch_frac': s['gate_att_at_switch_frac'],
            'class_decomp': s['class_decomp'],
            'per_chunk_chk': s['per_chunk_chk'],
            'mu_kc': {k: [[float(z.real), float(z.imag)] for z in s['mu_kc'][k]]
                      for k in CLASSES},
            'cnt_kc': {k: s['cnt_kc'][k].tolist() for k in CLASSES},
        }
        packed.append(rec)
    return packed


def main():
    start = datetime.now()
    print("Thor Session #117: Coherent vs Incoherent Class Combining")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  chunk={CHUNK_STEPS}  "
          f"warmup={WARMUP}  {N_SEEDS} seeds × {N_CHUNKS} chunks  "
          f"κ_p=0.30 ω_std=0.07")

    KAPPA_P = 0.30
    OMEGA_STD = 0.07
    KC_VALS = [0.30, 0.40, 0.50, 0.60, 0.70]
    A_VALS = [0.00, 0.40]

    cells_def = []
    for kc in KC_VALS:
        for A in A_VALS:
            label = f'kc{int(round(kc*100)):03d}_A{int(round(A*100)):03d}'
            cells_def.append((label, kc, A))

    meta = {
        'session': 117,
        'title': 'Coherent vs Incoherent Class Combining',
        'started': start.isoformat(),
        'common_params': {
            'sigma': SIGMA_NOISE, 'dt': DT, 'signal_freq': SIGNAL_FREQ,
            'C_threshold': C_THRESHOLD, 'warmup': WARMUP,
            'chunk_steps': CHUNK_STEPS, 'T_chunk_s': T_CHUNK_S,
            'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
            'dec_kura': DEC_KURA, 'lock_thr': LOCK_THR,
            'kappa_phase': KAPPA_P, 'omega_std': OMEGA_STD, 'omega_base': 0.1,
            'omega_offsets_unit': OMEGA_OFFSETS_UNIT.tolist(),
        },
        'cells_def': cells_def, 'kc_vals': KC_VALS, 'A_vals': A_VALS,
    }

    out_path = 'thor_session_117_class_detector_results.json'

    def checkpoint(cell_results, done):
        """Write results so far — a crash mid-run loses at most one cell."""
        meta_now = dict(meta)
        meta_now['cells_completed'] = done
        meta_now['n_cells_total'] = len(cells_def)
        with open(out_path, 'w') as f:
            json.dump({'meta': meta_now, 'cells': cell_results}, f,
                      indent=2, default=float)

    cell_results = {}
    for ci, (label, kc, A) in enumerate(cells_def):
        # distinct namespace; null (A=0) offset by +900_000 from signal
        seed_base = (117_000_000
                     + int(round(kc * 100)) * 100_000
                     + int(round(A * 100)) * 1000
                     + (900_000 if A == 0.0 else 0))
        seed_records, omega_vec = run_cell(
            label, KAPPA_P, kc, OMEGA_STD, A, seed_base)
        summary = summarize_cell(seed_records, A, KAPPA_P, kc, OMEGA_STD)
        ca = summary['class_agg']
        print(f"\n   ⇒ {label}: κ_C={kc:.2f} A={A:.2f}  "
              f"R_kura={summary['kura_mean_mean']:.3f}  "
              f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
              f"wedge={summary['wedge_aL_rN']:.0f}°  "
              f"<Nsw>={summary['n_sw_total_mean']:.0f}")
        print(f"      T_coh={summary['T_coh_mean']:.1f}±{summary['T_coh_std']:.1f}  "
              f"T_incoh={summary['T_incoh_mean']:.1f}±{summary['T_incoh_std']:.1f}")
        print(f"      class |μ|: aL={ca['att_lock']['mu_abs_per_seed_mean']:5.1f} "
              f"aN={ca['att_noise']['mu_abs_per_seed_mean']:5.1f} "
              f"rL={ca['rep_lock']['mu_abs_per_seed_mean']:5.1f} "
              f"rN={ca['rep_noise']['mu_abs_per_seed_mean']:5.1f}  "
              f"frac aL={ca['att_lock']['fraction_of_sw']:.2f} "
              f"rN={ca['rep_noise']['fraction_of_sw']:.2f}")
        cell_results[label] = {
            'kappa_phase': KAPPA_P, 'kappa_C': kc, 'omega_std': OMEGA_STD,
            'omega_vec': omega_vec, 'signal_amp': A, 'seed_base': seed_base,
            'summary': summary, 'per_seed': pack_per_seed(seed_records),
        }
        checkpoint(cell_results, ci + 1)
        print(f"   [checkpoint] {ci+1}/{len(cells_def)} cells written → {out_path}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_117_class_detector_results.json")


if __name__ == '__main__':
    main()
