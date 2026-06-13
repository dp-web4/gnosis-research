#!/usr/bin/env python3
"""S119 Part 1b: the two-regime anatomy of CV_sig on the existing full A ladder.

Part 1 showed d′ ≈ √2/CV_sig past AUC saturation, so the d′ inverted-U is the
CV_sig U-shape. S118-P2 predicted the LOO phase template error Var(φ̂_k) falls
∝1/A² at low A (noise-dominated phase estimate) and saturates/rises at high A,
with the crossover at the d′ peak. This script measures, on the EXISTING
ω_std=0.07 data (S117+S118, both κ_C), across the full A grid:

  - CV of |μ_i,rep_lock| across seeds  (amplitude scatter, dominant class)
  - circular std of arg(μ_i,rep_lock)  (phase scatter)
  - same for the T_cw_loo statistic CV (from Part 1)

and fits log-log slopes of the phase scatter below and above the d′ peak.
If the low-A branch is ≈ -1 (σ_φ ∝ 1/A) and the high-A branch positive, the
CV U is two distinct regimes: noise-limited template at low A, dynamics-limited
reproducibility at high A.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_117_detector_ladder import (
    load, mu_array, nsw_array, build_detectors, CLASSES,
)

S117 = 'thor_session_117_class_detector_results.json'
S118_MAIN = 'thor_session_118_detection_edge_results.json'
S118_LOWA = 'thor_session_118_lowA_results.json'

DET = 'T_cw_loo'
A_PEAK = 0.06


def circ_std(ang):
    R = abs(np.mean(np.exp(1j * ang)))
    return float(np.sqrt(max(0.0, -2.0 * np.log(max(R, 1e-12)))))


def gather(kc):
    cells = {}
    for path in (S117, S118_MAIN, S118_LOWA):
        r = load(path)
        if r is None:
            continue
        for cell in r['cells'].values():
            if (round(cell['kappa_C'], 2) == kc
                    and round(cell.get('omega_std', 0.07), 2) == 0.07):
                cells[round(cell['signal_amp'], 4)] = cell
    return cells


def main():
    out = {}
    jrep = CLASSES.index('rep_lock')
    for kc in (0.30, 0.70):
        cells = gather(kc)
        cn = cells[0.0]
        mu_null = mu_array(cn['per_seed']); nsw_null = nsw_array(cn['per_seed'])
        As = sorted(a for a in cells if a > 0)
        print(f"\n{'='*84}\nκ_C={kc:.2f}  ω_std=0.07  dominant class=rep_lock  "
              f"(A grid: {As})")
        print(f"{'A':>7} {'CV_T':>7} {'cv_amp':>7} {'σ_φ(rad)':>9}")
        rows = []
        for A in As:
            cs = cells[A]
            mu_sig = mu_array(cs['per_seed']); nsw_sig = nsw_array(cs['per_seed'])
            det, _, _ = build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
            _, sv = det[DET]
            sv = np.asarray(sv, float)
            cv_T = float(sv.std() / sv.mean()) if sv.mean() > 0 else float('nan')
            amp = np.abs(mu_sig[:, jrep])
            rows.append({
                'A': A, 'cv_T': cv_T,
                'cv_amp': float(amp.std() / amp.mean()),
                'sphi': circ_std(np.angle(mu_sig[:, jrep])),
            })
            r = rows[-1]
            print(f"{A:7.3f} {r['cv_T']:7.3f} {r['cv_amp']:7.3f} {r['sphi']:9.3f}")

        # log-log slopes of σ_φ below / above the peak
        slopes = {}
        for name, sel in (('low-A (A<=peak)', lambda a: a <= A_PEAK),
                          ('high-A (A>=peak)', lambda a: a >= A_PEAK)):
            pts = [(np.log(r['A']), np.log(r['sphi'])) for r in rows
                   if sel(r['A']) and r['sphi'] > 0]
            if len(pts) >= 3:
                x, y = map(np.array, zip(*pts))
                slope = float(np.polyfit(x, y, 1)[0])
                print(f"  σ_φ slope {name}: {slope:+.2f}")
                slopes[name.split()[0]] = slope
        out[str(kc)] = {'rows': rows, 'slopes': slopes}

    with open('thor_session_119_phase_scatter_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\n→ thor_session_119_phase_scatter_results.json")


if __name__ == '__main__':
    main()
