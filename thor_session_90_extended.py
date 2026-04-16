#!/usr/bin/env python3
"""
Thor Session #90 Extended: Find the True Efficiency Peak

Main run showed sigma_eta (N-body) at the upper edge (0.025). Extend the
range to find where efficiency actually peaks — or confirm that it keeps
rising until the system destroys signal transmission.

Also: refine sigma_eta (collective), which was at the LOWER edge (0.006).
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.path.insert(0, '.')
from thor_session_90_efficiency import (
    simulate, compute_mi_binned, compute_ep_nbody, response_amp_at_signal
)

sys.stdout.reconfigure(line_buffering=True)


def sweep_efficiency(sigmas, N=4, steps=60_000, warmup=10_000, n_seeds=3,
                     signal_amp=0.02, signal_freq=0.003, dt=0.1, label=""):
    results = []
    for sigma in sigmas:
        mi_vals = []
        ep_nbody_vals = []
        ep_coll_vals = []
        amp_vals = []
        ep_C_vals = []
        ep_phase_vals = []

        for seed in range(n_seeds):
            r_sig = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                             signal_freq=signal_freq, signal_amp=signal_amp, dt=dt)
            C_ss = r_sig['C_mean'][warmup:]
            sig_ss = r_sig['signal'][warmup:]
            mi_vals.append(compute_mi_binned(C_ss, sig_ss, n_bins=8))
            amp_vals.append(response_amp_at_signal(C_ss, dt, signal_freq))

            r_ep = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100 + 500,
                            signal_amp=0.0, dt=dt)
            ep = compute_ep_nbody(r_ep, warmup, dt)
            ep_nbody_vals.append(ep['ep_nbody'])
            ep_coll_vals.append(ep['ep_collective'])
            ep_C_vals.append(ep['ep_C_total'])
            ep_phase_vals.append(ep['ep_phase_total'])

        mi = float(np.mean(mi_vals))
        ep_nb = float(np.mean(ep_nbody_vals))
        ep_c = float(np.mean(ep_coll_vals))

        entry = {
            'sigma': round(float(sigma), 4),
            'MI_bits': round(mi, 5),
            'MI_std': round(float(np.std(mi_vals)), 5),
            'ep_nbody': round(ep_nb, 2),
            'ep_collective': round(ep_c, 2),
            'ep_C': round(float(np.mean(ep_C_vals)), 2),
            'ep_phase': round(float(np.mean(ep_phase_vals)), 2),
            'response_amp': round(float(np.mean(amp_vals)), 6),
            'eta_nbody': round(mi / ep_nb if ep_nb > 0 else 0, 7),
            'eta_collective': round(mi / ep_c if ep_c > 0 else 0, 6),
        }
        results.append(entry)
        print(f"  {label} σ={sigma:.4f}: MI={mi:.4f}±{entry['MI_std']:.4f} "
              f"EP_nb={ep_nb:7.1f} EP_c={ep_c:6.2f} "
              f"η_nb={entry['eta_nbody']:.5f} η_c={entry['eta_collective']:.5f} "
              f"amp={entry['response_amp']:.3f}")
    return results


if __name__ == '__main__':
    start = datetime.now()
    print(f"Thor Session #90 Extended: Finding the True Efficiency Peak")
    print(f"Started: {start.isoformat()}\n")

    # =================================================================
    # Extended upper sigma range for N-body efficiency peak
    # =================================================================
    print("=" * 70)
    print("EXTENSION 1: High-sigma range (is eta_nbody monotone or does it peak?)")
    print("=" * 70)
    hi_sigmas = np.array([0.025, 0.030, 0.035, 0.040, 0.045, 0.050,
                          0.060, 0.075, 0.100, 0.150, 0.200])
    hi_results = sweep_efficiency(hi_sigmas, label="hi")

    # =================================================================
    # Finer low sigma range for collective efficiency peak
    # =================================================================
    print("\n" + "=" * 70)
    print("EXTENSION 2: Low-sigma range (finer resolution near eta_coll peak)")
    print("=" * 70)
    lo_sigmas = np.array([0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008])
    lo_results = sweep_efficiency(lo_sigmas, steps=80_000, label="lo")

    # Find peaks in each range
    all_sigs = np.concatenate([np.array([r['sigma'] for r in lo_results]),
                                np.array([r['sigma'] for r in hi_results])])
    all_eta_nb = np.concatenate([np.array([r['eta_nbody'] for r in lo_results]),
                                  np.array([r['eta_nbody'] for r in hi_results])])
    all_eta_c = np.concatenate([np.array([r['eta_collective'] for r in lo_results]),
                                 np.array([r['eta_collective'] for r in hi_results])])
    all_MI = np.concatenate([np.array([r['MI_bits'] for r in lo_results]),
                             np.array([r['MI_bits'] for r in hi_results])])

    idx_eta_nb = int(np.argmax(all_eta_nb))
    idx_eta_c = int(np.argmax(all_eta_c))
    idx_MI = int(np.argmax(all_MI))

    print("\n" + "=" * 70)
    print("COMBINED PEAKS (extended range)")
    print("=" * 70)
    print(f"  sigma_eta_nbody_peak  = {all_sigs[idx_eta_nb]:.4f} (η = {all_eta_nb[idx_eta_nb]:.5f} bits/EP)")
    print(f"  sigma_eta_coll_peak   = {all_sigs[idx_eta_c]:.4f} (η = {all_eta_c[idx_eta_c]:.5f} bits/EP)")
    print(f"  sigma_MI_peak         = {all_sigs[idx_MI]:.4f} (MI = {all_MI[idx_MI]:.4f} bits)")

    results = {
        'extension_high_sigma': hi_results,
        'extension_low_sigma': lo_results,
        'sigma_eta_nbody_peak': float(all_sigs[idx_eta_nb]),
        'sigma_eta_collective_peak': float(all_sigs[idx_eta_c]),
        'sigma_MI_peak': float(all_sigs[idx_MI]),
        'eta_nbody_peak': float(all_eta_nb[idx_eta_nb]),
        'eta_collective_peak': float(all_eta_c[idx_eta_c]),
    }

    with open('thor_session_90_extended_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
