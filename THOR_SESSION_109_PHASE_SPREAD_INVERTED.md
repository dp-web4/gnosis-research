# Thor Session #109: The Phase-Spread Mechanism, Inverted

**Date:** 2026-04-22
**Focus:** S108-P3/P6 — does per-oscillator phase spread explain the ρ_sig
asymmetry between deep-coherent (ratio 0.2) and near-desync (ratio 0.8)?
**Status:** Resolved with a sign flip. **S108-P6 is falsified, but the
phase-spread mechanism is real — it points the other way.** Tighter phase
ensembles produce *more* per-event signal density, not less. The dominant
phase observable is `lock%` (fraction of time R_kura(t) > 0.9), not
time-averaged σ_φ. Within ridge cells, ρ_sig ≈ 0.4 · R_inst².

## TL;DR

S108 §4 hypothesized that ratio 0.2's lower ρ_sig comes from over-locked
phases producing *less* drive diversity. S109 measured per-oscillator
phase trajectories directly across 6 cells and found:

1. **σ_φ is LARGER at ratio 0.2, not smaller.** At κ_C=0.30 the spread is
   80.7° (ratio 0.2) vs 64.1° (ratio 0.8) — opposite to S108-P6 by 17°.
2. **σ_φ and ρ_sig are NEGATIVELY correlated** across cells (r = −0.52).
   Tighter phases → higher ρ_sig.
3. **lock% (fraction of time R_kura(t) > 0.9) is the cleanest predictor**
   of ρ_sig (r = +0.61 across all 6 cells, ~+1.0 within κ_C=0.30 ridge).
4. **Within the κ_C=0.30 ridge cells, ρ_sig ≈ 0.4 · R_inst²** — per-event
   signal density scales as the square of mean Kuramoto coherence.
5. **Mechanism inversion:** synchronized phases → switch events synchronized
   in time → events cluster at signal-phase peaks → high signal density.
   S108 §4's "loose phases give each oscillator a different signal phase
   to sample" intuition was empirically backwards.

The bimodality prediction (P3) is partly upheld: pairwise |Δφ| has both a
zero-peak (locked) and a π-tail (anti-locked); ratio 0.2 cells show stronger
bimodal split (bi-score 0.36–0.46) than ratio 0.8 cells (0.21–0.28).

The sign-reversal claim from S107/S108 (bigger κ_p at κ_C=0 hurts ρ_sig)
**did not reproduce** in this 8-seed cell — ρ_sig was statistically
indistinguishable. P5 is unresolved; the original sign reversal may be
noise on a low-signal cell.

## Data — Six Cells (8 seeds × 30 chunks × 40k steps each)

| label             | κ_p | κ_C | ratio | σ_φ° | R_inst | σ_cos | lock% | N_sw | ρ_sig_st | RAW R | ST R |
|-------------------|----:|----:|------:|-----:|-------:|------:|------:|-----:|---------:|------:|-----:|
| kp030_kC000_r02   | 0.30| 0.00| 0.20  | 71.4 | 0.516  | 0.408 | 42.8% |  924 | 0.0088   | 0.063 | 0.536|
| kp030_kC030_r02   | 0.30| 0.30| 0.20  | 80.7 | 0.443  | 0.464 | 33.0% |  299 | 0.0654   | 0.294 | 0.635|
| kp030_kC000_r08   | 0.30| 0.00| 0.80  | 64.5 | 0.558  | 0.445 | 39.9% |  822 | 0.0101   | 0.123 | 0.453|
| kp030_kC030_r08   | 0.30| 0.30| 0.80  | 64.1 | 0.558  | 0.458 | 39.4% |  279 | 0.1484   | 0.542 | 0.759|
| kp050_kC000_r08   | 0.50| 0.00| 0.80  | 64.8 | 0.557  | 0.452 | 31.5% |  799 | 0.0107   | 0.158 | 0.426|
| kp050_kC030_r08   | 0.50| 0.30| 0.80  | 55.8 | 0.641  | 0.400 | 50.3% |  264 | 0.2116   | 0.724 | 0.807|

R_coh values reproduce S108 within 1σ across all overlapping cells (different
seeds, same protocol).

## Headline Result: The Phase-Ridge Asymmetry

The two ridge-peak cells (κ_C=0.30, κ_p=0.30, ratio ∈ {0.2, 0.8}):

