#!/usr/bin/env python3
"""Thor Session #109: Phase-Ensemble Spread — Does it Explain the ρ_sig Asymmetry?

Context (S108, S108-P6)
-----------------------
S108 found the κ_C ≈ 0.27 ridge holds at ratio 0.2 (deep coherent) with the
same LOCATION but only 61% of the HEIGHT seen at ratio 0.8. The mechanism
hypothesis (S108 §4):

  "At ratio 0.8, partial phase desynchronization leaves 'room' for each
   C-oscillator to acquire a distinct phase of the signal forcing;
   averaging across the N=4 array produces a coherent composite response.
   At ratio 0.2, phases collapse onto a single trajectory; all four C's
   receive nearly the same instantaneous forcing; less net amplification."

S108-P6: per-oscillator phase std relative to ensemble mean phase should be
markedly smaller at ratio 0.2 than at ratio 0.8 for κ_C away from 0.
Loose prediction: std ≈ 5° at ratio 0.2, ≈ 25° at ratio 0.8.

BUT — R_kura data already warns the mechanism may be more subtle:
  ratio 0.2 κ_C=0.30: R_kura = 0.447  ⇒ σ_φ ~ sqrt(-2·ln 0.447) ≈ 72°
  ratio 0.8 κ_C=0.30: R_kura = 0.584  ⇒ σ_φ ~ sqrt(-2·ln 0.584) ≈ 59°

If those time-averaged R_kura values track instantaneous spread, ratio 0.2
would be MORE spread than ratio 0.8 at κ_C=0.30 — opposite to S108-P6.

Either:
  A) R_kura_mean mis-maps to spread (e.g., wrapped normal breaks for
     bimodal distributions); direct per-sample spread needed.
  B) The S108-P6 prediction was wrong — phase spread is LARGER at ratio 0.2
     under strong κ_C, and the ρ_sig asymmetry has a different source.

Design
------
Modify the S106 simulator to ALSO record decimated phase samples (shape
n_dec × N). Compute phase-ensemble observables directly:

  R_kura(t) min/mean/std/max  — instantaneous order parameter
  σ_φ_inst(t)                  — per-sample circular std of (φ_k − Ψ(t))
  σ_φ_time_mean                — time-average of σ_φ_inst (the key observable)
  pairwise-|Δφ| distribution   — detect bimodality (locked vs anti-locked)
  σ_cos[cos(φ_k)]_{k,t}        — the actual drive diversity on C

Cells (6): κ_p ∈ {0.30, 0.50} × κ_C ∈ {0.00, 0.30} × ratio ∈ {0.2, 0.8}
selected as follows (to avoid a 2×2×2 box while covering interesting regimes):

  1. kp030_kC000_r02  (κ_C=0 control, ratio 0.2)
  2. kp030_kC030_r02  (ridge peak, ratio 0.2)
  3. kp030_kC000_r08  (κ_C=0 control, ratio 0.8)
  4. kp030_kC030_r08  (ridge peak, ratio 0.8) — S108's highest RAW R_coh
  5. kp050_kC000_r08  (S108 sign-reversal regime: κ_p↑ HURTS ρ_sig at κ_C=0)
  6. kp050_kC030_r08  (S108: κ_p↑ HELPS ρ_sig at κ_C=0.30)

Each: 8 seeds × 30 chunks × 40k steps + 10k warmup = 1.21 M steps/seed
≈ 30 s/seed ≈ 4 min/cell. Total ≈ 24 min compute.

Protocol matches S108's (same chunk_steps, warmup, σ, A, signal_freq)
so R_coh numbers are directly comparable across sessions, with 30 chunks
in place of 50 (sufficient for per-seed R_coh with 8 seeds).

Seeds: 109_NNN_NNN block, disjoint from all prior sessions.

Predictions
-----------
P1 (S108-P6 literal): σ_φ_ratio02 < σ_φ_ratio08 for κ_C=0.30. Probability
    low given R_kura data — listed for falsification.

P2 (R_kura-consistent): σ_φ_ratio02 > σ_φ_ratio08 for κ_C=0.30. S108 §5
    already inferred this from Kuramoto drops. This reading implies the
    ρ_sig asymmetry is NOT a phase-spread effect — look elsewhere.

P3 (bimodal split): pairwise |Δφ| at ratio 0.2 κ_C=0.30 shows a
    locked-vs-anti-locked bimodality (peaks near 0 and π). R_kura averages
    low but at each instant the ensemble is either tight-locked or split.

P4 (drive-diversity): regardless of phase spread, σ_cos[cos(φ_k)] should
    TRACK ρ_sig across cells — it's the actual diversity of drive forces
    on the N C-components. Test: corr(σ_cos, ρ_sig_st) > 0.7 across the
    6 cells.

P5 (κ_p sign reversal at κ_C=0): kp050_kC000_r08 should show TIGHTER
    phase-locking (smaller σ_φ) than kp030_kC000_r08 — stronger κ_p with
    no C-coupling homogenizes phases more, which reduces drive diversity
    and degrades ρ_sig. Confirms the sign-reversal mechanism from S108.
"""
import json
import sys
import time
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55
SIGNAL_FREQ = 0.003
A_SIGNAL = 0.30
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
T_CHUNK_S = CHUNK_STEPS * DT
N_SEEDS = 8
N_CHUNKS = 30
KURA_DECIMATE = 10        # same as S106/S108 for cross-compatibility
PHASE_DECIMATE = 100      # coarser than KURA_DECIMATE to save memory
                          # signal period = 1/(f_s·dt) = 3333 steps
                          # PHASE_DECIMATE=100 gives ~33 samples/cycle


