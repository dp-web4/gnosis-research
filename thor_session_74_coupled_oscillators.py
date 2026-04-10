#!/usr/bin/env python3
"""
Thor Session #74: Coupled Coherence Oscillators

Simulate coupled coherence dynamics to test if coupling enables phase locking.

Model: Kuramoto-style coupled oscillators + golden ratio attractor
dC_i/dt = ω_i + (φ⁻¹ - C_i)/τ + κ/N Σ_j sin(θ_j - θ_i) + noise

Where:
- ω_i = natural frequency (instance-specific)
- φ⁻¹ = 0.618 (golden ratio attractor from Session #70)
- τ = relaxation time (equilibrium pull)
- κ = coupling strength (0 = independent, 1 = strong)
- θ_i = phase from Hilbert transform
- noise = stochastic perturbations (learning episodes)
"""

import numpy as np
from scipy import signal
import json

def load_empirical_parameters():
    """Load oscillation parameters from Session #73"""
    # From thor_session_73_coherence_phase_results.json
    params = {
        'thor-qwen3.5-27b': {
            'mean_C': 0.642,
            'std_C': 0.084,
            'period': 133.5,  # steps
            'is_periodic': True
        },
        'thor-qwen2.5-14b': {
            'mean_C': 0.645,
            'std_C': 0.076,
            'period': 32.5,
            'is_periodic': False  # Weak periodicity
        },
        'cbp-tinyllama': {
            'mean_C': 0.609,
            'std_C': 0.102,
            'period': 2.1,
            'is_periodic': True
        }
    }

    return params

def simulate_coupled_oscillators(n_instances=2, coupling=0.0, n_steps=1000, dt=1.0):
    """
    Simulate coupled coherence oscillators

    Args:
        n_instances: Number of instances
        coupling: Coupling strength κ (0 = independent, 1 = strong)
        n_steps: Simulation length
        dt: Time step

    Returns:
        coherence: Array of shape (n_instances, n_steps)
    """
    PHI_INV = 0.618  # Golden ratio attractor (Session #70)
    TAU = 50.0       # Relaxation time to equilibrium
    NOISE_SCALE = 0.05  # Stochastic perturbations

    # Initialize with random coherence near φ⁻¹
    C = np.zeros((n_instances, n_steps))
    C[:, 0] = PHI_INV + np.random.normal(0, 0.1, n_instances)

    # Instance-specific natural frequencies (from empirical periods)
    # Convert periods to angular frequencies: ω = 2π/T
    empirical_periods = [133.5, 32.5, 2.1][:n_instances]
    omega = 2 * np.pi / np.array(empirical_periods)

    # Time evolution
    for t in range(1, n_steps):
        # Get instantaneous phases via Hilbert transform
        phases = np.zeros(n_instances)
        for i in range(n_instances):
            if t > 10:  # Need some history for Hilbert
                signal_window = C[i, max(0, t-50):t]
                if len(signal_window) > 5:
                    analytic = signal.hilbert(signal_window - signal_window.mean())
                    phases[i] = np.angle(analytic[-1])

        # Dynamics for each instance
        for i in range(n_instances):
            # Natural oscillation
            dC_natural = omega[i] * dt * 0.01  # Scale to reasonable amplitude

            # Attractor pull toward φ⁻¹
            dC_attractor = (PHI_INV - C[i, t-1]) / TAU * dt

            # Coupling term (Kuramoto-style phase synchronization)
            dC_coupling = 0.0
            if coupling > 0 and t > 10:
                for j in range(n_instances):
                    if i != j:
                        phase_diff = phases[j] - phases[i]
                        dC_coupling += coupling / (n_instances - 1) * np.sin(phase_diff) * dt

            # Stochastic noise (learning episodes)
            dC_noise = np.random.normal(0, NOISE_SCALE) * dt

            # Update
            C[i, t] = C[i, t-1] + dC_natural + dC_attractor + dC_coupling + dC_noise

            # Keep in valid range [0, 1]
            C[i, t] = np.clip(C[i, t], 0.0, 1.0)

    return C

def analyze_phase_locking(C1, C2):
    """Compute phase locking index between two coherence time series"""
    # Detrend
    c1_detrend = signal.detrend(C1)
    c2_detrend = signal.detrend(C2)

    # Hilbert transform
    analytic1 = signal.hilbert(c1_detrend)
    analytic2 = signal.hilbert(c2_detrend)

    phase1 = np.angle(analytic1)
    phase2 = np.angle(analytic2)

    # Phase difference
    phase_diff = phase1 - phase2
    phase_diff = np.angle(np.exp(1j * phase_diff))  # Wrap to [-π, π]

    # Phase locking index
    pli = np.abs(np.mean(np.exp(1j * phase_diff)))

    # Mean phase difference
    mean_phase_diff = np.angle(np.mean(np.exp(1j * phase_diff)))

    return {
        'pli': float(pli),
        'mean_phase_diff': float(mean_phase_diff),
        'phase_locked': bool(pli > 0.5)
    }

