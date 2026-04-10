#!/usr/bin/env python3
"""
Thor Session #77: N-Body Coherence Scaling Law
Extension of S74 (N=2) and S76 (N=3) to N=2..10

Research questions:
1. Does the 2π/N maximum symmetry prediction hold for N=4,5,6...?
2. At what critical N does synchronization degrade?
3. Do chimera states (partial sync) emerge at larger N?
4. How does collective coherence scale with group size?

Hypothesis: Phase spacing follows 2π/N for small N, but metabolic
constraints create critical N_c beyond which full sync breaks down.

Builds on:
- S70: φ⁻¹ universal attractor
- S73: Coherence IS phase (oscillatory dynamics)
- S74: N=2 → anti-phase (π) locking, PLI jump at κ>0
- S75: Transfer rule validated for coherence
- S76: N=3 → 120° balanced triad, robust attractor
"""

import numpy as np
import json
from datetime import datetime
from itertools import combinations
from collections import Counter


# ─── Core Model ───────────────────────────────────────────────────────────────

class NBodyCoherenceSystem:
    """N coupled coherence oscillators with Kuramoto-style coupling.

    Generalization of S76's ThreeBodyCoherenceSystem to arbitrary N.
    """

    def __init__(self, N, kappa=0.15, omega_base=0.1, omega_spread=0.02,
                 phi_inverse=0.618, dt=0.1, noise_std=0.02,
                 initial_phases=None, seed=None):
        self.N = N
        self.kappa = kappa
        self.phi_inverse = phi_inverse
        self.dt = dt
        self.noise_std = noise_std

        if seed is not None:
            np.random.seed(seed)

        # Initialize agents
        self.C = np.array([phi_inverse + np.random.normal(0, 0.05) for _ in range(N)])
        self.C = np.clip(self.C, 0.01, 0.99)

        if initial_phases is not None:
            self.phase = np.array(initial_phases, dtype=float)
        else:
            self.phase = np.random.uniform(0, 2 * np.pi, N)

        self.omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

        # History storage (store every step for analysis)
        self.history_C = []
        self.history_phase = []
        self.history_order = []

    def R(self, C):
        """Saturation function: R(C) = 1 - C^2"""
        return 1 - C**2

    def step(self):
        """Single time step: Kuramoto phase + coherence dynamics + noise"""
        N = self.N

        # ── Phase dynamics (Kuramoto all-to-all) ──
        # dθ_i/dt = ω_i + (κ/N) Σ_j sin(θ_j - θ_i)
        # Note: normalize coupling by N to keep effective strength comparable
        dphase = self.omega.copy()
        for i in range(N):
            coupling = np.sum(np.sin(self.phase - self.phase[i]))
            # Normalize by (N-1) so coupling per-agent stays constant as N grows
            dphase[i] += self.kappa * coupling / (N - 1)

        self.phase += self.dt * dphase
        self.phase = self.phase % (2 * np.pi)

        # ── Coherence dynamics ──
        # dC_i/dt = -R(C_i)(C_i - φ⁻¹)cos(θ_i) + κ Σ_j (C_j - C_i)R(C_i) / (N-1)
        dC = np.zeros(N)
        for i in range(N):
            # Attractor term (S70: φ⁻¹ universal attractor)
            dC[i] = -self.R(self.C[i]) * (self.C[i] - self.phi_inverse) * np.cos(self.phase[i])
            # Coupling term (S75: transfer rule)
            coupling = np.sum(self.C - self.C[i])
            dC[i] += self.kappa * coupling * self.R(self.C[i]) / (N - 1)

        self.C += self.dt * dC
        self.C = np.clip(self.C, 0, 1)

        # ── Noise (learning episodes, S71-72) ──
        self.C += np.random.normal(0, self.noise_std, N)
        self.C = np.clip(self.C, 0, 1)
        self.phase += np.random.normal(0, self.noise_std, N)
        self.phase = self.phase % (2 * np.pi)

        # ── Record ──
        self.history_C.append(self.C.copy())
        self.history_phase.append(self.phase.copy())
        # Kuramoto order parameter
        R = np.abs(np.mean(np.exp(1j * self.phase)))
        self.history_order.append(R)

    def run(self, steps=5000):
        for _ in range(steps):
            self.step()


