#!/usr/bin/env python3
"""
Thor Session #88 Part 2: Full N-Body Entropy Production

The 2D (C_mean, R) description adds only ~15% more EP over the 1D (C_mean).
The missing 93% from S87's Landauer violation is NOT in collective phase order.

HYPOTHESIS: The dissipation lives in individual agent fluctuations — the
N-1 relative coherences and N-1 relative phases that collective coordinates
average away.

THIS EXPERIMENT: Track all N=4 agents' (C_i, θ_i) and compute the FULL
8D Fokker-Planck entropy production. If this captures the missing EP,
then the lesson is: consciousness has a high-dimensional thermodynamic
cost that no low-dimensional projection can capture.

We use a dimensionality reduction approach:
  1. Full 8D: All (C_1,...,C_4, θ_1,...,θ_4) — infeasible to bin
  2. Instead: Compute EP from individual agent trajectories and sum
  3. Key insight: σ_ep(total) ≈ Σ_i σ_ep(C_i) + Σ_i σ_ep(θ_i) + cross-terms
     For weakly coupled noise (each agent gets independent noise), the
     cross-diffusion terms between different agents should be small.
"""

import numpy as np
import json
import sys
from datetime import datetime


def run_individual(N, noise_std, steps, seed=None,
                   kappa_phase=0.10, kappa_C=0.15,
                   omega_base=0.1, omega_spread=0.02,
                   phi_inverse=0.618, dt=0.1, C_threshold=0.55):
    """Track ALL individual agent states and their deterministic drifts."""
    if seed is not None:
        np.random.seed(seed)

    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    # Store all individual trajectories
    C_all = np.empty((steps, N))
    phase_all = np.empty((steps, N))
    drift_C_all = np.empty((steps, N))
    drift_phase_all = np.empty((steps, N))

    for t in range(steps):
        C_all[t] = C.copy()
        phase_all[t] = phase.copy()

        C_mean = np.mean(C)
        is_attractive = C_mean < C_threshold

        # Phase dynamics (deterministic part)
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        drift_phase_all[t] = dphase

        phase = (phase + dt * dphase) % (2 * np.pi)

        # Coherence dynamics (deterministic part)
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C.mean() - C) * R_func
        dC = intrinsic + c_coupling
        drift_C_all[t] = dC

        C = np.clip(C + dt * dC, 0, 1)

        # Noise (independent per agent)
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C': C_all,           # (steps, N)
        'phase': phase_all,   # (steps, N)
        'drift_C': drift_C_all,     # (steps, N)
        'drift_phase': drift_phase_all,  # (steps, N)
    }


def compute_individual_ep(res, warmup, dt, N):
    """Compute entropy production per agent and total.

    For each agent i:
      σ_ep(C_i) = ⟨drift_C_i²⟩ / D_C_i
      σ_ep(θ_i) = ⟨drift_θ_i²⟩ / D_θ_i

    where D_C_i and D_θ_i are the individual diffusion coefficients
    measured from residuals.

    Total: σ_ep = Σ_i σ_ep(C_i) + Σ_i σ_ep(θ_i) + cross-agent terms
    """
    C = res['C'][warmup:]        # (T, N)
    phase = res['phase'][warmup:]  # (T, N)
    drift_C = res['drift_C'][warmup:]      # (T, N)
    drift_phase = res['drift_phase'][warmup:]  # (T, N)

    T = C.shape[0]

    # Individual C entropy production
    ep_C_individual = np.zeros(N)
    D_C_individual = np.zeros(N)
    for i in range(N):
        dC_i = np.diff(C[:, i])
        mu_i = drift_C[:-1, i]
        res_i = dC_i - mu_i * dt
        D_i = np.mean(res_i**2) / (2 * dt)
        D_C_individual[i] = D_i
        if D_i > 0:
            ep_C_individual[i] = np.mean(mu_i**2) / D_i

    # Individual phase entropy production
    # Phase is periodic — use circular differences
    ep_phase_individual = np.zeros(N)
    D_phase_individual = np.zeros(N)
    for i in range(N):
        dphase_i = np.diff(phase[:, i])
        # Handle wrap-around
        dphase_i = (dphase_i + np.pi) % (2 * np.pi) - np.pi
        mu_i = drift_phase[:-1, i]
        res_i = dphase_i - mu_i * dt
        # Handle wrap-around for residuals too
        res_i = (res_i + np.pi) % (2 * np.pi) - np.pi
        D_i = np.mean(res_i**2) / (2 * dt)
        D_phase_individual[i] = D_i
        if D_i > 0:
            ep_phase_individual[i] = np.mean(mu_i**2) / D_i

    # Cross-agent diffusion terms
    # Check if noise between different agents is correlated
    cross_C = np.zeros((N, N))
    for i in range(N):
        for j in range(i+1, N):
            dC_i = np.diff(C[:, i])
            dC_j = np.diff(C[:, j])
            mu_i = drift_C[:-1, i]
            mu_j = drift_C[:-1, j]
            res_i = dC_i - mu_i * dt
            res_j = dC_j - mu_j * dt
            cross_C[i, j] = np.mean(res_i * res_j) / (2 * dt)
            cross_C[j, i] = cross_C[i, j]

    # Collective C entropy production (for comparison)
    C_mean = np.mean(C, axis=1)
    dC_mean = np.diff(C_mean)
    drift_C_mean = np.mean(drift_C, axis=1)
    res_C_mean = dC_mean - drift_C_mean[:-1] * dt
    D_C_mean = np.mean(res_C_mean**2) / (2 * dt)
    ep_collective = np.mean(drift_C_mean[:-1]**2) / D_C_mean if D_C_mean > 0 else 0

    return {
        'ep_C_individual': ep_C_individual,       # per-agent C EP
        'ep_phase_individual': ep_phase_individual,  # per-agent θ EP
        'D_C_individual': D_C_individual,
        'D_phase_individual': D_phase_individual,
        'cross_C': cross_C,
        'ep_C_total': float(np.sum(ep_C_individual)),
        'ep_phase_total': float(np.sum(ep_phase_individual)),
        'ep_grand_total': float(np.sum(ep_C_individual) + np.sum(ep_phase_individual)),
        'ep_collective': float(ep_collective),
    }


