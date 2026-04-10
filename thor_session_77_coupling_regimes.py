#!/usr/bin/env python3
"""
Thor Session #77: Coupling Regime Discovery

Critical finding: S76's "120° balanced triad" was misclassified.
Standard Kuramoto (positive coupling) → in-phase for ALL N.
Anti-Kuramoto (negative coupling) → 2π/N splay state.

This experiment tests THREE coupling regimes:
1. ATTRACTIVE (standard Kuramoto): κ sin(Δθ) → in-phase
2. REPULSIVE (anti-Kuramoto): -κ sin(Δθ) → splay state (2π/N)
3. RESOURCE-COMPETITIVE: coupling sign depends on phase proximity
   - Nearby phases → repulsive (resource competition)
   - Distant phases → attractive (cooperation benefit)
   This is analogous to Lennard-Jones potential

Key question: Which regime matches S74's empirical observations?
S74 found: anti-correlation r = -0.83 to -0.97 (anti-phase behavior)
→ Predicts: REPULSIVE or RESOURCE-COMPETITIVE coupling

Builds on: S70 (φ⁻¹ attractor), S73 (phase dynamics), S74 (anti-phase),
           S75 (transfer rule), S76 (three-body)
"""

import numpy as np
import json
from datetime import datetime
from itertools import combinations


def compute_order_parameter(phases):
    """Kuramoto R: 1=in-phase, 0=uniformly distributed"""
    return float(np.abs(np.mean(np.exp(1j * np.array(phases)))))


def compute_pli(p1, p2):
    """Phase Locking Index"""
    return float(np.abs(np.mean(np.exp(1j * (np.array(p1) - np.array(p2))))))


def circular_mean_diff(phase_series_i, phase_series_j):
    """Mean phase difference (circular, in degrees)"""
    d = (np.array(phase_series_i) - np.array(phase_series_j)) % (2 * np.pi)
    mean_rad = float(np.angle(np.mean(np.exp(1j * d))) % (2 * np.pi))
    return mean_rad * 180 / np.pi


def compute_phase_spacings(phases):
    """Sort phases and compute nearest-neighbor spacings (degrees)"""
    sorted_p = np.sort(np.array(phases) % (2 * np.pi))
    spacings = np.diff(sorted_p)
    spacings = np.append(spacings, 2 * np.pi - sorted_p[-1] + sorted_p[0])
    return spacings * 180 / np.pi


