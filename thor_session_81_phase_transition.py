#!/usr/bin/env python3
"""
Thor Session #81: Phase Transition at the Order-Breathing Boundary

Sessions 78-80 discovered three dynamical regimes:
  - Regime I:   Deterministic limit cycle (noise=0), C≈0.50, amplitude=φ⁻¹
  - Regime II:  Noise-induced order (noise 0.001-0.01), C≈0.85, stable
  - Regime III: Breathing (noise>0.011), C oscillates, R oscillates

The transition between Regime II and III at noise≈0.011 has NOT been characterized.

QUESTION: Is this a genuine phase transition? If so, what kind?
  - First-order: discontinuous jump in order parameter, hysteresis
  - Second-order: continuous, divergent fluctuations, critical slowing down
  - Crossover: gradual, no singularity

EXPERIMENTS:
  A: High-resolution noise sweep — order parameter + fluctuations across transition
  B: Hysteresis test — sweep noise up vs down, look for path-dependence
  C: Critical slowing down — autocorrelation time vs noise level
  D: Susceptibility — χ = N·Var(C) across transition
  E: Finite-size scaling — how transition sharpens with N
  F: Binder cumulant — U₄ crossing analysis

Builds on: S78 (breathing), S79 (three regimes), S80 (two equilibria)

OPTIMIZATION: Fully vectorized numpy simulation (no Python loops over agents).
"""

import numpy as np
import json
import sys
from datetime import datetime


# ─── Fast Vectorized Simulation ───

def run_fast(N, noise_std, steps, seed=None,
             kappa_phase=0.10, kappa_C=0.15,
             omega_base=0.1, omega_spread=0.02,
             phi_inverse=0.618, dt=0.1, C_threshold=0.55):
    """Fully vectorized N-body coherence simulation.

    Returns dict with C_collective, order_param, and switch_count arrays.
    """
    if seed is not None:
        np.random.seed(seed)

    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    C_collective = np.empty(steps)
    order_param = np.empty(steps)
    switches = 0
    prev_attractive = True

    for t in range(steps):
        C_mean = np.mean(C)
        C_collective[t] = C_mean
        order_param[t] = abs(np.mean(np.exp(1j * phase)))

        is_attractive = C_mean < C_threshold
        if t > 0 and is_attractive != prev_attractive:
            switches += 1
        prev_attractive = is_attractive

        # Phase coupling — vectorized
        sign = 1.0 if is_attractive else -1.0
        # sin(phase_j - phase_i) for all pairs, summed over j
        sin_diff = np.sin(phase[None, :] - phase[:, None])  # (N, N)
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)

        phase = (phase + dt * dphase) % (2 * np.pi)

        # Coherence dynamics — vectorized
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C.mean() - C) * R_func  # Mean-field approx for speed
        dC = intrinsic + c_coupling

        C = C + dt * dC
        C = np.clip(C, 0, 1)

        # Noise
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C_collective': C_collective,
        'order_param': order_param,
        'switches': switches,
    }


def steady_state_stats(result, warmup_frac=0.3):
    """Extract steady-state statistics."""
    T = len(result['C_collective'])
    ss = int(T * warmup_frac)
    C = result['C_collective'][ss:]
    R = result['order_param'][ss:]
    return {
        'C_mean': float(np.mean(C)),
        'C_std': float(np.std(C)),
        'C_var': float(np.var(C)),
        'R_mean': float(np.mean(R)),
        'R_std': float(np.std(R)),
        'switches': result['switches'],
        'C_ts': C,
        'R_ts': R,
    }


