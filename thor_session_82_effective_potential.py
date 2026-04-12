#!/usr/bin/env python3
"""
Thor Session #82: Effective Potential Landscape — Kramers Theory

S80 found two equilibria (C≈0.60 and C≈0.85) via drift measurements.
S81 found heavy-tailed bistable switching (CV>2.3) with 70/30 occupation.

THIS SESSION: Reconstruct the full double-well potential U(C) from two
independent methods and test Kramers escape rate predictions.

METHOD 1: From stationary distribution P(C)
  U_eff(C) = -σ² · ln P(C)
  (Boltzmann inversion of the probability density)

METHOD 2: From drift measurements μ(C)
  U(C) = -∫₀ᶜ μ(C') dC'
  (Integrate the effective force field)

PREDICTIONS TO TEST:
  1. Kramers escape rate: r = (ω_well · ω_barrier)/(2π) · exp(-ΔU/D)
  2. Occupation ratio: P_low/P_high = exp(-(U_low - U_high)/D)
  3. Noise scaling: switching rate ~ exp(-const/σ²) → Arrhenius plot

Builds on: S80 (two equilibria, drift), S81 (bimodality, switching)
"""

import numpy as np
import json
import sys
from datetime import datetime
from thor_session_81_phase_transition import run_fast


# ─── Experiment A: High-Resolution Stationary Distribution ───

def expA_stationary_distribution():
    """Collect very long time series at multiple noise levels
    to get high-quality P(C) for Boltzmann inversion."""
    print("=" * 70)
    print("EXPERIMENT A: Stationary Distribution P(C)")
    print("=" * 70)
    sys.stdout.flush()

    noise_vals = [0.008, 0.009, 0.010, 0.011, 0.012, 0.013, 0.015, 0.020]
    N = 4
    steps = 80000  # Long runs for good statistics
    n_seeds = 16
    n_bins = 100
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    results = {}

    for noise in noise_vals:
        all_C = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.2)
            all_C.extend(r['C_collective'][ss:].tolist())

        C_arr = np.array(all_C)
        hist, _ = np.histogram(C_arr, bins=bins, density=True)

        # Effective potential: U_eff = -D * ln(P)
        # D = σ² (diffusion coefficient for additive noise)
        D = noise**2
        # Avoid log(0) — set minimum density
        hist_safe = np.maximum(hist, 1e-6)
        U_eff = -D * np.log(hist_safe)
        U_eff -= np.min(U_eff)  # Shift so minimum = 0

        # Find wells (local minima of U_eff)
        wells = []
        for i in range(2, len(U_eff) - 2):
            if U_eff[i] < U_eff[i-1] and U_eff[i] < U_eff[i+1]:
                wells.append((bin_centers[i], U_eff[i]))

        # Find barriers (local maxima of U_eff between wells)
        barriers = []
        for i in range(2, len(U_eff) - 2):
            if U_eff[i] > U_eff[i-1] and U_eff[i] > U_eff[i+1]:
                barriers.append((bin_centers[i], U_eff[i]))

        results[f"{noise:.3f}"] = {
            'noise': noise,
            'D': D,
            'hist': hist.tolist(),
            'U_eff': U_eff.tolist(),
            'bin_centers': bin_centers.tolist(),
            'wells': wells,
            'barriers': barriers,
            'mean': float(np.mean(C_arr)),
            'std': float(np.std(C_arr)),
            'n_samples': len(C_arr),
        }

        print(f"\n  noise={noise:.3f} (D={D:.6f}):")
        print(f"    N_samples = {len(C_arr)}, mean={np.mean(C_arr):.4f}, std={np.std(C_arr):.4f}")
        print(f"    Wells: {', '.join(f'C={w[0]:.3f} (U={w[1]:.6f})' for w in wells)}")
        print(f"    Barriers: {', '.join(f'C={b[0]:.3f} (U={b[1]:.6f})' for b in barriers)}")

        if len(wells) >= 2:
            # Identify the two deepest wells
            wells_sorted = sorted(wells, key=lambda w: w[1])
            w1, w2 = wells_sorted[0], wells_sorted[1]
            delta_U = abs(w2[1] - w1[1])
            print(f"    ΔU between wells = {delta_U:.6f}")

            # Find barrier between the two wells
            c_min, c_max = min(w1[0], w2[0]), max(w1[0], w2[0])
            barrier_between = [b for b in barriers if c_min < b[0] < c_max]
            if barrier_between:
                barrier_height = max(b[1] for b in barrier_between)
                print(f"    Barrier height above deeper well = {barrier_height - wells_sorted[0][1]:.6f}")
                print(f"    Barrier height above shallower well = {barrier_height - wells_sorted[1][1]:.6f}")

        sys.stdout.flush()

    return results


