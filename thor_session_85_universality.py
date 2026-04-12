#!/usr/bin/env python3
"""
Thor Session #85: Universality Class Identification

Session 84 found Var(C) ~ N^(-0.12) — strikingly close to 1/8 = 0.125.

WHY THIS MATTERS:
  For 2D Ising at criticality: Var(m) ~ N^(-1/8) = N^(-0.125)
  For mean-field (Curie-Weiss): Var(m) ~ N^(-1/2)
  Measured: Var(C) ~ N^(-0.12) ≈ N^(-1/8)

CRITICAL TESTS:
  A. Binder cumulant U₄(σ, N) — crossing identifies σ_c and its universal value
  B. Multiple critical exponents at σ_c
  C. Data collapse with 2D Ising vs mean-field exponents
  D. Distribution shape (kurtosis) at criticality
  E. Correlation time scaling (critical slowing down)

Builds on: S84 (finite-size scaling), S83 (Fokker-Planck), S82 (Kramers)
"""

import numpy as np
import json
import sys
from datetime import datetime


def run_batch(N, noise_std, steps, n_seeds, dt=0.1,
              kappa_phase=0.10, kappa_C=0.15,
              omega_base=0.1, omega_spread=0.02,
              phi_inverse=0.618, C_threshold=0.55, warmup_frac=0.2):
    """Run multiple seeds and return concatenated steady-state C values.

    Batches seeds sequentially but returns aggregated statistics efficiently.
    """
    ss = int(steps * warmup_frac)
    n_ss = steps - ss
    C_all = np.empty(n_seeds * n_ss)
    R_all = np.empty(n_seeds * n_ss)

    for s in range(n_seeds):
        np.random.seed(s * 1000 + N * 100 + int(noise_std * 100000))

        C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
        phase = np.random.uniform(0, 2 * np.pi, N)
        omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

        # Run warmup without storing
        for t in range(ss):
            C_mean = np.mean(C)
            Z = np.mean(np.exp(1j * phase))
            R = abs(Z)

            is_attractive = C_mean < C_threshold
            sign = 1.0 if is_attractive else -1.0
            Z_conj = np.conj(Z)
            coupling = -np.imag(Z_conj * np.exp(1j * phase))
            dphase = omega + sign * kappa_phase * N / (N - 1) * coupling
            phase = (phase + dt * dphase) % (2 * np.pi)

            R_func = 1 - C**2
            intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
            c_coupling = kappa_C * (C_mean - C) * R_func
            C = np.clip(C + dt * (intrinsic + c_coupling), 0, 1)

            if noise_std > 0:
                C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
                phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

        # Run steady state and store
        idx_base = s * n_ss
        for t in range(n_ss):
            C_mean = np.mean(C)
            C_all[idx_base + t] = C_mean

            Z = np.mean(np.exp(1j * phase))
            R_all[idx_base + t] = abs(Z)

            is_attractive = C_mean < C_threshold
            sign = 1.0 if is_attractive else -1.0
            Z_conj = np.conj(Z)
            coupling = -np.imag(Z_conj * np.exp(1j * phase))
            dphase = omega + sign * kappa_phase * N / (N - 1) * coupling
            phase = (phase + dt * dphase) % (2 * np.pi)

            R_func = 1 - C**2
            intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
            c_coupling = kappa_C * (C_mean - C) * R_func
            C = np.clip(C + dt * (intrinsic + c_coupling), 0, 1)

            if noise_std > 0:
                C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
                phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return C_all, R_all


def compute_stats(C_arr, N):
    """Compute all relevant statistics from a C timeseries array."""
    C_mean = np.mean(C_arr)
    delta = C_arr - C_mean
    m2 = np.mean(delta**2)
    m3 = np.mean(delta**3)
    m4 = np.mean(delta**4)
    m6 = np.mean(delta**6)

    skew = m3 / m2**1.5 if m2 > 0 else 0
    kurt = m4 / m2**2 if m2 > 0 else 3
    U4 = 1.0 - m4 / (3.0 * m2**2) if m2 > 0 else 0

    m_abs = np.mean(np.abs(C_arr - 0.5))
    chi = N * m2

    return {
        'C_mean': float(C_mean),
        'C_var': float(m2),
        'skewness': float(skew),
        'kurtosis': float(kurt),
        'U4': float(U4),
        'm_abs': float(m_abs),
        'chi': float(chi),
        'm4': float(m4),
        'm6': float(m6),
    }