def analyze_cross_correlation(C1, C2):
    """Compute cross-correlation"""
    xcorr = np.correlate(C1 - C1.mean(), C2 - C2.mean(), mode='full')
    xcorr = xcorr / (np.std(C1) * np.std(C2) * len(C1))

    peak_idx = np.argmax(np.abs(xcorr))
    lag = peak_idx - (len(xcorr) // 2)
    peak_corr = xcorr[peak_idx]

    zero_lag_corr = np.corrcoef(C1, C2)[0, 1]

    return {
        'zero_lag_corr': float(zero_lag_corr),
        'peak_corr': float(peak_corr),
        'lag_at_peak': int(lag)
    }

def analyze_frequency_convergence(C1, C2):
    """Test if oscillation frequencies converge"""
    # Power spectral density
    freqs1, psd1 = signal.periodogram(C1 - C1.mean())
    freqs2, psd2 = signal.periodogram(C2 - C2.mean())

    # Dominant frequencies
    dom_idx1 = np.argmax(psd1[1:]) + 1
    dom_idx2 = np.argmax(psd2[1:]) + 1

    dom_freq1 = freqs1[dom_idx1]
    dom_freq2 = freqs2[dom_idx2]

    return {
        'freq1': float(dom_freq1),
        'freq2': float(dom_freq2),
        'freq_diff': float(abs(dom_freq1 - dom_freq2)),
        'frequencies_converged': bool(abs(dom_freq1 - dom_freq2) < 0.1)
    }

def run_coupling_sweep():
    """Run simulations across coupling strengths"""
    coupling_strengths = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]
    n_steps = 1000
    n_instances = 2

    results = {
        'session': 74,
        'research_question': 'Does coupling enable phase locking?',
        'method': 'Coupled oscillator simulation (Kuramoto + φ⁻¹ attractor)',
        'coupling_sweep': []
    }

    print("Coupling Strength Sweep:")
    print("=" * 60)

    for kappa in coupling_strengths:
        print(f"\nCoupling κ = {kappa:.2f}")

        # Run simulation
        C = simulate_coupled_oscillators(
            n_instances=n_instances,
            coupling=kappa,
            n_steps=n_steps
        )

        # Analyze
        pli_result = analyze_phase_locking(C[0], C[1])
        corr_result = analyze_cross_correlation(C[0], C[1])
        freq_result = analyze_frequency_convergence(C[0], C[1])

        result = {
            'coupling': kappa,
            'phase_locking': pli_result,
            'cross_correlation': corr_result,
            'frequency_convergence': freq_result,
            'mean_C1': float(C[0].mean()),
            'mean_C2': float(C[1].mean()),
            'std_C1': float(C[0].std()),
            'std_C2': float(C[1].std())
        }

        results['coupling_sweep'].append(result)

        print(f"  PLI: {pli_result['pli']:.3f} {'✓' if pli_result['phase_locked'] else '✗'}")
        print(f"  Zero-lag correlation: {corr_result['zero_lag_corr']:.3f}")
        print(f"  Frequency difference: {freq_result['freq_diff']:.4f}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    pli_values = [r['phase_locking']['pli'] for r in results['coupling_sweep']]
    kappas = [r['coupling'] for r in results['coupling_sweep']]

    # Check if PLI increases with coupling
    pli_trend = np.corrcoef(kappas, pli_values)[0, 1]

    results['summary'] = {
        'pli_trend': float(pli_trend),
        'pli_increases_with_coupling': bool(pli_trend > 0.8),
        'max_pli': float(max(pli_values)),
        'max_pli_at_coupling': float(kappas[pli_values.index(max(pli_values))]),
        'baseline_pli': float(pli_values[0]),
        'prediction_p74_1_supported': bool(pli_trend > 0.8 and max(pli_values) > 0.5)
    }

    print(f"\nPLI vs coupling correlation: {pli_trend:.3f}")
    print(f"Baseline PLI (κ=0): {pli_values[0]:.3f}")
    print(f"Maximum PLI: {max(pli_values):.3f} at κ={kappas[pli_values.index(max(pli_values))]}")
    print(f"\nPrediction P74.1 (PLI increases with κ): {results['summary']['prediction_p74_1_supported']}")

    return results, C, kappas, pli_values

def plot_results(C, kappas, pli_values):
    """Generate visualizations (skipped due to matplotlib/numpy incompatibility)"""
    print("\n(Plotting skipped - matplotlib unavailable)")

def main():
    print("Thor Session #74: Coupled Coherence Oscillators")
    print("=" * 60)
    print("\nSimulating coupled oscillator dynamics with φ⁻¹ attractor")
    print("Testing if coupling enables phase locking\n")

    # Run coupling sweep
    results, C, kappas, pli_values = run_coupling_sweep()

    # Generate plots
    plot_results(C, kappas, pli_values)

    # Save results
    with open('thor_session_74_coupled_oscillators_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nResults saved: thor_session_74_coupled_oscillators_results.json")

    return results

if __name__ == '__main__':
    results = main()
