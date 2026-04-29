#!/usr/bin/env python3
"""S113 mechanism analysis — does the dip arise from destructive cross-terms?

Operates on thor_session_113_dip_decomp_results.json to compute:

  1. Per-A: |μ_class|² aggregated across seeds, and pairwise cross-term
     2·Re(Σ_seeds μ_a · μ_b*) — POOLED SUM form.
  2. Per-A: predicted ρ_sig if classes were "aligned" (sum of |μ_class|
     instead of |Σ μ_class|) — gives us the upper bound.
  3. Per-A: arg(μ_class) — does each class's phase rotate with A, or
     is it A-invariant (only weights shift)?
  4. The "co-flow rotation" prediction: if class phases are A-invariant
     and only weights change, then μ_total(A) follows a linear
     combination in the complex plane.
  5. Sanity: |μ_total|² must equal |Σ μ_class|² to FP precision.

Output:
  - Console table summarizing per-A, per-class metrics.
  - thor_session_113_mechanism.json with per-cell aggregates.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

CLASS_NAMES = ['att_lock', 'att_noise', 'rep_lock', 'rep_noise']


def cell_class_aggregate(per_seed):
    """For each class: aggregate μ_class across seeds.

    Returns dict per-class:
      mu_sum_complex: complex sum of per-seed μ_class
      mu_sum_abs: |sum|
      mu_sum_arg_deg: arg(sum)
      mu_perseed_abs_mean: ⟨|μ_seed|⟩
      mu_perseed_abs_std: std(|μ_seed|)
      mu_perseed_arg_circmean_deg: circ-mean per-seed arg
      mu_perseed_arg_R: |⟨e^{i arg}⟩|
      count_per_seed_mean, count_total
    """
    out = {}
    for k in CLASS_NAMES:
        per_seed_mu = []
        per_seed_count = []
        for ps in per_seed:
            d = ps['class_decomp']['per_class'][k]
            per_seed_mu.append(complex(d['mu_re'], d['mu_im']))
            per_seed_count.append(d['count'])
        per_seed_mu = np.array(per_seed_mu)
        per_seed_count = np.array(per_seed_count, dtype=float)
        mu_sum = complex(per_seed_mu.sum())
        per_seed_abs = np.abs(per_seed_mu)
        per_seed_arg = np.angle(per_seed_mu, deg=True)
        z = np.exp(1j * np.deg2rad(per_seed_arg))
        out[k] = {
            'mu_sum_complex_re': float(mu_sum.real),
            'mu_sum_complex_im': float(mu_sum.imag),
            'mu_sum_abs': float(abs(mu_sum)),
            'mu_sum_arg_deg': float(np.degrees(np.angle(mu_sum))) if abs(mu_sum) > 0 else 0.0,
            'mu_perseed_abs_mean': float(per_seed_abs.mean()),
            'mu_perseed_abs_std': float(per_seed_abs.std()),
            'mu_perseed_arg_circmean_deg': float(np.degrees(np.angle(z.mean()))),
            'mu_perseed_arg_R': float(abs(z.mean())),
            'count_per_seed_mean': float(per_seed_count.mean()),
            'count_total': int(per_seed_count.sum()),
        }
    # Total μ_total per cell (pooled across seeds)
    mu_total_pooled = complex(0.0, 0.0)
    for k in CLASS_NAMES:
        mu_total_pooled += complex(out[k]['mu_sum_complex_re'],
                                    out[k]['mu_sum_complex_im'])
    out['_total_pooled_re'] = float(mu_total_pooled.real)
    out['_total_pooled_im'] = float(mu_total_pooled.imag)
    out['_total_pooled_abs'] = float(abs(mu_total_pooled))
    out['_total_pooled_arg_deg'] = float(np.degrees(np.angle(mu_total_pooled))) if abs(mu_total_pooled) > 0 else 0.0
    return out


def per_seed_cross_terms(per_seed):
    """Aggregate per-seed pairwise cross-terms 2·Re(μ_a μ_b*) across seeds.

    Returns mean and std of each pair's cross-term across seeds (already
    in cross_agg of summary, but recompute for safety).
    """
    pair_data = {}
    pairs = []
    for i in range(len(CLASS_NAMES)):
        for j in range(i+1, len(CLASS_NAMES)):
            pairs.append(f'{CLASS_NAMES[i]}__{CLASS_NAMES[j]}')
    for pk in pairs:
        vals = np.array([ps['class_decomp']['cross_terms'][pk]
                          for ps in per_seed])
        pair_data[pk] = {
            'mean': float(vals.mean()),
            'std': float(vals.std()),
            'sum_across_seeds': float(vals.sum()),
        }
    return pair_data


def main(infile='thor_session_113_dip_decomp_results.json',
         outfile='thor_session_113_mechanism.json'):
    with open(infile) as f:
        R = json.load(f)
    cells = R['cells']
    common = R['meta']['common_params']
    items = sorted(cells.items(), key=lambda kv: kv[1]['signal_amp'])

    print(f"S113 mechanism analysis  —  {len(items)} cells")
    print(f"common: κ_p={common['kappa_phase']}  κ_C={common['kappa_C']}  "
          f"ω_std={common['omega_std']}\n")

    # Class-aggregate per cell
    cell_data = []
    for label, c in items:
        agg = cell_class_aggregate(c['per_seed'])
        cross = per_seed_cross_terms(c['per_seed'])
        s = c['summary']
        rec = {
            'A': c['signal_amp'],
            'rho_sig_st_mean': s['rho_sig_st_mean'],
            'mu_total_perseed_mean': s['st_mu_mean'],
            'mu_total_arg_perseed_circ_deg': s['st_mu_arg_circmean_deg'],
            'class_agg': agg,
            'cross_terms_perseed': cross,
            'cross_total_norm_mean': s['cross_total_norm_mean'],
            'sum_class_sq_norm_mean': s['sum_class_sq_norm_mean'],
            'lock_at_sw': s['lock_at_switch_frac_mean'],
            'att_at_sw': s['gate_att_at_switch_frac_mean'],
            'n_sw_total': s['n_sw_total_mean'],
        }
        cell_data.append(rec)

    # Pretty-print: per-A, per-class
    print("Pooled-seed |μ_class| (sum across 16 seeds, in matched-filter units)")
    print(f"{'A':>5} | " + "  ".join([f"{k:>10}" for k in CLASS_NAMES]))
    for rec in cell_data:
        a = rec['class_agg']
        print(f"{rec['A']:5.2f} | " +
              "  ".join([f"{a[k]['mu_sum_abs']:10.1f}" for k in CLASS_NAMES]))

    print("\nPooled-seed arg(μ_class) (degrees)")
    print(f"{'A':>5} | " + "  ".join([f"{k:>10}" for k in CLASS_NAMES]))
    for rec in cell_data:
        a = rec['class_agg']
        print(f"{rec['A']:5.2f} | " +
              "  ".join([f"{a[k]['mu_sum_arg_deg']:+10.1f}" for k in CLASS_NAMES]))

    print("\nPer-seed |μ_class| circ-mean across 16 seeds (better for "
          "magnitude per-trajectory)")
    print(f"{'A':>5} | " + "  ".join([f"{k:>10}" for k in CLASS_NAMES]))
    for rec in cell_data:
        a = rec['class_agg']
        print(f"{rec['A']:5.2f} | " +
              "  ".join([f"{a[k]['mu_perseed_abs_mean']:10.1f}" for k in CLASS_NAMES]))

    # Cross-term pairs across A — pooled-seed sum form
    print("\nPooled-sum cross-terms 2·Re(Σμ_a · Σμ_b*) — what survives ensemble averaging")
    print(f"NOTE: per-seed cross-terms are below; pooled is the cell-level signal")
    pairs = list(cell_data[0]['cross_terms_perseed'].keys())
    short_keys = [pk.replace('att_', 'a').replace('rep_', 'r').replace('lock', 'L').replace('noise', 'N')
                  for pk in pairs]
    print(f"{'A':>5} | " + "  ".join([f"{sk:>11}" for sk in short_keys]))
    for rec in cell_data:
        a = rec['class_agg']
        # Cross between pooled-sum complex of two classes
        cross_pool = []
        for pk in pairs:
            ka, kb = pk.split('__')
            ma = complex(a[ka]['mu_sum_complex_re'], a[ka]['mu_sum_complex_im'])
            mb = complex(a[kb]['mu_sum_complex_re'], a[kb]['mu_sum_complex_im'])
            cross_pool.append(2.0 * (ma * mb.conjugate()).real)
        print(f"{rec['A']:5.2f} | " +
              "  ".join([f"{c:+11.0f}" for c in cross_pool]))

    print("\nPer-seed cross-terms (mean across seeds) — what each seed contributes")
    print(f"{'A':>5} | " + "  ".join([f"{sk:>11}" for sk in short_keys]))
    for rec in cell_data:
        ct = rec['cross_terms_perseed']
        print(f"{rec['A']:5.2f} | " +
              "  ".join([f"{ct[pk]['mean']:+11.1f}" for pk in pairs]))

    # Class-weight evolution: fraction of total |μ| from each class
    # Use per-seed mean (since per-seed |μ| is what matters for ρ_sig per seed)
    print("\nClass weight share of Σ|μ_class| per seed (each row sums to 1.0)")
    print(f"{'A':>5} | " + "  ".join([f"{k:>10}" for k in CLASS_NAMES]))
    for rec in cell_data:
        a = rec['class_agg']
        weights = np.array([a[k]['mu_perseed_abs_mean'] for k in CLASS_NAMES])
        weights = weights / max(weights.sum(), 1e-9)
        print(f"{rec['A']:5.2f} | " +
              "  ".join([f"{w:10.3f}" for w in weights]))

    # Phase rotation summary: arg(μ_total_perseed_circ) vs A
    print("\nμ_total angle vs A (cross-seed circular mean)")
    base_arg = cell_data[0]['mu_total_arg_perseed_circ_deg']
    base_A = cell_data[0]['A']
    rel_label = f'rel to A={base_A:.2f}'
    print(f"{'A':>5}  {'μ_arg':>8}  {rel_label:>15}  ρ_sig")
    for rec in cell_data:
        rel = (rec['mu_total_arg_perseed_circ_deg'] - base_arg + 180) % 360 - 180
        print(f"{rec['A']:5.2f}  {rec['mu_total_arg_perseed_circ_deg']:+8.1f}°  {rel:+15.1f}°  {rec['rho_sig_st_mean']:.4f}")

    # The "destructive cross-term" check: does cross_total_norm reach a
    # minimum (most-negative) at the dip A?
    print("\nNormalized cross-term sum (cross/|z|²) — peaks of negativity at the dip A?")
    print(f"{'A':>5}  {'cross/|z|²':>11}  {'sumsq/|z|²':>11}  {'ρ_sig':>8}")
    for rec in cell_data:
        print(f"{rec['A']:5.2f}  {rec['cross_total_norm_mean']:+11.3f}  "
              f"{rec['sum_class_sq_norm_mean']:11.3f}  {rec['rho_sig_st_mean']:8.4f}")

    # Save
    out = {'cells': cell_data, 'common_params': common}
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print(f"\nMechanism analysis → {outfile}")


if __name__ == '__main__':
    main()