# ─── Experiment A: Binder Cumulant ───

def expA_binder_cumulant():
    """Binder cumulant U₄(σ, N) to identify σ_c."""
    print("=" * 70)
    print("EXPERIMENT A: Binder Cumulant U₄(σ, N)")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [4, 8, 16, 32]
    noise_vals = [round(x, 4) for x in np.arange(0.007, 0.021, 0.002)]
    n_seeds = 6
    steps = 30000

    results = {}

    for N in N_vals:
        results[N] = {}
        print(f"\n  N = {N}:")
        sys.stdout.flush()

        for noise in noise_vals:
            C_arr, _ = run_batch(N, noise, steps, n_seeds)
            stats = compute_stats(C_arr, N)
            results[N][str(noise)] = stats
            print(f"    σ={noise:.3f}: U₄={stats['U4']:.4f}, ⟨C⟩={stats['C_mean']:.4f}, "
                  f"Var={stats['C_var']:.6f}")
            sys.stdout.flush()

    # Find crossings
    crossings = []
    for i in range(len(N_vals) - 1):
        N1, N2 = N_vals[i], N_vals[i + 1]
        for j in range(len(noise_vals) - 1):
            s1, s2 = str(noise_vals[j]), str(noise_vals[j + 1])
            if s1 in results[N1] and s1 in results[N2] and s2 in results[N1] and s2 in results[N2]:
                diff_lo = results[N1][s1]['U4'] - results[N2][s1]['U4']
                diff_hi = results[N1][s2]['U4'] - results[N2][s2]['U4']
                if diff_lo * diff_hi < 0:
                    frac = diff_lo / (diff_lo - diff_hi)
                    sigma_cross = noise_vals[j] + frac * (noise_vals[j + 1] - noise_vals[j])
                    U_cross = results[N1][s1]['U4'] + frac * (results[N1][s2]['U4'] - results[N1][s1]['U4'])
                    crossings.append({
                        'N_pair': [N1, N2],
                        'sigma_c': float(sigma_cross),
                        'U4_c': float(U_cross),
                    })

    print(f"\n  Binder cumulant crossings:")
    for cr in crossings:
        print(f"    N={cr['N_pair']}: σ_c={cr['sigma_c']:.4f}, U₄={cr['U4_c']:.4f}")

    results['crossings'] = crossings
    return results


# ─── Experiment B: Critical Exponents ───

def expB_critical_exponents(sigma_c):
    """Multiple exponent measurements at σ_c."""
    print("=" * 70)
    print(f"EXPERIMENT B: Critical Exponents at σ_c = {sigma_c:.4f}")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [3, 4, 6, 8, 12, 16, 24, 32, 48, 64]
    n_seeds = 8
    steps = 40000

    results = {}

    for N in N_vals:
        C_arr, R_arr = run_batch(N, sigma_c, steps, n_seeds)
        stats = compute_stats(C_arr, N)
        stats['R_mean'] = float(np.mean(R_arr))
        results[N] = stats
        print(f"  N={N:3d}: ⟨C⟩={stats['C_mean']:.4f}, Var={stats['C_var']:.6f}, "
              f"χ={stats['chi']:.4f}, |m|={stats['m_abs']:.4f}, U₄={stats['U4']:.4f}")
        sys.stdout.flush()

    # Power-law fits
    N_arr = np.array(N_vals, dtype=float)
    fits = {}

    quantities = {
        'var': ('C_var', 'Var(C)'),
        'chi': ('chi', 'χ = N·Var'),
        'm_abs': ('m_abs', '⟨|C-0.5|⟩'),
    }

    print(f"\n  Power-law fits: quantity ~ N^α")
    for key, (field, label) in quantities.items():
        vals = np.array([results[N][field] for N in N_vals])
        valid = vals > 0
        if valid.sum() >= 4:
            coeffs = np.polyfit(np.log(N_arr[valid]), np.log(vals[valid]), 1)
            alpha = coeffs[0]
            y = np.log(vals[valid])
            y_pred = np.polyval(coeffs, np.log(N_arr[valid]))
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            fits[key] = {'alpha': float(alpha), 'r_squared': float(r2)}
            print(f"    {label:15s} ~ N^({alpha:+.4f})  R²={r2:.4f}")

    print(f"\n  COMPARISON:")
    print(f"  {'Quantity':20s} {'Measured':>10s} {'2D Ising':>10s} {'Mean-field':>12s}")
    print(f"  {'-'*55}")
    predictions = {
        'var':   ('Var(C)',     -0.125,  -0.500),
        'chi':   ('χ = N·Var',   0.875,   0.500),
        'm_abs': ('⟨|C-0.5|⟩', -0.0625, -0.250),
    }
    for key, (label, ising_2d, mf) in predictions.items():
        if key in fits:
            measured = fits[key]['alpha']
            print(f"  {label:20s} {measured:+10.4f} {ising_2d:+10.4f} {mf:+12.4f}")

    results['fits'] = fits
    return results


