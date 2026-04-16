#!/usr/bin/env python3
"""
Thor Session #89: EP Equipartition — Universal Principle or Coincidence?

Session 88 discovered that at the SR optimum (sigma~0.011), entropy production
is approximately equally split between phase and coherence degrees of freedom.

QUESTION: Is this a deep principle or a parameter-specific coincidence?

EXPERIMENTS:
  A. High-resolution sigma scan — locate sigma_MI and sigma_EP_equi precisely
  B. N-dependence — N=4,8,16,32
  C. Coupling sweep — kappa_phase, kappa_C
  D. Threshold sweep — C_threshold
  E. MI verification
"""

import numpy as np
import json
import sys
from datetime import datetime

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)


def simulate_agents(N, noise_std, steps, seed=None,
                    kappa_phase=0.10, kappa_C=0.15,
                    omega_base=0.1, omega_spread=0.02,
                    phi_inverse=0.618, dt=0.1, C_threshold=0.55,
                    signal_freq=0.003, signal_amp=0.0):
    """Run N-agent simulation returning trajectories and drifts."""
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

        # Phase dynamics
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        drift_phase[t] = dphase
        phase = (phase + dt * dphase) % (2 * np.pi)

        # Coherence dynamics
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
        dC = intrinsic + c_coupling
        drift_C[t] = dC
        C = np.clip(C + dt * dC, 0, 1)

        # Noise
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

    return {
        'C': C_hist, 'phase': phase_hist,
        'drift_C': drift_C, 'drift_phase': drift_phase,
        'C_mean': C_mean_hist
    }


def compute_ep_decomposition(result, noise_std):
    """EP decomposed into coherence and phase contributions."""
    N = result['C'].shape[1]
    dt = 0.1
    D = noise_std**2 if noise_std > 0 else 1e-10

    ep_C = 0.0
    ep_phase = 0.0
    for i in range(N):
        mu_C = result['drift_C'][:, i] * dt
        ep_C += np.mean(mu_C**2) / D
        mu_phase = result['drift_phase'][:, i] * dt
        ep_phase += np.mean(mu_phase**2) / D

    ep_total = ep_C + ep_phase
    frac_C = ep_C / ep_total if ep_total > 0 else 0.5

    return {
        'ep_C': float(ep_C), 'ep_phase': float(ep_phase),
        'ep_total': float(ep_total), 'frac_C': float(frac_C),
    }


def compute_spectral_Q(noise_std, N=4, steps=50000, dt=0.1,
                       signal_freq=0.003, signal_amp=0.02, seed=42,
                       **kwargs):
    """Spectral amplification Q — fast SR metric."""
    r1 = simulate_agents(N=N, noise_std=noise_std, steps=steps, seed=seed,
                         signal_freq=signal_freq, signal_amp=signal_amp,
                         dt=dt, **kwargs)
    r2 = simulate_agents(N=N, noise_std=noise_std, steps=steps, seed=seed+1,
                         signal_freq=signal_freq, signal_amp=0.0,
                         dt=dt, **kwargs)

    freq = np.fft.rfftfreq(steps, d=dt)
    psd1 = np.abs(np.fft.rfft(r1['C_mean'] - r1['C_mean'].mean()))**2 / steps
    psd2 = np.abs(np.fft.rfft(r2['C_mean'] - r2['C_mean'].mean()))**2 / steps
    idx = np.argmin(np.abs(freq - signal_freq))

    return float(psd1[idx] / max(psd2[idx], 1e-20))


def find_crossover(sigmas, fracs):
    """Find sigma where frac_C crosses 0.5 by linear interpolation."""
    crossings = []
    for i in range(len(fracs) - 1):
        if (fracs[i] - 0.5) * (fracs[i+1] - 0.5) < 0:
            s = sigmas[i] + (0.5 - fracs[i]) / (fracs[i+1] - fracs[i]) * (sigmas[i+1] - sigmas[i])
            crossings.append(float(s))
    return crossings


