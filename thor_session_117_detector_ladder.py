#!/usr/bin/env python3
"""S117 supplement: a realizable detector ladder for the over-coupled regime.

Motivation
----------
The base analyzer (thor_session_117_analyze.py) compares:
  T_coh   = |Σ_k μ_k|²        naive coherent  (current ρ_sig·N_sw)
  T_incoh = Σ_k |μ_k|²        naive incoherent energy
  T_wedge = |Σ_k μ_k e^{-iφ̂_k}|²   wedge-corrected coherent

but T_wedge there is an *oracle*: φ̂_k is the circular mean of the SAME
signal seeds it then scores. With 32 seeds that in-sample reuse inflates
T_wedge — it is an optimistic upper bound, not a realizable detector.
The project's own methodology (S96 null-null calibration, S103) demands
we separate "what an oracle could do" from "what a built detector does".

This supplement adds a defensible detector ladder:

  T_coh        |Σ_k μ_k|²                       coherent, phase-naive
  T_white      Σ_k |μ_k|²/σ²_k                  whitened incoherent (energy GLRT,
                                                 phase-BLIND optimum); σ²_k from
                                                 INDEPENDENT null seeds
  T_cw_oracle  |Σ_k μ_k e^{-iφ̂_k}/σ²_k|²        whitened-coherent matched filter,
                                                 in-sample φ̂ (optimistic)
  T_cw_loo     same, but φ̂_k^(-i) leaves seed i out for signal seeds
                                                 (null seeds use full φ̂ — no leak);
                                                 the REALIZABLE matched-filter optimum
  T_wedge_loo  |Σ_k μ_k e^{-iφ̂_k}|² with LOO φ̂  realizable wedge (no whitening)

Whitening uses σ²_k = E_null[|μ_k|²] measured on the paired A=0 cell — the
empirical per-class null energy, NOT the random-phase prediction n_k (which
S116 showed is badly violated by phase-anti-correlated switch events).

The headline question: in the over-coupled regime (κ_C ≥ 0.50) where the
coherent combine T_coh collapses, does a REALIZABLE detector (T_white phase-
blind, or T_cw_loo phase-aware) recover detection power? AUC vs the paired
null is the calibrated metric (rank-based, no Gaussian assumption).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

CLASSES = ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']


def load(path):
    if not Path(path).exists():
        return None
    with open(path) as f:
        return json.load(f)


def mu_array(per_seed):
    """[n_seeds, 4] complex per-class phasor (sum over chunks of mu_kc)."""
    out = np.zeros((len(per_seed), len(CLASSES)), dtype=complex)
    for i, ps in enumerate(per_seed):
        for j, k in enumerate(CLASSES):
            arr = np.array(ps['mu_kc'][k])  # [n_chunks, 2]
            out[i, j] = complex(arr[:, 0].sum(), arr[:, 1].sum())
    return out


def nsw_array(per_seed):
    return np.array([ps['switch_total'] for ps in per_seed], float)


def auc(null_vals, sig_vals):
    """Mann-Whitney AUC = P(sig > null), 0.5 for ties."""
    null_vals = np.asarray(null_vals)
    gt = 0.0
    for s in sig_vals:
        gt += np.sum(s > null_vals) + 0.5 * np.sum(s == null_vals)
    return gt / (len(null_vals) * len(sig_vals))


def auc_ci(null_vals, sig_vals, B=2000, seed=12345):
    rng = np.random.default_rng(seed)
    nn, ns = len(null_vals), len(sig_vals)
    boots = np.empty(B)
    for b in range(B):
        n = null_vals[rng.integers(0, nn, nn)]
        s = sig_vals[rng.integers(0, ns, ns)]
        boots[b] = auc(n, s)
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def circ_mean_angle(mu_col):
    """Circular mean unit phasor angle of a complex column (ignores |μ|)."""
    nz = mu_col[np.abs(mu_col) > 0]
    if len(nz) == 0:
        return 0.0
    return float(np.angle(np.mean(nz / np.abs(nz))))


def build_detectors(mu_sig, nsw_sig, mu_null, nsw_null):
    """Return dict det_name -> (null_vals, sig_vals).

    mu_*: [n_seeds, 4] complex. Whitening + phase templates are trained on
    the appropriate cells:
      σ²_k        from null cell (independent)
      φ̂_k (full)  from signal cell  -> applied to NULL seeds
      φ̂_k^(-i)    LOO over signal seeds -> applied to each SIGNAL seed i
    """
    ns_sig = mu_sig.shape[0]
    sig2 = np.array([max(np.mean(np.abs(mu_null[:, j])**2), 1e-9)
                     for j in range(len(CLASSES))])           # per-class null energy
    phi_full_sig = np.array([circ_mean_angle(mu_sig[:, j])
                             for j in range(len(CLASSES))])    # in-sample (oracle)

    det = {}

    # --- phase-naive ---
    det['T_coh'] = (np.abs(mu_null.sum(1))**2, np.abs(mu_sig.sum(1))**2)
    det['T_incoh'] = (np.sum(np.abs(mu_null)**2, 1), np.sum(np.abs(mu_sig)**2, 1))
    det['T_white'] = (np.sum(np.abs(mu_null)**2 / sig2, 1),
                      np.sum(np.abs(mu_sig)**2 / sig2, 1))

    # --- oracle phase-aware (in-sample φ̂ from signal cell) ---
    w_or = np.exp(-1j * phi_full_sig)
    det['T_wedge_oracle'] = (np.abs((mu_null * w_or).sum(1))**2,
                             np.abs((mu_sig * w_or).sum(1))**2)
    det['T_cw_oracle'] = (np.abs((mu_null * w_or / sig2).sum(1))**2,
                          np.abs((mu_sig * w_or / sig2).sum(1))**2)

    # --- realizable LOO phase-aware ---
    # null seeds scored with the full signal-cell template (it is the trained
    # model; null never participated in training -> no leakage).
    wedge_null = np.abs((mu_null * w_or).sum(1))**2
    cw_null = np.abs((mu_null * w_or / sig2).sum(1))**2
    wedge_sig = np.empty(ns_sig)
    cw_sig = np.empty(ns_sig)
    for i in range(ns_sig):
        keep = np.ones(ns_sig, bool)
        keep[i] = False
        phi_loo = np.array([circ_mean_angle(mu_sig[keep, j])
                            for j in range(len(CLASSES))])
        w_loo = np.exp(-1j * phi_loo)
        wedge_sig[i] = np.abs((mu_sig[i] * w_loo).sum())**2
        cw_sig[i] = np.abs((mu_sig[i] * w_loo / sig2).sum())**2
    det['T_wedge_loo'] = (wedge_null, wedge_sig)
    det['T_cw_loo'] = (cw_null, cw_sig)

    return det, sig2, phi_full_sig


def main():
    res = load('thor_session_117_class_detector_results.json')
    if res is None:
        print("S117 results not found — run thor_session_117_class_detector.py first.")
        return
    cells = res['cells']
    kc_vals = res['meta']['kc_vals']

    by_kc = {}
    for label, cell in cells.items():
        by_kc.setdefault(cell['kappa_C'], {})[cell['signal_amp']] = cell

    det_order = ['T_coh', 'T_incoh', 'T_white',
                 'T_wedge_loo', 'T_cw_loo',
                 'T_wedge_oracle', 'T_cw_oracle']

    rows = []
    print("\n=== AUC (null A=0 vs signal A=0.40), realizable + oracle ladder ===")
    print(f"{'κ_C':>5} {'wedge°':>7} " + " ".join(f"{d:>14}" for d in det_order))
    for kc in kc_vals:
        if kc not in by_kc or 0.0 not in by_kc[kc] or 0.40 not in by_kc[kc]:
            continue
        cs, cn = by_kc[kc][0.40], by_kc[kc][0.0]
        mu_sig, mu_null = mu_array(cs['per_seed']), mu_array(cn['per_seed'])
        nsw_sig, nsw_null = nsw_array(cs['per_seed']), nsw_array(cn['per_seed'])
        det, sig2, phi = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
        wedge = cs['summary']['wedge_aL_rN']
        aucs = {d: auc(*det[d]) for d in det_order}
        row = {'kappa_C': kc, 'wedge': wedge, 'auc': aucs,
               'sig2': sig2.tolist(), 'phi_deg': np.degrees(phi).tolist()}
        rows.append(row)
        print(f"{kc:5.2f} {wedge:7.1f} " +
              " ".join(f"{aucs[d]:14.3f}" for d in det_order))

    # Headline: best REALIZABLE detector vs naive coherent, with CIs
    print("\n=== HEADLINE: best realizable detector vs T_coh (with 95% CI) ===")
    print(f"{'κ_C':>5} {'wedge°':>7} {'AUC_coh[CI]':>22} "
          f"{'best_realizable':>16} {'AUC[CI]':>22} {'Δ':>7}")
    realizable = ['T_coh', 'T_incoh', 'T_white', 'T_wedge_loo', 'T_cw_loo']
    head = []
    for kc in kc_vals:
        if kc not in by_kc or 0.0 not in by_kc[kc] or 0.40 not in by_kc[kc]:
            continue
        cs, cn = by_kc[kc][0.40], by_kc[kc][0.0]
        mu_sig, mu_null = mu_array(cs['per_seed']), mu_array(cn['per_seed'])
        nsw_sig, nsw_null = nsw_array(cs['per_seed']), nsw_array(cn['per_seed'])
        det, _, _ = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
        wedge = cs['summary']['wedge_aL_rN']
        a_coh = auc(*det['T_coh'])
        lo_c, hi_c = auc_ci(*det['T_coh'])
        # pick best realizable EXCLUDING T_coh
        cand = {d: auc(*det[d]) for d in realizable if d != 'T_coh'}
        best = max(cand, key=cand.get)
        lo_b, hi_b = auc_ci(*det[best])
        print(f"{kc:5.2f} {wedge:7.1f} "
              f"{a_coh:6.3f}[{lo_c:.2f},{hi_c:.2f}]   "
              f"{best:>16} {cand[best]:6.3f}[{lo_b:.2f},{hi_b:.2f}]   "
              f"{cand[best]-a_coh:+7.3f}")
        head.append({'kappa_C': kc, 'wedge': wedge,
                     'auc_coh': a_coh, 'auc_coh_ci': [lo_c, hi_c],
                     'best_realizable': best, 'auc_best': cand[best],
                     'auc_best_ci': [lo_b, hi_b]})

    out = {'session': 117, 'supplement': 'detector_ladder',
           'rows': rows, 'headline': head}
    with open('thor_session_117_detector_ladder.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nLadder analysis → thor_session_117_detector_ladder.json")


if __name__ == '__main__':
    main()
