#!/usr/bin/env python3
"""S118 supplementary: paired-bootstrap CIs on detector AUCs and on the
key detector-DIFFERENCES at the detection edge.

Motivation
----------
The main S118 analyzer (thor_session_118_analyze.py) reports AUC point
estimates. Near the detection floor, 32-vs-32-seed AUC has an SE of
~0.05-0.07, so an "inversion" of Δ_AUC ≈ 0.02 between two detectors is
not, by itself, evidence of anything. The hypotheses S118 cares about are
all DIFFERENCES between detectors evaluated on the SAME seeds:

  H2: T_cw_loo  −  T_coh   > 0   near threshold
  H4: Fusion    −  max(T_coh, N_sw) ≥ 0   at every κ_C

Because every detector is a deterministic function of the same per-seed
μ-vectors and switch counts, the correct test is a PAIRED bootstrap:
resample null-seed indices and signal-seed indices ONCE per iteration and
score every detector on that single resample, then take the difference.
This cancels the shared-seed variance and is far tighter than comparing
two independent CIs.

Templates (σ²_k whitening, φ̂_k phase) are fixed at full-sample values;
we resample only the scoring. This understates template-estimation
variance slightly but is the standard fixed-model bootstrap and is
appropriate for ranking realizable detectors whose templates are, by
construction, what you would ship.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, auc, build_detectors,
)
from thor_session_118_analyze import S118, S117, KC_VALS, lda_loo_auc

B = 4000
RNG_SEED = 20240608


def auc_fast(null_vals, sig_vals):
    """Vectorised Mann-Whitney AUC = P(sig > null) with 0.5 ties."""
    null_vals = np.asarray(null_vals)
    sig_vals = np.asarray(sig_vals)
    # broadcast compare: [ns, nn]
    d = sig_vals[:, None] - null_vals[None, :]
    return (np.sum(d > 0) + 0.5 * np.sum(d == 0)) / (d.size)


def paired_bootstrap(score_pairs, rng):
    """score_pairs: dict name -> (null_vals[nn], sig_vals[ns]).

    Returns dict name -> bootstrap AUC array [B], all resampled on the SAME
    per-iteration index draws so differences are paired.
    """
    names = list(score_pairs)
    nn = len(next(iter(score_pairs.values()))[0])
    ns = len(next(iter(score_pairs.values()))[1])
    boots = {n: np.empty(B) for n in names}
    for b in range(B):
        in_ = rng.integers(0, nn, nn)
        is_ = rng.integers(0, ns, ns)
        for n in names:
            nv, sv = score_pairs[n]
            boots[n][b] = auc_fast(nv[in_], sv[is_])
    return boots


def ci(arr):
    return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


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

    rng = np.random.default_rng(RNG_SEED)
    out = {}

    for kc in KC_VALS:
        cells = by_kc[kc]
        if 0.0 not in cells:
            print(f"κ_C={kc}: no null, skip"); continue
        cn = cells[0.0]
        mu_null = mu_array(cn['per_seed'])
        nsw_null = nsw_array(cn['per_seed'])
        a_sig = sorted(a for a in cells if a > 0.0)

        print(f"\n{'='*92}\nκ_C={kc}  paired-bootstrap AUC (95% CI), B={B}")
        print(f"{'A':>5}  {'T_coh':>22} {'T_cw_loo':>22} {'N_sw':>22} {'Fusion':>22}")
        out[str(kc)] = []
        for A in a_sig:
            cs = cells[A]
            mu_sig = mu_array(cs['per_seed'])
            nsw_sig = nsw_array(cs['per_seed'])
            det, sig2, phi = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)

            pairs = {
                'T_coh': det['T_coh'],
                'T_cw_loo': det['T_cw_loo'],
                'N_sw': (nsw_null, nsw_sig),
            }
            boots = paired_bootstrap(pairs, rng)
            # Fusion AUC point estimate (LOO LDA) — not bootstrapped per-iter
            # (its LOO retraining per draw is too costly); report point only.
            fus = lda_loo_auc(nsw_null, det['T_coh'][0], nsw_sig, det['T_coh'][1])

            pt = {n: auc_fast(*pairs[n]) for n in pairs}
            cis = {n: ci(boots[n]) for n in boots}

            # paired differences
            d_cwl = boots['T_cw_loo'] - boots['T_coh']      # H2
            ci_cwl = ci(d_cwl); p_cwl = float(np.mean(d_cwl <= 0))

            row = {
                'A': A,
                'auc': {**{n: pt[n] for n in pairs}, 'Fusion': fus},
                'ci': cis,
                'diff_cwl_coh': {'mean': float(d_cwl.mean()),
                                 'ci': ci_cwl, 'p_le0': p_cwl},
            }
            out[str(kc)].append(row)

            def fmt(n):
                return f"{pt[n]:.3f}[{cis[n][0]:.2f},{cis[n][1]:.2f}]"
            print(f"{A:5.2f}  {fmt('T_coh'):>22} {fmt('T_cw_loo'):>22} "
                  f"{fmt('N_sw'):>22} {fus:>22.3f}")
            star = '*' if (ci_cwl[0] > 0 or ci_cwl[1] < 0) else ' '
            print(f"       Δ(cw_loo−coh)={d_cwl.mean():+.3f} "
                  f"CI[{ci_cwl[0]:+.3f},{ci_cwl[1]:+.3f}] "
                  f"P(Δ≤0)={p_cwl:.3f} {star}")

    with open('thor_session_118_ci_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\n→ thor_session_118_ci_results.json")


if __name__ == '__main__':
    main()
