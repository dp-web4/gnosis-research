#!/usr/bin/env python3
"""S118 analyzer: detector-ladder AUC vs A at the detection edge.

Stitches the S118 low-A signal cells with the reused S117 anchors
(A=0 null + A=0.40 saturated) at κ_C ∈ {0.30, 0.50, 0.70} to produce a
7-point A curve per κ_C: A ∈ {0, 0.03, 0.06, 0.10, 0.16, 0.24, 0.40}.

For each (κ_C, A>0) signal cell, builds detectors against the matched
κ_C null (A=0) and reports rank-based AUC with bootstrap CIs:

  T_coh     |Σ_k μ_k|²                     naive coherent  (S117 headline)
  T_white   Σ_k |μ_k|²/σ²_k                whitened incoherent (phase-blind)
  T_cw_loo  |Σ_k μ_k e^{-iφ̂_k}/σ²_k|²      realizable whitened-coherent (LOO φ̂)
  N_sw      total switch count             rate channel (signed by sign test)
  Fusion    LDA(log N_sw, T_coh), LOO      2-feature rate⊕timing fusion

T_coh / T_white / T_cw_loo reuse S117's build_detectors verbatim.

Outputs AUC(A) per detector per κ_C, the per-detector detection floor
A50 (smallest A with AUC≥0.90, linearly interpolated), and tests the
three hypotheses (floor-vs-κ_C inversion; ordering inversion at
threshold; N_sw sign-of-usefulness; fusion robustness).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, auc, auc_ci, build_detectors, CLASSES,
)

S118 = 'thor_session_118_detection_edge_results.json'
S117 = 'thor_session_117_class_detector_results.json'
KC_VALS = [0.30, 0.50, 0.70]
AUC_FLOOR = 0.90   # AUC level defining the "detection floor"


def lda_loo_auc(nsw_null, tcoh_null, nsw_sig, tcoh_sig):
    """LOO 2-feature Fisher LDA AUC on (log N_sw, T_coh).

    Pooled within-class covariance, leave-one-out over BOTH classes so no
    sample scores itself. Returns AUC of the projected discriminant.
    """
    def feat(nsw, tcoh):
        return np.column_stack([np.log(np.maximum(nsw, 1.0)), tcoh])

    Xn = feat(nsw_null, tcoh_null)   # class 0
    Xs = feat(nsw_sig, tcoh_sig)     # class 1
    nn, ns = len(Xn), len(Xs)

    def project(train_n, train_s, x):
        mn, ms = train_n.mean(0), train_s.mean(0)
        Sw = (np.cov(train_n.T, bias=True) * len(train_n)
              + np.cov(train_s.T, bias=True) * len(train_s)) / (len(train_n) + len(train_s))
        Sw += 1e-9 * np.eye(2)
        w = np.linalg.solve(Sw, ms - mn)
        return float(x @ w)

    scores_n = np.empty(nn)
    for i in range(nn):
        keep = np.ones(nn, bool); keep[i] = False
        scores_n[i] = project(Xn[keep], Xs, Xn[i])
    scores_s = np.empty(ns)
    for i in range(ns):
        keep = np.ones(ns, bool); keep[i] = False
        scores_s[i] = project(Xn, Xs[keep], Xs[i])
    return auc(scores_n, scores_s)


def interp_floor(a_vals, auc_vals, level=AUC_FLOOR):
    """Smallest A where AUC first reaches `level` (linear interp). None if never."""
    a = np.asarray(a_vals, float); y = np.asarray(auc_vals, float)
    order = np.argsort(a); a, y = a[order], y[order]
    for i in range(1, len(a)):
        if y[i-1] < level <= y[i]:
            t = (level - y[i-1]) / (y[i] - y[i-1])
            return float(a[i-1] + t * (a[i] - a[i-1]))
    if y[0] >= level:
        return float(a[0])
    return None


def main():
    r118, r117 = load(S118), load(S117)
    if r118 is None:
        print("S118 results not found — run thor_session_118_detection_edge.py first.")
        return
    if r117 is None:
        print("S117 results not found — needed for nulls + A=0.40 anchors.")
        return

    # index cells by (kappa_C, A) from both files
    by_kc = {kc: {} for kc in KC_VALS}
    for src in (r117, r118):
        for cell in src['cells'].values():
            kc = round(cell['kappa_C'], 2)
            if kc in by_kc:
                by_kc[kc][round(cell['signal_amp'], 2)] = cell

    det_order = ['T_coh', 'T_white', 'T_cw_loo', 'N_sw', 'Fusion']
    all_rows = {}

    for kc in KC_VALS:
        cells = by_kc[kc]
        if 0.0 not in cells:
            print(f"κ_C={kc}: no null cell, skipping"); continue
        cn = cells[0.0]
        mu_null = mu_array(cn['per_seed'])
        nsw_null = nsw_array(cn['per_seed'])
        a_sig = sorted(a for a in cells if a > 0.0)

        print(f"\n{'='*96}\nκ_C = {kc}   (null seeds={len(cn['per_seed'])})")
        print(f"{'A':>5} {'wedge°':>7} {'<Nsw_s>':>8} {'ρ_sig':>7} " +
              " ".join(f"{d:>9}" for d in det_order))

        rows = []
        for A in a_sig:
            cs = cells[A]
            mu_sig = mu_array(cs['per_seed'])
            nsw_sig = nsw_array(cs['per_seed'])
            det, sig2, phi = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)

            aucs = {}
            aucs['T_coh'] = auc(*det['T_coh'])
            aucs['T_white'] = auc(*det['T_white'])
            aucs['T_cw_loo'] = auc(*det['T_cw_loo'])
            aucs['N_sw'] = auc(nsw_null, nsw_sig)
            aucs['Fusion'] = lda_loo_auc(nsw_null, det['T_coh'][0],
                                         nsw_sig, det['T_coh'][1])
            wedge = cs['summary']['wedge_aL_rN']
            rho = cs['summary']['rho_sig_st_mean']
            nsw_m = cs['summary']['n_sw_total_mean']
            rows.append({'A': A, 'wedge': wedge, 'rho_sig': rho,
                         'nsw_sig_mean': nsw_m, 'nsw_null_mean': float(nsw_null.mean()),
                         'auc': aucs})
            print(f"{A:5.2f} {wedge:7.0f} {nsw_m:8.0f} {rho:7.4f} " +
                  " ".join(f"{aucs[d]:9.3f}" for d in det_order))

        # detection floors per detector (interp to AUC=0.90)
        print(f"  floor A@AUC={AUC_FLOOR}: " + "  ".join(
            f"{d}={interp_floor([x['A'] for x in rows], [x['auc'][d] for x in rows])}"
            for d in det_order))
        all_rows[kc] = rows

    # ---- cross-κ_C hypothesis tests ----
    print(f"\n{'='*96}\nHYPOTHESIS SUMMARY")

    # H1: floor vs κ_C, best-single-detector floor
    print("\nH1 (floor inverts vs A=0.40): per-κ_C floor of best realizable detector")
    floors = {}
    for kc in KC_VALS:
        if kc not in all_rows:
            continue
        rows = all_rows[kc]
        best_floor = {}
        for d in ['T_coh', 'T_white', 'T_cw_loo', 'Fusion']:
            f = interp_floor([x['A'] for x in rows], [x['auc'][d] for x in rows])
            best_floor[d] = f
        valid = {d: f for d, f in best_floor.items() if f is not None}
        bd = min(valid, key=valid.get) if valid else None
        floors[kc] = best_floor
        parts = []
        for d, f in best_floor.items():
            parts.append(f"{d}:{f:.3f}" if f is not None else f"{d}:none")
        tail = f"  → lowest: {bd}={valid[bd]:.3f}" if bd else f"  (none reached {AUC_FLOOR})"
        print(f"  κ_C={kc}: floors {{" + ", ".join(parts) + "}" + tail)

    # H2: ordering inversion — does T_cw_loo beat T_coh at the lowest A?
    print("\nH2 (T_cw_loo beats T_coh near threshold):")
    for kc in KC_VALS:
        if kc not in all_rows:
            continue
        rows = sorted(all_rows[kc], key=lambda x: x['A'])
        lo = rows[0]
        d_cwl = lo['auc']['T_cw_loo'] - lo['auc']['T_coh']
        print(f"  κ_C={kc} @A={lo['A']:.2f}: T_coh={lo['auc']['T_coh']:.3f}  "
              f"T_cw_loo={lo['auc']['T_cw_loo']:.3f}  Δ={d_cwl:+.3f}  "
              f"{'INVERTED' if d_cwl > 0.02 else 'no inversion'}")

    # H3: N_sw sign of usefulness across A
    print("\nH3 (N_sw channel): AUC(N_sw) vs 0.5 across A (anti-informative at ridge?)")
    for kc in KC_VALS:
        if kc not in all_rows:
            continue
        rows = sorted(all_rows[kc], key=lambda x: x['A'])
        seq = "  ".join(f"A{x['A']:.2f}:{x['auc']['N_sw']:.2f}" for x in rows)
        print(f"  κ_C={kc}: {seq}")

    # H4: fusion floor vs single-channel floor
    print("\nH4 (fusion floor-robust): does Fusion floor ≤ min(T_coh, N_sw) floor at every κ_C?")
    for kc in KC_VALS:
        if kc not in all_rows:
            continue
        rows = all_rows[kc]
        A_list = [x['A'] for x in rows]
        f_fus = interp_floor(A_list, [x['auc']['Fusion'] for x in rows])
        f_coh = interp_floor(A_list, [x['auc']['T_coh'] for x in rows])
        f_nsw = interp_floor(A_list, [x['auc']['N_sw'] for x in rows])
        print(f"  κ_C={kc}: Fusion={f_fus}  T_coh={f_coh}  N_sw={f_nsw}")

    out = {'session': 118, 'auc_floor_level': AUC_FLOOR,
           'rows_by_kc': {str(k): v for k, v in all_rows.items()},
           'floors_by_kc': {str(k): v for k, v in floors.items()}}
    with open('thor_session_118_analyze_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\n→ thor_session_118_analyze_results.json")


if __name__ == '__main__':
    main()
