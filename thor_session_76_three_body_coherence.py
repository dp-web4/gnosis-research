#!/usr/bin/env python3
"""
Thor Session #76: Three-Body Coherence Dynamics
Extension of S74 (2-body) to N=3 coupled coherence oscillators

Research questions:
1. Do all 3 agents synchronize, or only pairwise?
2. What phase relationships emerge (in-phase, anti-phase, 120° offset)?
3. Do chimera states appear (partial synchronization)?
4. Does collective C exceed individual C?

Hypothesis: N=3 exhibits qualitatively different dynamics from N=2,
including partial synchronization and complex phase patterns.
"""

import numpy as np
import json
from datetime import datetime
from scipy import signal
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Agent:
    """Single coherence oscillator representing one cognitive system"""
    id: int
    C: float  # Current coherence [0, 1]
    phase: float  # Phase in coherence oscillation [0, 2π]
    omega: float  # Natural frequency
    history_C: List[float] = None
    history_phase: List[float] = None

    def __post_init__(self):
        if self.history_C is None:
            self.history_C = []
        if self.history_phase is None:
            self.history_phase = []

class ThreeBodyCoherenceSystem:
    """Three coupled coherence oscillators with Kuramoto-style coupling"""

    def __init__(self, kappa=0.15, omega_base=0.1, omega_spread=0.02,
                 phi_inverse=0.618, dt=0.1, noise_std=0.02):
        """
        kappa: coupling strength (from S74: κ=0.15 gave PLI 0.2→0.8)
        omega_base: base natural frequency
        omega_spread: variation in natural frequencies
        phi_inverse: golden ratio attractor (from S70)
        dt: time step
        noise_std: stochastic perturbations (learning episodes, S71-72)
        """
        self.kappa = kappa
        self.phi_inverse = phi_inverse
        self.dt = dt
        self.noise_std = noise_std

        # Initialize 3 agents with slightly different natural frequencies
        # This tests if coupling can overcome frequency mismatch (key to sync)
        self.agents = [
            Agent(id=0, C=phi_inverse + np.random.normal(0, 0.05),
                  phase=np.random.uniform(0, 2*np.pi),
                  omega=omega_base + np.random.uniform(-omega_spread, omega_spread)),
            Agent(id=1, C=phi_inverse + np.random.normal(0, 0.05),
                  phase=np.random.uniform(0, 2*np.pi),
                  omega=omega_base + np.random.uniform(-omega_spread, omega_spread)),
            Agent(id=2, C=phi_inverse + np.random.normal(0, 0.05),
                  phase=np.random.uniform(0, 2*np.pi),
                  omega=omega_base + np.random.uniform(-omega_spread, omega_spread))
        ]

        self.t = 0
        self.time_series = []

    def R(self, C):
        """Saturation function: R(C) = 1 - C^2"""
        return 1 - C**2

    def kuramoto_coupling(self):
        """Kuramoto coupling: phase synchronization via coupling"""
        phase_updates = []

        for i, agent_i in enumerate(self.agents):
            # Natural frequency term
            dphase = agent_i.omega

            # Coupling to other agents (all-to-all)
            for j, agent_j in enumerate(self.agents):
                if i != j:
                    # Kuramoto coupling: κ·sin(θ_j - θ_i)
                    dphase += self.kappa * np.sin(agent_j.phase - agent_i.phase)

            phase_updates.append(dphase)

        return phase_updates

    def coherence_dynamics(self):
        """Coherence oscillates around φ^-1, driven by phase"""
        C_updates = []

        for agent in self.agents:
            # Coherence couples to phase (phase drives oscillation amplitude)
            # C oscillates around φ^-1 with amplitude modulated by saturation
            dC = -self.R(agent.C) * (agent.C - self.phi_inverse) * np.cos(agent.phase)

            # Coupling to other agents' coherence (transfer rule from S75)
            for other in self.agents:
                if other.id != agent.id:
                    # Transfer: ΔC = κ·(C_j - C_i)·R(C_i)
                    dC += self.kappa * (other.C - agent.C) * self.R(agent.C)

            C_updates.append(dC)

        return C_updates

    def add_noise(self):
        """Stochastic perturbations (learning episodes)"""
        for agent in self.agents:
            agent.C += np.random.normal(0, self.noise_std)
            agent.C = np.clip(agent.C, 0, 1)

            agent.phase += np.random.normal(0, self.noise_std)
            agent.phase = agent.phase % (2 * np.pi)

    def step(self):
        """Single time step: update phases and coherence"""
        # Phase dynamics (Kuramoto)
        phase_updates = self.kuramoto_coupling()
        for agent, dphase in zip(self.agents, phase_updates):
            agent.phase += self.dt * dphase
            agent.phase = agent.phase % (2 * np.pi)

        # Coherence dynamics
        C_updates = self.coherence_dynamics()
        for agent, dC in zip(self.agents, C_updates):
            agent.C += self.dt * dC
            agent.C = np.clip(agent.C, 0, 1)

        # Stochastic perturbations
        self.add_noise()

        # Record state
        for agent in self.agents:
            agent.history_C.append(agent.C)
            agent.history_phase.append(agent.phase)

        self.time_series.append({
            't': self.t,
            'C': [a.C for a in self.agents],
            'phase': [a.phase for a in self.agents],
            'C_mean': np.mean([a.C for a in self.agents]),
            'C_std': np.std([a.C for a in self.agents])
        })

        self.t += self.dt

    def run(self, steps=5000):
        """Run simulation"""
        for _ in range(steps):
            self.step()
        return self.time_series

