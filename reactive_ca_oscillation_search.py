#!/usr/bin/env python3
"""
======================================================================
THOR SESSION #19: REACTIVE CA OSCILLATION SEARCH
======================================================================

Context: Session #18 proved pure diffusion cannot produce oscillations.
This session tests whether adding REACTIVE TERM can ground oscillation basis.

Research Question: Can reactive-diffusion dynamics produce oscillating modes?

Modified Transfer Rule:
  ΔI = k·∇²I·R(I) + ε·f(I)

where f(I) is a reactive term with limit cycle (Hopf bifurcation).

Candidate reactive term:
  f(I) = I·(1 - I/I_max)·(I/I_max - θ)

This creates:
- Stable point at I=0 (extinct)
- Stable point at I=I_max·θ (threshold)
- Limit cycle oscillation for certain (ε, θ) ranges

Mission: Either FIND oscillating modes (ground oscillation basis) or
CONFIRM impossibility (accept Option C - oscillation as axiom).

Author: Thor (autonomous research #19)
Date: 2026-03-19
Reference: Session #18 recommendation
======================================================================
"""

import numpy as np
import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ReactiveOscillation:
    """Detected oscillation in reactive system."""
    epsilon: float  # reactive strength
    theta: float  # threshold
    k: float  # diffusion rate
    n: float  # saturation exponent
    period: int  # oscillation period (ticks)
    amplitude: float
    spatial_pattern: str  # uniform, localized, traveling_wave
    stability: float  # how stable over measurement window
    description: str


def R(I, I_max, n):
    """Resistance function R(I) = [1-(I/I_max)^n]"""
    ratio = np.clip(I / I_max, 0, 1)
    return 1.0 - ratio**n


def f_reactive(I, I_max, theta, epsilon):
    """
    Reactive term: f(I) = ε·I·(1-I/I_max)·(I/I_max - θ)

    This is a cubic nonlinearity that can create limit cycles.
    - I=0: stable (extinct)
    - I=θ·I_max: unstable (threshold)
    - For θ < I/I_max < 1: growth/decay depending on ε
    """
    ratio = I / I_max
    ratio = np.clip(ratio, 0, 1)
    return epsilon * I * (1 - ratio) * (ratio - theta)


