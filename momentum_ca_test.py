#!/usr/bin/env python3
"""
Momentum-Augmented CA Test - Option B1

Tests whether adding a momentum/velocity term enables oscillations through
energy reflection at saturation walls.

Physics: Second-order CA with inertial memory
- v_t = α·v_{t-1} + k·∇²I·R(I)  (momentum update)
- I_{t+1} = I_t + v_t              (position update)

This differs from Sessions #18-20 (first-order CA) by adding velocity field v
that carries directional memory, enabling energy reflection at boundaries.

Author: Thor autonomous session
Date: 2026-03-20
Directive: Research/proposals/B1_momentum_augmented_ca.md
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
    alpha: float       # Momentum retention factor (NEW)
    config_id: int     # Unique configuration identifier


@dataclass
class ReflectionResult:
    """Results from reflection detection at walls."""
    reflection_detected: bool
    max_velocity_reversal: float  # Maximum |Δv| at wall boundary
    reversal_count: int  # Number of times velocity reversed sign at walls
    wall_bounce_strength: float  # Average velocity change at walls


@dataclass
class OscillationResult:
    """Results from oscillation detection."""
    oscillating: bool
    period: Optional[float]  # Oscillation period (timesteps)
    frequency: Optional[float]  # Oscillation frequency (1/timesteps)
    autocorr_peak: float  # Peak autocorrelation value
    spatial_modes: List[float]  # Dominant Fourier modes in cavity


@dataclass
class EntityCriterion:
    """Entity criterion measurements."""
    gamma: Optional[float]  # Decay width (wall leakage rate)
    mass: Optional[float]  # Cavity energy
    gamma_over_mass: Optional[float]  # Ratio
    satisfies_criterion: bool  # Γ < m ?


@dataclass
class TestResult:
    """Complete results for single configuration."""
    config: Configuration
    reflection: ReflectionResult
    oscillation: OscillationResult
    entity: EntityCriterion
    final_state: str  # "standing_wave", "reflected", "thermalized", "dispersed"


class MomentumCA:
    """1D cellular automaton with momentum-augmented transfer rule."""

    def __init__(self, N: int = 200, I_max: float = 1.0, dt: float = 0.01):
        """
        Initialize CA lattice with velocity field.

        Args:
            N: Number of cells
            I_max: Maximum intent density (saturation threshold)
            dt: Timestep size
        """
        self.N = N
        self.I_max = I_max
        self.dt = dt
        self.I = np.zeros(N)  # Intent density field
        self.v = np.zeros(N)  # Velocity field (NEW - second-order dynamics)

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
        Velocity initialized to zero (energy at rest).
        """
        if x0 is None:
            x0 = self.N // 2

        x = np.arange(self.N)
        self.I = A * np.exp(-(x - x0)**2 / (2 * sigma**2))
        self.I = np.clip(self.I, 0, None)
        self.v = np.zeros(self.N)  # Start at rest

    def step(self, k: float, n: int, alpha: float):
        """
        Single timestep of SECOND-ORDER CA evolution with momentum.

        v_t = α·v_{t-1} + k·∇²I·R(I)  (momentum update)
        I_{t+1} = I_t + v_t             (position update)

        Args:
            k: Coupling strength
            n: Saturation exponent
            alpha: Momentum retention factor
        """
        # Compute acceleration from current state
        acceleration = np.zeros(self.N)

        for x in range(self.N):
            # Periodic boundary conditions
            x_left = (x - 1) % self.N
            x_right = (x + 1) % self.N

            # Resistance at current cell
            R_x = self.R(np.array([self.I[x]]), n)[0]

            # Laplacian: ∇²I ≈ (I_{x+1} + I_{x-1} - 2I_x)
            laplacian = self.I[x_left] + self.I[x_right] - 2 * self.I[x]

            # Acceleration from diffusion with saturation
            acceleration[x] = k * laplacian * R_x

        # Momentum update: v_t = α·v_{t-1} + a_t
        v_new = alpha * self.v + self.dt * acceleration

        # Position update: I_{t+1} = I_t + v_t
        I_new = self.I + self.dt * v_new

        # Enforce physical constraints
        I_new = np.clip(I_new, 0, None)  # No negative intent

        # Update state
        self.I = I_new
        self.v = v_new

    def detect_walls(self, threshold: float = 0.01) -> List[int]:
        """Detect cells where saturation walls form (R(I) < threshold)."""
        R_vals = self.R(self.I, n=4)  # Use n=4 for detection
        wall_cells = np.where(R_vals < threshold)[0].tolist()
        return wall_cells

    def measure_velocity_reversal_at_walls(self, wall_cells: List[int],
                                           prev_v: np.ndarray) -> float:
        """
        Measure velocity reversal at wall boundaries.

        Returns maximum |Δv| at wall locations.
        """
        if len(wall_cells) == 0:
            return 0.0

        reversals = []
        for wall in wall_cells:
            # Check if velocity changed sign
            if prev_v[wall] * self.v[wall] < 0:
                reversals.append(abs(self.v[wall] - prev_v[wall]))

        return max(reversals) if reversals else 0.0


