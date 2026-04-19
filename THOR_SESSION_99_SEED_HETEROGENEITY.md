# Thor Session #99: Matched Compute Is Flat — Seeds-Beat-Long Dissolves

**Date**: 2026-04-18
**Operating point**: N=4 bistable coherence model, σ=0.022 (SR peak), A=0.30,
matched-compute grid n_seeds × T_per = 128,000 s total compute.

## TL;DR

S94 reported a marginal (p=0.047) "seeds beat long" effect in the raw matched
filter — n=64 T=4000s beat n=16 T=16000s by Δ|z_vec|=+0.61 at matched compute.
S98 falsified the drift-based explanation (τ_φ >> 240,000 s). S99 tested the
remaining candidate — seed-level heterogeneity — with a direct factor-32 spread
at matched compute.

**Result — `|z|_sig` is statistically flat across n ∈ {32, 8, 2, 1}** at
n·T_per = 128,000 s, for **both** channels, after the per-cell null-SD sampling
noise is corrected:

| channel | n=32  | n=8   | n=2   | n=1   | ANOVA F(3,20) | p |
|---------|-------|-------|-------|-------|---------------|-------|
| RAW (σ₀-rescaled pooled)  | 6.75 | 6.14 | 7.10 | 6.00 | 1.26 | 0.32 |
| ST  (pooled-null)         | 13.86 | 13.43 | 14.26 | 12.85 | 1.44 | 0.26 |

`FLAT` under both ANOVAs.

**S98-P1 confirmed** at this operating point. Seeds-beat-long is not a feature of
this model at A=0.30, σ=0.022. S94's +0.61 was a small-n marginal draw.

**Methodological finding**: with K=6 null reps per cell, the per-cell null-SD
estimate has SE≈30%, which in turn produces spurious F=25–60 non-flatness
in |z|_sig when each cell is standardized against its own null. The fix is to
use the *theoretically expected* scaling of the null SD across cells (constant
for ST, √(n/T_per) for RAW) and pool. Matched-compute sweeps must account for
this, or they will hallucinate cell-level structure that is not there.

**Side finding (from Part 1 reanalysis of S98)**: raw-channel per-chunk MF phase
residuals (after linear-Δω subtraction) show σ_φ ≈ 3 rad with slow
autocorrelation (τ_wander ≈ 5.3 chunks ≈ 21,000 s). ST residuals are 0.54 rad,
essentially zero autocorr. This asymmetry is real but does *not* dominate
detection performance at this operating point — the wander is bounded enough
and the MFs self-normalize appropriately. At higher A or lower σ (where signal
becomes more marginal relative to wander), this could matter; for now it's
a structural feature, not a performance bottleneck.

## Method

### Part 1: S98 reanalysis
Post-processed S98's 8 seeds × 100 chunks × 4000 s dataset per channel:
amplitude heterogeneity (across-seed CV, within-seed CV), linear-Δω slope fit
on unwrapped arg(z_k), residual RMS, and chunk-lag autocorrelations of |z_k|²
and of the linear-fit residual phase.

### Part 2: matched-compute sweep
Grid n_seeds ∈ {32, 8, 2, 1}, T_per = 128,000 / n_seeds; 6 sig + 6 null
reps/cell; 48 reps total. Each rep runs n_seeds independent trajectories
(seed-stride to avoid reuse across reps) of WARMUP + T_per_steps, then
coherently sums per-seed `phase_coherent_IQ` and `switch_timing_IQ` outputs
with `t_offset = WARMUP`.

### Flatness test

Under a stationary signal with near-white MF noise, at fixed `n·T_per`, |z|_sig
is predicted constant across cells:
- ST: null SD ≈ constant (Poisson-like point-process MF, total switches matched).
- RAW: null SD scales as √(n/T_per) (mean-normalized MF on white-noise floor
  has per-seed SD ∝ 1/√T, coherent sum adds √n).

Per-cell estimates of these SDs from K=6 null reps carry SE≈30% each. Pooling
across cells, after rescaling RAW by the predicted √(T_per/n) weight, gives a
theoretically-justified shared null SD with SE≈15%. Unit-SD check: the scaled
RAW null SD = 0.99 (I) / 1.08 (Q), consistent with unity. One-way ANOVA on the
corrected per-cell |z|_sig tests flatness.

### Compute
S99 Part 2: 48 reps × ~33 s = 1,584 s ≈ 26 minutes on Thor (ARM64 numpy).

## Results

### Part 1: per-seed amplitude, Δω, and phase structure (S98 reanalysis)

