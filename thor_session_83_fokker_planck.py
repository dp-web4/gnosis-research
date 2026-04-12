#!/usr/bin/env python3
"""
Thor Session #83: Fokker-Planck Reconstruction — State-Dependent Diffusion

Session 82 confirmed Kramers escape (R²=0.997) but found a PUZZLE:
  - The effective potential is noise-DEPENDENT (occupation ratio flips)
  - BUT Arrhenius law holds (constant barrier height)

Session 82 used V_eff = -σ²·ln(P) — assuming CONSTANT diffusion.
But Experiment G measured D(C)/σ² varying from 2.5 to 4.5!

THE HYPOTHESIS: The apparent noise-dependence of the potential is an
ARTIFACT of the constant-D assumption. When we account for D(C),
the CORRECT potential may be noise-independent.

THE FOKKER-PLANCK EQUATION with state-dependent diffusion:
  ∂P/∂t = -∂[μ(C)P]/∂C + (1/2)∂²[D(C)P]/∂C²

Stationary solution:
  P_st(C) ∝ (1/D(C)) · exp(∫₀ᶜ 2μ(C')/D(C') dC')

Correct effective potential:
  V_eff(C) = -∫₀ᶜ μ(C')/D(C') dC'    (Stratonovich interpretation)

Three methods compared:
  Method 1: V = -D₀·ln(P)              (S82: constant D assumption)
  Method 2: V = -∫μ(C)/D(C) dC         (correct FP potential)
  Method 3: V = -(1/2)·ln(P·D)         (Boltzmann with measured D)

EXPERIMENTS:
  A: High-resolution μ(C) and D(C) at multiple noise levels
  B: Three-method potential comparison
  C: Noise-independence test — does the corrected potential collapse?
  D: Corrected Kramers rates — does the Arrhenius fit change?
  E: Analytical D(C) prediction from R(C) = 1-C²

Builds on: S82 (Kramers confirmed), S80 (drift), S79 (three regimes)
"""

import numpy as np
import json
import sys
from datetime import datetime
from thor_session_81_phase_transition import run_fast


# ─── Experiment A: High-Resolution Kramers-Moyal Coefficients ───

def expA_kramers_moyal(noise_vals=None):
    """Measure drift μ(C) and diffusion D(C) at high resolution
    from the conditional moments of ΔC.

    μ(C) = ⟨ΔC|C⟩ / Δt     (first Kramers-Moyal coefficient)
    D(C) = ⟨(ΔC)²|C⟩ / Δt   (second Kramers-Moyal coefficient)

    Both measured at multiple noise levels to check noise-dependence.
    """
    print("=" * 70)
    print("EXPERIMENT A: Kramers-Moyal Coefficients μ(C) and D(C)")
    print("=" * 70)
    sys.stdout.flush()

    if noise_vals is None:
        noise_vals = [0.008, 0.009, 0.010, 0.011, 0.012, 0.013, 0.015, 0.018]

    N = 4
    steps = 120000
    n_seeds = 24
    dt = 0.1

    # C bins for conditional measurement
    C_bin_edges = np.arange(0.20, 0.98, 0.015)
    C_bin_centers = (C_bin_edges[:-1] + C_bin_edges[1:]) / 2

    all_km = {}

    for noise in noise_vals:
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

        # Compute μ(C) and D(C) in each bin
        mu_vals = []
        D_vals = []
        n_pts_vals = []
        valid_C = []

        for i in range(len(C_bin_centers)):
            mask = (C_arr >= C_bin_edges[i]) & (C_arr < C_bin_edges[i + 1])
            n_pts = mask.sum()

            if n_pts < 200:
                mu_vals.append(np.nan)
                D_vals.append(np.nan)
                n_pts_vals.append(n_pts)
                valid_C.append(False)
                continue

            dC_bin = dC_arr[mask]
            mu = np.mean(dC_bin) / dt
            D = np.var(dC_bin) / dt  # Var, not mean-square (removes drift)
            # Also compute the second moment for cross-check
            # D_raw = np.mean(dC_bin**2) / dt  # includes drift²·dt

            mu_vals.append(mu)
            D_vals.append(D)
            n_pts_vals.append(n_pts)
            valid_C.append(True)

        mu_arr = np.array(mu_vals)
        D_arr = np.array(D_vals)
        valid = np.array(valid_C)

        # Compute D/σ² ratio
        D_ratio = D_arr / noise**2

        all_km[f"{noise:.3f}"] = {
            'noise': noise,
            'sigma_sq': noise**2,
            'C_bins': C_bin_centers.tolist(),
            'mu': mu_arr.tolist(),
            'D': D_arr.tolist(),
            'D_ratio': D_ratio.tolist(),
            'n_pts': n_pts_vals,
            'valid': valid.tolist(),
        }

        # Print summary
        valid_D = D_arr[valid & ~np.isnan(D_arr)]
        valid_mu = mu_arr[valid & ~np.isnan(mu_arr)]
        valid_Cs = C_bin_centers[valid]

        print(f"\n  noise={noise:.3f}:")
        print(f"    D/σ² range: [{np.nanmin(D_ratio[valid]):.2f}, {np.nanmax(D_ratio[valid]):.2f}]")
        print(f"    D/σ² mean:  {np.nanmean(D_ratio[valid]):.2f}")
        print(f"    D/σ² CV:    {np.nanstd(D_ratio[valid])/np.nanmean(D_ratio[valid]):.3f}")

        # Find drift zeros (equilibria)
        for j in range(len(mu_arr) - 1):
            if valid[j] and valid[j+1] and not np.isnan(mu_arr[j]) and not np.isnan(mu_arr[j+1]):
                if mu_arr[j] * mu_arr[j+1] < 0:
                    C_zero = C_bin_centers[j] - mu_arr[j] * (C_bin_centers[j+1] - C_bin_centers[j]) / (mu_arr[j+1] - mu_arr[j])
                    slope = (mu_arr[j+1] - mu_arr[j]) / (C_bin_centers[j+1] - C_bin_centers[j])
                    stab = "STABLE" if slope < 0 else "UNSTABLE"
                    print(f"    Equilibrium: C={C_zero:.4f} ({stab})")

        sys.stdout.flush()

    return all_km


