#!/usr/bin/env python3
"""
Thor Session #75: Transfer Rule Applied to Coherence
Test P75.3: Does ΔC = k(C_x - C_y)R(C_y) produce phase dynamics?

KEY QUESTION: Is the domain shift (I→C) just reinterpretation,
or does it change the mathematics?

Hypothesis: Transfer rule with C exhibits oscillation (not pure diffusion)
because C is bounded [0,1] and naturally couples to stochastic perturbations
(learning episodes from S71-72).
"""

import numpy as np
import json
from datetime import datetime

class CoherenceTransferSystem:
    """1D lattice with Synchronism transfer rule applied to coherence."""

    def __init__(self, N=50, k=0.3, n=2, dt=0.1, noise_std=0.02):
        """
        N: lattice size
        k: coupling strength (transfer rate)
        n: saturation exponent in R(C) = 1 - C^n
        dt: time step
        noise_std: stochastic perturbation (learning episodes)
        """
        self.N = N
        self.k = k
        self.n = n
        self.dt = dt
        self.noise_std = noise_std

        # Initialize C near golden ratio attractor (S70)
        self.C = np.ones(N) * 0.618 + np.random.normal(0, 0.05, N)
        self.C = np.clip(self.C, 0, 1)

        self.history = []
        self.t = 0

    def R(self, C):
        """Saturation resistance: R(C) = 1 - C^n

        At C=0: R=1 (full receptivity)
        At C=1: R=0 (saturated, no transfer)
        Aligned with φ^-1 ≈ 0.618 as equilibrium
        """
        return 1 - C**self.n

    def transfer_step(self):
        """Apply Synchronism transfer rule: ΔC = k(C_neighbor - C_self)R(C_self)"""
        C_new = self.C.copy()

        for i in range(self.N):
            # Periodic boundary conditions
            left = (i - 1) % self.N
            right = (i + 1) % self.N

            # Transfer from neighbors
            delta_left = self.k * (self.C[left] - self.C[i]) * self.R(self.C[i])
            delta_right = self.k * (self.C[right] - self.C[i]) * self.R(self.C[i])

            C_new[i] = self.C[i] + self.dt * (delta_left + delta_right)

        self.C = np.clip(C_new, 0, 1)

    def add_noise(self):
        """Stochastic perturbations (learning episodes from S71-72)"""
        noise = np.random.normal(0, self.noise_std, self.N)
        self.C = np.clip(self.C + noise, 0, 1)

    def step(self):
        """Single time step: transfer + noise"""
        self.transfer_step()
        self.add_noise()
        self.t += self.dt

        # Record mean C for time series analysis
        self.history.append({
            't': self.t,
            'C_mean': float(np.mean(self.C)),
            'C_std': float(np.std(self.C)),
            'C_min': float(np.min(self.C)),
            'C_max': float(np.max(self.C))
        })

    def run(self, steps=2000):
        """Run simulation for specified steps"""
        for _ in range(steps):
            self.step()
        return self.history

