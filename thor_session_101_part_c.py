#!/usr/bin/env python3
"""S101 Part C: ω_spread sweep at A=0.30 — where does the 22ks wander come from?

Part A (A=0, ω_spread=0.02) showed the raw-channel chunk-ACF is WHITE at
A=0 — |Φ(m)| ≈ 0.04 (null floor 0.035) for all m>0. The 22ks wander
S99/S100 found is not intrinsic to the free dynamics.

That leaves the question: where does it come from? It emerges only when
the signal is present, so it must live in the forced response. Two
hypotheses:
  H1: N=4 collective phase drift, scales as τ ∝ 1/ω_spread
  H2: something else (bistability transition phase, mean-field wobble) —
      τ invariant in ω_spread

With signal present, the chunk-to-chunk z_raw has a large constant
signal component. To see the wander we compute the RESIDUAL:
    r_k = z_raw_k − mean_seed(z_raw)
and measure the ACF of r_k. That's what S99/S100 measured.

Part C protocol:
  A=0.30, σ=0.022, ω_spread ∈ {0.0, 0.005, 0.02, 0.08}, 4 seeds × 200ks.
  For each seed and channel, compute residual z̃_k = z_k - ⟨z⟩_seed,
  then C_resid(m) = ⟨z̃_k · conj(z̃_{k+m})⟩ / ⟨|z̃_k|²⟩.
  Fit exp(-m·T_chunk/τ) to |C_resid(m)|.

Compute: 4 × 4 × 2,010,000 ≈ 32e6 steps ≈ 13 min.
"""

import numpy as np
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_101_intrinsic_wander import (
    run_long_chunked_omega, fit_tau_from_rho,
)

C_THRESHOLD = 0.55


def residual_complex_autocorr(z_seeds_list, max_lag):
    """Subtract per-seed complex mean (the signal response), then pool
    z̃_k · conj(z̃_{k+m}) across seeds and starting indices.
    Returns dict with |C_resid(m)| and counts per lag."""
    max_lag = int(max_lag)
    num = np.zeros(max_lag + 1, dtype=complex)
    count = np.zeros(max_lag + 1, dtype=int)
    var_acc = 0.0
    n_tot = 0
    for z in z_seeds_list:
        zr = z - z.mean()
        var_acc += float(np.sum(np.abs(zr)**2))
        n_tot += len(zr)
        for m in range(max_lag + 1):
            if m == 0:
                num[0] += np.sum(zr * np.conj(zr))
                count[0] += len(zr)
            else:
                if len(zr) - m <= 0:
                    continue
                num[m] += np.sum(zr[:-m] * np.conj(zr[m:]))
                count[m] += len(zr) - m
    mean_var = var_acc / max(n_tot, 1)
    C_resid = np.zeros(max_lag + 1, dtype=complex)
    for m in range(max_lag + 1):
        if count[m] > 0:
            C_resid[m] = num[m] / count[m] / mean_var
    return {'C_resid_abs': np.abs(C_resid).tolist(),
            'C_resid_arg_deg': np.degrees(np.angle(C_resid)).tolist(),
            'count': count.tolist(),
            'mean_var_resid': float(mean_var)}


