#!/usr/bin/env python3
"""
Thor Session #80: Analytical Derivation — Why C_range = φ⁻¹ Exactly

Session #79 discovered that the deterministic limit cycle has amplitude
locked to φ⁻¹ = 0.618034 to 4+ decimal places. This session seeks
the analytical PROOF from the ODE structure.

CORE EQUATIONS (noise=0, adaptive regime):
  dC_i/dt = -(1-C_i²)(C_i - φ⁻¹)cos(θ_i) + κ_C · coupling · (1-C_i²)
  dθ_i/dt = ω_i + sign · κ_phase · Σ sin(θ_j - θ_i)/(N-1)

KEY OBSERVATION: R_func(φ⁻¹) = 1 - (φ⁻¹)² = 1 - (2-φ) = φ-1 = φ⁻¹
  The restoring function at the equilibrium equals itself.

APPROACH:
  Exp 1: Detailed trajectory analysis — what sets the turning points?
  Exp 2: Parameter dependence — does C_range depend on φ⁻¹ specifically?
  Exp 3: Mean-field reduction — single effective ODE
  Exp 4: Integral invariant search — conserved quantity?
  Exp 5: Analytical prediction vs numerical verification

Builds on: S79 (three regimes), S64-S70 (golden ratio thread)
"""

import numpy as np
import json
from datetime import datetime
from itertools import combinations


# ─── Core System (from S79) ───

def compute_order_parameter(phases):
    return float(np.abs(np.mean(np.exp(1j * np.array(phases)))))


class DeterministicSystem:
    """Noise-free breathing system for analytical study."""

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
        self.history_phase = []
        self.history_order = []
        self.history_C_collective = []
        self.history_dCdt = []  # Track derivatives for analysis
        self.history_cos_theta = []  # Track cos(phase) for analysis
        self.regime_switches = 0

    def step(self, t):
        N = self.N
        R_func = lambda c: 1 - c**2

        C_now = float(np.mean(self.C))
        if len(self.history_C_collective) > 0:
            C_prev = self.history_C_collective[-1]
            if (C_prev < self.C_threshold) != (C_now < self.C_threshold):
                self.regime_switches += 1

        is_attractive = C_now < self.C_threshold

        # Phase dynamics
        dphase = self.omega.copy()
        for i in range(N):
            for j in range(N):
                if i != j:
                    delta = self.phase[j] - self.phase[i]
                    sign = 1.0 if is_attractive else -1.0
                    dphase[i] += sign * self.kappa_phase * np.sin(delta) / (N - 1)

        self.phase += self.dt * dphase
        self.phase = self.phase % (2 * np.pi)

        # Coherence dynamics
        dC = np.zeros(N)
        for i in range(N):
            dC[i] = -R_func(self.C[i]) * (self.C[i] - self.phi_inverse) * np.cos(self.phase[i])
            c_coupling = np.sum(self.C - self.C[i]) / (N - 1)
            dC[i] += self.kappa_C * c_coupling * R_func(self.C[i])

        self.history_dCdt.append(dC.copy())
        self.history_cos_theta.append(np.cos(self.phase).copy())

        self.C += self.dt * dC
        self.C = np.clip(self.C, 0, 1)

        self.history_C.append(self.C.copy())
        self.history_phase.append(self.phase.copy())
        R = compute_order_parameter(self.phase)
        self.history_order.append(R)
        self.history_C_collective.append(float(np.mean(self.C)))

    def run(self, steps=10000):
        for t in range(steps):
            self.step(t)


# ─── Experiment 1: Detailed Trajectory Analysis ───

