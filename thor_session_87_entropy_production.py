#!/usr/bin/env python3
"""
Thor Session #87: Entropy Production and the Arrow of Time

Sessions 82-86 established: coherence dynamics are BISTABLE with mean-field
exponents, suprathreshold stochastic resonance at σ=0.011, and an
information channel capacity of ~0.023 bits at the optimum.

THE QUESTION: What is the thermodynamic cost of this information processing?
The system is a noise-driven engine that converts environmental noise into
signal detection. Every such engine must produce entropy.

KEY CONCEPTS:
  - Entropy production rate: σ_ep = <J·F/D> where J is probability current,
    F is drift force, D is diffusion
  - For discrete trajectories: σ_ep ≈ Σ (ΔC - μΔt)² / (2DΔt) - d/2·ln(2πDΔt)
    compared to time-reversed path
  - Time-reversal asymmetry: KL divergence between forward and reversed paths
  - Information-thermodynamic bound: bits ≤ σ_ep / (2·ln2)

EXPERIMENTS:
  A: Entropy production rate vs noise — where is dissipation maximized?
  B: Time-reversal asymmetry — can you tell time's direction from C(t)?
  C: Fluctuation theorem test — P(σ)/P(-σ) = exp(σ)?
  D: Dissipation per switching event — thermodynamic cost of each transition
  E: Information-thermodynamic efficiency — bits per unit entropy production
  F: Landauer limit — does switching cost ≥ kT·ln2 per bit erased?

Builds on: S82 (Kramers), S83 (Fokker-Planck D(C)), S86 (SR + MI)
"""

import numpy as np
import json
import sys
from datetime import datetime
from thor_session_81_phase_transition import run_fast


# ─── Enhanced simulation returning full trajectory + increments ───

def run_with_increments(N, noise_std, steps, seed=None,
                        kappa_phase=0.10, kappa_C=0.15,
                        omega_base=0.1, omega_spread=0.02,
                        phi_inverse=0.618, dt=0.1, C_threshold=0.55):
    """Simulation that records both trajectory AND deterministic drift at each step.

    This lets us decompose ΔC = drift·dt + noise·√dt to measure entropy production.
    """
    if seed is not None:
        np.random.seed(seed)

    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    C_collective = np.empty(steps)
    drift_collective = np.empty(steps)
    order_param = np.empty(steps)
    switches = 0
    prev_attractive = True
    switch_times = []

    for t in range(steps):
        C_mean = np.mean(C)
        C_collective[t] = C_mean
        order_param[t] = abs(np.mean(np.exp(1j * phase)))

        is_attractive = C_mean < C_threshold
        if t > 0 and is_attractive != prev_attractive:
            switches += 1
            switch_times.append(t)
        prev_attractive = is_attractive

        # Phase coupling
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        phase = (phase + dt * dphase) % (2 * np.pi)

        # Coherence dynamics — record drift BEFORE adding noise
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C.mean() - C) * R_func
        dC_drift = intrinsic + c_coupling
        drift_collective[t] = np.mean(dC_drift)

        C = np.clip(C + dt * dC_drift, 0, 1)

        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C_collective': C_collective,
        'drift_collective': drift_collective,
        'order_param': order_param,
        'switches': switches,
        'switch_times': np.array(switch_times),
    }


# ─── Experiment A: Entropy Production Rate vs Noise ───

