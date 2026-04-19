#!/usr/bin/env python3
"""S99 smoke: tiny-budget sanity check of both parts."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from thor_session_99_seed_heterogeneity import part1_post_s98, part2_matched_compute

print(">>> PART 1 smoke (actual S98 post-process) <<<")
p1 = part1_post_s98()
print(">>> PART 2 smoke: tiny N_total, K=2 <<<")
p2 = part2_matched_compute(N_total_steps=80_000, K_sig=2, K_null=2,
                           sigma=0.022, A=0.30, seed_offset=777_000)
print("\nSmoke OK")
print("  |z| sig means by n:", [(c['n_seeds'], round(c['z_mag_sig_mean'],2)) for c in p2])
print("  |z| null means by n:", [(c['n_seeds'], round(c['z_mag_null_mean'],2)) for c in p2])