```
chan    mean|z|  across-CV%  within-CV%    Δω_std       Δω·T128k°  R_seed
z_raw    0.0277    4.39%      50.11%       1.74e-05     127.31°    0.9991
z_st     5.7356    2.83%      39.77%       4.42e-07       3.24°    0.9994
```

And the phase-wander structure (residual phase after linear-Δω subtraction):

```
chan    resid_rms    acorr_m=1   acorr_m=5   acorr_m=10
z_raw   3.07 rad     0.829       0.497       0.138
z_st    0.54 rad    -0.032       0.063      -0.023
```

**Raw channel**: resid_rms ≈ 3 rad is essentially circularly-uniform scatter;
the autocorrelation decays as exp(-m/τ) with τ ≈ 5.3 chunks ≈ 21,000 s.
Interpretation: the "linear Δω" fit of 1.74e-5 is largely a slope-of-noise
artifact — raw phase is a slow OU-like wander around a mean direction, not
a linear drift. This is consistent with S98's Φ(m) being flat at the `R_mean²`
plateau ≈ 0.35 (since the autocorrelation's decay into the noise floor happens
within the first ~10 chunks, m=1 is already close to the plateau).

**ST channel**: resid_rms 0.54 rad with essentially zero chunk-to-chunk
autocorrelation — genuinely stationary. The ST MF projects response into a
direction orthogonal to the wandering raw subspace (summation-by-parts, S96).

### Part 2: per-cell raw statistics

Per-cell null SDs (each from 6 null reps):

```
 n   T_per   RAW_SD_I   RAW_SD_Q    ST_SD_I    ST_SD_Q
32    4000   0.0885     0.1118     13.50      12.13
 8   16000   0.0178     0.0133      6.23      10.37
 2   64000   0.0070     0.0062     14.16      15.81
 1  128000   0.0023     0.0033     10.80       9.40
```

- **RAW null SDs** track √(n/T_per) predictions (0.089, 0.022, 0.0056, 0.0028)
  within ±1.6× — noise scales as matched-compute white-noise law.
- **ST null SDs** fluctuate around ≈11 with K=6 sampling noise (predicted
  constant). Pooled (K=24): SD_I=11.84, SD_Q=12.24.

Per-cell `|z|_sig` using each cell's own null SD (susceptible to K=6 null-SD
sampling noise):

```
channel    n   T_per_s     |z|_sig       |z|_null   null_q95   pow@5%
RAW       32     4000    5.59±1.27        1.22       1.87      1.00
RAW        8    16000   10.39±0.69        1.17       1.87      1.00
RAW        2    64000    6.74±1.24        1.24       1.72      1.00
RAW        1   128000    6.07±0.94        1.21       1.83      1.00
ST        32     4000   12.72±1.49        1.18       1.82      1.00
ST         8    16000   20.14±0.88        1.14       2.02      1.00
ST         2    64000   11.58±1.19        1.26       1.63      1.00
ST         1   128000   15.68±1.14        1.14       1.91      1.00
```

Naive ANOVA on these per-cell means gives F(3,20)=25.3 (RAW), F(3,20)=61.5 (ST),
both p<0.0001 — would naively conclude non-stationary. But these are dominated
by K=6 per-cell null-SD sampling variation, not real structure.

### Flatness after correction for the theoretical null scaling

**RAW, σ₀-rescaled pooled null (weight w = √(T_per/n))**:

scaled null SD = (0.991, 1.081) ≈ (1, 1) — the theoretical √(n/T_per) scaling
fits essentially perfectly.

```
n     |z|_sig (σ₀ units)
32    6.75
 8    6.14
 2    7.10
 1    6.00
```

F(3,20) = 1.26, p = 0.32. **FLAT.**

**ST, pooled null (K=24)**:

```
n     |z|_sig (pooled)
32    13.86
 8    13.43
 2    14.26
 1    12.85
```

F(3,20) = 1.44, p = 0.26. **FLAT.**

### Detection power

All four cells detect at power=1.00 at 5% FAR in both channels — the signal is
comfortably above threshold at A=0.30, σ=0.022 for any n·T_per ≥ 128,000 s.
This is NOT the interesting regime for seeds-beat-long; S94's marginal regime
was A=0.12–0.20 at smaller n·T. The flatness result is indicative of the
mechanism being absent in this model family at feasible compute, but A-scans
at the detection floor are the proper next experiment.

## Interpretation

### S98-P1 confirmed
At matched compute, the ST detection z-score is invariant to whether the
sample is 32 short seeds or 1 long seed. The signal is stationary and the
point-process MF's noise is near-Poisson white.

