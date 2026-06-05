#!/usr/bin/env python3
"""Thor Session #116: Past-Ridge κ_C — Signal Rescue and aL_arg Beyond −96°
==========================================================================

Context (S115-P4, S115-P5)
--------------------------
S115 mapped the wedge mechanism vs κ_C at κ_p=0.30 ω_std=0.07:
  κ_C ≤ 0.10   → un-formed (classes co-rotate, wedge ~0°)
  κ_C ∈ [0.25, 0.35] → A-modulated (wedge peaks at A=0.40 — dip regime)
  κ_C ≥ 0.40   → saturated (wedge flat at ~57° in A)

Two open S115 predictions point past the ridge:
  P4: att_lock saturation arg rotates monotonically with κ_C
      −110° (kc=0.05) → −86° (kc=0.40). Predict crosses 0° at κ_C≈0.55.
      Falsified geometric "−96° signal-min asymptote invariant" (S114-P4).
  P5: at κ_C=0.40, R_kura is depressed (0.43→0.49→0.52 across A∈{0.30..0.50}).
      Signal RESCUES dynamics from over-coupled collapse.
      Predict ρ_sig(A) is STEEPER at higher κ_C past saturation.

Smoke test (200k step, single seed) at κ_p=0.30 ω_std=0.07:
   κ_C  A=0.30 R_kura  A=0.50 R_kura   ΔR_kura
   0.40   0.448           0.540          +0.092
   0.50   0.378           0.491          +0.113
   0.60   0.353           0.456          +0.103
   0.70   0.298           0.479          +0.181 ← strongest rescue
Signal-rescue magnitude monotone in κ_C — confirms P5 direction at smoke scale.

Question
--------
What is the structure of detection past the wedge-ridge? Does the system
fail gradually (over-collapse dominates) or transition to a distinct
"signal-driven" regime where ρ_sig recovers via the rescue mechanism?

Design
------
Grid: 3 NEW κ_C × 4 A (12 cells) + 1 anchor cell (κ_C=0.40, A=0.60).
  κ_C ∈ {0.50, 0.60, 0.70}   (past-ridge / over-collapsed)
  A   ∈ {0.30, 0.40, 0.50, 0.60}  (extended past S115's A=0.50)
  Anchor: κ_C=0.40 A=0.60 (extends S115 κ_C=0.40 row for slope-vs-A test)
  ω fixed at offsets {−3,−1,1,3}/√5 · ω_std=0.07 (well below ω cliff).
  κ_p = 0.30 fixed.
  16 seeds × 25 chunks × 1.01M steps.

For continuity with S115 (which has κ_C=0.40 at A∈{0.30, 0.40, 0.50})
and S113 (which has κ_C=0.30 at A∈{0.30, 0.40, 0.50}), the analyzer
will splice those rows in.

Each cell records the same observables as S115:
  - per-seed z_st, z_raw → R_coh, mu, sigma_n, mu_arg
  - per-seed lock_at_switch_frac, gate_att_at_switch_frac
  - per-seed class decomposition (att_lock, att_noise, rep_lock, rep_noise)
  - mod_amp_at_fs_lock, mod_amp_at_fs_kura
  - R_kura mean (for the signal-rescue measurement)

Compute: 13 × 16 × 1.01M × 25 µs ≈ 88 min.

Predictions
-----------
P1 (signal-rescue slope dR_kura/dA monotone in κ_C):
  ΔR_kura(A=0.30→0.60) at κ_C=0.40 vs 0.50 vs 0.60 vs 0.70 — grows.

P2 (aL_arg rotation continues past −86°):
  At A=0.40, aL_arg vs κ_C extends the S115 sequence
     0.05:-110, 0.15:-107, 0.25:-101, 0.30:-98, 0.40:-87.
  Predict κ_C=0.50: ~-65°, κ_C=0.60: ~-40°, κ_C=0.70: ~-15°.
  The S115-P4 prediction "crosses 0° at κ_C ≈ 0.55" is aggressive
  (rotation rate at κ_C=0.40 is 110°/unit, not yet at the rate to
  reach 0° by κ_C=0.55). My competing prediction: crossing at
  κ_C ≈ 0.70-0.80.

P3 (ρ_sig recovery with A in over-collapsed regime):
  At κ_C=0.60, 0.70 ρ_sig(A=0.30) low (~0.03-0.05); at A=0.60 it
  recovers toward 0.10-0.15. dρ_sig/dA grows with κ_C — bigger in
  over-collapsed regime than at the ridge.

P4 (lock@sw saturates as κ_C → ∞):
  S115 lock@sw at A=0.40: 0.26→0.36→0.50→0.55→0.64 (κ_C 0.05→0.40).
  Predict lock@sw asymptotes near 1.0 at κ_C ≳ 0.70.

P5 (wedge maintains saturation OR collapses):
  Past-saturation wedge could (a) stay at ~57° (geometric ceiling
  hypothesis), (b) shrink as classes merge (over-collapse hypothesis),
  or (c) WIDEN past 90° to point classes into anti-phase (decoupled
  hypothesis). Smoke data hints at decoupled story: at κ_C=0.70 the
  N_sw is much reduced, suggesting fewer events per class.

P6 (mod_amp_at_fs_lock vs A):
  At over-collapsed κ_C, the bistable system might lose its A-driven
  modulation of R_kura at f_s. Predict mod_amp grows with A at all
  κ_C, but saturates faster at higher κ_C (less dynamic range).

Failure modes
-------------
- If at κ_C=0.70 the system becomes fully phase-locked (R_kura
  saturates near 1.0 regardless of A), n_sw collapses and detection
  becomes pure-signal direct via threshold modulation, similar to
  S112's past-cliff residual ρ_sig ≈ 0.08.
- If at κ_C=0.70 the dynamics become noise-dominated (R_kura → low),
  switches become Poisson-like and ρ_sig drops to near-floor.
- Either outcome IS informative: it bounds the operational regime
  of the wedge mechanism and characterizes the over-collapsed limit.
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
    first_principles_z_st,
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
N_SEEDS = 16
N_CHUNKS = 25
DEC_KURA = 10
LOCK_THR = 0.9


def run_cell(label, kappa_phase, kappa_C, omega_std, signal_amp, seed_base,
             n_chunks=N_CHUNKS, n_seeds=N_SEEDS, omega_base=0.1):
    omega_vec = build_omega(omega_base, omega_std)
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> {label}: κ_p={kappa_phase:.3f}  κ_C={kappa_C:.3f}  "
          f"ω_std={omega_std:.4f}  ω={np.round(omega_vec,4).tolist()}  "
          f"A={signal_amp:.4f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  steps={total_steps}")
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
        I_kura, Q_kura, mod_amp_kura, mod_arg_kura = kura_modulation_at_fs(
            kdec, spdec)
        kura_at_sw, gate_at_sw, lock_at_sw = per_switch_state(
            sw_steps, sw_dirs, kdec, gdec)
        decomp = class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw)
        rec = {
            'seed': seed_base + s,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw_chunks': n_sw_chunks,
            'raw_per_seed': raw_st, 'st_per_seed': st_st,
            'kura_mean': k_mean,
            'lock_frac_global': float((kdec > LOCK_THR).mean()),
            'mod_amp_at_fs_lock': mod_amp_lock,
            'mod_arg_at_fs_lock_deg': mod_arg_lock,
            'mod_amp_at_fs_kura': mod_amp_kura,
            'mod_arg_at_fs_kura_deg': mod_arg_kura,
            'switch_total': int(len(sw_steps)),
            'lock_at_switch_frac': float(lock_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'gate_att_at_switch_frac': float(gate_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'kura_at_switch_mean': float(kura_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'class_decomp': decomp,
        }
        seed_records.append(rec)
        elapsed = time.time() - t0
        cls = decomp['per_class']
        print(f"   seed={seed_base+s:9d} {elapsed:5.1f}s   "
              f"|<z_st>|={abs(z_st.mean()):.3f}  arg={np.degrees(np.angle(z_st.mean())):+6.1f}°  "
              f"R_k={k_mean:.3f}  "
              f"lock@sw={float(lock_at_sw.mean()) if len(sw_steps)>0 else 0:.2f}  "
              f"Nsw={len(sw_steps)}  "
              f"|μ| aL={cls['att_lock']['mu_abs']:5.1f} "
              f"aN={cls['att_noise']['mu_abs']:5.1f} "
              f"rL={cls['rep_lock']['mu_abs']:5.1f} "
              f"rN={cls['rep_noise']['mu_abs']:5.1f}")
    print(f"   total {time.time()-cell_start:.0f}s")
    return seed_records, omega_vec.tolist()


def summarize_cell(seed_records, signal_amp, kappa_phase, kappa_C, omega_std):
    n = len(seed_records)
    raw_R = np.array([s['raw_per_seed']['R_coh'] for s in seed_records])
    st_R = np.array([s['st_per_seed']['R_coh'] for s in seed_records])
    raw_mu = np.array([s['raw_per_seed']['mu_abs'] for s in seed_records])
    st_mu = np.array([s['st_per_seed']['mu_abs'] for s in seed_records])
    st_mu_arg = np.array([s['st_per_seed']['mu_arg_deg'] for s in seed_records])
    st_sigma_n = np.array([s['st_per_seed']['sigma_n'] for s in seed_records])
    mod_lock = np.array([s['mod_amp_at_fs_lock'] for s in seed_records])
    mod_kura = np.array([s['mod_amp_at_fs_kura'] for s in seed_records])
    lock_global = np.array([s['lock_frac_global'] for s in seed_records])
    kura_mean_arr = np.array([s['kura_mean'] for s in seed_records])
    n_sw_total = np.array([s['switch_total'] for s in seed_records])
    lock_at_sw = np.array([s['lock_at_switch_frac'] for s in seed_records])
    att_at_sw = np.array([s['gate_att_at_switch_frac'] for s in seed_records])

    z_arg = np.exp(1j * np.deg2rad(st_mu_arg))
    R_ang = float(abs(z_arg.mean()))
    mean_arg = float(np.degrees(np.angle(z_arg.mean())))

    rho_sig = []
    for s in seed_records:
        mu2 = abs(s['z_st'].mean())**2
        nsw = float(np.mean(s['n_sw_chunks']))
        rho_sig.append(mu2 / nsw if nsw > 0 else 0.0)
    rho_sig = np.array(rho_sig)

    classes = ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
    class_agg = {}
    for k in classes:
        mu_re = np.array([s['class_decomp']['per_class'][k]['mu_re']
                          for s in seed_records])
        mu_im = np.array([s['class_decomp']['per_class'][k]['mu_im']
                          for s in seed_records])
        cnt = np.array([s['class_decomp']['per_class'][k]['count']
                        for s in seed_records], dtype=float)
        mu_abs_per_seed = np.sqrt(mu_re**2 + mu_im**2)
        mu_arg_per_seed = np.degrees(np.arctan2(mu_im, mu_re))
        z_class = np.exp(1j * np.deg2rad(mu_arg_per_seed))
        z_class_mean = z_class.mean()
        sw_total_arr = np.array([s['switch_total'] for s in seed_records],
                                 dtype=float)
        class_agg[k] = {
            'mu_abs_per_seed_mean': float(mu_abs_per_seed.mean()),
            'mu_abs_per_seed_std': float(mu_abs_per_seed.std()),
            'mu_arg_per_seed_circmean_deg': float(np.degrees(np.angle(z_class_mean))),
            'mu_arg_R_seedpair': float(abs(z_class_mean)),
            'count_per_seed_mean': float(cnt.mean()),
            'fraction_of_sw': float(cnt.sum() / max(1, sw_total_arr.sum())),
        }

    cross_keys = list(seed_records[0]['class_decomp']['cross_terms'].keys())
    cross_agg = {}
    for ck in cross_keys:
        vals = np.array([s['class_decomp']['cross_terms'][ck]
                         for s in seed_records])
        cross_agg[ck] = {
            'mean': float(vals.mean()),
            'std': float(vals.std()),
        }

    return {
        'signal_amp': signal_amp,
        'kappa_phase': kappa_phase,
        'kappa_C': kappa_C,
        'omega_std': omega_std,
        'n_seeds': n,
        'raw_R_coh_mean': float(raw_R.mean()),
        'raw_R_coh_std':  float(raw_R.std()),
        'st_R_coh_mean':  float(st_R.mean()),
        'st_R_coh_std':   float(st_R.std()),
        'raw_mu_mean':    float(raw_mu.mean()),
        'st_mu_mean':     float(st_mu.mean()),
        'st_mu_std':      float(st_mu.std()),
        'st_mu_arg_circmean_deg': mean_arg,
        'st_mu_arg_R':    R_ang,
        'st_sigma_n_mean': float(st_sigma_n.mean()),
        'mod_amp_at_fs_lock_mean': float(mod_lock.mean()),
        'mod_amp_at_fs_lock_std':  float(mod_lock.std()),
        'mod_amp_at_fs_kura_mean': float(mod_kura.mean()),
        'mod_amp_at_fs_kura_std':  float(mod_kura.std()),
        'lock_frac_global_mean': float(lock_global.mean()),
        'kura_mean_mean': float(kura_mean_arr.mean()),
        'kura_mean_std':  float(kura_mean_arr.std()),
        'rho_sig_st_mean': float(rho_sig.mean()),
        'rho_sig_st_std':  float(rho_sig.std()),
        'rho_sig_st_sem':  float(rho_sig.std() / np.sqrt(max(1, n))),
        'n_sw_total_mean': float(n_sw_total.mean()),
        'n_sw_total_std':  float(n_sw_total.std()),
        'lock_at_switch_frac_mean': float(lock_at_sw.mean()),
        'lock_at_switch_frac_std': float(lock_at_sw.std()),
        'gate_att_at_switch_frac_mean': float(att_at_sw.mean()),
        'class_agg': class_agg,
        'cross_agg': cross_agg,
    }


def pack_per_seed(seed_records):
    return [{
        'seed': s['seed'],
        'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
        'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
        'n_sw_chunks': s['n_sw_chunks'].tolist(),
        'raw_per_seed': s['raw_per_seed'],
        'st_per_seed': s['st_per_seed'],
        'kura_mean': s['kura_mean'],
        'lock_frac_global': s['lock_frac_global'],
        'mod_amp_at_fs_lock': s['mod_amp_at_fs_lock'],
        'mod_arg_at_fs_lock_deg': s['mod_arg_at_fs_lock_deg'],
        'mod_amp_at_fs_kura': s['mod_amp_at_fs_kura'],
        'mod_arg_at_fs_kura_deg': s['mod_arg_at_fs_kura_deg'],
        'switch_total': s['switch_total'],
        'lock_at_switch_frac': s['lock_at_switch_frac'],
        'gate_att_at_switch_frac': s['gate_att_at_switch_frac'],
        'kura_at_switch_mean': s['kura_at_switch_mean'],
        'class_decomp': s['class_decomp'],
    } for s in seed_records]


def main():
    start = datetime.now()
    print("Thor Session #116: Past-Ridge κ_C — Signal Rescue and aL_arg Beyond −96°")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"chunk={CHUNK_STEPS} steps  T_chunk={T_CHUNK_S}s  "
          f"warmup={WARMUP}  decimate={DEC_KURA}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks  "
          f"κ_p=0.30, ω_std=0.07 fixed; sweep (κ_C, A)")

    KAPPA_P = 0.30
    OMEGA_STD = 0.07

    # κ_C × A grid for past-ridge regime
    # κ_C=0.40 line is recycled from S115 (A∈{0.30, 0.40, 0.50}); add A=0.60 anchor here
    primary_kc = [0.50, 0.60, 0.70]
    primary_A = [0.30, 0.40, 0.50, 0.60]
    anchor_cells = [(0.40, 0.60)]  # extends S115 κ_C=0.40 row for slope-vs-A

    cells_def = []
    for kc in primary_kc:
        for A in primary_A:
            label = f'kc{int(round(kc*100)):03d}_A{int(round(A*100)):03d}'
            cells_def.append((label, kc, A))
    for kc, A in anchor_cells:
        label = f'kc{int(round(kc*100)):03d}_A{int(round(A*100)):03d}'
        cells_def.append((label, kc, A))

    cells = []
    for label, kc, A in cells_def:
        # Distinct seed namespace from prior sessions
        seed_base = (116_000_000
                     + int(round(kc * 100)) * 100_000
                     + int(round(A * 100)) * 1000)
        cells.append({
            'label': label,
            'kappa_phase': KAPPA_P, 'kappa_C': kc,
            'omega_std': OMEGA_STD, 'signal_amp': A,
            'seed_base': seed_base,
        })

    cell_results = {}
    for cd in cells:
        seed_records, omega_vec = run_cell(
            cd['label'], cd['kappa_phase'], cd['kappa_C'],
            cd['omega_std'], cd['signal_amp'], cd['seed_base'])
        summary = summarize_cell(seed_records, cd['signal_amp'],
                                 cd['kappa_phase'], cd['kappa_C'],
                                 cd['omega_std'])
        ca = summary['class_agg']
        print(f"\n   ⇒ {cd['label']}: κ_C={cd['kappa_C']:.2f}  "
              f"A={cd['signal_amp']:.2f}  "
              f"R_kura={summary['kura_mean_mean']:.3f}  "
              f"lock_frac={summary['lock_frac_global_mean']:.3f}  "
              f"lock@sw={summary['lock_at_switch_frac_mean']:.3f}  "
              f"|μ_st|={summary['st_mu_mean']:.2f}  "
              f"arg={summary['st_mu_arg_circmean_deg']:+6.1f}°  "
              f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
              f"<Nsw>={summary['n_sw_total_mean']:.0f}")
        print(f"      class |μ| mean: aL={ca['att_lock']['mu_abs_per_seed_mean']:5.1f} "
              f"aN={ca['att_noise']['mu_abs_per_seed_mean']:5.1f} "
              f"rL={ca['rep_lock']['mu_abs_per_seed_mean']:5.1f} "
              f"rN={ca['rep_noise']['mu_abs_per_seed_mean']:5.1f}")
        print(f"      class ⟨arg⟩: aL={ca['att_lock']['mu_arg_per_seed_circmean_deg']:+6.1f}° "
              f"aN={ca['att_noise']['mu_arg_per_seed_circmean_deg']:+6.1f}° "
              f"rL={ca['rep_lock']['mu_arg_per_seed_circmean_deg']:+6.1f}° "
              f"rN={ca['rep_noise']['mu_arg_per_seed_circmean_deg']:+6.1f}°")
        print(f"      class fraction: aL={ca['att_lock']['fraction_of_sw']:.3f} "
              f"aN={ca['att_noise']['fraction_of_sw']:.3f} "
              f"rL={ca['rep_lock']['fraction_of_sw']:.3f} "
              f"rN={ca['rep_noise']['fraction_of_sw']:.3f}")
        cell_results[cd['label']] = {
            'kappa_phase': cd['kappa_phase'],
            'kappa_C': cd['kappa_C'],
            'omega_std': cd['omega_std'],
            'omega_vec': omega_vec,
            'signal_amp': cd['signal_amp'],
            'seed_base': cd['seed_base'],
            'summary': summary,
            'per_seed': pack_per_seed(seed_records),
        }

    out = {
        'meta': {
            'session': 116,
            'title': 'Past-Ridge κ_C — Signal Rescue and aL_arg Beyond −96°',
            'started': start.isoformat(),
            'common_params': {
                'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'dec_kura': DEC_KURA, 'lock_thr': LOCK_THR,
                'kappa_phase': KAPPA_P,
                'omega_std': OMEGA_STD,
                'omega_base': 0.1,
                'omega_offsets_unit': OMEGA_OFFSETS_UNIT.tolist(),
            },
            'cells_def': cells_def,
            'kc_primary': primary_kc,
            'A_primary': primary_A,
            'anchor_cells': anchor_cells,
        },
        'cells': cell_results,
    }
    with open('thor_session_116_past_ridge_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_116_past_ridge_results.json")


if __name__ == '__main__':
    main()