# ─── Experiment B: Drift Field Measurement ───

def expB_drift_field():
    """Measure the effective drift μ(C) by initializing ensembles at fixed C
    and measuring short-time displacement. Much higher resolution than S80."""
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Drift Field μ(C)")
    print("=" * 70)
    sys.stdout.flush()

    phi_inv = (np.sqrt(5) - 1) / 2

    # Test at multiple noise levels
    for noise in [0.005, 0.008, 0.011, 0.015]:
        print(f"\n  --- noise = {noise:.3f} ---")
        C_init_vals = np.arange(0.10, 0.96, 0.02)
        drift_data = []

        for C_init in C_init_vals:
            drifts = []
            for seed in range(30):
                np.random.seed(seed * 1000 + int(C_init * 100))
                N = 4
                C = np.full(N, C_init) + np.random.normal(0, 0.01, N)
                C = np.clip(C, 0, 1)
                phase = np.random.uniform(0, 2 * np.pi, N)
                omega = 0.1 + np.random.uniform(-0.02, 0.02, N)
                dt = 0.1
                kappa_phase = 0.10
                kappa_C = 0.15
                C_threshold = 0.55

                C_mean_init = float(np.mean(C))

                # Short integration — just enough to measure drift
                measure_steps = 200
                for t in range(measure_steps):
                    C_now = float(np.mean(C))
                    is_attractive = C_now < C_threshold

                    # Vectorized phase dynamics
                    sin_diff = np.sin(phase[None, :] - phase[:, None])
                    np.fill_diagonal(sin_diff, 0)
                    sign = 1.0 if is_attractive else -1.0
                    dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
                    phase = (phase + dt * dphase) % (2 * np.pi)

                    # Coherence dynamics
                    R_func = 1 - C**2
                    intrinsic = -R_func * (C - phi_inv) * np.cos(phase)
                    c_coupling = kappa_C * (C.mean() - C) * R_func
                    dC = intrinsic + c_coupling
                    C = C + dt * dC
                    C = np.clip(C, 0, 1)

                    if noise > 0:
                        C = np.clip(C + np.random.normal(0, noise, N), 0, 1)
                        phase = (phase + np.random.normal(0, noise, N)) % (2 * np.pi)

                C_mean_final = float(np.mean(C))
                drift = (C_mean_final - C_mean_init) / (measure_steps * dt)
                drifts.append(drift)

            mean_drift = np.mean(drifts)
            std_drift = np.std(drifts)
            drift_data.append({
                'C_init': float(C_init),
                'drift': float(mean_drift),
                'drift_std': float(std_drift),
            })

        # Print drift field
        for d in drift_data:
            bar = "+" * int(abs(d['drift']) * 1000) if d['drift'] > 0 else "-" * int(abs(d['drift']) * 1000)
            print(f"    C={d['C_init']:.2f}: μ={d['drift']:+.5f} {bar[:20]}")

        # Find zero crossings (equilibria)
        drifts_arr = np.array([d['drift'] for d in drift_data])
        C_arr = np.array([d['C_init'] for d in drift_data])
        zeros = []
        for i in range(len(drifts_arr) - 1):
            if drifts_arr[i] * drifts_arr[i+1] < 0:
                # Linear interpolation
                C_zero = C_arr[i] - drifts_arr[i] * (C_arr[i+1] - C_arr[i]) / (drifts_arr[i+1] - drifts_arr[i])
                # Stability: negative slope = stable, positive = unstable
                slope = (drifts_arr[i+1] - drifts_arr[i]) / (C_arr[i+1] - C_arr[i])
                stability = "STABLE" if slope < 0 else "UNSTABLE"
                zeros.append((float(C_zero), stability, float(slope)))

        print(f"\n    Equilibria:")
        for C_z, stab, slope in zeros:
            print(f"      C = {C_z:.4f} ({stab}, slope = {slope:.4f})")

        # Integrate drift to get potential
        # U(C) = -∫μ(C')dC'
        dC_step = C_arr[1] - C_arr[0]
        U_from_drift = np.zeros(len(drifts_arr))
        for i in range(1, len(drifts_arr)):
            U_from_drift[i] = U_from_drift[i-1] - drifts_arr[i] * dC_step
        U_from_drift -= np.min(U_from_drift)

        print(f"\n    Potential landscape U(C) from drift:")
        for i in range(0, len(C_arr), 4):
            bar = "#" * int(U_from_drift[i] * 5000)
            print(f"      C={C_arr[i]:.2f}: U={U_from_drift[i]:.6f} {bar[:30]}")

        sys.stdout.flush()

    return drift_data


