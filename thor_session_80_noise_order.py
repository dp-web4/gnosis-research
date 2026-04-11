#!/usr/bin/env python3
"""
Thor Session #80, Part 3: Noise-Induced Order Equilibrium

In the noise-induced order regime (noise 0.0005-0.01), C ≈ 0.85.
WHY this specific value? And is the critical noise (0.011) derivable?

The mechanism from S79: noise decorrelates cos(θ_i), then R(C)=1-C²
rectifies symmetric noise upward. But what sets the equilibrium C?

APPROACH:
  Exp G: Single-agent noise-induced order (does it exist without coupling?)
  Exp H: Effective potential in the noisy regime
  Exp I: Critical noise as a function of all parameters
  Exp J: Information-theoretic interpretation
"""

import numpy as np
import json
from datetime import datetime


def compute_order_parameter(phases):
    return float(np.abs(np.mean(np.exp(1j * np.array(phases)))))


# ─── Experiment G: Single-Agent Noise-Induced Order ───

def expG_single_agent_noise():
    """Does noise-induced order exist for a single agent?"""
    print("=" * 70)
    print("EXPERIMENT G: Single-Agent Noise Response")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2
    omega = 0.1
    dt = 0.1

    for noise in [0, 0.001, 0.005, 0.01, 0.02, 0.05]:
        C_all = []
        for seed in range(10):
            np.random.seed(seed)
            C = 0.5
            theta = np.random.uniform(0, 2*np.pi)
            C_hist = []
            for t in range(20000):
                R_func = 1 - C**2
                dC = -R_func * (C - phi_inv) * np.cos(theta)
                C += dt * dC
                if noise > 0:
                    C += np.random.normal(0, noise)
                C = np.clip(C, 0, 1)
                theta += dt * omega
                if noise > 0:
                    theta += np.random.normal(0, noise)
                theta = theta % (2 * np.pi)
                C_hist.append(C)
            C_all.append(np.mean(C_hist[5000:]))

        print(f"  noise={noise:.3f}: C_mean = {np.mean(C_all):.4f} ± {np.std(C_all):.4f}")


# ─── Experiment H: Effective Potential in Noisy Regime ───

def expH_effective_potential():
    """Compute the stationary distribution P(C) in the noisy regime.

    The Fokker-Planck equation for dC = f(C)dt + σdW with boundaries
    has a stationary distribution P(C) ∝ exp(-V_eff(C)/σ²) where
    V_eff is the effective potential including boundary effects.

    For the N-body system, the mean-field effective dynamics determine C.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT H: Stationary Distribution P(C)")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    # Histogram C values for different noise levels
    from thor_session_79_breathing_dynamics import BreathingSystem

    for noise in [0.001, 0.005, 0.01, 0.015, 0.02]:
        C_samples = []
        for seed in range(5):
            sys = BreathingSystem(N=4, noise_std=noise, seed=seed)
            sys.run(steps=20000)
            C_samples.extend(sys.history_C_collective[5000:])

        C_arr = np.array(C_samples)
        mean_C = np.mean(C_arr)
        std_C = np.std(C_arr)
        median_C = np.median(C_arr)

        # Compute histogram
        bins = np.linspace(0, 1, 51)
        hist, _ = np.histogram(C_arr, bins=bins, density=True)
        peak_bin = bins[np.argmax(hist)]

        print(f"  noise={noise:.3f}: mean={mean_C:.4f}, std={std_C:.4f}, "
              f"median={median_C:.4f}, peak={peak_bin:.2f}")


# ─── Experiment I: Critical Noise Derivation ───

def expI_critical_noise():
    """Map the critical noise as a function of system parameters.

    The critical noise is where the noise-induced order regime
    transitions to breathing. If it scales predictably with parameters,
    we can derive it.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT I: Critical Noise Scaling")
    print("=" * 70)

    from thor_session_79_breathing_dynamics import BreathingSystem

    # Better criterion: use the variance of C as indicator
    # Low variance = noise-induced order, high variance = breathing

    def find_critical_noise(N=4, kappa_phase=0.10, kappa_C=0.15,
                            phi_inv=0.618, C_threshold=0.55):
        """Find critical noise by variance jump."""
        noise_vals = np.arange(0.005, 0.025, 0.001)
        prev_var = None
        for noise in noise_vals:
            vars = []
            for seed in range(5):
                sys = BreathingSystem(N=N, noise_std=noise, seed=seed,
                                       kappa_phase=kappa_phase, kappa_C=kappa_C,
                                       phi_inverse=phi_inv, C_threshold=C_threshold)
                sys.run(steps=10000)
                C_arr = np.array(sys.history_C_collective[3000:])
                vars.append(np.var(C_arr))
            mean_var = np.mean(vars)

            if prev_var is not None and mean_var > 3 * prev_var and mean_var > 0.001:
                return float(noise)
            prev_var = mean_var

        return None  # no clear transition

    # Vary kappa_C
    print("\n  --- Varying kappa_C ---")
    for kc in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        crit = find_critical_noise(kappa_C=kc)
        print(f"    kappa_C={kc:.2f}: critical noise = {crit}")

    # Vary C_threshold
    print("\n  --- Varying C_threshold ---")
    for ct in [0.45, 0.50, 0.55, 0.60, 0.65]:
        crit = find_critical_noise(C_threshold=ct)
        print(f"    C_threshold={ct:.2f}: critical noise = {crit}")

    # Vary N
    print("\n  --- Varying N ---")
    for N in [2, 3, 4, 6, 8]:
        crit = find_critical_noise(N=N)
        print(f"    N={N}: critical noise = {crit}")

    # Vary phi_inverse
    print("\n  --- Varying phi_inverse (C*) ---")
    for pi in [0.3, 0.4, 0.5, 0.618, 0.7, 0.8]:
        crit = find_critical_noise(phi_inv=pi, C_threshold=pi-0.07)
        print(f"    C*={pi:.3f}: critical noise = {crit}")