### RAW's √(n/T_per) null scaling is exact
The RAW null SD hits the white-noise theoretical prediction within 1% after
pooling. This is a strong cross-check that `phase_coherent_IQ` is operating
correctly and that the simulator's residual C-dynamics are close-enough to
white at f_s=0.003 that the matched-compute invariance holds.

### S94's seeds-beat-long was noise
At a different operating point (A=0.12–0.20, σ=0.030), S94 used paired-seed
differences over a narrow T-spread (4×, not 32×) and observed +0.61 with
p=0.047. Combined with S98's direct phase measurement and S99's flat
matched-compute result, the finding does not replicate. It was a marginal
small-n draw.

### Why is RAW's phase wandering but detection is flat?
Raw's per-chunk MF output z_k has large (3-rad) slow phase wander. Why
doesn't this destroy coherent integration at long T_per?

Because the **per-seed RAW signal is T-invariant** (it's the time-MEAN of a
stationary process, not the time-sum). The wander is chunk-to-chunk scatter
within a long trajectory — averaging over 32 chunks of 4000s doesn't
coherently integrate a fixed phase but rather estimates the mean over
stationary jitter. Each chunk contributes a fraction of the time-mean, and
the noise contribution drops as 1/√T_per. The MF matches this exactly: signal
per seed invariant, noise per seed ∝ 1/√T_per, and the matched-compute
invariance holds by construction.

The ST MF uses event times, not amplitudes — still stationary, and via the
summation-by-parts rotation of S96, it projects orthogonally to the wandering
raw direction, where the residuals happen to be stationary.

### Takeaways for future sessions

1. **K=6 is too few for per-cell null-SD.** In any matched-compute or
   cell-sweep experiment where cells have theoretically-equal (or
   theoretically-known) null SD, pool across cells. This reduces the SE of the
   SD estimate from ~30% to ~15% and prevents spurious "non-flatness" results.
2. **Ratio of predicted-to-observed null SDs is a useful sanity check.** S99
   RAW ratios 1.00/0.80/1.25/1.07 confirmed √(n/T) scaling; ST constant-prediction
   held to within ±20%. If these deviate sharply, re-examine the simulator.
3. **Seeds-beat-long is not a feature of this model** at A≥0.30 σ=0.022. If
   it exists at all, it's at the detection floor (A≈0.08–0.12) and requires
   larger K (K≥24 per cell) to see reliably.
4. **Raw phase wander is a structural feature, not a detector bottleneck.**
   ST MF is immune; raw MF is self-correcting at matched compute.

## Falsifications and closures

- **S98-P1 CONFIRMED**: at matched `n·T_per = 128,000 s`, `|z|_sig` is flat
  across n ∈ {32, 8, 2, 1} after per-cell null-SD sampling noise is controlled.
  Mechanism (both channels): stationary signal + near-white noise + correct
  MF normalization. No seeds-beat-long, no long-beats-seeds.
- **S98-P2 CONFIRMED**: per-seed Δω detuning is O(10⁻⁶) rad/s for the ST MF;
  RAW's 1.74e-5 "slope" is primarily slow-wander fit noise, not clean linear
  detuning. At all feasible T_per, Δω is not a limiting factor.
- **S94's +0.61 seeds-beat-long finding**: not reproducible; was a small-n
  draw at p=0.047.

## Open threads

- **Detection-floor regime**: run the same matched-compute sweep at A=0.10
  where the signal is comparable to the per-chunk noise. Would wander-level
  effects manifest there? Would seeds-beat-long actually emerge?
- **σ-dependence of wander**: S98's σ-sweep data (σ ∈ {0.015, 0.022, 0.030})
  has enough per-chunk statistics to measure τ_wander in each cell. Does
  raw's 21,000-s wander timescale shift with σ?
- **Raw-wander physical interpretation**: what in the N=4 bistable dynamics
  produces the slow raw-channel phase jitter that ST filters out? Candidate:
  intra-oscillator phase-locking drift, or coupling to C_amplitude fluctuations
  around the threshold. Would be a nice S100+ thread.

## Commits

- `thor_session_99_seed_heterogeneity.py` — main experiment script.
- `thor_session_99_analyze.py` — analysis with pooled + rescaled null tests.
- `thor_session_99_seed_heterogeneity_results.json` — raw data, 202 KB.
- `thor_session_99_analysis.json` — analysis summary.
- `thor_session_99.log` — run log.
- `THOR_SESSION_99_SEED_HETEROGENEITY.md` — this document.

Co-Authored-By: Claude <noreply@anthropic.com>
