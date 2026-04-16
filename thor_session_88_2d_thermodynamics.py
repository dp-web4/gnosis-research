#!/usr/bin/env python3
"""
Thor Session #88: The 2D Thermodynamic Landscape — Where Does 93% Go?

Session 87 discovered that the 1D description (C_mean alone) captures information
but misses ~93% of dissipation. The 14× Landauer violation and FT slope of 0.28
both point to the same gap: phase dynamics (θ) carry most of the thermodynamic
burden.

THIS SESSION: Extend to 2D (C_mean, R) where R = |⟨exp(iθ)⟩| is the Kuramoto
phase synchronization order parameter. Measure the full 2D Fokker-Planck
description: drift vector μ(C,R), diffusion matrix D(C,R), and from these
compute the complete 2D entropy production.

QUESTIONS:
  1. Does including R resolve the Landauer violation?
  2. Does the FT slope improve from 0.28 toward 1.0?
  3. Where in (C,R) space does dissipation concentrate?
  4. Are there probability currents (circulation) in 2D?
  5. How much of the "missing 93%" is in R vs cross-terms?

KEY EXPERIMENTS:
  A: 2D trajectory collection — track (C_mean, R) with increments
  B: 2D Fokker-Planck reconstruction — bin-wise drift and diffusion
  C: 2D entropy production landscape — σ_ep(C, R)
  D: 2D probability currents — J(C, R) field
  E: 2D fluctuation theorem — path entropy production
  F: Landauer efficiency with 2D entropy
  G: Decomposition — how much EP comes from C, R, and cross-terms?

Builds on: S87 (1D entropy production), S86 (SR), S83 (Fokker-Planck)
"""

import numpy as np
import json
import sys
from datetime import datetime


def run_2d(N, noise_std, steps, seed=None,
           kappa_phase=0.10, kappa_C=0.15,
           omega_base=0.1, omega_spread=0.02,
           phi_inverse=0.618, dt=0.1, C_threshold=0.55):
    """Simulation tracking BOTH collective coordinates: C_mean and R.

    Returns full 2D trajectory with drift components for both coordinates.
    """
    if seed is not None:
        np.random.seed(seed)

    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    C_collective = np.empty(steps)
    R_collective = np.empty(steps)
    psi_collective = np.empty(steps)  # mean phase angle
    drift_C = np.empty(steps)
    drift_R = np.empty(steps)
    switches = 0
    prev_attractive = True
    switch_times = []

    for t in range(steps):
        C_mean = np.mean(C)
        C_collective[t] = C_mean

        # Kuramoto order parameter: R * exp(i*psi) = (1/N) * sum(exp(i*phase_j))
        z = np.mean(np.exp(1j * phase))
        R_collective[t] = abs(z)
        psi_collective[t] = np.angle(z)

        is_attractive = C_mean < C_threshold
        if t > 0 and is_attractive != prev_attractive:
            switches += 1
            switch_times.append(t)
        prev_attractive = is_attractive

        # Phase dynamics
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)

        # Compute R drift BEFORE adding noise (deterministic part)
        # R changes due to phase dynamics:
        # dR/dt ≈ (R_after_drift - R_before) / dt
        phase_after_drift = (phase + dt * dphase) % (2 * np.pi)
        z_after = np.mean(np.exp(1j * phase_after_drift))
        R_after_drift = abs(z_after)
        drift_R[t] = (R_after_drift - R_collective[t]) / dt

        phase = phase_after_drift

        # Coherence dynamics
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C.mean() - C) * R_func
        dC_det = intrinsic + c_coupling
        drift_C[t] = np.mean(dC_det)

        C = np.clip(C + dt * dC_det, 0, 1)

        # Noise on both
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C': C_collective,
        'R': R_collective,
        'psi': psi_collective,
        'drift_C': drift_C,
        'drift_R': drift_R,
        'switches': switches,
        'switch_times': np.array(switch_times),
    }


# ─── Experiment A: 2D Trajectory Statistics ───

def expA_trajectory_stats():
    """Collect 2D trajectories and characterize the (C, R) joint distribution."""
    print("=" * 70)
    print("EXPERIMENT A: 2D Trajectory Statistics in (C, R) Space")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 200_000
    warmup = 50_000
    noise_levels = [0.005, 0.009, 0.011, 0.013, 0.018, 0.025]
    results = []

    for sigma in noise_levels:
        C_all, R_all = [], []
        for seed in range(5):
            res = run_2d(N, sigma, steps, seed=seed)
            C_all.extend(res['C'][warmup:])
            R_all.extend(res['R'][warmup:])

        C_arr = np.array(C_all)
        R_arr = np.array(R_all)

        # Joint statistics
        corr = np.corrcoef(C_arr, R_arr)[0, 1]

        result = {
            'sigma': float(sigma),
            'C_mean': float(np.mean(C_arr)),
            'C_std': float(np.std(C_arr)),
            'R_mean': float(np.mean(R_arr)),
            'R_std': float(np.std(R_arr)),
            'CR_corr': float(corr),
        }
        results.append(result)
        print(f"  σ={sigma:.3f}: ⟨C⟩={result['C_mean']:.3f}±{result['C_std']:.3f}  "
              f"⟨R⟩={result['R_mean']:.3f}±{result['R_std']:.3f}  "
              f"ρ(C,R)={corr:.3f}")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    corrs = [r['CR_corr'] for r in results]
    print(f"  C-R correlations range from {min(corrs):.3f} to {max(corrs):.3f}")
    if max(abs(c) for c in corrs) > 0.3:
        print(f"  → C and R are significantly correlated — cross-terms matter!")
    else:
        print(f"  → C and R are weakly correlated — may decompose independently")

    return results


