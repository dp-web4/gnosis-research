#!/usr/bin/env python3
"""
Thor Session #103: ω_spread Sweep of τ_RAW (tests S102-P3)

Context
-------
S102's two-component fits (lags 1..30 of per-chunk MF residual-phase ACF,
T_chunk = 4000s) gave RAW exponential timescales τ ≈ 83 ks at A=0.30,
89 ks at A=0.40, 136 ks at A=0.50, all at ω_spread = 0.02.  ST stays
plateau-dominated (τ → ∞) at A ≥ 0.30.

Hypothesis (S102-P3): the RAW slow timescale is set by the N=4 collective-
oscillator beat frequency Δω = ω_spread.  Specifically τ_RAW ∝ 1/ω_spread.
Predictions at A=0.30, σ=0.022:
   ω_spread = 0.005  →  τ ≈ 320 ks   (4× slower)
   ω_spread = 0.02   →  τ ≈ 80 ks    (S102 baseline)
   ω_spread = 0.04   →  τ ≈ 40 ks    (2× faster)
   ω_spread = 0.08   →  τ ≈ 20 ks    (4× faster)

If the relation holds: collective-oscillator beating is the mechanism.
If it doesn't: the slow RAW residual has a different origin (possibly
intra-oscillator phase-locking dynamics, Kramers reset, or coupling-noise
cross-talk between C_mean and individual-oscillator phases).

Protocol
--------
For each ω_spread, A=0.30, σ=0.022, T_chunk=4000s, 8 seeds.
Per-seed lengths chosen so max lag covers ≥ 3·τ_predicted:
   ω_spread=0.005 → 250 chunks (lag window 996 ks)
   ω_spread=0.04  → 100 chunks (lag window 396 ks)
   ω_spread=0.08  → 60 chunks  (lag window 236 ks)
   ω_spread=0.02 reused from S98 main (8 × 100 chunks).

Compute (~25 µs/step):
   ω=0.005: 8 × 10.01 M = 80 M steps → ~33 min
   ω=0.04 : 8 ×  4.01 M = 32 M steps → ~13 min
   ω=0.08 : 8 ×  2.41 M = 19 M steps → ~ 8 min
   Total ≈ 54 min.

Outputs
-------
- per-cell summary stats (|⟨z⟩|, σ_n, switch rate)
- per-cell ACF curves at full lag depth
- two-component fits (plateau + exponential) per cell
- τ vs ω_spread test of inverse-proportionality

Side checks
-----------
- ST plateau at all ω_spread (does it survive narrow ω_spread?).
- per-seed Δω in the residual (is it ω_spread-dependent or noise-dependent?).
- per-chunk switch rate vs ω_spread (does narrower spread reduce switching?).
"""

import json
import numpy as np
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55


def run_cell(omega_spread, n_chunks, A=0.30, sigma=0.022, n_seeds=8,
             warmup=10_000, chunk_steps=40_000, dt=0.1,
             signal_freq=0.003, seed_base=103_000):
    """Per ω_spread cell: run n_seeds long trajectories, split into chunks."""
    total_steps = warmup + n_chunks * chunk_steps
    print(f"\n>> ω_spread={omega_spread}  A={A}  σ={sigma}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  "
          f"total_steps={total_steps}  seed_base={seed_base}")
    per_seed = []
    start = datetime.now()
    for seed in range(n_seeds):
        t0 = datetime.now()
        x = simulate(N=4, noise_std=sigma, steps=total_steps,
                     seed=seed_base + seed,
                     signal_freq=signal_freq, signal_amp=A,
                     omega_spread=omega_spread, dt=dt)
        xp = x[warmup:]
        assert len(xp) >= n_chunks * chunk_steps
        z_raw = np.zeros(n_chunks, dtype=complex)
        z_st = np.zeros(n_chunks, dtype=complex)
        n_sw = np.zeros(n_chunks, dtype=int)
        for c in range(n_chunks):
            chunk = xp[c*chunk_steps:(c+1)*chunk_steps]
            t_off = warmup + c * chunk_steps
            Ir, Qr = phase_coherent_IQ(chunk, dt, signal_freq, t_offset=t_off)
            Is, Qs, n = switch_timing_IQ(chunk, dt, signal_freq,
                                          t_offset=t_off, threshold=C_THRESHOLD)
            z_raw[c] = Ir + 1j*Qr
            z_st[c] = Is + 1j*Qs
            n_sw[c] = n
        elapsed = (datetime.now() - t0).total_seconds()
        per_seed.append({
            'seed': seed_base + seed,
            'n_chunks': n_chunks,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw': n_sw,
        })
        print(f"   seed={seed_base + seed:6d}  {elapsed:5.1f}s   "
              f"|⟨z_raw⟩|={np.abs(z_raw.mean()):.4e}   "
              f"|⟨z_st⟩|={np.abs(z_st.mean()):.3f}   "
              f"N_sw/chunk={n_sw.mean():.1f}")
    print(f"   ω_spread={omega_spread} total {(datetime.now()-start).total_seconds():.0f}s")
    return per_seed