def detect_oscillation(time_series: np.ndarray, min_period: int = 5,
                       max_period: int = 500) -> Tuple[bool, Optional[float], float]:
    """
    Detect periodic oscillation in time series via autocorrelation.

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

    if np.std(signal_centered) < 1e-10:
        return False, None, 0.0

    # Autocorrelation
    autocorr = np.correlate(signal_centered, signal_centered, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]

    # Find peaks
    peaks = []
    for lag in range(min_period, min(len(autocorr), max_period)):
        if autocorr[lag] > 0.5:
            if lag > 0 and lag < len(autocorr) - 1:
                if autocorr[lag] > autocorr[lag-1] and autocorr[lag] > autocorr[lag+1]:
                    peaks.append((lag, autocorr[lag]))

    if not peaks:
        return False, None, np.max(autocorr[1:]) if len(autocorr) > 1 else 0.0

    best_peak = max(peaks, key=lambda p: p[1])
    period, corr = best_peak

    is_oscillating = corr > 0.7
    return is_oscillating, float(period) if is_oscillating else None, corr


def measure_entity_criterion(energy_history: List[float],
                             n_cycles: int = 5) -> EntityCriterion:
    """
    Measure Γ (decay width) and m (mass) from energy time series.

    Γ = energy loss rate per cycle
    m = average cavity energy
    """
    if len(energy_history) < 100:
        return EntityCriterion(None, None, None, False)

    energy_array = np.array(energy_history[-500:])  # Last 500 steps

    # Mass: average energy
    mass = np.mean(energy_array)

    if mass < 1e-6:
        return EntityCriterion(None, mass, None, False)

    # Gamma: decay rate (fit exponential to energy envelope)
    time = np.arange(len(energy_array))

    # Simple decay estimate: ΔE/E per timestep
    if len(energy_array) > 10:
        energy_change = energy_array[-1] - energy_array[0]
        time_span = len(energy_array)
        gamma = -energy_change / (mass * time_span) if mass > 0 else 0.0
        gamma = abs(gamma)  # Decay width is positive
    else:
        gamma = 0.0

    # Ratio
    ratio = gamma / mass if mass > 0 else float('inf')

    # Criterion: Γ < m (natural units)
    satisfies = gamma < mass

    return EntityCriterion(gamma, mass, ratio, satisfies)


def run_single_test(config: Configuration, n_steps: int = 10000,
                    record_interval: int = 10) -> TestResult:
    """
    Run single configuration test with momentum.

    Args:
        config: Parameter configuration (includes alpha)
        n_steps: Number of timesteps
        record_interval: Record state every N steps

    Returns:
        Complete test results
    """
    # Initialize CA with momentum
    ca = MomentumCA(N=200, I_max=1.0, dt=0.01)
    A = config.A_over_Imax * ca.I_max
    ca.initialize_gaussian_pulse(A, config.sigma)

    # Storage
    cavity_energy_history = []
    velocity_reversals = []
    prev_v = ca.v.copy()

    # Evolution
    for step in range(n_steps):
        ca.step(config.k, config.n, config.alpha)

        if step % record_interval == 0:
            # Measure energy
            walls = ca.detect_walls(threshold=0.01)
            if len(walls) >= 2:
                walls_sorted = sorted(walls)
                left = walls_sorted[0]
                right = walls_sorted[-1]
                cavity_energy = np.sum(ca.I[left:right+1])
            else:
                cavity_energy = np.sum(ca.I)

            cavity_energy_history.append(cavity_energy)

            # Measure velocity reversal at walls
            if len(walls) > 0:
                reversal = ca.measure_velocity_reversal_at_walls(walls, prev_v)
                velocity_reversals.append(reversal)

            prev_v = ca.v.copy()

    # Analyze reflection
    reflection_detected = len(velocity_reversals) > 0 and max(velocity_reversals) > 0.01
    max_reversal = max(velocity_reversals) if velocity_reversals else 0.0
    reversal_count = sum(1 for v in velocity_reversals if v > 0.01)
    avg_bounce = np.mean([v for v in velocity_reversals if v > 0.01]) if reversal_count > 0 else 0.0

    reflection_result = ReflectionResult(
        reflection_detected=reflection_detected,
        max_velocity_reversal=max_reversal,
        reversal_count=reversal_count,
        wall_bounce_strength=avg_bounce
    )

    # Analyze oscillation
    energy_array = np.array(cavity_energy_history)
    is_osc, period, peak_corr = detect_oscillation(energy_array)

    frequency = 1.0 / period if period else None

    oscillation_result = OscillationResult(
        oscillating=is_osc,
        period=period,
        frequency=frequency,
        autocorr_peak=peak_corr,
        spatial_modes=[]  # TODO: Add Fourier analysis
    )

    # Analyze entity criterion
    entity_result = measure_entity_criterion(cavity_energy_history)

    # Classify final state
    if is_osc and reflection_detected:
        final_state = "standing_wave"
    elif reflection_detected and not is_osc:
        final_state = "reflected"
    elif energy_array[-1] < 0.01 * energy_array[0]:
        final_state = "dispersed"
    else:
        final_state = "thermalized"

    return TestResult(
        config=config,
        reflection=reflection_result,
        oscillation=oscillation_result,
        entity=entity_result,
        final_state=final_state
    )


def generate_configurations() -> List[Configuration]:
    """
    Generate configurations for momentum CA test.

    Focus on Session #20's wall-forming configs + alpha sweep.
    """
    # From Session #20: A/I_max ≥ 1.2, lower k favor walls
    A_over_Imax_values = [1.2, 2.0]  # Wall-forming amplitudes
    sigma_values = [10, 20]  # Pulse widths
    k_values = [0.05, 0.1]  # Coupling strengths
    n_values = [4, 8]  # Saturation sharpness

    # Momentum sweep (key new parameter)
    alpha_values = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99]

    configs = []
    config_id = 0

    for A in A_over_Imax_values:
        for sigma in sigma_values:
            for k in k_values:
                for n in n_values:
                    for alpha in alpha_values:
                        configs.append(Configuration(
                            A_over_Imax=A,
                            sigma=sigma,
                            k=k,
                            n=n,
                            alpha=alpha,
                            config_id=config_id
                        ))
                        config_id += 1

    return configs


def main():
    """Run momentum-augmented CA test (Option B1)."""
    print("=" * 80)
    print("MOMENTUM-AUGMENTED CA TEST - Option B1")
    print("=" * 80)
    print()
    print("Hypothesis: Adding momentum term v_t = α·v_{t-1} + acceleration")
    print("enables energy reflection at saturation walls, producing oscillations.")
    print()
    print("This tests whether second-order dynamics can produce what first-order")
    print("CA could not (Sessions #18-20: 0/696 oscillations).")
    print()

    # Generate configurations
    configs = generate_configurations()
    print(f"Total configurations: {len(configs)}")
    print(f"Alpha values: {sorted(set(c.alpha for c in configs))}")
    print()

    # Run tests
    results = []
    reflection_count = 0
    oscillation_count = 0
    standing_wave_count = 0
    entity_criterion_count = 0

    for i, config in enumerate(configs):
        if (i + 1) % 20 == 0:
            print(f"Progress: {i+1}/{len(configs)} ({100*(i+1)/len(configs):.1f}%)")

        result = run_single_test(config, n_steps=10000, record_interval=10)
        results.append(result)

        if result.reflection.reflection_detected:
            reflection_count += 1
        if result.oscillation.oscillating:
            oscillation_count += 1
        if result.final_state == "standing_wave":
            standing_wave_count += 1
        if result.entity.satisfies_criterion:
            entity_criterion_count += 1

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"Configurations tested: {len(results)}")
    print(f"Reflections detected: {reflection_count} ({100*reflection_count/len(results):.1f}%)")
    print(f"Oscillations detected: {oscillation_count} ({100*oscillation_count/len(results):.1f}%)")
    print(f"Standing waves: {standing_wave_count} ({100*standing_wave_count/len(results):.1f}%)")
    print(f"Entity criterion (Γ<m): {entity_criterion_count} ({100*entity_criterion_count/len(results):.1f}%)")
    print()

    # Save results
    results_file = "momentum_ca_results.json"
    results_data = {
        "summary": {
            "total_configs": len(results),
            "reflections": reflection_count,
            "oscillations": oscillation_count,
            "standing_waves": standing_wave_count,
            "entity_criterion_satisfied": entity_criterion_count
        },
        "results": [
            {
                "config": asdict(r.config),
                "reflection": asdict(r.reflection),
                "oscillation": asdict(r.oscillation),
                "entity": asdict(r.entity),
                "final_state": r.final_state
            }
            for r in results
        ]
    }

    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"Detailed results saved to: {results_file}")
    print()

    # Analyze by alpha
    if reflection_count > 0 or oscillation_count > 0:
        print("=" * 80)
        print("ALPHA DEPENDENCE")
        print("=" * 80)
        print()

        alpha_values = sorted(set(c.alpha for c in configs))
        for alpha in alpha_values:
            alpha_results = [r for r in results if r.config.alpha == alpha]
            alpha_reflect = sum(1 for r in alpha_results if r.reflection.reflection_detected)
            alpha_osc = sum(1 for r in alpha_results if r.oscillation.oscillating)
            alpha_sw = sum(1 for r in alpha_results if r.final_state == "standing_wave")

            print(f"α = {alpha:.2f}: {len(alpha_results)} configs")
            print(f"  Reflections: {alpha_reflect}/{len(alpha_results)} ({100*alpha_reflect/len(alpha_results):.0f}%)")
            print(f"  Oscillations: {alpha_osc}/{len(alpha_results)} ({100*alpha_osc/len(alpha_results):.0f}%)")
            print(f"  Standing waves: {alpha_sw}/{len(alpha_results)} ({100*alpha_sw/len(alpha_results):.0f}%)")
            print()

    # Report best cases
    if standing_wave_count > 0:
        print("=" * 80)
        print("STANDING WAVE CONFIGURATIONS (Top 10)")
        print("=" * 80)
        print()

        sw_results = [r for r in results if r.final_state == "standing_wave"]
        sw_results.sort(key=lambda r: r.oscillation.autocorr_peak, reverse=True)

        for r in sw_results[:10]:
            c = r.config
            print(f"Config {c.config_id}: α={c.alpha:.2f}, A/I_max={c.A_over_Imax:.1f}, k={c.k:.2f}")
            print(f"  Period: {r.oscillation.period:.1f} steps")
            print(f"  Autocorr: {r.oscillation.autocorr_peak:.3f}")
            print(f"  Γ/m: {r.entity.gamma_over_mass:.4f if r.entity.gamma_over_mass else 'N/A'}")
            print()

    # Final verdict
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print()

    if standing_wave_count > 0:
        print(f"✅ SUCCESS - MOMENTUM ENABLES OSCILLATION")
        print(f"   {standing_wave_count} configurations produced standing waves")
        print(f"   Second-order CA overcomes first-order thermalization")
        print(f"   Option B1 validates - oscillations emerge from substrate")
    elif reflection_count > 0:
        print(f"⚠️  PARTIAL - REFLECTION WITHOUT OSCILLATION")
        print(f"   {reflection_count} configurations showed velocity reversal")
        print(f"   Energy reflects but doesn't form stable standing waves")
        print(f"   May need parameter tuning or longer evolution time")
    else:
        print(f"❌ FAILURE - NO REFLECTION OR OSCILLATION")
        print(f"   Momentum term insufficient for energy reflection")
        print(f"   Option B1 fails - oscillation remains axiomatic")
    print()


if __name__ == "__main__":
    main()
