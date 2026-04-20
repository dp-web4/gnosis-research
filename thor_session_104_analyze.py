#!/usr/bin/env python3
"""S104 analysis: combine S104 cells with S103 cells, plot R_coh vs ω/κ
and ω separately, fit Kuramoto-style R(ratio) for the cliff."""
import json
import numpy as np


def load_cells():
    """Returns list of (kappa, omega, R_raw, R_st, R_raw_sd, R_st_sd, R_angle_raw, R_angle_st, source)."""
    cells = []
    # S103: ω=0.02 main (S98), ω=0.04, ω=0.08 sweep — all at κ=0.10
    # S98 main reference (THOR_SESSION_103_SNR_FLOOR.md table)
    cells.append({
        'kappa': 0.10, 'omega': 0.02,
        'R_raw': 0.375, 'R_st': 0.706,
        'R_raw_sd': 0.015, 'R_st_sd': 0.014,
        'R_angle_raw': 0.999, 'R_angle_st': 0.999,
        'source': 'S98/S103 main', 'n_seeds': 8, 'n_chunks': 100,
    })
    s103 = json.load(open('thor_session_103_sweep_fast_results.json'))
    for ow_str, c in s103['per_cell'].items():
        ow = float(ow_str)
        rs, ss = c['raw_seeds'], c['st_seeds']
        rmu, rsig = rs['mean_mu_abs'], rs['mean_sigma_n']
        smu, ssig = ss['mean_mu_abs'], ss['mean_sigma_n']
        # Per-seed R_coh array for sd
        per_seed_R_raw = [m**2/(m**2+s**2) for m, s in
                          zip(rs['per_seed_mu_abs'], rs['per_seed_sigma_n'])]
        per_seed_R_st = [m**2/(m**2+s**2) for m, s in
                         zip(ss['per_seed_mu_abs'], ss['per_seed_sigma_n'])]
        cells.append({
            'kappa': 0.10, 'omega': ow,
            'R_raw': float(np.mean(per_seed_R_raw)),
            'R_st': float(np.mean(per_seed_R_st)),
            'R_raw_sd': float(np.std(per_seed_R_raw)),
            'R_st_sd': float(np.std(per_seed_R_st)),
            'R_angle_raw': None, 'R_angle_st': None,
            'source': f'S103 sweep ω={ow}', 'n_seeds': 8, 'n_chunks': 100,
        })
    # S104 cells
    s104 = json.load(open('thor_session_104_kuramoto_results.json'))
    for label, c in s104['cells'].items():
        s = c['summary']
        cells.append({
            'kappa': c['kappa_phase'], 'omega': c['omega_spread'],
            'R_raw': s['raw_R_coh_mean'], 'R_st': s['st_R_coh_mean'],
            'R_raw_sd': s['raw_R_coh_std'], 'R_st_sd': s['st_R_coh_std'],
            'R_angle_raw': s['cross_seed_R_angle_raw'],
            'R_angle_st': s['cross_seed_R_angle_st'],
            'source': f'S104 {label}', 'n_seeds': 8, 'n_chunks': 50,
        })
    return cells


