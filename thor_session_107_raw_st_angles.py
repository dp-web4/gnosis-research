#!/usr/bin/env python3
"""S107 sub-analysis: angle between RAW and ST detector responses.

S96 established (SBP identity) that RAW and ST live in the same 2D
signal plane, with their response angles ~π/2 apart. So if we report
the per-seed angle of <z_raw> and <z_st> in the complex plane, their
difference should be approximately π/2 (90°) and stable across seeds.

Across cells (varying κ_C), the absolute angle reflects which
combination of in-phase / quadrature signal coupling dominates. If
the angle changes with κ_C, that says κ_C reshapes the response phase
geometry — which would mean the two channels (κ_phase, κ_C) are not
just amplitude knobs but also phase knobs.
"""
import json
import numpy as np


def cell_angles(cell):
    arg_raws = []
    arg_sts = []
    for sp in cell['per_seed_z']:
        z_raw = np.array([complex(r, i) for r, i in sp['z_raw']]).mean()
        z_st = np.array([complex(r, i) for r, i in sp['z_st']]).mean()
        arg_raws.append(np.angle(z_raw, deg=True))
        arg_sts.append(np.angle(z_st, deg=True))
    arg_raws = np.array(arg_raws); arg_sts = np.array(arg_sts)
    # Cross-seed circular mean
    raw_R = abs(np.mean(np.exp(1j*np.deg2rad(arg_raws))))
    st_R = abs(np.mean(np.exp(1j*np.deg2rad(arg_sts))))
    raw_mean_arg = float(np.degrees(np.angle(np.mean(np.exp(1j*np.deg2rad(arg_raws))))))
    st_mean_arg = float(np.degrees(np.angle(np.mean(np.exp(1j*np.deg2rad(arg_sts))))))
    delta = st_mean_arg - raw_mean_arg
    delta = ((delta + 180) % 360) - 180  # wrap to [-180, 180]
    return {'raw_arg_deg': raw_mean_arg, 'st_arg_deg': st_mean_arg,
            'delta_st_minus_raw_deg': delta,
            'cross_seed_R_raw': float(raw_R),
            'cross_seed_R_st': float(st_R)}


def main():
    s106 = json.load(open('thor_session_106_kappa_c_channel_results.json'))
    print("RAW ↔ ST detector angle relationship across S106 cells:")
    print(f"{'cell':>22} | κ_p   κ_C  | <arg(z_raw)>° | <arg(z_st)>° | Δ (ST-RAW) | Rraw  Rst")
    print("-" * 100)
    for label, cell in s106['cells'].items():
        a = cell_angles(cell)
        kp = cell['kappa_phase']; kC = cell['kappa_C']
        print(f"{label:>22} | {kp:.2f} {kC:.2f} | "
              f"{a['raw_arg_deg']:>13.1f} | {a['st_arg_deg']:>12.1f} | "
              f"{a['delta_st_minus_raw_deg']:>+10.1f} | "
              f"{a['cross_seed_R_raw']:.2f}  {a['cross_seed_R_st']:.2f}")


if __name__ == '__main__':
    main()
