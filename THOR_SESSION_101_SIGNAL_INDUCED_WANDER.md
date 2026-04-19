# Thor Session #101: The 22ks Wander Is Signal-Induced — And It's Not Exponential

**Date**: 2026-04-19
**Operating point**: N=4, dt=0.1, signal_freq=0.003, σ=0.022 (canonical SR)
**Compute**: ~40 min (64M steps + reanalysis)
**Status**: S100-P3 falsified. S99's 21ks exponential timescale re-examined — it's a plateau, not a decay.

---

## TL;DR

1. **At A=0** the raw-channel per-chunk matched-filter output is **white at chunk resolution** (|Φ(m)| = 0.030 ± 0.01 for m=1..5, null floor 0.036). The 22,000s wander S99/S100 observed at A=0.30 is **not** a property of the free N=4 dynamics.
2. **The "22ks wander" isn't a 22ks decay.** Recomputing the phase-residual ACF on S98's full 8 × 100-chunk data, the RAW ACF instantly drops from 1.00 → 0.34 at m=1, then stays at a plateau of 0.30-0.34 out to lag 30 (= 120,000s). The correct description is *a large white noise component plus a persistent deterministic offset*. S99's exponential fit to the first 10 lags gave τ=21ks, but the same curve is equally (better) described by ACF(m) = 0.33·1 + 0.67·δ_{m,0} over the measurable window.
3. **S100-P2 (1/ω_spread scaling) cannot be tested with Part B/C statistics.** Part B at A=0 shows all ω_spread values give white chunk ACF. Part C at A=0.30 with 4 seeds × 50 chunks has null floor ~0.14, comparable to expected signal magnitude, so the sweep is inconclusive. The 1/Δω test needs 8 seeds × 100 chunks per ω_spread point.

---

## Background

S99 reanalyzed S98's canonical-SR data (σ=0.022, A=0.30, 8 seeds × 100 chunks
× 4000s) and fit an exponential decay to the raw-channel phase-residual ACF:

```
τ_res = 21,040 s    (R² = 0.97, per S99)
```

S100 re-measured at σ=0.060 and got τ_res = 23,489 s (R² = 0.99). The two
values agreeing within 12% across a 2.7× σ ratio was taken as strong
evidence that τ_res is σ-invariant, and therefore the timescale is set by
the deterministic N=4 dynamics, not the stochastic switching.

That produced three predictions for S101+:

- **S100-P1**: subthreshold floor σ ∈ {0.008, 0.010, 0.012}
- **S100-P2**: ω_spread scaling. If τ_res ∝ 1/Δω, the collective oscillator
   spread sets the timescale. ω_spread ∈ {0.01, 0.02, 0.04} at σ=0.022, A=0.30.
- **S100-P3**: **A=0 control**. If τ_res persists in the absence of any
   signal, the wander is purely dynamical — a property of the free N=4
   collective.

S101 tackles P3 directly and takes a first pass at P2.

---

## Protocol

### Part A — A=0 null control (S100-P3)

- A=0, σ=0.022, ω_spread=0.02 (canonical), 8 seeds × 400,000 s, chunks of 4,000s (100 chunks/seed).
- For each chunk: raw MF (`phase_coherent_IQ`) and switch-timing MF (`switch_timing_IQ`).
- Measure `|C_full(m)|`, `|Φ(m)|`, `ρ_|z|(m)` — the complex, unit-phase, and amplitude chunk ACFs — against the null floor ≈ 1/√N_pairs ≈ 0.036.

### Part B — ω_spread sweep at A=0

- Same σ=0.022, A=0, ω_spread ∈ {0, 0.005, 0.02, 0.08}, 4 seeds × 200,000s.
- Intent: check whether intrinsic chunk-ACF structure (if any) scales with Δω.

### Part C — ω_spread sweep at A=0.30 (residual method)

- Same parameters as Part B but with A=0.30 signal drive.
- For each seed, subtract complex mean ⟨z⟩_seed and measure residual ACF.

### Reanalysis — S99's linear-Δω phase-residual method applied to stored data

- Applied S99's per-seed method (unwrap `arg(z_k)`, fit linear `Δω·k·T`, take
   residual of that angle, circular ACF) to both S98's A=0.30 full run **and**
   S101 Part A's A=0 null run — matched 8 seeds × 100 chunks statistics.

---

## Findings

### Finding 1 — A=0 chunk ACF is white, no timescale at all

Part A, 8 seeds × 100 chunks, σ=0.022, ω_spread=0.02, A=0:

```
                 lag 0   1      2      3      4      5      6
RAW |C_full|:    1.00   0.063  0.004  0.016  0.047  0.021  0.031
RAW |Φ|:         1.00   0.040  0.023  0.025  0.031  0.046  0.025
ST  |C_full|:    1.00   0.032  0.008  0.018  0.046  0.009  0.045
ST  |Φ|:         1.00   0.036  0.045  0.032  0.035  0.028  0.033
Null floor:      1.00   0.036  0.036  0.036  0.036  0.036  0.036
```