def main():
    cells = load_cells()
    cells.sort(key=lambda c: (c['kappa'], c['omega']))

    print("=" * 90)
    print(f"{'source':<25} {'κ':>5} {'ω':>7} {'ω/κ':>5} "
          f"{'R_raw':>7} {'±sd':>5} {'R_st':>7} {'±sd':>5} "
          f"{'Rangθ_RAW':>9} {'Rangθ_ST':>9}")
    print("=" * 90)
    for c in cells:
        ra = '   —' if c['R_angle_raw'] is None else f"{c['R_angle_raw']:.3f}"
        rs = '   —' if c['R_angle_st'] is None else f"{c['R_angle_st']:.3f}"
        print(f"{c['source']:<25} {c['kappa']:5.2f} {c['omega']:7.4f} "
              f"{c['omega']/c['kappa']:5.2f} "
              f"{c['R_raw']:7.3f} {c['R_raw_sd']:5.3f} "
              f"{c['R_st']:7.3f} {c['R_st_sd']:5.3f}    "
              f"{ra:>9}  {rs:>9}")

    # Test of ratio invariance: group cells by ω/κ and check R_coh agreement
    print("\n" + "=" * 70)
    print("RATIO INVARIANCE TEST: cells grouped by ω/κ")
    print("=" * 70)
    from collections import defaultdict
    by_ratio = defaultdict(list)
    for c in cells:
        r = round(c['omega'] / c['kappa'], 3)
        by_ratio[r].append(c)
    for r in sorted(by_ratio.keys()):
        group = by_ratio[r]
        if len(group) >= 2:
            print(f"  ratio={r}:  ", end='')
            for c in group:
                print(f"(κ={c['kappa']}, ω={c['omega']}) "
                      f"R_raw={c['R_raw']:.3f} R_st={c['R_st']:.3f}; ", end='')
            R_raws = [c['R_raw'] for c in group]
            R_sts = [c['R_st'] for c in group]
            print(f"\n        Δ_R_raw={max(R_raws)-min(R_raws):.3f}  "
                  f"Δ_R_st={max(R_sts)-min(R_sts):.3f}")

    # Cliff fit at κ=0.10
    print("\n" + "=" * 70)
    print("CLIFF FIT: R_coh vs ω_spread at κ=0.10")
    print("=" * 70)
    k010 = [c for c in cells if abs(c['kappa']-0.10) < 1e-9]
    k010.sort(key=lambda c: c['omega'])
    print(f"{'ω':>7} {'R_raw':>7} {'R_st':>7}")
    for c in k010:
        print(f"{c['omega']:7.4f} {c['R_raw']:7.3f} {c['R_st']:7.3f}")
    # Try Kuramoto sigmoid fit:
    # R(Δ) = R0 · max(0, 1 - (Δ/Δ_c)^p)^q   plus a baseline
    from scipy.optimize import least_squares
    omegas = np.array([c['omega'] for c in k010])
    R_raws = np.array([c['R_raw'] for c in k010])
    R_sts = np.array([c['R_st'] for c in k010])

    def kuramoto_curve(p, om):
        R0, dc, alpha, baseline = p
        x = np.maximum(1.0 - om/dc, 0.0)
        return baseline + R0 * x**alpha

    def fit(R, init_R0):
        try:
            res = least_squares(
                lambda p: kuramoto_curve(p, omegas) - R,
                [init_R0, 0.08, 0.5, 0.05],
                bounds=([0, 0.02, 0.1, -0.1], [1.0, 0.5, 3.0, 0.5]))
            return res.x.tolist(), float(np.sum(res.fun**2)/len(R))
        except Exception as e:
            return None, str(e)

    p_raw, mse_raw = fit(R_raws, 0.4)
    p_st, mse_st = fit(R_sts, 0.7)
    if p_raw:
        print(f"\nRAW Kuramoto fit: R(ω)= {p_raw[3]:.3f} + {p_raw[0]:.3f}·max(0, 1-ω/{p_raw[1]:.4f})^{p_raw[2]:.2f}")
        print(f"   Δ_c_RAW = {p_raw[1]:.4f}    MSE = {mse_raw:.4f}")
    if p_st:
        print(f"\nST  Kuramoto fit: R(ω)= {p_st[3]:.3f} + {p_st[0]:.3f}·max(0, 1-ω/{p_st[1]:.4f})^{p_st[2]:.2f}")
        print(f"   Δ_c_ST  = {p_st[1]:.4f}    MSE = {mse_st:.4f}")
    print(f"\nKuramoto theory (uniform-Δ): Δ_c = πK/4 = {np.pi*0.10/4:.4f} for κ=0.10")

    # Save analysis bundle
    out = {
        'all_cells': cells,
        'by_kappa_010': [{'omega': c['omega'], 'R_raw': c['R_raw'],
                          'R_st': c['R_st']} for c in k010],
        'kuramoto_fit_raw': {'params': p_raw, 'mse': mse_raw},
        'kuramoto_fit_st': {'params': p_st, 'mse': mse_st},
        'kuramoto_theory_dc_uniform': float(np.pi * 0.10 / 4),
    }
    with open('thor_session_104_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nAnalysis → thor_session_104_analysis.json")


if __name__ == '__main__':
    main()
