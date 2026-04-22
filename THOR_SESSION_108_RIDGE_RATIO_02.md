# Thor Session #108: The Ridge Survives at Ratio 0.2 — But Its Height Does Not

**Date:** 2026-04-21
**Focus:** S107-P3 — does the κ_C ≈ 0.27 ridge location shift with ω/κ_p ratio?
**Status:** Resolved. κ_C* shifts only slightly left at ratio 0.2 (RAW −0.03, ST −0.06), but **ridge HEIGHT drops 31% (RAW)**. Deep-coherent regime is a *worse* detection environment than near-desync, despite sharper phase locking.

## TL;DR

Ratio 0.2 slice at κ_p=0.30 (ω=0.06), same κ_C grid as S106/S107 (0.00, 0.05, 0.15, 0.30, 0.50), with the S105 r02_k030 cell recycled at κ_C=0.15.

| regime         | ω   | RAW κ_C* | RAW R_peak | ST κ_C* | ST R_peak |
|----------------|----:|---------:|-----------:|--------:|----------:|
| ratio 0.8 (near desync) | 0.24 | 0.274 | 0.637 | 0.253 | 0.831 |
| ratio 0.2 (deep coherent) | 0.06 | 0.249 | 0.442 | 0.190 | 0.758 |
| Δ (0.2 − 0.8)  |     | −0.026 | −0.195 | −0.062 | −0.073 |

**Ridge location is approximately universal in κ_C** (shift within the grid-spacing resolution of ±0.075 between the 0.15 and 0.30 sample points — although the ST shift is a real ~1/3-grid-step leftward drift).

**Ridge height is NOT universal.** RAW ridge collapses by 31% in the deep-coherent regime. ST is more robust (−9%) because it's nearer its ceiling of 1.

Side finding (S107-P4 answered): **ρ_sig(κ_p, κ_C) does NOT factorize.** Log-rank-1 fit on the S107 ratio-0.8 grid gives R²=0.93 but row ratios ρ(κ_p=0.50)/ρ(κ_p=0.30) span 0.57→1.64 across κ_C with a sign reversal at κ_C=0. The κ_p × κ_C interaction is non-multiplicative.

## Data — Ratio 0.2 (κ_p=0.30, ω=0.06)

| κ_C  | R_raw | R_st  | μ_raw  | μ_st | σ_n_raw | σ_n_st | N_sw | R_kura | ρ_sig_st | source        |
|-----:|------:|------:|-------:|-----:|--------:|-------:|-----:|-------:|---------:|---------------|
| 0.00 | 0.031 | 0.494 | 0.003  | 2.74 | 0.016   | 2.76   |  928 | 0.522  | 0.0081   | S108 new      |
| 0.05 | 0.226 | 0.694 | 0.009  | 4.21 | 0.017   | 2.77   |  800 | 0.531  | 0.0221   | S108 new      |
| 0.15 | 0.495 | 0.779 | 0.023  | 5.85 | 0.023   | 3.11   |  566 | 0.524  | 0.0604   | S105 (recycled) |
| 0.30 | 0.324 | 0.641 | 0.019  | 4.42 | 0.027   | 3.29   |  296 | 0.447  | 0.0661   | S108 new      |
| 0.50 | 0.098 | 0.202 | 0.008  | 1.33 | 0.024   | 2.68   |  118 | 0.296  | 0.0150   | S108 new      |

Quadratic fit (R = a κ² + b κ + c):
- RAW: κ_C* = 0.249, R_peak = 0.442, r² = 0.81, curvature a = −5.9
- ST:  κ_C* = 0.190, R_peak = 0.758, r² = 0.96, curvature a = −5.9

## Data — Ratio 0.8 reference (κ_p=0.30, ω=0.24)

| κ_C  | R_raw | R_st  | μ_raw  | μ_st | σ_n_raw | σ_n_st | N_sw | R_kura | ρ_sig_st |
|-----:|------:|------:|-------:|-----:|--------:|-------:|-----:|-------:|---------:|
| 0.00 | 0.091 | 0.469 | 0.005  | 2.63 | 0.015   | 2.75   |  829 | 0.551  | 0.0083   |
| 0.05 | 0.250 | 0.653 | 0.011  | 4.07 | 0.018   | 2.92   |  737 | 0.552  | 0.0224   |
| 0.15 | 0.559 | 0.790 | 0.027  | 6.20 | 0.024   | 3.19   |  512 | 0.568  | 0.0751   |
| 0.30 | 0.610 | 0.795 | 0.038  | 6.78 | 0.028   | 3.30   |  269 | 0.584  | 0.1710   |
| 0.50 | 0.269 | 0.520 | 0.017  | 3.30 | 0.027   | 2.98   |  156 | 0.450  | 0.0696   |

Quadratic fit:
- RAW: κ_C* = 0.274, R_peak = 0.637, r² = 0.99, curvature a = −7.3
- ST:  κ_C* = 0.253, R_peak = 0.831, r² = 0.97, curvature a = −5.2

## Observations