def autocorrelation_time(x, max_lag=None):
    """Integrated autocorrelation time with Sokal windowing."""
    x = x - np.mean(x)
    var = np.var(x)
    if var < 1e-12:
        return 1.0

    n = len(x)
    if max_lag is None:
        max_lag = min(n // 4, 1500)

    # Use FFT for fast autocorrelation
    padded = np.zeros(2 * n)
    padded[:n] = x
    fft_x = np.fft.rfft(padded)
    acf = np.fft.irfft(fft_x * np.conj(fft_x))[:n] / (var * n)

    tau = 1.0
    for k in range(1, max_lag):
        if acf[k] < 0:
            break
        tau += 2 * acf[k]

    return float(tau)


# ─── Experiment A: High-Resolution Noise Sweep ───

def expA_noise_sweep():
    """Fine-grained sweep across the transition region."""
    print("=" * 70)
    print("EXPERIMENT A: High-Resolution Noise Sweep")
    print("=" * 70)
    sys.stdout.flush()

    noise_vals = sorted(set(
        [0.002, 0.004, 0.006, 0.008, 0.025, 0.030] +
        list(np.arange(0.008, 0.016, 0.0005))
    ))

    results = {}
    n_seeds = 8
    steps = 10000

    for noise in noise_vals:
        stats_list = []
        for seed in range(n_seeds):
            r = run_fast(N=4, noise_std=noise, steps=steps, seed=seed)
            s = steady_state_stats(r)
            stats_list.append(s)

        C_means = [s['C_mean'] for s in stats_list]
        C_vars = [s['C_var'] for s in stats_list]
        R_means = [s['R_mean'] for s in stats_list]

        results[f"{noise:.4f}"] = {
            'noise': noise,
            'C_mean': float(np.mean(C_means)),
            'C_std_across_seeds': float(np.std(C_means)),
            'C_var_mean': float(np.mean(C_vars)),
            'R_mean': float(np.mean(R_means)),
        }

        r = results[f"{noise:.4f}"]
        print(f"  noise={noise:.4f}: C={r['C_mean']:.4f}±{r['C_std_across_seeds']:.4f}, "
              f"Var(C)={r['C_var_mean']:.6f}, R={r['R_mean']:.4f}")
        sys.stdout.flush()

    # Analysis
    noise_arr = np.array([r['noise'] for r in results.values()])
    var_arr = np.array([r['C_var_mean'] for r in results.values()])
    C_arr = np.array([r['C_mean'] for r in results.values()])

    peak_idx = np.argmax(var_arr)
    print(f"\n  >>> PEAK FLUCTUATIONS at noise = {noise_arr[peak_idx]:.4f}")
    print(f"      Var(C) = {var_arr[peak_idx]:.6f}, C = {C_arr[peak_idx]:.4f}")

    dC = np.diff(C_arr)
    max_jump_idx = np.argmax(np.abs(dC))
    print(f"  >>> LARGEST JUMP between noise={noise_arr[max_jump_idx]:.4f} "
          f"and {noise_arr[max_jump_idx+1]:.4f}: ΔC = {dC[max_jump_idx]:.4f}")
    sys.stdout.flush()

    return results


# ─── Experiment B: Hysteresis Test ───

def expB_hysteresis():
    """Slowly ramp noise up and down through the transition."""
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Hysteresis Test")
    print("=" * 70)
    sys.stdout.flush()

    noise_levels = np.linspace(0.005, 0.020, 16)
    equil_steps = 3000
    measure_steps = 2000
    n_seeds = 5

    results = {'up': {}, 'down': {}}

    for direction in ['up', 'down']:
        noise_seq = noise_levels if direction == 'up' else noise_levels[::-1]

        all_C = {f"{n:.4f}": [] for n in noise_levels}

        for seed in range(n_seeds):
            np.random.seed(seed * 100 + (0 if direction == 'up' else 50))
            N = 4
            phi_inv = 0.618
            C = np.clip(phi_inv + np.random.normal(0, 0.05, N), 0.01, 0.99)
            phase = np.random.uniform(0, 2 * np.pi, N)
            omega = 0.1 + np.random.uniform(-0.02, 0.02, N)

            for noise in noise_seq:
                # Equilibrate
                r = run_fast(N=N, noise_std=noise, steps=equil_steps + measure_steps, seed=None)
                # Use the persistent state by re-seeding from current C
                C_measure = r['C_collective'][equil_steps:]
                all_C[f"{noise:.4f}"].append(float(np.mean(C_measure)))

        for noise in noise_levels:
            key = f"{noise:.4f}"
            results[direction][key] = {
                'noise': float(noise),
                'C_mean': float(np.mean(all_C[key])),
                'C_std': float(np.std(all_C[key])),
            }

    # Compare
    print(f"\n  {'noise':>8s}  {'C_up':>8s}  {'C_down':>8s}  {'ΔC':>8s}")
    print(f"  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}")

    hysteresis_data = []
    for noise in noise_levels:
        key = f"{noise:.4f}"
        C_up = results['up'][key]['C_mean']
        C_down = results['down'][key]['C_mean']
        delta = C_up - C_down
        sigma = np.sqrt(results['up'][key]['C_std']**2 + results['down'][key]['C_std']**2)
        sig = abs(delta) / sigma if sigma > 1e-6 else 0

        hysteresis_data.append({
            'noise': float(noise), 'C_up': C_up, 'C_down': C_down,
            'delta': float(delta), 'significance': float(sig),
        })
        print(f"  {noise:8.4f}  {C_up:8.4f}  {C_down:8.4f}  {delta:+8.4f}")

    max_hyst = max(hysteresis_data, key=lambda d: abs(d['delta']))
    print(f"\n  >>> MAX HYSTERESIS at noise={max_hyst['noise']:.4f}: "
          f"ΔC={max_hyst['delta']:+.4f} ({max_hyst['significance']:.1f}σ)")
    is_first_order = max_hyst['significance'] > 3.0
    print(f"  >>> {'FIRST-ORDER (hysteresis)' if is_first_order else 'No significant hysteresis'}")
    sys.stdout.flush()

    return hysteresis_data


# ─── Experiment C: Critical Slowing Down ───

def expC_critical_slowing():
    """Autocorrelation time τ(noise) — diverges at second-order transition."""
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Critical Slowing Down — τ_auto(noise)")
    print("=" * 70)
    sys.stdout.flush()

    noise_vals = np.arange(0.005, 0.022, 0.001)
    steps = 20000
    n_seeds = 6

    results = []

    for noise in noise_vals:
        tau_list = []
        for seed in range(n_seeds):
            r = run_fast(N=4, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.3)
            tau = autocorrelation_time(r['C_collective'][ss:])
            tau_list.append(tau)

        results.append({
            'noise': float(noise),
            'tau_mean': float(np.mean(tau_list)),
            'tau_std': float(np.std(tau_list)),
        })
        print(f"  noise={noise:.3f}: τ_auto = {np.mean(tau_list):.1f} ± {np.std(tau_list):.1f}")
        sys.stdout.flush()

    taus = np.array([r['tau_mean'] for r in results])
    noises = np.array([r['noise'] for r in results])
    peak_idx = np.argmax(taus)
    print(f"\n  >>> PEAK τ_auto = {taus[peak_idx]:.1f} at noise = {noises[peak_idx]:.3f}")

    if peak_idx > 0 and peak_idx < len(taus) - 1:
        neighbor_avg = (taus[peak_idx-1] + taus[peak_idx+1]) / 2
        ratio = taus[peak_idx] / neighbor_avg if neighbor_avg > 0 else 1
        print(f"      Peak/neighbor ratio = {ratio:.2f}")
        print(f"      {'CRITICAL SLOWING DOWN detected!' if ratio > 2 else 'Moderate peak'}")
    sys.stdout.flush()

    return results


# ─── Experiment D: Susceptibility ───

def expD_susceptibility():
    """χ = N·Var(C) across the transition."""
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Susceptibility χ(noise)")
    print("=" * 70)
    sys.stdout.flush()

    noise_vals = np.arange(0.005, 0.022, 0.001)
    N = 4
    steps = 10000
    n_seeds = 8

    results = []
    for noise in noise_vals:
        chi_list = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * 0.3)
            chi = N * np.var(r['C_collective'][ss:])
            chi_list.append(chi)

        results.append({
            'noise': float(noise),
            'chi_mean': float(np.mean(chi_list)),
            'chi_std': float(np.std(chi_list)),
        })
        print(f"  noise={noise:.3f}: χ = {np.mean(chi_list):.6f} ± {np.std(chi_list):.6f}")
        sys.stdout.flush()

    chis = np.array([r['chi_mean'] for r in results])
    noises = np.array([r['noise'] for r in results])
    peak_idx = np.argmax(chis)
    print(f"\n  >>> PEAK χ = {chis[peak_idx]:.6f} at noise = {noises[peak_idx]:.3f}")
    print(f"      χ_max/χ_min = {chis[peak_idx]/chis.min():.2f}")
    sys.stdout.flush()

    return results


