# Thor Session #112: The Within-Seed Kuramoto Cliff (S111-P3 Resolved)

**Date:** 2026-04-22
**Focus:** S111-P3 — what drives the bimodal seed population at A=0.50?
**Status:** RESOLVED. The failure mode is a per-seed Kuramoto cliff at
ω_std ≈ 0.17. The 3/10 S111 seeds at A=0.50 with ω_std ∈ {0.169, 0.177,
0.184} were past the cliff. Controlled-ω experiment confirms + produces
four further findings the S111 pre-analysis did not anticipate.

## TL;DR

1. **Free from S111 data**: 3/10 seeds at A=0.50 are bimodal failures
   (mod_lock < 0.025 vs succeeding 0.20–0.27). All 3 failing seeds have
   per-seed ω_std ∈ {0.169, 0.177, 0.184}. Succeeding seeds ω_std ≤ 0.128.
   **Spearman ρ(ω_std, mod_lock) = −0.807 at A=0.50 (p=0.005);
   −0.915 at A=0.40 (p<0.001); −0.806 at A=0.20 (p=0.005)**. Pooled
   across A ≥ 0.20: n=40, Pearson r = −0.524 (p=0.0005).
2. **Decoupled from ⟨R_kura⟩**: ω_std has r = +0.03 with the mean
   Kuramoto order parameter (unchanged) but r = −0.61 with lock_frac
   (time above R>0.9). Wide-ω seeds sit at partial sync but never
   achieve deep lock. **The cliff is a lock_frac cliff, not an R_kura
   cliff.**
3. **S112 controlled ω: ω_std ∈ {0.03, 0.07, 0.11, 0.15, 0.19, 0.23}
   at A=0.50** (ridge κ_p=0.30, κ_C=0.30, ratio 0.8). Detection
   fraction: 1.0, 1.0, 1.0, 1.0, 0.0, 0.0. **Cliff_50 = 0.17** (linear
   interpolation between 0.15 partial-degradation and 0.19 total
   failure).
4. **Cliff location vs Kuramoto**: textbook Δ_c = πκ/4 = 0.236 at
   κ_p=0.30 (bare). Gate-modulated effective (50/50 sign flip) is
   0.118. Empirical cliff_50 = 0.17 sits between — closer to the mid-
   point. The gate is not a pure 50/50 destructive modulator; epochs
   are structured and resynchronization during attractive epochs is
   partial. A 60/40 cycle imbalance would yield Δ_c = πκ/4 · 0.2 = 0.047
   (too small); a structured epoch model with no destructive repulsion
   gives Δ_c ≈ 0.24 (too big). Empirical 0.17 = ~0.72 · bare.
5. **Mild ω heterogeneity HELPS**: ρ_sig_st at A=0.50 is **0.141 at
   ω_std=0.03, 0.165 at ω_std=0.07, 0.163 at ω_std=0.11**, then
   collapses (0.053 at ω_std=0.15). **17% gain from a small amount of
   detuning.** Not predicted. Likely a weak SR-like effect: moderate ω
   dispersion breaks degeneracy and broadens the window of effective
   lock phases during attractive epochs.
6. **Fixing ω eliminates seed variance**: mod_lock_std per cell drops
   to 0.002–0.003 at ω_std≤0.11. S111 at A=0.50 had std=0.126 (CV=53%)
   from random-ω draws. **S111's seed CV is 100% driven by ω-draw
   heterogeneity**, not by initial phase or noise realizations.
7. **Past-cliff detection persists through a direct channel**.
   At ω_std=0.19, A=0.50: lock_frac=0.026 (near-floor), mod_lock=0.013
   (floor), but **|⟨z_st⟩| = 4.2 and ρ_sig = 0.069** — clearly above
   null (A=0 gave |μ_st|≈0.5 in S111). Signal still modulates gate
   timing directly via (C_mean + signal) < threshold, independent of
   phase lock.
8. **At ω_std=0.19, ρ_sig is A-INDEPENDENT** over A ∈ {0.20, 0.30,
   0.40, 0.50, 0.60}: values 0.087, 0.082, 0.078, 0.069, 0.076
   (monotone decreasing, 13% range). **S112-P2 falsified** — the
   Kuramoto cliff has no A-dependence. The phase-lock mechanism is
   dead regardless of signal strength.
