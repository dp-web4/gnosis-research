#!/usr/bin/env python3
"""Thor Session #115: Does the Dip Need Lock@sw? — κ_C-Sweep at the Dip A
==========================================================================

Context (S114-P5)
-----------------
S114 mapped dip-A vs κ_p at fixed ratio ω_std/κ_p = 0.233:
  κ_p = 0.10  →  no dip (max lock@sw = 0.42 at A=0.30, below ~0.5 threshold)
  κ_p = 0.30  →  dip at A=0.40 (lock@sw = 0.55)            ← S113 baseline
  κ_p = 0.50  →  small dip at A=0.70 (lock@sw = 0.64; 6%, z≈0.9)

The S114 mechanism story: the (att_lock, rep_noise) wedge widens as A
grows, peaking at A=dip-A. For the wedge to be wide enough for a
destructive cross-term (≥30°), the att_lock class needs enough events
that the att_lock μ-vector dominates its half-plane and rotates from
(near-zero-A) ~−170° toward saturation at ~−96°. **att_lock fraction is
gated by lock@sw: if too few switches happen during R_kura(t)>0.9 epochs,
the class decomposition collapses.**

S114-P5 is the direct test: at κ_p=0.30 fixed, sweep κ_C — which
controls switch-rate concentration and therefore lock@sw — and measure
whether the dip vanishes when lock@sw at A=dip-A drops below ~0.5.

Why κ_C: S107/S110 established κ_C is the switch-rate concentrator.
At ratio 0.8, κ_C=0.30 is the ridge; κ_C=0.05 brings ρ_sig to a near-
floor; κ_C=0.50 over-collapses switching (S106). For ratio 0.233 (our
deep-coherent regime, S108-territory) the ridge sits a little earlier
(~0.25 RAW; S108 found κ_C*=0.249 RAW at ratio 0.2). We sample below,
near, and slightly above the ridge.

Design
------
Grid: 4 NEW κ_C values × 3 A values = 12 cells.
  κ_C ∈ {0.05, 0.15, 0.25, 0.40}  (S113 κ_C=0.30 cells reused for analysis)
  A   ∈ {0.30, 0.40, 0.50}        (brackets known dip at A=0.40)
  16 seeds × 25 chunks per cell.
  ω_std = 0.07 fixed (S113 baseline, well below ω_std≈0.17 cliff).
  κ_p  = 0.30 fixed.

Each cell records:
  - per-seed z_st, z_raw → R_coh, mu, sigma_n, mu_arg
  - per-seed lock_at_switch_frac, gate_att_at_switch_frac
  - per-seed class decomposition (att_lock, att_noise, rep_lock,
    rep_noise) → |μ_class|, arg(μ_class), counts
  - mod_amp_at_fs_lock (signal-driven R_kura(t) modulation amplitude)

Compute: 12 × 16 × 1.01M steps × ~25 µs/step ≈ 81 min.

Predictions
-----------
P1 (lock-fraction monotone in κ_C): lock_frac_global and lock@sw both
   grow with κ_C in [0.05, 0.40]. At fixed A=0.40:
     κ_C=0.05  → lock@sw < 0.20
     κ_C=0.15  → lock@sw ~0.30–0.40
     κ_C=0.25  → lock@sw ~0.45–0.55
     κ_C=0.40  → lock@sw > 0.60

P2 (dip-presence threshold): the dip (ρ_sig(A=0.40) below the linear
   interpolation of ρ_sig at A=0.30 and A=0.50) APPEARS only when
   lock@sw at A=0.40 ≥ ~0.5. So:
     κ_C=0.05, 0.15: dip absent (ρ_sig monotone in A)
     κ_C=0.25 (near ridge): dip present (similar to S113's 3% drop)
     κ_C=0.40: dip present, possibly larger

P3 (wedge angle gates the dip): Δφ_aL,rN at A=0.40 grows with κ_C.
   Wedge ≥ ~30° required for destructive interference of the dominant
   pair to dent ρ_sig.

P4 (att_lock fraction at A=0.40): grows with κ_C. At κ_C=0.05, the
   att_lock fraction will be low (<0.2) — the dominant class becomes
   rep_noise, which has a different angle structure.

P5 (μ_arg shift at A=0.40 across κ_C): the total μ_arg at A=0.40
   should rotate as κ_C grows because the class composition shifts.
   Predict ≥10° shift across κ_C ∈ [0.05, 0.40].

P6 (R_kura monotone in κ_C in this range): consistent with S106 at
   ratio 0.8 (R_kura roughly flat 0.55-0.58 up to κ_C=0.30, drops at
   0.50). Probably similar shape here.

Failure modes
-------------
- If at κ_C=0.05 the system is essentially un-coupled and switches
  are signal-driven directly (S112 past-cliff residual), ρ_sig may
  still be ~0.08 across A (signal-direct channel). That floor is
  visible by A-monotonicity, not dip.
- If κ_C=0.40 is past-ridge for ratio 0.233 (likely), ρ_sig may
  collapse and the dip becomes invisible against rising error bars.
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
        'lock_frac_global_mean': float(lock_global.mean()),
        'kura_mean_mean': float(kura_mean_arr.mean()),
        'rho_sig_st_mean': float(rho_sig.mean()),
        'rho_sig_st_std':  float(rho_sig.std()),
        'rho_sig_st_sem':  float(rho_sig.std() / np.sqrt(max(1, n))),
        'n_sw_total_mean': float(n_sw_total.mean()),
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
    print("Thor Session #115: Does the Dip Need Lock@sw? — κ_C-Sweep at the Dip A")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"chunk={CHUNK_STEPS} steps  T_chunk={T_CHUNK_S}s  "
          f"warmup={WARMUP}  decimate={DEC_KURA}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks  "
          f"κ_p=0.30, ω_std=0.07 fixed; sweep (κ_C, A)")

    KAPPA_P = 0.30
    OMEGA_STD = 0.07

    # κ_C × A grid; κ_C=0.30 line is recycled from S113 in the analyzer.
    kc_grid = [0.05, 0.15, 0.25, 0.40]
    A_grid = [0.30, 0.40, 0.50]

    cells_def = []
    for kc in kc_grid:
        for A in A_grid:
            label = f'kc{int(round(kc*100)):03d}_A{int(round(A*100)):03d}'
            cells_def.append((label, kc, A))

    cells = []
    for label, kc, A in cells_def:
        # Distinct seed namespace from S113/S114
        seed_base = (115_000_000
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
            'session': 115,
            'title': 'κ_C-Sweep at the Dip A — testing lock@sw threshold',
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
            'kc_grid': kc_grid,
            'A_grid': A_grid,
        },
        'cells': cell_results,
    }
    with open('thor_session_115_kc_dip_gate_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_115_kc_dip_gate_results.json")


if __name__ == '__main__':
    main()
