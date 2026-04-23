#!/usr/bin/env python3
"""S112 analyzer: within-seed Kuramoto cliff at A=0.50.

Inputs:  thor_session_112_omega_cliff_results.json
Outputs: thor_session_112_analysis.json + stdout report.

Verdicts:
  P1 failure_fraction(ω_std) monotonic at A=0.50; cliff 0.12–0.18.
  P2 failure_fraction(A) at ω_std=0.19 monotonic; low-A keeps locking.
  P3 per-seed |μ_st| distribution bimodal near cliff.
  P4 mu_st (succeeding) holds across ω_std.
  P5 ρ_sig_succ approximately flat in ω_std; remaining variation via N_sw.

Cross-check with S111 data to re-interpret the A-sweep variance.
"""
import json
import sys
import numpy as np

sys.stdout.reconfigure(line_buffering=True)


def cell_A_key(cell):
    return (cell.get('exp',''), cell['signal_amp'], cell['omega_std_target'])


def main():
    with open('thor_session_112_omega_cliff_results.json') as f:
        data = json.load(f)
    cells = data['cells']

    # Separate experiments
    exp_A = []  # ω_std sweep at A=0.50
    exp_B = []  # A sweep at ω_std=0.19
    for lbl, c in cells.items():
        if c['exp'] == 'A':
            exp_A.append((lbl, c))
        else:
            exp_B.append((lbl, c))
    exp_A.sort(key=lambda kv: kv[1]['omega_std_target'])
    exp_B.sort(key=lambda kv: kv[1]['signal_amp'])

    print("=" * 96)
    print(" Experiment A: ω_std sweep at A=0.50")
    print(" (ridge κ_p=0.30, κ_C=0.30, ratio 0.8, n_seeds=10, n_chunks=25)")
    print("=" * 96)
    print(f"{'ω_std':>6} {'fail':>5} {'frac':>6} {'lock_frac':>10} {'R_kura':>8} "
          f"{'mod_lock':>10} {'mod_lock_s':>12} {'|μ_st|_s':>10} "
          f"{'ρ_sig':>9} {'ρ_sig_s':>9} {'<Nsw>':>7}")

    summary_A = []
    for lbl, c in exp_A:
        s = c['summary']
        omstd = c['omega_std_target']
        row = {
            'omega_std': omstd,
            'n_fail': s['n_fail'], 'n_total': s['n_total'],
            'fail_frac': s['n_fail'] / s['n_total'],
            'detection_frac': s['detection_fraction'],
            'lock_frac_mean': s['lock_frac_global_mean'],
            'R_kura_mean': s['kura_mean_mean'],
            'mod_lock_mean': s['mod_amp_at_fs_lock_mean'],
            'mod_lock_mean_succ': s['mod_lock_mean_succeeding'],
            'mu_st_mean_succ': s['mu_st_mean_succeeding'],
            'rho_sig_mean': s['rho_sig_st_mean'],
            'rho_sig_mean_succ': s['rho_sig_mean_succeeding'],
            'n_sw_total_mean': s['n_sw_total_mean'],
        }
        summary_A.append(row)
        print(f"{omstd:>6.3f} {s['n_fail']:>5} {row['fail_frac']:>6.2f} "
              f"{s['lock_frac_global_mean']:>10.3f} {s['kura_mean_mean']:>8.3f} "
              f"{s['mod_amp_at_fs_lock_mean']:>10.4f} "
              f"{s['mod_lock_mean_succeeding']:>12.4f} "
              f"{s['mu_st_mean_succeeding']:>10.3f} "
              f"{s['rho_sig_st_mean']:>9.4f} {s['rho_sig_mean_succeeding']:>9.4f} "
              f"{s['n_sw_total_mean']:>7.0f}")

    # P1: cliff location estimate
    ff = np.array([r['fail_frac'] for r in summary_A])
    omstd_arr = np.array([r['omega_std'] for r in summary_A])
    half_idx = np.searchsorted(ff, 0.5)
    if 0 < half_idx < len(ff):
        w0, w1 = omstd_arr[half_idx-1], omstd_arr[half_idx]
        f0, f1 = ff[half_idx-1], ff[half_idx]
        if f1 != f0:
            cliff_50 = w0 + (0.5 - f0) * (w1 - w0) / (f1 - f0)
        else:
            cliff_50 = (w0 + w1) / 2
    else:
        cliff_50 = float('nan')
    print(f"\n P1: cliff_50 (ω_std at fail_frac=0.5) = {cliff_50:.3f}")
    print(f"     textbook Δ_c = πκ/4 at κ=κ_p=0.30: {np.pi*0.3/4:.3f}")
    print(f"     effective (gate-modulated 50/50): {np.pi*0.3/8:.3f}")

    # P3/P4: per-seed distributions
    print("\n" + "=" * 96)
    print(" P3, P4: per-seed |μ_st| and mod_lock distributions")
    print("=" * 96)
    per_seed_sig = {}
    for lbl, c in exp_A:
        omstd = c['omega_std_target']
        ps = c['per_seed']
        mus = np.array([s['st_per_seed']['mu_abs'] for s in ps])
        mods = np.array([s['mod_amp_at_fs_lock'] for s in ps])
        print(f"\nω_std={omstd:.3f}  A=0.50")
        print(f"   mod_lock sorted: {np.round(sorted(mods),4).tolist()}")
        print(f"   |μ_st|  sorted: {np.round(sorted(mus),2).tolist()}")
        per_seed_sig[omstd] = {'mods': mods.tolist(), 'mus': mus.tolist()}

    print("\n" + "=" * 96)
    print(" Experiment B: A sweep at ω_std=0.19 (past-cliff seeds)")
    print("=" * 96)
    summary_B = []
    print(f"{'A':>6} {'fail':>5} {'frac':>6} {'lock_frac':>10} {'R_kura':>8} "
          f"{'mod_lock':>10} {'mod_lock_s':>12} {'|μ_st|_s':>10} "
          f"{'ρ_sig':>9} {'<Nsw>':>7}")
    for lbl, c in exp_B:
        s = c['summary']
        A = c['signal_amp']
        row = {
            'A': A,
            'n_fail': s['n_fail'], 'n_total': s['n_total'],
            'fail_frac': s['n_fail'] / s['n_total'],
            'lock_frac_mean': s['lock_frac_global_mean'],
            'R_kura_mean': s['kura_mean_mean'],
            'mod_lock_mean': s['mod_amp_at_fs_lock_mean'],
            'mod_lock_mean_succ': s['mod_lock_mean_succeeding'],
            'mu_st_mean_succ': s['mu_st_mean_succeeding'],
            'rho_sig_mean': s['rho_sig_st_mean'],
            'n_sw_total_mean': s['n_sw_total_mean'],
        }
        summary_B.append(row)
        print(f"{A:>6.2f} {s['n_fail']:>5} {row['fail_frac']:>6.2f} "
              f"{s['lock_frac_global_mean']:>10.3f} {s['kura_mean_mean']:>8.3f} "
              f"{s['mod_amp_at_fs_lock_mean']:>10.4f} "
              f"{s['mod_lock_mean_succeeding']:>12.4f} "
              f"{s['mu_st_mean_succeeding']:>10.3f} "
              f"{s['rho_sig_st_mean']:>9.4f} "
              f"{s['n_sw_total_mean']:>7.0f}")

    # P2: fail_frac vs A monotone? Cliff gets sharper at higher A?
    ff_B = np.array([r['fail_frac'] for r in summary_B])
    A_B = np.array([r['A'] for r in summary_B])
    # Also include the A=0.50 result from Experiment A (om_std=0.19)
    om019_row = None
    for r in summary_A:
        if abs(r['omega_std'] - 0.19) < 1e-6:
            om019_row = r
            break
    if om019_row is not None:
        ff_B_full = np.concatenate([ff_B, [om019_row['fail_frac']]])
        A_B_full = np.concatenate([A_B, [0.50]])
        sorti = np.argsort(A_B_full)
        ff_B_full = ff_B_full[sorti]
        A_B_full = A_B_full[sorti]
        print(f"\n P2: fail_frac vs A at ω_std=0.19 (incl. A=0.50 from expA):")
        print(f"   A:           {np.round(A_B_full,2).tolist()}")
        print(f"   fail_frac:   {np.round(ff_B_full,2).tolist()}")
        mono = np.all(np.diff(ff_B_full) >= -0.05)  # allow small noise
        print(f"   monotone (ε=0.05): {mono}")

    # P5: ρ_sig_succ approximately flat in ω_std?
    print("\n" + "=" * 96)
    print(" P5: ρ_sig succeeding-seed mean across ω_std (flat?)")
    print("=" * 96)
    rs = np.array([r['rho_sig_mean_succ'] for r in summary_A if r['rho_sig_mean_succ'] > 0])
    oms = np.array([r['omega_std'] for r in summary_A if r['rho_sig_mean_succ'] > 0])
    if len(rs) > 1:
        print(f"   ω_std: {np.round(oms,3).tolist()}")
        print(f"   ρ_sig_succ: {np.round(rs,4).tolist()}")
        cv = rs.std() / rs.mean()
        print(f"   mean={rs.mean():.4f}  std={rs.std():.4f}  CV={cv*100:.1f}%")

    # S111 cross-check: apply ω-binned failure classification to S111 data
    print("\n" + "=" * 96)
    print(" S111 Re-interpretation: filter failing seeds from A-sweep")
    print("=" * 96)
    try:
        with open('thor_session_111_dose_response_results.json') as f:
            s111 = json.load(f)
        print(f"{'A':>5} {'n_fail':>6} {'succ':>6} {'ρ_sig_all':>10} "
              f"{'ρ_sig_succ':>10} {'mu_st_succ':>11} {'Nsw_succ':>9}")
        s111_filtered = []
        for k in sorted(s111['cells'].keys(), key=lambda x: s111['cells'][x]['signal_amp']):
            c = s111['cells'][k]
            A = c['signal_amp']
            ps = c['per_seed']
            mod_arr = np.array([r['mod_amp_at_fs_lock'] for r in ps])
            succ = mod_arr >= 0.04
            n_fail = int((~succ).sum())
            if A == 0:
                # Null cell — don't "succ-filter"
                succ = np.ones(len(ps), dtype=bool)
            mu_arr = np.array([r['st_per_seed']['mu_abs'] for r in ps])
            nsw_arr = np.array([float(np.mean(r['n_sw_chunks'])) for r in ps])
            rho_arr = mu_arr**2 / np.maximum(nsw_arr, 1)
            rho_all = rho_arr.mean()
            rho_succ = rho_arr[succ].mean() if succ.any() else 0.0
            mu_succ = mu_arr[succ].mean() if succ.any() else 0.0
            nsw_succ = nsw_arr[succ].mean() if succ.any() else 0.0
            s111_filtered.append({
                'A': A, 'n_fail': n_fail, 'n_succ': int(succ.sum()),
                'rho_sig_all': float(rho_all),
                'rho_sig_succ': float(rho_succ),
                'mu_st_succ': float(mu_succ),
                'n_sw_succ': float(nsw_succ),
            })
            print(f"{A:>5.2f} {n_fail:>6} {int(succ.sum()):>6} "
                  f"{rho_all:>10.4f} {rho_succ:>10.4f} "
                  f"{mu_succ:>11.3f} {nsw_succ:>9.0f}")
    except Exception as e:
        print(f"(S111 cross-check skipped: {e})")
        s111_filtered = []

    out = {
        'exp_A_summary': summary_A,
        'exp_B_summary': summary_B,
        'per_seed_exp_A': per_seed_sig,
        'cliff_50_estimate_ω_std': float(cliff_50) if cliff_50 == cliff_50 else None,
        'delta_c_bare_kappa_p': float(np.pi * 0.3 / 4),
        'delta_c_effective_half_gate': float(np.pi * 0.3 / 8),
        's111_filtered_by_mod_lock': s111_filtered,
    }
    with open('thor_session_112_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nSaved → thor_session_112_analysis.json")


if __name__ == '__main__':
    main()
