#!/usr/bin/env python3
"""
Thor Session #94: The Detection Cliff
=====================================
Tests the scaling law z_I ∝ A · √(n·T) for matched-filter SR detection
in the N=4 bistable coherence model. Directly tests two of S93's
falsifiable predictions:

  Prediction #3: Longer trajectories are MORE cost-effective than more
    seeds (at matched compute).
  Prediction #5: Minimum detectable A at z=2, S93 budget, is ≈ 0.08 ± 0.02.

EXPERIMENTAL DESIGN
-------------------
Fix σ = 0.022 (S92/S93 SR peak), f_s = 0.003 (signal frequency).

Grid:
  A ∈ {0.04, 0.08, 0.12, 0.20}
  Compute budget B ∈ {1, 2, 4, 8}  (base config: n=16, T = B × 40k)

At B=4, also run n=64 × T=40k (seeds-variant) for direct seeds-vs-length
comparison at matched compute.

For each cell, run matched pairs with/without signal using independent
seeds. Compute z_I, z_Q, T² on the WITH-WITHOUT difference.

HYPOTHESES (falsifiable at session close)
-----------------------------------------
H1 (scaling): z_I(A, B) / A should be independent of A at fixed B,
   and proportional to √B. Fit z_I = k·A·√B; test R² > 0.9.
H2 (length vs seeds): at B=4, n=16×160k vs n=64×40k give same z_I
   within statistical error. (S93 Prediction #3 says long > more; std
   theory says equal.)
H3 (detection floor): A_min(z_thr=2, B) = 2/(k·√B). With k ≈ 20 from S93,
   A_min(B=1) = 0.10, A_min(B=8) = 0.035.

COMPUTE BUDGET
--------------
Base cells: 4 A × (1+2+4+8) × 16 seeds × 40k steps × 2 conditions
          ≈ 76.8M steps
Seeds variant: 4 A × 1 × 64 seeds × 40k × 2   ≈ 20.5M steps
Total ≈ 97M steps × 25 µs = ~40 min wall time.
"""

import numpy as np
import json
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)


# ─── Simulator (identical to S92/S93) ───
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
    C_mean_hist = np.empty(steps)
    for t in range(steps):
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean
        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        is_attractive = (C_mean + signal) < C_threshold
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        phase = (phase + dt * dphase) % (2 * np.pi)
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
        dC = intrinsic + c_coupling
        C = np.clip(C + dt * dC, 0, 1)
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)
    return C_mean_hist


def phase_coherent_IQ(x, dt, signal_freq, t_offset):
    """Matched filter projection of x onto sin/cos at signal_freq,
    aligned with the driving signal's phase (t_offset = warmup steps)."""
    x = x - x.mean()
    t = (np.arange(len(x)) + t_offset) * dt
    sin_ref = np.sin(2 * np.pi * signal_freq * t)
    cos_ref = np.cos(2 * np.pi * signal_freq * t)
    I = float(np.mean(x * sin_ref))
    Q = float(np.mean(x * cos_ref))
    return I, Q


def zdiff(a, b):
    a = np.asarray(a); b = np.asarray(b)
    m = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))
    return float(m), float(se), float(m / se) if se > 0 else 0.0


