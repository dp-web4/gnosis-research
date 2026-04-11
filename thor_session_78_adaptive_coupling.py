#!/usr/bin/env python3
"""
Thor Session #78: Breaking the Coherence-Coordination Trade-off

Session #77 discovered the fundamental trade-off:
  - Attractive coupling → C≈0.57, R≈1 (coherent but uniform)
  - Repulsive coupling → C≈0.33, R≈0 (diverse but incoherent)

QUESTION: Can any coupling regime achieve BOTH C > 0.5 AND R < 0.5?
          i.e., collective coherence above the Gnosis boundary
          while maintaining phase diversity (coordination differentiation).

APPROACH: Five novel coupling regimes:

1. DECOUPLED: Independent κ_phase (repulsive) and κ_C (attractive)
   - S77 used same κ for both; decoupling may find a sweet spot

2. ADAPTIVE: Coupling sign flips based on collective coherence
   - C_collective < 0.5 → attractive (recover coherence)
   - C_collective > 0.5 → repulsive (gain diversity)
   - Metacognitive coupling: the collective monitors its own state

3. COHERENCE-GATED: Repulsive coupling only when individual C > threshold
   - Agents only "push away" when they can afford it
   - Low-C agents attract to recover

4. ASYMMETRIC: Hub-spoke topology
   - One "anchor" agent with strong attractive coupling
   - Others repulsively coupled to each other but attracted to anchor

5. FRUSTRATED: Random coupling signs (spin-glass-like)
   - Some pairs attract, others repel
   - Frustration creates non-trivial equilibria

Builds on: S70 (φ⁻¹ attractor), S74 (anti-phase), S77 (coupling regimes)
"""

import numpy as np
import json
from datetime import datetime
from itertools import combinations


# ─── Metrics ───

def compute_order_parameter(phases):
    """Kuramoto R: 1=in-phase, 0=uniformly distributed"""
    return float(np.abs(np.mean(np.exp(1j * np.array(phases)))))


def compute_pli(p1, p2):
    """Phase Locking Index"""
    return float(np.abs(np.mean(np.exp(1j * (np.array(p1) - np.array(p2))))))


def compute_phase_spacings(phases):
    """Sort phases and compute nearest-neighbor spacings (degrees)"""
    sorted_p = np.sort(np.array(phases) % (2 * np.pi))
    spacings = np.diff(sorted_p)
    spacings = np.append(spacings, 2 * np.pi - sorted_p[-1] + sorted_p[0])
    return spacings * 180 / np.pi


# ─── Extended N-Body System ───

