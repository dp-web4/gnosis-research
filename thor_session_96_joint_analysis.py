"""
Thor Session #96 — Part A: Joint-detector analysis of S95 per-seed data.

Tests S95 Prediction #4: joint T²_joint = z_I_raw² + z_Q_raw² + z_I_st² + z_Q_st²
should give ~√2× improvement over ST alone.

Also computes:
- Per-cell cross-correlations between (I_raw, Q_raw, I_st, Q_st) across the 32 seeds,
  both within-condition (w, o separately) and for the difference series.
- Hotelling T² (correlation-aware) vs naive-joint (correlation-ignorant) sum-of-squares.
- Detection-threshold crossings at p=0.05 for χ²(2) vs χ²(4) null distributions.
"""

import json
import numpy as np
from scipy import stats

PATH = "/home/dp/gnosis-research/thor_session_95_switch_timing_results.json"
OUT = "/home/dp/gnosis-research/thor_session_96_joint_results.json"

d = json.load(open(PATH))
rows = d["rows_main"]

out = {
    "meta": {
        "session": 96,
        "part": "A",
        "title": "Joint-detector analysis on S95 per-seed data",
        "source": PATH,
        "n_seeds": d["meta"]["params"]["n_seeds"],
        "sigma": d["meta"]["params"]["sigma"],
    },
    "rows": [],
}

# chi-squared thresholds at two-sided p=0.05 for comparison
CHI2_2_P05 = stats.chi2.ppf(0.95, df=2)  # 5.99
CHI2_4_P05 = stats.chi2.ppf(0.95, df=4)  # 9.49
print(f"χ²(2) p=0.05 threshold: {CHI2_2_P05:.3f}")
print(f"χ²(4) p=0.05 threshold: {CHI2_4_P05:.3f}")

print(f"\n{'A':>6} {'|z|_raw':>8} {'|z|_st':>8} "
      f"{'T²_joint':>9} {'|z|_joint':>9} "
      f"{'T²_hot':>8} {'|z|_hot':>8} "
      f"{'χ²2 cross':>10} {'χ²4 cross':>10}")