def simulate_with_phase_trace(N, noise_std, steps, seed,
                              kappa_phase=0.10, kappa_C=0.15,
                              omega_base=0.1, omega_spread=0.02,
                              phi_inverse=0.618, dt=0.1,
                              C_threshold=0.55,
                              signal_freq=0.003, signal_amp=0.0):
    """Canonical simulator + decimated phase trace post-warmup.

    Identical dynamics to simulate_with_kura (S106). Returns
    (C_mean_hist, R_kura_mean, R_kura_std, phase_samples)
    where phase_samples has shape (n_phase_samples, N).

    Phase samples are recorded every PHASE_DECIMATE steps in the
    post-warmup window. phase_samples[0] is taken at t=WARMUP.
    """
    np.random.seed(seed)
    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)
    C_mean_hist = np.empty(steps)
    post_warm_len = max(0, steps - WARMUP)
    n_kura = post_warm_len // KURA_DECIMATE + 1
    n_phase = post_warm_len // PHASE_DECIMATE + 1
    kura_samples = np.empty(n_kura)
    phase_samples = np.empty((n_phase, N))
    k_idx = 0
    p_idx = 0
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
        if post >= 0 and post % KURA_DECIMATE == 0:
            z_sum = np.mean(np.exp(1j * phase))
            kura_samples[k_idx] = abs(z_sum)
            k_idx += 1
        if post >= 0 and post % PHASE_DECIMATE == 0:
            phase_samples[p_idx] = phase
            p_idx += 1
    kura_samples = kura_samples[:k_idx]
    phase_samples = phase_samples[:p_idx]
    return (C_mean_hist,
            float(kura_samples.mean()),
            float(kura_samples.std()),
            phase_samples)


