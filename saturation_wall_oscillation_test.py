#!/usr/bin/env python3
"""
Saturation Wall Oscillation Test - Session #20

Tests whether R(I) saturation can produce oscillations through GEOMETRIC CONFINEMENT
rather than amplitude instability (which Sessions #18-19 proved impossible).

Physical hypothesis:
- R(I) → 0 as I → I_max creates reflective boundaries
- Energy cannot propagate through saturation walls
- Localized energy pulse creates self-confining cavity
- Standing waves form between walls: f ~ v/2L

This is fundamentally different from Sessions #18-19 which looked for
temporal oscillation at single points via Hopf bifurcation.

Author: Thor autonomous session
Date: 2026-03-19
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional


@dataclass
class Configuration:
    """Parameter configuration for single test run."""
    A_over_Imax: float  # Pulse amplitude relative to saturation
    sigma: float        # Initial pulse width (cells)
    k: float           # Coupling strength
    n: int             # Saturation sharpness exponent
    config_id: int     # Unique configuration identifier


@dataclass
class WallDetection:
    """Results from saturation wall detection."""
    walls_detected: bool
    wall_positions: List[int]  # Cell indices where walls form
    wall_separation: Optional[float]  # Distance between walls
    wall_stability: float  # Fraction of time walls remain stable


@dataclass
class OscillationResult:
    """Results from oscillation detection."""
    oscillating: bool
    period: Optional[float]  # Oscillation period (timesteps)
    frequency: Optional[float]  # Oscillation frequency (1/timesteps)
    autocorr_peak: float  # Peak autocorrelation value
    persistence_time: int  # How long pattern persists


@dataclass
class TestResult:
    """Complete results for single configuration."""
    config: Configuration
    walls: WallDetection
    oscillation: OscillationResult
    final_state: str  # "standing_wave", "dispersed", "collapsed", "thermalized"


class SaturationWallCA:
    """1D cellular automaton with saturation-based transfer rule."""

    def __init__(self, N: int = 200, I_max: float = 1.0, dt: float = 0.01):
        """
        Initialize CA lattice.

        Args:
            N: Number of cells
            I_max: Maximum intent density (saturation threshold)
            dt: Timestep size
        """
        self.N = N
        self.I_max = I_max
        self.dt = dt
        self.I = np.zeros(N)  # Intent density field

    def R(self, I: np.ndarray, n: int) -> np.ndarray:
        """
        Saturation resistance function.

        R(I) = [1 - (I/I_max)^n]

        As I → I_max, R → 0 (saturation wall forms).
        """
        ratio = np.clip(I / self.I_max, 0, 1)
        return 1 - ratio**n

    def initialize_gaussian_pulse(self, A: float, sigma: float, x0: Optional[int] = None):
        """
        Initialize with localized Gaussian pulse.

        Args:
            A: Pulse amplitude
            sigma: Pulse width (cells)
            x0: Pulse center (default: middle of lattice)
        """
        if x0 is None:
            x0 = self.N // 2

        x = np.arange(self.N)
        self.I = A * np.exp(-(x - x0)**2 / (2 * sigma**2))
        self.I = np.clip(self.I, 0, None)  # No negative intent

    def step(self, k: float, n: int):
        """
        Single timestep of discrete CA evolution.

        Transfer rule: ΔI_x = k · Σ_neighbors (I_y - I_x) · R(I_y)

        Args:
            k: Coupling strength
            n: Saturation exponent
        """
        I_new = self.I.copy()

        for x in range(self.N):
            # Periodic boundary conditions
            x_left = (x - 1) % self.N
            x_right = (x + 1) % self.N

            # Resistance at neighbor sites
            R_left = self.R(np.array([self.I[x_left]]), n)[0]
            R_right = self.R(np.array([self.I[x_right]]), n)[0]

            # Transfer from neighbors
            dI_left = k * (self.I[x_left] - self.I[x]) * R_left
            dI_right = k * (self.I[x_right] - self.I[x]) * R_right

            I_new[x] = self.I[x] + self.dt * (dI_left + dI_right)
            I_new[x] = np.clip(I_new[x], 0, None)  # No negative intent

        self.I = I_new

    def detect_walls(self, threshold: float = 0.01, min_stability: int = 100) -> Tuple[List[int], np.ndarray]:
        """
        Detect where saturation walls form (R(I) < threshold).

        Returns:
            wall_cells: List of cell indices where walls are detected
            R_values: Resistance values across lattice
        """
        R_vals = self.R(self.I, n=2)  # Use n=2 for detection
        wall_cells = np.where(R_vals < threshold)[0].tolist()
        return wall_cells, R_vals


def detect_oscillation(time_series: np.ndarray, min_period: int = 5,
                       max_period: int = 500) -> Tuple[bool, Optional[float], float]:
    """
    Detect periodic oscillation in time series via autocorrelation.

    Args:
        time_series: 1D array of values over time
        min_period: Minimum oscillation period to consider
        max_period: Maximum oscillation period to search

    Returns:
        is_oscillating: Whether oscillation detected
        period: Oscillation period if detected
        peak_corr: Peak autocorrelation value
    """
    if len(time_series) < 2 * max_period:
        return False, None, 0.0

    # Use second half to avoid transients
    start = len(time_series) // 2
    signal = time_series[start:]

    # Center and normalize
    mean = np.mean(signal)
    signal_centered = signal - mean

    if np.std(signal_centered) < 1e-10:  # No variation
        return False, None, 0.0

    # Autocorrelation
    autocorr = np.correlate(signal_centered, signal_centered, mode='full')
    autocorr = autocorr[len(autocorr)//2:]  # Keep positive lags
    autocorr = autocorr / autocorr[0]  # Normalize

    # Find peaks beyond minimum period
    peaks = []
    for lag in range(min_period, min(len(autocorr), max_period)):
        if autocorr[lag] > 0.5:  # Significant correlation
            # Check if it's a local maximum
            if lag > 0 and lag < len(autocorr) - 1:
                if autocorr[lag] > autocorr[lag-1] and autocorr[lag] > autocorr[lag+1]:
                    peaks.append((lag, autocorr[lag]))

    if not peaks:
        return False, None, np.max(autocorr[1:]) if len(autocorr) > 1 else 0.0

    # Return strongest peak
    best_peak = max(peaks, key=lambda p: p[1])
    period, corr = best_peak

    is_oscillating = corr > 0.7  # Strong correlation threshold
    return is_oscillating, float(period) if is_oscillating else None, corr


def analyze_wall_stability(wall_history: List[List[int]],
                           min_stability: int = 100) -> Tuple[bool, Optional[float]]:
    """
    Analyze whether walls remain stable over time.

    Args:
        wall_history: List of wall positions at each timestep
        min_stability: Minimum timesteps for stable walls

    Returns:
        walls_stable: Whether stable walls detected
        separation: Average wall separation if stable
    """
    if len(wall_history) < min_stability:
        return False, None

    # Check last min_stability steps
    recent_walls = wall_history[-min_stability:]

    # Count how many timesteps have exactly 2 walls
    two_wall_count = sum(1 for walls in recent_walls if len(walls) >= 2)

    if two_wall_count < 0.8 * min_stability:  # Require 80% stability
        return False, None

    # Compute average separation for timesteps with 2+ walls
    separations = []
    for walls in recent_walls:
        if len(walls) >= 2:
            # Use outermost walls
            walls_sorted = sorted(walls)
            sep = walls_sorted[-1] - walls_sorted[0]
            separations.append(sep)

    if not separations:
        return False, None

    avg_separation = np.mean(separations)
    return True, avg_separation


def run_single_test(config: Configuration, n_steps: int = 10000,
                    record_interval: int = 10) -> TestResult:
    """
    Run single configuration test.

    Args:
        config: Parameter configuration
        n_steps: Number of timesteps
        record_interval: Record state every N steps

    Returns:
        Complete test results
    """
    # Initialize CA
    ca = SaturationWallCA(N=200, I_max=1.0, dt=0.01)
    A = config.A_over_Imax * ca.I_max
    ca.initialize_gaussian_pulse(A, config.sigma)

    # Storage for analysis
    wall_history = []
    cavity_energy_history = []

    # Evolution
    for step in range(n_steps):
        ca.step(config.k, config.n)

        if step % record_interval == 0:
            # Detect walls
            wall_cells, R_vals = ca.detect_walls(threshold=0.01)
            wall_history.append(wall_cells)

            # Measure energy in cavity (if walls exist)
            if len(wall_cells) >= 2:
                walls_sorted = sorted(wall_cells)
                left_wall = walls_sorted[0]
                right_wall = walls_sorted[-1]
                cavity_energy = np.sum(ca.I[left_wall:right_wall+1])
            else:
                cavity_energy = np.sum(ca.I)  # Total energy

            cavity_energy_history.append(cavity_energy)

    # Analyze walls
    walls_stable, wall_separation = analyze_wall_stability(wall_history)
    wall_positions = wall_history[-1] if wall_history else []

    wall_detection = WallDetection(
        walls_detected=walls_stable,
        wall_positions=wall_positions,
        wall_separation=wall_separation,
        wall_stability=1.0 if walls_stable else 0.0
    )

    # Analyze oscillation
    cavity_energy_array = np.array(cavity_energy_history)
    is_osc, period, peak_corr = detect_oscillation(cavity_energy_array)

    frequency = 1.0 / period if period else None

    # Estimate persistence (when does energy drop below threshold?)
    energy_threshold = 0.1 * cavity_energy_array[0]  # 10% of initial
    persistence_steps = n_steps
    for i, E in enumerate(cavity_energy_array):
        if E < energy_threshold:
            persistence_steps = i * record_interval
            break

    oscillation_result = OscillationResult(
        oscillating=is_osc,
        period=period,
        frequency=frequency,
        autocorr_peak=peak_corr,
        persistence_time=persistence_steps
    )

    # Classify final state
    if is_osc and walls_stable:
        final_state = "standing_wave"
    elif walls_stable and not is_osc:
        final_state = "thermalized"
    elif cavity_energy_array[-1] < 0.01 * cavity_energy_array[0]:
        final_state = "dispersed"
    else:
        final_state = "collapsed"

    return TestResult(
        config=config,
        walls=wall_detection,
        oscillation=oscillation_result,
        final_state=final_state
    )


def generate_configurations() -> List[Configuration]:
    """
    Generate all parameter configurations for sweep.

    REDUCED SCOPE: 4 × 3 × 3 × 2 = 72 configurations (faster for Session #20)
    """
    A_over_Imax_values = [0.5, 0.9, 1.2, 2.0]  # Reduced from 8
    sigma_values = [5, 10, 20]  # Reduced from 4
    k_values = [0.05, 0.1, 0.2]  # Reduced from 4
    n_values = [4, 8]  # Reduced from 3

    configs = []
    config_id = 0

    for A in A_over_Imax_values:
        for sigma in sigma_values:
            for k in k_values:
                for n in n_values:
                    configs.append(Configuration(
                        A_over_Imax=A,
                        sigma=sigma,
                        k=k,
                        n=n,
                        config_id=config_id
                    ))
                    config_id += 1

    return configs


def main():
    """Run complete saturation wall oscillation test."""
    print("=" * 80)
    print("SATURATION WALL OSCILLATION TEST - Session #20")
    print("=" * 80)
    print()
    print("Hypothesis: R(I) saturation creates reflective boundaries that confine")
    print("energy into oscillating cavities (geometric confinement, not amplitude")
    print("instability).")
    print()
    print("This tests a fundamentally different mechanism than Sessions #18-19.")
    print()

    # Generate configurations
    configs = generate_configurations()
    print(f"Total configurations: {len(configs)}")
    print()

    # Run tests
    results = []
    standing_wave_count = 0
    wall_count = 0
    oscillation_count = 0

    for i, config in enumerate(configs):
        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{len(configs)} ({100*(i+1)/len(configs):.1f}%)")

        result = run_single_test(config, n_steps=5000, record_interval=10)  # Reduced from 10000
        results.append(result)

        if result.walls.walls_detected:
            wall_count += 1
        if result.oscillation.oscillating:
            oscillation_count += 1
        if result.final_state == "standing_wave":
            standing_wave_count += 1

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"Configurations tested: {len(results)}")
    print(f"Stable walls detected: {wall_count} ({100*wall_count/len(results):.1f}%)")
    print(f"Oscillations detected: {oscillation_count} ({100*oscillation_count/len(results):.1f}%)")
    print(f"Standing waves (walls + oscillation): {standing_wave_count} ({100*standing_wave_count/len(results):.1f}%)")
    print()

    # Save results
    results_file = "saturation_wall_results.json"
    results_data = {
        "summary": {
            "total_configs": len(results),
            "walls_detected": wall_count,
            "oscillations_detected": oscillation_count,
            "standing_waves": standing_wave_count
        },
        "results": [
            {
                "config": asdict(r.config),
                "walls": asdict(r.walls),
                "oscillation": asdict(r.oscillation),
                "final_state": r.final_state
            }
            for r in results
        ]
    }

    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"Detailed results saved to: {results_file}")
    print()

    # Report best cases
    if standing_wave_count > 0:
        print("=" * 80)
        print("STANDING WAVE CONFIGURATIONS (Top 10)")
        print("=" * 80)
        print()

        standing_waves = [r for r in results if r.final_state == "standing_wave"]
        standing_waves.sort(key=lambda r: r.oscillation.autocorr_peak, reverse=True)

        for r in standing_waves[:10]:
            c = r.config
            print(f"Config {c.config_id}: A/I_max={c.A_over_Imax:.1f}, σ={c.sigma:.0f}, k={c.k:.2f}, n={c.n}")
            print(f"  Wall separation: {r.walls.wall_separation:.1f} cells")
            print(f"  Oscillation period: {r.oscillation.period:.1f} steps")
            print(f"  Autocorr peak: {r.oscillation.autocorr_peak:.3f}")
            print(f"  Persistence: {r.oscillation.persistence_time} steps")
            print()

    # Final verdict
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print()

    if standing_wave_count > 0:
        print(f"✅ SATURATION WALL MECHANISM CONFIRMED")
        print(f"   {standing_wave_count} configurations produced standing waves")
        print(f"   Oscillations emerge from geometric confinement")
        print(f"   Option B is viable with corrected mechanism")
    elif wall_count > 0:
        print(f"⚠️  WALLS FORM BUT NO OSCILLATION")
        print(f"   {wall_count} configurations produced stable walls")
        print(f"   Energy thermalizes inside cavity")
        print(f"   Mechanism partially works but incomplete")
    else:
        print(f"❌ SATURATION WALL MECHANISM FAILS")
        print(f"   No stable walls detected in any configuration")
        print(f"   R(I) saturation too soft for confinement")
        print(f"   Oscillation basis remains axiomatic")
    print()


if __name__ == "__main__":
    main()
