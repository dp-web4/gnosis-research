#!/usr/bin/env python3
"""
Thor Session #96 — Part B: Dwell-weighted detector vs ST vs raw.

Context: S95-P4 predicted √2× gain from joint (raw ⊕ ST) test. S96 Part A
found naive joint gives only ~1.1× because raw and ST are nearly colinear:
per-seed correlations ρ(I_raw, Q_st) = +0.90, ρ(Q_raw, I_st) = −0.96.

Theoretical prediction (from integration-by-parts on Kramers ML derivation):
the "dwell-weighted" detector
        I_dw = ∫₀^T state(t)·sin(2π f_s t) dt,    state(t) = sign(C−θ)
satisfies the identity
        I_dw = (1/ω)·[−state(T)cos(ωT) + state(0)]  +  (2/ω)·Q_st
So the dwell detector is *also* a near-rotation of ST (coefficient 2/ω ≈ 106 s).

This session: (i) implement I_dw, Q_dw; (ii) verify the identity empirically
via per-seed correlation; (iii) compare 6-component joint detection power to
ST alone — is there ANY extra signal dimension?

Fixed conditions (same as S95): σ=0.022, f_s=0.003 Hz, warmup=10k, dt=0.1,
T_post=4000s. n=32 independent seeds per condition. Amplitudes focused on
detectable regime: [0.08, 0.12, 0.20, 0.30].
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55


def dwell_IQ(C_mean, dt, signal_freq, t_offset, threshold=C_THRESHOLD):
    """Dwell-weighted matched filter: I_dw = Σ_k state(k)·sin(2π f_s t_k)·dt
    where state(k) = sign(C_mean(k) - threshold). Continuous-time limit:
    ∫state(t)·sin(ωt)dt.
    """
    state = np.where(C_mean >= threshold, 1.0, -1.0)
    t = (np.arange(len(C_mean)) + t_offset) * dt
    s_sin = np.sin(2 * np.pi * signal_freq * t)
    s_cos = np.cos(2 * np.pi * signal_freq * t)
    I_dw = float(np.sum(state * s_sin) * dt)
    Q_dw = float(np.sum(state * s_cos) * dt)
    return I_dw, Q_dw, float(state.mean())  # also return dwell bias


def zdiff(a, b):
    a, b = np.asarray(a), np.asarray(b)
    m = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(m), float(se), (float(m / se) if se > 0 else 0.0)


def sweep_A(A_list, sigma, n_seeds, steps, warmup, dt=0.1, signal_freq=0.003):
    rows = []
    for A in A_list:
        data_w = {k: [] for k in
                  ('I_raw', 'Q_raw', 'I_st', 'Q_st', 'I_dw', 'Q_dw',
                   'n_switch', 'dwell_bias')}
        data_o = {k: [] for k in data_w}
        print(f"\n>> A={A:.3f}  n_seeds={n_seeds}  "
              f"T={steps-warmup}·dt={dt*(steps-warmup):.0f}s")
        for seed in range(n_seeds):
            # WITH signal
            xw = simulate(N=4, noise_std=sigma, steps=steps,
                          seed=seed * 100 + 123,
                          signal_freq=signal_freq, signal_amp=A, dt=dt)
            xw_post = xw[warmup:]
            Iw, Qw = phase_coherent_IQ(xw_post, dt, signal_freq, t_offset=warmup)
            Ist, Qst, nsw = switch_timing_IQ(xw_post, dt, signal_freq,
                                             t_offset=warmup)
            Idw, Qdw, db = dwell_IQ(xw_post, dt, signal_freq, t_offset=warmup)
            data_w['I_raw'].append(Iw); data_w['Q_raw'].append(Qw)
            data_w['I_st'].append(Ist); data_w['Q_st'].append(Qst)
            data_w['I_dw'].append(Idw); data_w['Q_dw'].append(Qdw)
            data_w['n_switch'].append(nsw); data_w['dwell_bias'].append(db)

            # WITHOUT signal (independent seed)
            xo = simulate(N=4, noise_std=sigma, steps=steps,
                          seed=seed * 100 + 77_777,
                          signal_freq=signal_freq, signal_amp=0.0, dt=dt)
            xo_post = xo[warmup:]
            Io, Qo = phase_coherent_IQ(xo_post, dt, signal_freq, t_offset=warmup)
            Ist0, Qst0, nsw0 = switch_timing_IQ(xo_post, dt, signal_freq,
                                                t_offset=warmup)
            Idw0, Qdw0, db0 = dwell_IQ(xo_post, dt, signal_freq,
                                       t_offset=warmup)
            data_o['I_raw'].append(Io); data_o['Q_raw'].append(Qo)
            data_o['I_st'].append(Ist0); data_o['Q_st'].append(Qst0)
            data_o['I_dw'].append(Idw0); data_o['Q_dw'].append(Qdw0)
            data_o['n_switch'].append(nsw0); data_o['dwell_bias'].append(db0)

        # z scores for each component
        z = {}
        for key in ('I_raw', 'Q_raw', 'I_st', 'Q_st', 'I_dw', 'Q_dw'):
            _, _, zk = zdiff(data_w[key], data_o[key])
            z[key] = zk

        T2_raw = z['I_raw']**2 + z['Q_raw']**2
        T2_st  = z['I_st']**2  + z['Q_st']**2
        T2_dw  = z['I_dw']**2  + z['Q_dw']**2
        T2_all6 = T2_raw + T2_st + T2_dw

        row = {
            'A': A,
            'z': z,
            'T2_raw': T2_raw, 'T2_st': T2_st, 'T2_dw': T2_dw,
            'T2_joint_raw_st': T2_raw + T2_st,
            'T2_joint_all6':   T2_all6,
            'mean_switches': float(np.mean(data_w['n_switch'] + data_o['n_switch'])),
            'mean_dwell_bias_w': float(np.mean(data_w['dwell_bias'])),
            'mean_dwell_bias_o': float(np.mean(data_o['dwell_bias'])),
            'per_seed_w': data_w,
            'per_seed_o': data_o,
        }
        rows.append(row)
        print(f"   z_raw: I={z['I_raw']:+5.2f} Q={z['Q_raw']:+5.2f} |z|={np.sqrt(T2_raw):4.2f}  "
              f"z_st:  I={z['I_st']:+5.2f} Q={z['Q_st']:+5.2f} |z|={np.sqrt(T2_st):4.2f}  "
              f"z_dw:  I={z['I_dw']:+5.2f} Q={z['Q_dw']:+5.2f} |z|={np.sqrt(T2_dw):4.2f}")
    return rows


def per_cell_correlations(row):
    """Compute 6x6 correlation matrix across seeds for both conditions,
    plus key targeted correlations relevant to the summation-by-parts theory.
    """
    keys = ('I_raw', 'Q_raw', 'I_st', 'Q_st', 'I_dw', 'Q_dw')
    arr_w = np.array([row['per_seed_w'][k] for k in keys])  # (6, n_seeds)
    arr_o = np.array([row['per_seed_o'][k] for k in keys])
    return {
        'corr_w': np.corrcoef(arr_w).tolist(),
        'corr_o': np.corrcoef(arr_o).tolist(),
        'keys': list(keys),
    }


def test_sum_by_parts_identity(rows, f_s=0.003):
    """For each cell, check: I_dw ≈ (2/ω)·Q_st + boundary corr.
    Under the identity, regressing I_dw on Q_st (per seed) should give slope
    ≈ 2/ω = 2/(2π f_s) = 1/(π f_s) ≈ 106.1 s (for f_s=0.003).

    Boundary correction is small; residuals should be ≤ 1% of typical I_dw.
    """
    omega = 2 * np.pi * f_s
    expected_slope = 2.0 / omega
    print(f"\nSummation-by-parts identity test: I_dw = (2/ω)·Q_st + boundary")
    print(f"Expected slope: 2/ω = {expected_slope:.2f} s  (for f_s={f_s})")
    print(f"{'A':>6} {'slope_w':>10} {'R²_w':>6} {'slope_o':>10} {'R²_o':>6}")
    out = []
    for r in rows:
        A = r['A']
        for cond_label, bucket in (('w', r['per_seed_w']), ('o', r['per_seed_o'])):
            pass
        Q_st_w = np.array(r['per_seed_w']['Q_st'])
        I_dw_w = np.array(r['per_seed_w']['I_dw'])
        Q_st_o = np.array(r['per_seed_o']['Q_st'])
        I_dw_o = np.array(r['per_seed_o']['I_dw'])

        def fit(x, y):
            if x.std() < 1e-12:
                return float('nan'), float('nan')
            slope = np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean())**2)
            intercept = y.mean() - slope * x.mean()
            pred = slope * x + intercept
            ss_tot = np.sum((y - y.mean())**2)
            ss_res = np.sum((y - pred)**2)
            return float(slope), float(1 - ss_res / ss_tot if ss_tot > 0 else 0)

        slope_w, R2_w = fit(Q_st_w, I_dw_w)
        slope_o, R2_o = fit(Q_st_o, I_dw_o)
        out.append({'A': A, 'slope_w': slope_w, 'R2_w': R2_w,
                    'slope_o': slope_o, 'R2_o': R2_o,
                    'expected_slope': expected_slope})
        print(f"{A:6.3f} {slope_w:10.2f} {R2_w:6.3f} {slope_o:10.2f} {R2_o:6.3f}")
    return out


def main():
    start = datetime.now()
    print(f"Thor Session #96 Part B: Dwell-weighted detector\n"
          f"Started: {start.isoformat()}\n")

    sigma = 0.022
    signal_freq = 0.003
    warmup = 10_000
    dt = 0.1
    steps_base = 50_000  # T_post = 40000 steps = 4000 s
    A_list = [0.00, 0.08, 0.12, 0.20, 0.30]  # include A=0 as null baseline
    n_seeds = 32

    rows = sweep_A(A_list, sigma=sigma, n_seeds=n_seeds,
                   steps=steps_base, warmup=warmup,
                   dt=dt, signal_freq=signal_freq)

    # Correlation structure per cell
    corrs = [per_cell_correlations(r) for r in rows]

    # Sum-by-parts identity test
    idtest = test_sum_by_parts_identity(rows, f_s=signal_freq)

    # Summary comparison: individual vs joint |z|
    print("\n" + "=" * 76)
    print("DETECTOR COMPARISON at σ=0.022, n=32 seeds, T=4000s")
    print("=" * 76)
    print(f"  {'A':>6}  {'|z|_raw':>7} {'|z|_st':>7} {'|z|_dw':>7} "
          f"{'|z|_raw+st':>10} {'|z|_all6':>9}")
    for r in rows:
        print(f"  {r['A']:6.3f}  {np.sqrt(r['T2_raw']):7.2f} "
              f"{np.sqrt(r['T2_st']):7.2f} {np.sqrt(r['T2_dw']):7.2f} "
              f"{np.sqrt(r['T2_joint_raw_st']):10.2f} "
              f"{np.sqrt(r['T2_joint_all6']):9.2f}")

    # Print correlation matrix averaged over detectable cells
    print("\nMean correlation matrix (with signal, A ≥ 0.08):")
    detectable = [c for r, c in zip(rows, corrs) if r['A'] >= 0.08]
    if detectable:
        M = np.mean([np.array(c['corr_w']) for c in detectable], axis=0)
        keys = corrs[0]['keys']
        print("          " + " ".join(f"{k:>7}" for k in keys))
        for i, k in enumerate(keys):
            print(f"{k:>7}   " + " ".join(f"{M[i,j]:+.3f}".rjust(7) for j in range(6)))

    print("\nMean correlation matrix (null, averaged over all A):")
    M_o = np.mean([np.array(c['corr_o']) for c in corrs], axis=0)
    keys = corrs[0]['keys']
    print("          " + " ".join(f"{k:>7}" for k in keys))
    for i, k in enumerate(keys):
        print(f"{k:>7}   " + " ".join(f"{M_o[i,j]:+.3f}".rjust(7) for j in range(6)))

    out = {
        'meta': {
            'session': 96,
            'part': 'B',
            'title': 'Dwell-weighted detector vs ST vs raw',
            'started': start.isoformat(),
            'params': {
                'sigma': sigma, 'signal_freq': signal_freq,
                'warmup': warmup, 'dt': dt, 'steps_base': steps_base,
                'A_list': A_list, 'n_seeds': n_seeds,
            },
        },
        'rows': rows,
        'per_cell_correlations': corrs,
        'sum_by_parts_identity': idtest,
    }
    with open('thor_session_96_dwell_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")


if __name__ == '__main__':
    main()