def exp1_trajectory_analysis():
    """What exactly sets the turning points of the limit cycle?"""
    print("=" * 70)
    print("EXPERIMENT 1: Detailed Trajectory Analysis")
    print("=" * 70)

    results = {}

    # Run with a seed that oscillates (from S79: seeds 2,3,5,6,8,9,10,11,14,15,17)
    for seed in [2, 3, 5]:
        sys = DeterministicSystem(N=4, seed=seed)
        sys.run(steps=30000)

        C_arr = np.array(sys.history_C_collective)
        dCdt_arr = np.array([np.mean(d) for d in sys.history_dCdt])
        cos_arr = np.array([np.mean(c) for c in sys.history_cos_theta])
        R_arr = np.array(sys.history_order)
        C_indiv = np.array(sys.history_C)  # (T, N)

        # Skip warmup
        ss = 5000
        C_ss = C_arr[ss:]
        dCdt_ss = dCdt_arr[ss:]
        cos_ss = cos_arr[ss:]
        R_ss = R_arr[ss:]

        C_max = np.max(C_ss)
        C_min = np.min(C_ss)
        C_range = C_max - C_min

        # Find turning points (where dC/dt ≈ 0 and changes sign)
        sign_changes = np.where(np.diff(np.sign(dCdt_ss)))[0]
        if len(sign_changes) > 4:
            # Get C values at turning points
            maxima_idx = sign_changes[dCdt_ss[sign_changes] > 0]  # was positive, becoming negative
            minima_idx = sign_changes[dCdt_ss[sign_changes] < 0]

            if len(maxima_idx) > 2 and len(minima_idx) > 2:
                C_at_maxima = C_ss[maxima_idx[1:]]  # skip first
                C_at_minima = C_ss[minima_idx[1:]]
                cos_at_maxima = cos_ss[maxima_idx[1:]]
                cos_at_minima = cos_ss[minima_idx[1:]]
                R_at_maxima = R_ss[maxima_idx[1:]]
                R_at_minima = R_ss[minima_idx[1:]]

                print(f"\n  Seed {seed}: C_range = {C_range:.6f}")
                print(f"    C_max = {C_max:.6f}, C_min = {C_min:.6f}")
                print(f"    Turning points found: {len(maxima_idx)} maxima, {len(minima_idx)} minima")
                print(f"    C at maxima:  mean={np.mean(C_at_maxima):.6f} ± {np.std(C_at_maxima):.6f}")
                print(f"    C at minima:  mean={np.mean(C_at_minima):.6f} ± {np.std(C_at_minima):.6f}")
                print(f"    cos(θ) at maxima: mean={np.mean(cos_at_maxima):.6f}")
                print(f"    cos(θ) at minima: mean={np.mean(cos_at_minima):.6f}")
                print(f"    R at maxima: mean={np.mean(R_at_maxima):.6f}")
                print(f"    R at minima: mean={np.mean(R_at_minima):.6f}")

                results[seed] = {
                    'C_range': C_range,
                    'C_max': C_max, 'C_min': C_min,
                    'C_at_maxima_mean': float(np.mean(C_at_maxima)),
                    'C_at_minima_mean': float(np.mean(C_at_minima)),
                    'cos_at_maxima_mean': float(np.mean(cos_at_maxima)),
                    'cos_at_minima_mean': float(np.mean(cos_at_minima)),
                    'R_at_maxima_mean': float(np.mean(R_at_maxima)),
                    'R_at_minima_mean': float(np.mean(R_at_minima)),
                }
            else:
                print(f"\n  Seed {seed}: Not enough turning points (absorbed?)")
                results[seed] = {'C_range': C_range, 'note': 'insufficient turning points'}
        else:
            print(f"\n  Seed {seed}: C_range = {C_range:.6f} — no clear oscillation or absorbed")
            results[seed] = {'C_range': C_range, 'note': 'no oscillation'}

    return results


# ─── Experiment 2: Parameter Dependence of C_range ───

