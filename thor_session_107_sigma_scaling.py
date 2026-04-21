#!/usr/bin/env python3
"""S107 sub-analysis: how does σ_n² of the ST detector scale with N_sw?

The ST detector is z_st = sum_k δ_k exp(-iωt_k) over N_sw threshold
crossings. If crossings were independent and times were uniformly random,
σ_n²(z_st) = N_sw/2 (variance of complex sum of N unit phasors with
random arguments). Then R_coh = |μ|²/(|μ|² + N/2) which scales linearly
with the per-event signal density |μ|²/N.

For the *chunked* mean z̄ = (1/M) Σ z_chunk, σ_n² of the chunk-mean
should be (1/M)·var(z_chunk). If chunk-level z_st is ~Gaussian with
variance ~N_sw/(2*chunks_per_seed), then the per-seed σ_n we measure
for the chunk-of-chunks should track √N_sw.

We test this: for each S106 cell, plot σ_n_st vs √(N_sw_per_chunk).
A linear relationship with intercept~0 means ST σ_n is dominated by
event-count noise (Poisson-like). Deviations would indicate correlated
event timing (sub-Poisson, indicates signal-induced regularity).
"""
import json
import numpy as np


def main():
    s106 = json.load(open('thor_session_106_kappa_c_channel_results.json'))
    rows = []
    for label, cell in s106['cells'].items():
        kp = cell['kappa_phase']; kC = cell['kappa_C']
        for seed_pack in cell['per_seed_z']:
            z_st = np.array([complex(r, i) for r, i in seed_pack['z_st']])
            n_sw = np.array(seed_pack['n_sw'])
            mu = z_st.mean()
            dev = z_st - mu
            sigma_n2 = float(np.mean(np.abs(dev)**2))
            sigma_n = float(np.sqrt(sigma_n2))
            mean_n = float(n_sw.mean())
            rows.append({'label': label, 'kp': kp, 'kC': kC,
                         'seed': seed_pack['seed'],
                         'mean_n_sw': mean_n,
                         'sigma_n_st': sigma_n,
                         'sigma_n_st_squared': sigma_n2,
                         'mu_abs': float(abs(mu)),
                         'sigma_over_sqrt_n': sigma_n / np.sqrt(mean_n)
                                             if mean_n > 0 else 0.0,
                        })

    print("ST detector noise scaling per seed (S106 cells, kp=0.30 sweep):")
    print(f"{'label':>22} | {'<N_sw>':>7} | σ_n_ST | σ²/N | σ/√N | |μ|")
    print("-" * 78)
    # Aggregate per cell
    by_cell = {}
    for r in rows:
        by_cell.setdefault(r['label'], []).append(r)
    for label, rs in sorted(by_cell.items(), key=lambda kv: (kv[1][0]['kp'], kv[1][0]['kC'])):
        nsw = np.mean([r['mean_n_sw'] for r in rs])
        sn = np.mean([r['sigma_n_st'] for r in rs])
        sn2_over_n = np.mean([r['sigma_n_st_squared']/r['mean_n_sw'] for r in rs if r['mean_n_sw']>0])
        sn_over_sqrtn = np.mean([r['sigma_over_sqrt_n'] for r in rs])
        mu = np.mean([r['mu_abs'] for r in rs])
        print(f"{label:>22} | {nsw:7.0f} | {sn:6.3f} | {sn2_over_n:5.4f} | {sn_over_sqrtn:5.4f} | {mu:5.3f}")

    # Pearson correlation σ_n vs √N across cells
    cell_nsws = []
    cell_sigs = []
    for label, rs in by_cell.items():
        cell_nsws.append(float(np.mean([r['mean_n_sw'] for r in rs])))
        cell_sigs.append(float(np.mean([r['sigma_n_st'] for r in rs])))
    cell_nsws = np.array(cell_nsws); cell_sigs = np.array(cell_sigs)
    sqrt_n = np.sqrt(cell_nsws)
    if len(cell_nsws) >= 2:
        r = float(np.corrcoef(sqrt_n, cell_sigs)[0,1])
        # slope: σ_n = a √N + b
        A = np.column_stack([sqrt_n, np.ones_like(sqrt_n)])
        (a, b), *_ = np.linalg.lstsq(A, cell_sigs, rcond=None)
        print(f"\nCross-cell: σ_n_ST = {float(a):.4f} · √N + {float(b):.3f}, r = {r:.3f}")
        # Theoretical: for Gaussian-noise chunk z_st with var = N_sw/2 per chunk,
        # mean over M chunks has var = N_sw/(2M). So σ_chunk_mean ≈ √(N/2M).
        # With M_chunks = 50, predict slope = √(1/(2·50)) = 0.1.
        predicted = 1/np.sqrt(2*50)
        print(f"Theory (Gaussian-event Poisson, M=50 chunks): slope = {predicted:.4f}")
        print(f"Observed/Theory ratio: {float(a)/predicted:.3f}")


if __name__ == '__main__':
    main()
