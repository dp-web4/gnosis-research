#!/usr/bin/env python3
"""
Thor Session #91 extension: Bias Floor Control

Session 91 main experiment found that coupling ablation (kp=0, kc=0) at sigma=0.100
gave MI=0.0145, which is HIGHER than the baseline MI=0.0117. This is suspicious
because with both couplings off, the signal has no legal entry point into the
dynamics — MI should be pure estimator bias.

Control experiments:
  1. MI(signal vs SYNTHETIC random time series) — pure bias floor
  2. MI(signal vs C_mean) for varying n_seeds — variance estimation
  3. MI for uncoupled signal-less runs vs MI-to-signal — compare to bias floor

If baseline MI at sigma=0.100 is NOT significantly above bias floor, then the
S90 "efficiency peak" is an artifact of MI estimation in a regime where the
system has essentially stopped transmitting information.

Hypothesis: at sigma=0.100, real MI is within factor of 2 of bias floor. The
apparent efficiency peak is the limit of the estimator, not a real cognitive
optimum.
"""

import numpy as np
import json
from datetime import datetime


def simulate(N, noise_std, steps, seed=None,
             kappa_phase=0.10, kappa_C=0.15,
             omega_base=0.1, omega_spread=0.02,
             phi_inverse=0.618, dt=0.1, C_threshold=0.55,
             signal_freq=0.003, signal_amp=0.0):
    if seed is not None:
        np.random.seed(seed)
    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)
    C_mean_hist = np.empty(steps)
    signal_hist = np.empty(steps)
    for t in range(steps):
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean
        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        signal_hist[t] = signal
        is_attractive = (C_mean + signal) < C_threshold
        sign = 1.0 if is_attractive else -1.0
        if kappa_phase > 0:
            sin_diff = np.sin(phase[None, :] - phase[:, None])
            np.fill_diagonal(sin_diff, 0)
            dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        else:
            dphase = omega.copy()
        phase = (phase + dt * dphase) % (2 * np.pi)
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
        dC = intrinsic + c_coupling
        C = np.clip(C + dt * dC, 0, 1)
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)
    return C_mean_hist, signal_hist


def compute_mi_binned(x, y, n_bins=8):
    x_bins = np.linspace(x.min() - 1e-10, x.max() + 1e-10, n_bins + 1)
    y_bins = np.linspace(y.min() - 1e-10, y.max() + 1e-10, n_bins + 1)
    xi = np.clip(np.digitize(x, x_bins) - 1, 0, n_bins - 1)
    yi = np.clip(np.digitize(y, y_bins) - 1, 0, n_bins - 1)
    joint = np.zeros((n_bins, n_bins))
    for a, b in zip(xi, yi):
        joint[a, b] += 1
    total = joint.sum()
    if total == 0:
        return 0.0
    joint /= total
    p_x = joint.sum(axis=1)
    p_y = joint.sum(axis=0)
    mi = 0.0
    for i in range(n_bins):
        for j in range(n_bins):
            if joint[i, j] > 0 and p_x[i] > 0 and p_y[j] > 0:
                mi += joint[i, j] * np.log2(joint[i, j] / (p_x[i] * p_y[j]))
    return mi


# ========================================================================
# Control 1: MI(signal, random_signal) — pure bias floor
# ========================================================================

def control_bias_floor(steps=50000, n_bins=8, n_reps=200, signal_freq=0.003, signal_amp=0.02):
    """MI between real signal and independent noise traces. Pure bias."""
    dt = 0.1
    t = np.arange(steps)
    signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
    mis = []
    for rep in range(n_reps):
        np.random.seed(9000 + rep)
        # C_mean-like: random walk stuck in (0, 1)
        y = 0.5 + 0.1 * np.cumsum(np.random.normal(0, 1, steps)) / np.sqrt(steps) \
            + np.random.normal(0, 0.1, steps)
        y = np.clip(y, 0, 1)
        mis.append(compute_mi_binned(y, signal, n_bins))
    mis = np.array(mis)
    return {
        'mi_mean': float(mis.mean()),
        'mi_median': float(np.median(mis)),
        'mi_std': float(mis.std()),
        'mi_p95': float(np.percentile(mis, 95)),
        'mi_p99': float(np.percentile(mis, 99)),
        'n_reps': n_reps,
    }


# ========================================================================
# Control 2: MI(signal, C_mean) at sigma with many seeds for stable mean
# ========================================================================

def mi_at_sigma(sigma, n_seeds, kappa_phase=0.10, kappa_C=0.15,
                signal_amp=0.02, steps=50000, warmup=10000):
    mis = []
    for seed in range(n_seeds):
        C_mean, signal = simulate(N=4, noise_std=sigma, steps=steps, seed=seed * 100,
                                  kappa_phase=kappa_phase, kappa_C=kappa_C,
                                  signal_amp=signal_amp, signal_freq=0.003)
        mis.append(compute_mi_binned(C_mean[warmup:], signal[warmup:], n_bins=8))
    return mis


