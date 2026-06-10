#!/usr/bin/env python3
"""S118 supplement: the rate channel (N_sw) scaling vs the coherent channel —
directly settling pre-registration claim P-B.

Why this script exists
----------------------
S118's main analyzer reports AUC(N_sw) across A and the detection floors, and
the d′ script fits d′(A) ∝ A^p for the three ENERGY detectors (T_coh, T_white,
T_cw_loo). Neither fits the RATE channel's amplitude scaling, because N_sw is
anti-informative at the ridge (signal REDUCES switches → d′ < 0 → log-log fit
breaks). But the entire P-B question — does the floor inversion (H1) survive for
the *realizable* ladder, or does N_sw rate-rescue pull the over-coupled floor
back below the ridge? — is a statement about how fast the rate channel separates
relative to the coherent channel as A→0.

P-B prediction (pre-registered): "rescue is higher-order; H1 holds for the
realizable ladder too, but with a smaller margin than the coherent-only gap."
Concretely: q_rate > q_coh, i.e. |ΔN_sw|(A) vanishes faster than |m_tot|(A) as
A→0, so near threshold the coherent channel always wins even in the over-coupled
regime where N_sw dominates at A=0.40.

What it computes (per κ_C, per A vs the paired A=0 null)
-------------------------------------------------------
  <Nsw_null>, <Nsw_sig>, ΔN_sw = <Nsw_sig> − <Nsw_null>   (signed)
  d′_Nsw       = ΔN_sw / sqrt(½(var_sig + var_null))       (signed effect size)
  AUC(N_sw)    Mann–Whitney (the calibrated rate detectability)
  |m_tot|(A)   = | mean_seed Σ_k μ_k |  (coherent phasor magnitude; T_coh = |·|²)
  d′_coh       = coherent-channel effect size for reference

Then small-A power-law fits (A ≤ 0.16, sign-folded for the rate channel):
  |ΔN_sw|(A) ∝ A^q_rate      r²
  |m_tot|(A) ∝ A^q_coh       r²
and the P-B verdict q_rate vs q_coh per κ_C, plus the realizable crossover A*
where AUC(N_sw) first overtakes AUC(T_coh) (None if it never does in-range).

No new simulation — reads the S118 + S117 result JSONs.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, auc,
)
from thor_session_118_analyze import S118, S117, KC_VALS


def signed_dprime(null_vals, sig_vals):
    null_vals = np.asarray(null_vals, float)
    sig_vals = np.asarray(sig_vals, float)
    pooled = 0.5 * (np.var(sig_vals) + np.var(null_vals))
    if pooled <= 0:
        return 0.0
    return float((sig_vals.mean() - null_vals.mean()) / np.sqrt(pooled))


def fit_loglog(a, y):
    """Least-squares log-log slope of |y| vs a over a>0, |y|>0 points."""
    a = np.asarray(a, float)
    y = np.abs(np.asarray(y, float))
    m = (a > 0) & (y > 0)
    if m.sum() < 2:
        return float('nan'), float('nan')
    la, ly = np.log(a[m]), np.log(y[m])
    M = np.vstack([la, np.ones_like(la)]).T
    slope, intercept = np.linalg.lstsq(M, ly, rcond=None)[0]
    pred = M @ np.array([slope, intercept])
    ss_res = np.sum((ly - pred) ** 2)
    ss_tot = np.sum((ly - ly.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return float(slope), float(r2)


def coherent_mtot(per_seed):
    """| mean over seeds of (Σ_k μ_k) |  — the coherent phasor magnitude."""
    mu = mu_array(per_seed)            # [n_seeds, 4] complex
    m_tot = mu.sum(axis=1).mean()      # complex scalar
    return float(np.abs(m_tot))


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

    out = {}
    A_FIT_MAX = 0.16   # small-A regime for the scaling fit

    for kc in KC_VALS:
        cells = by_kc[kc]
        if 0.0 not in cells:
            print(f"κ_C={kc}: no null cell, skip"); continue
        cn = cells[0.0]
        nsw_null = nsw_array(cn['per_seed'])
        nsw_null_mean = float(nsw_null.mean())
        a_sig = sorted(a for a in cells if a > 0.0)

        print(f"\n{'='*100}")
        print(f"κ_C = {kc}   rate channel vs coherent channel "
              f"(null <Nsw>={nsw_null_mean:.0f}, {len(nsw_null)} null seeds)")
        print(f"{'A':>5} {'<Nsw_sig>':>10} {'ΔNsw':>9} {'dʹ_Nsw':>8} "
              f"{'AUC_Nsw':>8} {'|m_tot|':>9} {'dʹ_coh':>8} {'AUC_coh':>8}")

        rows = []
        for A in a_sig:
            cs = cells[A]
            nsw_sig = nsw_array(cs['per_seed'])
            mu_sig = mu_array(cs['per_seed'])
            mu_null = mu_array(cn['per_seed'])

            dnsw = float(nsw_sig.mean() - nsw_null_mean)
            dp_nsw = signed_dprime(nsw_null, nsw_sig)
            auc_nsw = auc(nsw_null, nsw_sig)

            # coherent channel
            tcoh_null = np.abs(mu_null.sum(1))**2
            tcoh_sig = np.abs(mu_sig.sum(1))**2
            dp_coh = signed_dprime(tcoh_null, tcoh_sig)
            auc_coh = auc(tcoh_null, tcoh_sig)
            m_tot = coherent_mtot(cs['per_seed'])

            rows.append({'A': A, 'nsw_sig_mean': float(nsw_sig.mean()),
                         'dNsw': dnsw, 'dprime_nsw': dp_nsw, 'auc_nsw': auc_nsw,
                         'm_tot': m_tot, 'dprime_coh': dp_coh, 'auc_coh': auc_coh})
            print(f"{A:5.2f} {nsw_sig.mean():10.0f} {dnsw:9.0f} {dp_nsw:8.2f} "
                  f"{auc_nsw:8.3f} {m_tot:9.1f} {dp_coh:8.2f} {auc_coh:8.3f}")

        # --- small-A scaling fits ---
        a_lo = [r['A'] for r in rows if r['A'] <= A_FIT_MAX]
        q_rate, r2_rate = fit_loglog(a_lo,
                                     [r['dNsw'] for r in rows if r['A'] <= A_FIT_MAX])
        q_coh, r2_coh = fit_loglog(a_lo,
                                   [r['m_tot'] for r in rows if r['A'] <= A_FIT_MAX])
        # sign of the rate response (rescue vs anti-informative)
        sign_lo = np.sign(np.mean([r['dNsw'] for r in rows if r['A'] <= A_FIT_MAX]))
        rate_sign = ('rescue (+, signal raises Nsw)' if sign_lo > 0
                     else 'anti-informative (−, signal lowers Nsw)')

        # realizable crossover: smallest A where AUC(N_sw) ≥ AUC(T_coh)
        cross = None
        for r in sorted(rows, key=lambda x: x['A']):
            if r['auc_nsw'] >= r['auc_coh']:
                cross = r['A']; break

        print(f"  small-A (A≤{A_FIT_MAX}):  |ΔNsw| ∝ A^{q_rate:.2f} (r²={r2_rate:.2f})   "
              f"|m_tot| ∝ A^{q_coh:.2f} (r²={r2_coh:.2f})")
        print(f"  rate channel sign: {rate_sign}")
        verdict = ('rate higher-order (P-B supported: coherent wins at threshold)'
                   if (np.isfinite(q_rate) and np.isfinite(q_coh) and q_rate > q_coh)
                   else 'rate NOT higher-order (P-B challenged)')
        print(f"  P-B (q_rate > q_coh)? {q_rate:.2f} vs {q_coh:.2f} → {verdict}")
        print(f"  AUC(N_sw) overtakes AUC(T_coh) at A* = {cross}")

        out[str(kc)] = {
            'null_nsw_mean': nsw_null_mean,
            'rows': rows,
            'q_rate': q_rate, 'r2_rate': r2_rate,
            'q_coh': q_coh, 'r2_coh': r2_coh,
            'rate_sign': float(sign_lo),
            'crossover_A': cross,
            'pb_supported': bool(np.isfinite(q_rate) and np.isfinite(q_coh)
                                 and q_rate > q_coh),
        }

    # --- cross-κ_C P-B synthesis ---
    print(f"\n{'='*100}\nP-B SYNTHESIS — rate vs coherent amplitude scaling per κ_C")
    print(f"{'κ_C':>5} {'q_rate':>8} {'q_coh':>7} {'q_rate−q_coh':>13} "
          f"{'rate_sign':>10} {'crossA*':>8} {'P-B':>5}")
    for kc in KC_VALS:
        if str(kc) not in out:
            continue
        o = out[str(kc)]
        sgn = '+' if o['rate_sign'] > 0 else '−'
        ca = f"{o['crossover_A']:.2f}" if o['crossover_A'] is not None else 'none'
        print(f"{kc:5.2f} {o['q_rate']:8.2f} {o['q_coh']:7.2f} "
              f"{o['q_rate']-o['q_coh']:+13.2f} {sgn:>10} {ca:>8} "
              f"{'yes' if o['pb_supported'] else 'NO':>5}")

    with open('thor_session_118_rate_channel_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\n→ thor_session_118_rate_channel_results.json")


if __name__ == '__main__':
    main()