### 1. The ridge LOCATION is approximately universal in κ_C.
Both ratios peak near κ_C ≈ 0.2–0.3. The peak shifts leftward at ratio 0.2 by 0.025 (RAW) or 0.063 (ST). For RAW this is below grid-spacing resolution; for ST it is ~1/3 of a grid step — a real but modest shift. **The rate-vs-precision balance that defines the κ_C ridge is a C-dynamics property, with only weak dependence on phase regime.**

### 2. The ridge HEIGHT is NOT universal.
At the ridge peak, RAW R_coh drops from 0.637 (ratio 0.8) to 0.442 (ratio 0.2) — a 31% reduction. ST drops from 0.831 to 0.758 (9% reduction, but ST is near its ceiling so this understates the effect). **Near-desync phase regime (ratio 0.8) is a better signal environment than deep-coherent (ratio 0.2).**

This inverts a naive expectation: at ratio 0.2 phases are tightly locked, so one might expect coherent signal driving. Empirically, the opposite holds — sharply phase-locked oscillators produce *less* per-event signal density.

### 3. N_sw is nearly ratio-invariant.
For κ_C ≤ 0.30, ratio-0.2 / ratio-0.8 N_sw ≈ 1.10–1.12. Switch rate is set by κ_C (and A, σ), essentially independent of ω/κ_p. This confirms S107's "N_sw(κ_C) is κ_p-invariant" — now also ratio-invariant. The event rate is a robust property of the C-dynamics. (Exception: at κ_C=0.50, N_sw is slightly lower at ratio 0.2 — 118 vs 156 — probably because deep-locked phases reinforce the over-homogenization collapse.)

### 4. ρ_sig diverges between regimes at κ_C ≥ 0.15.
Per-event signal density ρ_sig = |⟨z_st⟩|² / ⟨N_sw⟩ at κ_C=0.30: 0.066 at ratio 0.2 vs 0.171 at ratio 0.8. Ratio 0.2 / ratio 0.8 ≈ 0.39 at κ_C=0.30, 0.22 at κ_C=0.50. **At ratio 0.2, each switch event carries less signal information than at ratio 0.8 — specifically when κ_C is sufficient to homogenize C.**

Interpretation candidate: at ratio 0.8, partial phase desynchronization leaves "room" for each C-oscillator to acquire a *distinct* phase of the signal forcing; averaging across the N=4 array produces a coherent composite response. At ratio 0.2, phases collapse onto a single trajectory; all four C's receive nearly the same instantaneous forcing; mean-field averaging gives less net signal amplification.

### 5. R_kura differs systematically.
At ratio 0.8, R_kura ≈ 0.55 ± 0.05 across κ_C ∈ [0.00, 0.30], dropping to 0.45 at κ_C=0.50.
At ratio 0.2, R_kura drops monotonically from 0.52 at κ_C=0 to 0.30 at κ_C=0.50 — strong κ_C-sensitivity.

This is counter-intuitive: deep-coherent ratio 0.2 ought to give HIGHER instantaneous phase coherence than ratio 0.8. The explanation is that strong κ_C homogenizes C_mean, making the sign-flip gate on kappa_phase trigger more sharply and synchronously. At ratio 0.2, where phases were already deep-locked by κ_phase, the sharper attractive/repulsive cycles actively DE-synchronize the phase ensemble. At ratio 0.8 the phases weren't tightly locked to begin with, so the sharper cycling doesn't cost as much.

### 6. σ_n_ST flatness is universal (S107-P5 confirmed).
- Ratio 0.2: σ_n_ST min/max 2.68/3.29, CV = 0.080
- Ratio 0.8: σ_n_ST min/max 2.75/3.30, CV = 0.064

The switch-timing detector noise is ≈ 3.0 regardless of cell. This is sub-Poisson (expected √N scaling would give ~20% variation given N_sw varies 7×). σ_n_ST is a property of chunk-length clock noise, not event count.

## ρ_sig Separability (S107-P4 side analysis)

Using the S107 ratio-0.8 grid (3 κ_p × 5 κ_C), fit log(ρ_sig) to a rank-1 additive model: log(ρ) ≈ a[κ_p] + b[κ_C] + c.

```
ρ_sig_st grid (rows = κ_p, cols = κ_C, all at ratio 0.8):
κ_p\κ_C     0.00    0.05    0.15    0.30    0.50
0.15      0.0091  0.0203  0.0661  0.0875  0.0320
0.30      0.0083  0.0224  0.0751  0.1710  0.0696
0.50      0.0051  0.0129  0.1232  0.2028  0.1052
```

- Log-space R² = 0.930. Max residual 0.47 (factor of ~1.6× in log).
- Row ratios ρ(κ_p=0.50)/ρ(κ_p=0.30) across κ_C: {0.61, 0.57, 1.64, 1.19, 1.51}. **3× variation**.
- At κ_C ∈ {0.00, 0.05}: BIGGER κ_p gives SMALLER ρ_sig (ratio < 1).
- At κ_C ≥ 0.15: bigger κ_p gives BIGGER ρ_sig (ratio > 1).

