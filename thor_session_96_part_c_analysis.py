"""
Thor Session #96 — Part C: Rank analysis and null-null Hotelling check.

Questions:
  1. What is the EFFECTIVE dimensionality of the 6-component detector space?
     Hypothesis: rank 2, because raw ≈ rotated ST and dwell ≈ rotated ST.
  2. Is the "Hotelling gain" from Part A spurious (covariance-inversion
     amplification of rank-deficient directions)?
  3. Does the Fisher-optimal 2D projection give |z| equal to ST alone, or
     does it beat ST (implying another information channel)?
"""

import json
import numpy as np
from scipy import stats

DWELL = "/home/dp/gnosis-research/thor_session_96_dwell_results.json"
OUT = "/home/dp/gnosis-research/thor_session_96_part_c_results.json"

d = json.load(open(DWELL))
rows = d['rows']
keys = ['I_raw', 'Q_raw', 'I_st', 'Q_st', 'I_dw', 'Q_dw']

# Thresholds
chi2_2 = stats.chi2.ppf(0.95, df=2)
chi2_4 = stats.chi2.ppf(0.95, df=4)
chi2_6 = stats.chi2.ppf(0.95, df=6)

print("Thresholds for joint detection (p=0.05):")
print(f"  χ²(2) = {chi2_2:.2f}")
print(f"  χ²(4) = {chi2_4:.2f}")
print(f"  χ²(6) = {chi2_6:.2f}")

out_rows = []
for r in rows:
    A = r['A']
    n = d['meta']['params']['n_seeds']

    obs_w = np.array([r['per_seed_w'][k] for k in keys])  # (6, n)
    obs_o = np.array([r['per_seed_o'][k] for k in keys])

    mean_w = obs_w.mean(axis=1)
    mean_o = obs_o.mean(axis=1)
    diff_mean = mean_w - mean_o

    # Pooled covariance of the 6 observables (independent-seeds model)
    cov_w = np.cov(obs_w, ddof=1)
    cov_o = np.cov(obs_o, ddof=1)

    # Standardize by per-seed SE of each component, then compute rank
    # Use correlation matrix (normalized cov) — its eigenvalues partition total variance
    corr_w = np.corrcoef(obs_w)
    eigvals_w = np.sort(np.linalg.eigvalsh(corr_w))[::-1]
    var_explained_w = eigvals_w / eigvals_w.sum()

    # Full Hotelling T² (6 dof)
    cov_diff = cov_w / n + cov_o / n
    try:
        T2_hot = float(diff_mean @ np.linalg.solve(cov_diff, diff_mean))
    except np.linalg.LinAlgError:
        T2_hot = float('nan')

    # RANK-2 Hotelling: project onto top-2 eigenvectors of corr_w, then compute T²
    # in that reduced space. This asks: does the OPTIMAL 2D projection beat ST?
    # Use the pooled data's top-2 PCs (conservative — defines the 2D basis without
    # peeking at signal direction)
    pooled_obs = np.hstack([obs_w, obs_o])
    pooled_mean = pooled_obs.mean(axis=1, keepdims=True)
    pooled_cov = np.cov(pooled_obs - pooled_mean, ddof=1)
    # Use standardized obs for PCA
    stds = np.sqrt(np.diag(pooled_cov))
    pooled_z = (pooled_obs - pooled_mean) / stds[:, None]
    pooled_corr = np.cov(pooled_z, ddof=1)
    eigvals_p, eigvecs_p = np.linalg.eigh(pooled_corr)
    idx_sort = np.argsort(eigvals_p)[::-1]
    eigvals_p = eigvals_p[idx_sort]
    eigvecs_p = eigvecs_p[:, idx_sort]

    # Project each observation into top-k PCs for varying k
    rank_results = []
    for k_rank in [1, 2, 3, 4, 5, 6]:
        P = eigvecs_p[:, :k_rank]
        proj_w = P.T @ ((obs_w - pooled_mean) / stds[:, None])
        proj_o = P.T @ ((obs_o - pooled_mean) / stds[:, None])
        m_w = proj_w.mean(axis=1)
        m_o = proj_o.mean(axis=1)
        dm = m_w - m_o
        cw = np.cov(proj_w, ddof=1) if k_rank > 1 else np.array([[proj_w.var(ddof=1)]])
        co = np.cov(proj_o, ddof=1) if k_rank > 1 else np.array([[proj_o.var(ddof=1)]])
        cov_dm = cw / n + co / n
        try:
            if k_rank == 1:
                T2 = float(dm[0]**2 / cov_dm[0,0])
            else:
                T2 = float(dm @ np.linalg.solve(cov_dm, dm))
        except np.linalg.LinAlgError:
            T2 = float('nan')
        rank_results.append({'k': k_rank, 'T2': T2, 'z': float(np.sqrt(max(0, T2))),
                             'eigval_k': float(eigvals_p[k_rank-1]),
                             'cumvar': float(eigvals_p[:k_rank].sum() / eigvals_p.sum())})

    T2_raw = r['T2_raw']; T2_st = r['T2_st']; T2_dw = r['T2_dw']
    T2_jrs = r['T2_joint_raw_st']
    T2_all6 = r['T2_joint_all6']

    print(f"\nA={A:.3f}: "
          f"|z|_raw={np.sqrt(T2_raw):.2f} |z|_st={np.sqrt(T2_st):.2f} "
          f"|z|_dw={np.sqrt(T2_dw):.2f} |z|_hot={np.sqrt(max(0,T2_hot)):.2f}")
    print(f"  Pooled corr eigvals: " + ", ".join(f"{e:.3f}" for e in eigvals_p))
    print(f"  Cum var explained: " + ", ".join(
        f"{eigvals_p[:k+1].sum()/eigvals_p.sum()*100:5.1f}%" for k in range(6)))
    print(f"  Rank-k T²: " + ", ".join(
        f"k={rr['k']}:T²={rr['T2']:.2f}" for rr in rank_results))

    out_rows.append({
        'A': A,
        'T2_raw': T2_raw, 'T2_st': T2_st, 'T2_dw': T2_dw,
        'T2_joint_raw_st': T2_jrs, 'T2_joint_all6': T2_all6,
        'T2_hotelling_6': T2_hot,
        'eigvals_corr_pooled': eigvals_p.tolist(),
        'eigvecs_corr_pooled': eigvecs_p.tolist(),
        'rank_k_Hotelling': rank_results,
    })

