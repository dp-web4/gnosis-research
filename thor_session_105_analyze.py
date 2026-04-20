#!/usr/bin/env python3
"""S105 analysis: combine S103/S104/S105 cells, test the κ-strength
enhancement hypothesis by comparing R_coh vs κ at fixed ω/κ ratios,
and against the measured Kuramoto order parameter R_kura."""
import json
import numpy as np


def load_all_cells():
    """Unified cell list from S103 sweep, S104 cells, and S105 cells.

    Returns list of dicts with:
        kappa, omega, ratio, R_raw, R_st, R_raw_sd, R_st_sd,
        R_angle_raw, R_angle_st, R_kura (optional), source, n_seeds, n_chunks.
    """
    cells = []

    # S98/S103 anchor: κ=0.10, ω=0.02 (ratio 0.2) — the canonical main cell.
    cells.append({
        'kappa': 0.10, 'omega': 0.02, 'ratio': 0.20,
        'R_raw': 0.375, 'R_st': 0.706,
        'R_raw_sd': 0.015, 'R_st_sd': 0.014,
        'R_angle_raw': 0.999, 'R_angle_st': 0.999,
        'R_kura': None,
        'source': 'S98/S103 main', 'n_seeds': 8, 'n_chunks': 100,
    })

    # S103 ω-sweep at κ=0.10.
    try:
        s103 = json.load(open('thor_session_103_sweep_fast_results.json'))
        for ow_str, c in s103['per_cell'].items():
            ow = float(ow_str)
            rs, ss = c['raw_seeds'], c['st_seeds']
            per_seed_R_raw = [m**2/(m**2+s**2) for m, s in
                              zip(rs['per_seed_mu_abs'], rs['per_seed_sigma_n'])]
            per_seed_R_st = [m**2/(m**2+s**2) for m, s in
                             zip(ss['per_seed_mu_abs'], ss['per_seed_sigma_n'])]
            cells.append({
                'kappa': 0.10, 'omega': ow, 'ratio': ow / 0.10,
                'R_raw': float(np.mean(per_seed_R_raw)),
                'R_st': float(np.mean(per_seed_R_st)),
                'R_raw_sd': float(np.std(per_seed_R_raw)),
                'R_st_sd': float(np.std(per_seed_R_st)),
                'R_angle_raw': None, 'R_angle_st': None,
                'R_kura': None,
                'source': f'S103 sweep ω={ow}', 'n_seeds': 8, 'n_chunks': 100,
            })
    except FileNotFoundError:
        pass

    # S104 cells.
    try:
        s104 = json.load(open('thor_session_104_kuramoto_results.json'))
        for label, c in s104['cells'].items():
            s = c['summary']
            cells.append({
                'kappa': c['kappa_phase'], 'omega': c['omega_spread'],
                'ratio': c['ratio_omega_over_kappa'],
                'R_raw': s['raw_R_coh_mean'], 'R_st': s['st_R_coh_mean'],
                'R_raw_sd': s['raw_R_coh_std'], 'R_st_sd': s['st_R_coh_std'],
                'R_angle_raw': s['cross_seed_R_angle_raw'],
                'R_angle_st': s['cross_seed_R_angle_st'],
                'R_kura': None,
                'source': f'S104 {label}', 'n_seeds': 8, 'n_chunks': 50,
            })
    except FileNotFoundError:
        pass

    # S105 cells (with R_kura).
    try:
        s105 = json.load(open('thor_session_105_kappa_strength_results.json'))
        for label, c in s105['cells'].items():
            s = c['summary']
            cells.append({
                'kappa': c['kappa_phase'], 'omega': c['omega_spread'],
                'ratio': c['ratio_omega_over_kappa'],
                'R_raw': s['raw_R_coh_mean'], 'R_st': s['st_R_coh_mean'],
                'R_raw_sd': s['raw_R_coh_std'], 'R_st_sd': s['st_R_coh_std'],
                'R_angle_raw': s['cross_seed_R_angle_raw'],
                'R_angle_st': s['cross_seed_R_angle_st'],
                'R_kura': s['R_kura_cross_seed_mean'],
                'R_kura_sd': s['R_kura_cross_seed_std'],
                'R_kura_within_seed_sd': s['R_kura_within_seed_mean_std'],
                'source': f'S105 {label}', 'n_seeds': 8, 'n_chunks': 50,
            })
    except FileNotFoundError:
        pass

    return cells


def group_by_ratio(cells, ratio_target, tol=0.02):
    """Cells at ω/κ ≈ ratio_target, sorted by κ."""
    sel = [c for c in cells if abs(c['ratio'] - ratio_target) < tol]
    return sorted(sel, key=lambda c: c['kappa'])


