#!/usr/bin/env python3
"""
Thor Session #97: Breaking the Matched-Filter Ceiling?

S96 closed the matched-filter-class detector ladder via summation-by-parts:
raw, ST, and dwell all live on the same 2D signal plane; ST (I_st, Q_st) is
the leading-order ML sufficient statistic. S96-P5 predicted:

  "To beat ST, one must leave the matched-filter class — e.g., use a
   maximum-likelihood estimator with the full Kramers-rate model, or a
   non-linear detector that captures higher harmonics."

This session implements BOTH:

  (A) FULL ML DETECTOR on the Kramers rate model.
      Model: escape rate r_escape(s,t) = r0 * exp(-s·k·sin(ωt + φ))
      where s ∈ {+1,-1} is the current state, k is effective drive-
      amplitude-to-barrier ratio, φ is response phase.
      Likelihood-ratio statistic Λ(k,φ) = 2[log L(k,φ) - log L(0)].
      Under H0 asymptotically Λ ~ χ²(2). Maximize over (k, φ).

  (B) 2f_s SWITCH-TIMING MATCHED FILTER.
      I_st2 = Σ_k d_k · sin(2ωτ_k), Q_st2 = Σ_k d_k · cos(2ωτ_k).
      Orthogonal to f_s plane. Kramers exp-expansion gives an A²
      component at 2f_s from the Bessel-I_2(k) coefficient of
      exp(k·sin(ωt)). If measurable, this IS a genuine new rung,
      orthogonal to the S96 2D plane.

Design:
  - σ=0.022 (SR peak), n=32 seeds with/without signal, T=8000 steps * dt=0.1 = 800s wall.
    Wait, T=8000s means 80000 steps at dt=0.1 — that's the S95/S96 standard
    for response-phase-coherent analysis.
  - Amplitudes: A ∈ {0.00, 0.04, 0.08, 0.12, 0.20}. Captures detection floor
    region where S96 placed ST at A≈0.12 and 6D-Hotelling at A≈0.08.
  - Same simulator / switch extraction / t_offset as S93/S95/S96.
  - Per trajectory compute: (I_st, Q_st) at f_s, (I_st2, Q_st2) at 2f_s,
    Λ_ML = max over (k,φ) of Kramers likelihood ratio.
  - Independent seeds (seed = i*100 + 123*A_idx for with, + 77777 for without).

Tests:
  T1. Does Λ_ML null distribution match χ²(2) or need empirical calibration?
  T2. Does Λ_ML show stronger detection than T²_ST at A=0.08?
  T3. Does the 2f_s detector show signal distinct from f_s? Scales as A²?
  T4. Is combined T²_ST + T²_2f a two-rung detector (truly orthogonal) or
      yet another redundancy trap?
  T5. How does fitted k_hat scale with A? Kramers theory predicts
      k_hat ∝ A (linear in drive amplitude).
"""

import numpy as np
import json
import sys
from datetime import datetime
from scipy.optimize import minimize
from scipy.stats import chi2

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_events, switch_timing_IQ


C_THRESHOLD = 0.55
SIGMA = 0.022
F_S = 0.003
DT = 0.1
STEPS = 90_000     # 10,000 warmup + 80,000 post-warmup
WARMUP = 10_000
N_SEEDS = 32


# ─── State trajectory (piecewise constant between switches) ───

def state_trajectory(C_mean, threshold=C_THRESHOLD):
    """Return state s(t) = sign(C_mean[t] - threshold) with ties → +1."""
    s = np.sign(C_mean - threshold)
    s[s == 0] = 1
    return s


# ─── 2f_s switch-timing detector ───

def switch_timing_IQ_2f(C_mean, dt, signal_freq, t_offset,
                        threshold=C_THRESHOLD):
    """Switch-timing matched filter at TWICE the signal frequency."""
    idx, dirs = switch_events(C_mean, threshold=threshold)
    if len(idx) < 2:
        return 0.0, 0.0, len(idx)
    t = (idx + t_offset) * dt
    omega_2 = 2 * np.pi * (2 * signal_freq)
    I = float(np.sum(dirs * np.sin(omega_2 * t)))
    Q = float(np.sum(dirs * np.cos(omega_2 * t)))
    return I, Q, len(idx)