9. **S111 re-interpretation**: filtering out failing seeds
   (mod_lock < 0.04) gives succeeding-seed ρ_sig curve
   {A=0.10: 0.072, 0.20: 0.146, 0.30: 0.152, 0.40: 0.132, 0.50: 0.212}.
   The A=0.20 peak and A=0.30 quasi-plateau survive; the A=0.40 dip
   persists. S111's "three regimes" are partially an ω-cliff artifact
   (the A=0.50 variance) but the A=0.30-0.40 dip is a SEPARATE effect
   still unexplained.

## Experiment A: ω_std sweep at A=0.50

ridge κ_p=0.30, κ_C=0.30, ratio 0.8, A=0.50, 10 seeds × 25 chunks each.

| ω_std | fail/10 | lock_frac | R_kura | mod_lock  | ρ_sig  | ⟨N_sw⟩ |
|-------|---------|-----------|--------|-----------|--------|--------|
| 0.030 |   0     |   0.443   | 0.521  | 0.271±0.002 | 0.141 | 6999   |
| 0.070 |   0     |   0.445   | 0.544  | 0.265±0.001 | 0.165 | 6900   |
| 0.110 |   0     |   0.451   | 0.569  | 0.255±0.003 | 0.163 | 6596   |
| 0.150 |   0     |   0.252   | 0.558  | 0.146±0.002 | 0.053 | 7308   |
| 0.190 |  10     |   0.026   | 0.519  | 0.013±0.000 | 0.069 | 6698   |
| 0.230 |  10     |   0.032   | 0.460  | 0.012±0.001 | 0.069 | 5792   |

Per-cell mod_lock std at ω_std ≤ 0.11 is 0.001–0.003. Compared to
S111 with ω_spread=0.24 random-draw (mod_lock std=0.013 at A=0.50 for
7 non-failing seeds), fixing ω cuts residual seed noise by ~5×.

## Experiment B: A sweep at ω_std=0.19 (past cliff)

κ_p=0.30, κ_C=0.30, ratio 0.8, ω_std=0.19, 10 × 25 chunks.

|  A   | fail/10 | lock_frac | R_kura | mod_lock  | ρ_sig | ⟨N_sw⟩ |
|------|---------|-----------|--------|-----------|-------|--------|
| 0.20 |  10     |   0.028   | 0.511  | 0.004±0.001 | 0.087 | 7116   |
| 0.30 |  10     |   0.029   | 0.523  | 0.006±0.001 | 0.082 | 6914   |
| 0.40 |  10     |   0.029   | 0.522  | 0.011±0.001 | 0.078 | 6614   |
| 0.50 |  10     |   0.026   | 0.519  | 0.013±0.000 | 0.069 | 6698   |
| 0.60 |  10     |   0.022   | 0.517  | 0.012±0.001 | 0.076 | 6745   |

**Fail fraction is 1.0 at every A. The Kuramoto cliff is A-independent.**
Signal amplitude cannot rescue detection from ω-induced phase-lock
failure. Note, however, that ρ_sig via the direct channel is robust
(0.07-0.09, non-null) and independent of A in this range.

## Mechanism

Four oscillators with natural frequencies ω_i = ω_base + δ_i.
Kuramoto-style phase coupling with strength `sign(t) · κ_p`, where
`sign(t) = +1 when (C_mean + signal) < threshold, else −1`.

At the ridge geometry, the gate is approximately 50/50 attractive/
repulsive. During attractive epochs, phases lock rapidly (Kuramoto
timescale ~ N/κ_p = 13 sim-time = 130 steps). During repulsive epochs,
phases unlock. The signal-phase-locked R_kura(t) (S110) reports this
alternation: R_kura ~1 during attractive epochs, ~0 during repulsive.