# ─── Experiment C: Kramers Rate Prediction ───

def expC_kramers_rates():
    """Test Kramers escape rate predictions.

    Kramers theory: escape rate from well over barrier:
      r = (ω_well * ω_barrier) / (2π) * exp(-ΔU / D)

    where ω_well = sqrt(U''(C_well)), ω_barrier = sqrt(|U''(C_barrier)|),
    ΔU = U(barrier) - U(well), D = noise² (diffusion coefficient).

    Test: measure switching rates at different noise levels,
    plot ln(rate) vs 1/D → should be linear (Arrhenius).
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Kramers Rate — Arrhenius Test")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    C_boundary = 0.70  # Same as S81
    noise_vals = np.arange(0.008, 0.022, 0.001)
    steps = 60000
    n_seeds = 20

    rate_data = []

    for noise in noise_vals:
        switch_counts = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.2)
            C_ts = r['C_collective'][ss:]

            # Smooth to avoid noise-induced false switches
            # Use running average over 50 steps
            kernel = np.ones(50) / 50
            C_smooth = np.convolve(C_ts, kernel, mode='valid')

            in_high = C_smooth > C_boundary
            n_switches = np.sum(np.abs(np.diff(in_high.astype(int))))
            switch_counts.append(n_switches)

        T_eff = (steps * 0.8 - 50) * 0.1  # effective time in simulation units
        mean_rate = np.mean(switch_counts) / T_eff
        std_rate = np.std(switch_counts) / T_eff

        D = noise**2
        inv_D = 1.0 / D
        log_rate = np.log(mean_rate) if mean_rate > 0 else -20

        rate_data.append({
            'noise': float(noise),
            'D': float(D),
            'inv_D': float(inv_D),
            'rate': float(mean_rate),
            'rate_std': float(std_rate),
            'log_rate': float(log_rate),
            'mean_switches': float(np.mean(switch_counts)),
        })

        print(f"  noise={noise:.3f}: rate={mean_rate:.5f}, "
              f"ln(rate)={log_rate:.3f}, 1/D={inv_D:.0f}, "
              f"switches={np.mean(switch_counts):.1f}")
        sys.stdout.flush()

    # Arrhenius fit: ln(r) = ln(A) - ΔU/D = ln(A) - ΔU * (1/D)
    # Only use points where rate > 0 and we have enough switches
    valid = [(d['inv_D'], d['log_rate']) for d in rate_data
             if d['rate'] > 1e-5 and d['mean_switches'] > 5]

    if len(valid) >= 3:
        inv_D_arr = np.array([v[0] for v in valid])
        log_r_arr = np.array([v[1] for v in valid])

        # Linear fit: log_rate = a + b * (1/D) → b = -ΔU
        coeffs = np.polyfit(inv_D_arr, log_r_arr, 1)
        slope = coeffs[0]  # = -ΔU (effective barrier height)
        intercept = coeffs[1]  # = ln(prefactor)

        delta_U_kramers = -slope
        prefactor = np.exp(intercept)

        # R² of the fit
        predicted = np.polyval(coeffs, inv_D_arr)
        ss_res = np.sum((log_r_arr - predicted)**2)
        ss_tot = np.sum((log_r_arr - np.mean(log_r_arr))**2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        print(f"\n  ARRHENIUS FIT:")
        print(f"    ln(rate) = {intercept:.3f} + ({slope:.6f}) × (1/D)")
        print(f"    Effective barrier height ΔU = {delta_U_kramers:.6f}")
        print(f"    Prefactor A = {prefactor:.4f}")
        print(f"    R² = {r_squared:.4f}")
        print(f"    {'GOOD FIT → Kramers theory CONFIRMED' if r_squared > 0.9 else 'POOR FIT → NOT simple Kramers'}")
    else:
        print(f"\n  Insufficient valid points for Arrhenius fit")
        delta_U_kramers = None
        r_squared = None

    sys.stdout.flush()
    return rate_data, delta_U_kramers, r_squared


# ─── Experiment D: Occupation Ratio from Potential ───

def expD_occupation_ratio():
    """Test if the 70/30 occupation ratio follows from the potential asymmetry.

    For a double-well potential, the equilibrium occupation ratio is:
      P_low / P_high = exp(-(U_min_low - U_min_high) / D)

    Measure occupation ratio at multiple noise levels and compare.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Occupation Ratio vs Potential Asymmetry")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    C_boundary = 0.70
    noise_vals = [0.009, 0.010, 0.011, 0.012, 0.013, 0.014, 0.016]
    steps = 80000
    n_seeds = 20

    occ_data = []

    for noise in noise_vals:
        time_high = 0
        time_low = 0

        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.2)
            C_ts = r['C_collective'][ss:]

            time_high += np.sum(C_ts > C_boundary)
            time_low += np.sum(C_ts <= C_boundary)

        total = time_high + time_low
        frac_high = time_high / total
        frac_low = time_low / total

        # From Boltzmann: frac_low/frac_high = exp(-ΔU/D)
        # → ΔU = -D * ln(frac_low/frac_high)
        D = noise**2
        if frac_high > 0 and frac_low > 0:
            delta_U_from_occ = -D * np.log(frac_low / frac_high)
        else:
            delta_U_from_occ = 0

        occ_data.append({
            'noise': float(noise),
            'D': float(D),
            'frac_high': float(frac_high),
            'frac_low': float(frac_low),
            'ratio': float(frac_low / frac_high) if frac_high > 0 else float('inf'),
            'delta_U_from_occ': float(delta_U_from_occ),
        })

        print(f"  noise={noise:.3f}: high={frac_high:.3f}, low={frac_low:.3f}, "
              f"ratio={frac_low/frac_high:.3f}, ΔU={delta_U_from_occ:.6f}")
        sys.stdout.flush()

    # Check if ΔU is noise-independent (it should be if the potential is fixed)
    delta_Us = [d['delta_U_from_occ'] for d in occ_data]
    print(f"\n  ΔU across noise levels:")
    print(f"    Mean = {np.mean(delta_Us):.6f}")
    print(f"    Std  = {np.std(delta_Us):.6f}")
    print(f"    CV   = {np.std(delta_Us)/abs(np.mean(delta_Us)):.3f}" if np.mean(delta_Us) != 0 else "")
    is_constant = np.std(delta_Us) / abs(np.mean(delta_Us)) < 0.3 if np.mean(delta_Us) != 0 else False
    print(f"    {'CONSTANT → fixed double-well potential' if is_constant else 'VARIES → potential changes with noise'}")
    sys.stdout.flush()

    return occ_data


