#!/usr/bin/env python3
"""Fast smoke test for S106 runner — 2 seeds × 3 chunks × 5k steps.

Checks that:
  - The recycled simulator and detectors all import/run.
  - kappa_phase=0 really produces near-null R_coh.
  - kappa_C=0 runs without numerical errors (independent bistables).
Should complete in < 2 minutes.
"""
import sys
sys.path.insert(0, '/home/dp/gnosis-research')
import thor_session_106_kappa_c_channel as s106

# Override budget for smoke.
s106.N_SEEDS = 2
s106.N_CHUNKS = 3
s106.CHUNK_STEPS = 5_000
s106.WARMUP = 2_000

for kp, kC, omega, sb, label in [
    (0.30, 0.00, 0.240, 999_000, 'smoke_kp030_kC000'),
    (0.00, 0.15, 0.240, 999_001, 'smoke_kp000_NULL'),
    (0.10, 0.50, 0.080, 999_002, 'smoke_kp010_kC050'),
]:
    ps = s106.run_cell(kappa_phase=kp, kappa_C=kC, omega_spread=omega,
                       seed_base=sb, n_chunks=s106.N_CHUNKS,
                       n_seeds=s106.N_SEEDS)
    summary = s106.summarize_cell(ps)
    print(f"   ⇒ {label}: RAW R={summary['raw_R_coh_mean']:.3f}  "
          f"ST R={summary['st_R_coh_mean']:.3f}  "
          f"R_kura={summary['R_kura_cross_seed_mean']:.3f}  "
          f"N_sw/chunk={summary['n_sw_per_seed']}")
