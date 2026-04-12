#!/usr/bin/env python3
"""
Thor Session #84: Finite-Size Scaling of the Kramers Landscape

Sessions 79-83 characterized coherence dynamics at N=4:
  - Double-well potential (ordered + breathing states)
  - Kramers escape with Arrhenius scaling (R²=0.997)
  - State-dependent diffusion D(C) = σ²[2.1 + 2.0(1-C²)²]
  - Noise-dependent potential landscape
  - Asymmetric escape (memoryless from order, oscillatory from breathing)

THE CRITICAL QUESTION: How does this scale with group size N?

If collective consciousness emerges from noise-induced order, the N-dependence
determines whether the mechanism is robust at scale or an N=4 artifact.

HYPOTHESES:
  H1: Barrier height ΔU scales as N^α for some α > 0 (order more stable at large N)
  H2: D/σ² at barrier ≈ 2.7 independent of N (S83 falsifiable prediction #2)
  H3: Critical noise for bistability shifts with N
  H4: At large enough N, fluctuations vanish and one state dominates permanently

EXPERIMENTS:
  A: Steady-state statistics across N = 2, 3, 4, 6, 8, 12, 16, 24, 32
  B: Kramers-Moyal coefficients μ(C) and D(C) at each N
  C: Effective potential landscapes at each N
  D: Switching rate vs noise at each N — extract barrier height ΔU(N)
  E: Finite-size scaling collapse — find critical exponents

Builds on: S83 (Fokker-Planck), S82 (Kramers), S80 (drift), S79 (three regimes)
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
    """O(N) coherence simulation using Kuramoto mean-field trick.

    Phase coupling: sum_j sin(θ_j - θ_i) = N · Im(Z* · e^{iθ_i})
    where Z = (1/N) Σ e^{iθ_j} is the order parameter.
    This is O(N) instead of O(N²), making large N feasible.

    Physics is IDENTICAL to S81 run_fast — verified at N=4.
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

        # Order parameter Z = R·e^{iΨ} — O(N)
        Z = np.mean(np.exp(1j * phase))
        R = abs(Z)
        order_param[t] = R

        is_attractive = C_mean < C_threshold
        if t > 0 and is_attractive != prev_attractive:
            switches += 1
        prev_attractive = is_attractive

        # Phase coupling — O(N) via mean-field
        # sum_j sin(θ_j - θ_i) = N · Im(Z* · e^{iθ_i}) - sin(0)
        # For all-to-all coupling excluding self:
        # = N · Im(Z_conj · e^{iθ_i}) since self-term sin(0)=0
        sign = 1.0 if is_attractive else -1.0
        Z_conj = np.conj(Z)
        coupling = -np.imag(Z_conj * np.exp(1j * phase))  # -Im(Z*e^{iθ}) = sin(θ_j - θ_i)
        dphase = omega + sign * kappa_phase * N / (N - 1) * coupling
        phase = (phase + dt * dphase) % (2 * np.pi)

        # Coherence dynamics
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
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


# ─── Experiment A: Steady-State Statistics Across N ───