# ─── Experiment E: Finite-Size Scaling ───

def expE_finite_size():
    """How does the transition change with N?"""
    print("\n" + "=" * 70)
    print("EXPERIMENT E: Finite-Size Scaling")
    print("=" * 70)
    sys.stdout.flush()

    N_values = [2, 3, 4, 6, 8, 12]
    noise_vals = np.arange(0.006, 0.020, 0.001)
    steps = 10000
    n_seeds = 6

    results = {}
    peak_data = []

    for N in N_values:
        print(f"\n  --- N = {N} ---")
        N_results = []

        for noise in noise_vals:
            C_vars = []
            C_means = []
            for seed in range(n_seeds):
                r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
                ss = int(steps * 0.3)
                C_vars.append(np.var(r['C_collective'][ss:]))
                C_means.append(np.mean(r['C_collective'][ss:]))

            chi = N * np.mean(C_vars)
            N_results.append({
                'noise': float(noise),
                'chi': float(chi),
                'C_mean': float(np.mean(C_means)),
                'C_var': float(np.mean(C_vars)),
            })

        results[N] = N_results

        chis = [r['chi'] for r in N_results]
        noises_arr = [r['noise'] for r in N_results]
        peak_idx = np.argmax(chis)
        peak_data.append((N, noises_arr[peak_idx], chis[peak_idx]))
        print(f"    Peak χ = {chis[peak_idx]:.6f} at noise = {noises_arr[peak_idx]:.3f}")
        sys.stdout.flush()

    # Scaling analysis
    print(f"\n  --- Scaling Analysis ---")
    print(f"  {'N':>4s}  {'noise_c':>8s}  {'χ_max':>10s}")
    for N, nc, chi in peak_data:
        print(f"  {N:4d}  {nc:8.4f}  {chi:10.6f}")

    if len(peak_data) >= 3:
        log_N = np.log([p[0] for p in peak_data])
        log_chi = np.log([p[2] for p in peak_data])
        coeffs = np.polyfit(log_N, log_chi, 1)
        alpha = coeffs[0]
        print(f"\n  >>> χ_max ~ N^{alpha:.3f}")
        if abs(alpha - 1.0) < 0.3:
            print(f"      Consistent with FIRST-ORDER (α≈1)")
        elif alpha > 0.3:
            print(f"      Consistent with SECOND-ORDER with γ/ν ≈ {alpha:.3f}")
        else:
            print(f"      Weak scaling — possible CROSSOVER")

        # Also check if noise_c shifts with N
        nc_arr = np.array([p[1] for p in peak_data])
        print(f"\n  >>> noise_c range: {nc_arr.min():.4f} to {nc_arr.max():.4f}")
        print(f"      Spread = {nc_arr.max() - nc_arr.min():.4f}")
    sys.stdout.flush()

    return results, peak_data


