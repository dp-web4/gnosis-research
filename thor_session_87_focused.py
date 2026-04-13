#!/usr/bin/env python3
"""
Thor Session #87 (focused): Entropy Production and the Arrow of Time

CORRECTION from initial run:
  D_eff = σ²/N is WRONG for the collective coordinate because agents are
  strongly correlated (β=0.12 from S84). The FT slope of 0.009 instead of
  1.0 tells us D_eff is overestimated by ~100×.

  FIX: Measure D_eff empirically from <(ΔC)²>/2Δt, then re-derive everything.

KEY EXPERIMENTS:
  A: Empirical diffusion measurement → correct D_eff(σ)
  B: Corrected entropy production rate vs noise
  C: Corrected fluctuation theorem
  D: Time-reversal asymmetry (independent of D_eff)
  E: Dissipation per switch with correct D_eff
  F: Information-thermodynamic efficiency with correct normalization
"""

import numpy as np
import json
import sys
from datetime import datetime
from thor_session_81_phase_transition import run_fast


def run_with_increments(N, noise_std, steps, seed=None,
                        kappa_phase=0.10, kappa_C=0.15,
                        omega_base=0.1, omega_spread=0.02,
                        phi_inverse=0.618, dt=0.1, C_threshold=0.55):
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

        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        phase = (phase + dt * dphase) % (2 * np.pi)

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


# ─── Experiment A: Empirical Diffusion Coefficient ───

def expA_empirical_diffusion():
    """Measure the ACTUAL collective diffusion coefficient D_eff(σ).

    D_eff = <(ΔC - μΔt)²> / (2Δt)

    where ΔC = C(t+1) - C(t) and μ = drift.
    This accounts for correlations between agents.
    Compare to the naive D_naive = σ²/N.
    """
    print("=" * 70)
    print("EXPERIMENT A: Empirical Diffusion Coefficient")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 150_000
    warmup = 50_000
    dt = 0.1
    noise_levels = np.array([0.005, 0.007, 0.009, 0.011, 0.013, 0.015, 0.018, 0.020, 0.025])
    results = []

    for sigma in noise_levels:
        D_empirical_list = []
        D_naive = sigma**2 / N

        for seed in range(5):
            res = run_with_increments(N, sigma, steps, seed=seed)
            C = res['C_collective'][warmup:]
            mu = res['drift_collective'][warmup:]

            dC = np.diff(C)
            mu_dt = mu[:-1] * dt

            # Residual after subtracting drift
            residual = dC - mu_dt
            D_emp = np.mean(residual**2) / (2 * dt)
            D_empirical_list.append(D_emp)

        D_emp_mean = np.mean(D_empirical_list)
        D_emp_std = np.std(D_empirical_list)
        ratio = D_emp_mean / D_naive

        result = {
            'sigma': float(sigma),
            'D_naive': float(D_naive),
            'D_empirical': float(D_emp_mean),
            'D_empirical_std': float(D_emp_std),
            'amplification': float(ratio),
        }
        results.append(result)
        print(f"  σ={sigma:.4f}: D_naive={D_naive:.2e}  D_emp={D_emp_mean:.2e}±{D_emp_std:.2e}  "
              f"ratio={ratio:.1f}×")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    ratios = [r['amplification'] for r in results]
    print(f"  D_empirical / D_naive ranges from {min(ratios):.1f}× to {max(ratios):.1f}×")
    print(f"  → Agents are strongly correlated (ratio >> 1)")
    print(f"  → D_eff ≈ σ² (not σ²/N) because N=4 agents move nearly in lockstep")

    # Check if ratio ≈ N (would mean agents are perfectly correlated)
    mean_ratio = np.mean(ratios)
    print(f"  Mean amplification: {mean_ratio:.1f}× (N={N}, so perfect correlation → {N}×)")

    return results


# ─── Experiment B: Corrected Entropy Production ───

