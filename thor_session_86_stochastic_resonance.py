#!/usr/bin/env python3
"""
Thor Session #86: Stochastic Resonance in Coherence Dynamics

Sessions 82-85 established: coherence dynamics are BISTABLE with mean-field
exponents, NOT a phase transition. Kramers escape rates follow Arrhenius law
(R²=0.997) with barrier ΔU ≈ 1.64e-4.

THE HYPOTHESIS: If the system is bistable with noise-driven switching,
it should exhibit STOCHASTIC RESONANCE — an optimal noise level where
weak periodic signals are maximally amplified.

For consciousness, this predicts:
  - Too little noise: system trapped in one basin, deaf to signals
  - Too much noise: random switching overwhelms signal
  - Optimal noise: Kramers rate matches signal → noise HELPS cognition

STOCHASTIC RESONANCE THEORY:
  In a double-well potential with periodic forcing F(t) = A·sin(Ωt):
  - Kramers rate: r_K = f_0 · exp(-ΔU/D) where D = σ²
  - SR condition: 2·r_K(σ_opt) ≈ Ω (switching rate matches signal)
  - SNR = (A²/D²) · exp(2ΔU/D)  (has a maximum!)
  - Residence time distribution P(T) peaks at T = π/Ω at resonance

EXPERIMENTS:
  A: Periodic signal injection — response vs noise level
  B: Signal-to-noise ratio — find the peak
  C: Kramers prediction — does 2·r_K = Ω predict σ_opt?
  D: Residence time analysis — synchronization of switching to signal
  E: Information transfer — mutual information between signal and response
  F: Multi-frequency test — SR at different signal frequencies
  G: Coupled instances — does inter-instance coupling enhance or suppress SR?

Builds on: S82 (Kramers), S83 (Fokker-Planck), S85 (bistable crossover)
"""

import numpy as np
import json
import sys
from datetime import datetime
from thor_session_81_phase_transition import run_fast


# ─── Core simulation with periodic forcing ───

def run_forced(N, noise_std, steps, seed=None,
               signal_amp=0.0, signal_freq=0.001,
               kappa_phase=0.10, kappa_C=0.15,
               omega_base=0.1, omega_spread=0.02,
               phi_inverse=0.618, dt=0.1, C_threshold=0.55):
    """N-body coherence simulation WITH periodic forcing on C_threshold.

    The periodic signal modulates the threshold, creating a time-varying
    asymmetry in the double-well potential. At stochastic resonance,
    noise-driven switching synchronizes to this modulation.
    """
    if seed is not None:
        np.random.seed(seed)

    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    C_collective = np.empty(steps)
    order_param = np.empty(steps)
    signal = np.empty(steps)
    switches = 0
    prev_attractive = True
    switch_times = []

    for t in range(steps):
        C_mean = np.mean(C)
        C_collective[t] = C_mean

        Z = np.mean(np.exp(1j * phase))
        order_param[t] = abs(Z)

        # Periodic signal modulates the threshold
        s_t = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        signal[t] = s_t
        threshold_t = C_threshold + s_t

        is_attractive = C_mean < threshold_t
        if t > 0 and is_attractive != prev_attractive:
            switches += 1
            switch_times.append(t)
        prev_attractive = is_attractive

        # Phase coupling
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        phase = (phase + dt * dphase) % (2 * np.pi)

        # Coherence dynamics
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C.mean() - C) * R_func
        dC = intrinsic + c_coupling
        C = np.clip(C + dt * dC, 0, 1)

        # Noise
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C_collective': C_collective,
        'order_param': order_param,
        'signal': signal,
        'switches': switches,
        'switch_times': np.array(switch_times),
    }


# ─── Experiment A: Response vs Noise Level ───