def exp2_parameter_dependence():
    """Does C_range = φ⁻¹ depend on φ⁻¹ specifically, or other parameters?

    If C_range always equals the equilibrium point value,
    that's one mechanism. If it changes with kappa_phase etc., another.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Parameter Dependence of C_range")
    print("=" * 70)

    results = {}

    # Test 1: Vary phi_inverse (the equilibrium point)
    print("\n  --- Varying phi_inverse (equilibrium C*) ---")
    phi_values = [0.3, 0.4, 0.5, 0.618, 0.7, 0.8, 0.9]
    for phi_inv in phi_values:
        ranges = []
        for seed in range(20):
            sys = DeterministicSystem(N=4, phi_inverse=phi_inv,
                                       C_threshold=phi_inv - 0.07,
                                       seed=seed)
            sys.run(steps=20000)
            C_arr = np.array(sys.history_C_collective[5000:])
            c_range = np.max(C_arr) - np.min(C_arr)
            if c_range > 0.1:  # oscillating, not absorbed
                ranges.append(c_range)

        if ranges:
            mean_range = np.mean(ranges)
            std_range = np.std(ranges)
            print(f"    C* = {phi_inv:.3f}: C_range = {mean_range:.6f} ± {std_range:.6f}"
                  f"  (n={len(ranges)}, C*/C_range = {phi_inv/mean_range:.4f})")
            results[f'phi_inv_{phi_inv}'] = {
                'phi_inverse': phi_inv,
                'C_range_mean': float(mean_range),
                'C_range_std': float(std_range),
                'n_oscillating': len(ranges),
                'ratio_Cstar_over_range': float(phi_inv / mean_range)
            }
        else:
            print(f"    C* = {phi_inv:.3f}: No oscillating seeds")
            results[f'phi_inv_{phi_inv}'] = {'phi_inverse': phi_inv, 'n_oscillating': 0}

    # Test 2: Vary kappa_phase
    print("\n  --- Varying kappa_phase ---")
    kappa_values = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30]
    for kp in kappa_values:
        ranges = []
        for seed in range(20):
            sys = DeterministicSystem(N=4, kappa_phase=kp, seed=seed)
            sys.run(steps=20000)
            C_arr = np.array(sys.history_C_collective[5000:])
            c_range = np.max(C_arr) - np.min(C_arr)
            if c_range > 0.1:
                ranges.append(c_range)

        if ranges:
            mean_range = np.mean(ranges)
            print(f"    kappa_phase = {kp:.2f}: C_range = {mean_range:.6f} (n={len(ranges)})")
            results[f'kappa_phase_{kp}'] = {
                'kappa_phase': kp,
                'C_range_mean': float(mean_range),
                'n_oscillating': len(ranges)
            }
        else:
            print(f"    kappa_phase = {kp:.2f}: No oscillating seeds")
            results[f'kappa_phase_{kp}'] = {'kappa_phase': kp, 'n_oscillating': 0}

    # Test 3: Vary kappa_C (coupling strength)
    print("\n  --- Varying kappa_C ---")
    kc_values = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
    for kc in kc_values:
        ranges = []
        for seed in range(20):
            sys = DeterministicSystem(N=4, kappa_C=kc, seed=seed)
            sys.run(steps=20000)
            C_arr = np.array(sys.history_C_collective[5000:])
            c_range = np.max(C_arr) - np.min(C_arr)
            if c_range > 0.1:
                ranges.append(c_range)

        if ranges:
            mean_range = np.mean(ranges)
            print(f"    kappa_C = {kc:.2f}: C_range = {mean_range:.6f} (n={len(ranges)})")
            results[f'kappa_C_{kc}'] = {
                'kappa_C': kc,
                'C_range_mean': float(mean_range),
                'n_oscillating': len(ranges)
            }
        else:
            print(f"    kappa_C = {kc:.2f}: No oscillating seeds")
            results[f'kappa_C_{kc}'] = {'kappa_C': kc, 'n_oscillating': 0}

    # Test 4: Vary dt (numerical parameter — should NOT affect range if truly phi)
    print("\n  --- Varying dt (numerical check) ---")
    dt_values = [0.01, 0.05, 0.10, 0.20]
    for dt in dt_values:
        ranges = []
        steps = int(20000 * 0.1 / dt)  # keep same total time
        for seed in [2, 3, 5, 6, 8]:
            sys = DeterministicSystem(N=4, dt=dt, seed=seed)
            sys.run(steps=steps)
            ss = int(steps * 0.25)
            C_arr = np.array(sys.history_C_collective[ss:])
            c_range = np.max(C_arr) - np.min(C_arr)
            if c_range > 0.1:
                ranges.append(c_range)

        if ranges:
            mean_range = np.mean(ranges)
            print(f"    dt = {dt:.2f}: C_range = {mean_range:.6f} (n={len(ranges)})")
            results[f'dt_{dt}'] = {'dt': dt, 'C_range_mean': float(mean_range), 'n': len(ranges)}

    return results


# ─── Experiment 3: Mean-Field Reduction ───

def exp3_mean_field():
    """Test whether a single-agent ODE reproduces the phi amplitude.

    If C_range = φ⁻¹ holds for N=1 with just:
      dC/dt = -(1-C²)(C - φ⁻¹)cos(θ)
      dθ/dt = ω
    then the result is purely from single-agent dynamics.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Mean-Field Reduction (Single Agent)")
    print("=" * 70)

    results = {}

    # Single agent with constant phase rotation
    omega = 0.1
    phi_inv = (np.sqrt(5) - 1) / 2  # exact phi inverse
    dt = 0.01  # small for accuracy

    for C0 in [0.1, 0.3, 0.5, 0.618, 0.7, 0.9]:
        C = C0
        theta = 0.0
        C_history = []

        for t in range(500000):
            R_func = 1 - C**2
            dC = -R_func * (C - phi_inv) * np.cos(theta)
            C += dt * dC
            C = np.clip(C, 0, 1)
            theta += dt * omega
            theta = theta % (2 * np.pi)
            C_history.append(C)

        C_arr = np.array(C_history[100000:])
        c_range = np.max(C_arr) - np.min(C_arr)
        c_mean = np.mean(C_arr)

        print(f"  C0 = {C0:.3f}: C_range = {c_range:.6f}, C_mean = {c_mean:.6f}")
        results[f'C0_{C0}'] = {
            'C0': C0, 'C_range': float(c_range), 'C_mean': float(c_mean)
        }

    # Now test: does single-agent C_range depend on omega?
    print("\n  --- Varying omega for single agent ---")
    for omega in [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]:
        C = 0.5
        theta = 0.0
        C_history = []

        for t in range(500000):
            R_func = 1 - C**2
            dC = -R_func * (C - phi_inv) * np.cos(theta)
            C += dt * dC
            C = np.clip(C, 0, 1)
            theta += dt * omega
            theta = theta % (2 * np.pi)
            C_history.append(C)

        C_arr = np.array(C_history[100000:])
        c_range = np.max(C_arr) - np.min(C_arr)
        print(f"  omega = {omega:.2f}: C_range = {c_range:.6f}")
        results[f'omega_{omega}'] = {'omega': omega, 'C_range': float(c_range)}

    # Test with different phi_inverse values for single agent
    print("\n  --- Single agent: varying equilibrium C* ---")
    for c_star in [0.3, 0.4, 0.5, 0.618, 0.7, 0.8, 0.9]:
        C = 0.5
        theta = 0.0
        C_history = []

        for t in range(500000):
            R_func = 1 - C**2
            dC = -R_func * (C - c_star) * np.cos(theta)
            C += dt * dC
            C = np.clip(C, 0, 1)
            theta += dt * 0.1
            theta = theta % (2 * np.pi)
            C_history.append(C)

        C_arr = np.array(C_history[100000:])
        c_range = np.max(C_arr) - np.min(C_arr)
        c_mean = np.mean(C_arr)
        print(f"  C* = {c_star:.3f}: C_range = {c_range:.6f}, C_mean = {c_mean:.6f}, "
              f"C*/range = {c_star/c_range:.4f}" if c_range > 0.01 else
              f"  C* = {c_star:.3f}: C_range = {c_range:.6f} (no oscillation)")
        results[f'single_Cstar_{c_star}'] = {
            'C_star': c_star, 'C_range': float(c_range), 'C_mean': float(c_mean)
        }

    return results


