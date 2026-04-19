#!/usr/bin/env python3
"""
Thor Session #99: Mechanism of "seeds-beat-long" — amplitude CV vs detuning vs wander.

BACKGROUND
----------
S94 matched-compute result: at n_seeds·T = 8·4000s total compute, the n=8 T=4000
configuration beat n=1 T=32000 in |z_st| by +0.61 (p=0.047). Small but real.
S98 then measured phase drift directly — |Φ(m)| is FLAT from 4,000s to 240,000s at
σ=0.022, A=0.30. τ_φ >> 240,000s. Per-seed mean angles also cluster extraordinarily
tight across seeds (R_across=0.999, 2° spread). So seeds-beat-long CANNOT be
driven by within-seed phase drift or across-seed phase detuning at coarse level.

That leaves three remaining mechanisms:
    (A) Per-seed SIGNAL amplitude heterogeneity (the |z_st|_seed CV).
        Many-short averages it out (law of large numbers on amplitudes).
        Few-long is stuck with one realization.
    (B) Per-seed subtle FREQUENCY detuning Δω_seed (fit slope of arg(z_k) vs k).
        Detuning × long-T accumulates within-seed phase drift, penalizing few-long.
    (C) Per-seed within-run AMPLITUDE wander on O(10^4-10^5 s) timescale
        (|z_k|² autocorrelation). Amplitude dropouts penalize few-long more than
        many-short.

THIS SESSION
------------
PART 1 (post-process S98 data, 8 seeds × 100 chunks × 4000s):
  1a. Per-seed mean (I, Q) across 100 chunks, per-seed magnitude, amplitude CV.
  1b. Unwrapped arg(z_k) linear fit per seed → Δω_seed. Std across 8 seeds.
  1c. Within-seed autocorrelation of |z_st,k|² at lags 1..60 → amplitude coherence.
  1d. Within-seed autocorrelation of arg(z_st,k) → residual phase-lag autocorr.

PART 2 (new matched-compute sweep):
  Grid: n_seeds ∈ {32, 8, 2, 1}, T_per = 128000s / n_seeds  (constant total compute)
  At each cell: K=6 signal reps (A=0.30) + K=6 null reps (A=0.0), σ=0.022.
  Metric per rep: (I_sum, Q_sum) via coherent sum across seeds of switch-timing IQ.
  z-score signal reps against null-rep SD → |z_combined|.
  Compare mean |z_combined| across n. If amplitude-CV (A) or detuning (B):
      n=32 > n=8 > n=2 > n=1 monotonically.
  If stationary-no-heterogeneity:
      |z_combined| flat across n (all equivalent at matched compute).

FALSIFICATION CRITERIA
----------------------
  S98-P1  : At matched compute, mean |z_combined| same for n=1 and n=32
            (within 1σ of inter-rep scatter). If false → seed heterogeneity is real.
  S98-P2  : Std of per-seed Δω is O(10^-6 rad/s), small enough that Δω·T_per
            matters at T_per=128000s but not at T_per=4000s.

COMPUTE BUDGET (Thor, ~25 µs/step)
----------------------------------
  Part 2: Per rep ≈ 1.3–1.6M steps × 25µs ≈ 35 s.
  4 cells × 12 reps/cell = 48 reps ≈ 28 min.
  Part 1 is post-processing (seconds).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import simulate, phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

HERE = Path(__file__).parent
S98_RESULTS = HERE / "thor_session_98_phase_drift_results.json"

DT = 0.1
F_S = 0.003
WARMUP = 10000
C_THRESH = 0.55


# ─── Part 1: post-process S98 ─────────────────────────────────────────────

def unwrap_angle_sequence(z_complex):
    """Unwrap complex-valued phase series in radians."""
    return np.unwrap(np.angle(z_complex))


def per_seed_stats(per_seed_list, channel_key, T_chunk_s):
    """For each seed, compute magnitude CV, Δω fit, and within-seed autocorrs.

    Each entry in per_seed_list has:
        'seed', 'z_raw': list[[I,Q], ...], 'z_st': list[[I,Q], ...], 'n_sw': [...]
    """
    rows = []
    for ps in per_seed_list:
        z_list = np.array(ps[channel_key])  # shape (n_chunks, 2)
        z_c = z_list[:, 0] + 1j * z_list[:, 1]
        n_chunks = len(z_c)

        # Mean-subtracted for amplitude autocorr (|z|² around its own mean)
        mag2 = (z_list ** 2).sum(axis=1)
        mag = np.sqrt(mag2)
        mean_mag = mag.mean()
        cv_mag = mag.std(ddof=1) / mean_mag if mean_mag > 0 else np.nan

        # Unwrapped angle linear fit → Δω (rad/s)
        phi_unwrapped = np.unwrap(np.angle(z_c))
        t = np.arange(n_chunks) * T_chunk_s
        # robust to angle wander: least-squares slope
        slope, intercept = np.polyfit(t, phi_unwrapped, 1)
        resid = phi_unwrapped - (slope * t + intercept)

        # autocorrs
        def lag_autocorr(x, max_lag=30):
            x0 = x - x.mean()
            denom = (x0 * x0).sum()
            out = []
            for m in range(1, max_lag + 1):
                num = (x0[:-m] * x0[m:]).sum()
                out.append(float(num / denom) if denom > 0 else 0.0)
            return out

        rows.append({
            "seed": ps["seed"],
            "n_chunks": n_chunks,
            "mean_mag": float(mean_mag),
            "cv_mag": float(cv_mag),
            "mean_angle_deg": float(np.degrees(np.angle(z_c.mean()))),
            "delta_omega_rad_per_s": float(slope),
            "intercept_rad": float(intercept),
            "resid_rms_rad": float(np.sqrt((resid ** 2).mean())),
            "acorr_mag2": lag_autocorr(mag2, max_lag=30),
            "acorr_resid_phase": lag_autocorr(resid, max_lag=30),
        })
    return rows


def part1_post_s98():
    print("\n=== PART 1: post-process S98 per-seed data ===\n")
    d = json.loads(S98_RESULTS.read_text())
    per_seed = d["main"]["per_seed"]
    T_chunk_s = d["meta"]["params"]["T_chunk_s"]

    # Raw and ST channels
    out = {"T_chunk_s": T_chunk_s, "channels": {}}
    for ch in ["z_raw", "z_st"]:
        rows = per_seed_stats(per_seed, ch, T_chunk_s)
        # Aggregate across seeds
        delta_omega = np.array([r["delta_omega_rad_per_s"] for r in rows])
        mean_mags = np.array([r["mean_mag"] for r in rows])
        cv_mags = np.array([r["cv_mag"] for r in rows])
        angles = np.radians(np.array([r["mean_angle_deg"] for r in rows]))
        R_across = float(np.abs(np.mean(np.exp(1j * angles))))
        print(f"\n-- channel {ch} --")
        print(f"  per-seed mean |z|: mean={mean_mags.mean():.4f} sd={mean_mags.std(ddof=1):.4f}  "
              f"across-seed CV={mean_mags.std(ddof=1)/mean_mags.mean():.3%}")
        print(f"  per-seed within CV of |z|: mean={cv_mags.mean():.3%}  sd={cv_mags.std(ddof=1):.3%}")
        print(f"  per-seed Δω (rad/s): mean={delta_omega.mean():.3e}  "
              f"std={delta_omega.std(ddof=1):.3e}  "
              f"range=[{delta_omega.min():.3e}, {delta_omega.max():.3e}]")
        print(f"  Δω·T_per at T_per=128000s: "
              f"spread = {delta_omega.std(ddof=1) * 128000:.4f} rad "
              f"(~{np.degrees(delta_omega.std(ddof=1) * 128000):.2f}°)")
        print(f"  R_across seed mean angles: {R_across:.4f}")
        out["channels"][ch] = {
            "per_seed_rows": rows,
            "summary": {
                "across_seed_mag_mean": float(mean_mags.mean()),
                "across_seed_mag_sd": float(mean_mags.std(ddof=1)),
                "across_seed_mag_cv": float(mean_mags.std(ddof=1) / mean_mags.mean()),
                "within_seed_cv_mean": float(cv_mags.mean()),
                "within_seed_cv_sd": float(cv_mags.std(ddof=1)),
                "delta_omega_mean": float(delta_omega.mean()),
                "delta_omega_std": float(delta_omega.std(ddof=1)),
                "delta_omega_min": float(delta_omega.min()),
                "delta_omega_max": float(delta_omega.max()),
                "R_across_seed_angles": R_across,
            },
        }
    return out


# ─── Part 2: matched-compute sweep (n·T = const) ──────────────────────────

def one_rep(n_seeds, T_per_steps, sigma, A, seed_base):
    """Run n_seeds independent trajectories of T_per_steps (incl. warmup),
    compute BOTH raw-signal MF and switch-timing MF (I, Q) per seed starting
    from post-warmup, and return coherent sums per channel and per-seed lists.

    t_offset for each seed's MF = WARMUP. Each seed's simulator is reset
    at t=0, so its post-warmup samples start at global index 'WARMUP'.

    NOTE: raw MF and ST MF differ in normalization — raw_IQ = mean(x·sin),
    ST_IQ = sum(direction·sin). Coherent sums use the native normalization
    of each, and null SD is estimated per-channel.
    """
    I_raw_sum, Q_raw_sum = 0.0, 0.0
    I_st_sum, Q_st_sum = 0.0, 0.0
    n_sw_total = 0
    per = []
    for s in range(n_seeds):
        x = simulate(N=4, noise_std=sigma,
                     steps=WARMUP + T_per_steps,
                     seed=seed_base + s,
                     signal_freq=F_S, signal_amp=A,
                     dt=DT, C_threshold=C_THRESH)
        x_meas = x[WARMUP:]
        I_raw, Q_raw = phase_coherent_IQ(x_meas, DT, F_S, WARMUP)
        I_st, Q_st, n_sw = switch_timing_IQ(x_meas, DT, F_S, WARMUP, threshold=C_THRESH)
        I_raw_sum += I_raw; Q_raw_sum += Q_raw
        I_st_sum += I_st; Q_st_sum += Q_st
        n_sw_total += n_sw
        per.append({"seed": seed_base + s,
                    "I_raw": I_raw, "Q_raw": Q_raw,
                    "I_st": I_st, "Q_st": Q_st, "n_sw": n_sw})
    return {
        "I_raw_sum": I_raw_sum, "Q_raw_sum": Q_raw_sum,
        "I_st_sum": I_st_sum, "Q_st_sum": Q_st_sum,
        "n_sw_total": n_sw_total, "per_seed": per,
    }


def part2_matched_compute(N_total_steps=1_280_000, K_sig=6, K_null=6,
                          sigma=0.022, A=0.30, seed_offset=100_000):
    """Grid n_seeds ∈ {32, 8, 2, 1}, T_per = N_total/n_seeds.

    Returns per-cell lists of signal-rep (I_sum, Q_sum) and null-rep (I_sum, Q_sum).
    """
    print("\n=== PART 2: matched-compute sweep ===\n")
    cells = [32, 8, 2, 1]
    results = []
    global_seed = seed_offset

    for n_seeds in cells:
        T_per_steps = N_total_steps // n_seeds
        T_per_s = T_per_steps * DT
        print(f"\n>> n_seeds={n_seeds}  T_per_steps={T_per_steps}  T_per_s={T_per_s:.0f}")

        # Signal reps
        sig_reps = []
        t0 = datetime.now()
        for k in range(K_sig):
            r = one_rep(n_seeds, T_per_steps, sigma, A, global_seed)
            global_seed += n_seeds
            sig_reps.append(r)
            dt_s = (datetime.now() - t0).total_seconds()
            print(f"  sig rep {k+1}/{K_sig}  "
                  f"raw(I,Q)=({r['I_raw_sum']:.4f},{r['Q_raw_sum']:.4f})  "
                  f"st(I,Q)=({r['I_st_sum']:.2f},{r['Q_st_sum']:.2f})  "
                  f"n_sw={r['n_sw_total']}  elapsed={dt_s:.0f}s")

        # Null reps
        null_reps = []
        t0 = datetime.now()
        for k in range(K_null):
            r = one_rep(n_seeds, T_per_steps, sigma, 0.0, global_seed)
            global_seed += n_seeds
            null_reps.append(r)
            dt_s = (datetime.now() - t0).total_seconds()
            print(f"  null rep {k+1}/{K_null}  "
                  f"raw(I,Q)=({r['I_raw_sum']:.4f},{r['Q_raw_sum']:.4f})  "
                  f"st(I,Q)=({r['I_st_sum']:.2f},{r['Q_st_sum']:.2f})  "
                  f"n_sw={r['n_sw_total']}  elapsed={dt_s:.0f}s")

        def zscore_channel(sig_I, sig_Q, null_I, null_Q):
            sd_I = float(np.std(null_I, ddof=1))
            sd_Q = float(np.std(null_Q, ddof=1))
            mu_I = float(np.mean(null_I))
            mu_Q = float(np.mean(null_Q))
            z_I = (sig_I - mu_I) / sd_I if sd_I > 0 else np.zeros_like(sig_I)
            z_Q = (sig_Q - mu_Q) / sd_Q if sd_Q > 0 else np.zeros_like(sig_Q)
            z_I_self = (null_I - mu_I) / sd_I if sd_I > 0 else np.zeros_like(null_I)
            z_Q_self = (null_Q - mu_Q) / sd_Q if sd_Q > 0 else np.zeros_like(null_Q)
            z_mag_sig = np.sqrt(z_I ** 2 + z_Q ** 2)
            z_mag_null = np.sqrt(z_I_self ** 2 + z_Q_self ** 2)
            return {
                "null_SD_I": sd_I, "null_SD_Q": sd_Q,
                "null_mean_I": mu_I, "null_mean_Q": mu_Q,
                "z_I_sig": z_I.tolist(), "z_Q_sig": z_Q.tolist(),
                "z_mag_sig_list": z_mag_sig.tolist(),
                "z_mag_null_list": z_mag_null.tolist(),
                "z_I_sig_mean": float(z_I.mean()),
                "z_I_sig_sd": float(z_I.std(ddof=1)),
                "z_Q_sig_mean": float(z_Q.mean()),
                "z_Q_sig_sd": float(z_Q.std(ddof=1)),
                "z_mag_sig_mean": float(z_mag_sig.mean()),
                "z_mag_sig_sd": float(z_mag_sig.std(ddof=1)),
                "z_mag_null_mean": float(z_mag_null.mean()),
                "z_mag_null_sd": float(z_mag_null.std(ddof=1)),
            }

        sig_I_raw = np.array([r["I_raw_sum"] for r in sig_reps])
        sig_Q_raw = np.array([r["Q_raw_sum"] for r in sig_reps])
        null_I_raw = np.array([r["I_raw_sum"] for r in null_reps])
        null_Q_raw = np.array([r["Q_raw_sum"] for r in null_reps])
        raw_stats = zscore_channel(sig_I_raw, sig_Q_raw, null_I_raw, null_Q_raw)

        sig_I_st = np.array([r["I_st_sum"] for r in sig_reps])
        sig_Q_st = np.array([r["Q_st_sum"] for r in sig_reps])
        null_I_st = np.array([r["I_st_sum"] for r in null_reps])
        null_Q_st = np.array([r["Q_st_sum"] for r in null_reps])
        st_stats = zscore_channel(sig_I_st, sig_Q_st, null_I_st, null_Q_st)

        print(f"   RAW: null SD I={raw_stats['null_SD_I']:.4f} Q={raw_stats['null_SD_Q']:.4f}  "
              f"|z|_sig={raw_stats['z_mag_sig_mean']:.2f}±{raw_stats['z_mag_sig_sd']:.2f}  "
              f"|z|_null={raw_stats['z_mag_null_mean']:.2f}")
        print(f"   ST : null SD I={st_stats['null_SD_I']:.3f} Q={st_stats['null_SD_Q']:.3f}  "
              f"|z|_sig={st_stats['z_mag_sig_mean']:.2f}±{st_stats['z_mag_sig_sd']:.2f}  "
              f"|z|_null={st_stats['z_mag_null_mean']:.2f}")

        results.append({
            "n_seeds": n_seeds,
            "T_per_steps": T_per_steps,
            "T_per_s": T_per_s,
            "sigma": sigma,
            "A": A,
            "K_sig": K_sig,
            "K_null": K_null,
            "sig_reps": sig_reps,
            "null_reps": null_reps,
            "raw_channel": raw_stats,
            "st_channel": st_stats,
        })

    return results


def main():
    started = datetime.now().isoformat()
    print(f"S99 start: {started}")

    part1 = part1_post_s98()

    part2 = part2_matched_compute(
        N_total_steps=1_280_000,
        K_sig=6, K_null=6,
        sigma=0.022, A=0.30,
        seed_offset=990_000,  # avoid collision with S98 seed_base=98000..
    )

    out = {
        "meta": {
            "session": 99,
            "title": "Mechanism of seeds-beat-long — amplitude CV vs detuning vs wander",
            "started": started,
            "ended": datetime.now().isoformat(),
        },
        "part1_s98_postprocess": part1,
        "part2_matched_compute": part2,
    }
    out_path = HERE / "thor_session_99_seed_heterogeneity_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
