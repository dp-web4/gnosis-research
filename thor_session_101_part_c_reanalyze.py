#!/usr/bin/env python3
"""S101 Part C reanalysis using S99's linear-Δω phase-residual method.

Per seed:
  1. Extract per-chunk phase φ_k = arg(z_k).
  2. Fit linear Δω: φ_k = φ_0 + Δω · k · T_chunk (unwrapped).
  3. Residual φ̃_k = φ_k - (φ_0 + Δω·k·T_chunk).
  4. ACF of residual phase (on unit circle: ⟨exp(i·(φ̃_k − φ̃_{k+m}))⟩).
Then fit exp(-m·T_chunk/τ) to the ACF.

Compare τ(ω_spread) to S99's 21,040s at σ=0.022 A=0.30 ω_spread=0.02.
"""

import json
import numpy as np
import sys

sys.stdout.reconfigure(line_buffering=True)


def phase_residual_acf(z_list, max_lag, T_chunk_s):
    """Per seed: linear-Δω fit then circular ACF of residual."""
    per_seed_results = []
    # Pool circular ACF across seeds
    num_circ = np.zeros(max_lag + 1, dtype=complex)
    count = np.zeros(max_lag + 1, dtype=int)

    for z in z_list:
        phi = np.unwrap(np.angle(z))
        k = np.arange(len(phi))
        # fit phi = phi_0 + Δω·k·T_chunk
        dw_per_chunk, phi0 = np.polyfit(k, phi, 1)
        pred = phi0 + dw_per_chunk * k
        resid = phi - pred
        resid_rms = float(np.std(resid))
        # circular ACF of residual
        u = np.exp(1j * resid)
        for m in range(max_lag + 1):
            if m == 0:
                num_circ[0] += np.sum(u * np.conj(u))
                count[0] += len(u)
            else:
                if len(u) - m <= 0:
                    continue
                num_circ[m] += np.sum(u[:-m] * np.conj(u[m:]))
                count[m] += len(u) - m
        per_seed_results.append({
            'dw_per_chunk': float(dw_per_chunk),
            'dw_per_s': float(dw_per_chunk / T_chunk_s),
            'phi0': float(phi0),
            'resid_rms_rad': resid_rms,
            'n_chunks': int(len(phi)),
        })

    acf = np.zeros(max_lag + 1, dtype=complex)
    for m in range(max_lag + 1):
        if count[m] > 0:
            acf[m] = num_circ[m] / count[m]
    return {
        'abs_acf': np.abs(acf).tolist(),
        'arg_acf_deg': np.degrees(np.angle(acf)).tolist(),
        'count': count.tolist(),
        'per_seed': per_seed_results,
    }


def fit_tau(rho, lags_time_s, floor=0.05):
    rho = np.array(rho)
    lags = np.array(lags_time_s)
    ok = (rho > floor) & (lags > 0)
    if ok.sum() < 3:
        return None
    y = np.log(rho[ok])
    x = lags[ok]
    slope, intercept = np.polyfit(x, y, 1)
    tau = -1.0 / slope if slope < 0 else float('inf')
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred)**2))
    ss_tot = float(np.sum((y - y.mean())**2))
    R2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {'tau_s': float(tau), 'R2': float(R2),
            'n_fit': int(ok.sum()), 'slope': float(slope),
            'max_lag_s': float(x.max())}