class NBodyCoherence:
    """N-body coherence system with configurable coupling regime."""

    def __init__(self, N, kappa=0.15, regime='attractive',
                 omega_base=0.1, omega_spread=0.02,
                 phi_inverse=0.618, dt=0.1, noise_std=0.02,
                 competition_radius=np.pi/3, seed=None):
        """
        regime: 'attractive', 'repulsive', or 'competitive'
        competition_radius: for 'competitive' regime, phases closer than
                           this experience repulsion, further → attraction
        """
        self.N = N
        self.kappa = kappa
        self.regime = regime
        self.phi_inverse = phi_inverse
        self.dt = dt
        self.noise_std = noise_std
        self.competition_radius = competition_radius

        if seed is not None:
            np.random.seed(seed)

        self.C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
        self.phase = np.random.uniform(0, 2 * np.pi, N)
        self.omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

        self.history_C = []
        self.history_phase = []
        self.history_order = []

    def coupling_function(self, delta_theta):
        """Phase coupling function depending on regime.

        Returns the coupling term for dθ/dt.

        ATTRACTIVE: κ sin(Δθ) — standard Kuramoto, pulls toward in-phase
        REPULSIVE: -κ sin(Δθ) — anti-Kuramoto, pushes toward splay
        COMPETITIVE: κ [-sin(Δθ) if |Δθ| < r, else +sin(Δθ)]
                     Resource competition at close range, cooperation at distance
        """
        if self.regime == 'attractive':
            return self.kappa * np.sin(delta_theta)
        elif self.regime == 'repulsive':
            return -self.kappa * np.sin(delta_theta)
        elif self.regime == 'competitive':
            # Phase distance (0 to π)
            dist = abs(delta_theta) % (2 * np.pi)
            dist = min(dist, 2 * np.pi - dist)

            if dist < self.competition_radius:
                # Close phases → repulsion (resource competition)
                return -self.kappa * np.sin(delta_theta)
            else:
                # Distant phases → attraction (cooperation benefit)
                return self.kappa * np.sin(delta_theta)
        else:
            raise ValueError(f"Unknown regime: {self.regime}")

    def step(self):
        N = self.N
        R_func = lambda c: 1 - c**2

        # Phase dynamics
        dphase = self.omega.copy()
        for i in range(N):
            for j in range(N):
                if i != j:
                    dphase[i] += self.coupling_function(self.phase[j] - self.phase[i]) / (N - 1)

        self.phase += self.dt * dphase
        self.phase = self.phase % (2 * np.pi)

        # Coherence dynamics (same for all regimes - coherence coupling is always equalizing)
        dC = np.zeros(N)
        for i in range(N):
            dC[i] = -R_func(self.C[i]) * (self.C[i] - self.phi_inverse) * np.cos(self.phase[i])
            c_coupling = np.sum(self.C - self.C[i]) / (N - 1)
            dC[i] += self.kappa * c_coupling * R_func(self.C[i])

        self.C += self.dt * dC
        self.C = np.clip(self.C, 0, 1)

        # Noise
        self.C += np.random.normal(0, self.noise_std, N)
        self.C = np.clip(self.C, 0, 1)
        self.phase += np.random.normal(0, self.noise_std, N)
        self.phase = self.phase % (2 * np.pi)

        self.history_C.append(self.C.copy())
        self.history_phase.append(self.phase.copy())
        self.history_order.append(compute_order_parameter(self.phase))

    def run(self, steps=8000):
        for _ in range(steps):
            self.step()


def analyze(system):
    """Analyze steady-state dynamics."""
    N = system.N
    T = len(system.history_phase)
    ss = T // 2

    phases_ss = np.array(system.history_phase[ss:])
    C_ss = np.array(system.history_C[ss:])
    order_ss = np.array(system.history_order[ss:])

    mean_R = float(np.mean(order_ss))

    # Pairwise PLI
    pairs = list(combinations(range(N), 2))
    plis = [compute_pli(phases_ss[:, i], phases_ss[:, j]) for i, j in pairs]
    mean_pli = float(np.mean(plis))

    # Phase spacings in final state
    spacings = compute_phase_spacings(system.phase)
    expected_spacing = 360.0 / N
    spacing_error = float(np.mean(np.abs(spacings - expected_spacing)))

    # Coherence correlations (to compare with S74's anti-correlation)
    C_corrs = []
    for i, j in pairs:
        r = np.corrcoef(C_ss[:, i], C_ss[:, j])[0, 1]
        if not np.isnan(r):
            C_corrs.append(float(r))
    mean_C_corr = float(np.mean(C_corrs)) if C_corrs else 0.0

    # Collective coherence
    C_collective = float(np.mean(C_ss))
    C_temporal_std = float(np.std(np.mean(C_ss, axis=1)))

    # Phase pattern: splay (2π/N) vs in-phase vs other
    if mean_R > 0.9:
        pattern = "IN_PHASE"
    elif mean_R < 0.15 and spacing_error < 20:
        pattern = f"SPLAY_{int(expected_spacing)}deg"
    elif mean_R < 0.15:
        pattern = "DISPERSED"
    elif mean_R < 0.5:
        pattern = "PARTIAL_SYNC"
    else:
        pattern = "CLUSTERED"

    return {
        'N': N,
        'regime': system.regime,
        'kappa': system.kappa,
        'mean_R': mean_R,
        'mean_pli': mean_pli,
        'pattern': pattern,
        'spacing_error_deg': spacing_error,
        'spacings_deg': [float(s) for s in spacings],
        'expected_spacing_deg': expected_spacing,
        'mean_C_corr': mean_C_corr,
        'C_collective': C_collective,
        'C_temporal_std': C_temporal_std,
    }


