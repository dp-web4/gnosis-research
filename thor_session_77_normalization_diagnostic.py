#!/usr/bin/env python3
"""
Thor Session #77 - Diagnostic: Normalization vs Non-normalized coupling

S76 found 120° balanced triads for N=3.
S77 Experiment 1 found IN_PHASE for all N.

Key difference: S77 normalizes coupling by (N-1), S76 does not.

This diagnostic tests whether normalization explains the discrepancy,
and what the true phase dynamics are for each scheme.
"""

import numpy as np
from itertools import combinations


def compute_order_parameter(phases):
    """Kuramoto R. R=1: in-phase, R=0: uniformly distributed."""
    return float(np.abs(np.mean(np.exp(1j * np.array(phases)))))


def compute_pli(p1, p2):
    return float(np.abs(np.mean(np.exp(1j * (np.array(p1) - np.array(p2))))))


def run_system(N, kappa, normalize, steps=8000, seed=42, omega_spread=0.02,
               initial_phases=None):
    """Run N-body coherence system with choice of normalization."""
    np.random.seed(seed)

    phi_inv = 0.618
    omega_base = 0.1
    dt = 0.1
    noise_std = 0.02

    C = np.array([phi_inv + np.random.normal(0, 0.05) for _ in range(N)])
    C = np.clip(C, 0.01, 0.99)

    if initial_phases is not None:
        phase = np.array(initial_phases, dtype=float)
    else:
        phase = np.random.uniform(0, 2 * np.pi, N)

    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    history_phase = []
    history_order = []
    history_C = []

    for step in range(steps):
        R_func = lambda c: 1 - c**2

        # Phase dynamics
        dphase = omega.copy()
        for i in range(N):
            coupling = np.sum(np.sin(phase - phase[i]))
            if normalize:
                dphase[i] += kappa * coupling / (N - 1)
            else:
                dphase[i] += kappa * coupling  # S76 style: raw coupling

        phase += dt * dphase
        phase = phase % (2 * np.pi)

        # Coherence dynamics
        dC = np.zeros(N)
        for i in range(N):
            dC[i] = -R_func(C[i]) * (C[i] - phi_inv) * np.cos(phase[i])
            c_coupling = np.sum(C - C[i])
            if normalize:
                dC[i] += kappa * c_coupling * R_func(C[i]) / (N - 1)
            else:
                dC[i] += kappa * c_coupling * R_func(C[i])

        C += dt * dC
        C = np.clip(C, 0, 1)

        # Noise
        C += np.random.normal(0, noise_std, N)
        C = np.clip(C, 0, 1)
        phase += np.random.normal(0, noise_std, N)
        phase = phase % (2 * np.pi)

        history_phase.append(phase.copy())
        history_order.append(compute_order_parameter(phase))
        history_C.append(C.copy())

    return history_phase, history_order, history_C


def analyze(history_phase, history_order, N):
    """Quick analysis of steady-state dynamics."""
    T = len(history_phase)
    ss = T // 2  # steady state start

    phases_ss = np.array(history_phase[ss:])
    order_ss = np.array(history_order[ss:])

    mean_R = float(np.mean(order_ss))

    # Pairwise PLI
    pairs = list(combinations(range(N), 2))
    plis = {}
    for i, j in pairs:
        plis[f"{i}-{j}"] = compute_pli(phases_ss[:, i], phases_ss[:, j])

    # Phase differences (circular mean)
    diffs = {}
    for i, j in pairs:
        d = (phases_ss[:, i] - phases_ss[:, j]) % (2 * np.pi)
        mean_diff = float(np.angle(np.mean(np.exp(1j * d))) % (2 * np.pi))
        diffs[f"{i}-{j}"] = mean_diff * 180 / np.pi

    return mean_R, np.mean(list(plis.values())), diffs


