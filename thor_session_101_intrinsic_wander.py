#!/usr/bin/env python3
"""
Thor Session #101: Is the 22ks Raw-Channel Wander Intrinsic or Signal-Induced?

Context
-------
S99 reanalysis of S98's long-chunked data found raw-channel per-chunk MF
residual-phase ACF decays exponentially with τ_res ≈ 21,000s (R²=0.97)
at σ=0.022, A=0.30. S100 confirmed τ_res is σ-invariant (21ks at σ=0.022,
23ks at σ=0.060 — same within ~10%). This points to the N=4 deterministic
collective dynamics as the origin, not switching noise.

Two open predictions resolve this:
  S100-P3: Run the A=0 control. If raw-channel z itself (chunk-to-chunk,
           NOT residual relative to signal) has the same ~22ks ACF, the
           wander is fully intrinsic to the dynamics. If it's white, the
           wander requires signal drive.
  S100-P2: Sweep omega_spread. If τ_wander ∝ 1/Δω, the wander timescale
           is set by the spread of individual oscillator frequencies
           within the N=4 collective — direct evidence it's phase-drift
           in the collective.

This session runs both.

Part A: A=0, σ=0.022, ω_spread=0.02 (canonical), 8 seeds × 400ks.
        Measure z_raw, z_st chunk ACF directly (no signal → no "residual"
        needed; the chunk MF output IS the noise at f_s).

Part B: A=0, σ=0.022, ω_spread ∈ {0, 0.005, 0.02, 0.08}, 4 seeds × 200ks.
        Measure τ_wander of z_raw vs ω_spread. Tests the 1/Δω scaling.

Compute budget:
  Part A: 8 seeds × 4,010,000 steps × 25µs ≈ 800s = 13 min
  Part B: 16 seeds × 2,010,000 steps × 25µs ≈ 800s = 13 min
  Total ≈ 26 min.

Detectors reused as-is:
  - phase_coherent_IQ (raw matched filter)
  - switch_timing_IQ  (point-process matched filter)
  - autocorr_channel  (S98: complex ACF, |Φ(m)|, var_dφ)
  - run_long_chunked  (S98: long-trajectory chunking)
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_98_phase_drift import (
    autocorr_channel,
    fit_phase_diffusion,
    fit_rotation_rate,
    per_seed_phase_stats,
)

C_THRESHOLD = 0.55


def run_long_chunked_omega(sigma, A, n_seeds, total_steps, warmup,
                           chunk_steps, omega_spread,
                           dt=0.1, signal_freq=0.003, seed_base=1000):
    """Same as S98 run_long_chunked, but with configurable omega_spread.
    The S98 version pinned omega_spread=0.02 through the simulate default.
    """
    print(f"\n>> long-chunk run: σ={sigma}, A={A}, ω_spread={omega_spread}, "
          f"n_seeds={n_seeds}, total_steps={total_steps}, "
          f"chunk_steps={chunk_steps}")
    per_seed = []
    start = datetime.now()
    for seed in range(n_seeds):
        t0 = datetime.now()
        x = simulate(N=4, noise_std=sigma, steps=total_steps,
                     seed=seed_base + seed,
                     signal_freq=signal_freq, signal_amp=A, dt=dt,
                     omega_spread=omega_spread)
        xp = x[warmup:]
        n_chunks = len(xp) // chunk_steps

        z_raw = np.zeros(n_chunks, dtype=complex)
        z_st = np.zeros(n_chunks, dtype=complex)
        n_sw = np.zeros(n_chunks, dtype=int)

        for c in range(n_chunks):
            chunk = xp[c * chunk_steps:(c + 1) * chunk_steps]
            t_off = warmup + c * chunk_steps
            I_r, Q_r = phase_coherent_IQ(chunk, dt, signal_freq,
                                         t_offset=t_off)
            I_s, Q_s, n = switch_timing_IQ(chunk, dt, signal_freq,
                                           t_offset=t_off,
                                           threshold=C_THRESHOLD)
            z_raw[c] = I_r + 1j * Q_r
            z_st[c] = I_s + 1j * Q_s
            n_sw[c] = n

        elapsed = (datetime.now() - t0).total_seconds()
        per_seed.append({
            'seed': seed_base + seed,
            'n_chunks': n_chunks,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw': n_sw,
        })
        print(f"   seed={seed_base + seed:6d}  n_chunks={n_chunks}  "
              f"{elapsed:5.1f}s  "
              f"|mean(z_raw)|={np.abs(z_raw.mean()):.3e}  "
              f"|mean(z_st)|={np.abs(z_st.mean()):.3e}  "
              f"mean(N_sw)/chunk={n_sw.mean():.1f}")

    total_elapsed = (datetime.now() - start).total_seconds()
    print(f"   [total {total_elapsed:.1f}s for {n_seeds} seeds]")
    return per_seed


def fit_tau_from_rho(rho, lags_time_s, rho_floor=0.05):
    """Fit τ_wander from rho(m) = exp(-m·dt/τ) on lags with rho > floor."""
    rho = np.array(rho)
    lags_time_s = np.array(lags_time_s)
    ok = (rho > rho_floor) & (lags_time_s > 0)
    if ok.sum() < 3:
        return None
    y = np.log(rho[ok])
    x = lags_time_s[ok]
    slope, intercept = np.polyfit(x, y, 1)
    tau = -1.0 / slope if slope < 0 else float('inf')
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred)**2))
    ss_tot = float(np.sum((y - y.mean())**2))
    R2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        'tau_s': float(tau),
        'R2': float(R2),
        'n_fit': int(ok.sum()),
        'slope': float(slope),
        'intercept': float(intercept),
        'max_lag_s_used': float(x.max()),
    }


def summarize_channel_null(name, per_seed, max_lag, chunk_time_s):
    """Compute ACF curves for one channel. With A=0 we can't define a
    'response angle', so we compute:
      - |C_full(m)| : full complex ACF magnitude (amp+phase jointly)
      - Φ(m)       : phase-only ACF (circular ACF of arg(z_k))
      - ρ_abs(m)   : amplitude-only ACF ⟨|z_k||z_{k+m}|⟩/⟨|z|²⟩
    and fit each to exp(-t/τ).
    """
    z_list = [s[name] for s in per_seed]
    ac = autocorr_channel(z_list, max_lag)
    lags_time = np.arange(max_lag + 1) * chunk_time_s

    # Normalize amplitude ACF so ρ(0)=1 (autocorr_channel gives us
    # ρ_abs(0) = ⟨|z|²⟩/⟨|z|²⟩ = 1 already).
    rho_abs = np.array(ac['rho_abs'])
    # Center the amplitude ACF around its asymptote: true ⟨|z_k||z_{k+m}|⟩
    # under uniform phase goes to ⟨|z|⟩² (not 0) as m→∞. So subtract the
    # asymptote for a proper exp fit.
    rho_abs_centered = rho_abs - rho_abs[-5:].mean()
    # Rescale so centered(0) = 1 for readability.
    if abs(rho_abs_centered[0]) > 1e-6:
        rho_abs_centered = rho_abs_centered / rho_abs_centered[0]

    # Complex ACF magnitude: full |C_full(m)| — falls to 0 at m=∞.
    C_full = np.array([complex(v[0], v[1])
                       if isinstance(v, (list, tuple)) else v
                       for v in ac['C_full']])
    C_abs = np.abs(C_full)

    Phi = np.array(ac['Phi'])
    Phi_abs = np.abs(Phi)

    fits = {
        'tau_Cfull':  fit_tau_from_rho(C_abs, lags_time),
        'tau_Phi':    fit_tau_from_rho(Phi_abs, lags_time),
        'tau_rhoabs': fit_tau_from_rho(rho_abs_centered, lags_time),
    }

    return {
        'channel': name,
        'lags_time_s': lags_time.tolist(),
        'C_full_abs': C_abs.tolist(),
        'Phi_abs': Phi_abs.tolist(),
        'rho_abs_raw': rho_abs.tolist(),
        'rho_abs_asym': float(rho_abs[-5:].mean()),
        'rho_abs_centered': rho_abs_centered.tolist(),
        'mean_z2': ac['mean_z2'],
        'fits': fits,
        'per_seed_stats': per_seed_phase_stats(z_list),
    }


def print_summary_row(sigma, A, omega_spread, channel_summary):
    f_c = channel_summary['fits']['tau_Cfull']
    f_p = channel_summary['fits']['tau_Phi']
    f_r = channel_summary['fits']['tau_rhoabs']
    c_abs = channel_summary['C_full_abs']
    p_abs = channel_summary['Phi_abs']
    mean_mag = np.sqrt(channel_summary['mean_z2'])
    print(f"  A={A:.2f} σ={sigma} ωsp={omega_spread:.3f}  "
          f"{channel_summary['channel']}:")
    print(f"    mean|z|={mean_mag:.3e}  "
          f"|C_full| first 6 = "
          f"[{', '.join(f'{v:.3f}' for v in c_abs[:6])}]")
    print(f"    |Φ|     first 6 = "
          f"[{', '.join(f'{v:.3f}' for v in p_abs[:6])}]")
    if f_c:
        print(f"    τ(C_full) = {f_c['tau_s']:.0f}s  R²={f_c['R2']:.2f}  "
              f"n_fit={f_c['n_fit']}")
    if f_p:
        print(f"    τ(|Φ|)   = {f_p['tau_s']:.0f}s  R²={f_p['R2']:.2f}  "
              f"n_fit={f_p['n_fit']}")
    if f_r:
        print(f"    τ(|z|-amp) = {f_r['tau_s']:.0f}s  R²={f_r['R2']:.2f}  "
              f"n_fit={f_r['n_fit']}")


if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #101: Intrinsic vs Signal-Induced Wander")
    print(f"Started: {start.isoformat()}\n")

    dt = 0.1
    signal_freq = 0.003
    warmup = 10_000
    T_CHUNK_S = 4000.0
    chunk_steps = int(T_CHUNK_S / dt)  # 40,000

    # ── Part A: A=0 null control (S100-P3) ──
    PART_A_SIGMA = 0.022
    PART_A_A = 0.0
    PART_A_OMEGA = 0.02
    PART_A_N_SEEDS = 8
    PART_A_TOTAL_STEPS = warmup + 100 * chunk_steps  # 400,000s
    PART_A_MAX_LAG = 60

    print("=" * 72)
    print("PART A: A=0 null at σ=0.022, ω_spread=0.02, 8 seeds × 400,000s")
    print("=" * 72)
    part_a_ps = run_long_chunked_omega(
        sigma=PART_A_SIGMA, A=PART_A_A, n_seeds=PART_A_N_SEEDS,
        total_steps=PART_A_TOTAL_STEPS, warmup=warmup,
        chunk_steps=chunk_steps, omega_spread=PART_A_OMEGA,
        dt=dt, signal_freq=signal_freq, seed_base=101_000)
    part_a_raw = summarize_channel_null('z_raw', part_a_ps,
                                        PART_A_MAX_LAG, T_CHUNK_S)
    part_a_st = summarize_channel_null('z_st', part_a_ps,
                                       PART_A_MAX_LAG, T_CHUNK_S)
    print("\n-- Part A summary --")
    for s in (part_a_raw, part_a_st):
        print_summary_row(PART_A_SIGMA, PART_A_A, PART_A_OMEGA, s)

    # ── Part B: omega_spread sweep (S100-P2) ──
    PART_B_SIGMA = 0.022
    PART_B_A = 0.0
    PART_B_OMEGAS = [0.0, 0.005, 0.02, 0.08]
    PART_B_N_SEEDS = 4
    PART_B_TOTAL_STEPS = warmup + 50 * chunk_steps  # 200,000s
    PART_B_MAX_LAG = 30

    print("\n" + "=" * 72)
    print("PART B: ω_spread sweep {0.0, 0.005, 0.02, 0.08}, A=0, 4 seeds × 200ks")
    print("=" * 72)
    omega_results = {}
    for om in PART_B_OMEGAS:
        print(f"\n-- ω_spread = {om} --")
        ps = run_long_chunked_omega(
            sigma=PART_B_SIGMA, A=PART_B_A, n_seeds=PART_B_N_SEEDS,
            total_steps=PART_B_TOTAL_STEPS, warmup=warmup,
            chunk_steps=chunk_steps, omega_spread=om,
            dt=dt, signal_freq=signal_freq,
            seed_base=101_500 + int(om * 1e5))
        raw_s = summarize_channel_null('z_raw', ps, PART_B_MAX_LAG, T_CHUNK_S)
        st_s = summarize_channel_null('z_st', ps, PART_B_MAX_LAG, T_CHUNK_S)
        omega_results[f'{om:.4f}'] = {
            'omega_spread': om, 'sigma': PART_B_SIGMA, 'A': PART_B_A,
            'n_seeds': PART_B_N_SEEDS,
            'total_steps': PART_B_TOTAL_STEPS,
            'raw': raw_s, 'st': st_s,
        }
        for s in (raw_s, st_s):
            print_summary_row(PART_B_SIGMA, PART_B_A, om, s)

    # ── Scaling check: τ_wander vs 1/Δω ──
    print("\n" + "=" * 72)
    print("SCALING CHECK: does τ_wander(raw) scale with 1/ω_spread?")
    print("=" * 72)
    print(f"{'ω_spread':>10} {'1/ω_spread':>11} {'τ_Cfull_raw':>13} "
          f"{'τ_Phi_raw':>11} {'τ_amp_raw':>11}")
    for om in PART_B_OMEGAS:
        r = omega_results[f'{om:.4f}']['raw']['fits']
        inv = 1.0 / om if om > 0 else float('inf')
        tc = r['tau_Cfull']['tau_s'] if r['tau_Cfull'] else None
        tp = r['tau_Phi']['tau_s'] if r['tau_Phi'] else None
        ta = r['tau_rhoabs']['tau_s'] if r['tau_rhoabs'] else None
        tc_s = f"{tc:>10.0f}s" if tc else "     n/a"
        tp_s = f"{tp:>8.0f}s" if tp else "    n/a"
        ta_s = f"{ta:>8.0f}s" if ta else "    n/a"
        inv_s = f"{inv:>8.1f}" if inv < float('inf') else "      inf"
        print(f"  {om:>8.4f} {inv_s}  {tc_s:>13} {tp_s:>11} {ta_s:>11}")

    # ── Save everything ──
    def pack_seeds(per_seed):
        return [
            {
                'seed': s['seed'],
                'n_chunks': s['n_chunks'],
                'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
                'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
                'n_sw': s['n_sw'].tolist(),
            }
            for s in per_seed
        ]

    out = {
        'meta': {
            'session': 101,
            'title': 'Intrinsic vs Signal-Induced Wander — S100-P2 & S100-P3',
            'started': start.isoformat(),
            'params': {
                'dt': dt, 'signal_freq': signal_freq, 'warmup': warmup,
                'T_chunk_s': T_CHUNK_S, 'chunk_steps': chunk_steps,
                'part_a': {
                    'sigma': PART_A_SIGMA, 'A': PART_A_A,
                    'omega_spread': PART_A_OMEGA,
                    'n_seeds': PART_A_N_SEEDS,
                    'total_steps': PART_A_TOTAL_STEPS,
                    'max_lag': PART_A_MAX_LAG,
                },
                'part_b': {
                    'sigma': PART_B_SIGMA, 'A': PART_B_A,
                    'omega_spreads': PART_B_OMEGAS,
                    'n_seeds': PART_B_N_SEEDS,
                    'total_steps': PART_B_TOTAL_STEPS,
                    'max_lag': PART_B_MAX_LAG,
                },
            },
        },
        'part_a': {
            'per_seed': pack_seeds(part_a_ps),
            'raw': part_a_raw,
            'st': part_a_st,
        },
        'part_b': omega_results,
    }
    with open('thor_session_101_intrinsic_wander_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s "
          f"({elapsed/60:.1f} min)")
    print(f"Results saved → thor_session_101_intrinsic_wander_results.json")