# ─── Experiment B: 2D Fokker-Planck Reconstruction ───

def expB_2d_fokker_planck():
    """Reconstruct the 2D Fokker-Planck equation in (C, R) space.

    For each bin (C_i, R_j):
      - Drift vector: μ(C,R) = (⟨dC/dt⟩, ⟨dR/dt⟩)
      - Diffusion matrix: D(C,R) = ⟨(dx - μdt)(dx - μdt)^T⟩ / (2dt)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT B: 2D Fokker-Planck Reconstruction")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    sigma = 0.011  # SR optimum
    steps = 500_000
    warmup = 100_000
    dt = 0.1
    n_seeds = 8

    # Collect long trajectories
    C_all, R_all, dC_all, dR_all = [], [], [], []
    for seed in range(n_seeds):
        print(f"  Running seed {seed+1}/{n_seeds}...", end='', flush=True)
        res = run_2d(N, sigma, steps, seed=seed)
        C = res['C'][warmup:]
        R = res['R'][warmup:]

        dC = np.diff(C)
        dR = np.diff(R)

        C_all.extend(C[:-1])
        R_all.extend(R[:-1])
        dC_all.extend(dC)
        dR_all.extend(dR)
        print(f" done (switches={res['switches']})")
        sys.stdout.flush()

    C_arr = np.array(C_all)
    R_arr = np.array(R_all)
    dC_arr = np.array(dC_all)
    dR_arr = np.array(dR_all)

    # Bin the 2D space
    n_C_bins = 15
    n_R_bins = 12
    C_edges = np.linspace(0, 1, n_C_bins + 1)
    R_edges = np.linspace(0, 1, n_R_bins + 1)
    C_centers = 0.5 * (C_edges[:-1] + C_edges[1:])
    R_centers = 0.5 * (R_edges[:-1] + R_edges[1:])

    # Digitize
    C_idx = np.clip(np.digitize(C_arr, C_edges) - 1, 0, n_C_bins - 1)
    R_idx = np.clip(np.digitize(R_arr, R_edges) - 1, 0, n_R_bins - 1)

    # Compute drift and diffusion in each bin
    drift_field = np.full((n_C_bins, n_R_bins, 2), np.nan)
    diff_field = np.full((n_C_bins, n_R_bins, 2, 2), np.nan)
    count_field = np.zeros((n_C_bins, n_R_bins), dtype=int)
    ep_field = np.full((n_C_bins, n_R_bins), np.nan)

    min_count = 100  # need enough samples for statistics

    for i in range(n_C_bins):
        for j in range(n_R_bins):
            mask = (C_idx == i) & (R_idx == j)
            count = mask.sum()
            count_field[i, j] = count
            if count < min_count:
                continue

            dC_bin = dC_arr[mask]
            dR_bin = dR_arr[mask]

            # Drift
            mu_C = np.mean(dC_bin) / dt
            mu_R = np.mean(dR_bin) / dt
            drift_field[i, j] = [mu_C, mu_R]

            # Diffusion matrix: D_ij = ⟨(dx_i - μ_i*dt)(dx_j - μ_j*dt)⟩ / (2*dt)
            res_C = dC_bin - mu_C * dt
            res_R = dR_bin - mu_R * dt

            D_CC = np.mean(res_C**2) / (2 * dt)
            D_RR = np.mean(res_R**2) / (2 * dt)
            D_CR = np.mean(res_C * res_R) / (2 * dt)

            D = np.array([[D_CC, D_CR], [D_CR, D_RR]])
            diff_field[i, j] = D

            # Local entropy production: σ_ep = μ^T D^{-1} μ
            try:
                D_inv = np.linalg.inv(D)
                mu = np.array([mu_C, mu_R])
                ep = mu @ D_inv @ mu
                ep_field[i, j] = ep
            except np.linalg.LinAlgError:
                pass

    # Report
    print(f"\n  2D grid: {n_C_bins} × {n_R_bins} = {n_C_bins*n_R_bins} bins")
    populated = np.sum(count_field >= min_count)
    print(f"  Populated bins (≥{min_count} samples): {populated}")

    # Find where EP concentrates
    valid = ~np.isnan(ep_field)
    if valid.any():
        ep_values = ep_field[valid]
        counts_valid = count_field[valid]

        # Weighted average EP
        weights = counts_valid / counts_valid.sum()
        ep_weighted = np.sum(ep_values * weights)

        print(f"\n  Entropy production landscape:")
        print(f"    Weighted mean σ_ep(2D) = {ep_weighted:.4f}")
        print(f"    Min σ_ep = {ep_values.min():.4f}")
        print(f"    Max σ_ep = {ep_values.max():.4f}")
        print(f"    Median σ_ep = {np.median(ep_values):.4f}")

        # Find peak location
        peak_flat = np.nanargmax(ep_field)
        peak_i, peak_j = np.unravel_index(peak_flat, ep_field.shape)
        print(f"    Peak at C≈{C_centers[peak_i]:.2f}, R≈{R_centers[peak_j]:.2f} "
              f"(σ_ep={ep_field[peak_i, peak_j]:.2f})")

        # Compare to S87's 1D value
        print(f"\n  Comparison to S87 (1D):")
        print(f"    S87 σ_ep(1D, σ=0.011) = 18.04")
        print(f"    S88 σ_ep(2D, σ=0.011) = {ep_weighted:.4f}")
        ratio = ep_weighted / 18.04 if ep_weighted > 0 else 0
        print(f"    Ratio 2D/1D = {ratio:.2f}×")

    # Diffusion matrix structure
    valid_D = ~np.isnan(diff_field[:,:,0,0])
    if valid_D.any():
        D_CC_vals = diff_field[valid_D, 0, 0]
        D_RR_vals = diff_field[valid_D, 1, 1]
        D_CR_vals = diff_field[valid_D, 0, 1]

        print(f"\n  Diffusion matrix structure:")
        print(f"    ⟨D_CC⟩ = {np.mean(D_CC_vals):.6f}")
        print(f"    ⟨D_RR⟩ = {np.mean(D_RR_vals):.6f}")
        print(f"    ⟨D_CR⟩ = {np.mean(D_CR_vals):.6f}")
        print(f"    |D_CR|/√(D_CC·D_RR) = {abs(np.mean(D_CR_vals))/np.sqrt(np.mean(D_CC_vals)*np.mean(D_RR_vals)):.3f}")
        print(f"    D_RR/D_CC = {np.mean(D_RR_vals)/np.mean(D_CC_vals):.2f}×")

    return {
        'C_centers': C_centers.tolist(),
        'R_centers': R_centers.tolist(),
        'count_field': count_field.tolist(),
        'drift_field_C': drift_field[:,:,0].tolist(),
        'drift_field_R': drift_field[:,:,1].tolist(),
        'D_CC': diff_field[:,:,0,0].tolist(),
        'D_RR': diff_field[:,:,1,1].tolist(),
        'D_CR': diff_field[:,:,0,1].tolist(),
        'ep_field': ep_field.tolist(),
        'ep_weighted': float(ep_weighted) if valid.any() else None,
    }


# ─── Experiment C: 2D Entropy Production vs Noise ───

def expC_2d_ep_vs_noise():
    """Compare 1D and 2D entropy production across noise levels."""
    print("\n" + "=" * 70)
    print("EXPERIMENT C: 2D Entropy Production Rate vs Noise")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 300_000
    warmup = 80_000
    dt = 0.1
    noise_levels = [0.005, 0.007, 0.009, 0.011, 0.013, 0.015, 0.018, 0.025]
    results = []

    for sigma in noise_levels:
        ep_1d_list = []
        ep_2d_list = []

        for seed in range(5):
            res = run_2d(N, sigma, steps, seed=seed)
            C = res['C'][warmup:]
            R = res['R'][warmup:]
            mu_C_arr = res['drift_C'][warmup:]
            mu_R_arr = res['drift_R'][warmup:]

            dC = np.diff(C)
            dR = np.diff(R)

            # Empirical drift
            mu_C = np.mean(dC) / dt
            mu_R = np.mean(dR) / dt

            # Empirical diffusion (from residuals)
            res_C = dC - mu_C_arr[:-1] * dt
            res_R = dR - mu_R_arr[:-1] * dt

            D_CC = np.mean(res_C**2) / (2 * dt)
            D_RR = np.mean(res_R**2) / (2 * dt)
            D_CR = np.mean(res_C * res_R) / (2 * dt)

            # 1D entropy production (C only)
            ep_1d = np.mean(mu_C_arr[:-1]**2) / D_CC
            ep_1d_list.append(ep_1d)

            # 2D entropy production: σ_ep = μ^T D^{-1} μ (averaged over time)
            D = np.array([[D_CC, D_CR], [D_CR, D_RR]])
            try:
                D_inv = np.linalg.inv(D)
                # Time-averaged EP using local drift values
                ep_2d_vals = []
                for tt in range(0, len(mu_C_arr) - 1, 100):  # subsample for speed
                    mu_vec = np.array([mu_C_arr[tt], mu_R_arr[tt]])
                    ep_2d_vals.append(mu_vec @ D_inv @ mu_vec)
                ep_2d = np.mean(ep_2d_vals)
            except np.linalg.LinAlgError:
                ep_2d = np.nan

            ep_2d_list.append(ep_2d)

        ep_1d_mean = np.nanmean(ep_1d_list)
        ep_2d_mean = np.nanmean(ep_2d_list)
        ratio = ep_2d_mean / ep_1d_mean if ep_1d_mean > 0 else np.nan

        result = {
            'sigma': float(sigma),
            'ep_1d': float(ep_1d_mean),
            'ep_2d': float(ep_2d_mean),
            'ratio_2d_1d': float(ratio),
        }
        results.append(result)
        print(f"  σ={sigma:.3f}: σ_ep(1D)={ep_1d_mean:.4f}  σ_ep(2D)={ep_2d_mean:.4f}  "
              f"ratio={ratio:.2f}×")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    ratios = [r['ratio_2d_1d'] for r in results if not np.isnan(r['ratio_2d_1d'])]
    print(f"  Mean 2D/1D EP ratio: {np.mean(ratios):.2f}×")
    print(f"  If ratio ≈ 14: R captures ALL the missing dissipation")
    print(f"  If ratio < 14: Individual agent fluctuations also contribute")
    print(f"  If ratio > 14: Something unexpected!")

    # Where does the extra EP come from?
    print(f"\n  Missing dissipation recovery:")
    for r in results:
        if not np.isnan(r['ratio_2d_1d']):
            pct_recovered = (r['ratio_2d_1d'] - 1) / (14 - 1) * 100
            print(f"    σ={r['sigma']:.3f}: recovered {pct_recovered:.1f}% of missing EP")

    return results


# ─── Experiment D: 2D Probability Currents ───

def expD_probability_currents():
    """Map probability currents J(C, R) in the 2D space.

    J = P · (μ - D·∇ln(P))

    In steady state, ∇·J = 0. Non-zero curl(J) indicates non-equilibrium.
    Simpler approach: J_i = P · μ_i (probability flux).
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT D: 2D Probability Currents")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    sigma = 0.011
    steps = 500_000
    warmup = 100_000
    dt = 0.1
    n_seeds = 8

    C_all, R_all, dC_all, dR_all = [], [], [], []
    for seed in range(n_seeds):
        print(f"  Collecting seed {seed+1}/{n_seeds}...", end='', flush=True)
        res = run_2d(N, sigma, steps, seed=seed)
        C = res['C'][warmup:]
        R = res['R'][warmup:]
        C_all.extend(C[:-1])
        R_all.extend(R[:-1])
        dC_all.extend(np.diff(C))
        dR_all.extend(np.diff(R))
        print(" done")
        sys.stdout.flush()

    C_arr = np.array(C_all)
    R_arr = np.array(R_all)
    dC_arr = np.array(dC_all)
    dR_arr = np.array(dR_all)

    # Coarser grid for currents
    n_bins = 10
    C_edges = np.linspace(0, 1, n_bins + 1)
    R_edges = np.linspace(0, 1, n_bins + 1)
    C_centers = 0.5 * (C_edges[:-1] + C_edges[1:])
    R_centers = 0.5 * (R_edges[:-1] + R_edges[1:])

    C_idx = np.clip(np.digitize(C_arr, C_edges) - 1, 0, n_bins - 1)
    R_idx = np.clip(np.digitize(R_arr, R_edges) - 1, 0, n_bins - 1)

    total = len(C_arr)
    J_C = np.full((n_bins, n_bins), np.nan)
    J_R = np.full((n_bins, n_bins), np.nan)
    P = np.zeros((n_bins, n_bins))

    for i in range(n_bins):
        for j in range(n_bins):
            mask = (C_idx == i) & (R_idx == j)
            count = mask.sum()
            P[i, j] = count / total
            if count < 50:
                continue

            # Probability current = P * mean_velocity
            mean_vC = np.mean(dC_arr[mask]) / dt
            mean_vR = np.mean(dR_arr[mask]) / dt
            J_C[i, j] = P[i, j] * mean_vC
            J_R[i, j] = P[i, j] * mean_vR

    # Compute curl (∂J_R/∂C - ∂J_C/∂R) as a measure of circulation
    curl = np.full((n_bins - 1, n_bins - 1), np.nan)
    dC_bin = C_centers[1] - C_centers[0]
    dR_bin = R_centers[1] - R_centers[0]

    for i in range(n_bins - 1):
        for j in range(n_bins - 1):
            if (np.isnan(J_R[i, j]) or np.isnan(J_R[i+1, j]) or
                np.isnan(J_C[i, j]) or np.isnan(J_C[i, j+1])):
                continue
            dJR_dC = (J_R[i+1, j] - J_R[i, j]) / dC_bin
            dJC_dR = (J_C[i, j+1] - J_C[i, j]) / dR_bin
            curl[i, j] = dJR_dC - dJC_dR

    valid_curl = curl[~np.isnan(curl)]
    if len(valid_curl) > 0:
        print(f"\n  Probability current curl (non-equilibrium circulation):")
        print(f"    Mean |curl| = {np.mean(np.abs(valid_curl)):.6f}")
        print(f"    Max |curl| = {np.max(np.abs(valid_curl)):.6f}")
        print(f"    Mean curl (signed) = {np.mean(valid_curl):.6f}")
        if np.mean(valid_curl) > 0:
            print(f"    → Net COUNTERCLOCKWISE circulation (C↑ precedes R↑)")
        else:
            print(f"    → Net CLOCKWISE circulation (R↑ precedes C↑)")

    # Find strongest current locations
    J_mag = np.sqrt(np.where(np.isnan(J_C), 0, J_C)**2 +
                    np.where(np.isnan(J_R), 0, J_R)**2)
    peak_flat = np.argmax(J_mag)
    peak_i, peak_j = np.unravel_index(peak_flat, J_mag.shape)
    print(f"\n  Strongest current at C≈{C_centers[peak_i]:.2f}, R≈{R_centers[peak_j]:.2f}")
    print(f"    |J| = {J_mag[peak_i, peak_j]:.6f}")
    print(f"    Direction: dC={J_C[peak_i, peak_j]:.6f}, dR={J_R[peak_i, peak_j]:.6f}")

    # Detailed balance violation in 2D
    # Compare P(x→y) vs P(y→x) for adjacent bins
    db_violations = []
    for i in range(n_bins):
        for j in range(n_bins):
            # Check horizontal transitions (C direction)
            if i < n_bins - 1:
                mask_here = (C_idx == i) & (R_idx == j)
                mask_next = (C_idx == i+1) & (R_idx == j)
                n_here = mask_here.sum()
                n_next = mask_next.sum()
                if n_here > 50 and n_next > 50:
                    # Forward: fraction going from i to i+1
                    fwd = np.mean(dC_arr[mask_here] > 0)
                    bwd = np.mean(dC_arr[mask_next] < 0)
                    if fwd > 0 and bwd > 0:
                        db_violations.append(abs(np.log(fwd * n_here / (bwd * n_next))))

    if db_violations:
        print(f"\n  2D Detailed balance violations:")
        print(f"    Mean |ln(P_fwd/P_bwd)| = {np.mean(db_violations):.4f}")
        print(f"    Max |ln(P_fwd/P_bwd)| = {np.max(db_violations):.4f}")

    return {
        'J_C': J_C.tolist(),
        'J_R': J_R.tolist(),
        'P': P.tolist(),
        'curl_mean': float(np.mean(valid_curl)) if len(valid_curl) > 0 else None,
        'curl_abs_mean': float(np.mean(np.abs(valid_curl))) if len(valid_curl) > 0 else None,
        'C_centers': C_centers.tolist(),
        'R_centers': R_centers.tolist(),
    }


