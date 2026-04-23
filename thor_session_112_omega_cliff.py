#!/usr/bin/env python3
"""Thor Session #112: The Within-Seed Kuramoto Cliff Explains A=0.50 Bimodality
=================================================================================

Context (S111-P3)
-----------------
S111 ran A-sweep at the ridge (κ_p=0.30, κ_C=0.30, ratio 0.8) and
reported three surprises: (a) mod_lock linear in A up to 0.20 then
super-linear, (b) ρ_sig non-monotonic with peak at A=0.20 and dip at
A=0.30–0.40, (c) HIGH seed variance at A=0.50 (CV=53%).

Post-hoc analysis of the S111 per-seed data revealed **bimodality at
A=0.50**: 3/10 seeds with mod_amp_at_fs_lock < 0.025 ("failing") and
7/10 with mod_amp > 0.20 ("succeeding"). The 3 failing seeds all had
per-seed ω_std in {0.169, 0.177, 0.184} while succeeding seeds had
ω_std ∈ [0.066, 0.128]. Pooled across A ≥ 0.20: Mann-Whitney p = 0.031.

Hypothesis: The failure mode is a within-seed Kuramoto cliff. With
κ_p=0.30 the bare Δ_c = πκ/4 = 0.236. Gate-modulation flips the sign
of phase coupling, reducing effective κ to ~0.15 when gate spends
half the time attractive and half repulsive. Effective Δ_c drops to
~0.118, matching the observed failure threshold ω_std ≈ 0.15.

As A rises toward threshold 0.55, the gate spends MORE time flipping
near the boundary — effective κ drops further — more seeds fall past
the cliff. This explains the increasing variance at high A and the
bimodal seed population at A=0.50.

Design
------
Patched simulator accepts explicit omega_override: 4 fixed ω values.
We set them equally-spaced around ω_base=0.1 to produce a target
per-seed ω_std exactly:
  ω_i = ω_base + ω_std · {-1.342, -0.447, 0.447, 1.342}

Experiment A: ω_std sweep at A=0.50, κ_p=0.30, κ_C=0.30, ratio 0.8.
  ω_std ∈ {0.03, 0.07, 0.11, 0.15, 0.19, 0.23}  (6 cells)
  10 seeds × 25 chunks each.
  Predict: detection_fraction (seeds with mod_lock > 0.04) = 1.0 at
  low ω_std, cliff near ω_std ≈ 0.15.

Experiment B: A-dependence at ω_std=0.19 (past cliff in S111 failing
seeds). A ∈ {0.20, 0.30, 0.40, 0.60}. 10 seeds × 25 chunks.
  Predict: failure fraction grows with A — lower A (0.20) has more
  detecting seeds because gate doesn't near-saturate toggle rate.

Experiment C: control — ω_std=0.03 at A=0.50. Predict 10/10 detect.
Covered in Experiment A.

Predictions:
  P1: failure_fraction(ω_std) monotonic at A=0.50; cliff 0.12–0.18.
  P2: failure_fraction(A) at ω_std=0.19 monotonic; detects at low A.
  P3: per-seed |μ_st| distribution at near-cliff cell is bimodal.
  P4: mod_lock_mean drops with ω_std, but |μ_st_succeeding| holds.
  P5: ρ_sig_filtered (excl. failing seeds) is near-constant in ω_std.
      Remaining ω_std effect on ρ_sig is through N_sw, not signal.

Compute: ~40 min on Thor.
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
    summarize_cell,
    pack_per_seed,
)

C_THRESHOLD = 0.55
SIGNAL_FREQ = 0.003
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
T_CHUNK_S = CHUNK_STEPS * DT
N_SEEDS = 10
N_CHUNKS = 25
DEC_KURA = 10
N_BINS = 12

# Equally-spaced-4 offsets that yield per-seed ω_std exactly = target:
#  std of {-3a/2, -a/2, a/2, 3a/2} = a·√(5)/2 = 1.118·a
#  so for std = s → offsets = s · (2/√5) · {-3/2, -1/2, 1/2, 3/2}
#                          = s · {-3/√5, -1/√5, 1/√5, 3/√5}
#                          = s · {-1.342, -0.447, 0.447, 1.342}
OMEGA_OFFSETS_UNIT = np.array([-3, -1, 1, 3]) / np.sqrt(5.0)


def build_omega(omega_base, omega_std, N=4):
    if N != 4:
        raise NotImplementedError("Omega override tuned for N=4.")
    return omega_base + omega_std * OMEGA_OFFSETS_UNIT


def simulate_with_omega(N, noise_std, steps, seed, omega,
                         kappa_phase=0.30, kappa_C=0.30,
                         phi_inverse=0.618, dt=0.1,
                         C_threshold=0.55,
                         signal_freq=0.003, signal_amp=0.0):
    """S111 simulator with ω array supplied externally.

    The random seed still controls C and phase initialization, and
    noise draws — only ω is fixed.

    Returns the same tuple as simulate_dose_response.
    """
    np.random.seed(seed)
    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    # NOTE: we do NOT draw the usual np.random.uniform(-omega_spread,...).
    # This keeps future np.random calls deterministic for the same seed.
    omega = np.asarray(omega, dtype=float)
    if len(omega) != N:
        raise ValueError(f"omega length {len(omega)} != N {N}")
    C_mean_hist = np.empty(steps)
    post_warm_len = max(0, steps - WARMUP)
    n_dec = post_warm_len // DEC_KURA + 1
    kura_dec = np.empty(n_dec)
    mean_phase_dec = np.empty(n_dec)
    gate_dec = np.empty(n_dec, dtype=bool)
    C_mean_dec = np.empty(n_dec)
    sig_dec = np.empty(n_dec)
    sig_phase_dec = np.empty(n_dec)
    d_idx = 0
    switch_steps = []
    switch_dirs = []
    prev_sign = None
    for t in range(steps):
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean
        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        is_attractive = (C_mean + signal) < C_threshold
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        phase = (phase + dt * dphase) % (2 * np.pi)
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
        dC = intrinsic + c_coupling
        C = np.clip(C + dt * dC, 0, 1)
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

        post = t - WARMUP
        if post >= 0:
            if post % DEC_KURA == 0:
                z_sum = np.mean(np.exp(1j * phase))
                kura_dec[d_idx] = abs(z_sum)
                mean_phase_dec[d_idx] = float(np.angle(z_sum))
                gate_dec[d_idx] = bool(is_attractive)
                C_mean_dec[d_idx] = C_mean
                sig_dec[d_idx] = signal
                sig_phase_dec[d_idx] = (2.0 * np.pi * signal_freq * t * dt) % (2.0 * np.pi)
                d_idx += 1
            cur_sign = 1 if (C_mean_hist[t] - C_threshold) > 0 else -1
            if prev_sign is not None and cur_sign != prev_sign:
                switch_steps.append(post)
                switch_dirs.append(cur_sign)
            prev_sign = cur_sign
    kura_dec = kura_dec[:d_idx]
    mean_phase_dec = mean_phase_dec[:d_idx]
    gate_dec = gate_dec[:d_idx]
    C_mean_dec = C_mean_dec[:d_idx]
    sig_dec = sig_dec[:d_idx]
    sig_phase_dec = sig_phase_dec[:d_idx]
    return (C_mean_hist, kura_dec, mean_phase_dec, gate_dec, C_mean_dec,
            sig_dec, sig_phase_dec,
            np.array(switch_steps, dtype=int),
            np.array(switch_dirs, dtype=int),
            float(kura_dec.mean()) if d_idx > 0 else 0.0)


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
        n_sw = np.zeros(n_chunks, dtype=int)
        for c in range(n_chunks):
            chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
            t_off = WARMUP + c * CHUNK_STEPS
            Ir, Qr = phase_coherent_IQ(chunk, DT, SIGNAL_FREQ, t_offset=t_off)
            Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ,
                                          t_offset=t_off,
                                          threshold=C_THRESHOLD)
            z_raw[c] = Ir + 1j * Qr
            z_st[c] = Is + 1j * Qs
            n_sw[c] = n
        raw_st = per_seed_R_coh(z_raw)
        st_st = per_seed_R_coh(z_st)
        lock_per_bin, cnt_per_bin, bin_centers = signal_phase_binned_lock(
            kdec, spdec, n_bins=n_bins)
        gate_cond = gate_conditional_lock(kdec, gdec)
        I_lock, Q_lock, mod_amp_lock, mod_arg_lock = lock_modulation_at_fs(
            kdec, spdec)
        I_kura, Q_kura, mod_amp_kura, mod_arg_kura = kura_modulation_at_fs(
            kdec, spdec)
        up_b, dn_b, _, all_b = signal_phase_binned_switches(
            sw_steps, sw_dirs, SIGNAL_FREQ, DT, n_bins=n_bins)
        Ip, Qp, fp_z_total = first_principles_z_st(
            sw_steps, sw_dirs, SIGNAL_FREQ, DT)
        meas_z_total = float(abs(z_st.sum()))
        bin_edges = np.linspace(0.0, 2.0 * np.pi, n_bins + 1)
        bidx = np.digitize(spdec, bin_edges[1:-1])
        kura_per_bin = np.zeros(n_bins)
        for b in range(n_bins):
            mask = bidx == b
            if mask.any():
                kura_per_bin[b] = float(kdec[mask].mean())
        cosphi = np.cos(mphdec)
        cphi_dm = cosphi - cosphi.mean()
        I_cp = float(np.mean(cphi_dm * np.sin(spdec)))
        Q_cp = float(np.mean(cphi_dm * np.cos(spdec)))
        mod_amp_cosphi = float(np.sqrt(I_cp*I_cp + Q_cp*Q_cp))
        mod_arg_cosphi = float(np.degrees(np.arctan2(Q_cp, I_cp)))
        rec = {
            'seed': seed_base + s,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw_chunks': n_sw,
            'raw_per_seed': raw_st, 'st_per_seed': st_st,
            'kura_mean': k_mean,
            'kura_dec_len': int(len(kdec)),
            'lock_frac_global': float((kdec > 0.9).mean()),
            'lock_per_bin': lock_per_bin.tolist(),
            'cnt_per_bin': cnt_per_bin.tolist(),
            'kura_per_bin': kura_per_bin.tolist(),
            'gate_cond': gate_cond,
            'mod_amp_at_fs_lock': mod_amp_lock,
            'mod_arg_at_fs_lock_deg': mod_arg_lock,
            'mod_amp_at_fs_kura': mod_amp_kura,
            'mod_arg_at_fs_kura_deg': mod_arg_kura,
            'mod_amp_at_fs_cosphi': mod_amp_cosphi,
            'mod_arg_at_fs_cosphi_deg': mod_arg_cosphi,
            'switch_total': int(len(sw_steps)),
            'switch_up_per_bin': up_b.tolist(),
            'switch_dn_per_bin': dn_b.tolist(),
            'switch_all_per_bin': all_b.tolist(),
            'fp_z_total_pred': fp_z_total,
            'meas_z_total': meas_z_total,
        }
        seed_records.append(rec)
        elapsed = time.time() - t0
        print(f"   seed={seed_base+s:9d} {elapsed:5.1f}s   "
              f"|<z_st>|={abs(z_st.mean()):.3f}  "
              f"R_kura={k_mean:.3f}  "
              f"lock_frac={float((kdec>0.9).mean()):.3f}  "
              f"mod_lock={mod_amp_lock:.4f}  "
              f"Nsw={len(sw_steps)}")
    bin_centers_list = (np.linspace(0.0, 2.0 * np.pi, n_bins + 1)[:-1]
                        + np.pi / n_bins).tolist()
    print(f"   total {time.time()-cell_start:.0f}s")
    return seed_records, bin_centers_list, omega_vec.tolist()


def main():
    start = datetime.now()
    print("Thor Session #112: The Within-Seed Kuramoto Cliff (S111-P3)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"chunk={CHUNK_STEPS} steps  T_chunk={T_CHUNK_S}s  "
          f"warmup={WARMUP}  decimate={DEC_KURA}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks")

    RIDGE_KP = 0.30
    RIDGE_KC = 0.30

    # Experiment A: ω_std sweep at A=0.50 (find the cliff)
    # Experiment B: A sweep at ω_std=0.19 (past-cliff behavior)
    # Experiment C: high-A × wide-ω control (bimodality confirmation)
    cell_defs = []

    # A-suite: 6 ω_std levels at A=0.50
    for om_std in [0.03, 0.07, 0.11, 0.15, 0.19, 0.23]:
        seed_base = 112_000_000 + int(round(om_std * 1000)) * 100
        cell_defs.append({
            'label': f'A050_om{int(round(om_std*1000)):03d}',
            'exp': 'A',
            'kappa_phase': RIDGE_KP, 'kappa_C': RIDGE_KC,
            'omega_std': om_std, 'signal_amp': 0.50,
            'seed_base': seed_base,
            'notes': 'Experiment A: ω_std cliff search at A=0.50',
        })

    # B-suite: A ∈ {0.20, 0.30, 0.40, 0.60} at ω_std=0.19 (past-cliff at A=0.50)
    #          A=0.50 already covered by A-suite
    for A in [0.20, 0.30, 0.40, 0.60]:
        seed_base = 112_100_000 + int(round(A * 100)) * 100
        cell_defs.append({
            'label': f'om190_A{int(round(A*100)):03d}',
            'exp': 'B',
            'kappa_phase': RIDGE_KP, 'kappa_C': RIDGE_KC,
            'omega_std': 0.19, 'signal_amp': A,
            'seed_base': seed_base,
            'notes': 'Experiment B: A sweep at past-cliff ω_std=0.19',
        })

    cell_results = {}
    for cd in cell_defs:
        seed_records, bin_centers, omega_vec = run_cell(
            cd['label'], cd['kappa_phase'], cd['kappa_C'],
            cd['omega_std'], cd['signal_amp'], cd['seed_base'])
        summary = summarize_cell(seed_records, bin_centers,
                                  signal_amp=cd['signal_amp'])
        # Add failure/success classification
        mod_locks = np.array([s['mod_amp_at_fs_lock'] for s in seed_records])
        n_fail = int((mod_locks < 0.04).sum())
        summary['detection_threshold'] = 0.04
        summary['n_fail'] = n_fail
        summary['n_total'] = len(seed_records)
        summary['detection_fraction'] = (len(seed_records) - n_fail) / len(seed_records)
        # Stats on succeeding seeds only
        succ = mod_locks >= 0.04
        if succ.any():
            mu_st_arr = np.array([s['st_per_seed']['mu_abs'] for s in seed_records])
            nsw_arr = np.array([s['switch_total'] for s in seed_records])
            rho_per_seed = mu_st_arr**2 / np.maximum(np.array([
                float(np.mean(s['n_sw_chunks'])) for s in seed_records]), 1)
            summary['mod_lock_mean_succeeding'] = float(mod_locks[succ].mean())
            summary['mod_lock_std_succeeding'] = float(mod_locks[succ].std())
            summary['mu_st_mean_succeeding'] = float(mu_st_arr[succ].mean())
            summary['rho_sig_mean_succeeding'] = float(rho_per_seed[succ].mean())
        else:
            summary['mod_lock_mean_succeeding'] = 0.0
            summary['mod_lock_std_succeeding'] = 0.0
            summary['mu_st_mean_succeeding'] = 0.0
            summary['rho_sig_mean_succeeding'] = 0.0

        print(f"\n   ⇒ {cd['label']}: "
              f"fail={n_fail}/{len(seed_records)}  "
              f"R_kura={summary['kura_mean_mean']:.3f}  "
              f"lock_frac={summary['lock_frac_global_mean']:.3f}  "
              f"mod_lock={summary['mod_amp_at_fs_lock_mean']:.4f}±{summary['mod_amp_at_fs_lock_std']:.4f}  "
              f"[succ: {summary['mod_lock_mean_succeeding']:.4f}±{summary['mod_lock_std_succeeding']:.4f}]  "
              f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
              f"ST_R={summary['st_R_coh_mean']:.3f}  "
              f"<Nsw>={summary['n_sw_total_mean']:.0f}")
        cell_results[cd['label']] = {
            'exp': cd['exp'],
            'kappa_phase': cd['kappa_phase'], 'kappa_C': cd['kappa_C'],
            'omega_std_target': cd['omega_std'],
            'omega_vec': omega_vec,
            'signal_amp': cd['signal_amp'],
            'seed_base': cd['seed_base'], 'notes': cd['notes'],
            'summary': summary,
            'per_seed': pack_per_seed(seed_records),
        }

    out = {
        'meta': {
            'session': 112,
            'title': 'Within-Seed Kuramoto Cliff at A=0.50',
            'started': start.isoformat(),
            'common_params': {
                'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'dec_kura': DEC_KURA, 'n_bins': N_BINS,
                'kappa_phase': RIDGE_KP,
                'kappa_C': RIDGE_KC,
                'omega_base': 0.1,
                'omega_offsets_unit': OMEGA_OFFSETS_UNIT.tolist(),
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_112_omega_cliff_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_112_omega_cliff_results.json")


if __name__ == '__main__':
    main()