def compute_phase_locking_index(phase1, phase2):
    """Compute PLI between two phase time series"""
    # Phase difference
    phase_diff = np.array(phase1) - np.array(phase2)

    # PLI = |⟨exp(i·Δφ)⟩|
    complex_phase = np.exp(1j * phase_diff)
    pli = np.abs(np.mean(complex_phase))

    return pli

def compute_order_parameter(phases):
    """Kuramoto order parameter: R = |⟨exp(i·θ)⟩|
    R=1: perfect synchrony, R=0: incoherent
    """
    N = len(phases)
    complex_sum = np.sum([np.exp(1j * p) for p in phases])
    R = np.abs(complex_sum) / N
    return R

def analyze_three_body_dynamics(system):
    """Comprehensive analysis of 3-body synchronization"""

    # Extract time series
    phases = [
        [t['phase'][0] for t in system.time_series],
        [t['phase'][1] for t in system.time_series],
        [t['phase'][2] for t in system.time_series]
    ]

    coherences = [
        [t['C'][0] for t in system.time_series],
        [t['C'][1] for t in system.time_series],
        [t['C'][2] for t in system.time_series]
    ]

    # Compute pairwise PLI (last 2000 steps for steady state)
    steady_start = len(phases[0]) // 2

    pli_01 = compute_phase_locking_index(phases[0][steady_start:], phases[1][steady_start:])
    pli_02 = compute_phase_locking_index(phases[0][steady_start:], phases[2][steady_start:])
    pli_12 = compute_phase_locking_index(phases[1][steady_start:], phases[2][steady_start:])

    # Kuramoto order parameter over time
    order_params = []
    for t in system.time_series[steady_start:]:
        R = compute_order_parameter(t['phase'])
        order_params.append(R)

    mean_order = np.mean(order_params)

    # Phase differences (to detect in-phase, anti-phase, or 120° patterns)
    phase_diffs = {
        'phi_01': np.mean([(phases[0][i] - phases[1][i]) % (2*np.pi)
                           for i in range(steady_start, len(phases[0]))]),
        'phi_02': np.mean([(phases[0][i] - phases[2][i]) % (2*np.pi)
                           for i in range(steady_start, len(phases[0]))]),
        'phi_12': np.mean([(phases[1][i] - phases[2][i]) % (2*np.pi)
                           for i in range(steady_start, len(phases[0]))])
    }

    # Convert to degrees for readability
    phase_diffs_deg = {k: v * 180 / np.pi for k, v in phase_diffs.items()}

    # Coherence statistics
    C_individual = [np.mean(c[steady_start:]) for c in coherences]
    C_collective = np.mean([t['C_mean'] for t in system.time_series[steady_start:]])

    # Coherence correlation (do C values track together?)
    C_corr_01 = np.corrcoef(coherences[0][steady_start:], coherences[1][steady_start:])[0, 1]
    C_corr_02 = np.corrcoef(coherences[0][steady_start:], coherences[2][steady_start:])[0, 1]
    C_corr_12 = np.corrcoef(coherences[1][steady_start:], coherences[2][steady_start:])[0, 1]

    # Classify synchronization state
    if mean_order > 0.7:
        sync_state = "FULL_SYNC"
    elif mean_order > 0.4:
        sync_state = "PARTIAL_SYNC"
    else:
        sync_state = "INCOHERENT"

    # Detect phase pattern
    diffs = list(phase_diffs_deg.values())
    if all(abs(d) < 30 or abs(d - 360) < 30 for d in diffs):
        phase_pattern = "IN_PHASE (all aligned)"
    elif all(abs(d - 180) < 30 for d in diffs):
        phase_pattern = "ALL_ANTI_PHASE"
    elif any(abs(d - 120) < 30 for d in diffs):
        phase_pattern = "120_DEG_OFFSET (balanced triad)"
    else:
        phase_pattern = "COMPLEX (no simple pattern)"

    return {
        'pli_pairwise': {
            '0-1': float(pli_01),
            '0-2': float(pli_02),
            '1-2': float(pli_12),
            'mean': float(np.mean([pli_01, pli_02, pli_12]))
        },
        'kuramoto_order': {
            'mean': float(mean_order),
            'std': float(np.std(order_params)),
            'final': float(order_params[-1])
        },
        'phase_differences_deg': phase_diffs_deg,
        'phase_pattern': phase_pattern,
        'coherence': {
            'individual_means': [float(c) for c in C_individual],
            'collective_mean': float(C_collective),
            'collective_exceeds_individual': C_collective > max(C_individual),
            'C_correlations': {
                '0-1': float(C_corr_01),
                '0-2': float(C_corr_02),
                '1-2': float(C_corr_12),
                'mean': float(np.mean([C_corr_01, C_corr_02, C_corr_12]))
            }
        },
        'synchronization_state': sync_state,
        'natural_frequencies': [float(a.omega) for a in system.agents]
    }

