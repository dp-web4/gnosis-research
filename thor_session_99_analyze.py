#!/usr/bin/env python3
"""Analyze S99 results: seed-heterogeneity mechanism for seeds-beat-long.

Ingests thor_session_99_seed_heterogeneity_results.json and produces:
- Part-1 summary table (per-channel per-seed stats from S98 reanalysis)
- Part-2 across-cell table: mean |z|_sig, SD, |z|_null, detection power
- Predicted vs observed per-channel scaling from detuning sinc model
- Writes thor_session_99_analysis.json + prints a punch summary
"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
RESULTS = HERE / "thor_session_99_seed_heterogeneity_results.json"


def sinc_loss(delta_omega_std, T_seconds):
    """Expected |z| loss for coherent integration under Gaussian detuning Δω.

    Single trajectory length T, detuning ~N(0, σ_Δω). Expected magnitude
    E[|sinc(Δω·T/2)|] averaged over Δω. Closed form for Gaussian Δω is
    not pretty — Monte Carlo it. Returns E[sinc(Δω·T/2)] as fraction retained.
    """
    rng = np.random.default_rng(1)
    N = 50_000
    dw = rng.normal(0.0, delta_omega_std, size=N)
    x = dw * T_seconds / 2.0
    # np.sinc uses normalized sinc (sin(pi x)/(pi x)); we need sin(x)/x.
    s = np.where(np.abs(x) < 1e-9, 1.0, np.sin(x) / x)
    return float(np.mean(s)), float(np.std(s, ddof=1))


def ou_wander_gain(sigma_phi_rad, tau_wander_s, T_per_s, N_real=5000,
                   n_steps_per_tau=20):
    """Monte-Carlo E[|G|²] for coherent integration of exp(iφ(t)) over T_per,
    where φ(t) is OU with steady-state SD σ_φ and correlation time τ_wander.

    Discretized with dt = τ_wander / n_steps_per_tau.
    G = (1/T) ∫ exp(iφ(t)) dt; returns mean |G| and sqrt(mean |G|²).
    """
    dt = tau_wander_s / n_steps_per_tau
    n_steps = max(2, int(T_per_s / dt))
    # AR(1) coefficient for OU: phi_{k+1} = a*phi_k + sqrt(1-a²)*σ_φ*η
    a = np.exp(-dt / tau_wander_s)
    innov_std = sigma_phi_rad * np.sqrt(1 - a**2)
    rng = np.random.default_rng(42)
    # vectorize across realizations
    phi = rng.normal(0.0, sigma_phi_rad, size=N_real)  # stationary start
    I_sum = np.zeros(N_real)
    Q_sum = np.zeros(N_real)
    for k in range(n_steps):
        I_sum += np.cos(phi)
        Q_sum += np.sin(phi)
        phi = a * phi + innov_std * rng.normal(size=N_real)
    I_avg = I_sum / n_steps
    Q_avg = Q_sum / n_steps
    mag = np.sqrt(I_avg**2 + Q_avg**2)
    return float(mag.mean()), float(np.sqrt((mag**2).mean()))


def cell_table(part2):
    """Summarize part2 cells into a tidy table."""
    rows = []
    for c in part2:
        for ch_name, ch_key in [("RAW", "raw_channel"), ("ST", "st_channel")]:
            ch = c[ch_key]
            rows.append({
                "n_seeds": c["n_seeds"],
                "T_per_s": c["T_per_s"],
                "channel": ch_name,
                "z_mag_sig_mean": ch["z_mag_sig_mean"],
                "z_mag_sig_sd": ch["z_mag_sig_sd"],
                "z_mag_null_mean": ch["z_mag_null_mean"],
                "z_mag_null_sd": ch["z_mag_null_sd"],
                "null_SD_I": ch["null_SD_I"],
                "null_SD_Q": ch["null_SD_Q"],
                "null_mean_I": ch["null_mean_I"],
                "null_mean_Q": ch["null_mean_Q"],
            })
    return rows


def detection_power(ch):
    """Compute detection power at 5% FAR using null |z| distribution as threshold."""
    null_mags = np.array(ch["z_mag_null_list"])
    sig_mags = np.array(ch["z_mag_sig_list"])
    # 95th percentile of null
    if len(null_mags) == 0:
        return float("nan"), float("nan")
    thr = float(np.quantile(null_mags, 0.95))
    pw = float((sig_mags > thr).mean())
    return thr, pw


def main():
    d = json.loads(RESULTS.read_text())
    part1 = d["part1_s98_postprocess"]
    part2 = d["part2_matched_compute"]

    analysis = {"meta": d["meta"], "part1_summary": {}, "part2_cells": [],
                "sinc_predictions": {}, "mechanism_verdict": {},
                "phase_wander": {}}

    # ─── Phase-wander (residual after linear Δω fit) ──────────────────────
    print("\n=== PHASE WANDER (residual after linear Δω fit) ===\n")
    print(f"{'chan':<6} {'resid_rms':>10} {'acorr_m=1':>10} {'acorr_m=5':>10} {'acorr_m=10':>11}")
    for ch_key in ["z_raw", "z_st"]:
        rows = part1["channels"][ch_key]["per_seed_rows"]
        resid_rms = np.array([r["resid_rms_rad"] for r in rows])
        ac_resid = np.array([r["acorr_resid_phase"] for r in rows])  # (n_seeds, 30)
        mean_ac = ac_resid.mean(axis=0)
        print(f"{ch_key:<6} {resid_rms.mean():>7.3f}±{resid_rms.std(ddof=1):<.2f} "
              f"{mean_ac[0]:>10.3f} {mean_ac[4]:>10.3f} {mean_ac[9]:>11.3f}")
        analysis["phase_wander"][ch_key] = {
            "resid_rms_mean": float(resid_rms.mean()),
            "resid_rms_sd": float(resid_rms.std(ddof=1)),
            "acorr_resid_phase_mean_30lags": mean_ac.tolist(),
        }
    print("\n  NOTE: raw-channel phase after linear-fit residual is ~3 rad RMS with")
    print("  slow (~10-chunk) autocorrelation decay. Not linear drift; slow RANDOM WALK.")
    print("  ST-channel residual is 0.54 rad RMS with essentially zero autocorr.")
    print("  Δω_std for raw is partly noisy-fit artifact on wandering phase.\n")


    # ─── Part 1 summary ────────────────────────────────────────────────────
    print("\n=== PART 1 SUMMARY (S98 per-seed reanalysis) ===\n")
    print(f"{'chan':<6} {'mean|z|':>10} {'across-CV%':>11} {'within-CV%':>11} "
          f"{'Δω_std':>10} {'Δω·T128k°':>11} {'R_seed':>7}")
    for ch_key in ["z_raw", "z_st"]:
        s = part1["channels"][ch_key]["summary"]
        dw_std = s["delta_omega_std"]
        dw_T128 = dw_std * 128_000
        print(f"{ch_key:<6} {s['across_seed_mag_mean']:>10.4f} "
              f"{100*s['across_seed_mag_cv']:>10.2f}% "
              f"{100*s['within_seed_cv_mean']:>10.2f}% "
              f"{dw_std:>10.2e} {np.degrees(dw_T128):>10.2f}° "
              f"{s['R_across_seed_angles']:>7.4f}")
        analysis["part1_summary"][ch_key] = dict(s)
        analysis["part1_summary"][ch_key]["delta_omega_T128000_rad"] = dw_T128
        analysis["part1_summary"][ch_key]["delta_omega_T128000_deg"] = float(np.degrees(dw_T128))

    # ─── OU-wander predictions (raw channel; ST has no meaningful wander) ─
    print("\n=== OU-WANDER PREDICTION (raw only; ST has no meaningful wander) ===\n")
    # Estimate τ_wander from raw residual-phase autocorr: fit exp(-m/τ) to first 10 lags
    rows = part1["channels"]["z_raw"]["per_seed_rows"]
    ac_raw = np.array([r["acorr_resid_phase"] for r in rows]).mean(axis=0)[:10]
    m_lags = np.arange(1, 11)
    pos_mask = ac_raw > 0.05
    if pos_mask.sum() >= 3:
        slope, _ = np.polyfit(m_lags[pos_mask], np.log(ac_raw[pos_mask]), 1)
        tau_wander_chunks = float(-1.0 / slope) if slope < 0 else float("inf")
    else:
        tau_wander_chunks = float("inf")
    T_chunk_s = part1["T_chunk_s"]
    tau_wander_s = tau_wander_chunks * T_chunk_s
    sigma_phi_raw = float(np.mean([r["resid_rms_rad"] for r in rows]))
    print(f"  raw residual σ_φ = {sigma_phi_raw:.2f} rad, τ_wander = {tau_wander_chunks:.1f} chunks "
          f"= {tau_wander_s:.0f}s")
    ou_pred = {}
    for n, T in [(32, 4000), (8, 16000), (2, 64000), (1, 128000)]:
        g_mean, g_rms = ou_wander_gain(sigma_phi_raw, tau_wander_s, T)
        print(f"    n={n:>2} T={T:>6}s  E[|G|]={g_mean:.3f}  √E[|G|²]={g_rms:.3f}")
        ou_pred[n] = {"T_per_s": T, "E_G_mean": g_mean, "E_G_rms": g_rms}
    analysis["ou_wander"] = {
        "sigma_phi_raw": sigma_phi_raw,
        "tau_wander_chunks": tau_wander_chunks,
        "tau_wander_s": tau_wander_s,
        "predictions_per_n": ou_pred,
    }

    # ─── Sinc-loss predictions ────────────────────────────────────────────
    print("\n=== DETUNING-SINC PREDICTION vs n ===\n")
    print("Per-seed detuning σ_Δω fit from S98. Expected fractional magnitude")
    print("retained = E[sin(x)/x], x=Δω·T_per/2. Matched compute: n·T_per = 128000s.\n")
    for ch_key, ch_label in [("z_raw", "RAW"), ("z_st", "ST")]:
        dw_std = part1["channels"][ch_key]["summary"]["delta_omega_std"]
        print(f"  {ch_label:<4} Δω_std={dw_std:.3e}")
        analysis["sinc_predictions"][ch_label] = {}
        for n, T in [(32, 4000), (8, 16000), (2, 64000), (1, 128000)]:
            mean_sinc, sd_sinc = sinc_loss(dw_std, T)
            # Per-seed signal retained × n (coherent sum) → signal magnitude.
            # Per-seed noise scales as √T (number of events). Coherent sum of n
            # seeds: noise ∝ √n·√T = √(n·T) = √128000 (constant across cells).
            # So |z|_cell ∝ n × mean_sinc_per_seed × √T_per  (since signal ∝ T)
            # wait: per-seed signal ∝ T × mean_sinc. coherent sum of n: n × T × mean_sinc
            # noise: √(n·T). |z| ∝ √(n·T) × mean_sinc.  (since √(n·T)=const, |z| ∝ mean_sinc)
            # Actually: signal_per_seed ∝ T, noise_per_seed ∝ √T, coherent sum n seeds:
            # signal_sum = n·T·mean_sinc, noise_sum = √n·√T. |z| = √(n·T)·mean_sinc.
            # √(n·T) is constant → |z| ∝ mean_sinc.
            print(f"    n={n:>2} T={T:>6}s  E[sinc]={mean_sinc:.3f}  (predicted |z| scale)")
            analysis["sinc_predictions"][ch_label][n] = {
                "T_per_s": T, "mean_sinc": mean_sinc, "sd_sinc": sd_sinc,
            }

    # ─── Per-cell null SD ─── also check if matched-compute constancy holds ──
    print("\n=== PER-CELL NULL SD (expected constant under matched-compute) ===\n")
    print(f"{'n':>3} {'T_per':>7} {'RAW_SD_I':>10} {'RAW_SD_Q':>10} {'ST_SD_I':>9} {'ST_SD_Q':>9}")
    for c in part2:
        print(f"{c['n_seeds']:>3} {c['T_per_s']:>7.0f} "
              f"{c['raw_channel']['null_SD_I']:>10.4f} {c['raw_channel']['null_SD_Q']:>10.4f} "
              f"{c['st_channel']['null_SD_I']:>9.3f} {c['st_channel']['null_SD_Q']:>9.3f}")

    # ─── Part 2 cells: per-cell |z| using EACH cell's own null SD ─────────
    print("\n=== PART 2 RESULTS (per-cell |z| vs pooled-null |z|) ===\n")
    # Organize by channel
    by_channel = {"RAW": [], "ST": []}
    for c in part2:
        for ch_key, ch_label in [("raw_channel", "RAW"), ("st_channel", "ST")]:
            ch = c[ch_key]
            thr95, pw = detection_power(ch)
            row = {
                "n_seeds": c["n_seeds"], "T_per_s": c["T_per_s"],
                "z_mag_sig_mean": ch["z_mag_sig_mean"],
                "z_mag_sig_sd": ch["z_mag_sig_sd"],
                "z_mag_null_mean": ch["z_mag_null_mean"],
                "z_mag_null_sd": ch["z_mag_null_sd"],
                "null_q95": thr95, "power_5pct_far": pw,
                "null_SD_I": ch["null_SD_I"], "null_SD_Q": ch["null_SD_Q"],
            }
            by_channel[ch_label].append(row)
            analysis["part2_cells"].append({**row, "channel": ch_label})

    # Pooled-null analysis: if noise is stationary at matched compute, pooling
    # across cells gives a much more stable null-SD estimate (K_total=24 vs 6).
    print("\n=== POOLED-NULL |z| (pools 24 null reps across cells per channel) ===\n")
    # Collect all null reps across cells per channel
    pooled_null = {"RAW": {"I": [], "Q": []}, "ST": {"I": [], "Q": []}}
    for c in part2:
        for ch_key, ch_label in [("raw_channel", "RAW"), ("st_channel", "ST")]:
            ch = c[ch_key]
            # Retrieve null rep raw IQ values
            null_reps = c["null_reps"]
            for nr in null_reps:
                if ch_label == "RAW":
                    pooled_null["RAW"]["I"].append(nr["I_raw_sum"])
                    pooled_null["RAW"]["Q"].append(nr["Q_raw_sum"])
                else:
                    pooled_null["ST"]["I"].append(nr["I_st_sum"])
                    pooled_null["ST"]["Q"].append(nr["Q_st_sum"])

    analysis["pooled_null"] = {}
    for ch_label in ["RAW", "ST"]:
        Ivals = np.array(pooled_null[ch_label]["I"])
        Qvals = np.array(pooled_null[ch_label]["Q"])
        sd_I_pool = float(Ivals.std(ddof=1))
        sd_Q_pool = float(Qvals.std(ddof=1))
        mean_I_pool = float(Ivals.mean())
        mean_Q_pool = float(Qvals.mean())
        analysis["pooled_null"][ch_label] = {
            "sd_I_pool": sd_I_pool, "sd_Q_pool": sd_Q_pool,
            "mean_I_pool": mean_I_pool, "mean_Q_pool": mean_Q_pool,
            "n_pool": len(Ivals),
        }
        print(f"  {ch_label:<4} pooled null: SD_I={sd_I_pool:.4f} SD_Q={sd_Q_pool:.4f}"
              f"  (vs per-cell estimates SE ~30%)")

    # Recompute per-cell |z|_sig using the POOLED null SD.
    print(f"\n  {'channel':<6} {'n':>3} {'T_per':>7} {'|z|_sig_pooled':>15} {'|z|_sig_percell':>18}")
    for c in part2:
        for ch_key, ch_label in [("raw_channel", "RAW"), ("st_channel", "ST")]:
            sd_I_p = analysis["pooled_null"][ch_label]["sd_I_pool"]
            sd_Q_p = analysis["pooled_null"][ch_label]["sd_Q_pool"]
            mu_I_p = analysis["pooled_null"][ch_label]["mean_I_pool"]
            mu_Q_p = analysis["pooled_null"][ch_label]["mean_Q_pool"]
            sig_reps = c["sig_reps"]
            if ch_label == "RAW":
                Is = np.array([s["I_raw_sum"] for s in sig_reps])
                Qs = np.array([s["Q_raw_sum"] for s in sig_reps])
            else:
                Is = np.array([s["I_st_sum"] for s in sig_reps])
                Qs = np.array([s["Q_st_sum"] for s in sig_reps])
            zI = (Is - mu_I_p) / sd_I_p
            zQ = (Qs - mu_Q_p) / sd_Q_p
            mag = np.sqrt(zI**2 + zQ**2)
            z_pooled_mean = float(mag.mean())
            z_pooled_sd = float(mag.std(ddof=1))
            print(f"  {ch_label:<6} {c['n_seeds']:>3} {c['T_per_s']:>7.0f} "
                  f"{z_pooled_mean:>6.2f}±{z_pooled_sd:<5.2f}        "
                  f"{c[ch_key]['z_mag_sig_mean']:>6.2f}±{c[ch_key]['z_mag_sig_sd']:<5.2f}")
            # Store in analysis dict
            for r in analysis["part2_cells"]:
                if r["n_seeds"] == c["n_seeds"] and r["channel"] == ch_label:
                    r["z_mag_sig_mean_pooled"] = z_pooled_mean
                    r["z_mag_sig_sd_pooled"] = z_pooled_sd

    for label, rows in by_channel.items():
        print(f"\n  {label} channel:")
        print(f"  {'n':>3} {'T_per_s':>8} {'|z|_sig':>12} {'|z|_null':>10} "
              f"{'null_q95':>9} {'pow@5%':>8}")
        for r in rows:
            print(f"  {r['n_seeds']:>3} {r['T_per_s']:>8.0f} "
                  f"{r['z_mag_sig_mean']:>6.2f}±{r['z_mag_sig_sd']:<5.2f} "
                  f"{r['z_mag_null_mean']:>10.2f} "
                  f"{r['null_q95']:>9.2f} {r['power_5pct_far']:>8.2f}")

    # ─── Flatness tests ────────────────────────────────────────────────────
    print("\n=== FLATNESS OF |z|_sig ACROSS CELLS ===\n")
    print("Under stationary signal + white noise at matched compute, |z|_sig is")
    print("predicted to be CONSTANT across cells. Test with 1-way ANOVA F.\n")
    analysis["flatness"] = {}
    for c_idx, c in enumerate(part2):
        pass  # placeholder
    for ch_label in ["RAW", "ST"]:
        # Gather per-rep |z|_sig using PER-CELL null SD (keeps channel-specific
        # null scaling intact for raw). This is the right statistic for RAW.
        cell_zmags = []
        for c in part2:
            ch = c["raw_channel"] if ch_label == "RAW" else c["st_channel"]
            cell_zmags.append(np.array(ch["z_mag_sig_list"]))
        # One-way ANOVA
        overall_mean = np.mean([m.mean() for m in cell_zmags])
        n_k = [len(m) for m in cell_zmags]
        K = len(cell_zmags)
        grand_mean = np.concatenate(cell_zmags).mean()
        ss_between = sum(n * (m.mean() - grand_mean)**2 for n, m in zip(n_k, cell_zmags))
        ss_within = sum(((m - m.mean())**2).sum() for m in cell_zmags)
        df_b = K - 1
        df_w = sum(n_k) - K
        ms_b = ss_between / df_b
        ms_w = ss_within / df_w if df_w > 0 else float("inf")
        F = ms_b / ms_w if ms_w > 0 else float("inf")
        from scipy import stats as _stats
        p_F = 1.0 - _stats.f.cdf(F, df_b, df_w)
        per_cell_means = [float(m.mean()) for m in cell_zmags]
        per_cell_sds = [float(m.std(ddof=1)) for m in cell_zmags]
        print(f"  {ch_label}:")
        print(f"    per-cell |z|_sig means: {[round(x, 2) for x in per_cell_means]}")
        print(f"    per-cell |z|_sig SDs:   {[round(x, 2) for x in per_cell_sds]}")
        print(f"    F({df_b},{df_w}) = {F:.2f}, p = {p_F:.4f}")
        flat_verdict = "FLAT (consistent with stationary + matched-compute)" if p_F > 0.05 \
            else "NOT flat (possible non-stationarity)"
        print(f"    verdict: {flat_verdict}\n")
        analysis["flatness"][ch_label] = {
            "per_cell_z_means": per_cell_means, "per_cell_z_sds": per_cell_sds,
            "F": float(F), "df_b": df_b, "df_w": df_w, "p_F": float(p_F),
            "verdict": flat_verdict,
        }

        # RAW-rescaled check: at matched compute, null SD_sum for RAW is
        # expected ∝ √(n/T_per) (per-seed mean-normalized MF on white noise).
        # Standardize each cell by its *expected* scale, then pool.
        if ch_label == "RAW":
            pooled_zmags = []
            # Collect all null reps across cells with scaling to unit SD under
            # white-noise prediction. The theoretical null SD scale per cell is
            # σ_0·√(n/T_per). Fit σ_0 from pooled (signal-free) null.
            scaled_null_I = []
            scaled_null_Q = []
            for c in part2:
                w = np.sqrt(c["T_per_s"] / c["n_seeds"])  # inverse of √(n/T)
                for nr in c["null_reps"]:
                    scaled_null_I.append(nr["I_raw_sum"] * w)
                    scaled_null_Q.append(nr["Q_raw_sum"] * w)
            scaled_null_I = np.array(scaled_null_I)
            scaled_null_Q = np.array(scaled_null_Q)
            sd_I_sc = float(scaled_null_I.std(ddof=1))
            sd_Q_sc = float(scaled_null_Q.std(ddof=1))
            mu_I_sc = float(scaled_null_I.mean())
            mu_Q_sc = float(scaled_null_Q.mean())
            print(f"  RAW (scaled-pooled-null check, σ_0 units):")
            print(f"    scaled pool null: SD_I={sd_I_sc:.4f} SD_Q={sd_Q_sc:.4f}")
            for c in part2:
                w = np.sqrt(c["T_per_s"] / c["n_seeds"])
                sig = c["sig_reps"]
                Is = np.array([s["I_raw_sum"] for s in sig]) * w
                Qs = np.array([s["Q_raw_sum"] for s in sig]) * w
                zI = (Is - mu_I_sc) / sd_I_sc
                zQ = (Qs - mu_Q_sc) / sd_Q_sc
                pooled_zmags.append(np.sqrt(zI**2 + zQ**2))
            means = [float(m.mean()) for m in pooled_zmags]
            sds = [float(m.std(ddof=1)) for m in pooled_zmags]
            ss_b = sum(6 * (m.mean() - np.concatenate(pooled_zmags).mean())**2
                       for m in pooled_zmags)
            ss_w = sum(((m - m.mean())**2).sum() for m in pooled_zmags)
            F_p = (ss_b / 3) / (ss_w / 20)
            p_Fp = 1.0 - _stats.f.cdf(F_p, 3, 20)
            print(f"    per-cell |z|_pool means: {[round(x, 2) for x in means]}")
            print(f"    F(3,20) = {F_p:.2f}, p = {p_Fp:.4f}")
            analysis["flatness"]["RAW_scaled"] = {
                "per_cell_z_scaled_means": means,
                "per_cell_z_scaled_sds": sds,
                "F": float(F_p), "p_F": float(p_Fp),
                "sd_I_sigma0": sd_I_sc, "sd_Q_sigma0": sd_Q_sc,
            }

        # Also do the ST-pooled check: since ST expected flat null, a fairer
        # test uses pooled-null |z|.
        if ch_label == "ST":
            pooled_zmags = []
            sd_I_p = analysis["pooled_null"]["ST"]["sd_I_pool"]
            sd_Q_p = analysis["pooled_null"]["ST"]["sd_Q_pool"]
            mu_I_p = analysis["pooled_null"]["ST"]["mean_I_pool"]
            mu_Q_p = analysis["pooled_null"]["ST"]["mean_Q_pool"]
            for c in part2:
                sig = c["sig_reps"]
                Is = np.array([s["I_st_sum"] for s in sig])
                Qs = np.array([s["Q_st_sum"] for s in sig])
                zI = (Is - mu_I_p) / sd_I_p
                zQ = (Qs - mu_Q_p) / sd_Q_p
                pooled_zmags.append(np.sqrt(zI**2 + zQ**2))
            means = [float(m.mean()) for m in pooled_zmags]
            sds = [float(m.std(ddof=1)) for m in pooled_zmags]
            ss_b = sum(6 * (m.mean() - np.concatenate(pooled_zmags).mean())**2
                       for m in pooled_zmags)
            ss_w = sum(((m - m.mean())**2).sum() for m in pooled_zmags)
            F_p = (ss_b / 3) / (ss_w / 20)
            p_Fp = 1.0 - _stats.f.cdf(F_p, 3, 20)
            print(f"  ST (pooled-null check):")
            print(f"    per-cell |z|_pool means: {[round(x, 2) for x in means]}")
            print(f"    F(3,20) = {F_p:.2f}, p = {p_Fp:.4f}")
            analysis["flatness"]["ST_pooled"] = {
                "per_cell_z_pooled_means": means, "per_cell_z_pooled_sds": sds,
                "F": float(F_p), "p_F": float(p_Fp),
            }

    # ─── Mechanism verdict ────────────────────────────────────────────────
    print("\n=== MECHANISM VERDICT ===\n")
    for label, rows in by_channel.items():
        rows_sorted = sorted(rows, key=lambda r: -r["n_seeds"])  # n=32 first
        z_n32 = next(r["z_mag_sig_mean"] for r in rows_sorted if r["n_seeds"] == 32)
        z_n1 = next(r["z_mag_sig_mean"] for r in rows_sorted if r["n_seeds"] == 1)
        sd_avg = np.mean([r["z_mag_sig_sd"] for r in rows_sorted])
        ratio = z_n32 / z_n1 if z_n1 > 0 else float("nan")
        diff = z_n32 - z_n1
        z_sep = diff / (sd_avg * np.sqrt(2.0 / 6.0))  # 6 reps each
        # Sinc prediction
        sinc_preds = analysis["sinc_predictions"][label]
        sinc_ratio = sinc_preds[32]["mean_sinc"] / sinc_preds[1]["mean_sinc"]
        print(f"  {label}: |z|(n=32)={z_n32:.2f}  |z|(n=1)={z_n1:.2f}  "
              f"ratio={ratio:.2f}  (z-separation={z_sep:.1f}σ)")
        print(f"        sinc-model predicted ratio = {sinc_ratio:.2f}")
        verdict = "flat" if abs(z_sep) < 1.5 else (
            "seeds > long" if z_sep > 0 else "long > seeds")
        print(f"        verdict: {verdict}")
        analysis["mechanism_verdict"][label] = {
            "z_n32": z_n32, "z_n1": z_n1, "ratio_obs": ratio,
            "ratio_sinc_pred": sinc_ratio, "z_separation_sigma": z_sep,
            "verdict": verdict,
        }

    out_path = HERE / "thor_session_99_analysis.json"
    out_path.write_text(json.dumps(analysis, indent=2, default=float))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
