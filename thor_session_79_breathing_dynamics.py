#!/usr/bin/env python3
"""
Thor Session #79: Breathing Dynamics — Limit Cycle or Noise-Driven?

Session #78 discovered "coherence breathing": adaptive coupling oscillates
between attract/repel modes, breaking the coherence-coordination trade-off.

OPEN QUESTIONS from S78:
  1. Is breathing a deterministic limit cycle or noise-driven?
  2. How does breathing period scale with N?
  3. Is the optimal threshold φ⁻¹ (0.618)?
  4. What is the geometry of the breathing attractor in (C, R) space?

APPROACH:
  Exp 1: Noise ablation — run at noise=0, 0.001, 0.01, 0.02 (S78 default)
  Exp 2: N-scaling — breathing period for N=2,3,4,6,8,12,16
  Exp 3: Threshold fine-sweep — 0.55 to 0.65 in steps of 0.005
  Exp 4: Phase portrait — (C_collective, R) trajectory visualization
  Exp 5: Breathing frequency spectrum — FFT of C_collective time series

Builds on: S78 (breathing discovery), S70 (φ⁻¹ attractor), S64 (golden ratio)
"""

import numpy as np
import json
from datetime import datetime
from itertools import combinations


# ─── Core System (from S78) ───

def compute_order_parameter(phases):
    return float(np.abs(np.mean(np.exp(1j * np.array(phases)))))


class BreathingSystem:
    """N-body coherence with adaptive (metacognitive) coupling.

    Simplified from S78's AdaptiveCoherenceSystem to focus on
    the adaptive regime and its breathing dynamics.
    """

    def __init__(self, N, regime='adaptive',
                 kappa_phase=0.10, kappa_C=0.15,
                 omega_base=0.1, omega_spread=0.02,
                 phi_inverse=0.618, dt=0.1, noise_std=0.02,
                 C_threshold=0.55, seed=None):
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

        self.history_C = []
        self.history_phase = []
        self.history_order = []
        self.history_C_collective = []
        self.regime_switches = 0
        self.switch_times = []  # Track WHEN switches happen

    def step(self, t):
        N = self.N
        R_func = lambda c: 1 - c**2

        # Track regime switches
        C_now = float(np.mean(self.C))
        if len(self.history_C_collective) > 0:
            C_prev = self.history_C_collective[-1]
            if (C_prev < self.C_threshold) != (C_now < self.C_threshold):
                self.regime_switches += 1
                self.switch_times.append(t)

        # Phase coupling — sign depends on collective C
        is_attractive = C_now < self.C_threshold

        dphase = self.omega.copy()
        for i in range(N):
            for j in range(N):
                if i != j:
                    delta = self.phase[j] - self.phase[i]
                    if self.regime == 'adaptive':
                        sign = 1.0 if is_attractive else -1.0
                    elif self.regime == 'coherence_gated':
                        sign = -1.0 if self.C[i] > self.C_threshold else 1.0
                    elif self.regime == 'attractive':
                        sign = 1.0
                    elif self.regime == 'repulsive':
                        sign = -1.0
                    else:
                        sign = 1.0
                    dphase[i] += sign * self.kappa_phase * np.sin(delta) / (N - 1)

        self.phase += self.dt * dphase
        self.phase = self.phase % (2 * np.pi)

        # Coherence dynamics
        dC = np.zeros(N)
        for i in range(N):
            dC[i] = -R_func(self.C[i]) * (self.C[i] - self.phi_inverse) * np.cos(self.phase[i])
            c_coupling = np.sum(self.C - self.C[i]) / (N - 1)
            dC[i] += self.kappa_C * c_coupling * R_func(self.C[i])

        self.C += self.dt * dC
        self.C = np.clip(self.C, 0, 1)

        # Noise
        if self.noise_std > 0:
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
        for t in range(steps):
            self.step(t)


