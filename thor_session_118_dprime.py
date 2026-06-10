#!/usr/bin/env python3
"""S118 supplement: d′ vs AUC at the detection edge — formalizing S117-P5.

Motivation (S117-P5)
--------------------
S117 showed that a coherent matched filter can keep AUC ≈ 1.0 while its d′
collapses, because the χ²-like detector statistics (T_coh = |Σμ|² and
friends are non-negative, heavy-tailed energy quantities) are NOT Gaussian.
For a Gaussian-null detector, AUC = Φ(d′/√2) exactly; for heavy-tailed
nulls the rank statistic (AUC) and the moment statistic (d′) decouple.

This script makes that quantitative on the S118 detection-edge sweep. For
every (κ_C, A) signal cell vs its paired A=0 null, and every detector in
the ladder, it computes:

  d′            = (⟨T⟩_sig − ⟨T⟩_null) / sqrt(½(var_sig + var_null))
  AUC_meas      = Mann–Whitney rank AUC (the calibrated detectability)
  AUC_gauss     = Φ(d′/√2)                (what AUC *would* be if Gaussian)
  gap           = AUC_meas − AUC_gauss    (non-Gaussianity signature)

and per detector per κ_C fits the small-A scaling exponent of d′:

  d′(A) ≈ c · A^p

A coherent matched filter on a signal of amplitude A has test-statistic
non-centrality λ ∝ A² (signal POWER), so a *Gaussianised* d′ should grow
∝ A² at small A. But the realized d′ on the heavy-tailed energy statistic
need not — and ρ_sig (the effect size) was found to grow as A^1.21 (S111),
not A². Comparing the d′ exponent of the *detector* to the ρ_sig exponent
of the *morphology* separates "how fast does the statistic separate" from
"how fast does the signal phasor grow".

No new simulation — reads the S118 + S117 result JSONs.
"""
import json
import math
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, build_detectors,
)
from thor_session_118_analyze import S118, S117, KC_VALS

# standard normal CDF without scipy
_erf = np.vectorize(math.erf)
def Phi(x):
    return 0.5 * (1.0 + _erf(np.asarray(x, float) / np.sqrt(2.0)))


def dprime(null_vals, sig_vals):
    null_vals = np.asarray(null_vals, float)
    sig_vals = np.asarray(sig_vals, float)
    pooled = 0.5 * (np.var(sig_vals) + np.var(null_vals))
    if pooled <= 0:
        return 0.0
    return float((sig_vals.mean() - null_vals.mean()) / np.sqrt(pooled))


def auc_meas(null_vals, sig_vals):
    null_vals = np.asarray(null_vals)
    sig_vals = np.asarray(sig_vals)
    d = sig_vals[:, None] - null_vals[None, :]
    return (np.sum(d > 0) + 0.5 * np.sum(d == 0)) / d.size


def fit_exponent(a, y):
    """Least-squares log-log slope of y vs a over points with y>0, a>0."""
    a = np.asarray(a, float); y = np.asarray(y, float)
    m = (a > 0) & (y > 0)
    if m.sum() < 2:
        return float('nan'), float('nan')
    la, ly = np.log(a[m]), np.log(y[m])
    A = np.vstack([la, np.ones_like(la)]).T
    slope, intercept = np.linalg.lstsq(A, ly, rcond=None)[0]
    # r²
    pred = A @ np.array([slope, intercept])
    ss_res = np.sum((ly - pred) ** 2)
    ss_tot = np.sum((ly - ly.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return float(slope), float(r2)


def main():
    r118, r117 = load(S118), load(S117)
    if r118 is None or r117 is None:
        print("results missing — run experiment + ensure S117 json present.")
        return

    by_kc = {kc: {} for kc in KC_VALS}
    for src in (r117, r118):
        for cell in src['cells'].values():
            kc = round(cell['kappa_C'], 2)
            if kc in by_kc:
                by_kc[kc][round(cell['signal_amp'], 2)] = cell

    det_order = ['T_coh', 'T_white', 'T_cw_loo']
    out = {}

    for kc in KC_VALS:
        cells = by_kc[kc]
        if 0.0 not in cells:
            print(f"κ_C={kc}: no null cell, skip"); continue
        cn = cells[0.0]
        mu_null = mu_array(cn['per_seed'])
        nsw_null = nsw_array(cn['per_seed'])
        a_sig = sorted(a for a in cells if a > 0.0)

        print(f"\n{'='*100}\nκ_C = {kc}   d′ vs AUC (paired null A=0, {len(cn['per_seed'])} null seeds)")
        print(f"{'A':>5} " + " ".join(
            f"{d+'_d′':>10} {d+'_AUC':>9} {d+'_gap':>7}" for d in det_order))

        rows = []
        for A in a_sig:
            cs = cells[A]
            mu_sig = mu_array(cs['per_seed'])
            nsw_sig = nsw_array(cs['per_seed'])
            det, sig2, phi = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)

            rec = {'A': A}
            line = f"{A:5.2f} "
            for d in det_order:
                nv, sv = det[d]
                dp = dprime(nv, sv)
                am = float(auc_meas(nv, sv))
                ag = float(Phi(dp / np.sqrt(2.0)))
                rec[d] = {'dprime': dp, 'auc_meas': am, 'auc_gauss': ag,
                          'gap': am - ag}
                line += f"{dp:10.3f} {am:9.3f} {am-ag:+7.3f} "
            rows.append(rec)
            print(line)

        # small-A scaling exponent of d′ for each detector (use A ≤ 0.16)
        print(f"  d′(A) ∝ A^p  (small-A fit, A ≤ 0.16):")
        scal = {}
        for d in det_order:
            a_lo = [r['A'] for r in rows if r['A'] <= 0.16]
            y_lo = [r[d]['dprime'] for r in rows if r['A'] <= 0.16]
            p, r2 = fit_exponent(a_lo, y_lo)
            scal[d] = {'exponent': p, 'r2': r2}
            print(f"    {d:>10}: p={p:+.2f}  r²={r2:.3f}")
        out[str(kc)] = {'rows': rows, 'scaling': scal}

    # cross-κ_C synthesis: where does Gaussian mapping break worst?
    print(f"\n{'='*100}\nS117-P5 SUMMARY: max |gap| (AUC_meas − Φ(d′/√2)) per detector per κ_C")
    print("  (large positive gap ⇒ rank-detectability exceeds what d′ implies ⇒ heavy-tailed null)")
    for kc in KC_VALS:
        if str(kc) not in out:
            continue
        rows = out[str(kc)]['rows']
        parts = []
        for d in det_order:
            gaps = [r[d]['gap'] for r in rows]
            imax = int(np.argmax(np.abs(gaps)))
            parts.append(f"{d}:{gaps[imax]:+.3f}@A{rows[imax]['A']:.2f}")
        print(f"  κ_C={kc}: " + "   ".join(parts))

    with open('thor_session_118_dprime_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\n→ thor_session_118_dprime_results.json")


if __name__ == '__main__':
    main()
