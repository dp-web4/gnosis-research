#!/usr/bin/env python3
"""
Thor Session #91: The Mechanism of Nearly-Free Information

Session 90 discovered the efficiency peak sits at sigma ~ 0.10, about 5x beyond
the stochastic resonance optimum (sigma ~ 0.022). Claim: "agents aren't burning
EP on internal clocks, but bits still transmit." That's a DESCRIPTION not a
MECHANISM.

This session asks: WHAT actually carries the information at the efficiency peak?

Three testable hypotheses:
  H1 (burst): MI is concentrated in rare switching events. Between events the
      system carries no signal, but pays no EP. Efficient because informative
      segments are short.
  H2 (diffuse): MI is spread uniformly in time. Every sample carries a little
      bit at low EP. Efficient because EP is low everywhere.
  H3 (decoherent relay): Phase coupling collapses (Kuramoto R -> 0) but C_mean
      still tracks signal slowly because C-dynamics are slower than phase.
      Efficient because phase-rotation EP vanishes while slow C-drift survives.

Experiments:
  A. Phase coherence across sigma. Compute Kuramoto order R(t) at sigma in
     {0.011, 0.022, 0.050, 0.100, 0.150}. If R collapses but MI survives at
     high sigma, H3 is live.
  B. Temporal structure of MI. Sliding-window MI(t) between signal and C_mean.
     Measure burstiness: what fraction of windows carries top-10% of MI? If
     burstiness is high at sigma=0.10, H1 is live.
  C. Conditional EP. Split trajectory into "active" (|dC_mean/dt| high) and
     "quiet" segments. Does EP concentrate where information is? Does the
     quiet fraction grow with sigma?
  D. Coupling ablation. At sigma=0.10, reduce kappa_phase and kappa_C to
     zero one at a time. Which channel carries the surviving MI?

Model matches S88/S89/S90 exactly.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)


# =============================================================================
# Simulation (matching S90)
# =============================================================================

def simulate(N, noise_std, steps, seed=None,
             kappa_phase=0.10, kappa_C=0.15,
             omega_base=0.1, omega_spread=0.02,
             phi_inverse=0.618, dt=0.1, C_threshold=0.55,
             signal_freq=0.003, signal_amp=0.0):
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
    signal_hist = np.empty(steps)

    for t in range(steps):
        C_hist[t] = C
        phase_hist[t] = phase
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean

        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        signal_hist[t] = signal
        is_attractive = (C_mean + signal) < C_threshold

        sign = 1.0 if is_attractive else -1.0
        if kappa_phase > 0:
            sin_diff = np.sin(phase[None, :] - phase[:, None])
            np.fill_diagonal(sin_diff, 0)
            dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        else:
            dphase = omega.copy()
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
        'C_mean': C_mean_hist, 'signal': signal_hist,
    }


# =============================================================================
# Metrics
# =============================================================================

def compute_mi_binned(x, y, n_bins=8):
    x_bins = np.linspace(x.min() - 1e-10, x.max() + 1e-10, n_bins + 1)
    y_bins = np.linspace(y.min() - 1e-10, y.max() + 1e-10, n_bins + 1)
    xi = np.clip(np.digitize(x, x_bins) - 1, 0, n_bins - 1)
    yi = np.clip(np.digitize(y, y_bins) - 1, 0, n_bins - 1)
    joint = np.zeros((n_bins, n_bins))
    for a, b in zip(xi, yi):
        joint[a, b] += 1
    total = joint.sum()
    if total == 0:
        return 0.0
    joint /= total
    p_x = joint.sum(axis=1)
    p_y = joint.sum(axis=0)
    mi = 0.0
    for i in range(n_bins):
        for j in range(n_bins):
            if joint[i, j] > 0 and p_x[i] > 0 and p_y[j] > 0:
                mi += joint[i, j] * np.log2(joint[i, j] / (p_x[i] * p_y[j]))
    return mi


def kuramoto_order(phase_hist):
    """Kuramoto order parameter R(t) = |<e^{i*phi}>|."""
    z = np.exp(1j * phase_hist).mean(axis=1)
    return np.abs(z)


def compute_ep_nbody(result, warmup, dt):
    C = result['C'][warmup:]
    phase = result['phase'][warmup:]
    drift_C = result['drift_C'][warmup:]
    drift_phase = result['drift_phase'][warmup:]
    N = C.shape[1]

    ep_C_ind = np.zeros(N)
    ep_phase_ind = np.zeros(N)
    for i in range(N):
        dC_i = np.diff(C[:, i])
        mu_i = drift_C[:-1, i]
        res_i = dC_i - mu_i * dt
        D_i = np.mean(res_i**2) / (2 * dt)
        if D_i > 0:
            ep_C_ind[i] = np.mean(mu_i**2) / D_i
        dphase_i = np.diff(phase[:, i])
        dphase_i = (dphase_i + np.pi) % (2 * np.pi) - np.pi
        mu_i = drift_phase[:-1, i]
        res_i = dphase_i - mu_i * dt
        res_i = (res_i + np.pi) % (2 * np.pi) - np.pi
        D_i = np.mean(res_i**2) / (2 * dt)
        if D_i > 0:
            ep_phase_ind[i] = np.mean(mu_i**2) / D_i

    return {
        'ep_C_total': float(np.sum(ep_C_ind)),
        'ep_phase_total': float(np.sum(ep_phase_ind)),
        'ep_nbody': float(np.sum(ep_C_ind) + np.sum(ep_phase_ind)),
    }


def windowed_mi(signal, C_mean, window, stride, n_bins=6):
    """MI per sliding window. Returns array of MI values and window centers."""
    n = len(signal)
    starts = np.arange(0, n - window + 1, stride)
    mis = np.empty(len(starts))
    for k, s in enumerate(starts):
        mis[k] = compute_mi_binned(C_mean[s:s+window], signal[s:s+window], n_bins)
    centers = starts + window // 2
    return centers, mis


def burstiness(x):
    """Fraction of total in top-10% of samples by magnitude."""
    x = np.asarray(x, dtype=float)
    if x.sum() <= 0:
        return 0.0
    k = max(1, int(0.1 * len(x)))
    idx = np.argsort(x)[::-1][:k]
    return float(x[idx].sum() / x.sum())


# =============================================================================
# EXPERIMENT A: Phase coherence vs sigma
# =============================================================================

def experiment_A():
    print("=" * 70)
    print("EXPERIMENT A: Phase Coherence vs sigma")
    print("=" * 70)
    print("  Testing H3 (decoherent relay): does Kuramoto R collapse but MI survive?\n")

    sigmas = [0.005, 0.011, 0.018, 0.022, 0.035, 0.050, 0.075, 0.100, 0.150]
    N = 4
    dt = 0.1
    steps = 40_000
    warmup = 8_000
    n_seeds = 3
    signal_amp = 0.02
    signal_freq = 0.003

    data = []
    for sigma in sigmas:
        R_means = []
        R_stds = []
        MIs = []
        ep_phase_fracs = []
        ep_nbody_vals = []
        for seed in range(n_seeds):
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                         signal_amp=signal_amp, signal_freq=signal_freq, dt=dt)
            R_t = kuramoto_order(r['phase'][warmup:])
            R_means.append(float(R_t.mean()))
            R_stds.append(float(R_t.std()))
            MIs.append(compute_mi_binned(r['C_mean'][warmup:], r['signal'][warmup:], n_bins=8))
            # EP without signal
            r_ep = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100 + 500,
                            signal_amp=0.0, dt=dt)
            ep = compute_ep_nbody(r_ep, warmup, dt)
            ep_nbody_vals.append(ep['ep_nbody'])
            if ep['ep_nbody'] > 0:
                ep_phase_fracs.append(ep['ep_phase_total'] / ep['ep_nbody'])

        entry = {
            'sigma': sigma,
            'R_mean': round(float(np.mean(R_means)), 4),
            'R_std_intra': round(float(np.mean(R_stds)), 4),
            'R_std_across_seeds': round(float(np.std(R_means)), 4),
            'MI_bits': round(float(np.mean(MIs)), 5),
            'ep_nbody': round(float(np.mean(ep_nbody_vals)), 2),
            'ep_phase_frac': round(float(np.mean(ep_phase_fracs)), 3) if ep_phase_fracs else 0.0,
            'eta_nbody': round(float(np.mean(MIs) / np.mean(ep_nbody_vals)) if np.mean(ep_nbody_vals) > 0 else 0, 6),
        }
        data.append(entry)
        print(f"  sigma={sigma:.4f}: R={entry['R_mean']:.3f}+/-{entry['R_std_intra']:.3f}  "
              f"MI={entry['MI_bits']:.4f}  EP_nb={entry['ep_nbody']:.1f}  "
              f"phase_frac={entry['ep_phase_frac']:.2f}  eta={entry['eta_nbody']:.5f}")

    # Verdict
    print("\n  VERDICT:")
    R_low = [d for d in data if d['sigma'] >= 0.075]
    R_high = [d for d in data if d['sigma'] <= 0.022]
    R_low_mean = np.mean([d['R_mean'] for d in R_low])
    R_high_mean = np.mean([d['R_mean'] for d in R_high])
    MI_low = np.mean([d['MI_bits'] for d in R_low])
    MI_high = np.mean([d['MI_bits'] for d in R_high])
    print(f"    Avg R at sigma<=0.022: {R_high_mean:.3f}  (MI={MI_high:.4f})")
    print(f"    Avg R at sigma>=0.075: {R_low_mean:.3f}  (MI={MI_low:.4f})")
    R_drop = 1 - R_low_mean / R_high_mean if R_high_mean > 0 else 0
    MI_drop = 1 - MI_low / MI_high if MI_high > 0 else 0
    print(f"    R drop = {100*R_drop:.0f}% | MI drop = {100*MI_drop:.0f}%")
    if R_drop > 0.5 and MI_drop < R_drop:
        print(f"    H3 SUPPORTED: phase decoheres faster than MI collapses")
    else:
        print(f"    H3 NOT supported here")

    return {'data': data, 'R_drop': float(R_drop), 'MI_drop': float(MI_drop)}


# =============================================================================
# EXPERIMENT B: Temporal structure of MI
# =============================================================================

def experiment_B():
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Temporal Structure of MI")
    print("=" * 70)
    print("  Testing H1 (burst) vs H2 (diffuse): is MI concentrated in rare events?\n")

    sigmas = [0.011, 0.022, 0.050, 0.100]
    N = 4
    dt = 0.1
    steps = 80_000
    warmup = 10_000
    signal_amp = 0.02
    signal_freq = 0.003
    # Window: ~2 periods of signal. signal_freq=0.003, dt=0.1 -> period = 3333 steps.
    window = 5000
    stride = 500

    data = []
    for sigma in sigmas:
        burst_vals = []
        activity_corr_vals = []
        for seed in range(3):
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                         signal_amp=signal_amp, signal_freq=signal_freq, dt=dt)
            C_ss = r['C_mean'][warmup:]
            sig_ss = r['signal'][warmup:]
            centers, mis = windowed_mi(sig_ss, C_ss, window, stride, n_bins=6)
            # Activity proxy: |dC_mean| per window
            activity = np.empty(len(centers))
            for k, c in enumerate(centers):
                lo, hi = c - window // 2, c + window // 2
                activity[k] = np.std(C_ss[lo:hi])
            burst_vals.append(burstiness(mis))
            # Correlation of per-window activity and per-window MI
            if np.std(mis) > 0 and np.std(activity) > 0:
                activity_corr_vals.append(float(np.corrcoef(activity, mis)[0, 1]))

        entry = {
            'sigma': sigma,
            'burstiness_MI': round(float(np.mean(burst_vals)), 3),
            'activity_MI_corr': round(float(np.mean(activity_corr_vals)), 3) if activity_corr_vals else 0.0,
        }
        data.append(entry)
        # Uniform random would give burstiness ~ 0.10, perfect burst -> 1.0
        print(f"  sigma={sigma:.3f}: burstiness(MI) = {entry['burstiness_MI']:.3f}  "
              f"(uniform=0.10, pure burst=1.0)  |  corr(activity,MI) = {entry['activity_MI_corr']:+.3f}")

    print("\n  VERDICT:")
    b_sr = next(d['burstiness_MI'] for d in data if d['sigma'] == 0.022)
    b_eff = next(d['burstiness_MI'] for d in data if d['sigma'] == 0.100)
    print(f"    burstiness at SR (sigma=0.022):       {b_sr:.3f}")
    print(f"    burstiness at eff peak (sigma=0.100): {b_eff:.3f}")
    if b_eff > b_sr * 1.3:
        print("    H1 SUPPORTED: MI is more bursty at efficiency peak")
    elif b_eff < b_sr * 0.8:
        print("    H2 SUPPORTED: MI is more uniform at efficiency peak")
    else:
        print("    INCONCLUSIVE between H1 and H2")

    return {'data': data}


# =============================================================================
# EXPERIMENT C: Conditional EP analysis
# =============================================================================

def experiment_C():
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Conditional EP (active vs quiet segments)")
    print("=" * 70)
    print("  Does EP concentrate during active segments? Does quiet fraction grow?\n")

    sigmas = [0.011, 0.022, 0.050, 0.100]
    N = 4
    dt = 0.1
    steps = 60_000
    warmup = 10_000
    signal_amp = 0.02

    data = []
    for sigma in sigmas:
        active_fracs = []
        active_ep_fracs = []
        active_mi_fracs = []
        for seed in range(3):
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                         signal_amp=signal_amp, signal_freq=0.003, dt=dt)
            C = r['C'][warmup:]
            drift_C = r['drift_C'][warmup:]
            drift_phase = r['drift_phase'][warmup:]
            C_mean = r['C_mean'][warmup:]
            sig = r['signal'][warmup:]

            # Activity proxy: per-timestep phase-drift magnitude mean
            # (this dominates EP in the locked regime)
            phase_drift_mag = np.mean(np.abs(drift_phase), axis=1)
            threshold = np.median(phase_drift_mag)
            active_mask = phase_drift_mag > threshold  # half active, half quiet by definition

            # EP in active vs quiet (use phase-drift^2 as EP proxy)
            ep_proxy = np.mean(drift_phase**2, axis=1)
            total_ep = ep_proxy.sum()
            if total_ep > 0:
                active_ep = ep_proxy[active_mask].sum()
                active_ep_fracs.append(float(active_ep / total_ep))

            # MI in active vs quiet segments
            if active_mask.sum() > 200 and (~active_mask).sum() > 200:
                mi_active = compute_mi_binned(C_mean[active_mask], sig[active_mask], n_bins=6)
                mi_quiet = compute_mi_binned(C_mean[~active_mask], sig[~active_mask], n_bins=6)
                total_mi = mi_active + mi_quiet
                if total_mi > 0:
                    active_mi_fracs.append(float(mi_active / total_mi))

            active_fracs.append(float(active_mask.mean()))

        entry = {
            'sigma': sigma,
            'active_fraction': round(float(np.mean(active_fracs)), 3),
            'ep_frac_active': round(float(np.mean(active_ep_fracs)), 3) if active_ep_fracs else 0.0,
            'mi_frac_active': round(float(np.mean(active_mi_fracs)), 3) if active_mi_fracs else 0.0,
        }
        data.append(entry)
        # By definition active ~= 0.5 of samples; EP and MI fractions are the informative numbers
        print(f"  sigma={sigma:.3f}: active={entry['active_fraction']:.2f}  "
              f"EP_frac_active={entry['ep_frac_active']:.2f}  "
              f"MI_frac_active={entry['mi_frac_active']:.2f}")

    return {'data': data}


# =============================================================================
# EXPERIMENT D: Coupling ablation at efficiency peak
# =============================================================================

def experiment_D():
    print("\n" + "=" * 70)
    print("EXPERIMENT D: Coupling Ablation at Efficiency Peak")
    print("=" * 70)
    print("  At sigma=0.100, which coupling channel carries the MI?\n")

    conditions = [
        ('baseline',   0.10, 0.15),
        ('no_phase',   0.00, 0.15),  # Kills phase coupling
        ('no_C',       0.10, 0.00),  # Kills C mean-field coupling
        ('both_off',   0.00, 0.00),
    ]
    sigma = 0.100
    N = 4
    dt = 0.1
    steps = 60_000
    warmup = 10_000
    signal_amp = 0.02
    signal_freq = 0.003

    data = []
    for name, kp, kc in conditions:
        MIs = []
        ep_nb_vals = []
        R_means = []
        for seed in range(3):
            r = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100,
                         kappa_phase=kp, kappa_C=kc,
                         signal_amp=signal_amp, signal_freq=signal_freq, dt=dt)
            C_ss = r['C_mean'][warmup:]
            sig_ss = r['signal'][warmup:]
            MIs.append(compute_mi_binned(C_ss, sig_ss, n_bins=8))
            R_t = kuramoto_order(r['phase'][warmup:])
            R_means.append(float(R_t.mean()))
            r_ep = simulate(N=N, noise_std=sigma, steps=steps, seed=seed * 100 + 500,
                            kappa_phase=kp, kappa_C=kc, signal_amp=0.0, dt=dt)
            ep = compute_ep_nbody(r_ep, warmup, dt)
            ep_nb_vals.append(ep['ep_nbody'])

        mi = float(np.mean(MIs))
        ep_nb = float(np.mean(ep_nb_vals))
        entry = {
            'condition': name,
            'kappa_phase': kp,
            'kappa_C': kc,
            'MI_bits': round(mi, 5),
            'ep_nbody': round(ep_nb, 2),
            'eta_nbody': round(mi / ep_nb if ep_nb > 0 else 0, 6),
            'R_mean': round(float(np.mean(R_means)), 3),
        }
        data.append(entry)
        print(f"  {name:12s} (kp={kp:.2f}, kc={kc:.2f}): "
              f"MI={entry['MI_bits']:.4f}  EP_nb={entry['ep_nbody']:.1f}  "
              f"eta={entry['eta_nbody']:.5f}  R={entry['R_mean']:.3f}")

    mi_base = next(d['MI_bits'] for d in data if d['condition'] == 'baseline')
    mi_no_phase = next(d['MI_bits'] for d in data if d['condition'] == 'no_phase')
    mi_no_C = next(d['MI_bits'] for d in data if d['condition'] == 'no_C')
    mi_off = next(d['MI_bits'] for d in data if d['condition'] == 'both_off')

    print("\n  VERDICT (at sigma=0.100):")
    def frac(x):
        return x / mi_base if mi_base > 0 else 0.0
    print(f"    baseline MI:           {mi_base:.4f}")
    print(f"    no phase coupling:     {mi_no_phase:.4f}  ({100*frac(mi_no_phase):.0f}% of baseline)")
    print(f"    no C coupling:         {mi_no_C:.4f}  ({100*frac(mi_no_C):.0f}% of baseline)")
    print(f"    both off (uncoupled):  {mi_off:.4f}  ({100*frac(mi_off):.0f}% of baseline)")

    if frac(mi_no_C) < 0.3:
        carrier = "C coupling (mean-field)"
    elif frac(mi_no_phase) < 0.3:
        carrier = "phase coupling"
    elif frac(mi_off) > 0.3:
        carrier = "neither — signal is detected uncoupled (signal enters C_mean directly via threshold)"
    else:
        carrier = "BOTH channels required"
    print(f"    MI carrier identified: {carrier}")

    return {'data': data, 'carrier': carrier}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    start = datetime.now()
    print(f"Thor Session #91: The Mechanism of Nearly-Free Information")
    print(f"Started: {start.isoformat()}\n")

    results = {}
    results['A'] = experiment_A()
    results['B'] = experiment_B()
    results['C'] = experiment_C()
    results['D'] = experiment_D()

    with open('thor_session_91_mechanism_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
    print(f"Results -> thor_session_91_mechanism_results.json")
