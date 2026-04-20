#!/usr/bin/env python3
"""R_coh = |μ|²/(|μ|²+σ_n²) scaling across ω_spread.

Combines: ω_spread=0.02 from S98, and ω_spread ∈ {0.04, 0.08} from
the S103 fast sweep (once it finishes).

Reports per-cell:
 - Per-seed |μ| ± CV across seeds (mean angular coherence)
 - Per-seed σ_n ± CV
 - R_coh per seed + cross-seed mean and std
 - Per-seed |Φ_z(1)| vs theoretical prediction
 - Cross-seed angle coherence R_angle = |mean(exp(i·arg(<z>_seed)))|
"""
import json
import numpy as np


def per_seed_cplx(records, key):
    return [np.array([complex(p[0], p[1]) for p in s[key]]) for s in records]


def r_coh_per_seed(zs):
    out = []
    for z in zs:
        mu = z.mean()
        sig_n = np.sqrt(np.mean(np.abs(z - mu)**2))
        r = abs(mu)**2 / (abs(mu)**2 + sig_n**2)
        out.append({'mu_abs': float(abs(mu)), 'mu_angle_deg': float(np.degrees(np.angle(mu))),
                    'sigma_n': float(sig_n), 'R_coh': float(r)})
    return out


def complex_acf_lag1(z):
    mu = z.mean()  # don't demean — we want the plateau
    var = np.mean(np.abs(z)**2)
    ac = np.mean(z[:-1] * np.conj(z[1:])) / var
    return float(abs(ac))


def summarize_cell(zs_raw, zs_st, label):
    raw_stats = r_coh_per_seed(zs_raw)
    st_stats = r_coh_per_seed(zs_st)
    raw_angles = np.deg2rad([s['mu_angle_deg'] for s in raw_stats])
    st_angles = np.deg2rad([s['mu_angle_deg'] for s in st_stats])
    R_angle_raw = abs(np.mean(np.exp(1j * raw_angles)))
    R_angle_st = abs(np.mean(np.exp(1j * st_angles)))

    raw_r = [s['R_coh'] for s in raw_stats]
    st_r = [s['R_coh'] for s in st_stats]
    raw_mu = [s['mu_abs'] for s in raw_stats]
    st_mu = [s['mu_abs'] for s in st_stats]
    raw_sig = [s['sigma_n'] for s in raw_stats]
    st_sig = [s['sigma_n'] for s in st_stats]
    raw_phi1 = [complex_acf_lag1(z) for z in zs_raw]
    st_phi1 = [complex_acf_lag1(z) for z in zs_st]

    def mstd(v):
        return float(np.mean(v)), float(np.std(v))

    return {
        'label': label,
        'n_seeds': len(zs_raw),
        'raw': {
            'mu_mean': mstd(raw_mu)[0], 'mu_std': mstd(raw_mu)[1],
            'sigma_n_mean': mstd(raw_sig)[0], 'sigma_n_std': mstd(raw_sig)[1],
            'R_coh_mean': mstd(raw_r)[0], 'R_coh_std': mstd(raw_r)[1],
            'phi_z1_mean': mstd(raw_phi1)[0], 'phi_z1_std': mstd(raw_phi1)[1],
            'R_angle': float(R_angle_raw),
            'per_seed_angle_deg': [s['mu_angle_deg'] for s in raw_stats],
        },
        'st': {
            'mu_mean': mstd(st_mu)[0], 'mu_std': mstd(st_mu)[1],
            'sigma_n_mean': mstd(st_sig)[0], 'sigma_n_std': mstd(st_sig)[1],
            'R_coh_mean': mstd(st_r)[0], 'R_coh_std': mstd(st_r)[1],
            'phi_z1_mean': mstd(st_phi1)[0], 'phi_z1_std': mstd(st_phi1)[1],
            'R_angle': float(R_angle_st),
            'per_seed_angle_deg': [s['mu_angle_deg'] for s in st_stats],
        },
    }