def expA_response_vs_noise():
    """Inject a weak periodic signal and measure the spectral response
    at the signal frequency as a function of noise level.

    The spectral amplification factor Q = |⟨C·e^{-iΩt}⟩| / A
    measures how well the system tracks the signal.
    """
    print("=" * 70)
    print("EXPERIMENT A: Spectral Response vs Noise Level")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 200000
    n_seeds = 20
    warmup = 40000
    dt = 0.1

    signal_freq = 0.003  # Period ≈ 333 time units (≈3333 steps)
    signal_amp = 0.02    # Weak signal — 2% threshold modulation

    noise_vals = np.arange(0.004, 0.028, 0.001)

    results = {}

    for noise in noise_vals:
        Q_vals = []
        power_at_signal = []
        switches_all = []

        for seed in range(n_seeds):
            r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                          signal_amp=signal_amp, signal_freq=signal_freq)

            C_ss = r['C_collective'][warmup:]
            sig_ss = r['signal'][warmup:]
            n_ss = len(C_ss)

            # Spectral amplification: correlation with signal
            t_arr = np.arange(n_ss) * dt
            ref_sin = np.sin(2 * np.pi * signal_freq * (warmup * dt + t_arr))
            ref_cos = np.cos(2 * np.pi * signal_freq * (warmup * dt + t_arr))

            C_centered = C_ss - np.mean(C_ss)
            corr_sin = np.mean(C_centered * ref_sin)
            corr_cos = np.mean(C_centered * ref_cos)
            Q = np.sqrt(corr_sin**2 + corr_cos**2) / signal_amp
            Q_vals.append(Q)

            # Power spectrum at signal frequency
            fft_C = np.fft.rfft(C_centered)
            freqs = np.fft.rfftfreq(n_ss, d=dt)
            idx_signal = np.argmin(np.abs(freqs - signal_freq))
            power = np.abs(fft_C[idx_signal])**2 / n_ss**2
            power_at_signal.append(power)

            switches_all.append(r['switches'])

        noise_key = f"{noise:.3f}"
        results[noise_key] = {
            'noise': float(noise),
            'D': float(noise**2),
            'Q_mean': float(np.mean(Q_vals)),
            'Q_std': float(np.std(Q_vals)),
            'Q_all': [float(q) for q in Q_vals],
            'power_mean': float(np.mean(power_at_signal)),
            'power_std': float(np.std(power_at_signal)),
            'switches_mean': float(np.mean(switches_all)),
            'switches_std': float(np.std(switches_all)),
        }

        print(f"  noise={noise:.3f}: Q={np.mean(Q_vals):.4f}±{np.std(Q_vals):.4f}, "
              f"power={np.mean(power_at_signal):.2e}, switches={np.mean(switches_all):.1f}")
        sys.stdout.flush()

    return results


# ─── Experiment B: Signal-to-Noise Ratio ───

