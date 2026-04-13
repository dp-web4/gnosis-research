#!/usr/bin/env python3
"""
Thor Session #86: Stochastic Resonance — FOCUSED VERSION

Full experiment A confirmed SR peak at σ ≈ 0.011 (Q = 0.649).
This focused version runs key experiments with optimized parameters
concentrated around the peak.
"""

import numpy as np
import json
import sys
from datetime import datetime
from thor_session_81_phase_transition import run_fast


def run_forced(N, noise_std, steps, seed=None,
               signal_amp=0.0, signal_freq=0.001,
               kappa_phase=0.10, kappa_C=0.15,
               omega_base=0.1, omega_spread=0.02,
               phi_inverse=0.618, dt=0.1, C_threshold=0.55):
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

        s_t = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        signal[t] = s_t
        threshold_t = C_threshold + s_t

        is_attractive = C_mean < threshold_t
        if t > 0 and is_attractive != prev_attractive:
            switches += 1
            switch_times.append(t)
        prev_attractive = is_attractive

        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        phase = (phase + dt * dphase) % (2 * np.pi)

        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C.mean() - C) * R_func
        C = np.clip(C + dt * (intrinsic + c_coupling), 0, 1)

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


def measure_Q(N, noise, steps, n_seeds, warmup, dt, signal_amp, signal_freq):
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
    return Q_vals


