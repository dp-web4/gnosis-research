#!/usr/bin/env python3
"""Per-seed vs pool comparison on S98 ST channel (analogous to RAW analysis).

If ST is a genuine plateau at 0.76 both per-seed and cross-seed, seeds all
lock to the same phase. If per-seed is 0.76 plateau but cross-seed |mean(Φ)|
decays like RAW does, the "plateau" is also a seed-heterogeneity artifact.
"""
import json
import numpy as np

with open('thor_session_98_phase_drift_results.json') as f:
    s98 = json.load(f)


def per_seed_complex(records, key):
    return [np.array([complex(p[0], p[1]) for p in s[key]]) for s in records]


def single_seed_acf(z, max_lag):
    phi = np.unwrap(np.angle(z))
    k = np.arange(len(phi))
    slope, _ = np.polyfit(k, phi, 1)
    resid = phi - slope * k - phi[0]
    u = np.exp(1j * resid)
    acf = np.zeros(max_lag + 1, dtype=complex)
    acf[0] = 1.0
    for m in range(1, max_lag + 1):
        if len(u) - m <= 0: continue
        acf[m] = np.mean(u[:-m] * np.conj(u[m:]))
    return acf


z_sts = per_seed_complex(s98['main']['per_seed'], 'z_st')
z_raws = per_seed_complex(s98['main']['per_seed'], 'z_raw')

print("ST: per-seed ACF magnitudes + seed-angle mean")
print("=" * 78)
print(f"{'seed':>4}  {'|<z>|':>8}  {'arg(<z>)':>9}  {'|Φ(1)|':>8}  {'|Φ(20)|':>8}  {'|Φ(60)|':>8}")
seed_acfs_st = []
seed_angles_st = []
for i, z in enumerate(z_sts):
    mu = z.mean()
    seed_angles_st.append(np.angle(mu))
    acf = single_seed_acf(z, 80)
    seed_acfs_st.append(acf)
    print(f"{i:>4}  {abs(mu):>8.3f}  {np.degrees(np.angle(mu)):>+8.1f}°  "
          f"{abs(acf[1]):>7.3f}   {abs(acf[20]):>7.3f}   {abs(acf[60]):>7.3f}")

stacked_st = np.array(seed_acfs_st)
pooled_cplx_st = np.mean(stacked_st, axis=0)
pooled_abs_mean_st = np.mean(np.abs(stacked_st), axis=0)

print("\nST: |mean(Φ)| vs mean(|Φ|):")
for m in [1, 10, 20, 30, 40, 50, 60, 70, 80]:
    a = abs(pooled_cplx_st[m])
    b = pooled_abs_mean_st[m]
    print(f"  lag {m:>3}:  |mean(Φ)|={a:.3f}   mean(|Φ|)={b:.3f}    diff={a-b:+.3f}")

# Cross-seed angle coherence: R = |mean(exp(i*seed_angle))|
R_seeds_st = abs(np.mean(np.exp(1j * np.array(seed_angles_st))))
print(f"\nST seed-level mean angle: {np.degrees(np.mean(seed_angles_st)):.1f}°")
print(f"ST seed-level angle coherence R = {R_seeds_st:.3f}")

# Same for RAW for comparison
seed_angles_raw = []
for z in z_raws:
    seed_angles_raw.append(np.angle(z.mean()))
R_seeds_raw = abs(np.mean(np.exp(1j * np.array(seed_angles_raw))))
print(f"\nRAW seed angles (deg): {[f'{np.degrees(a):+.0f}' for a in seed_angles_raw]}")
print(f"RAW seed-level angle coherence R = {R_seeds_raw:.3f}")
print(f"ST  seed angles (deg): {[f'{np.degrees(a):+.0f}' for a in seed_angles_st]}")

# KEY: check whether within-seed ACF(m) differs from mean(|Φ_seed|) at m
# which it will if seeds have drift WITHIN the seed.
print("\nWithin-seed stability: arg(Φ_seed(m)) spread across seeds at each m")
print("If seeds all had the same drift, arg would be the same per seed at each m.")
print(f"{'lag':>4}  {'arg std (RAW,°)':>15}  {'arg std (ST,°)':>15}")
seed_acfs_raw = [single_seed_acf(z, 80) for z in z_raws]
for m in [1, 5, 10, 20, 40, 60, 80]:
    raw_args = [np.degrees(np.angle(a[m])) for a in seed_acfs_raw]
    st_args = [np.degrees(np.angle(a[m])) for a in seed_acfs_st]
    # Use circular std: R = |mean(e^{iθ})|; σ_circ = sqrt(-2·ln(R))
    def cstd(angles_deg):
        r = abs(np.mean(np.exp(1j * np.deg2rad(angles_deg))))
        return float(np.degrees(np.sqrt(-2*np.log(r)))) if r > 0.01 else None
    print(f"{m:>4}  {cstd(raw_args):>14.1f}°  {cstd(st_args):>14.1f}°")

out = {
    'source': 'S98 main (ω_spread=0.02, A=0.30, σ=0.022), 8 seeds × 100 chunks',
    'raw_seed_angles_rad': [float(a) for a in seed_angles_raw],
    'raw_seed_angle_coherence_R': float(R_seeds_raw),
    'st_seed_angles_rad': [float(a) for a in seed_angles_st],
    'st_seed_angle_coherence_R': float(R_seeds_st),
    'raw_pooled_mean_complex_abs': [float(abs(z)) for z in pooled_cplx_st.tolist()],
    'st_pooled_mean_complex_abs': [float(abs(z)) for z in pooled_cplx_st.tolist()],
    'st_pooled_absmean': pooled_abs_mean_st.tolist(),
    'raw_per_seed_abs_acf': [np.abs(a).tolist() for a in seed_acfs_raw],
    'st_per_seed_abs_acf': [np.abs(a).tolist() for a in seed_acfs_st],
}
with open('thor_session_103_per_seed_st.json', 'w') as f:
    json.dump(out, f, indent=2, default=float)
print("\nSaved → thor_session_103_per_seed_st.json")