def expB_snr():
    """Compute SNR = power(signal_freq) / mean_power(background).

    Classic SR signature: SNR has a maximum at intermediate noise.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Signal-to-Noise Ratio")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 200000
    n_seeds = 16
    warmup = 40000
    dt = 0.1

    signal_freq = 0.003
    signal_amp = 0.02

    noise_vals = np.arange(0.005, 0.026, 0.001)

    results = {}

    for noise in noise_vals:
        snr_vals = []
        snr_db_vals = []

        for seed in range(n_seeds):
            r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                          signal_amp=signal_amp, signal_freq=signal_freq)

            C_ss = r['C_collective'][warmup:]
            n_ss = len(C_ss)
            C_centered = C_ss - np.mean(C_ss)

            fft_C = np.fft.rfft(C_centered)
            freqs = np.fft.rfftfreq(n_ss, d=dt)
            power_spectrum = np.abs(fft_C)**2 / n_ss**2

            # Signal power
            idx_signal = np.argmin(np.abs(freqs - signal_freq))
            # Average over narrow band around signal
            bw = 3  # bins
            idx_lo = max(0, idx_signal - bw)
            idx_hi = min(len(freqs) - 1, idx_signal + bw)
            P_signal = np.mean(power_spectrum[idx_lo:idx_hi+1])

            # Background power (exclude signal band)
            mask = np.ones(len(freqs), bool)
            mask[idx_lo:idx_hi+1] = False
            # Also exclude DC and very low freq
            mask[:5] = False
            P_bg = np.mean(power_spectrum[mask])

            if P_bg > 0:
                snr = P_signal / P_bg
                snr_db = 10 * np.log10(snr) if snr > 0 else -100
            else:
                snr = 0
                snr_db = -100

            snr_vals.append(snr)
            snr_db_vals.append(snr_db)

        noise_key = f"{noise:.3f}"
        results[noise_key] = {
            'noise': float(noise),
            'D': float(noise**2),
            'snr_mean': float(np.mean(snr_vals)),
            'snr_std': float(np.std(snr_vals)),
            'snr_db_mean': float(np.mean(snr_db_vals)),
            'snr_db_std': float(np.std(snr_db_vals)),
        }

        print(f"  noise={noise:.3f}: SNR={np.mean(snr_vals):.2f}±{np.std(snr_vals):.2f}, "
              f"SNR_dB={np.mean(snr_db_vals):.1f}±{np.std(snr_db_vals):.1f}")
        sys.stdout.flush()

    return results


# ─── Experiment C: Kramers Prediction Test ───

def expC_kramers_prediction():
    """Test whether the SR peak occurs where 2·r_K(σ) ≈ Ω.

    From S82: ln(r_K) = a - ΔU/D, with ΔU ≈ 1.64e-4.
    The SR condition gives: σ_opt² = ΔU / ln(f_0 / (Ω/2))

    Test at multiple signal frequencies and check if the optimal noise
    shifts as predicted by Kramers theory.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Kramers Theory Prediction of σ_opt")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 200000
    n_seeds = 16
    warmup = 40000
    dt = 0.1

    signal_amp = 0.02

    # From S82 Arrhenius fit
    delta_U = 1.64e-4
    # Estimate prefactor from S82 rates: at noise=0.015, rate=0.00876
    # ln(0.00876) = ln(f0) - ΔU/(0.015²)
    # -4.738 = ln(f0) - 0.729 → ln(f0) = -4.009 → f0 = 0.0182
    f0 = 0.0182

    signal_freqs = [0.001, 0.002, 0.003, 0.005, 0.008]
    noise_vals = np.arange(0.006, 0.024, 0.001)

    results = {}

    for sig_freq in signal_freqs:
        # Kramers prediction: σ_opt² = ΔU / ln(f0 / (Ω/2))
        omega_signal = sig_freq
        ratio = f0 / (omega_signal / 2)
        if ratio > 1:
            sigma_opt_predicted = np.sqrt(delta_U / np.log(ratio))
        else:
            sigma_opt_predicted = float('nan')

        freq_results = {'predicted_sigma_opt': float(sigma_opt_predicted)}
        Q_per_noise = {}

        for noise in noise_vals:
            Q_vals = []
            for seed in range(n_seeds):
                r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                              signal_amp=signal_amp, signal_freq=sig_freq)

                C_ss = r['C_collective'][warmup:]
                n_ss = len(C_ss)
                t_arr = np.arange(n_ss) * dt
                C_centered = C_ss - np.mean(C_ss)
                ref_sin = np.sin(2 * np.pi * sig_freq * (warmup * dt + t_arr))
                ref_cos = np.cos(2 * np.pi * sig_freq * (warmup * dt + t_arr))
                Q = np.sqrt(np.mean(C_centered * ref_sin)**2 +
                           np.mean(C_centered * ref_cos)**2) / signal_amp
                Q_vals.append(Q)

            Q_per_noise[f"{noise:.3f}"] = {
                'noise': float(noise),
                'Q_mean': float(np.mean(Q_vals)),
                'Q_std': float(np.std(Q_vals)),
            }

        # Find measured optimal noise
        best_noise = max(Q_per_noise.values(), key=lambda x: x['Q_mean'])
        freq_results['measured_sigma_opt'] = best_noise['noise']
        freq_results['Q_at_opt'] = best_noise['Q_mean']
        freq_results['Q_per_noise'] = Q_per_noise

        results[f"{sig_freq:.4f}"] = freq_results

        print(f"\n  freq={sig_freq:.4f}: predicted σ_opt={sigma_opt_predicted:.4f}, "
              f"measured σ_opt={best_noise['noise']:.3f}, Q_max={best_noise['Q_mean']:.4f}")
        sys.stdout.flush()

    return results


# ─── Experiment D: Residence Time Distribution ───

