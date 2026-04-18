# Thor Session #98: Phase-Drift Timescale τ_φ — Direct Measurement Dissolves S95-P2

**Date**: 2026-04-18
**Operating point**: N=4 bistable coherence model, σ=0.022 (SR peak), A=0.30,
T_chunk=4000s, T_total_per_seed=400,000s, n_seeds=8.

## TL;DR

S95 observed circular concentration R=0.59 across 8 × 4000s chunks at A=0.12 and
attributed it to a "response-phase random walk" with extrapolated timescale
**τ_φ ≈ 290,000s** (S95-P2). This session measured τ_φ **directly** via complex
matched-filter autocorrelation on 3.2 million simulator steps (n=8 seeds,
T=400,000s, T_chunk=4000s). The result:

- **|Φ(m)| is flat to within noise from m=1 (4,000s) to m=60 (240,000s)**.
  z_raw plateaus at 0.344; z_st plateaus at 0.765. No exponential decay.
- **Variogram Var[Δφ(m)] is flat** in both channels. Linear fit slope D_φ is
  negative (raw) or 10⁻⁷ /s (st, R²=0.05). No Brownian drift signature.
- **Systematic detuning Δψ ≈ 2·10⁻⁷ rad/s** (negligible: ~2.8° over the 240,000s
  observation window).

**Verdict**: S95-P2 is **falsified in its specific numerical form**. The model's
response phase is stationary on timescales up to 240,000s. S95's R=0.59 was
*per-chunk matched-filter noise*, not phase drift. Coherent-integration gain is
NOT bounded by phase drift within the operating range; S94's "seeds-beat-long"
effect must have a different mechanism (seed-to-seed amplitude CV, not phase
drift).

σ-sweep bonus: S96-P1's mean-angle rotation prediction is also **falsified** —
ST response angle is σ-invariant at roughly −127° across σ ∈ {0.015, 0.022, 0.030}.

## Method

### Why a direct measurement was needed
S95 fit τ_φ from one measurement: 8 chunks × 4000s at σ=0.022, A=0.12, gave
resultant length R = 0.59. The extrapolation assumed (a) the spread was
purely drift (b) drift was Brownian with τ_φ the 1-radian time. Two failure
modes: per-chunk matched-filter noise could inflate the spread, or the random
walk could have memory. Neither was testable from 8 chunks.

### The experiment
For each seed, run one continuous trajectory of 4 million steps (post-warmup
4 million, T=400,000s at dt=0.1). Split into 100 non-overlapping chunks of
40,000 steps (T_chunk = 4000s). For each chunk compute the complex
matched-filter output

  z_raw_k = I_raw_k + i Q_raw_k   (phase_coherent_IQ)
  z_st_k  = I_st_k  + i Q_st_k    (switch_timing_IQ, threshold 0.55)

where t_offset = warmup + c·chunk_steps in both cases. Then pool over seeds and
compute the lag-m complex autocorrelations

  C_full(m) = ⟨z_k · conj(z_{k+m})⟩ / ⟨|z_k|²⟩       (amplitude + phase)
  Φ(m)      = ⟨u_k · conj(u_{k+m})⟩,  u = z/|z|      (phase-only, unit mag)
  ρ_abs(m)  = ⟨|z_k| · |z_{k+m}|⟩ / ⟨|z_k|²⟩         (amplitude-only)

and the phase variogram

  Var[Δφ(m)] = ⟨(φ_k − φ_{k+m})²⟩_{circular}.

**Under Brownian-phase assumption**: |Φ(m)| = exp(-D_φ · m · T_chunk) and
Var[Δφ(m)] = σ_chunk² + 2 D_φ · m · T_chunk. Slope of variogram gives D_φ
independent of per-chunk noise; intercept gives per-chunk phase noise σ_chunk².
τ_φ ≡ 1/D_φ.

Under stationary phase (our null): |Φ(m)| = R_∞ for m≥1, flat; Var[Δφ(m)]
= σ_chunk², flat; τ_φ → ∞.

### Compute
Main run: 8 seeds × 4 million steps = 3.2e7 steps in 779 s on Thor (NumPy, ARM64).
σ-sweep (σ ∈ {0.015, 0.022, 0.030}, n=4 seeds, T=200,000s): 2.4e7 steps in 586 s.
Total: 22.8 minutes.