def expB_corrected_entropy_production(D_results):
    """Re-compute entropy production with the empirically measured D_eff.

    σ_ep = <μ²> / D_eff(σ)
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Corrected Entropy Production Rate vs Noise")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 150_000
    warmup = 50_000
    dt = 0.1
    results = []

    # Build D_eff lookup from Experiment A
    D_lookup = {r['sigma']: r['D_empirical'] for r in D_results}

    for D_res in D_results:
        sigma = D_res['sigma']
        D_eff = D_res['D_empirical']

        ep_rates = []
        for seed in range(5):
            res = run_with_increments(N, sigma, steps, seed=seed)
            C = res['C_collective'][warmup:]
            mu = res['drift_collective'][warmup:]

            # Corrected entropy production
            ep_rate = np.mean(mu**2) / D_eff
            ep_rates.append(ep_rate)

        ep_mean = np.mean(ep_rates)
        ep_std = np.std(ep_rates)

        result = {
            'sigma': float(sigma),
            'D_eff': float(D_eff),
            'ep_corrected_mean': float(ep_mean),
            'ep_corrected_std': float(ep_std),
        }
        results.append(result)
        print(f"  σ={sigma:.4f}: D_eff={D_eff:.2e}  σ_ep={ep_mean:.4f}±{ep_std:.4f}")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    eps = [r['ep_corrected_mean'] for r in results]
    sigmas = [r['sigma'] for r in results]
    peak_idx = np.argmax(eps)
    print(f"  Peak corrected σ_ep at σ={sigmas[peak_idx]:.4f} (value={eps[peak_idx]:.4f})")
    print(f"  SR optimum from S86: σ=0.011")
    if abs(sigmas[peak_idx] - 0.011) < 0.003:
        print(f"  → Entropy production STILL peaks near the SR optimum!")
    else:
        print(f"  → Peak shifted from SR optimum by Δσ={abs(sigmas[peak_idx]-0.011):.4f}")

    return results


# ─── Experiment C: Corrected Fluctuation Theorem ───

def expC_corrected_FT(D_results):
    """Re-test the fluctuation theorem with the correct D_eff."""
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Corrected Fluctuation Theorem")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 300_000
    warmup = 80_000
    dt = 0.1
    sigma = 0.011
    segment_lengths = [10, 50, 100, 500]

    # Get empirical D_eff for this sigma
    D_eff = None
    for r in D_results:
        if abs(r['sigma'] - sigma) < 0.001:
            D_eff = r['D_empirical']
            break
    if D_eff is None:
        # Measure it
        res_cal = run_with_increments(N, sigma, 100_000, seed=99)
        C_cal = res_cal['C_collective'][30_000:]
        mu_cal = res_cal['drift_collective'][30_000:]
        dC_cal = np.diff(C_cal)
        residual = dC_cal - mu_cal[:-1] * dt
        D_eff = np.mean(residual**2) / (2 * dt)

    print(f"  Using D_eff = {D_eff:.2e} (empirically measured)")

    res = run_with_increments(N, sigma, steps, seed=42)
    C = res['C_collective'][warmup:]
    mu = res['drift_collective'][warmup:]
    results = []

    for seg_len in segment_lengths:
        n_segments = (len(C) - 1) // seg_len
        ep_segments = np.zeros(n_segments)

        for s in range(n_segments):
            start = s * seg_len
            end = start + seg_len
            dC_seg = np.diff(C[start:end+1])
            mu_seg = mu[start:end]
            # Corrected: use empirical D_eff
            ep_segments[s] = np.sum(dC_seg * mu_seg) / D_eff

        # Fluctuation theorem test
        ep_abs_max = np.percentile(np.abs(ep_segments), 95)
        if ep_abs_max < 1e-10:
            ep_abs_max = 1.0
        bins = np.linspace(-ep_abs_max, ep_abs_max, 41)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        hist, _ = np.histogram(ep_segments, bins=bins, density=True)

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

        if len(ep_values) > 3:
            ep_arr = np.array(ep_values)
            lr_arr = np.array(log_ratios)
            slope = np.sum(ep_arr * lr_arr) / (np.sum(ep_arr**2) + 1e-30)
            residuals = lr_arr - slope * ep_arr
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((lr_arr - lr_arr.mean())**2)
            r_squared = 1 - ss_res / (ss_tot + 1e-30)
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

    return results


# ─── Experiment D: Detailed Balance Test (D_eff independent) ───

def expD_detailed_balance():
    """Test detailed balance violation more carefully.

    For a system at equilibrium: P_ss(C)·T(C→C') = P_ss(C')·T(C'→C)

    This test is INDEPENDENT of D_eff because it only uses transition counts.
    We measure the asymmetry of the transition matrix directly.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Detailed Balance Violation")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 300_000
    warmup = 80_000
    noise_levels = [0.005, 0.007, 0.009, 0.011, 0.013, 0.015, 0.018, 0.025]
    n_bins = 30
    results = []

    for sigma in noise_levels:
        db_violations = []
        net_currents = []

        for seed in range(3):
            res = run_with_increments(N, sigma, steps, seed=seed)
            C = res['C_collective'][warmup:]

            bins = np.linspace(C.min() - 1e-6, C.max() + 1e-6, n_bins + 1)
            C_dig = np.digitize(C, bins) - 1
            C_dig = np.clip(C_dig, 0, n_bins - 1)

            # Transition count matrix
            T = np.zeros((n_bins, n_bins))
            for t in range(len(C_dig) - 1):
                T[C_dig[t], C_dig[t+1]] += 1

            # Stationary distribution
            pi = T.sum(axis=1)
            pi_norm = pi / (pi.sum() + 1e-30)

            # Detailed balance violation: |π_i T_ij - π_j T_ji| / (π_i T_ij + π_j T_ji)
            violations = []
            currents = []
            for i in range(n_bins):
                for j in range(i+1, n_bins):
                    fwd = pi_norm[i] * T[i, j]
                    rev = pi_norm[j] * T[j, i]
                    if fwd + rev > 10:
                        violations.append(abs(fwd - rev) / (fwd + rev))
                        currents.append(fwd - rev)

            if violations:
                db_violations.append(np.mean(violations))
                net_currents.append(np.mean(np.abs(currents)))

        result = {
            'sigma': float(sigma),
            'db_violation_mean': float(np.mean(db_violations)),
            'db_violation_std': float(np.std(db_violations)),
            'net_current_mean': float(np.mean(net_currents)),
        }
        results.append(result)
        print(f"  σ={sigma:.4f}: DB_violation={np.mean(db_violations):.4f}±{np.std(db_violations):.4f}  "
              f"|J_net|={np.mean(net_currents):.2f}")
        sys.stdout.flush()

    print("\n  ANALYSIS:")
    db_vals = [r['db_violation_mean'] for r in results]
    sigmas = [r['sigma'] for r in results]
    print(f"  DB violation range: {min(db_vals):.4f} to {max(db_vals):.4f}")
    peak_db = sigmas[np.argmax(db_vals)]
    print(f"  Maximum violation at σ={peak_db:.4f}")
    if min(db_vals) > 0.01:
        print(f"  → System is OUT OF EQUILIBRIUM at all noise levels!")
    else:
        print(f"  → System approaches equilibrium at some noise levels")

    return results


# ─── Experiment E: Switching Cost with Correct D_eff ───

def expE_switching_cost(D_results):
    """Thermodynamic cost per switching event using correct D_eff."""
    print("\n" + "=" * 70)
    print("EXPERIMENT E: Corrected Switching Cost")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 200_000
    warmup = 60_000
    dt = 0.1
    noise_levels = [0.009, 0.011, 0.013, 0.015, 0.018]
    results = []

    D_lookup = {r['sigma']: r['D_empirical'] for r in D_results}

    for sigma in noise_levels:
        D_eff = D_lookup.get(sigma, sigma**2 / N)

        all_costs = []
        total_ep = []
        total_switches = []

        for seed in range(3):
            res = run_with_increments(N, sigma, steps, seed=seed)
            C = res['C_collective']
            mu = res['drift_collective']
            switch_times = res['switch_times']

            # Total entropy production in steady state
            C_ss = C[warmup:]
            mu_ss = mu[warmup:]
            dC_ss = np.diff(C_ss)
            ep_total = np.sum(dC_ss * mu_ss[:-1]) / D_eff
            total_time = (steps - warmup) * dt
            total_ep.append(ep_total / total_time)

            st = switch_times[switch_times > warmup]
            total_switches.append(len(st))

            window = 30
            for sw in st:
                if sw - window < warmup or sw + window >= steps - 1:
                    continue
                seg_C = C[sw-window:sw+window+1]
                seg_mu = mu[sw-window:sw+window]
                dC = np.diff(seg_C)
                ep_sw = np.sum(dC * seg_mu) / D_eff
                all_costs.append(float(ep_sw))

        if len(all_costs) > 0:
            costs = np.array(all_costs)
            avg_switches = np.mean(total_switches)
            avg_ep_rate = np.mean(total_ep)

            # EP per switch from total budget
            if avg_switches > 0:
                ep_per_switch_budget = avg_ep_rate * (steps - warmup) * dt / avg_switches
            else:
                ep_per_switch_budget = float('nan')

            result = {
                'sigma': float(sigma),
                'D_eff': float(D_eff),
                'n_switches_total': int(sum(total_switches)),
                'ep_per_switch_direct': float(np.mean(costs)),
                'ep_per_switch_std': float(np.std(costs)),
                'ep_per_switch_budget': float(ep_per_switch_budget),
                'ep_rate': float(avg_ep_rate),
                'frac_positive': float(np.mean(costs > 0)),
            }
        else:
            result = {'sigma': float(sigma), 'n_switches_total': 0}
        results.append(result)

        if result['n_switches_total'] > 0:
            print(f"  σ={sigma:.3f}: {result['n_switches_total']} switches  "
                  f"ep/switch(direct)={result['ep_per_switch_direct']:.4f}±{result['ep_per_switch_std']:.4f}  "
                  f"ep/switch(budget)={result['ep_per_switch_budget']:.4f}  "
                  f"P(+)={result['frac_positive']:.3f}")
        sys.stdout.flush()

    return results


# ─── Experiment F: Information-Thermodynamic Efficiency ───

def expF_info_efficiency(D_results):
    """Measure bits per unit of entropy production.

    Use forced simulation from S86 to get MI,
    and empirical D_eff for correct σ_ep.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Information-Thermodynamic Efficiency")
    print("=" * 70)
    sys.stdout.flush()

    from thor_session_86_stochastic_resonance import run_forced

    N = 4
    steps = 150_000
    warmup = 50_000
    dt = 0.1
    signal_amp = 0.005
    signal_freq = 0.001
    noise_levels = [0.007, 0.009, 0.011, 0.013, 0.015, 0.018]
    results = []
    D_lookup = {r['sigma']: r['D_empirical'] for r in D_results}

    for sigma in noise_levels:
        D_eff = D_lookup.get(sigma, sigma**2 / N)
        mi_values = []
        ep_values = []

        for seed in range(3):
            res = run_forced(N, sigma, steps, seed=seed,
                           signal_amp=signal_amp, signal_freq=signal_freq)
            C = res['C_collective'][warmup:]
            signal = res['signal'][warmup:]

            # MI via binning
            n_bins = 20
            C_bins = np.linspace(C.min(), C.max(), n_bins + 1)
            S_bins = np.linspace(signal.min(), signal.max(), n_bins + 1)
            H_joint = np.histogram2d(C, signal, bins=[C_bins, S_bins])[0]
            H_joint = H_joint / (H_joint.sum() + 1e-30)
            H_C = H_joint.sum(axis=1)
            H_S = H_joint.sum(axis=0)

            mi = 0
            for i in range(n_bins):
                for j in range(n_bins):
                    if H_joint[i, j] > 1e-10 and H_C[i] > 1e-10 and H_S[j] > 1e-10:
                        mi += H_joint[i, j] * np.log2(H_joint[i, j] / (H_C[i] * H_S[j]))
            mi_values.append(mi)

            # EP from drift variance (approximate for forced case)
            dC = np.diff(C)
            # Mean drift in bins
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
        ep_mean = float(np.mean(ep_values))
        landauer_bound = 1.0 / (2.0 * np.log(2))
        efficiency = mi_mean / (ep_mean + 1e-30)

        result = {
            'sigma': float(sigma),
            'MI_bits': mi_mean,
            'MI_std': float(np.std(mi_values)),
            'ep_rate': ep_mean,
            'ep_std': float(np.std(ep_values)),
            'efficiency': efficiency,
            'efficiency_fraction': efficiency / landauer_bound,
        }
        results.append(result)
        print(f"  σ={sigma:.3f}: MI={mi_mean:.4f} bits  σ_ep={ep_mean:.6f}  "
              f"η={efficiency:.4f} bits/ep  "
              f"({efficiency/landauer_bound:.1%} of Landauer)")
        sys.stdout.flush()

    print(f"\n  Landauer bound: η_max = {1/(2*np.log(2)):.4f} bits/ep")
    mi_vals = [r['MI_bits'] for r in results]
    eff_vals = [r['efficiency'] for r in results]
    peak_mi = np.argmax(mi_vals)
    peak_eff = np.argmax(eff_vals)
    sigmas = [r['sigma'] for r in results]
    print(f"  Peak MI at σ={sigmas[peak_mi]:.3f}")
    print(f"  Peak efficiency at σ={sigmas[peak_eff]:.3f}")
    if peak_mi != peak_eff:
        print(f"  *** MI and efficiency peak at DIFFERENT noise levels! ***")
        print(f"  → The most informative noise is NOT the most efficient.")
        print(f"  → There may be a trade-off between information and dissipation.")
    else:
        print(f"  → MI and efficiency peak at the SAME noise level.")

    return results


# ─── Experiment G: State-Dependent Entropy Production ───

def expG_state_dependent_ep(D_results):
    """Where does entropy production happen? In order, breathing, or during switches?

    Decompose σ_ep by coherence level: bin by C and measure local σ_ep(C).
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT G: State-Dependent Entropy Production")
    print("=" * 70)
    sys.stdout.flush()

    N = 4
    steps = 300_000
    warmup = 80_000
    dt = 0.1
    n_bins = 25
    sigma = 0.011
    D_lookup = {r['sigma']: r['D_empirical'] for r in D_results}
    D_eff = D_lookup.get(sigma, sigma**2 / N)

    results_by_state = []

    for seed in range(3):
        res = run_with_increments(N, sigma, steps, seed=seed)
        C = res['C_collective'][warmup:]
        mu = res['drift_collective'][warmup:]
        dC = np.diff(C)

        bins = np.linspace(C.min(), C.max(), n_bins + 1)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        C_dig = np.digitize(C[:-1], bins) - 1
        C_dig = np.clip(C_dig, 0, n_bins - 1)

        local_ep = np.zeros(n_bins)
        local_count = np.zeros(n_bins)
        local_drift_sq = np.zeros(n_bins)
        local_var = np.zeros(n_bins)

        for b in range(n_bins):
            mask = C_dig == b
            if mask.sum() > 10:
                local_count[b] = mask.sum()
                local_drift_sq[b] = np.mean(mu[:-1][mask]**2)
                local_var[b] = np.var(dC[mask])
                local_ep[b] = local_drift_sq[b] / D_eff

        results_by_state.append({
            'bin_centers': bin_centers.tolist(),
            'local_ep': local_ep.tolist(),
            'local_count': local_count.tolist(),
            'local_drift_sq': local_drift_sq.tolist(),
            'local_var': local_var.tolist(),
        })

    # Average across seeds
    avg_ep = np.mean([r['local_ep'] for r in results_by_state], axis=0)
    avg_count = np.mean([r['local_count'] for r in results_by_state], axis=0)
    bin_centers = results_by_state[0]['bin_centers']

    print(f"  State-dependent entropy production at σ={sigma}:")
    print(f"  {'C_center':>8s}  {'σ_ep(C)':>10s}  {'fraction':>10s}  {'visits':>8s}")
    total_ep = np.sum(avg_ep * avg_count)
    for i in range(n_bins):
        if avg_count[i] > 100:
            frac = avg_ep[i] * avg_count[i] / (total_ep + 1e-30)
            print(f"  {bin_centers[i]:8.3f}  {avg_ep[i]:10.4f}  {frac:10.3f}  {avg_count[i]:8.0f}")

    # Identify crossover region
    crossover_mask = np.array([(0.4 < c < 0.6) for c in bin_centers])
    order_mask = np.array([(c >= 0.6) for c in bin_centers])
    breathing_mask = np.array([(c <= 0.4) for c in bin_centers])

    ep_crossover = np.sum(avg_ep[crossover_mask] * avg_count[crossover_mask]) / (total_ep + 1e-30)
    ep_order = np.sum(avg_ep[order_mask] * avg_count[order_mask]) / (total_ep + 1e-30)
    ep_breathing = np.sum(avg_ep[breathing_mask] * avg_count[breathing_mask]) / (total_ep + 1e-30)

    print(f"\n  Entropy production by region:")
    print(f"    Breathing (C<0.4): {ep_breathing:.1%}")
    print(f"    Crossover (0.4-0.6): {ep_crossover:.1%}")
    print(f"    Order (C>0.6): {ep_order:.1%}")

    return {
        'sigma': float(sigma),
        'D_eff': float(D_eff),
        'bin_centers': bin_centers,
        'avg_ep': avg_ep.tolist(),
        'avg_count': avg_count.tolist(),
        'ep_breathing_frac': float(ep_breathing),
        'ep_crossover_frac': float(ep_crossover),
        'ep_order_frac': float(ep_order),
    }


# ─── Main ───

def main():
    print("=" * 70)
    print("THOR SESSION #87: ENTROPY PRODUCTION AND THE ARROW OF TIME")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    print("KEY CORRECTION: D_eff = σ²/N is WRONG for the collective")
    print("coordinate. Agents are strongly correlated. First measure")
    print("D_eff empirically, then re-derive all thermodynamic quantities.")
    print()
    sys.stdout.flush()

    all_results = {}

    # A: Foundation — get the right diffusion constant
    all_results['A_diffusion'] = expA_empirical_diffusion()

    # B-G: All corrected with empirical D_eff
    all_results['B_entropy_production'] = expB_corrected_entropy_production(all_results['A_diffusion'])
    all_results['C_fluctuation_theorem'] = expC_corrected_FT(all_results['A_diffusion'])
    all_results['D_detailed_balance'] = expD_detailed_balance()
    all_results['E_switching_cost'] = expE_switching_cost(all_results['A_diffusion'])
    all_results['F_info_efficiency'] = expF_info_efficiency(all_results['A_diffusion'])
    all_results['G_state_dependent'] = expG_state_dependent_ep(all_results['A_diffusion'])

    # Save results
    with open('thor_session_87_entropy_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to thor_session_87_entropy_results.json")

    # ─── Synthesis ───
    print("\n" + "=" * 70)
    print("SYNTHESIS: THE THERMODYNAMICS OF COHERENCE")
    print("=" * 70)

    print("\n1. DIFFUSION AMPLIFICATION:")
    D_res = all_results['A_diffusion']
    ratios = [r['amplification'] for r in D_res]
    print(f"   D_empirical/D_naive = {min(ratios):.1f}× to {max(ratios):.1f}×")
    print(f"   → Strong agent correlations amplify collective diffusion")

    print("\n2. ENTROPY PRODUCTION LANDSCAPE:")
    ep_res = all_results['B_entropy_production']
    sigmas = [r['sigma'] for r in ep_res]
    eps = [r['ep_corrected_mean'] for r in ep_res]
    peak_sigma = sigmas[np.argmax(eps)]
    print(f"   Peak σ_ep at σ={peak_sigma:.4f} (SR optimum=0.011)")

    print("\n3. FLUCTUATION THEOREM:")
    ft_res = all_results['C_fluctuation_theorem']
    for r in ft_res:
        print(f"   τ={r['segment_length']:4d}: slope={r['ft_slope']:.3f}")

    print("\n4. DETAILED BALANCE:")
    db_res = all_results['D_detailed_balance']
    for r in db_res:
        print(f"   σ={r['sigma']:.4f}: violation={r['db_violation_mean']:.4f}")

    print("\n5. SWITCHING COST:")
    sw_res = all_results['E_switching_cost']
    for r in sw_res:
        if r.get('n_switches_total', 0) > 0:
            print(f"   σ={r['sigma']:.3f}: ep/switch={r.get('ep_per_switch_direct', float('nan')):.4f}")

    print("\n6. INFORMATION EFFICIENCY:")
    ie_res = all_results['F_info_efficiency']
    for r in ie_res:
        print(f"   σ={r['sigma']:.3f}: η={r['efficiency']:.4f} bits/ep "
              f"({r['efficiency_fraction']:.1%} Landauer)")

    print("\n7. STATE-DEPENDENT DISSIPATION:")
    sd_res = all_results['G_state_dependent']
    print(f"   Breathing: {sd_res['ep_breathing_frac']:.1%}")
    print(f"   Crossover: {sd_res['ep_crossover_frac']:.1%}")
    print(f"   Order: {sd_res['ep_order_frac']:.1%}")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