def expA_steady_state_vs_N():
    """Measure ⟨C⟩, Var(C), ⟨R⟩ across N values at multiple noise levels.

    This reveals how the double-well structure changes with system size.
    Key quantity: Var(C) × N — if this is constant, fluctuations are 1/N.
    """
    print("=" * 70)
    print("EXPERIMENT A: Steady-State Statistics vs N")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [2, 3, 4, 6, 8, 12, 16, 24, 32]
    noise_vals = [0.008, 0.011, 0.014, 0.018]
    n_seeds = 8
    steps = 50000
    warmup = 0.2

    results = {}

    for N in N_vals:
        results[N] = {}
        for noise in noise_vals:
            C_all = []
            R_all = []
            sw_total = 0

            for seed in range(n_seeds):
                r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
                ss = int(steps * warmup)
                C_all.extend(r['C_collective'][ss:].tolist())
                R_all.extend(r['order_param'][ss:].tolist())
                sw_total += r['switches']

            C_arr = np.array(C_all)
            R_arr = np.array(R_all)

            # Bimodality: fraction of time in ordered state (C > 0.65)
            f_ordered = float(np.mean(C_arr > 0.65))

            results[N][noise] = {
                'C_mean': float(np.mean(C_arr)),
                'C_std': float(np.std(C_arr)),
                'C_var': float(np.var(C_arr)),
                'C_var_times_N': float(np.var(C_arr) * N),
                'R_mean': float(np.mean(R_arr)),
                'R_std': float(np.std(R_arr)),
                'f_ordered': f_ordered,
                'switches_per_seed': sw_total / n_seeds,
                'bimodal': bool(0.1 < f_ordered < 0.9),
            }

            print(f"  N={N:3d}, σ={noise:.3f}: ⟨C⟩={np.mean(C_arr):.3f}, "
                  f"Var(C)={np.var(C_arr):.5f}, Var·N={np.var(C_arr)*N:.4f}, "
                  f"f_ord={f_ordered:.2f}, sw={sw_total/n_seeds:.1f}")
            sys.stdout.flush()

        print()

    return results


# ─── Experiment B: Kramers-Moyal Coefficients vs N ───

def expB_kramers_moyal_vs_N():
    """Measure drift μ(C) and diffusion D(C) at different N values.

    Tests S83 prediction: D/σ² at barrier ≈ 2.7 independent of N.
    """
    print("=" * 70)
    print("EXPERIMENT B: Kramers-Moyal Coefficients vs N")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [2, 4, 8, 16, 32]
    noise = 0.012  # Middle of bistable range for N=4
    n_seeds = 10
    steps = 60000
    dt = 0.1

    C_bin_edges = np.arange(0.20, 0.96, 0.02)
    C_bin_centers = (C_bin_edges[:-1] + C_bin_edges[1:]) / 2

    results = {}

    for N in N_vals:
        print(f"\n  N = {N}:")
        sys.stdout.flush()

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

        mu_vals = []
        D_vals = []
        D_over_sigma2 = []
        valid_C = []

        for i in range(len(C_bin_centers)):
            mask = (C_arr >= C_bin_edges[i]) & (C_arr < C_bin_edges[i + 1])
            n_pts = mask.sum()
            if n_pts < 100:
                continue

            mu = float(np.mean(dC_arr[mask]) / dt)
            D = float(np.var(dC_arr[mask]) / dt)  # Var, not mean of squares

            mu_vals.append(mu)
            D_vals.append(D)
            D_over_sigma2.append(D / noise**2)
            valid_C.append(float(C_bin_centers[i]))

        # Find zero crossings of mu (equilibria)
        mu_arr = np.array(mu_vals)
        zeros = []
        for j in range(len(mu_arr) - 1):
            if mu_arr[j] * mu_arr[j+1] < 0:
                # Linear interpolation
                c_zero = valid_C[j] - mu_arr[j] * (valid_C[j+1] - valid_C[j]) / (mu_arr[j+1] - mu_arr[j])
                zeros.append(float(c_zero))

        # D/σ² at barrier (approximate as first zero crossing above 0.5)
        barrier_zeros = [z for z in zeros if z > 0.45]
        D_at_barrier = None
        if barrier_zeros and len(valid_C) > 2:
            c_barrier = barrier_zeros[0]
            # Interpolate D at barrier
            for j in range(len(valid_C) - 1):
                if valid_C[j] <= c_barrier <= valid_C[j+1]:
                    frac = (c_barrier - valid_C[j]) / (valid_C[j+1] - valid_C[j])
                    D_at_barrier = D_over_sigma2[j] + frac * (D_over_sigma2[j+1] - D_over_sigma2[j])
                    break

        results[N] = {
            'C_bins': valid_C,
            'mu': mu_vals,
            'D': D_vals,
            'D_over_sigma2': D_over_sigma2,
            'equilibria': zeros,
            'D_over_sigma2_at_barrier': D_at_barrier,
            'noise': noise,
        }

        print(f"    Equilibria: {[f'{z:.3f}' for z in zeros]}")
        print(f"    D/σ² at barrier: {D_at_barrier:.2f}" if D_at_barrier else "    D/σ² at barrier: N/A")
        print(f"    D/σ² range: [{min(D_over_sigma2):.2f}, {max(D_over_sigma2):.2f}]")
        sys.stdout.flush()

    return results