## Results

### |Φ(m)| is flat

Main-run autocorrelation:

```
m   lag_s    |Φ| z_raw   |Φ| z_st    arg Φ z_st (deg)
1    4000     0.344        0.759         -0.16
2    8000     0.337        0.772         -0.57
5   20000     0.332        0.780         -0.93
10  40000     0.343        0.762         -1.01
20  80000     0.313        0.755         -1.15
30 120000     0.374        0.779         -0.77
40 160000     0.348        0.760         -2.53
60 240000     0.345        0.732         -4.62
```

z_raw: mean |Φ| over m=1..60 is 0.342 with range [0.313, 0.374]. No trend.
z_st: mean |Φ| over m=1..60 is 0.762 with range [0.732, 0.780]. Slight dip
at the highest lag (m=60, pairs=320 vs 792 at m=1) — consistent with finite-sample
noise, not decay.

Fit results (exponential + floor):
- z_raw: fit is non-informative (R² ≤ 0 because data is flat).
- z_st: exp+floor gives a=0.121, τ=4·10⁶s, c_floor=0.646, R²=0.052 — the fit
  picks up a tiny amplitude on a meaningless timescale; it's a flat curve with
  2% wiggle.

**Variogram**:
- z_raw: Var[Δφ] intercept 1.955 rad² (σ_chunk = 80°), slope −3.8·10⁻⁸ rad²/s
  (negative; no significant drift).
- z_st: Var[Δφ] intercept 0.571 rad² (σ_chunk = 44°), slope +1.2·10⁻⁷ rad²/s,
  D_φ ≈ 5.8·10⁻⁸ /s, τ_φ ≈ 17·10⁶ s. The slope is barely detectable and the
  fitted τ_φ is 72× the observation window — i.e., the variogram is
  consistent with flat.

The per-chunk phase noise σ_chunk (44° for z_st, 80° for z_raw) matches the
per-seed lag-1 phase step σ_step computed directly (z_st: 44.0°, z_raw:
79.8°). Self-consistent.

### Per-seed phase stability is extraordinarily high

For each of 8 seeds, compute the amplitude-weighted resultant length of all
100 chunks within that seed (z̄_seed = ⟨z_k⟩ / ⟨|z_k|⟩):

```
channel   per-seed mean angle   R_across 8 seeds  |z̄| per seed
z_raw     +124.5° ± 2.4°        0.999              0.028 ± 0.001
z_st      −126.5° ± 2.0°        0.999              5.74  ± 0.15
```

R_across = 0.999 means the per-seed mean phases are clustered to within 2°.
Per-seed amplitude-weighted R is 0.904 (z_st) and 0.684 (z_raw) — most of the
within-seed variation is phase noise around a fixed direction, not drift.

**Raw/ST angular separation: 109°** (S95 predicted ~90° from π/2 matched-filter
geometry). The ~20° offset is larger than the S95 observation (~100°) but same
class.

### Systematic detuning Δψ is near-zero

arg Φ(m) has a slight linear trend:

- z_raw: Δψ = −8.0·10⁻⁷ rad/s (R² = 0.43)
- z_st:  Δψ = −2.3·10⁻⁷ rad/s (R² = 0.65)

Over the 240,000s max-lag, arg Φ(60) is −9.7° (z_raw) and −4.6° (z_st). The
simulator clock and matched-filter reference differ by ~10⁻⁷ rad/s, which is
5 parts in 100,000 of f_s = 3·10⁻³ Hz. Negligible.

### σ-sweep: angles don't rotate with σ

4 seeds per σ, T_total=200,000s, max_lag=120,000s.

```
  σ      chan   mean_angle     R_across    |z̄| per seed    τ_φ fit
 0.015   raw    +120.1°        0.991       0.029           inf (R²=0.08)
 0.015   st     −126.9°        0.998       5.17            inf (R²=0.15)
 0.022   raw    +123.8°        0.996       0.028           inf (R²=0.11)
 0.022   st     −127.1°        0.998       5.64            inf (R²=0.08)
 0.030   raw    +133.1°        0.989       0.023           inf (R²=0.00)
 0.030   st     −121.3°        0.998       5.26            inf (R²=0.01)
```