if __name__ == '__main__':
    start = datetime.now()
    print("S101 Part C: A=0.30 ω_spread sweep")
    print(f"Started: {start.isoformat()}\n")

    dt = 0.1
    signal_freq = 0.003
    warmup = 10_000
    T_chunk_s = 4000.0
    chunk_steps = int(T_chunk_s / dt)

    SIGMA = 0.022
    A = 0.30
    OMEGAS = [0.0, 0.005, 0.02, 0.08]
    N_SEEDS = 4
    TOTAL_STEPS = warmup + 50 * chunk_steps  # 200,000s
    MAX_LAG = 30

    per_omega = {}
    for om in OMEGAS:
        print(f"\n-- ω_spread={om} --")
        ps = run_long_chunked_omega(
            sigma=SIGMA, A=A, n_seeds=N_SEEDS,
            total_steps=TOTAL_STEPS, warmup=warmup,
            chunk_steps=chunk_steps, omega_spread=om,
            dt=dt, signal_freq=signal_freq,
            seed_base=101_800 + int(om * 1e5))

        lags_time = np.arange(MAX_LAG + 1) * T_chunk_s
        result = {'omega_spread': om, 'A': A, 'sigma': SIGMA,
                  'n_seeds': N_SEEDS, 'total_steps': TOTAL_STEPS,
                  'channels': {}}

        for ch in ('z_raw', 'z_st'):
            z_list = [s[ch] for s in ps]
            per_seed_means = [complex(z.mean().real, z.mean().imag)
                              for z in z_list]
            mean_mag = np.mean([abs(m) for m in per_seed_means])
            ac = residual_complex_autocorr(z_list, MAX_LAG)
            fit = fit_tau_from_rho(ac['C_resid_abs'], lags_time)
            ac['lags_time_s'] = lags_time.tolist()
            ac['per_seed_mean_mag'] = float(mean_mag)
            ac['tau_fit'] = fit
            result['channels'][ch] = ac

            lags_str = ' '.join(f"{x:.3f}" for x in ac['C_resid_abs'][:8])
            mean_mag_s = f"{mean_mag:.3e}"
            fit_s = (f"τ={fit['tau_s']:.0f}s R²={fit['R2']:.2f} "
                     f"n_fit={fit['n_fit']}" if fit else "no fit")
            print(f"   {ch:>6} |⟨z⟩|_seed={mean_mag_s}  "
                  f"|C_resid| lags 0..7 = [{lags_str}]")
            print(f"          {fit_s}")

        per_omega[f'{om:.4f}'] = result

    # ── Scaling fit: τ(raw) vs ω_spread ──
    print("\n" + "=" * 72)
    print("SCALING: τ_raw_residual vs ω_spread (A=0.30)")
    print("=" * 72)
    print(f"  {'ω_spread':>10} {'1/ω':>10} {'τ_raw':>12} {'R²':>6} "
          f"{'τ_st':>12} {'R²_st':>6}")
    ws, taus_raw, taus_st = [], [], []
    for om in OMEGAS:
        r = per_omega[f'{om:.4f}']['channels']
        tR = r['z_raw']['tau_fit']
        tS = r['z_st']['tau_fit']
        tR_s = f"{tR['tau_s']:10.0f}s" if tR else "     n/a"
        tR_R = f"{tR['R2']:5.2f}" if tR else " n/a"
        tS_s = f"{tS['tau_s']:10.0f}s" if tS else "     n/a"
        tS_R = f"{tS['R2']:5.2f}" if tS else " n/a"
        inv = 1/om if om > 0 else float('inf')
        inv_s = f"{inv:10.1f}" if inv < 1e4 else "       inf"
        print(f"  {om:>10.4f} {inv_s:>10} {tR_s:>12} {tR_R:>6} "
              f"{tS_s:>12} {tS_R:>6}")
        if om > 0 and tR and tR['R2'] > 0.3 and tR['tau_s'] < 1e6:
            ws.append(om); taus_raw.append(tR['tau_s'])
        if om > 0 and tS and tS['R2'] > 0.3 and tS['tau_s'] < 1e6:
            taus_st.append(tS['tau_s'])

    # log-log fit
    def loglog_fit(ws, taus):
        if len(ws) < 2:
            return None
        x = np.log(np.array(ws))
        y = np.log(np.array(taus))
        slope, intercept = np.polyfit(x, y, 1)
        pred = slope * x + intercept
        ss_res = float(np.sum((y - pred)**2))
        ss_tot = float(np.sum((y - y.mean())**2))
        R2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return {'slope': float(slope), 'intercept': float(intercept),
                'R2': float(R2), 'tau_at_omega_002':
                    float(np.exp(intercept + slope * np.log(0.02))),
                'n_fit': len(ws)}
    scaling_raw = loglog_fit(ws, taus_raw)
    print("\n  log-log fit τ_raw vs ω_spread (expected -1 for 1/Δω):")
    if scaling_raw:
        print(f"    slope = {scaling_raw['slope']:+.2f}  "
              f"R²={scaling_raw['R2']:.3f}  "
              f"τ_pred(ω=0.02) = {scaling_raw['tau_at_omega_002']:.0f}s  "
              f"(S99/S100 observed: ~22,000s)")
    else:
        print("    insufficient data")

    out = {
        'meta': {'session': 101, 'part': 'C',
                 'title': 'A=0.30 ω_spread sweep — residual wander',
                 'started': start.isoformat(),
                 'params': {
                    'dt': dt, 'signal_freq': signal_freq, 'warmup': warmup,
                    'T_chunk_s': T_chunk_s, 'chunk_steps': chunk_steps,
                    'sigma': SIGMA, 'A': A, 'omega_spreads': OMEGAS,
                    'n_seeds': N_SEEDS, 'total_steps': TOTAL_STEPS,
                    'max_lag': MAX_LAG}},
        'per_omega': per_omega,
        'scaling_raw_residual': scaling_raw,
    }
    with open('thor_session_101_part_c_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")
    print(f"Saved → thor_session_101_part_c_results.json")