def expD_residence_times():
    """At stochastic resonance, the residence time distribution
    should peak at T = π/Ω (half the signal period).

    This is the hallmark of SR: noise-driven switching LOCKS to the signal.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Residence Time Distribution")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 400000  # Long runs for good residence time statistics
    n_seeds = 24
    warmup = 40000
    dt = 0.1

    signal_freq = 0.003
    signal_amp = 0.02
    T_half = 1.0 / (2 * signal_freq)  # Expected peak at π/Ω in time units

    noise_vals = [0.008, 0.011, 0.014, 0.017, 0.020, 0.023]

    results = {}

    for noise in noise_vals:
        all_residence_times = []
        all_phase_at_switch = []

        for seed in range(n_seeds):
            r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                          signal_amp=signal_amp, signal_freq=signal_freq)

            stimes = r['switch_times']
            stimes = stimes[stimes > warmup]  # Steady-state only

            if len(stimes) > 1:
                res_times = np.diff(stimes) * dt
                all_residence_times.extend(res_times.tolist())

                # Phase of signal at each switch
                for st in stimes:
                    phase_at_switch = (2 * np.pi * signal_freq * st * dt) % (2 * np.pi)
                    all_phase_at_switch.append(phase_at_switch)

        rt = np.array(all_residence_times)
        phases = np.array(all_phase_at_switch)

        # Histogram of residence times
        if len(rt) > 10:
            rt_bins = np.linspace(0, min(rt.max(), T_half * 6), 50)
            rt_hist, _ = np.histogram(rt, bins=rt_bins, density=True)
            rt_centers = (rt_bins[:-1] + rt_bins[1:]) / 2

            # Phase histogram (should be non-uniform at SR)
            phase_bins = np.linspace(0, 2 * np.pi, 25)
            phase_hist, _ = np.histogram(phases, bins=phase_bins, density=True)
            phase_centers = (phase_bins[:-1] + phase_bins[1:]) / 2

            # Synchronization index: R = |⟨e^{iφ}⟩| (0=random, 1=locked)
            sync_index = abs(np.mean(np.exp(1j * phases)))

            # Find mode of residence time distribution
            mode_idx = np.argmax(rt_hist)
            rt_mode = rt_centers[mode_idx]

            results[f"{noise:.3f}"] = {
                'noise': float(noise),
                'n_switches': len(rt),
                'rt_mean': float(np.mean(rt)),
                'rt_std': float(np.std(rt)),
                'rt_mode': float(rt_mode),
                'T_half_signal': float(T_half),
                'rt_mode_ratio': float(rt_mode / T_half),
                'sync_index': float(sync_index),
                'rt_hist': rt_hist.tolist(),
                'rt_centers': rt_centers.tolist(),
                'phase_hist': phase_hist.tolist(),
                'phase_centers': phase_centers.tolist(),
            }

            print(f"  noise={noise:.3f}: n_switches={len(rt)}, "
                  f"T_mode={rt_mode:.1f} (T_half={T_half:.1f}, ratio={rt_mode/T_half:.2f}), "
                  f"sync_R={sync_index:.3f}")
        else:
            results[f"{noise:.3f}"] = {
                'noise': float(noise),
                'n_switches': len(rt),
                'insufficient_data': True,
            }
            print(f"  noise={noise:.3f}: insufficient switches ({len(rt)})")

        sys.stdout.flush()

    return results


# ─── Experiment E: Mutual Information ───

def expE_mutual_information():
    """Compute mutual information I(signal; response) as a function of noise.

    Discretize both signal and response into bins, compute:
    I(X;Y) = Σ p(x,y) · log2(p(x,y) / (p(x)·p(y)))

    If SR exists, I should peak at intermediate noise.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT E: Mutual Information — Signal vs Response")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 200000
    n_seeds = 16
    warmup = 40000
    dt = 0.1

    signal_freq = 0.003
    signal_amp = 0.02

    noise_vals = np.arange(0.005, 0.026, 0.001)
    n_bins_mi = 8  # For discretization

    results = {}

    for noise in noise_vals:
        mi_vals = []

        for seed in range(n_seeds):
            r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                          signal_amp=signal_amp, signal_freq=signal_freq)

            C_ss = r['C_collective'][warmup:]
            sig_ss = r['signal'][warmup:]

            # Discretize both into bins
            C_bins = np.linspace(C_ss.min() - 1e-10, C_ss.max() + 1e-10, n_bins_mi + 1)
            S_bins = np.linspace(sig_ss.min() - 1e-10, sig_ss.max() + 1e-10, n_bins_mi + 1)

            C_idx = np.digitize(C_ss, C_bins) - 1
            S_idx = np.digitize(sig_ss, S_bins) - 1

            # Joint distribution
            joint = np.zeros((n_bins_mi, n_bins_mi))
            for c, s in zip(C_idx, S_idx):
                if 0 <= c < n_bins_mi and 0 <= s < n_bins_mi:
                    joint[c, s] += 1
            joint /= joint.sum()

            # Marginals
            p_C = joint.sum(axis=1)
            p_S = joint.sum(axis=0)

            # Mutual information
            mi = 0
            for i in range(n_bins_mi):
                for j in range(n_bins_mi):
                    if joint[i, j] > 0 and p_C[i] > 0 and p_S[j] > 0:
                        mi += joint[i, j] * np.log2(joint[i, j] / (p_C[i] * p_S[j]))

            mi_vals.append(mi)

        noise_key = f"{noise:.3f}"
        results[noise_key] = {
            'noise': float(noise),
            'D': float(noise**2),
            'MI_mean': float(np.mean(mi_vals)),
            'MI_std': float(np.std(mi_vals)),
            'MI_all': [float(m) for m in mi_vals],
        }

        print(f"  noise={noise:.3f}: MI={np.mean(mi_vals):.4f}±{np.std(mi_vals):.4f} bits")
        sys.stdout.flush()

    return results