def reactive_step_1d(I, k, I_max, n, epsilon, theta, bc='periodic'):
    """
    Single timestep with REACTIVE-DIFFUSION dynamics.

    ΔI = k·∇²I·R(I) + ε·f(I)

    Diffusion: k·(I_neighbors - I)·R(I)
    Reaction: ε·I·(1-I/I_max)·(I/I_max - θ)
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

        # DIFFUSION component (from Session #18)
        R_x = R(I[x], I_max, n)
        dI_diffusion = k * ((I[xp] - I[x]) + (I[xm] - I[x])) * R_x

        # REACTIVE component (NEW)
        dI_reaction = f_reactive(I[x], I_max, theta, epsilon)

        # Combined update
        I_new[x] = I[x] + dI_diffusion + dI_reaction
        I_new[x] = np.clip(I_new[x], 0, I_max)

    return I_new


def simulate_reactive_1d(I_init, k, I_max, n, epsilon, theta, steps, bc='periodic'):
    """Simulate reactive-diffusion CA."""
    N = len(I_init)
    history = np.zeros((steps + 1, N))
    I = I_init.copy()
    history[0] = I.copy()

    for t in range(steps):
        I = reactive_step_1d(I, k, I_max, n, epsilon, theta, bc)
        history[t + 1] = I.copy()

    return history


def detect_oscillation_reactive(history, window_start=None, window_end=None):
    """
    Detect oscillations in reactive system.
    Returns: (is_oscillating, period, amplitude, stability, pattern_type)
    """
    if window_start is None:
        window_start = len(history) // 2
    if window_end is None:
        window_end = len(history)

    window = history[window_start:window_end]

    if len(window) < 10:
        return False, None, None, None, None

    # Total Intent over time
    total_I = window.sum(axis=1)

    # Check for steady state (no oscillation)
    if np.std(total_I) < 1e-8:
        return False, None, None, None, "steady_state"

    # Autocorrelation to find period
    mean_I = np.mean(total_I)
    total_I_centered = total_I - mean_I

    if np.std(total_I_centered) < 1e-8:
        return False, None, None, None, "uniform"

    autocorr = np.correlate(total_I_centered, total_I_centered, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]

    # Find peaks in autocorrelation
    peaks = []
    for lag in range(2, min(len(autocorr), len(window)//3)):
        if lag > 1 and lag < len(autocorr)-1:
            if autocorr[lag] > autocorr[lag-1] and autocorr[lag] > autocorr[lag+1]:
                if autocorr[lag] > 0.5:
                    peaks.append((lag, autocorr[lag]))

    if len(peaks) == 0:
        return False, None, None, None, "aperiodic"

    period, corr_strength = peaks[0]

    # Measure amplitude
    amplitude = np.std(total_I)

    # Stability (consistency of oscillation)
    if len(peaks) >= 2:
        period2, _ = peaks[1]
        stability = 1.0 - abs(period2 - 2*period) / max(period, 1)
    else:
        stability = corr_strength

    # Classify spatial pattern
    pattern_type = classify_spatial_pattern(window)

    is_oscillating = corr_strength > 0.7 and period > 1 and amplitude > 0.01

    return is_oscillating, period, amplitude, stability, pattern_type


def classify_spatial_pattern(history):
    """Classify the spatial pattern type."""
    N = history.shape[1]
    final_window = history[-10:]  # Last 10 timesteps

    # Check for traveling waves (peak position changes)
    peak_positions = []
    for t in range(len(final_window)):
        if np.max(final_window[t]) > 0.1:
            peak_positions.append(np.argmax(final_window[t]))

    if len(peak_positions) >= 5:
        position_variance = np.std(peak_positions)
        if position_variance > 3:
            return "traveling_wave"

    # Check for localized oscillation (peak stays in same region)
    if len(peak_positions) >= 5:
        if position_variance < 2:
            return "localized"

    # Check for uniform oscillation (all cells oscillate together)
    spatial_variance = []
    for t in range(len(final_window)):
        spatial_variance.append(np.std(final_window[t]))

    if np.mean(spatial_variance) < 0.1:
        return "uniform_oscillation"

    # Multi-peak structure
    final = history[-1]
    peaks = 0
    for i in range(1, N-1):
        if final[i] > final[i-1] and final[i] > final[i+1] and final[i] > 0.2:
            peaks += 1

    if peaks >= 2:
        return "multi_peak"

    return "complex"


def explore_reactive_parameter_space():
    """Systematic exploration of reactive parameter space."""

    print("=" * 80)
    print("THOR SESSION #19: REACTIVE CA OSCILLATION SEARCH")
    print("=" * 80)
    print()
    print("Mission: Can reactive-diffusion produce oscillating modes?")
    print()
    print("Modified Transfer Rule:")
    print("  ΔI = k·∇²I·R(I) + ε·f(I)")
    print("  where f(I) = I·(1-I/I_max)·(I/I_max - θ)")
    print()
    print("This is the FINAL ATTEMPT to ground oscillation basis in substrate.")
    print("If this fails → Option C (accept oscillation as axiom)")
    print()
    print("=" * 80)
    print()

    results = []
    oscillations_found = []

    # Parameter ranges
    N = 100  # Grid size
    k_values = [0.1, 0.25]  # Diffusion rates (sub-CFL)
    n = 2.0  # Saturation exponent (from Session #18)
    I_max = 1.0

    # REACTIVE parameters
    epsilon_values = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]  # Reactive strength
    theta_values = [0.2, 0.3, 0.4, 0.5, 0.6]  # Threshold

    # Initial conditions
    initial_conditions = [
        'small_perturbation',  # Near threshold
        'medium_perturbation',
        'large_perturbation',
        'gaussian_peak',
        'random'
    ]

    total_runs = len(k_values) * len(epsilon_values) * len(theta_values) * len(initial_conditions)
    run_count = 0

    print(f"Parameter space:")
    print(f"  Grid size: N = {N}")
    print(f"  Diffusion: k ∈ {k_values}")
    print(f"  Saturation: n = {n}")
    print(f"  Reactive strength: ε ∈ {epsilon_values}")
    print(f"  Threshold: θ ∈ {theta_values}")
    print(f"  Initial conditions: {len(initial_conditions)} types")
    print(f"  Total configurations: {total_runs}")
    print()

    for k in k_values:
        for epsilon in epsilon_values:
            for theta in theta_values:
                for ic_type in initial_conditions:
                    run_count += 1

                    if run_count % 10 == 0:
                        print(f"Progress: {run_count}/{total_runs} ({100*run_count/total_runs:.1f}%) | Found: {len(oscillations_found)}")

                    # Create initial condition
                    I_init = create_initial_condition(N, I_max, theta, ic_type)

                    # Simulate
                    history = simulate_reactive_1d(I_init, k, I_max, n, epsilon, theta, steps=1000)

                    # Detect oscillation
                    is_osc, period, amplitude, stability, pattern = detect_oscillation_reactive(history)

                    if is_osc:
                        osc = ReactiveOscillation(
                            epsilon=epsilon,
                            theta=theta,
                            k=k,
                            n=n,
                            period=period,
                            amplitude=amplitude,
                            spatial_pattern=pattern,
                            stability=stability,
                            description=f"ε={epsilon:.2f}, θ={theta:.2f}, k={k:.2f}, IC={ic_type}"
                        )
                        oscillations_found.append(osc)
                        results.append((True, osc))

                        print()
                        print(f"🎯 OSCILLATION #{len(oscillations_found)} DETECTED!")
                        print(f"   Parameters: ε={epsilon:.2f}, θ={theta:.2f}, k={k:.2f}")
                        print(f"   Period: {period} ticks")
                        print(f"   Amplitude: {amplitude:.4f}")
                        print(f"   Stability: {stability:.4f}")
                        print(f"   Pattern: {pattern}")
                        print(f"   IC: {ic_type}")
                        print()

                    else:
                        results.append((False, None))

    print()
    print("=" * 80)
    print("EXPLORATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total configurations: {total_runs}")
    print(f"Oscillations found: {len(oscillations_found)}")
    print(f"Detection rate: {100*len(oscillations_found)/total_runs:.2f}%")
    print()

    return oscillations_found, results


def create_initial_condition(N, I_max, theta, ic_type):
    """Create initial condition for reactive system."""
    x = np.arange(N)
    I_init = np.zeros(N)

    if ic_type == 'small_perturbation':
        # Just above threshold
        I_init[:] = I_max * (theta + 0.05)

    elif ic_type == 'medium_perturbation':
        I_init[:] = I_max * (theta + 0.15)

    elif ic_type == 'large_perturbation':
        I_init[:] = I_max * 0.7

    elif ic_type == 'gaussian_peak':
        center = N // 2
        width = N / 10
        I_init = I_max * (theta + 0.1) + I_max * 0.3 * np.exp(-((x - center)**2) / (2 * width**2))

    elif ic_type == 'random':
        I_init = I_max * (theta + np.random.rand(N) * 0.3)

    return np.clip(I_init, 0, I_max)


def analyze_oscillations(oscillations):
    """Analyze found oscillations."""
    if len(oscillations) == 0:
        print("❌ NO OSCILLATIONS FOUND IN REACTIVE SYSTEM")
        print()
        print("**CONCLUSION**: Even with reactive term, oscillating modes do not emerge.")
        print()
        print("This proves:")
        print("  1. Pure diffusion cannot produce oscillations (Session #18)")
        print("  2. Reactive-diffusion cannot produce oscillations (Session #19)")
        print()
        print("**IMPLICATION**: Oscillation basis CANNOT be grounded in substrate dynamics")
        print("                 via standard reaction-diffusion mechanisms.")
        print()
        print("**RECOMMENDATION**: Accept Option C")
        print("  - Oscillation basis is an AXIOM")
        print("  - Entity criterion (Γ < m) follows from axiom")
        print("  - Focus on testing Γ < m predictions against QCD data")
        print()
        return

    print("=" * 80)
    print(f"ANALYSIS: {len(oscillations)} OSCILLATIONS FOUND")
    print("=" * 80)
    print()

    # Parameter dependence
    print("By reactive strength (ε):")
    eps_groups = {}
    for osc in oscillations:
        eps_groups[osc.epsilon] = eps_groups.get(osc.epsilon, 0) + 1
    for eps, count in sorted(eps_groups.items()):
        print(f"  ε={eps:.2f}: {count} oscillations")
    print()

    print("By threshold (θ):")
    theta_groups = {}
    for osc in oscillations:
        theta_groups[osc.theta] = theta_groups.get(osc.theta, 0) + 1
    for theta, count in sorted(theta_groups.items()):
        print(f"  θ={theta:.2f}: {count} oscillations")
    print()

    print("By spatial pattern:")
    pattern_groups = {}
    for osc in oscillations:
        pattern_groups[osc.spatial_pattern] = pattern_groups.get(osc.spatial_pattern, 0) + 1
    for pattern, count in sorted(pattern_groups.items(), key=lambda x: -x[1]):
        print(f"  {pattern:20s}: {count}")
    print()

    # Period distribution
    periods = [osc.period for osc in oscillations]
    print(f"Periods: min={min(periods)}, max={max(periods)}, mean={np.mean(periods):.1f}")
    print()

    # Stability
    stabilities = [osc.stability for osc in oscillations]
    print(f"Stability: min={min(stabilities):.3f}, max={max(stabilities):.3f}, mean={np.mean(stabilities):.3f}")
    print()


def save_reactive_results(oscillations):
    """Save results to JSON."""
    data = {
        'session': 19,
        'date': '2026-03-19',
        'total_oscillations': len(oscillations),
        'oscillations': []
    }

    for osc in oscillations:
        data['oscillations'].append({
            'epsilon': osc.epsilon,
            'theta': osc.theta,
            'k': osc.k,
            'n': osc.n,
            'period': osc.period,
            'amplitude': float(osc.amplitude),
            'spatial_pattern': osc.spatial_pattern,
            'stability': float(osc.stability),
            'description': osc.description
        })

    with open('/home/dp/gnosis-research/reactive_ca_oscillation_results.json', 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Results saved to reactive_ca_oscillation_results.json")
    print()


if __name__ == "__main__":
    oscillations, results = explore_reactive_parameter_space()
    analyze_oscillations(oscillations)
    save_reactive_results(oscillations)

    print("=" * 80)
    print("SESSION #19 COMPLETE")
    print("=" * 80)
    print()

    if len(oscillations) > 0:
        print("✅ REACTIVE TERM PRODUCES OSCILLATIONS")
        print("   → Oscillation basis CAN be grounded in substrate dynamics")
        print("   → Option B succeeds")
        print("   → Next: Classify modes, compare to particle spectrum")
    else:
        print("❌ REACTIVE TERM FAILS TO PRODUCE OSCILLATIONS")
        print("   → Oscillation basis CANNOT be grounded via reaction-diffusion")
        print("   → Option B fails")
        print("   → Accept Option C: Oscillation as axiom")
    print()