# ---- Null-null Hotelling baseline: split null samples into halves, compute T² ----
# If T²_hot is legitimately measuring signal (vs spurious covariance inversion),
# then T² computed on null-halves should be near expected under H0.
print("\n" + "=" * 76)
print("NULL-NULL HOTELLING BASELINE (split null samples in half, compute T²)")
print("=" * 76)

null_T2_samples = []
null_T2_rank2_samples = []
for r in rows:
    obs_o = np.array([r['per_seed_o'][k] for k in keys])  # (6, 32)
    n = obs_o.shape[1]
    if n < 16:
        continue
    # Multiple random halvings
    rng = np.random.default_rng(42)
    for trial in range(100):
        perm = rng.permutation(n)
        half1 = obs_o[:, perm[:n//2]]
        half2 = obs_o[:, perm[n//2:]]
        dm = half1.mean(axis=1) - half2.mean(axis=1)
        cov = np.cov(half1, ddof=1)/half1.shape[1] + np.cov(half2, ddof=1)/half2.shape[1]
        try:
            T2 = float(dm @ np.linalg.solve(cov, dm))
            null_T2_samples.append(T2)
        except np.linalg.LinAlgError:
            pass
        # Rank-2 version (on same basis as above — recompute PCs from pooled null)
        pooled = obs_o
        pm = pooled.mean(axis=1, keepdims=True)
        ps = pooled.std(axis=1, ddof=1, keepdims=True)
        pcorr = np.cov((pooled - pm) / ps, ddof=1)
        ev, vecs = np.linalg.eigh(pcorr)
        order = np.argsort(ev)[::-1]
        P = vecs[:, order][:, :2]
        p1 = P.T @ ((half1 - pm) / ps)
        p2 = P.T @ ((half2 - pm) / ps)
        dm2 = p1.mean(axis=1) - p2.mean(axis=1)
        cov2 = np.cov(p1, ddof=1)/p1.shape[1] + np.cov(p2, ddof=1)/p2.shape[1]
        try:
            T22 = float(dm2 @ np.linalg.solve(cov2, dm2))
            null_T2_rank2_samples.append(T22)
        except np.linalg.LinAlgError:
            pass

null_T2_samples = np.array(null_T2_samples)
null_T2_rank2_samples = np.array(null_T2_rank2_samples)
print(f"n_samples (full 6D): {len(null_T2_samples)}")
print(f"  mean: {null_T2_samples.mean():.3f}  median: {np.median(null_T2_samples):.3f}")
print(f"  95%: {np.percentile(null_T2_samples, 95):.3f}  "
      f"99%: {np.percentile(null_T2_samples, 99):.3f}")
print(f"  expected E[χ²(6)] = 6  ;  χ²(6) p=0.05 = {chi2_6:.2f}")
print(f"n_samples (rank-2):  {len(null_T2_rank2_samples)}")
print(f"  mean: {null_T2_rank2_samples.mean():.3f}  median: {np.median(null_T2_rank2_samples):.3f}")
print(f"  95%: {np.percentile(null_T2_rank2_samples, 95):.3f}")
print(f"  expected E[χ²(2)] = 2  ;  χ²(2) p=0.05 = {chi2_2:.2f}")

# Save
summary = {
    'meta': {
        'session': 96, 'part': 'C',
        'title': 'Rank analysis + null-null Hotelling validation',
        'source': DWELL,
    },
    'thresholds': {'chi2_2': chi2_2, 'chi2_4': chi2_4, 'chi2_6': chi2_6},
    'per_A_rows': out_rows,
    'null_null_T2_full6': {
        'n': int(len(null_T2_samples)),
        'mean': float(null_T2_samples.mean()),
        'median': float(np.median(null_T2_samples)),
        'p95': float(np.percentile(null_T2_samples, 95)),
        'p99': float(np.percentile(null_T2_samples, 99)),
    },
    'null_null_T2_rank2': {
        'n': int(len(null_T2_rank2_samples)),
        'mean': float(null_T2_rank2_samples.mean()),
        'median': float(np.median(null_T2_rank2_samples)),
        'p95': float(np.percentile(null_T2_rank2_samples, 95)),
    },
}
with open(OUT, 'w') as f:
    json.dump(summary, f, indent=2)
print(f"\nWrote {OUT}")