def main():
    # Load Part C per-seed data. Part C didn't store raw per-seed z;
    # load from the simulation log instead via cached JSON. But we only
    # saved C_resid in Part C... let me re-load from fresh.
    # ACTUALLY: Part C saved 'C_resid_abs' and 'per_seed_mean_mag' only.
    # So we need to re-run Part C to keep per-seed z for this analysis.
    # Instead, use Part A's A=0 data for baseline and S98's A=0.30 data
    # for Part C equivalent (ω_spread=0.02, which is what S98 used).
    print("Loading S98 main data (σ=0.022, A=0.30, ω_spread=0.02, 8×100chunks)")
    with open('thor_session_98_phase_drift_results.json') as f:
        s98 = json.load(f)
    T_chunk_s = s98['meta']['params']['T_chunk_s']
    # per-seed z_raw and z_st as complex
    z_raws = []
    z_sts = []
    for s in s98['main']['per_seed']:
        z_raws.append(np.array([complex(p[0], p[1]) for p in s['z_raw']]))
        z_sts.append(np.array([complex(p[0], p[1]) for p in s['z_st']]))

    print(f"  {len(z_raws)} seeds × {len(z_raws[0])} chunks each")
    MAX_LAG = 30

    for ch_label, z_list in (('RAW', z_raws), ('ST', z_sts)):
        print(f"\n--- {ch_label} channel ---")
        r = phase_residual_acf(z_list, MAX_LAG, T_chunk_s)
        lags = np.arange(MAX_LAG + 1) * T_chunk_s
        dw_s = [f"{p['dw_per_s']:+.2e}" for p in r['per_seed']]
        rms_s = [f"{p['resid_rms_rad']:.3f}" for p in r['per_seed']]
        print(f"  per-seed Δω (rad/s): {dw_s}")
        print(f"  per-seed resid RMS (rad): {rms_s}")
        abs_acf = r['abs_acf']
        print(f"  |ACF_resid| lags 0..10: "
              f"[{', '.join(f'{v:.3f}' for v in abs_acf[:11])}]")
        fit = fit_tau(abs_acf, lags)
        if fit:
            print(f"  τ fit: {fit['tau_s']:.0f}s  R²={fit['R2']:.3f}  "
                  f"n_fit={fit['n_fit']}  (S99 reported 21,040s for RAW)")
        else:
            print(f"  τ fit: no fit above floor")

    # Now do the same for Part A's A=0 data
    print("\n\nLoading S101 Part A (A=0, σ=0.022, ω_spread=0.02, 8×100)")
    with open('thor_session_101_intrinsic_wander_results.json') as f:
        s101 = json.load(f)
    z_raws_A0 = []
    z_sts_A0 = []
    for s in s101['part_a']['per_seed']:
        z_raws_A0.append(np.array([complex(p[0], p[1]) for p in s['z_raw']]))
        z_sts_A0.append(np.array([complex(p[0], p[1]) for p in s['z_st']]))
    print(f"  {len(z_raws_A0)} seeds × {len(z_raws_A0[0])} chunks each")
    for ch_label, z_list in (('RAW(A=0)', z_raws_A0),
                             ('ST(A=0)', z_sts_A0)):
        print(f"\n--- {ch_label} ---")
        r = phase_residual_acf(z_list, MAX_LAG, T_chunk_s)
        lags = np.arange(MAX_LAG + 1) * T_chunk_s
        abs_acf = r['abs_acf']
        dw_list = [p['dw_per_s'] for p in r['per_seed']]
        rms_list = [p['resid_rms_rad'] for p in r['per_seed']]
        print(f"  per-seed Δω (rad/s): {[f'{v:+.2e}' for v in dw_list]}")
        print(f"  per-seed resid RMS (rad): {[f'{v:.3f}' for v in rms_list]}")
        print(f"  |ACF_resid| lags 0..10: "
              f"[{', '.join(f'{v:.3f}' for v in abs_acf[:11])}]")
        fit = fit_tau(abs_acf, lags)
        if fit:
            print(f"  τ fit: {fit['tau_s']:.0f}s  R²={fit['R2']:.3f}  "
                  f"n_fit={fit['n_fit']}")
        else:
            print(f"  τ fit: no fit above floor")

    # Summary comparison
    print("\n" + "=" * 72)
    print("COMPARISON (A=0 vs A=0.30), all with σ=0.022, ω_spread=0.02")
    print("=" * 72)
    # RAW: A=0 vs A=0.30
    r_A30 = phase_residual_acf(z_raws, MAX_LAG, T_chunk_s)
    r_A00 = phase_residual_acf(z_raws_A0, MAX_LAG, T_chunk_s)
    s_A30 = phase_residual_acf(z_sts, MAX_LAG, T_chunk_s)
    s_A00 = phase_residual_acf(z_sts_A0, MAX_LAG, T_chunk_s)
    lags = np.arange(MAX_LAG + 1) * T_chunk_s

    print("\nRAW channel, phase-residual ACF (linear Δω subtracted):")
    print(f"  A=0.00:  lags 0..8: "
          f"{[float(f'{v:.3f}') for v in r_A00['abs_acf'][:9]]}")
    print(f"  A=0.30:  lags 0..8: "
          f"{[float(f'{v:.3f}') for v in r_A30['abs_acf'][:9]]}")
    f_A00 = fit_tau(r_A00['abs_acf'], lags)
    f_A30 = fit_tau(r_A30['abs_acf'], lags)
    print(f"  A=0.00 τ: {f_A00['tau_s']:.0f}s R²={f_A00['R2']:.3f}"
          if f_A00 else "  A=0.00: no τ fit")
    print(f"  A=0.30 τ: {f_A30['tau_s']:.0f}s R²={f_A30['R2']:.3f}"
          if f_A30 else "  A=0.30: no τ fit")
    print("\nST channel, phase-residual ACF:")
    print(f"  A=0.00:  lags 0..8: "
          f"{[float(f'{v:.3f}') for v in s_A00['abs_acf'][:9]]}")
    print(f"  A=0.30:  lags 0..8: "
          f"{[float(f'{v:.3f}') for v in s_A30['abs_acf'][:9]]}")
    f_s00 = fit_tau(s_A00['abs_acf'], lags)
    f_s30 = fit_tau(s_A30['abs_acf'], lags)
    print(f"  A=0.00 τ: {f_s00['tau_s']:.0f}s R²={f_s00['R2']:.3f}"
          if f_s00 else "  A=0.00: no τ fit")
    print(f"  A=0.30 τ: {f_s30['tau_s']:.0f}s R²={f_s30['R2']:.3f}"
          if f_s30 else "  A=0.30: no τ fit")

    out = {
        'RAW_A0':  {'abs_acf': r_A00['abs_acf'],
                    'per_seed_dw': [p['dw_per_s']
                                    for p in r_A00['per_seed']],
                    'per_seed_resid_rms':
                        [p['resid_rms_rad'] for p in r_A00['per_seed']],
                    'tau_fit': f_A00},
        'RAW_A30': {'abs_acf': r_A30['abs_acf'],
                    'per_seed_dw': [p['dw_per_s']
                                    for p in r_A30['per_seed']],
                    'per_seed_resid_rms':
                        [p['resid_rms_rad'] for p in r_A30['per_seed']],
                    'tau_fit': f_A30},
        'ST_A0':   {'abs_acf': s_A00['abs_acf'],
                    'per_seed_dw': [p['dw_per_s']
                                    for p in s_A00['per_seed']],
                    'per_seed_resid_rms':
                        [p['resid_rms_rad'] for p in s_A00['per_seed']],
                    'tau_fit': f_s00},
        'ST_A30':  {'abs_acf': s_A30['abs_acf'],
                    'per_seed_dw': [p['dw_per_s']
                                    for p in s_A30['per_seed']],
                    'per_seed_resid_rms':
                        [p['resid_rms_rad'] for p in s_A30['per_seed']],
                    'tau_fit': f_s30},
        'T_chunk_s': T_chunk_s,
        'lags_time_s': lags.tolist(),
    }
    with open('thor_session_101_part_c_reanalysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nSaved → thor_session_101_part_c_reanalysis.json")


if __name__ == '__main__':
    main()