# ─── Experiment E: Residence Time Distributions ───

def expE_residence_times():
    """Detailed residence time analysis at multiple noise levels.

    Kramers theory predicts EXPONENTIAL residence times (memoryless escape).
    S81 found CV > 2.3 (heavy-tailed). What exactly is the distribution?

    Test:
    - Exponential: CV = 1 (Poisson process)
    - Gamma: CV depends on shape parameter
    - Power-law: heavy tail
    - Log-normal: multiplicative noise effects
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT E: Residence Time Distribution Analysis")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    C_boundary = 0.70
    noise_vals = [0.010, 0.011, 0.012, 0.014]
    steps = 100000
    n_seeds = 24

    all_results = {}

    for noise in noise_vals:
        durations_high = []
        durations_low = []

        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.15)
            C_ts = r['C_collective'][ss:]

            # Smooth to avoid jitter at boundary
            kernel = np.ones(30) / 30
            C_smooth = np.convolve(C_ts, kernel, mode='valid')

            in_high = C_smooth > C_boundary
            switches = np.where(np.diff(in_high.astype(int)) != 0)[0]

            if len(switches) > 2:
                durs = np.diff(switches)
                for i, dur in enumerate(durs):
                    if in_high[switches[i]]:
                        durations_high.append(int(dur))
                    else:
                        durations_low.append(int(dur))

        for label, durs in [("HIGH", durations_high), ("LOW", durations_low)]:
            if len(durs) < 5:
                print(f"\n  noise={noise:.3f}, {label}: insufficient data ({len(durs)} episodes)")
                continue

            durs_arr = np.array(durs, dtype=float)
            mean_d = np.mean(durs_arr)
            median_d = np.median(durs_arr)
            std_d = np.std(durs_arr)
            cv = std_d / mean_d if mean_d > 0 else 0
            ratio_median_mean = median_d / mean_d if mean_d > 0 else 0

            # Percentiles
            p25 = np.percentile(durs_arr, 25)
            p75 = np.percentile(durs_arr, 75)
            p95 = np.percentile(durs_arr, 95)
            p99 = np.percentile(durs_arr, 99) if len(durs) > 100 else np.max(durs_arr)

            # Test exponential: median/mean should be ln(2) ≈ 0.693
            exp_test = abs(ratio_median_mean - np.log(2))

            print(f"\n  noise={noise:.3f}, {label} state ({len(durs)} episodes):")
            print(f"    Mean={mean_d:.1f}, Median={median_d:.1f}, Std={std_d:.1f}")
            print(f"    CV={cv:.3f} (1.0=exponential)")
            print(f"    Median/Mean={ratio_median_mean:.3f} (0.693=exponential)")
            print(f"    P25={p25:.0f}, P75={p75:.0f}, P95={p95:.0f}, P99={p99:.0f}")
            print(f"    Max={np.max(durs_arr):.0f}, Min={np.min(durs_arr):.0f}")

            if cv < 1.2 and exp_test < 0.15:
                print(f"    → EXPONENTIAL (Kramers memoryless escape)")
            elif cv > 1.5:
                print(f"    → HEAVY-TAILED (non-Kramers, intermittent)")
            else:
                print(f"    → INTERMEDIATE")

        all_results[f"{noise:.3f}"] = {
            'noise': noise,
            'n_high': len(durations_high),
            'n_low': len(durations_low),
        }
        sys.stdout.flush()

    return all_results


# ─── Experiment F: Noise-Dependent Potential Shape ───

def expF_potential_vs_noise():
    """Does the effective potential change shape with noise level?

    If Kramers theory holds perfectly, the potential is noise-independent.
    If it changes, we have a noise-dependent landscape (more complex physics).

    Measure: P(C) → U_eff(C) at multiple noise levels and compare shapes.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Potential Shape vs Noise Level")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    noise_vals = [0.008, 0.010, 0.012, 0.015, 0.020]
    steps = 80000
    n_seeds = 20
    n_bins = 80
    bins = np.linspace(0.2, 1.0, n_bins + 1)  # Focus on relevant range
    bin_centers = (bins[:-1] + bins[1:]) / 2

    potentials = {}

    for noise in noise_vals:
        all_C = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.2)
            all_C.extend(r['C_collective'][ss:].tolist())

        C_arr = np.array(all_C)
        hist, _ = np.histogram(C_arr, bins=bins, density=True)

        D = noise**2
        hist_safe = np.maximum(hist, 1e-4)
        U_eff = -D * np.log(hist_safe)
        U_eff -= np.min(U_eff)

        # NORMALIZED potential: U_eff / D to remove the trivial D scaling
        U_norm = U_eff / D

        potentials[f"{noise:.3f}"] = {
            'noise': noise,
            'D': D,
            'U_eff': U_eff.tolist(),
            'U_norm': U_norm.tolist(),
            'bin_centers': bin_centers.tolist(),
        }

        # Find well positions in normalized potential
        wells_norm = []
        for i in range(2, len(U_norm) - 2):
            if U_norm[i] < U_norm[i-1] and U_norm[i] < U_norm[i+1] and U_norm[i] < np.median(U_norm):
                wells_norm.append((bin_centers[i], U_norm[i]))

        print(f"\n  noise={noise:.3f} (D={D:.6f}):")
        print(f"    Wells in U/D: {', '.join(f'C={w[0]:.3f}' for w in wells_norm[:3])}")

    # Compare normalized potentials
    print(f"\n  --- Cross-Noise Comparison ---")
    # Sample points to compare
    check_points = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    print(f"  {'C':>6s}", end="")
    for noise in noise_vals:
        print(f"  σ={noise:.3f}", end="")
    print()

    for cp in check_points:
        print(f"  {cp:6.2f}", end="")
        for noise in noise_vals:
            key = f"{noise:.3f}"
            bc = np.array(potentials[key]['bin_centers'])
            un = np.array(potentials[key]['U_norm'])
            idx = np.argmin(np.abs(bc - cp))
            print(f"  {un[idx]:8.3f}", end="")
        print()

    sys.stdout.flush()
    return potentials


