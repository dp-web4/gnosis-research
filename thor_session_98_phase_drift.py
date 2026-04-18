#!/usr/bin/env python3
"""
Thor Session #98: Phase-Drift Timescale τ_φ — Direct Measurement.

S95 observed response-phase non-stationarity indirectly: 8 chunks × 4000s
gave circular concentration R=0.59 instead of the stationary prediction
R≈0.95. From those numbers S95 back-of-the-envelope'd

    τ_φ ≈ 4000s · (π/0.37)²  ≈ 290,000s

as the 1-radian drift timescale (S95 P2). That was a single-point extrapolation
from one σ and one A.

This session measures τ_φ DIRECTLY. Run very long trajectories, chunk them
into non-overlapping T_chunk-long pieces, compute the complex matched-filter
output Z_k = I_k + i·Q_k for each chunk, and measure the complex autocorrelation

    C(m) = ⟨ Z_k · conj(Z_{k+m}) ⟩  /  ⟨ |Z_k|² ⟩         (full)
    Φ(m) = ⟨ exp(i(φ_k − φ_{k+m})) ⟩                     (phase-only, unit mag)

Two channels: raw-signal MF (phase_coherent_IQ) and switch-timing MF
(switch_timing_IQ) — per S95, they sit ~π/2 apart in the response plane, so
their phase-drift should be coupled but need not be identical.

What we get out:
  1. |Φ(m)| vs m·T_chunk — the direct phase-coherence decay curve.
     Fit exp(−m·T_chunk/τ_φ) → phase-diffusion time τ_φ = 1/D_φ.
  2. arg(Φ(m)) vs m·T_chunk — mean systematic rotation rate.
     Nonzero Δω means simulator rhythm differs from detector reference
     (interesting: is the effective f_s drifting?).
  3. Var[Δφ_m] = Var[φ_k − φ_{k+m}] — the variogram. Linear in m·T_chunk
     confirms Brownian phase random walk; nonlinearity flags memory.
  4. Amplitude autocorrelation ρ(|Z|) — fast decorrelation ⇒ the signal
     magnitude fluctuates; slow decorrelation ⇒ amplitude is stable
     even while the phase drifts.

σ-dependence (small test):
  If phase drift is driven by switching-event jitter, τ_φ should depend
  strongly on σ (switch rate → σ-sensitive). S96-P1 predicts the mean
  response angle itself rotates with σ (toward Q_st at low σ). We can
  check both mean angle AND τ_φ across σ in a single sweep.

Compute budget (Thor, ~25 µs/step):
  Main run:  n=8 seeds × T_total=400,000s × 10 steps/s = 3.2e7 steps ≈ 13 min
  σ sweep:   3 values × n=4 seeds × T_total=200,000s = 2.4e7 steps ≈ 10 min
  Total ≈ 25 min.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55


def run_long_chunked(sigma, A, n_seeds, total_steps, warmup, chunk_steps,
                     dt=0.1, signal_freq=0.003, seed_base=1000):
    """For each seed, simulate a long trajectory, chop into non-overlapping
    chunks, and compute (I_raw, Q_raw, I_st, Q_st, n_switch) per chunk.

    Returns per-seed dicts:
        z_raw: complex array of length n_chunks
        z_st:  complex array of length n_chunks
        n_st:  int array of switch-counts per chunk
    plus metadata."""
    print(f"\n>> long-chunk run: σ={sigma}, A={A}, n_seeds={n_seeds}, "
          f"total_steps={total_steps}, chunk_steps={chunk_steps}")

    per_seed = []
    start = datetime.now()
    for seed in range(n_seeds):
        t0 = datetime.now()
        x = simulate(N=4, noise_std=sigma, steps=total_steps,
                     seed=seed_base + seed,
                     signal_freq=signal_freq, signal_amp=A, dt=dt)
        xp = x[warmup:]
        n_chunks = len(xp) // chunk_steps

        z_raw = np.zeros(n_chunks, dtype=complex)
        z_st = np.zeros(n_chunks, dtype=complex)
        n_sw = np.zeros(n_chunks, dtype=int)

        for c in range(n_chunks):
            chunk = xp[c * chunk_steps:(c + 1) * chunk_steps]
            t_off = warmup + c * chunk_steps
            I_r, Q_r = phase_coherent_IQ(chunk, dt, signal_freq, t_offset=t_off)
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
        print(f"   seed={seed_base + seed:5d}  n_chunks={n_chunks}  "
              f"{elapsed:5.1f}s  "
              f"|mean(z_raw)|={np.abs(z_raw.mean()):.3e}  "
              f"|mean(z_st)|={np.abs(z_st.mean()):.3e}  "
              f"mean(N_sw)/chunk={n_sw.mean():.1f}")

    total_elapsed = (datetime.now() - start).total_seconds()
    print(f"   [total {total_elapsed:.1f}s for {n_seeds} seeds]")
    return per_seed


def complex_autocorr(z_seeds, max_lag):
    """Given a list of per-seed complex chunk-series, compute the
    cross-seed-averaged complex autocorrelation at lags 0..max_lag.

    Three curves:
      C_full(m)   = ⟨ z_k · conj(z_{k+m}) ⟩ / ⟨ |z_k|² ⟩       (amp+phase)
      Φ_unit(m)   = ⟨ u_k · conj(u_{k+m}) ⟩     where u = z/|z|  (phase-only)
      rho_abs(m)  = ⟨ |z_k| · |z_{k+m}| ⟩ / ⟨ |z_k|² ⟩          (amp-only)

    All averages are over seeds AND starting-chunk-positions (pooled pairs).
    Returns dict with arrays indexed by m (length max_lag+1)."""
    C_num = np.zeros(max_lag + 1, dtype=complex)
    Phi_num = np.zeros(max_lag + 1, dtype=complex)
    abs_num = np.zeros(max_lag + 1, dtype=float)
    denom_c = 0.0
    denom_a = 0.0
    # counts per lag
    counts = np.zeros(max_lag + 1, dtype=int)

    for seed in z_seeds:
        z = seed['z_raw']  # just a placeholder; caller supplies the channel
        pass  # overridden below

    return None  # stub -- replaced by per-channel version


def autocorr_channel(z_seeds_list, max_lag):
    """For one channel: given a list of complex arrays (one per seed),
    return dict of C_full[m], Phi_unit[m], rho_abs[m], counts[m],
    and pair-variance of phase difference (variogram)."""
    max_lag = int(max_lag)
    # Accumulators across all (seed, starting index) pairs
    C_acc = np.zeros(max_lag + 1, dtype=complex)
    Phi_acc = np.zeros(max_lag + 1, dtype=complex)
    abs_acc = np.zeros(max_lag + 1, dtype=float)
    count = np.zeros(max_lag + 1, dtype=int)
    # For phase variance we accumulate unwrapped-mod-2π differences
    dphi_sq_acc = np.zeros(max_lag + 1, dtype=float)

    # Total |z|² (averaged across seeds) is the normalizer for C_full
    z2_num = 0.0
    z2_den = 0

    for z in z_seeds_list:
        n = len(z)
        mag = np.abs(z)
        phi = np.angle(z)
        u = z / np.maximum(mag, 1e-18)
        z2_num += float(np.sum(mag**2))
        z2_den += n

        for m in range(max_lag + 1):
            if m == 0:
                C_acc[0] += np.sum(z * np.conj(z))
                Phi_acc[0] += np.sum(u * np.conj(u))
                abs_acc[0] += np.sum(mag * mag)
                count[0] += n
                dphi_sq_acc[0] += 0.0
            else:
                if n - m <= 0:
                    continue
                # z_k · conj(z_{k+m})
                zc = z[:-m] * np.conj(z[m:])
                C_acc[m] += np.sum(zc)
                Phi_acc[m] += np.sum(u[:-m] * np.conj(u[m:]))
                abs_acc[m] += np.sum(mag[:-m] * mag[m:])
                count[m] += (n - m)
                # Circular phase difference, wrapped to (−π, π]
                dphi = phi[:-m] - phi[m:]
                dphi = (dphi + np.pi) % (2 * np.pi) - np.pi
                dphi_sq_acc[m] += float(np.sum(dphi**2))

    mean_z2 = z2_num / max(z2_den, 1)

    C_full = np.zeros(max_lag + 1, dtype=complex)
    Phi = np.zeros(max_lag + 1, dtype=complex)
    rho_abs = np.zeros(max_lag + 1, dtype=float)
    var_dphi = np.zeros(max_lag + 1, dtype=float)
    for m in range(max_lag + 1):
        c = count[m]
        if c > 0:
            C_full[m] = C_acc[m] / c / mean_z2
            Phi[m] = Phi_acc[m] / c
            rho_abs[m] = abs_acc[m] / c / mean_z2
            var_dphi[m] = dphi_sq_acc[m] / c
    return {
        'C_full': C_full,
        'Phi': Phi,
        'rho_abs': rho_abs,
        'var_dphi': var_dphi,
        'count': count,
        'mean_z2': mean_z2,
    }


def fit_phase_diffusion(Phi, lags_time):
    """|Φ(m)| = exp(-D_φ · m·Δt). Fit D_φ by linear regression on
    log|Φ| vs m·Δt, weighted by count. Returns dict with D_phi, tau_phi,
    R²."""
    absPhi = np.abs(Phi)
    # Keep only lags where |Φ| is comfortably above the noise floor.
    # (|Φ| < 0.1 starts to get dominated by finite-sample fluctuations.)
    ok = (absPhi > 0.10) & (lags_time > 0)
    if ok.sum() < 3:
        return None
    y = np.log(absPhi[ok])
    x = lags_time[ok]
    # fit y = -D_phi · x + intercept
    slope, intercept = np.polyfit(x, y, 1)
    D_phi = -slope
    tau_phi = 1.0 / D_phi if D_phi > 0 else float('inf')
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred)**2))
    ss_tot = float(np.sum((y - y.mean())**2))
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        'D_phi_per_s': float(D_phi),
        'tau_phi_s': float(tau_phi),
        'intercept': float(intercept),
        'R2': float(R2),
        'n_fit': int(ok.sum()),
        'max_lag_s_used': float(x.max()),
    }


def fit_rotation_rate(Phi, lags_time):
    """arg(Φ(m)) ≈ −Δω · m·Δt (mod 2π). Unwrap and fit slope, restricting
    to lags where |Φ| > 0.2 so the angle is well-defined."""
    absPhi = np.abs(Phi)
    angle = np.angle(Phi)
    ok = (absPhi > 0.20) & (lags_time > 0)
    if ok.sum() < 3:
        return None
    y_raw = angle[ok]
    x = lags_time[ok]
    # Unwrap by construction: sort by x and then np.unwrap
    idx = np.argsort(x)
    xs = x[idx]
    ys = np.unwrap(y_raw[idx])
    slope, intercept = np.polyfit(xs, ys, 1)
    # Convention: Φ(m) ≈ exp(-D·mΔt + i·ψ·mΔt). slope = ψ; Δω_response = -ψ
    pred = slope * xs + intercept
    ss_res = float(np.sum((ys - pred)**2))
    ss_tot = float(np.sum((ys - ys.mean())**2))
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        'rotation_rate_rad_per_s': float(slope),
        'intercept_rad': float(intercept),
        'R2': float(R2),
        'n_fit': int(ok.sum()),
    }


def per_seed_phase_stats(z_seeds_list):
    """For each seed, compute mean angle (weighted by |z|), chunk-to-chunk
    step size (circular std of lag-1 differences), and resultant length."""
    out = []
    for z in z_seeds_list:
        mag = np.abs(z)
        phi = np.angle(z)
        # resultant vector using z itself (amplitude-weighted circular mean)
        Z_bar = z.mean()
        ang_bar = float(np.angle(Z_bar))
        R_weighted = float(np.abs(Z_bar) / max(mag.mean(), 1e-18))
        # lag-1 phase step
        dphi = phi[:-1] - phi[1:]
        dphi = (dphi + np.pi) % (2 * np.pi) - np.pi
        sigma_step = float(np.std(dphi))
        out.append({
            'mean_angle_deg': float(np.degrees(ang_bar)),
            'R_weighted': R_weighted,
            'sigma_step_deg': float(np.degrees(sigma_step)),
            'n_chunks': int(len(z)),
            'mean_mag': float(mag.mean()),
        })
    return out


def summarize_channel(name, per_seed, max_lag, chunk_time_s):
    z_list = [s[name] for s in per_seed]
    ac = autocorr_channel(z_list, max_lag)
    lags_time = np.arange(max_lag + 1) * chunk_time_s
    fit_d = fit_phase_diffusion(ac['Phi'], lags_time)
    fit_r = fit_rotation_rate(ac['Phi'], lags_time)
    stats = per_seed_phase_stats(z_list)
    # Report-friendly conversion
    def to_list(c):
        return [[float(x.real), float(x.imag)] for x in c]
    return {
        'channel': name,
        'lags_time_s': lags_time.tolist(),
        'C_full': to_list(ac['C_full']),
        'Phi': to_list(ac['Phi']),
        'rho_abs': ac['rho_abs'].tolist(),
        'var_dphi': ac['var_dphi'].tolist(),
        'count': ac['count'].tolist(),
        'mean_z2': ac['mean_z2'],
        'phase_diffusion_fit': fit_d,
        'rotation_rate_fit': fit_r,
        'per_seed_stats': stats,
    }


# ─── Main ───

if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #98: Phase-Drift Timescale τ_φ — Direct Measurement")
    print(f"Started: {start.isoformat()}\n")

    dt = 0.1
    signal_freq = 0.003
    warmup = 10_000
    T_CHUNK_S = 4000.0  # per-chunk integration window
    chunk_steps = int(T_CHUNK_S / dt)  # 40_000

    # ── Main run: canonical SR operating point ──
    #    Long enough to cover τ_φ ≈ 290,000s comfortably. Compute budget
    #    stays under 15 min.
    MAIN_TOTAL_STEPS = warmup + 100 * chunk_steps   # 100 chunks = 400,000s
    MAIN_N_SEEDS = 8
    MAIN_SIGMA = 0.022
    MAIN_A = 0.30
    # max_lag: with 100 chunks per seed and 8 seeds, max_lag=50 still gives
    # 400 pairs at m=50 and 800 at m=1. We do 60 for margin.
    MAIN_MAX_LAG = 60

    main_per_seed = run_long_chunked(
        sigma=MAIN_SIGMA, A=MAIN_A,
        n_seeds=MAIN_N_SEEDS,
        total_steps=MAIN_TOTAL_STEPS,
        warmup=warmup,
        chunk_steps=chunk_steps,
        dt=dt, signal_freq=signal_freq, seed_base=98_000,
    )

    main_raw_summary = summarize_channel('z_raw', main_per_seed,
                                         MAIN_MAX_LAG, T_CHUNK_S)
    main_st_summary = summarize_channel('z_st', main_per_seed,
                                        MAIN_MAX_LAG, T_CHUNK_S)

    print("\n" + "=" * 72)
    print(f"MAIN  σ={MAIN_SIGMA}, A={MAIN_A}, n_seeds={MAIN_N_SEEDS}, "
          f"T_total={(MAIN_TOTAL_STEPS - warmup)*dt:.0f}s, "
          f"T_chunk={T_CHUNK_S:.0f}s")
    print("=" * 72)
    for summ in (main_raw_summary, main_st_summary):
        print(f"\n  {summ['channel']}:")
        f = summ['phase_diffusion_fit']
        r = summ['rotation_rate_fit']
        if f:
            print(f"    |Φ(m)| decay: D_φ = {f['D_phi_per_s']:.3e} /s, "
                  f"τ_φ = {f['tau_phi_s']:.0f}s, R²={f['R2']:.3f}, "
                  f"n_fit={f['n_fit']}")
        else:
            print(f"    |Φ(m)| decay: insufficient signal above floor")
        if r:
            print(f"    arg Φ slope: Δψ = {r['rotation_rate_rad_per_s']:.3e}"
                  f" rad/s,  R²={r['R2']:.3f}")
        print(f"    mean |z|²: {summ['mean_z2']:.3e}")
        Phi = [complex(x[0], x[1]) for x in summ['Phi']]
        abs_phi = [abs(p) for p in Phi]
        print(f"    |Φ| first 10 lags: "
              f"[{', '.join(f'{v:.3f}' for v in abs_phi[:10])}]")

    # ── σ-sweep: test phase-drift σ-dependence and S96-P1 angle rotation ──
    SIGMA_SWEEP = [0.015, 0.022, 0.030]
    SWEEP_N_SEEDS = 4
    SWEEP_TOTAL_STEPS = warmup + 50 * chunk_steps   # 50 chunks = 200,000s
    SWEEP_MAX_LAG = 30
    SWEEP_A = 0.30

    sigma_results = {}
    for sig in SIGMA_SWEEP:
        print(f"\n\n── σ-sweep step: σ={sig} ──")
        ps = run_long_chunked(
            sigma=sig, A=SWEEP_A,
            n_seeds=SWEEP_N_SEEDS,
            total_steps=SWEEP_TOTAL_STEPS,
            warmup=warmup,
            chunk_steps=chunk_steps,
            dt=dt, signal_freq=signal_freq, seed_base=98_500 + int(sig * 1e5),
        )
        sig_raw = summarize_channel('z_raw', ps, SWEEP_MAX_LAG, T_CHUNK_S)
        sig_st = summarize_channel('z_st', ps, SWEEP_MAX_LAG, T_CHUNK_S)
        sigma_results[f'{sig:.3f}'] = {
            'sigma': sig, 'A': SWEEP_A, 'n_seeds': SWEEP_N_SEEDS,
            'total_steps': SWEEP_TOTAL_STEPS,
            'raw': sig_raw, 'st': sig_st,
        }
        for summ in (sig_raw, sig_st):
            f = summ['phase_diffusion_fit']
            r = summ['rotation_rate_fit']
            tstr = f"τ_φ={f['tau_phi_s']:.0f}s R²={f['R2']:.2f}" if f \
                else "τ_φ: no fit"
            rstr = f"Δψ={r['rotation_rate_rad_per_s']:.2e}" if r else ""
            # mean angle across seeds
            ang = np.array([s['mean_angle_deg'] for s in summ['per_seed_stats']])
            ang_mean = float(np.degrees(np.angle(np.mean(np.exp(
                1j * np.radians(ang))))))
            print(f"   σ={sig}  {summ['channel']}:  "
                  f"mean_angle={ang_mean:+6.1f}°  {tstr}  {rstr}")

    # ── Save all data ──
    # Convert complex arrays in per_seed to serializable lists
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
            'session': 98,
            'title': 'Phase-Drift Timescale τ_φ — Direct Measurement',
            'started': start.isoformat(),
            'params': {
                'dt': dt, 'signal_freq': signal_freq, 'warmup': warmup,
                'T_chunk_s': T_CHUNK_S, 'chunk_steps': chunk_steps,
                'main_total_steps': MAIN_TOTAL_STEPS,
                'main_n_seeds': MAIN_N_SEEDS,
                'main_sigma': MAIN_SIGMA, 'main_A': MAIN_A,
                'main_max_lag': MAIN_MAX_LAG,
                'sigma_sweep': SIGMA_SWEEP,
                'sweep_n_seeds': SWEEP_N_SEEDS,
                'sweep_total_steps': SWEEP_TOTAL_STEPS,
                'sweep_max_lag': SWEEP_MAX_LAG,
                'sweep_A': SWEEP_A,
            },
        },
        'main': {
            'per_seed': pack_seeds(main_per_seed),
            'raw': main_raw_summary,
            'st': main_st_summary,
        },
        'sigma_sweep': sigma_results,
    }
    with open('thor_session_98_phase_drift_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s")
    print(f"Results saved → thor_session_98_phase_drift_results.json")