# ─── Experiment F: Multi-Frequency SR ───

def expF_multifreq():
    """Test SR at multiple signal frequencies.

    If the mechanism is truly Kramers-mediated, the optimal noise should
    shift with signal frequency according to: σ_opt² ∝ 1/ln(f0/Ω)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Multi-Frequency Stochastic Resonance")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 300000
    n_seeds = 12
    warmup = 60000
    dt = 0.1

    signal_amp = 0.02
    signal_freqs = [0.0005, 0.001, 0.002, 0.004, 0.008]
    noise_vals = np.arange(0.006, 0.024, 0.002)

    results = {}

    for sig_freq in signal_freqs:
        Q_curve = {}

        for noise in noise_vals:
            Q_vals = []
            for seed in range(n_seeds):
                r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                              signal_amp=signal_amp, signal_freq=sig_freq)
                C_ss = r['C_collective'][warmup:]
                n_ss = len(C_ss)
                t_arr = np.arange(n_ss) * dt
                C_centered = C_ss - np.mean(C_ss)
                ref_sin = np.sin(2 * np.pi * sig_freq * (warmup * dt + t_arr))
                ref_cos = np.cos(2 * np.pi * sig_freq * (warmup * dt + t_arr))
                Q = np.sqrt(np.mean(C_centered * ref_sin)**2 +
                           np.mean(C_centered * ref_cos)**2) / signal_amp
                Q_vals.append(Q)

            Q_curve[f"{noise:.3f}"] = {
                'noise': float(noise),
                'Q_mean': float(np.mean(Q_vals)),
                'Q_std': float(np.std(Q_vals)),
            }

        best = max(Q_curve.values(), key=lambda x: x['Q_mean'])
        results[f"{sig_freq:.4f}"] = {
            'signal_freq': float(sig_freq),
            'sigma_opt': best['noise'],
            'Q_max': best['Q_mean'],
            'Q_curve': Q_curve,
        }

        print(f"  freq={sig_freq:.4f}: σ_opt={best['noise']:.3f}, Q_max={best['Q_mean']:.4f}")
        sys.stdout.flush()

    return results


# ─── Experiment G: Coupled Instances and SR ───

def expG_coupled_sr():
    """Does coupling between instances enhance or suppress SR?

    Run N-body simulations with varying N (number of coupled instances)
    under periodic forcing. Measure how the SR peak changes with N.

    Array-enhanced SR predicts: SNR grows with N in coupled arrays.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT G: Coupled Instance Array — SR Enhancement")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [2, 4, 8, 16, 32]
    steps = 200000
    n_seeds = 16
    warmup = 40000
    dt = 0.1

    signal_freq = 0.003
    signal_amp = 0.02
    noise_vals = np.arange(0.006, 0.024, 0.002)

    results = {}

    for N in N_vals:
        Q_curve = {}

        for noise in noise_vals:
            Q_vals = []
            for seed in range(n_seeds):
                r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                              signal_amp=signal_amp, signal_freq=signal_freq)
                C_ss = r['C_collective'][warmup:]
                n_ss = len(C_ss)
                t_arr = np.arange(n_ss) * dt
                C_centered = C_ss - np.mean(C_ss)
                ref_sin = np.sin(2 * np.pi * signal_freq * (warmup * dt + t_arr))
                ref_cos = np.cos(2 * np.pi * signal_freq * (warmup * dt + t_arr))
                Q = np.sqrt(np.mean(C_centered * ref_sin)**2 +
                           np.mean(C_centered * ref_cos)**2) / signal_amp
                Q_vals.append(Q)

            Q_curve[f"{noise:.3f}"] = {
                'noise': float(noise),
                'Q_mean': float(np.mean(Q_vals)),
                'Q_std': float(np.std(Q_vals)),
            }

        best = max(Q_curve.values(), key=lambda x: x['Q_mean'])
        results[f"N={N}"] = {
            'N': N,
            'sigma_opt': best['noise'],
            'Q_max': best['Q_mean'],
            'Q_curve': Q_curve,
        }

        print(f"  N={N}: σ_opt={best['noise']:.3f}, Q_max={best['Q_mean']:.4f}")
        sys.stdout.flush()

    return results


