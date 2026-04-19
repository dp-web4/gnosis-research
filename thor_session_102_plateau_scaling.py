#!/usr/bin/env python3
"""
Thor Session #102: Plateau-Height Scaling in A (tests S101-P1)

Context
-------
S101 reanalysis of S98's A=0.30 data showed the raw-channel per-chunk MF
residual-phase ACF is NOT exponential — it's a plateau + white noise:

    ACF_resid(m) ≈ 0.33 · 1  +  0.67 · δ_{m,0}     (RAW)
    ACF_resid(m) ≈ 0.76 · 1  +  0.24 · δ_{m,0}     (ST)

S101 Part A at A=0 showed a null-level ACF (plateau ≈ 0).  So the plateau
is signal-induced.

Two natural models for the plateau height p(A):

   Model M1 (SNR² form, S101-P1 as memoried):
       p(A) = A² / (A² + σ_A²)

   Model M2 (Gaussian chunk-noise around deterministic mean — first
             principles):
       Decompose per-chunk z_k = μ + η_k, μ deterministic ∝ A, η_k iid
       with variance σ_n²/2 per component. The small-noise approximation
       for the circular ACF of arg(z_k / ⟨z⟩) gives
           p(A) = exp(-σ_n² / |μ(A)|²)
       Equivalently p = exp(-1/SNR²) where SNR = |μ|/σ_n.

   M1 and M2 agree qualitatively (monotone in A, p→0 at A=0, p→1 at
   A=∞) but differ in shape: M1 rises quadratically near 0, M2 rises
   super-exponentially (zero until SNR>1, then fast).

Both models make identifiable side predictions:
   (a) |⟨z⟩_seed| should be linear in A (signal-induced mean).
   (b) per-chunk (z_k - ⟨z⟩) RMS σ_n should be (near-)A-invariant
       (intrinsic chunk-MF noise from bistable dynamics).
   (c) the ACF plateau should be flat (constant) across lags 1..30+,
       NOT a slow exponential.

Protocol
--------
Sweep A ∈ {0.10, 0.20, 0.40, 0.50} fresh at σ=0.022, ω_spread=0.02,
8 seeds × 100 chunks × T_chunk=4000s (matches S98/S101 statistics).

Combine with reused data:
  - A=0.00 from S101 Part A (8 seeds × 100 chunks, σ=0.022, ω_sp=0.02)
  - A=0.30 from S98 main  (8 seeds × 100 chunks, σ=0.022, ω_sp=0.02)

For each A measure:
  - per-seed ⟨z⟩ (the "μ")
  - per-seed σ_n (RMS of per-chunk residual vs ⟨z⟩_seed)
  - residual-phase ACF using S99's linear-Δω method (lags 0..30)
  - plateau height p = mean(ACF[1..30])
  - "flatness" check: std(ACF[1..30]) and slope vs lag

Fit both M1 and M2 to p(A) globally; compare side predictions on
per-seed μ(A) and σ_n(A).

Compute
-------
4 new A-values × 8 seeds × 4.01M steps × ~25 µs/step ≈ 3210s = 54 min.
Plus S98/S101 reuse (no new compute). Analysis is fast.
"""

import json
import numpy as np
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55