def print_cell(s):
    L = s['label']
    r, st = s['raw'], s['st']
    print(f"\n  {L}:  ({s['n_seeds']} seeds)")
    print(f"    RAW  |μ|={r['mu_mean']:.4e} ± {r['mu_std']:.1e}  "
          f"σ_n={r['sigma_n_mean']:.4e} ± {r['sigma_n_std']:.1e}")
    print(f"         R_coh = {r['R_coh_mean']:.3f} ± {r['R_coh_std']:.3f}   "
          f"|Φ_z(1)| = {r['phi_z1_mean']:.3f}  "
          f"R_angle = {r['R_angle']:.3f}")
    print(f"    ST   |μ|={st['mu_mean']:.3f} ± {st['mu_std']:.3f}  "
          f"σ_n={st['sigma_n_mean']:.3f} ± {st['sigma_n_std']:.3f}")
    print(f"         R_coh = {st['R_coh_mean']:.3f} ± {st['R_coh_std']:.3f}   "
          f"|Φ_z(1)| = {st['phi_z1_mean']:.3f}  "
          f"R_angle = {st['R_angle']:.3f}")


def main():
    cells = []

    # ω_spread=0.02 from S98 main
    with open('thor_session_98_phase_drift_results.json') as f:
        s98 = json.load(f)
    z_raws_02 = per_seed_cplx(s98['main']['per_seed'], 'z_raw')
    z_sts_02 = per_seed_cplx(s98['main']['per_seed'], 'z_st')
    cells.append(('ω=0.02', 0.02, summarize_cell(z_raws_02, z_sts_02, 'ω_spread=0.02 (S98)')))

    # ω_spread ∈ {0.04, 0.08} from S103 fast sweep
    try:
        with open('thor_session_103_sweep_fast_results.json') as f:
            s103 = json.load(f)
        for ow_key in ['0.04', '0.08']:
            if ow_key in s103['per_cell']:
                ps = s103['per_cell'][ow_key]['per_seed']
                z_raws = [np.array([complex(p[0], p[1]) for p in s['z_raw']]) for s in ps]
                z_sts = [np.array([complex(p[0], p[1]) for p in s['z_st']]) for s in ps]
                cells.append((f'ω={ow_key}', float(ow_key),
                              summarize_cell(z_raws, z_sts, f'ω_spread={ow_key} (S103)')))
    except FileNotFoundError:
        print("(S103 sweep results not yet available.)")

    print("R_coh scaling across ω_spread  (A=0.30, σ=0.022)")
    print("=" * 72)
    for _, _, s in cells:
        print_cell(s)

    if len(cells) >= 2:
        print("\n" + "=" * 72)
        print("Scaling table  (compare R_coh and |μ|)")
        print("=" * 72)
        print(f"{'ω_spread':>10}  {'|μ|_RAW':>12}  {'R_coh RAW':>10}  "
              f"{'|μ|_ST':>8}  {'R_coh ST':>10}  {'R_angle(raw/st)':>16}")
        for label, ow, s in cells:
            r, st = s['raw'], s['st']
            print(f"  {ow:>8.3f}  {r['mu_mean']:>12.4e}  {r['R_coh_mean']:>10.3f}  "
                  f"{st['mu_mean']:>8.3f}  {st['R_coh_mean']:>10.3f}  "
                  f"{r['R_angle']:>7.3f}/{st['R_angle']:<7.3f}")
        # Log-log fit
        ows = [c[1] for c in cells]
        if len(ows) >= 2:
            print("\nLog-log fits  (slope for ∝ ω_spread^k):")
            for (chname, key) in [('|μ|_RAW', ('raw', 'mu_mean')),
                                    ('|μ|_ST', ('st', 'mu_mean')),
                                    ('σ_n_RAW', ('raw', 'sigma_n_mean')),
                                    ('σ_n_ST', ('st', 'sigma_n_mean')),
                                    ('R_coh_RAW', ('raw', 'R_coh_mean')),
                                    ('R_coh_ST', ('st', 'R_coh_mean'))]:
                values = [c[2][key[0]][key[1]] for c in cells]
                if all(v > 0 for v in values):
                    slope, intercept = np.polyfit(np.log(ows), np.log(values), 1)
                    print(f"  {chname:>10s}: slope = {slope:+.3f}")

    # Save
    out = {
        'meta': {'A': 0.30, 'sigma': 0.022,
                 'T_chunk_s': 4000.0, 'n_chunks_per_cell': 100},
        'cells': [{'omega_spread': ow, 'summary': s} for _, ow, s in cells],
    }
    with open('thor_session_103_r_coh_scaling.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nSaved → thor_session_103_r_coh_scaling.json")


if __name__ == '__main__':
    main()