def phase_ensemble_stats(phase_samples):
    """Compute phase-ensemble spread observables from (n_dec, N) trace.

    Returns dict with:
      R_kura_inst_mean, R_kura_inst_std, R_kura_inst_min, R_kura_inst_max
      sigma_phi_rad     (time-average of per-sample circular std)
      sigma_phi_deg
      sigma_cos_mean    (time-average of std_k[cos(φ_k)])
      sigma_sin_mean    (time-average of std_k[sin(φ_k)])
      pairwise_dphi_mean  (rad)
      pairwise_dphi_std   (rad)
      pairwise_dphi_hist  (8 bins from 0 to π)
      frac_locked_above_09 (fraction of time with R_kura > 0.9)
    """
    n_dec, N = phase_samples.shape
    # Complex representation per-sample
    z_k = np.exp(1j * phase_samples)          # (n_dec, N)
    z_bar = z_k.mean(axis=1)                  # (n_dec,)
    R_inst = np.abs(z_bar)                    # (n_dec,)
    psi_inst = np.angle(z_bar)                # (n_dec,)

    # Circular std (wrapped normal approx) per sample
    R_clip = np.clip(R_inst, 1e-6, 1.0 - 1e-12)
    sigma_phi_rad_inst = np.sqrt(-2.0 * np.log(R_clip))
    sigma_phi_rad = float(sigma_phi_rad_inst.mean())

    # cos / sin spread across the ensemble, per-sample
    cos_phi = np.cos(phase_samples)
    sin_phi = np.sin(phase_samples)
    sigma_cos_inst = cos_phi.std(axis=1)       # std across k, per t
    sigma_sin_inst = sin_phi.std(axis=1)
    sigma_cos_mean = float(sigma_cos_inst.mean())
    sigma_sin_mean = float(sigma_sin_inst.mean())

    # Pairwise phase differences (all i<j), wrapped to [-π,π] → [0,π]
    iu = np.triu_indices(N, k=1)
    dphi = phase_samples[:, iu[0]] - phase_samples[:, iu[1]]
    dphi = np.angle(np.exp(1j * dphi))          # wrap to [-π,π]
    dphi_abs = np.abs(dphi)                     # [0,π]
    hist, _ = np.histogram(dphi_abs, bins=8, range=(0, np.pi))
    hist = hist.astype(float) / hist.sum()

    return {
        'R_kura_inst_mean': float(R_inst.mean()),
        'R_kura_inst_std':  float(R_inst.std()),
        'R_kura_inst_min':  float(R_inst.min()),
        'R_kura_inst_max':  float(R_inst.max()),
        'sigma_phi_rad':    sigma_phi_rad,
        'sigma_phi_deg':    float(np.degrees(sigma_phi_rad)),
        'sigma_cos_mean':   sigma_cos_mean,
        'sigma_sin_mean':   sigma_sin_mean,
        'pairwise_dphi_mean': float(dphi_abs.mean()),
        'pairwise_dphi_std':  float(dphi_abs.std()),
        'pairwise_dphi_hist': hist.tolist(),
        'frac_locked_above_09': float((R_inst > 0.9).mean()),
        'n_phase_samples': int(n_dec),
    }


def per_seed_R_coh(z_list):
    out = []
    for z in z_list:
        mu = z.mean()
        dev = z - mu
        sigma_n2 = float(np.mean(np.abs(dev)**2))
        mu2 = float(abs(mu)**2)
        out.append({
            'mu_abs': float(abs(mu)),
            'mu_arg_deg': float(np.degrees(np.angle(mu))),
            'sigma_n': float(np.sqrt(sigma_n2)),
            'R_coh': mu2 / (mu2 + sigma_n2) if (mu2 + sigma_n2) > 0 else 0.0,
        })
    return out


def cross_seed_angle_R(per_seed_stats):
    args = np.array([np.deg2rad(p['mu_arg_deg']) for p in per_seed_stats])
    return float(abs(np.mean(np.exp(1j * args))))


def run_cell(kappa_phase, kappa_C, omega_spread, seed_base,
             n_chunks=N_CHUNKS, n_seeds=N_SEEDS):
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> κ_p={kappa_phase:.3f}  κ_C={kappa_C:.3f}  "
          f"ω_spread={omega_spread:.4f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  "
          f"steps={total_steps}  seed_base={seed_base}")
    per_seed = []
    cell_start = time.time()
    for s in range(n_seeds):
        t0 = time.time()
        x, kura_mean, kura_std, phase_samples = simulate_with_phase_trace(
            N=4, noise_std=SIGMA_NOISE, steps=total_steps,
            seed=seed_base + s,
            kappa_phase=kappa_phase, kappa_C=kappa_C,
            signal_freq=SIGNAL_FREQ, signal_amp=A_SIGNAL,
            omega_spread=omega_spread, dt=DT)
        xp = x[WARMUP:]
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
        ph_stats = phase_ensemble_stats(phase_samples)
        per_seed.append({
            'seed': seed_base + s,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw': n_sw,
            'kura_mean': kura_mean, 'kura_std': kura_std,
            'phase_stats': ph_stats,
        })
        elapsed = time.time() - t0
        print(f"   seed={seed_base+s:9d}  {elapsed:5.1f}s   "
              f"|<z_raw>|={abs(z_raw.mean()):.3e}   "
              f"|<z_st>|={abs(z_st.mean()):.3f}   "
              f"σ_φ={ph_stats['sigma_phi_deg']:5.1f}°  "
              f"R_kura={kura_mean:.3f}  "
              f"Nsw={n_sw.mean():.0f}")
    print(f"   total {time.time()-cell_start:.0f}s")
    return per_seed