def expA_entropy_production_vs_noise():
    """Measure entropy production rate across the noise spectrum.

    For a 1D Langevin process dC = μ(C)dt + σdW:
      entropy production rate = <μ²>/D where D = σ²/2

    For the collective coordinate, we use the measured drift and
    noise intensity to compute the local entropy production.

    Also compute via time-series: σ_ep = lim (1/T) Σ ln[P(ΔC|C) / P(-ΔC|C)]
    """
    print("=" * 70)
    print("EXPERIMENT A: Entropy Production Rate vs Noise Level")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 200_000
    warmup = 60_000
    noise_levels = np.array([0.005, 0.007, 0.009, 0.010, 0.011, 0.012,
                              0.013, 0.014, 0.016, 0.018, 0.020, 0.025])
    dt = 0.1
    results = []

    for sigma in noise_levels:
        ep_rates = []
        for seed in range(5):
            res = run_with_increments(N, sigma, steps, seed=seed)
            C = res['C_collective'][warmup:]
            mu = res['drift_collective'][warmup:]

            # Method 1: <μ²>/D where D = σ² (effective diffusion for collective coord)
            # The collective diffusion is σ²/N for N independent agents
            D_eff = sigma**2 / N
            ep_rate_drift = np.mean(mu**2) / D_eff

            # Method 2: From trajectory increments
            # ΔC = C[t+1] - C[t], forward path log-likelihood vs reverse
            dC = np.diff(C)
            # Forward: P(ΔC|C) ∝ exp(-(ΔC - μdt)²/(2Ddt))
            # Reverse: P(-ΔC|C') ∝ exp(-(-ΔC - μ'dt)²/(2Ddt))
            # σ_ep per step = (ΔC·μ·dt)/(D·dt) = ΔC·μ/D
            mu_steps = mu[:-1]
            ep_per_step = dC * mu_steps * dt / (D_eff * dt)
            ep_rate_traj = np.mean(ep_per_step) / dt

            ep_rates.append({
                'ep_drift': float(ep_rate_drift),
                'ep_traj': float(ep_rate_traj),
            })

        ep_drift_mean = np.mean([r['ep_drift'] for r in ep_rates])
        ep_drift_std = np.std([r['ep_drift'] for r in ep_rates])
        ep_traj_mean = np.mean([r['ep_traj'] for r in ep_rates])
        ep_traj_std = np.std([r['ep_traj'] for r in ep_rates])

        result = {
            'sigma': float(sigma),
            'ep_drift_mean': float(ep_drift_mean),
            'ep_drift_std': float(ep_drift_std),
            'ep_traj_mean': float(ep_traj_mean),
            'ep_traj_std': float(ep_traj_std),
            'D_eff': float(D_eff),
        }
        results.append(result)
        print(f"  σ={sigma:.4f}: σ_ep(drift)={ep_drift_mean:.6f}±{ep_drift_std:.6f}  "
              f"σ_ep(traj)={ep_traj_mean:.6f}±{ep_traj_std:.6f}")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    ep_drifts = [r['ep_drift_mean'] for r in results]
    peak_idx = np.argmax(ep_drifts)
    print(f"  Peak entropy production at σ={results[peak_idx]['sigma']:.4f}")
    print(f"  Peak rate = {results[peak_idx]['ep_drift_mean']:.6f}")

    ep_trajs = [r['ep_traj_mean'] for r in results]
    peak_idx2 = np.argmax(ep_trajs)
    print(f"  Trajectory method peak at σ={results[peak_idx2]['sigma']:.4f}")

    return results


# ─── Experiment B: Time-Reversal Asymmetry ───

