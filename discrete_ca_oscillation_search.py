#!/usr/bin/env python3
"""
======================================================================
THOR SESSION #18: DISCRETE CA OSCILLATION MODE SEARCH
======================================================================

Context: Synchronism stress test Session #13 proved the transfer rule
cannot produce oscillating entities in the continuum limit (CFL analysis).
But what about the DISCRETE dynamics directly?

Research Question: Does the discrete cellular automaton with the Intent
transfer rule produce oscillating modes?

Transfer Rule: ΔI(x→y) = k·(I_x - I_y)·R(I_y)
                where R(I) = [1-(I/I_max)^n]

Session #13 finding: Continuum limit + CFL stability → no localized
oscillating solutions. But discrete CA can violate CFL and may have
modes not captured by continuum analysis.

Mission: Systematic exploration to either:
1. Find oscillating modes → validate oscillation basis computationally
2. Confirm no oscillating modes → strengthen "transfer rule incomplete"
3. Identify conditions for oscillation → guide Option B (fix the rule)

Author: Thor (autonomous research #18)
Date: 2026-03-18
Reference: synchronism/Research/proposals/stress_test_arc_closure.md (Option B)
======================================================================
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional


@dataclass
class OscillationMode:
    """Detected oscillating pattern."""
    period: int  # ticks
    amplitude: float
    spatial_extent: int  # number of cells involved
    stability: float  # how stable over measurement window
    initial_condition: str
    parameters: dict
    description: str


@dataclass
class ExplorationResult:
    """Results from one parameter configuration."""
    N: int  # grid size
    k: float  # transfer rate
    n: float  # saturation exponent
    I_max: float
    initial_condition: str
    oscillation_detected: bool
    oscillation_mode: Optional[OscillationMode]
    final_state: str  # uniform, localized, chaotic, etc.
    notes: str


def R(I, I_max, n):
    """Resistance function: R(I) = [1-(I/I_max)^n]"""
    ratio = np.clip(I / I_max, 0, 1)
    return 1.0 - ratio**n


def transfer_step_1d(I, k, I_max, n, bc='periodic'):
    """
    Single discrete time step of Intent transfer in 1D.

    Transfer rule: ΔI(x→y) = k·(I_x - I_y)·R(I_y)

    At each cell x:
      I_new(x) = I(x) + ΔI_from_neighbors
    """
    N = len(I)
    I_new = I.copy()

    for x in range(N):
        if bc == 'periodic':
            xp = (x + 1) % N
            xm = (x - 1) % N
        elif bc == 'fixed':
            xp = min(x + 1, N - 1)
            xm = max(x - 1, 0)
        else:
            raise ValueError(f"Unknown BC: {bc}")

        # Transfer FROM neighbors TO x
        # Right neighbor contributes: k·(I[xp] - I[x])·R(I[x])
        # Left neighbor contributes: k·(I[xm] - I[x])·R(I[x])

        R_x = R(I[x], I_max, n)
        dI_right = k * (I[xp] - I[x]) * R_x
        dI_left = k * (I[xm] - I[x]) * R_x

        I_new[x] = I[x] + dI_right + dI_left
        I_new[x] = np.clip(I_new[x], 0, I_max)

    return I_new


def simulate_1d(I_init, k, I_max, n, steps, bc='periodic'):
    """Simulate 1D discrete Intent dynamics."""
    N = len(I_init)
    history = np.zeros((steps + 1, N))
    I = I_init.copy()
    history[0] = I.copy()

    for t in range(steps):
        I = transfer_step_1d(I, k, I_max, n, bc)
        history[t + 1] = I.copy()

    return history


def detect_oscillation(history, window_start=None, window_end=None):
    """
    Detect if history contains oscillating behavior.

    Returns: (is_oscillating, period, amplitude, stability)
    """
    if window_start is None:
        window_start = len(history) // 2  # Skip transient
    if window_end is None:
        window_end = len(history)

    window = history[window_start:window_end]

    if len(window) < 10:
        return False, None, None, None

    # Measure temporal variance of total Intent
    total_I = window.sum(axis=1)

    if np.std(total_I) < 1e-10:
        # Converged to steady state
        return False, None, None, None

    # Look for periodicity in total Intent
    # Use autocorrelation
    mean_I = np.mean(total_I)
    total_I_centered = total_I - mean_I

    if np.std(total_I_centered) < 1e-10:
        return False, None, None, None

    autocorr = np.correlate(total_I_centered, total_I_centered, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]  # Normalize

    # Find first peak after lag=1
    peaks = []
    for lag in range(2, min(len(autocorr), len(window)//3)):
        if lag > 1 and lag < len(autocorr)-1:
            if autocorr[lag] > autocorr[lag-1] and autocorr[lag] > autocorr[lag+1]:
                if autocorr[lag] > 0.5:  # Significant peak
                    peaks.append((lag, autocorr[lag]))

    if len(peaks) == 0:
        return False, None, None, None

    # First significant peak is the period
    period, corr_strength = peaks[0]

    # Measure amplitude
    amplitude = np.std(total_I)

    # Measure stability (how consistent is the oscillation)
    # Check if multiple peaks exist at integer multiples
    if len(peaks) >= 2:
        period2, _ = peaks[1]
        stability = 1.0 - abs(period2 - 2*period) / period
    else:
        stability = corr_strength

    is_oscillating = corr_strength > 0.7 and period > 1

    return is_oscillating, period, amplitude, stability


def measure_spatial_extent(history, threshold=0.1):
    """How many cells have significant Intent variation?"""
    final_state = history[-1]
    I_max_actual = np.max(final_state)

    if I_max_actual < 1e-10:
        return 0

    significant = np.sum(final_state > threshold * I_max_actual)
    return significant


def classify_final_state(history):
    """Classify the final state of the system."""
    final = history[-1]
    N = len(final)

    # Uniform?
    if np.std(final) < 1e-6:
        return "uniform"

    # All zero?
    if np.max(final) < 1e-10:
        return "extinct"

    # Localized peak?
    max_idx = np.argmax(final)
    peak_region = final[max(0, max_idx-2):min(N, max_idx+3)]
    if np.sum(peak_region) / np.sum(final) > 0.8:
        return "localized_peak"

    # Checkerboard? (alternating high/low)
    checkerboard_score = 0
    for i in range(N-1):
        if (final[i] > 0.5 and final[i+1] < 0.5) or (final[i] < 0.5 and final[i+1] > 0.5):
            checkerboard_score += 1

    if checkerboard_score > 0.8 * (N-1):
        return "checkerboard"

    # Multiple peaks?
    peaks = 0
    for i in range(1, N-1):
        if final[i] > final[i-1] and final[i] > final[i+1] and final[i] > 0.3:
            peaks += 1

    if peaks >= 2:
        return "multi_peak"

    # Default
    if np.std(final) > 0.1:
        return "structured"
    else:
        return "dispersed"


def explore_configuration(N, k, n, I_max, initial_condition, steps=500):
    """
    Explore one configuration for oscillating modes.

    initial_condition types:
    - 'single_peak': Gaussian peak at center
    - 'double_peak': Two Gaussian peaks
    - 'random': Random initialization
    - 'step': Step function
    - 'sinusoid': Sin wave
    """
    # Create initial condition
    x = np.arange(N)
    I_init = np.zeros(N)

    if initial_condition == 'single_peak':
        center = N // 2
        width = N / 10
        I_init = I_max * 0.8 * np.exp(-((x - center)**2) / (2 * width**2))

    elif initial_condition == 'double_peak':
        c1 = N // 4
        c2 = 3 * N // 4
        width = N / 15
        I_init = I_max * 0.6 * (
            np.exp(-((x - c1)**2) / (2 * width**2)) +
            np.exp(-((x - c2)**2) / (2 * width**2))
        )

    elif initial_condition == 'random':
        I_init = I_max * np.random.rand(N) * 0.5

    elif initial_condition == 'step':
        I_init[N//3:2*N//3] = I_max * 0.7

    elif initial_condition == 'sinusoid':
        I_init = I_max * 0.5 * (1 + 0.8 * np.sin(2 * np.pi * x / N))

    elif initial_condition == 'two_sinusoids':
        I_init = I_max * 0.5 * (
            1 + 0.4 * np.sin(2 * np.pi * x / N) +
            0.4 * np.sin(4 * np.pi * x / N)
        )

    # Simulate
    history = simulate_1d(I_init, k, I_max, n, steps)

    # Detect oscillation
    is_osc, period, amplitude, stability = detect_oscillation(history)

    # Classify final state
    final_state_type = classify_final_state(history)

    # Build result
    result = ExplorationResult(
        N=N,
        k=k,
        n=n,
        I_max=I_max,
        initial_condition=initial_condition,
        oscillation_detected=is_osc,
        oscillation_mode=None,
        final_state=final_state_type,
        notes=""
    )

    if is_osc:
        spatial_extent = measure_spatial_extent(history)
        result.oscillation_mode = OscillationMode(
            period=period,
            amplitude=amplitude,
            spatial_extent=spatial_extent,
            stability=stability,
            initial_condition=initial_condition,
            parameters={'N': N, 'k': k, 'n': n, 'I_max': I_max},
            description=f"Period-{period} oscillation, extent={spatial_extent} cells"
        )
        result.notes = f"OSCILLATION FOUND: {result.oscillation_mode.description}"

    return result, history


def systematic_exploration():
    """Systematic parameter sweep looking for oscillating modes."""

    print("=" * 80)
    print("THOR SESSION #18: DISCRETE CA OSCILLATION MODE SEARCH")
    print("=" * 80)
    print()
    print("Mission: Search for oscillating modes in discrete Intent CA")
    print("Transfer Rule: ΔI(x→y) = k·(I_x - I_y)·R(I_y), R(I) = [1-(I/I_max)^n]")
    print()
    print("Context: Session #13 proved continuum limit has no oscillating solutions")
    print("Question: Does the discrete CA have modes not in continuum limit?")
    print()
    print("=" * 80)
    print()

    results = []

    # Parameter ranges
    grid_sizes = [50, 100, 200]
    k_values = [0.05, 0.1, 0.25, 0.5, 0.75, 1.0]  # Include super-CFL
    n_values = [1.0, 2.0, 4.0]
    I_max = 1.0
    initial_conditions = ['single_peak', 'double_peak', 'random', 'step', 'sinusoid', 'two_sinusoids']

    total_runs = len(grid_sizes) * len(k_values) * len(n_values) * len(initial_conditions)
    run_count = 0

    print(f"Total configurations to explore: {total_runs}")
    print()

    oscillations_found = 0

    for N in grid_sizes:
        for k in k_values:
            for n in n_values:
                for ic in initial_conditions:
                    run_count += 1

                    if run_count % 10 == 0:
                        print(f"Progress: {run_count}/{total_runs} ({100*run_count/total_runs:.1f}%)")

                    result, history = explore_configuration(N, k, n, I_max, ic, steps=500)
                    results.append(result)

                    if result.oscillation_detected:
                        oscillations_found += 1
                        print()
                        print(f"🎯 OSCILLATION #{oscillations_found} DETECTED!")
                        print(f"   N={N}, k={k:.3f}, n={n:.1f}, IC='{ic}'")
                        print(f"   Period: {result.oscillation_mode.period} ticks")
                        print(f"   Amplitude: {result.oscillation_mode.amplitude:.4f}")
                        print(f"   Stability: {result.oscillation_mode.stability:.4f}")
                        print(f"   Spatial extent: {result.oscillation_mode.spatial_extent} cells")
                        print()

                        # Plot disabled due to matplotlib numpy compatibility
                        # save_oscillation_plot(history, result, oscillations_found)

    print()
    print("=" * 80)
    print("EXPLORATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total configurations: {total_runs}")
    print(f"Oscillations found: {oscillations_found}")
    print(f"Detection rate: {100*oscillations_found/total_runs:.2f}%")
    print()

    # Analyze results
    analyze_results(results)

    # Save results
    save_results(results)

    return results


def analyze_results(results):
    """Analyze the exploration results."""
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    # Final state distribution
    print("Final State Distribution:")
    final_states = {}
    for r in results:
        fs = r.final_state
        final_states[fs] = final_states.get(fs, 0) + 1

    for state, count in sorted(final_states.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(results)
        print(f"  {state:20s}: {count:4d} ({pct:5.1f}%)")
    print()

    # Oscillation analysis
    oscillating = [r for r in results if r.oscillation_detected]

    if len(oscillating) > 0:
        print(f"Oscillating Modes Found: {len(oscillating)}")
        print()

        # By parameter
        print("Oscillations by k:")
        k_osc = {}
        for r in oscillating:
            k_osc[r.k] = k_osc.get(r.k, 0) + 1
        for k, count in sorted(k_osc.items()):
            print(f"  k={k:.3f}: {count} oscillations")
        print()

        print("Oscillations by n:")
        n_osc = {}
        for r in oscillating:
            n_osc[r.n] = n_osc.get(r.n, 0) + 1
        for n, count in sorted(n_osc.items()):
            print(f"  n={n:.1f}: {count} oscillations")
        print()

        print("Oscillations by initial condition:")
        ic_osc = {}
        for r in oscillating:
            ic_osc[r.initial_condition] = ic_osc.get(r.initial_condition, 0) + 1
        for ic, count in sorted(ic_osc.items(), key=lambda x: -x[1]):
            print(f"  {ic:20s}: {count}")
        print()

        # Period distribution
        periods = [r.oscillation_mode.period for r in oscillating]
        print(f"Periods: min={min(periods)}, max={max(periods)}, mean={np.mean(periods):.1f}")
        print()

    else:
        print("❌ NO OSCILLATING MODES FOUND")
        print()
        print("This strengthens Session #13's finding:")
        print("  The transfer rule ΔI = k·(I_x - I_y)·R(I_y) cannot produce")
        print("  stable oscillating entities, even in discrete dynamics.")
        print()
        print("Implication: The oscillation basis is an INDEPENDENT POSTULATE,")
        print("not derivable from the transfer rule.")
        print()


def save_oscillation_plot(history, result, osc_num):
    """Save visualization of oscillating mode (disabled - matplotlib issue)."""
    pass
    # Matplotlib disabled due to numpy compatibility issues
    # Would save spacetime diagram and total Intent time series


def save_results(results):
    """Save results to JSON."""
    # Convert to serializable format
    data = []
    for r in results:
        d = {
            'N': r.N,
            'k': r.k,
            'n': r.n,
            'I_max': r.I_max,
            'initial_condition': r.initial_condition,
            'oscillation_detected': r.oscillation_detected,
            'final_state': r.final_state,
            'notes': r.notes
        }

        if r.oscillation_mode:
            d['oscillation_mode'] = {
                'period': r.oscillation_mode.period,
                'amplitude': float(r.oscillation_mode.amplitude),
                'spatial_extent': r.oscillation_mode.spatial_extent,
                'stability': float(r.oscillation_mode.stability),
                'description': r.oscillation_mode.description
            }

        data.append(d)

    with open('/home/dp/gnosis-research/discrete_ca_oscillation_results.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("Results saved to discrete_ca_oscillation_results.json")
    print()


if __name__ == "__main__":
    results = systematic_exploration()

    print("=" * 80)
    print("SESSION COMPLETE")
    print("=" * 80)
    print()
    print("Explored discrete Intent CA for oscillating modes.")
    print("See discrete_ca_oscillation_results.json for full data.")
    print()