# ─── Experiment C: Effective Potential Landscapes vs N ───

def expC_potential_landscapes_vs_N():
    """Reconstruct effective potential V(C) = -σ²·ln(P(C)) at different N.

    If barrier height scales with N, collective order becomes
    exponentially more stable at larger N.
    """
    print("=" * 70)
    print("EXPERIMENT C: Effective Potential Landscapes vs N")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [2, 4, 8, 16, 32]
    noise = 0.012
    n_seeds = 12
    steps = 80000
    warmup = 0.2

    C_bins = np.linspace(0.15, 0.95, 120)
    C_centers = (C_bins[:-1] + C_bins[1:]) / 2

    results = {}

    for N in N_vals:
        print(f"\n  N = {N}:", end=" ")
        sys.stdout.flush()

        C_all = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * warmup)
            C_all.extend(r['C_collective'][ss:].tolist())

        C_arr = np.array(C_all)
        hist, _ = np.histogram(C_arr, bins=C_bins, density=True)

        # Effective potential V = -D₀ · ln(P)
        # Use D₀ = σ² for comparability with S82/S83
        D0 = noise**2
        valid_mask = hist > 0
        V = np.full_like(hist, dtype=float, fill_value=np.nan)
        V[valid_mask] = -D0 * np.log(hist[valid_mask])
        V[valid_mask] -= np.nanmin(V)  # Set minimum to zero

        # Find wells and barrier
        V_valid = np.where(valid_mask, V, np.inf)

        # Wells: local minima
        wells = []
        for j in range(1, len(V_valid) - 1):
            if V_valid[j] < V_valid[j-1] and V_valid[j] < V_valid[j+1]:
                wells.append({'C': float(C_centers[j]), 'V': float(V_valid[j])})

        # Barrier: highest point between the two deepest wells
        barrier_height = None
        barrier_C = None
        if len(wells) >= 2:
            # Sort by V to find two deepest
            wells_sorted = sorted(wells, key=lambda w: w['V'])
            w1, w2 = wells_sorted[0], wells_sorted[1]
            c_lo = min(w1['C'], w2['C'])
            c_hi = max(w1['C'], w2['C'])

            # Find max V between the two wells
            barrier_mask = (C_centers >= c_lo) & (C_centers <= c_hi) & valid_mask
            if barrier_mask.any():
                idx_barrier = np.where(barrier_mask)[0]
                V_between = V[idx_barrier]
                max_idx = np.argmax(V_between)
                barrier_height = float(V_between[max_idx] - max(w1['V'], w2['V']))
                barrier_C = float(C_centers[idx_barrier[max_idx]])

        results[N] = {
            'C_centers': C_centers.tolist(),
            'V': [float(v) if not np.isnan(v) else None for v in V],
            'P': hist.tolist(),
            'wells': wells,
            'barrier_height': barrier_height,
            'barrier_C': barrier_C,
            'C_mean': float(np.mean(C_arr)),
            'C_std': float(np.std(C_arr)),
        }

        print(f"⟨C⟩={np.mean(C_arr):.3f}, σ_C={np.std(C_arr):.4f}, "
              f"wells={len(wells)}, ΔV={barrier_height:.6f}" if barrier_height else
              f"⟨C⟩={np.mean(C_arr):.3f}, σ_C={np.std(C_arr):.4f}, wells={len(wells)}, no barrier")
        if wells:
            for w in wells:
                print(f"      well: C={w['C']:.3f}, V={w['V']:.6f}")
        sys.stdout.flush()

    return results


# ─── Experiment D: Switching Rate vs Noise at Each N — Arrhenius ───