def expB_time_reversal():
    """Quantify how distinguishable forward from reversed trajectories are.

    For an equilibrium system, the forward and reversed trajectories have
    identical statistics. For a non-equilibrium system, they differ —
    the KL divergence D_KL(P_fwd || P_rev) = <σ_ep> / 2.

    We measure this by:
    1. Computing transition matrices P(C_{t+1} | C_t) for forward and reversed
    2. KL divergence between them
    3. A simpler test: skewness of ΔC conditioned on C — nonzero means time-asymmetric
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Time-Reversal Asymmetry")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 500_000
    warmup = 100_000
    noise_levels = [0.007, 0.011, 0.014, 0.020]
    n_bins = 50
    results = []

    for sigma in noise_levels:
        res = run_with_increments(N, sigma, steps, seed=42)
        C = res['C_collective'][warmup:]
        dC = np.diff(C)
        C_mid = C[:-1]

        # Bin by C value, compute statistics of ΔC in each bin
        bins = np.linspace(C.min(), C.max(), n_bins + 1)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        mean_dC = np.zeros(n_bins)
        skew_dC = np.zeros(n_bins)
        counts = np.zeros(n_bins)

        for i in range(n_bins):
            mask = (C_mid >= bins[i]) & (C_mid < bins[i+1])
            if mask.sum() > 100:
                dc_bin = dC[mask]
                counts[i] = len(dc_bin)
                mean_dC[i] = np.mean(dc_bin)
                m3 = np.mean((dc_bin - np.mean(dc_bin))**3)
                m2 = np.mean((dc_bin - np.mean(dc_bin))**2)
                skew_dC[i] = m3 / (m2**1.5 + 1e-30)

        # Forward transition matrix
        C_digitized = np.digitize(C, bins) - 1
        C_digitized = np.clip(C_digitized, 0, n_bins - 1)
        T_fwd = np.zeros((n_bins, n_bins))
        for t in range(len(C) - 1):
            T_fwd[C_digitized[t], C_digitized[t+1]] += 1

        # Normalize rows
        row_sums = T_fwd.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        T_fwd_norm = T_fwd / row_sums

        # Reversed = transpose of forward (for detailed balance test)
        # If detailed balance holds: T_fwd[i,j]·π[i] = T_fwd[j,i]·π[j]
        pi = T_fwd.sum(axis=1)
        pi = pi / pi.sum()

        # Measure detailed balance violation
        db_violation = 0
        db_count = 0
        for i in range(n_bins):
            for j in range(i+1, n_bins):
                if T_fwd[i, j] > 10 and T_fwd[j, i] > 10:
                    forward_flow = T_fwd[i, j] * pi[i]
                    reverse_flow = T_fwd[j, i] * pi[j]
                    if forward_flow > 0 and reverse_flow > 0:
                        ratio = forward_flow / reverse_flow
                        db_violation += abs(np.log(ratio))
                        db_count += 1

        avg_db_violation = db_violation / max(db_count, 1)

        # KL divergence between T_fwd and T_rev = T_fwd.T (with proper normalization)
        T_rev = T_fwd.T.copy()
        row_sums_rev = T_rev.sum(axis=1, keepdims=True)
        row_sums_rev[row_sums_rev == 0] = 1
        T_rev_norm = T_rev / row_sums_rev

        kl_div = 0
        kl_count = 0
        for i in range(n_bins):
            if pi[i] > 0.001:
                for j in range(n_bins):
                    if T_fwd_norm[i, j] > 1e-6 and T_rev_norm[i, j] > 1e-6:
                        kl_div += pi[i] * T_fwd_norm[i, j] * np.log(T_fwd_norm[i, j] / T_rev_norm[i, j])
                        kl_count += 1

        # Overall skewness of ΔC (should be zero for equilibrium)
        overall_skew = float(np.mean(dC**3) / (np.mean(dC**2)**1.5 + 1e-30))

        # Time asymmetry via velocity autocorrelation
        # For equilibrium: <v(t)·v(t+τ)> is symmetric in τ
        # Non-equilibrium: asymmetric
        max_lag = 200
        v = dC
        v_centered = v - np.mean(v)
        v_var = np.var(v)
        autocorr = np.correlate(v_centered[:10000], v_centered[:10000], mode='full')
        mid = len(autocorr) // 2
        fwd_corr = autocorr[mid:mid+max_lag]
        rev_corr = autocorr[mid-max_lag+1:mid+1][::-1]
        time_asym = np.mean(np.abs(fwd_corr - rev_corr)) / (np.abs(fwd_corr).mean() + 1e-30)

        result = {
            'sigma': float(sigma),
            'overall_skew': overall_skew,
            'db_violation_mean': float(avg_db_violation),
            'kl_fwd_rev': float(kl_div),
            'time_asymmetry': float(time_asym),
            'n_bins_active': int((pi > 0.001).sum()),
        }
        results.append(result)
        print(f"  σ={sigma:.3f}: skew(ΔC)={overall_skew:.4f}  "
              f"DB_violation={avg_db_violation:.4f}  "
              f"KL(fwd||rev)={kl_div:.6f}  "
              f"time_asym={time_asym:.4f}")
        sys.stdout.flush()

    return results


# ─── Experiment C: Fluctuation Theorem ───

def expC_fluctuation_theorem():
    """Test the detailed fluctuation theorem: P(σ_ep=+A) / P(σ_ep=-A) = exp(A).

    For each trajectory segment of length τ, compute the entropy production.
    The ratio of probabilities of positive to negative entropy production
    should follow an exponential relationship.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Fluctuation Theorem Test")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 500_000
    warmup = 100_000
    dt = 0.1
    segment_lengths = [10, 50, 100, 500]
    sigma = 0.011  # SR optimum
    results = []

    res = run_with_increments(N, sigma, steps, seed=42)
    C = res['C_collective'][warmup:]
    mu = res['drift_collective'][warmup:]
    D_eff = sigma**2 / N

    for seg_len in segment_lengths:
        # Compute entropy production for each segment
        n_segments = (len(C) - 1) // seg_len
        ep_segments = np.zeros(n_segments)

        for s in range(n_segments):
            start = s * seg_len
            end = start + seg_len
            dC_seg = np.diff(C[start:end+1])
            mu_seg = mu[start:end]
            # σ_ep for segment = Σ (ΔC·μ)/(D) per step
            ep_segments[s] = np.sum(dC_seg * mu_seg * dt) / (D_eff * dt)

        # Test: ln[P(σ)/P(-σ)] ≈ σ
        # Bin the entropy production values
        ep_abs_max = np.percentile(np.abs(ep_segments), 95)
        if ep_abs_max < 1e-10:
            ep_abs_max = 1.0
        bins = np.linspace(-ep_abs_max, ep_abs_max, 41)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        hist, _ = np.histogram(ep_segments, bins=bins, density=True)

        # Compare P(+A) vs P(-A) for positive A
        n_half = len(bin_centers) // 2
        log_ratios = []
        ep_values = []
        for i in range(n_half):
            pos_idx = n_half + i
            neg_idx = n_half - 1 - i
            if hist[pos_idx] > 0 and hist[neg_idx] > 0:
                log_ratio = np.log(hist[pos_idx] / hist[neg_idx])
                log_ratios.append(log_ratio)
                ep_values.append(bin_centers[pos_idx])

        # Fit: log_ratio = slope * ep_value (theory predicts slope = 1)
        if len(ep_values) > 3:
            ep_arr = np.array(ep_values)
            lr_arr = np.array(log_ratios)
            slope = np.sum(ep_arr * lr_arr) / np.sum(ep_arr**2)
            residuals = lr_arr - slope * ep_arr
            r_squared = 1 - np.sum(residuals**2) / (np.sum((lr_arr - lr_arr.mean())**2) + 1e-30)
        else:
            slope = float('nan')
            r_squared = float('nan')

        result = {
            'segment_length': seg_len,
            'n_segments': int(n_segments),
            'ep_mean': float(np.mean(ep_segments)),
            'ep_std': float(np.std(ep_segments)),
            'frac_positive': float(np.mean(ep_segments > 0)),
            'ft_slope': float(slope),
            'ft_r_squared': float(r_squared),
        }
        results.append(result)
        print(f"  τ={seg_len:4d}: <σ_ep>={np.mean(ep_segments):.4f}±{np.std(ep_segments):.4f}  "
              f"P(+)={np.mean(ep_segments > 0):.3f}  "
              f"FT slope={slope:.3f} (theory=1.0)  R²={r_squared:.3f}")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    print(f"  Second law: <σ_ep> > 0 for all segment lengths? "
          f"{all(r['ep_mean'] > 0 for r in results)}")
    slopes_str = ', '.join(f'{r["ft_slope"]:.3f}' for r in results)
    print(f"  Fluctuation theorem slope → 1 as τ → ∞? slopes = [{slopes_str}]")

    return results