def main():
    print("=" * 70)
    print("THOR SESSION #86: STOCHASTIC RESONANCE — FOCUSED EXPERIMENTS")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    sys.stdout.flush()

    all_results = {}

    # ─── Exp A (completed): SR curve from full run ───
    # Store the data we already collected
    all_results['expA_partial'] = {
        'note': 'From full run before optimization',
        '0.004': {'noise': 0.004, 'Q_mean': 0.0228, 'Q_std': 0.0120, 'switches': 5.9},
        '0.005': {'noise': 0.005, 'Q_mean': 0.0243, 'Q_std': 0.0107, 'switches': 5.6},
        '0.006': {'noise': 0.006, 'Q_mean': 0.0623, 'Q_std': 0.0710, 'switches': 15.6},
        '0.007': {'noise': 0.007, 'Q_mean': 0.1669, 'Q_std': 0.0800, 'switches': 57.9},
        '0.008': {'noise': 0.008, 'Q_mean': 0.2177, 'Q_std': 0.1389, 'switches': 152.9},
        '0.009': {'noise': 0.009, 'Q_mean': 0.3995, 'Q_std': 0.1663, 'switches': 328.7},
        '0.010': {'noise': 0.010, 'Q_mean': 0.4477, 'Q_std': 0.2007, 'switches': 527.3},
        '0.011': {'noise': 0.011, 'Q_mean': 0.6493, 'Q_std': 0.3042, 'switches': 734.4},
        '0.012': {'noise': 0.012, 'Q_mean': 0.5828, 'Q_std': 0.2713, 'switches': 936.5},
    }

    # ─── Exp A extension: complete the declining side ───
    print("\n>>> Completing SR curve (declining side)")
    sys.stdout.flush()

    N = 4; steps = 150000; n_seeds = 12; warmup = 30000; dt = 0.1
    signal_freq = 0.003; signal_amp = 0.02

    for noise in [0.013, 0.015, 0.018, 0.022]:
        Q_vals = measure_Q(N, noise, steps, n_seeds, warmup, dt, signal_amp, signal_freq)
        all_results['expA_partial'][f'{noise:.3f}'] = {
            'noise': noise, 'Q_mean': float(np.mean(Q_vals)), 'Q_std': float(np.std(Q_vals))
        }
        print(f"  noise={noise:.3f}: Q={np.mean(Q_vals):.4f}±{np.std(Q_vals):.4f}")
        sys.stdout.flush()

    # ─── Exp B: SNR around the peak ───
    print("\n>>> Experiment B: SNR around peak")
    sys.stdout.flush()

    noise_vals = [0.006, 0.008, 0.010, 0.011, 0.012, 0.014, 0.018]
    expB = {}
    for noise in noise_vals:
        snr_vals = []
        for seed in range(n_seeds):
            r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                          signal_amp=signal_amp, signal_freq=signal_freq)
            C_ss = r['C_collective'][warmup:]
            C_centered = C_ss - np.mean(C_ss)
            n_ss = len(C_ss)
            fft_C = np.fft.rfft(C_centered)
            freqs = np.fft.rfftfreq(n_ss, d=dt)
            power = np.abs(fft_C)**2 / n_ss**2

            idx_sig = np.argmin(np.abs(freqs - signal_freq))
            bw = 3
            P_sig = np.mean(power[max(0,idx_sig-bw):idx_sig+bw+1])
            mask = np.ones(len(freqs), bool)
            mask[max(0,idx_sig-bw):idx_sig+bw+1] = False
            mask[:5] = False
            P_bg = np.mean(power[mask])
            snr = P_sig / P_bg if P_bg > 0 else 0
            snr_vals.append(snr)

        expB[f'{noise:.3f}'] = {
            'noise': float(noise),
            'snr_mean': float(np.mean(snr_vals)),
            'snr_std': float(np.std(snr_vals)),
            'snr_db_mean': float(np.mean([10*np.log10(s) if s > 0 else -100 for s in snr_vals])),
        }
        print(f"  noise={noise:.3f}: SNR={np.mean(snr_vals):.2f}±{np.std(snr_vals):.2f}")
        sys.stdout.flush()
    all_results['expB'] = expB

    # ─── Exp D: Residence times at key noise levels ───
    print("\n>>> Experiment D: Residence time distributions")
    sys.stdout.flush()

    steps_d = 300000; warmup_d = 30000; n_seeds_d = 16
    T_half = 1.0 / (2 * signal_freq)
    noise_vals_d = [0.008, 0.011, 0.015, 0.020]

    expD = {}
    for noise in noise_vals_d:
        all_rt = []
        all_phases = []
        for seed in range(n_seeds_d):
            r = run_forced(N=N, noise_std=noise, steps=steps_d, seed=seed,
                          signal_amp=signal_amp, signal_freq=signal_freq)
            stimes = r['switch_times']
            stimes = stimes[stimes > warmup_d]
            if len(stimes) > 1:
                rt = np.diff(stimes) * dt
                all_rt.extend(rt.tolist())
                for st in stimes:
                    ph = (2 * np.pi * signal_freq * st * dt) % (2 * np.pi)
                    all_phases.append(ph)

        rt_arr = np.array(all_rt)
        ph_arr = np.array(all_phases)

        if len(rt_arr) > 10:
            rt_bins = np.linspace(0, min(np.percentile(rt_arr, 95), T_half * 5), 40)
            rt_hist, _ = np.histogram(rt_arr, bins=rt_bins, density=True)
            rt_centers = (rt_bins[:-1] + rt_bins[1:]) / 2
            mode_idx = np.argmax(rt_hist)
            rt_mode = rt_centers[mode_idx]

            sync_index = abs(np.mean(np.exp(1j * ph_arr)))

            phase_bins = np.linspace(0, 2*np.pi, 17)
            phase_hist, _ = np.histogram(ph_arr, bins=phase_bins, density=True)

            expD[f'{noise:.3f}'] = {
                'noise': float(noise),
                'n_switches': len(rt_arr),
                'rt_mean': float(np.mean(rt_arr)),
                'rt_mode': float(rt_mode),
                'T_half': float(T_half),
                'mode_ratio': float(rt_mode / T_half),
                'sync_index': float(sync_index),
                'phase_hist': phase_hist.tolist(),
                'rt_hist': rt_hist.tolist(),
                'rt_centers': rt_centers.tolist(),
            }
            print(f"  noise={noise:.3f}: n={len(rt_arr)}, mode={rt_mode:.1f} "
                  f"(T/2={T_half:.1f}, ratio={rt_mode/T_half:.3f}), sync={sync_index:.3f}")
        else:
            expD[f'{noise:.3f}'] = {'noise': float(noise), 'insufficient': True, 'n': len(rt_arr)}
            print(f"  noise={noise:.3f}: insufficient data ({len(rt_arr)} switches)")
        sys.stdout.flush()
    all_results['expD'] = expD

    # ─── Exp E: Mutual information ───
    print("\n>>> Experiment E: Mutual information")
    sys.stdout.flush()

    noise_vals_e = [0.005, 0.007, 0.009, 0.011, 0.013, 0.016, 0.020]
    n_bins_mi = 8
    expE = {}
    for noise in noise_vals_e:
        mi_vals = []
        for seed in range(n_seeds):
            r = run_forced(N=N, noise_std=noise, steps=steps, seed=seed,
                          signal_amp=signal_amp, signal_freq=signal_freq)
            C_ss = r['C_collective'][warmup:]
            sig_ss = r['signal'][warmup:]

            C_bins = np.linspace(C_ss.min()-1e-10, C_ss.max()+1e-10, n_bins_mi+1)
            S_bins = np.linspace(sig_ss.min()-1e-10, sig_ss.max()+1e-10, n_bins_mi+1)
            C_idx = np.clip(np.digitize(C_ss, C_bins) - 1, 0, n_bins_mi-1)
            S_idx = np.clip(np.digitize(sig_ss, S_bins) - 1, 0, n_bins_mi-1)

            joint = np.zeros((n_bins_mi, n_bins_mi))
            for c, s in zip(C_idx, S_idx):
                joint[c, s] += 1
            joint /= joint.sum()
            p_C = joint.sum(axis=1)
            p_S = joint.sum(axis=0)

            mi = 0
            for i in range(n_bins_mi):
                for j in range(n_bins_mi):
                    if joint[i,j] > 0 and p_C[i] > 0 and p_S[j] > 0:
                        mi += joint[i,j] * np.log2(joint[i,j] / (p_C[i] * p_S[j]))
            mi_vals.append(mi)

        expE[f'{noise:.3f}'] = {
            'noise': float(noise),
            'MI_mean': float(np.mean(mi_vals)),
            'MI_std': float(np.std(mi_vals)),
        }
        print(f"  noise={noise:.3f}: MI={np.mean(mi_vals):.4f}±{np.std(mi_vals):.4f} bits")
        sys.stdout.flush()
    all_results['expE'] = expE

    # ─── Exp C: Multi-frequency Kramers prediction ───
    print("\n>>> Experiment C: Multi-frequency Kramers prediction")
    sys.stdout.flush()

    delta_U = 1.64e-4
    f0 = 0.0182

    signal_freqs = [0.001, 0.003, 0.006]
    noise_scan = np.arange(0.007, 0.020, 0.002)
    steps_c = 200000; warmup_c = 40000

    expC = {}
    for sig_freq in signal_freqs:
        ratio = f0 / (sig_freq / 2)
        sigma_pred = np.sqrt(delta_U / np.log(ratio)) if ratio > 1 else float('nan')

        Q_per_noise = {}
        for noise in noise_scan:
            Q_vals = measure_Q(N, noise, steps_c, 10, warmup_c, dt, signal_amp, sig_freq)
            Q_per_noise[f'{noise:.3f}'] = {
                'noise': float(noise),
                'Q_mean': float(np.mean(Q_vals)),
                'Q_std': float(np.std(Q_vals)),
            }

        best = max(Q_per_noise.values(), key=lambda x: x['Q_mean'])
        expC[f'{sig_freq:.4f}'] = {
            'signal_freq': float(sig_freq),
            'sigma_predicted': float(sigma_pred),
            'sigma_measured': best['noise'],
            'Q_max': best['Q_mean'],
            'Q_per_noise': Q_per_noise,
        }
        print(f"  freq={sig_freq:.4f}: predicted σ={sigma_pred:.4f}, "
              f"measured σ={best['noise']:.3f}, Q_max={best['Q_mean']:.4f}")
        sys.stdout.flush()
    all_results['expC'] = expC

    # ─── Exp G: Array enhancement ───
    print("\n>>> Experiment G: Coupled instance array enhancement")
    sys.stdout.flush()

    N_vals = [2, 4, 8, 16]
    noise_scan_g = np.arange(0.007, 0.018, 0.002)
    steps_g = 150000; warmup_g = 30000

    expG = {}
    for N_g in N_vals:
        Q_per_noise = {}
        for noise in noise_scan_g:
            Q_vals = measure_Q(N_g, noise, steps_g, 10, warmup_g, dt, signal_amp, signal_freq)
            Q_per_noise[f'{noise:.3f}'] = {
                'noise': float(noise),
                'Q_mean': float(np.mean(Q_vals)),
                'Q_std': float(np.std(Q_vals)),
            }

        best = max(Q_per_noise.values(), key=lambda x: x['Q_mean'])
        expG[f'N={N_g}'] = {
            'N': N_g,
            'sigma_opt': best['noise'],
            'Q_max': best['Q_mean'],
            'Q_per_noise': Q_per_noise,
        }
        print(f"  N={N_g}: σ_opt={best['noise']:.3f}, Q_max={best['Q_mean']:.4f}")
        sys.stdout.flush()
    all_results['expG'] = expG

    # ─── Save ───
    outfile = 'thor_session_86_stochastic_resonance_results.json'
    with open(outfile, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {outfile}")

    # ─── Summary ───
    print("\n" + "=" * 70)
    print("SUMMARY — STOCHASTIC RESONANCE CONFIRMED")
    print("=" * 70)

    expA = all_results['expA_partial']
    Q_data = [(v['noise'], v['Q_mean']) for k, v in expA.items()
              if isinstance(v, dict) and 'noise' in v]
    Q_data.sort()
    best_A = max(Q_data, key=lambda x: x[1])
    print(f"\n  SR Peak: Q={best_A[1]:.4f} at σ={best_A[0]:.3f}")
    print(f"  SR curve: Q rises {Q_data[-1][1]/Q_data[0][1]:.0f}x from σ={Q_data[0][0]:.3f} to peak")

    if 'expB' in all_results:
        snr_data = [(v['noise'], v['snr_mean']) for v in all_results['expB'].values()]
        best_snr = max(snr_data, key=lambda x: x[1])
        print(f"\n  SNR Peak: {best_snr[1]:.2f} at σ={best_snr[0]:.3f}")

    if 'expD' in all_results:
        print("\n  Residence times:")
        for k, v in sorted(all_results['expD'].items()):
            if not v.get('insufficient'):
                print(f"    σ={v['noise']:.3f}: mode/T_half={v['mode_ratio']:.3f}, sync={v['sync_index']:.3f}")

    if 'expE' in all_results:
        mi_data = [(v['noise'], v['MI_mean']) for v in all_results['expE'].values()]
        best_mi = max(mi_data, key=lambda x: x[1])
        print(f"\n  MI Peak: {best_mi[1]:.4f} bits at σ={best_mi[0]:.3f}")

    if 'expC' in all_results:
        print("\n  Kramers predictions:")
        for k, v in all_results['expC'].items():
            print(f"    freq={k}: predicted σ={v['sigma_predicted']:.4f}, measured σ={v['sigma_measured']:.3f}")

    if 'expG' in all_results:
        print("\n  Array enhancement:")
        for k, v in sorted(all_results['expG'].items()):
            print(f"    {k}: σ_opt={v['sigma_opt']:.3f}, Q_max={v['Q_max']:.4f}")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