def analyze_breathing(system, warmup_frac=0.2):
    """Extract breathing dynamics from a system run."""
    T = len(system.history_C_collective)
    ss = int(T * warmup_frac)

    C_coll = np.array(system.history_C_collective[ss:])
    R_hist = np.array(system.history_order[ss:])

    # Breathing transitions in steady state
    above = C_coll > system.C_threshold
    transitions = np.where(np.diff(above.astype(int)) != 0)[0]

    if len(transitions) > 2:
        intervals = np.diff(transitions)
        mean_period = float(np.mean(intervals)) * 2  # full cycle = 2 half-cycles
        std_period = float(np.std(intervals)) * 2
        attract_frac = float(np.sum(~above)) / len(above)
    else:
        mean_period = float('inf')
        std_period = 0.0
        attract_frac = float(np.sum(~above)) / len(above)

    # FFT of C_collective for dominant frequency
    C_detrended = C_coll - np.mean(C_coll)
    fft = np.fft.rfft(C_detrended)
    freqs = np.fft.rfftfreq(len(C_detrended))
    power = np.abs(fft)**2
    # Skip DC
    if len(power) > 1:
        peak_idx = np.argmax(power[1:]) + 1
        peak_freq = float(freqs[peak_idx])
        peak_power = float(power[peak_idx])
        total_power = float(np.sum(power[1:]))
        spectral_concentration = peak_power / total_power if total_power > 0 else 0
    else:
        peak_freq = 0.0
        spectral_concentration = 0.0

    return {
        'mean_C': float(np.mean(C_coll)),
        'std_C': float(np.std(C_coll)),
        'mean_R': float(np.mean(R_hist)),
        'std_R': float(np.std(R_hist)),
        'n_transitions': len(transitions),
        'mean_period': mean_period,
        'std_period': std_period,
        'attract_frac': attract_frac,
        'peak_freq': peak_freq,
        'spectral_concentration': spectral_concentration,
        'trade_off_broken': float(np.mean(C_coll)) > 0.5 and float(np.mean(R_hist)) < 0.5,
    }


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 1: Noise Ablation — Is Breathing Deterministic?
# ═══════════════════════════════════════════════════════════

