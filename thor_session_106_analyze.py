#!/usr/bin/env python3
"""Thor Session #106 analysis: kappa_C channel isolation.

Pulls in S105 r08_k030 cell as kappa_C=0.15 point and combines with S106's
four kappa_C-variant cells for the primary sweep. Computes:

  - dR_coh/dkappa_C slope at fixed kappa_phase=0.30
  - Comparison against S105's dR_coh/dkappa_phase=+0.94 at ratio 0.8
  - R_kura response to kappa_C (should also be ~flat if phase dynamics
    dominate; a rising R_kura with kappa_C would mean C-coupling
    indirectly tightens phase locking — a different channel story)
  - Null cell diagnostic (kappa_phase=0 should give R ≈ 0)
  - Sanity cell diagnostic (kp=0.10 kC=0.50 vs S105 r08_k005 recycled
    kp=0.05 kC=0.15 — both at ratio 0.8, checks whether kappa_C dependence
    is weaker in weak-coupling regime)

Output: thor_session_106_analysis.json with full comparison table.
"""
import json
import numpy as np


def linfit(xs, ys):
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    A = np.column_stack([xs, np.ones_like(xs)])
    (b, a), *_ = np.linalg.lstsq(A, ys, rcond=None)
    yhat = A @ [b, a]
    ss_res = float(np.sum((ys - yhat)**2))
    ss_tot = float(np.sum((ys - ys.mean())**2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return {'slope': float(b), 'intercept': float(a), 'r2': r2,
            'n': int(len(xs))}


def main():
    s106 = json.load(open('thor_session_106_kappa_c_channel_results.json'))
    s105 = json.load(open('thor_session_105_kappa_strength_results.json'))

    # Recycle S105 r08_k030 as kappa_C=0.15 point (kappa_phase=0.30,
    # omega=0.24, kappa_C=0.15 default).
    r15 = s105['cells']['r08_k030']['summary']

    # Primary sweep rows.
    rows = []
    for kC, label in [
        (0.00, 'kp030_kC000'),
        (0.05, 'kp030_kC005'),
        (0.15, None),  # recycled
        (0.30, 'kp030_kC030'),
        (0.50, 'kp030_kC050'),
    ]:
        if label is None:
            s = r15
            source = 'S105 r08_k030 (recycled)'
        else:
            s = s106['cells'][label]['summary']
            source = f'S106 {label}'
        rows.append({
            'kappa_C': kC,
            'kappa_phase': 0.30,
            'source': source,
            'raw_R': s['raw_R_coh_mean'],
            'raw_R_sd': s['raw_R_coh_std'],
            'st_R': s['st_R_coh_mean'],
            'st_R_sd': s['st_R_coh_std'],
            'R_angle_raw': s['cross_seed_R_angle_raw'],
            'R_angle_st': s['cross_seed_R_angle_st'],
            'R_kura': s['R_kura_cross_seed_mean'],
            'R_kura_sd': s['R_kura_cross_seed_std'],
            'N_sw_median': float(np.median(s['n_sw_per_seed'])),
        })

    # Linear fits on primary sweep.
    kCs = [r['kappa_C'] for r in rows]
    fit_raw = linfit(kCs, [r['raw_R'] for r in rows])
    fit_st = linfit(kCs, [r['st_R'] for r in rows])
    fit_kura = linfit(kCs, [r['R_kura'] for r in rows])

    print("\n" + "=" * 78)
    print("PRIMARY SWEEP: kappa_phase=0.30, omega=0.24 (ratio 0.8), vary kappa_C")
    print("=" * 78)
    print(f"{'kappa_C':>9} {'raw_R':>9}{'±':>3}{'sd':>4} {'st_R':>8}{'±':>3}{'sd':>4} "
          f"{'R_ang_r':>8} {'R_ang_s':>8} {'R_kura':>8} {'N_sw':>6}  source")
    for r in rows:
        print(f"{r['kappa_C']:9.3f} "
              f"{r['raw_R']:9.3f} {'±':>3}{r['raw_R_sd']:4.2f} "
              f"{r['st_R']:8.3f} {'±':>3}{r['st_R_sd']:4.2f} "
              f"{r['R_angle_raw']:8.3f} {r['R_angle_st']:8.3f} "
              f"{r['R_kura']:8.3f} {r['N_sw_median']:6.0f}  {r['source']}")

    print(f"\nLinear fits over kappa_C ∈ {{0.00, 0.05, 0.15, 0.30, 0.50}}, n=5:")
    print(f"  R_raw  = {fit_raw['intercept']:+.4f} + {fit_raw['slope']:+.4f}·kappa_C   (r²={fit_raw['r2']:.3f})")
    print(f"  R_st   = {fit_st['intercept']:+.4f} + {fit_st['slope']:+.4f}·kappa_C   (r²={fit_st['r2']:.3f})")
    print(f"  R_kura = {fit_kura['intercept']:+.4f} + {fit_kura['slope']:+.4f}·kappa_C (r²={fit_kura['r2']:.3f})")
    print(f"\nComparison with S105 dR_raw/dkappa_phase = +0.943 at ratio 0.8:")
    ratio_slope = fit_raw['slope'] / 0.943
    print(f"  dR_raw/dkappa_C / dR_raw/dkappa_phase = {ratio_slope:+.3f}")
    if abs(fit_raw['slope']) < 0.2:
        verdict = "H0 SUPPORTED: kappa_C-insensitive (phase-coupling is the channel)"
    elif fit_raw['slope'] > 0.3:
        verdict = "H1 SUPPORTED: kappa_C also contributes (both channels matter)"
    elif fit_raw['slope'] < -0.3:
        verdict = "H2 SUPPORTED: kappa_C degrades signal (surprising)"
    else:
        verdict = "INTERMEDIATE: partial kappa_C dependence"
    print(f"  Verdict: {verdict}")

    # Null cell
    null = s106['cells']['kp000_kC015_NULL']['summary']
    print("\n" + "=" * 78)
    print("NULL CONTROL: kappa_phase=0.00 (signal has no path to dynamics)")
    print("=" * 78)
    print(f"  RAW R_coh = {null['raw_R_coh_mean']:.4f} ± {null['raw_R_coh_std']:.4f}")
    print(f"  ST  R_coh = {null['st_R_coh_mean']:.4f} ± {null['st_R_coh_std']:.4f}")
    print(f"  R_angle   = {null['cross_seed_R_angle_raw']:.3f} (raw)  / {null['cross_seed_R_angle_st']:.3f} (st)")
    print(f"  R_kura    = {null['R_kura_cross_seed_mean']:.3f} ± {null['R_kura_cross_seed_std']:.3f}")
    # Expected null R_coh with N=50 chunks: ~ 1/(N+1) ~ 0.02. Anything < 0.05 is fine.
    null_ok = (null['raw_R_coh_mean'] < 0.05 and null['st_R_coh_mean'] < 0.1)
    print(f"  Null as expected (R < 0.05 raw, 0.1 st)? {'YES' if null_ok else 'NO — INVESTIGATE'}")

    # Sanity cell vs baseline
    san = s106['cells']['kp010_kC050_ratio08']['summary']
    # Baseline: S105 or S103 r08_k010 (kp=0.10, kC=0.15, omega=0.08)
    base_kp010 = s105['cells']['r08_k015']['summary']  # closest we have — actually kp=0.15. Let's pull S103's kp=0.10 cell
    # Instead: S105 records 'r08_k015' for kp=0.15. For kp=0.10 at ratio 0.8 we need S103 sweep data, but S105
    # doesn't store that. Report kp=0.15 for context and flag.
    print("\n" + "=" * 78)
    print("SANITY: kappa_phase=0.10 kappa_C=0.50 ratio 0.8  vs  S105 r08_k015 (kp=0.15 kC=0.15)")
    print("=" * 78)
    print(f"  S106 kp=0.10 kC=0.50:  RAW R = {san['raw_R_coh_mean']:.3f} ± {san['raw_R_coh_std']:.3f}")
    print(f"                         ST  R = {san['st_R_coh_mean']:.3f} ± {san['st_R_coh_std']:.3f}")
    print(f"                         R_kura= {san['R_kura_cross_seed_mean']:.3f}")
    print(f"  S105 kp=0.15 kC=0.15:  RAW R = {base_kp010['raw_R_coh_mean']:.3f} ± {base_kp010['raw_R_coh_std']:.3f}")
    print(f"                         ST  R = {base_kp010['st_R_coh_mean']:.3f} ± {base_kp010['st_R_coh_std']:.3f}")
    print(f"                         R_kura= {base_kp010['R_kura_cross_seed_mean']:.3f}")

    out = {
        'primary_sweep_rows': rows,
        'linear_fits': {'R_raw_vs_kC': fit_raw,
                        'R_st_vs_kC': fit_st,
                        'R_kura_vs_kC': fit_kura},
        'null_control': {
            'kappa_phase': 0.00, 'kappa_C': 0.15,
            'raw_R': null['raw_R_coh_mean'],
            'raw_R_sd': null['raw_R_coh_std'],
            'st_R': null['st_R_coh_mean'],
            'st_R_sd': null['st_R_coh_std'],
            'R_kura': null['R_kura_cross_seed_mean'],
            'null_ok': null_ok,
        },
        'sanity_cell': {
            's106_kp010_kC050': {
                'raw_R': san['raw_R_coh_mean'],
                'raw_R_sd': san['raw_R_coh_std'],
                'st_R': san['st_R_coh_mean'],
                'st_R_sd': san['st_R_coh_std'],
                'R_kura': san['R_kura_cross_seed_mean'],
            },
            's105_kp015_kC015_ref': {
                'raw_R': base_kp010['raw_R_coh_mean'],
                'raw_R_sd': base_kp010['raw_R_coh_std'],
                'st_R': base_kp010['st_R_coh_mean'],
                'st_R_sd': base_kp010['st_R_coh_std'],
                'R_kura': base_kp010['R_kura_cross_seed_mean'],
            },
        },
        'comparison_to_s105': {
            'dR_dkappa_phase_ratio08_s105': 0.943,
            'dR_dkappa_C_ratio08_s106': fit_raw['slope'],
            'channel_ratio': ratio_slope,
            'verdict': verdict,
        },
    }

    with open('thor_session_106_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    print("\nAnalysis → thor_session_106_analysis.json")


if __name__ == '__main__':
    main()