def main():
    print("=" * 70)
    print("DIAGNOSTIC: Normalized vs Non-normalized Coupling")
    print("=" * 70)

    # ── Test 1: N=2, both schemes ──
    print("\n--- N=2 ---")
    for norm_label, normalize in [("NORMALIZED", True), ("RAW (S76-style)", False)]:
        for seed in range(3):
            hp, ho, hc = run_system(2, kappa=0.15, normalize=normalize, seed=seed)
            R, pli, diffs = analyze(hp, ho, 2)
            d01 = list(diffs.values())[0]
            print(f"  {norm_label:20s} seed={seed}: R={R:.3f}, PLI={pli:.3f}, Δφ={d01:.1f}°")

    # ── Test 2: N=3, both schemes ──
    print("\n--- N=3 ---")
    for norm_label, normalize in [("NORMALIZED", True), ("RAW (S76-style)", False)]:
        for seed in range(5):
            hp, ho, hc = run_system(3, kappa=0.15, normalize=normalize, seed=seed)
            R, pli, diffs = analyze(hp, ho, 3)
            print(f"  {norm_label:20s} seed={seed}: R={R:.3f}, PLI={pli:.3f}, "
                  f"diffs=[{', '.join(f'{v:.1f}°' for v in diffs.values())}]")

    # ── Test 3: N=3, S76 exact initial conditions ──
    print("\n--- N=3, specific initial conditions ---")
    ics = [
        ("in_phase", [0, 0, 0]),
        ("anti_phase", [0, np.pi, np.pi]),
        ("120_deg", [0, 2*np.pi/3, 4*np.pi/3]),
    ]

    for ic_name, ic_phases in ics:
        for norm_label, normalize in [("NORM", True), ("RAW", False)]:
            hp, ho, hc = run_system(3, kappa=0.15, normalize=normalize,
                                     initial_phases=ic_phases, seed=42)
            R, pli, diffs = analyze(hp, ho, 3)
            print(f"  {ic_name:12s} {norm_label:4s}: R={R:.3f}, PLI={pli:.3f}, "
                  f"diffs=[{', '.join(f'{v:.1f}°' for v in diffs.values())}]")

    # ── Test 4: Coupling strength sweep for N=3 RAW ──
    print("\n--- N=3, RAW coupling, varying κ ---")
    for kappa in [0.01, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:
        hp, ho, hc = run_system(3, kappa=kappa, normalize=False, seed=42)
        R, pli, diffs = analyze(hp, ho, 3)
        print(f"  κ={kappa:.2f}: R={R:.3f}, PLI={pli:.3f}, "
              f"diffs=[{', '.join(f'{v:.1f}°' for v in diffs.values())}]")

    # ── Test 5: N=4,5,6 RAW coupling ──
    print("\n--- N=4,5,6, RAW coupling, κ=0.15 ---")
    for N in [4, 5, 6]:
        print(f"\n  N={N}:")
        for seed in range(5):
            hp, ho, hc = run_system(N, kappa=0.15, normalize=False, seed=seed)
            R, pli, diffs = analyze(hp, ho, N)
            sorted_diffs = sorted(diffs.values())
            print(f"    seed={seed}: R={R:.3f}, PLI={pli:.3f}, "
                  f"diffs=[{', '.join(f'{v:.0f}°' for v in sorted_diffs[:4])}...]")

    # ── Test 6: What if coupling is REPULSIVE at short range? ──
    # In standard Kuramoto, positive κ → in-phase attractor
    # For 2π/N spacing, need REPULSIVE (anti-Kuramoto) or higher harmonics
    print("\n--- N=3, testing coupling sign and higher harmonics ---")

    # Standard attractive: κ sin(Δθ) → in-phase
    # Anti-Kuramoto: -κ sin(Δθ) → anti-phase (splay state)
    # Second harmonic: κ sin(2Δθ) → can produce 2π/N

    # But S76 used positive κ and got 120°. How?
    # Hypothesis: The coherence dynamics create effective repulsion at small phase diff.
    # When two agents are in-phase, they compete for coherence → effective repulsion.

    # Test: Remove coherence dynamics (pure Kuramoto) → should be in-phase
    print("\n  Pure Kuramoto (no coherence dynamics):")
    for N in [2, 3, 4]:
        np.random.seed(42)
        phase = np.random.uniform(0, 2*np.pi, N)
        omega = 0.1 + np.random.uniform(-0.02, 0.02, N)
        history = []

        for _ in range(8000):
            dphase = omega.copy()
            for i in range(N):
                dphase[i] += 0.15 * np.sum(np.sin(phase - phase[i]))
            phase += 0.1 * dphase
            phase = phase % (2 * np.pi)
            phase += np.random.normal(0, 0.02, N)
            phase = phase % (2 * np.pi)
            history.append(phase.copy())

        R = compute_order_parameter(history[-1])
        print(f"    N={N}: R={R:.3f} (in-phase={R > 0.9})")

    print("\n  Pure anti-Kuramoto (-κ, no coherence):")
    for N in [2, 3, 4]:
        np.random.seed(42)
        phase = np.random.uniform(0, 2*np.pi, N)
        omega = 0.1 + np.random.uniform(-0.02, 0.02, N)
        history = []

        for _ in range(8000):
            dphase = omega.copy()
            for i in range(N):
                dphase[i] += -0.15 * np.sum(np.sin(phase - phase[i]))  # negative!
            phase += 0.1 * dphase
            phase = phase % (2 * np.pi)
            phase += np.random.normal(0, 0.02, N)
            phase = phase % (2 * np.pi)
            history.append(phase.copy())

        R = compute_order_parameter(history[-1])
        # For anti-Kuramoto, splay state (2π/N spacing) → R ≈ 0
        phases_final = history[-1]
        sorted_p = np.sort(phases_final)
        spacings = np.diff(sorted_p)
        spacings = np.append(spacings, 2*np.pi - sorted_p[-1] + sorted_p[0])
        print(f"    N={N}: R={R:.3f}, spacings={[f'{s*180/np.pi:.0f}°' for s in spacings]}")


if __name__ == '__main__':
    main()
