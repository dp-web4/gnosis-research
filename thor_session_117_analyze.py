#!/usr/bin/env python3
"""S117 analyzer: coherent vs incoherent class-combining detectors.

For each κ_C we have a paired (A=0 null, A=0.40 signal) cell, 32 seeds
each. Per seed we extract a battery of detector statistics and compute
their detection performance (AUC and d′) between null and signal.

Detectors
---------
  N_sw         switch-count baseline (signal raises switch rate via rescue)
  T_coh        |Σ_k μ_k|²              naive coherent combine (= ρ_sig·N_sw)
  rho_sig      T_coh / N_sw            rate-normalized coherent (canonical)
  T_incoh      Σ_k |μ_k|²              4-class incoherent energy
  rho_incoh    T_incoh / N_sw          rate-normalized incoherent
  T_incoh2     |μ_aL|²+|μ_rN|²         2-class incoherent (drop small classes)
  T_wedge      |Σ_k μ_k e^{-iφ̂_k}|²    oracle wedge-corrected coherent
               (φ̂_k = signal-cell ensemble per-class mean angle; UPPER BOUND)

Key questions
-------------
  P1: does AUC(T_incoh) > AUC(T_coh) for κ_C ≥ 0.50 (over-coupled)?
  P2: does AUC(T_coh) ≥ AUC(T_incoh) at the ridge κ_C=0.30?
  P3: is T_wedge ≥ both naive variants at every κ_C (matched-filter optimum)?
  P5: does T_incoh2 (2-class) match/beat T_incoh (4-class)?
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


def mu_k_seed(ps):
    """per-seed complex μ_k for each class (sum over chunks of stored mu_kc)."""
    out = {}
    for k in CLASSES:
        arr = np.array(ps['mu_kc'][k])  # [n_chunks, 2]
        out[k] = complex(arr[:, 0].sum(), arr[:, 1].sum())
    return out


def class_null_floor(per_seed_null):
    """Per-class mean null energy E_null[|μ_k|²] for whitening."""
    floor = {}
    for k in CLASSES:
        e = []
        for ps in per_seed_null:
            arr = np.array(ps['mu_kc'][k])
            mu = complex(arr[:, 0].sum(), arr[:, 1].sum())
            e.append(abs(mu)**2)
        floor[k] = max(float(np.mean(e)), 1e-9)
    return floor


def detector_vec(per_seed, phi_hat=None, null_floor=None):
    """Return dict of detector_name -> array over seeds."""
    n = len(per_seed)
    N_sw = np.zeros(n)
    T_coh = np.zeros(n)
    T_incoh = np.zeros(n)
    T_incoh2 = np.zeros(n)
    T_white = np.zeros(n)
    T_wedge = np.zeros(n)
    for i, ps in enumerate(per_seed):
        mus = mu_k_seed(ps)
        N_sw[i] = ps['switch_total']
        z_tot = sum(mus[k] for k in CLASSES)
        T_coh[i] = abs(z_tot)**2
        T_incoh[i] = sum(abs(mus[k])**2 for k in CLASSES)
        T_incoh2[i] = abs(mus['att_lock'])**2 + abs(mus['rep_noise'])**2
        if null_floor is not None:
            T_white[i] = sum(abs(mus[k])**2 / null_floor[k] for k in CLASSES)
        if phi_hat is not None:
            z_w = sum(mus[k] * np.exp(-1j * phi_hat[k]) for k in CLASSES)
            T_wedge[i] = abs(z_w)**2
    rho_sig = np.where(N_sw > 0, T_coh / np.maximum(N_sw, 1), 0.0)
    rho_incoh = np.where(N_sw > 0, T_incoh / np.maximum(N_sw, 1), 0.0)
    d = {
        'N_sw': N_sw, 'T_coh': T_coh, 'rho_sig': rho_sig,
        'T_incoh': T_incoh, 'rho_incoh': rho_incoh, 'T_incoh2': T_incoh2,
    }
    if null_floor is not None:
        d['T_white'] = T_white
    if phi_hat is not None:
        d['T_wedge'] = T_wedge
        d['rho_wedge'] = np.where(N_sw > 0, T_wedge / np.maximum(N_sw, 1), 0.0)
    return d


def ensemble_phi(per_seed):
    """Ensemble per-class mean angle φ̂_k (circular mean over seeds)."""
    phi = {}
    for k in CLASSES:
        ang = []
        for ps in per_seed:
            arr = np.array(ps['mu_kc'][k])
            mu = complex(arr[:, 0].sum(), arr[:, 1].sum())
            if abs(mu) > 0:
                ang.append(mu / abs(mu))
        z = np.mean(ang) if ang else 1.0 + 0j
        phi[k] = float(np.angle(z))
    return phi


def auc(null_vals, sig_vals):
    """Mann-Whitney AUC = P(sig > null) with 0.5 for ties."""
    nn, ns = len(null_vals), len(sig_vals)
    # rank-based
    gt = 0.0
    for s in sig_vals:
        gt += np.sum(s > null_vals) + 0.5 * np.sum(s == null_vals)
    return gt / (nn * ns)


def auc_ci(null_vals, sig_vals, B=2000, seed=12345):
    rng = np.random.default_rng(seed)
    nn, ns = len(null_vals), len(sig_vals)
    boots = np.empty(B)
    for b in range(B):
        n = null_vals[rng.integers(0, nn, nn)]
        s = sig_vals[rng.integers(0, ns, ns)]
        boots[b] = auc(n, s)
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def dprime(null_vals, sig_vals):
    mn, ms = null_vals.mean(), sig_vals.mean()
    vn, vs = null_vals.var(), sig_vals.var()
    pooled = np.sqrt(0.5 * (vn + vs))
    return float((ms - mn) / pooled) if pooled > 0 else 0.0


def main():
    res = load('thor_session_117_class_detector_results.json')
    if res is None:
        print("S117 results not found.")
        return
    cells = res['cells']
    kc_vals = res['meta']['kc_vals']

    # Map (kc) -> {A: cell}
    by_kc = {}
    for label, cell in cells.items():
        kc = cell['kappa_C']
        A = cell['signal_amp']
        by_kc.setdefault(kc, {})[A] = cell

    det_names = ['N_sw', 'T_coh', 'rho_sig', 'T_incoh', 'rho_incoh',
                 'T_incoh2', 'T_white', 'T_wedge', 'rho_wedge']

    print("\n=== Per-κ_C detector performance (null A=0 vs signal A=0.40) ===")
    print(f"{'κ_C':>5} {'wedge°':>7} {'Nsw_n':>7} {'Nsw_s':>7} {'xterm_s':>9}")
    rows = []
    auc_table = {}
    for kc in kc_vals:
        if kc not in by_kc or 0.0 not in by_kc[kc] or 0.40 not in by_kc[kc]:
            continue
        cell_n = by_kc[kc][0.0]
        cell_s = by_kc[kc][0.40]
        phi_hat = ensemble_phi(cell_s['per_seed'])
        nfloor = class_null_floor(cell_n['per_seed'])
        dv_n = detector_vec(cell_n['per_seed'], phi_hat, nfloor)
        dv_s = detector_vec(cell_s['per_seed'], phi_hat, nfloor)

        wedge = cell_s['summary']['wedge_aL_rN']
        xterm = cell_s['summary']['T_coh_mean'] - cell_s['summary']['T_incoh_mean']
        print(f"{kc:5.2f} {wedge:7.1f} {dv_n['N_sw'].mean():7.0f} "
              f"{dv_s['N_sw'].mean():7.0f} {xterm:9.1f}")
        row = {'kappa_C': kc, 'wedge': wedge,
               'Nsw_null': float(dv_n['N_sw'].mean()),
               'Nsw_sig': float(dv_s['N_sw'].mean()),
               'xterm_sig': float(xterm)}
        aucs = {}
        for dn in det_names:
            if dn in dv_n and dn in dv_s:
                a = auc(dv_n[dn], dv_s[dn])
                dp = dprime(dv_n[dn], dv_s[dn])
                aucs[dn] = {'auc': a, 'dprime': dp}
        row['detectors'] = aucs
        rows.append(row)
        auc_table[kc] = aucs

    # AUC table
    print("\n=== AUC (null vs signal) by detector × κ_C ===")
    hdr = f"{'κ_C':>5} " + " ".join(f"{d:>10}" for d in det_names)
    print(hdr)
    for kc in kc_vals:
        if kc not in auc_table:
            continue
        line = f"{kc:5.2f} "
        for d in det_names:
            v = auc_table[kc].get(d, {}).get('auc')
            line += f"{v:10.3f} " if v is not None else f"{'-':>10} "
        print(line)

    # d' table
    print("\n=== d′ (null vs signal) by detector × κ_C ===")
    print(hdr)
    for kc in kc_vals:
        if kc not in auc_table:
            continue
        line = f"{kc:5.2f} "
        for d in det_names:
            v = auc_table[kc].get(d, {}).get('dprime')
            line += f"{v:10.2f} " if v is not None else f"{'-':>10} "
        print(line)

    # Headline crossover: coherent vs incoherent (rate-normalized = pure phase test)
    print("\n=== HEADLINE: rho_sig (coherent) vs rho_incoh (incoherent) ===")
    print(f"{'κ_C':>5} {'wedge°':>7} {'AUC_coh':>8} {'AUC_incoh':>10} "
          f"{'Δ(incoh-coh)':>13} {'d_coh':>7} {'d_incoh':>8} {'winner':>8}")
    for kc in kc_vals:
        if kc not in auc_table:
            continue
        ac = auc_table[kc]['rho_sig']['auc']
        ai = auc_table[kc]['rho_incoh']['auc']
        dc = auc_table[kc]['rho_sig']['dprime']
        di = auc_table[kc]['rho_incoh']['dprime']
        w = next(r['wedge'] for r in rows if r['kappa_C'] == kc)
        winner = 'incoh' if ai > ac else 'coh'
        print(f"{kc:5.2f} {w:7.1f} {ac:8.3f} {ai:10.3f} {ai-ac:+13.3f} "
              f"{dc:7.2f} {di:8.2f} {winner:>8}")

    # Same for RAW (operational) statistics
    print("\n=== OPERATIONAL: T_coh (raw coherent) vs T_incoh (raw incoherent) ===")
    print(f"{'κ_C':>5} {'wedge°':>7} {'AUC_coh':>8} {'AUC_incoh':>10} "
          f"{'Δ':>8} {'AUC_Nsw':>8} {'AUC_wedge':>10}")
    for kc in kc_vals:
        if kc not in auc_table:
            continue
        ac = auc_table[kc]['T_coh']['auc']
        ai = auc_table[kc]['T_incoh']['auc']
        an = auc_table[kc]['N_sw']['auc']
        aw = auc_table[kc].get('T_wedge', {}).get('auc')
        w = next(r['wedge'] for r in rows if r['kappa_C'] == kc)
        print(f"{kc:5.2f} {w:7.1f} {ac:8.3f} {ai:10.3f} {ai-ac:+8.3f} "
              f"{an:8.3f} {aw:10.3f}")

    # CI on the headline crossover detectors at extreme κ_C
    print("\n=== Bootstrap 95% CI on AUC (rho_sig, rho_incoh) ===")
    for kc in kc_vals:
        if kc not in by_kc or 0.0 not in by_kc[kc] or 0.40 not in by_kc[kc]:
            continue
        cell_n = by_kc[kc][0.0]; cell_s = by_kc[kc][0.40]
        phi_hat = ensemble_phi(cell_s['per_seed'])
        nfloor = class_null_floor(cell_n['per_seed'])
        dv_n = detector_vec(cell_n['per_seed'], phi_hat, nfloor)
        dv_s = detector_vec(cell_s['per_seed'], phi_hat, nfloor)
        lo_c, hi_c = auc_ci(dv_n['rho_sig'], dv_s['rho_sig'])
        lo_i, hi_i = auc_ci(dv_n['rho_incoh'], dv_s['rho_incoh'])
        print(f"  κ_C={kc:.2f}: coh AUC [{lo_c:.3f},{hi_c:.3f}]  "
              f"incoh AUC [{lo_i:.3f},{hi_i:.3f}]")

    out = {'session': 117, 'rows': rows}
    with open('thor_session_117_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nAnalysis → thor_session_117_analysis.json")


if __name__ == '__main__':
    main()
