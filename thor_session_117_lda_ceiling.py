#!/usr/bin/env python3
"""S117 supplement #2: the full-covariance LDA ceiling for class combining.

Motivation
----------
The detector ladder (thor_session_117_detector_ladder.py) tops out at

  T_cw_loo  = |Σ_k μ_k e^{-iφ̂_k}/σ²_k|²   whitened-coherent matched filter

but its whitening is DIAGONAL: σ²_k = E_null[|μ_k|²] treats the four class
phasors as independent noise channels. Switch events are phase-ANTI-correlated
(S116: per-seed |Σμ_k|² ≪ Σ|μ_k|² even in null), so the per-class phasors carry
CROSS-class covariance that a diagonal whitener cannot exploit. If those
off-diagonal correlations are detection-relevant, the true optimal linear
detector beats every diagonal-whitening rung.

The optimal linear detector on the 8-dim real phasor vector
  x = [Re μ_aL, Im μ_aL, Re μ_aN, Im μ_aN, Re μ_rL, Im μ_rL, Re μ_rN, Im μ_rN]
is Fisher's LDA:  w = Σ_w⁻¹ (m₁ − m₀),  score = wᵀx.
This is the realizable ceiling for ANY linear combine of the class phasors —
T_coh, T_incoh, T_white, T_cw are all constrained special cases of it.

We report two things per κ_C:
  • LDA_loo  — leave-one-out Fisher LDA AUC (REALIZABLE; honest, no leakage).
               Shrinkage-regularized covariance (Ledoit-Wolf-style λ) because
               8-dim with ~31+31 training points is borderline.
  • LDA_full — in-sample Mahalanobis Δ → Gaussian AUC = Φ(Δ/√2) (optimistic
               ceiling; tells us how much linear signal exists in principle).

The headline comparison: does LDA_loo beat the diagonal T_cw_loo? If yes by a
margin outside the bootstrap CI, cross-class phasor correlations carry detection
power that the project's hand-built combiners discard — a concrete S118 lead.
If no, the diagonal matched filter already captures the linear ceiling and the
class phasors are effectively independent channels for detection purposes.
"""
import json
import sys
from math import erf, sqrt
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

CLASSES = ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']


def load(path):
    if not Path(path).exists():
        return None
    with open(path) as f:
        return json.load(f)


def phasor_matrix(per_seed):
    """[n_seeds, 8] real feature matrix: (Re,Im) of each class per-seed phasor."""
    X = np.zeros((len(per_seed), 2 * len(CLASSES)))
    for i, ps in enumerate(per_seed):
        for j, k in enumerate(CLASSES):
            arr = np.array(ps['mu_kc'][k])          # [n_chunks, 2]
            X[i, 2 * j] = arr[:, 0].sum()
            X[i, 2 * j + 1] = arr[:, 1].sum()
    return X


def auc(null_vals, sig_vals):
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


def shrink_cov(S, lam):
    """Shrink toward a scaled identity: (1-λ)S + λ·μ·I, μ = tr(S)/p."""
    p = S.shape[0]
    mu = np.trace(S) / p
    return (1.0 - lam) * S + lam * mu * np.eye(p)


def pooled_within_cov(X0, X1):
    n0, n1 = len(X0), len(X1)
    S0 = np.cov(X0, rowvar=False)
    S1 = np.cov(X1, rowvar=False)
    return ((n0 - 1) * S0 + (n1 - 1) * S1) / (n0 + n1 - 2)


def lda_loo_auc(X0, X1, lam=0.15):
    """Leave-one-out Fisher LDA scores; return (null_scores, sig_scores).

    Each held-out seed (from either pool) is scored by a discriminant trained
    on all OTHER seeds (both pools). Realizable: no sample scores its own model.
    """
    n0, n1 = len(X0), len(X1)
    s0 = np.empty(n0)
    s1 = np.empty(n1)
    # null held-out
    for i in range(n0):
        keep = np.ones(n0, bool); keep[i] = False
        m0 = X0[keep].mean(0); m1 = X1.mean(0)
        Sw = shrink_cov(pooled_within_cov(X0[keep], X1), lam)
        w = np.linalg.solve(Sw, m1 - m0)
        s0[i] = w @ X0[i]
    # signal held-out
    for i in range(n1):
        keep = np.ones(n1, bool); keep[i] = False
        m0 = X0.mean(0); m1 = X1[keep].mean(0)
        Sw = shrink_cov(pooled_within_cov(X0, X1[keep]), lam)
        w = np.linalg.solve(Sw, m1 - m0)
        s1[i] = w @ X1[i]
    return s0, s1