def experiment_1_regime_comparison():
    """Compare three coupling regimes across N=2..8."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Coupling Regime Comparison (N=2..8)")
    print("=" * 70)

    results = {}

    for N in range(2, 9):
        results[N] = {}
        print(f"\n--- N={N} (expected splay = {360/N:.0f}°) ---")

        for regime in ['attractive', 'repulsive', 'competitive']:
            seed_results = []
            for seed in range(5):
                system = NBodyCoherence(N=N, kappa=0.15, regime=regime, seed=seed*100+N)
                system.run(steps=8000)
                a = analyze(system)
                seed_results.append(a)

            mean_R = np.mean([r['mean_R'] for r in seed_results])
            mean_pli = np.mean([r['mean_pli'] for r in seed_results])
            mean_C_corr = np.mean([r['mean_C_corr'] for r in seed_results])
            patterns = [r['pattern'] for r in seed_results]
            dominant = max(set(patterns), key=patterns.count)
            mean_spacing_err = np.mean([r['spacing_error_deg'] for r in seed_results])

            results[N][regime] = {
                'mean_R': float(mean_R),
                'mean_pli': float(mean_pli),
                'mean_C_corr': float(mean_C_corr),
                'dominant_pattern': dominant,
                'spacing_error_deg': float(mean_spacing_err),
                'C_collective': float(np.mean([r['C_collective'] for r in seed_results])),
            }

            print(f"  {regime:12s}: R={mean_R:.3f}, PLI={mean_pli:.3f}, "
                  f"C_corr={mean_C_corr:+.3f}, spacing_err={mean_spacing_err:.1f}°, "
                  f"pattern={dominant}")

    return results


def experiment_2_s74_replication():
    """
    Which regime replicates S74's observations?
    S74 found for N=2:
    - Anti-phase behavior (r = -0.83 to -0.97)
    - PLI jump from 0.2 (κ=0) to 0.8 (κ=0.1)
    - Phase difference → π
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: S74 Replication - Which Regime Matches?")
    print("=" * 70)
    print("S74 targets: C_corr ≈ -0.9, PLI ≈ 0.8, Δφ ≈ 180°")

    results = {}

    for regime in ['attractive', 'repulsive', 'competitive']:
        print(f"\n--- {regime.upper()} ---")
        results[regime] = []

        for kappa in [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]:
            seed_data = []
            for seed in range(10):
                if kappa == 0:
                    # No coupling baseline
                    system = NBodyCoherence(N=2, kappa=0.001, regime=regime, seed=seed*50)
                else:
                    system = NBodyCoherence(N=2, kappa=kappa, regime=regime, seed=seed*50)
                system.run(steps=8000)
                a = analyze(system)
                seed_data.append(a)

            mean_R = np.mean([r['mean_R'] for r in seed_data])
            mean_pli = np.mean([r['mean_pli'] for r in seed_data])
            mean_C_corr = np.mean([r['mean_C_corr'] for r in seed_data])

            # Phase difference
            mean_phase_diff = []
            for r in seed_data:
                if r['spacings_deg']:
                    mean_phase_diff.append(r['spacings_deg'][0])
            avg_diff = np.mean(mean_phase_diff) if mean_phase_diff else 0

            entry = {
                'kappa': kappa,
                'mean_R': float(mean_R),
                'mean_pli': float(mean_pli),
                'mean_C_corr': float(mean_C_corr),
                'mean_phase_diff': float(avg_diff),
            }
            results[regime].append(entry)

            # Score how well this matches S74
            s74_match = ""
            if abs(mean_C_corr - (-0.9)) < 0.2 and mean_pli > 0.7:
                s74_match = " ← S74 MATCH"

            print(f"  κ={kappa:.2f}: R={mean_R:.3f}, PLI={mean_pli:.3f}, "
                  f"C_corr={mean_C_corr:+.3f}, Δφ={avg_diff:.0f}°{s74_match}")

    return results


