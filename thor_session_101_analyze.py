#!/usr/bin/env python3
"""S101 analyzer: reads thor_session_101_intrinsic_wander_results.json
and produces a clear numerical summary with verdicts on S100-P2 and S100-P3.

Questions answered:
  Q1 (S100-P3): With A=0, does raw-channel z_k exhibit the ~22ks ACF
               decay S99/S100 saw at A=0.30? If yes → wander is intrinsic
               to the N=4 dynamics. If no → signal-induced.
  Q2 (S100-P2): Does τ_wander(raw) scale as 1/ω_spread across the sweep?
               If yes → wander originates in the spread of individual
               oscillator frequencies (N=4 collective phase drift).
               If invariant → wander has a different deterministic origin.

Outputs:
  1. Part A: full |C_full(m)|, |Φ(m)|, |z|-amp ACF curves for z_raw, z_st
     at A=0. Direct comparison against S100/S98 A=0.30 expectations.
  2. Part B: τ_wander per ω_spread + scaling fit (log τ vs log ω_spread).
  3. Verdicts on S100-P2 and S100-P3.
"""

import json
import numpy as np
import sys
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

RESULTS = Path('thor_session_101_intrinsic_wander_results.json')
S100_RESULTS = Path('thor_session_100_incoherent_drift_results.json')
S98_RESULTS = Path('thor_session_98_phase_drift_results.json')
OUT = Path('thor_session_101_analysis.json')


def load(path):
    with open(path) as f:
        return json.load(f)


def fit_exp(rho, lags_time_s, rho_floor=0.05):
    rho = np.array(rho)
    lags_time_s = np.array(lags_time_s)
    ok = (rho > rho_floor) & (lags_time_s > 0)
    if ok.sum() < 3:
        return None
    y = np.log(rho[ok])
    x = lags_time_s[ok]
    slope, intercept = np.polyfit(x, y, 1)
    tau = -1.0 / slope if slope < 0 else float('inf')
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred)**2))
    ss_tot = float(np.sum((y - y.mean())**2))
    R2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        'tau_s': float(tau), 'R2': float(R2),
        'n_fit': int(ok.sum()),
        'slope': float(slope),
        'intercept': float(intercept),
        'max_lag_s_used': float(x.max()),
    }


def null_floor_estimate(n_seeds, n_chunks, max_lag):
    """Under a true white null and unit circular ACF, expected |Φ(m)|
    for m>0 is approximately 1/√N_pairs where N_pairs ≈ n_seeds·(n_chunks-m).
    Return an array of expected null magnitudes."""
    out = np.zeros(max_lag + 1)
    for m in range(max_lag + 1):
        if m == 0:
            out[m] = 1.0
        else:
            n_pairs = max(1, n_seeds * (n_chunks - m))
            out[m] = 1.0 / np.sqrt(n_pairs)
    return out


