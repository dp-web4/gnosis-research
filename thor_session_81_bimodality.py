#!/usr/bin/env python3
"""
Thor Session #81, Part 2: Distribution Shape at the Critical Noise

The Binder cumulant U₄ went deeply negative (down to -40 for N=8),
indicating BIMODAL distribution — two coexisting states.

This follow-up characterizes the distribution P(C) at and near
the critical noise to understand what the bimodality looks like.
"""

import numpy as np
import json
import sys
from datetime import datetime
from thor_session_81_phase_transition import run_fast


def analyze_distribution():
    """Histogram P(C) at several noise levels across the transition."""
    print("=" * 70)
    print("DISTRIBUTION SHAPE ANALYSIS")
    print("=" * 70)
    sys.stdout.flush()

    noise_vals = [0.005, 0.008, 0.010, 0.011, 0.012, 0.014, 0.016, 0.020]
    N = 4
    steps = 20000
    n_seeds = 12
    bins = np.linspace(0, 1, 51)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    results = {}

    for noise in noise_vals:
        all_C = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.3)
            all_C.extend(r['C_collective'][ss:].tolist())

        C_arr = np.array(all_C)
        hist, _ = np.histogram(C_arr, bins=bins, density=True)

        # Find peaks (local maxima)
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                peaks.append((bin_centers[i], hist[i]))

        # Bimodality coefficient: (skew² + 1) / kurtosis
        from scipy.stats import skew, kurtosis
        sk = skew(C_arr)
        ku = kurtosis(C_arr, fisher=False)  # Excess=False → raw kurtosis
        bimod_coeff = (sk**2 + 1) / ku if ku > 0 else 0

        # Dip test approximation: fraction of distribution in the valley
        # between the two highest peaks
        n_peaks = len(peaks)
        if n_peaks >= 2:
            peaks_sorted = sorted(peaks, key=lambda p: p[1], reverse=True)
            p1_loc, p2_loc = sorted([peaks_sorted[0][0], peaks_sorted[1][0]])
            # Valley depth between peaks
            valley_mask = (bin_centers > p1_loc) & (bin_centers < p2_loc)
            if valley_mask.any():
                valley_min = hist[valley_mask].min()
                peak_avg = (peaks_sorted[0][1] + peaks_sorted[1][1]) / 2
                valley_ratio = valley_min / peak_avg if peak_avg > 0 else 1
            else:
                valley_ratio = 1.0
        else:
            valley_ratio = 1.0

        results[f"{noise:.3f}"] = {
            'noise': noise,
            'n_peaks': n_peaks,
            'peaks': peaks[:3],  # Top 3 peaks
            'bimod_coeff': float(bimod_coeff),
            'valley_ratio': float(valley_ratio),
            'mean': float(np.mean(C_arr)),
            'std': float(np.std(C_arr)),
            'skew': float(sk),
            'kurtosis': float(ku),
            'hist': hist.tolist(),
        }

        print(f"\n  noise={noise:.3f}: mean={np.mean(C_arr):.3f}, std={np.std(C_arr):.3f}")
        print(f"    Peaks ({n_peaks}): {', '.join(f'C={p[0]:.2f}' for p in peaks[:3])}")
        print(f"    Bimodality coeff = {bimod_coeff:.4f} (>5/9=0.556 → bimodal)")
        print(f"    Valley ratio = {valley_ratio:.3f} (low → deep valley → bimodal)")
        print(f"    Skew = {sk:.3f}, Kurtosis = {ku:.3f}")
        sys.stdout.flush()

    return results