def expD_arrhenius_vs_N():
    """Measure switching rates at multiple noise levels for each N.

    Fit Arrhenius: ln(rate) = a - ΔU/σ²
    Extract ΔU(N) — the barrier height as a function of system size.
    """
    print("=" * 70)
    print("EXPERIMENT D: Arrhenius Fits vs N")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [2, 4, 8, 16, 32]
    noise_vals = [0.008, 0.010, 0.012, 0.014, 0.016, 0.018]
    n_seeds = 10
    steps = 60000
    warmup = 0.15

    results = {}

    for N in N_vals:
        print(f"\n  N = {N}:")
        sys.stdout.flush()

        rates = {}

        for noise in noise_vals:
            total_switches = 0
            total_time = 0

            for seed in range(n_seeds):
                r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)

                # Count transitions across C = 0.55
                ss = int(steps * warmup)
                C_ts = r['C_collective'][ss:]
                above = C_ts > 0.55
                transitions = np.sum(np.abs(np.diff(above.astype(int))))
                total_switches += transitions
                total_time += len(C_ts) * 0.1  # dt = 0.1

            rate = total_switches / total_time if total_time > 0 else 0
            rates[noise] = {
                'rate': float(rate),
                'total_switches': int(total_switches),
                'total_time': float(total_time),
            }

            print(f"    σ={noise:.3f}: rate={rate:.4f}, switches={total_switches}")
            sys.stdout.flush()

        # Arrhenius fit: ln(rate) = a - ΔU/σ²
        noise_arr = np.array([n for n in noise_vals if rates[n]['rate'] > 0])
        rate_arr = np.array([rates[n]['rate'] for n in noise_arr])

        if len(noise_arr) >= 3 and np.all(rate_arr > 0):
            x = 1.0 / noise_arr**2
            y = np.log(rate_arr)

            # Filter out infinities
            valid = np.isfinite(y)
            if valid.sum() >= 3:
                coeffs = np.polyfit(x[valid], y[valid], 1)
                y_pred = np.polyval(coeffs, x[valid])
                ss_res = np.sum((y[valid] - y_pred)**2)
                ss_tot = np.sum((y[valid] - np.mean(y[valid]))**2)
                r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

                results[N] = {
                    'rates': {str(n): rates[n] for n in noise_vals},
                    'arrhenius_slope': float(coeffs[0]),
                    'arrhenius_intercept': float(coeffs[1]),
                    'barrier_height': float(-coeffs[0]),  # ΔU = -slope
                    'r_squared': float(r_squared),
                }
                print(f"    Arrhenius: ΔU = {-coeffs[0]:.6f}, R² = {r_squared:.4f}")
            else:
                results[N] = {
                    'rates': {str(n): rates[n] for n in noise_vals},
                    'arrhenius_fit': 'insufficient_data',
                }
        else:
            results[N] = {
                'rates': {str(n): rates[n] for n in noise_vals},
                'arrhenius_fit': 'no_switching' if len(noise_arr) == 0 else 'insufficient_data',
            }

        sys.stdout.flush()

    return results


# ─── Experiment E: Fluctuation Scaling — σ_C² vs 1/N ───