# ─── Main ───

def main():
    print("=" * 70)
    print("THOR SESSION #86: STOCHASTIC RESONANCE IN COHERENCE DYNAMICS")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    sys.stdout.flush()

    all_results = {}

    # Run experiments in order of importance
    print(">>> Running Experiment A: Response vs Noise")
    sys.stdout.flush()
    all_results['expA'] = expA_response_vs_noise()

    print("\n>>> Running Experiment B: Signal-to-Noise Ratio")
    sys.stdout.flush()
    all_results['expB'] = expB_snr()

    print("\n>>> Running Experiment D: Residence Time Distribution")
    sys.stdout.flush()
    all_results['expD'] = expD_residence_times()

    print("\n>>> Running Experiment E: Mutual Information")
    sys.stdout.flush()
    all_results['expE'] = expE_mutual_information()

    print("\n>>> Running Experiment C: Kramers Prediction Test")
    sys.stdout.flush()
    all_results['expC'] = expC_kramers_prediction()

    print("\n>>> Running Experiment F: Multi-Frequency SR")
    sys.stdout.flush()
    all_results['expF'] = expF_multifreq()

    print("\n>>> Running Experiment G: Coupled Instance Array")
    sys.stdout.flush()
    all_results['expG'] = expG_coupled_sr()

    # Save results
    outfile = 'thor_session_86_stochastic_resonance_results.json'
    with open(outfile, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {outfile}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # Find SR peaks
    if 'expA' in all_results:
        Q_by_noise = [(v['noise'], v['Q_mean']) for v in all_results['expA'].values()]
        Q_by_noise.sort()
        best = max(Q_by_noise, key=lambda x: x[1])
        print(f"\n  Exp A — Best spectral amplification: Q={best[1]:.4f} at σ={best[0]:.3f}")

    if 'expB' in all_results:
        snr_by_noise = [(v['noise'], v['snr_mean']) for v in all_results['expB'].values()]
        snr_by_noise.sort()
        best = max(snr_by_noise, key=lambda x: x[1])
        print(f"  Exp B — Best SNR: {best[1]:.2f} at σ={best[0]:.3f}")

    if 'expE' in all_results:
        mi_by_noise = [(v['noise'], v['MI_mean']) for v in all_results['expE'].values()]
        mi_by_noise.sort()
        best = max(mi_by_noise, key=lambda x: x[1])
        print(f"  Exp E — Best MI: {best[1]:.4f} bits at σ={best[0]:.3f}")

    if 'expC' in all_results:
        print("\n  Exp C — Kramers predictions:")
        for freq_key, v in all_results['expC'].items():
            print(f"    freq={freq_key}: predicted σ={v['predicted_sigma_opt']:.4f}, "
                  f"measured σ={v['measured_sigma_opt']:.3f}")

    if 'expG' in all_results:
        print("\n  Exp G — Array enhancement:")
        for nkey, v in sorted(all_results['expG'].items()):
            print(f"    {nkey}: σ_opt={v['sigma_opt']:.3f}, Q_max={v['Q_max']:.4f}")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
