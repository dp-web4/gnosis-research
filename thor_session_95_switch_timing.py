#!/usr/bin/env python3
"""
Thor Session #95: Switch-Timing Matched Filter — Does It Escape
the Amplitude-Saturation Cliff?

S94 observed α=0.30 scaling of raw-signal matched-filter |z_vec|(A)
at σ=0.022, in deep saturation regime (Kramers rate ≈ signal rate).
S94 Prediction #4:

  "Switch-timing matched filter should give α≈1 — because the
   switching instant's phase relative to drive is unbounded in A
   while signal envelope saturates."

This session tests that prediction directly:

  1. Same σ=0.022 point (SR peak), same amplitude grid as S94 plus
     A=0.02 (S86's amplitude) and A=0.30 (high end).
  2. n=32 independent seeds with signal, n=32 without, T=4000s.
  3. Two detectors computed on THE SAME trajectories:
     (a) raw-signal matched filter (S93 phase_coherent_IQ)
     (b) switch-timing matched filter (new)
  4. Fit α from log-log |z_vec|(A) for each.
  5. Bonus: for a smaller (A=0.12) set of long-T (T=32000s)
     trajectories, split into 8 chunks of 4000s and measure the
     phase angle of (I, Q) per chunk to test S94 P3 — response
     phase non-stationarity as the mechanism for seeds-beats-length.

Switch-timing detector:
  - For each trajectory, compute C_mean_hist (post-warmup).
  - Identify switch events as indices where the sign of
    (C_mean - C_threshold) changes. Each switch is a point
    process event with a direction (±1 = upward/downward cross).
  - I_st = Σ_k dir_k · sin(2π f_s · (t_k + warmup) · dt)
    Q_st = Σ_k dir_k · cos(2π f_s · (t_k + warmup) · dt)
  - Aggregate across seeds; z_I = (E[I|A] - E[I|0]) / pooled_SE

Under null (no signal), switch times are Poisson with rate r_K,
switch signs alternate, so E[I_st] = 0 and Var[I_st] = N_switch / 2.
Under signal, switches bunch near biased phases → nonzero E[I_st]
that scales LINEARLY with A (until the bunching saturates at a
delta-function-like timing pdf, which happens at much higher A
than the rate-saturation).

This is the prediction: α_st ≈ 1 while α_raw ≈ 0.30.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

# Reuse the canonical simulator from S93 (no changes)
from thor_session_93_phase_coherent import simulate, phase_coherent_IQ


C_THRESHOLD = 0.55


def switch_events(C_mean, threshold=C_THRESHOLD):
    """Return (indices, directions) of threshold-crossing events.
    direction = +1 for upward crossing (C_mean goes above threshold),
                -1 for downward crossing.
    Indices are post-warmup-slice relative (0-based within provided array).
    """
    diff = C_mean - threshold
    sign = np.sign(diff)
    sign[sign == 0] = 1  # treat exact-threshold as + to avoid ambiguity
    # A crossing occurs at index t if sign[t] != sign[t-1]
    crossings = np.where(np.diff(sign) != 0)[0] + 1
    if len(crossings) == 0:
        return np.array([], dtype=int), np.array([])
    directions = sign[crossings]  # the sign AFTER the crossing
    return crossings, directions


def switch_timing_IQ(C_mean, dt, signal_freq, t_offset,
                     threshold=C_THRESHOLD):
    """Point-process matched filter on threshold-crossing events.

    Returns (I_st, Q_st, n_switches).
    I_st, Q_st are normalized by sqrt(N_switches/2) so that under
    null they are approximately N(0, 1) — "per-unit-switch" z-like.
    """
    idx, direction = switch_events(C_mean, threshold)
    n = len(idx)
    if n < 2:
        return 0.0, 0.0, n
    t = (idx + t_offset) * dt
    I = float(np.sum(direction * np.sin(2 * np.pi * signal_freq * t)))
    Q = float(np.sum(direction * np.cos(2 * np.pi * signal_freq * t)))
    # Return raw (unnormalized) sums; z-scoring happens across seeds
    # via between-seed variance (independent-seed approach, like S93)
    return I, Q, n


def sweep_A(A_list, sigma, n_seeds, steps, warmup, dt=0.1,
            signal_freq=0.003, store_trajectories=False):
    """For each A, run n_seeds with signal and n_seeds without, compute
    both raw-signal and switch-timing (I, Q) per trajectory. Return a
    list of per-A dicts with z-scores for each detector.

    Uses INDEPENDENT seeds for with vs without (not paired).
    """
    rows = []
    stored = {}
    for A in A_list:
        I_raw_w, I_raw_o = [], []
        Q_raw_w, Q_raw_o = [], []
        I_st_w, I_st_o = [], []
        Q_st_w, Q_st_o = [], []
        n_sw_w, n_sw_o = [], []
        print(f"\n>> A={A:.3f}  n_seeds={n_seeds}  steps={steps}  "
              f"post-warmup={steps - warmup}")
        for seed in range(n_seeds):
            # WITH signal
            xw = simulate(N=4, noise_std=sigma, steps=steps,
                          seed=seed * 100 + 123,
                          signal_freq=signal_freq, signal_amp=A, dt=dt)
            xw_post = xw[warmup:]
            Iw, Qw = phase_coherent_IQ(xw_post, dt, signal_freq,
                                       t_offset=warmup)
            Ist, Qst, nsw = switch_timing_IQ(xw_post, dt, signal_freq,
                                             t_offset=warmup)
            I_raw_w.append(Iw); Q_raw_w.append(Qw)
            I_st_w.append(Ist); Q_st_w.append(Qst); n_sw_w.append(nsw)

            # WITHOUT signal (independent seed)
            xo = simulate(N=4, noise_std=sigma, steps=steps,
                          seed=seed * 100 + 77_777,
                          signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            xo_post = xo[warmup:]
            Io, Qo = phase_coherent_IQ(xo_post, dt, signal_freq,
                                       t_offset=warmup)
            Ist0, Qst0, nsw0 = switch_timing_IQ(xo_post, dt, signal_freq,
                                                t_offset=warmup)
            I_raw_o.append(Io); Q_raw_o.append(Qo)
            I_st_o.append(Ist0); Q_st_o.append(Qst0); n_sw_o.append(nsw0)

        def zdiff(a, b):
            a, b = np.asarray(a), np.asarray(b)
            m = a.mean() - b.mean()
            se = np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))
            return float(m), float(se), (float(m/se) if se > 0 else 0.0)

        # Raw-signal matched filter
        m_Iw, se_Iw, z_I_raw = zdiff(I_raw_w, I_raw_o)
        m_Qw, se_Qw, z_Q_raw = zdiff(Q_raw_w, Q_raw_o)
        T2_raw = z_I_raw**2 + z_Q_raw**2

        # Vector magnitude & its z-score
        vec_raw = np.sqrt(m_Iw**2 + m_Qw**2)
        vec_se_raw = np.sqrt((m_Iw * se_Iw)**2 + (m_Qw * se_Qw)**2) / max(vec_raw, 1e-12)
        z_vec_raw = vec_raw / vec_se_raw if vec_se_raw > 0 else 0.0

        # Switch-timing matched filter
        m_Istw, se_Istw, z_I_st = zdiff(I_st_w, I_st_o)
        m_Qstw, se_Qstw, z_Q_st = zdiff(Q_st_w, Q_st_o)
        T2_st = z_I_st**2 + z_Q_st**2

        vec_st = np.sqrt(m_Istw**2 + m_Qstw**2)
        vec_se_st = np.sqrt((m_Istw * se_Istw)**2 + (m_Qstw * se_Qstw)**2) / max(vec_st, 1e-12)
        z_vec_st = vec_st / vec_se_st if vec_se_st > 0 else 0.0

        mean_switches = float(np.mean(n_sw_w + n_sw_o))

        row = {
            'A': A, 'sigma': sigma, 'n_seeds': n_seeds,
            'steps': steps, 'warmup': warmup,
            'mean_switches': mean_switches,
            # Raw-signal matched filter
            'z_I_raw': z_I_raw, 'z_Q_raw': z_Q_raw,
            'T2_raw': T2_raw, 'z_vec_raw': z_vec_raw,
            # Switch-timing matched filter
            'z_I_st': z_I_st, 'z_Q_st': z_Q_st,
            'T2_st': T2_st, 'z_vec_st': z_vec_st,
            # Raw per-seed values (for optional re-analysis)
            'I_raw_w': I_raw_w, 'I_raw_o': I_raw_o,
            'Q_raw_w': Q_raw_w, 'Q_raw_o': Q_raw_o,
            'I_st_w': I_st_w, 'I_st_o': I_st_o,
            'Q_st_w': Q_st_w, 'Q_st_o': Q_st_o,
            'n_switches_w': n_sw_w, 'n_switches_o': n_sw_o,
        }
        rows.append(row)
        print(f"   raw MF:  z_I={z_I_raw:+6.2f}  z_Q={z_Q_raw:+6.2f}  "
              f"T²={T2_raw:6.1f}  |z_vec|={z_vec_raw:5.2f}")
        print(f"   ST MF:   z_I={z_I_st:+6.2f}  z_Q={z_Q_st:+6.2f}  "
              f"T²={T2_st:6.1f}  |z_vec|={z_vec_st:5.2f}   "
              f"(N_switch_mean={mean_switches:.0f})")
    return rows


def chunked_drift_test(A, sigma, n_seeds, total_steps, warmup, chunk_steps,
                       dt=0.1, signal_freq=0.003):
    """Simulate n_seeds long-T trajectories at amplitude A, split
    each into chunks of chunk_steps, compute raw-signal (I, Q) per
    chunk, and return per-chunk angles. Tests S94 P3 — response
    phase should drift across chunks if mechanism 1 (phase non-
    stationarity) is right.
    """
    print(f"\n>> Chunked drift test: A={A}, σ={sigma}, n_seeds={n_seeds}, "
          f"total_steps={total_steps}, chunk_steps={chunk_steps}")
    per_seed = []
    for seed in range(n_seeds):
        x = simulate(N=4, noise_std=sigma, steps=total_steps,
                     seed=seed * 100 + 501,
                     signal_freq=signal_freq, signal_amp=A, dt=dt)
        xp = x[warmup:]
        n_chunks = len(xp) // chunk_steps
        angles, mags, Is, Qs = [], [], [], []
        for c in range(n_chunks):
            chunk = xp[c*chunk_steps:(c+1)*chunk_steps]
            # t_offset must reference global time index of THIS chunk
            t_off = warmup + c * chunk_steps
            I, Q = phase_coherent_IQ(chunk, dt, signal_freq, t_offset=t_off)
            Is.append(I); Qs.append(Q)
            angles.append(float(np.degrees(np.arctan2(Q, I))))
            mags.append(float(np.sqrt(I**2 + Q**2)))
        per_seed.append({'seed': seed, 'angles_deg': angles,
                         'mags': mags, 'I': Is, 'Q': Qs})
        print(f"   seed={seed}  angles_deg={[f'{a:+6.1f}' for a in angles]}")
    return per_seed


# ─── Main ───

if __name__ == '__main__':
    start = datetime.now()
    print("Thor Session #95: Switch-Timing Matched Filter")
    print(f"Started: {start.isoformat()}\n")

    # Fixed conditions (same as S94 SR peak)
    sigma = 0.022
    signal_freq = 0.003
    warmup = 10_000
    dt = 0.1
    steps_base = 50_000    # T = 4000s post-warmup (n=32 seeds per cond)

    # Amplitude grid: A=0.02 probes S86 subthreshold, A=0.30 probes
    # deeper saturation. Others match S94 for direct comparison.
    A_list = [0.02, 0.04, 0.08, 0.12, 0.20, 0.30]

    # Phase 1: detector comparison at n=32
    rows_main = sweep_A(A_list, sigma=sigma, n_seeds=32,
                        steps=steps_base, warmup=warmup,
                        dt=dt, signal_freq=signal_freq)

    # Phase 2: chunked drift — 4 long trajectories at A=0.12, T=32000s,
    # split into 8 chunks of 4000s each.
    chunked = chunked_drift_test(A=0.12, sigma=sigma, n_seeds=4,
                                 total_steps=10_000 + 80_000,
                                 warmup=10_000,
                                 chunk_steps=10_000,
                                 dt=dt, signal_freq=signal_freq)

    # Fit α exponents on |z_vec| vs A (log-log)
    def fit_alpha(rows, key):
        A_arr = np.array([r['A'] for r in rows])
        z_arr = np.array([r[key] for r in rows])
        # Only include cells where z > 0 (otherwise log-log undefined)
        ok = z_arr > 0.1
        if ok.sum() < 2:
            return None
        logA = np.log(A_arr[ok])
        logZ = np.log(z_arr[ok])
        # z = k · A^α  →  log z = α log A + log k
        alpha, log_k = np.polyfit(logA, logZ, 1)
        pred = alpha * logA + log_k
        ss_res = np.sum((logZ - pred)**2)
        ss_tot = np.sum((logZ - logZ.mean())**2)
        R2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return {'alpha': float(alpha), 'k': float(np.exp(log_k)),
                'R2': float(R2), 'n_pts': int(ok.sum()),
                'A_kept': A_arr[ok].tolist(), 'z_kept': z_arr[ok].tolist()}

    fit_raw = fit_alpha(rows_main, 'z_vec_raw')
    fit_st = fit_alpha(rows_main, 'z_vec_st')

    # Summary printout
    print("\n" + "=" * 72)
    print("DETECTOR COMPARISON — |z_vec| at σ=0.022, n=32 seeds, T=4000s")
    print("=" * 72)
    print(f"  {'A':>6} {'raw |z|':>8} {'ST |z|':>8} {'ratio':>6} "
          f"{'N_sw':>6}")
    for r in rows_main:
        ratio = r['z_vec_st'] / r['z_vec_raw'] if r['z_vec_raw'] > 0.01 else 0
        print(f"  {r['A']:6.3f} {r['z_vec_raw']:8.2f} {r['z_vec_st']:8.2f} "
              f"{ratio:6.2f} {r['mean_switches']:6.0f}")

    print("\n" + "-" * 72)
    print("AMPLITUDE EXPONENT α FIT")
    print("-" * 72)
    if fit_raw:
        print(f"  raw MF:  α = {fit_raw['alpha']:5.3f}  k = {fit_raw['k']:.3f}  "
              f"R² = {fit_raw['R2']:+.3f}  (n={fit_raw['n_pts']})")
    if fit_st:
        print(f"  ST  MF:  α = {fit_st['alpha']:5.3f}  k = {fit_st['k']:.3f}  "
              f"R² = {fit_st['R2']:+.3f}  (n={fit_st['n_pts']})")

    print("\n" + "-" * 72)
    print("CHUNKED PHASE DRIFT (A=0.12, 8 chunks × 4000s)")
    print("-" * 72)
    for s in chunked:
        a = s['angles_deg']
        spread = max(a) - min(a) if len(a) > 1 else 0
        print(f"  seed {s['seed']}: angle range = {spread:.1f}°  "
              f"({min(a):+.1f} to {max(a):+.1f})")

    out = {
        'meta': {
            'session': 95,
            'title': 'Switch-Timing Matched Filter vs Raw-Signal',
            'started': start.isoformat(),
            'params': {
                'sigma': sigma, 'signal_freq': signal_freq,
                'warmup': warmup, 'dt': dt, 'steps_base': steps_base,
                'A_list': A_list, 'n_seeds': 32,
            },
        },
        'rows_main': rows_main,
        'fit_raw': fit_raw,
        'fit_st': fit_st,
        'chunked_drift': chunked,
    }
    with open('thor_session_95_switch_timing_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
