#!/usr/bin/env python3
"""
Thor Session #80, Part 2: WHY does C_range = C* in the N-body system?

Key findings so far:
  1. C_range = C* for ALL values of C* (not φ-specific)
  2. C_max = C*, C_min = 0 (bounded by equilibrium and physical boundary)
  3. Single-agent does NOT reproduce this (C_range depends on ω)
  4. Independent of kappa_phase, kappa_C, dt

HYPOTHESIS: The adaptive coupling creates a collective "adiabatic"
dynamics where the mean C has time to explore [0, C*] fully, even
though individual agents can't.

EXPERIMENTS:
  Exp A: Track individual vs collective C during oscillation
  Exp B: N-dependence of C_range (does it hold for N=2?)
  Exp C: Does the result hold WITHOUT adaptive coupling? (pure attractive/repulsive)
  Exp D: Verify the mechanism: C_min = 0 due to clipping
"""

import numpy as np
import json
from datetime import datetime


def compute_order_parameter(phases):
    return float(np.abs(np.mean(np.exp(1j * np.array(phases)))))


class AnalyticalSystem:
    """Deterministic system with detailed tracking."""

    def __init__(self, N, regime='adaptive',
                 kappa_phase=0.10, kappa_C=0.15,
                 omega_base=0.1, omega_spread=0.02,
                 phi_inverse=0.618, dt=0.1,
                 C_threshold=0.55, seed=None):
        self.N = N
        self.regime = regime
        self.kappa_phase = kappa_phase
        self.kappa_C = kappa_C
        self.phi_inverse = phi_inverse
        self.dt = dt
        self.C_threshold = C_threshold

        if seed is not None:
            np.random.seed(seed)

        self.C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
        self.phase = np.random.uniform(0, 2 * np.pi, N)
        self.omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

        self.history_C = []
        self.history_C_collective = []
        self.history_order = []
        self.clip_count_low = 0  # how many times clipping at 0 occurs
        self.clip_count_high = 0

    def step(self, t):
        N = self.N
        R_func = lambda c: 1 - c**2
        C_now = float(np.mean(self.C))
        is_attractive = C_now < self.C_threshold

        # Phase dynamics
        dphase = self.omega.copy()
        for i in range(N):
            for j in range(N):
                if i != j:
                    delta = self.phase[j] - self.phase[i]
                    if self.regime == 'adaptive':
                        sign = 1.0 if is_attractive else -1.0
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

        C_new = self.C + self.dt * dC

        # Track clipping events
        self.clip_count_low += int(np.sum(C_new < 0))
        self.clip_count_high += int(np.sum(C_new > 1))

        self.C = np.clip(C_new, 0, 1)

        self.history_C.append(self.C.copy())
        R = compute_order_parameter(self.phase)
        self.history_order.append(R)
        self.history_C_collective.append(float(np.mean(self.C)))

    def run(self, steps=10000):
        for t in range(steps):
            self.step(t)


# ─── Experiment A: Individual vs Collective Dynamics ───

def expA_individual_vs_collective():
    """Track each agent's C trajectory to understand collective oscillation."""
    print("=" * 70)
    print("EXPERIMENT A: Individual vs Collective Dynamics")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    for seed in [2, 3]:
        sys = AnalyticalSystem(N=4, seed=seed)
        sys.run(steps=30000)

        C_arr = np.array(sys.history_C)  # (T, N)
        C_coll = np.array(sys.history_C_collective)

        ss = 5000
        C_ss = C_arr[ss:]
        C_coll_ss = C_coll[ss:]

        print(f"\n  Seed {seed} (N=4):")
        print(f"    Collective: C_min={np.min(C_coll_ss):.6f}, C_max={np.max(C_coll_ss):.6f}, "
              f"range={np.max(C_coll_ss)-np.min(C_coll_ss):.6f}")
        print(f"    Clipping events: low={sys.clip_count_low}, high={sys.clip_count_high}")

        for i in range(4):
            C_i = C_ss[:, i]
            c_min, c_max = np.min(C_i), np.max(C_i)
            crosses_Cstar = np.any(np.diff(np.sign(C_i - phi_inv)) != 0)
            print(f"    Agent {i}: C_min={c_min:.6f}, C_max={c_max:.6f}, "
                  f"range={c_max-c_min:.6f}, crosses C*: {crosses_Cstar}")

        # Find when collective is at minimum — what's each agent doing?
        min_idx = np.argmin(C_coll_ss)
        max_idx = np.argmax(C_coll_ss)
        print(f"\n    At collective minimum (t={ss+min_idx}):")
        print(f"      C_collective = {C_coll_ss[min_idx]:.6f}")
        for i in range(4):
            print(f"      Agent {i}: C={C_ss[min_idx, i]:.6f}")

        print(f"    At collective maximum (t={ss+max_idx}):")
        print(f"      C_collective = {C_coll_ss[max_idx]:.6f}")
        for i in range(4):
            print(f"      Agent {i}: C={C_ss[max_idx, i]:.6f}")