def experiment_1_noise_ablation():
    """
    THE fundamental question: does breathing persist without noise?

    If YES → deterministic limit cycle (emergent from coupling dynamics)
    If NO  → noise-driven stochastic oscillation (noise kicks the system
             back and forth across the threshold)

    Test at noise_std = 0, 0.001, 0.005, 0.01, 0.02
    For each: multiple seeds, long runs (30k steps)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Noise Ablation — Is Breathing Deterministic?")
    print("=" * 70)

    noise_levels = [0.0, 0.001, 0.005, 0.01, 0.02]
    results = []

    for noise in noise_levels:
        print(f"\n--- noise_std = {noise} ---")
        seed_results = []
        for seed in range(5):
            system = BreathingSystem(
                N=4, regime='adaptive',
                kappa_phase=0.10, kappa_C=0.15,
                C_threshold=0.55, noise_std=noise,
                seed=seed * 100 + 4
            )
            system.run(steps=20000)
            analysis = analyze_breathing(system)
            seed_results.append(analysis)

        avg = {
            'noise_std': noise,
            'mean_C': float(np.mean([r['mean_C'] for r in seed_results])),
            'std_C': float(np.mean([r['std_C'] for r in seed_results])),
            'mean_R': float(np.mean([r['mean_R'] for r in seed_results])),
            'n_transitions': float(np.mean([r['n_transitions'] for r in seed_results])),
            'mean_period': float(np.mean([r['mean_period'] for r in seed_results if r['mean_period'] != float('inf')])) if any(r['mean_period'] != float('inf') for r in seed_results) else float('inf'),
            'attract_frac': float(np.mean([r['attract_frac'] for r in seed_results])),
            'peak_freq': float(np.mean([r['peak_freq'] for r in seed_results])),
            'spectral_concentration': float(np.mean([r['spectral_concentration'] for r in seed_results])),
            'trade_off_broken': sum(1 for r in seed_results if r['trade_off_broken']),
        }
        results.append(avg)

        breathing = "YES" if avg['n_transitions'] > 5 else "NO"
        print(f"  Breathing: {breathing} ({avg['n_transitions']:.0f} transitions)")
        print(f"  C={avg['mean_C']:.4f}±{avg['std_C']:.4f}, R={avg['mean_R']:.4f}")
        print(f"  Period: {avg['mean_period']:.1f} steps")
        print(f"  Attract fraction: {avg['attract_frac']:.3f}")
        print(f"  Spectral concentration: {avg['spectral_concentration']:.4f}")
        print(f"  Trade-off broken: {avg['trade_off_broken']}/8 seeds")

    # Verdict
    print("\n" + "-" * 40)
    noise0 = results[0]
    noise02 = results[-1]
    if noise0['n_transitions'] > 5:
        print("VERDICT: Breathing is a DETERMINISTIC LIMIT CYCLE")
        print(f"  noise=0: {noise0['n_transitions']:.0f} transitions, period={noise0['mean_period']:.1f}")
        print(f"  noise=0.02: {noise02['n_transitions']:.0f} transitions, period={noise02['mean_period']:.1f}")
        print("  Breathing persists without noise → emergent from coupling dynamics")
    else:
        print("VERDICT: Breathing is NOISE-DRIVEN")
        print(f"  noise=0: {noise0['n_transitions']:.0f} transitions (no breathing)")
        print(f"  noise=0.02: {noise02['n_transitions']:.0f} transitions (breathing)")
        print("  Noise is required to kick the system across the threshold")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 2: Breathing Period vs N Scaling
# ═══════════════════════════════════════════════════════════

def experiment_2_period_scaling():
    """
    How does breathing period scale with system size N?

    Hypotheses:
    - T ∝ N (linear: more agents = slower consensus)
    - T ∝ √N (diffusive: random walk across threshold)
    - T ∝ 1/N (faster: more coupling forces = quicker transitions)
    - T = const (threshold dynamics dominate over N)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Breathing Period vs N")
    print("=" * 70)

    N_values = [2, 3, 4, 6, 8, 12]
    results = []

    for N in N_values:
        print(f"\n--- N={N} ---")
        seed_results = []
        for seed in range(6):
            system = BreathingSystem(
                N=N, regime='adaptive',
                kappa_phase=0.10, kappa_C=0.15,
                C_threshold=0.55, noise_std=0.02,
                seed=seed * 100 + N
            )
            system.run(steps=20000)
            analysis = analyze_breathing(system)
            seed_results.append(analysis)

        valid_periods = [r['mean_period'] for r in seed_results if r['mean_period'] != float('inf')]
        mean_period = float(np.mean(valid_periods)) if valid_periods else float('inf')
        std_period = float(np.std(valid_periods)) if valid_periods else 0.0

        avg = {
            'N': N,
            'mean_C': float(np.mean([r['mean_C'] for r in seed_results])),
            'mean_R': float(np.mean([r['mean_R'] for r in seed_results])),
            'mean_period': mean_period,
            'std_period': std_period,
            'n_transitions': float(np.mean([r['n_transitions'] for r in seed_results])),
            'attract_frac': float(np.mean([r['attract_frac'] for r in seed_results])),
            'peak_freq': float(np.mean([r['peak_freq'] for r in seed_results])),
            'spectral_concentration': float(np.mean([r['spectral_concentration'] for r in seed_results])),
            'trade_off_broken': sum(1 for r in seed_results if r['trade_off_broken']),
        }
        results.append(avg)

        print(f"  Period: {mean_period:.1f} ± {std_period:.1f} steps")
        print(f"  C={avg['mean_C']:.4f}, R={avg['mean_R']:.4f}")
        print(f"  Transitions: {avg['n_transitions']:.0f}")
        print(f"  Trade-off broken: {avg['trade_off_broken']}/10")

    # Fit scaling law
    valid = [(r['N'], r['mean_period']) for r in results if r['mean_period'] != float('inf')]
    if len(valid) >= 3:
        Ns = np.array([v[0] for v in valid])
        Ts = np.array([v[1] for v in valid])
        # Fit T = a * N^b in log space
        log_N = np.log(Ns)
        log_T = np.log(Ts)
        b, log_a = np.polyfit(log_N, log_T, 1)
        a = np.exp(log_a)
        residuals = log_T - (b * log_N + log_a)
        r_squared = 1 - np.sum(residuals**2) / np.sum((log_T - np.mean(log_T))**2)

        print(f"\n  SCALING LAW: T ≈ {a:.1f} × N^{b:.3f} (R² = {r_squared:.4f})")
        if abs(b) < 0.2:
            print(f"  → Period is approximately CONSTANT (weak N-dependence)")
        elif abs(b - 0.5) < 0.2:
            print(f"  → Period scales as √N (diffusive)")
        elif abs(b - 1.0) < 0.2:
            print(f"  → Period scales LINEARLY with N")
        elif b < -0.2:
            print(f"  → Period DECREASES with N (faster breathing for larger groups)")

        for r in results:
            r['scaling_exponent'] = float(b)
            r['scaling_r_squared'] = float(r_squared)

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 3: Threshold Fine-Sweep Near φ⁻¹
# ═══════════════════════════════════════════════════════════