# ─── ML Kramers detector ───

def kramers_lambda(C_mean, dt, signal_freq, t_offset, threshold=C_THRESHOLD):
    """Compute max ML likelihood-ratio Λ = 2[log L(k,φ) - log L(0)] under
    the Kramers rate model r_esc(s,t) = r0·exp(-s·k·sin(ωt+φ)).

    Profile over r0 analytically. Maximize over (k, φ) numerically.

    Returns (Lambda_max, k_hat, phi_hat, n_switches).
    """
    idx, dirs = switch_events(C_mean, threshold=threshold)
    N = len(idx)
    if N < 4:
        return 0.0, 0.0, 0.0, N

    state = state_trajectory(C_mean, threshold=threshold)
    n_steps = len(C_mean)
    omega = 2 * np.pi * signal_freq

    t_event = (idx + t_offset) * dt
    t_step = (np.arange(n_steps) + t_offset) * dt

    # Switch-timing sums (linear-in-k event-term components)
    I_st = float(np.sum(dirs * np.sin(omega * t_event)))
    Q_st = float(np.sum(dirs * np.cos(omega * t_event)))

    # Precompute state-weighted sin/cos at each step
    sin_step = np.sin(omega * t_step)
    cos_step = np.cos(omega * t_step)
    s_sin = state * sin_step
    s_cos = state * cos_step

    def neg_lambda(params):
        k, phi = params
        # log r_esc(pre-switch state, τ_i) = log r0 - (-s_pre)·k·sin(...)
        # = log r0 + d_i · k · sin(ωτ_i + φ)  (since s_pre = -d_i)
        # sum over events: k·Σ d_i·sin(ωτ_i+φ) = k[cos(φ)·I_st + sin(φ)·Q_st]
        event_term = k * (np.cos(phi) * I_st + np.sin(phi) * Q_st)
        # integral term: r0·∫ exp(-s(t)·k·sin(ωt+φ)) dt
        # profile-MLE r̂0 = N / ∫ exp(...) dt (in step-dt units)
        arg = -k * (s_sin * np.cos(phi) + s_cos * np.sin(phi))
        arg = np.clip(arg, -50.0, 50.0)
        mean_exp = np.mean(np.exp(arg))
        lam = 2.0 * event_term - 2.0 * N * np.log(mean_exp)
        return -lam  # negate because scipy minimizes

    # Multi-start: (k,φ) unknown. Small restart grid — (k→−k, φ→φ+π) is a
    # symmetry so +k starts suffice. Under null, Λ is Davies-type heavy-tailed
    # (φ unidentified under H0) — calibrate empirically.
    best = (0.0, 0.0, 0.0)  # (Lambda, k, phi)
    for k_init in (0.2, 0.6):
        for phi_init in np.linspace(0, 2 * np.pi, 6, endpoint=False):
            try:
                res = minimize(neg_lambda, [k_init, phi_init],
                               method='Nelder-Mead',
                               options={'xatol': 1e-4, 'fatol': 1e-4,
                                        'maxiter': 300})
                lam = -res.fun
                if lam > best[0]:
                    best = (lam, res.x[0], res.x[1] % (2 * np.pi))
            except Exception:
                pass
    return best[0], best[1], best[2], N


# ─── Per-seed sweep ───