# ─── Analysis Functions ───────────────────────────────────────────────────────

def compute_pli(phase1, phase2):
    """Phase Locking Index between two phase series"""
    diff = np.array(phase1) - np.array(phase2)
    return float(np.abs(np.mean(np.exp(1j * diff))))


def circular_mean(angles):
    """Circular mean of angles in radians"""
    return float(np.angle(np.mean(np.exp(1j * np.array(angles)))) % (2 * np.pi))


def circular_distance(a, b):
    """Minimum angular distance between two angles (0 to π)"""
    d = abs(a - b) % (2 * np.pi)
    return min(d, 2 * np.pi - d)


def analyze_system(system, steady_fraction=0.5):
    """Comprehensive analysis of N-body coherence dynamics"""
    N = system.N
    T = len(system.history_phase)
    steady_start = int(T * steady_fraction)

    phases_steady = np.array(system.history_phase[steady_start:])  # (T', N)
    C_steady = np.array(system.history_C[steady_start:])  # (T', N)
    order_steady = np.array(system.history_order[steady_start:])

    # ── Pairwise PLI ──
    pairs = list(combinations(range(N), 2))
    pli_values = {}
    for i, j in pairs:
        pli_values[f"{i}-{j}"] = compute_pli(phases_steady[:, i], phases_steady[:, j])

    mean_pli = float(np.mean(list(pli_values.values())))

    # ── Kuramoto order parameter ──
    mean_order = float(np.mean(order_steady))
    std_order = float(np.std(order_steady))

    # ── Phase differences (steady-state mean) ──
    # For each pair, compute mean phase difference
    phase_diffs_rad = {}
    for i, j in pairs:
        diffs = (phases_steady[:, i] - phases_steady[:, j]) % (2 * np.pi)
        phase_diffs_rad[f"{i}-{j}"] = circular_mean(diffs)

    phase_diffs_deg = {k: float(v * 180 / np.pi) for k, v in phase_diffs_rad.items()}

    # ── Phase pattern classification ──
    # Test if phase differences match 2π/N pattern
    all_diffs_deg = list(phase_diffs_deg.values())

    # Expected spacing for uniform distribution: multiples of 360/N
    expected_spacing = 360.0 / N

    # Check if each pairwise diff is close to a multiple of expected_spacing
    match_count = 0
    for d in all_diffs_deg:
        # Find closest multiple of expected_spacing
        for k in range(1, N):
            target = k * expected_spacing
            if circular_distance(d * np.pi / 180, target * np.pi / 180) < 30 * np.pi / 180:
                match_count += 1
                break

    total_pairs = len(pairs)
    symmetry_ratio = match_count / total_pairs if total_pairs > 0 else 0

    if symmetry_ratio > 0.7:
        phase_pattern = f"SYMMETRIC ({int(expected_spacing)}° spacing)"
    elif mean_order > 0.9:
        # High order but not symmetric spacing → check for cluster patterns
        phase_pattern = "CLUSTERED"
    elif mean_order > 0.5:
        phase_pattern = "PARTIAL_SYNC"
    else:
        phase_pattern = "INCOHERENT"

    # ── Check for in-phase specifically ──
    if all(abs(d) < 20 or abs(d - 360) < 20 for d in all_diffs_deg):
        phase_pattern = "IN_PHASE"

    # ── Coherence statistics ──
    C_individual_means = [float(np.mean(C_steady[:, i])) for i in range(N)]
    C_collective_mean = float(np.mean(C_steady))
    C_collective_std = float(np.std(np.mean(C_steady, axis=1)))

    # ── Synchronization state ──
    if mean_order > 0.7:
        sync_state = "FULL_SYNC"
    elif mean_order > 0.4:
        sync_state = "PARTIAL_SYNC"
    else:
        sync_state = "INCOHERENT"

    # ── Chimera detection ──
    # Check if some agents are synchronized while others aren't
    # Compute per-agent "sync participation": how well each agent syncs with the group
    agent_sync = []
    for i in range(N):
        # Mean PLI of agent i with all others
        agent_plis = [pli_values[f"{min(i,j)}-{max(i,j)}"] for j in range(N) if j != i]
        agent_sync.append(float(np.mean(agent_plis)))

    sync_spread = float(np.max(agent_sync) - np.min(agent_sync))
    is_chimera = sync_spread > 0.3 and mean_order < 0.9 and mean_order > 0.3

    # ── Nearest-neighbor phase spacing ──
    # Sort final phases and compute spacings
    final_phases = phases_steady[-1]
    sorted_phases = np.sort(final_phases)
    spacings = np.diff(sorted_phases)
    # Include wrap-around
    spacings = np.append(spacings, (2 * np.pi - sorted_phases[-1] + sorted_phases[0]))
    spacing_std = float(np.std(spacings))
    spacing_mean = float(np.mean(spacings))
    # Uniformity measure: how close to 2π/N is the mean spacing?
    spacing_uniformity = 1.0 - abs(spacing_mean - 2 * np.pi / N) / (np.pi / N) if N > 1 else 1.0
    spacing_uniformity = max(0, min(1, spacing_uniformity))

    return {
        'N': N,
        'kappa': system.kappa,
        'mean_pli': mean_pli,
        'mean_order': mean_order,
        'std_order': std_order,
        'sync_state': sync_state,
        'phase_pattern': phase_pattern,
        'symmetry_ratio': float(symmetry_ratio),
        'expected_spacing_deg': float(expected_spacing),
        'phase_diffs_deg': phase_diffs_deg,
        'C_individual_means': C_individual_means,
        'C_collective_mean': C_collective_mean,
        'C_collective_std': C_collective_std,
        'agent_sync_participation': agent_sync,
        'sync_spread': sync_spread,
        'is_chimera': is_chimera,
        'spacing_uniformity': float(spacing_uniformity),
        'spacing_std': float(spacing_std),
        'natural_frequencies': [float(w) for w in system.omega],
    }