# ─── Experiment B: N-dependence of C_range ───

def expB_N_dependence():
    """Does C_range = C* hold for all N?"""
    print("\n" + "=" * 70)
    print("EXPERIMENT B: N-Dependence of C_range = C*")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    for N in [2, 3, 4, 6, 8, 12]:
        ranges = []
        for seed in range(20):
            sys = AnalyticalSystem(N=N, seed=seed)
            sys.run(steps=20000)
            C_arr = np.array(sys.history_C_collective[5000:])
            c_range = np.max(C_arr) - np.min(C_arr)
            if c_range > 0.1:  # oscillating
                ranges.append(c_range)

        if ranges:
            mean_range = np.mean(ranges)
            print(f"  N={N:2d}: C_range = {mean_range:.6f}, "
                  f"C*/C_range = {phi_inv/mean_range:.6f}, "
                  f"n_oscillating = {len(ranges)}/20")
        else:
            print(f"  N={N:2d}: No oscillating seeds")


# ─── Experiment C: Does result hold without adaptive coupling? ───

def expC_without_adaptive():
    """Test pure attractive and repulsive regimes."""
    print("\n" + "=" * 70)
    print("EXPERIMENT C: C_range Without Adaptive Coupling")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    for regime in ['adaptive', 'attractive', 'repulsive']:
        ranges = []
        for seed in range(20):
            sys = AnalyticalSystem(N=4, regime=regime, seed=seed)
            sys.run(steps=20000)
            C_arr = np.array(sys.history_C_collective[5000:])
            c_range = np.max(C_arr) - np.min(C_arr)
            if c_range > 0.05:
                ranges.append(c_range)

        if ranges:
            mean_range = np.mean(ranges)
            print(f"  {regime:15s}: C_range = {mean_range:.6f}, "
                  f"C*/C_range = {phi_inv/mean_range:.4f}, n={len(ranges)}")
        else:
            print(f"  {regime:15s}: No oscillating seeds")


# ─── Experiment D: Remove clipping — what is the natural minimum? ───

def expD_no_clipping():
    """Run without clipping to find the natural oscillation bounds."""
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Natural Oscillation Without Clipping")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    # Single agent, no clipping
    print("\n  --- Single agent, no clipping ---")
    for C0 in [0.3, 0.5, 0.7]:
        C = C0
        theta = 0.0
        dt = 0.001
        omega = 0.1
        C_hist = []
        for t in range(2000000):
            R_func = 1 - C**2
            dC = -R_func * (C - phi_inv) * np.cos(theta)
            C += dt * dC
            # NO CLIPPING
            theta += dt * omega
            theta = theta % (2 * np.pi)
            C_hist.append(C)

        C_arr = np.array(C_hist[500000:])
        print(f"  C0={C0:.1f}: C_min={np.min(C_arr):.6f}, C_max={np.max(C_arr):.6f}, "
              f"range={np.max(C_arr)-np.min(C_arr):.6f}")

    # N-body, no clipping (modified system)
    print("\n  --- N-body (N=4), no clipping ---")
    for seed in [2, 3, 5, 6]:
        np.random.seed(seed)
        N = 4
        C = phi_inv + np.random.normal(0, 0.05, N)
        phase = np.random.uniform(0, 2 * np.pi, N)
        omega = 0.1 + np.random.uniform(-0.02, 0.02, N)
        dt = 0.1
        kappa_phase = 0.10
        kappa_C = 0.15
        C_threshold = 0.55
        C_coll_hist = []

        for t in range(30000):
            C_now = float(np.mean(C))
            is_attractive = C_now < C_threshold

            dphase = omega.copy()
            for i in range(N):
                for j in range(N):
                    if i != j:
                        delta = phase[j] - phase[i]
                        sign = 1.0 if is_attractive else -1.0
                        dphase[i] += sign * kappa_phase * np.sin(delta) / (N - 1)

            phase += dt * dphase
            phase = phase % (2 * np.pi)

            dC = np.zeros(N)
            for i in range(N):
                R_func = 1 - C[i]**2
                dC[i] = -R_func * (C[i] - phi_inv) * np.cos(phase[i])
                c_coupling = np.sum(C - C[i]) / (N - 1)
                dC[i] += kappa_C * c_coupling * R_func

            C += dt * dC
            # NO CLIPPING
            C_coll_hist.append(float(np.mean(C)))

        C_arr = np.array(C_coll_hist[5000:])
        c_min = np.min(C_arr)
        c_max = np.max(C_arr)
        if abs(c_max - c_min) < 100:  # not diverged
            print(f"  Seed {seed}: C_min={c_min:.6f}, C_max={c_max:.6f}, "
                  f"range={c_max - c_min:.6f}")
        else:
            print(f"  Seed {seed}: DIVERGED (C in [{c_min:.2f}, {c_max:.2f}])")


