#!/usr/bin/env python3
"""S107 supplementary: rate vs precision decomposition for κ_C collapse.

Question: at κ_C=0.50 (S106), R_coh_RAW collapses 0.610 → 0.269 and
N_sw drops 820 → 156 per chunk. Is the collapse pure-rate (fewer events
to accumulate signal across) or does per-switch timing precision also
degrade?

Decomposition for ST detector:
  z_st = sum_k δ_k * e^{-i ω t_k}  where δ_k = ±1 (crossing direction)

  |<z_st>|_chunks = |chunk-averaged z_st|.

Per-switch signal density:
  ρ_sig = |<z_st>|^2 / <N_sw>
This is signal power per switch event. If oscillators decohere when
κ_C=0.50, ρ_sig should drop (each switch is less aligned with signal).
If pure-rate, ρ_sig should be ~similar but multiplied by fewer events.

We compute ρ_sig and N_sw across the S106 sweep and the S105 reference
points to see whether the κ_C=0.50 collapse is rate-driven or precision-
driven.
"""
import json
import numpy as np


def load_cell(json_path, label):
    src = json.load(open(json_path))
    cell = src['cells'][label]
    return cell


def per_seed_rho_and_rate(cell):
    """Return per-seed (rho_sig_st, mean_N_sw)."""
    out = []
    for seed_pack in cell['per_seed_z']:
        z_st = np.array([complex(r, i) for r, i in seed_pack['z_st']])
        n_sw = np.array(seed_pack['n_sw'])
        mu_z = z_st.mean()
        mean_nsw = float(n_sw.mean())
        rho = float(abs(mu_z)**2 / mean_nsw) if mean_nsw > 0 else 0.0
        out.append({
            'seed': seed_pack['seed'],
            'mu_st_abs': float(abs(mu_z)),
            'mean_N_sw': mean_nsw,
            'rho_sig_st': rho,
        })
    return out


def main():
    # All S106 κ_phase=0.30 cells
    rows = []
    s106 = json.load(open('thor_session_106_kappa_c_channel_results.json'))
    for label in ['kp030_kC000', 'kp030_kC005', 'kp030_kC030', 'kp030_kC050']:
        cell = s106['cells'][label]
        kC = cell['kappa_C']
        ps = per_seed_rho_and_rate(cell)
        rho = np.array([p['rho_sig_st'] for p in ps])
        nsw = np.array([p['mean_N_sw'] for p in ps])
        mu = np.array([p['mu_st_abs'] for p in ps])
        rows.append({
            'source': 'S106', 'label': label,
            'kappa_phase': 0.30, 'kappa_C': kC,
            'mean_N_sw': float(nsw.mean()),
            'mean_mu_st_abs': float(mu.mean()),
            'rho_sig_st_mean': float(rho.mean()),
            'rho_sig_st_std': float(rho.std()),
            'R_coh_st': cell['summary']['st_R_coh_mean'],
            'R_coh_raw': cell['summary']['raw_R_coh_mean'],
        })

    # S105 r08_k030 reference (κ_C=0.15 baseline)
    s105 = json.load(open('thor_session_105_kappa_strength_results.json'))
    cell = s105['cells']['r08_k030']
    ps = per_seed_rho_and_rate(cell)
    rho = np.array([p['rho_sig_st'] for p in ps])
    nsw = np.array([p['mean_N_sw'] for p in ps])
    mu = np.array([p['mu_st_abs'] for p in ps])
    rows.append({
        'source': 'S105', 'label': 'r08_k030',
        'kappa_phase': 0.30, 'kappa_C': 0.15,
        'mean_N_sw': float(nsw.mean()),
        'mean_mu_st_abs': float(mu.mean()),
        'rho_sig_st_mean': float(rho.mean()),
        'rho_sig_st_std': float(rho.std()),
        'R_coh_st': cell['summary']['st_R_coh_mean'],
        'R_coh_raw': cell['summary']['raw_R_coh_mean'],
    })

    # Sort by κ_C
    rows.sort(key=lambda r: r['kappa_C'])

    print("κ_p=0.30 ridge: signal/event ρ vs rate N_sw across κ_C")
    print("=" * 95)
    print(f"{'κ_C':>5} | {'src':>6} | {'<N_sw>':>7} | {'<|μ_st|>':>10} | "
          f"{'ρ_sig=|μ|²/N':>13} | {'R_coh_ST':>8} | {'R_coh_RAW':>9}")
    print("-" * 95)
    for r in rows:
        print(f"{r['kappa_C']:>5.2f} | {r['source']:>6} | "
              f"{r['mean_N_sw']:>7.0f} | "
              f"{r['mean_mu_st_abs']:>10.3f} | "
              f"{r['rho_sig_st_mean']:>13.4f} | "
              f"{r['R_coh_st']:>8.3f} | {r['R_coh_raw']:>9.3f}")

    # Decompose: at peak (κ_C=0.30) vs collapse (κ_C=0.50)
    peak = next(r for r in rows if r['kappa_C'] == 0.30)
    coll = next(r for r in rows if r['kappa_C'] == 0.50)

    rate_ratio = coll['mean_N_sw'] / peak['mean_N_sw']
    rho_ratio = coll['rho_sig_st_mean'] / peak['rho_sig_st_mean']
    R_ratio = coll['R_coh_st'] / peak['R_coh_st']
    # Check decomposition: |μ|² = ρ * N_sw
    # If R_coh ~ |μ|² / (|μ|² + σ_n²) and σ_n^2 ≈ N_sw (Poisson-like for ST),
    # then R_coh ~ ρ N / (ρ N + N) = ρ / (ρ + 1).
    # Rough sanity: predict R from ρ alone via R_pred = ρ/(ρ+1).

    print("\nκ_C=0.30 → κ_C=0.50 (peak → collapse) decomposition:")
    print(f"  Rate ratio (N_sw collapse / peak):       {rate_ratio:.3f}")
    print(f"  Per-event ρ_sig ratio (collapse/peak):   {rho_ratio:.3f}")
    print(f"  R_coh_ST ratio (collapse/peak):          {R_ratio:.3f}")
    if abs(rho_ratio - 1.0) < 0.20 and rate_ratio < 0.5:
        verdict = "RATE-DOMINATED: per-event signal density ~unchanged; collapse is fewer events."
    elif rho_ratio < 0.5 and rate_ratio > 0.7:
        verdict = "PRECISION-DOMINATED: events drop only modestly but each carries less signal."
    else:
        verdict = (f"BOTH: rate halved AND per-event signal density changed by {rho_ratio:.2f}×. "
                   "Cannot attribute collapse to a single channel.")
    print(f"  → {verdict}")

    out = {'rows': rows,
           'peak_to_collapse': {
               'rate_ratio': rate_ratio,
               'rho_ratio': rho_ratio,
               'R_coh_st_ratio': R_ratio,
               'verdict': verdict,
           }}
    with open('thor_session_107_decompose.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nSaved → thor_session_107_decompose.json")


if __name__ == '__main__':
    main()
