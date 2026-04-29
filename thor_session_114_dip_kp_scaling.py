#!/usr/bin/env python3
"""Thor Session #114: Dip-A vs κ_p — Att_lock Saturation as Kuramoto-Timescale-Gated
=====================================================================================

Context (S113)
--------------
S113 closed the A=0.40 dip at the ridge (κ_p=0.30, κ_C=0.30, ω_std=0.07,
ratio ω_std/κ_p = 0.233):

   ρ_sig(A) peak 0.141 at A=0.35, dips 0.137 at A=0.40 (3% drop), recovers
   to 0.147 at A=0.45 and 0.161 at A=0.50.

Mechanism: switches partition into 4 classes by (gate × R_kura > 0.9) at
switch time. By A ≥ 0.30, two classes (att_lock, rep_noise) carry ≥87% of
events. Each class's complex MF sum has its own arg, which rotates with A:

   att_lock arg : −157° → −96° (saturates near A=0.35, signal-min asymptote)
   rep_noise arg: +175° → −136° (monotone toward signal-max asymptote)

The dip arises because the wedge between the two dominant classes (att_lock,
rep_noise) widens to its maximum 49° at A=0.40, then narrows again. The
2 |μ_aL| |μ_rN| cos(Δφ) cross-term tracks the dip with 11% drop.

S113-P1: dip-A scales with κ_p
------------------------------
Theoretical argument: the att_lock saturation locus is set by the balance
between Kuramoto coupling K=κ_p (which keeps locked oscillators near a
common phase) and the signal force A (which biases that phase toward the
signal-min). At lock equilibrium Δφ ~ A/K saturates as A grows beyond K.

Therefore the saturation amplitude A_sat ∝ K = κ_p, and the dip-A — set by
the A at which arg(μ_aL) plateaus and arg(μ_rN) is still rotating — also
scales with κ_p.

Concrete prediction: dip-A(κ_p) = dip-A(κ_p=0.30) · (κ_p / 0.30)
   κ_p = 0.10 → dip-A ≈ 0.13
   κ_p = 0.50 → dip-A ≈ 0.67

Design
------
Hold ratio ω_std/κ_p = 0.233 to keep the system in the same phase-locking
regime across κ_p (avoiding any Kuramoto-cliff confound):
   κ_p = 0.10, ω_std = 0.0233   (cliff at πK/4 = 0.0785; well below)
   κ_p = 0.30, ω_std = 0.07     (S113 baseline; recycled)
   κ_p = 0.50, ω_std = 0.117    (cliff at πK/4 = 0.392; well below)

For each κ_p we run a fine A grid bracketing the predicted dip-A. The
analyzer (S114-analyze.py) extracts per-cell ρ_sig and per-class arg, and
fits A* (peak), dip-A, and the signal-min asymptote arg(μ_aL,sat).

A grids:
  κ_p=0.10: A ∈ {0.05, 0.10, 0.13, 0.16, 0.20, 0.30}    [6 cells]
  κ_p=0.30: recycle S113 — A ∈ {0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50}
  κ_p=0.50: A ∈ {0.40, 0.55, 0.65, 0.70, 0.80, 0.95}    [6 cells]

12 new cells × 16 seeds × 25 chunks × 1.01M steps × 25 µs/step ≈ 81 min.

Predictions
-----------
P1 (linear scaling): dip-A ∝ κ_p. Predicted dip-A: 0.13 (κ_p=0.10), 0.40
   (κ_p=0.30), 0.67 (κ_p=0.50). Linear regression slope ≈ 1.33 (i.e.
   dip-A = (4/3) · κ_p), intercept ≈ 0.

P2 (att_lock saturation arg invariant): arg(μ_aL) plateaus at the same
   geometric signal-min asymptote (~−96°) at high A regardless of κ_p.
   The A at which it saturates shifts, the saturated value does not.

P3 (rep_noise rotation rate per unit A inversely scales with κ_p):
   d(arg(μ_rN))/dA scales as 1/κ_p — rep_noise rotates faster (per unit A)
   at lower κ_p because the noise-driven channel sees no Kuramoto
   restoring force.

P4 (peak ρ_sig also shifts): at lower κ_p, the maximum-detection-power A
   shifts proportionally with dip-A (peak is just before dip). Predict A*
   peak at A ≈ 0.10 for κ_p=0.10 (S111-P1 also predicted 1/κ_p).

P5 (dip magnitude): the wedge-cross-term mechanism predicts a dip of
   similar relative magnitude (~3–5%) at all three κ_p, but the absolute
   ρ_sig at the dip drops with κ_p (ridge is ~linearly κ_p-dependent —
   see S107 +1.02 slope).

P6 (failure mode): if dip is absent at κ_p=0.10 — say, lock is so weak
   that att_lock class does not coexist with rep_noise — then the
   two-mechanism cross-term mechanism is regime-specific, and the
   "scales with κ_p" prediction is moot.
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
          f"ω_std={omega_std:.4f}  ratio={omega_std/kappa_phase:.3f}  "
          f"ω={np.round(omega_vec,4).tolist()}  A={signal_amp:.4f}  "
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


def summarize_cell(seed_records, signal_amp, kappa_phase, omega_std):
    n = len(seed_records)
    raw_R = np.array([s['raw_per_seed']['R_coh'] for s in seed_records])
    st_R = np.array([s['st_per_seed']['R_coh'] for s in seed_records])
    raw_mu = np.array([s['raw_per_seed']['mu_abs'] for s in seed_records])
    st_mu = np.array([s['st_per_seed']['mu_abs'] for s in seed_records])
    st_mu_arg = np.array([s['st_per_seed']['mu_arg_deg'] for s in seed_records])
    st_sigma_n = np.array([s['st_per_seed']['sigma_n'] for s in seed_records])
    mod_lock = np.array([s['mod_amp_at_fs_lock'] for s in seed_records])
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
        class_agg[k] = {
            'mu_abs_per_seed_mean': float(mu_abs_per_seed.mean()),
            'mu_abs_per_seed_std': float(mu_abs_per_seed.std()),
            'mu_arg_per_seed_circmean_deg': float(np.degrees(np.angle(z_class_mean))),
            'mu_arg_R_seedpair': float(abs(z_class_mean)),
            'count_per_seed_mean': float(cnt.mean()),
            'fraction_of_sw': float(cnt.sum() / max(1, sum(np.array(
                [s['switch_total'] for s in seed_records])))),
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
        'lock_frac_global_mean': float(lock_global.mean()),
        'kura_mean_mean': float(kura_mean_arr.mean()),
        'rho_sig_st_mean': float(rho_sig.mean()),
        'rho_sig_st_std':  float(rho_sig.std()),
        'rho_sig_st_sem':  float(rho_sig.std() / np.sqrt(max(1, n))),
        'n_sw_total_mean': float(n_sw_total.mean()),
        'lock_at_switch_frac_mean': float(lock_at_sw.mean()),
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
    print("Thor Session #114: Dip-A vs κ_p (att_lock saturation scaling)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"chunk={CHUNK_STEPS} steps  T_chunk={T_CHUNK_S}s  "
          f"warmup={WARMUP}  decimate={DEC_KURA}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks  "
          f"ratio ω_std/κ_p = 0.233 held fixed")

    KAPPA_C = 0.30
    RATIO = 0.233   # S113 baseline

    # Two new κ_p values bracketing S113's 0.30. ω_std = ratio · κ_p.
    # A grids bracket predicted dip-A ≈ 0.40 · (κ_p / 0.30).
    cells_def = [
        # κ_p = 0.10  ω_std = 0.0233   predicted dip-A ≈ 0.13
        ('kp010_A005', 0.10, 0.0233, 0.05),
        ('kp010_A010', 0.10, 0.0233, 0.10),
        ('kp010_A013', 0.10, 0.0233, 0.13),
        ('kp010_A016', 0.10, 0.0233, 0.16),
        ('kp010_A020', 0.10, 0.0233, 0.20),
        ('kp010_A030', 0.10, 0.0233, 0.30),
        # κ_p = 0.50  ω_std = 0.117    predicted dip-A ≈ 0.67
        ('kp050_A040', 0.50, 0.117,  0.40),
        ('kp050_A055', 0.50, 0.117,  0.55),
        ('kp050_A065', 0.50, 0.117,  0.65),
        ('kp050_A070', 0.50, 0.117,  0.70),
        ('kp050_A080', 0.50, 0.117,  0.80),
        ('kp050_A095', 0.50, 0.117,  0.95),
    ]

    cells = []
    for label, kp, omega_std, A in cells_def:
        seed_base = 114_000_000 + int(round(kp * 100)) * 100_000 + int(round(A * 100)) * 1000
        cells.append({
            'label': label,
            'kappa_phase': kp, 'kappa_C': KAPPA_C,
            'omega_std': omega_std, 'signal_amp': A,
            'seed_base': seed_base,
        })

    cell_results = {}
    for cd in cells:
        seed_records, omega_vec = run_cell(
            cd['label'], cd['kappa_phase'], cd['kappa_C'],
            cd['omega_std'], cd['signal_amp'], cd['seed_base'])
        summary = summarize_cell(seed_records, cd['signal_amp'],
                                 cd['kappa_phase'], cd['omega_std'])
        ca = summary['class_agg']
        print(f"\n   ⇒ {cd['label']}: κ_p={cd['kappa_phase']:.2f}  "
              f"A={cd['signal_amp']:.2f}  "
              f"R_kura={summary['kura_mean_mean']:.3f}  "
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
            'session': 114,
            'title': 'Dip-A vs κ_p (att_lock saturation scaling)',
            'started': start.isoformat(),
            'common_params': {
                'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'dec_kura': DEC_KURA, 'lock_thr': LOCK_THR,
                'kappa_C': KAPPA_C, 'ratio_omegastd_over_kp': 0.233,
                'omega_base': 0.1,
                'omega_offsets_unit': OMEGA_OFFSETS_UNIT.tolist(),
            },
            'cells_def': cells_def,
        },
        'cells': cell_results,
    }
    with open('thor_session_114_dip_kp_scaling_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_114_dip_kp_scaling_results.json")


if __name__ == '__main__':
    main()
