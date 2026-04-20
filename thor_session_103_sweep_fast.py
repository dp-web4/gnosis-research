#!/usr/bin/env python3
"""S103 fast ω_spread sweep: ω ∈ {0.04, 0.08} at A=0.30 σ=0.022.

Context
-------
Extended S98 analysis (thor_session_103_analyze_s98.py) revealed the RAW
residual-phase ACF at ω_spread=0.02 is a damped cosine with period ~150 ks,
NOT a clean exponential. S102's "τ≈80ks exponential" captured the first
lobe only.

Hypothesis: the oscillation period in the ACF scales as 1/ω_spread.
  ω_spread=0.02 → period 150 ks (extended S98)
  ω_spread=0.04 → predicted 75 ks = 19 lags (clear cycles over 100 lags)
  ω_spread=0.08 → predicted 38 ks = 9 lags

Cost: 8 seeds × 100 chunks × 40k steps each = 32 M steps per cell.
At 25 µs/step ≈ 13 min per cell → total ~26 min.

(ω=0.005 is saved for a follow-up — it needs 250+ chunks, ~33 min.)
"""
import json
import numpy as np
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55


def run_cell(omega_spread, n_chunks=100, A=0.30, sigma=0.022, n_seeds=8,
             warmup=10_000, chunk_steps=40_000, dt=0.1,
             signal_freq=0.003, seed_base=103_000):
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
            'seed': seed_base + seed, 'n_chunks': n_chunks,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw': n_sw,
        })
        print(f"   seed={seed_base + seed:6d}  {elapsed:5.1f}s   "
              f"|<z_raw>|={np.abs(z_raw.mean()):.4e}   "
              f"|<z_st>|={np.abs(z_st.mean()):.3f}   "
              f"N_sw/chunk={n_sw.mean():.1f}")
    print(f"   ω_spread={omega_spread} total {(datetime.now()-start).total_seconds():.0f}s")
    return per_seed


def residual_phase_acf(z_list, max_lag):
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
        for m in range(max_lag + 1):
            if m == 0:
                num[0] += np.sum(u * np.conj(u))
                cnt[0] += len(u)
            else:
                if len(u) - m <= 0: continue
                num[m] += np.sum(u[:-m] * np.conj(u[m:]))
                cnt[m] += len(u) - m
        per_seed.append({'dw_per_chunk': float(slope),
                         'resid_rms_rad': float(np.std(resid))})
    acf = np.zeros(max_lag + 1, dtype=complex)
    for m in range(max_lag + 1):
        if cnt[m] > 0:
            acf[m] = num[m] / cnt[m]
    return acf, cnt, per_seed


def seed_level_stats(z_list):
    mus = []; sigs = []
    for z in z_list:
        mu = z.mean()
        mus.append(abs(mu))
        dev = z - mu
        sigs.append(float(np.sqrt(np.mean(np.abs(dev)**2))))
    return {
        'per_seed_mu_abs': [float(x) for x in mus],
        'per_seed_sigma_n': [float(x) for x in sigs],
        'mean_mu_abs': float(np.mean(mus)),
        'std_mu_abs': float(np.std(mus)),
        'mean_sigma_n': float(np.mean(sigs)),
        'std_sigma_n': float(np.std(sigs)),
    }


def fit_damped_cos_and_exp(acf_abs, T_chunk_s, max_lag):
    from scipy.optimize import least_squares
    m = np.arange(1, max_lag + 1)
    y = np.array(acf_abs[1:max_lag + 1])

    def dcos(p, m): return p[0] + p[1]*np.exp(-m/p[2])*np.cos(p[3]*m + p[4])
    def expo(p, m): return p[0] + p[1]*np.exp(-m/p[2])

    best_dc = None
    for om_init in np.linspace(0.01, 0.5, 15):
        for tau_init in [20, 50, 100, 200]:
            try:
                r = least_squares(lambda p: dcos(p, m) - y,
                    [0.1, 0.3, tau_init, om_init, 0.0],
                    bounds=([-0.2, 0, 5, 0.001, -np.pi],
                            [0.8, 1.0, 1000, np.pi, np.pi]))
                ss = float(np.sum(r.fun**2))
                if best_dc is None or ss < best_dc['ss']:
                    best_dc = {'params': r.x.tolist(), 'ss': ss,
                               'rmse': float(np.sqrt(ss/max_lag))}
            except Exception:
                pass

    try:
        r = least_squares(lambda p: expo(p, m) - y, [0.15, 0.3, 40.0],
                          bounds=([-0.2, 0, 2], [0.8, 1.0, 1000]))
        ss = float(np.sum(r.fun**2))
        best_exp = {'params': r.x.tolist(), 'ss': ss,
                    'rmse': float(np.sqrt(ss/max_lag))}
    except Exception:
        best_exp = None

    p_pure = float(y.mean())
    ss_pure = float(np.sum((y - p_pure)**2))
    pure = {'plateau': p_pure, 'rmse': float(np.sqrt(ss_pure/max_lag))}

    return best_dc, best_exp, pure


def pack_per_seed(per_seed):
    return [{
        'seed': s['seed'], 'n_chunks': s['n_chunks'],
        'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
        'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
        'n_sw': s['n_sw'].tolist(),
    } for s in per_seed]


