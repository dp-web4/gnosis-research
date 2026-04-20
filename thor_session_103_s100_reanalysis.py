#!/usr/bin/env python3
"""Reanalyze S100 σ-sweep data through the R_coh lens.

S100 reported "τ_res σ-invariant at 21-23ks". Through the new lens, this
reduces to: R_coh changes with σ (which it must — σ is the signal-noise
ratio knob), and the "τ" was inter-seed angular dephasing artifact.

Prediction: R_coh peaks near SR optimum σ* ≈ 0.022, drops at σ=0.100 where
detection breaks down.
"""
import json
import numpy as np


def per_seed_cplx(records, key):
    return [np.array([complex(p[0], p[1]) for p in s[key]]) for s in records]


def r_coh(zs):
    out = []
    for z in zs:
        mu = z.mean()
        sig_n = np.sqrt(np.mean(np.abs(z - mu)**2))
        r = abs(mu)**2 / (abs(mu)**2 + sig_n**2) if sig_n > 0 else 1.0
        out.append((float(abs(mu)), float(sig_n), float(r),
                    float(np.degrees(np.angle(mu)))))
    return out


with open('thor_session_100_incoherent_drift_results.json') as f:
    s100 = json.load(f)

print("S100 structure keys:", list(s100.keys()))
if 'per_cell' in s100:
    cells = s100['per_cell']
elif 'per_sigma' in s100:
    cells = s100['per_sigma']
else:
    cells = s100

print("\nR_coh through σ-sweep (S100 data; A=0.30, ω_spread=0.02)")
print("=" * 85)
print(f"{'σ':>7}  {'ch':>4}  {'|μ|':>12}  {'σ_n':>12}  {'R_coh':>8}  "
      f"{'R_angle':>8}  {'mean_arg':>9}")

# Parse: figure out structure
def peek_keys(d, n=3):
    if isinstance(d, dict):
        return list(d.keys())[:n]
    return None


# Try to find per-sigma layout
for k in sorted(cells.keys()) if isinstance(cells, dict) else []:
    cell = cells[k]
    if not isinstance(cell, dict): continue
    if 'per_seed' not in cell:
        continue
    sigma_val = cell.get('sigma', k)
    for ch_k, ch_name in [('z_raw', 'raw'), ('z_st', 'st')]:
        zs = per_seed_cplx(cell['per_seed'], ch_k)
        if not zs or len(zs[0]) == 0: continue
        stats = r_coh(zs)
        mu = np.mean([s[0] for s in stats])
        sig = np.mean([s[1] for s in stats])
        r = np.mean([s[2] for s in stats])
        angs = np.deg2rad([s[3] for s in stats])
        R_a = abs(np.mean(np.exp(1j * angs)))
        mean_arg = np.degrees(np.angle(np.mean(np.exp(1j * angs))))
        print(f"  {float(sigma_val):>5.3f}  {ch_name:>4}  {mu:>12.4e}  {sig:>12.4e}  "
              f"{r:>8.3f}  {R_a:>8.3f}  {mean_arg:>+8.1f}°")

print("\nInterpretation:")
print("  R_coh should peak near σ=0.022 (SR optimum) and drop at σ=0.100.")
print("  R_angle ≈ 1.0 means seeds all point the same way — the seed-level")
print("  mean angle is the same across all seeds for that condition.")
