#!/usr/bin/env python3
"""Thor Session #94 analysis: fit scaling law + print detection cliff table."""
import json
import numpy as np

with open('thor_session_94_detection_cliff_results.json') as f:
    d = json.load(f)

rows = d['results']
base = [r for r in rows if r['config'] == 'base']
sv = [r for r in rows if r['config'] == 'seeds_variant']

A = np.array([r['A'] for r in base])
B = np.array([r['budget_B'] for r in base])
zI = np.array([r['z_I'] for r in base])
zQ = np.array([r['z_Q'] for r in base])
T2 = np.array([r['T2'] for r in base])
z_vec = np.sqrt(T2)

print("=" * 72)
print("1. Scaling law fit: |z_vec| = k · A · √B")
print("=" * 72)

x = A * np.sqrt(B)
k = float(np.sum(z_vec * x) / np.sum(x**2))
pred = k * x
ss_res = float(np.sum((z_vec - pred)**2))
ss_tot = float(np.sum((z_vec - z_vec.mean())**2))
r2 = 1 - ss_res / ss_tot

print(f"  k = {k:.2f}   R² = {r2:.3f}")
print(f"  A_min (z_thr=2) at B=1: {2/k:.3f}")
print(f"  A_min (z_thr=2) at B=4: {2/(k*2):.3f}")
print(f"  A_min (z_thr=2) at B=8: {2/(k*np.sqrt(8)):.3f}")

print("\n  {:>5}  {:>3}  {:>8}  {:>8}  {:>8}  {:>8}  {:>8}".format(
    "A", "B", "z_I", "z_Q", "|z_vec|", "pred(k)", "residual"))
for a, b, zi, zq, zv in zip(A, B, zI, zQ, z_vec):
    p = k * a * np.sqrt(b)
    print(f"  {a:5.2f}  {b:3d}  {zi:+8.2f}  {zq:+8.2f}  {zv:8.2f}  "
          f"{p:8.2f}  {zv-p:+8.2f}")

print("\n" + "=" * 72)
print("2. Scaling check per amplitude: z_vec(B) / z_vec(B=1) vs √B")
print("=" * 72)
print(f"  {'A':>5}  B1     B2     B4     B8    |   √B: 1.00 1.41 2.00 2.83")
for a in sorted(set(A)):
    zs = [r['T2']**0.5 for r in base if r['A'] == a]
    bs = [r['budget_B'] for r in base if r['A'] == a]
    order = np.argsort(bs)
    zs = [zs[i] for i in order]
    bs = [bs[i] for i in order]
    ratios = [z / zs[0] for z in zs]
    print(f"  A={a:.2f}  {zs[0]:4.2f}  {zs[1]:4.2f}  {zs[2]:4.2f}  {zs[3]:4.2f}  | "
          f"rel: {ratios[0]:4.2f} {ratios[1]:4.2f} {ratios[2]:4.2f} {ratios[3]:4.2f}")

print("\n" + "=" * 72)
print("3. Long-T vs More-Seeds at matched compute (B=4)")
print("=" * 72)
print(f"  {'A':>5}  long-T (n=16, T=16000s)     more-N (n=64, T=4000s)     Δ")
print(f"  {'':5}  {'z_I':>7} {'z_Q':>7} {'|z|':>5}     "
      f"{'z_I':>7} {'z_Q':>7} {'|z|':>5}     {'|z|':>6}")
for a in sorted(set(A)):
    bt = next(r for r in base if r['A'] == a and r['budget_B'] == 4)
    st = next(r for r in sv if r['A'] == a)
    bv = np.sqrt(bt['T2']); sv_v = np.sqrt(st['T2'])
    print(f"  {a:.2f}  {bt['z_I']:+7.2f} {bt['z_Q']:+7.2f} {bv:5.2f}     "
          f"{st['z_I']:+7.2f} {st['z_Q']:+7.2f} {sv_v:5.2f}     {sv_v-bv:+6.2f}")

# Test hypothesis: are the two sets statistically different?
# Under null of equivalence, expected mean diff = 0; std of diff ~ √2
diffs = []
for a in sorted(set(A)):
    bt = next(r for r in base if r['A'] == a and r['budget_B'] == 4)
    st = next(r for r in sv if r['A'] == a)
    diffs.append(np.sqrt(st['T2']) - np.sqrt(bt['T2']))
diffs = np.array(diffs)
mean_d = diffs.mean()
print(f"\n  Mean |z| difference (seeds - long) across 4 amplitudes: {mean_d:+.2f}")
print(f"  Per-amplitude std ~ √2 ≈ 1.41; 4-sample SE of mean ≈ 0.71")
t_stat = mean_d / 0.71
print(f"  t ≈ {t_stat:+.2f}  →  {'long > seeds' if mean_d < -1 else 'seeds > long' if mean_d > 1 else 'consistent with equivalence'}")