def main():
    start = datetime.now()
    print("Thor Session #103: ω_spread Sweep (fast variant — ω=0.04, 0.08)")
    print(f"Started: {start.isoformat()}\n")

    cells = [(0.04, 100, 100_100), (0.08, 100, 100_200)]
    T_CHUNK_S = 4000.0
    results = {}

    for ow, n_chunks, seed_base in cells:
        ps = run_cell(omega_spread=ow, n_chunks=n_chunks, A=0.30, sigma=0.022,
                      n_seeds=8, seed_base=seed_base)
        z_raws = [s['z_raw'] for s in ps]
        z_sts = [s['z_st'] for s in ps]
        n_sw_arr = [s['n_sw'] for s in ps]

        raw_acf, raw_cnt, raw_per_seed = residual_phase_acf(z_raws, n_chunks-1)
        st_acf, st_cnt, st_per_seed = residual_phase_acf(z_sts, n_chunks-1)
        raw_seeds = seed_level_stats(z_raws)
        st_seeds = seed_level_stats(z_sts)

        max_lag_fit = min(80, n_chunks - 20)
        raw_dc, raw_exp, raw_pure = fit_damped_cos_and_exp(
            np.abs(raw_acf).tolist(), T_CHUNK_S, max_lag_fit)
        st_dc, st_exp, st_pure = fit_damped_cos_and_exp(
            np.abs(st_acf).tolist(), T_CHUNK_S, max_lag_fit)

        print(f"\n  ω_spread={ow}")
        print(f"    RAW |<z>|={raw_seeds['mean_mu_abs']:.4e} ± "
              f"{raw_seeds['std_mu_abs']:.4e}  σ_n={raw_seeds['mean_sigma_n']:.4e}")
        print(f"    ST  |<z>|={st_seeds['mean_mu_abs']:.3f} ± "
              f"{st_seeds['std_mu_abs']:.3f}    σ_n={st_seeds['mean_sigma_n']:.3f}")
        print(f"    RAW ACF [m=1,5,10,20,30,40,60,80]: " +
              " ".join(f"{np.abs(raw_acf[k]):.3f}" for k in [1,5,10,20,30,40,60,80] if k<n_chunks))
        print(f"    ST  ACF [m=1,5,10,20,30,40,60,80]: " +
              " ".join(f"{np.abs(st_acf[k]):.3f}" for k in [1,5,10,20,30,40,60,80] if k<n_chunks))
        if raw_dc:
            p = raw_dc['params']
            period_s = 2*np.pi/p[3]*T_CHUNK_S
            print(f"    RAW dcos: p_∞={p[0]:.3f} B={p[1]:.3f} τ={p[2]*T_CHUNK_S/1000:.0f}ks "
                  f"ω={p[3]:.4f} T_osc={period_s/1000:.0f}ks   RMSE={raw_dc['rmse']:.4f}")
            print(f"    RAW exp:  p_∞={raw_exp['params'][0]:.3f} "
                  f"τ={raw_exp['params'][2]*T_CHUNK_S/1000:.0f}ks   RMSE={raw_exp['rmse']:.4f}")
        if st_dc:
            p = st_dc['params']
            period_s = 2*np.pi/p[3]*T_CHUNK_S
            print(f"    ST  dcos: p_∞={p[0]:.3f} B={p[1]:.3f} τ={p[2]*T_CHUNK_S/1000:.0f}ks "
                  f"ω={p[3]:.4f} T_osc={period_s/1000:.0f}ks   RMSE={st_dc['rmse']:.4f}")
            print(f"    ST  pure_plateau: {st_pure['plateau']:.3f}  RMSE={st_pure['rmse']:.4f}")

        results[ow] = {
            'per_seed': pack_per_seed(ps),
            'raw_acf_abs': np.abs(raw_acf).tolist(),
            'raw_acf_arg_deg': np.degrees(np.angle(raw_acf)).tolist(),
            'raw_acf_count': raw_cnt.tolist(),
            'raw_seeds': raw_seeds,
            'raw_damped_cos': raw_dc,
            'raw_pure_exp': raw_exp,
            'raw_pure_plateau': raw_pure,
            'raw_per_seed_dw': [p['dw_per_chunk'] for p in raw_per_seed],
            'raw_per_seed_resid_rms': [p['resid_rms_rad'] for p in raw_per_seed],
            'st_acf_abs': np.abs(st_acf).tolist(),
            'st_acf_arg_deg': np.degrees(np.angle(st_acf)).tolist(),
            'st_acf_count': st_cnt.tolist(),
            'st_seeds': st_seeds,
            'st_damped_cos': st_dc,
            'st_pure_exp': st_exp,
            'st_pure_plateau': st_pure,
            'st_per_seed_dw': [p['dw_per_chunk'] for p in st_per_seed],
            'st_per_seed_resid_rms': [p['resid_rms_rad'] for p in st_per_seed],
            'max_lag_fit': int(max_lag_fit),
        }

    out = {
        'meta': {
            'session': 103, 'title': 'ω_spread sweep — fast (ω=0.04, 0.08)',
            'started': start.isoformat(),
            'params': {'A': 0.30, 'sigma': 0.022,
                       'signal_freq': 0.003, 'warmup': 10000,
                       'T_chunk_s': T_CHUNK_S,
                       'n_seeds': 8, 'n_chunks_per_cell': 100,
                       'omega_spread_values': [c[0] for c in cells]},
        },
        'per_cell': {str(ow): results[ow] for ow in results},
    }
    with open('thor_session_103_sweep_fast_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_103_sweep_fast_results.json")


if __name__ == '__main__':
    main()