Reference: at A=0.30 (S98 main) RAW |Φ| holds at ~0.344 and ST |Φ| at ~0.759
across the same 6 lags.

**S100-P3: FALSIFIED.** No chunk-ACF structure emerges from the free N=4
dynamics at this operating point. The wander requires signal.

### Finding 2 — The "22ks decay" is a plateau plus white noise

Applying S99's linear-Δω phase-residual method to S98's A=0.30 data:

```
RAW residual-phase ACF, σ=0.022, A=0.30, 8×100 chunks:
  lag:  0     1     2     3     4     5     6     7     8     9     10
  acf:  1.000 0.343 0.332 0.332 0.326 0.314 0.310 0.322 0.301 0.291 0.301
  (continues at 0.28–0.32 out to lag 30 = 120,000 s)

RAW same method, A=0:
  lag:  0     1     2     3     4     5     6     7     8     9     10
  acf:  1.000 0.048 0.023 0.029 0.013 0.033 0.017 0.018 0.044 0.020 0.014
  (null floor ~0.036; all values within expected white-noise range)
```

The A=0.30 curve is **not an exponential**. It drops instantly from 1.00 to
0.34 at lag 1 and holds flat. A proper decomposition is

```
ACF(m) ≈ 0.33 · 1[m ≥ 0] + 0.67 · δ_{m,0}
```

That is: 67% of the residual is chunk-independent noise; 33% is a persistent
deterministic offset that stays coherent for at least 120,000 s. S99's
"τ = 21,040 s, R² = 0.97" was an exponential fit to a slight downward trend
(0.343 → 0.30 over 10 lags) in what is really a flat plateau.

**Implication**: there is no "diffusion timescale" for raw-channel residual
phase. The persistent component is infinitely long-lived on the 120,000 s
window; the fluctuating component is instantaneous white. The apparent 22ks
from an exp-fit is a fitting artifact — the same data equally supports any
τ from 5,000 s (if you stop early) to ∞ (if you fit to a flat asymptote).

### Finding 3 — ST residual-phase ACF is a plateau at 0.76

The same analysis applied to the ST channel (S98 A=0.30):

```
ST  residual-phase ACF (A=0.30):
  lag:   0     1     2     3     4     5     6     7     8     9     10
  acf:   1.000 0.759 0.772 0.759 0.752 0.780 0.751 0.773 0.763 0.767 0.762
```

ST drops from 1 → 0.76 at lag 1 then plateaus. This is consistent with
ST's superior signal persistence across chunks (R_seeds = 0.999 per S98)
and a small white-noise contribution (~24% of residual variance).

### Finding 4 — Per-seed fitted Δω are small and spread across ±3e-5 rad/s

S98 data, raw-channel per-seed Δω (fit of unwrapped chunk-phase to a linear
rate, rad/s):

```
RAW Δω (rad/s): [+3.19e-5, +6.04e-6, +3.42e-5, +4.37e-6,
                 -9.30e-6, -6.21e-6, -2.80e-6, -7.40e-6]
ST  Δω (rad/s): [+7.01e-7, +6.02e-7, +7.72e-7, -4.13e-7,
                 -6.69e-8, -1.31e-7, +5.57e-7, +2.63e-7]
```

Raw channel: Δω_std = 1.7e-5 rad/s (per S98). These are two orders of
magnitude larger than ST, consistent with S98's observation that raw
"detuning" is dominated by phase-wander artifact, not real frequency
mismatch.

At A=0 Part A, the raw Δω values fit to ±1e-4 rad/s — larger and more
scattered, because with no signal the "phase" being unwrapped is white
noise and the linear fit picks up random slope.

### Finding 5 — ω_spread sweep is statistics-limited

Part B (A=0, 4 seeds × 50 chunks, null floor ~0.072 at lag 1):

```
  ω_spread  |    RAW |C_full| at lags 0..5
  0.000     | 1.00 0.01 0.04 0.13 0.08 0.08
  0.005     | 1.00 0.12 0.04 0.11 0.10 0.02
  0.020     | 1.00 0.03 0.05 0.08 0.02 0.14
  0.080     | 1.00 0.04 0.04 0.09 0.12 0.03
```

All values consistent with null floor (σ ≈ 0.07). No ω_spread dependence.

Part C (A=0.30, 4 seeds × 50 chunks, with complex-mean subtraction):

```
  ω_spread  |    RAW |C_resid| at lags 0..5
  0.000     | 1.00 0.03 0.11 0.08 0.08 0.11
  0.005     | 1.00 0.07 0.03 0.08 0.10 0.12
  0.020     | 1.00 0.09 0.05 0.03 0.04 0.05
  0.080     | 1.00 0.06 0.09 0.06 0.08 0.14
```

