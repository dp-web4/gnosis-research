#!/usr/bin/env python3
"""
Thor Session #100: Does Phase Drift Appear in the Incoherent Regime?

S98 measured |Φ(m)| FLAT from 4,000s to 240,000s at σ ∈ {0.015, 0.022, 0.030},
A=0.30. Concluded τ_φ >> 240,000s in the coherent / SR-optimum regime.
S98-P4 identified σ=0.040+ as the falsification zone: if Kramers rate
scales ∝ exp(-ΔU/σ²), then at σ=0.040 (ratio 3.3x noise variance over
σ=0.022) switches come ~50x faster, and the same mechanism that stabilizes
response-phase at σ=0.022 may fail.

THIS SESSION:
    1. Repeat S98 methodology at σ ∈ {0.040, 0.060, 0.100} — the
       full incoherent ramp above the SR peak.
    2. Combine with S98's stored low-σ sweep (0.015/0.022/0.030) for
       a 6-point τ_φ(σ) curve on raw-signal and switch-timing channels.
    3. S99-P2 bonus: fit the raw-channel per-chunk |z| and phase
       autocorrelations → τ_wander(σ). Does the ~21,000s timescale S99
       observed at σ=0.022 shift (faster) with increasing σ?

Expected outcomes:
    (a) Phase drift APPEARS at high σ: τ_φ finite and visible on 200,000s
        window, scaling inversely with σ² (as per Kramers variance).
        → "phase stationarity" is a property of the coherent/SR regime,
        not a general feature of the model. S98-P4 CONFIRMED.
    (b) Phase remains stationary even at σ=0.100: → phase stationarity
        is robust across the full noise range in this model; drift is
        bounded by something other than switch jitter (symmetry?).
        S98-P4 FALSIFIED.
    (c) |Φ(0)| << 1 at high σ: switch-timing signal itself dissolves —
        nothing to drift in. Interesting secondary finding.

Compute budget:
    sweep: 3 σ × 4 seeds × 2,010,000 steps × 25µs/step ≈ 600s ≈ 10min
    main (best σ): 8 seeds × 4,010,000 steps × 25µs/step ≈ 800s ≈ 13min
    Total ≈ 25min.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_98_phase_drift import (
    run_long_chunked,
    autocorr_channel,
    fit_phase_diffusion,
    fit_rotation_rate,
    per_seed_phase_stats,
    summarize_channel,
)


def raw_chunk_autocorr(z_seeds_list, max_lag):
    """For each seed's z chunk-series, separately analyze:
        - |z_k| autocorrelation (amplitude wander)
        - arg(z_k) wrapped-diff autocorrelation (phase wander)
    returns per-channel, per-seed τ_wander fits plus seed-pooled curves."""
    max_lag = int(max_lag)
    # Accumulators for |z| ACF (normal autocorrelation on magnitude series)
    mag_sum = np.zeros(max_lag + 1, dtype=float)
    mag_count = np.zeros(max_lag + 1, dtype=int)
    mag_var_num = 0.0
    mag_var_den = 0

    # Accumulators for arg(z) ACF — use circular correlation via unit vectors
    u_sum = np.zeros(max_lag + 1, dtype=complex)
    u_count = np.zeros(max_lag + 1, dtype=int)

    mag_means = []
    for z in z_seeds_list:
        mag = np.abs(z)
        mag_c = mag - mag.mean()
        mag_means.append(float(mag.mean()))
        phi = np.angle(z)
        u = np.exp(1j * phi)
        mag_var_num += float(np.sum(mag_c**2))
        mag_var_den += len(mag_c)
        for m in range(max_lag + 1):
            if m == 0:
                mag_sum[0] += float(np.sum(mag_c * mag_c))
                mag_count[0] += len(mag_c)
                u_sum[0] += np.sum(u * np.conj(u))
                u_count[0] += len(u)
            else:
                if len(mag_c) - m <= 0:
                    continue
                mag_sum[m] += float(np.sum(mag_c[:-m] * mag_c[m:]))
                mag_count[m] += len(mag_c) - m
                u_sum[m] += np.sum(u[:-m] * np.conj(u[m:]))
                u_count[m] += len(u) - m

    mag_var = mag_var_num / max(mag_var_den, 1)
    rho_mag = np.zeros(max_lag + 1)
    rho_u = np.zeros(max_lag + 1, dtype=complex)
    for m in range(max_lag + 1):
        if mag_count[m] > 0 and mag_var > 0:
            rho_mag[m] = mag_sum[m] / mag_count[m] / mag_var
        if u_count[m] > 0:
            rho_u[m] = u_sum[m] / u_count[m]
    return {
        'rho_mag': rho_mag.tolist(),
        'rho_u_abs': np.abs(rho_u).tolist(),
        'rho_u_arg_deg': np.degrees(np.angle(rho_u)).tolist(),
        'mag_var': float(mag_var),
        'mean_mag_per_seed': mag_means,
    }


def fit_tau_wander(rho, lags_time_s):
    """Fit τ_wander from rho(m) = exp(-m·dt/τ) by regression on log(max(rho, eps))
    over lags where rho > 0.10. Returns dict with τ, R², slope."""
    rho = np.array(rho)
    lags_time_s = np.array(lags_time_s)
    ok = (rho > 0.10) & (lags_time_s > 0)
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
        'max_lag_s': float(x.max()),
    }


def analyze_wander(per_seed_list, channel_name, max_lag, chunk_time_s):
    z_list = [s[channel_name] for s in per_seed_list]
    ac = raw_chunk_autocorr(z_list, max_lag)
    lags_time = np.arange(max_lag + 1) * chunk_time_s
    mag_fit = fit_tau_wander(ac['rho_mag'], lags_time)
    phase_fit = fit_tau_wander(ac['rho_u_abs'], lags_time)
    return {
        'channel': channel_name,
        'lags_time_s': lags_time.tolist(),
        'rho_mag': ac['rho_mag'],
        'rho_u_abs': ac['rho_u_abs'],
        'rho_u_arg_deg': ac['rho_u_arg_deg'],
        'mag_var': ac['mag_var'],
        'mean_mag_per_seed': ac['mean_mag_per_seed'],
        'tau_mag_wander': mag_fit,
        'tau_phase_wander': phase_fit,
    }


if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #100: Phase Drift in the Incoherent Regime")
    print(f"Started: {start.isoformat()}\n")

    dt = 0.1
    signal_freq = 0.003
    warmup = 10_000
    T_CHUNK_S = 4000.0
    chunk_steps = int(T_CHUNK_S / dt)

    # ── Sweep: incoherent-regime σ values (mirror S98 sigma_sweep shape) ──
    SIGMA_SWEEP = [0.040, 0.060, 0.100]
    SWEEP_N_SEEDS = 4
    SWEEP_TOTAL_STEPS = warmup + 50 * chunk_steps   # 50 chunks = 200,000s
    SWEEP_MAX_LAG = 30
    SWEEP_A = 0.30

    sigma_results = {}
    for sig in SIGMA_SWEEP:
        print(f"\n\n── incoherent σ-step: σ={sig} ──")
        ps = run_long_chunked(
            sigma=sig, A=SWEEP_A,
            n_seeds=SWEEP_N_SEEDS,
            total_steps=SWEEP_TOTAL_STEPS,
            warmup=warmup,
            chunk_steps=chunk_steps,
            dt=dt, signal_freq=signal_freq,
            seed_base=100_000 + int(sig * 1e5),
        )
        sig_raw = summarize_channel('z_raw', ps, SWEEP_MAX_LAG, T_CHUNK_S)
        sig_st = summarize_channel('z_st', ps, SWEEP_MAX_LAG, T_CHUNK_S)
        wander_raw = analyze_wander(ps, 'z_raw', SWEEP_MAX_LAG, T_CHUNK_S)
        wander_st = analyze_wander(ps, 'z_st', SWEEP_MAX_LAG, T_CHUNK_S)
        sigma_results[f'{sig:.3f}'] = {
            'sigma': sig, 'A': SWEEP_A, 'n_seeds': SWEEP_N_SEEDS,
            'total_steps': SWEEP_TOTAL_STEPS,
            'raw': sig_raw, 'st': sig_st,
            'wander_raw': wander_raw, 'wander_st': wander_st,
        }
        for summ, wand in ((sig_raw, wander_raw), (sig_st, wander_st)):
            f = summ['phase_diffusion_fit']
            r = summ['rotation_rate_fit']
            tstr = (f"τ_φ={f['tau_phi_s']:.0f}s R²={f['R2']:.2f}"
                    if f else "τ_φ: no fit (|Φ| never above floor)")
            rstr = (f"Δψ={r['rotation_rate_rad_per_s']:.2e} rad/s"
                    if r else "")
            ang = np.array([s['mean_angle_deg']
                            for s in summ['per_seed_stats']])
            ang_mean = float(np.degrees(np.angle(np.mean(np.exp(
                1j * np.radians(ang))))))
            R_seeds = float(np.abs(np.mean(np.exp(1j * np.radians(ang)))))
            abs_phi = [abs(complex(a, b)) for (a, b) in summ['Phi'][:10]]
            tw_p = wand['tau_phase_wander']
            tw_m = wand['tau_mag_wander']
            tw_str = f"τ_wph={tw_p['tau_s']:.0f}s" if tw_p \
                else "τ_wph: n/a"
            tw_mstr = f"τ_wmag={tw_m['tau_s']:.0f}s" if tw_m \
                else "τ_wmag: n/a"
            print(f"   σ={sig}  {summ['channel']}:")
            print(f"     mean_angle={ang_mean:+6.1f}°  R_seeds={R_seeds:.3f}  "
                  f"{tstr}  {rstr}")
            print(f"     |Φ| lags 0–9: "
                  f"[{', '.join(f'{v:.3f}' for v in abs_phi)}]")
            print(f"     wander: {tw_str}  {tw_mstr}")

    # ── Main run at whichever incoherent σ shows nontrivial drift ──
    # Strategy: pick the σ where τ_φ comes in measurable (>1) but finite.
    # We do this selection after the sweep to avoid guessing wrong.
    best_sigma = None
    best_tau = None
    best_score = -1.0
    for key, res in sigma_results.items():
        # Pick the σ where the ST channel gives the cleanest finite τ_φ
        f = res['st']['phase_diffusion_fit']
        if f is None:
            continue
        tau = f['tau_phi_s']
        # Score = R² × (1 / (1 + |tau| / 200,000s))  — prefer smaller finite τ
        if tau > 0 and tau < 500_000:
            score = f['R2'] / (1.0 + tau / 100_000.0)
            if score > best_score:
                best_score = score
                best_sigma = res['sigma']
                best_tau = tau

    if best_sigma is None:
        # fallback: use 0.060 for main (middle incoherent point)
        best_sigma = 0.060
        print(f"\nNo τ_φ finite in sweep; main run at fallback σ={best_sigma}")
    else:
        print(f"\nSelected main σ={best_sigma} (sweep st τ_φ={best_tau:.0f}s, "
              f"score={best_score:.2f})")

    MAIN_N_SEEDS = 8
    MAIN_TOTAL_STEPS = warmup + 100 * chunk_steps   # 400,000s
    MAIN_MAX_LAG = 60
    MAIN_A = 0.30

    main_per_seed = run_long_chunked(
        sigma=best_sigma, A=MAIN_A,
        n_seeds=MAIN_N_SEEDS,
        total_steps=MAIN_TOTAL_STEPS,
        warmup=warmup,
        chunk_steps=chunk_steps,
        dt=dt, signal_freq=signal_freq,
        seed_base=100_000 + int(best_sigma * 1e5) + 500,
    )
    main_raw_summary = summarize_channel('z_raw', main_per_seed,
                                         MAIN_MAX_LAG, T_CHUNK_S)
    main_st_summary = summarize_channel('z_st', main_per_seed,
                                        MAIN_MAX_LAG, T_CHUNK_S)
    main_wander_raw = analyze_wander(main_per_seed, 'z_raw',
                                     MAIN_MAX_LAG, T_CHUNK_S)
    main_wander_st = analyze_wander(main_per_seed, 'z_st',
                                    MAIN_MAX_LAG, T_CHUNK_S)

    print("\n" + "=" * 72)
    print(f"MAIN  σ={best_sigma}, A={MAIN_A}, n_seeds={MAIN_N_SEEDS}, "
          f"T_total={(MAIN_TOTAL_STEPS - warmup)*dt:.0f}s, "
          f"T_chunk={T_CHUNK_S:.0f}s")
    print("=" * 72)
    for summ, wand in ((main_raw_summary, main_wander_raw),
                       (main_st_summary, main_wander_st)):
        f = summ['phase_diffusion_fit']
        r = summ['rotation_rate_fit']
        print(f"\n  {summ['channel']}:")
        if f:
            print(f"    |Φ(m)| decay: D_φ={f['D_phi_per_s']:.3e} /s, "
                  f"τ_φ={f['tau_phi_s']:.0f}s, R²={f['R2']:.3f}, "
                  f"n_fit={f['n_fit']}")
        else:
            print(f"    |Φ(m)| decay: no fit")
        if r:
            print(f"    arg Φ slope: Δψ={r['rotation_rate_rad_per_s']:.3e} "
                  f"rad/s, R²={r['R2']:.3f}")
        print(f"    mean |z|²: {summ['mean_z2']:.3e}")
        abs_phi = [abs(complex(a, b)) for (a, b) in summ['Phi'][:15]]
        print(f"    |Φ| lags 0–14: "
              f"[{', '.join(f'{v:.3f}' for v in abs_phi)}]")
        tw_p = wand['tau_phase_wander']
        tw_m = wand['tau_mag_wander']
        print(f"    τ_phase_wander: "
              f"{tw_p['tau_s']:.0f}s R²={tw_p['R2']:.2f}" if tw_p
              else "    τ_phase_wander: n/a")
        print(f"    τ_mag_wander:   "
              f"{tw_m['tau_s']:.0f}s R²={tw_m['R2']:.2f}" if tw_m
              else "    τ_mag_wander: n/a")

    # ── Cross-session combine: S98 low-σ + S100 high-σ → τ_φ(σ) curve ──
    # Just summarize key numbers for the report; actual S98 JSON stays
    # separate and is re-analyzed in the companion analyze script.
    print("\n" + "=" * 72)
    print("τ_φ(σ) CURVE (combined S98 + S100)")
    print("=" * 72)
    print("(low-σ half loaded from S98; extract in analysis)")

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
            'session': 100,
            'title': 'Phase Drift in the Incoherent Regime — S98-P4 test',
            'started': start.isoformat(),
            'params': {
                'dt': dt, 'signal_freq': signal_freq, 'warmup': warmup,
                'T_chunk_s': T_CHUNK_S, 'chunk_steps': chunk_steps,
                'sigma_sweep_incoherent': SIGMA_SWEEP,
                'sweep_n_seeds': SWEEP_N_SEEDS,
                'sweep_total_steps': SWEEP_TOTAL_STEPS,
                'sweep_max_lag': SWEEP_MAX_LAG,
                'sweep_A': SWEEP_A,
                'main_sigma_selected': best_sigma,
                'main_n_seeds': MAIN_N_SEEDS,
                'main_total_steps': MAIN_TOTAL_STEPS,
                'main_max_lag': MAIN_MAX_LAG,
                'main_A': MAIN_A,
            },
        },
        'sigma_sweep': sigma_results,
        'main': {
            'sigma': best_sigma,
            'per_seed': pack_seeds(main_per_seed),
            'raw': main_raw_summary,
            'st': main_st_summary,
            'wander_raw': main_wander_raw,
            'wander_st': main_wander_st,
        },
    }
    with open('thor_session_100_incoherent_drift_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s")
    print(f"Results saved → thor_session_100_incoherent_drift_results.json")