def experiment_3_splay_state_verification():
    """
    Verify 2π/N splay state for repulsive coupling.
    Test N=2..10 and measure how well spacing matches 2π/N.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Splay State Verification (Repulsive Coupling)")
    print("=" * 70)

    results = []

    for N in range(2, 11):
        seed_data = []
        for seed in range(8):
            system = NBodyCoherence(N=N, kappa=0.15, regime='repulsive', seed=seed*100+N)
            system.run(steps=10000)
            a = analyze(system)
            seed_data.append(a)

        mean_R = np.mean([r['mean_R'] for r in seed_data])
        mean_pli = np.mean([r['mean_pli'] for r in seed_data])
        mean_err = np.mean([r['spacing_error_deg'] for r in seed_data])
        std_err = np.std([r['spacing_error_deg'] for r in seed_data])
        mean_C_corr = np.mean([r['mean_C_corr'] for r in seed_data])
        mean_C = np.mean([r['C_collective'] for r in seed_data])
        mean_C_temporal = np.mean([r['C_temporal_std'] for r in seed_data])

        entry = {
            'N': N,
            'expected_spacing': 360.0 / N,
            'mean_R': float(mean_R),
            'mean_pli': float(mean_pli),
            'spacing_error_deg': float(mean_err),
            'spacing_error_std': float(std_err),
            'mean_C_corr': float(mean_C_corr),
            'C_collective': float(mean_C),
            'C_temporal_std': float(mean_C_temporal),
            'is_splay': bool(mean_R < 0.15 and mean_err < 15),
        }
        results.append(entry)

        verdict = "SPLAY ✓" if entry['is_splay'] else f"R={mean_R:.2f}"
        print(f"  N={N:2d}: expected={360/N:.0f}°, err={mean_err:.1f}±{std_err:.1f}°, "
              f"R={mean_R:.3f}, PLI={mean_pli:.3f}, C_corr={mean_C_corr:+.3f}, "
              f"C={mean_C:.3f} → {verdict}")

    return results


def experiment_4_competitive_radius_sweep():
    """
    For the competitive regime, how does the competition radius affect dynamics?
    Small radius → mostly attractive → in-phase
    Large radius → mostly repulsive → splay state
    Medium → hybrid patterns?
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Competition Radius Sweep (N=4)")
    print("=" * 70)

    results = []
    N = 4

    for radius_frac in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        radius = radius_frac * np.pi
        seed_data = []

        for seed in range(5):
            system = NBodyCoherence(N=N, kappa=0.15, regime='competitive',
                                    competition_radius=radius, seed=seed*100+N)
            system.run(steps=8000)
            a = analyze(system)
            seed_data.append(a)

        mean_R = np.mean([r['mean_R'] for r in seed_data])
        mean_C_corr = np.mean([r['mean_C_corr'] for r in seed_data])
        patterns = [r['pattern'] for r in seed_data]
        dominant = max(set(patterns), key=patterns.count)

        entry = {
            'radius_frac': radius_frac,
            'radius_deg': float(radius * 180 / np.pi),
            'mean_R': float(mean_R),
            'mean_C_corr': float(mean_C_corr),
            'dominant_pattern': dominant,
        }
        results.append(entry)

        print(f"  r={radius_frac:.1f}π ({radius*180/np.pi:.0f}°): R={mean_R:.3f}, "
              f"C_corr={mean_C_corr:+.3f}, pattern={dominant}")

    return results


