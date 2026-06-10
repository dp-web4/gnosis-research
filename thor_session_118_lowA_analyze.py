#!/usr/bin/env python3
"""S118 low-A analyzer: resolve the true floor of the optimal detector.

The main S118 analyzer rounds signal_amp to 2 decimals, which collapses the
sub-0.03 grid. This script keeps full precision and stitches:

  A = 0                 (S117 paired null, per κ_C)
  A ∈ {0.005 … 0.025}   (S118 low-A extension, this session)
  A ∈ {0.03 … 0.40}     (main S118 grid + S117 anchor)

into one fine A-curve per κ_C, builds the S117 detector ladder verbatim, and
reports AUC + d′ for T_coh / T_white / T_cw_loo, the interpolated floor
(smallest A with AUC ≥ 0.90), and the H1 floor-inversion verdict resolved at
the true (sub-0.03) floor of the realizable optimal detector T_cw_loo.
"""
import json
import math
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, auc, build_detectors,
)

S117 = 'thor_session_117_class_detector_results.json'
S118 = 'thor_session_118_detection_edge_results.json'
S118LOW = 'thor_session_118_lowA_results.json'
KC_VALS = [0.30, 0.50, 0.70]
AUC_FLOOR = 0.90

_erf = np.vectorize(math.erf)
def Phi(x):
    return 0.5 * (1.0 + _erf(np.asarray(x, float) / np.sqrt(2.0)))


def dprime(nv, sv):
    nv = np.asarray(nv, float); sv = np.asarray(sv, float)
    pooled = 0.5 * (np.var(sv) + np.var(nv))
    return float((sv.mean() - nv.mean()) / np.sqrt(pooled)) if pooled > 0 else 0.0


def interp_floor(a_vals, auc_vals, level=AUC_FLOOR):
    a = np.asarray(a_vals, float); y = np.asarray(auc_vals, float)
    order = np.argsort(a); a, y = a[order], y[order]
    for i in range(1, len(a)):
        if y[i-1] < level <= y[i]:
            t = (level - y[i-1]) / (y[i] - y[i-1])
            return float(a[i-1] + t * (a[i] - a[i-1]))
    if y[0] >= level:
        return float(a[0])   # already detecting at the lowest A → floor below grid
    return None


def main():
    srcs = [load(S117), load(S118), load(S118LOW)]
    if any(s is None for s in srcs):
        missing = [n for n, s in zip((S117, S118, S118LOW), srcs) if s is None]
        print("missing:", missing); return

    # index by (κ_C, exact A at 3-dp)
    by_kc = {kc: {} for kc in KC_VALS}
    for src in srcs:
        for cell in src['cells'].values():
            kc = round(cell['kappa_C'], 2)
            if kc in by_kc:
                by_kc[kc][round(cell['signal_amp'], 3)] = cell

    det_order = ['T_coh', 'T_white', 'T_cw_loo']
    out = {}
    floors = {}

    for kc in KC_VALS:
        cells = by_kc[kc]
        if 0.0 not in cells:
            print(f"κ_C={kc}: no null"); continue
        cn = cells[0.0]
        mu_null = mu_array(cn['per_seed']); nsw_null = nsw_array(cn['per_seed'])
        a_sig = sorted(a for a in cells if a > 0.0)

        print(f"\n{'='*100}\nκ_C = {kc}   fine A-curve (null seeds={len(cn['per_seed'])})")
        print(f"{'A':>6} {'wedge°':>7} {'<Nsw>':>7} " +
              " ".join(f"{d+'.AUC':>11} {d+'.dʹ':>7}" for d in det_order) +
              f" {'N_sw.AUC':>9}")

        rows = []
        for A in a_sig:
            cs = cells[A]
            mu_sig = mu_array(cs['per_seed']); nsw_sig = nsw_array(cs['per_seed'])
            det, sig2, phi = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
            rec = {'A': A, 'wedge': cs['summary']['wedge_aL_rN'],
                   'nsw': cs['summary']['n_sw_total_mean'], 'auc': {}, 'dp': {}}
            for d in det_order:
                nv, sv = det[d]
                rec['auc'][d] = auc(nv, sv); rec['dp'][d] = dprime(nv, sv)
            rec['auc']['N_sw'] = auc(nsw_null, nsw_sig)
            rows.append(rec)
            print(f"{A:6.3f} {rec['wedge']:7.0f} {rec['nsw']:7.0f} " +
                  " ".join(f"{rec['auc'][d]:11.3f} {rec['dp'][d]:7.2f}" for d in det_order) +
                  f" {rec['auc']['N_sw']:9.3f}")

        fl = {d: interp_floor([r['A'] for r in rows], [r['auc'][d] for r in rows])
              for d in det_order + ['N_sw']}
        floors[kc] = fl
        print("  floor A@AUC=0.90: " +
              "  ".join(f"{d}={fl[d]:.4f}" if fl[d] is not None else f"{d}=<below"
                        for d in det_order + ['N_sw']))
        out[str(kc)] = {'rows': rows, 'floors': fl}

    # ---- H1 resolved at the true floor ----
    print(f"\n{'='*100}\nH1 RESOLVED — floor of realizable optimal detector T_cw_loo vs κ_C")
    seq = []
    for kc in KC_VALS:
        f = floors.get(kc, {}).get('T_cw_loo')
        seq.append((kc, f))
        print(f"  κ_C={kc}: T_cw_loo floor = " +
              (f"{f:.4f}" if f is not None else "<below grid (AUC≥0.9 at A=0.005)>"))
    resolved = [f for _, f in seq if f is not None]
    if len(resolved) == len(seq) and len(seq) >= 2:
        inv = resolved[-1] > resolved[0]
        print(f"  → floor {'RISES' if inv else 'does NOT rise'} ridge→over-coupled "
              f"({resolved[0]:.4f} → {resolved[-1]:.4f})  "
              f"H1 {'CONFIRMED at sub-0.03' if inv else 'FALSIFIED'}")
    else:
        print("  → at least one κ_C floor still below A=0.005 — push lower to resolve H1.")

    with open('thor_session_118_lowA_analyze_results.json', 'w') as f:
        json.dump({'floors_by_kc': {str(k): v for k, v in floors.items()},
                   'rows_by_kc': out}, f, indent=2, default=float)
    print("\n→ thor_session_118_lowA_analyze_results.json")


if __name__ == '__main__':
    main()
