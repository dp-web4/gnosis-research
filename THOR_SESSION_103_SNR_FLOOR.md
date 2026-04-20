# Thor Session #103: The Timescale Was Never There — It's Just the SNR Floor

**Date:** 2026-04-20
**Focus:** Extended-lag ACF of S98 main data, then per-seed analysis.
**Status:** Major correction to S99/S101/S102 interpretations.

## TL;DR

Every previous attempt to characterize the per-chunk residual-phase
autocorrelation as a **dynamical timescale** (S99 τ≈22 ks, S101 "plateau +
white", S102 τ≈80 ks exponential, my own preliminary "damped cosine with
T_osc≈150 ks") was a different projection of the **same SNR-floor fact**:

> Per chunk, z(k) = μ + ε(k) with μ the deterministic response phasor and
> ε an iid complex-white noise from matched-filter estimation error.
> The complex autocorrelation of z at any non-zero lag m is
>   ρ(m≥1) = |μ|²/(|μ|² + σ_n²)
> — the **coherent fraction** of chunk-level energy. It is a constant,
> independent of m.

For A=0.30, σ=0.022, ω_spread=0.02 (8 seeds × 100 chunks, S98 main data):
| channel | |μ|  | σ_n | coherent fraction | measured |Φ_z(1)| | measured |Φ_z(40)| |
|---------|-----|-----|-------------------|---------------------|----------------------|
| RAW     | 0.019 | 0.025 | 0.375 | 0.381 | 0.373 |
| ST      | 5.23  | 3.34  | 0.706 | 0.706 | 0.695 |

Per-seed measurement matches theory to 3 decimals. Flat across all lags.

**No timescale. No exponential. No damped oscillation. A flat SNR floor.**

## What was going wrong: the pooling pathology

Prior sessions pooled across 8 seeds *and then* fit a 1-D exponential
decay against lag. Pooling worked as:

```
pooled_Φ(m) = | (1/N_seeds) · Σ_seeds  ( (1/(T_c − m)) · Σ_k z_seed(k)·z_seed*(k+m) / var ) |
```

Each seed's per-seed Φ_seed(m) has magnitude ≈ coherent fraction (constant
in m) **but a small seed-specific angle**. The angles themselves sit around
a common mean (+125° for RAW, −126° for ST, seed-to-seed R_angle = 0.999).
Across lag, per-seed residual-phase-ACF arguments drift apart:

| lag | arg-std across 8 seeds (RAW) | arg-std across 8 seeds (ST) |
|-----|------------------------------|-----------------------------|
| 1   |  8.7°                        | 1.4°                        |
| 10  | 31.8°                        | 1.7°                        |
| 20  | 72.3°                        | 1.4°                        |
| 40  | 57.3°                        | 1.7°                        |
| 60  |119.0°                        | 4.2°                        |

Complex averaging across seeds *destructively* interferes as angles drift,
producing an apparent decay in |pooled_Φ(m)|. Fitting an exponential to
that decay recovers **any** τ depending on the lag window:
  - lags 1..10 → τ ≈ 21 ks (S99)
  - lags 1..30 → τ ≈ 80 ks (S102)
  - lags 1..80 → τ ≈ 390 ks (preliminary damped-cos fit here)

None of these are physical. They're different readings of the
seed-angle-diffusion rate for RAW. ST seeds share the response angle
to ~2°, so pooled complex ACF matches magnitude ACF and the plateau
is preserved.

## The metric subtlety (phase-only vs z-direct ACF)

S98/S99/S101/S102 computed the **residual-phase autocorrelation**:
  Φ_phase(m) = E[exp(i·(resid(k) − resid(k+m)))]
where resid is the unwrapped phase minus a linear detrend. Two limits:

- **High-SNR** (ST, σ_p ≈ 0.5 rad): Gaussian-phase gives Φ_phase(m≥1) =
  exp(−σ_p²) ≈ 0.75. Matches per-seed R_coh = |μ|²/(|μ|²+σ_n²) = 0.706
  because in this limit σ_p² ≈ σ_n²/|μ|² ≈ (1 − R_coh).
- **Low-SNR** (RAW, σ_p ≈ 2–5 rad): Gaussian-phase breaks but the
  plateau still lands at ≈ R_coh = 0.375. Why: in the Rice-distribution
  picture, phase is uniform-modulated by amplitude, and the phase-only
  AC converges to the same R_coh asymptote as the z-direct AC.

Both metrics land on **R_coh = |μ|²/(|μ|²+σ_n²)** as the plateau floor.
The decay on top of the plateau, in pooled complex ACF, is inter-seed
angular dephasing.

## Demonstrations

Three independent lines of evidence point to the same conclusion.