def fit_linear_kappa(cells, y_key='R_raw'):
    """Fit R = a + b·κ at fixed ratio. Returns (a, b, r2, n)."""
    k = np.array([c['kappa'] for c in cells])
    y = np.array([c[y_key] for c in cells])
    if len(k) < 2:
        return None
    A = np.column_stack([np.ones_like(k), k])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(np.sum((y - pred)**2))
    ss_tot = float(np.sum((y - y.mean())**2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return {'a': float(coef[0]), 'b': float(coef[1]), 'r2': r2, 'n': len(k)}


def bootstrap_correlation(xs, ys, n_boot=5000, seed=42):
    """Bootstrap CI for Pearson correlation."""
    rng = np.random.default_rng(seed)
    x = np.array(xs); y = np.array(ys)
    if len(x) < 3:
        return None
    rs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(x), len(x))
        if len(set(idx)) < 2:
            continue
        cx, cy = x[idx], y[idx]
        if cx.std() == 0 or cy.std() == 0:
            continue
        rs.append(np.corrcoef(cx, cy)[0, 1])
    rs = np.sort(rs)
    r_point = float(np.corrcoef(x, y)[0, 1])
    return {
        'r': r_point,
        'r_lo_95': float(rs[int(0.025 * len(rs))]),
        'r_hi_95': float(rs[int(0.975 * len(rs))]),
        'n': len(x),
    }


def main():
    cells = load_all_cells()
    print(f"Loaded {len(cells)} cells total.\n")

    # Ratio 0.8 ladder — the headline test for κ-strength enhancement.
    r08 = group_by_ratio(cells, 0.80)
    print("─" * 80)
    print("RATIO ω/κ = 0.80 ladder (just below Kuramoto cliff)")
    print("─" * 80)
    print(f"{'κ':>6} {'ω':>6} {'R_raw':>8} {'R_st':>8} {'R_ang_raw':>10} "
          f"{'R_ang_st':>10} {'R_kura':>8} {'source':<20}")
    for c in r08:
        rk = f"{c.get('R_kura', ''):>.3f}" if c.get('R_kura') is not None else '   —  '
        rar = c['R_angle_raw']
        ras = c['R_angle_st']
        rar_s = f"{rar:>.3f}" if rar is not None else '   —  '
        ras_s = f"{ras:>.3f}" if ras is not None else '   —  '
        print(f"{c['kappa']:>6.3f} {c['omega']:>6.3f} "
              f"{c['R_raw']:>8.3f} {c['R_st']:>8.3f} "
              f"{rar_s:>10} {ras_s:>10} {rk:>8} {c['source']:<20}")

    fit_raw = fit_linear_kappa(r08, 'R_raw')
    fit_st = fit_linear_kappa(r08, 'R_st')
    print(f"\nR_raw(κ) linear fit at ratio 0.8: a={fit_raw['a']:.3f}  b={fit_raw['b']:+.3f}  r²={fit_raw['r2']:.3f}  n={fit_raw['n']}")
    print(f"R_st (κ) linear fit at ratio 0.8: a={fit_st['a']:.3f}  b={fit_st['b']:+.3f}  r²={fit_st['r2']:.3f}  n={fit_st['n']}")

    # Ratio 0.2 ladder — plateau check.
    r02 = group_by_ratio(cells, 0.20)
    print("\n" + "─" * 80)
    print("RATIO ω/κ = 0.20 ladder (deep sync, should be at plateau)")
    print("─" * 80)
    print(f"{'κ':>6} {'ω':>6} {'R_raw':>8} {'R_st':>8} {'R_ang_raw':>10} "
          f"{'R_ang_st':>10} {'R_kura':>8} {'source':<20}")
    for c in r02:
        rk = f"{c.get('R_kura', ''):>.3f}" if c.get('R_kura') is not None else '   —  '
        rar = c['R_angle_raw']; ras = c['R_angle_st']
        rar_s = f"{rar:>.3f}" if rar is not None else '   —  '
        ras_s = f"{ras:>.3f}" if ras is not None else '   —  '
        print(f"{c['kappa']:>6.3f} {c['omega']:>6.3f} "
              f"{c['R_raw']:>8.3f} {c['R_st']:>8.3f} "
              f"{rar_s:>10} {ras_s:>10} {rk:>8} {c['source']:<20}")

    fit_raw02 = fit_linear_kappa(r02, 'R_raw')
    fit_st02 = fit_linear_kappa(r02, 'R_st')
    print(f"\nR_raw(κ) linear fit at ratio 0.2: a={fit_raw02['a']:.3f}  b={fit_raw02['b']:+.3f}  r²={fit_raw02['r2']:.3f}  n={fit_raw02['n']}")
    print(f"R_st (κ) linear fit at ratio 0.2: a={fit_st02['a']:.3f}  b={fit_st02['b']:+.3f}  r²={fit_st02['r2']:.3f}  n={fit_st02['n']}")

    # R_kura vs R_coh within S105 cells.
    s105_cells = [c for c in cells if 'S105' in c['source']]
    if s105_cells:
        print("\n" + "─" * 80)
        print("R_kura vs R_coh correlation (S105 only)")
        print("─" * 80)
        kura = np.array([c['R_kura'] for c in s105_cells])
        rraw = np.array([c['R_raw'] for c in s105_cells])
        rst = np.array([c['R_st'] for c in s105_cells])
        kappa = np.array([c['kappa'] for c in s105_cells])
        c_raw = bootstrap_correlation(kura, rraw)
        c_st = bootstrap_correlation(kura, rst)
        print(f"R_kura range across S105: [{kura.min():.3f}, {kura.max():.3f}] (Δ={kura.max()-kura.min():.3f})")
        print(f"R_raw  range across S105: [{rraw.min():.3f}, {rraw.max():.3f}] (Δ={rraw.max()-rraw.min():.3f})")
        print(f"κ      range across S105: [{kappa.min():.3f}, {kappa.max():.3f}] (Δ={kappa.max()-kappa.min():.3f})")
        print(f"R_kura vs R_raw: r={c_raw['r']:+.3f}  CI95 [{c_raw['r_lo_95']:+.3f}, {c_raw['r_hi_95']:+.3f}]  n={c_raw['n']}")
        print(f"R_kura vs R_st : r={c_st['r']:+.3f}  CI95 [{c_st['r_lo_95']:+.3f}, {c_st['r_hi_95']:+.3f}]  n={c_st['n']}")

        # Joint regression: R_raw = a + b·κ + c·R_kura.
        # If all the variance goes through R_kura, coefficient on κ → 0.
        # If κ has independent explanatory power, coefficient on κ stays large.
        print("\n  Joint regression R_raw = a + b·κ + c·R_kura:")
        A = np.column_stack([np.ones_like(kappa), kappa, kura])
        coef, res, rank, _ = np.linalg.lstsq(A, rraw, rcond=None)
        pred = A @ coef
        ss_res = float(np.sum((rraw - pred)**2))
        ss_tot = float(np.sum((rraw - rraw.mean())**2))
        r2_full = 1 - ss_res / ss_tot
        print(f"    a={coef[0]:+.3f}  b(κ)={coef[1]:+.3f}  c(R_kura)={coef[2]:+.3f}  r²={r2_full:.3f}")
        # Marginal — κ only
        Ak = np.column_stack([np.ones_like(kappa), kappa])
        ck, _, _, _ = np.linalg.lstsq(Ak, rraw, rcond=None)
        ss_res_k = float(np.sum((rraw - Ak @ ck)**2))
        r2_k = 1 - ss_res_k / ss_tot
        print(f"    κ-only:   a={ck[0]:+.3f}  b(κ)={ck[1]:+.3f}  r²={r2_k:.3f}")
        # Marginal — R_kura only
        Au = np.column_stack([np.ones_like(kura), kura])
        cu, _, _, _ = np.linalg.lstsq(Au, rraw, rcond=None)
        ss_res_u = float(np.sum((rraw - Au @ cu)**2))
        r2_u = 1 - ss_res_u / ss_tot
        print(f"    R_kura-only: a={cu[0]:+.3f}  c(R_kura)={cu[1]:+.3f}  r²={r2_u:.3f}")
        print(f"  Interpretation: ΔR²(κ over R_kura)  = {r2_full - r2_u:+.3f}")
        print(f"                  ΔR²(R_kura over κ)  = {r2_full - r2_k:+.3f}")

    # Save a compact output.
    out = {
        'cells': cells,
        'fits': {
            'ratio_0.80_R_raw': fit_raw,
            'ratio_0.80_R_st': fit_st,
            'ratio_0.20_R_raw': fit_raw02,
            'ratio_0.20_R_st': fit_st02,
        },
    }
    with open('thor_session_105_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=lambda x: float(x) if hasattr(x, '__float__') else str(x))
    print("\nAnalysis → thor_session_105_analysis.json")


if __name__ == '__main__':
    main()
