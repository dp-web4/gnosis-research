#!/usr/bin/env python3
"""
Thor Session #92: Falsifiability Test of S86 SR Peak

S91 discovered that the response_amp metric used in S86-S90 is NOT a
signal-specific detector: with/without-signal amplitudes at signal_freq
are statistically indistinguishable. The "stochastic resonance peak"
at sigma ~ 0.022 may be a feature of the bare bistability spectrum,
not of signal transmission.

S91 left three sharp predictions. This session tests all three.

Experiment A — NATURAL PSD (Prediction #4):
  Simulate with signal_amp=0 across sigma. Measure the peak frequency
  of the C_mean power spectrum. Prediction: at sigma ~ 0.022, the
  natural bistability spectrum peaks near signal_freq=0.003.
  → explains why amp at signal_freq has a bump at sigma=0.022 without
    any signal being transmitted.

Experiment B — INDEPENDENT-SEED RESPONSE-AMP SR SWEEP (Prediction #1):
  Reproduce the S86 SR sweep, but compute amp_with - amp_without
  with INDEPENDENT seeds. Prediction: z < 2 at every sigma; the
  "SR peak" dissolves.

Experiment C — INDEPENDENT-SEED MI-BASED SR SWEEP (Prediction #2):
  Same sweep, but with histogram MI(C_mean, driving signal) vs
  MI(C_mean_no_signal, synthetic signal) under independent seeds.
  Prediction: MI-based signal-specific curve peaks at sigma ~ 0.022
  (the real SR location).

Together these determine whether the S86-S90 "SR discovery" survives.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)


# ─── Shared simulator (matches S91 model exactly) ───

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


def psd(x, dt):
    """Return (freq, power). Uses Welch-like averaging via segment halving."""
    x = x - x.mean()
    # Simple Hann-window periodogram
    w = np.hanning(len(x))
    xw = x * w
    spec = np.fft.rfft(xw)
    freq = np.fft.rfftfreq(len(x), d=dt)
    # normalization: power per unit frequency
    norm = (w**2).sum() * dt
    power = (np.abs(spec)**2) / norm
    return freq, power


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


# ─── Experiment A: Natural PSD vs sigma ───

def experiment_A(sigmas, N=4, dt=0.1, steps=50_000, warmup=10_000,
                 signal_freq=0.003, n_seeds=5):
    print("=" * 70)
    print("EXPERIMENT A — Natural bistability PSD (signal_amp=0)")
    print("=" * 70)
    print(f"  N={N}  steps={steps}  warmup={warmup}  n_seeds={n_seeds}\n")
    print(f"  {'sigma':>6} {'peak_freq':>10} {'peak_power':>12} "
          f"{'power@sigf':>12} {'peak/sigf ratio':>16}")

    rows = []
    for sigma in sigmas:
        peak_fs = []
        peak_ps = []
        pow_sigfs = []
        for seed in range(n_seeds):
            x = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 7 + 3,
                         signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            x = x[warmup:]
            freqs, pw = psd(x, dt)
            # Restrict peak search to 0 < f < 0.05 Hz (well-resolved band)
            mask = (freqs > 1e-4) & (freqs < 0.05)
            if not mask.any():
                continue
            k = np.argmax(pw[mask])
            peak_f = freqs[mask][k]
            peak_p = pw[mask][k]
            peak_fs.append(peak_f)
            peak_ps.append(peak_p)
            idx_sf = np.argmin(np.abs(freqs - signal_freq))
            pow_sigfs.append(pw[idx_sf])
        pf = float(np.mean(peak_fs))
        pp = float(np.mean(peak_ps))
        ps = float(np.mean(pow_sigfs))
        ratio = pp / ps if ps > 0 else np.inf
        row = {
            'sigma': sigma,
            'peak_freq': round(pf, 6),
            'peak_power': pp,
            'power_at_signal_freq': ps,
            'ratio_peak_over_sigf': ratio,
            'peak_freq_stderr': float(np.std(peak_fs) / np.sqrt(len(peak_fs))),
        }
        rows.append(row)
        print(f"  {sigma:6.4f} {pf:10.5f} {pp:12.4e} {ps:12.4e} {ratio:16.3f}")

    # Find sigma where peak_freq crosses signal_freq
    arr_sig = np.array([r['sigma'] for r in rows])
    arr_pf = np.array([r['peak_freq'] for r in rows])
    if (arr_pf > signal_freq).any() and (arr_pf < signal_freq).any():
        # linear interpolation
        cross = None
        for i in range(len(arr_sig) - 1):
            if (arr_pf[i] - signal_freq) * (arr_pf[i+1] - signal_freq) <= 0:
                f1, f2 = arr_pf[i], arr_pf[i+1]
                s1, s2 = arr_sig[i], arr_sig[i+1]
                if f2 != f1:
                    cross = s1 + (signal_freq - f1) * (s2 - s1) / (f2 - f1)
                else:
                    cross = (s1 + s2) / 2
                break
        print(f"\n  sigma at which natural peak_freq = signal_freq "
              f"({signal_freq}): ~{cross:.4f}" if cross else "\n  no crossing")
    else:
        print(f"\n  natural peak_freq never crosses signal_freq={signal_freq} "
              f"in this sigma range.")

    return rows


# ─── Experiment B: Independent-seed response-amp SR sweep ───

def experiment_B(sigmas, N=4, dt=0.1, steps=50_000, warmup=10_000,
                 signal_freq=0.003, signal_amp=0.02, n_seeds=8):
    print("\n" + "=" * 70)
    print("EXPERIMENT B — Independent-seed response_amp SR sweep")
    print("=" * 70)
    print(f"  N={N}  steps={steps}  n_seeds={n_seeds}  "
          f"A={signal_amp}  f={signal_freq}\n")
    print(f"  {'sigma':>6} {'amp_with':>10} {'amp_without':>12} "
          f"{'diff':>10} {'z':>6} {'survives?':>10}")

    rows = []
    for sigma in sigmas:
        aw_vals, awo_vals = [], []
        for seed in range(n_seeds):
            x_w = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                           signal_freq=signal_freq, signal_amp=signal_amp, dt=dt)
            aw_vals.append(response_amp_at(x_w[warmup:], dt, signal_freq))
            # Independent seed for the no-signal baseline
            x_wo = simulate(N=N, noise_std=sigma, steps=steps,
                            seed=seed * 100 + 50_000,
                            signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            awo_vals.append(response_amp_at(x_wo[warmup:], dt, signal_freq))
        aw = np.array(aw_vals)
        awo = np.array(awo_vals)
        a_w = float(aw.mean()); a_w_se = float(aw.std() / np.sqrt(n_seeds))
        a_wo = float(awo.mean()); a_wo_se = float(awo.std() / np.sqrt(n_seeds))
        diff = a_w - a_wo
        z = diff / np.sqrt(a_w_se**2 + a_wo_se**2) if (a_w_se > 0 or a_wo_se > 0) else 0.0
        survives = "yes" if z > 2 else ("marginal" if z > 1 else "NO")
        row = {
            'sigma': sigma,
            'amp_with': a_w,
            'amp_with_se': a_w_se,
            'amp_without': a_wo,
            'amp_without_se': a_wo_se,
            'diff': diff,
            'z': z,
            'survives': survives,
        }
        rows.append(row)
        print(f"  {sigma:6.4f} {a_w:10.4f} {a_wo:12.4f} {diff:10.4f} "
              f"{z:6.2f} {survives:>10}")

    zs = np.array([r['z'] for r in rows])
    max_z = float(zs.max())
    any_sig = int((zs > 2).sum())
    print(f"\n  max z across sigma: {max_z:.2f}")
    print(f"  sigmas with z > 2: {any_sig} / {len(rows)}")
    if any_sig == 0:
        print("  VERDICT: response_amp SR peak DISSOLVES with independent-seed controls.")
    elif any_sig <= 2:
        print("  VERDICT: response_amp signal detection is marginal / noisy.")
    else:
        print("  VERDICT: response_amp does carry signal information at some sigma.")

    return rows


# ─── Experiment C: Independent-seed MI SR sweep ───

def experiment_C(sigmas, N=4, dt=0.1, steps=50_000, warmup=10_000,
                 signal_freq=0.003, signal_amp=0.02, n_seeds=8, n_bins=8):
    print("\n" + "=" * 70)
    print("EXPERIMENT C — Independent-seed MI SR sweep")
    print("=" * 70)
    print(f"  N={N}  steps={steps}  n_seeds={n_seeds}  A={signal_amp}  "
          f"f={signal_freq}  n_bins={n_bins}\n")
    print(f"  {'sigma':>6} {'MI_with':>10} {'MI_without':>12} "
          f"{'diff':>10} {'z':>6} {'survives?':>10}")

    rows = []
    t_arr = np.arange(steps - warmup)
    driving_ref = signal_amp * np.sin(2 * np.pi * signal_freq * (warmup + t_arr) * dt)

    for sigma in sigmas:
        mi_w, mi_wo = [], []
        for seed in range(n_seeds):
            x_w = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                           signal_freq=signal_freq, signal_amp=signal_amp, dt=dt)
            mi_w.append(compute_mi_binned(x_w[warmup:], driving_ref, n_bins=n_bins))
            x_wo = simulate(N=N, noise_std=sigma, steps=steps,
                            seed=seed * 100 + 50_000,
                            signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            mi_wo.append(compute_mi_binned(x_wo[warmup:], driving_ref, n_bins=n_bins))
        mw = np.array(mi_w)
        mwo = np.array(mi_wo)
        m_w = float(mw.mean()); m_w_se = float(mw.std() / np.sqrt(n_seeds))
        m_wo = float(mwo.mean()); m_wo_se = float(mwo.std() / np.sqrt(n_seeds))
        diff = m_w - m_wo
        z = diff / np.sqrt(m_w_se**2 + m_wo_se**2) if (m_w_se > 0 or m_wo_se > 0) else 0.0
        survives = "yes" if z > 2 else ("marginal" if z > 1 else "NO")
        row = {
            'sigma': sigma,
            'mi_with': m_w,
            'mi_with_se': m_w_se,
            'mi_without': m_wo,
            'mi_without_se': m_wo_se,
            'diff': diff,
            'z': z,
            'survives': survives,
        }
        rows.append(row)
        print(f"  {sigma:6.4f} {m_w:10.5f} {m_wo:12.5f} {diff:10.5f} "
              f"{z:6.2f} {survives:>10}")

    # Find peak of (signal-specific MI)
    diffs = np.array([r['diff'] for r in rows])
    zs = np.array([r['z'] for r in rows])
    sigs = np.array([r['sigma'] for r in rows])
    idx_max_diff = int(np.argmax(diffs))
    idx_max_z = int(np.argmax(zs))
    n_sig = int((zs > 2).sum())
    print(f"\n  peak signal-specific MI at sigma = {sigs[idx_max_diff]:.4f}  "
          f"(ΔMI = {diffs[idx_max_diff]:.4f})")
    print(f"  peak z-score at sigma        = {sigs[idx_max_z]:.4f}  "
          f"(z = {zs[idx_max_z]:.2f})")
    print(f"  sigmas with z > 2: {n_sig} / {len(rows)}")

    return rows


# ─── Main ───

if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #92: SR Falsifiability — Three Controls")
    print(f"Started: {start.isoformat()}\n")

    # Sigma grid — focused around S86 SR peak (0.022) and S90 efficiency peak (0.100),
    # with denser coverage below/around SR where the S91 bistability hypothesis predicts
    # peak-frequency = signal_freq.
    sigmas = [0.005, 0.008, 0.011, 0.014, 0.018, 0.022, 0.028, 0.035,
              0.050, 0.075, 0.100, 0.150]

    dt = 0.1
    steps = 50_000
    warmup = 10_000
    signal_freq = 0.003
    signal_amp = 0.02
    N = 4

    rows_A = experiment_A(sigmas, N=N, dt=dt, steps=steps, warmup=warmup,
                          signal_freq=signal_freq, n_seeds=5)
    rows_B = experiment_B(sigmas, N=N, dt=dt, steps=steps, warmup=warmup,
                          signal_freq=signal_freq, signal_amp=signal_amp,
                          n_seeds=8)
    rows_C = experiment_C(sigmas, N=N, dt=dt, steps=steps, warmup=warmup,
                          signal_freq=signal_freq, signal_amp=signal_amp,
                          n_seeds=8, n_bins=8)

    out = {
        'meta': {
            'session': 92,
            'title': 'SR Falsifiability - Three Controls',
            'params': {
                'N': N, 'dt': dt, 'steps': steps, 'warmup': warmup,
                'signal_freq': signal_freq, 'signal_amp': signal_amp,
                'sigmas': sigmas,
            },
            'started': start.isoformat(),
        },
        'experiment_A_natural_psd': rows_A,
        'experiment_B_resp_amp_indep_seed': rows_B,
        'experiment_C_mi_indep_seed': rows_C,
    }
    with open('thor_session_92_sr_falsifiability_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s")