# ─── Experiment B: Three-Method Potential Comparison ───

def expB_potential_comparison(km_data):
    """Reconstruct V_eff(C) using three methods and compare.

    Method 1: V₁(C) = -D₀·ln(P(C))           [S82 constant-D]
    Method 2: V₂(C) = -∫μ(C')/D(C') dC'       [correct FP]
    Method 3: V₃(C) = -(1/2)·ln(P(C)·D(C))    [Boltzmann with D(C)]

    Methods 2 and 3 should agree (they're the same thing derived differently).
    Method 1 should differ where D(C) varies significantly.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Three-Method Potential Comparison")
    print("=" * 70)
    sys.stdout.flush()

    phi_inv = (np.sqrt(5) - 1) / 2
    results = {}

    for key, km in km_data.items():
        noise = km['noise']
        sigma_sq = noise**2
        C_bins = np.array(km['C_bins'])
        mu = np.array(km['mu'])
        D = np.array(km['D'])
        valid = np.array(km['valid'])

        # Need valid data
        mask = valid & ~np.isnan(mu) & ~np.isnan(D) & (D > 0)
        if mask.sum() < 10:
            print(f"\n  noise={noise:.3f}: insufficient valid data")
            continue

        C_v = C_bins[mask]
        mu_v = mu[mask]
        D_v = D[mask]

        # METHOD 1: V₁ = -D₀·ln(P)
        # We need P(C). Reconstruct from the bin counts.
        # Actually, we can compute P from the data we already have (n_pts is proportional to P)
        n_pts = np.array(km['n_pts'])[mask].astype(float)
        P = n_pts / (n_pts.sum() * (C_v[1] - C_v[0]))  # normalize to density
        P_safe = np.maximum(P, 1e-8)

        V1 = -sigma_sq * np.log(P_safe)
        V1 -= np.min(V1)

        # METHOD 2: V₂ = -∫[μ(C')/D(C')]dC'
        # Use trapezoidal integration
        mu_over_D = mu_v / D_v
        dC = np.diff(C_v)
        V2 = np.zeros(len(C_v))
        for i in range(1, len(C_v)):
            V2[i] = V2[i-1] - mu_over_D[i] * (C_v[i] - C_v[i-1])
        V2 -= np.min(V2)

        # METHOD 3: V₃ = -(1/2)·ln(P·D)
        # From the FP stationary solution: P(C) ∝ (1/D(C))·exp(-2V(C))
        # So: 2V(C) = -ln(P(C)·D(C)) + const
        V3 = -0.5 * np.log(P_safe * D_v)
        V3 -= np.min(V3)

        # Normalize all to same scale for comparison
        # Use the range of V2 as reference
        V2_range = np.max(V2) - np.min(V2) if np.max(V2) > np.min(V2) else 1
        V1_range = np.max(V1) - np.min(V1) if np.max(V1) > np.min(V1) else 1
        V3_range = np.max(V3) - np.min(V3) if np.max(V3) > np.min(V3) else 1

        # Find wells and barriers in each potential
        def find_extrema(C, V):
            wells = []
            barriers = []
            for i in range(2, len(V) - 2):
                if V[i] < V[i-1] and V[i] < V[i+1]:
                    wells.append((C[i], V[i]))
                elif V[i] > V[i-1] and V[i] > V[i+1]:
                    barriers.append((C[i], V[i]))
            return wells, barriers

        w1, b1 = find_extrema(C_v, V1)
        w2, b2 = find_extrema(C_v, V2)
        w3, b3 = find_extrema(C_v, V3)

        # Compute correlation between methods
        corr_12 = np.corrcoef(V1, V2)[0, 1] if len(V1) > 2 else 0
        corr_13 = np.corrcoef(V1, V3)[0, 1] if len(V1) > 2 else 0
        corr_23 = np.corrcoef(V2, V3)[0, 1] if len(V2) > 2 else 0

        results[key] = {
            'noise': noise,
            'C': C_v.tolist(),
            'V1': V1.tolist(),
            'V2': V2.tolist(),
            'V3': V3.tolist(),
            'V1_wells': w1,
            'V1_barriers': b1,
            'V2_wells': w2,
            'V2_barriers': b2,
            'V3_wells': w3,
            'V3_barriers': b3,
            'corr_12': float(corr_12),
            'corr_13': float(corr_13),
            'corr_23': float(corr_23),
            'mu_over_D': mu_over_D.tolist(),
            'D_ratio': (D_v / sigma_sq).tolist(),
        }

        print(f"\n  noise={noise:.3f}:")
        print(f"    Method 1 (const-D):  wells={[f'C={w[0]:.3f}' for w in w1[:3]]}")
        print(f"    Method 2 (FP):       wells={[f'C={w[0]:.3f}' for w in w2[:3]]}")
        print(f"    Method 3 (Boltz+D):  wells={[f'C={w[0]:.3f}' for w in w3[:3]]}")
        print(f"    Correlations: V1-V2={corr_12:.4f}, V1-V3={corr_13:.4f}, V2-V3={corr_23:.4f}")

        # Key comparison: barrier locations
        print(f"    Method 1 barriers:  {[f'C={b[0]:.3f}' for b in b1[:3]]}")
        print(f"    Method 2 barriers:  {[f'C={b[0]:.3f}' for b in b2[:3]]}")
        print(f"    Method 3 barriers:  {[f'C={b[0]:.3f}' for b in b3[:3]]}")

        # Barrier height comparison
        if len(w2) >= 2 and len(b2) >= 1:
            w_sorted = sorted(w2, key=lambda x: x[1])
            main_barrier = max(b2, key=lambda x: x[1])
            dU_2 = main_barrier[1] - w_sorted[0][1]
            print(f"    Method 2 barrier height: {dU_2:.6f}")
        if len(w1) >= 2 and len(b1) >= 1:
            w_sorted = sorted(w1, key=lambda x: x[1])
            main_barrier = max(b1, key=lambda x: x[1])
            dU_1 = main_barrier[1] - w_sorted[0][1]
            print(f"    Method 1 barrier height: {dU_1:.6f}")

        sys.stdout.flush()

    return results


# ─── Experiment C: Noise-Independence Test ───

def expC_noise_independence(km_data):
    """The key test: Is the CORRECTED potential noise-independent?

    S82 found that V₁ = -σ²·ln(P) changes with noise (occupation ratio flips).
    HYPOTHESIS: V₂ = -∫μ/D dC is noise-INDEPENDENT — the apparent change
    was an artifact of the constant-D assumption.

    Test: compute V₂ at multiple noise levels and check if they collapse
    onto a single curve (after normalization).
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Noise-Independence of Corrected Potential")
    print("=" * 70)
    sys.stdout.flush()

    phi_inv = (np.sqrt(5) - 1) / 2

    # Compute V₂ at each noise level
    potentials = {}
    barrier_heights = {}
    well_positions = {}

    for key, km in km_data.items():
        noise = km['noise']
        sigma_sq = noise**2
        C_bins = np.array(km['C_bins'])
        mu = np.array(km['mu'])
        D = np.array(km['D'])
        valid = np.array(km['valid'])

        mask = valid & ~np.isnan(mu) & ~np.isnan(D) & (D > 0)
        if mask.sum() < 10:
            continue

        C_v = C_bins[mask]
        mu_v = mu[mask]
        D_v = D[mask]

        # Method 1: V₁ (constant D)
        n_pts = np.array(km['n_pts'])[mask].astype(float)
        P = n_pts / (n_pts.sum() * (C_v[1] - C_v[0]))
        P_safe = np.maximum(P, 1e-8)
        V1 = -sigma_sq * np.log(P_safe)
        V1 -= np.min(V1)

        # Method 2: V₂ (correct FP)
        mu_over_D = mu_v / D_v
        V2 = np.zeros(len(C_v))
        for i in range(1, len(C_v)):
            V2[i] = V2[i-1] - mu_over_D[i] * (C_v[i] - C_v[i-1])
        V2 -= np.min(V2)

        potentials[key] = {
            'C': C_v,
            'V1': V1,
            'V2': V2,
            'noise': noise,
        }

        # Find barrier height in both methods
        for method_name, V in [('V1', V1), ('V2', V2)]:
            wells = []
            barriers = []
            for i in range(2, len(V) - 2):
                if V[i] < V[i-1] and V[i] < V[i+1]:
                    wells.append((C_v[i], V[i]))
                elif V[i] > V[i-1] and V[i] > V[i+1]:
                    barriers.append((C_v[i], V[i]))

            if wells and barriers:
                deepest = min(wells, key=lambda x: x[1])
                highest = max(barriers, key=lambda x: x[1])
                dU = highest[1] - deepest[1]
                if method_name not in barrier_heights:
                    barrier_heights[method_name] = []
                    well_positions[method_name] = []
                barrier_heights[method_name].append({
                    'noise': noise,
                    'dU': dU,
                    'barrier_C': highest[0],
                    'well_C': deepest[0],
                })
                well_positions[method_name].append({
                    'noise': noise,
                    'wells': [(w[0], w[1]) for w in wells],
                    'barriers': [(b[0], b[1]) for b in barriers],
                })

    # Analysis: How much does the barrier height vary?
    print("\n  BARRIER HEIGHT vs NOISE:")
    for method in ['V1', 'V2']:
        if method not in barrier_heights:
            continue
        bhs = barrier_heights[method]
        dUs = [b['dU'] for b in bhs]
        noises = [b['noise'] for b in bhs]
        mean_dU = np.mean(dUs)
        cv_dU = np.std(dUs) / mean_dU if mean_dU > 0 else float('inf')

        print(f"\n  {method} ({'constant D' if method == 'V1' else 'correct FP'}):")
        for b in bhs:
            print(f"    σ={b['noise']:.3f}: ΔU={b['dU']:.6f}, barrier at C={b['barrier_C']:.3f}, well at C={b['well_C']:.3f}")
        print(f"    ΔU mean = {mean_dU:.6f}")
        print(f"    ΔU CV   = {cv_dU:.4f}")

        if cv_dU < 0.15:
            print(f"    → NOISE-INDEPENDENT (CV < 0.15)")
        elif cv_dU < 0.30:
            print(f"    → WEAKLY noise-dependent (0.15 < CV < 0.30)")
        else:
            print(f"    → STRONGLY noise-dependent (CV > 0.30)")

    # Cross-noise potential comparison at specific C values
    print("\n  POTENTIAL VALUES at selected C (normalized so min=0):")
    check_Cs = [0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.90]
    for method in ['V1', 'V2']:
        print(f"\n  {method}:")
        print(f"  {'C':>6s}", end="")
        for key in sorted(potentials.keys()):
            print(f"  σ={potentials[key]['noise']:.3f}", end="")
        print()

        for cp in check_Cs:
            print(f"  {cp:6.2f}", end="")
            for key in sorted(potentials.keys()):
                C_v = potentials[key]['C']
                V = potentials[key][method]
                idx = np.argmin(np.abs(C_v - cp))
                if abs(C_v[idx] - cp) < 0.02:
                    print(f"  {V[idx]:8.5f}", end="")
                else:
                    print(f"  {'---':>8s}", end="")
            print()

    sys.stdout.flush()
    return potentials, barrier_heights