def summarize_cell(per_seed):
    z_raws = [s['z_raw'] for s in per_seed]
    z_sts = [s['z_st'] for s in per_seed]
    n_sws = np.array([np.mean(s['n_sw']) for s in per_seed])
    raw_stats = per_seed_R_coh(z_raws)
    st_stats = per_seed_R_coh(z_sts)

    def agg(stats, key):
        v = np.array([s[key] for s in stats])
        return float(v.mean()), float(v.std())

    raw_R, raw_R_sd = agg(raw_stats, 'R_coh')
    st_R, st_R_sd = agg(st_stats, 'R_coh')
    raw_mu, _ = agg(raw_stats, 'mu_abs')
    st_mu, _ = agg(st_stats, 'mu_abs')
    raw_sn, _ = agg(raw_stats, 'sigma_n')
    st_sn, _ = agg(st_stats, 'sigma_n')
    R_angle_raw = cross_seed_angle_R(raw_stats)
    R_angle_st = cross_seed_angle_R(st_stats)
    kura = np.array([s['kura_mean'] for s in per_seed])

    # Aggregate phase stats across seeds
    def agg_ph(key):
        v = np.array([s['phase_stats'][key] for s in per_seed])
        return float(v.mean()), float(v.std())

    sigma_phi_mean, sigma_phi_sd = agg_ph('sigma_phi_rad')
    R_inst_mean, R_inst_sd = agg_ph('R_kura_inst_mean')
    sigma_cos_mean, sigma_cos_sd = agg_ph('sigma_cos_mean')
    pair_dphi_mean, _ = agg_ph('pairwise_dphi_mean')
    frac_locked, _ = agg_ph('frac_locked_above_09')

    # ρ_sig = |<z_st>_chunks|² / <N_sw>_chunks (per seed, then mean)
    rho_sig_list = []
    for s in per_seed:
        mu_abs2 = abs(s['z_st'].mean())**2
        n_mean = float(np.mean(s['n_sw']))
        rho_sig_list.append(mu_abs2 / n_mean if n_mean > 0 else 0.0)
    rho_sig_arr = np.array(rho_sig_list)

    # Cross-cell: average pairwise |Δφ| histogram
    hist_list = np.array([s['phase_stats']['pairwise_dphi_hist']
                          for s in per_seed])
    hist_mean = hist_list.mean(axis=0).tolist()
    hist_std = hist_list.std(axis=0).tolist()

    return {
        'raw_per_seed': raw_stats,
        'st_per_seed': st_stats,
        'raw_R_coh_mean': raw_R, 'raw_R_coh_std': raw_R_sd,
        'st_R_coh_mean': st_R, 'st_R_coh_std': st_R_sd,
        'raw_mu_mean': raw_mu, 'st_mu_mean': st_mu,
        'raw_sigma_n_mean': raw_sn, 'st_sigma_n_mean': st_sn,
        'cross_seed_R_angle_raw': R_angle_raw,
        'cross_seed_R_angle_st': R_angle_st,
        'R_kura_cross_seed_mean': float(kura.mean()),
        'R_kura_cross_seed_std': float(kura.std()),
        'sigma_phi_rad_mean': sigma_phi_mean,
        'sigma_phi_rad_std':  sigma_phi_sd,
        'sigma_phi_deg_mean': float(np.degrees(sigma_phi_mean)),
        'R_inst_mean': R_inst_mean, 'R_inst_std': R_inst_sd,
        'sigma_cos_mean': sigma_cos_mean, 'sigma_cos_std': sigma_cos_sd,
        'pairwise_dphi_mean_rad': pair_dphi_mean,
        'pairwise_dphi_mean_deg': float(np.degrees(pair_dphi_mean)),
        'frac_locked_above_09': frac_locked,
        'pairwise_dphi_hist_mean': hist_mean,
        'pairwise_dphi_hist_std': hist_std,
        'n_sw_mean_per_seed': [float(x) for x in n_sws],
        'n_sw_mean': float(n_sws.mean()),
        'rho_sig_st_per_seed': [float(x) for x in rho_sig_arr],
        'rho_sig_st_mean': float(rho_sig_arr.mean()),
        'rho_sig_st_std':  float(rho_sig_arr.std()),
    }