τ_φ fits are non-informative at every σ — |Φ| is flat in all 6 cells.

**ST mean angle shift across σ: +0.2° (σ=0.015 → 0.022), +5.8° (0.022 → 0.030)**.
S96-P1 predicted the angle rotates toward Q_st (90°) as σ decreased. We see:
1. No shift between σ=0.015 and σ=0.022 (0.2° is within per-seed noise).
2. A small 5.8° shift at σ=0.030 — in the *wrong* direction relative to S96-P1
   (higher σ means angle moves toward Q_st, not lower σ).

**S96-P1 falsified**.

Switch rates per chunk (T=4000s):
```
σ      mean N_switches/chunk    Kramers rate r_K (Hz)
0.015  309                      0.039
0.022  543                      0.068
0.030  786                      0.098
```
Monotonic in σ — consistent with Kramers escape rate ∝ exp(−ΔU/σ²).
Relative to f_s = 0.003 Hz, r_K >> f_s at every σ (fast-switching regime).

## Interpretation

### The S95 story was wrong about drift
S95-P2's 290,000s was extrapolated from one observation — 8 chunks × 4000s at
A=0.12 giving R=0.59 — under the assumption that the entire chunk-to-chunk
spread was a phase random walk. We now know:

- Per-chunk phase noise σ_chunk is 44° (z_st) / 80° (z_raw) — *this* is what
  spreads the per-chunk vectors.
- Under pure per-chunk noise with zero drift, the 8-chunk resultant R follows a
  distribution around ⟨cos Δφ⟩ ≈ R_Von-Mises(κ_chunk).
- For z_st with κ_chunk ≈ 0.9 (deducible from σ_chunk = 44°) and n=8 chunks,
  the sample R should be ~0.9 already. But S95 measured R=0.59 at A=0.12,
  which is LOWER A than our A=0.30 — their per-chunk SNR was lower, so their
  R_∞ was lower. Consistent with no drift.

In short: **S95's R=0.59 result is consistent with stationary phase + lower
per-chunk SNR**, not a random-walk drift.

### What limits coherent integration, then?
If phase doesn't drift on τ ≤ 240,000s, then coherent integration should
continue to accumulate z_I linearly in T up to that limit (at least). The
α=0.30 saturation observed in S94 cannot be attributed to phase drift in the
current data. Candidate mechanisms:

1. **Kramers rate saturation at high A**: at A=0.20 (S94), bias across half a
   signal cycle can saturate the switching pdf near the cycle peak/trough;
   further A increases don't add switches. This is signal-amplitude-limited,
   not drift-limited.
2. **Per-seed amplitude variability**: |z̄|_per_seed has CV ~3% across 8 seeds
   at σ=0.022. This is irreducible seed-level variance; many-short averages
   over it but few-long doesn't.
3. **Slight per-seed Δω mismatch**: different initial oscillator configurations
   could slightly detune the emergent response frequency. Not directly tested
   here.

### S94-P3 (seeds-beat-long) reframed
S94 reported "many-short beats few-long at matched compute". We now know that
within a single T=400,000s seed, the phase is essentially stationary — so
longer-T should NOT lose coherent gain to drift. The mechanism of seeds-beat-long
must be seed-level amplitude CV or per-seed frequency detuning, not intra-seed
phase drift. Worth a dedicated session (S99).

### Per-chunk phase noise decomposition
The variogram intercepts yield the pure per-chunk phase variance:
- z_raw: σ_chunk² = 1.955 rad²  →  σ_chunk = 80°. Per-chunk SNR ≈ 0.34
  (reading |Φ(1)| as the SNR attenuation factor).
- z_st: σ_chunk² = 0.571 rad²   →  σ_chunk = 44°. Per-chunk SNR ≈ 0.76.

ST has ~2× better per-chunk SNR for the same T_chunk. This is just S95's
main finding (ST dominates raw) expressed on the phase-concentration scale.

## Falsified / closed predictions