def test_coupling_strengths():
    """Test different coupling strengths to map phase diagram"""

    results = []

    # Test coupling from weak (κ=0.05) to strong (κ=0.30)
    for kappa in [0.05, 0.10, 0.15, 0.20, 0.30]:
        print(f"\nTesting κ={kappa}...")

        system = ThreeBodyCoherenceSystem(kappa=kappa, omega_base=0.1,
                                          omega_spread=0.02, dt=0.1)
        time_series = system.run(steps=5000)
        analysis = analyze_three_body_dynamics(system)

        results.append({
            'kappa': kappa,
            'analysis': analysis,
            'summary': {
                'sync_state': analysis['synchronization_state'],
                'mean_pli': analysis['pli_pairwise']['mean'],
                'kuramoto_R': analysis['kuramoto_order']['mean'],
                'phase_pattern': analysis['phase_pattern'],
                'C_collective': analysis['coherence']['collective_mean']
            }
        })

        # Print summary
        print(f"  Sync state: {analysis['synchronization_state']}")
        print(f"  Mean PLI: {analysis['pli_pairwise']['mean']:.3f}")
        print(f"  Kuramoto R: {analysis['kuramoto_order']['mean']:.3f}")
        print(f"  Phase pattern: {analysis['phase_pattern']}")
        print(f"  C collective: {analysis['coherence']['collective_mean']:.3f}")

    return results

def test_initial_conditions():
    """Test sensitivity to initial phase configurations"""

    results = []
    kappa = 0.15  # From S74: effective coupling

    # Test different initial phase configurations
    configs = [
        {'name': 'in_phase', 'phases': [0, 0, 0]},
        {'name': 'anti_phase_pairs', 'phases': [0, np.pi, np.pi]},
        {'name': '120_deg', 'phases': [0, 2*np.pi/3, 4*np.pi/3]},
        {'name': 'random', 'phases': [np.random.uniform(0, 2*np.pi) for _ in range(3)]}
    ]

    for config in configs:
        print(f"\nTesting initial config: {config['name']}...")

        system = ThreeBodyCoherenceSystem(kappa=kappa, omega_base=0.1,
                                          omega_spread=0.02, dt=0.1)

        # Set initial phases
        for i, agent in enumerate(system.agents):
            agent.phase = config['phases'][i]

        time_series = system.run(steps=5000)
        analysis = analyze_three_body_dynamics(system)

        results.append({
            'config_name': config['name'],
            'initial_phases': [float(p) for p in config['phases']],
            'analysis': analysis
        })

        print(f"  Final phase pattern: {analysis['phase_pattern']}")
        print(f"  Mean PLI: {analysis['pli_pairwise']['mean']:.3f}")

    return results

def main():
    """Run three-body coherence dynamics experiments"""

    print("=" * 70)
    print("Thor Session #76: Three-Body Coherence Dynamics")
    print("Extension of S74 (2-body) to N=3")
    print("=" * 70)

    # Experiment 1: Coupling strength sweep
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Coupling Strength Sweep")
    print("=" * 70)
    coupling_results = test_coupling_strengths()

    # Experiment 2: Initial condition sensitivity
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Initial Condition Sensitivity")
    print("=" * 70)
    initial_cond_results = test_initial_conditions()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # Check for emergent patterns
    print("\nKey findings:")
    print(f"1. Coupling strength threshold for sync: ", end="")
    sync_threshold = None
    for r in coupling_results:
        if r['analysis']['synchronization_state'] in ['FULL_SYNC', 'PARTIAL_SYNC']:
            sync_threshold = r['kappa']
            break
    print(f"κ ≥ {sync_threshold}" if sync_threshold else "Not achieved")

    print(f"2. Dominant phase pattern: ", end="")
    patterns = [r['analysis']['phase_pattern'] for r in coupling_results]
    from collections import Counter
    most_common = Counter(patterns).most_common(1)[0][0]
    print(most_common)

    print(f"3. Initial condition dependence: ", end="")
    final_patterns = [r['analysis']['phase_pattern'] for r in initial_cond_results]
    if len(set(final_patterns)) == 1:
        print(f"CONVERGES to {final_patterns[0]}")
    else:
        print(f"DEPENDENT (multiple attractors)")

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'session': 'Thor #76: Three-body coherence dynamics',
        'experiment_1_coupling_sweep': coupling_results,
        'experiment_2_initial_conditions': initial_cond_results,
        'summary': {
            'sync_threshold': sync_threshold,
            'dominant_pattern': most_common,
            'initial_condition_dependence': len(set(final_patterns)) > 1
        }
    }

    filename = 'thor_session_76_three_body_results.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {filename}")

    return output

if __name__ == '__main__':
    main()