def main():
    d = load(RESULTS)
    params = d['meta']['params']
    dt = params['dt']
    T_chunk_s = params['T_chunk_s']

    analysis = {
        'meta': d['meta'],
        'part_a': {},
        'part_b': {},
        'verdicts': {},
    }

    # ─── Part A: A=0 null control ───────────────────────────────────────
    print("=" * 72)
    print("PART A: A=0 null at σ=0.022, ω_spread=0.02, 8 seeds × 400ks")
    print("=" * 72)
    pA = d['part_a']
    pA_params = d['meta']['params']['part_a']
    n_seeds_A = pA_params['n_seeds']
    total_steps_A = pA_params['total_steps']
    n_chunks_A = (total_steps_A - d['meta']['params']['warmup']) // \
                 d['meta']['params']['chunk_steps']
    max_lag_A = pA_params['max_lag']
    null_mag_A = null_floor_estimate(n_seeds_A, n_chunks_A, max_lag_A)

    # Load S100 main (σ=0.060) and S98 main (σ=0.022 A=0.30) for reference
    s100 = load(S100_RESULTS)
    s98 = load(S98_RESULTS)
    # S98 main was σ=0.022 A=0.30 ω_spread=0.02 (default) — direct comparison.
    s98_raw_Phi = np.array([complex(p[0], p[1])
                            for p in s98['main']['raw']['Phi']])
    s98_st_Phi = np.array([complex(p[0], p[1])
                           for p in s98['main']['st']['Phi']])

    print("\n  Parameter match with S98 main: σ=0.022, ω_spread=0.02.")
    print(f"  Only A differs (A=0 here, A=0.30 in S98).")
    print(f"  Expected null |Φ| floor @ lags 1..5 for 8 seeds × 100 chunks:")
    print(f"    {[float(f'{null_mag_A[m]:.3f}') for m in range(1,6)]}\n")

    for ch_key, ch_label in [('raw', 'RAW'), ('st', 'ST')]:
        s = pA[ch_key]
        lags = np.array(s['lags_time_s'])
        C_abs = np.array(s['C_full_abs'])
        Phi_abs = np.array(s['Phi_abs'])
        rho_c = np.array(s['rho_abs_centered'])
        print(f"\n  {ch_label} (A=0):")
        print(f"    mean |z|² = {s['mean_z2']:.3e}  "
              f"(S98 A=0.30: {s98['main'][ch_key]['mean_z2']:.3e})")
        print(f"    |C_full| lag 0..6: "
              f"{[f'{C_abs[m]:.3f}' for m in range(7)]}")
        print(f"    |Φ|     lag 0..6: "
              f"{[f'{Phi_abs[m]:.3f}' for m in range(7)]}")
        print(f"    null-floor       : "
              f"{[f'{null_mag_A[m]:.3f}' for m in range(7)]}")
        # S98 A=0.30 |Φ| lag 0..6 for direct comparison
        s98_Phi = s98_raw_Phi if ch_key == 'raw' else s98_st_Phi
        s98_abs = np.abs(s98_Phi)
        print(f"    S98 A=0.30 |Φ|   : "
              f"{[f'{s98_abs[m]:.3f}' for m in range(7)]}")

        fits = s['fits']
        for name, f in [('C_full', fits['tau_Cfull']),
                        ('|Φ|',    fits['tau_Phi']),
                        ('|z|-amp', fits['tau_rhoabs'])]:
            if f is None:
                print(f"    τ({name}): no fit (never above floor)")
            else:
                print(f"    τ({name}): {f['tau_s']:>8.0f}s "
                      f"R²={f['R2']:.3f} n_fit={f['n_fit']}")

        analysis['part_a'][ch_key] = {
            'lags_time_s': lags.tolist(),
            'C_full_abs': C_abs.tolist(),
            'Phi_abs': Phi_abs.tolist(),
            'rho_abs_centered': rho_c.tolist(),
            'null_floor_estimate': null_mag_A.tolist(),
            'mean_z2_A0': s['mean_z2'],
            'mean_z2_A30_s98': s98['main'][ch_key]['mean_z2'],
            'A30_Phi_abs_s98': s98_abs.tolist(),
            'fits': fits,
        }

    # ─── Part B: ω_spread sweep ─────────────────────────────────────────
    print("\n" + "=" * 72)
    print("PART B: ω_spread ∈ {0, 0.005, 0.02, 0.08} at A=0, σ=0.022")
    print("=" * 72)
    pB = d['part_b']
    pB_params = d['meta']['params']['part_b']
    omegas = sorted([float(k) for k in pB.keys()])
    print(f"\n  {'ω_spread':>10} | {'raw|C_full|':>30} | {'raw|Φ|':>30}")
    print(f"  {'-'*10}-+-{'-'*30}-+-{'-'*30}")
    for om in omegas:
        s = pB[f'{om:.4f}']
        raw = s['raw']
        C_s = ' '.join(f'{x:.2f}'
                       for x in raw['C_full_abs'][:6])
        Phi_s = ' '.join(f'{x:.2f}'
                         for x in raw['Phi_abs'][:6])
        print(f"  {om:>10.4f} | {C_s:>30} | {Phi_s:>30}")

    # Fit τ vs 1/ω_spread
    print(f"\n  {'ω_spread':>10} {'1/ω':>10} {'τ_Cfull':>10} {'τ_|Φ|':>10} "
          f"{'τ_|z|amp':>10}")
    taus_C = []
    taus_Phi = []
    taus_amp = []
    ws = []
    for om in omegas:
        s = pB[f'{om:.4f}']['raw']['fits']
        tC = s['tau_Cfull']['tau_s'] if s['tau_Cfull'] else None
        tP = s['tau_Phi']['tau_s'] if s['tau_Phi'] else None
        tA = s['tau_rhoabs']['tau_s'] if s['tau_rhoabs'] else None
        tC_s = f"{tC:>8.0f}s" if tC and tC < 1e7 else "     n/a"
        tP_s = f"{tP:>8.0f}s" if tP and tP < 1e7 else "     n/a"
        tA_s = f"{tA:>8.0f}s" if tA and tA < 1e7 else "     n/a"
        inv = 1.0/om if om > 0 else float('inf')
        inv_s = f"{inv:>8.1f}" if inv < 1e4 else "     inf"
        print(f"  {om:>10.4f} {inv_s:>10} {tC_s:>10} {tP_s:>10} {tA_s:>10}")
        if om > 0 and tC and tC < 1e7:
            ws.append(om); taus_C.append(tC)
        if om > 0 and tP and tP < 1e7:
            taus_Phi.append(tP)
        if om > 0 and tA and tA < 1e7:
            taus_amp.append(tA)

    # log-log fit τ = A · ω^β, expect β = -1 for 1/Δω scaling
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
        return {'slope': float(slope),
                'intercept': float(intercept),
                'R2': float(R2),
                'tau_at_omega_002': float(np.exp(intercept + slope * np.log(0.02))),
                'n_fit': len(ws)}

    scaling_C = loglog_fit(ws, taus_C)
    # For |Φ| and |z|amp we may not have enough fit points; skip if so.
    ws_phi = [om for om in omegas if om > 0
              and pB[f'{om:.4f}']['raw']['fits']['tau_Phi'] is not None
              and pB[f'{om:.4f}']['raw']['fits']['tau_Phi']['tau_s'] < 1e7]
    taus_phi_fit = [pB[f'{om:.4f}']['raw']['fits']['tau_Phi']['tau_s']
                    for om in ws_phi]
    scaling_Phi = loglog_fit(ws_phi, taus_phi_fit) if len(ws_phi) >= 2 else None

    print("\n  log-log fit of τ_Cfull vs ω_spread (expect slope = -1):")
    if scaling_C:
        print(f"    slope = {scaling_C['slope']:+.2f}  "
              f"R² = {scaling_C['R2']:.3f}  "
              f"predicted τ at ω=0.02: {scaling_C['tau_at_omega_002']:.0f}s  "
              f"(n_fit={scaling_C['n_fit']})")
    else:
        print("    insufficient fit points")
    print("  log-log fit of τ_|Φ| vs ω_spread (expect slope = -1):")
    if scaling_Phi:
        print(f"    slope = {scaling_Phi['slope']:+.2f}  "
              f"R² = {scaling_Phi['R2']:.3f}  "
              f"predicted τ at ω=0.02: {scaling_Phi['tau_at_omega_002']:.0f}s  "
              f"(n_fit={scaling_Phi['n_fit']})")
    else:
        print("    insufficient fit points")

    analysis['part_b'] = {
        'omega_spreads': omegas,
        'scaling_Cfull': scaling_C,
        'scaling_Phi': scaling_Phi,
        'per_omega': {
            f'{om:.4f}': {
                'raw_fits': pB[f'{om:.4f}']['raw']['fits'],
                'st_fits': pB[f'{om:.4f}']['st']['fits'],
                'raw_C_full_abs': pB[f'{om:.4f}']['raw']['C_full_abs'][:20],
                'raw_Phi_abs': pB[f'{om:.4f}']['raw']['Phi_abs'][:20],
                'st_C_full_abs': pB[f'{om:.4f}']['st']['C_full_abs'][:20],
                'st_Phi_abs': pB[f'{om:.4f}']['st']['Phi_abs'][:20],
            } for om in omegas
        },
    }

    # ─── Verdicts ───────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("VERDICTS")
    print("=" * 72)

    # S100-P3: is the wander intrinsic?
    raw_C_abs_A = np.array(pA['raw']['C_full_abs'])
    raw_Phi_abs_A = np.array(pA['raw']['Phi_abs'])
    # Look at C_full(1..5) — if it's comparable to the null floor (≈0.04
    # for n=8 seeds × 100 chunks), wander is absent at A=0.
    # If it's around 0.3-0.5 like A=0.30 regime, wander is intrinsic.
    C_low_lags = raw_C_abs_A[1:6].mean()
    null_floor_mean = null_mag_A[1:6].mean()
    # S98 at A=0.30 had |Φ(1..5)| around 0.34
    s98_raw_low_lags = np.abs(s98_raw_Phi[1:6]).mean()
    print(f"\n  S100-P3 (is the wander intrinsic?):")
    print(f"    A=0 raw |C_full| mean over lags 1..5: {C_low_lags:.3f}")
    print(f"    Null floor (white expected)         : {null_floor_mean:.3f}")
    print(f"    A=0.30 raw |Φ| mean over lags 1..5   : {s98_raw_low_lags:.3f} "
          f"(S98)")
    if C_low_lags > 3 * null_floor_mean and C_low_lags > 0.15:
        verdict_P3 = ("CONFIRMED: A=0 raw ACF shows strong correlations "
                      "above null floor → wander is intrinsic to N=4 dynamics.")
    elif C_low_lags < 2 * null_floor_mean:
        verdict_P3 = ("FALSIFIED: A=0 raw ACF is at null floor → wander "
                      "requires signal drive.")
    else:
        verdict_P3 = ("AMBIGUOUS: A=0 raw ACF between null and signal-regime. "
                      "Likely partial intrinsic component but weaker than "
                      "signal-regime.")
    print(f"  VERDICT: {verdict_P3}")

    # S100-P2: 1/ω_spread scaling?
    if scaling_C:
        slope_C = scaling_C['slope']
        if abs(slope_C + 1.0) < 0.3:
            verdict_P2 = ("CONFIRMED: τ_wander ∝ 1/ω_spread "
                          "(slope ≈ -1) — wander is N=4 collective phase drift.")
        elif abs(slope_C) < 0.3:
            verdict_P2 = ("FALSIFIED: τ_wander is ω_spread-invariant (slope ≈ 0) "
                          "— wander has another deterministic origin "
                          "(coupling, mean-field?).")
        else:
            verdict_P2 = (f"PARTIAL: slope = {slope_C:+.2f} — "
                          "nontrivial ω_spread dependence but not clean 1/Δω.")
    else:
        verdict_P2 = "INSUFFICIENT DATA: ω_spread sweep didn't yield τ fits."
    print(f"\n  S100-P2 (1/Δω scaling?):")
    print(f"  VERDICT: {verdict_P2}")

    analysis['verdicts'] = {
        'S100_P3': {'text': verdict_P3,
                    'raw_C_full_mean_lags_1to5_A0': float(C_low_lags),
                    'null_floor_mean_lags_1to5': float(null_floor_mean),
                    'raw_Phi_mean_lags_1to5_A30_s98': float(s98_raw_low_lags)},
        'S100_P2': {'text': verdict_P2,
                    'scaling_Cfull_slope':
                        scaling_C['slope'] if scaling_C else None,
                    'scaling_Cfull_R2':
                        scaling_C['R2'] if scaling_C else None},
    }

    with open(OUT, 'w') as f:
        json.dump(analysis, f, indent=2, default=float)
    print(f"\n  Analysis saved → {OUT}")


if __name__ == '__main__':
    main()
