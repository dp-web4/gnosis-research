#!/usr/bin/env python3
"""Thor Session #113: The A=0.40 Dip — Mechanism via Switch-Class Decomposition
================================================================================

Context (S111 + S112)
---------------------
S111 found ρ_sig non-monotonic in A at the ridge (κ_p=0.30, κ_C=0.30,
ratio 0.8): peak 0.154 at A=0.20, dip to 0.128 at A=0.40, recovery to
0.203 at A=0.50.  S112 attributed the A=0.50 high seed variance to a
within-seed Kuramoto cliff at ω_std ≈ 0.17, but FOUND that the
A=0.30→0.40 dip survives ω-cliff filtering: succ-only ρ_sig at A=0.20,
0.30, 0.40 is 0.146, 0.152, 0.132 — a real 13% drop.

Re-analysis of the S111 data shows the matched-filter angle ROTATES:
  A=0.05 → −121°
  A=0.10 → −127°
  A=0.20 → −126°    (peak ρ_sig)
  A=0.30 → −119°
  A=0.40 → −109°    (dip)
  A=0.50 → −115°

A 17° rotation between peak and dip strongly suggests two switch sub-
populations with distinct phases interfere destructively at A=0.40.

Hypothesis: switches divide into 4 classes by (gate_state × lock_state)
at switch time:
  - gate=attractive · lock-on   ("att·lock")
  - gate=attractive · lock-off  ("att·noise")
  - gate=repulsive · lock-on    ("rep·lock")  (rare; gate just flipped)
  - gate=repulsive · lock-off   ("rep·noise")

Each class has its own complex matched-filter sum μ_class. The total
satisfies μ_total = Σ μ_class.  ρ_sig = |μ_total|² / N_sw_total.

When A is such that |μ_class|² · phase-alignment of classes is maximal,
ρ_sig peaks. When A causes class weights to shift such that the two
strongest classes are π/2 (or π) apart, |μ_total|² drops below the
class-square sum: destructive interference.

S112-P6 prediction: at A=0.40 the cross-term Re(μ_a · conj(μ_b)) for
the two strongest classes is more negative than at A=0.20 or A=0.50.

Design
------
Fixed ω with ω_std=0.07 (well below cliff, S112's mild-heterogeneity
sweet spot, +17% gain over ω_std=0.03). 16 seeds × 25 chunks at the
ridge geometry. A ∈ {0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50}.

Per switch: lookup kura_dec[step//10] and gate_dec[step//10] (decimation
=10 in the simulator; this is the closest-snapshot lookup with ~5-step
precision, well below the Kuramoto timescale ~130 steps).

Per-cell decomposition computes |μ_class|, arg(μ_class), and the cross-
term sum.  Validated by checking μ_total = Σ μ_class to floating-point
precision.

Predictions
-----------
P1 (rotation reproduces): at fixed ω_std=0.07, μ_arg still rotates
   monotonically from A=0.10 to A=0.40 by ≥10°.
P2 (dip reproduces): ρ_sig is non-monotonic — peak near A=0.20, dip
   between A=0.30 and A=0.45.
P3 (class decomposition): att·lock dominates at low A. At higher A,
   one of the other classes (likely att·noise or rep·noise) gains
   weight with a different phase.
P4 (destructive cross-term): cross-term Re(μ_a · conj(μ_b)) for the
   two strongest classes is more negative at the dip A than at flanking
   A values; difference of ≥0.5 in normalized cross-term.
P5 (per-class μ_arg ~A-invariant within class): each class's mu_arg
   should be approximately A-invariant; only the weights shift. If
   classes' mu_args themselves rotate, mechanism is more complex.
P6 (lock_frac at switch): the fraction of switches at lock-on grows
   with A in [0.20, 0.40], possibly peaks before A=0.40, then falls
   as gate-disrupted regime takes over (S111-P3 framing).

Compute estimate
----------------
8 cells × 16 seeds × 1.01M steps × 25 µs/step ≈ 54 min.
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
    signal_phase_binned_lock,
    gate_conditional_lock,
    signal_phase_binned_switches,
    lock_modulation_at_fs,
    kura_modulation_at_fs,
    first_principles_z_st,
)
from thor_session_112_omega_cliff import (
    OMEGA_OFFSETS_UNIT,
    build_omega,
    simulate_with_omega,
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
N_BINS = 12
LOCK_THR = 0.9


def per_switch_state(switch_steps, switch_dirs, kura_dec, gate_dec,
                     dec=DEC_KURA, lock_thr=LOCK_THR):
    """Look up R_kura and gate at each switch event by decimated index.

    switch_steps are post-warmup; kura_dec/gate_dec are sampled every
    `dec` steps starting from step 0.  Closest-decimation lookup.
    """
    if len(switch_steps) == 0:
        return (np.zeros(0), np.zeros(0, dtype=bool),
                np.zeros(0, dtype=bool))
    idx = np.minimum(switch_steps // dec, len(kura_dec) - 1)
    kura_at_sw = kura_dec[idx]
    gate_at_sw = gate_dec[idx]
    lock_at_sw = kura_at_sw > lock_thr
    return kura_at_sw, gate_at_sw, lock_at_sw


def class_decompose(switch_steps, switch_dirs, gate_at_sw, lock_at_sw,
                    signal_freq=SIGNAL_FREQ, dt=DT, warmup=WARMUP):
    """Split switch list into 4 classes by (gate × lock) and compute
    per-class complex matched-filter sums.

    Returns dict with per-class:
      - count
      - mu_complex (Σ direction · exp(i 2πf_s t))
      - mu_abs (|Σ|)
      - mu_arg_deg
    Plus the total-sum equality check and cross-terms.
    """
    classes = {
        'att_lock':   gate_at_sw & lock_at_sw,
        'att_noise':  gate_at_sw & ~lock_at_sw,
        'rep_lock':   ~gate_at_sw & lock_at_sw,
        'rep_noise':  ~gate_at_sw & ~lock_at_sw,
    }
    per_class = {}
    z_total_check = 0.0 + 0.0j
    if len(switch_steps) > 0:
        abs_t = (switch_steps + warmup) * dt
        arg = 2.0 * np.pi * signal_freq * abs_t
        s_dirs = switch_dirs.astype(float)
        # contribution per-event as complex: dir * (sin + i cos)
        contrib = s_dirs * (np.sin(arg) + 1j * np.cos(arg))
    else:
        contrib = np.zeros(0, dtype=complex)
    for name, mask in classes.items():
        if mask.any():
            mu = complex(contrib[mask].sum())
            cnt = int(mask.sum())
        else:
            mu = 0.0 + 0.0j
            cnt = 0
        per_class[name] = {
            'count': cnt,
            'mu_re': float(mu.real),
            'mu_im': float(mu.imag),
            'mu_abs': float(abs(mu)),
            'mu_arg_deg': float(np.degrees(np.angle(mu))) if abs(mu) > 0 else 0.0,
        }
        z_total_check += mu

    # Cross-terms 2·Re(μ_a · conj μ_b) for all unordered pairs
    keys = list(classes.keys())
    cross_terms = {}
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            a, b = keys[i], keys[j]
            ca = complex(per_class[a]['mu_re'], per_class[a]['mu_im'])
            cb = complex(per_class[b]['mu_re'], per_class[b]['mu_im'])
            cross_terms[f'{a}__{b}'] = float(2.0 * (ca * cb.conjugate()).real)

    sum_class_sq = sum(per_class[k]['mu_abs']**2 for k in keys)
    cross_total = sum(cross_terms.values())
    z_total_abs2 = float(abs(z_total_check)**2)

    return {
        'per_class': per_class,
        'cross_terms': cross_terms,
        'sum_class_sq': sum_class_sq,
        'cross_total': cross_total,
        'z_total_re': float(z_total_check.real),
        'z_total_im': float(z_total_check.imag),
        'z_total_abs': float(abs(z_total_check)),
        'z_total_abs2': z_total_abs2,
        'class_sum_check': z_total_abs2 - (sum_class_sq + cross_total),
    }


def run_cell(label, kappa_phase, kappa_C, omega_std, signal_amp, seed_base,
             n_chunks=N_CHUNKS, n_seeds=N_SEEDS, n_bins=N_BINS,
             omega_base=0.1):
    omega_vec = build_omega(omega_base, omega_std)
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> {label}: κ_p={kappa_phase:.3f}  κ_C={kappa_C:.3f}  "
          f"ω_std={omega_std:.4f}  ω={np.round(omega_vec,4).tolist()}  "
          f"A={signal_amp:.4f}  "
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
        I_kura, Q_kura, mod_amp_kura, mod_arg_kura = kura_modulation_at_fs(
            kdec, spdec)
        kura_at_sw, gate_at_sw, lock_at_sw = per_switch_state(
            sw_steps, sw_dirs, kdec, gdec)
        decomp = class_decompose(sw_steps, sw_dirs, gate_at_sw, lock_at_sw)
        # First-principles total sum check for this seed
        Ip, Qp, fp_z_total = first_principles_z_st(
            sw_steps, sw_dirs, SIGNAL_FREQ, DT)
        # Class-sum should equal first-principles z_total to FP precision
        rec = {
            'seed': seed_base + s,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw_chunks': n_sw_chunks,
            'raw_per_seed': raw_st, 'st_per_seed': st_st,
            'kura_mean': k_mean,
            'kura_dec_len': int(len(kdec)),
            'lock_frac_global': float((kdec > LOCK_THR).mean()),
            'mod_amp_at_fs_lock': mod_amp_lock,
            'mod_arg_at_fs_lock_deg': mod_arg_lock,
            'mod_amp_at_fs_kura': mod_amp_kura,
            'mod_arg_at_fs_kura_deg': mod_arg_kura,
            'switch_total': int(len(sw_steps)),
            'lock_at_switch_frac': float(lock_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'gate_att_at_switch_frac': float(gate_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'kura_at_switch_mean': float(kura_at_sw.mean()) if len(sw_steps) > 0 else 0.0,
            'fp_z_total_pred': fp_z_total,
            'class_decomp': decomp,
        }
        seed_records.append(rec)
        elapsed = time.time() - t0
        cls = decomp['per_class']
        print(f"   seed={seed_base+s:9d} {elapsed:5.1f}s   "
              f"|<z_st>|={abs(z_st.mean()):.3f}  arg={np.degrees(np.angle(z_st.mean())):+6.1f}°  "
              f"R_k={k_mean:.3f}  "
              f"lock@sw={float(lock_at_sw.mean()) if len(sw_steps)>0 else 0:.2f}  "
              f"att@sw={float(gate_at_sw.mean()) if len(sw_steps)>0 else 0:.2f}  "
              f"Nsw={len(sw_steps)}  "
              f"|μ_class|: aL={cls['att_lock']['mu_abs']:5.1f} "
              f"aN={cls['att_noise']['mu_abs']:5.1f} "
              f"rL={cls['rep_lock']['mu_abs']:5.1f} "
              f"rN={cls['rep_noise']['mu_abs']:5.1f}")
    print(f"   total {time.time()-cell_start:.0f}s")
    return seed_records, omega_vec.tolist()


def summarize_cell(seed_records, signal_amp):
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

    # Cross-seed angle coherence on |⟨z_st⟩|
    z_arg = np.exp(1j * np.deg2rad(st_mu_arg))
    R_ang = float(abs(z_arg.mean()))
    mean_arg = float(np.degrees(np.angle(z_arg.mean())))

    # ρ_sig = |⟨z_st⟩|² / ⟨N_sw⟩ per seed
    rho_sig = []
    for s in seed_records:
        mu2 = abs(s['z_st'].mean())**2
        nsw = float(np.mean(s['n_sw_chunks']))
        rho_sig.append(mu2 / nsw if nsw > 0 else 0.0)
    rho_sig = np.array(rho_sig)

    # Per-class aggregates: take cross-seed sum of mu_complex, average count
    classes = ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
    class_agg = {}
    for k in classes:
        mu_re = np.array([s['class_decomp']['per_class'][k]['mu_re']
                          for s in seed_records])
        mu_im = np.array([s['class_decomp']['per_class'][k]['mu_im']
                          for s in seed_records])
        cnt = np.array([s['class_decomp']['per_class'][k]['count']
                        for s in seed_records], dtype=float)
        # Per-seed |μ_class|, then mean
        mu_abs_per_seed = np.sqrt(mu_re**2 + mu_im**2)
        mu_arg_per_seed = np.degrees(np.arctan2(mu_im, mu_re))
        # Cross-seed phase coherence on per-seed class angles
        z_class = np.exp(1j * np.deg2rad(mu_arg_per_seed))
        z_class_mean = z_class.mean()
        class_agg[k] = {
            'mu_abs_per_seed_mean': float(mu_abs_per_seed.mean()),
            'mu_abs_per_seed_std': float(mu_abs_per_seed.std()),
            'mu_arg_per_seed_circmean_deg': float(np.degrees(np.angle(z_class_mean))),
            'mu_arg_R_seedpair': float(abs(z_class_mean)),
            'count_per_seed_mean': float(cnt.mean()),
            'fraction_of_sw': float(cnt.sum() / max(1, sum(np.array([s['switch_total']
                                          for s in seed_records])))),
        }

    # Cross-term aggregates: pooled seeds, pairwise
    cross_keys = list(seed_records[0]['class_decomp']['cross_terms'].keys())
    cross_agg = {}
    for ck in cross_keys:
        vals = np.array([s['class_decomp']['cross_terms'][ck]
                         for s in seed_records])
        cross_agg[ck] = {
            'mean': float(vals.mean()),
            'std': float(vals.std()),
        }

    # Per-seed normalized cross-term sum vs sum_class_sq
    cross_norm = []
    sum_sq_norm = []
    for s in seed_records:
        d = s['class_decomp']
        if d['z_total_abs2'] > 0:
            cross_norm.append(d['cross_total'] / d['z_total_abs2'])
            sum_sq_norm.append(d['sum_class_sq'] / d['z_total_abs2'])
    cross_norm = np.array(cross_norm)
    sum_sq_norm = np.array(sum_sq_norm)

    return {
        'signal_amp': signal_amp,
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
        'n_sw_total_mean': float(n_sw_total.mean()),
        'lock_at_switch_frac_mean': float(lock_at_sw.mean()),
        'gate_att_at_switch_frac_mean': float(att_at_sw.mean()),
        'class_agg': class_agg,
        'cross_agg': cross_agg,
        'cross_total_norm_mean': float(cross_norm.mean()) if len(cross_norm) > 0 else 0.0,
        'cross_total_norm_std':  float(cross_norm.std()) if len(cross_norm) > 0 else 0.0,
        'sum_class_sq_norm_mean': float(sum_sq_norm.mean()) if len(sum_sq_norm) > 0 else 0.0,
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
        'fp_z_total_pred': s['fp_z_total_pred'],
        'class_decomp': s['class_decomp'],
    } for s in seed_records]


def main():
    start = datetime.now()
    print("Thor Session #113: A=0.40 Dip — Switch-Class Decomposition")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"chunk={CHUNK_STEPS} steps  T_chunk={T_CHUNK_S}s  "
          f"warmup={WARMUP}  decimate={DEC_KURA}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks  ω_std=0.07  "
          f"(below cliff, S112's mild-heterogeneity sweet spot)")

    RIDGE_KP = 0.30
    RIDGE_KC = 0.30
    OMEGA_STD = 0.07

    # Fine A grid covering the dip
    A_VALUES = [0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

    cells = []
    for A in A_VALUES:
        seed_base = 113_000_000 + int(round(A * 100)) * 1000
        cells.append({
            'label': f'A{int(round(A*100)):03d}',
            'kappa_phase': RIDGE_KP, 'kappa_C': RIDGE_KC,
            'omega_std': OMEGA_STD, 'signal_amp': A,
            'seed_base': seed_base,
        })

    cell_results = {}
    for cd in cells:
        seed_records, omega_vec = run_cell(
            cd['label'], cd['kappa_phase'], cd['kappa_C'],
            cd['omega_std'], cd['signal_amp'], cd['seed_base'])
        summary = summarize_cell(seed_records, signal_amp=cd['signal_amp'])
        ca = summary['class_agg']
        print(f"\n   ⇒ {cd['label']}: A={cd['signal_amp']:.2f}  "
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
        print(f"      cross_total/|z|² = {summary['cross_total_norm_mean']:+.3f}  "
              f"sum_class²/|z|² = {summary['sum_class_sq_norm_mean']:.3f}")
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
            'session': 113,
            'title': 'A=0.40 Dip via Switch-Class Decomposition',
            'started': start.isoformat(),
            'common_params': {
                'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'dec_kura': DEC_KURA, 'lock_thr': LOCK_THR, 'n_bins': N_BINS,
                'kappa_phase': RIDGE_KP, 'kappa_C': RIDGE_KC,
                'omega_base': 0.1, 'omega_std': OMEGA_STD,
                'omega_offsets_unit': OMEGA_OFFSETS_UNIT.tolist(),
                'A_values': A_VALUES,
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_113_dip_decomp_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_113_dip_decomp_results.json")


if __name__ == '__main__':
    main()