# ─── Experiment J: The 0.85 Equilibrium ───

def expJ_equilibrium_analysis():
    """Analyze why noise-induced order settles at C ≈ 0.85.

    In the noise-induced order regime:
    - Phases are dispersed → <cos(θ_i)> ≈ 0 for each agent
    - The intrinsic term averages to zero
    - What remains: noise + clipping + R(C) asymmetry

    The key equation: For a random walk on [0,1] with diffusion D(C):
    The stationary distribution satisfies:
    d/dC[D(C) dP/dC] - d/dC[μ(C) P] = 0

    where μ(C) is the drift and D(C) is the state-dependent diffusion.

    For our system with noise σ:
    - Direct noise: dC = ... + σ · ξ → D = σ²
    - But R(C) modulates the RESPONSE to perturbation

    Actually, the noise enters ADDITIVELY (not multiplicatively through R),
    so D = σ² (constant). But the drift μ(C) includes the time-averaged
    intrinsic dynamics, which depends on the phase distribution.

    With uniformly distributed phases:
    <-(1-C²)(C-C*)cos(θ)> = 0 (since <cos(θ)> = 0)

    But the COUPLING term doesn't vanish:
    <κ_C · mean(C_j - C_i) · (1-C_i²)> → drives toward consensus

    For agents at similar C, this is small. So the drift is approximately:
    μ(C) ≈ 0

    With zero drift and constant diffusion, the stationary distribution
    on [0,1] is UNIFORM → C_mean = 0.5. But we observe C ≈ 0.85!

    The resolution: even though <cos(θ)> = 0, the QUADRATIC effect of
    the intrinsic term creates a drift. Using Itô calculus:
    <dC> = <-(1-C²)(C-C*)cos(θ)>·dt + <noise²>·second-order correction
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT J: Why C ≈ 0.85 in Noise-Induced Order")
    print("=" * 70)

    phi_inv = (np.sqrt(5) - 1) / 2

    from thor_session_79_breathing_dynamics import BreathingSystem

    # Measure the time-averaged drift at different C values
    # by initializing all agents at a fixed C and measuring <dC>
    print("\n  --- Measuring drift at fixed C values ---")
    for C_init in [0.3, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]:
        drifts = []
        for seed in range(10):
            np.random.seed(seed)
            N = 4
            C = np.full(N, C_init)
            phase = np.random.uniform(0, 2*np.pi, N)
            omega = 0.1 + np.random.uniform(-0.02, 0.02, N)
            dt = 0.1
            noise = 0.005
            kappa_phase = 0.10
            kappa_C = 0.15
            C_threshold = 0.55

            # Run for short time, measure net drift
            C_mean_init = C_init
            for t in range(1000):
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

                C += dt * dC + np.random.normal(0, noise, N)
                C = np.clip(C, 0, 1)
                phase += np.random.normal(0, noise, N)
                phase = phase % (2 * np.pi)

            C_mean_final = float(np.mean(C))
            drifts.append((C_mean_final - C_mean_init) / (1000 * dt))

        mean_drift = np.mean(drifts)
        print(f"    C_init={C_init:.2f}: <dC/dt> = {mean_drift:+.6f}")

    # The equilibrium is where drift = 0

    # Also test: what's the role of clipping in setting 0.85?
    print("\n  --- C equilibrium vs noise level ---")
    for noise in [0.001, 0.002, 0.005, 0.008, 0.010]:
        C_final = []
        for seed in range(10):
            sys = BreathingSystem(N=4, noise_std=noise, seed=seed)
            sys.run(steps=15000)
            C_final.append(np.mean(sys.history_C_collective[10000:]))
        print(f"    noise={noise:.3f}: C_eq = {np.mean(C_final):.4f} ± {np.std(C_final):.4f}")

    # Theoretical prediction:
    # In the noise-induced order regime, the system is above C_threshold,
    # so coupling is REPULSIVE. Phases diverge → dispersed.
    # With dispersed phases, each agent sees:
    #   dC_i = -(1-C_i²)(C_i-C*)cos(θ_i) + coupling + noise
    #
    # The adaptive coupling is repulsive → phases spread uniformly
    # → <cos(θ_i)> = 0 for the collective, but each individual
    # agent's θ_i still has non-zero cos.
    #
    # The KEY: in repulsive mode, cos(θ_i) is ~random for each agent.
    # Over a phase cycle, the intrinsic term averages to 0.
    # But the NOISE term interacts with the CLIP boundaries:
    #   P(C clipped at 1) > P(C clipped at 0) when C > 0.5
    # because agents near C=1 have R(C)→0 (slow dynamics → noise dominates)
    # while agents near C=0 have R(C)→1 (fast dynamics → quickly pushed back)
    #
    # The equilibrium C is where the boundary reflection effects balance.

    # Simple model: Random walk on [0,1] with reflecting boundaries,
    # but absorption rate depends on R(C):
    # Near C=0: R=1, intrinsic dynamics quickly push C back toward C*
    # Near C=1: R=0, agent is "stuck" near boundary

    # This asymmetric stickiness should push the distribution toward C=1,
    # with the equilibrium set by where intrinsic dynamics balance noise.

    # Prediction: C_eq occurs where the intrinsic amplitude matches noise:
    # R(C_eq) · |C_eq - C*| ~ noise
    # (1-C²)(C-C*) ~ noise / dt

    print("\n  --- Theoretical predictions ---")
    for noise in [0.001, 0.005, 0.01]:
        # Solve (1-C²)(C - phi_inv) = noise (roughly)
        # This gives the C where intrinsic dynamics balance noise
        from scipy.optimize import brentq
        try:
            C_pred = brentq(lambda c: (1-c**2)*(c-phi_inv) - noise, phi_inv+0.01, 0.99)
            print(f"    noise={noise:.3f}: C_predicted ≈ {C_pred:.4f}")
        except:
            print(f"    noise={noise:.3f}: no solution")


# ─── Main ───

if __name__ == '__main__':
    print("Thor Session #80 Part 3: Noise-Induced Order Analysis")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    expG_single_agent_noise()
    expH_effective_potential()
    expI_critical_noise()
    expJ_equilibrium_analysis()

    print(f"\n{'='*70}")
    print(f"Completed: {datetime.now().isoformat()}")