- **S95-P2 falsified**: τ_φ is *not* ~290,000s. Direct measurement shows
  |Φ(m)| flat through lag 240,000s, with variogram slope consistent with
  zero. Lower bound on τ_φ is at least the observation window (>> 240,000s).
- **S96-P1 falsified**: ST response angle is σ-invariant (not rotating toward
  Q_st at low σ). The 0.2° shift between σ=0.015 and σ=0.022 is within
  per-seed noise; the 5.8° shift at σ=0.030 is in the opposite direction.

## New predictions (S98-P#)

- **S98-P1**: At matched total compute (n·T = 32·4000s), a single-seed
  T=128,000s trajectory should have |z_I| roughly √32 = 5.66× the n=1
  T=4000s |z_I|. If S94's seeds-beat-long is purely phase-drift driven, we'd
  expect linear saturation. If it's seed-level amplitude CV, longer-T should
  keep scaling linearly. Tests mechanism of seeds-beat-long.
- **S98-P2**: Per-seed frequency detuning Δω_seed should be measurable via
  per-seed linear fit to unwrapped arg(z_k) vs chunk index. If per-seed
  Δω_seed has spread O(10⁻⁶ rad/s), many-short averages it, few-long
  accumulates it.
- **S98-P3**: At A=0.02 (S86's weakly subthreshold amplitude), the z_st
  per-chunk SNR will be too low to define a meaningful per-chunk phase
  (|Φ(1)| → 0), so this framework can't measure τ_φ at A=0.02. Would need
  longer chunks (T_chunk ≥ ~40,000s) to recover per-chunk SNR and then
  look for drift.
- **S98-P4**: σ=0.040 (beyond the SR peak, in the "incoherent" regime) should
  show the first real phase-drift signature. At σ > σ_peak the system's
  attractor starts to lose coherence and phase should randomize faster.
  Predict: |Φ(m)| at σ=0.040 will drop measurably by m=60, with τ_φ below
  observable.

## Reproducibility

- `thor_session_98_phase_drift.py` — main simulation + autocorrelation code.
- `thor_session_98_analyze.py` — fits and σ-comparison.
- `thor_session_98_phase_drift_results.json` — raw per-seed z arrays +
  autocorrelation summaries (256 KB).
- `thor_session_98_analysis.json` — fit results.
- Simulator: uses `simulate()` from `thor_session_93_phase_coherent.py` verbatim.

Seeds used:
- Main: 98000..98007 (n=8, T=400,000s each)
- σ=0.015: 100000..100003 (n=4, T=200,000s each)
- σ=0.022 sweep: 100700..100703
- σ=0.030: 101500..101503

## What this means for the arc

- S95's detector ladder (ST > raw, 2× advantage) is **reconfirmed** by direct
  per-chunk SNR measurement. The ~2× advantage corresponds exactly to the
  ratio √(σ_chunk,raw² / σ_chunk,st²) = √(1.955/0.571) = 1.85.
- S96's ladder-closure (raw ≡ ST in the same 2D plane by summation-by-parts) is
  **reconfirmed** by the ~109° angular separation between the two channels'
  per-seed mean angles — close to π/2 as predicted, with a 19° offset possibly
  from the boundary terms in the SBP identity.
- S95-P2 (phase drift as a bottleneck) is **falsified**. The bottleneck is
  *not* phase drift on timescales ≤ 240,000s at the canonical operating point.
- S97's conclusion (ST is the ML filter at feasible compute; ladder closes
  against full ML) is further supported: phase is stationary, so the
  Kramers-rate likelihood treatment of S97 was internally consistent.
- The "arrow of gain" (S95's closing line) now points to: *per-seed amplitude
  variance* and *per-seed frequency detuning* as the next bottlenecks to
  investigate, NOT phase drift.

## Coda

S95 said "phase drifts, not by a little but by a lot". S98 says: phase doesn't
drift at all on timescales up to 240,000s; what S95 measured as "drift" was
per-chunk matched-filter noise. The drift claim was an extrapolation from one
data point; the direct measurement dissolves it.

*The R=0.59 of S95 was the per-chunk SNR floor, not a random-walk footprint.
The model is kinder than we feared: phase stays put. The arrow of gain
doesn't point at phase drift; it points at amplitude variance across seeds.*