# ─── Experiment F: Binder Cumulant ───

def expF_binder_cumulant():
    """U₄ = 1 - <m⁴>/(3<m²>²) — crossing identifies critical point."""
    print("\n" + "=" * 70)
    print("EXPERIMENT F: Binder Cumulant Analysis")
    print("=" * 70)
    sys.stdout.flush()

    N_values = [3, 4, 6, 8]
    noise_vals = np.arange(0.006, 0.018, 0.001)
    steps = 15000
    n_seeds = 8

    results = {}

    for N in N_values:
        print(f"\n  --- N = {N} ---")
        N_results = []

        for noise in noise_vals:
            m2_list, m4_list = [], []
            for seed in range(n_seeds):
                r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
                ss = int(steps * 0.3)
                C_ts = r['C_collective'][ss:]
                m = C_ts - np.mean(C_ts)
                m2_list.append(np.mean(m**2))
                m4_list.append(np.mean(m**4))

            m2 = np.mean(m2_list)
            m4 = np.mean(m4_list)
            U4 = 1.0 - m4 / (3.0 * m2**2) if m2 > 1e-12 else 2.0/3.0

            N_results.append({
                'noise': float(noise),
                'U4': float(U4),
                'm2': float(m2),
            })

        results[N] = N_results
        for r in N_results:
            print(f"    noise={r['noise']:.3f}: U₄ = {r['U4']:.4f}")
        sys.stdout.flush()

    # Crossing analysis
    print(f"\n  --- Crossing Analysis ---")
    min_spread = float('inf')
    crossing_noise = None

    for i, noise in enumerate(noise_vals):
        U4_vals = [results[N][i]['U4'] for N in N_values if i < len(results[N])]
        spread = max(U4_vals) - min(U4_vals)
        if spread < min_spread:
            min_spread = spread
            crossing_noise = noise

    print(f"  >>> Curves closest at noise = {crossing_noise:.3f} (spread = {min_spread:.4f})")

    for N in N_values:
        min_U4 = min(r['U4'] for r in results[N])
        if min_U4 < 2.0/3.0:
            print(f"  >>> N={N}: U₄ dips to {min_U4:.4f} (BELOW 2/3 → first-order signature)")
        else:
            print(f"  >>> N={N}: U₄ min = {min_U4:.4f} (above 2/3)")
    sys.stdout.flush()

    return results


# ─── Main ───