def run_cell(A, sigma, n_seeds, steps, warmup, signal_freq, dt, label,
             seed_offset=0):
    """One (A, n_seeds, steps) cell. Returns z_I, z_Q, T², and details."""
    iw, iwo = [], []
    qw, qwo = [], []
    t0 = time.time()
    for s in range(n_seeds):
        sw = seed_offset + s * 100
        swo = seed_offset + s * 100 + 50_000
        x_w = simulate(N=4, noise_std=sigma, steps=steps, seed=sw,
                       signal_freq=signal_freq, signal_amp=A, dt=dt)
        xw = x_w[warmup:]
        Iw, Qw = phase_coherent_IQ(xw, dt, signal_freq, t_offset=warmup)
        iw.append(Iw); qw.append(Qw)

        x_wo = simulate(N=4, noise_std=sigma, steps=steps, seed=swo,
                        signal_freq=signal_freq, signal_amp=0.0, dt=dt)
        xwo = x_wo[warmup:]
        Iwo, Qwo = phase_coherent_IQ(xwo, dt, signal_freq, t_offset=warmup)
        iwo.append(Iwo); qwo.append(Qwo)

    I_m, I_se, z_I = zdiff(iw, iwo)
    Q_m, Q_se, z_Q = zdiff(qw, qwo)
    T2 = z_I**2 + z_Q**2
    vec_mag = np.sqrt(I_m**2 + Q_m**2)

    elapsed = time.time() - t0
    effective_T = (steps - warmup) * dt
    compute_units = n_seeds * (steps - warmup)   # post-warmup compute units

    row = {
        'label': label,
        'A': A,
        'sigma': sigma,
        'n_seeds': n_seeds,
        'steps': steps,
        'warmup': warmup,
        'effective_T_s': effective_T,
        'compute_units': compute_units,
        'I_with': float(np.mean(iw)),
        'I_without': float(np.mean(iwo)),
        'Q_with': float(np.mean(qw)),
        'Q_without': float(np.mean(qwo)),
        'I_mean_diff': I_m,
        'I_se': I_se,
        'z_I': z_I,
        'Q_mean_diff': Q_m,
        'Q_se': Q_se,
        'z_Q': z_Q,
        'T2': T2,
        'vec_mag': float(vec_mag),
        'elapsed_s': elapsed,
    }
    print(f"    {label:16s} A={A:.2f}  n={n_seeds:3d}  T={effective_T:7.0f}s  "
          f"comp={compute_units:>10d}  z_I={z_I:+6.2f}  z_Q={z_Q:+6.2f}  "
          f"T²={T2:6.1f}  [{elapsed:.0f}s]")
    return row