for row in rows:
    A = row["A"]
    n = row["n_seeds"]

    # Stack per-seed data: shape (4, n_seeds) for w and o
    obs_w = np.array([row["I_raw_w"], row["Q_raw_w"], row["I_st_w"], row["Q_st_w"]])
    obs_o = np.array([row["I_raw_o"], row["Q_raw_o"], row["I_st_o"], row["Q_st_o"]])

    # Per-seed differences: same-seed used for both w and o (paired), but
    # the S95 protocol actually uses INDEPENDENT seeds for the two conditions.
    # z-score per component via difference-of-means / sqrt(var_w/n + var_o/n)
    mean_w = obs_w.mean(axis=1)
    mean_o = obs_o.mean(axis=1)
    var_w = obs_w.var(axis=1, ddof=1)
    var_o = obs_o.var(axis=1, ddof=1)

    se = np.sqrt(var_w/n + var_o/n)
    z = (mean_w - mean_o) / se  # 4-vector

    # --- Individual detector z²
    z_sq_raw = z[0]**2 + z[1]**2
    z_sq_st  = z[2]**2 + z[3]**2

    # --- Naive joint test (assumes independence)
    T2_joint_naive = z_sq_raw + z_sq_st
    z_vec_joint_naive = np.sqrt(T2_joint_naive)

    # --- Hotelling-style joint test (correlation-aware)
    # Covariance of (mean_w - mean_o) vector across the 4 observables.
    # Under independent seeds for w and o: Cov(Δμ) = (1/n)·Σ_w + (1/n)·Σ_o
    cov_w = np.cov(obs_w, ddof=1)  # (4,4)
    cov_o = np.cov(obs_o, ddof=1)
    cov_diff_mean = cov_w/n + cov_o/n

    diff_mean = mean_w - mean_o
    # Hotelling T² = Δμᵀ · Cov(Δμ)⁻¹ · Δμ
    try:
        T2_hot = float(diff_mean @ np.linalg.solve(cov_diff_mean, diff_mean))
    except np.linalg.LinAlgError:
        T2_hot = float("nan")
    z_vec_hot = np.sqrt(T2_hot) if T2_hot >= 0 else float("nan")

    # --- Cross-correlation matrix under H1 (using w-data)
    corr_w = np.corrcoef(obs_w)
    corr_o = np.corrcoef(obs_o)

    # --- Detection threshold crossings
    cross_chi2_2 = T2_joint_naive > CHI2_2_P05  # treating 4-vec as 2 independent 2-vecs — wrong but for comparison
    cross_chi2_4 = T2_joint_naive > CHI2_4_P05

    rec = {
        "A": A,
        "z_I_raw": float(z[0]), "z_Q_raw": float(z[1]),
        "z_I_st":  float(z[2]), "z_Q_st":  float(z[3]),
        "T2_raw":   float(z_sq_raw),
        "T2_st":    float(z_sq_st),
        "T2_joint_naive": float(T2_joint_naive),
        "z_vec_joint_naive": float(z_vec_joint_naive),
        "T2_hotelling":   float(T2_hot),
        "z_vec_hotelling": float(z_vec_hot),
        "corr_w": corr_w.tolist(),
        "corr_o": corr_o.tolist(),
        "cross_chi2_4_p05": bool(cross_chi2_4),
    }
    out["rows"].append(rec)

    cross_str = (f"{'yes' if cross_chi2_2 else 'no':>10} "
                 f"{'yes' if cross_chi2_4 else 'no':>10}")

    print(f"{A:6.3f} {np.sqrt(z_sq_raw):8.3f} {np.sqrt(z_sq_st):8.3f} "
          f"{T2_joint_naive:9.3f} {z_vec_joint_naive:9.3f} "
          f"{T2_hot:8.3f} {z_vec_hot:8.3f} "
          f"{cross_str}")

# --- Summary: ratio of joint to ST
print("\nRatios (joint / ST in |z|):")
for r in out["rows"]:
    z_st = np.sqrt(r["T2_st"])
    z_joint_naive = r["z_vec_joint_naive"]
    z_joint_hot = r["z_vec_hotelling"]
    ratio_n = z_joint_naive / z_st if z_st > 0 else float("nan")
    ratio_h = z_joint_hot / z_st if z_st > 0 else float("nan")
    print(f"  A={r['A']:.3f}  |z|_st={z_st:.3f}  naive ratio={ratio_n:.3f}  hot ratio={ratio_h:.3f}")

# --- Summary: correlation structure (average over amplitudes)
print("\nMean correlation matrix (with-signal trajectories, averaged over A):")
print("           I_raw   Q_raw   I_st    Q_st")
M_w = np.mean([np.array(r["corr_w"]) for r in out["rows"]], axis=0)
for i, lbl in enumerate(["I_raw", "Q_raw", "I_st", "Q_st"]):
    print(f"{lbl:>8}   " + "  ".join(f"{M_w[i,j]:+.3f}" for j in range(4)))

print("\nMean correlation matrix (without-signal trajectories, averaged over A):")
print("           I_raw   Q_raw   I_st    Q_st")
M_o = np.mean([np.array(r["corr_o"]) for r in out["rows"]], axis=0)
for i, lbl in enumerate(["I_raw", "Q_raw", "I_st", "Q_st"]):
    print(f"{lbl:>8}   " + "  ".join(f"{M_o[i,j]:+.3f}" for j in range(4)))

out["summary"] = {
    "chi2_2_p05": CHI2_2_P05,
    "chi2_4_p05": CHI2_4_P05,
    "mean_corr_w": M_w.tolist(),
    "mean_corr_o": M_o.tolist(),
}

with open(OUT, "w") as f:
    json.dump(out, f, indent=2)
print(f"\nWrote {OUT}")
