#!/usr/bin/env python3
"""
Thor Session #92 (follow-up): Loud-Signal SR Sweep

Experiments A-C established that at signal_amp=0.02 (the value used in
S86-S90), neither response_amp nor histogram MI shows a statistically
significant SR peak under independent-seed controls. The response_amp
peak reported in S86 is driven by the bare bistability PSD evaluated
at signal_freq, not by signal transmission.

OPEN QUESTION: does this model exhibit SR at any signal amplitude?
If so, where?

At sigma=0.022 with A=0.10 (S91), z for MI was 2.98 (real transmission).
At A=0.20, z was 6.60. So the pipeline and signal CAN transmit — A=0.02
is just subthreshold.

This experiment runs an MI-based SR sweep at A=0.10 (where the signal
clearly transmits) and asks:
  - Where does MI_with - MI_without peak across sigma?
  - Is there a true SR peak, and if so where?

Prediction: at A=0.10, MI-based signal-specific response peaks at
sigma ~ 0.022 (the Kramers resonance point). If peak is elsewhere,
the "classical SR" narrative in this model is fundamentally wrong,
not just obscured by a bad estimator.
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


def response_amp_at(x, dt, freq_target, band=0.0005):
    steps = len(x)
    freq = np.fft.rfftfreq(steps, d=dt)
    spec = np.fft.rfft(x - x.mean())
    idx = np.argmin(np.abs(freq - freq_target))
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
    return float(mi)


if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #92 follow-up: Loud-Signal SR Sweep")
    print(f"Started: {start.isoformat()}\n")

    sigmas = [0.005, 0.008, 0.011, 0.014, 0.018, 0.022, 0.028, 0.035,
              0.050, 0.075, 0.100, 0.150]
    dt = 0.1
    steps = 50_000
    warmup = 10_000
    n_seeds = 8
    N = 4
    signal_freq = 0.003
    amps = [0.10, 0.20]

    t_arr = np.arange(steps - warmup)

    results = {'meta': {
        'session': '92-followup',
        'title': 'Loud-signal SR sweep',
        'sigmas': sigmas, 'amps': amps,
        'N': N, 'steps': steps, 'warmup': warmup, 'n_seeds': n_seeds,
        'signal_freq': signal_freq,
        'started': start.isoformat(),
    }, 'sweeps': {}}

    for A in amps:
        driving_ref = A * np.sin(2 * np.pi * signal_freq * (warmup + t_arr) * dt)

        print("=" * 74)
        print(f"SR SWEEP @ signal_amp = {A}")
        print("=" * 74)
        print(f"  {'sigma':>6} {'amp_with':>10} {'amp_wo':>10} {'z_amp':>6}  "
              f"{'MI_with':>9} {'MI_wo':>9} {'z_MI':>6}  {'eta_mi':>10}")

        rows = []
        for sigma in sigmas:
            aw_vals, awo_vals = [], []
            mi_w, mi_wo = [], []
            for seed in range(n_seeds):
                x_w = simulate(N=N, noise_std=sigma, steps=steps,
                               seed=seed * 100 + int(A * 1000),
                               signal_freq=signal_freq, signal_amp=A, dt=dt)
                aw_vals.append(response_amp_at(x_w[warmup:], dt, signal_freq))
                mi_w.append(compute_mi_binned(x_w[warmup:], driving_ref, n_bins=8))
                x_wo = simulate(N=N, noise_std=sigma, steps=steps,
                                seed=seed * 100 + int(A * 1000) + 50_000,
                                signal_freq=signal_freq, signal_amp=0.0, dt=dt)
                awo_vals.append(response_amp_at(x_wo[warmup:], dt, signal_freq))
                mi_wo.append(compute_mi_binned(x_wo[warmup:], driving_ref, n_bins=8))
            aw = np.array(aw_vals); awo = np.array(awo_vals)
            mw = np.array(mi_w); mwo = np.array(mi_wo)
            a_diff = aw.mean() - awo.mean()
            a_se = np.sqrt((aw.std()**2 + awo.std()**2) / n_seeds)
            z_a = float(a_diff / a_se) if a_se > 0 else 0.0
            m_diff = mw.mean() - mwo.mean()
            m_se = np.sqrt((mw.std()**2 + mwo.std()**2) / n_seeds)
            z_m = float(m_diff / m_se) if m_se > 0 else 0.0
            # Signal-specific MI in bits per sample ÷ power of signal
            eta_mi = float(m_diff / A) if m_diff > 0 else 0.0
            row = {
                'sigma': sigma,
                'amp_with': float(aw.mean()),
                'amp_without': float(awo.mean()),
                'z_amp': z_a,
                'mi_with': float(mw.mean()),
                'mi_without': float(mwo.mean()),
                'z_mi': z_m,
                'mi_diff': float(m_diff),
                'eta_mi_per_amp': eta_mi,
            }
            rows.append(row)
            print(f"  {sigma:6.4f} {aw.mean():10.4f} {awo.mean():10.4f} "
                  f"{z_a:6.2f}  {mw.mean():9.4f} {mwo.mean():9.4f} "
                  f"{z_m:6.2f}  {eta_mi:10.4f}")

        diffs = np.array([r['mi_diff'] for r in rows])
        zs = np.array([r['z_mi'] for r in rows])
        sigs = np.array([r['sigma'] for r in rows])
        idx = int(np.argmax(diffs))
        idx_z = int(np.argmax(zs))
        n_sig = int((zs > 2).sum())
        print(f"\n  Peak signal-specific MI at sigma = {sigs[idx]:.4f}  "
              f"(ΔMI = {diffs[idx]:.4f}, z = {zs[idx]:.2f})")
        print(f"  Peak z at sigma                 = {sigs[idx_z]:.4f}  "
              f"(z = {zs[idx_z]:.2f})")
        print(f"  Sigmas with z > 2: {n_sig} / {len(rows)}\n")

        results['sweeps'][f'A={A}'] = {
            'rows': rows,
            'peak_mi_sigma': float(sigs[idx]),
            'peak_z_sigma': float(sigs[idx_z]),
            'peak_mi_value': float(diffs[idx]),
            'peak_z_value': float(zs[idx_z]),
            'n_significant': n_sig,
        }

    with open('thor_session_92_loud_sweep_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"Completed in {elapsed:.0f}s")