def run_seed(seed, A, steps=STEPS, warmup=WARMUP, sigma=SIGMA):
    """Simulate one trajectory and compute all detectors."""
    C_mean_hist = simulate(N=4, noise_std=sigma, steps=steps,
                           seed=seed, signal_freq=F_S, signal_amp=A, dt=DT)
    C_post = C_mean_hist[warmup:]
    # f_s raw matched filter (S93)
    I_raw, Q_raw = phase_coherent_IQ(C_post, DT, F_S, t_offset=warmup)
    # f_s switch-timing (S95)
    I_st, Q_st, n_sw = switch_timing_IQ(C_post, DT, F_S, t_offset=warmup)
    # 2f_s switch-timing (new S97)
    I_st2, Q_st2, _ = switch_timing_IQ_2f(C_post, DT, F_S, t_offset=warmup)
    # ML Kramers (new S97)
    lam, k_hat, phi_hat, _ = kramers_lambda(
        C_post, DT, F_S, t_offset=warmup)
    return dict(I_raw=I_raw, Q_raw=Q_raw,
                I_st=I_st, Q_st=Q_st,
                I_st2=I_st2, Q_st2=Q_st2,
                lam=lam, k_hat=k_hat, phi_hat=phi_hat,
                n_switches=n_sw)


def sweep_A(amplitudes, n_seeds=N_SEEDS):
    """Run null trajectories ONCE (reused across amplitudes) plus one with-signal
    batch per A. Halves compute vs per-A null duplication."""
    # Shared null: seeds i*100 + 77777
    print(f"\n>> Null batch (A=0, shared across A-sweep, n={n_seeds})")
    null_rows = []
    for s_i in range(n_seeds):
        sw0 = run_seed(seed=s_i * 100 + 77777, A=0.0)
        null_rows.append(sw0)
        if (s_i + 1) % 8 == 0:
            print(f"   null seed {s_i+1:2d}/{n_seeds}  "
                  f"λ={null_rows[-1]['lam']:5.2f}  "
                  f"n_sw={null_rows[-1]['n_switches']}")

    results = {'null': null_rows}
    for i_A, A in enumerate(amplitudes):
        print(f"\n>> A = {A:.3f}  (A_idx={i_A})")
        rows_with = []
        for s_i in range(n_seeds):
            sw = run_seed(seed=s_i * 100 + 123 * (i_A + 1), A=A)
            rows_with.append(sw)
            if (s_i + 1) % 8 == 0:
                print(f"   seed {s_i+1:2d}/{n_seeds}  "
                      f"λ={rows_with[-1]['lam']:5.2f}  "
                      f"k̂={rows_with[-1]['k_hat']:+.3f}  "
                      f"(I_st={rows_with[-1]['I_st']:+.1f}, "
                      f"Q_st={rows_with[-1]['Q_st']:+.1f})")
        results[f"A={A}"] = {'with': rows_with}
    return results


# ─── Detection analysis ───

