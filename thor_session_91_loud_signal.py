#!/usr/bin/env python3
"""
Thor Session #91: Loud-Signal Sanity Check

Bias-floor and spectral controls showed that at signal_amp=0.02 (the value used
in S86-S90), the signal does not produce a statistically significant amp or MI
bump over the bistable-dynamics bias floor at any sigma.

Is the signal truly subthreshold at A=0.02, or is the whole pipeline broken?

Sanity: test with signal_amp in {0.02, 0.05, 0.10, 0.20} at sigma=0.022 (SR).
If transmission IS detectable at larger A, then A=0.02 is genuinely subthreshold
and the past results were measuring bistability geometry, not signal.
If transmission is not detectable at ANY A, the pipeline itself is wrong.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)


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
    return C_mean_hist


def response_amp_at(C_mean, dt, signal_freq, band=0.0005):
    steps = len(C_mean)
    freq = np.fft.rfftfreq(steps, d=dt)
    spec = np.fft.rfft(C_mean - C_mean.mean())
    idx = np.argmin(np.abs(freq - signal_freq))
    band_n = max(1, int(band / (freq[1] - freq[0]))) if len(freq) > 1 else 1
    lo, hi = max(0, idx - band_n), min(len(spec), idx + band_n + 1)
    return float(np.sqrt(np.mean(np.abs(spec[lo:hi])**2)) / np.sqrt(steps))


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


if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #91: Loud-Signal Sanity Check")
    print(f"Started: {start.isoformat()}\n")

    # Test at SR optimum sigma=0.022 with varying signal amplitudes
    sigma = 0.022
    signal_freq = 0.003
    dt = 0.1
    steps = 50_000
    warmup = 10_000
    n_seeds = 8
    N = 4
    amps = [0.02, 0.05, 0.10, 0.20]

    print(f"At sigma=0.022 (SR optimum), varying signal_amp:\n")
    for A in amps:
        amp_with_vals = []
        amp_without_vals = []
        mi_with_vals = []
        mi_without_vals = []
        for seed in range(n_seeds):
            C_with = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                              signal_freq=signal_freq, signal_amp=A, dt=dt)
            amp_with_vals.append(response_amp_at(C_with[warmup:], dt, signal_freq))
            # MI computed with the actual driving signal
            t = np.arange(steps)
            driving_sig = A * np.sin(2 * np.pi * signal_freq * t * dt)
            mi_with_vals.append(compute_mi_binned(C_with[warmup:], driving_sig[warmup:], n_bins=8))

            C_without = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100 + 1000,
                                 signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            amp_without_vals.append(response_amp_at(C_without[warmup:], dt, signal_freq))
            # MI computed against synthetic (non-driving) signal
            mi_without_vals.append(compute_mi_binned(C_without[warmup:], driving_sig[warmup:], n_bins=8))

        a_w = np.mean(amp_with_vals)
        a_w_se = np.std(amp_with_vals) / np.sqrt(n_seeds)
        a_wo = np.mean(amp_without_vals)
        a_wo_se = np.std(amp_without_vals) / np.sqrt(n_seeds)
        m_w = np.mean(mi_with_vals)
        m_w_se = np.std(mi_with_vals) / np.sqrt(n_seeds)
        m_wo = np.mean(mi_without_vals)
        m_wo_se = np.std(mi_without_vals) / np.sqrt(n_seeds)

        z_amp = (a_w - a_wo) / np.sqrt(a_w_se**2 + a_wo_se**2)
        z_mi = (m_w - m_wo) / np.sqrt(m_w_se**2 + m_wo_se**2)

        print(f"  A={A:.2f}: amp={a_w:.3f}+-{a_w_se:.3f} vs {a_wo:.3f}+-{a_wo_se:.3f} "
              f"(z={z_amp:5.2f})  MI={m_w:.4f}+-{m_w_se:.4f} vs {m_wo:.4f}+-{m_wo_se:.4f} "
              f"(z={z_mi:5.2f})")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