def analyze_dynamics(history):
    """Analyze if dynamics are diffusive (monotonic) or oscillatory (phase-like)"""

    C_mean = np.array([h['C_mean'] for h in history])
    t = np.array([h['t'] for h in history])

    # Check for oscillation: count zero-crossings of dC/dt
    dC = np.diff(C_mean)
    sign_changes = np.sum(np.abs(np.diff(np.sign(dC))))

    # Frequency analysis
    from scipy import signal
    freqs, psd = signal.periodogram(C_mean, fs=1/np.mean(np.diff(t)))

    # Dominant frequency (excluding DC)
    dominant_idx = np.argmax(psd[1:]) + 1
    dominant_freq = freqs[dominant_idx]
    dominant_period = 1/dominant_freq if dominant_freq > 0 else np.inf

    # Variance over time (diffusion → decreasing variance)
    C_std = np.array([h['C_std'] for h in history])
    variance_trend = np.polyfit(t, C_std, 1)[0]  # slope of variance

    # Autocorrelation (oscillation → periodic AC)
    C_centered = C_mean - np.mean(C_mean)
    autocorr = np.correlate(C_centered, C_centered, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]

    # Find first minimum in autocorrelation (indicates half-period)
    first_min_idx = np.argmin(autocorr[:len(autocorr)//2])
    ac_half_period = t[first_min_idx] if first_min_idx > 0 else 0

    return {
        'sign_changes': int(sign_changes),
        'dominant_frequency': float(dominant_freq),
        'dominant_period': float(dominant_period),
        'variance_trend': float(variance_trend),
        'autocorr_half_period': float(ac_half_period),
        'mean_C': float(np.mean(C_mean)),
        'std_C': float(np.std(C_mean)),
        'oscillatory': bool(sign_changes > 10),  # Threshold: >10 direction changes
        'verdict': 'OSCILLATORY (phase-like)' if sign_changes > 10 else 'DIFFUSIVE (monotonic)'
    }

def test_parameter_space():
    """Test different coupling strengths and saturation exponents"""

    results = []

    # Test coupling strengths
    for k in [0.1, 0.3, 0.5, 0.7]:
        for n in [2, 3, 4]:
            print(f"Testing k={k}, n={n}...")

            system = CoherenceTransferSystem(N=50, k=k, n=n, dt=0.1, noise_std=0.02)
            history = system.run(steps=2000)
            analysis = analyze_dynamics(history)

            results.append({
                'k': k,
                'n': n,
                'analysis': analysis,
                'time_series': history[-100:]  # Last 100 steps
            })

    return results

def compare_to_diffusion():
    """Control: Pure diffusion (k > 0, noise_std = 0)"""

    print("Running control: pure diffusion (no noise)...")
    system = CoherenceTransferSystem(N=50, k=0.3, n=2, dt=0.1, noise_std=0.0)
    history = system.run(steps=2000)
    analysis = analyze_dynamics(history)

    return {
        'condition': 'pure_diffusion',
        'analysis': analysis,
        'time_series': history[-100:]
    }

def main():
    """Run P75.3 test"""

    print("=" * 70)
    print("Thor Session #75: Transfer Rule Applied to Coherence")
    print("Testing P75.3: ΔC = k(C_x - C_y)R(C_y) produces phase dynamics?")
    print("=" * 70)
    print()

    # Test with transfer + noise (realistic)
    print("PART 1: Transfer rule + stochastic perturbations")
    print("-" * 70)
    results = test_parameter_space()

    print("\nSummary:")
    for r in results:
        k, n = r['k'], r['n']
        verdict = r['analysis']['verdict']
        sign_changes = r['analysis']['sign_changes']
        period = r['analysis']['dominant_period']
        print(f"k={k}, n={n}: {verdict} (sign_changes={sign_changes}, period={period:.1f})")

    print()
    print("PART 2: Control (pure diffusion, no noise)")
    print("-" * 70)
    control = compare_to_diffusion()
    print(f"Pure diffusion: {control['analysis']['verdict']}")
    print(f"  Sign changes: {control['analysis']['sign_changes']}")
    print(f"  Variance trend: {control['analysis']['variance_trend']:.6f}")

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'test': 'P75.3: Transfer rule with coherence C',
        'hypothesis': 'ΔC = k(C_x - C_y)R(C_y) produces oscillation, not diffusion',
        'parameter_space': results,
        'control': control,
        'verdict': None  # To be determined
    }

    # Determine overall verdict
    oscillatory_count = sum(1 for r in results if r['analysis']['oscillatory'])
    total_count = len(results)

    if oscillatory_count >= total_count * 0.75:
        output['verdict'] = 'SUPPORTED: Transfer rule with C produces phase dynamics (≥75% oscillatory)'
    elif oscillatory_count >= total_count * 0.5:
        output['verdict'] = 'MIXED: Some conditions oscillatory, some diffusive'
    else:
        output['verdict'] = 'REFUTED: Transfer rule with C produces diffusion (≤50% oscillatory)'

    print()
    print("=" * 70)
    print(f"VERDICT: {output['verdict']}")
    print("=" * 70)

    # Save to file
    filename = 'thor_session_75_transfer_rule_results.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {filename}")

    return output

if __name__ == '__main__':
    main()