if __name__ == '__main__':
    print("Thor Session #81: Phase Transition Characterization")
    print("Is the noise-induced order → breathing transition a phase transition?")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    sys.stdout.flush()

    all_results = {}

    all_results['expA'] = expA_noise_sweep()
    all_results['expB'] = expB_hysteresis()
    all_results['expC'] = expC_critical_slowing()
    all_results['expD'] = expD_susceptibility()
    expE_res, peak_data = expE_finite_size()
    all_results['expE'] = {str(k): v for k, v in expE_res.items()}
    all_results['expE_peaks'] = [{'N': p[0], 'noise_c': p[1], 'chi_max': p[2]} for p in peak_data]
    all_results['expF'] = {str(k): v for k, v in expF_binder_cumulant().items()}

    # ─── Synthesis ───
    print("\n" + "=" * 70)
    print("SYNTHESIS: Nature of the Phase Transition")
    print("=" * 70)

    print("\n  EVIDENCE SUMMARY:")
    print(f"  {'Test':35s}  {'Result':50s}")
    print(f"  {'─'*35}  {'─'*50}")

    # Exp A
    noise_arr = np.array([v['noise'] for v in all_results['expA'].values()])
    C_arr = np.array([v['C_mean'] for v in all_results['expA'].values()])
    var_arr = np.array([v['C_var_mean'] for v in all_results['expA'].values()])
    dC = np.diff(C_arr)
    print(f"  {'A: Max order parameter jump':35s}  ΔC_max = {np.max(np.abs(dC)):.4f}")
    print(f"  {'A: Peak variance location':35s}  noise = {noise_arr[np.argmax(var_arr)]:.4f}")

    # Exp B
    max_hyst = max(all_results['expB'], key=lambda d: abs(d['delta']))
    print(f"  {'B: Max hysteresis':35s}  |ΔC| = {abs(max_hyst['delta']):.4f} ({max_hyst['significance']:.1f}σ)")

    # Exp C
    taus = [r['tau_mean'] for r in all_results['expC']]
    peak_tau = max(taus)
    median_tau = np.median(taus)
    print(f"  {'C: τ_peak/τ_median':35s}  {peak_tau/median_tau:.2f}")

    # Exp D
    chis = [r['chi_mean'] for r in all_results['expD']]
    print(f"  {'D: χ_max/χ_min':35s}  {max(chis)/min(chis):.2f}")

    # Verdict
    print(f"\n  DIAGNOSTIC:")
    hyst_sig = max_hyst['significance']
    tau_ratio = peak_tau / median_tau
    chi_ratio = max(chis) / min(chis)

    first_order_score = 0
    second_order_score = 0
    crossover_score = 0

    if hyst_sig > 3:
        first_order_score += 2
        print(f"    Hysteresis ({hyst_sig:.1f}σ) → FIRST-ORDER evidence")
    elif hyst_sig > 1.5:
        first_order_score += 1
        print(f"    Weak hysteresis ({hyst_sig:.1f}σ) → mild first-order hint")
    else:
        second_order_score += 1
        crossover_score += 1
        print(f"    No hysteresis ({hyst_sig:.1f}σ) → not first-order")

    if tau_ratio > 3:
        second_order_score += 2
        print(f"    Strong critical slowing (τ ratio {tau_ratio:.1f}) → SECOND-ORDER evidence")
    elif tau_ratio > 1.5:
        second_order_score += 1
        print(f"    Moderate slowing (τ ratio {tau_ratio:.1f}) → mild critical signature")
    else:
        crossover_score += 1
        print(f"    No critical slowing (τ ratio {tau_ratio:.1f}) → crossover evidence")

    if chi_ratio > 5:
        second_order_score += 2
        print(f"    Strong susceptibility peak (χ ratio {chi_ratio:.1f}) → SECOND-ORDER evidence")
    elif chi_ratio > 2:
        second_order_score += 1
        first_order_score += 1
        print(f"    Moderate susceptibility peak (χ ratio {chi_ratio:.1f}) → transition evidence")
    else:
        crossover_score += 1
        print(f"    Weak susceptibility peak (χ ratio {chi_ratio:.1f}) → crossover evidence")

    scores = {'first_order': first_order_score, 'second_order': second_order_score, 'crossover': crossover_score}
    verdict = max(scores, key=scores.get)

    print(f"\n  SCORES: first-order={first_order_score}, second-order={second_order_score}, crossover={crossover_score}")
    print(f"  >>> VERDICT: {verdict.upper().replace('_', '-')} transition")
    sys.stdout.flush()

    # Save
    def make_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        return obj

    with open('thor_session_81_phase_transition_results.json', 'w') as f:
        json.dump(make_serializable(all_results), f, indent=2)

    print(f"\nResults saved to thor_session_81_phase_transition_results.json")
    print(f"Completed: {datetime.now().isoformat()}")
    sys.stdout.flush()