def run_A(A, sigma, omega_spread, n_seeds, n_chunks, warmup, chunk_steps,
          dt=0.1, signal_freq=0.003, seed_base=102_000):
    """Per A: run n_seeds long trajectories, split into n_chunks chunks,
    return per-seed z_raw, z_st arrays."""
    total_steps = warmup + n_chunks * chunk_steps
    print(f"\n>> A={A:.2f} σ={sigma} ω_sp={omega_spread}  "
          f"n_seeds={n_seeds} n_chunks={n_chunks} "
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
        print(f"   seed={seed_base + seed:6d} {elapsed:5.1f}s  "
              f"|⟨z_raw⟩|={np.abs(z_raw.mean()):.4e}  "
              f"|⟨z_st⟩|={np.abs(z_st.mean()):.3f}  "
              f"N_sw/chunk={n_sw.mean():.1f}")
    print(f"   A={A:.2f} total {(datetime.now()-start).total_seconds():.0f}s")
    return per_seed


def residual_phase_acf(z_list, max_lag):
    """S99 linear-Δω method applied per seed, then circular-pool across
    seeds."""
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
        # also per-seed ACF magnitude across lags 1..L
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


def plateau_stats(abs_acf, lag_lo=1, lag_hi=None):
    """Compute plateau height, flatness, and slope across lags [lag_lo..lag_hi]."""
    a = np.array(abs_acf)
    if lag_hi is None:
        lag_hi = len(a) - 1
    seg = a[lag_lo:lag_hi + 1]
    lags = np.arange(lag_lo, lag_hi + 1)
    p = float(seg.mean())
    std = float(seg.std())
    # linear fit vs lag
    if len(seg) >= 2:
        slope, intercept = np.polyfit(lags, seg, 1)
    else:
        slope, intercept = 0.0, p
    return {
        'plateau_mean': p,
        'plateau_std': std,
        'slope_per_lag': float(slope),
        'intercept': float(intercept),
        'lag_lo': lag_lo, 'lag_hi': lag_hi,
    }


def seed_level_stats(z_list):
    """Per-seed |⟨z⟩|, per-seed σ_n (chunk residual RMS), and
    cross-seed mean/std of these."""
    mus = []
    sigs = []  # RMS of |z_k - μ| per seed
    for z in z_list:
        mu = z.mean()
        mus.append(abs(mu))
        # variance of chunk around mean; use per-component RMS
        dev = z - mu
        # 2D variance = <|dev|²> = σ_I² + σ_Q²; σ_n (per component) = sqrt(<|dev|²>/2)
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
    """Convert stored [real,imag] pair lists into a list of complex arrays."""
    out = []
    for s in records:
        pairs = s[key]
        out.append(np.array([complex(p[0], p[1]) for p in pairs]))
    return out


def summarize_A(A, z_raws, z_sts, max_lag):
    raw_acf = residual_phase_acf(z_raws, max_lag)
    st_acf = residual_phase_acf(z_sts, max_lag)
    raw_plat = plateau_stats(raw_acf['abs_acf'], 1, max_lag)
    st_plat = plateau_stats(st_acf['abs_acf'], 1, max_lag)
    raw_seeds = seed_level_stats(z_raws)
    st_seeds = seed_level_stats(z_sts)
    return {
        'A': A,
        'n_seeds': len(z_raws),
        'n_chunks': int(len(z_raws[0])),
        'raw': {
            'abs_acf': raw_acf['abs_acf'],
            'arg_acf_deg': raw_acf['arg_acf_deg'],
            'plateau': raw_plat,
            'seeds': raw_seeds,
            'per_seed_dw': [p['dw_per_chunk']
                            for p in raw_acf['per_seed']],
            'per_seed_resid_rms': [p['resid_rms_rad']
                                   for p in raw_acf['per_seed']],
        },
        'st': {
            'abs_acf': st_acf['abs_acf'],
            'arg_acf_deg': st_acf['arg_acf_deg'],
            'plateau': st_plat,
            'seeds': st_seeds,
            'per_seed_dw': [p['dw_per_chunk']
                            for p in st_acf['per_seed']],
            'per_seed_resid_rms': [p['resid_rms_rad']
                                   for p in st_acf['per_seed']],
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


def fit_M2(A_vals, p_vals, mu_vals, sig_vals):
    """Model M2: p = exp(-σ_n²/μ²).  Given measured μ(A) and σ_n(A),
    predict p(A) and compute residuals."""
    A_arr = np.array(A_vals)
    p_arr = np.array(p_vals)
    mu_arr = np.array(mu_vals)
    sig_arr = np.array(sig_vals)
    with np.errstate(divide='ignore', invalid='ignore'):
        snr2 = np.where(sig_arr > 0, (mu_arr / sig_arr) ** 2, 0.0)
        pred = np.exp(-1.0 / np.where(snr2 > 1e-10, snr2, 1e-10))
    pred = np.where(snr2 > 1e-10, pred, 0.0)
    resid = p_arr - pred
    return {
        'A': A_arr.tolist(),
        'measured_mu_abs': mu_arr.tolist(),
        'measured_sigma_n': sig_arr.tolist(),
        'snr_squared': snr2.tolist(),
        'predicted_plateau': pred.tolist(),
        'measured_plateau': p_arr.tolist(),
        'residual': resid.tolist(),
        'rmse': float(np.sqrt(np.mean(resid**2))),
    }


def fit_M1(A_vals, p_vals):
    """Model M1: p = A² / (A² + σ_A²).  Fit σ_A² by least squares."""
    A_arr = np.array(A_vals)
    p_arr = np.array(p_vals)
    # Given p = A²/(A² + σ²), σ² = A² (1-p) / p
    # For A>0, p∈(0,1). Compute per-point σ_A² then take median.
    ok = (A_arr > 0) & (p_arr > 0) & (p_arr < 1)
    if ok.sum() < 2:
        return None
    sigA2_vals = A_arr[ok]**2 * (1 - p_arr[ok]) / p_arr[ok]
    sigA2_best = float(np.median(sigA2_vals))
    # Try to also nonlinear-LS fit
    from scipy.optimize import minimize_scalar
    def loss(sigA2):
        pred = A_arr**2 / (A_arr**2 + sigA2)
        return float(np.sum((pred - p_arr)**2))
    res = minimize_scalar(loss, bracket=(1e-6, 1.0),
                          bounds=(1e-10, 10.0), method='bounded')
    sigA2_fit = float(res.x)
    pred_fit = A_arr**2 / (A_arr**2 + sigA2_fit)
    return {
        'sigA2_median_per_point': sigA2_best,
        'sigA2_LS': sigA2_fit,
        'predicted_plateau': pred_fit.tolist(),
        'residual': (p_arr - pred_fit).tolist(),
        'rmse': float(np.sqrt(np.mean((p_arr - pred_fit)**2))),
    }


def main():
    start = datetime.now()
    print("Thor Session #102: Plateau-Height Scaling in A  (S101-P1)")
    print(f"Started: {start.isoformat()}\n")

    dt = 0.1
    sigma = 0.022
    omega_spread = 0.02
    signal_freq = 0.003
    warmup = 10_000
    T_CHUNK_S = 4000.0
    chunk_steps = int(T_CHUNK_S / dt)
    N_SEEDS = 8
    N_CHUNKS = 100
    MAX_LAG = 30

    # ── New A values ──
    A_NEW = [0.10, 0.20, 0.40, 0.50]
    per_A_ps = {}
    for i, A in enumerate(A_NEW):
        ps = run_A(A=A, sigma=sigma, omega_spread=omega_spread,
                   n_seeds=N_SEEDS, n_chunks=N_CHUNKS,
                   warmup=warmup, chunk_steps=chunk_steps,
                   dt=dt, signal_freq=signal_freq,
                   seed_base=102_000 + i * 100)
        per_A_ps[A] = ps

    # ── Reuse A=0 from S101 Part A ──
    print("\n>> Loading A=0.00 from S101 Part A")
    with open('thor_session_101_intrinsic_wander_results.json') as f:
        s101 = json.load(f)
    z_raws_A0 = per_seed_from_json(s101['part_a']['per_seed'], 'z_raw')
    z_sts_A0 = per_seed_from_json(s101['part_a']['per_seed'], 'z_st')
    print(f"   {len(z_raws_A0)} seeds × {len(z_raws_A0[0])} chunks")

    # ── Reuse A=0.30 from S98 main ──
    print("\n>> Loading A=0.30 from S98 main")
    with open('thor_session_98_phase_drift_results.json') as f:
        s98 = json.load(f)
    z_raws_A30 = per_seed_from_json(s98['main']['per_seed'], 'z_raw')
    z_sts_A30 = per_seed_from_json(s98['main']['per_seed'], 'z_st')
    print(f"   {len(z_raws_A30)} seeds × {len(z_raws_A30[0])} chunks")

    # ── Summarize each A ──
    print("\n" + "="*72)
    print("PER-A SUMMARY (plateau = mean |ACF_resid| over lags 1..30)")
    print("="*72)
    A_all = [0.00] + A_NEW[:2] + [0.30] + A_NEW[2:]  # sorted
    A_sources = {
        0.00: ('S101-A', [z_raws_A0, z_sts_A0]),
        0.10: ('S102-new', None),
        0.20: ('S102-new', None),
        0.30: ('S98-main', [z_raws_A30, z_sts_A30]),
        0.40: ('S102-new', None),
        0.50: ('S102-new', None),
    }
    summaries = []
    for A in A_all:
        src, zs = A_sources[A]
        if zs is None:
            ps = per_A_ps[A]
            zrs = [s['z_raw'] for s in ps]
            zss = [s['z_st'] for s in ps]
        else:
            zrs, zss = zs
        summ = summarize_A(A, zrs, zss, MAX_LAG)
        summ['source'] = src
        summaries.append(summ)
        print(f"\n  A={A:.2f} ({src})")
        rp = summ['raw']['plateau']
        sp = summ['st']['plateau']
        rs = summ['raw']['seeds']
        ss = summ['st']['seeds']
        print(f"    RAW plateau= {rp['plateau_mean']:.3f} ± "
              f"{rp['plateau_std']:.3f}  slope={rp['slope_per_lag']:+.4f}/lag")
        print(f"    ST  plateau= {sp['plateau_mean']:.3f} ± "
              f"{sp['plateau_std']:.3f}  slope={sp['slope_per_lag']:+.4f}/lag")
        print(f"    RAW |⟨z⟩|={rs['mean_mu_abs']:.4e} ± "
              f"{rs['std_mu_abs']:.4e}  σ_n={rs['mean_sigma_n']:.4e} ± "
              f"{rs['std_sigma_n']:.4e}")
        print(f"    ST  |⟨z⟩|={ss['mean_mu_abs']:.3f} ± "
              f"{ss['std_mu_abs']:.3f}  σ_n={ss['mean_sigma_n']:.3f} ± "
              f"{ss['std_sigma_n']:.3f}")
        print(f"    RAW first 6 lags: "
              f"[{', '.join(f'{v:.3f}' for v in summ['raw']['abs_acf'][:6])}]")
        print(f"    ST  first 6 lags: "
              f"[{', '.join(f'{v:.3f}' for v in summ['st']['abs_acf'][:6])}]")

    # ── Fits ──
    A_vals = [s['A'] for s in summaries]
    p_raw = [s['raw']['plateau']['plateau_mean'] for s in summaries]
    p_st = [s['st']['plateau']['plateau_mean'] for s in summaries]
    mu_raw = [s['raw']['seeds']['mean_mu_abs'] for s in summaries]
    mu_st = [s['st']['seeds']['mean_mu_abs'] for s in summaries]
    sig_raw = [s['raw']['seeds']['mean_sigma_n'] for s in summaries]
    sig_st = [s['st']['seeds']['mean_sigma_n'] for s in summaries]

    print("\n" + "="*72)
    print("SCALING FITS")
    print("="*72)
    print("\nRAW channel:")
    fit_m1_raw = fit_M1(A_vals, p_raw)
    fit_m2_raw = fit_M2(A_vals, p_raw, mu_raw, sig_raw)
    if fit_m1_raw:
        print(f"  M1 (p = A²/(A² + σ_A²)):")
        print(f"    σ_A² (LS) = {fit_m1_raw['sigA2_LS']:.5f}  "
              f"RMSE = {fit_m1_raw['rmse']:.4f}")
        print(f"    predicted: "
              f"{[f'{v:.3f}' for v in fit_m1_raw['predicted_plateau']]}")
        print(f"    measured : {[f'{v:.3f}' for v in p_raw]}")
    print(f"  M2 (p = exp(-σ_n²/|μ|²), using measured μ and σ_n):")
    print(f"    SNR² = {[f'{v:.3f}' for v in fit_m2_raw['snr_squared']]}")
    print(f"    predicted: "
          f"{[f'{v:.3f}' for v in fit_m2_raw['predicted_plateau']]}")
    print(f"    measured : {[f'{v:.3f}' for v in p_raw]}")
    print(f"    RMSE = {fit_m2_raw['rmse']:.4f}")

    print("\nST channel:")
    fit_m1_st = fit_M1(A_vals, p_st)
    fit_m2_st = fit_M2(A_vals, p_st, mu_st, sig_st)
    if fit_m1_st:
        print(f"  M1 (p = A²/(A² + σ_A²)):")
        print(f"    σ_A² (LS) = {fit_m1_st['sigA2_LS']:.5f}  "
              f"RMSE = {fit_m1_st['rmse']:.4f}")
        print(f"    predicted: "
              f"{[f'{v:.3f}' for v in fit_m1_st['predicted_plateau']]}")
        print(f"    measured : {[f'{v:.3f}' for v in p_st]}")
    print(f"  M2 (p = exp(-σ_n²/|μ|²), using measured μ and σ_n):")
    print(f"    SNR² = {[f'{v:.3f}' for v in fit_m2_st['snr_squared']]}")
    print(f"    predicted: "
          f"{[f'{v:.3f}' for v in fit_m2_st['predicted_plateau']]}")
    print(f"    measured : {[f'{v:.3f}' for v in p_st]}")
    print(f"    RMSE = {fit_m2_st['rmse']:.4f}")

    # ── μ(A) linearity check ──
    print("\n" + "="*72)
    print("SIDE-PREDICTION CHECKS")
    print("="*72)
    # RAW |⟨z⟩| should be linear in A
    Aarr = np.array(A_vals)
    muarr = np.array(mu_raw)
    slope_raw, _ = np.polyfit(Aarr, muarr, 1)
    pred_lin_raw = slope_raw * Aarr
    r2_raw = 1 - np.sum((muarr - pred_lin_raw)**2) / np.sum((muarr - muarr.mean())**2)
    print(f"  RAW |⟨z⟩| vs A:  slope={slope_raw:.4f}   R²(no intercept)={r2_raw:.4f}")
    muarr_st = np.array(mu_st)
    slope_st, _ = np.polyfit(Aarr, muarr_st, 1)
    pred_lin_st = slope_st * Aarr
    r2_st = 1 - np.sum((muarr_st - pred_lin_st)**2) / np.sum((muarr_st - muarr_st.mean())**2)
    print(f"  ST  |⟨z⟩| vs A:  slope={slope_st:.4f}   R²(no intercept)={r2_st:.4f}")
    print(f"\n  σ_n(RAW) by A: "
          f"{[f'{v:.4e}' for v in sig_raw]}  "
          f"(A-invariance?)")
    print(f"  σ_n(ST)  by A: "
          f"{[f'{v:.3f}' for v in sig_st]}")

    # ── Save ──
    out = {
        'meta': {
            'session': 102,
            'title': 'Plateau-Height Scaling in A — S101-P1',
            'started': start.isoformat(),
            'params': {
                'dt': dt, 'sigma': sigma, 'omega_spread': omega_spread,
                'signal_freq': signal_freq, 'warmup': warmup,
                'T_chunk_s': T_CHUNK_S, 'chunk_steps': chunk_steps,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'max_lag': MAX_LAG, 'A_values': A_all,
                'A_new': A_NEW, 'A_sources': {str(k): v[0]
                                              for k, v in A_sources.items()},
            },
        },
        'per_A': {f"{s['A']:.2f}": {
            'source': s['source'], 'A': s['A'],
            'n_seeds': s['n_seeds'], 'n_chunks': s['n_chunks'],
            'raw': s['raw'], 'st': s['st'],
        } for s in summaries},
        'per_A_new_per_seed': {f"{A:.2f}": pack_per_seed(per_A_ps[A])
                               for A in A_NEW},
        'fits': {
            'raw': {'M1': fit_m1_raw, 'M2': fit_m2_raw,
                    'mu_linearity': {'slope': float(slope_raw),
                                     'R2': float(r2_raw)}},
            'st': {'M1': fit_m1_st, 'M2': fit_m2_st,
                   'mu_linearity': {'slope': float(slope_st),
                                    'R2': float(r2_st)}},
            'A_vals': A_vals,
            'p_raw': p_raw, 'p_st': p_st,
            'mu_raw': mu_raw, 'mu_st': mu_st,
            'sig_raw': sig_raw, 'sig_st': sig_st,
        },
    }
    with open('thor_session_102_plateau_scaling_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_102_plateau_scaling_results.json")


if __name__ == '__main__':
    main()