def residual_phase_acf(z_list, max_lag):
    """S99 linear-Δω method per seed, then circular-pool across seeds."""
    num = np.zeros(max_lag + 1, dtype=complex)
    cnt = np.zeros(max_lag + 1, dtype=int)
    per_seed = []
    for z in z_list:
        phi = np.unwrap(np.angle(z))
        k = np.arange(len(phi))
        slope, intercept = np.polyfit(k, phi, 1)
        pred = slope * k + intercept
        resid = phi - pred
        u = np.exp(1j * resid)
        seed_num = np.zeros(max_lag + 1, dtype=complex)
        seed_cnt = np.zeros(max_lag + 1, dtype=int)
        for m in range(max_lag + 1):
            if m == 0:
                num[0] += np.sum(u * np.conj(u))
                cnt[0] += len(u)
                seed_num[0] += len(u)
                seed_cnt[0] += len(u)
            else:
                if len(u) - m <= 0:
                    continue
                num[m] += np.sum(u[:-m] * np.conj(u[m:]))
                cnt[m] += len(u) - m
                seed_num[m] += np.sum(u[:-m] * np.conj(u[m:]))
                seed_cnt[m] += len(u) - m
        seed_acf = np.zeros(max_lag + 1, dtype=complex)
        for m in range(max_lag + 1):
            if seed_cnt[m] > 0:
                seed_acf[m] = seed_num[m] / seed_cnt[m]
        per_seed.append({
            'dw_per_chunk': float(slope),
            'resid_rms_rad': float(np.std(resid)),
            'acf_abs': np.abs(seed_acf).tolist(),
        })
    acf = np.zeros(max_lag + 1, dtype=complex)
    for m in range(max_lag + 1):
        if cnt[m] > 0:
            acf[m] = num[m] / cnt[m]
    return {
        'abs_acf': np.abs(acf).tolist(),
        'arg_acf_deg': np.degrees(np.angle(acf)).tolist(),
        'count': cnt.tolist(),
        'per_seed': per_seed,
    }


def fit_two_component(acf_values, max_lag, T_chunk_s):
    """Fit ACF(m) = p_inf + B*exp(-m·T/τ) on lags 1..max_lag.
    Grid over p_inf, then log-linear fit of (acf-p_inf)."""
    a = np.array(acf_values[1:max_lag + 1])
    m = np.arange(1, max_lag + 1)
    # Grid search over p_inf
    grid = np.linspace(-0.02, max(0.01, a.min() + 0.01), 100)
    best = None
    for p_inf in grid:
        y = a - p_inf
        ok = y > 0.005
        if ok.sum() < 4:
            continue
        logy = np.log(y[ok])
        slope, intercept = np.polyfit(m[ok], logy, 1)
        if slope >= 0:
            tau_lag = float('inf')
            B = float(np.exp(intercept))
            pred = np.full_like(m, p_inf, dtype=float) + B
        else:
            tau_lag = -1.0 / slope
            B = float(np.exp(intercept))
            pred = p_inf + B * np.exp(-m / tau_lag)
        ss_res = float(np.sum((a - pred)**2))
        if best is None or ss_res < best['ss_res']:
            best = {'p_inf': float(p_inf), 'B': float(B),
                    'tau_lag': float(tau_lag),
                    'tau_s': float(tau_lag * T_chunk_s) if np.isfinite(tau_lag) else float('inf'),
                    'ss_res': ss_res,
                    'rmse': float(np.sqrt(ss_res / max_lag)),
                    'pred': pred.tolist()}
    # Pure plateau (1-param)
    p_pure = float(a.mean())
    ss_pure = float(np.sum((a - p_pure)**2))
    pure = {'plateau': p_pure,
            'rmse_pure': float(np.sqrt(ss_pure / max_lag))}
    # Pure exp (no plateau)
    if (a > 0.005).sum() >= 4:
        ok = a > 0.005
        slope, intercept = np.polyfit(m[ok], np.log(a[ok]), 1)
        if slope < 0:
            tau_pe = -1.0 / slope
            B_pe = float(np.exp(intercept))
            pred_pe = B_pe * np.exp(-m / tau_pe)
            ss_pe = float(np.sum((a - pred_pe)**2))
            pure_exp = {'B': B_pe, 'tau_lag': float(tau_pe),
                        'tau_s': float(tau_pe * T_chunk_s),
                        'rmse': float(np.sqrt(ss_pe / max_lag))}
        else:
            pure_exp = None
    else:
        pure_exp = None
    return best, pure, pure_exp


