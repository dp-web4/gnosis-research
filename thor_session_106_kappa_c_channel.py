#!/usr/bin/env python3
"""Thor Session #106: Channel Isolation — Does kappa_C carry the κ-gain, or only kappa_phase?

Context (S105, S105-P4)
-----------------------
S105 showed R_coh rises ~linearly with kappa_phase at fixed ω/kappa_phase ratio,
slope +0.94 at ratio 0.8 (r²=0.89). R_kura stays ~flat, so the κ-gain is NOT
mediated through bare Kuramoto phase locking. S105 hypothesized the channel is
kappa_phase's signal-gated amplification of the Σcos(φₖ) drive on C-dynamics —
i.e., the enhancement enters purely through the PHASE coupling, not the
C-coupling term.

The simulator has TWO coupling constants:
  - kappa_phase: scales sin_diff.sum() in the phase ODE, with a SIGN FLIP
    gated by (C_mean + signal) < C_threshold. This is the only channel through
    which the signal influences the dynamics.
  - kappa_C: scales (C_mean - C) * R_func in the C ODE — a passive
    mean-reverting coupling between C components. It does NOT see the signal.

If the S105 hypothesis is right, R_coh should be INSENSITIVE to kappa_C at
fixed kappa_phase. If R_coh also rises with kappa_C, the enhancement has a
C-coupling component we missed.

Design
------
Primary sweep: fix kappa_phase=0.30, ω_spread=0.24 (ratio 0.80, S105 r08_k030,
known R_raw=0.559 ± 0.110). Sweep kappa_C ∈ {0.00, 0.05, 0.15, 0.30, 0.50}.
  - kappa_C=0.00 disables C-coupling entirely (each C is independent bistable)
  - kappa_C=0.15 is simulator default (S105 r08_k030 data reused from S105)
  - kappa_C=0.50 is 3.3× default

Null control: kappa_phase=0.00, kappa_C=0.15. With no phase coupling the
signal has NO path to affect dynamics (signal enters only via the sign-flip
gate on kappa_phase). Expected R_coh ≈ noise floor. If not, we've misread
the simulator.

Sanity control: kappa_phase=0.10 (S105 baseline weak-coupling), kappa_C=0.50.
Paired with kappa_phase=0.10 kappa_C=0.15 (recycled from S103 omega_spread=0.08
cell). Tests whether kappa_C independence holds at weaker kappa_phase too,
or is a strong-coupling-specific invariance.

Observables: per-seed R_coh (RAW and ST), cross-seed R_angle, R_kura (phase
oscillator Kuramoto order parameter, decimated by 10), switch count per chunk.

Cost
----
8 seeds × 50 chunks × 40k steps + 10k warmup = 2.01 M steps per seed.
At ~25 μs/step, ~50 s/seed, ~7 min/cell. 6 new cells ≈ 42 min.
(Cells recycled from prior sessions: r08_k030 from S105 at kappa_C=0.15 primary
point, S103 ω=0.08 run for kappa_phase=0.10 kappa_C=0.15.)

Predictions
-----------
H0 (S105 mechanism — phase-coupling channel only):
    R_coh nearly invariant under kappa_C sweep.
    |dR/dkappa_C| < 0.2 (compare with dR/dkappa_phase ~ 0.94 at ratio 0.8).

H1 (C-coupling also contributes):
    R_coh rises with kappa_C at fixed kappa_phase, slope > 0.3.

H2 (coupling channel swap — signal only through C-dynamics):
    R_coh FALLS as kappa_C rises (signal has less room in mean-reverting pool)
    — not expected, but listed for completeness.

Null:
    kappa_phase=0 must give R_coh ≈ 0.006 (floor from S103 A=0 control).
    If R_coh > 0.05 at kappa_phase=0, something is wrong with the simulator
    or the matched filter.
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
KURA_DECIMATE = 10


def simulate_with_kura(N, noise_std, steps, seed,
                       kappa_phase=0.10, kappa_C=0.15,
                       omega_base=0.1, omega_spread=0.02,
                       phi_inverse=0.618, dt=0.1,
                       C_threshold=0.55,
                       signal_freq=0.003, signal_amp=0.0):
    """Canonical simulate() from S93 + Kuramoto-R observable.

    Identical to S105's simulate_with_kura. Returns
    (C_mean_hist, R_kura_mean, R_kura_std) — kura stats are post-warmup
    decimated averages of |<e^{iφ_k}>_k|.
    """
    np.random.seed(seed)
    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)
    C_mean_hist = np.empty(steps)
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
        x, kura_mean, kura_std = simulate_with_kura(
            N=4, noise_std=SIGMA_NOISE, steps=total_steps,
            seed=seed_base + s,
            kappa_phase=kappa_phase,
            kappa_C=kappa_C,
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
    print("Thor Session #106: κ_C channel isolation (S105-P4)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: A={A_SIGNAL}  σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks × {CHUNK_STEPS} steps")

    # (kappa_phase, kappa_C, omega_spread, seed_base, label)
    cells = [
        # Primary sweep: vary kappa_C at kappa_phase=0.30, ω=0.24 (ratio 0.8).
        # kappa_C=0.15 is recycled from S105 r08_k030 (R_raw=0.559).
        (0.30, 0.00, 0.240, 106_030_000, 'kp030_kC000'),
        (0.30, 0.05, 0.240, 106_030_005, 'kp030_kC005'),
        (0.30, 0.30, 0.240, 106_030_030, 'kp030_kC030'),
        (0.30, 0.50, 0.240, 106_030_050, 'kp030_kC050'),
        # Null control: kappa_phase=0 — signal cannot affect dynamics.
        (0.00, 0.15, 0.240, 106_000_015, 'kp000_kC015_NULL'),
        # Sanity: does kappa_C insensitivity hold at weak kappa_phase?
        (0.10, 0.50, 0.080, 106_010_050, 'kp010_kC050_ratio08'),
    ]

    cell_results = {}
    for kp, kC, omega, sb, label in cells:
        ps = run_cell(kappa_phase=kp, kappa_C=kC,
                      omega_spread=omega, seed_base=sb)
        summary = summarize_cell(ps)
        print(f"   ⇒ {label}: "
              f"RAW R_coh={summary['raw_R_coh_mean']:.3f} ± {summary['raw_R_coh_std']:.3f}   "
              f"ST R_coh={summary['st_R_coh_mean']:.3f} ± {summary['st_R_coh_std']:.3f}   "
              f"R_angle RAW/ST = {summary['cross_seed_R_angle_raw']:.3f} / {summary['cross_seed_R_angle_st']:.3f}   "
              f"<R_kura>={summary['R_kura_cross_seed_mean']:.3f} ± {summary['R_kura_cross_seed_std']:.3f}")
        cell_results[label] = {
            'kappa_phase': kp, 'kappa_C': kC, 'omega_spread': omega,
            'ratio_omega_over_kappa_phase': omega / kp if kp > 0 else float('inf'),
            'seed_base': sb,
            'summary': summary,
            'per_seed_z': pack_per_seed(ps),
        }

    out = {
        'meta': {
            'session': 106,
            'title': 'κ_C channel isolation (S105-P4)',
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
                'purpose': 'Isolate whether κ-enhancement acts through kappa_phase or kappa_C.',
                'H0_phase_only': 'dR/dkappa_C ≈ 0 at fixed kappa_phase.',
                'H1_C_also':  'R_coh rises with kappa_C at fixed kappa_phase.',
                'null_sim_check': 'kappa_phase=0 cell should have R_coh ≈ noise floor.',
            },
            'recycle_note': 'r08_k030 from S105 (kappa_phase=0.30, kappa_C=0.15) is reused as kappa_C=0.15 point in the primary sweep — NOT re-run here.',
        },
        'cells': cell_results,
    }
    with open('thor_session_106_kappa_c_channel_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_106_kappa_c_channel_results.json")


if __name__ == '__main__':
    main()