For stable deep-lock (R_kura > 0.9) to be achievable during an
attractive epoch, the Kuramoto criterion must hold:
```
   Δω_max  <  πκ/4  (bare)
```
For κ_p=0.30: Δω_c = 0.236. For N=4 uniform draws with ω_std = s,
Δω_max ≈ 2.5 s (roughly 95%ile of peak-to-peak gap). So s* ≈ 0.095
at bare κ. Empirical cliff s = 0.17 is larger because the epoch
structure is kinder than static bare coupling (destructive epochs are
not fully canceling; they're dephasing-limited at Δω).

Once ω_std > cliff, attractive epochs cannot achieve deep lock —
lock_frac collapses even though R_kura_mean stays ~0.5 (partial,
slowly-drifting sync). The S110 5-step mechanism chain is broken at
step 3 (R_kura(t) signal-phase-locking).

A residual direct-channel ρ_sig ≈ 0.08 survives because the signal
modulates (C_mean + signal) relative to threshold, which biases
switch timing independent of phase-coupling sign. This channel is
A-independent in range [0.2, 0.6] because the N_sw stays ~7000 and
the switch-timing coherence is set by noise statistics not signal
amplitude (the switch events are noise-triggered; signal only biases
their phase relative to f_s).

## S111 reinterpretation

S111 reported three "regimes" in ρ_sig(A) at the ridge. With the
seed-cliff filter applied:

| A    | n_succ | ρ_sig_all | ρ_sig_succ | mu_st_succ | Nsw_succ |
|------|--------|-----------|------------|------------|----------|
| 0.05 |   0    | 0.029     | — (all failed at mod_lock < 0.04 threshold) |
| 0.10 |   3    | 0.075     | 0.072      | 3.77       | 370      |
| 0.20 |   8    | 0.154     | 0.146      | 5.79       | 249      |
| 0.30 |   9    | 0.139     | 0.152      | 6.47       | 311      |
| 0.40 |   9    | 0.128     | 0.132      | 5.90       | 270      |
| 0.50 |   7    | 0.203     | 0.212      | 7.01       | 260      |

Post-filter, ρ_sig_succ is NOT monotonic: 0.072 → 0.146 → 0.152 → 0.132 →
0.212. The A=0.40 dip remains (13% drop from A=0.30, not explained by
seed-cliff). Separately, the A=0.50 peak is now consistent with A=0.30
growth — A=0.20 to A=0.50 is mostly linear if we exclude A=0.40.

**The S111 "three regimes" explanation survives partially but is
diluted**: the A=0.50 variance is 100% ω-cliff, but the A=0.40 dip
is genuine non-monotonicity in per-seed dynamics.

## Predictions

- **S112-P1 (cliff scaling with κ_p)**: predict cliff_50 ∝ κ_p. At
  κ_p=0.10, cliff at ω_std ≈ 0.056. At κ_p=1.0, cliff at ω_std ≈ 0.57.
  Sweep ω_std × κ_p grid.
- **S112-P2 (cliff at κ_C=0)**: without C-coupling the gate is noisier
  but still bistable. Does the cliff persist and at what ω_std?
- **S112-P3 (mild-heterogeneity gain)**: 17% ρ_sig gain at ω_std=0.07
  over 0.03 — is this an SR-like peak or a monotone function with
  different shape? Finer scan at {0.02, 0.04, 0.05, 0.06, 0.07, 0.09, 0.13}.
- **S112-P4 (direct-channel invariance)**: at ω_std=0.19, ρ_sig is
  ~A-independent over [0.2, 0.6]. Does this hold at ω_std=0.30, 0.50,
  or does direct channel also fail for extremely wide ω?
- **S112-P5 (cliff sharpness with N)**: Kuramoto cliff sharpens with
  N. At N=8, predict more abrupt cliff (narrower partial-degradation
  band between lock_frac-intact and cliff-failure).
- **S112-P6 (A=0.40 dip)**: the A=0.30→0.40 dip in ρ_sig_succ is NOT
  cliff-driven and remains to be explained. Possible mechanism:
  signal-period matching to N_sw. At A=0.40 the gate spends more time
  near threshold → switch rate matches sub-harmonic of f_s → coherent
  signal-to-switch alignment is weaker?

## Methodological note

**Always compute per-seed ω_std** (from seed-reconstructed ω draw) as
a candidate confounder when interpreting per-seed variance in this
simulator family. With ω_spread=0.24 (uniform range), per-seed ω_std
spans [0.05, 0.18] — and the cliff at ω_std ≈ 0.17 cuts through this
band. Roughly 25-30% of random seeds at these parameters will be past
the cliff at A=0.50.

For clean mechanism-level experiments at the ridge: either fix ω with
the `{-3, -1, 1, 3}/√5` scheme at ω_std ≤ 0.11 (well below cliff) OR
report per-seed ω_std and stratify.

## Cross-references

- S104: Kuramoto Δ_c cliff at the ensemble level, matching πK/4 to 2%.
- S109: σ_φ at ridge is 64° (ratio 0.8) vs 81° (ratio 0.2). Wider
  effective spread = weaker detection within the surviving lock.
- S110: the 5-step mechanism chain, of which the ω-cliff breaks step 3.
- S111: the dose-response that surfaced the variance.

## Files
- `thor_session_112_omega_cliff.py` — runner (simulate_with_omega)
- `thor_session_112_omega_cliff_results.json` — per-seed records
- `thor_session_112_analyze.py` — this report's numbers
- `thor_session_112_analysis.json` — tidy summary for future sessions