# ─── Experiment D: Corrected Arrhenius Test ───

def expD_corrected_arrhenius(km_data, barrier_heights):
    """Redo the Arrhenius analysis using the CORRECTED barrier height from V₂.

    S82 found R²=0.9968 using rates vs 1/σ². Does the fit change when
    we use the correct D(C) at the barrier location?

    Key insight: In the corrected Kramers formula,
      rate ~ exp(-ΔV₂/D_eff)
    where D_eff is the diffusion at the barrier top, not σ².
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Corrected Arrhenius Analysis")
    print("=" * 70)
    sys.stdout.flush()

    # First, measure switching rates at each noise level
    N = 4
    C_boundary = 0.70
    steps = 80000
    n_seeds = 24

    noise_vals = [0.008, 0.009, 0.010, 0.011, 0.012, 0.013, 0.014, 0.016, 0.018, 0.020]

    rate_data = []

    for noise in noise_vals:
        switch_counts = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.2)
            C_ts = r['C_collective'][ss:]

            kernel = np.ones(50) / 50
            C_smooth = np.convolve(C_ts, kernel, mode='valid')
            in_high = C_smooth > C_boundary
            n_switches = np.sum(np.abs(np.diff(in_high.astype(int))))
            switch_counts.append(n_switches)

        T_eff = (steps * 0.8 - 50) * 0.1
        mean_rate = np.mean(switch_counts) / T_eff
        std_rate = np.std(switch_counts) / T_eff

        D_nominal = noise**2

        # Get effective D at barrier from KM data if available
        km_key = f"{noise:.3f}"
        D_barrier = D_nominal  # default
        if km_key in km_data:
            km = km_data[km_key]
            C_bins = np.array(km['C_bins'])
            D_arr = np.array(km['D'])
            valid = np.array(km['valid'])
            # Barrier is at C ≈ 0.63-0.65
            idx_barrier = np.argmin(np.abs(C_bins - 0.64))
            if valid[idx_barrier] and not np.isnan(D_arr[idx_barrier]) and D_arr[idx_barrier] > 0:
                D_barrier = D_arr[idx_barrier]

        rate_data.append({
            'noise': float(noise),
            'D_nominal': float(D_nominal),
            'D_barrier': float(D_barrier),
            'rate': float(mean_rate),
            'rate_std': float(std_rate),
            'log_rate': float(np.log(mean_rate)) if mean_rate > 0 else -20,
            'mean_switches': float(np.mean(switch_counts)),
        })

        print(f"  σ={noise:.3f}: rate={mean_rate:.5f}, "
              f"D_nom={D_nominal:.6f}, D_barrier={D_barrier:.6f}, "
              f"D_barrier/σ²={D_barrier/D_nominal:.2f}")
        sys.stdout.flush()

    # Arrhenius fit: ln(rate) vs 1/D
    valid_pts = [d for d in rate_data if d['rate'] > 1e-5 and d['mean_switches'] > 3]

    if len(valid_pts) >= 3:
        print(f"\n  ARRHENIUS FITS (comparing D_nominal vs D_barrier):")

        for D_key, D_label in [('D_nominal', 'σ² (S82 method)'), ('D_barrier', 'D(C_barrier)')]:
            inv_D = np.array([1.0 / d[D_key] for d in valid_pts])
            log_r = np.array([d['log_rate'] for d in valid_pts])

            coeffs = np.polyfit(inv_D, log_r, 1)
            predicted = np.polyval(coeffs, inv_D)
            ss_res = np.sum((log_r - predicted)**2)
            ss_tot = np.sum((log_r - np.mean(log_r))**2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            delta_U = -coeffs[0]
            prefactor = np.exp(coeffs[1])

            print(f"\n    Using {D_label}:")
            print(f"      ln(rate) = {coeffs[1]:.3f} + ({coeffs[0]:.6f}) × (1/D)")
            print(f"      ΔU = {delta_U:.6f}")
            print(f"      R² = {r_sq:.4f}")
            print(f"      Prefactor = {prefactor:.4f}")

    sys.stdout.flush()
    return rate_data


# ─── Experiment E: Analytical D(C) from R(C) = 1-C² ───

def expE_analytical_diffusion(km_data):
    """Can we PREDICT D(C) analytically from the model equations?

    The noise enters as additive: C_i → C_i + σξ_i
    For C̄ = (1/N)ΣC_i: instantaneous D = σ²/N

    But the MEASURED D is much larger! The amplification comes from:
    1. The deterministic dynamics R(C)·(C-φ⁻¹)·cos(θ) creating variance
    2. The coupling κ_C·(C̄-C_i)·R(C) redistributing noise

    On a single dt step, the variance of ΔC̄ includes:
    - Direct noise: σ²/N per step
    - Amplified noise from nonlinear dynamics

    The effective D on the SLOW timescale includes accumulated variance
    from the fast cos(θ) oscillation.

    PREDICTION: D(C) ∝ 1 + α·(1-C²)²·(C-φ⁻¹)² where α depends on
    the correlation time of the cos(θ) forcing.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT E: Analytical Diffusion Prediction")
    print("=" * 70)
    sys.stdout.flush()

    phi_inv = (np.sqrt(5) - 1) / 2

    # The noise amplification should scale with R(C)² = (1-C²)²
    # because R(C) appears in the deterministic dynamics as a prefactor.
    # Hypothesis: D_eff(C) = σ²/N · [1 + β·R(C)²·(C-φ⁻¹)²·τ_corr/dt]
    # where β accounts for coupling and τ_corr is the cos(θ) correlation time.

    # Model: D(C)/σ² = a + b·(1-C²)² + c·(1-C²)²·(C-φ⁻¹)²

    # Collect measured D(C)/σ² across all noise levels to find universal curve
    all_C = []
    all_D_ratio = []
    all_noise = []

    for key, km in km_data.items():
        noise = km['noise']
        C_bins = np.array(km['C_bins'])
        D = np.array(km['D'])
        valid = np.array(km['valid'])

        for i in range(len(C_bins)):
            if valid[i] and not np.isnan(D[i]) and D[i] > 0:
                all_C.append(C_bins[i])
                all_D_ratio.append(D[i] / noise**2)
                all_noise.append(noise)

    C_arr = np.array(all_C)
    D_ratio_arr = np.array(all_D_ratio)
    noise_arr = np.array(all_noise)

    # Bin by C (combine all noise levels)
    C_test = np.arange(0.25, 0.95, 0.02)
    D_ratio_mean = []
    D_ratio_std = []
    D_ratio_by_noise = {f"{n:.3f}": [] for n in sorted(set(all_noise))}

    for cp in C_test:
        mask = np.abs(C_arr - cp) < 0.02
        if mask.sum() > 3:
            D_ratio_mean.append(np.mean(D_ratio_arr[mask]))
            D_ratio_std.append(np.std(D_ratio_arr[mask]))
        else:
            D_ratio_mean.append(np.nan)
            D_ratio_std.append(np.nan)

    D_ratio_mean = np.array(D_ratio_mean)
    D_ratio_std = np.array(D_ratio_std)

    # Test analytical predictions
    R_sq = (1 - C_test**2)**2
    R_sq_dev = R_sq * (C_test - phi_inv)**2

    # Fit: D/σ² = a + b·R² + c·R²·(C-φ⁻¹)²
    valid_fit = ~np.isnan(D_ratio_mean)
    if valid_fit.sum() > 5:
        A = np.column_stack([
            np.ones(valid_fit.sum()),
            R_sq[valid_fit],
            R_sq_dev[valid_fit],
        ])
        y = D_ratio_mean[valid_fit]
        coeffs, residuals, _, _ = np.linalg.lstsq(A, y, rcond=None)

        predicted = A @ coeffs
        ss_res = np.sum((y - predicted)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_sq_fit = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        print(f"\n  ANALYTICAL FIT: D/σ² = {coeffs[0]:.3f} + {coeffs[1]:.3f}·(1-C²)² + {coeffs[2]:.3f}·(1-C²)²·(C-φ⁻¹)²")
        print(f"  R² = {r_sq_fit:.4f}")

        # Simpler model: D/σ² = a + b·(1-C²)²
        A2 = np.column_stack([
            np.ones(valid_fit.sum()),
            R_sq[valid_fit],
        ])
        coeffs2, _, _, _ = np.linalg.lstsq(A2, y, rcond=None)
        predicted2 = A2 @ coeffs2
        ss_res2 = np.sum((y - predicted2)**2)
        r_sq_fit2 = 1 - ss_res2 / ss_tot if ss_tot > 0 else 0

        print(f"\n  SIMPLER FIT: D/σ² = {coeffs2[0]:.3f} + {coeffs2[1]:.3f}·(1-C²)²")
        print(f"  R² = {r_sq_fit2:.4f}")

        # Even simpler: D/σ² = a + b·(1-C²)
        R_lin = (1 - C_test**2)
        A3 = np.column_stack([
            np.ones(valid_fit.sum()),
            R_lin[valid_fit],
        ])
        coeffs3, _, _, _ = np.linalg.lstsq(A3, y, rcond=None)
        predicted3 = A3 @ coeffs3
        ss_res3 = np.sum((y - predicted3)**2)
        r_sq_fit3 = 1 - ss_res3 / ss_tot if ss_tot > 0 else 0

        print(f"\n  LINEAR FIT: D/σ² = {coeffs3[0]:.3f} + {coeffs3[1]:.3f}·(1-C²)")
        print(f"  R² = {r_sq_fit3:.4f}")

        # Print measured vs predicted comparison
        print(f"\n  {'C':>6s}  {'D/σ²_meas':>10s}  {'D/σ²_pred':>10s}  {'residual':>10s}")
        for i in range(0, len(C_test), 3):
            if valid_fit[i]:
                idx_in_valid = np.sum(valid_fit[:i+1]) - 1
                print(f"  {C_test[i]:6.3f}  {y[idx_in_valid]:10.3f}  {predicted[idx_in_valid]:10.3f}  {y[idx_in_valid]-predicted[idx_in_valid]:+10.3f}")

    # Check universality: does D/σ² collapse across noise levels?
    print(f"\n  UNIVERSALITY CHECK: D/σ² at C=0.50 across noise levels:")
    for noise_key in sorted(D_ratio_by_noise.keys()):
        noise_val = float(noise_key)
        mask = (np.abs(C_arr - 0.50) < 0.03) & (np.abs(noise_arr - noise_val) < 0.0005)
        if mask.sum() > 0:
            print(f"    σ={noise_key}: D/σ² = {np.mean(D_ratio_arr[mask]):.3f} ± {np.std(D_ratio_arr[mask]):.3f} (n={mask.sum()})")

    print(f"\n  UNIVERSALITY CHECK: D/σ² at C=0.80 across noise levels:")
    for noise_key in sorted(D_ratio_by_noise.keys()):
        noise_val = float(noise_key)
        mask = (np.abs(C_arr - 0.80) < 0.03) & (np.abs(noise_arr - noise_val) < 0.0005)
        if mask.sum() > 0:
            print(f"    σ={noise_key}: D/σ² = {np.mean(D_ratio_arr[mask]):.3f} ± {np.std(D_ratio_arr[mask]):.3f} (n={mask.sum()})")

    sys.stdout.flush()
    return {
        'C_test': C_test.tolist(),
        'D_ratio_mean': D_ratio_mean.tolist(),
        'D_ratio_std': D_ratio_std.tolist(),
    }


# ─── Experiment F: Probability Current Test ───

def expF_probability_current(km_data):
    """In true steady state, the probability current J(C) must be zero everywhere.

    J(C) = μ(C)·P(C) - (1/2)·d[D(C)·P(C)]/dC

    If J ≠ 0, the system is NOT in equilibrium — there's a probability current
    (e.g., from boundary effects or non-equilibrium dynamics).

    This is an independent check on the Fokker-Planck reconstruction.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Probability Current J(C) — Equilibrium Test")
    print("=" * 70)
    sys.stdout.flush()

    for key, km in km_data.items():
        noise = km['noise']
        C_bins = np.array(km['C_bins'])
        mu = np.array(km['mu'])
        D = np.array(km['D'])
        valid = np.array(km['valid'])
        n_pts = np.array(km['n_pts']).astype(float)

        mask = valid & ~np.isnan(mu) & ~np.isnan(D) & (D > 0) & (n_pts > 200)
        if mask.sum() < 10:
            continue

        C_v = C_bins[mask]
        mu_v = mu[mask]
        D_v = D[mask]
        n_v = n_pts[mask]

        # P(C) from histogram
        P = n_v / (n_v.sum() * (C_v[1] - C_v[0]))

        # Probability current: J = μ·P - (1/2)·d(D·P)/dC
        DP = D_v * P
        dDP_dC = np.gradient(DP, C_v)
        J = mu_v * P - 0.5 * dDP_dC

        # Normalize J by P for interpretability
        J_normalized = J / np.maximum(P, 1e-10)

        # Check magnitude relative to drift
        J_rms = np.sqrt(np.mean(J**2))
        mu_rms = np.sqrt(np.mean((mu_v * P)**2))
        ratio = J_rms / mu_rms if mu_rms > 0 else float('inf')

        print(f"\n  noise={noise:.3f}:")
        print(f"    J_rms = {J_rms:.6f}")
        print(f"    |μ·P|_rms = {mu_rms:.6f}")
        print(f"    J_rms / |μP|_rms = {ratio:.4f}")
        if ratio < 0.15:
            print(f"    → EQUILIBRIUM (J ≈ 0, detailed balance holds)")
        elif ratio < 0.30:
            print(f"    → NEAR-EQUILIBRIUM (small current)")
        else:
            print(f"    → NON-EQUILIBRIUM (significant probability current)")

        # Where is J largest?
        peak_idx = np.argmax(np.abs(J))
        print(f"    Peak |J| at C = {C_v[peak_idx]:.3f}")

    sys.stdout.flush()


# ─── Main ───

if __name__ == '__main__':
    print("Thor Session #83: Fokker-Planck Reconstruction")
    print("State-Dependent Diffusion and the Correct Effective Potential")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    sys.stdout.flush()

    all_results = {}

    # A: High-resolution Kramers-Moyal coefficients
    print("\n>>> Running Experiment A: Kramers-Moyal coefficients...")
    sys.stdout.flush()
    km_data = expA_kramers_moyal()
    all_results['expA'] = km_data

    # B: Three-method potential comparison
    print("\n>>> Running Experiment B: Three-method comparison...")
    sys.stdout.flush()
    pot_comparison = expB_potential_comparison(km_data)
    all_results['expB'] = pot_comparison

    # C: Noise-independence test
    print("\n>>> Running Experiment C: Noise-independence test...")
    sys.stdout.flush()
    potentials, barrier_heights = expC_noise_independence(km_data)
    all_results['expC_barriers'] = barrier_heights

    # D: Corrected Arrhenius
    print("\n>>> Running Experiment D: Corrected Arrhenius...")
    sys.stdout.flush()
    rate_data = expD_corrected_arrhenius(km_data, barrier_heights)
    all_results['expD'] = rate_data

    # E: Analytical diffusion
    print("\n>>> Running Experiment E: Analytical D(C) prediction...")
    sys.stdout.flush()
    diff_analysis = expE_analytical_diffusion(km_data)
    all_results['expE'] = diff_analysis

    # F: Probability current
    print("\n>>> Running Experiment F: Probability current...")
    sys.stdout.flush()
    expF_probability_current(km_data)

    # ─── SYNTHESIS ───
    print("\n" + "=" * 70)
    print("SYNTHESIS: Fokker-Planck Reconstruction")
    print("=" * 70)

    print("\n  SESSION QUESTIONS:")
    print("  1. Does accounting for D(C) change the effective potential?")
    print("  2. Does the corrected potential become noise-independent?")
    print("  3. Can we predict D(C) analytically from R(C) = 1-C²?")
    print("  4. Is the system truly in equilibrium (J = 0)?")

    # Extract key findings
    if 'V2' in barrier_heights:
        bhs = barrier_heights['V2']
        dUs = [b['dU'] for b in bhs]
        cv = np.std(dUs) / np.mean(dUs) if np.mean(dUs) > 0 else float('inf')
        print(f"\n  ANSWER 1-2: V₂ barrier height CV across noise = {cv:.4f}")
        if cv < 0.15:
            print(f"    → YES: Corrected potential is noise-INDEPENDENT!")
            print(f"    → S82's noise-dependence was an ARTIFACT of constant-D assumption")
        elif cv < 0.30:
            print(f"    → PARTIALLY: Some noise-dependence remains")
        else:
            print(f"    → NO: Potential is genuinely noise-dependent")

    if 'V1' in barrier_heights:
        bhs = barrier_heights['V1']
        dUs = [b['dU'] for b in bhs]
        cv1 = np.std(dUs) / np.mean(dUs) if np.mean(dUs) > 0 else float('inf')
        print(f"  V₁ (constant-D) barrier height CV = {cv1:.4f}")

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

    with open('thor_session_83_fokker_planck_results.json', 'w') as f:
        json.dump(make_serializable(all_results), f, indent=2)

    print(f"\nResults saved to thor_session_83_fokker_planck_results.json")
    print(f"Completed: {datetime.now().isoformat()}")
    sys.stdout.flush()