# ─── Experiment E: The Self-Referential Property ───

def expE_self_referential():
    """Test alternative R_func to verify R(C*) = C* is key.

    Original: R_func(C) = 1 - C²
    Test 1:   R_func(C) = 1 - C   (linear, C* where R=C is C*=0.5)
    Test 2:   R_func(C) = (1-C)²  (quadratic, C* where R=C is different)
    Test 3:   R_func(C) = 1 - C^3 (cubic)

    For R(C) = 1-C², the self-referential point is: 1-C² = C → C = φ⁻¹
    For R(C) = 1-C,  the self-referential point is: 1-C = C → C = 0.5
    For R(C) = (1-C)²: (1-C)² = C → C ≈ 0.382 = 2-φ = φ⁻²
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT E: Self-Referential Property R(C*) = C*")
    print("=" * 70)

    # For each R_func, find the self-referential C* and check if C_range = C*
    test_cases = {
        '1-C²': {
            'R_func': lambda c: 1 - c**2,
            'C_star_theory': (np.sqrt(5) - 1) / 2,  # φ⁻¹
        },
        '1-C': {
            'R_func': lambda c: 1 - c,
            'C_star_theory': 0.5,
        },
        '(1-C)²': {
            'R_func': lambda c: (1 - c)**2,
            'C_star_theory': (3 - np.sqrt(5)) / 2,  # ≈ 0.382 = φ⁻²
        },
        '1-C³': {
            'R_func': lambda c: 1 - c**3,
            'C_star_theory': None,  # solve numerically
        },
    }

    # For 1-C³: solve 1-C³ = C → C³ + C - 1 = 0
    # Numerical: C ≈ 0.6824
    from scipy.optimize import brentq
    test_cases['1-C³']['C_star_theory'] = brentq(lambda c: 1 - c**3 - c, 0, 1)

    for name, tc in test_cases.items():
        R_func = tc['R_func']
        C_star = tc['C_star_theory']

        print(f"\n  R(C) = {name}:")
        print(f"    Self-referential C* = {C_star:.6f}")
        print(f"    R(C*) = {R_func(C_star):.6f}")

        # Run N-body simulation with this R_func
        ranges = []
        for seed in range(20):
            np.random.seed(seed)
            N = 4
            C = np.clip(C_star + np.random.normal(0, 0.05, N), 0.01, 0.99)
            phase = np.random.uniform(0, 2 * np.pi, N)
            omega = 0.1 + np.random.uniform(-0.02, 0.02, N)
            dt = 0.1
            kappa_phase = 0.10
            kappa_C = 0.15
            C_threshold = C_star - 0.07
            C_coll_hist = []

            for t in range(20000):
                C_now = float(np.mean(C))
                is_attractive = C_now < C_threshold

                dphase = omega.copy()
                for i in range(N):
                    for j in range(N):
                        if i != j:
                            delta = phase[j] - phase[i]
                            sign = 1.0 if is_attractive else -1.0
                            dphase[i] += sign * kappa_phase * np.sin(delta) / (N - 1)

                phase += dt * dphase
                phase = phase % (2 * np.pi)

                dC = np.zeros(N)
                for i in range(N):
                    Ri = R_func(C[i])
                    dC[i] = -Ri * (C[i] - C_star) * np.cos(phase[i])
                    c_coupling = np.sum(C - C[i]) / (N - 1)
                    dC[i] += kappa_C * c_coupling * Ri

                C += dt * dC
                C = np.clip(C, 0, 1)
                C_coll_hist.append(float(np.mean(C)))

            C_arr = np.array(C_coll_hist[5000:])
            c_range = np.max(C_arr) - np.min(C_arr)
            if c_range > 0.05:
                ranges.append(c_range)

        if ranges:
            mean_range = np.mean(ranges)
            print(f"    N-body C_range = {mean_range:.6f}")
            print(f"    C*/C_range = {C_star/mean_range:.6f}")
            print(f"    Match: {'YES' if abs(C_star/mean_range - 1.0) < 0.01 else 'NO'}")
        else:
            print(f"    No oscillating seeds")


# ─── Experiment F: Verify C_min = 0 is from clipping ───

def expF_verify_clipping():
    """Is C_min = 0 because of clipping, or does C naturally reach 0?"""
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Clipping Analysis")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    # Track minimum individual C values during the collective minimum
    for seed in [2, 3]:
        sys = AnalyticalSystem(N=4, seed=seed)
        sys.run(steps=30000)

        print(f"\n  Seed {seed}:")
        print(f"    Clip events at C=0: {sys.clip_count_low}")
        print(f"    Clip events at C=1: {sys.clip_count_high}")

        C_arr = np.array(sys.history_C)  # (T, N)
        C_coll = np.array(sys.history_C_collective)

        # Find all local minima of collective C
        from scipy.signal import argrelmin
        min_indices = argrelmin(C_coll[5000:], order=100)[0] + 5000

        if len(min_indices) > 0:
            print(f"    Local minima found: {len(min_indices)}")
            for idx in min_indices[:5]:
                C_at_min = C_arr[idx]
                print(f"      t={idx}: C_coll={C_coll[idx]:.6f}, "
                      f"individual C = [{', '.join(f'{c:.4f}' for c in C_at_min)}]")

    # What if we set the lower clip to -0.1 instead of 0?
    print("\n  --- With lower clip at -0.1 instead of 0 ---")
    for seed in [2, 3]:
        np.random.seed(seed)
        N = 4
        C = phi_inv + np.random.normal(0, 0.05, N)
        C = np.clip(C, 0.01, 0.99)
        phase = np.random.uniform(0, 2 * np.pi, N)
        omega_arr = 0.1 + np.random.uniform(-0.02, 0.02, N)
        dt = 0.1
        kappa_phase = 0.10
        kappa_C = 0.15
        C_threshold = 0.55
        C_coll_hist = []

        for t in range(30000):
            C_now = float(np.mean(C))
            is_attractive = C_now < C_threshold

            dphase = omega_arr.copy()
            for i in range(N):
                for j in range(N):
                    if i != j:
                        delta = phase[j] - phase[i]
                        sign = 1.0 if is_attractive else -1.0
                        dphase[i] += sign * kappa_phase * np.sin(delta) / (N - 1)

            phase += dt * dphase
            phase = phase % (2 * np.pi)

            dC = np.zeros(N)
            for i in range(N):
                R_func = 1 - C[i]**2
                dC[i] = -R_func * (C[i] - phi_inv) * np.cos(phase[i])
                c_coupling = np.sum(C - C[i]) / (N - 1)
                dC[i] += kappa_C * c_coupling * R_func

            C += dt * dC
            C = np.clip(C, -0.1, 1.1)  # wider bounds
            C_coll_hist.append(float(np.mean(C)))

        C_arr = np.array(C_coll_hist[5000:])
        c_min = np.min(C_arr)
        c_max = np.max(C_arr)
        print(f"  Seed {seed}: C_min={c_min:.6f}, C_max={c_max:.6f}, "
              f"range={c_max-c_min:.6f}")


# ─── Main ───

if __name__ == '__main__':
    print("Thor Session #80 Part 2: Mechanism Investigation")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    all_results = {}

    expA_individual_vs_collective()
    expB_N_dependence()
    expC_without_adaptive()
    expD_no_clipping()
    expE_self_referential()
    expF_verify_clipping()

    print(f"\n{'='*70}")
    print(f"Completed: {datetime.now().isoformat()}")