def main():
    start = datetime.now()
    print("=" * 72)
    print("Thor Session #94: The Detection Cliff")
    print(f"Started: {start.isoformat()}")
    print("=" * 72)

    SIGMA = 0.022      # SR peak from S92/S93
    SIGNAL_FREQ = 0.003
    WARMUP = 10_000    # same as S92/S93 (10k steps at dt=0.1 = 1000 s)
    DT = 0.1

    amplitudes = [0.04, 0.08, 0.12, 0.20]

    # Budget grid — base configs (n=16 seeds, T scales)
    # B = 1: 16 × 40k = 640k post-warmup compute (matches S93 baseline)
    # B = 2, 4, 8: increase T proportionally
    base_budgets = [
        (1, 16, 50_000),   # 16 × (50k - 10k warmup) = 640k compute units
        (2, 16, 90_000),   # 16 × 80k = 1.28M
        (4, 16, 170_000),  # 16 × 160k = 2.56M
        (8, 16, 330_000),  # 16 × 320k = 5.12M
    ]

    # Seeds variant at B=4: n=64, T=40k (same compute as B=4 base)
    # 64 × (50k - 10k) = 2.56M compute units — matches B=4 base exactly
    seeds_variant = (4, 64, 50_000)

    print(f"\nFixed: σ={SIGMA}, f_s={SIGNAL_FREQ}, warmup={WARMUP}, dt={DT}")
    print(f"Amplitudes: {amplitudes}")
    print(f"Base budgets (B, n_seeds, steps_total):")
    for b in base_budgets:
        B, n, s = b
        comp = n * (s - WARMUP)
        print(f"   B={B}  n={n:3d}  steps={s:6d}  compute_units={comp:>10d}")
    print(f"Seeds variant @ B=4: n={seeds_variant[1]}, steps={seeds_variant[2]}  "
          f"compute={seeds_variant[1] * (seeds_variant[2] - WARMUP):>10d}")

    total_steps_est = 0
    for A in amplitudes:
        for (B, n, s) in base_budgets:
            total_steps_est += 2 * n * s
        B, n, s = seeds_variant
        total_steps_est += 2 * n * s
    print(f"\nEstimated total simulated steps: {total_steps_est:,}  "
          f"(~{total_steps_est * 25e-6 / 60:.1f} min at 25 µs/step)")

    # ─── Run the grid ───
    results = []
    for A in amplitudes:
        print(f"\n── Amplitude A = {A} ──")
        for (B, n_seeds, steps) in base_budgets:
            label = f"base_B{B}"
            row = run_cell(A, SIGMA, n_seeds, steps, WARMUP,
                           SIGNAL_FREQ, DT, label, seed_offset=int(A*1e6))
            row['budget_B'] = B
            row['config'] = 'base'
            results.append(row)

        # Seeds variant at B=4
        B, n_seeds, steps = seeds_variant
        label = f"seeds_B{B}"
        row = run_cell(A, SIGMA, n_seeds, steps, WARMUP,
                       SIGNAL_FREQ, DT, label,
                       seed_offset=int(A*1e6) + 1_000_000)
        row['budget_B'] = B
        row['config'] = 'seeds_variant'
        results.append(row)

    # ─── Fit scaling law z_I = k · A · √B using base cells only ───
    print("\n" + "=" * 72)
    print("Scaling law fit: z_I = k · A · √B  (vec_z = T / A√B should be flat)")
    print("=" * 72)

    base_rows = [r for r in results if r['config'] == 'base']
    A_arr = np.array([r['A'] for r in base_rows])
    B_arr = np.array([r['budget_B'] for r in base_rows])
    zI_arr = np.array([r['z_I'] for r in base_rows])
    zQ_arr = np.array([r['z_Q'] for r in base_rows])
    T2_arr = np.array([r['T2'] for r in base_rows])
    vec_z = np.sqrt(T2_arr)  # magnitude of the (z_I, z_Q) vector

    # Fit |z_vec| = k · A · √B (can be negative for z_I alone;
    # vector magnitude is more stable)
    predictor = A_arr * np.sqrt(B_arr)
    # Least-squares k:
    k_vec = float(np.sum(vec_z * predictor) / np.sum(predictor**2))
    pred = k_vec * predictor
    residuals = vec_z - pred
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((vec_z - vec_z.mean())**2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    print(f"\n  k_vec = {k_vec:.2f}  (so |z_vec| ≈ {k_vec:.1f} · A · √B)")
    print(f"  R² of fit = {r2:.3f}")
    print(f"  Predicted A_min(z=2) at B=1: {2/k_vec:.3f}")
    print(f"  Predicted A_min(z=2) at B=8: {2/(k_vec * np.sqrt(8)):.3f}")

    # ─── Compare seeds-variant vs long-T at B=4 ───
    print("\n" + "=" * 72)
    print("Long-T vs More-Seeds at matched compute (B=4, 2.56M units each)")
    print("=" * 72)
    for A in amplitudes:
        base_b4 = next(r for r in results
                       if r['A'] == A and r['config'] == 'base'
                       and r['budget_B'] == 4)
        sv = next(r for r in results
                  if r['A'] == A and r['config'] == 'seeds_variant')
        dz_I = sv['z_I'] - base_b4['z_I']
        dT2 = sv['T2'] - base_b4['T2']
        print(f"  A={A:.2f}  long-T (n=16, T=16000): z_I={base_b4['z_I']:+6.2f}"
              f"  T²={base_b4['T2']:6.2f}")
        print(f"         more-N (n=64, T= 4000): z_I={sv['z_I']:+6.2f}"
              f"  T²={sv['T2']:6.2f}")
        print(f"         Δ(more-long): z_I={dz_I:+6.2f}  T²={dT2:+6.2f}")

    # ─── Save ───
    out = {
        'meta': {
            'session': 94,
            'title': 'The Detection Cliff: scaling law for matched-filter SR',
            'started': start.isoformat(),
            'params': {
                'sigma': SIGMA, 'signal_freq': SIGNAL_FREQ,
                'warmup': WARMUP, 'dt': DT, 'amplitudes': amplitudes,
                'base_budgets': base_budgets, 'seeds_variant': seeds_variant,
            },
        },
        'results': results,
        'fit': {
            'k_vec': k_vec, 'r2': r2,
            'A_min_B1_z2': 2/k_vec,
            'A_min_B8_z2': 2/(k_vec * np.sqrt(8)),
        },
    }
    outfile = 'thor_session_94_detection_cliff_results.json'
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print(f"\nSaved → {outfile}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"Total wall time: {elapsed:.0f}s ({elapsed/60:.1f} min)")


if __name__ == '__main__':
    main()
