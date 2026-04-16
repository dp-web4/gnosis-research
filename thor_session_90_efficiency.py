#!/usr/bin/env python3
"""
Thor Session #90: The Efficiency Landscape

Where does collective cognition work SMARTEST — not loudest (SR peak), not
most evenly (EP equipartition), but highest bits-per-entropy?

Open questions from prior sessions:
  S86 found sigma_SR ~ 0.011 (maximum response amplitude).
  S88 found sigma_EP ~ 0.011-0.013 (phase/coherence EP equipartition).
  S88 reported eta = MI/EP = 0.0002 bits/EP at sigma=0.011.
  S88 reported N-body/collective EP ratio of 7x at sigma=0.011 (huge swing
    across sigma: 284x at sigma=0.005 down to 3.6x at sigma=0.025).

Not yet asked:
  1. Where along sigma is eta = MI/EP MAXIMIZED?
  2. Does sigma_eff coincide with sigma_SR, sigma_EP_equi, or neither?
  3. How does the N-body/collective EP ratio scale with N (Prediction 2 of S88)?

This session answers all three.

Experiments:
  A. Efficiency sweep: sigma in [0.005, 0.025] with signal injected. Measure
     MI, EP(collective), EP(N-body), response amplitude. Compute eta at both
     scales.
  B. N-scaling: at sigma_SR = 0.011, vary N in [4, 8, 16, 32]. Test whether
     N-body/collective EP ratio grows with N (S88 Prediction 2) and whether
     D_C amplification grows with N (S89 Prediction 1).
  C. Signal-amplitude ablation: at fixed sigma, vary signal amplitude. Does
     eta peak location depend on signal strength, or is it a geometric
     property of the system?
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)


# =============================================================================
# Simulation (matching S89/S88 exactly)
# =============================================================================

def simulate(N, noise_std, steps, seed=None,
             kappa_phase=0.10, kappa_C=0.15,
             omega_base=0.1, omega_spread=0.02,
             phi_inverse=0.618, dt=0.1, C_threshold=0.55,
             signal_freq=0.003, signal_amp=0.0):
    """Identical model to S88/S89. Returns trajectories and drifts."""
    if seed is not None:
        np.random.seed(seed)

    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    C_hist = np.empty((steps, N))
    phase_hist = np.empty((steps, N))
    drift_C = np.empty((steps, N))
    drift_phase = np.empty((steps, N))
    C_mean_hist = np.empty(steps)
    signal_hist = np.empty(steps)

    for t in range(steps):
        C_hist[t] = C
        phase_hist[t] = phase
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean

        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        signal_hist[t] = signal
        is_attractive = (C_mean + signal) < C_threshold

        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        drift_phase[t] = dphase
        phase = (phase + dt * dphase) % (2 * np.pi)

        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
        dC = intrinsic + c_coupling
        drift_C[t] = dC
        C = np.clip(C + dt * dC, 0, 1)

        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C': C_hist, 'phase': phase_hist,
        'drift_C': drift_C, 'drift_phase': drift_phase,
        'C_mean': C_mean_hist, 'signal': signal_hist,
    }


# =============================================================================
# Metrics
# =============================================================================

def compute_mi_binned(x, y, n_bins=8):
    """Mutual information via histogram estimator (S86 convention)."""
    x_bins = np.linspace(x.min() - 1e-10, x.max() + 1e-10, n_bins + 1)
    y_bins = np.linspace(y.min() - 1e-10, y.max() + 1e-10, n_bins + 1)
    xi = np.clip(np.digitize(x, x_bins) - 1, 0, n_bins - 1)
    yi = np.clip(np.digitize(y, y_bins) - 1, 0, n_bins - 1)

    joint = np.zeros((n_bins, n_bins))
    for a, b in zip(xi, yi):
        joint[a, b] += 1
    joint /= joint.sum()

    p_x = joint.sum(axis=1)
    p_y = joint.sum(axis=0)

    mi = 0.0
    for i in range(n_bins):
        for j in range(n_bins):
            if joint[i, j] > 0 and p_x[i] > 0 and p_y[j] > 0:
                mi += joint[i, j] * np.log2(joint[i, j] / (p_x[i] * p_y[j]))
    return mi


def compute_ep_nbody(result, warmup, dt):
    """N-body EP using empirical D per-agent (S88 convention)."""
    C = result['C'][warmup:]
    phase = result['phase'][warmup:]
    drift_C = result['drift_C'][warmup:]
    drift_phase = result['drift_phase'][warmup:]
    N = C.shape[1]

    ep_C_individual = np.zeros(N)
    ep_phase_individual = np.zeros(N)
    D_C_individual = np.zeros(N)
    D_phase_individual = np.zeros(N)

    for i in range(N):
        dC_i = np.diff(C[:, i])
        mu_i = drift_C[:-1, i]
        res_i = dC_i - mu_i * dt
        D_i = np.mean(res_i**2) / (2 * dt)
        D_C_individual[i] = D_i
        if D_i > 0:
            ep_C_individual[i] = np.mean(mu_i**2) / D_i

        dphase_i = np.diff(phase[:, i])
        dphase_i = (dphase_i + np.pi) % (2 * np.pi) - np.pi
        mu_i = drift_phase[:-1, i]
        res_i = dphase_i - mu_i * dt
        res_i = (res_i + np.pi) % (2 * np.pi) - np.pi
        D_i = np.mean(res_i**2) / (2 * dt)
        D_phase_individual[i] = D_i
        if D_i > 0:
            ep_phase_individual[i] = np.mean(mu_i**2) / D_i

    # Collective EP (C_mean only)
    C_mean = np.mean(C, axis=1)
    dC_mean = np.diff(C_mean)
    drift_C_mean = np.mean(drift_C, axis=1)
    res_C_mean = dC_mean - drift_C_mean[:-1] * dt
    D_C_mean = np.mean(res_C_mean**2) / (2 * dt)
    ep_collective = np.mean(drift_C_mean[:-1]**2) / D_C_mean if D_C_mean > 0 else 0

    return {
        'ep_C_total': float(np.sum(ep_C_individual)),
        'ep_phase_total': float(np.sum(ep_phase_individual)),
        'ep_nbody': float(np.sum(ep_C_individual) + np.sum(ep_phase_individual)),
        'ep_collective': float(ep_collective),
        'D_C_mean': float(np.mean(D_C_individual)),
        'D_phase_mean': float(np.mean(D_phase_individual)),
        'frac_C_pct': float(100 * np.sum(ep_C_individual) /
                            (np.sum(ep_C_individual) + np.sum(ep_phase_individual))
                            if (np.sum(ep_C_individual) + np.sum(ep_phase_individual)) > 0
                            else 0),
    }


def response_amp_at_signal(C_mean, dt, signal_freq):
    """Single-frequency amplitude via FFT."""
    steps = len(C_mean)
    freq = np.fft.rfftfreq(steps, d=dt)
    spec = np.fft.rfft(C_mean - C_mean.mean())
    idx = np.argmin(np.abs(freq - signal_freq))
    band = max(1, int(0.0005 / (freq[1] - freq[0]))) if len(freq) > 1 else 1
    lo, hi = max(0, idx - band), min(len(spec), idx + band + 1)
    amp = np.sqrt(np.mean(np.abs(spec[lo:hi])**2)) / np.sqrt(steps)
    return float(amp)


# =============================================================================
# EXPERIMENT A: Efficiency sweep (find sigma_eff)
# =============================================================================

def experiment_A():
    """Sweep sigma. Measure MI, EP (both scales), efficiency eta."""
    print("=" * 70)
    print("EXPERIMENT A: Efficiency Landscape (eta = MI/EP)")
    print("=" * 70)

    # Fine sigma grid, dense near SR optimum
    sigmas = np.array([
        0.005, 0.006, 0.007, 0.008, 0.009, 0.010,
        0.011, 0.012, 0.013, 0.014, 0.015, 0.016,
        0.018, 0.020, 0.022, 0.025
    ])

    N = 4
    dt = 0.1
    steps = 60_000
    warmup = 10_000
    n_seeds = 3
    signal_amp = 0.02
    signal_freq = 0.003

    results = []
    for sigma in sigmas:
        mi_vals = []
        ep_nbody_vals = []
        ep_coll_vals = []
        ep_C_vals = []
        ep_phase_vals = []
        D_C_vals = []
        amp_vals = []
        frac_C_vals = []

        for seed in range(n_seeds):
            # With signal (for MI + amp)
            r_sig = simulate(
                N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                signal_freq=signal_freq, signal_amp=signal_amp, dt=dt
            )
            C_ss = r_sig['C_mean'][warmup:]
            sig_ss = r_sig['signal'][warmup:]
            mi_vals.append(compute_mi_binned(C_ss, sig_ss, n_bins=8))
            amp_vals.append(response_amp_at_signal(C_ss, dt, signal_freq))

            # Without signal (for clean EP)
            r_ep = simulate(
                N=N, noise_std=sigma, steps=steps, seed=seed * 100 + 500,
                signal_amp=0.0, dt=dt
            )
            ep = compute_ep_nbody(r_ep, warmup, dt)
            ep_nbody_vals.append(ep['ep_nbody'])
            ep_coll_vals.append(ep['ep_collective'])
            ep_C_vals.append(ep['ep_C_total'])
            ep_phase_vals.append(ep['ep_phase_total'])
            D_C_vals.append(ep['D_C_mean'])
            frac_C_vals.append(ep['frac_C_pct'])

        mi = np.mean(mi_vals)
        ep_nbody = np.mean(ep_nbody_vals)
        ep_coll = np.mean(ep_coll_vals)

        entry = {
            'sigma': round(float(sigma), 4),
            'MI_bits': round(float(mi), 5),
            'MI_std': round(float(np.std(mi_vals)), 5),
            'ep_nbody': round(float(ep_nbody), 2),
            'ep_collective': round(float(ep_coll), 2),
            'ep_C': round(float(np.mean(ep_C_vals)), 2),
            'ep_phase': round(float(np.mean(ep_phase_vals)), 2),
            'frac_C_pct': round(float(np.mean(frac_C_vals)), 2),
            'D_C_mean': round(float(np.mean(D_C_vals)), 6),
            'D_C_over_sigma2': round(float(np.mean(D_C_vals) / sigma**2), 2),
            'response_amp': round(float(np.mean(amp_vals)), 6),
            'eta_nbody': round(float(mi / ep_nbody) if ep_nbody > 0 else 0, 6),
            'eta_collective': round(float(mi / ep_coll) if ep_coll > 0 else 0, 6),
        }
        results.append(entry)

        print(f"  σ={sigma:.4f}: MI={mi:.4f} ± {np.std(mi_vals):.4f} bits | "
              f"EP_nb={ep_nbody:7.2f} EP_c={ep_coll:6.2f} | "
              f"η_nb={entry['eta_nbody']:.5f} η_c={entry['eta_collective']:.5f} | "
              f"amp={entry['response_amp']:.4f} fC%={entry['frac_C_pct']:.1f}")

    # Find peaks
    sigs = np.array([r['sigma'] for r in results])
    mis = np.array([r['MI_bits'] for r in results])
    eta_nb = np.array([r['eta_nbody'] for r in results])
    eta_c = np.array([r['eta_collective'] for r in results])
    amps = np.array([r['response_amp'] for r in results])
    frac_C = np.array([r['frac_C_pct'] for r in results])

    # Sigma where frac_C crosses 50% (EP equipartition)
    sigma_EP_equi = None
    for i in range(len(frac_C) - 1):
        if (frac_C[i] - 50) * (frac_C[i + 1] - 50) < 0:
            sigma_EP_equi = sigs[i] + (50 - frac_C[i]) / (frac_C[i + 1] - frac_C[i]) * (sigs[i + 1] - sigs[i])
            break

    idx_MI = int(np.argmax(mis))
    idx_amp = int(np.argmax(amps))
    idx_eta_nb = int(np.argmax(eta_nb))
    idx_eta_c = int(np.argmax(eta_c))

    print("\n  KEY POINTS:")
    print(f"    sigma_MI_peak    = {sigs[idx_MI]:.4f} (MI = {mis[idx_MI]:.4f} bits)")
    print(f"    sigma_amp_peak   = {sigs[idx_amp]:.4f} (amp = {amps[idx_amp]:.4f})")
    print(f"    sigma_EP_equi    = {sigma_EP_equi:.4f} (frac_C crosses 50%)"
          if sigma_EP_equi is not None else "    sigma_EP_equi not found in range")
    print(f"    sigma_eta_nb     = {sigs[idx_eta_nb]:.4f} (η = {eta_nb[idx_eta_nb]:.5f} bits/EP)")
    print(f"    sigma_eta_coll   = {sigs[idx_eta_c]:.4f} (η = {eta_c[idx_eta_c]:.5f} bits/EP)")

    return {
        'data': results,
        'sigma_MI_peak': float(sigs[idx_MI]),
        'sigma_amp_peak': float(sigs[idx_amp]),
        'sigma_EP_equi': float(sigma_EP_equi) if sigma_EP_equi is not None else None,
        'sigma_eta_nbody': float(sigs[idx_eta_nb]),
        'sigma_eta_collective': float(sigs[idx_eta_c]),
        'MI_peak': float(mis[idx_MI]),
        'eta_nbody_peak': float(eta_nb[idx_eta_nb]),
        'eta_collective_peak': float(eta_c[idx_eta_c]),
    }


# =============================================================================
# EXPERIMENT B: N-scaling of EP ratio (tests S88 Prediction 2, S89 Prediction 1)
# =============================================================================

def experiment_B():
    """N-scaling at sigma_SR = 0.011. Ratio N-body/collective AND D amplification."""
    print("\n" + "=" * 70)
    print("EXPERIMENT B: N-Scaling of EP Ratio (S88 P2) and D Amplification (S89 P1)")
    print("=" * 70)

    N_values = [4, 8, 16, 32, 64]
    sigma = 0.011
    dt = 0.1

    results = []
    for N in N_values:
        # Scale steps down for large N to keep runtime reasonable; large N
        # self-averages so fewer steps are needed for stable statistics.
        if N <= 16:
            steps = 60_000
        elif N <= 32:
            steps = 40_000
        else:
            steps = 25_000
        warmup = steps // 6

        n_seeds = 3 if N <= 16 else 2
        ratios = []
        ep_nb_vals = []
        ep_c_vals = []
        D_C_vals = []
        frac_C_vals = []

        for seed in range(n_seeds):
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                         signal_amp=0.0, dt=dt)
            ep = compute_ep_nbody(r, warmup, dt)
            ep_nb_vals.append(ep['ep_nbody'])
            ep_c_vals.append(ep['ep_collective'])
            D_C_vals.append(ep['D_C_mean'])
            frac_C_vals.append(ep['frac_C_pct'])
            if ep['ep_collective'] > 0:
                ratios.append(ep['ep_nbody'] / ep['ep_collective'])

        entry = {
            'N': N,
            'steps': steps,
            'ep_nbody': round(float(np.mean(ep_nb_vals)), 2),
            'ep_collective': round(float(np.mean(ep_c_vals)), 2),
            'ratio': round(float(np.mean(ratios)) if ratios else 0, 2),
            'ratio_std': round(float(np.std(ratios)) if ratios else 0, 2),
            'D_C_mean': round(float(np.mean(D_C_vals)), 6),
            'D_C_over_sigma2': round(float(np.mean(D_C_vals) / sigma**2), 2),
            'frac_C_pct': round(float(np.mean(frac_C_vals)), 2),
            'ep_per_agent_nbody': round(float(np.mean(ep_nb_vals)) / N, 2),
            'ep_per_agent_collective': round(float(np.mean(ep_c_vals)) / N, 4),
        }
        results.append(entry)
        print(f"  N={N:3d}: EP_nb={entry['ep_nbody']:7.2f} EP_c={entry['ep_collective']:6.2f} "
              f"ratio={entry['ratio']:6.1f}x  "
              f"D_C/σ²={entry['D_C_over_sigma2']:5.1f}  "
              f"frac_C={entry['frac_C_pct']:.1f}%  "
              f"EP_nb/N={entry['ep_per_agent_nbody']:.2f}")

    # Fit power-law scaling for both quantities
    Ns = np.array([r['N'] for r in results])
    ratios = np.array([r['ratio'] for r in results])
    D_amps = np.array([r['D_C_over_sigma2'] for r in results])

    # log-log fit
    valid_ratio = ratios > 0
    if valid_ratio.sum() >= 3:
        p_ratio = np.polyfit(np.log(Ns[valid_ratio]), np.log(ratios[valid_ratio]), 1)
        print(f"\n  N-body/collective ratio ~ N^{p_ratio[0]:.3f}")
    else:
        p_ratio = [np.nan, np.nan]

    if (D_amps > 0).sum() >= 3:
        p_D = np.polyfit(np.log(Ns), np.log(D_amps), 1)
        print(f"  D_C/σ² ~ N^{p_D[0]:.3f}")
    else:
        p_D = [np.nan, np.nan]

    # S88 Prediction 2 verdict
    print("\n  S88 Prediction 2 (EP ratio grows with N):")
    if not np.isnan(p_ratio[0]):
        if p_ratio[0] > 0.3:
            print(f"    STRONGLY CONFIRMED (alpha={p_ratio[0]:.3f})")
        elif p_ratio[0] > 0.1:
            print(f"    WEAKLY CONFIRMED (alpha={p_ratio[0]:.3f})")
        elif p_ratio[0] > -0.1:
            print(f"    FALSE — ratio is independent of N (alpha={p_ratio[0]:.3f})")
        else:
            print(f"    INVERTED — ratio DECREASES with N (alpha={p_ratio[0]:.3f})")

    # S89 Prediction 1 verdict
    print("\n  S89 Prediction 1 (D_C amplification grows with N):")
    if not np.isnan(p_D[0]):
        if p_D[0] > 0.1:
            print(f"    CONFIRMED (alpha={p_D[0]:.3f})")
        elif p_D[0] > -0.1:
            print(f"    FALSE — amplification independent of N (alpha={p_D[0]:.3f})")
        else:
            print(f"    INVERTED — amplification DECREASES with N (alpha={p_D[0]:.3f})")

    return {
        'data': results,
        'ratio_scaling_exponent': float(p_ratio[0]) if not np.isnan(p_ratio[0]) else None,
        'D_amp_scaling_exponent': float(p_D[0]) if not np.isnan(p_D[0]) else None,
    }


# =============================================================================
# EXPERIMENT C: Signal-amplitude ablation (does sigma_eff shift?)
# =============================================================================

def experiment_C():
    """Does the peak-efficiency sigma depend on signal amplitude?"""
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Signal-Amplitude Ablation of Efficiency Peak")
    print("=" * 70)

    signal_amps = [0.01, 0.02, 0.04, 0.06]
    sigmas = np.array([0.008, 0.010, 0.011, 0.012, 0.013, 0.014, 0.016, 0.020])
    N = 4
    dt = 0.1
    steps = 50_000
    warmup = 10_000
    n_seeds = 2

    all_results = {}
    for A in signal_amps:
        print(f"\n  Signal amplitude A = {A:.3f}")
        data = []
        for sigma in sigmas:
            mi_vals = []
            ep_nbody_vals = []
            ep_coll_vals = []
            for seed in range(n_seeds):
                r_sig = simulate(
                    N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                    signal_freq=0.003, signal_amp=A, dt=dt
                )
                C_ss = r_sig['C_mean'][warmup:]
                sig_ss = r_sig['signal'][warmup:]
                mi_vals.append(compute_mi_binned(C_ss, sig_ss, n_bins=8))

                r_ep = simulate(
                    N=N, noise_std=sigma, steps=steps, seed=seed * 100 + 500,
                    signal_amp=0.0, dt=dt
                )
                ep = compute_ep_nbody(r_ep, warmup, dt)
                ep_nbody_vals.append(ep['ep_nbody'])
                ep_coll_vals.append(ep['ep_collective'])

            mi = float(np.mean(mi_vals))
            ep_nb = float(np.mean(ep_nbody_vals))
            ep_c = float(np.mean(ep_coll_vals))
            entry = {
                'sigma': float(sigma),
                'MI_bits': round(mi, 5),
                'ep_nbody': round(ep_nb, 2),
                'ep_collective': round(ep_c, 2),
                'eta_nbody': round(mi / ep_nb if ep_nb > 0 else 0, 6),
                'eta_collective': round(mi / ep_c if ep_c > 0 else 0, 6),
            }
            data.append(entry)
            print(f"    σ={sigma:.3f}: MI={mi:.4f} EP_nb={ep_nb:.1f} "
                  f"η_nb={entry['eta_nbody']:.5f} η_c={entry['eta_collective']:.5f}")

        sigs = np.array([d['sigma'] for d in data])
        eta_nb = np.array([d['eta_nbody'] for d in data])
        eta_c = np.array([d['eta_collective'] for d in data])
        MIs = np.array([d['MI_bits'] for d in data])

        idx_eta_nb = int(np.argmax(eta_nb))
        idx_eta_c = int(np.argmax(eta_c))
        idx_MI = int(np.argmax(MIs))

        all_results[f'A={A}'] = {
            'data': data,
            'sigma_eta_nbody': float(sigs[idx_eta_nb]),
            'sigma_eta_collective': float(sigs[idx_eta_c]),
            'sigma_MI_peak': float(sigs[idx_MI]),
            'eta_nbody_peak': float(eta_nb[idx_eta_nb]),
            'eta_collective_peak': float(eta_c[idx_eta_c]),
        }
        print(f"    → σ_eta_nb={sigs[idx_eta_nb]:.4f}  "
              f"σ_eta_c={sigs[idx_eta_c]:.4f}  "
              f"σ_MI={sigs[idx_MI]:.4f}")

    # Check if sigma_eta shifts with A
    As = np.array(signal_amps)
    sigma_eta_nb_vals = np.array([all_results[f'A={A}']['sigma_eta_nbody'] for A in As])
    sigma_eta_c_vals = np.array([all_results[f'A={A}']['sigma_eta_collective'] for A in As])

    print(f"\n  Signal dependence of sigma_eta (N-body): "
          f"range {sigma_eta_nb_vals.min():.4f} - {sigma_eta_nb_vals.max():.4f} "
          f"(spread {sigma_eta_nb_vals.max() - sigma_eta_nb_vals.min():.4f})")
    print(f"  Signal dependence of sigma_eta (collective): "
          f"range {sigma_eta_c_vals.min():.4f} - {sigma_eta_c_vals.max():.4f}")

    return all_results


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    start = datetime.now()
    print(f"Thor Session #90: The Efficiency Landscape")
    print(f"Started: {start.isoformat()}")
    print()

    results = {}
    results['A'] = experiment_A()
    results['B'] = experiment_B()
    results['C'] = experiment_C()

    # =================================================================
    # GRAND SYNTHESIS
    # =================================================================
    print("\n" + "=" * 70)
    print("GRAND SYNTHESIS")
    print("=" * 70)

    A = results['A']
    print(f"\n  Baseline (N=4, kp=0.10, kc=0.15, C_thresh=0.55):")
    print(f"    sigma_MI_peak        = {A['sigma_MI_peak']:.4f}")
    print(f"    sigma_amp_peak (SR)  = {A['sigma_amp_peak']:.4f}")
    print(f"    sigma_EP_equi        = {A.get('sigma_EP_equi', 'n/a')}")
    print(f"    sigma_eta (N-body)   = {A['sigma_eta_nbody']:.4f}")
    print(f"    sigma_eta (coll)     = {A['sigma_eta_collective']:.4f}")
    print(f"    eta_peak (N-body)    = {A['eta_nbody_peak']:.5f} bits/EP")
    print(f"    eta_peak (coll)      = {A['eta_collective_peak']:.5f} bits/EP")

    # Save
    with open('thor_session_90_efficiency_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