def pack_per_seed(per_seed):
    return [{
        'seed': s['seed'],
        'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
        'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
        'n_sw': s['n_sw'].tolist(),
        'kura_mean': s['kura_mean'], 'kura_std': s['kura_std'],
        'phase_stats': s['phase_stats'],
    } for s in per_seed]


def main():
    start = datetime.now()
    print("Thor Session #109: Phase-Ensemble Spread Mechanism (S108-P3/P6)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: A={A_SIGNAL}  σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks × {CHUNK_STEPS} steps")
    print(f"Phase decimate: every {PHASE_DECIMATE} steps "
          f"({CHUNK_STEPS*N_CHUNKS//PHASE_DECIMATE} samples/seed post-warmup)")

    # Seed codes: 9_PP_CC_R where PP=kp·100, CC=kC·100, R=ratio·10.
    # Kept under 2**32 so each base + 0..N_SEEDS-1 fits in numpy's seed range.
    cells = [
        # (κ_p, κ_C, ω_spread, seed_base, label, notes)
        (0.30, 0.00, 0.060, 9_030_00_2, 'kp030_kC000_r02',
         'κ_C=0 control, ratio 0.2'),
        (0.30, 0.30, 0.060, 9_030_30_2, 'kp030_kC030_r02',
         'ridge peak, ratio 0.2 (deep coherent)'),
        (0.30, 0.00, 0.240, 9_030_00_8, 'kp030_kC000_r08',
         'κ_C=0 control, ratio 0.8'),
        (0.30, 0.30, 0.240, 9_030_30_8, 'kp030_kC030_r08',
         'ridge peak, ratio 0.8 (near desync)'),
        (0.50, 0.00, 0.400, 9_050_00_8, 'kp050_kC000_r08',
         'sign-reversal regime: κ_p↑ hurts ρ_sig at κ_C=0'),
        (0.50, 0.30, 0.400, 9_050_30_8, 'kp050_kC030_r08',
         'S107 highest-R_coh cell: κ_p↑ helps ρ_sig at ridge'),
    ]

    cell_results = {}
    for kp, kC, omega, sb, label, notes in cells:
        ps = run_cell(kappa_phase=kp, kappa_C=kC,
                      omega_spread=omega, seed_base=sb)
        summary = summarize_cell(ps)
        print(f"   ⇒ {label}: "
              f"RAW R={summary['raw_R_coh_mean']:.3f}±{summary['raw_R_coh_std']:.3f}  "
              f"ST R={summary['st_R_coh_mean']:.3f}±{summary['st_R_coh_std']:.3f}  "
              f"σ_φ={summary['sigma_phi_deg_mean']:.1f}°  "
              f"R_inst={summary['R_inst_mean']:.3f}  "
              f"ρ_sig_st={summary['rho_sig_st_mean']:.4f}  "
              f"Nsw={summary['n_sw_mean']:.0f}")
        cell_results[label] = {
            'kappa_phase': kp, 'kappa_C': kC, 'omega_spread': omega,
            'ratio_omega_over_kappa_phase': omega / kp if kp > 0 else float('inf'),
            'seed_base': sb, 'notes': notes,
            'summary': summary,
            'per_seed_z': pack_per_seed(ps),
        }

    out = {
        'meta': {
            'session': 109,
            'title': 'Phase-Ensemble Spread Mechanism (S108-P3/P6)',
            'started': start.isoformat(),
            'common_params': {
                'A': A_SIGNAL, 'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'kura_decimate': KURA_DECIMATE,
                'phase_decimate': PHASE_DECIMATE,
            },
            'design_notes': {
                'purpose': 'Direct mechanism test for S108 ρ_sig asymmetry: '
                           'is phase-ensemble spread the driver?',
                'P1_S108_literal': 'σ_φ smaller at ratio 0.2 — S108-P6.',
                'P2_R_kura_consistent': 'σ_φ LARGER at ratio 0.2 — falsifies S108-P6.',
                'P3_bimodal': 'Pairwise |Δφ| bimodal at deep coherent.',
                'P4_drive_diversity': 'σ_cos tracks ρ_sig across cells.',
                'P5_signreversal': 'kp050_kC000_r08 σ_φ < kp030_kC000_r08 σ_φ.',
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_109_phase_spread_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_109_phase_spread_results.json")


if __name__ == '__main__':
    main()