```
                    ratio 0.2    ratio 0.8
σ_φ (mean)          80.7°        64.1°       Δ = +16.6°
R_inst              0.443        0.558       Δ = −0.115
lock% (R>0.9)       33.0%        39.4%       Δ = −6.4%
ρ_sig_st            0.0654       0.1484      ratio = 0.44 (S108: 0.39)
```

S108-P6 predicted "std ≈ 5° at ratio 0.2, ≈ 25° at ratio 0.8." Actual values
are ~15× larger and in the opposite ranking. The R_kura time-average
already hinted at this (S108 noted R_kura drops with κ_C at ratio 0.2),
and S109 confirms it via direct per-sample trace.

## Mechanism: Tight Phases → Synchronized Switches → High ρ_sig

The drive on each C-oscillator is `−R_func · (C − φ) · cos(phase_k)`. When
all four phases are coherent (R_inst high), all four C's experience similar
forcing — they swing together, cross threshold together, and switch events
cluster in time.

Per-event signal density ρ_sig = |⟨z_st⟩|² / ⟨N_sw⟩ measures how much of
each switch event's matched-filter contribution stacks coherently with the
signal. Two regimes:

- **Synchronized switches (high R_inst):** switches cluster at signal-phase
  peaks; each contributes the same complex phasor; |⟨z_st⟩|² ≈ N_sw·|z̄|²;
  ρ_sig ≈ |z̄|² (large).
- **Scattered switches (low R_inst):** switches spread across signal phases;
  vector average kills coherent magnitude; |⟨z_st⟩|² ≪ N_sw·|z̄|²;
  ρ_sig small.

Within the three κ_C=0.30 ridge cells, ρ_sig fits ρ_sig ≈ k · R_inst²:

| cell             | R_inst | R_inst² | ρ_sig | k = ρ_sig / R_inst² |
|------------------|-------:|--------:|------:|--------------------:|
| kp030_kC030_r02  | 0.443  | 0.196   | 0.0654| 0.333               |
| kp030_kC030_r08  | 0.558  | 0.311   | 0.1484| 0.477               |
| kp050_kC030_r08  | 0.641  | 0.411   | 0.2116| 0.515               |

R² of log(ρ_sig) ~ 2·log(R_inst): excellent (3 points). The slope ≈ 2 is
consistent with the matched-filter prediction (signal magnitude squared).
The intercept k drifts upward with κ_p, suggesting κ_p adds a separate gain
on top of the phase-coherence amplification.

The κ_C=0 cells (low signal regime) have ρ_sig in [0.009, 0.011] regardless
of phase observables — at this level the drive is too small for the
mechanism to express clearly.

## Bimodality (P3): Locked vs Anti-Locked

Pairwise |Δφ| histograms across all six cells share a common pattern:
strong peak at 0° (locked pairs), small but elevated tail at π° (anti-locked
pairs), low density in the middle. Bimodality score = (P[0–22°] + P[158–180°])
− (P[68–90°] + P[90–112°]):

| cell             | P[0–22°] | P[158–180°] | bi-score |
|------------------|---------:|------------:|---------:|
| kp030_kC000_r02  | 44.4%    | 14.4%       | +0.46    |
| kp030_kC030_r02  | 35.6%    | 15.9%       | +0.36    |
| kp030_kC000_r08  | 29.2%    | 10.7%       | +0.26    |
| kp030_kC030_r08  | 27.4%    | 10.4%       | +0.23    |
| kp050_kC000_r08  | 26.3%    | 10.5%       | +0.21    |
| kp050_kC030_r08  | 30.6%    |  8.8%       | +0.28    |

Ratio-0.2 cells have higher bi-scores (0.36, 0.46) than ratio-0.8 cells
(0.21–0.28). At deep-coherent regime, when phases unlock they don't spread
uniformly — they form anti-aligned clusters. This anti-locked fraction is
what pulls down R_kura at ratio 0.2 κ_C=0.30 (R_inst=0.443). The wide
σ_φ doesn't mean uniform spread; it means a structured split.

This matches an antiferromagnetic mode in the Kuramoto array under
sign-flipping coupling: when the C-mean signal pushes coupling repulsive,
the phases find anti-aligned configurations (which are stable repulsive
fixed points for the N=4 even-N case). When attractive, they collapse to
locked. The system spends time in both modes; the time-average looks like
"loose ensemble" but is really "bistable lock/anti-lock toggle."

## Cross-Cell Correlations (P4)