# ─── Experiment D: Dissipation Per Switching Event ───

def expD_switching_cost():
    """Measure the thermodynamic cost of each order↔breathing transition.

    For each switching event:
    1. Extract the trajectory segment around the switch
    2. Compute the entropy produced during the transition
    3. Compare to the barrier height ΔU from Kramers theory (S82)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Thermodynamic Cost Per Switching Event")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 500_000
    warmup = 100_000
    dt = 0.1
    noise_levels = [0.009, 0.011, 0.013, 0.015, 0.018]
    results = []

    for sigma in noise_levels:
        D_eff = sigma**2 / N
        all_switch_costs = []

        for seed in range(5):
            res = run_with_increments(N, sigma, steps, seed=seed)
            C = res['C_collective']
            mu = res['drift_collective']
            switch_times = res['switch_times']

            # Only use switches after warmup
            st = switch_times[switch_times > warmup]
            if len(st) < 2:
                continue

            # For each switch, compute entropy production in a window around it
            window = 50  # steps before and after
            for sw in st:
                if sw - window < warmup or sw + window >= steps - 1:
                    continue
                seg_C = C[sw-window:sw+window+1]
                seg_mu = mu[sw-window:sw+window]
                dC = np.diff(seg_C)
                ep_switch = np.sum(dC * seg_mu * dt) / (D_eff * dt)
                all_switch_costs.append(float(ep_switch))

        if len(all_switch_costs) > 0:
            costs = np.array(all_switch_costs)
            result = {
                'sigma': float(sigma),
                'n_switches': len(all_switch_costs),
                'ep_per_switch_mean': float(np.mean(costs)),
                'ep_per_switch_median': float(np.median(costs)),
                'ep_per_switch_std': float(np.std(costs)),
                'frac_positive': float(np.mean(costs > 0)),
                'ep_per_switch_abs_mean': float(np.mean(np.abs(costs))),
            }
        else:
            result = {
                'sigma': float(sigma),
                'n_switches': 0,
                'ep_per_switch_mean': float('nan'),
            }
        results.append(result)
        n_sw = result['n_switches']
        if n_sw > 0:
            print(f"  σ={sigma:.3f}: {n_sw} switches, "
                  f"<σ_ep/switch>={result['ep_per_switch_mean']:.4f}±{result['ep_per_switch_std']:.4f}  "
                  f"|σ_ep|={result['ep_per_switch_abs_mean']:.4f}  "
                  f"P(+)={result['frac_positive']:.3f}")
        else:
            print(f"  σ={sigma:.3f}: no switches detected")
        sys.stdout.flush()

    # Kramers barrier from S82: ΔU ≈ 1.64e-4
    # Dissipation per switch should relate to barrier height
    print("\n  ANALYSIS:")
    print(f"  Kramers barrier ΔU ≈ 1.64e-4 (from S82)")
    for r in results:
        if r['n_switches'] > 0:
            ratio = r['ep_per_switch_abs_mean'] / 1.64e-4 if r['ep_per_switch_abs_mean'] else float('nan')
            print(f"  σ={r['sigma']:.3f}: |σ_ep|/ΔU = {ratio:.1f}")

    return results


# ─── Experiment E: Information-Thermodynamic Efficiency ───

def expE_info_thermo_efficiency():
    """Measure bits of information transfer per unit of entropy production.

    From S86: At σ=0.011, MI = 0.023 bits between signal and response.
    Here we measure both MI and σ_ep simultaneously to get the efficiency:
      η = MI / σ_ep

    The fundamental bound is: MI ≤ σ_ep / (2·ln2)
    So efficiency η ≤ 1/(2·ln2) ≈ 0.72 bits per unit entropy
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT E: Information-Thermodynamic Efficiency")
    print("=" * 70)
    sys.stdout.flush()

    from thor_session_86_stochastic_resonance import run_forced

    N = 4
    steps = 200_000
    warmup = 60_000
    dt = 0.1
    signal_amp = 0.005
    signal_freq = 0.001
    noise_levels = [0.007, 0.009, 0.011, 0.013, 0.015, 0.018]
    results = []

    for sigma in noise_levels:
        D_eff = sigma**2 / N
        mi_values = []
        ep_values = []

        for seed in range(5):
            res = run_forced(N, sigma, steps, seed=seed,
                           signal_amp=signal_amp, signal_freq=signal_freq)
            C = res['C_collective'][warmup:]
            signal = res['signal'][warmup:]

            # Mutual information via binning
            n_bins = 20
            C_bins = np.linspace(C.min(), C.max(), n_bins + 1)
            S_bins = np.linspace(signal.min(), signal.max(), n_bins + 1)

            H_joint = np.histogram2d(C, signal, bins=[C_bins, S_bins])[0]
            H_joint = H_joint / H_joint.sum()
            H_C = H_joint.sum(axis=1)
            H_S = H_joint.sum(axis=0)

            mi = 0
            for i in range(n_bins):
                for j in range(n_bins):
                    if H_joint[i, j] > 1e-10 and H_C[i] > 1e-10 and H_S[j] > 1e-10:
                        mi += H_joint[i, j] * np.log2(H_joint[i, j] / (H_C[i] * H_S[j]))
            mi_values.append(mi)

            # Entropy production (approximate — we don't have drift from run_forced)
            # Use trajectory-based estimate: σ_ep ≈ <(ΔC)²>/(2·D_eff·dt) - 1/(2dt)
            # Actually simpler: use the velocity autocorrelation method
            dC = np.diff(C)
            # Entropy production per step ≈ <dC>²/(2·D_eff·dt) for the mean current
            # Better: total EP = Σ (mean_drift)² / D_eff
            # Approximate drift from ΔC statistics in bins
            C_mid = C[:-1]
            C_dig = np.digitize(C_mid, C_bins) - 1
            C_dig = np.clip(C_dig, 0, n_bins - 1)
            local_drift = np.zeros(n_bins)
            for b in range(n_bins):
                mask = C_dig == b
                if mask.sum() > 10:
                    local_drift[b] = np.mean(dC[mask]) / dt

            ep_rate = 0
            for b in range(n_bins):
                if H_C[b] > 1e-10:
                    ep_rate += H_C[b] * local_drift[b]**2 / D_eff
            ep_values.append(ep_rate)

        mi_mean = float(np.mean(mi_values))
        mi_std = float(np.std(mi_values))
        ep_mean = float(np.mean(ep_values))
        ep_std = float(np.std(ep_values))

        # Efficiency: bits per unit entropy production
        landauer_bound = 1.0 / (2.0 * np.log(2))  # ≈ 0.72
        efficiency = mi_mean / (ep_mean + 1e-30)

        result = {
            'sigma': float(sigma),
            'MI_bits': mi_mean,
            'MI_std': mi_std,
            'ep_rate': ep_mean,
            'ep_std': ep_std,
            'efficiency': efficiency,
            'landauer_bound': landauer_bound,
            'efficiency_fraction': efficiency / landauer_bound,
        }
        results.append(result)
        print(f"  σ={sigma:.3f}: MI={mi_mean:.4f}±{mi_std:.4f} bits  "
              f"σ_ep={ep_mean:.6f}±{ep_std:.6f}  "
              f"η={efficiency:.4f} bits/ep  "
              f"(η/η_max={efficiency/landauer_bound:.3f})")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    print(f"  Landauer bound: η_max = 1/(2·ln2) ≈ {1/(2*np.log(2)):.4f} bits per unit σ_ep")
    mi_vals = [r['MI_bits'] for r in results]
    eff_vals = [r['efficiency'] for r in results]
    peak_mi = np.argmax(mi_vals)
    peak_eff = np.argmax(eff_vals)
    print(f"  Peak MI at σ={results[peak_mi]['sigma']:.3f}")
    print(f"  Peak efficiency at σ={results[peak_eff]['sigma']:.3f}")
    if peak_mi != peak_eff:
        print(f"  *** MI and efficiency peak at DIFFERENT noise levels! ***")
        print(f"  This means the most informative noise is NOT the most efficient.")
    else:
        print(f"  MI and efficiency peak at the SAME noise level.")

    return results


