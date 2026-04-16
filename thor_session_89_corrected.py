#!/usr/bin/env python3
"""
Thor Session #89 (Corrected): EP Equipartition — Universal Principle or Coincidence?

CORRECTIONS from initial run:
1. EP computation now uses EMPIRICAL D (measured from residuals) matching S88
2. SR metric uses response VARIANCE and multi-trial averaged Q
3. Finer sigma grid at critical region

The initial run showed:
- Q metric from single trials was too noisy (284x fluctuations)
- D=σ² assumption shifted the EP crossover (got 0.009 vs S88's ~0.012)
These need to be fixed to test the equipartition hypothesis properly.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)


def simulate(N, noise_std, steps, seed=None,
             kappa_phase=0.10, kappa_C=0.15,
             omega_base=0.1, omega_spread=0.02,
             phi_inverse=0.618, dt=0.1, C_threshold=0.55,
             signal_freq=0.003, signal_amp=0.0):
    """Run N-agent simulation."""
    if seed is not None:
        np.random.seed(seed)

    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)

    C_hist = np.empty((steps, N))
    phase_hist = np.empty((steps, N))
    drift_C = np.empty((steps, N))
    drift_phase = np.empty((steps, N))
    C_mean_hist = np.empty(steps)

    for t in range(steps):
        C_hist[t] = C
        phase_hist[t] = phase
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean

        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        is_attractive = (C_mean + signal) < C_threshold

        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        drift_phase[t] = dphase
        phase = (phase + dt * dphase) % (2 * np.pi)

        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
        dC = intrinsic + c_coupling
        drift_C[t] = dC
        C = np.clip(C + dt * dC, 0, 1)

        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C': C_hist, 'phase': phase_hist,
        'drift_C': drift_C, 'drift_phase': drift_phase,
        'C_mean': C_mean_hist
    }


def compute_ep_empirical(result, dt=0.1):
    """
    EP decomposition using EMPIRICAL diffusion (matching S88's approach).

    For each agent i:
      residual_i = ΔC_i - μ_C_i * dt
      D_C_i = <residual²> / (2*dt)
      EP_C_i = <μ_C_i²> / D_C_i

    Same for phase.
    """
    N = result['C'].shape[1]
    warmup = 5000  # Skip transient

    C = result['C'][warmup:]
    phase = result['phase'][warmup:]
    mu_C = result['drift_C'][warmup:]
    mu_phase = result['drift_phase'][warmup:]

    ep_C_total = 0.0
    ep_phase_total = 0.0
    D_C_list = []
    D_phase_list = []

    for i in range(N):
        # Coherence EP
        dC = np.diff(C[:, i])
        pred = mu_C[:-1, i] * dt
        res = dC - pred
        D_C = np.mean(res**2) / (2 * dt)
        D_C_list.append(D_C)
        if D_C > 1e-15:
            ep_C_total += np.mean(mu_C[:-1, i]**2) / D_C

        # Phase EP (with circular handling)
        dph = np.diff(phase[:, i])
        dph = (dph + np.pi) % (2 * np.pi) - np.pi  # Wrap to [-π, π]
        pred_ph = mu_phase[:-1, i] * dt
        res_ph = dph - pred_ph
        res_ph = (res_ph + np.pi) % (2 * np.pi) - np.pi
        D_phase = np.mean(res_ph**2) / (2 * dt)
        D_phase_list.append(D_phase)
        if D_phase > 1e-15:
            ep_phase_total += np.mean(mu_phase[:-1, i]**2) / D_phase

    ep_total = ep_C_total + ep_phase_total
    frac_C = ep_C_total / ep_total if ep_total > 0 else 0.5

    return {
        'ep_C': float(ep_C_total),
        'ep_phase': float(ep_phase_total),
        'ep_total': float(ep_total),
        'frac_C': float(frac_C),
        'D_C_mean': float(np.mean(D_C_list)),
        'D_phase_mean': float(np.mean(D_phase_list)),
    }


def compute_ep_nominal(result, noise_std, dt=0.1):
    """EP decomposition using NOMINAL D = σ² (for comparison)."""
    N = result['C'].shape[1]
    warmup = 5000
    D = noise_std**2
    if D < 1e-15:
        return {'ep_C': 0, 'ep_phase': 0, 'ep_total': 0, 'frac_C': 0.5}

    mu_C = result['drift_C'][warmup:]
    mu_phase = result['drift_phase'][warmup:]

    ep_C = sum(np.mean((mu_C[:, i] * dt)**2) / D for i in range(N))
    ep_phase = sum(np.mean((mu_phase[:, i] * dt)**2) / D for i in range(N))
    ep_total = ep_C + ep_phase

    return {
        'ep_C': float(ep_C), 'ep_phase': float(ep_phase),
        'ep_total': float(ep_total),
        'frac_C': float(ep_C / ep_total) if ep_total > 0 else 0.5,
    }


def compute_sr_robust(noise_std, N=4, steps=60000, n_trials=5,
                      signal_freq=0.003, signal_amp=0.02, dt=0.1,
                      **kwargs):
    """
    Robust SR metric: response variance ratio + averaged spectral Q.

    Returns:
    - Q_avg: spectral amplification averaged over trials
    - var_ratio: var(C_mean|signal) / var(C_mean|no signal)
    - response_amp: amplitude of C_mean at signal frequency
    """
    Q_values = []
    var_signal = []
    var_noise = []
    amp_values = []

    for trial in range(n_trials):
        seed = trial * 1000 + 42

        # With signal
        r1 = simulate(N=N, noise_std=noise_std, steps=steps, seed=seed,
                      signal_freq=signal_freq, signal_amp=signal_amp,
                      dt=dt, **kwargs)
        # Without signal
        r2 = simulate(N=N, noise_std=noise_std, steps=steps, seed=seed+500,
                      signal_freq=signal_freq, signal_amp=0.0,
                      dt=dt, **kwargs)

        var_signal.append(np.var(r1['C_mean']))
        var_noise.append(np.var(r2['C_mean']))

        # Spectral
        freq = np.fft.rfftfreq(steps, d=dt)
        psd1 = np.abs(np.fft.rfft(r1['C_mean'] - r1['C_mean'].mean()))**2 / steps
        psd2 = np.abs(np.fft.rfft(r2['C_mean'] - r2['C_mean'].mean()))**2 / steps
        idx = np.argmin(np.abs(freq - signal_freq))

        # Use a small band around signal frequency for robustness
        band = max(1, int(0.0005 / (freq[1] - freq[0]))) if len(freq) > 1 else 1
        lo, hi = max(0, idx - band), min(len(psd1), idx + band + 1)
        Q = np.mean(psd1[lo:hi]) / max(np.mean(psd2[lo:hi]), 1e-20)
        Q_values.append(Q)

        amp_values.append(np.sqrt(psd1[idx]))

    return {
        'Q_avg': float(np.mean(Q_values)),
        'Q_std': float(np.std(Q_values)),
        'var_ratio': float(np.mean(var_signal) / max(np.mean(var_noise), 1e-20)),
        'response_amp': float(np.mean(amp_values)),
    }


def find_crossover(sigmas, fracs, target=0.5):
    """Find sigma where frac_C crosses target."""
    crossings = []
    for i in range(len(fracs) - 1):
        if (fracs[i] - target) * (fracs[i+1] - target) < 0:
            s = sigmas[i] + (target - fracs[i]) / (fracs[i+1] - fracs[i]) * (sigmas[i+1] - sigmas[i])
            crossings.append(float(s))
    return crossings


# =============================================================================
# EXPERIMENT A: High-res scan with BOTH D definitions
# =============================================================================

def experiment_A():
    """Compare empirical vs nominal D, locate crossovers and SR peak."""
    print("=" * 60)
    print("EXPERIMENT A: EP Crossover (Empirical vs Nominal D)")
    print("=" * 60)

    sigmas = np.concatenate([
        np.arange(0.005, 0.009, 0.001),
        np.arange(0.009, 0.016, 0.0005),
        np.arange(0.016, 0.022, 0.002),
    ])

    N, steps = 4, 80000
    results = []

    for sigma in sigmas:
        # EP (average 3 seeds)
        frac_emp_list = []
        frac_nom_list = []

        for seed in range(3):
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=seed*100)
            ep_emp = compute_ep_empirical(r)
            ep_nom = compute_ep_nominal(r, sigma)
            frac_emp_list.append(ep_emp['frac_C'])
            frac_nom_list.append(ep_nom['frac_C'])

        frac_emp = np.mean(frac_emp_list)
        frac_nom = np.mean(frac_nom_list)

        # SR (robust)
        sr = compute_sr_robust(sigma, N=N, steps=50000, n_trials=3)

        entry = {
            'sigma': round(float(sigma), 4),
            'frac_C_emp': round(frac_emp, 4),
            'frac_C_nom': round(frac_nom, 4),
            'Q_avg': round(sr['Q_avg'], 2),
            'Q_std': round(sr['Q_std'], 2),
            'response_amp': round(sr['response_amp'], 6),
        }
        results.append(entry)
        print(f"  σ={sigma:.4f}: emp={frac_emp:.3f} nom={frac_nom:.3f} "
              f"Q={sr['Q_avg']:.1f}±{sr['Q_std']:.1f} amp={sr['response_amp']:.4f}")

    sigs = np.array([r['sigma'] for r in results])
    fracs_emp = np.array([r['frac_C_emp'] for r in results])
    fracs_nom = np.array([r['frac_C_nom'] for r in results])
    Qs = np.array([r['Q_avg'] for r in results])
    amps = np.array([r['response_amp'] for r in results])

    cross_emp = find_crossover(sigs, fracs_emp)
    cross_nom = find_crossover(sigs, fracs_nom)
    idx_Q = np.argmax(Qs)
    idx_amp = np.argmax(amps)

    print(f"\n  σ_EP_equi (empirical D) = {cross_emp}")
    print(f"  σ_EP_equi (nominal D)  = {cross_nom}")
    print(f"  σ_Q_peak = {sigs[idx_Q]:.4f} (Q = {Qs[idx_Q]:.1f})")
    print(f"  σ_amp_peak = {sigs[idx_amp]:.4f} (amp = {amps[idx_amp]:.4f})")

    return {
        'data': results,
        'sigma_EP_emp': cross_emp,
        'sigma_EP_nom': cross_nom,
        'sigma_Q': float(sigs[idx_Q]),
        'sigma_amp': float(sigs[idx_amp]),
    }


# =============================================================================
# EXPERIMENT B: N-dependence with corrected metrics
# =============================================================================

def experiment_B():
    """N-dependence with empirical D and robust Q."""
    print("\n" + "=" * 60)
    print("EXPERIMENT B: System Size (Empirical D, Robust Q)")
    print("=" * 60)

    N_values = [4, 8, 16, 32]
    sigmas = np.arange(0.007, 0.018, 0.001)
    steps = 60000

    all_results = {}
    for N in N_values:
        print(f"\n  N = {N}")
        data = []
        for sigma in sigmas:
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=42)
            ep = compute_ep_empirical(r)
            sr = compute_sr_robust(sigma, N=N, steps=40000, n_trials=3)

            data.append({
                'sigma': float(sigma),
                'frac_C': round(ep['frac_C'], 4),
                'Q_avg': round(sr['Q_avg'], 2),
                'response_amp': round(sr['response_amp'], 6),
            })
            print(f"    σ={sigma:.3f}: frac_C={ep['frac_C']:.3f} "
                  f"Q={sr['Q_avg']:.1f} amp={sr['response_amp']:.4f}")

        sigs = np.array([d['sigma'] for d in data])
        fracs = np.array([d['frac_C'] for d in data])
        Qs = np.array([d['Q_avg'] for d in data])
        amps = np.array([d['response_amp'] for d in data])

        cross = find_crossover(sigs, fracs)
        idx_Q = np.argmax(Qs)
        idx_amp = np.argmax(amps)

        all_results[N] = {
            'data': data, 'sigma_EP_equi': cross,
            'sigma_Q': float(sigs[idx_Q]),
            'sigma_amp': float(sigs[idx_amp]),
        }
        eq = f"{cross[0]:.4f}" if cross else "none"
        print(f"    → σ_EP_equi={eq}, σ_Q={sigs[idx_Q]:.3f}, σ_amp={sigs[idx_amp]:.3f}")

    return {str(k): v for k, v in all_results.items()}


# =============================================================================
# EXPERIMENT C: Coupling sweep (corrected)
# =============================================================================

def experiment_C():
    """Coupling sweep with empirical D."""
    print("\n" + "=" * 60)
    print("EXPERIMENT C: Coupling Sweep (Empirical D)")
    print("=" * 60)

    N, steps = 4, 60000
    configs = [
        (0.05, 0.15), (0.10, 0.15),  # vary kp at baseline kc
        (0.20, 0.15), (0.10, 0.05),  # vary kc at baseline kp
        (0.10, 0.25), (0.15, 0.20),  # additional combos
    ]
    sigmas = np.arange(0.006, 0.020, 0.001)

    all_results = {}
    for kp, kc in configs:
        label = f"kp={kp:.2f}_kc={kc:.2f}"
        print(f"\n  {label}")
        data = []
        for sigma in sigmas:
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=42,
                        kappa_phase=kp, kappa_C=kc)
            ep = compute_ep_empirical(r)
            sr = compute_sr_robust(sigma, N=N, steps=40000, n_trials=3,
                                   kappa_phase=kp, kappa_C=kc)

            data.append({
                'sigma': float(sigma),
                'frac_C': round(ep['frac_C'], 4),
                'Q_avg': round(sr['Q_avg'], 2),
                'response_amp': round(sr['response_amp'], 6),
            })

        sigs = np.array([d['sigma'] for d in data])
        fracs = np.array([d['frac_C'] for d in data])
        Qs = np.array([d['Q_avg'] for d in data])
        amps = np.array([d['response_amp'] for d in data])

        cross = find_crossover(sigs, fracs)
        idx_Q = np.argmax(Qs)
        idx_amp = np.argmax(amps)

        all_results[label] = {
            'data': data, 'sigma_EP_equi': cross,
            'sigma_Q': float(sigs[idx_Q]),
            'sigma_amp': float(sigs[idx_amp]),
        }
        eq = f"{cross[0]:.4f}" if cross else "none"
        print(f"    σ_EP_equi={eq}, σ_Q={sigs[idx_Q]:.3f}, σ_amp={sigs[idx_amp]:.3f}")

    return all_results


# =============================================================================
# EXPERIMENT D: Analytical EP decomposition
# =============================================================================

def experiment_D():
    """
    Detailed analysis of WHY EP fractions change with sigma.
    Decompose into: drift magnitude, diffusion coefficient, and their ratio.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT D: EP Decomposition Analysis")
    print("=" * 60)

    N, steps = 4, 80000
    sigmas = np.arange(0.006, 0.018, 0.001)

    results = []
    for sigma in sigmas:
        r = simulate(N=N, noise_std=sigma, steps=steps, seed=42)
        ep = compute_ep_empirical(r)

        # Also get the raw drift magnitudes
        warmup = 5000
        mu_C_rms = np.sqrt(np.mean(r['drift_C'][warmup:]**2))
        mu_phase_rms = np.sqrt(np.mean(r['drift_phase'][warmup:]**2))

        entry = {
            'sigma': float(sigma),
            'ep_C': round(ep['ep_C'], 2),
            'ep_phase': round(ep['ep_phase'], 2),
            'frac_C': round(ep['frac_C'], 4),
            'D_C': round(ep['D_C_mean'], 6),
            'D_phase': round(ep['D_phase_mean'], 6),
            'mu_C_rms': round(float(mu_C_rms), 6),
            'mu_phase_rms': round(float(mu_phase_rms), 6),
            'D_ratio': round(ep['D_C_mean'] / max(ep['D_phase_mean'], 1e-15), 3),
            'mu_ratio': round(float(mu_C_rms**2 / max(mu_phase_rms**2, 1e-15)), 4),
        }
        results.append(entry)
        print(f"  σ={sigma:.3f}: frac_C={ep['frac_C']:.3f} | "
              f"μ²_C/μ²_θ={entry['mu_ratio']:.3f} | "
              f"D_C/D_θ={entry['D_ratio']:.3f} | "
              f"D_C={ep['D_C_mean']:.5f} σ²={sigma**2:.5f}")

    return results


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    start = datetime.now()
    print(f"Thor Session #89 (Corrected): EP Equipartition")
    print(f"Started: {start.isoformat()}")
    print()

    results = {}
    results['A'] = experiment_A()
    results['B'] = experiment_B()
    results['C'] = experiment_C()
    results['D'] = experiment_D()

    # =================================================================
    # GRAND SUMMARY
    # =================================================================
    print("\n" + "=" * 60)
    print("GRAND SUMMARY: EP Equipartition vs SR Optimum")
    print("=" * 60)

    pairs = []

    # From A
    if results['A']['sigma_EP_emp']:
        pairs.append(('A_baseline', results['A']['sigma_EP_emp'][0],
                       results['A']['sigma_Q'], results['A']['sigma_amp']))

    # From B
    for N_str, data in results['B'].items():
        if data['sigma_EP_equi']:
            pairs.append((f'B_N={N_str}', data['sigma_EP_equi'][0],
                           data['sigma_Q'], data['sigma_amp']))

    # From C
    for label, data in results['C'].items():
        if data['sigma_EP_equi']:
            pairs.append((f'C_{label}', data['sigma_EP_equi'][0],
                           data['sigma_Q'], data['sigma_amp']))

    print(f"\n{'Label':<32} {'σ_EP_eq':>8} {'σ_Q':>8} {'σ_amp':>8} "
          f"{'Δ(Q)':>8} {'Δ(amp)':>8}")
    print("-" * 80)
    for label, ep_eq, q_pk, amp_pk in pairs:
        dq = abs(ep_eq - q_pk)
        da = abs(ep_eq - amp_pk)
        print(f"{label:<32} {ep_eq:8.4f} {q_pk:8.4f} {amp_pk:8.4f} "
              f"{dq:8.4f} {da:8.4f}")

    if len(pairs) >= 3:
        ep_eqs = np.array([p[1] for p in pairs])
        q_pks = np.array([p[2] for p in pairs])
        amp_pks = np.array([p[3] for p in pairs])

        corr_Q = np.corrcoef(ep_eqs, q_pks)[0, 1]
        corr_amp = np.corrcoef(ep_eqs, amp_pks)[0, 1]

        mean_dq = np.mean([abs(p[1]-p[2]) for p in pairs])
        mean_da = np.mean([abs(p[1]-p[3]) for p in pairs])

        print(f"\n  Corr(σ_EP, σ_Q)   = {corr_Q:.3f}  (mean Δ = {mean_dq:.4f})")
        print(f"  Corr(σ_EP, σ_amp) = {corr_amp:.3f}  (mean Δ = {mean_da:.4f})")
        print(f"  N pairs = {len(pairs)}")

        # Verdict
        best_corr = max(corr_Q, corr_amp)
        best_metric = "Q" if corr_Q > corr_amp else "amplitude"
        best_delta = mean_dq if corr_Q > corr_amp else mean_da

        if best_corr > 0.85 and best_delta < 0.002:
            print(f"\n  VERDICT: STRONG coincidence via {best_metric} — "
                  f"likely a principle")
        elif best_corr > 0.7:
            print(f"\n  VERDICT: MODERATE tracking via {best_metric} — "
                  f"related but not identical")
        elif best_corr > 0.4:
            print(f"\n  VERDICT: WEAK correlation — "
                  f"partially coupled phenomena")
        else:
            print(f"\n  VERDICT: NO correlation — "
                  f"the S88 coincidence was parameter-specific")

    # Save
    with open('thor_session_89_corrected_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