class AdaptiveCoherenceSystem:
    """N-body coherence with novel coupling regimes."""

    def __init__(self, N, regime='decoupled',
                 kappa_phase=0.15, kappa_C=0.15,
                 omega_base=0.1, omega_spread=0.02,
                 phi_inverse=0.618, dt=0.1, noise_std=0.02,
                 C_threshold=0.5, frustration_seed=None,
                 seed=None):
        self.N = N
        self.regime = regime
        self.kappa_phase = kappa_phase
        self.kappa_C = kappa_C
        self.phi_inverse = phi_inverse
        self.dt = dt
        self.noise_std = noise_std
        self.C_threshold = C_threshold

        if seed is not None:
            np.random.seed(seed)

        self.C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
        self.phase = np.random.uniform(0, 2 * np.pi, N)
        self.omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

        # For frustrated regime: random coupling matrix
        if frustration_seed is not None:
            rng = np.random.RandomState(frustration_seed)
        else:
            rng = np.random.RandomState(seed if seed else 42)
        self.coupling_matrix = np.sign(rng.randn(N, N))
        np.fill_diagonal(self.coupling_matrix, 0)
        # Make symmetric
        self.coupling_matrix = np.triu(self.coupling_matrix) + np.triu(self.coupling_matrix).T

        # For asymmetric regime: agent 0 is the hub
        self.hub_idx = 0

        self.history_C = []
        self.history_phase = []
        self.history_order = []
        self.history_C_collective = []
        self.regime_switches = 0  # Track adaptive switches

    def phase_coupling(self, i, j, delta_theta):
        """Compute phase coupling term for agent i from agent j."""

        if self.regime == 'decoupled':
            # Repulsive phase coupling (independent strength from coherence coupling)
            return -self.kappa_phase * np.sin(delta_theta)

        elif self.regime == 'adaptive':
            # Metacognitive: coupling sign depends on collective coherence
            C_collective = float(np.mean(self.C))
            if C_collective < self.C_threshold:
                # Below Gnosis boundary → attract (recover coherence)
                return self.kappa_phase * np.sin(delta_theta)
            else:
                # Above Gnosis boundary → repel (gain diversity)
                return -self.kappa_phase * np.sin(delta_theta)

        elif self.regime == 'coherence_gated':
            # Only repel if YOUR coherence is high enough
            if self.C[i] > self.C_threshold:
                return -self.kappa_phase * np.sin(delta_theta)
            else:
                # Low-C agent: attract to recover
                return self.kappa_phase * np.sin(delta_theta)

        elif self.regime == 'asymmetric':
            # Hub-spoke: hub attracts all, others repel each other
            if i == self.hub_idx or j == self.hub_idx:
                return self.kappa_phase * np.sin(delta_theta)
            else:
                return -self.kappa_phase * np.sin(delta_theta)

        elif self.regime == 'frustrated':
            # Random coupling signs from pre-generated matrix
            sign = self.coupling_matrix[i, j]
            return sign * self.kappa_phase * np.sin(delta_theta)

        elif self.regime == 'attractive':
            return self.kappa_phase * np.sin(delta_theta)

        elif self.regime == 'repulsive':
            return -self.kappa_phase * np.sin(delta_theta)

        else:
            raise ValueError(f"Unknown regime: {self.regime}")

    def step(self):
        N = self.N
        R_func = lambda c: 1 - c**2

        # Track adaptive regime switches
        if self.regime == 'adaptive' and len(self.history_C_collective) > 0:
            C_prev = self.history_C_collective[-1]
            C_now = float(np.mean(self.C))
            if (C_prev < self.C_threshold) != (C_now < self.C_threshold):
                self.regime_switches += 1

        # Phase dynamics
        dphase = self.omega.copy()
        for i in range(N):
            for j in range(N):
                if i != j:
                    delta = self.phase[j] - self.phase[i]
                    dphase[i] += self.phase_coupling(i, j, delta) / (N - 1)

        self.phase += self.dt * dphase
        self.phase = self.phase % (2 * np.pi)

        # Coherence dynamics (always attractive/equalizing, using kappa_C)
        dC = np.zeros(N)
        for i in range(N):
            # Intrinsic dynamics: relax toward φ⁻¹
            dC[i] = -R_func(self.C[i]) * (self.C[i] - self.phi_inverse) * np.cos(self.phase[i])
            # Coherence coupling: always equalizing (attractive)
            c_coupling = np.sum(self.C - self.C[i]) / (N - 1)
            dC[i] += self.kappa_C * c_coupling * R_func(self.C[i])

        self.C += self.dt * dC
        self.C = np.clip(self.C, 0, 1)

        # Noise
        self.C += np.random.normal(0, self.noise_std, N)
        self.C = np.clip(self.C, 0, 1)
        self.phase += np.random.normal(0, self.noise_std, N)
        self.phase = self.phase % (2 * np.pi)

        # Record
        self.history_C.append(self.C.copy())
        self.history_phase.append(self.phase.copy())
        R = compute_order_parameter(self.phase)
        self.history_order.append(R)
        self.history_C_collective.append(float(np.mean(self.C)))

    def run(self, steps=10000):
        for _ in range(steps):
            self.step()