def compute_mi(noise_std, N=4, steps=30000, n_trials=5,
               signal_freq=0.003, signal_amp=0.02, dt=0.1, **kwargs):
    """Binned MI between signal and response."""
    mi_vals = []
    for trial in range(n_trials):
        r = simulate_agents(N=N, noise_std=noise_std, steps=steps,
                            seed=trial*1000+42, signal_freq=signal_freq,
                            signal_amp=signal_amp, dt=dt, **kwargs)
        t_arr = np.arange(steps) * dt
        sig = signal_amp * np.sin(2 * np.pi * signal_freq * t_arr)

        n_bins = 15
        sig_bins = np.linspace(sig.min()-1e-10, sig.max()+1e-10, n_bins+1)
        resp_bins = np.linspace(r['C_mean'].min()-1e-10, r['C_mean'].max()+1e-10, n_bins+1)
        si = np.clip(np.digitize(sig, sig_bins)-1, 0, n_bins-1)
        ri = np.clip(np.digitize(r['C_mean'], resp_bins)-1, 0, n_bins-1)

        joint = np.zeros((n_bins, n_bins))
        for s, rv in zip(si, ri):
            joint[s, rv] += 1
        joint /= joint.sum()
        ps = joint.sum(axis=1)
        pr = joint.sum(axis=0)

        mi = 0.0
        for a in range(n_bins):
            for b in range(n_bins):
                if joint[a,b] > 0 and ps[a] > 0 and pr[b] > 0:
                    mi += joint[a,b] * np.log2(joint[a,b] / (ps[a]*pr[b]))
        mi_vals.append(mi)
    return float(np.mean(mi_vals)), float(np.std(mi_vals))


# =============================================================================
# EXPERIMENTS
# =============================================================================

def experiment_A():
    """High-resolution sigma scan."""
    print("=" * 60)
    print("EXPERIMENT A: High-Resolution Sigma Scan")
    print("=" * 60)

    sigmas = np.concatenate([
        np.arange(0.006, 0.010, 0.001),
        np.arange(0.010, 0.016, 0.0005),
        np.arange(0.016, 0.022, 0.002),
    ])

    N, steps = 4, 80000
    results = []

    for sigma in sigmas:
        # EP (average 3 seeds)
        fracs = []
        ep_tot = 0
        for seed in range(3):
            r = simulate_agents(N=N, noise_std=sigma, steps=steps, seed=seed*100)
            ep = compute_ep_decomposition(r, sigma)
            fracs.append(ep['frac_C'])
            ep_tot = ep['ep_total']

        frac_C = np.mean(fracs)
        frac_C_std = np.std(fracs)

        # Q
        Q = compute_spectral_Q(sigma, N=N, steps=50000)

        entry = {
            'sigma': round(float(sigma), 4),
            'frac_C': round(frac_C, 4),
            'frac_C_std': round(frac_C_std, 4),
            'Q': round(Q, 1),
            'ep_total': round(ep_tot, 1),
        }
        results.append(entry)
        print(f"  σ={sigma:.4f}: frac_C={frac_C:.3f}±{frac_C_std:.3f}, "
              f"frac_θ={1-frac_C:.3f}, Q={Q:.1f}")

    sigs = np.array([r['sigma'] for r in results])
    fracs = np.array([r['frac_C'] for r in results])
    Qs = np.array([r['Q'] for r in results])

    crossings = find_crossover(sigs, fracs)
    idx_Q = np.argmax(Qs)
    sigma_Q = float(sigs[idx_Q])

    print(f"\n  RESULTS:")
    print(f"    σ_EP_equi  = {crossings}")
    print(f"    σ_Q_peak   = {sigma_Q:.4f} (Q = {Qs[idx_Q]:.1f})")
    if crossings:
        sep = abs(crossings[0] - sigma_Q)
        print(f"    Separation = {sep:.4f} ({sep/sigma_Q:.1%} relative)")

    return {'experiment': 'A', 'data': results,
            'sigma_EP_equi': crossings, 'sigma_Q_peak': sigma_Q}


