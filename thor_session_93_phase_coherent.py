#!/usr/bin/env python3
"""
Thor Session #93: Phase-Coherent Detection Recovers Subthreshold SR

S92 showed that response_amp (|FFT at signal_freq|) is a broken detector:
it produced a "SR peak" at A=0.02 from pure bistability Lorentzian noise.
S92 Prediction #4 claimed an adaptive (phase-locked) detector would
recover real SR even at A=0.02, because a matched filter projects the
signal onto a known axis instead of rectifying noise.

THIS SESSION: implement the phase-coherent detector and compare directly
with response_amp across the S92 sigma grid at S86's amplitude A=0.02.

Why it should work (theory):
- |FFT at f_s| is a magnitude ≈ sqrt(I² + Q²). Under null, it has a
  Rayleigh mean of sqrt(π/2) σ_n. Signal adds to I; resulting Rice
  mean shift is quadratic in A (for weak A): ΔE[|X|] ≈ A²/(4σ_n).
  Weak-signal sensitivity decays as A².
- Phase-coherent in-phase projection: I = <x(t) sin(2π f_s t)>.
  Under null, E[I] = 0, Var(I) = (S(f_s)/T). Signal adds A*g/2 to I
  directly — shift is LINEAR in A.
- So at low A, phase-coherent SNR scales as A; magnitude SNR as A².

This predicts: phase-coherent detector should detect SR at A=0.02,
where response_amp cannot. We test this directly.

We also compute a combined test statistic T² = z_I² + z_Q² to account
for unknown phase delay in the system response.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)


# ─── Shared simulator (matches S92 exactly) ───

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
    """S86/S92-style narrowband magnitude detector."""
    steps = len(x)
    freq = np.fft.rfftfreq(steps, d=dt)
    spec = np.fft.rfft(x - x.mean())
    idx = np.argmin(np.abs(freq - freq_target))
    band_n = max(1, int(band / (freq[1] - freq[0]))) if len(freq) > 1 else 1
    lo, hi = max(0, idx - band_n), min(len(spec), idx + band_n + 1)
    return float(np.sqrt(np.mean(np.abs(spec[lo:hi])**2)) / np.sqrt(steps))


def phase_coherent_IQ(x, dt, signal_freq, t_offset):
    """Matched-filter projection of x onto sin / cos at signal_freq,
    with known initial phase (same reference used by the driving signal).

    The driving signal in simulate() is signal_amp * sin(2π f_s t * dt)
    with t indexed from 0. After dropping warmup, the returned x[0]
    corresponds to global time index t_offset = warmup.
    """
    x = x - x.mean()
    t = (np.arange(len(x)) + t_offset) * dt
    sin_ref = np.sin(2 * np.pi * signal_freq * t)
    cos_ref = np.cos(2 * np.pi * signal_freq * t)
    I = float(np.mean(x * sin_ref))
    Q = float(np.mean(x * cos_ref))
    return I, Q


def sweep(sigmas, A, n_seeds, N=4, dt=0.1, steps=50_000, warmup=10_000,
          signal_freq=0.003):
    """For each sigma, run n_seeds WITH signal (A) and n_seeds WITHOUT,
    using independent seeds. Record response_amp, I, Q for each run."""
    rows = []
    print(f"\n>> Sweep at A={A}, n_seeds={n_seeds}, sigmas={sigmas}")
    for sigma in sigmas:
        aw, awo = [], []
        iw, iwo = [], []
        qw, qwo = [], []
        for seed in range(n_seeds):
            x_w = simulate(N=N, noise_std=sigma, steps=steps,
                           seed=seed * 100,
                           signal_freq=signal_freq, signal_amp=A, dt=dt)
            xw = x_w[warmup:]
            aw.append(response_amp_at(xw, dt, signal_freq))
            Iw, Qw = phase_coherent_IQ(xw, dt, signal_freq, t_offset=warmup)
            iw.append(Iw)
            qw.append(Qw)
            x_wo = simulate(N=N, noise_std=sigma, steps=steps,
                            seed=seed * 100 + 50_000,
                            signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            xwo = x_wo[warmup:]
            awo.append(response_amp_at(xwo, dt, signal_freq))
            Iwo, Qwo = phase_coherent_IQ(xwo, dt, signal_freq, t_offset=warmup)
            iwo.append(Iwo)
            qwo.append(Qwo)
        aw = np.array(aw); awo = np.array(awo)
        iw = np.array(iw); iwo = np.array(iwo)
        qw = np.array(qw); qwo = np.array(qwo)

        def zdiff(a, b):
            m = a.mean() - b.mean()
            se = np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))
            return float(m), float(se), float(m / se) if se > 0 else 0.0

        amp_m, amp_se, z_amp = zdiff(aw, awo)
        I_m, I_se, z_I = zdiff(iw, iwo)
        Q_m, Q_se, z_Q = zdiff(qw, qwo)
        T2 = z_I**2 + z_Q**2

        # Signal vector norm vs noise scale
        I_pooled_se = np.sqrt(iw.var(ddof=1)/len(iw) + iwo.var(ddof=1)/len(iwo))
        Q_pooled_se = np.sqrt(qw.var(ddof=1)/len(qw) + qwo.var(ddof=1)/len(qwo))
        vec_mag = np.sqrt(I_m**2 + Q_m**2)
        vec_se = np.sqrt((I_m * I_pooled_se)**2 + (Q_m * Q_pooled_se)**2) / max(vec_mag, 1e-12)
        z_vec = vec_mag / vec_se if vec_se > 0 else 0.0

        # In expected-signal direction: since signal is A sin(ωt), the
        # in-phase component is I. For a system with arbitrary phase delay
        # φ, the signal contributes A*g/2 * cos(φ) to I and -A*g/2*sin(φ)
        # to Q. The best unbiased combination when phase is unknown is T².
        # When phase is known (matched filter), use z_I.

        row = {
            'sigma': sigma,
            'amp_with': float(aw.mean()), 'amp_without': float(awo.mean()),
            'z_amp': z_amp,
            'I_with': float(iw.mean()), 'I_without': float(iwo.mean()),
            'z_I': z_I,
            'Q_with': float(qw.mean()), 'Q_without': float(qwo.mean()),
            'z_Q': z_Q,
            'T2': T2,
            'z_vec': z_vec,
            'vec_mag': vec_mag,
        }
        rows.append(row)
        print(f"  σ={sigma:6.4f}  z_amp={z_amp:+6.2f}  "
              f"z_I={z_I:+6.2f}  z_Q={z_Q:+6.2f}  "
              f"T²={T2:6.1f}  z_vec={z_vec:5.2f}")
    return rows


# ─── Main ───

if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #93: Phase-Coherent SR Detection")
    print(f"Started: {start.isoformat()}\n")

    sigmas_fine = [0.008, 0.011, 0.014, 0.018, 0.022, 0.028,
                   0.035, 0.050, 0.075, 0.100]
    n_seeds = 16

    # Sweep 1: A=0.02 (S86's amplitude where response_amp failed)
    results_A02 = sweep(sigmas_fine, A=0.02, n_seeds=n_seeds)

    # Sweep 2: A=0.00 — pure null control. All z should be |z| < 2.
    results_null = sweep(sigmas_fine, A=0.00, n_seeds=n_seeds)

    # Sweep 3: A=0.20 — strong signal, confirms both detectors at classical SR
    results_A20 = sweep([0.014, 0.022, 0.050], A=0.20, n_seeds=8)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY — A=0.02 (where response_amp failed in S92)")
    print("=" * 70)
    print(f"  {'σ':>7} {'z_amp':>7} {'z_I':>7} {'z_Q':>7} {'T²':>8} "
          f"{'amp detects?':>14} {'PL detects?':>12}")
    for r in results_A02:
        amp_ok = "YES" if abs(r['z_amp']) > 2 else "no"
        # T² > 6 ≈ p < 0.05 with 2 df (chi-squared critical value)
        pl_ok = "YES" if r['T2'] > 6.0 else "no"
        print(f"  {r['sigma']:7.4f} {r['z_amp']:+7.2f} "
              f"{r['z_I']:+7.2f} {r['z_Q']:+7.2f} {r['T2']:8.2f} "
              f"{amp_ok:>14} {pl_ok:>12}")

    print("\n" + "=" * 70)
    print("NULL CONTROL (A=0.00) — everything should be |z|<2")
    print("=" * 70)
    max_T2_null = max(r['T2'] for r in results_null)
    max_z_amp_null = max(abs(r['z_amp']) for r in results_null)
    print(f"  max T² across null = {max_T2_null:.2f}  "
          f"(expect < 6 under null with 10 sigmas)")
    print(f"  max |z_amp| across null = {max_z_amp_null:.2f}  "
          f"(expect < 3 across 10 sigmas)")

    # Save everything
    out = {
        'meta': {
            'session': 93,
            'title': 'Phase-Coherent SR Detection',
            'params': {
                'N': 4, 'dt': 0.1, 'steps': 50_000, 'warmup': 10_000,
                'signal_freq': 0.003, 'n_seeds': n_seeds,
                'sigmas_fine': sigmas_fine,
            },
            'started': start.isoformat(),
        },
        'sweep_A02': results_A02,
        'sweep_null': results_null,
        'sweep_A20': results_A20,
    }
    with open('thor_session_93_phase_coherent_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s")