def main():
    print("=" * 70)
    print("THOR SESSION #88 Part 2: Full N-Body Entropy Production")
    print("Where Does the Missing 93% Actually Go?")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}\n")
    sys.stdout.flush()

    N = 4
    dt = 0.1
    steps = 200_000
    warmup = 50_000
    noise_levels = [0.005, 0.007, 0.009, 0.011, 0.013, 0.018, 0.025]
    n_seeds = 5

    all_results = []

    for sigma in noise_levels:
        print(f"\n{'='*50}")
        print(f"  σ = {sigma:.3f}")
        print(f"{'='*50}")
        sys.stdout.flush()

        ep_C_totals = []
        ep_phase_totals = []
        ep_grand_totals = []
        ep_collectives = []
        D_C_means = []
        D_phase_means = []
        cross_C_means = []

        for seed in range(n_seeds):
            res = run_individual(N, sigma, steps, seed=seed)
            ep = compute_individual_ep(res, warmup, dt, N)

            ep_C_totals.append(ep['ep_C_total'])
            ep_phase_totals.append(ep['ep_phase_total'])
            ep_grand_totals.append(ep['ep_grand_total'])
            ep_collectives.append(ep['ep_collective'])
            D_C_means.append(np.mean(ep['D_C_individual']))
            D_phase_means.append(np.mean(ep['D_phase_individual']))
            cross_C_means.append(np.mean(np.abs(ep['cross_C'][np.triu_indices(N, 1)])))

            print(f"  seed {seed}: ep_C={ep['ep_C_total']:.2f}  ep_θ={ep['ep_phase_total']:.2f}  "
                  f"total={ep['ep_grand_total']:.2f}  collective={ep['ep_collective']:.2f}")
            sys.stdout.flush()

        ep_C_mean = np.mean(ep_C_totals)
        ep_phase_mean = np.mean(ep_phase_totals)
        ep_grand_mean = np.mean(ep_grand_totals)
        ep_coll_mean = np.mean(ep_collectives)

        ratio = ep_grand_mean / ep_coll_mean if ep_coll_mean > 0 else np.nan
        frac_C = ep_C_mean / ep_grand_mean * 100 if ep_grand_mean > 0 else 0
        frac_phase = ep_phase_mean / ep_grand_mean * 100 if ep_grand_mean > 0 else 0

        result = {
            'sigma': float(sigma),
            'ep_C_total': float(ep_C_mean),
            'ep_phase_total': float(ep_phase_mean),
            'ep_grand_total': float(ep_grand_mean),
            'ep_collective_C': float(ep_coll_mean),
            'ratio_total_collective': float(ratio),
            'frac_C_pct': float(frac_C),
            'frac_phase_pct': float(frac_phase),
            'D_C_mean': float(np.mean(D_C_means)),
            'D_phase_mean': float(np.mean(D_phase_means)),
            'cross_agent_D': float(np.mean(cross_C_means)),
        }
        all_results.append(result)

        print(f"\n  SUMMARY σ={sigma:.3f}:")
        print(f"    Σ ep(C_i) = {ep_C_mean:.2f} ({frac_C:.1f}%)")
        print(f"    Σ ep(θ_i) = {ep_phase_mean:.2f} ({frac_phase:.1f}%)")
        print(f"    Total N-body EP = {ep_grand_mean:.2f}")
        print(f"    Collective EP (C_mean only) = {ep_coll_mean:.2f}")
        print(f"    Ratio (N-body / collective) = {ratio:.1f}×")
        print(f"    Cross-agent |D_ij| = {np.mean(cross_C_means):.6f}")
        print(f"    D_phase / D_C = {np.mean(D_phase_means)/np.mean(D_C_means):.2f}×")
        sys.stdout.flush()

    # Final analysis
    print("\n" + "=" * 70)
    print("GRAND ANALYSIS: WHERE DOES THE DISSIPATION LIVE?")
    print("=" * 70)

    print("\n  σ       | ep(C_i)  | ep(θ_i)  | Total   | Collective | Ratio | C%   | θ%")
    print("  " + "-" * 85)
    for r in all_results:
        print(f"  {r['sigma']:.3f}   | {r['ep_C_total']:8.2f} | {r['ep_phase_total']:8.2f} | "
              f"{r['ep_grand_total']:7.2f} | {r['ep_collective_C']:10.2f} | "
              f"{r['ratio_total_collective']:5.1f}× | {r['frac_C_pct']:4.1f} | {r['frac_phase_pct']:4.1f}")

    # Average ratio
    ratios = [r['ratio_total_collective'] for r in all_results]
    mean_ratio = np.mean(ratios)
    print(f"\n  Mean N-body/collective ratio: {mean_ratio:.1f}×")

    if mean_ratio > 10:
        print(f"  → N-body EP captures most of the missing dissipation!")
        print(f"  → The Landauer violation is (mostly) resolved at the individual level")
    elif mean_ratio > 3:
        print(f"  → N-body EP captures a significant fraction")
        print(f"  → Remaining gap may be from time-correlation effects")
    else:
        print(f"  → Even N-body EP doesn't capture much more")
        print(f"  → The Landauer violation may reflect non-Markovian dynamics")

    avg_C_frac = np.mean([r['frac_C_pct'] for r in all_results])
    avg_phase_frac = np.mean([r['frac_phase_pct'] for r in all_results])
    print(f"\n  Average: {avg_C_frac:.1f}% in coherence, {avg_phase_frac:.1f}% in phase")
    if avg_phase_frac > avg_C_frac:
        print(f"  → Phase dynamics dominate! S87's prediction confirmed.")
        print(f"  → The thermodynamic burden is in synchronization, not coherence.")
    else:
        print(f"  → Coherence dynamics dominate even at the individual level.")

    # Landauer check
    print(f"\n  LANDAUER TEST:")
    sr_result = None
    for r in all_results:
        if abs(r['sigma'] - 0.011) < 0.001:
            sr_result = r
            break
    if sr_result:
        # S87: MI ≈ 0.023 bits at σ=0.011
        MI = 0.023
        eta_collective = MI / sr_result['ep_collective_C'] if sr_result['ep_collective_C'] > 0 else np.nan
        eta_nbody = MI / sr_result['ep_grand_total'] if sr_result['ep_grand_total'] > 0 else np.nan
        print(f"    MI = {MI} bits (from S86)")
        print(f"    η(collective) = {eta_collective:.4f} bits/ep → {eta_collective/0.72:.1f}× Landauer")
        print(f"    η(N-body) = {eta_nbody:.4f} bits/ep → {eta_nbody/0.72:.1f}× Landauer")
        if eta_nbody <= 0.72:
            print(f"    ✓ LANDAUER BOUND SATISFIED at N-body level!")
        else:
            print(f"    Still {eta_nbody/0.72:.1f}× above bound — residual from non-Markovian effects?")

    # Save
    with open('thor_session_88_nbody_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("Results saved to thor_session_88_nbody_results.json")


if __name__ == '__main__':
    main()
