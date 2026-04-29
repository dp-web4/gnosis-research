#!/usr/bin/env python3
"""S113 analysis: characterize the A-dependent ρ_sig dip via switch-class
decomposition and matched-filter angle rotation.

Output:
  - Tidy table: A, ρ_sig, |μ_st|, μ_arg, R_ang, lock@sw, att@sw,
    per-class |μ| and arg, per-class fraction.
  - Cross-term decomposition: |μ_total|² = Σ |μ_class|² + Σ 2·Re(μ_a μ_b*)
    Show normalized cross-term sum per A.
  - Class-pair cross-terms: which pair drives the negative cross-term?
  - Predict ρ_sig from per-class data alone, validate.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)


def analyze(infile='thor_session_113_dip_decomp_results.json',
            outfile='thor_session_113_analysis.json'):
    with open(infile) as f:
        R = json.load(f)
    cells = R['cells']
    common = R['meta']['common_params']

    # Sort cells by A
    items = sorted(cells.items(), key=lambda kv: kv[1]['signal_amp'])

    print(f"Thor Session #113 analysis — {len(items)} cells")
    print(f"Common: κ_p={common['kappa_phase']}  κ_C={common['kappa_C']}  "
          f"ω_std={common['omega_std']}  σ={common['sigma']}  "
          f"f_s={common['signal_freq']}")
    print(f"        {common['n_seeds']} seeds × {common['n_chunks']} chunks "
          f"= {common['n_seeds']*common['n_chunks']} chunk-trials per A\n")

    print(f"=" * 130)
    print(f"{'A':>5} {'ρ_sig':>7} {'|μ_st|':>7} {'μ_arg°':>7} {'R_ang':>6} "
          f"{'<Nsw>':>6} {'lock@sw':>7} {'att@sw':>7} {'lock_g':>7} "
          f"{'<R_k>':>6} {'cross/|z|²':>10} {'sumsq/|z|²':>10}")
    print(f"-" * 130)
    rows = []
    for label, c in items:
        s = c['summary']
        A = c['signal_amp']
        rows.append({
            'A': A,
            'rho_sig': s['rho_sig_st_mean'],
            'rho_sig_std': s['rho_sig_st_std'],
            'mu_st': s['st_mu_mean'],
            'mu_arg': s['st_mu_arg_circmean_deg'],
            'R_ang': s['st_mu_arg_R'],
            'n_sw': s['n_sw_total_mean'],
            'lock_at_sw': s['lock_at_switch_frac_mean'],
            'att_at_sw': s['gate_att_at_switch_frac_mean'],
            'lock_global': s['lock_frac_global_mean'],
            'R_kura': s['kura_mean_mean'],
            'cross_norm': s['cross_total_norm_mean'],
            'sumsq_norm': s['sum_class_sq_norm_mean'],
            'class_agg': s['class_agg'],
            'cross_agg': s['cross_agg'],
        })
        print(f"{A:5.2f} {s['rho_sig_st_mean']:7.4f} {s['st_mu_mean']:7.2f} "
              f"{s['st_mu_arg_circmean_deg']:+7.1f} {s['st_mu_arg_R']:6.3f} "
              f"{s['n_sw_total_mean']:6.0f} "
              f"{s['lock_at_switch_frac_mean']:7.3f} "
              f"{s['gate_att_at_switch_frac_mean']:7.3f} "
              f"{s['lock_frac_global_mean']:7.3f} "
              f"{s['kura_mean_mean']:6.3f} "
              f"{s['cross_total_norm_mean']:+10.3f} "
              f"{s['sum_class_sq_norm_mean']:10.3f}")

    # Per-class table: |μ| per seed (mean), arg, fraction
    print()
    print(f"=" * 130)
    print("Per-class |μ| (per-seed mean) — magnitude in matched-filter units")
    print(f"-" * 130)
    cls_names = ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']
    print(f"{'A':>5} | " +
          "  ".join([f"{n:>10}" for n in cls_names]))
    for r in rows:
        ca = r['class_agg']
        cells_str = "  ".join([f"{ca[n]['mu_abs_per_seed_mean']:10.2f}"
                                for n in cls_names])
        print(f"{r['A']:5.2f} | {cells_str}")

    print()
    print("Per-class arg(μ) circular mean across seeds — degrees")
    print(f"-" * 130)
    print(f"{'A':>5} | " +
          "  ".join([f"{n:>10}" for n in cls_names]) +
          f" | (cross-seed phase R)")
    for r in rows:
        ca = r['class_agg']
        cells_str = "  ".join([
            f"{ca[n]['mu_arg_per_seed_circmean_deg']:+10.1f}"
            for n in cls_names])
        Rs = "  ".join([f"{ca[n]['mu_arg_R_seedpair']:.2f}"
                          for n in cls_names])
        print(f"{r['A']:5.2f} | {cells_str} | {Rs}")

    print()
    print("Per-class fraction of switches")
    print(f"-" * 130)
    print(f"{'A':>5} | " +
          "  ".join([f"{n:>10}" for n in cls_names]))
    for r in rows:
        ca = r['class_agg']
        cells_str = "  ".join([f"{ca[n]['fraction_of_sw']:10.3f}"
                                for n in cls_names])
        print(f"{r['A']:5.2f} | {cells_str}")

    # Cross-term pairs — which dominates?
    print()
    print(f"=" * 130)
    print("Pairwise cross-terms 2·Re(μ_a μ_b*) — per-seed mean")
    print(f"-" * 130)
    cross_keys = list(rows[0]['cross_agg'].keys())
    print(f"{'A':>5} | " +
          "  ".join([f"{k.replace('att_','a').replace('rep_','r').replace('lock','L').replace('noise','N'):>10}"
                      for k in cross_keys]))
    for r in rows:
        cells_str = "  ".join([f"{r['cross_agg'][ck]['mean']:+10.1f}"
                                for ck in cross_keys])
        print(f"{r['A']:5.2f} | {cells_str}")

    # ρ_sig prediction from per-class — we have the cross_total_norm and sumsq_norm
    # |μ_total|² = sumsq · |z|² + cross · |z|²; but each seed normalizes its own.
    # Let's also compute pooled-cross as sum of pairwise means / mean(|z|²).
    print()
    print("=" * 130)
    print("Identity check (per-cell): cross/|z|² + sumsq/|z|² should ≈ 1")
    print(f"-" * 130)
    for r in rows:
        total = r['cross_norm'] + r['sumsq_norm']
        print(f"  A={r['A']:.2f}: sumsq={r['sumsq_norm']:.3f}  cross={r['cross_norm']:+.3f}  "
              f"total={total:.3f}")

    # Find the dip: A with min ρ_sig in [0.20, 0.50]
    candidates = [r for r in rows if 0.15 <= r['A'] <= 0.50]
    if len(candidates) > 0:
        rho_arr = np.array([r['rho_sig'] for r in candidates])
        A_arr = np.array([r['A'] for r in candidates])
        i_min = int(np.argmin(rho_arr))
        i_max = int(np.argmax(rho_arr))
        print()
        print("=" * 130)
        print(f"In A ∈ [{A_arr.min():.2f}, {A_arr.max():.2f}]:")
        print(f"  ρ_sig PEAK at A={A_arr[i_max]:.2f}: {rho_arr[i_max]:.4f}")
        print(f"  ρ_sig DIP  at A={A_arr[i_min]:.2f}: {rho_arr[i_min]:.4f}")
        print(f"  Drop: {(1 - rho_arr[i_min]/rho_arr[i_max])*100:.1f}%")

    # μ_arg rotation: across all A, how much does it rotate?
    args = np.array([r['mu_arg'] for r in rows])
    # unwrap-ish: shift to relative
    rel = args - args[0]
    rel = (rel + 180) % 360 - 180
    print()
    print("μ_arg rotation across A:")
    print(f"  A    mu_arg   rel_to_first")
    for r, rl in zip(rows, rel):
        print(f"  {r['A']:.2f}  {r['mu_arg']:+7.1f}°  {rl:+7.1f}°")

    out = {
        'rows': rows,
        'common_params': common,
    }
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print(f"\nAnalysis → {outfile}")


if __name__ == '__main__':
    analyze()
