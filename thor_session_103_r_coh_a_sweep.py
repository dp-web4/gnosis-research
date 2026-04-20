#!/usr/bin/env python3
"""Closing validation: R_coh across S102 A-sweep.

S102 reported pool-ACF 'plateaus' at each A. Through the per-seed R_coh
lens, the coherent fraction |μ|²/(|μ|²+σ_n²) should grow monotonically
with A in both channels — this is just the physical detection SNR.
"""
import json
import numpy as np


def per_seed_cplx(records, key):
    return [np.array([complex(p[0], p[1]) for p in s[key]]) for s in records]


with open('thor_session_102_plateau_scaling_results.json') as f:
    s102 = json.load(f)

print("R_coh across S102 A-sweep (σ=0.022, ω_spread=0.02, 8×100 chunks)")
print("=" * 75)
print(f"{'A':>5}  {'RAW |μ|':>10}  {'RAW σ_n':>10}  {'RAW R_coh':>9}  "
      f"{'ST |μ|':>8}  {'ST σ_n':>8}  {'ST R_coh':>9}")

A_list = []
raw_rcoh_list = []
st_rcoh_list = []
raw_zdet = []
st_zdet = []

# A=0 and A=0.30 don't have per_A_new_per_seed (they're reused from S101/S98)
# Use per_A.seeds.per_seed_mu_abs and per_seed_sigma_n instead
for A_key in sorted(s102['per_A'].keys(), key=lambda k: float(k)):
    A = s102['per_A'][A_key]['A']
    raw_seeds = s102['per_A'][A_key]['raw']['seeds']
    st_seeds = s102['per_A'][A_key]['st']['seeds']
    raw_mus = np.array(raw_seeds['per_seed_mu_abs'])
    raw_sigs = np.array(raw_seeds['per_seed_sigma_n'])
    st_mus = np.array(st_seeds['per_seed_mu_abs'])
    st_sigs = np.array(st_seeds['per_seed_sigma_n'])
    raw_R = float(np.mean(raw_mus**2 / (raw_mus**2 + raw_sigs**2)))
    st_R = float(np.mean(st_mus**2 / (st_mus**2 + st_sigs**2)))
    raw_mu = float(raw_mus.mean())
    raw_sig = float(raw_sigs.mean())
    st_mu = float(st_mus.mean())
    st_sig = float(st_sigs.mean())
    # z_detection ≈ √(N_chunks · R_coh/(1 - R_coh))
    # Equivalently: |μ|/σ_n · √N_chunks
    n_chunks = 100
    raw_z = raw_mu / raw_sig * np.sqrt(n_chunks) if raw_sig > 0 else 0
    st_z = st_mu / st_sig * np.sqrt(n_chunks) if st_sig > 0 else 0
    A_list.append(A)
    raw_rcoh_list.append(raw_R)
    st_rcoh_list.append(st_R)
    raw_zdet.append(raw_z)
    st_zdet.append(st_z)
    print(f"{A:>5.2f}  {raw_mu:>10.4e}  {raw_sig:>10.4e}  {raw_R:>9.3f}  "
          f"{st_mu:>8.3f}  {st_sig:>8.3f}  {st_R:>9.3f}")

# Detection z-scores
print("\nz_detection = |μ|/σ_n · √N_chunks  (N_chunks=100)")
print(f"{'A':>5}  {'z_det RAW':>10}  {'z_det ST':>10}")
for A, zr, zs in zip(A_list, raw_zdet, st_zdet):
    print(f"{A:>5.2f}  {zr:>10.2f}  {zs:>10.2f}")

# S102 reported pool-ACF plateaus: compare
print("\nComparison: S102 pool-ACF plateau vs per-seed R_coh")
print("(plateau = fit_p_inf; should be close to R_coh but biased upward)")
print(f"{'A':>5}  {'RAW plateau':>12}  {'RAW R_coh':>10}  {'ST plateau':>10}  {'ST R_coh':>9}")
for A_key in sorted(s102['per_A'].keys(), key=lambda k: float(k)):
    cell = s102['per_A'][A_key]
    A = cell['A']
    raw_p = cell['raw']['plateau']['plateau_mean']
    st_p = cell['st']['plateau']['plateau_mean']
    raw_seeds = cell['raw']['seeds']
    st_seeds = cell['st']['seeds']
    raw_mus = np.array(raw_seeds['per_seed_mu_abs'])
    raw_sigs = np.array(raw_seeds['per_seed_sigma_n'])
    st_mus = np.array(st_seeds['per_seed_mu_abs'])
    st_sigs = np.array(st_seeds['per_seed_sigma_n'])
    raw_R = float(np.mean(raw_mus**2 / (raw_mus**2 + raw_sigs**2)))
    st_R = float(np.mean(st_mus**2 / (st_mus**2 + st_sigs**2)))
    print(f"{A:>5.2f}  {raw_p:>12.3f}  {raw_R:>10.3f}  {st_p:>10.3f}  {st_R:>9.3f}")

# Save
out = {
    'title': 'R_coh validation across S102 A-sweep',
    'n_chunks': 100,
    'A_values': A_list,
    'raw_R_coh': raw_rcoh_list,
    'st_R_coh': st_rcoh_list,
    'raw_z_det': raw_zdet,
    'st_z_det': st_zdet,
}
with open('thor_session_103_r_coh_a_sweep.json', 'w') as f:
    json.dump(out, f, indent=2)
print("\nSaved → thor_session_103_r_coh_a_sweep.json")