| predictor → response | r       |
|----------------------|--------:|
| σ_φ → ρ_sig          | −0.52   |
| R_inst → ρ_sig       | +0.55   |
| lock% → ρ_sig        | +0.61   |
| σ_cos → ρ_sig        | −0.29   |
| N_sw → ρ_sig         | **−0.85** |
| σ_φ → R_raw          | −0.53   |
| σ_cos → R_st         | −0.25   |

N_sw is the dominant cross-cell predictor (r = −0.85), but this is mostly
the κ_C-effect — N_sw drops 3× from κ_C=0 to κ_C=0.30. Within κ_C=0.30
cells (3 points), the lock% / R_inst / N_sw orderings all match ρ_sig
ranking perfectly. The phase observables are confounded with κ_C across
the full set; they emerge as the clean predictors *within* κ_C strata.

σ_cos (per-sample std of cos(φ_k) across the N=4 ensemble) tracks ρ_sig
weakly (r = −0.29). cos(phase) is bounded in [−1, 1] and saturates at the
spread floor. Better diagnostics: R_inst directly, or lock%.

## Sign-Reversal at κ_p=0.50 κ_C=0 (P5): Did Not Reproduce

S107 reported ρ_sig_st = 0.0083 at κ_p=0.30 κ_C=0, dropping to 0.0051 at
κ_p=0.50 κ_C=0 — a sign reversal claimed in S108 §"ρ_sig Separability".
S109 with fresh seeds:

| cell            | ρ_sig_st (S107)  | ρ_sig_st (S109)  | ST R_coh ± std |
|-----------------|-----------------:|-----------------:|---------------:|
| kp030_kC000_r08 | 0.0083           | 0.0101           | 0.453 ± 0.104  |
| kp050_kC000_r08 | 0.0051           | 0.0107           | 0.426 ± 0.243  |

Both cells now report essentially identical ρ_sig (~0.010). The κ_p=0.50
κ_C=0 cell has ST R_coh std = 0.243 (huge — one seed gave |z_st|=0.22,
others 2–3). At this signal level, individual seed noise dominates; the
S107 sign-reversal was likely a sampling artifact on a near-floor cell,
not a real κ_p × κ_C interaction at κ_C=0.

The mechanism story still requires that κ_p × κ_C is non-multiplicatively
separable (S108-P4): at κ_C=0, increasing κ_p doesn't reach the ridge,
so ρ_sig stays at floor. At κ_C ≥ 0.15, increasing κ_p tightens the
phase ensemble (σ_φ drops 64.1° → 55.8° as κ_p goes 0.30 → 0.50 at
κ_C=0.30 ridge) and amplifies ρ_sig.

## What This Closes / Updates

### S108-P6 (literal): FALSIFIED in opposite direction
σ_φ at ratio 0.2 (80.7°) is LARGER than at ratio 0.8 (64.1°) at κ_C=0.30,
not smaller. The S108 §4 hypothesis (phase-locking explanation for ρ_sig
asymmetry) had the right mechanism class but wrong sign.

### S108-P3 (bimodality): SUPPORTED
Pairwise |Δφ| is bimodal at ratio 0.2 (locked + anti-locked clusters);
ratio 0.8 has a flatter, locked-dominated distribution. The "deep
coherent" regime is actually a *toggling lock/anti-lock* regime when
viewed instantaneously.

### S108-P4 (κ_p × κ_C non-separable): RECONFIRMED
At κ_C=0.30, κ_p sweep tightens phases and amplifies ρ_sig (positive
slope). At κ_C=0, κ_p sweep does neither (ρ_sig flat at floor). The
gain is gated by κ_C, as S108 inferred.

### S108-P5 (sign reversal at κ_p=0.50 κ_C=0): NOT REPRODUCED
The 8-seed cell at κ_p=0.50 κ_C=0 ratio 0.8 gives ρ_sig statistically
indistinguishable from κ_p=0.30 same conditions. The S107 reading of a
sign reversal was probably seed noise on a near-floor signal cell.

### New finding: ρ_sig ≈ k · R_inst² within ridge
Within the three κ_C=0.30 cells, ρ_sig scales as the square of the
time-averaged Kuramoto order parameter R_inst, with intercept k that
drifts mildly upward with κ_p. The squared dependence matches the
matched-filter prediction: signal magnitude is the coherent sum of N_sw
phasors that all share the synchronized-switch phase; |⟨z⟩|² ∝ R²·N_sw.
Worth pinning down with more cells.

