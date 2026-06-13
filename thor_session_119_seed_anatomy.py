#!/usr/bin/env python3
"""S119 Part 3: Seed anatomy of the reproducibility limit.

Part 1 established d′ ≈ √2/CV_sig at the edge: the T_cw_loo d′ inverted-U
is the U-shape of the statistic's seed-to-seed CV. Part 2 (ω series) tests
whether ω-detuning drives the high-A CV rise. This part asks WHAT, within
a cell, distinguishes a low-response seed from a high-response seed —
i.e. which dynamical variable carries the irreproducibility.

For each (ω_std, A) cell at κ_C=0.30 it computes the per-seed T_cw_loo
values and their Spearman correlation with per-seed dynamical covariates:

    switch_total            total switch count
    kura_mean               mean Kuramoto R
    lock_frac_global        fraction of time phase-locked
    lock_at_switch_frac     fraction of switches taken while locked
    gate_att_at_switch_frac fraction of switches with gate attenuated
    mod_amp_at_fs_lock      lock-channel modulation amplitude at f_s

It also decomposes the statistic by class: per-class whitened weight
w_k = ⟨|μ_k|⟩/σ²_k (share of the combined sum), per-class CV of |μ_ik|
across seeds, and per-class circular std of arg(μ_ik) — locating whether
the seed scatter lives in class amplitude or class phase, and in which
class.

Prediction (if ω-detuning → stochastic-locking is the mechanism): at
ω_std>0, high-A T correlates with locking covariates and the dominant
class's phase scatter grows with A past the peak; at ω_std=0 both
signatures are suppressed.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, build_detectors, CLASSES,
)

S119 = 'thor_session_119_omega_heterogeneity_results.json'
S117 = 'thor_session_117_class_detector_results.json'
S118_MAIN = 'thor_session_118_detection_edge_results.json'
S118_LOWA = 'thor_session_118_lowA_results.json'

KC = 0.30
DET = 'T_cw_loo'
COMMON_A = [0.02, 0.06, 0.16, 0.40]
COVARS = ['switch_total', 'kura_mean', 'lock_frac_global',
          'lock_at_switch_frac', 'gate_att_at_switch_frac',
          'mod_amp_at_fs_lock']


def gather():
    by = {}
    r119 = load(S119)
    if r119 is not None:
        for cell in r119['cells'].values():
            if round(cell['kappa_C'], 2) == KC:
                by.setdefault(round(cell['omega_std'], 2), {})[
                    round(cell['signal_amp'], 4)] = cell
    for path in (S117, S118_MAIN, S118_LOWA):
        r = load(path)
        if r is None:
            continue
        for cell in r['cells'].values():
            if (round(cell['kappa_C'], 2) == KC
                    and round(cell.get('omega_std', 0.07), 2) == 0.07):
                by.setdefault(0.07, {})[round(cell['signal_amp'], 4)] = cell
    return by


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / den) if den > 0 else 0.0


def circ_std(ang):
    """Circular std (rad) of angles."""
    R = abs(np.mean(np.exp(1j * ang)))
    return float(np.sqrt(max(0.0, -2.0 * np.log(max(R, 1e-12)))))


def main():
    by = gather()
    have = sorted(by.keys())
    print(f"ω_std series at κ_C={KC}: {have}")
    out = {}
    for omstd in have:
        cells = by[omstd]
        if 0.0 not in cells:
            print(f"ω_std={omstd}: no null, skip"); continue
        cn = cells[0.0]
        mu_null = mu_array(cn['per_seed']); nsw_null = nsw_array(cn['per_seed'])
        print(f"\n{'='*100}\nω_std = {omstd:.2f}   κ_C={KC}   detector={DET}")
        ser = []
        for A in COMMON_A:
            if A not in cells:
                continue
            cs = cells[A]
            ps = cs['per_seed']
            mu_sig = mu_array(ps); nsw_sig = nsw_array(ps)
            det, _, _ = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
            _, sv = det[DET]
            sv = np.asarray(sv, float)
            cv = float(sv.std() / sv.mean()) if sv.mean() > 0 else float('nan')
            # covariate correlations
            cors = {}
            for cvr in COVARS:
                vals = np.array([s[cvr] for s in ps], float)
                cors[cvr] = spearman(sv, vals)
            # per-class anatomy
            sig2 = np.array([max(np.mean(np.abs(mu_null[:, j])**2), 1e-9)
                             for j in range(len(CLASSES))])
            cls = {}
            for j, k in enumerate(CLASSES):
                amp = np.abs(mu_sig[:, j])
                w = float(amp.mean() / sig2[j])
                cls[k] = {'w': w,
                          'cv_amp': float(amp.std() / amp.mean()) if amp.mean() > 0 else float('nan'),
                          'circ_std': circ_std(np.angle(mu_sig[:, j]))}
            wtot = sum(c['w'] for c in cls.values())
            for c in cls.values():
                c['w_share'] = c['w'] / wtot if wtot > 0 else float('nan')
            dom = max(cls, key=lambda k: cls[k]['w'])
            cstr = ' '.join(f"{cvr.split('_')[0][:4]}:{cors[cvr]:+.2f}"
                            for cvr in COVARS)
            print(f"A={A:5.2f}  CV={cv:.3f}  ρ_s[{cstr}]")
            print(f"         dominant class={dom} (share {cls[dom]['w_share']:.2f}) "
                  f"cv_amp={cls[dom]['cv_amp']:.3f} circ_std={cls[dom]['circ_std']:.3f} rad")
            ser.append({'A': A, 'cv': cv, 'cors': cors, 'classes': cls,
                        'dominant': dom})
        out[str(omstd)] = ser

    with open('thor_session_119_seed_anatomy_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\n→ thor_session_119_seed_anatomy_results.json")


if __name__ == '__main__':
    main()