def experiment_B():
    """N-dependence."""
    print("\n" + "=" * 60)
    print("EXPERIMENT B: System Size Dependence")
    print("=" * 60)

    N_values = [4, 8, 16, 32]
    sigmas = np.arange(0.007, 0.018, 0.001)
    steps = 50000

    all_results = {}
    for N in N_values:
        print(f"\n  N = {N}")
        data = []
        for sigma in sigmas:
            r = simulate_agents(N=N, noise_std=sigma, steps=steps, seed=42)
            ep = compute_ep_decomposition(r, sigma)
            Q = compute_spectral_Q(sigma, N=N, steps=40000)
            data.append({'sigma': float(sigma), 'frac_C': ep['frac_C'], 'Q': Q})
            print(f"    σ={sigma:.3f}: frac_C={ep['frac_C']:.3f}, Q={Q:.1f}")

        sigs = np.array([d['sigma'] for d in data])
        fracs = np.array([d['frac_C'] for d in data])
        Qs = np.array([d['Q'] for d in data])
        crossings = find_crossover(sigs, fracs)
        idx_Q = np.argmax(Qs)

        all_results[N] = {
            'data': data, 'sigma_EP_equi': crossings,
            'sigma_Q_peak': float(sigs[idx_Q]),
        }
        eq = f"{crossings[0]:.4f}" if crossings else "none"
        print(f"    → σ_EP_equi={eq}, σ_Q={sigs[idx_Q]:.3f}")

    return {'experiment': 'B', 'results': {str(k): v for k, v in all_results.items()}}


def experiment_C():
    """Coupling parameter sweep."""
    print("\n" + "=" * 60)
    print("EXPERIMENT C: Coupling Sweep")
    print("=" * 60)

    N, steps = 4, 50000
    kp_values = [0.05, 0.10, 0.20]
    kc_values = [0.05, 0.15, 0.25]
    sigmas = np.arange(0.006, 0.022, 0.002)

    all_results = {}
    for kp in kp_values:
        for kc in kc_values:
            label = f"kp={kp:.2f}_kc={kc:.2f}"
            print(f"\n  {label}")
            data = []
            for sigma in sigmas:
                r = simulate_agents(N=N, noise_std=sigma, steps=steps, seed=42,
                                    kappa_phase=kp, kappa_C=kc)
                ep = compute_ep_decomposition(r, sigma)
                Q = compute_spectral_Q(sigma, N=N, steps=40000,
                                       kappa_phase=kp, kappa_C=kc)
                data.append({'sigma': float(sigma), 'frac_C': ep['frac_C'], 'Q': Q})

            sigs = np.array([d['sigma'] for d in data])
            fracs = np.array([d['frac_C'] for d in data])
            Qs = np.array([d['Q'] for d in data])
            crossings = find_crossover(sigs, fracs)
            idx_Q = np.argmax(Qs)

            all_results[label] = {
                'data': data, 'sigma_EP_equi': crossings,
                'sigma_Q_peak': float(sigs[idx_Q]),
                'Q_peak': float(Qs[idx_Q]),
            }
            eq = f"{crossings[0]:.4f}" if crossings else "none"
            print(f"    σ_EP_equi={eq}, σ_Q={sigs[idx_Q]:.3f}, Q={Qs[idx_Q]:.1f}")

    return {'experiment': 'C', 'results': all_results}


def experiment_D():
    """Threshold sweep."""
    print("\n" + "=" * 60)
    print("EXPERIMENT D: Threshold Sweep")
    print("=" * 60)

    N, steps = 4, 50000
    thresholds = [0.40, 0.50, 0.55, 0.60, 0.70]
    sigmas = np.arange(0.006, 0.024, 0.002)

    all_results = {}
    for thresh in thresholds:
        print(f"\n  C_threshold = {thresh:.2f}")
        data = []
        for sigma in sigmas:
            r = simulate_agents(N=N, noise_std=sigma, steps=steps, seed=42,
                                C_threshold=thresh)
            ep = compute_ep_decomposition(r, sigma)
            Q = compute_spectral_Q(sigma, N=N, steps=40000, C_threshold=thresh)
            data.append({'sigma': float(sigma), 'frac_C': ep['frac_C'], 'Q': Q})

        sigs = np.array([d['sigma'] for d in data])
        fracs = np.array([d['frac_C'] for d in data])
        Qs = np.array([d['Q'] for d in data])
        crossings = find_crossover(sigs, fracs)
        idx_Q = np.argmax(Qs)

        all_results[f"{thresh:.2f}"] = {
            'data': data, 'sigma_EP_equi': crossings,
            'sigma_Q_peak': float(sigs[idx_Q]),
        }
        eq = f"{crossings[0]:.4f}" if crossings else "none"
        print(f"    σ_EP_equi={eq}, σ_Q={sigs[idx_Q]:.3f}")

    return {'experiment': 'D', 'results': all_results}