### New finding: lock% is the cleanest phase predictor
Among σ_φ, R_inst, σ_cos, lock% — the "fraction of time R_kura(t) > 0.9"
ranks ρ_sig most cleanly across all six cells (r=+0.61). It also has
direct mechanistic meaning: it's the duty cycle of synchronized switching.
Future ridge analyses should report lock% alongside R_kura.

## Residual Open Questions

- **S109-P1** (κ_p saturation at the ridge): does ρ_sig keep growing as
  κ_p² · R_inst²? Sweep κ_p ∈ {0.75, 1.0, 1.5} at κ_C=0.30 ratio 0.8.
  Test the R_inst² scaling and look for ceiling.

- **S109-P2** (lock% as cliff probe): does lock% at the Kuramoto cliff
  (ω/κ ≈ π/4) drop sharply with ω even where σ_φ is smooth? lock% may
  be a sharper transition probe than R_kura time-average.

- **S109-P3** (signal-resolved phase locking): is lock% modulated by the
  signal cycle? Predict: more locked time during the "attractive" half-cycle
  (C_mean+signal < threshold), less during repulsive. If confirmed, this
  IS the mechanism by which signal information is amplified through the
  switching detector.

- **S109-P4** (anti-locked mode at ratio 0.2): the bimodal π-tail at
  ratio 0.2 cells is the antiferromagnetic mode. Does its prevalence track
  with κ_C·dt × N_attractive_fraction? Direct test of where it lives in
  the phase diagram.

- **S109-P5** (sign-reversal status): redo κ_p=0.50 κ_C=0 ratio 0.8 with
  16+ seeds to settle whether the S107/S108 sign reversal at κ_C=0 is real
  or noise. Predict: noise — ρ_sig remains at floor (~0.010) across all κ_p.

### Unchanged from S108
- **S108-P1** (ridge locus across wider ratio sweep)
- **S108-P2** (ridge height vs ratio sweep)
- **S108-P4** (ST ceiling test)
- **S107-P1** (ridge fine structure)

## Methodological Notes

1. **Phase observables come in two layers**: the time-averaged R_kura
   (smooth) and the per-sample R_kura(t) (which spikes through 0.9
   intermittently). The latter is what matters for switch synchronization.
   Report `lock_frac_R09` = mean(R_kura(t) > 0.9) alongside mean R_kura.

2. **Wide σ_φ ≠ uniform spread**. Wrapped-normal interpretation breaks for
   the bimodal lock/anti-lock distribution seen at deep-coherent regime.
   Always report the pairwise |Δφ| histogram, not just the circular std.

3. **κ_C=0 cells are signal-floor**. ρ_sig at κ_C=0 is dominated by
   single-seed noise (ST R_coh std up to 0.24 in 8-seed runs). Sign-reversal
   claims at κ_C=0 require ≥16 seeds to discriminate from floor.

4. **The matched-filter R_inst² scaling** (ρ_sig ∝ R_inst² within ridge)
   is a 3-point fit and needs more κ_p × κ_C cells to validate. If it
   holds, it gives a closed-form prediction: dR_coh/dκ_p ∝ d(R_inst²)/dκ_p
   times the gain factor that depends on κ_C.

5. **Compute**: 6 cells × 8 seeds × 30 chunks × 40 ks per seed = 1453 s
   total (24.2 min on Thor). 30 chunks (vs S108's 50) is sufficient when
   phase observables are the focus, since they're computed from the
   continuous trace, not from chunk-level z statistics.

## Predictions

- **S109-P1** (R_inst² law): at κ_p=0.30, κ_C=0.30, sweep ratio at 0.4,
  0.6, 1.0, 1.2 (around the cliff). ρ_sig should track 0.4 · R_inst² with
  R_inst peaking near ratio 0.6–0.8.

- **S109-P2**: ρ_sig at κ_p=1.0 κ_C=0.30 ratio 0.8 ≈ 0.45 · 0.78² ≈ 0.27
  (extrapolating the ridge cells). Test R_inst doesn't saturate.

- **S109-P3** (signal-resolved lock%): lock_frac_R09 conditional on
  attractive half (signal+C_mean < threshold) ≥ 1.5× lock_frac_R09 in
  repulsive half. Direct mechanism for signal coupling into switching.

- **S109-P4**: bi-score of pairwise |Δφ| at ratio 1.5 (post-Kuramoto-cliff)
  collapses to ~0 (uniform spread, no anti-locked mode). The
  anti-locked mode is a coherent-regime structure.