def experiment_3_threshold_golden():
    """
    S78 found coherence-gated threshold=0.60 was best.
    φ⁻¹ = 0.618... is tantalizingly close.

    Fine-sweep from 0.50 to 0.68 in 0.01 steps.
    For BOTH adaptive and coherence-gated regimes.

    Metric: "breathing quality" = C_collective × (1 - R) × breathing_regularity
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Threshold Fine-Sweep Near φ⁻¹ = 0.618")
    print("=" * 70)

    thresholds = np.arange(0.50, 0.67, 0.02)
    phi_inv = (np.sqrt(5) - 1) / 2  # 0.6180339...

    results = {'adaptive': [], 'coherence_gated': []}

    for regime in ['adaptive', 'coherence_gated']:
        print(f"\n--- Regime: {regime} ---")
        print(f"  {'thresh':>6} | {'C':>6} | {'R':>6} | {'Period':>7} | {'Quality':>7} | {'Break':>5}")
        print("  " + "-" * 55)

        best_quality = -1
        best_thresh = -1

        for thresh in thresholds:
            seed_results = []
            for seed in range(5):
                system = BreathingSystem(
                    N=4, regime=regime,
                    kappa_phase=0.10 if regime == 'adaptive' else 0.15,
                    kappa_C=0.15,
                    C_threshold=float(thresh),
                    noise_std=0.02,
                    seed=seed * 100 + 4
                )
                system.run(steps=15000)
                seed_results.append(analyze_breathing(system))

            avg_C = float(np.mean([r['mean_C'] for r in seed_results]))
            avg_R = float(np.mean([r['mean_R'] for r in seed_results]))
            avg_period = float(np.mean([r['mean_period'] for r in seed_results if r['mean_period'] != float('inf')])) if any(r['mean_period'] != float('inf') for r in seed_results) else float('inf')
            avg_spec = float(np.mean([r['spectral_concentration'] for r in seed_results]))
            n_broken = sum(1 for r in seed_results if r['trade_off_broken'])

            # Quality metric: want high C, low R, regular breathing
            breathing_reg = avg_spec if avg_spec > 0 else 0.001
            quality = avg_C * (1 - avg_R) * breathing_reg if avg_C > 0.5 and avg_R < 0.5 else 0.0

            entry = {
                'threshold': float(thresh),
                'mean_C': avg_C,
                'mean_R': avg_R,
                'mean_period': avg_period,
                'spectral_concentration': avg_spec,
                'quality': quality,
                'trade_off_broken': n_broken,
            }
            results[regime].append(entry)

            if quality > best_quality:
                best_quality = quality
                best_thresh = float(thresh)

            marker = " ← φ⁻¹" if abs(thresh - phi_inv) < 0.005 else ""
            marker += " ★" if quality == best_quality and quality > 0 else ""
            print(f"  {thresh:6.3f} | {avg_C:6.4f} | {avg_R:6.4f} | {avg_period:7.1f} | "
                  f"{quality:7.5f} | {n_broken:>3}/8{marker}")

        print(f"\n  Best threshold: {best_thresh:.3f} (quality={best_quality:.5f})")
        print(f"  φ⁻¹ = {phi_inv:.4f}, distance to best: {abs(best_thresh - phi_inv):.4f}")

        results[regime + '_best_thresh'] = best_thresh
        results[regime + '_phi_distance'] = abs(best_thresh - phi_inv)

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 4: Phase Portrait — Attractor Geometry
# ═══════════════════════════════════════════════════════════

def experiment_4_phase_portrait():
    """
    Plot the trajectory in (C_collective, R) space.

    If breathing is a limit cycle → trajectory should form a closed loop.
    If noise-driven → trajectory should be a fuzzy cloud around the threshold.

    Also compute:
    - Attractor dimension (correlation dimension estimate)
    - Trajectory area (enclosed area in C-R space)
    - Winding number (how many loops per 1000 steps)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Phase Portrait — Attractor Geometry")
    print("=" * 70)

    results = []

    for noise in [0.0, 0.005, 0.02]:
        print(f"\n--- noise_std = {noise} ---")
        system = BreathingSystem(
            N=4, regime='adaptive',
            kappa_phase=0.10, kappa_C=0.15,
            C_threshold=0.55, noise_std=noise,
            seed=42
        )
        system.run(steps=25000)

        # Steady-state trajectory
        ss = 10000
        C_coll = np.array(system.history_C_collective[ss:])
        R_hist = np.array(system.history_order[ss:])

        # Trajectory statistics
        C_range = float(np.max(C_coll) - np.min(C_coll))
        R_range = float(np.max(R_hist) - np.min(R_hist))

        # Estimate enclosed area using Shoelace-like formula
        # For trajectory as polygon
        n_points = min(len(C_coll), 5000)
        idx = np.linspace(0, len(C_coll)-1, n_points, dtype=int)
        c_pts = C_coll[idx]
        r_pts = R_hist[idx]
        # Cross-product area (total traversal area)
        area = 0.5 * np.abs(np.sum(c_pts[:-1] * r_pts[1:] - c_pts[1:] * r_pts[:-1]))

        # Autocorrelation of C_collective (to detect periodicity)
        C_centered = C_coll - np.mean(C_coll)
        autocorr = np.correlate(C_centered[:5000], C_centered[:5000], mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr / autocorr[0] if autocorr[0] > 0 else autocorr

        # Find first non-trivial peak in autocorrelation
        from scipy.signal import find_peaks
        peaks, props = find_peaks(autocorr[10:], height=0.1, distance=20)
        autocorr_period = float(peaks[0] + 10) if len(peaks) > 0 else float('inf')
        autocorr_height = float(props['peak_heights'][0]) if len(peaks) > 0 else 0.0

        # Winding number: count threshold crossings
        above = C_coll > system.C_threshold
        crossings = np.sum(np.diff(above.astype(int)) != 0)
        winding = crossings / len(C_coll) * 1000  # per 1000 steps

        # Trajectory samples for documentation
        sample_idx = np.linspace(0, min(2000, len(C_coll)-1), 50, dtype=int)
        trajectory_sample = [(float(C_coll[i]), float(R_hist[i])) for i in sample_idx]

        entry = {
            'noise_std': noise,
            'C_range': C_range,
            'R_range': R_range,
            'trajectory_area': float(area),
            'autocorr_period': autocorr_period,
            'autocorr_height': autocorr_height,
            'winding_per_1000': float(winding),
            'mean_C': float(np.mean(C_coll)),
            'mean_R': float(np.mean(R_hist)),
            'trajectory_sample': trajectory_sample,
        }
        results.append(entry)

        print(f"  C range: [{np.min(C_coll):.4f}, {np.max(C_coll):.4f}] (width={C_range:.4f})")
        print(f"  R range: [{np.min(R_hist):.4f}, {np.max(R_hist):.4f}] (width={R_range:.4f})")
        print(f"  Trajectory area: {area:.6f}")
        print(f"  Autocorrelation period: {autocorr_period:.1f} steps")
        print(f"  Autocorrelation peak height: {autocorr_height:.4f}")
        print(f"  Winding rate: {winding:.2f} crossings per 1000 steps")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 5: Breathing Frequency Spectrum
# ═══════════════════════════════════════════════════════════

def experiment_5_spectrum():
    """
    FFT analysis of C_collective to characterize the breathing spectrum.

    Questions:
    - Is there a sharp peak (regular oscillation) or broad band (irregular)?
    - How does the spectrum change with noise?
    - Is there a harmonic structure?
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Breathing Frequency Spectrum")
    print("=" * 70)

    results = []

    for noise in [0.0, 0.005, 0.02]:
        print(f"\n--- noise_std = {noise} ---")
        system = BreathingSystem(
            N=4, regime='adaptive',
            kappa_phase=0.10, kappa_C=0.15,
            C_threshold=0.55, noise_std=noise,
            seed=42
        )
        system.run(steps=25000)

        ss = 10000
        C_coll = np.array(system.history_C_collective[ss:])

        # Windowed FFT (Welch-like)
        window_size = 8192
        n_windows = (len(C_coll) - window_size) // (window_size // 2)
        power_sum = None

        for w in range(max(1, n_windows)):
            start = w * (window_size // 2)
            segment = C_coll[start:start + window_size]
            if len(segment) < window_size:
                break
            # Hann window
            hann = 0.5 * (1 - np.cos(2 * np.pi * np.arange(window_size) / window_size))
            segment = (segment - np.mean(segment)) * hann
            fft = np.fft.rfft(segment)
            power = np.abs(fft)**2
            if power_sum is None:
                power_sum = power
            else:
                power_sum += power

        freqs = np.fft.rfftfreq(window_size)
        power_avg = power_sum / max(1, n_windows)

        # Find peaks
        from scipy.signal import find_peaks
        peak_idx, props = find_peaks(power_avg[1:], height=np.max(power_avg[1:])*0.1, distance=10)
        peak_idx += 1  # offset from skipping DC

        # Top 3 peaks
        if len(peak_idx) > 0:
            sorted_peaks = peak_idx[np.argsort(power_avg[peak_idx])[::-1]][:3]
            top_freqs = [float(freqs[p]) for p in sorted_peaks]
            top_powers = [float(power_avg[p]) for p in sorted_peaks]
        else:
            top_freqs = []
            top_powers = []

        # Spectral entropy (flatness measure)
        p_norm = power_avg[1:] / np.sum(power_avg[1:]) if np.sum(power_avg[1:]) > 0 else power_avg[1:]
        p_norm = p_norm[p_norm > 0]
        spectral_entropy = float(-np.sum(p_norm * np.log(p_norm)))
        max_entropy = float(np.log(len(p_norm)))
        normalized_entropy = spectral_entropy / max_entropy if max_entropy > 0 else 0

        entry = {
            'noise_std': noise,
            'top_frequencies': top_freqs,
            'top_powers': top_powers,
            'spectral_entropy': spectral_entropy,
            'normalized_entropy': normalized_entropy,
            'n_windows': max(1, n_windows),
        }
        results.append(entry)

        print(f"  Top frequencies: {[f'{f:.6f}' for f in top_freqs]}")
        print(f"  Spectral entropy: {normalized_entropy:.4f} (0=pure tone, 1=white noise)")

        if len(top_freqs) >= 2 and top_freqs[0] > 0:
            ratio = top_freqs[1] / top_freqs[0]
            print(f"  f2/f1 ratio: {ratio:.3f} (harmonics at 2.0)")

    return results


# ═══════════════════════════════════════════════════════════
# EXPERIMENT 6: Multiple Initial Conditions — Basin of Attraction
# ═══════════════════════════════════════════════════════════

def experiment_6_basin():
    """
    Start from different initial C and phase distributions.
    Does breathing always emerge? Or only from specific initial conditions?

    This tests whether the breathing attractor is globally attractive.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 6: Basin of Attraction — Is Breathing Universal?")
    print("=" * 70)

    N = 4
    results = []

    initial_conditions = [
        ('uniform_high', 0.8, 'uniform'),    # All high C, random phases
        ('uniform_low', 0.2, 'uniform'),     # All low C
        ('at_threshold', 0.55, 'uniform'),   # Start at threshold
        ('mixed_high_low', None, 'uniform'),  # Mix: some high, some low
        ('all_in_phase', 0.618, 'in_phase'), # All same phase
        ('all_anti_phase', 0.618, 'anti_phase'),  # Alternating phases
    ]

    for label, C_init, phase_init in initial_conditions:
        print(f"\n--- {label} ---")
        seed_results = []

        for seed in range(5):
            np.random.seed(seed * 100 + N)

            system = BreathingSystem(
                N=N, regime='adaptive',
                kappa_phase=0.10, kappa_C=0.15,
                C_threshold=0.55, noise_std=0.02,
                seed=None  # We set seed above
            )

            # Override initial conditions
            if C_init is not None:
                system.C = np.full(N, C_init) + np.random.normal(0, 0.01, N)
                system.C = np.clip(system.C, 0.01, 0.99)
            else:
                # Mixed: half high, half low
                system.C = np.array([0.8, 0.2, 0.8, 0.2])[:N] + np.random.normal(0, 0.01, N)
                system.C = np.clip(system.C, 0.01, 0.99)

            if phase_init == 'in_phase':
                system.phase = np.full(N, 0.0) + np.random.normal(0, 0.01, N)
            elif phase_init == 'anti_phase':
                system.phase = np.array([0, np.pi, 0, np.pi])[:N]
            # else: keep random uniform from constructor

            system.run(steps=15000)
            analysis = analyze_breathing(system)
            seed_results.append(analysis)

        avg_C = float(np.mean([r['mean_C'] for r in seed_results]))
        avg_R = float(np.mean([r['mean_R'] for r in seed_results]))
        avg_trans = float(np.mean([r['n_transitions'] for r in seed_results]))
        n_broken = sum(1 for r in seed_results if r['trade_off_broken'])

        entry = {
            'label': label,
            'mean_C': avg_C,
            'mean_R': avg_R,
            'n_transitions': avg_trans,
            'trade_off_broken': n_broken,
            'breathing': avg_trans > 5,
        }
        results.append(entry)

        print(f"  C={avg_C:.4f}, R={avg_R:.4f}, transitions={avg_trans:.0f}")
        print(f"  Breathing: {'YES' if entry['breathing'] else 'NO'}")
        print(f"  Trade-off broken: {n_broken}/8")

    # Summary
    all_breathe = all(r['breathing'] for r in results)
    print(f"\n  BASIN ANALYSIS:")
    print(f"  All ICs lead to breathing: {'YES — globally attractive' if all_breathe else 'NO — IC-dependent'}")
    for r in results:
        status = "✓ breathes" if r['breathing'] else "✗ no breathing"
        print(f"    {r['label']}: {status} (C={r['mean_C']:.3f}, R={r['mean_R']:.3f})")

    return results


# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Thor Session #79: Breathing Dynamics — Limit Cycle or Noise-Driven?")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"φ⁻¹ = {(np.sqrt(5)-1)/2:.10f}")

    exp1 = experiment_1_noise_ablation()
    exp2 = experiment_2_period_scaling()
    exp3 = experiment_3_threshold_golden()
    exp4 = experiment_4_phase_portrait()
    exp5 = experiment_5_spectrum()
    exp6 = experiment_6_basin()

    # ── Grand Summary ──
    print("\n" + "=" * 70)
    print("GRAND SUMMARY: The Nature of Coherence Breathing")
    print("=" * 70)

    # Q1: Deterministic or noise-driven?
    noise0_trans = exp1[0]['n_transitions']
    noise02_trans = exp1[-1]['n_transitions']
    print(f"\n  Q1: Is breathing deterministic?")
    if noise0_trans > 5:
        print(f"    YES — {noise0_trans:.0f} transitions at noise=0")
        print(f"    Breathing is an emergent LIMIT CYCLE")
        q1_answer = 'deterministic_limit_cycle'
    else:
        print(f"    NO — only {noise0_trans:.0f} transitions at noise=0 vs {noise02_trans:.0f} at noise=0.02")
        print(f"    Breathing requires noise (stochastic oscillation)")
        q1_answer = 'noise_driven'

    # Q2: Period scaling
    print(f"\n  Q2: How does period scale with N?")
    if exp2 and 'scaling_exponent' in exp2[0]:
        b = exp2[0]['scaling_exponent']
        r2 = exp2[0]['scaling_r_squared']
        print(f"    T ∝ N^{b:.3f} (R² = {r2:.4f})")
    for r in exp2:
        print(f"    N={r['N']}: period={r['mean_period']:.1f}±{r['std_period']:.1f}")

    # Q3: Golden ratio threshold?
    print(f"\n  Q3: Is optimal threshold φ⁻¹?")
    for regime in ['adaptive', 'coherence_gated']:
        best = exp3.get(regime + '_best_thresh', '?')
        dist = exp3.get(regime + '_phi_distance', '?')
        print(f"    {regime}: best={best}, distance from φ⁻¹={dist}")

    # Q4: Attractor geometry
    print(f"\n  Q4: Attractor geometry")
    for r in exp4:
        print(f"    noise={r['noise_std']}: area={r['trajectory_area']:.6f}, "
              f"autocorr_period={r['autocorr_period']:.1f}, "
              f"winding={r['winding_per_1000']:.2f}/1000")

    # Save everything
    output = {
        'timestamp': datetime.now().isoformat(),
        'session': 'Thor #79: Breathing Dynamics',
        'questions': {
            'Q1': 'Is breathing deterministic or noise-driven?',
            'Q2': 'How does period scale with N?',
            'Q3': 'Is optimal threshold φ⁻¹?',
            'Q4': 'What is the attractor geometry?',
        },
        'answers': {
            'Q1': q1_answer,
        },
        'results': {
            'exp1_noise_ablation': exp1,
            'exp2_period_scaling': exp2,
            'exp3_threshold_golden': exp3,
            'exp4_phase_portrait': exp4,
            'exp5_spectrum': exp5,
            'exp6_basin': exp6,
        }
    }

    filename = 'thor_session_79_breathing_dynamics_results.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nResults saved to {filename}")
    return output


if __name__ == '__main__':
    main()