def seed_level_stats(z_list):
    mus = []
    sigs = []
    for z in z_list:
        mu = z.mean()
        mus.append(abs(mu))
        dev = z - mu
        sig = np.sqrt(np.mean(np.abs(dev)**2))
        sigs.append(float(sig))
    return {
        'per_seed_mu_abs': [float(x) for x in mus],
        'per_seed_sigma_n': [float(x) for x in sigs],
        'mean_mu_abs': float(np.mean(mus)),
        'std_mu_abs': float(np.std(mus)),
        'mean_sigma_n': float(np.mean(sigs)),
        'std_sigma_n': float(np.std(sigs)),
    }


def per_seed_from_json(records, key):
    out = []
    for s in records:
        pairs = s[key]
        out.append(np.array([complex(p[0], p[1]) for p in pairs]))
    return out


def summarize_cell(omega_spread, z_raws, z_sts, n_sw_list, max_lag, T_chunk_s):
    raw_acf = residual_phase_acf(z_raws, max_lag)
    st_acf = residual_phase_acf(z_sts, max_lag)
    raw_seeds = seed_level_stats(z_raws)
    st_seeds = seed_level_stats(z_sts)
    raw_two, raw_pure, raw_pe = fit_two_component(raw_acf['abs_acf'],
                                                    max_lag, T_chunk_s)
    st_two, st_pure, st_pe = fit_two_component(st_acf['abs_acf'],
                                                max_lag, T_chunk_s)
    return {
        'omega_spread': omega_spread,
        'n_seeds': len(z_raws),
        'n_chunks': int(len(z_raws[0])),
        'max_lag': max_lag,
        'mean_n_sw_per_chunk': float(np.mean([n.mean() for n in n_sw_list]))
            if n_sw_list is not None else None,
        'raw': {
            'abs_acf': raw_acf['abs_acf'],
            'arg_acf_deg': raw_acf['arg_acf_deg'],
            'two_component': raw_two,
            'pure_plateau': raw_pure,
            'pure_exp': raw_pe,
            'seeds': raw_seeds,
            'per_seed_dw': [p['dw_per_chunk'] for p in raw_acf['per_seed']],
            'per_seed_resid_rms': [p['resid_rms_rad'] for p in raw_acf['per_seed']],
        },
        'st': {
            'abs_acf': st_acf['abs_acf'],
            'arg_acf_deg': st_acf['arg_acf_deg'],
            'two_component': st_two,
            'pure_plateau': st_pure,
            'pure_exp': st_pe,
            'seeds': st_seeds,
            'per_seed_dw': [p['dw_per_chunk'] for p in st_acf['per_seed']],
            'per_seed_resid_rms': [p['resid_rms_rad'] for p in st_acf['per_seed']],
        },
    }


def pack_per_seed(per_seed):
    return [{
        'seed': s['seed'],
        'n_chunks': s['n_chunks'],
        'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
        'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
        'n_sw': s['n_sw'].tolist(),
    } for s in per_seed]