def analyze(results, amplitudes):
    """Compute T² statistics, detection outcomes per A. Uses shared null batch."""
    summary = []
    rwo = results['null']  # shared null batch
    for A in amplitudes:
        key = f"A={A}"
        rw = results[key]['with']

        def extract(key_, rows):
            return np.array([r[key_] for r in rows])

        # f_s raw
        I_raw_w = extract('I_raw', rw); I_raw_o = extract('I_raw', rwo)
        Q_raw_w = extract('Q_raw', rw); Q_raw_o = extract('Q_raw', rwo)
        # f_s ST
        I_st_w = extract('I_st', rw); I_st_o = extract('I_st', rwo)
        Q_st_w = extract('Q_st', rw); Q_st_o = extract('Q_st', rwo)
        # 2f_s ST
        I_st2_w = extract('I_st2', rw); I_st2_o = extract('I_st2', rwo)
        Q_st2_w = extract('Q_st2', rw); Q_st2_o = extract('Q_st2', rwo)
        # Kramers Λ
        lam_w = extract('lam', rw); lam_o = extract('lam', rwo)
        k_hat_w = extract('k_hat', rw); k_hat_o = extract('k_hat', rwo)

        def zdiff(a, b):
            m = a.mean() - b.mean()
            se = np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))
            return float(m), float(se), float(m/se) if se > 0 else 0.0

        _, _, z_I_raw = zdiff(I_raw_w, I_raw_o)
        _, _, z_Q_raw = zdiff(Q_raw_w, Q_raw_o)
        T2_raw = z_I_raw**2 + z_Q_raw**2

        _, _, z_I_st = zdiff(I_st_w, I_st_o)
        _, _, z_Q_st = zdiff(Q_st_w, Q_st_o)
        T2_st = z_I_st**2 + z_Q_st**2

        _, _, z_I_st2 = zdiff(I_st2_w, I_st2_o)
        _, _, z_Q_st2 = zdiff(Q_st2_w, Q_st2_o)
        T2_st2 = z_I_st2**2 + z_Q_st2**2

        # Kramers Λ: compare with-signal mean of λ to without-signal mean
        # (Λ is itself a test-statistic, so also report raw mean λ with)
        _, _, z_lam = zdiff(lam_w, lam_o)

        summary.append({
            'A': A,
            'n': len(rw),
            'T2_raw': T2_raw,
            'T2_st': T2_st,
            'T2_st2': T2_st2,
            'z_I_raw': z_I_raw, 'z_Q_raw': z_Q_raw,
            'z_I_st': z_I_st, 'z_Q_st': z_Q_st,
            'z_I_st2': z_I_st2, 'z_Q_st2': z_Q_st2,
            'lam_mean_w': float(lam_w.mean()),
            'lam_mean_o': float(lam_o.mean()),
            'lam_median_w': float(np.median(lam_w)),
            'lam_median_o': float(np.median(lam_o)),
            'lam_95_o': float(np.percentile(lam_o, 95)),
            'lam_frac_gt_95_w': float(np.mean(lam_w > np.percentile(lam_o, 95))),
            'lam_frac_gt_chi2_05_w': float(np.mean(lam_w > chi2.ppf(0.95, 2))),
            'z_lam': z_lam,
            'k_hat_mean_w': float(k_hat_w.mean()),
            'k_hat_mean_o': float(k_hat_o.mean()),
            'k_hat_std_w': float(k_hat_w.std(ddof=1)),
        })
    return summary


if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #97: ML Kramers Detector vs ST")
    print(f"Started: {start.isoformat()}")
    print(f"σ={SIGMA}, f_s={F_S}, T={(STEPS-WARMUP)*DT:.0f}s, "
          f"n_seeds={N_SEEDS}")

    amplitudes = [0.00, 0.04, 0.08, 0.12, 0.20]
    results = sweep_A(amplitudes, n_seeds=N_SEEDS)

    summary = analyze(results, amplitudes)

    print("\n" + "=" * 78)
    print("S97 SUMMARY")
    print("=" * 78)
    print(f"{'A':>6} {'T²_raw':>8} {'T²_st':>8} {'T²_st2':>8} "
          f"{'λ̄_with':>8} {'λ̄_without':>10} {'λ_95null':>9} "
          f"{'frac>95':>8} {'k̂':>6}")
    for r in summary:
        print(f"{r['A']:6.3f} {r['T2_raw']:8.2f} {r['T2_st']:8.2f} "
              f"{r['T2_st2']:8.2f} {r['lam_mean_w']:8.2f} "
              f"{r['lam_mean_o']:10.2f} {r['lam_95_o']:9.2f} "
              f"{r['lam_frac_gt_95_w']:8.2f} {r['k_hat_mean_w']:+6.3f}")

    print(f"\nχ²(2) 95% = {chi2.ppf(0.95, 2):.3f}  (textbook null threshold)")

    # Save results
    out = {
        'meta': {
            'session': 97,
            'title': 'ML Kramers Detector vs ST (breaking the matched-filter ceiling?)',
            'params': {
                'sigma': SIGMA, 'f_s': F_S,
                'steps': STEPS, 'warmup': WARMUP,
                'n_seeds': N_SEEDS,
                'amplitudes': amplitudes,
            },
            'started': start.isoformat(),
        },
        'summary': summary,
        'results': results,  # full per-seed data
    }
    with open('thor_session_97_ml_kramers_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