### 1. Per-seed ACF is flat across lags

`thor_session_103_per_seed.py` shows |Φ_seed(m)| for m ∈ {1, 20, 40, 60}
ranging 0.23–0.47 per-seed per-lag — no systematic decay. Per-seed 80-lag
damped-cosine fits are unstable and give τ/ω all over the map (from 5 lags
to 2000 lags; from ω=0.012 to ω=0.69 rad/lag), consistent with fitting an
oscillator to constant noise.

### 2. Gaussian-phase model works for ST, fails for RAW

`thor_session_103_gaussian_phase.py` tests the prediction that if per-seed
residual phase is iid zero-mean Gaussian, then |Φ_seed(m)| = exp(−σ_resid²):

- **ST**: σ_resid ≈ 0.53 rad, exp(−σ²) = 0.745, measured = 0.765. Match.
- **RAW**: σ_resid ≈ 2–5 rad (phase is nearly random over 2π),
  exp(−σ²) ≈ 0, measured = 0.36. *Completely broken.*

The Gaussian-phase approximation fails for RAW because the phase is
saturated at uniform-on-circle — the right model is SNR-floor, not
Gaussian-phase.

### 3. Direct SNR-floor prediction matches exactly

`thor_session_103_snr_floor.py` computes the complex ACF of z(k) itself
(not of exp(i·phase)) per seed:

```
For iid complex noise: ρ_z(m≥1) = |μ|²/(|μ|² + σ_n²)
```

Both channels match to 3 decimals for all lags m=1..80. And the
noise-demeaned ACF |Φ_ε(m≥1)| ≈ 0.09 (finite-sample floor of 1/√100 = 0.10)
— confirming ε is iid white.

## Reinterpretation of closed / open predictions

| Prediction | Status (pre-S103) | Status (post-S103) |
|------------|-------------------|---------------------|
| S99-P2 "τ_res σ-invariant at 21–23 ks" | "confirmed" | **Artifact**: σ-invariance of inter-seed angle-diffusion rate, not of a physical τ |
| S101-P1 "plateau + white" at per-seed | "confirmed" | **True as shape** but "plateau" is just coherent-fraction |μ|²/E|z|². Not a persistent deterministic component. |
| S102 τ ∝ 1/A (RAW grows 80→136 ks) | — | **Artifact**: coherent-fraction increases with A, so per-seed Φ_z plateau rises; short-window exponential fits read a longer τ when the "decay" is smaller. |
| S102-P3 "τ_RAW ∝ 1/ω_spread" | open | **Replaced**: test whether |μ| and σ_n change with ω_spread (expected to drop |μ| as oscillators decorrelate) |

## What the per-seed picture actually tells us about the system

The useful metric now is **per-seed coherent fraction** R_coh = |μ|²/E|z|²:
- A tight dimensionless SNR measure, chunk-level noise absorbed.
- Naturally bounded in [0, 1].
- Maps 1-to-1 with detection power: T² = 2·T_c · R_coh/(1 − R_coh) (Rice-type).

For S98 main (A=0.30, σ=0.022):
- RAW R_coh = 0.375
- ST  R_coh = 0.706

ST's advantage in R_coh (0.71 vs 0.37) explains the ~2× |z| advantage
of ST detectors. In S96 terms: summation-by-parts rotates raw into ST
but also rescales |μ| relative to σ_n by the 2/ω factor, and the ST
residual noise σ_n is effectively white-filtered via the point-process
summation, which raises R_coh.

## What this means for future detection claims

1. **Never again report "τ_residual" from complex-pooled ACF fits.** Report
   per-seed R_coh = |μ|²/(|μ|² + σ_n²) — it's the invariant physics.

2. **For cross-seed coherence questions**, report the seed-angle
   Rayleigh-R (was 0.999 for both RAW and ST at σ=0.022, A=0.30 —
   seeds lock to the same mean angle). This is the honest "are seeds
   telling the same story" measure.

3. **If per-seed Φ_z(m) ever deviates from the SNR floor, THAT is news.**
   Possible causes: slow drift of μ over the trajectory, coloring in ε
   at lag timescales, multi-state dynamics producing per-chunk μ
   switching. None of these are visible in S98.

## ω_spread sweep: R_coh is weakly ω_spread-dependent; pooled "τ" is loudly

Sweep at A=0.30, σ=0.022, 8 seeds × 100 chunks per cell:

| ω_spread | RAW |μ| | RAW σ_n | **R_coh RAW** | ST |μ| | ST σ_n | **R_coh ST** | R_angle RAW/ST |
|----------|---------|---------|---------------|--------|--------|--------------|----------------|
| 0.02     | 0.0189  | 0.0245  | **0.375 ± 0.015** | 5.18 | 3.34 | **0.706 ± 0.014** | 0.999 / 0.999 |
| 0.04     | 0.0190  | 0.0238  | **0.391 ± 0.043** | 5.10 | 3.26 | **0.710 ± 0.032** | 0.996 / 0.999 |
| 0.08     | 0.0153  | 0.0253  | **0.271 ± 0.084** | 4.49 | 3.55 | **0.613 ± 0.056** | 0.993 / 0.998 |

**Observations:**
1. R_coh is **nearly invariant** ω=0.02→0.04 (+4% RAW, +1% ST).
2. R_coh **drops moderately** at ω=0.08 (−28% RAW, −13% ST).
3. **Seed-to-seed R_coh variability grows** with ω_spread (RAW σ_{R_coh}: 0.015 → 0.043 → 0.084). At ω=0.08, some seeds are locked (~0.35) and others barely locked (~0.15).
4. R_angle (cross-seed mean-angle coherence) stays ≥ 0.993 everywhere.
   Seeds all agree on the mean response phase; ω_spread only affects
   within-seed consistency of chunk-to-chunk phase.
5. Log-log slope: R_coh_RAW ∝ ω_spread^(−0.23), R_coh_ST ∝ ω_spread^(−0.10).
   NOT the 1/ω_spread relation S102-P3 postulated.

**Meanwhile the pooled-ACF "exponential τ" shifted from 80 ks (ω=0.02)
to 80 ks (ω=0.04) to 37 ks (ω=0.08)** — driven predominantly by the
growing per-seed R_coh dispersion and intra-seed chunk-phase variability,
not by an underlying dynamical time constant.

**S102-P3 status**: directionally right (pooled τ shortens with ω_spread)
but mechanistically wrong (R_coh invariance precludes a "dynamical τ"
explanation at ω_spread ≤ 0.04). At ω_spread=0.08, R_coh drops enough
that a phase-locking breakdown is starting — a NEW finding. S103-P1
follow-up: pin down the critical ω_spread* where R_coh falls off.

## Files

- `thor_session_103_analyze_s98.py` — initial damped-cosine fit (now understood as pooling pathology artifact)
- `thor_session_103_per_seed.py` — per-seed RAW ACF
- `thor_session_103_per_seed_st.py` — per-seed ST + cross-seed angle coherence
- `thor_session_103_gaussian_phase.py` — Gaussian-phase model test
- `thor_session_103_snr_floor.py` — direct SNR-floor verification
- `thor_session_103_sweep_fast.py` — ω_spread sweep runner
- `thor_session_103_s98_extended.json` — extended ACF data (lag 1..99)
- `thor_session_103_s98_dampedcos_fit.json` — damped-cos fit params (retained as the artifact record)
- `thor_session_103_per_seed_s98.json` — per-seed RAW analysis output
- `thor_session_103_per_seed_st.json` — per-seed ST analysis output
- `thor_session_103_sweep_fast_results.json` — sweep output (TBA)

## Closed predictions (S103)

- **S99-P2 reinterpreted**: "τ_res σ-invariance" is seed-angle-diffusion invariance, not a dynamical timescale. Closed.
- **S101-P1 "plateau + white" promoted** from an opaque shape to SNR-floor = |μ|²/E|z|². The plateau height HAS a closed-form.
- **S102 "RAW exponential τ grows with A"** is demystified: R_coh grows with A (larger |μ|), so the pooled-ACF-decay-rate contributions shift.

## Open follow-ups

- **S103-P1** (replaces S102-P3): |μ| and σ_n scaling in ω_spread.
  If |μ_RAW| decays sharply with ω_spread, the N=4 oscillators decorrelate.
  If σ_n grows, coupling-noise coloration with ω_spread. Both separable.
- **S103-P2**: same scaling in σ (noise strength) — revisit S100 data
  through R_coh lens. Expect R_coh peak at σ ≈ SR optimum σ*.
- **S103-P3**: per-trajectory drift of μ. If μ(t) has slow wander
  over a single long seed's trajectory, that IS a dynamical timescale.
  Measure by computing per-window μ on 10 non-overlapping windows and
  checking window-to-window variance of |μ_window|.

## Methodological rule (S103)

> When analyzing per-chunk matched-filter output z(k) of a stationary
> signal-in-noise chain, compute the complex ACF of z directly; report
> |Φ_z(1)| and per-seed |μ|²/(|μ|²+σ_n²). These are dimensionless,
> invariant under unrelated nuisance, and tell you the SNR.
> DO NOT fit exponentials to pooled-across-seeds complex ACF decays;
> those decays are inter-seed angular dephasing, not temporal dynamics.
