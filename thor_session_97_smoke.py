#!/usr/bin/env python3
"""S97 smoke test: check ML optimizer behavior on a few seeds."""
import numpy as np
import sys
import time

sys.stdout.reconfigure(line_buffering=True)

from thor_session_97_ml_kramers import (run_seed, STEPS, WARMUP, SIGMA, F_S,
                                         kramers_lambda)
from thor_session_93_phase_coherent import simulate

print("Smoke test S97")
print(f"STEPS={STEPS}, WARMUP={WARMUP}")

for A in [0.00, 0.12, 0.20]:
    print(f"\nA = {A}")
    lams = []
    ks = []
    t0 = time.time()
    for seed in range(4):
        r = run_seed(seed=seed * 100 + 17, A=A)
        lams.append(r['lam'])
        ks.append(r['k_hat'])
        print(f"  seed {seed}: λ={r['lam']:+6.2f}  k̂={r['k_hat']:+.3f}  "
              f"φ̂={r['phi_hat']:+.2f}  n_sw={r['n_switches']}  "
              f"(I_st={r['I_st']:+7.1f}, Q_st={r['Q_st']:+7.1f})")
    dt = time.time() - t0
    print(f"  mean λ={np.mean(lams):.2f}, mean k̂={np.mean(ks):+.3f}  "
          f"({dt:.1f}s for 4 seeds)")
