#!/usr/bin/env python3
"""
Thor Session #91: Spectral Control

Control 3 (bias floor) showed histogram MI at sigma=0.100 is indistinguishable
from MI computed with signal absent from dynamics. But does the signal ACTUALLY
transmit at all sigma? The response-amplitude-at-signal-frequency is
signal-specific in a way that histogram MI is not.

Two quantities:
  resp_amp_with_signal:    narrow-band FFT amplitude at signal_freq in
                           C_mean when signal is driving dynamics
  resp_amp_without_signal: same narrow-band amplitude when signal_amp=0
                           (pure noise floor in that band)

If resp_amp_with >> resp_amp_without, the signal IS transmitting.
We also compute a SPECTRAL efficiency:
  eta_spec = (resp_amp_with - resp_amp_without)^2 / EP_nbody

This is a signal-specific alternative to eta = MI/EP. Its peak location tells
us where signal transmission is most thermodynamically efficient, without the
MI-estimator pathology.

Hypothesis: the SPECTRAL efficiency peak will be at SR (sigma ~ 0.022), not
at sigma ~ 0.100 where the S90 MI-based peak sits. If so, the S90 "efficiency
peak" is a measurement artifact and the true efficiency optimum coincides
with SR.
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
    C_hist = np.empty((steps, N))
    phase_hist = np.empty((steps, N))
    drift_C = np.empty((steps, N))
    drift_phase = np.empty((steps, N))
    C_mean_hist = np.empty(steps)
    for t in range(steps):
        C_hist[t] = C
        phase_hist[t] = phase
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean
        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        is_attractive = (C_mean + signal) < C_threshold
        sign = 1.0 if is_attractive else -1.0
        if kappa_phase > 0:
            sin_diff = np.sin(phase[None, :] - phase[:, None])
            np.fill_diagonal(sin_diff, 0)
            dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        else:
            dphase = omega.copy()
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
        'C_mean': C_mean_hist,
    }


def response_amp_at(C_mean, dt, signal_freq, band=0.0005):
    steps = len(C_mean)
    freq = np.fft.rfftfreq(steps, d=dt)
    spec = np.fft.rfft(C_mean - C_mean.mean())
    idx = np.argmin(np.abs(freq - signal_freq))
    band_n = max(1, int(band / (freq[1] - freq[0]))) if len(freq) > 1 else 1
    lo, hi = max(0, idx - band_n), min(len(spec), idx + band_n + 1)
    return float(np.sqrt(np.mean(np.abs(spec[lo:hi])**2)) / np.sqrt(steps))


def compute_ep_nbody(result, warmup, dt):
    C = result['C'][warmup:]
    phase = result['phase'][warmup:]
    drift_C = result['drift_C'][warmup:]
    drift_phase = result['drift_phase'][warmup:]
    N = C.shape[1]
    ep = 0.0
    for i in range(N):
        dC_i = np.diff(C[:, i])
        mu_i = drift_C[:-1, i]
        res_i = dC_i - mu_i * dt
        D_i = np.mean(res_i**2) / (2 * dt)
        if D_i > 0:
            ep += np.mean(mu_i**2) / D_i
        dphase_i = np.diff(phase[:, i])
        dphase_i = (dphase_i + np.pi) % (2 * np.pi) - np.pi
        mu_i = drift_phase[:-1, i]
        res_i = dphase_i - mu_i * dt
        res_i = (res_i + np.pi) % (2 * np.pi) - np.pi
        D_i = np.mean(res_i**2) / (2 * dt)
        if D_i > 0:
            ep += np.mean(mu_i**2) / D_i
    return float(ep)


if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #91: Spectral Efficiency Control")
    print(f"Started: {start.isoformat()}\n")

    sigmas = [0.011, 0.018, 0.022, 0.035, 0.050, 0.075, 0.100, 0.150]
    N = 4
    dt = 0.1
    steps = 50_000
    warmup = 10_000
    n_seeds = 5
    signal_freq = 0.003
    signal_amp = 0.02

    print("=" * 70)
    print("Spectral amplitude WITH vs WITHOUT signal, and eta_spec = A^2/EP")
    print("=" * 70)

    rows = []
    for sigma in sigmas:
        amp_with = []
        amp_without = []
        ep_vals = []
        for seed in range(n_seeds):
            r_with = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                              signal_freq=signal_freq, signal_amp=signal_amp, dt=dt)
            amp_with.append(response_amp_at(r_with['C_mean'][warmup:], dt, signal_freq))

            r_without = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100 + 1000,
                                 signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            amp_without.append(response_amp_at(r_without['C_mean'][warmup:], dt, signal_freq))
            ep_vals.append(compute_ep_nbody(r_without, warmup, dt))

        a_with = float(np.mean(amp_with))
        a_with_std = float(np.std(amp_with) / np.sqrt(n_seeds))
        a_without = float(np.mean(amp_without))
        a_without_std = float(np.std(amp_without) / np.sqrt(n_seeds))
        a_signal = max(0.0, a_with - a_without)  # Signal-specific amplitude
        ep = float(np.mean(ep_vals))

        # eta_spec: use (signal-specific amplitude)^2 as the "information"
        # proxy. Power of the signal-transmitted component.
        eta_spec = (a_signal**2) / ep if ep > 0 else 0
        # z-score of the amplitude difference
        z = (a_with - a_without) / np.sqrt(a_with_std**2 + a_without_std**2)

        row = {
            'sigma': sigma,
            'amp_with': round(a_with, 5),
            'amp_with_stderr': round(a_with_std, 5),
            'amp_without': round(a_without, 5),
            'amp_without_stderr': round(a_without_std, 5),
            'amp_signal_specific': round(a_signal, 5),
            'z_score_amp_diff': round(z, 2),
            'ep_nbody': round(ep, 2),
            'eta_spec': round(eta_spec, 9),
        }
        rows.append(row)
        print(f"  sigma={sigma:.3f}: amp_with={a_with:.4f}+-{a_with_std:.4f}  "
              f"amp_without={a_without:.4f}+-{a_without_std:.4f}  "
              f"z={z:5.2f}  EP_nb={ep:6.2f}  eta_spec={eta_spec:.2e}")

    # Find peaks
    sigs = np.array([r['sigma'] for r in rows])
    amp_signal_specific = np.array([r['amp_signal_specific'] for r in rows])
    eta_spec = np.array([r['eta_spec'] for r in rows])
    z_scores = np.array([r['z_score_amp_diff'] for r in rows])

    idx_amp = int(np.argmax(amp_signal_specific))
    idx_eta = int(np.argmax(eta_spec))
    idx_z = int(np.argmax(z_scores))

    print("\n" + "=" * 70)
    print("PEAK LOCATIONS (spectral analysis)")
    print("=" * 70)
    print(f"  sigma @ max signal-specific amp: {sigs[idx_amp]:.3f} "
          f"(amp_signal = {amp_signal_specific[idx_amp]:.4f})")
    print(f"  sigma @ max z-score:             {sigs[idx_z]:.3f} "
          f"(z = {z_scores[idx_z]:.2f})")
    print(f"  sigma @ max eta_spec:            {sigs[idx_eta]:.3f} "
          f"(eta_spec = {eta_spec[idx_eta]:.2e})")

    print("\n" + "=" * 70)
    print("COMPARISON to S90 MI-based peaks")
    print("=" * 70)
    print(f"  S90 MI peak:            sigma ~ 0.018-0.025 (consistent with SR)")
    print(f"  S90 MI/EP efficiency peak: sigma ~ 0.100")
    print(f"  Spectral amp peak (this session):       sigma = {sigs[idx_amp]:.3f}")
    print(f"  Spectral efficiency peak (this session): sigma = {sigs[idx_eta]:.3f}")
    if abs(sigs[idx_eta] - sigs[idx_amp]) / sigs[idx_amp] < 0.5:
        print(f"  VERDICT: spectral efficiency coincides with spectral amp peak — "
              f"TRUE efficiency is at SR, not 5x beyond it.")
    else:
        print(f"  VERDICT: spectral efficiency still decouples from amp peak.")

    out = {
        'data': rows,
        'peaks': {
            'sigma_amp_specific': float(sigs[idx_amp]),
            'sigma_z_max': float(sigs[idx_z]),
            'sigma_eta_spec': float(sigs[idx_eta]),
            'amp_peak_value': float(amp_signal_specific[idx_amp]),
            'eta_spec_peak_value': float(eta_spec[idx_eta]),
        },
    }
    with open('thor_session_91_spectral_results.json', 'w') as f:
        json.dump(out, f, indent=2)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
