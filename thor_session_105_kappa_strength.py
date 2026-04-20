#!/usr/bin/env python3
"""Thor Session #105: κ-strength enhancement of R_coh beyond Kuramoto ratio.

Context (S104, S104-P1)
-----------------------
S104 located the R_coh cliff at ω_spread* ≈ 0.080 for κ_phase=0.10, matching
Kuramoto Δ_c = πκ/4 = 0.0785 to +2%. Ratio invariance R_coh = f(ω/κ) held
from κ=0.05→κ=0.10 (at ratio 0.8, R_raw = 0.289 vs 0.271, within 1σ) but
BROKE at κ=0.20 (ratio 0.8, R_raw = 0.515 — nearly 2× the κ=0.10 cell).

S104-P1 asks: is this a real coupling-strength enhancement, or an N=4
finite-size noise artifact?  If R_coh rises monotonically with κ at fixed
ratio ω/κ, there is an additional physics beyond pure Kuramoto.

Design
------
Fixed: A=0.30, σ=0.022, signal_freq=0.003, N=4, n_seeds=8, n_chunks=50.

Sweep κ ∈ {0.05, 0.15, 0.30, 0.50} at fixed ratio ω/κ = 0.8 (just below
the Kuramoto cliff at ratio 1.0).  Existing cells from S104 at ratio 0.8:
κ ∈ {0.05, 0.10, 0.20}.  With S105 additions we get six κ rungs.

Sweep κ ∈ {0.05, 0.30, 0.50} at fixed ratio ω/κ = 0.2 (deep in sync).
Existing cells from S103/S104 at ratio 0.2: κ ∈ {0.10 (S98/S103), 0.20 (S104 k020_w040)}.
With S105 additions we get five κ rungs in the plateau too.

Also measure the Kuramoto order parameter R_kura = |<e^{iφ_k}>_k| of the
phase oscillators directly.  If R_coh scales linearly with R_kura across
cells, R_coh enhancement IS just Kuramoto enhancement (stronger coupling
→ tighter phase locking → larger coherent signal component).  If R_coh
scales with κ beyond what R_kura explains, there is a separate effect
(e.g., the bistable C-dynamics amplifying a small coherent drive).

Cost
----
8 seeds × 50 chunks × 40k steps = 16M steps per cell.
R_kura sampling every 10 steps adds ≤ 20% CPU overhead (small 4-vector op).
Expected: ~8 min/cell, 7 cells ≈ 55 min.
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
N_CHUNKS = 50
KURA_DECIMATE = 10  # sample R_kura every 10 steps


def simulate_with_kura(N, noise_std, steps, seed,
                       kappa_phase=0.10, kappa_C=0.15,
                       omega_base=0.1, omega_spread=0.02,
                       phi_inverse=0.618, dt=0.1,
                       C_threshold=0.55,
                       signal_freq=0.003, signal_amp=0.0):
    """Canonical simulate() but also records Kuramoto-R (post-warmup, decimated).

    Returns (C_mean_hist, R_kura_mean, R_kura_std) where the kura stats are
    computed over the post-warmup trajectory, decimated by KURA_DECIMATE.
    """
    np.random.seed(seed)
    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)
    C_mean_hist = np.empty(steps)
    # Pre-allocate kura samples (post-warmup only).
    post_warm_len = max(0, steps - WARMUP)
    n_kura = post_warm_len // KURA_DECIMATE + 1
    kura_samples = np.empty(n_kura)
    k_idx = 0
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
        if t >= WARMUP and (t - WARMUP) % KURA_DECIMATE == 0:
            z_sum = np.mean(np.exp(1j * phase))
            kura_samples[k_idx] = abs(z_sum)
            k_idx += 1
    kura_samples = kura_samples[:k_idx]
    return C_mean_hist, float(kura_samples.mean()), float(kura_samples.std())


def run_cell(kappa, omega_spread, seed_base,
             n_chunks=N_CHUNKS, n_seeds=N_SEEDS):
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    ratio = omega_spread / kappa
    print(f"\n>> κ={kappa:.3f}  ω_spread={omega_spread:.4f}  "
          f"ratio={ratio:.2f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  "
          f"steps={total_steps}  seed_base={seed_base}")
    per_seed = []
    cell_start = time.time()
    for s in range(n_seeds):
        t0 = time.time()
        x, kura_mean, kura_std = simulate_with_kura(
            N=4, noise_std=SIGMA_NOISE, steps=total_steps,
            seed=seed_base + s,
            kappa_phase=kappa,
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
        per_seed.append({
            'seed': seed_base + s,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw': n_sw,
            'kura_mean': kura_mean, 'kura_std': kura_std,
        })
        elapsed = time.time() - t0
        print(f"   seed={seed_base+s:6d}  {elapsed:5.1f}s   "
              f"|<z_raw>|={abs(z_raw.mean()):.3e}   "
              f"|<z_st>|={abs(z_st.mean()):.3f}   "
              f"<R_kura>={kura_mean:.3f} ± {kura_std:.3f}   "
              f"N_sw/chunk={n_sw.mean():.0f}")
    print(f"   total {time.time()-cell_start:.0f}s")
    return per_seed


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


def summarize_cell(per_seed):
    z_raws = [s['z_raw'] for s in per_seed]
    z_sts = [s['z_st'] for s in per_seed]
    raw_stats = per_seed_R_coh(z_raws)
    st_stats = per_seed_R_coh(z_sts)

    def agg(stats, key):
        v = np.array([s[key] for s in stats])
        return float(v.mean()), float(v.std())

    raw_R, raw_R_sd = agg(raw_stats, 'R_coh')
    st_R, st_R_sd = agg(st_stats, 'R_coh')
    raw_mu, raw_mu_sd = agg(raw_stats, 'mu_abs')
    st_mu, st_mu_sd = agg(st_stats, 'mu_abs')
    raw_sn, _ = agg(raw_stats, 'sigma_n')
    st_sn, _ = agg(st_stats, 'sigma_n')
    R_angle_raw = cross_seed_angle_R(raw_stats)
    R_angle_st = cross_seed_angle_R(st_stats)
    kura = np.array([s['kura_mean'] for s in per_seed])
    kura_std_within = np.array([s['kura_std'] for s in per_seed])
    n_sw_per_seed = [float(np.mean(s['n_sw'])) for s in per_seed]

    return {
        'raw_per_seed': raw_stats,
        'st_per_seed': st_stats,
        'raw_R_coh_mean': raw_R, 'raw_R_coh_std': raw_R_sd,
        'st_R_coh_mean': st_R, 'st_R_coh_std': st_R_sd,
        'raw_mu_mean': raw_mu, 'raw_mu_std': raw_mu_sd,
        'st_mu_mean': st_mu, 'st_mu_std': st_mu_sd,
        'raw_sigma_n_mean': raw_sn, 'st_sigma_n_mean': st_sn,
        'cross_seed_R_angle_raw': R_angle_raw,
        'cross_seed_R_angle_st': R_angle_st,
        'R_kura_cross_seed_mean': float(kura.mean()),
        'R_kura_cross_seed_std': float(kura.std()),
        'R_kura_within_seed_mean_std': float(kura_std_within.mean()),
        'n_sw_per_seed': n_sw_per_seed,
    }


def pack_per_seed(per_seed):
    return [{
        'seed': s['seed'],
        'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
        'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
        'n_sw': s['n_sw'].tolist(),
        'kura_mean': s['kura_mean'], 'kura_std': s['kura_std'],
    } for s in per_seed]


def main():
    start = datetime.now()
    print("Thor Session #105: κ-strength enhancement of R_coh (S104-P1)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: A={A_SIGNAL}  σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks × {CHUNK_STEPS} steps")

    # (kappa, omega_spread, seed_base, label)
    cells = [
        # Ratio 0.8 sweep — new cells to fill out S104's ratio-0.8 ladder.
        # (κ=0.05, 0.10, 0.20 already in S104; this adds 0.15, 0.30, 0.50.)
        (0.15, 0.120, 105_015, 'r08_k015'),
        (0.30, 0.240, 105_030, 'r08_k030'),
        (0.50, 0.400, 105_050, 'r08_k050'),
        # Ratio 0.2 sweep — plateau check at wider κ range.
        # (κ=0.10, 0.20 already in S103/S104; this adds 0.05, 0.30, 0.50.)
        (0.05, 0.010, 105_205, 'r02_k005'),
        (0.30, 0.060, 105_230, 'r02_k030'),
        (0.50, 0.100, 105_250, 'r02_k050'),
    ]

    cell_results = {}
    for kappa, omega, sb, label in cells:
        ps = run_cell(kappa=kappa, omega_spread=omega, seed_base=sb)
        summary = summarize_cell(ps)
        print(f"   ⇒ {label}: "
              f"RAW R_coh={summary['raw_R_coh_mean']:.3f} ± {summary['raw_R_coh_std']:.3f}   "
              f"ST R_coh={summary['st_R_coh_mean']:.3f} ± {summary['st_R_coh_std']:.3f}   "
              f"R_angle RAW/ST = {summary['cross_seed_R_angle_raw']:.3f} / {summary['cross_seed_R_angle_st']:.3f}   "
              f"<R_kura>={summary['R_kura_cross_seed_mean']:.3f} ± {summary['R_kura_cross_seed_std']:.3f}")
        cell_results[label] = {
            'kappa_phase': kappa, 'omega_spread': omega,
            'ratio_omega_over_kappa': omega / kappa,
            'seed_base': sb,
            'summary': summary,
            'per_seed_z': pack_per_seed(ps),
        }

    out = {
        'meta': {
            'session': 105,
            'title': 'κ-strength enhancement of R_coh (S104-P1)',
            'started': start.isoformat(),
            'common_params': {
                'A': A_SIGNAL, 'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'kura_decimate': KURA_DECIMATE,
            },
            'design_notes': {
                'purpose': 'Test if R_coh at fixed ω/κ ratio depends on κ alone',
                'null_hypothesis': 'R_coh = f(ω/κ) only (pure Kuramoto).',
                'alt_hypothesis': 'R_coh rises with κ at fixed ratio (strong-coupling enhancement).',
                'new_observable': 'R_kura = |<e^{iφ_k}>_k| of phase oscillators, post-warmup, decimated by 10.',
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_105_kappa_strength_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_105_kappa_strength_results.json")


if __name__ == '__main__':
    main()