# ─── Experiments ──────────────────────────────────────────────────────────────

def experiment_1_n_scaling(kappa=0.15, n_seeds=5, steps=5000):
    """
    Experiment 1: N-scaling at fixed coupling strength.
    Test N=2..10, multiple seeds for statistical reliability.

    Key predictions:
    - N=4 → 90° (π/2) spacing
    - N=5 → 72° (2π/5) spacing
    - Pattern: 2π/N phase spacing (maximum symmetry)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: N-Body Scaling (N=2..10)")
    print(f"κ={kappa}, {n_seeds} seeds per N, {steps} steps")
    print("=" * 70)

    results = {}

    for N in range(2, 11):
        print(f"\n--- N={N} ---")
        seed_results = []

        for seed in range(n_seeds):
            system = NBodyCoherenceSystem(N=N, kappa=kappa, seed=seed * 100 + N)
            system.run(steps=steps)
            analysis = analyze_system(system)
            seed_results.append(analysis)

            print(f"  seed={seed}: R={analysis['mean_order']:.3f}, "
                  f"PLI={analysis['mean_pli']:.3f}, "
                  f"pattern={analysis['phase_pattern']}, "
                  f"chimera={analysis['is_chimera']}")

        # Aggregate across seeds
        mean_R = np.mean([r['mean_order'] for r in seed_results])
        std_R = np.std([r['mean_order'] for r in seed_results])
        mean_pli = np.mean([r['mean_pli'] for r in seed_results])
        std_pli = np.std([r['mean_pli'] for r in seed_results])
        mean_C = np.mean([r['C_collective_mean'] for r in seed_results])
        mean_uniformity = np.mean([r['spacing_uniformity'] for r in seed_results])
        chimera_count = sum(1 for r in seed_results if r['is_chimera'])

        patterns = [r['phase_pattern'] for r in seed_results]
        dominant_pattern = Counter(patterns).most_common(1)[0][0]

        results[N] = {
            'mean_order': float(mean_R),
            'std_order': float(std_R),
            'mean_pli': float(mean_pli),
            'std_pli': float(std_pli),
            'C_collective_mean': float(mean_C),
            'spacing_uniformity': float(mean_uniformity),
            'chimera_fraction': chimera_count / n_seeds,
            'dominant_pattern': dominant_pattern,
            'pattern_distribution': dict(Counter(patterns)),
            'expected_spacing_deg': 360.0 / N,
            'seed_results': seed_results,
        }

        print(f"  AGGREGATE: R={mean_R:.3f}±{std_R:.3f}, "
              f"PLI={mean_pli:.3f}±{std_pli:.3f}, "
              f"C={mean_C:.3f}, uniformity={mean_uniformity:.3f}, "
              f"chimeras={chimera_count}/{n_seeds}")

    return results


def experiment_2_coupling_vs_n(n_values=[3, 5, 7, 10], steps=5000):
    """
    Experiment 2: Coupling strength × N interaction.
    Does the critical coupling depend on N?

    Theory: As N grows, each agent has more coupling partners,
    but coupling per partner is normalized by (N-1).
    Question: Does total coupling compensate, or does sync weaken?
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Coupling Strength × N Interaction")
    print("=" * 70)

    kappa_values = [0.01, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50]
    results = {}

    for N in n_values:
        results[N] = []
        print(f"\n--- N={N} ---")

        for kappa in kappa_values:
            system = NBodyCoherenceSystem(N=N, kappa=kappa, seed=42 + N * 100)
            system.run(steps=steps)
            analysis = analyze_system(system)

            results[N].append({
                'kappa': kappa,
                'mean_order': analysis['mean_order'],
                'mean_pli': analysis['mean_pli'],
                'sync_state': analysis['sync_state'],
                'phase_pattern': analysis['phase_pattern'],
                'C_collective_mean': analysis['C_collective_mean'],
            })

            print(f"  κ={kappa:.2f}: R={analysis['mean_order']:.3f}, "
                  f"PLI={analysis['mean_pli']:.3f}, "
                  f"sync={analysis['sync_state']}")

    return results