def analyze(system):
    """Analyze steady-state dynamics."""
    N = system.N
    T = len(system.history_phase)
    ss = T // 2  # Second half = steady state

    phases_ss = np.array(system.history_phase[ss:])
    C_ss = np.array(system.history_C[ss:])
    order_ss = np.array(system.history_order[ss:])
    C_coll_ss = np.array(system.history_C_collective[ss:])

    mean_R = float(np.mean(order_ss))
    std_R = float(np.std(order_ss))

    # Collective coherence
    C_collective = float(np.mean(C_coll_ss))
    C_temporal_std = float(np.std(C_coll_ss))

    # Individual coherences
    C_individual_means = [float(np.mean(C_ss[:, i])) for i in range(N)]
    C_individual_min = min(C_individual_means)

    # Pairwise correlations
    pairs = list(combinations(range(N), 2))
    C_corrs = []
    for i, j in pairs:
        r = np.corrcoef(C_ss[:, i], C_ss[:, j])[0, 1]
        if not np.isnan(r):
            C_corrs.append(float(r))
    mean_C_corr = float(np.mean(C_corrs)) if C_corrs else 0.0

    # Phase spacings
    spacings = compute_phase_spacings(system.phase)
    expected_spacing = 360.0 / N
    spacing_error = float(np.mean(np.abs(spacings - expected_spacing)))

    # PLI
    plis = [compute_pli(phases_ss[:, i], phases_ss[:, j]) for i, j in pairs]
    mean_pli = float(np.mean(plis))

    # THE KEY METRIC: Does this regime break the trade-off?
    above_gnosis = C_collective > 0.5
    has_diversity = mean_R < 0.5
    trade_off_broken = above_gnosis and has_diversity

    return {
        'N': N,
        'regime': system.regime,
        'kappa_phase': system.kappa_phase,
        'kappa_C': system.kappa_C,
        'mean_R': mean_R,
        'std_R': std_R,
        'mean_pli': mean_pli,
        'C_collective': C_collective,
        'C_temporal_std': C_temporal_std,
        'C_individual_means': C_individual_means,
        'C_individual_min': C_individual_min,
        'mean_C_corr': mean_C_corr,
        'spacing_error_deg': spacing_error,
        'regime_switches': system.regime_switches,
        'above_gnosis': above_gnosis,
        'has_diversity': has_diversity,
        'trade_off_broken': trade_off_broken,
    }


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 1: Decoupled Coupling Strength Sweep
# ═══════════════════════════════════════════════════════════

def experiment_1_decoupled_sweep():
    """
    Sweep κ_phase and κ_C independently.
    S77 used same κ=0.15 for both.
    Hypothesis: Strong coherence coupling + weak repulsive phase coupling
    could maintain C > 0.5 while allowing some diversity.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Decoupled Coupling Sweep (N=4)")
    print("κ_phase (repulsive) vs κ_C (coherence equalizing)")
    print("=" * 70)

    results = []
    N = 4

    kappa_phases = [0.01, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30]
    kappa_Cs = [0.05, 0.10, 0.15, 0.20, 0.30]

    print(f"\n{'κ_phase':>8} | {'κ_C':>5} | {'R':>5} | {'C_coll':>6} | {'C_corr':>6} | {'Break?':>6}")
    print("-" * 55)

    for kp in kappa_phases:
        for kc in kappa_Cs:
            seed_data = []
            for seed in range(5):
                system = AdaptiveCoherenceSystem(
                    N=N, regime='decoupled',
                    kappa_phase=kp, kappa_C=kc, seed=seed * 100 + N
                )
                system.run(steps=10000)
                seed_data.append(analyze(system))

            avg = {
                'kappa_phase': kp, 'kappa_C': kc,
                'mean_R': float(np.mean([r['mean_R'] for r in seed_data])),
                'C_collective': float(np.mean([r['C_collective'] for r in seed_data])),
                'mean_C_corr': float(np.mean([r['mean_C_corr'] for r in seed_data])),
            }
            avg['above_gnosis'] = avg['C_collective'] > 0.5
            avg['has_diversity'] = avg['mean_R'] < 0.5
            avg['trade_off_broken'] = avg['above_gnosis'] and avg['has_diversity']
            results.append(avg)

            marker = " ← BREAK!" if avg['trade_off_broken'] else ""
            print(f"  {kp:6.2f} | {kc:5.2f} | {avg['mean_R']:5.3f} | "
                  f"{avg['C_collective']:6.3f} | {avg['mean_C_corr']:+6.3f} | "
                  f"{'YES' if avg['trade_off_broken'] else 'no':>6}{marker}")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 2: Adaptive (Metacognitive) Coupling
# ═══════════════════════════════════════════════════════════

def experiment_2_adaptive():
    """
    The coupling sign flips based on collective coherence:
      C_collective < threshold → attractive (recover)
      C_collective > threshold → repulsive (diversify)

    This is the most cognitively motivated regime: the collective
    monitors its own coherence and adjusts its social strategy.

    Sweep: threshold values and coupling strengths.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Adaptive (Metacognitive) Coupling")
    print("Coupling sign flips at C_collective = threshold")
    print("=" * 70)

    results = []

    for N in [2, 3, 4, 6, 8]:
        print(f"\n--- N={N} ---")
        for threshold in [0.40, 0.45, 0.50, 0.55, 0.60]:
            for kp in [0.05, 0.10, 0.15]:
                seed_data = []
                for seed in range(5):
                    system = AdaptiveCoherenceSystem(
                        N=N, regime='adaptive',
                        kappa_phase=kp, kappa_C=0.15,
                        C_threshold=threshold,
                        seed=seed * 100 + N
                    )
                    system.run(steps=12000)
                    seed_data.append(analyze(system))

                avg_R = float(np.mean([r['mean_R'] for r in seed_data]))
                avg_C = float(np.mean([r['C_collective'] for r in seed_data]))
                avg_switches = float(np.mean([r['regime_switches'] for r in seed_data]))
                std_R = float(np.mean([r['std_R'] for r in seed_data]))

                entry = {
                    'N': N, 'threshold': threshold, 'kappa_phase': kp,
                    'mean_R': avg_R, 'std_R': std_R,
                    'C_collective': avg_C,
                    'regime_switches': avg_switches,
                    'trade_off_broken': avg_C > 0.5 and avg_R < 0.5,
                }
                results.append(entry)

                marker = " ← BREAK!" if entry['trade_off_broken'] else ""
                if kp == 0.10:  # Only print middle κ to save space
                    print(f"  thresh={threshold:.2f}, κ={kp:.2f}: "
                          f"R={avg_R:.3f}±{std_R:.3f}, C={avg_C:.3f}, "
                          f"switches={avg_switches:.0f}{marker}")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 3: Coherence-Gated Coupling