# ─── Experiment C: Data Collapse ───

def expC_data_collapse(sigma_c):
    """Finite-size scaling collapse with different universality hypotheses."""
    print("=" * 70)
    print(f"EXPERIMENT C: Data Collapse at σ_c = {sigma_c:.4f}")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [4, 8, 16, 32]
    noise_offsets = [-0.004, -0.003, -0.002, -0.001, 0.0, 0.001, 0.002, 0.003, 0.004]
    n_seeds = 6
    steps = 30000

    raw_data = {}

    for N in N_vals:
        raw_data[N] = {}
        print(f"\n  N = {N}:", end=" ")
        sys.stdout.flush()

        for offset in noise_offsets:
            noise = round(sigma_c + offset, 4)
            if noise < 0.004:
                continue
            C_arr, _ = run_batch(N, noise, steps, n_seeds)
            stats = compute_stats(C_arr, N)
            raw_data[N][str(noise)] = stats
            print(f"σ={noise:.3f}", end=" ")
            sys.stdout.flush()
        print()

    # Test collapse quality for different hypotheses
    hypotheses = {
        '2D_Ising':   {'nu_d': 2.0,   'gamma_nu_d': 0.875},
        'mean_field':  {'nu_d': 2.0,   'gamma_nu_d': 0.500},
        '3D_Ising':    {'nu_d': 1.896, 'gamma_nu_d': 0.655},
    }

    def collapse_quality(nu_d, gamma_nu_d):
        all_points = []
        for N in N_vals:
            for s_noise, stats in raw_data[N].items():
                noise = float(s_noise)
                x = (noise - sigma_c) * N**(1.0 / nu_d)
                y = stats['chi'] * N**(-gamma_nu_d)
                all_points.append((x, y, N))

        if not all_points:
            return float('inf')

        all_points.sort(key=lambda p: p[0])
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]

        x_min, x_max = min(xs), max(xs)
        n_bins = 10
        bin_edges = np.linspace(x_min, x_max, n_bins + 1)
        cvs = []
        for b in range(n_bins):
            in_bin = [ys[i] for i in range(len(xs))
                      if bin_edges[b] <= xs[i] < bin_edges[b + 1]]
            if len(in_bin) >= 2:
                mean_y = np.mean(in_bin)
                if mean_y > 0:
                    cvs.append(np.std(in_bin) / mean_y)
        return float(np.mean(cvs)) if cvs else float('inf')

    collapse_results = {}
    for name, params in hypotheses.items():
        q = collapse_quality(params['nu_d'], params['gamma_nu_d'])
        collapse_results[name] = {**params, 'quality': q}
        print(f"  {name:15s}: quality = {q:.4f} (lower = better)")

    # Grid search for best exponents
    print(f"\n  Optimizing exponents...")
    best_q = float('inf')
    best_nu_d = 2.0
    best_gamma = 0.875

    for nu_d_try in np.arange(0.5, 5.1, 0.5):
        for gamma_try in np.arange(0.2, 1.6, 0.05):
            q = collapse_quality(nu_d_try, gamma_try)
            if q < best_q:
                best_q = q
                best_nu_d = nu_d_try
                best_gamma = gamma_try

    # Refine
    for nu_d_try in np.arange(max(0.5, best_nu_d - 0.5), best_nu_d + 0.6, 0.1):
        for gamma_try in np.arange(max(0.1, best_gamma - 0.1), best_gamma + 0.15, 0.01):
            q = collapse_quality(nu_d_try, gamma_try)
            if q < best_q:
                best_q = q
                best_nu_d = nu_d_try
                best_gamma = gamma_try

    collapse_results['optimized'] = {
        'nu_d': float(best_nu_d), 'gamma_nu_d': float(best_gamma), 'quality': float(best_q)
    }
    print(f"  Optimized: νd={best_nu_d:.2f}, γ/(νd)={best_gamma:.3f}, quality={best_q:.4f}")

    # Interpret
    print(f"\n  INTERPRETATION:")
    print(f"  2D Ising:   νd=2.0, γ/(νd)=0.875")
    print(f"  Mean-field: νd=2.0, γ/(νd)=0.500")
    print(f"  Best fit:   νd={best_nu_d:.1f}, γ/(νd)={best_gamma:.3f}")

    return {'raw': {str(N): {s: v for s, v in d.items()} for N, d in raw_data.items()},
            'collapse': collapse_results}