# ========================================================================
# Control 3: MI(signal, C_mean_signal_absent) — simulate without signal,
#            then compute MI against a SYNTHETIC signal
# ========================================================================

def mi_signal_absent(sigma, n_seeds, kappa_phase=0.10, kappa_C=0.15,
                     steps=50000, warmup=10000, signal_freq=0.003, signal_amp=0.02):
    """Simulate with signal_amp=0 (no signal affects dynamics), then compute
    MI against the synthetic signal. This is the pure bias floor for THIS
    model geometry."""
    mis = []
    dt = 0.1
    for seed in range(n_seeds):
        C_mean, _ = simulate(N=4, noise_std=sigma, steps=steps, seed=seed * 100,
                             kappa_phase=kappa_phase, kappa_C=kappa_C,
                             signal_amp=0.0, signal_freq=signal_freq)
        t = np.arange(steps)
        synth_signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        mis.append(compute_mi_binned(C_mean[warmup:], synth_signal[warmup:], n_bins=8))
    return mis


# ========================================================================
# MAIN
# ========================================================================

if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #91: Bias Floor Control")
    print(f"Started: {start.isoformat()}\n")

    results = {}

    print("=" * 70)
    print("CONTROL 1: pure synthetic bias floor (signal vs random walks)")
    print("=" * 70)
    bias = control_bias_floor()
    print(f"  MI (synthetic random walks)")
    print(f"    mean   = {bias['mi_mean']:.5f}")
    print(f"    median = {bias['mi_median']:.5f}")
    print(f"    std    = {bias['mi_std']:.5f}")
    print(f"    95%ile = {bias['mi_p95']:.5f}")
    print(f"    99%ile = {bias['mi_p99']:.5f}")
    results['control_1_synthetic'] = bias

    print("\n" + "=" * 70)
    print("CONTROL 2: MI at sigma values, with many seeds")
    print("=" * 70)
    results['control_2'] = {}
    for sigma in [0.011, 0.022, 0.050, 0.100, 0.150]:
        mis = mi_at_sigma(sigma, n_seeds=10)
        mean = float(np.mean(mis))
        std = float(np.std(mis))
        stderr = std / np.sqrt(len(mis))
        entry = {
            'mi_mean': round(mean, 5),
            'mi_std': round(std, 5),
            'mi_stderr': round(stderr, 5),
            'n_seeds': len(mis),
        }
        results['control_2'][f'sigma_{sigma}'] = entry
        print(f"  sigma={sigma:.3f}: MI = {mean:.4f} +- {stderr:.4f} (SE, n={len(mis)})")

    print("\n" + "=" * 70)
    print("CONTROL 3: MI with signal ABSENT from dynamics")
    print("=" * 70)
    results['control_3_signal_absent'] = {}
    for sigma in [0.011, 0.022, 0.050, 0.100, 0.150]:
        mis = mi_signal_absent(sigma, n_seeds=10)
        mean = float(np.mean(mis))
        std = float(np.std(mis))
        stderr = std / np.sqrt(len(mis))
        entry = {
            'mi_mean': round(mean, 5),
            'mi_std': round(std, 5),
            'mi_stderr': round(stderr, 5),
            'n_seeds': len(mis),
        }
        results['control_3_signal_absent'][f'sigma_{sigma}'] = entry
        print(f"  sigma={sigma:.3f}: MI_bias = {mean:.4f} +- {stderr:.4f}")

    print("\n" + "=" * 70)
    print("VERDICT: Is the signal genuinely transmitted at sigma=0.100?")
    print("=" * 70)
    for sigma in [0.011, 0.022, 0.050, 0.100, 0.150]:
        with_sig = results['control_2'][f'sigma_{sigma}']['mi_mean']
        without_sig = results['control_3_signal_absent'][f'sigma_{sigma}']['mi_mean']
        signal_above_bias = with_sig - without_sig
        ratio = with_sig / max(without_sig, 1e-6)
        err_with = results['control_2'][f'sigma_{sigma}']['mi_stderr']
        err_without = results['control_3_signal_absent'][f'sigma_{sigma}']['mi_stderr']
        combined_err = np.sqrt(err_with**2 + err_without**2)
        z_score = signal_above_bias / max(combined_err, 1e-6)
        print(f"  sigma={sigma:.3f}: MI_signal={with_sig:.4f}, MI_bias={without_sig:.4f} "
              f"(diff={signal_above_bias:+.4f}, ratio={ratio:.2f}x, z={z_score:.1f})")

    with open('thor_session_91_bias_control_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
    print("Results -> thor_session_91_bias_control_results.json")