def main():
    start = datetime.now()
    print("Thor Session #103: ω_spread Sweep of τ_RAW  (S102-P3)")
    print(f"Started: {start.isoformat()}\n")

    dt = 0.1
    sigma = 0.022
    A = 0.30
    signal_freq = 0.003
    warmup = 10_000
    T_CHUNK_S = 4000.0
    chunk_steps = int(T_CHUNK_S / dt)
    N_SEEDS = 8

    # ω_spread cells with chunk count tuned to expected τ ∝ 1/ω_spread
    # (5τ ≈ N_chunks·T_chunk_s for adequate window).
    # Reuse ω=0.02 from S98 main (8 seeds × 100 chunks).
    cells = [
        ('S103-new', 0.005, 250, 250),  # 250 chunks, max_lag 250
        ('S103-new', 0.04,  100, 100),
        ('S103-new', 0.08,  60,  60),
    ]

    per_cell_ps = {}
    for i, (src, ow, n_chunks, max_lag) in enumerate(cells):
        ps = run_cell(omega_spread=ow, n_chunks=n_chunks,
                      A=A, sigma=sigma, n_seeds=N_SEEDS,
                      warmup=warmup, chunk_steps=chunk_steps,
                      dt=dt, signal_freq=signal_freq,
                      seed_base=103_000 + i * 100)
        per_cell_ps[ow] = ps

    # Reuse ω=0.02 from S98 main (8 × 100 chunks at A=0.30 σ=0.022)
    print("\n>> Loading ω_spread=0.02 from S98 main")
    with open('thor_session_98_phase_drift_results.json') as f:
        s98 = json.load(f)
    z_raws_02 = per_seed_from_json(s98['main']['per_seed'], 'z_raw')
    z_sts_02 = per_seed_from_json(s98['main']['per_seed'], 'z_st')
    n_sw_02 = [np.array(s.get('n_sw', [0]*len(z_raws_02[0])))
                for s in s98['main']['per_seed']]
    print(f"   {len(z_raws_02)} seeds × {len(z_raws_02[0])} chunks")

    # ── Summarize all cells ──
    print("\n" + "="*72)
    print("PER-CELL SUMMARY")
    print("="*72)
    cell_specs = [
        (0.005, 'S103-new', None, 250),
        (0.02,  'S98-main', (z_raws_02, z_sts_02, n_sw_02), 99),
        (0.04,  'S103-new', None, 100),
        (0.08,  'S103-new', None, 60),
    ]
    summaries = []
    for ow, src, reused, max_lag in cell_specs:
        if reused is not None:
            zrs, zss, n_sw = reused
        else:
            ps = per_cell_ps[ow]
            zrs = [s['z_raw'] for s in ps]
            zss = [s['z_st'] for s in ps]
            n_sw = [s['n_sw'] for s in ps]
        summ = summarize_cell(ow, zrs, zss, n_sw, max_lag, T_CHUNK_S)
        summ['source'] = src
        summaries.append(summ)
        print(f"\n  ω_spread={ow}  ({src})")
        rs = summ['raw']['seeds']
        ss = summ['st']['seeds']
        print(f"    RAW |⟨z⟩|={rs['mean_mu_abs']:.4e} ± {rs['std_mu_abs']:.4e}  "
              f"σ_n={rs['mean_sigma_n']:.4e} ± {rs['std_sigma_n']:.4e}")
        print(f"    ST  |⟨z⟩|={ss['mean_mu_abs']:.3f} ± {ss['std_mu_abs']:.3f}  "
              f"σ_n={ss['mean_sigma_n']:.3f} ± {ss['std_sigma_n']:.3f}")
        if summ['mean_n_sw_per_chunk'] is not None:
            print(f"    mean N_sw/chunk = {summ['mean_n_sw_per_chunk']:.1f}")
        rt = summ['raw']['two_component']
        st_ = summ['st']['two_component']
        print(f"    RAW 2-comp: p_inf={rt['p_inf']:.3f} B={rt['B']:.3f} "
              f"τ={rt['tau_s']:.0f}s  RMSE={rt['rmse']:.4f}  "
              f"(pure: {summ['raw']['pure_plateau']['rmse_pure']:.4f})")
        print(f"    ST  2-comp: p_inf={st_['p_inf']:.3f} B={st_['B']:.3f} "
              f"τ={st_['tau_s']:.0f}s  RMSE={st_['rmse']:.4f}  "
              f"(pure: {summ['st']['pure_plateau']['rmse_pure']:.4f})")
        # First few lag values to eyeball shape
        ra = summ['raw']['abs_acf']
        sa = summ['st']['abs_acf']
        print(f"    RAW ACF [m=1,5,10,20,40, max]: "
              f"{ra[1]:.3f}, {ra[5]:.3f}, "
              f"{ra[min(10,len(ra)-1)]:.3f}, "
              f"{ra[min(20,len(ra)-1)]:.3f}, "
              f"{ra[min(40,len(ra)-1)]:.3f}, "
              f"{ra[-1]:.3f}")
        print(f"    ST  ACF [m=1,5,10,20,40, max]: "
              f"{sa[1]:.3f}, {sa[5]:.3f}, "
              f"{sa[min(10,len(sa)-1)]:.3f}, "
              f"{sa[min(20,len(sa)-1)]:.3f}, "
              f"{sa[min(40,len(sa)-1)]:.3f}, "
              f"{sa[-1]:.3f}")

    # ── τ vs ω_spread inverse-proportionality test ──
    print("\n" + "="*72)
    print("τ_RAW vs ω_spread")
    print("="*72)
    ows = []; taus = []
    for s in summaries:
        ow = s['omega_spread']
        tau = s['raw']['two_component']['tau_s']
        if np.isfinite(tau):
            ows.append(ow); taus.append(tau)
        print(f"  ω_spread={ow}  τ_RAW={tau:.0f}s   "
              f"τ·ω_spread={tau*ow:.1f}s")
    inv_test = None
    if len(ows) >= 2:
        log_ow = np.log(ows)
        log_tau = np.log(taus)
        slope, intercept = np.polyfit(log_ow, log_tau, 1)
        # Predicted: τ ∝ 1/ω_spread → log τ = -log ω + const → slope=-1
        ss_res = float(np.sum((log_tau - (slope*log_ow + intercept))**2))
        ss_tot = float(np.sum((log_tau - log_tau.mean())**2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        inv_test = {
            'log_log_slope': float(slope),
            'log_log_intercept': float(intercept),
            'R2': float(r2),
            'omega_values': ows,
            'tau_values': taus,
            'tau_omega_product': [float(t*o) for t, o in zip(taus, ows)],
        }
        print(f"\n  log-log fit: log(τ) = {slope:+.3f}·log(ω_spread) + {intercept:.2f}")
        print(f"  R² = {r2:.4f}")
        print(f"  Pure 1/ω prediction → slope = -1.000")
        print(f"  τ·ω_spread (s, should be constant ~ 1600 if τ_predicted=80ks at ω=0.02): "
              f"{[f'{t*o:.1f}' for t, o in zip(taus, ows)]}")

    # ── ST plateau scaling ──
    print("\n" + "="*72)
    print("ST PLATEAU vs ω_spread")
    print("="*72)
    for s in summaries:
        ow = s['omega_spread']
        st = s['st']['two_component']
        plateau = st['p_inf'] + st['B']  # asymptotic at m=1 if τ→∞
        print(f"  ω_spread={ow}  ST p_inf={st['p_inf']:.3f}  "
              f"B={st['B']:.3f}  τ={st['tau_s']:.0f}s  "
              f"|⟨z⟩|/σ_n={s['st']['seeds']['mean_mu_abs']/s['st']['seeds']['mean_sigma_n']:.2f}")

    # ── Save ──
    out = {
        'meta': {
            'session': 103,
            'title': 'ω_spread Sweep of τ_RAW — S102-P3',
            'started': start.isoformat(),
            'params': {
                'dt': dt, 'sigma': sigma, 'A': A,
                'signal_freq': signal_freq, 'warmup': warmup,
                'T_chunk_s': T_CHUNK_S, 'chunk_steps': chunk_steps,
                'n_seeds': N_SEEDS,
                'omega_spread_values': [c[0] for c in cell_specs],
                'sources': {str(c[0]): c[1] for c in cell_specs},
                'max_lag_per_cell': {str(c[0]): c[3] for c in cell_specs},
            },
        },
        'per_cell': {f"{s['omega_spread']}": {
            'omega_spread': s['omega_spread'],
            'source': s['source'],
            'n_seeds': s['n_seeds'],
            'n_chunks': s['n_chunks'],
            'max_lag': s['max_lag'],
            'mean_n_sw_per_chunk': s['mean_n_sw_per_chunk'],
            'raw': s['raw'],
            'st': s['st'],
        } for s in summaries},
        'per_cell_new_per_seed': {f"{ow}": pack_per_seed(per_cell_ps[ow])
                                   for ow in per_cell_ps},
        'tau_vs_omega_test': inv_test,
    }
    with open('thor_session_103_omega_spread_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_103_omega_spread_results.json")


if __name__ == '__main__':
    main()