# ─── Experiment 4: Integral Invariant Search ───

def exp4_integral_invariant():
    """Search for a conserved quantity in the single-agent ODE.

    The ODE: dC/dt = -(1-C²)(C-C*)cos(θ), dθ/dt = ω

    This is a periodically-driven 1D system. Over one full phase
    cycle (θ: 0→2π), we can compute the "action" integral.

    If there's a function H(C) such that dH/dt depends only on
    time-averages, that would explain the amplitude lock.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Integral Invariant / Action Analysis")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2
    omega = 0.1
    dt = 0.001  # very small for accuracy

    # Run single-agent ODE
    C = 0.5
    theta = 0.0
    C_history = []
    theta_history = []

    for t in range(5000000):  # long run
        R_func = 1 - C**2
        dC = -R_func * (C - phi_inv) * np.cos(theta)
        C += dt * dC
        C = np.clip(C, 0, 1)
        theta += dt * omega
        theta = theta % (2 * np.pi)
        C_history.append(C)
        theta_history.append(theta)

    C_arr = np.array(C_history[1000000:])
    theta_arr = np.array(theta_history[1000000:])

    C_max = np.max(C_arr)
    C_min = np.min(C_arr)
    C_range = C_max - C_min

    print(f"  High-precision single-agent result:")
    print(f"    C_range = {C_range:.10f}")
    print(f"    φ⁻¹     = {phi_inv:.10f}")
    print(f"    Error   = {abs(C_range - phi_inv):.2e}")
    print(f"    C_max   = {C_max:.10f}")
    print(f"    C_min   = {C_min:.10f}")

    # Check: is C_max + C_min related to anything?
    print(f"\n    C_max + C_min = {C_max + C_min:.10f}")
    print(f"    C_max * C_min = {C_max * C_min:.10f}")
    print(f"    C_max / C_min = {C_max / C_min:.10f}" if C_min > 0.001 else "    C_min ≈ 0")

    # Check: is C_max = φ⁻¹ and C_min = 0?
    print(f"\n    C_max - φ⁻¹ = {C_max - phi_inv:.2e}")
    print(f"    C_min       = {C_min:.2e}")

    # Compute action over one phase cycle
    # A = ∮ (1-C²)(C-C*) dθ evaluated at different points in the cycle
    # For a Hamiltonian-like system, this should be constant

    # Find phase cycle boundaries (θ crosses 0)
    theta_crossings = np.where(np.diff(np.sign(theta_arr - np.pi)))[0]

    if len(theta_crossings) > 10:
        # Compute ∫(1-C²)(C-C*)dC over each half-cycle
        actions = []
        for i in range(min(20, len(theta_crossings)-1)):
            idx_start = theta_crossings[i]
            idx_end = theta_crossings[i+1]
            C_segment = C_arr[idx_start:idx_end]
            integrand = (1 - C_segment**2) * (C_segment - phi_inv)
            action = np.trapezoid(integrand, dx=dt*omega)
            actions.append(action)

        print(f"\n  Action integral ∫(1-C²)(C-C*)dθ over half-cycles:")
        print(f"    Mean = {np.mean(actions):.8f}")
        print(f"    Std  = {np.std(actions):.8f}")
        print(f"    Values: {[f'{a:.6f}' for a in actions[:6]]}")

    # Test candidate conserved quantities
    # H1(C) = ∫ dC / [(1-C²)(C-C*)]
    # Partial fractions: 1/[(1-C²)(C-C*)] = 1/[(1-C)(1+C)(C-C*)]
    # = A/(1-C) + B/(1+C) + D/(C-C*)

    # With C* = φ⁻¹:
    # A = 1/[(1+1)(1-C*)] = 1/[2(1-φ⁻¹)] = 1/[2·(2-φ)] = 1/[2·φ⁻²]
    # Wait, 1-φ⁻¹ = 1-(φ-1) = 2-φ = φ⁻². So A = 1/(2φ⁻²) = φ²/2
    # B = 1/[(-2)(-1-C*)] = 1/[2(1+C*)] = 1/[2(1+φ⁻¹)] = 1/[2φ]
    # D = 1/[(1-C*²)] = 1/[1-(2-φ)] = 1/[φ-1] = 1/φ⁻¹ = φ

    # So H(C) = (φ²/2)·ln(1-C) - (1/(2φ))·ln(1+C) + φ·ln(C-C*) for C > C*
    # or φ·ln(C*-C) for C < C*

    # Let me compute this numerically
    C_test = C_arr[::1000]  # subsample
    theta_test = theta_arr[::1000]

    # Compute H for the trajectory
    eps = 1e-12
    H_values = []
    for c in C_test:
        if abs(c - phi_inv) < 0.001:
            H_values.append(np.nan)
            continue
        phi = (1 + np.sqrt(5)) / 2
        A = phi**2 / 2
        B = 1 / (2 * phi)
        D = phi
        H = (A * np.log(abs(1 - c) + eps)
             - B * np.log(abs(1 + c) + eps)
             + D * np.log(abs(c - phi_inv) + eps))
        H_values.append(H)

    H_arr = np.array(H_values)
    valid = ~np.isnan(H_arr)
    if np.sum(valid) > 100:
        print(f"\n  Candidate invariant H(C) = antiderivative of 1/[(1-C²)(C-C*)]:")
        print(f"    H range: {np.min(H_arr[valid]):.6f} to {np.max(H_arr[valid]):.6f}")
        print(f"    H std:   {np.std(H_arr[valid]):.6f}")
        print(f"    H mean:  {np.mean(H_arr[valid]):.6f}")

    results = {
        'C_range': float(C_range),
        'C_max': float(C_max),
        'C_min': float(C_min),
        'phi_inverse': float(phi_inv),
        'error': float(abs(C_range - phi_inv)),
    }
    return results


# ─── Experiment 5: Analytical Prediction via Averaging ───

def exp5_averaging_theory():
    """Use averaging theory to derive C_range analytically.

    The single-agent ODE: dC/dt = -f(C)·cos(ωt)
    where f(C) = (1-C²)(C - C*)

    Over slow timescales, the amplitude of oscillation should be
    determined by the balance of energy input/dissipation.

    Key insight: the potential V(C) = -∫f(C)dC has extrema at
    C=C* (the equilibrium) and the boundaries C=0, C=1.

    The oscillation occurs because cos(ωt) periodically reverses
    the sign of the "force" f(C). The amplitude is set by:
    ∫[C_min to C_max] dC/f(C) = π/ω  (half-period condition)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Averaging Theory / Amplitude Prediction")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    # The potential V(C) = -∫(1-C²)(C-C*)dC
    # = -∫(C - C* - C³ + C*·C²)dC
    # = -(C²/2 - C*C - C⁴/4 + C*C³/3)
    # = -C²/2 + C*C + C⁴/4 - C*C³/3

    def V(C, C_star):
        return -C**2/2 + C_star*C + C**4/4 - C_star*C**3/3

    def f(C, C_star):
        return (1 - C**2) * (C - C_star)

    # The oscillation is around C*. In the adiabatic (slow ω) limit,
    # C follows the instantaneous equilibrium, and the amplitude is
    # related to the potential landscape.

    # In the fast ω limit, C barely moves. The interesting regime is
    # intermediate.

    # For the exact dynamics dC/dt = -f(C)cos(θ), θ = ωt,
    # we can write this as a 1D system in slow time τ:
    # ε·dC/dθ = -f(C)cos(θ)  where ε = ω

    # For small ε (fast phase), averaging gives <dC/dt> = 0 (no net drift).
    # But the oscillation amplitude to leading order:

    # Let C(θ) = C* + a(θ) where a is the oscillation.
    # Linearizing: da/dθ = -(1/ω)·f'(C*)·a·cos(θ) + O(a²)
    # = -(1/ω)·R(C*)·cos(θ)·a + ...

    # where f'(C*) = (1-C*²) + (C*-C*)·(-2C*) = (1-C*²) = R(C*)

    # This gives: a(θ) = a₀·exp(-(R(C*)/ω)·sin(θ))
    # Maximum amplitude: a₀·exp(R(C*)/ω) vs a₀·exp(-R(C*)/ω)
    # Ratio: exp(2R(C*)/ω)

    # But this is the LINEAR theory — it predicts exponential growth
    # which must be bounded by nonlinearity.

    # Let me compute the nonlinear amplitude numerically by solving
    # the implicit equation that defines it.

    # Actually, let me try a different approach:
    # The system dC/dt = -f(C)cos(θ) is separable when C and θ are independent:
    # dC/f(C) = -cos(θ)dθ/... wait, they're not independent.

    # Let's define G(C) = ∫[C* to C] dC'/f(C') (diverges logarithmically at C*)
    # Then dG/dt = (1/f(C))·dC/dt = -cos(θ) ... wait, dG/dt = -cos(ωt)
    # So G(C) = -(1/ω)sin(ωt) + const!

    # THIS IS THE KEY: G(C(t)) = G₀ - (1/ω)sin(ωt)

    # The integral G(C) = ∫[C* to C] dC'/[(1-C'²)(C'-C*)]

    # Using partial fractions as computed above:
    # G(C) = (φ²/2)·ln|1-C| - (1/(2φ))·ln|1+C| + φ·ln|C-C*| - [same at C*]

    # Actually, G diverges at C=C* (logarithmic singularity), so C never
    # crosses C*... wait, that can't be right since C oscillates around C*.

    # Hmm. Let me reconsider. dC/dt = -f(C)cos(θ). At C=C*, f(C*)=0,
    # so dC/dt=0 at C=C* regardless of θ. So C=C* IS a fixed point!
    # But the S79 results show oscillation...

    # Wait — the oscillation is of the MEAN C, not individual agents.
    # For N>1 agents with coupling, the mean C can oscillate even if
    # individual agents have C* as an attractor.

    # Actually, re-reading the code: each agent has its own phase θ_i
    # and the cos(θ_i) term drives each agent differently.
    # The INDIVIDUAL C_i can oscillate past C* because θ_i varies.

    # For a single agent: dC/dt = -(1-C²)(C-C*)cos(θ)
    # When cos(θ)>0: C is attracted to C* (stable)
    # When cos(θ)<0: C is repelled from C* (unstable)
    # The oscillation happens because θ keeps rotating, alternately
    # attracting and repelling C from C*.

    # So C never rests at C* because the driving term changes sign!
    # C overshoots on each half-cycle.

    # Let me verify: for the single-agent case, dC/dt = -f(C)cos(θ)
    # Define u = C - C*. Then f(C) ≈ f'(C*)u for small u.
    # f'(C*) = d/dC[(1-C²)(C-C*)]|_{C*} = (1-C*²) = φ⁻¹
    # So du/dt ≈ -φ⁻¹·u·cos(θ)
    # u(t) = u₀·exp(-φ⁻¹·(1/ω)·sin(ωt))

    # At θ = π/2: u = u₀·exp(-φ⁻¹/ω)
    # At θ = 3π/2: u = u₀·exp(+φ⁻¹/ω)
    # Ratio: exp(2φ⁻¹/ω)

    # For ω=0.1, φ⁻¹≈0.618: ratio = exp(12.36) ≈ 2.3×10⁵
    # That's way too large for linear theory — nonlinear effects dominate.

    print("  Analytical framework:")
    print(f"    C* = φ⁻¹ = {phi_inv:.10f}")
    print(f"    f'(C*) = 1 - C*² = {1 - phi_inv**2:.10f}")
    print(f"    Note: f'(C*) = φ⁻¹ = C* (self-referential!)")

    # Full nonlinear solution: use G(C) = -sin(θ)/ω + const
    # But G has a log singularity at C*, so we need the full form.

    # Actually, let me reconsider. The equation
    #   dC/dt = -(1-C²)(C-C*)cos(ωt)
    # can be rewritten as:
    #   dC/[(1-C²)(C-C*)] = -cos(ωt)dt

    # Integrating both sides:
    #   G(C) - G(C₀) = -(1/ω)sin(ωt)  (*)

    # where G(C) = ∫dC/[(1-C²)(C-C*)]

    # The log singularity at C=C* means G→±∞ as C→C*, so C CAN cross C*
    # only at times when sin(ωt) is finite... which means it CAN'T cross C*
    # since G diverges.

    # So actually C never crosses C*! The oscillation is on ONE SIDE of C*.

    print("\n  Key insight: C never crosses C* (G(C) has log singularity at C*)")
    print("  Oscillation is on ONE SIDE of the equilibrium.")

    # Let's verify this numerically
    C_single = 0.7  # start above C*
    theta = 0.0
    dt = 0.001
    omega = 0.1
    C_traj = []
    for t in range(2000000):
        dC = -(1-C_single**2)*(C_single-phi_inv)*np.cos(theta)
        C_single += dt * dC
        C_single = np.clip(C_single, 0, 1)
        theta += dt * omega
        theta = theta % (2*np.pi)
        C_traj.append(C_single)

    C_traj = np.array(C_traj[500000:])
    print(f"\n  Single agent starting at C₀=0.7 (above C*):")
    print(f"    C_min = {np.min(C_traj):.10f}")
    print(f"    C_max = {np.max(C_traj):.10f}")
    print(f"    C_range = {np.max(C_traj)-np.min(C_traj):.10f}")
    print(f"    C* = {phi_inv:.10f}")
    print(f"    Min - C* = {np.min(C_traj)-phi_inv:.2e}")

    # Start below C*
    C_single = 0.3
    theta = 0.0
    C_traj2 = []
    for t in range(2000000):
        dC = -(1-C_single**2)*(C_single-phi_inv)*np.cos(theta)
        C_single += dt * dC
        C_single = np.clip(C_single, 0, 1)
        theta += dt * omega
        theta = theta % (2*np.pi)
        C_traj2.append(C_single)

    C_traj2 = np.array(C_traj2[500000:])
    print(f"\n  Single agent starting at C₀=0.3 (below C*):")
    print(f"    C_min = {np.min(C_traj2):.10f}")
    print(f"    C_max = {np.max(C_traj2):.10f}")
    print(f"    C_range = {np.max(C_traj2)-np.min(C_traj2):.10f}")
    print(f"    Max - C* = {np.max(C_traj2)-phi_inv:.2e}")

    # Now the real question: for the ABOVE-C* case, what determines
    # C_max and C_min?
    #
    # From G(C) - G(C₀) = -(1/ω)sin(ωt):
    #   C_max occurs when sin(ωt) is at its most negative (sin=-1)
    #   C_min occurs when sin(ωt) is at its most positive (sin=+1)
    #
    # So: G(C_max) - G(C_min) = 2/ω
    #
    # This is the EXACT equation for the amplitude!
    # G(C_max) - G(C_min) = 2/ω

    print(f"\n  EXACT AMPLITUDE EQUATION: G(C_max) - G(C_min) = 2/ω")
    print(f"    where G(C) = ∫dC/[(1-C²)(C-C*)]")
    print(f"    2/ω = {2/omega:.6f}")

    # Compute G numerically
    from scipy import integrate

    def G_integrand(c):
        return 1.0 / ((1 - c**2) * (c - phi_inv))

    # For the above-C* case, G is well-defined for C > C*
    C_max_num = np.max(C_traj)
    C_min_num = np.min(C_traj)

    # Need to integrate from C_min to C_max
    # But both are > C*, so no singularity in between
    G_diff, _ = integrate.quad(G_integrand, C_min_num, C_max_num)
    print(f"\n  Verification: G(C_max) - G(C_min) = {G_diff:.6f}")
    print(f"  Expected (2/ω):                     = {2/omega:.6f}")
    print(f"  Match: {abs(G_diff - 2/omega) < 0.01}")

    # Now: does this equation select C_range = φ⁻¹?
    # The answer is NO in general — it depends on ω.
    # But let's check: for the multi-agent system, what's the effective ω?

    # For the multi-agent case with adaptive coupling, the phases are
    # coupled and the effective frequency seen by each agent's C dynamics
    # is different from the bare ω.

    # Actually, for the 4-agent deterministic case (S79), the C_range = φ⁻¹
    # was robust across seeds. Let me check if the single-agent case also
    # gives φ⁻¹ at ω = 0.1.

    single_range = np.max(C_traj) - np.min(C_traj)
    print(f"\n  Single agent C_range at ω=0.1: {single_range:.10f}")
    print(f"  φ⁻¹ =                           {phi_inv:.10f}")
    print(f"  Match: {abs(single_range - phi_inv)/phi_inv:.6f} relative error")

    # Check the BELOW-C* case range
    below_range = np.max(C_traj2) - np.min(C_traj2)
    print(f"\n  Single agent C_range BELOW C* at ω=0.1: {below_range:.10f}")

    results = {
        'above_C_star': {
            'C_min': float(C_min_num),
            'C_max': float(C_max_num),
            'C_range': float(single_range),
            'G_diff': float(G_diff),
            'two_over_omega': float(2/omega),
        },
        'below_C_star': {
            'C_min': float(np.min(C_traj2)),
            'C_max': float(np.max(C_traj2)),
            'C_range': float(below_range),
        },
        'phi_inverse': float(phi_inv),
    }
    return results