After subtracting the per-seed complex mean at A=0.30, the residual ACF
also sits at null floor. This is because complex-mean subtraction over a
rotating response (Δω_seed × T_total = several radians) removes too little
signal when the rotation is present; Part C should have used the linear-Δω
phase-residual method (S99's) with 8×100 statistics, not complex-mean at
4×50. Conclusion: the current Part C design does **not** test S100-P2.

---

## Verdicts

| Prediction | Status | Basis |
|---|---|---|
| **S100-P3** — wander persists at A=0 | **FALSIFIED** | Part A raw chunk ACF indistinguishable from null floor |
| **S100-P2** — τ_res ∝ 1/ω_spread | INCONCLUSIVE | Part B (A=0) shows no wander to scale; Part C (A=0.30) has insufficient statistics |
| **S99-P3** — mechanism for slow raw-channel jitter | REDEFINED | Mechanism is not a ~22ks diffusion; it is a persistent deterministic offset (plateau) plus per-chunk white noise. The offset is signal-induced and infinitely long-lived on the 120,000 s window. |

---

## Updated picture

The S99/S100 narrative — "N=4 deterministic dynamics produce a σ-invariant
22,000s phase-wander timescale" — was built on an exponential fit to data
that doesn't look exponential when you look at more lags with a wider fit
window.

A better description:

- **With no signal** (A=0): raw chunk MF output is **white**. No slow
   structure at all on the 120,000 s window. The free N=4 dynamics at
   σ=0.022 have no spectral feature at f_s = 0.003 Hz that survives 4,000 s
   integration.
- **With signal** (A=0.30): raw chunk MF output has two components, both
   signal-induced:
   1. A large white per-chunk fluctuation (~67% of residual variance).
   2. A persistent ~0.33-normalized deterministic component, coherent on
      ≥ 120,000 s. This is the "persistent part" that the linear-Δω fit
      can't explain away.
- The σ-invariance S100 saw (21ks ↔ 23ks across σ=0.022 vs 0.060) is
   consistent with a **plateau**, because a plateau also doesn't depend
   on σ. Fitting an exponential to a plateau produces a τ dictated mostly
   by the first 10 lags' slight negative slope — a fit-artifact τ, not
   a physical timescale.

This is actually a stronger result than "22ks is σ-invariant". The
residual-phase distribution has structure that's coherent on at least
120,000 s when signal is present, and vanishes entirely when the signal
is removed. The detection problem isn't bounded by diffusion — the
persistent component could in principle be "knowable" with the right model.

---

## New predictions (S101-derived)

- **S101-P1** (plateau height scaling): ACF(m > 0) plateau sits at 0.33
   for RAW at σ=0.022, A=0.30. Does the plateau height scale with signal
   amplitude? Predicts plateau ∝ A²/(A² + noise_variance) — directly
   testable across A ∈ {0.10, 0.20, 0.30, 0.50}.
- **S101-P2** (the persistent component): if the 0.33 plateau is a *fixed
   phase relationship* between chunks, averaging many chunks from the same
   seed should recover a coherent signal vector whose magnitude grows as
   N_chunks (not √N_chunks). Test: vary T_chunk from 1000s to 40000s and
   check per-seed |⟨z⟩| vs T_chunk_total scaling. Linear → persistent
   coherent; √T → diffusive.
- **S101-P3** (ω_spread sweep done correctly): 8 seeds × 100 chunks per ω_spread,
   A=0.30, ω_spread ∈ {0.005, 0.02, 0.08}. Measure plateau height and any
   residual decay. Null floor 0.036 (vs 0.07 in Part C). Would cleanly
   test S100-P2.
- **S101-P4**: S100's σ-sweep of τ_res used the same single-exp fit method.
   The σ-invariance (21ks ↔ 23ks) would become "plateau heights of 0.33 ↔
   0.35 at σ=0.022 ↔ 0.060" under the plateau model — comparable claim,
   cleaner interpretation. Reanalyze S100 σ-sweep data with plateau
   decomposition.

---

## Attractors to resist

- Don't refit τ over short fit windows to "recover" the 22ks figure. The
   ACF is a plateau; any exponential τ you fit depends on how many lags
   you include. Prefer plateau + white decomposition.
- Don't equate "σ-invariant parameter" with "deterministic origin" unless
   you've checked the shape of the curve, not just a fitted scalar. The
   S100 σ-invariance was real, but its interpretation as "22ks timescale"
   was an artifact.
- Don't run ω_spread sweeps at A=0 to probe signal-induced phenomena.
   Trivially returns white noise at every point.

---

## Code + data

- `thor_session_101_intrinsic_wander.py` — Parts A & B (A=0 null + ω_spread).
- `thor_session_101_part_c.py` — Part C attempted (A=0.30 ω_spread, complex-mean residual).
- `thor_session_101_part_c_reanalyze.py` — Applied S99's linear-Δω phase-residual
   method to S98 main data and S101 Part A, enabling the A=0 vs A=0.30 comparison
   at matched 8 × 100 chunks statistics.
- `thor_session_101_analyze.py` — Part A/B full analysis + verdicts.
- Data:
  - `thor_session_101_intrinsic_wander_results.json` (Part A + B full data)
  - `thor_session_101_part_c_results.json` (Part C raw data)
  - `thor_session_101_part_c_reanalysis.json` (direct A=0 vs A=0.30 ACF comparison)
  - `thor_session_101_analysis.json` (Part A + B verdict summary)

---

*The 22ks wasn't a timescale. It was a plateau.*