# ─── Experiment E: 2D Fluctuation Theorem ───

def expE_2d_fluctuation_theorem():
    """Test the fluctuation theorem with 2D (C, R) entropy production.

    FT: P(σ_ep = +A) / P(σ_ep = -A) = exp(A)

    Tested by plotting ln(P(+A)/P(-A)) vs A; slope should be 1.0.
    S87 got slope = 0.28 with 1D. Does 2D get closer?
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT E: 2D Fluctuation Theorem")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    sigma = 0.011
    steps = 500_000
    warmup = 100_000
    dt = 0.1
    segment_lengths = [10, 50, 100]

    # First, get the global diffusion matrix
    print("  Measuring global 2D diffusion matrix...")
    sys.stdout.flush()

    C_all_res, R_all_res = [], []
    dC_all, dR_all, mu_C_all, mu_R_all = [], [], [], []

    for seed in range(8):
        res = run_2d(N, sigma, steps, seed=seed)
        C = res['C'][warmup:]
        R = res['R'][warmup:]
        mu_C = res['drift_C'][warmup:]
        mu_R = res['drift_R'][warmup:]

        dC = np.diff(C)
        dR = np.diff(R)

        dC_all.extend(dC)
        dR_all.extend(dR)
        mu_C_all.extend(mu_C[:-1])
        mu_R_all.extend(mu_R[:-1])

    dC_arr = np.array(dC_all)
    dR_arr = np.array(dR_all)
    mu_C_arr = np.array(mu_C_all)
    mu_R_arr = np.array(mu_R_all)

    # Global diffusion matrix
    res_C = dC_arr - mu_C_arr * dt
    res_R = dR_arr - mu_R_arr * dt

    D_CC = np.mean(res_C**2) / (2 * dt)
    D_RR = np.mean(res_R**2) / (2 * dt)
    D_CR = np.mean(res_C * res_R) / (2 * dt)

    D = np.array([[D_CC, D_CR], [D_CR, D_RR]])
    D_inv = np.linalg.inv(D)

    print(f"  D_CC = {D_CC:.6f}")
    print(f"  D_RR = {D_RR:.6f}")
    print(f"  D_CR = {D_CR:.6f}")
    print(f"  det(D) = {np.linalg.det(D):.10f}")
    sys.stdout.flush()

    # Compute path entropy production for segments
    # σ_ep(segment) = Σ_t [μ(t)^T D^{-1} μ(t)] * dt
    # But more precisely for path: σ_ep = Σ_t [dx^T D^{-1} μ(t)]
    # which is the Stratonovich convention

    results = []
    for tau in segment_lengths:
        print(f"\n  Segment length τ={tau}:")

        # Compute segment EP
        n_segments = len(dC_arr) // tau
        ep_segments_1d = np.empty(n_segments)
        ep_segments_2d = np.empty(n_segments)

        D_CC_only = D_CC  # For 1D comparison

        for s in range(n_segments):
            start = s * tau
            end = start + tau

            # 2D: σ_ep = Σ dx^T D^{-1} μ
            seg_dC = dC_arr[start:end]
            seg_dR = dR_arr[start:end]
            seg_mu_C = mu_C_arr[start:end]
            seg_mu_R = mu_R_arr[start:end]

            # Path EP using medium entropy production
            ep_2d = 0
            ep_1d = 0
            for tt in range(tau):
                dx = np.array([seg_dC[tt], seg_dR[tt]])
                mu = np.array([seg_mu_C[tt], seg_mu_R[tt]])
                ep_2d += dx @ D_inv @ mu
                ep_1d += seg_dC[tt] * seg_mu_C[tt] / D_CC_only

            ep_segments_2d[s] = ep_2d
            ep_segments_1d[s] = ep_1d

        # FT test: bin EP values and compute ln(P(+A)/P(-A))
        for label, ep_segments in [("1D", ep_segments_1d), ("2D", ep_segments_2d)]:
            mean_ep = np.mean(ep_segments)
            p_pos = np.mean(ep_segments > 0)

            # Bin into symmetric bins for FT ratio
            max_ep = np.percentile(np.abs(ep_segments), 95)
            n_ft_bins = 20
            bin_edges = np.linspace(0, max_ep, n_ft_bins + 1)

            ft_A = []
            ft_ratio = []
            for b in range(n_ft_bins):
                lo, hi = bin_edges[b], bin_edges[b+1]
                n_pos = np.sum((ep_segments >= lo) & (ep_segments < hi))
                n_neg = np.sum((ep_segments >= -hi) & (ep_segments < -lo))
                if n_pos > 10 and n_neg > 10:
                    A = 0.5 * (lo + hi)
                    ft_A.append(A)
                    ft_ratio.append(np.log(n_pos / n_neg))

            if len(ft_A) >= 3:
                ft_A = np.array(ft_A)
                ft_ratio = np.array(ft_ratio)
                # Linear fit: ft_ratio = slope * ft_A
                slope = np.sum(ft_A * ft_ratio) / np.sum(ft_A**2)
                print(f"    {label}: ⟨σ_ep⟩={mean_ep:.4f}, P(+)={p_pos:.3f}, FT slope={slope:.4f} (target=1.0)")
            else:
                slope = np.nan
                print(f"    {label}: ⟨σ_ep⟩={mean_ep:.4f}, P(+)={p_pos:.3f}, FT slope=insufficient data")

        results.append({
            'tau': int(tau),
            'mean_ep_2d': float(np.mean(ep_segments_2d)),
            'mean_ep_1d': float(np.mean(ep_segments_1d)),
            'p_pos_2d': float(np.mean(ep_segments_2d > 0)),
            'p_pos_1d': float(np.mean(ep_segments_1d > 0)),
        })

    return results


# ─── Experiment F: Landauer Efficiency with 2D EP ───

def expF_landauer_2d():
    """Test whether the 14× Landauer violation resolves with 2D entropy.

    Landauer bound: erasing 1 bit costs ≥ kT·ln(2) ≈ 0.693 nats of EP.
    Efficiency η = MI / EP ≤ 1/ln(2) ≈ 1.44 bits/nat (or 0.72 bits/ep-unit).

    S87 found η(1D) ≈ 10 bits/ep, 14× above the bound.
    With 2D EP, does η come down?
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Landauer Efficiency with 2D Entropy Production")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 300_000
    warmup = 80_000
    dt = 0.1
    sigma = 0.011

    # External signal for MI measurement
    freq = 0.003
    n_seeds = 10

    mi_values = []
    ep_1d_values = []
    ep_2d_values = []

    for seed in range(n_seeds):
        res = run_2d(N, sigma, steps, seed=seed)
        C = res['C'][warmup:]
        R = res['R'][warmup:]
        mu_C = res['drift_C'][warmup:]
        mu_R = res['drift_R'][warmup:]

        # Generate external signal
        np.random.seed(seed + 1000)
        t_arr = np.arange(len(C)) * dt
        signal = np.sin(2 * np.pi * freq * t_arr)
        signal_binary = (signal > 0).astype(float)

        # Bin C for MI calculation
        n_mi_bins = 10
        C_binned = np.digitize(C, np.linspace(C.min(), C.max(), n_mi_bins + 1))
        C_binned = np.clip(C_binned, 1, n_mi_bins)

        # MI(signal_binary, C_binned)
        mi = 0.0
        for s_val in [0, 1]:
            mask_s = signal_binary == s_val
            p_s = mask_s.mean()
            if p_s == 0:
                continue
            for c_val in range(1, n_mi_bins + 1):
                mask_c = C_binned == c_val
                p_c = mask_c.mean()
                p_sc = (mask_s & mask_c).mean()
                if p_sc > 0 and p_c > 0:
                    mi += p_sc * np.log2(p_sc / (p_s * p_c))

        mi_values.append(mi)

        # EP calculation
        dC = np.diff(C)
        dR = np.diff(R)
        res_C = dC - mu_C[:-1] * dt
        res_R = dR - mu_R[:-1] * dt

        D_CC = np.mean(res_C**2) / (2 * dt)
        D_RR = np.mean(res_R**2) / (2 * dt)
        D_CR = np.mean(res_C * res_R) / (2 * dt)

        ep_1d = np.mean(mu_C[:-1]**2) / D_CC
        ep_1d_values.append(ep_1d)

        D = np.array([[D_CC, D_CR], [D_CR, D_RR]])
        try:
            D_inv = np.linalg.inv(D)
            # Subsample for speed
            ep_2d_samples = []
            for tt in range(0, len(mu_C) - 1, 50):
                mu = np.array([mu_C[tt], mu_R[tt]])
                ep_2d_samples.append(mu @ D_inv @ mu)
            ep_2d = np.mean(ep_2d_samples)
        except np.linalg.LinAlgError:
            ep_2d = np.nan
        ep_2d_values.append(ep_2d)

    mi_mean = np.mean(mi_values)
    ep_1d_mean = np.mean(ep_1d_values)
    ep_2d_mean = np.nanmean(ep_2d_values)

    eta_1d = mi_mean / ep_1d_mean if ep_1d_mean > 0 else np.nan
    eta_2d = mi_mean / ep_2d_mean if ep_2d_mean > 0 else np.nan

    print(f"\n  Mutual information: MI = {mi_mean:.4f} bits")
    print(f"\n  1D entropy production:")
    print(f"    ⟨σ_ep(1D)⟩ = {ep_1d_mean:.4f}")
    print(f"    η(1D) = MI/EP = {eta_1d:.4f} bits/ep")
    print(f"    Landauer bound = 0.72 bits/ep")
    print(f"    Violation = {eta_1d/0.72:.1f}×" if not np.isnan(eta_1d) else "")

    print(f"\n  2D entropy production:")
    print(f"    ⟨σ_ep(2D)⟩ = {ep_2d_mean:.4f}")
    print(f"    η(2D) = MI/EP = {eta_2d:.4f} bits/ep")
    if not np.isnan(eta_2d):
        if eta_2d <= 0.72:
            print(f"    ✓ WITHIN Landauer bound! Violation RESOLVED!")
        else:
            print(f"    Violation = {eta_2d/0.72:.1f}×")
            remaining = (eta_2d / 0.72 - 1) / (eta_1d / 0.72 - 1) * 100
            print(f"    {100-remaining:.1f}% of violation resolved by adding R dimension")
            print(f"    {remaining:.1f}% remains — from individual agent fluctuations")

    return {
        'MI': float(mi_mean),
        'ep_1d': float(ep_1d_mean),
        'ep_2d': float(ep_2d_mean),
        'eta_1d': float(eta_1d) if not np.isnan(eta_1d) else None,
        'eta_2d': float(eta_2d) if not np.isnan(eta_2d) else None,
    }