# ─── Experiment D: Distribution Shape ───

def expD_distribution_shape(sigma_c):
    """Kurtosis and distribution shape at σ_c."""
    print("=" * 70)
    print(f"EXPERIMENT D: Distribution Shape at σ_c = {sigma_c:.4f}")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [4, 8, 16, 32, 64]
    n_seeds = 10
    steps = 40000

    results = {}

    for N in N_vals:
        C_arr, _ = run_batch(N, sigma_c, steps, n_seeds)
        stats = compute_stats(C_arr, N)

        # Peak count
        hist, bin_edges = np.histogram(C_arr, bins=60, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        peaks = []
        for j in range(1, len(hist) - 1):
            if hist[j] > hist[j-1] and hist[j] > hist[j+1] and hist[j] > 0.3:
                peaks.append(float(bin_centers[j]))

        stats['n_peaks'] = len(peaks)
        stats['peak_locations'] = peaks
        results[N] = stats

        print(f"  N={N:3d}: κ={stats['kurtosis']:.3f}, skew={stats['skewness']:.3f}, "
              f"U₄={stats['U4']:.4f}, peaks={len(peaks)}")
        sys.stdout.flush()

    print(f"\n  KURTOSIS COMPARISON:")
    print(f"  Gaussian:       κ = 3.000")
    print(f"  2D Ising T_c:   κ ≈ 1.75")
    print(f"  Mean-field T_c: κ ≈ 2.19")
    print(f"  Bimodal:        κ < 1.8 (typically)")

    return results


# ─── Experiment E: Correlation Time ───

def expE_correlation_time(sigma_c):
    """Autocorrelation time at σ_c — test for critical slowing down."""
    print("=" * 70)
    print(f"EXPERIMENT E: Correlation Time at σ_c = {sigma_c:.4f}")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [4, 8, 16, 32]
    n_seeds = 4
    steps = 50000
    warmup_frac = 0.15
    dt = 0.1

    results = {}

    for N in N_vals:
        tau_estimates = []

        for seed in range(n_seeds):
            np.random.seed(seed * 1000 + N * 100 + int(sigma_c * 100000))

            C_state = np.clip(0.618 + np.random.normal(0, 0.05, N), 0.01, 0.99)
            phase = np.random.uniform(0, 2 * np.pi, N)
            omega = 0.1 + np.random.uniform(-0.02, 0.02, N)

            ss = int(steps * warmup_frac)
            C_ts = np.empty(steps - ss)

            for t in range(steps):
                C_mean = np.mean(C_state)
                if t >= ss:
                    C_ts[t - ss] = C_mean

                Z = np.mean(np.exp(1j * phase))
                is_attractive = C_mean < 0.55
                sign = 1.0 if is_attractive else -1.0
                Z_conj = np.conj(Z)
                coupling = -np.imag(Z_conj * np.exp(1j * phase))
                dphase = omega + sign * 0.10 * N / (N - 1) * coupling
                phase = (phase + dt * dphase) % (2 * np.pi)

                R_func = 1 - C_state**2
                intrinsic = -R_func * (C_state - 0.618) * np.cos(phase)
                c_coupling = 0.15 * (C_mean - C_state) * R_func
                C_state = np.clip(C_state + dt * (intrinsic + c_coupling), 0, 1)

                if sigma_c > 0:
                    C_state = np.clip(C_state + np.random.normal(0, sigma_c, N), 0, 1)
                    phase = (phase + np.random.normal(0, sigma_c, N)) % (2 * np.pi)

            # Autocorrelation via FFT
            delta = C_ts - np.mean(C_ts)
            var = np.mean(delta**2)
            if var < 1e-10:
                continue

            n = len(delta)
            fft = np.fft.fft(delta, n=2*n)
            acf = np.real(np.fft.ifft(fft * np.conj(fft)))[:n] / (var * n)

            tau_int = 0.5
            for lag in range(1, min(n // 4, 3000)):
                if acf[lag] < 0.01:
                    break
                tau_int += acf[lag]

            tau_estimates.append(float(tau_int * dt))

        if tau_estimates:
            results[N] = {
                'tau_mean': float(np.mean(tau_estimates)),
                'tau_std': float(np.std(tau_estimates)),
            }
            print(f"  N={N:3d}: τ = {np.mean(tau_estimates):.2f} ± {np.std(tau_estimates):.2f}")
        else:
            results[N] = {'tau_mean': 0, 'tau_std': 0}
            print(f"  N={N:3d}: insufficient data")
        sys.stdout.flush()

    # Power-law fit
    N_arr = np.array([n for n in N_vals if results[n]['tau_mean'] > 0], dtype=float)
    tau_arr = np.array([results[n]['tau_mean'] for n in N_vals if results[n]['tau_mean'] > 0])

    if len(N_arr) >= 3:
        coeffs = np.polyfit(np.log(N_arr), np.log(tau_arr), 1)
        z_eff = coeffs[0]
        y = np.log(tau_arr)
        y_pred = np.polyval(coeffs, np.log(N_arr))
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        results['scaling'] = {'z_eff': float(z_eff), 'r_squared': float(r2)}
        print(f"\n  τ ~ N^({z_eff:.3f}), R² = {r2:.4f}")
        print(f"  2D Ising (Glauber): z/(νd) ≈ {2.17/2:.3f}")
        print(f"  Mean-field:         z/(νd) = {2/2:.3f}")

    return results


# ─── Main ───

def main():
    start_time = datetime.now()
    print(f"Thor Session #85: Universality Class Identification")
    print(f"Started: {start_time}")
    print(f"Question: Is β = 0.12 ≈ 1/8 the 2D Ising exponent?")
    print()

    all_results = {}

    # A: Binder cumulant → find σ_c
    all_results['A_binder'] = expA_binder_cumulant()

    crossings = all_results['A_binder'].get('crossings', [])
    if crossings:
        sigma_c = float(np.median([c['sigma_c'] for c in crossings]))
        U4_c = float(np.median([c['U4_c'] for c in crossings]))
        print(f"\n  >>> CRITICAL NOISE: σ_c = {sigma_c:.4f}")
        print(f"  >>> CRITICAL U₄: {U4_c:.4f}")
        print(f"      2D Ising: U₄ ≈ 0.611, Mean-field: U₄ = 0.667")
    else:
        sigma_c = 0.012
        U4_c = None
        print(f"\n  >>> No crossing. Using σ_c = 0.012 (S84 default)")

    all_results['sigma_c'] = sigma_c
    all_results['U4_c'] = U4_c

    # B: Critical exponents
    all_results['B_exponents'] = expB_critical_exponents(sigma_c)

    # C: Data collapse
    all_results['C_collapse'] = expC_data_collapse(sigma_c)

    # D: Distribution shape
    all_results['D_distribution'] = expD_distribution_shape(sigma_c)

    # E: Correlation time
    all_results['E_correlation'] = expE_correlation_time(sigma_c)

    # ─── SYNTHESIS ───
    print("\n" + "=" * 70)
    print("SYNTHESIS: Universality Class Identification")
    print("=" * 70)

    evidence = {'2D_Ising': 0, 'mean_field': 0, 'neither': 0}

    # Evidence 1: U₄ at crossing
    if U4_c is not None:
        print(f"\n  1. U₄ at crossing: {U4_c:.4f}")
        d_ising = abs(U4_c - 0.611)
        d_mf = abs(U4_c - 0.667)
        if d_ising < d_mf:
            evidence['2D_Ising'] += 1
            print(f"     → Closer to 2D Ising (0.611)")
        elif d_mf < d_ising:
            evidence['mean_field'] += 1
            print(f"     → Closer to mean-field (0.667)")
        else:
            evidence['neither'] += 1

    # Evidence 2: Exponents
    if 'fits' in all_results['B_exponents']:
        fits = all_results['B_exponents']['fits']
        print(f"\n  2. Critical exponents:")
        predictions = {
            'var':   ('Var(C)',     -0.125,  -0.500),
            'chi':   ('χ = N·Var',   0.875,   0.500),
            'm_abs': ('⟨|C-0.5|⟩', -0.0625, -0.250),
        }
        for key, (label, ising, mf) in predictions.items():
            if key in fits:
                measured = fits[key]['alpha']
                d_i = abs(measured - ising)
                d_m = abs(measured - mf)
                winner = "2D Ising" if d_i < d_m else "Mean-field"
                if d_i < d_m:
                    evidence['2D_Ising'] += 1
                else:
                    evidence['mean_field'] += 1
                print(f"     {label:15s}: {measured:+.4f} (2D Ising: {ising:+.4f}, MF: {mf:+.4f}) → {winner}")

    # Evidence 3: Data collapse
    if 'collapse' in all_results['C_collapse']:
        collapse = all_results['C_collapse']['collapse']
        print(f"\n  3. Data collapse quality (lower = better):")
        for name, res in collapse.items():
            print(f"     {name:15s}: {res['quality']:.4f}")

        named = {k: v for k, v in collapse.items() if k in ['2D_Ising', 'mean_field']}
        if named:
            best = min(named.items(), key=lambda x: x[1]['quality'])
            evidence[best[0]] += 1
            print(f"     → {best[0]} collapses better")

    # Evidence 4: Kurtosis
    if all_results.get('D_distribution'):
        dist = all_results['D_distribution']
        # Use largest N for most reliable kurtosis
        largest_N = max(N for N in dist.keys() if isinstance(N, int))
        kurt = dist[largest_N]['kurtosis']
        print(f"\n  4. Kurtosis at N={largest_N}: κ = {kurt:.3f}")
        print(f"     (Gaussian: 3.0, 2D Ising: ~1.75, Mean-field: ~2.19)")
        d_i = abs(kurt - 1.75)
        d_m = abs(kurt - 2.19)
        if d_i < d_m:
            evidence['2D_Ising'] += 1
            print(f"     → Closer to 2D Ising")
        else:
            evidence['mean_field'] += 1
            print(f"     → Closer to mean-field")

    # Evidence 5: Dynamic exponent
    if 'scaling' in all_results.get('E_correlation', {}):
        z = all_results['E_correlation']['scaling']['z_eff']
        print(f"\n  5. Dynamic exponent z/(νd) = {z:.3f}")
        print(f"     (2D Ising Glauber: ~1.085, Mean-field: 1.0)")
        d_i = abs(z - 1.085)
        d_m = abs(z - 1.0)
        if d_i < d_m:
            evidence['2D_Ising'] += 1
        else:
            evidence['mean_field'] += 1

    print(f"\n  VERDICT:")
    print(f"  Evidence for 2D Ising:  {evidence['2D_Ising']}")
    print(f"  Evidence for mean-field: {evidence['mean_field']}")
    print(f"  Inconclusive:           {evidence['neither']}")

    total = evidence['2D_Ising'] + evidence['mean_field']
    if total > 0:
        if evidence['2D_Ising'] > evidence['mean_field']:
            print(f"\n  >>> The collective coherence system appears to be in the 2D ISING universality class.")
            print(f"  >>> Effective dimensionality = 2, consistent with (C, θ) phase space.")
        elif evidence['mean_field'] > evidence['2D_Ising']:
            print(f"\n  >>> The system appears to be in the MEAN-FIELD universality class.")
            print(f"  >>> Consistent with all-to-all coupling structure.")
        else:
            print(f"\n  >>> INCONCLUSIVE — neither universality class clearly dominates.")
            print(f"  >>> The system may belong to a novel non-equilibrium universality class.")

    # Save
    end_time = datetime.now()
    all_results['metadata'] = {
        'session': 85,
        'title': 'Universality Class Identification',
        'question': 'Is β = 0.12 the 2D Ising exponent 1/8?',
        'start_time': str(start_time),
        'end_time': str(end_time),
        'duration_minutes': (end_time - start_time).total_seconds() / 60,
    }
    all_results['evidence'] = evidence

    with open('thor_session_85_universality_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n\nCompleted in {(end_time - start_time).total_seconds() / 60:.1f} minutes")
    print("Results saved to thor_session_85_universality_results.json")

    return all_results


if __name__ == '__main__':
    main()