def bistability_switching():
    """Analyze switching dynamics between the two states near critical noise."""
    print("\n" + "=" * 70)
    print("BISTABILITY SWITCHING DYNAMICS")
    print("=" * 70)
    sys.stdout.flush()

    noise = 0.011  # Critical noise
    N = 4
    steps = 50000
    n_seeds = 6

    # Threshold between the two states
    C_boundary = 0.70  # Midpoint between high-C (0.85) and breathing center (0.55)

    all_durations_high = []
    all_durations_low = []

    for seed in range(n_seeds):
        r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
        ss = int(steps * 0.2)
        C_ts = r['C_collective'][ss:]

        # Find state residence times
        in_high = C_ts > C_boundary
        switches = np.where(np.diff(in_high.astype(int)) != 0)[0]

        if len(switches) > 2:
            durations = np.diff(switches)
            for i, dur in enumerate(durations):
                # Even indices: starting state, odd: other state
                start_state = in_high[switches[i]]
                if start_state:
                    all_durations_high.append(dur)
                else:
                    all_durations_low.append(dur)

    if all_durations_high and all_durations_low:
        dh = np.array(all_durations_high)
        dl = np.array(all_durations_low)

        print(f"\n  At noise = {noise}:")
        print(f"    High-C state (C > {C_boundary}):")
        print(f"      Mean residence time: {np.mean(dh):.1f} steps")
        print(f"      Median: {np.median(dh):.1f}, Max: {np.max(dh)}")
        print(f"      N episodes: {len(dh)}")

        print(f"    Low-C state (C < {C_boundary}):")
        print(f"      Mean residence time: {np.mean(dl):.1f} steps")
        print(f"      Median: {np.median(dl):.1f}, Max: {np.max(dl)}")
        print(f"      N episodes: {len(dl)}")

        # Check if durations follow exponential (Poisson process → memoryless switching)
        # vs power-law (critical → scale-free switching)
        # Simple test: coefficient of variation. CV=1 → exponential, CV>1 → heavy-tailed
        cv_high = np.std(dh) / np.mean(dh)
        cv_low = np.std(dl) / np.mean(dl)
        print(f"\n    CV(high) = {cv_high:.3f}, CV(low) = {cv_low:.3f}")
        print(f"    (CV=1 → exponential/Poisson, CV>1 → heavy-tailed/critical)")

        # Fraction of time in each state
        frac_high = np.sum(dh) / (np.sum(dh) + np.sum(dl))
        print(f"\n    Fraction in high-C: {frac_high:.3f}")
        print(f"    Fraction in low-C: {1-frac_high:.3f}")
    else:
        print(f"    Insufficient switching at noise={noise}")

    # Now check across noise levels
    print(f"\n  --- Switching rate vs noise ---")
    for noise in [0.008, 0.009, 0.010, 0.011, 0.012, 0.013, 0.014, 0.016]:
        switch_counts = []
        for seed in range(8):
            r = run_fast(N=N, noise_std=noise, steps=30000, seed=seed)
            ss = int(30000 * 0.2)
            C_ts = r['C_collective'][ss:]
            in_high = C_ts > C_boundary
            n_switches = np.sum(np.abs(np.diff(in_high.astype(int))))
            switch_counts.append(n_switches)

        rate = np.mean(switch_counts) / (30000 * 0.8)  # switches per step
        print(f"    noise={noise:.3f}: switch_rate = {rate:.5f} ({np.mean(switch_counts):.0f} total)")
    sys.stdout.flush()


def N_scaling_bimodality():
    """Does bimodality increase with N? (predicts first-order in thermodynamic limit)"""
    print("\n" + "=" * 70)
    print("N-SCALING OF BIMODALITY")
    print("=" * 70)
    sys.stdout.flush()

    noise = 0.010  # In the transition region
    N_values = [2, 3, 4, 6, 8, 12, 16]
    steps = 15000
    n_seeds = 10

    for N in N_values:
        all_C = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.3)
            all_C.extend(r['C_collective'][ss:].tolist())

        C_arr = np.array(all_C)
        from scipy.stats import kurtosis
        ku = kurtosis(C_arr, fisher=True)  # Excess kurtosis
        # Negative excess kurtosis → platykurtic → bimodal tendency
        # Positive → leptokurtic → unimodal/peaked

        # Count how often system is in "gap" region
        gap_frac = np.mean((C_arr > 0.60) & (C_arr < 0.75))

        print(f"  N={N:2d}: mean={np.mean(C_arr):.3f}, std={np.std(C_arr):.3f}, "
              f"excess_kurtosis={ku:.3f}, gap_frac={gap_frac:.3f}")
    sys.stdout.flush()


if __name__ == '__main__':
    print("Thor Session #81 Part 2: Bimodality Analysis")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}\n")
    sys.stdout.flush()

    dist_results = analyze_distribution()
    bistability_switching()
    N_scaling_bimodality()

    # Save
    def make_serializable(obj):
        if isinstance(obj, (np.float64, np.float32)): return float(obj)
        if isinstance(obj, (np.int64, np.int32)): return int(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, dict): return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list): return [make_serializable(v) for v in obj]
        if isinstance(obj, tuple): return [make_serializable(v) for v in obj]
        return obj

    with open('thor_session_81_bimodality_results.json', 'w') as f:
        json.dump(make_serializable(dist_results), f, indent=2)

    print(f"\nCompleted: {datetime.now().isoformat()}")
    sys.stdout.flush()