def experiment_5_n_body_collective_coherence():
    """
    How does collective coherence scale with N under repulsive coupling?

    With splay states: agents peak at different times → smoothing effect.
    Hypothesis: C_collective → φ⁻¹ as N→∞ (perfect smoothing).
    Temporal std should decrease with N (less fluctuation).
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Collective Coherence Scaling (Repulsive)")
    print("=" * 70)

    results = []

    for N in range(2, 16):
        seed_data = []
        for seed in range(8):
            system = NBodyCoherence(N=N, kappa=0.15, regime='repulsive', seed=seed*50+N)
            system.run(steps=8000)
            a = analyze(system)
            seed_data.append(a)

        mean_C = np.mean([r['C_collective'] for r in seed_data])
        std_C = np.std([r['C_collective'] for r in seed_data])
        mean_temporal = np.mean([r['C_temporal_std'] for r in seed_data])

        entry = {
            'N': N,
            'C_collective_mean': float(mean_C),
            'C_collective_std': float(std_C),
            'C_temporal_std': float(mean_temporal),
        }
        results.append(entry)

        marker = " ← φ⁻¹" if abs(mean_C - 0.618) < 0.02 else ""
        print(f"  N={N:2d}: C={mean_C:.4f}±{std_C:.4f}, "
              f"temporal_std={mean_temporal:.4f}{marker}")

    return results


def main():
    print("=" * 70)
    print("Thor Session #77: Coupling Regime Discovery")
    print("Which coupling mechanism governs cognitive synchronization?")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")

    exp1 = experiment_1_regime_comparison()
    exp2 = experiment_2_s74_replication()
    exp3 = experiment_3_splay_state_verification()
    exp4 = experiment_4_competitive_radius_sweep()
    exp5 = experiment_5_n_body_collective_coherence()

    # ── Grand Summary ──
    print("\n" + "=" * 70)
    print("GRAND SUMMARY: Coupling Regime Discovery")
    print("=" * 70)

    print("\n1. REGIME COMPARISON (N=2..8):")
    print(f"   {'N':>3} | {'Attractive':>20} | {'Repulsive':>20} | {'Competitive':>20}")
    print("   " + "-" * 70)
    for N in range(2, 9):
        row = f"   {N:3d} |"
        for regime in ['attractive', 'repulsive', 'competitive']:
            r = exp1[N][regime]
            row += f" R={r['mean_R']:.2f} {r['dominant_pattern']:>10s} |"
        print(row)

    print("\n2. S74 REPLICATION VERDICT:")
    for regime in ['attractive', 'repulsive', 'competitive']:
        # Find κ=0.15 result
        r15 = [r for r in exp2[regime] if abs(r['kappa'] - 0.15) < 0.01][0]
        match_score = 0
        if r15['mean_C_corr'] < -0.5:
            match_score += 1
        if abs(r15['mean_phase_diff'] - 180) < 30:
            match_score += 1
        if r15['mean_pli'] > 0.7:
            match_score += 1
        verdict = "MATCH" if match_score >= 2 else "NO MATCH"
        print(f"   {regime:12s} (κ=0.15): C_corr={r15['mean_C_corr']:+.3f}, "
              f"Δφ={r15['mean_phase_diff']:.0f}°, PLI={r15['mean_pli']:.3f} → {verdict}")

    print("\n3. SPLAY STATE (2π/N) VERIFICATION:")
    splay_holds = True
    for r in exp3:
        status = "✓" if r['is_splay'] else "✗"
        print(f"   N={r['N']:2d}: {r['expected_spacing']:.0f}° ± {r['spacing_error_deg']:.1f}° {status}")
        if not r['is_splay'] and r['N'] <= 8:
            splay_holds = False

    print(f"\n   2π/N law holds for N≤8: {'YES' if splay_holds else 'NO'}")

    print("\n4. COLLECTIVE COHERENCE SCALING (Repulsive):")
    for r in exp5:
        marker = " ← φ⁻¹" if abs(r['C_collective_mean'] - 0.618) < 0.02 else ""
        print(f"   N={r['N']:2d}: C={r['C_collective_mean']:.4f}, "
              f"temporal_std={r['C_temporal_std']:.4f}{marker}")

    # ── Save ──
    output = {
        'timestamp': datetime.now().isoformat(),
        'session': 'Thor #77: Coupling Regime Discovery',
        'finding': 'S76 120° was misclassified. Coupling sign determines phase pattern.',
        'experiment_1_regime_comparison': {str(k): v for k, v in exp1.items()},
        'experiment_2_s74_replication': exp2,
        'experiment_3_splay_verification': exp3,
        'experiment_4_competition_radius': exp4,
        'experiment_5_collective_coherence': exp5,
    }

    filename = 'thor_session_77_coupling_regimes_results.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {filename}")
    return output


if __name__ == '__main__':
    main()