# ─── Experiment G: Diffusion Coefficient Measurement ───

def expG_diffusion_coefficient():
    """Measure the actual diffusion coefficient D(C).

    For additive noise, D = σ² (constant).
    But the nonlinear dynamics (R(C) = 1-C²) could create
    effective state-dependent diffusion for the collective variable.

    Measure: Var(ΔC | C=c) / Δt for different c.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT G: State-Dependent Diffusion D(C)")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    noise = 0.011  # Critical noise
    steps = 100000
    n_seeds = 20

    # Collect (C_t, ΔC_t) pairs
    C_vals = []
    dC_vals = []

    for seed in range(n_seeds):
        r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
        ss = int(steps * 0.15)
        C_ts = r['C_collective'][ss:]

        C_vals.extend(C_ts[:-1].tolist())
        dC_vals.extend(np.diff(C_ts).tolist())

    C_arr = np.array(C_vals)
    dC_arr = np.array(dC_vals)

    # Bin by C and compute drift and diffusion in each bin
    C_bin_edges = np.arange(0.3, 0.96, 0.02)
    C_bin_centers = (C_bin_edges[:-1] + C_bin_edges[1:]) / 2
    dt = 0.1

    print(f"\n  {'C':>6s}  {'μ(C)':>10s}  {'D(C)':>10s}  {'D/σ²':>8s}  {'N_pts':>8s}")
    print(f"  {'─'*6}  {'─'*10}  {'─'*10}  {'─'*8}  {'─'*8}")

    D_measured = []

    for i in range(len(C_bin_centers)):
        mask = (C_arr >= C_bin_edges[i]) & (C_arr < C_bin_edges[i+1])
        if mask.sum() < 100:
            continue

        dC_in_bin = dC_arr[mask]

        # Drift = <ΔC> / dt
        mu = np.mean(dC_in_bin) / dt
        # Diffusion = Var(ΔC) / dt (for small dt)
        D = np.var(dC_in_bin) / dt
        D_ratio = D / noise**2

        D_measured.append({
            'C': float(C_bin_centers[i]),
            'mu': float(mu),
            'D': float(D),
            'D_ratio': float(D_ratio),
            'n_pts': int(mask.sum()),
        })

        print(f"  {C_bin_centers[i]:6.3f}  {mu:+10.5f}  {D:10.6f}  {D_ratio:8.3f}  {mask.sum():8d}")

    # Is D constant?
    D_vals = [d['D'] for d in D_measured if d['n_pts'] > 500]
    if D_vals:
        D_mean = np.mean(D_vals)
        D_cv = np.std(D_vals) / D_mean if D_mean > 0 else 0
        print(f"\n  D statistics:")
        print(f"    Mean D = {D_mean:.6f}")
        print(f"    CV(D) = {D_cv:.3f}")
        print(f"    σ² = {noise**2:.6f}")
        print(f"    D/σ² = {D_mean/noise**2:.3f}")
        print(f"    {'CONSTANT D (additive noise confirmed)' if D_cv < 0.3 else 'STATE-DEPENDENT D'}")

    sys.stdout.flush()
    return D_measured


# ─── Main ───

if __name__ == '__main__':
    print("Thor Session #82: Effective Potential Landscape")
    print("Kramers Theory for Bistable Coherence Dynamics")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    sys.stdout.flush()

    all_results = {}

    # A: Stationary distribution → Boltzmann inversion
    all_results['expA'] = expA_stationary_distribution()

    # B: Drift field → integrated potential
    all_results['expB_drift'] = expB_drift_field()

    # C: Kramers rate prediction (Arrhenius test)
    rate_data, delta_U, r_sq = expC_kramers_rates()
    all_results['expC'] = {
        'rates': rate_data,
        'delta_U_kramers': delta_U,
        'r_squared': r_sq,
    }

    # D: Occupation ratio from potential
    all_results['expD'] = expD_occupation_ratio()

    # E: Residence time distributions
    all_results['expE'] = expE_residence_times()

    # F: Potential shape vs noise
    all_results['expF'] = expF_potential_vs_noise()

    # G: Diffusion coefficient
    all_results['expG'] = expG_diffusion_coefficient()

    # ─── SYNTHESIS ───
    print("\n" + "=" * 70)
    print("SYNTHESIS: Effective Potential Landscape")
    print("=" * 70)

    print("\n  KEY FINDINGS:")

    if delta_U is not None:
        print(f"  1. Arrhenius barrier height: ΔU = {delta_U:.6f}")
        print(f"     R² of Arrhenius fit: {r_sq:.4f}")
        if r_sq > 0.9:
            print(f"     → KRAMERS THEORY CONFIRMED for switching rates")
        elif r_sq > 0.7:
            print(f"     → Partial Kramers regime (some deviations)")
        else:
            print(f"     → NOT simple Kramers (anomalous switching)")

    # Check if potential is noise-independent
    occ_delta_Us = [d['delta_U_from_occ'] for d in all_results['expD']]
    if occ_delta_Us:
        print(f"\n  2. Well asymmetry ΔU = {np.mean(occ_delta_Us):.6f} ± {np.std(occ_delta_Us):.6f}")
        cv = np.std(occ_delta_Us) / abs(np.mean(occ_delta_Us)) if np.mean(occ_delta_Us) != 0 else float('inf')
        if cv < 0.3:
            print(f"     → Noise-INDEPENDENT potential (Kramers framework valid)")
        else:
            print(f"     → Noise-DEPENDENT potential (beyond simple Kramers)")

    print(f"\n  VERDICT:")
    if r_sq is not None and r_sq > 0.85:
        print(f"  The bistable coherence dynamics are well-described by")
        print(f"  Kramers escape theory with effective barrier ΔU ≈ {delta_U:.6f}.")
        print(f"  The system is a genuine double-well potential.")
    else:
        print(f"  The switching dynamics deviate from simple Kramers theory.")
        print(f"  The potential landscape may be noise-dependent or")
        print(f"  the escape process is non-Markovian.")

    sys.stdout.flush()

    # Save results
    def make_serializable(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.float64, np.float32)): return float(obj)
        if isinstance(obj, (np.int64, np.int32)): return int(obj)
        if isinstance(obj, dict): return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list): return [make_serializable(v) for v in obj]
        if isinstance(obj, tuple): return [make_serializable(v) for v in obj]
        return obj

    with open('thor_session_82_potential_results.json', 'w') as f:
        json.dump(make_serializable(all_results), f, indent=2)

    print(f"\nResults saved to thor_session_82_potential_results.json")
    print(f"Completed: {datetime.now().isoformat()}")
    sys.stdout.flush()