def experiment_3_chimera_search(steps=8000):
    """
    Experiment 3: Deliberate chimera state search.
    Initialize N=6 with 3 agents pre-synchronized and 3 random.
    Does the split persist, or does one pattern dominate?

    Also test N=8 with two groups of 4 at different frequencies.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Chimera State Search")
    print("=" * 70)

    results = []

    # ── Test 3a: N=6, split initialization ──
    print("\n--- 3a: N=6, split init (3 synced + 3 random) ---")
    for trial in range(5):
        np.random.seed(trial * 77)
        # First 3 agents: 120° pattern (known attractor from S76)
        # Last 3 agents: random phases
        init_phases = [0, 2*np.pi/3, 4*np.pi/3,
                       np.random.uniform(0, 2*np.pi),
                       np.random.uniform(0, 2*np.pi),
                       np.random.uniform(0, 2*np.pi)]

        system = NBodyCoherenceSystem(N=6, kappa=0.15, initial_phases=init_phases,
                                      seed=None)  # seed already set
        system.run(steps=steps)
        analysis = analyze_system(system)

        # Check if group structure persists
        group1_plis = [compute_pli(
            np.array(system.history_phase[steps//2:])[:, i],
            np.array(system.history_phase[steps//2:])[:, j]
        ) for i, j in combinations(range(3), 2)]

        group2_plis = [compute_pli(
            np.array(system.history_phase[steps//2:])[:, i],
            np.array(system.history_phase[steps//2:])[:, j]
        ) for i, j in combinations(range(3, 6), 2)]

        cross_plis = [compute_pli(
            np.array(system.history_phase[steps//2:])[:, i],
            np.array(system.history_phase[steps//2:])[:, j]
        ) for i in range(3) for j in range(3, 6)]

        result = {
            'trial': trial,
            'group1_mean_pli': float(np.mean(group1_plis)),
            'group2_mean_pli': float(np.mean(group2_plis)),
            'cross_group_mean_pli': float(np.mean(cross_plis)),
            'overall_order': analysis['mean_order'],
            'is_chimera': analysis['is_chimera'],
            'phase_pattern': analysis['phase_pattern'],
            'sync_spread': analysis['sync_spread'],
        }
        results.append({'test': '3a_split_init', **result})

        print(f"  trial={trial}: R={analysis['mean_order']:.3f}, "
              f"G1_PLI={np.mean(group1_plis):.3f}, "
              f"G2_PLI={np.mean(group2_plis):.3f}, "
              f"cross={np.mean(cross_plis):.3f}, "
              f"chimera={analysis['is_chimera']}")

    # ── Test 3b: N=8, frequency heterogeneity ──
    print("\n--- 3b: N=8, frequency heterogeneity ---")
    for spread in [0.02, 0.05, 0.10, 0.20]:
        system = NBodyCoherenceSystem(N=8, kappa=0.15, omega_spread=spread, seed=42)
        system.run(steps=steps)
        analysis = analyze_system(system)

        result = {
            'omega_spread': spread,
            'mean_order': analysis['mean_order'],
            'mean_pli': analysis['mean_pli'],
            'sync_state': analysis['sync_state'],
            'is_chimera': analysis['is_chimera'],
            'sync_spread': analysis['sync_spread'],
            'phase_pattern': analysis['phase_pattern'],
        }
        results.append({'test': '3b_freq_hetero', **result})

        print(f"  spread={spread:.2f}: R={analysis['mean_order']:.3f}, "
              f"PLI={analysis['mean_pli']:.3f}, "
              f"chimera={analysis['is_chimera']}, "
              f"sync_spread={analysis['sync_spread']:.3f}")

    # ── Test 3c: N=10, weak coupling (near transition) ──
    print("\n--- 3c: N=10, varying coupling near critical ---")
    for kappa in [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]:
        system = NBodyCoherenceSystem(N=10, kappa=kappa, seed=42)
        system.run(steps=steps)
        analysis = analyze_system(system)

        result = {
            'kappa': kappa,
            'mean_order': analysis['mean_order'],
            'mean_pli': analysis['mean_pli'],
            'sync_state': analysis['sync_state'],
            'is_chimera': analysis['is_chimera'],
            'sync_spread': analysis['sync_spread'],
            'agent_sync': analysis['agent_sync_participation'],
        }
        results.append({'test': '3c_n10_critical', **result})

        print(f"  κ={kappa:.2f}: R={analysis['mean_order']:.3f}, "
              f"PLI={analysis['mean_pli']:.3f}, "
              f"chimera={analysis['is_chimera']}, "
              f"spread={analysis['sync_spread']:.3f}")

    return results


def experiment_4_collective_coherence_scaling(kappa=0.15, steps=5000):
    """
    Experiment 4: How does collective coherence scale with N?

    S76 found C_collective ≈ 0.53 for N=3 (below φ⁻¹=0.618).
    Hypothesis: As N grows, C_collective → C_attractor because
    phase offsets average out temporal fluctuations.

    Alternative: C_collective decreases with N (resource dilution).
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Collective Coherence vs. N")
    print("=" * 70)

    results = []

    for N in range(2, 16):
        seed_Cs = []
        for seed in range(5):
            system = NBodyCoherenceSystem(N=N, kappa=kappa, seed=seed * 50 + N)
            system.run(steps=steps)
            C_steady = np.array(system.history_C[steps//2:])
            C_collective = float(np.mean(C_steady))
            C_individual_mean = float(np.mean([np.mean(C_steady[:, i]) for i in range(N)]))
            C_std_across_agents = float(np.std([np.mean(C_steady[:, i]) for i in range(N)]))
            # Temporal stability: how stable is collective C over time?
            C_temporal_std = float(np.std(np.mean(C_steady, axis=1)))
            seed_Cs.append({
                'C_collective': C_collective,
                'C_individual_mean': C_individual_mean,
                'C_std_across': C_std_across_agents,
                'C_temporal_std': C_temporal_std,
            })

        mean_C = np.mean([r['C_collective'] for r in seed_Cs])
        std_C = np.std([r['C_collective'] for r in seed_Cs])
        mean_temporal_std = np.mean([r['C_temporal_std'] for r in seed_Cs])

        results.append({
            'N': N,
            'C_collective_mean': float(mean_C),
            'C_collective_std': float(std_C),
            'C_temporal_std': float(mean_temporal_std),
            'C_individual_mean': float(np.mean([r['C_individual_mean'] for r in seed_Cs])),
        })

        print(f"  N={N:2d}: C_collective={mean_C:.4f}±{std_C:.4f}, "
              f"temporal_std={mean_temporal_std:.4f}")

    return results


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Thor Session #77: N-Body Coherence Scaling Law")
    print("From Dyads to Collectives (N=2..10+)")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Run all experiments
    exp1 = experiment_1_n_scaling(kappa=0.15, n_seeds=5, steps=5000)
    exp2 = experiment_2_coupling_vs_n(n_values=[3, 5, 7, 10], steps=5000)
    exp3 = experiment_3_chimera_search(steps=8000)
    exp4 = experiment_4_collective_coherence_scaling(kappa=0.15, steps=5000)

    # ── Summary Table ──
    print("\n" + "=" * 70)
    print("SUMMARY: N-Body Scaling Law")
    print("=" * 70)
    print(f"{'N':>3} | {'R (order)':>12} | {'PLI':>12} | {'C_coll':>8} | {'Uniformity':>10} | {'Chimeras':>8} | {'Pattern':>20}")
    print("-" * 90)
    for N in sorted(exp1.keys()):
        r = exp1[N]
        print(f"{N:3d} | {r['mean_order']:.3f}±{r['std_order']:.3f} | "
              f"{r['mean_pli']:.3f}±{r['std_pli']:.3f} | "
              f"{r['C_collective_mean']:.3f}    | "
              f"{r['spacing_uniformity']:.3f}      | "
              f"{r['chimera_fraction']:.1f}      | "
              f"{r['dominant_pattern']}")

    # ── Test 2π/N hypothesis ──
    print("\n" + "=" * 70)
    print("HYPOTHESIS TEST: 2π/N Maximum Symmetry")
    print("=" * 70)
    for N in sorted(exp1.keys()):
        r = exp1[N]
        expected = 360.0 / N
        uniformity = r['spacing_uniformity']
        verdict = "CONFIRMED" if uniformity > 0.7 else ("PARTIAL" if uniformity > 0.4 else "REJECTED")
        print(f"  N={N}: expected {expected:.0f}° spacing, "
              f"uniformity={uniformity:.3f} → {verdict}")

    # ── Critical N analysis ──
    print("\n" + "=" * 70)
    print("CRITICAL N ANALYSIS")
    print("=" * 70)
    for N in sorted(exp1.keys()):
        r = exp1[N]
        if r['mean_order'] < 0.5:
            print(f"  *** Synchronization breakdown at N={N} (R={r['mean_order']:.3f}) ***")
            break
    else:
        print(f"  Full synchronization maintained through N=10 (min R = "
              f"{min(r['mean_order'] for r in exp1.values()):.3f})")

    # ── Collective coherence scaling ──
    print("\n" + "=" * 70)
    print("COLLECTIVE COHERENCE SCALING")
    print("=" * 70)
    for r in exp4:
        marker = " ← φ⁻¹" if abs(r['C_collective_mean'] - 0.618) < 0.02 else ""
        print(f"  N={r['N']:2d}: C={r['C_collective_mean']:.4f} ± {r['C_collective_std']:.4f}, "
              f"temporal_std={r['C_temporal_std']:.4f}{marker}")

    # ── Save results ──
    output = {
        'timestamp': datetime.now().isoformat(),
        'session': 'Thor #77: N-Body Coherence Scaling Law',
        'experiment_1_n_scaling': {str(k): {kk: vv for kk, vv in v.items() if kk != 'seed_results'}
                                   for k, v in exp1.items()},
        'experiment_2_coupling_x_n': {str(k): v for k, v in exp2.items()},
        'experiment_3_chimera_search': exp3,
        'experiment_4_collective_coherence': exp4,
    }

    filename = 'thor_session_77_n_body_results.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {filename}")
    return output


if __name__ == '__main__':
    main()