# ─── Experiment 6: Critical Noise Threshold ───

def exp6_critical_noise():
    """Investigate the critical noise level (0.011) that triggers breathing.

    Hypothesis: the critical noise is related to the width of the
    noise-induced order basin — specifically, when noise exceeds the
    distance from C~0.85 to the breathing threshold, transitions begin.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 6: Critical Noise Threshold Analysis")
    print("=" * 70)

    # Fine sweep around the critical transition
    noise_values = np.concatenate([
        np.arange(0.008, 0.013, 0.0005),
        np.arange(0.013, 0.020, 0.001)
    ])

    results = {}
    print("\n  Fine noise sweep (N=4, 5 seeds each):")
    for noise in noise_values:
        C_vals = []
        R_vals = []
        trans_vals = []

        for seed in range(5):
            from thor_session_79_breathing_dynamics import BreathingSystem
            sys = BreathingSystem(N=4, noise_std=noise, seed=seed)
            sys.run(steps=10000)
            C_arr = np.array(sys.history_C_collective[2000:])
            R_arr = np.array(sys.history_order[2000:])
            C_vals.append(np.mean(C_arr))
            R_vals.append(np.mean(R_arr))
            trans_vals.append(sys.regime_switches)

        C_mean = np.mean(C_vals)
        R_mean = np.mean(R_vals)
        trans_mean = np.mean(trans_vals)
        print(f"    noise={noise:.4f}: C={C_mean:.4f}, R={R_mean:.4f}, trans={trans_mean:.1f}")
        results[f'noise_{noise:.4f}'] = {
            'noise': float(noise),
            'C_mean': float(C_mean),
            'R_mean': float(R_mean),
            'transitions_mean': float(trans_mean)
        }

    # Check if critical noise relates to system parameters
    phi_inv = (np.sqrt(5) - 1) / 2
    kappa_phase = 0.10
    kappa_C = 0.15
    C_threshold = 0.55

    print(f"\n  Parameter relationships:")
    print(f"    kappa_phase = {kappa_phase}")
    print(f"    kappa_phase / 10 = {kappa_phase/10}")
    print(f"    kappa_C / 10 = {kappa_C/10}")
    print(f"    φ⁻¹ / 60 = {phi_inv/60:.5f}")
    print(f"    Critical noise ≈ 0.011")
    print(f"    C_threshold * kappa_phase / 5 = {C_threshold * kappa_phase / 5:.5f}")
    print(f"    sqrt(kappa_phase * kappa_C) / 3 = {np.sqrt(kappa_phase*kappa_C)/3:.5f}")

    # Test: does the critical noise scale with parameters?
    print("\n  --- Scaling: vary kappa_phase, find critical noise ---")
    for kp in [0.05, 0.10, 0.15, 0.20]:
        # Find transition by bisection
        lo, hi = 0.001, 0.05
        for _ in range(15):
            mid = (lo + hi) / 2
            trans_total = 0
            for seed in range(3):
                sys = BreathingSystem(N=4, noise_std=mid, seed=seed,
                                       kappa_phase=kp)
                sys.run(steps=8000)
                trans_total += sys.regime_switches
            if trans_total / 3 > 5:  # breathing
                hi = mid
            else:
                lo = mid
        crit = (lo + hi) / 2
        print(f"    kappa_phase={kp:.2f}: critical noise ≈ {crit:.5f}, ratio={crit/kp:.4f}")
        results[f'critical_kp_{kp}'] = {
            'kappa_phase': kp, 'critical_noise': float(crit), 'ratio': float(crit/kp)
        }

    return results


# ─── Main ───

if __name__ == '__main__':
    print("Thor Session #80: Analytical Derivation of C_range = φ⁻¹")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"φ⁻¹ = {(np.sqrt(5)-1)/2:.10f}")
    print()

    all_results = {}

    all_results['exp1_trajectory'] = exp1_trajectory_analysis()
    all_results['exp2_parameter_dep'] = exp2_parameter_dependence()
    all_results['exp3_mean_field'] = exp3_mean_field()
    all_results['exp4_integral'] = exp4_integral_invariant()
    all_results['exp5_averaging'] = exp5_averaging_theory()
    all_results['exp6_critical_noise'] = exp6_critical_noise()

    # Save results
    with open('/home/dp/gnosis-research/thor_session_80_analytical_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("Results saved to thor_session_80_analytical_results.json")