# ═══════════════════════════════════════════════════════════

def experiment_3_coherence_gated():
    """
    Each agent decides its coupling sign based on its OWN coherence:
      C_i > threshold → repulsive (can afford diversity)
      C_i < threshold → attractive (need to recover)

    This is agent-level metacognition, not collective.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Coherence-Gated Coupling")
    print("Individual agents switch coupling based on own C")
    print("=" * 70)

    results = []

    for N in [2, 4, 6, 8]:
        print(f"\n--- N={N} ---")
        for threshold in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
            seed_data = []
            for seed in range(5):
                system = AdaptiveCoherenceSystem(
                    N=N, regime='coherence_gated',
                    kappa_phase=0.15, kappa_C=0.15,
                    C_threshold=threshold,
                    seed=seed * 100 + N
                )
                system.run(steps=10000)
                seed_data.append(analyze(system))

            avg_R = float(np.mean([r['mean_R'] for r in seed_data]))
            avg_C = float(np.mean([r['C_collective'] for r in seed_data]))
            avg_Cmin = float(np.mean([r['C_individual_min'] for r in seed_data]))

            entry = {
                'N': N, 'threshold': threshold,
                'mean_R': avg_R, 'C_collective': avg_C,
                'C_individual_min': avg_Cmin,
                'trade_off_broken': avg_C > 0.5 and avg_R < 0.5,
            }
            results.append(entry)

            marker = " ← BREAK!" if entry['trade_off_broken'] else ""
            print(f"  thresh={threshold:.2f}: R={avg_R:.3f}, C={avg_C:.3f}, "
                  f"C_min={avg_Cmin:.3f}{marker}")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 4: Asymmetric (Hub-Spoke) Coupling
# ═══════════════════════════════════════════════════════════

def experiment_4_asymmetric():
    """
    Agent 0 is a "hub" with attractive coupling to all.
    All other agents repulsively coupled to each other.
    The hub stabilizes collective coherence while periphery diversifies.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Asymmetric Hub-Spoke Coupling")
    print("Hub (agent 0) attracts all; others repel each other")
    print("=" * 70)

    results = []

    for N in [3, 4, 5, 6, 8]:
        print(f"\n--- N={N} ---")
        seed_data = []
        for seed in range(8):
            system = AdaptiveCoherenceSystem(
                N=N, regime='asymmetric',
                kappa_phase=0.15, kappa_C=0.15,
                seed=seed * 100 + N
            )
            system.run(steps=10000)
            seed_data.append(analyze(system))

        avg_R = float(np.mean([r['mean_R'] for r in seed_data]))
        avg_C = float(np.mean([r['C_collective'] for r in seed_data]))
        avg_C_indiv = [float(np.mean([r['C_individual_means'][i] for r in seed_data]))
                       for i in range(N)]

        entry = {
            'N': N,
            'mean_R': avg_R, 'C_collective': avg_C,
            'C_individual_means': avg_C_indiv,
            'trade_off_broken': avg_C > 0.5 and avg_R < 0.5,
        }
        results.append(entry)

        marker = " ← BREAK!" if entry['trade_off_broken'] else ""
        hub_C = avg_C_indiv[0]
        periph_C = float(np.mean(avg_C_indiv[1:]))
        print(f"  R={avg_R:.3f}, C={avg_C:.3f}, hub_C={hub_C:.3f}, "
              f"periph_C={periph_C:.3f}{marker}")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 5: Frustrated (Spin-Glass) Coupling
