#!/usr/bin/env python3
"""Thor Session #104: Is the R_coh cliff a Kuramoto desync transition?

Context (from S103)
-------------------
At A=0.30, σ=0.022 with κ_phase=0.10, per-seed coherent fraction was
nearly invariant ω_spread 0.02→0.04 (R_coh_RAW 0.38→0.39) but dropped
at 0.08 (R_coh_RAW 0.27).  S103 framed this as a follow-up: where is
the critical ω_spread* and what mechanism sets it?

Hypothesis (Kuramoto-on-bistable)
---------------------------------
The simulator phase-couples N=4 oscillators via ±κ_phase·sin(Δφ)/(N-1)
(sign depends on whether C_mean is above/below threshold). The natural
frequencies are uniform on [ω_base-Δ, ω_base+Δ] with Δ ≡ ω_spread.
Classical Kuramoto on uniform[-Δ,Δ]: K_c = 4Δ/π → Δ_c = πK/4 ≈ 0.079
for K=κ_phase=0.10. That is exactly where R_coh starts dropping in S103.

If the cliff is Kuramoto-driven, R_coh should depend only on the
dimensionless ratio Δω/κ_phase — NOT on κ_phase or Δω separately.

Design
------
Two sweeps at A=0.30, σ=0.022, signal_freq=0.003.

Sweep A — fine ω_spread at κ_phase=0.10 (fills S103 gaps):
    ω_spread ∈ {0.005, 0.06, 0.10, 0.13}

Sweep B — κ_phase at fixed ω_spread, to test ratio invariance:
    (κ, ω): (0.05, 0.04) ratio 0.8  → predict R_coh ≈ S103(κ=0.10, ω=0.08)
    (0.20, 0.04) ratio 0.2          → predict R_coh ≈ S103(κ=0.10, ω=0.02)
    (0.20, 0.16) ratio 0.8          → predict R_coh ≈ S103(κ=0.10, ω=0.08)

Cost
----
8 seeds × 50 chunks × 40k steps = 16M steps per cell.
Per S103 timing (97s for 100 chunks × 40k steps × 1 seed): ~50s/seed,
~7 min/cell. 7 cells ≈ 50 min total.
"""
import json
import sys
import time
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

# Reuse the canonical simulator and detectors. Note: the original
# `simulate` is fine for sweep A (κ_phase default 0.10). For sweep B we
# need to override κ_phase per-cell, and the original `simulate`
# accepts kappa_phase as a kwarg already, so just pass it in.
from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55
SIGNAL_FREQ = 0.003
A_SIGNAL = 0.30
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
T_CHUNK_S = CHUNK_STEPS * DT  # 4000 s
N_SEEDS = 8
N_CHUNKS = 50


def run_cell(omega_spread, kappa_phase, seed_base,
             n_chunks=N_CHUNKS, n_seeds=N_SEEDS):
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> κ={kappa_phase:.2f}  ω_spread={omega_spread:.4f}  "
          f"ratio={omega_spread/kappa_phase:.2f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  "
          f"steps={total_steps}  seed_base={seed_base}")
    per_seed = []
    cell_start = time.time()
    for s in range(n_seeds):
        t0 = time.time()
        x = simulate(N=4, noise_std=SIGMA_NOISE, steps=total_steps,
                     seed=seed_base + s,
                     kappa_phase=kappa_phase,
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
        })
        elapsed = time.time() - t0
        print(f"   seed={seed_base+s:6d}  {elapsed:5.1f}s   "
              f"|<z_raw>|={abs(z_raw.mean()):.4e}   "
              f"|<z_st>|={abs(z_st.mean()):.3f}   "
              f"N_sw/chunk={n_sw.mean():.0f}")
    print(f"   total {time.time()-cell_start:.0f}s")
    return per_seed


def per_seed_R_coh(z_list):
    """Returns R_coh per seed = |μ|² / (|μ|² + σ_n²)."""
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
    """Rayleigh-R of per-seed mean-response angles."""
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
        'n_sw_per_seed': n_sw_per_seed,
    }


def pack_per_seed(per_seed):
    return [{
        'seed': s['seed'],
        'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
        'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
        'n_sw': s['n_sw'].tolist(),
    } for s in per_seed]


def main():
    start = datetime.now()
    print("Thor Session #104: Kuramoto desync test for R_coh cliff")
    print(f"Started: {start.isoformat()}")
    print(f"Common: A={A_SIGNAL}  σ={SIGMA_NOISE}  signal_freq={SIGNAL_FREQ}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks × {CHUNK_STEPS} steps")

    # (kappa_phase, omega_spread, seed_base, label)
    cells = [
        # Sweep A: ω_spread fine sweep at κ=0.10
        (0.10, 0.005, 104_010, 'sA_w0005'),
        (0.10, 0.060, 104_060, 'sA_w060'),
        (0.10, 0.100, 104_100, 'sA_w100'),
        (0.10, 0.130, 104_130, 'sA_w130'),
        # Sweep B: κ_phase variation at fixed ω, testing ratio invariance
        (0.05, 0.040, 104_205, 'sB_k005_w040'),  # ratio 0.80
        (0.20, 0.040, 104_220, 'sB_k020_w040'),  # ratio 0.20
        (0.20, 0.160, 104_216, 'sB_k020_w160'),  # ratio 0.80
    ]

    cell_results = {}
    for kappa, omega, sb, label in cells:
        ps = run_cell(omega_spread=omega, kappa_phase=kappa, seed_base=sb)
        summary = summarize_cell(ps)
        print(f"   ⇒ {label}: RAW R_coh={summary['raw_R_coh_mean']:.3f} "
              f"± {summary['raw_R_coh_std']:.3f}   "
              f"ST R_coh={summary['st_R_coh_mean']:.3f} "
              f"± {summary['st_R_coh_std']:.3f}   "
              f"R_angle RAW/ST = {summary['cross_seed_R_angle_raw']:.3f} "
              f"/ {summary['cross_seed_R_angle_st']:.3f}")
        cell_results[label] = {
            'kappa_phase': kappa, 'omega_spread': omega,
            'ratio_omega_over_kappa': omega / kappa,
            'seed_base': sb,
            'summary': summary,
            'per_seed_z': pack_per_seed(ps),
        }

    out = {
        'meta': {
            'session': 104,
            'title': 'Kuramoto desync test for R_coh cliff (S103-P1)',
            'started': start.isoformat(),
            'common_params': {
                'A': A_SIGNAL, 'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
            },
            'design_notes': {
                'sweep_A_purpose': 'fine ω_spread fill at κ=0.10 to locate cliff',
                'sweep_B_purpose': 'κ_phase variation testing R_coh = f(ω/κ) only',
                'kuramoto_prediction': 'K_c = 4Δ/π for uniform; for κ=0.10 → Δ_c≈0.079',
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_104_kuramoto_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_104_kuramoto_results.json")


if __name__ == '__main__':
    main()