def mahalanobis_full(X0, X1, lam=0.15):
    """In-sample Mahalanobis Δ and Gaussian-approx AUC = Φ(Δ/√2)."""
    m0, m1 = X0.mean(0), X1.mean(0)
    Sw = shrink_cov(pooled_within_cov(X0, X1), lam)
    diff = m1 - m0
    delta2 = float(diff @ np.linalg.solve(Sw, diff))
    delta = sqrt(max(delta2, 0.0))
    auc_g = 0.5 * (1.0 + erf((delta / sqrt(2.0)) / sqrt(2.0)))
    return delta, auc_g


def diag_cw_loo_auc(X0, X1):
    """Reproduce the diagonal whitened-coherent matched filter (T_cw_loo) AUC
    on the SAME feature matrices, so the LDA comparison is apples-to-apples.

    Per-class complex μ_k reconstructed from feature columns; whitening
    σ²_k = E_null[|μ_k|²]; phase template φ̂_k = circular mean of signal seeds
    (LOO for signal, full for null)."""
    def to_complex(X):
        return X[:, 0::2] + 1j * X[:, 1::2]      # [n, 4] complex
    M0, M1 = to_complex(X0), to_complex(X1)
    sig2 = np.maximum(np.mean(np.abs(M0) ** 2, 0), 1e-9)

    def circ(col):
        nz = col[np.abs(col) > 0]
        return 0.0 if len(nz) == 0 else np.angle(np.mean(nz / np.abs(nz)))

    phi_full = np.array([circ(M1[:, j]) for j in range(4)])
    w_full = np.exp(-1j * phi_full)
    cw_null = np.abs((M0 * w_full / sig2).sum(1)) ** 2
    n1 = len(M1)
    cw_sig = np.empty(n1)
    for i in range(n1):
        keep = np.ones(n1, bool); keep[i] = False
        phi = np.array([circ(M1[keep, j]) for j in range(4)])
        w = np.exp(-1j * phi)
        cw_sig[i] = np.abs((M1[i] * w / sig2).sum()) ** 2
    return cw_null, cw_sig


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

    print("\n=== LDA ceiling vs diagonal matched filter (null A=0 vs signal A=0.40) ===")
    print(f"{'κ_C':>5} {'wedge°':>7} {'cwLOO':>17} {'ldaLOO':>17} "
          f"{'Δ(lda-cw)':>10} {'LDAfull':>9} {'Δmaha':>7}")
    rows = []
    for kc in kc_vals:
        if kc not in by_kc or 0.0 not in by_kc[kc] or 0.40 not in by_kc[kc]:
            continue
        cn, cs = by_kc[kc][0.0], by_kc[kc][0.40]
        X0 = phasor_matrix(cn['per_seed'])
        X1 = phasor_matrix(cs['per_seed'])
        wedge = cs['summary']['wedge_aL_rN']

        cw_n, cw_s = diag_cw_loo_auc(X0, X1)
        a_cw = auc(cw_n, cw_s)
        lo_cw, hi_cw = auc_ci(cw_n, cw_s)

        s0, s1 = lda_loo_auc(X0, X1)
        a_lda = auc(s0, s1)
        lo_l, hi_l = auc_ci(s0, s1)

        delta, auc_full = mahalanobis_full(X0, X1)

        print(f"{kc:5.2f} {wedge:7.1f} "
              f"{a_cw:.3f}[{lo_cw:.2f},{hi_cw:.2f}] "
              f"{a_lda:.3f}[{lo_l:.2f},{hi_l:.2f}] "
              f"{a_lda - a_cw:+10.3f} {auc_full:9.3f} {delta:7.2f}")
        rows.append({
            'kappa_C': kc, 'wedge': wedge,
            'auc_cw_loo': a_cw, 'auc_cw_loo_ci': [lo_cw, hi_cw],
            'auc_lda_loo': a_lda, 'auc_lda_loo_ci': [lo_l, hi_l],
            'auc_lda_full_gauss': auc_full, 'mahalanobis_delta': delta,
        })

    out = {'session': 117, 'supplement': 'lda_ceiling', 'rows': rows}
    with open('thor_session_117_lda_ceiling.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nInterpretation: where LDA_loo CI lies ABOVE cw_loo CI, cross-class")
    print("phasor correlations carry detection power the diagonal matched filter")
    print("discards. Where they overlap, the diagonal MF already hits the linear")
    print("ceiling and the classes are effectively independent detection channels.")
    print("\nLDA ceiling → thor_session_117_lda_ceiling.json")


if __name__ == '__main__':
    main()