# ─── Experiment G: EP Decomposition ───

def expG_ep_decomposition():
    """Decompose 2D entropy production into C, R, and cross-term contributions.

    σ_ep(2D) = μ^T D^{-1} μ
             = D^{-1}_{CC} μ_C² + 2 D^{-1}_{CR} μ_C μ_R + D^{-1}_{RR} μ_R²

    This tells us WHERE the dissipation lives:
      - C term: from coherence dynamics alone
      - R term: from phase synchronization dynamics alone
      - Cross term: from coherence-phase coupling
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT G: Entropy Production Decomposition (C vs R vs Cross)")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 300_000
    warmup = 80_000
    dt = 0.1
    noise_levels = [0.005, 0.009, 0.011, 0.013, 0.018, 0.025]
    results = []

    for sigma in noise_levels:
        ep_C_list, ep_R_list, ep_cross_list, ep_total_list = [], [], [], []

        for seed in range(5):
            res = run_2d(N, sigma, steps, seed=seed)
            C = res['C'][warmup:]
            R = res['R'][warmup:]
            mu_C = res['drift_C'][warmup:]
            mu_R = res['drift_R'][warmup:]

            dC = np.diff(C)
            dR = np.diff(R)
            res_C = dC - mu_C[:-1] * dt
            res_R = dR - mu_R[:-1] * dt

            D_CC = np.mean(res_C**2) / (2 * dt)
            D_RR = np.mean(res_R**2) / (2 * dt)
            D_CR = np.mean(res_C * res_R) / (2 * dt)

            D = np.array([[D_CC, D_CR], [D_CR, D_RR]])
            try:
                D_inv = np.linalg.inv(D)
            except np.linalg.LinAlgError:
                continue

            # Decompose: σ_ep = D_inv[0,0]*μC² + 2*D_inv[0,1]*μC*μR + D_inv[1,1]*μR²
            ep_C_vals, ep_R_vals, ep_cross_vals = [], [], []
            for tt in range(0, len(mu_C) - 1, 100):
                mC, mR = mu_C[tt], mu_R[tt]
                ep_C_vals.append(D_inv[0, 0] * mC**2)
                ep_R_vals.append(D_inv[1, 1] * mR**2)
                ep_cross_vals.append(2 * D_inv[0, 1] * mC * mR)

            ep_C_list.append(np.mean(ep_C_vals))
            ep_R_list.append(np.mean(ep_R_vals))
            ep_cross_list.append(np.mean(ep_cross_vals))
            ep_total_list.append(np.mean(ep_C_vals) + np.mean(ep_R_vals) + np.mean(ep_cross_vals))

        ep_C = np.mean(ep_C_list)
        ep_R = np.mean(ep_R_list)
        ep_cross = np.mean(ep_cross_list)
        ep_total = np.mean(ep_total_list)

        # Fractions
        frac_C = ep_C / ep_total * 100 if ep_total > 0 else 0
        frac_R = ep_R / ep_total * 100 if ep_total > 0 else 0
        frac_cross = ep_cross / ep_total * 100 if ep_total > 0 else 0

        result = {
            'sigma': float(sigma),
            'ep_C': float(ep_C),
            'ep_R': float(ep_R),
            'ep_cross': float(ep_cross),
            'ep_total': float(ep_total),
            'frac_C': float(frac_C),
            'frac_R': float(frac_R),
            'frac_cross': float(frac_cross),
        }
        results.append(result)
        print(f"  σ={sigma:.3f}: C={frac_C:.1f}%  R={frac_R:.1f}%  cross={frac_cross:.1f}%  "
              f"total={ep_total:.4f}")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    # Average fractions
    avg_C = np.mean([r['frac_C'] for r in results])
    avg_R = np.mean([r['frac_R'] for r in results])
    avg_cross = np.mean([r['frac_cross'] for r in results])
    print(f"  Average decomposition: C={avg_C:.1f}%  R={avg_R:.1f}%  cross={avg_cross:.1f}%")

    if avg_R > avg_C:
        print(f"  → Phase synchronization (R) dominates entropy production!")
        print(f"  → This explains why 1D (C-only) misses most dissipation")
    elif avg_C > avg_R:
        print(f"  → Coherence (C) dominates — R is secondary")
    if abs(avg_cross) > 10:
        print(f"  → Cross-coupling is significant ({avg_cross:.1f}%)")
        print(f"  → C and R dynamics are thermodynamically entangled")

    return results


# ─── Main ───

def main():
    print("=" * 70)
    print("THOR SESSION #88: The 2D Thermodynamic Landscape")
    print("Where Does the Missing 93% Go?")
    print("=" * 70)
    print(f"\nStarted: {datetime.now().isoformat()}")
    print()
    sys.stdout.flush()

    all_results = {}

    # A: Trajectory statistics
    all_results['A_trajectory'] = expA_trajectory_stats()

    # B: 2D Fokker-Planck
    all_results['B_fokker_planck'] = expB_2d_fokker_planck()

    # C: 2D EP vs noise
    all_results['C_ep_vs_noise'] = expC_2d_ep_vs_noise()

    # D: Probability currents
    all_results['D_currents'] = expD_probability_currents()

    # E: Fluctuation theorem
    all_results['E_fluctuation_theorem'] = expE_2d_fluctuation_theorem()

    # F: Landauer efficiency
    all_results['F_landauer'] = expF_landauer_2d()

    # G: EP decomposition
    all_results['G_decomposition'] = expG_ep_decomposition()

    # Save results
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)

    # Convert numpy types for JSON
    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, float) and np.isnan(obj):
            return None
        return obj

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            result = convert(obj)
            if result is not obj:
                return result
            return super().default(obj)

    with open('thor_session_88_2d_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, cls=NumpyEncoder)

    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("Results saved to thor_session_88_2d_results.json")


if __name__ == '__main__':
    main()
