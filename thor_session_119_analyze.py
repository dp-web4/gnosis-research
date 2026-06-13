#!/usr/bin/env python3
"""S119 analyzer: does ω-detuning drive the T_cw_loo d′ inverted-U?

Stitches three ω_std series at κ_C=0.30:
  ω_std=0.00, 0.13  -> thor_session_119_omega_heterogeneity_results.json (NEW)
  ω_std=0.07        -> S117 (A∈{0,0.40}) + S118 main + S118 lowA (existing)

For each ω_std, on the COMMON A grid {0, 0.02, 0.06, 0.16, 0.40} it builds
T_cw_loo via the S117 detector ladder and computes d′, AUC, CV_sig and the
closed-form check d′ ≈ √2/CV_sig. Tests:
  H1 ω_std=0 suppresses the high-A d′ fall (monotone rise→saturate).
  H2 high-A d′ and inverted-U depth order ω_std=0.00 < 0.07 < 0.13.
  H3 AUC≈1 across the edge for every ω_std (margin robust); d′≈√2/CV holds.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, build_detectors,
)

S119 = 'thor_session_119_omega_heterogeneity_results.json'
S117 = 'thor_session_117_class_detector_results.json'
S118_MAIN = 'thor_session_118_detection_edge_results.json'
S118_LOWA = 'thor_session_118_lowA_results.json'

KC = 0.30
DET = 'T_cw_loo'
COMMON_A = [0.02, 0.06, 0.16, 0.40]   # signal A's present in all three series
ROOT2 = np.sqrt(2.0)


def gather():
    """by_omstd[omstd][A] = cell, all at κ_C=0.30."""
    by = {}
    r119 = load(S119)
    if r119 is not None:
        for cell in r119['cells'].values():
            if round(cell['kappa_C'], 2) == KC:
                by.setdefault(round(cell['omega_std'], 2), {})[round(cell['signal_amp'], 4)] = cell
    # ω_std=0.07 stitched from S117 + S118
    for path in (S117, S118_MAIN, S118_LOWA):
        r = load(path)
        if r is None:
            continue
        for cell in r['cells'].values():
            if round(cell['kappa_C'], 2) == KC and round(cell.get('omega_std', 0.07), 2) == 0.07:
                by.setdefault(0.07, {})[round(cell['signal_amp'], 4)] = cell
    return by


def dprime(nv, sv):
    nv = np.asarray(nv, float); sv = np.asarray(sv, float)
    pooled = 0.5 * (np.var(sv) + np.var(nv))
    return float((sv.mean() - nv.mean()) / np.sqrt(pooled)) if pooled > 0 else 0.0


def auc_meas(nv, sv):
    nv = np.asarray(nv); sv = np.asarray(sv)
    d = sv[:, None] - nv[None, :]
    return float((np.sum(d > 0) + 0.5 * np.sum(d == 0)) / d.size)


def curve_for(cells):
    """Return list of row dicts over COMMON_A for the T_cw_loo detector."""
    cn = cells[0.0]
    mu_null = mu_array(cn['per_seed']); nsw_null = nsw_array(cn['per_seed'])
    rows = []
    for A in COMMON_A:
        if A not in cells:
            continue
        cs = cells[A]
        mu_sig = mu_array(cs['per_seed']); nsw_sig = nsw_array(cs['per_seed'])
        det, _, _ = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
        nv, sv = det[DET]
        nv = np.asarray(nv, float); sv = np.asarray(sv, float)
        cv = float(sv.std() / sv.mean()) if sv.mean() > 0 else float('nan')
        rows.append({
            'A': A, 'dprime': dprime(nv, sv), 'auc': auc_meas(nv, sv),
            'cv_sig': cv, 'dprime_pred': ROOT2 / cv if cv > 0 else float('nan'),
            'var_null': float(np.var(nv)), 'var_sig': float(np.var(sv)),
            'mean_null': float(nv.mean()), 'mean_sig': float(sv.mean()),
            'rkura': cs['summary']['kura_mean_mean'],
            'nsw': cs['summary']['n_sw_total_mean'],
        })
    return rows


def main():
    by = gather()
    have = sorted(by.keys())
    print(f"ω_std series available at κ_C={KC}: {have}")
    out = {}
    for omstd in have:
        cells = by[omstd]
        if 0.0 not in cells:
            print(f"ω_std={omstd}: no null cell, skip"); continue
        rows = curve_for(cells)
        out[str(omstd)] = rows
        print(f"\n{'='*96}")
        print(f"ω_std = {omstd:.2f}   κ_C={KC}   detector={DET}   "
              f"ω={np.round(cells[0.0]['omega_vec'],3).tolist()}")
        print(f"{'A':>6} {'d′':>8} {'√2/CV':>8} {'AUC':>7} {'CV_sig':>7} "
              f"{'R_kura':>7} {'<Nsw>':>7}")
        for r in rows:
            print(f"{r['A']:6.3f} {r['dprime']:8.2f} {r['dprime_pred']:8.2f} "
                  f"{r['auc']:7.3f} {r['cv_sig']:7.3f} {r['rkura']:7.3f} {r['nsw']:7.0f}")

    # ---- H1/H2: high-A d′ and inverted-U depth vs ω_std ----
    print(f"\n{'='*96}\nH1/H2: inverted-U depth (d′_peak / d′_@0.40) vs ω_std")
    print(f"{'ω_std':>7} {'d′_peak':>9} {'A_peak':>7} {'d′@0.40':>9} {'depth=pk/hi':>12} "
          f"{'CV@0.06':>8} {'CV@0.40':>8}")
    summ = []
    for omstd in have:
        if str(omstd) not in out:
            continue
        rows = out[str(omstd)]
        dps = np.array([r['dprime'] for r in rows])
        As = np.array([r['A'] for r in rows])
        ipk = int(np.argmax(dps))
        hi = next((r for r in rows if r['A'] == 0.40), None)
        cv006 = next((r['cv_sig'] for r in rows if r['A'] == 0.06), float('nan'))
        cv040 = hi['cv_sig'] if hi else float('nan')
        depth = dps[ipk] / hi['dprime'] if hi and hi['dprime'] > 0 else float('nan')
        summ.append({'omega_std': omstd, 'd_peak': float(dps[ipk]),
                     'A_peak': float(As[ipk]), 'd_hi': hi['dprime'] if hi else None,
                     'depth': float(depth), 'cv006': cv006, 'cv040': cv040})
        print(f"{omstd:7.2f} {dps[ipk]:9.2f} {As[ipk]:7.3f} "
              f"{(hi['dprime'] if hi else float('nan')):9.2f} {depth:12.2f} "
              f"{cv006:8.3f} {cv040:8.3f}")

    print("\nH1: ω_std=0 should give depth≈1 (no fall). "
          "H2: depth should increase with ω_std.")
    with open('thor_session_119_analyze_results.json', 'w') as f:
        json.dump({'curves': out, 'summary': summ, 'common_A': COMMON_A}, f,
                  indent=2, default=float)
    print("→ thor_session_119_analyze_results.json")


if __name__ == '__main__':
    main()