**ρ_sig is not factorizable.** There is a sign reversal: without C-coupling, stronger κ_p actively *degrades* per-event signal density. This matches S107's "ST R_coh drops with κ_p at κ_C=0 (slope −0.30)" observation and identifies the mechanism as per-event signal density reduction, not an event-count effect.

Physical reading: κ_C and κ_p interact through a gated structure. When κ_C = 0, each C is an independent bistable; stronger κ_p creates stronger phase-lock cycles that drive all C's to swing in-phase, which *cancels* rather than reinforces the signal density when projected onto the switch-timing detector. When κ_C > 0, the C-field homogenizes through κ_C, and κ_p's phase-lock cycles now produce a genuinely coherent switch response.

## What This Closes / Updates

### S107-P3 answered (partial universality)
Ridge position in κ_C is universal to within a fraction of a grid step (RAW) or ~1/3 grid step (ST). Ridge HEIGHT depends strongly on regime: deep-coherent ratio 0.2 loses 31% of peak RAW R_coh compared to near-desync ratio 0.8.

### S107-P4 answered (not factorizable)
ρ_sig(κ_p, κ_C) is not multiplicatively separable. Rank-1 log fit R²=0.93 with 1.6× residuals and a sign-reversal around κ_C=0. κ_p's effect on ρ_sig is κ_C-gated.

### S107-P5 progressed (σ_n_ST flatness universal)
σ_n_ST ≈ 3.0 with CV ~7–8% across cells at both ratios. Confirms σ_n_ST is a chunk-length property of the detector, not an event-count property.

### S106/S107 retroactive read
S107 concluded that κ_C and κ_p have "separable roles". Revised: κ_C's role (setting N_sw and the ridge location) is genuinely separable from κ_p. But κ_p's role (modulating ρ_sig) is NOT separable from κ_C — the two interact with a sign reversal at κ_C=0. S107's "κ_p is a gain on ρ_sig" is approximately true only at κ_C ≳ 0.15.

## Residual Open Questions

- **S108-P1** (ridge locus across wider ratio sweep): does κ_C* converge/diverge as ω/κ_p crosses 1.0 (the Kuramoto cliff)? Ratio 0.8 → 0.2 shifts ST κ_C* by −0.06. Extrapolating, ratio 1.5 (post-cliff) should shift it rightward. Sweep ratio ∈ {0.2, 0.5, 0.8, 1.1, 1.5} at κ_p=0.30, κ_C ∈ {0.15, 0.20, 0.25, 0.30, 0.35}.

- **S108-P2** (ridge height vs ratio): R_peak(ratio) is max near ratio 0.8. Is ratio 0.8 truly optimal, or is there a sweet spot in [0.5, 1.0]? Sweep ratio at κ_C=0.27 (ridge), κ_p=0.30.

- **S108-P3** (mechanism for height drop): is the ratio-0.2 signal-density collapse due to phase-lock over-homogenization? Test: at ratio 0.2 κ_C=0.30, record the distribution of per-oscillator phase relative to mean — if all four phases are within ±5° of each other while at ratio 0.8 they span ±45°, the mechanism is confirmed.

- **S108-P4** (ST ceiling): ST R_coh = 0.83 at ratio 0.8 seems close to a detector ceiling. Does sweeping κ_p up (S107-P2) at the ridge push ST past 0.9? Or is 0.8+ a structural limit of ST in this N=4 system?

### Still untouched from S107

- S107-P1 (ridge fine structure): pin down peak κ_C* to ±0.01 with tighter grid.
- S107-P2 (ridge height saturation): test κ_p ∈ {0.75, 1.0, 1.5} at κ_C=0.30. (S108-P2 overlaps.)
- S106-P5 / N-scaling of ridge: κ_C*(N) for N ∈ {8, 16, 32}.

## Predictions

- **S108-P5**: at ratio 0.2, the RAW detection floor (A_min) is ~30% higher than at ratio 0.8 for comparable chunk counts. Direct test: sweep A ∈ {0.10, 0.20, 0.30} at ratio 0.2 κ_C=0.15 and compute the A_min via R_coh → z_det scaling.

- **S108-P6** (phase-ensemble spread): per-simulation std of (phase_k − mean(phase_k)) should be smaller at ratio 0.2 than at ratio 0.8. Predicting: std ≈ 5° at ratio 0.2, ≈ 25° at ratio 0.8 when both are away from the Kuramoto cliff. If so, this directly explains the ρ_sig asymmetry.

## Methodological Notes

1. When comparing ridges across regimes, the peak LOCATION and peak HEIGHT are independent findings. This session shows they can move separately — location is approximately universal, height is not. Report both; don't collapse to a single "is the ridge the same" question.

2. The S105-recycled r02_k030 cell was run with identical protocol (8 seeds × 50 chunks × 40 k steps × 0.1 s dt). Recycling saved ~7 min but required explicit cross-check that R_kura and σ_n_ST matched the S108-style cells (they do).

3. Matplotlib/numpy version mismatch on Thor prevented generating plots this session. Analyzer tables were the primary output.