def experiment_E():
    """MI verification — confirm Q tracks MI."""
    print("\n" + "=" * 60)
    print("EXPERIMENT E: MI Verification")
    print("=" * 60)

    sigmas = [0.008, 0.010, 0.011, 0.012, 0.013, 0.015]
    N = 4
    results = []

    for sigma in sigmas:
        mi, mi_std = compute_mi(sigma, N=N, steps=30000, n_trials=3)
        Q = compute_spectral_Q(sigma, N=N, steps=50000)
        r = simulate_agents(N=N, noise_std=sigma, steps=50000, seed=42)
        ep = compute_ep_decomposition(r, sigma)

        entry = {'sigma': sigma, 'MI': round(mi, 5), 'MI_std': round(mi_std, 5),
                 'Q': round(Q, 1), 'frac_C': round(ep['frac_C'], 4)}
        results.append(entry)
        print(f"  σ={sigma:.4f}: MI={mi:.4f}±{mi_std:.4f}, Q={Q:.1f}, frac_C={ep['frac_C']:.3f}")

    mis = np.array([r['MI'] for r in results])
    idx = np.argmax(mis)
    print(f"\n  σ_MI_peak = {results[idx]['sigma']:.4f} (MI = {mis[idx]:.4f})")

    return {'experiment': 'E', 'data': results, 'sigma_MI_peak': results[idx]['sigma']}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    start = datetime.now()
    print(f"Thor Session #89: EP Equipartition Universality")
    print(f"Started: {start.isoformat()}")
    print()

    results = {}
    results['A'] = experiment_A()
    results['B'] = experiment_B()
    results['C'] = experiment_C()
    results['D'] = experiment_D()
    results['E'] = experiment_E()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: EP Equipartition vs SR Optimum")
    print("=" * 60)

    # Collect all (sigma_EP_equi, sigma_Q) pairs
    pairs = []

    # From A
    if results['A']['sigma_EP_equi']:
        pairs.append(('A_baseline', results['A']['sigma_EP_equi'][0],
                       results['A']['sigma_Q_peak']))

    # From B
    for N_str, data in results['B']['results'].items():
        if data['sigma_EP_equi']:
            pairs.append((f'B_N={N_str}', data['sigma_EP_equi'][0],
                           data['sigma_Q_peak']))

    # From C
    for label, data in results['C']['results'].items():
        if data['sigma_EP_equi']:
            pairs.append((f'C_{label}', data['sigma_EP_equi'][0],
                           data['sigma_Q_peak']))

    # From D
    for label, data in results['D']['results'].items():
        if data['sigma_EP_equi']:
            pairs.append((f'D_thresh={label}', data['sigma_EP_equi'][0],
                           data['sigma_Q_peak']))

    print(f"\n{'Label':<30} {'σ_EP_equi':>10} {'σ_Q_peak':>10} {'Δ':>8} {'Δ/σ_Q':>8}")
    print("-" * 70)
    for label, ep_eq, q_pk in pairs:
        delta = abs(ep_eq - q_pk)
        rel = delta / q_pk if q_pk > 0 else 0
        print(f"{label:<30} {ep_eq:10.4f} {q_pk:10.4f} {delta:8.4f} {rel:8.1%}")

    # Correlation
    if len(pairs) >= 3:
        ep_eqs = np.array([p[1] for p in pairs])
        q_pks = np.array([p[2] for p in pairs])
        corr = np.corrcoef(ep_eqs, q_pks)[0, 1]
        mean_rel = np.mean([abs(p[1]-p[2])/p[2] for p in pairs])
        print(f"\n  Correlation(σ_EP_equi, σ_Q_peak) = {corr:.3f}")
        print(f"  Mean relative separation = {mean_rel:.1%}")
        print(f"  N pairs = {len(pairs)}")

        if corr > 0.9 and mean_rel < 0.2:
            print("\n  VERDICT: EP EQUIPARTITION TRACKS SR OPTIMUM — likely a principle")
        elif corr > 0.7:
            print("\n  VERDICT: MODERATE correlation — robust feature, not exact")
        else:
            print("\n  VERDICT: WEAK correlation — likely a coincidence at baseline params")

    # Save
    with open('thor_session_89_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