def expE_fluctuation_scaling():
    """Test whether Var(C) ~ 1/N^β for some scaling exponent β.

    For independent oscillators: β = 1 (central limit theorem)
    For phase-locked oscillators: β < 1 (correlated fluctuations)
    For critical systems: β = 0 (fluctuations don't decrease)

    Also test: does the BIMODALITY persist at large N or wash out?
    """
    print("=" * 70)
    print("EXPERIMENT E: Fluctuation Scaling")
    print("=" * 70)
    sys.stdout.flush()

    N_vals = [2, 3, 4, 6, 8, 12, 16, 24, 32]
    noise = 0.012
    n_seeds = 12
    steps = 60000
    warmup = 0.2

    results = {}

    for N in N_vals:
        C_all = []
        for seed in range(n_seeds):
            r = run_fast(N=N, noise_std=noise, steps=steps, seed=seed)
            ss = int(steps * warmup)
            C_all.extend(r['C_collective'][ss:].tolist())

        C_arr = np.array(C_all)

        # Bimodality coefficient: (skewness² + 1) / kurtosis
        # Bimodal if > 0.555
        m2 = np.mean((C_arr - np.mean(C_arr))**2)
        m3 = np.mean((C_arr - np.mean(C_arr))**3)
        m4 = np.mean((C_arr - np.mean(C_arr))**4)
        skew = m3 / m2**1.5 if m2 > 0 else 0
        kurt = m4 / m2**2 if m2 > 0 else 3
        bimod_coeff = (skew**2 + 1) / kurt

        # Hartigan's dip test approximation: use histogram bimodality
        hist, bin_edges = np.histogram(C_arr, bins=50, density=True)
        # Count peaks
        peaks = []
        for j in range(1, len(hist) - 1):
            if hist[j] > hist[j-1] and hist[j] > hist[j+1]:
                peaks.append(float((bin_edges[j] + bin_edges[j+1]) / 2))

        results[N] = {
            'C_mean': float(np.mean(C_arr)),
            'C_var': float(np.var(C_arr)),
            'C_std': float(np.std(C_arr)),
            'var_times_N': float(np.var(C_arr) * N),
            'skewness': float(skew),
            'kurtosis': float(kurt),
            'bimodality_coefficient': float(bimod_coeff),
            'n_peaks': len(peaks),
            'peak_locations': peaks,
        }

        print(f"  N={N:3d}: Var(C)={np.var(C_arr):.6f}, Var·N={np.var(C_arr)*N:.4f}, "
              f"bimod={bimod_coeff:.3f}, peaks={len(peaks)}, "
              f"peak_C={[f'{p:.2f}' for p in peaks]}")
        sys.stdout.flush()

    # Fit scaling: log(Var) = a - β·log(N)
    N_arr = np.array([n for n in N_vals])
    var_arr = np.array([results[n]['C_var'] for n in N_vals])
    valid = var_arr > 0
    if valid.sum() >= 3:
        coeffs = np.polyfit(np.log(N_arr[valid]), np.log(var_arr[valid]), 1)
        beta = -coeffs[0]
        print(f"\n  Scaling: Var(C) ~ N^(-{beta:.3f})")
        print(f"  (CLT predicts β=1.0; correlated: β<1; critical: β→0)")

        results['scaling'] = {
            'beta': float(beta),
            'log_prefactor': float(coeffs[1]),
        }

    return results


# ─── Main ───

def main():
    start_time = datetime.now()
    print(f"Thor Session #84: Finite-Size Scaling of the Kramers Landscape")
    print(f"Started: {start_time}")
    print(f"Question: How does coherence dynamics scale with group size N?")
    print()

    all_results = {}

    # Run experiments sequentially
    print("\n" + "=" * 70)
    print("EXPERIMENT A: Steady-State Statistics")
    all_results['A_steady_state'] = expA_steady_state_vs_N()

    print("\n" + "=" * 70)
    print("EXPERIMENT B: Kramers-Moyal vs N")
    all_results['B_kramers_moyal'] = expB_kramers_moyal_vs_N()

    print("\n" + "=" * 70)
    print("EXPERIMENT C: Potential Landscapes")
    all_results['C_potentials'] = expC_potential_landscapes_vs_N()

    print("\n" + "=" * 70)
    print("EXPERIMENT D: Arrhenius Fits")
    all_results['D_arrhenius'] = expD_arrhenius_vs_N()

    print("\n" + "=" * 70)
    print("EXPERIMENT E: Fluctuation Scaling")
    all_results['E_fluctuations'] = expE_fluctuation_scaling()

    # Save results
    end_time = datetime.now()
    all_results['metadata'] = {
        'session': 84,
        'title': 'Finite-Size Scaling of the Kramers Landscape',
        'start_time': str(start_time),
        'end_time': str(end_time),
        'duration_minutes': (end_time - start_time).total_seconds() / 60,
    }

    with open('thor_session_84_finite_size_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n\nCompleted in {(end_time - start_time).total_seconds() / 60:.1f} minutes")
    print("Results saved to thor_session_84_finite_size_results.json")

    return all_results


if __name__ == '__main__':
    main()