# ═══════════════════════════════════════════════════════════

def experiment_5_frustrated():
    """
    Random coupling signs between pairs.
    Frustration prevents both full alignment AND full splay.
    May create non-trivial equilibria.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Frustrated (Spin-Glass) Coupling")
    print("Random coupling signs create frustrated equilibria")
    print("=" * 70)

    results = []

    for N in [3, 4, 5, 6, 8]:
        print(f"\n--- N={N} ---")
        seed_data = []
        for seed in range(10):
            system = AdaptiveCoherenceSystem(
                N=N, regime='frustrated',
                kappa_phase=0.15, kappa_C=0.15,
                frustration_seed=seed * 7 + N,
                seed=seed * 100 + N
            )
            system.run(steps=10000)
            seed_data.append(analyze(system))

        avg_R = float(np.mean([r['mean_R'] for r in seed_data]))
        std_R = float(np.std([r['mean_R'] for r in seed_data]))
        avg_C = float(np.mean([r['C_collective'] for r in seed_data]))
        std_C = float(np.std([r['C_collective'] for r in seed_data]))

        entry = {
            'N': N,
            'mean_R': avg_R, 'std_R': std_R,
            'C_collective': avg_C, 'C_collective_std': std_C,
            'trade_off_broken': avg_C > 0.5 and avg_R < 0.5,
        }
        results.append(entry)

        marker = " ← BREAK!" if entry['trade_off_broken'] else ""
        print(f"  R={avg_R:.3f}±{std_R:.3f}, C={avg_C:.3f}±{std_C:.3f}{marker}")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 6: Comprehensive Comparison
# ═══════════════════════════════════════════════════════════

def experiment_6_head_to_head(N=4):
    """
    Head-to-head comparison of ALL regimes at N=4.
    Use best parameters found from earlier experiments.
    """
    print("\n" + "=" * 70)
    print(f"EXPERIMENT 6: Head-to-Head Comparison (N={N})")
    print("All regimes with best parameters")
    print("=" * 70)

    configs = [
        {'regime': 'attractive', 'kappa_phase': 0.15, 'kappa_C': 0.15,
         'label': 'Attractive (S77 baseline)'},
        {'regime': 'repulsive', 'kappa_phase': 0.15, 'kappa_C': 0.15,
         'label': 'Repulsive (S77 baseline)'},
        {'regime': 'decoupled', 'kappa_phase': 0.05, 'kappa_C': 0.30,
         'label': 'Decoupled (weak repul + strong coh)'},
        {'regime': 'decoupled', 'kappa_phase': 0.03, 'kappa_C': 0.30,
         'label': 'Decoupled (very weak repul + strong coh)'},
        {'regime': 'adaptive', 'kappa_phase': 0.10, 'kappa_C': 0.15,
         'C_threshold': 0.50, 'label': 'Adaptive (threshold=0.50)'},
        {'regime': 'adaptive', 'kappa_phase': 0.10, 'kappa_C': 0.15,
         'C_threshold': 0.55, 'label': 'Adaptive (threshold=0.55)'},
        {'regime': 'coherence_gated', 'kappa_phase': 0.15, 'kappa_C': 0.15,
         'C_threshold': 0.55, 'label': 'Coherence-gated (thresh=0.55)'},
        {'regime': 'coherence_gated', 'kappa_phase': 0.15, 'kappa_C': 0.15,
         'C_threshold': 0.60, 'label': 'Coherence-gated (thresh=0.60)'},
        {'regime': 'asymmetric', 'kappa_phase': 0.15, 'kappa_C': 0.15,
         'label': 'Asymmetric hub-spoke'},
        {'regime': 'frustrated', 'kappa_phase': 0.15, 'kappa_C': 0.15,
         'label': 'Frustrated (random signs)'},
    ]

    results = []

    print(f"\n{'Regime':<40} | {'R':>5} | {'C':>5} | {'C>0.5':>5} | {'R<0.5':>5} | {'BREAK':>5}")
    print("-" * 80)

    for cfg in configs:
        seed_data = []
        for seed in range(8):
            kwargs = {
                'N': N, 'regime': cfg['regime'],
                'kappa_phase': cfg['kappa_phase'],
                'kappa_C': cfg['kappa_C'],
                'seed': seed * 100 + N,
            }
            if 'C_threshold' in cfg:
                kwargs['C_threshold'] = cfg['C_threshold']
            if cfg['regime'] == 'frustrated':
                kwargs['frustration_seed'] = seed * 7 + N

            system = AdaptiveCoherenceSystem(**kwargs)
            system.run(steps=12000)
            seed_data.append(analyze(system))

        avg_R = float(np.mean([r['mean_R'] for r in seed_data]))
        avg_C = float(np.mean([r['C_collective'] for r in seed_data]))
        above = avg_C > 0.5
        diverse = avg_R < 0.5
        broken = above and diverse

        entry = {
            'label': cfg['label'],
            'regime': cfg['regime'],
            'mean_R': avg_R,
            'C_collective': avg_C,
            'above_gnosis': above,
            'has_diversity': diverse,
            'trade_off_broken': broken,
        }
        results.append(entry)

        marker = " <<<" if broken else ""
        print(f"  {cfg['label']:<38} | {avg_R:5.3f} | {avg_C:5.3f} | "
              f"{'YES' if above else 'no':>5} | {'YES' if diverse else 'no':>5} | "
              f"{'YES' if broken else 'no':>5}{marker}")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 7: Time-Series of Adaptive Regime
# ═══════════════════════════════════════════════════════════

def experiment_7_adaptive_dynamics():
    """
    Detailed time-series analysis of the adaptive regime.
    How does the system oscillate between attract/repel modes?
    Does it settle or keep oscillating? What's the characteristic period?
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 7: Adaptive Coupling Dynamics (Time-Series)")
    print("=" * 70)

    N = 4
    system = AdaptiveCoherenceSystem(
        N=N, regime='adaptive',
        kappa_phase=0.10, kappa_C=0.15,
        C_threshold=0.55,
        seed=42
    )
    system.run(steps=20000)

    C_coll = np.array(system.history_C_collective)
    R_hist = np.array(system.history_order)

    # Identify regime transitions
    above = C_coll > system.C_threshold
    transitions = np.where(np.diff(above.astype(int)) != 0)[0]

    print(f"\n  Total steps: {len(C_coll)}")
    print(f"  Regime transitions: {len(transitions)}")
    print(f"  Mean C_collective: {np.mean(C_coll):.4f}")
    print(f"  Mean R: {np.mean(R_hist):.4f}")

    if len(transitions) > 2:
        intervals = np.diff(transitions)
        print(f"  Mean inter-transition interval: {np.mean(intervals):.1f} steps")
        print(f"  Std inter-transition interval: {np.std(intervals):.1f} steps")

        # Time in each regime
        attract_time = np.sum(~above) / len(above)
        repel_time = np.sum(above) / len(above)
        print(f"  Time in attractive mode: {attract_time*100:.1f}%")
        print(f"  Time in repulsive mode: {repel_time*100:.1f}%")

    # Phase diversity over time (windowed)
    window = 500
    windowed_R = [float(np.mean(R_hist[max(0, i-window):i])) for i in range(window, len(R_hist), window)]
    windowed_C = [float(np.mean(C_coll[max(0, i-window):i])) for i in range(window, len(C_coll), window)]

    print(f"\n  Windowed analysis ({window}-step windows):")
    print(f"  {'Window':>6} | {'R':>5} | {'C':>5} | {'Mode':>10}")
    print("  " + "-" * 35)
    for idx, (wr, wc) in enumerate(zip(windowed_R, windowed_C)):
        mode = "attract" if wc < system.C_threshold else "repel"
        print(f"  {idx*window:6d} | {wr:5.3f} | {wc:5.3f} | {mode:>10}")

    return {
        'transitions': len(transitions),
        'mean_C': float(np.mean(C_coll)),
        'mean_R': float(np.mean(R_hist)),
        'windowed_R': windowed_R,
        'windowed_C': windowed_C,
    }


# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Thor Session #78: Breaking the Coherence-Coordination Trade-off")
    print("Can any coupling regime achieve BOTH C > 0.5 AND R < 0.5?")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")

    exp1 = experiment_1_decoupled_sweep()
    exp2 = experiment_2_adaptive()
    exp3 = experiment_3_coherence_gated()
    exp4 = experiment_4_asymmetric()
    exp5 = experiment_5_frustrated()
    exp6 = experiment_6_head_to_head()
    exp7 = experiment_7_adaptive_dynamics()

    # ── Grand Summary ──
    print("\n" + "=" * 70)
    print("GRAND SUMMARY: Can the Trade-off Be Broken?")
    print("=" * 70)

    # Count which regimes broke it
    all_results = {
        'exp1_decoupled': exp1,
        'exp2_adaptive': exp2,
        'exp3_coherence_gated': exp3,
        'exp4_asymmetric': exp4,
        'exp5_frustrated': exp5,
        'exp6_head_to_head': exp6,
        'exp7_adaptive_dynamics': exp7,
    }

    breaks_found = []
    for exp_name, results in all_results.items():
        if isinstance(results, list):
            for r in results:
                if isinstance(r, dict) and r.get('trade_off_broken'):
                    breaks_found.append((exp_name, r))

    if breaks_found:
        print(f"\n  TRADE-OFF BROKEN in {len(breaks_found)} configurations!")
        for exp_name, r in breaks_found:
            label = r.get('label', r.get('regime', '?'))
            print(f"    {exp_name}: {label} → R={r['mean_R']:.3f}, C={r['C_collective']:.3f}")
    else:
        print("\n  TRADE-OFF NOT BROKEN in any configuration tested.")
        print("  The coherence-coordination trade-off appears fundamental.")

    # Phase diagram summary from head-to-head
    print("\n  HEAD-TO-HEAD (N=4):")
    print(f"  {'Regime':<35} | {'R':>5} | {'C':>5} | {'Verdict':>10}")
    print("  " + "-" * 65)
    for r in exp6:
        verdict = "BREAK" if r['trade_off_broken'] else ("C>0.5" if r['above_gnosis'] else "diverse")
        print(f"  {r['label']:<35} | {r['mean_R']:5.3f} | {r['C_collective']:5.3f} | {verdict:>10}")

    # Save
    output = {
        'timestamp': datetime.now().isoformat(),
        'session': 'Thor #78: Breaking the Coherence-Coordination Trade-off',
        'question': 'Can any coupling regime achieve C > 0.5 AND R < 0.5?',
        'breaks_found': len(breaks_found),
        'results': {
            'exp1_decoupled_sweep': exp1,
            'exp2_adaptive': exp2,
            'exp3_coherence_gated': exp3,
            'exp4_asymmetric': exp4,
            'exp5_frustrated': exp5,
            'exp6_head_to_head': exp6,
            'exp7_adaptive_dynamics': exp7,
        }
    }

    filename = 'thor_session_78_adaptive_coupling_results.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nResults saved to {filename}")
    return output


if __name__ == '__main__':
    main()
