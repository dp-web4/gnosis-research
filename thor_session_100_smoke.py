#!/usr/bin/env python3
"""Quick smoke test of S100's new pieces before the long run."""
import numpy as np
from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ
from thor_session_98_phase_drift import run_long_chunked, summarize_channel
from thor_session_100_incoherent_drift import (
    raw_chunk_autocorr, fit_tau_wander, analyze_wander,
)

if __name__ == '__main__':
    print("S100 smoke — tiny σ=0.060 run, 2 seeds × 20 chunks")
    ps = run_long_chunked(
        sigma=0.060, A=0.30,
        n_seeds=2,
        total_steps=10_000 + 20 * 40_000,
        warmup=10_000,
        chunk_steps=40_000,
        dt=0.1, signal_freq=0.003,
        seed_base=888_000,
    )
    s_raw = summarize_channel('z_raw', ps, max_lag=10, chunk_time_s=4000.0)
    s_st = summarize_channel('z_st', ps, max_lag=10, chunk_time_s=4000.0)
    w_raw = analyze_wander(ps, 'z_raw', max_lag=10, chunk_time_s=4000.0)
    w_st = analyze_wander(ps, 'z_st', max_lag=10, chunk_time_s=4000.0)
    for name, summ, wand in [('raw', s_raw, w_raw), ('st', s_st, w_st)]:
        f = summ['phase_diffusion_fit']
        print(f"  {name}: τ_φ=", f['tau_phi_s'] if f else 'n/a')
        tw_p = wand['tau_phase_wander']
        tw_m = wand['tau_mag_wander']
        print(f"    rho_mag[:5]={[round(v, 3) for v in wand['rho_mag'][:5]]}")
        print(f"    rho_u_abs[:5]={[round(v, 3) for v in wand['rho_u_abs'][:5]]}")
        print(f"    τ_mag={(tw_m['tau_s'] if tw_m else None)}  "
              f"τ_ph={(tw_p['tau_s'] if tw_p else None)}")
    print("smoke ok")
