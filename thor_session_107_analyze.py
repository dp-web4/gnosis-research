#!/usr/bin/env python3
"""Thor Session #107 analysis: 2D Ridge Map across (κ_phase, κ_C) at ratio 0.8.

Pulls in:
  - S107: 8 new cells (kp=0.15 × kC ∈ {0.00, 0.05, 0.30, 0.50},
          kp=0.50 × kC ∈ {0.00, 0.05, 0.30, 0.50})
  - S106: kp=0.30 slice (kC ∈ {0.00, 0.05, 0.15, 0.30, 0.50})
  - S105: kp=0.15 kC=0.15 (r08_k015), kp=0.50 kC=0.15 (r08_k050)

Produces:
  1. 3×5 ridge-map table of R_coh_raw, R_coh_st, R_kura, N_sw.
  2. For each κ_phase slice: peak κ_C location, R_peak, R at κ_C=0.00 vs peak.
  3. Linear fits vs κ_phase at (a) κ_C=0.15 (the S105 default), (b) κ_C=0.30 (ridge).
     Compare slopes to see if κ_phase × κ_C is separable.
  4. Verdict on hypotheses A–D from runner.
"""
import json
import numpy as np


def linfit(xs, ys):
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    A = np.column_stack([xs, np.ones_like(xs)])
    (b, a), *_ = np.linalg.lstsq(A, ys, rcond=None)
    yhat = A @ [b, a]
    ss_res = float(np.sum((ys - yhat)**2))
    ss_tot = float(np.sum((ys - ys.mean())**2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return {'slope': float(b), 'intercept': float(a), 'r2': r2,
            'n': int(len(xs))}


def quadfit_peak(xs, ys):
    """Fit y = a*x^2 + b*x + c and return peak location x* = -b/(2a)."""
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    A = np.column_stack([xs**2, xs, np.ones_like(xs)])
    coef, *_ = np.linalg.lstsq(A, ys, rcond=None)
    a, b, c = [float(v) for v in coef]
    if abs(a) < 1e-9:
        return {'a': a, 'b': b, 'c': c, 'peak_x': None, 'peak_y': None,
                'note': 'nearly linear — no extremum'}
    xstar = -b / (2*a)
    ystar = a*xstar**2 + b*xstar + c
    yhat = A @ coef
    ss_res = float(np.sum((ys - yhat)**2))
    ss_tot = float(np.sum((ys - ys.mean())**2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    curvature = 'peak (concave)' if a < 0 else 'bowl (convex)'
    return {'a': a, 'b': b, 'c': c,
            'peak_x': float(xstar), 'peak_y': float(ystar),
            'r2': r2, 'curvature': curvature}


def get_cell_summary(source_json, label):
    return source_json['cells'][label]['summary']


def get_cell(source_json, label):
    return source_json['cells'][label]


def per_seed_rho_st(cell):
    """Per-seed signal-density-per-switch ρ_st = |<z_st>|^2 / <N_sw>."""
    rhos = []
    nsws = []
    mus = []
    for seed_pack in cell['per_seed_z']:
        z_st = np.array([complex(r, i) for r, i in seed_pack['z_st']])
        n_sw = np.array(seed_pack['n_sw'])
        mu_z = z_st.mean()
        mean_nsw = float(n_sw.mean())
        rhos.append(abs(mu_z)**2 / mean_nsw if mean_nsw > 0 else 0.0)
        nsws.append(mean_nsw)
        mus.append(abs(mu_z))
    return {'rho_mean': float(np.mean(rhos)),
            'rho_std': float(np.std(rhos)),
            'nsw_mean': float(np.mean(nsws)),
            'mu_st_mean': float(np.mean(mus))}


def get_row_from(src, label, kp, kC, source_name):
    cell = src['cells'][label]
    summary = cell['summary']
    rho = per_seed_rho_st(cell)
    return {
        'kappa_phase': kp, 'kappa_C': kC, 'source': source_name,
        'raw_R': summary['raw_R_coh_mean'],
        'raw_R_sd': summary['raw_R_coh_std'],
        'st_R': summary['st_R_coh_mean'],
        'st_R_sd': summary['st_R_coh_std'],
        'R_angle_raw': summary['cross_seed_R_angle_raw'],
        'R_angle_st': summary['cross_seed_R_angle_st'],
        'R_kura': summary['R_kura_cross_seed_mean'],
        'R_kura_sd': summary['R_kura_cross_seed_std'],
        'N_sw_median': float(np.median(summary['n_sw_per_seed'])),
        'N_sw_mean': rho['nsw_mean'],
        'mu_st_mean': rho['mu_st_mean'],
        'rho_st_mean': rho['rho_mean'],
        'rho_st_std': rho['rho_std'],
    }


def main():
    s107 = json.load(open('thor_session_107_ridge_map_results.json'))
    s106 = json.load(open('thor_session_106_kappa_c_channel_results.json'))
    s105 = json.load(open('thor_session_105_kappa_strength_results.json'))

    # Compose the 3×5 grid.
    # kp_phase rows: 0.15, 0.30, 0.50
    # kC cols:      0.00, 0.05, 0.15, 0.30, 0.50
    grid = {}
    # kp=0.15 row
    grid[(0.15, 0.00)] = get_row_from(s107, 'kp015_kC000', 0.15, 0.00, 'S107')
    grid[(0.15, 0.05)] = get_row_from(s107, 'kp015_kC005', 0.15, 0.05, 'S107')
    grid[(0.15, 0.15)] = get_row_from(s105, 'r08_k015',    0.15, 0.15, 'S105 (recycled)')
    grid[(0.15, 0.30)] = get_row_from(s107, 'kp015_kC030', 0.15, 0.30, 'S107')
    grid[(0.15, 0.50)] = get_row_from(s107, 'kp015_kC050', 0.15, 0.50, 'S107')
    # kp=0.30 row (all from S106; kC=0.15 is S105 r08_k030 recycled by S106)
    grid[(0.30, 0.00)] = get_row_from(s106, 'kp030_kC000', 0.30, 0.00, 'S106')
    grid[(0.30, 0.05)] = get_row_from(s106, 'kp030_kC005', 0.30, 0.05, 'S106')
    grid[(0.30, 0.15)] = get_row_from(s105, 'r08_k030',    0.30, 0.15, 'S105 (recycled)')
    grid[(0.30, 0.30)] = get_row_from(s106, 'kp030_kC030', 0.30, 0.30, 'S106')
    grid[(0.30, 0.50)] = get_row_from(s106, 'kp030_kC050', 0.30, 0.50, 'S106')
    # kp=0.50 row
    grid[(0.50, 0.00)] = get_row_from(s107, 'kp050_kC000', 0.50, 0.00, 'S107')
    grid[(0.50, 0.05)] = get_row_from(s107, 'kp050_kC005', 0.50, 0.05, 'S107')
    grid[(0.50, 0.15)] = get_row_from(s105, 'r08_k050',    0.50, 0.15, 'S105 (recycled)')
    grid[(0.50, 0.30)] = get_row_from(s107, 'kp050_kC030', 0.50, 0.30, 'S107')
    grid[(0.50, 0.50)] = get_row_from(s107, 'kp050_kC050', 0.50, 0.50, 'S107')

    # --- Ridge table ---
    kps = [0.15, 0.30, 0.50]
    kCs = [0.00, 0.05, 0.15, 0.30, 0.50]
    print("\n" + "=" * 100)
    print("2D RIDGE MAP — RAW R_coh (ratio ω/κ_phase = 0.80, A=0.30, σ=0.022)")
    print("=" * 100)
    print(f"{'':>10} | " + " | ".join([f"κ_C={kC:.2f}" for kC in kCs]) + " | peak κ_C* | R_peak")
    print("-" * 100)
    slice_fits_raw = {}
    slice_fits_st = {}
    for kp in kps:
        raw_row = [grid[(kp, kC)]['raw_R'] for kC in kCs]
        st_row = [grid[(kp, kC)]['st_R'] for kC in kCs]
        fit_raw = quadfit_peak(kCs, raw_row)
        fit_st = quadfit_peak(kCs, st_row)
        slice_fits_raw[kp] = fit_raw
        slice_fits_st[kp] = fit_st
        peak_s = f"{fit_raw['peak_x']:.3f}" if fit_raw['peak_x'] is not None else 'NA'
        peak_y_s = f"{fit_raw['peak_y']:.3f}" if fit_raw.get('peak_y') is not None else 'NA'
        row_s = " | ".join([f"{v:6.3f}" for v in raw_row])
        print(f"κ_p={kp:.2f} | {row_s} |    {peak_s}  |  {peak_y_s}")

    print("\n" + "=" * 100)
    print("2D RIDGE MAP — ST R_coh (ratio ω/κ_phase = 0.80)")
    print("=" * 100)
    print(f"{'':>10} | " + " | ".join([f"κ_C={kC:.2f}" for kC in kCs]) + " | peak κ_C* | R_peak")
    print("-" * 100)
    for kp in kps:
        st_row = [grid[(kp, kC)]['st_R'] for kC in kCs]
        fit_st = slice_fits_st[kp]
        peak_s = f"{fit_st['peak_x']:.3f}" if fit_st['peak_x'] is not None else 'NA'
        peak_y_s = f"{fit_st['peak_y']:.3f}" if fit_st.get('peak_y') is not None else 'NA'
        row_s = " | ".join([f"{v:6.3f}" for v in st_row])
        print(f"κ_p={kp:.2f} | {row_s} |    {peak_s}  |  {peak_y_s}")

    # --- Horizontal fits: R vs κ_phase at fixed κ_C ---
    print("\n" + "=" * 100)
    print("LINEAR FITS vs κ_phase (n=3 per fit; slopes only indicative)")
    print("=" * 100)
    hfits_raw = {}
    hfits_st = {}
    for kC in kCs:
        raw_col = [grid[(kp, kC)]['raw_R'] for kp in kps]
        st_col  = [grid[(kp, kC)]['st_R']  for kp in kps]
        hfits_raw[kC] = linfit(kps, raw_col)
        hfits_st[kC]  = linfit(kps, st_col)
        print(f"κ_C={kC:.2f}: dR_raw/dκ_phase = {hfits_raw[kC]['slope']:+.3f}  r²={hfits_raw[kC]['r2']:.2f}"
              f"   |   dR_st/dκ_phase = {hfits_st[kC]['slope']:+.3f}  r²={hfits_st[kC]['r2']:.2f}")

    # S105 reference for context: slope at κ_C=0.15 was +0.943 over 6 kp points.
    print(f"\n  Reference (S105, κ_C=0.15, 6 kp points): dR_raw/dκ_phase = +0.943 (r²=0.89)")

    # --- Peak position vs κ_phase ---
    print("\n" + "=" * 100)
    print("κ_C PEAK POSITION SHIFT WITH κ_phase (quadratic fits, 5 points per slice)")
    print("=" * 100)
    for kp in kps:
        fr = slice_fits_raw[kp]
        fs = slice_fits_st[kp]
        p_raw = f"{fr['peak_x']:.3f}" if fr['peak_x'] is not None else 'NA'
        p_st  = f"{fs['peak_x']:.3f}" if fs['peak_x'] is not None else 'NA'
        print(f"κ_p={kp:.2f}: peak κ_C* = {p_raw} (RAW)   {p_st} (ST)   "
              f"r²_raw={fr.get('r2', float('nan')):.2f}  r²_st={fs.get('r2', float('nan')):.2f}")

    # --- Verdict ---
    peaks_raw = [slice_fits_raw[kp]['peak_x'] for kp in kps if slice_fits_raw[kp]['peak_x'] is not None]
    peak_spread = max(peaks_raw) - min(peaks_raw) if len(peaks_raw) > 1 else 0
    print("\n" + "=" * 100)
    print("VERDICT")
    print("=" * 100)
    print(f"Peak κ_C* spread across κ_phase slices: {peak_spread:.3f}")
    if peak_spread < 0.10:
        verdict_A = "A: κ_C peak APPROXIMATELY STABLE across κ_phase (spread < 0.10)"
    elif peaks_raw[0] > peaks_raw[-1] + 0.10:
        verdict_A = "B: κ_C peak SHIFTS DOWN with κ_phase (weak→strong κ_phase moves peak lower)"
    elif peaks_raw[0] + 0.10 < peaks_raw[-1]:
        verdict_A = "C: κ_C peak SHIFTS UP with κ_phase (weak→strong κ_phase moves peak higher)"
    else:
        verdict_A = "MIXED: peak shifts but not monotonically"
    print(f"  {verdict_A}")

    # Check hypothesis D: is kp=0.15 monotone rather than peaked?
    fr015 = slice_fits_raw[0.15]
    kp015_row = [grid[(0.15, kC)]['raw_R'] for kC in kCs]
    is_monotone_015 = all(kp015_row[i+1] >= kp015_row[i] - 0.02 for i in range(len(kp015_row)-1))
    if is_monotone_015:
        verdict_D = "D (partial): κ_p=0.15 slice is MONOTONE — peak emerges only at strong κ_phase"
    else:
        verdict_D = "D rejected: κ_p=0.15 slice has a peak (non-monotone)"
    print(f"  {verdict_D}")
    kp030_row = [grid[(0.30, kC)]['raw_R'] for kC in kCs]
    kp050_row = [grid[(0.50, kC)]['raw_R'] for kC in kCs]
    print(f"  κ_p=0.15 raw row: {[f'{v:.3f}' for v in kp015_row]}")
    print(f"  κ_p=0.30 raw row: {[f'{v:.3f}' for v in kp030_row]}")
    print(f"  κ_p=0.50 raw row: {[f'{v:.3f}' for v in kp050_row]}")

    # --- Rate-vs-precision decomposition ---
    # ρ_st = |<z_st>|^2 / <N_sw>  measures signal density per switch event.
    # If R_coh peak is rate-driven, ρ_st should be flat through the peak.
    # If precision-driven, ρ_st should rise into the peak.
    print("\n" + "=" * 100)
    print("ρ_st (signal-per-switch) and N_sw (event rate) — rate vs precision decomposition")
    print("=" * 100)
    print(f"{'':>10} | " + " | ".join([f"κ_C={kC:.2f}" for kC in kCs]))
    print("-" * 100)
    for kp in kps:
        nsw_row = [grid[(kp, kC)]['N_sw_mean'] for kC in kCs]
        rho_row = [grid[(kp, kC)]['rho_st_mean'] for kC in kCs]
        nsw_str = " | ".join([f"{v:6.0f}" for v in nsw_row])
        rho_str = " | ".join([f"{v:6.4f}" for v in rho_row])
        print(f"κ_p={kp:.2f}  N_sw    | {nsw_str}")
        print(f"          ρ_st    | {rho_str}")
        # Crossover diagnostic: at peak κ_C*, ρ rising and N falling.
        peak_kC = slice_fits_raw[kp]['peak_x']
        print(f"           (peak κ_C*={peak_kC:.3f}, R_peak={slice_fits_raw[kp]['peak_y']:.3f})")
        print()

    # --- Save ---
    out = {
        'grid': [grid[(kp, kC)] | {'kappa_phase': kp, 'kappa_C': kC} for kp in kps for kC in kCs],
        'slice_peak_fits_raw': {str(kp): slice_fits_raw[kp] for kp in kps},
        'slice_peak_fits_st': {str(kp): slice_fits_st[kp] for kp in kps},
        'horizontal_linfits_raw': {str(kC): hfits_raw[kC] for kC in kCs},
        'horizontal_linfits_st': {str(kC): hfits_st[kC] for kC in kCs},
        'verdict_peak_shift': verdict_A,
        'verdict_kp015_shape': verdict_D,
        'peak_spread': peak_spread,
    }
    with open('thor_session_107_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nAnalysis → thor_session_107_analysis.json")


if __name__ == '__main__':
    main()