# ─── Experiment F: Irreversibility Spectrum ───

def expF_irreversibility_spectrum():
    """Measure the spectral decomposition of irreversibility.

    The entropy production can be decomposed by frequency:
      σ_ep(ω) = |J(ω)|² / D(ω)

    where J(ω) is the Fourier transform of the probability current.
    This tells us WHICH timescales contribute to irreversibility.

    Prediction: the switching timescale (Kramers rate) should dominate.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Irreversibility Spectrum")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 500_000
    warmup = 100_000
    dt = 0.1
    noise_levels = [0.009, 0.011, 0.014, 0.020]
    results = []

    for sigma in noise_levels:
        res = run_with_increments(N, sigma, steps, seed=42)
        C = res['C_collective'][warmup:]
        mu = res['drift_collective'][warmup:]
        D_eff = sigma**2 / N

        # Velocity = dC/dt
        v = np.diff(C) / dt

        # Power spectrum of velocity
        n_fft = min(len(v), 2**16)
        v_fft = np.fft.rfft(v[:n_fft])
        freqs = np.fft.rfftfreq(n_fft, d=dt)
        psd_v = np.abs(v_fft)**2 / n_fft

        # Power spectrum of drift (deterministic part)
        mu_fft = np.fft.rfft(mu[:n_fft])
        psd_mu = np.abs(mu_fft)**2 / n_fft

        # Irreversibility at each frequency: |drift|² / D
        irreversibility = psd_mu / D_eff

        # Find dominant frequency of irreversibility
        # Skip DC component
        irrev_no_dc = irreversibility.copy()
        irrev_no_dc[0] = 0
        peak_freq_idx = np.argmax(irrev_no_dc[:len(irrev_no_dc)//4])
        peak_freq = freqs[peak_freq_idx] if peak_freq_idx < len(freqs) else 0

        # Kramers rate from S82: r_K ≈ 0.05 * exp(-1.64e-4/σ²) (approximate)
        kramers_rate = 0.05 * np.exp(-1.64e-4 / sigma**2)

        # Fraction of irreversibility at low freq (< 0.01) vs high freq
        low_freq_mask = freqs < 0.01
        high_freq_mask = freqs >= 0.01
        frac_low = np.sum(irreversibility[low_freq_mask]) / (np.sum(irreversibility) + 1e-30)

        # Switching rate from data
        switches = res['switches']
        total_time = (steps - warmup) * dt
        empirical_rate = switches / total_time

        result = {
            'sigma': float(sigma),
            'peak_irrev_freq': float(peak_freq),
            'kramers_rate': float(kramers_rate),
            'empirical_switch_rate': float(empirical_rate),
            'frac_low_freq': float(frac_low),
            'total_irreversibility': float(np.sum(irreversibility)),
        }
        results.append(result)
        print(f"  σ={sigma:.3f}: peak_freq={peak_freq:.5f}  "
              f"r_Kramers={kramers_rate:.5f}  "
              f"r_empirical={empirical_rate:.5f}  "
              f"frac_low_f={frac_low:.3f}")
        sys.stdout.flush()

    return results


# ─── Main ───

def main():
    print("=" * 70)
    print("THOR SESSION #87: ENTROPY PRODUCTION AND THE ARROW OF TIME")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    print("MOTIVATION: Sessions 82-86 established the coherence system as a")
    print("noise-driven bistable information engine. Every information engine")
    print("must produce entropy. This session quantifies the thermodynamic")
    print("costs and tests whether the SR optimum (σ=0.011) is also a")
    print("thermodynamic optimum.")
    print()
    sys.stdout.flush()

    all_results = {}

    all_results['A_entropy_production'] = expA_entropy_production_vs_noise()
    all_results['B_time_reversal'] = expB_time_reversal()
    all_results['C_fluctuation_theorem'] = expC_fluctuation_theorem()
    all_results['D_switching_cost'] = expD_switching_cost()
    all_results['E_info_efficiency'] = expE_info_thermo_efficiency()
    all_results['F_irreversibility_spectrum'] = expF_irreversibility_spectrum()

    # Save results
    with open('thor_session_87_entropy_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to thor_session_87_entropy_results.json")

    # ─── Synthesis ───
    print("\n" + "=" * 70)
    print("SYNTHESIS")
    print("=" * 70)

    print("\n1. ENTROPY PRODUCTION LANDSCAPE:")
    ep_results = all_results['A_entropy_production']
    sigmas = [r['sigma'] for r in ep_results]
    eps = [r['ep_drift_mean'] for r in ep_results]
    peak_ep = sigmas[np.argmax(eps)]
    print(f"   Peak entropy production at σ = {peak_ep:.4f}")
    print(f"   SR optimum at σ = 0.011")
    if abs(peak_ep - 0.011) < 0.002:
        print(f"   → EP peaks NEAR the SR optimum!")
    else:
        print(f"   → EP peak is SEPARATED from SR optimum by Δσ = {abs(peak_ep-0.011):.4f}")

    print("\n2. ARROW OF TIME:")
    tr_results = all_results['B_time_reversal']
    for r in tr_results:
        print(f"   σ={r['sigma']:.3f}: KL(fwd||rev) = {r['kl_fwd_rev']:.6f}  "
              f"DB_violation = {r['db_violation_mean']:.4f}")

    print("\n3. FLUCTUATION THEOREM:")
    ft_results = all_results['C_fluctuation_theorem']
    for r in ft_results:
        print(f"   τ={r['segment_length']:4d}: slope = {r['ft_slope']:.3f} (theory=1.0)")

    print("\n4. SWITCHING COST:")
    sw_results = all_results['D_switching_cost']
    for r in sw_results:
        if r['n_switches'] > 0:
            print(f"   σ={r['sigma']:.3f}: {r['ep_per_switch_abs_mean']:.4f} entropy per switch")

    print("\n5. INFORMATION-THERMODYNAMIC EFFICIENCY:")
    ie_results = all_results['E_info_efficiency']
    for r in ie_results:
        print(f"   σ={r['sigma']:.3f}: η = {r['efficiency']:.4f} bits/ep  "
              f"({r['efficiency_fraction']:.1%} of Landauer)")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
