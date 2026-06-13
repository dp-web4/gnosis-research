#!/usr/bin/env python3
"""S119 Part 1: Decompose the T_cw_loo d′(A) inverted-U on EXISTING data.

Context (S118)
--------------
The realizable optimal detector T_cw_loo (whitened-coherent, LOO phase
template) has an *inverted-U* d′(A): d′ rises to a peak near A≈0.06 then
FALLS toward a floor (~3.4 at A=0.40, ridge), while AUC saturates at 1.0
by A≈0.02. The memory attributes the fall to "signal-phasor heterogeneity
inflating signal-class variance" but never pins the mechanism.

This analysis (no new sim) decomposes d′(A) into its numerator and the two
variance components, to test a closed-form model:

  d′(A) = ΔT(A) / sqrt( var_null + ½·β(A)·ΔT(A)² )

  ΔT(A)   = ⟨T⟩_sig − ⟨T⟩_null         (signal energy; the numerator)
  var_null                              (A-independent noise-floor variance)
  β(A)    = (var_sig − var_null)/ΔT²    (signal-energy heterogeneity coeff)

Predictions of the closed form:
  - low A:  var_sig ≈ var_null   ⇒  d′ ≈ ΔT/√var_null  rises  ∝ ΔT
  - high A: if β CONSTANT ⇒ d′ → √(2/β)  (saturates, no fall)
            if β GROWS with A ⇒ d′ FALLS  (the inverted-U)
  So the inverted-U exists IFF dβ/dA > 0. We measure β(A) directly and
  test whether the d′ peak coincides with where var_sig overtakes var_null
  and whether the high-A fall tracks β growth.

Reads S117 (anchors A∈{0,0.40}) + S118 main (A∈{0.03..0.24}) + S118 lowA
(A∈{0.005..0.025}). Builds T_cw_loo via the S117 detector ladder exactly.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, build_detectors,
)

S117 = 'thor_session_117_class_detector_results.json'
S118_MAIN = 'thor_session_118_detection_edge_results.json'
S118_LOWA = 'thor_session_118_lowA_results.json'
KC_VALS = [0.30, 0.70]
DET = 'T_cw_loo'


def gather():
    by_kc = {kc: {} for kc in KC_VALS}
    for path in (S117, S118_MAIN, S118_LOWA):
        r = load(path)
        if r is None:
            print(f"missing {path}"); continue
        for cell in r['cells'].values():
            kc = round(cell['kappa_C'], 2)
            if kc in by_kc:
                by_kc[kc][round(cell['signal_amp'], 4)] = cell
    return by_kc


def dprime(nv, sv):
    nv = np.asarray(nv, float); sv = np.asarray(sv, float)
    pooled = 0.5 * (np.var(sv) + np.var(nv))
    return float((sv.mean() - nv.mean()) / np.sqrt(pooled)) if pooled > 0 else 0.0


def auc_meas(nv, sv):
    nv = np.asarray(nv); sv = np.asarray(sv)
    d = sv[:, None] - nv[None, :]
    return float((np.sum(d > 0) + 0.5 * np.sum(d == 0)) / d.size)


def main():
    by_kc = gather()
    out = {}
    for kc in KC_VALS:
        cells = by_kc[kc]
        if 0.0 not in cells:
            print(f"κ_C={kc}: no null"); continue
        cn = cells[0.0]
        mu_null = mu_array(cn['per_seed'])
        nsw_null = nsw_array(cn['per_seed'])
        var_null_ref = None
        a_sig = sorted(a for a in cells if a > 0.0)

        print(f"\n{'='*108}")
        print(f"κ_C = {kc}   detector = {DET}   ({len(cn['per_seed'])} null seeds)")
        print(f"{'A':>6} {'d′':>8} {'AUC':>6} {'ΔT':>11} {'var_null':>11} "
              f"{'var_sig':>11} {'XV=vs-vn':>11} {'β=XV/ΔT²':>10} {'√(2/β)':>8} {'CV_sig':>7}")
        rows = []
        for A in a_sig:
            cs = cells[A]
            mu_sig = mu_array(cs['per_seed'])
            nsw_sig = nsw_array(cs['per_seed'])
            det, _, _ = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
            nv, sv = det[DET]
            nv = np.asarray(nv, float); sv = np.asarray(sv, float)
            var_null = float(np.var(nv))
            var_sig = float(np.var(sv))
            if var_null_ref is None:
                var_null_ref = var_null
            dT = float(sv.mean() - nv.mean())
            xv = var_sig - var_null
            beta = xv / dT**2 if dT > 0 else float('nan')
            floor = np.sqrt(2.0 / beta) if beta > 0 else float('nan')
            cv_sig = float(sv.std() / sv.mean()) if sv.mean() > 0 else float('nan')
            dp = dprime(nv, sv)
            am = auc_meas(nv, sv)
            rows.append({'A': A, 'dprime': dp, 'auc': am, 'dT': dT,
                         'var_null': var_null, 'var_sig': var_sig,
                         'xv': xv, 'beta': beta, 'floor': floor, 'cv_sig': cv_sig})
            print(f"{A:6.3f} {dp:8.2f} {am:6.3f} {dT:11.1f} {var_null:11.1f} "
                  f"{var_sig:11.1f} {xv:11.1f} {beta:10.4f} {floor:8.2f} {cv_sig:7.3f}")

        # locate empirical d′ peak and the var crossover
        ds = np.array([r['dprime'] for r in rows])
        As = np.array([r['A'] for r in rows])
        ipk = int(np.argmax(ds))
        # crossover: first A where var_sig > 2*var_null (signal var dominates noise)
        xover = None
        for r in rows:
            if r['var_sig'] > 2 * r['var_null']:
                xover = r['A']; break
        print(f"  → d′ peak at A={As[ipk]:.3f} (d′={ds[ipk]:.2f}); "
              f"var_sig>2·var_null first at A={xover}")
        # is β growing across the falling limb (A >= peak)?
        fall = [r for r in rows if r['A'] >= As[ipk]]
        if len(fall) >= 2:
            bf = np.array([r['beta'] for r in fall])
            af = np.array([r['A'] for r in fall])
            m = (bf > 0)
            if m.sum() >= 2:
                slope = np.polyfit(np.log(af[m]), np.log(bf[m]), 1)[0]
                print(f"  → β(A) on falling limb: log-log slope = {slope:+.2f} "
                      f"(>0 ⇒ heterogeneity grows ⇒ d′ falls)")
        out[str(kc)] = {'rows': rows, 'peak_A': float(As[ipk]),
                        'peak_dprime': float(ds[ipk]), 'xover_A': xover}

    with open('thor_session_119_dprime_decomp_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\n→ thor_session_119_dprime_decomp_results.json")


if __name__ == '__main__':
    main()
