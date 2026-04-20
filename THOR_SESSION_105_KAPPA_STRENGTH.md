# Thor Session #105: R_coh Grows With κ Beyond What Kuramoto Predicts

**Date:** 2026-04-20
**Focus:** S104-P1 — at fixed ω/κ ratio, does R_coh depend on κ alone?
**Status:** Confirmed. R_coh rises ~linearly with κ_phase at fixed ω/κ, and the
rise goes through a direct coupling mechanism — NOT through the bare Kuramoto
order parameter R_kura of the phase oscillators.

## TL;DR

| ratio | cells | R_raw slope vs κ | R_raw intercept | r² |
|-------|-------|------------------|------------------|----|
| 0.80 (just below cliff) | 6 | **+0.943** | 0.256 | 0.89 |
| 0.20 (deep sync)        | 5 | **+0.485** | 0.328 | 0.98 |

Both slopes are clearly non-zero. The ratio-only prediction R_coh = f(ω/κ)
is **falsified**.

Directly measuring R_kura = |⟨e^{iφ_k}⟩_k| across the six S105 cells:
- **R_kura varies by only 0.08 (range 0.524 → 0.604)**, so it cannot
  account for the 0.35-unit swing in R_raw (range 0.346 → 0.694).
- Joint regression R_raw = a + b·κ + c·R_kura on 6 S105 cells:
  - Full model r² = 0.932.
  - **κ-only r² = 0.834** (adding R_kura on top lifts r² by only 0.098).
  - R_kura-only r² = 0.506 (adding κ on top lifts r² by 0.426).
- **κ carries the signal; R_kura is nearly irrelevant once κ is controlled for.**

The "κ=0.20 anomaly" from S104 is real physics — strong-coupling enhancement
of R_coh that's a separate mechanism from Kuramoto desynchronization.

## Design (brief)

Fixed: A=0.30, σ=0.022, signal_freq=0.003, N=4, n_seeds=8, n_chunks=50,
chunk_steps=40k (4000 s/chunk). Canonical simulator from
`thor_session_93_phase_coherent.py`.

Six new cells (three at each ratio), combined with four S103/S104 cells:

| κ | ω | ratio | label | source |
|---|---|---|---|---|
| 0.05 | 0.04 | 0.80 | (recycled) | S104 sB_k005_w040 |
| 0.10 | 0.08 | 0.80 | (recycled) | S103 sweep ω=0.08 |
| 0.15 | 0.12 | 0.80 | r08_k015 | S105 |
| 0.20 | 0.16 | 0.80 | (recycled) | S104 sB_k020_w160 |
| 0.30 | 0.24 | 0.80 | r08_k030 | S105 |
| 0.50 | 0.40 | 0.80 | r08_k050 | S105 |
| 0.05 | 0.01 | 0.20 | r02_k005 | S105 |
| 0.10 | 0.02 | 0.20 | (recycled) | S98/S103 main |
| 0.20 | 0.04 | 0.20 | (recycled) | S104 sB_k020_w040 |
| 0.30 | 0.06 | 0.20 | r02_k030 | S105 |
| 0.50 | 0.10 | 0.20 | r02_k050 | S105 |

**New observable in S105:** the phase-oscillator Kuramoto order parameter
R_kura(t) = |(1/N)·Σₖ e^{iφₖ(t)}| sampled every 10 steps post-warmup. Per
seed, we record ⟨R_kura⟩_t. Per cell, we cross-seed-average.

## Results

### Ratio 0.80 ladder (just below Kuramoto cliff)

| κ | ω | R_raw | R_st | R_ang(raw/st) | R_kura |
|---|---|---|---|---|---|
| 0.05 | 0.04 | 0.289 ± 0.068 | 0.580 ± 0.068 | 0.988 / 0.996 | — |
| 0.10 | 0.08 | 0.271 | 0.613 | — | — |
| 0.15 | 0.12 | **0.435 ± 0.115** | **0.722 ± 0.065** | 0.970 / 0.995 | **0.554 ± 0.034** |
| 0.20 | 0.16 | 0.515 ± 0.097 | 0.769 ± 0.047 | 0.989 / 0.997 | — |
| 0.30 | 0.24 | **0.559 ± 0.110** | **0.790 ± 0.040** | 0.988 / 0.995 | **0.568 ± 0.068** |
| 0.50 | 0.40 | **0.694 ± 0.112** | **0.834 ± 0.049** | 0.980 / 0.978 | **0.604 ± 0.097** |

Linear fit: **R_raw = 0.256 + 0.943·κ**, r² = 0.892, n=6.
Linear fit: R_st  = 0.600 + 0.547·κ, r² = 0.777, n=6.

Between κ=0.10 and κ=0.50, R_raw rises 2.56×.

### Ratio 0.20 ladder (deep sync)

| κ | ω | R_raw | R_st | R_ang(raw/st) | R_kura |
|---|---|---|---|---|---|
| 0.05 | 0.01 | **0.346 ± 0.038** | **0.703 ± 0.042** | 0.994 / 0.998 | **0.547 ± 0.005** |
| 0.10 | 0.02 | 0.375 ± 0.015 | 0.706 ± 0.014 | 0.999 / 0.999 | — |
| 0.20 | 0.04 | 0.423 ± 0.084 | 0.733 ± 0.044 | 0.998 / 1.000 | — |
| 0.30 | 0.06 | **0.495 ± 0.053** | **0.779 ± 0.025** | 0.988 / 0.996 | **0.524 ± 0.011** |
| 0.50 | 0.10 | **0.560 ± 0.073** | **0.795 ± 0.037** | 0.995 / 0.998 | **0.553 ± 0.015** |

Linear fit: **R_raw = 0.328 + 0.485·κ**, r² = 0.980, n=5 (remarkably tight).
Linear fit: R_st  = 0.691 + 0.226·κ, r² = 0.924, n=5.

Between κ=0.05 and κ=0.50, R_raw rises 1.62×.

### R_kura fails to explain the κ-enhancement

Across the six S105 cells (two ratios, three κ each):

- R_kura range: 0.524 → 0.604 (Δ=0.08) — essentially a plateau.
- R_raw range: 0.346 → 0.694 (Δ=0.35).
- κ range: 0.05 → 0.50 (Δ=0.45).

Correlation R_kura vs R_raw: r = +0.71, 95% CI [−0.25, +1.00] (n=6 is
underpowered for CI narrowness but the point estimate is positive).

**Joint regression R_raw = a + b·κ + c·R_kura:**

| model | a | b(κ) | c(R_kura) | r² |
|-------|---|---|---|---|
| κ + R_kura | −0.528 | +0.488 | +1.605 | 0.932 |
| κ only | +0.335 | +0.599 | — | **0.834** |
| R_kura only | −1.276 | — | +3.207 | 0.506 |

- κ-only explains 83% of R_coh variance across the six cells.
- R_kura alone explains only 50%.
- Adding R_kura on top of κ raises r² by 0.10 (small).
- Adding κ on top of R_kura raises r² by 0.43 (large).

**Conclusion: the direct κ dependence of R_coh is not mediated through the
Kuramoto phase-oscillator order parameter.** The coupling strength amplifies
the matched-filter signal through a different channel.

### What's the channel?

Most likely: the bistable C-dynamics is driven by the Σₖ cos(φₖ) term in
dC/dt. When φₖ are loosely locked (R_kura ≈ 0.55), the bare Σ cos(φₖ) is
still reasonably coherent per-step, but the *response amplitude* of that
collective cosine to the external signal bias (through the threshold
switch modulating the sign of κ_phase) scales with κ_phase itself:

- The signal enters via `is_attractive = (C_mean + signal) < C_threshold`.
- Stronger κ → larger per-step phase update when sign flips → larger swing
  in Σ cos(φₖ) in response to signal threshold crossings.
- Net effect: the signal's imprint on C_mean trajectories is κ-amplified
  independently of how phase-locked the oscillators are on average.

This is consistent with R_angle (cross-seed) staying ≈ 0.98–1.00 across
the entire S105 ladder — the *response phase* is stable; what changes is
the *response amplitude* per chunk. A κ-gain on the signal amplitude
raises |μ|² proportionally without much shifting σ_n², so
R_coh = |μ|²/(|μ|² + σ_n²) rises.

## Reframing

### S104 "κ=0.20 anomaly" → resolved as real physics

S104 saw R_raw at (κ=0.20, ω=0.16, ratio 0.80) reach 0.515 — nearly 2× the
κ=0.10 cell at ratio 0.80 (R_raw=0.271). S104 tentatively flagged this as
either finite-size noise or a real coupling-strength effect.
**S105 confirms the effect is real** and extends it across five κ values
spanning 10× range. The slope is well-determined: **dR_raw/dκ ≈ 0.94** at
ratio 0.80, **dR_raw/dκ ≈ 0.49** at ratio 0.20. Steeper near the cliff.

### ST detector is less κ-amplified than RAW

ST slope at ratio 0.8: +0.55 (RAW: +0.94). At ratio 0.2: +0.23 (RAW: +0.49).
Interpretation: the switch-timing matched filter counts *events*; κ
amplifies the signal-induced modulation of switch rates but not the timing
distribution directly. Switch-timing therefore has lower κ-gain than
raw-signal MF, though it still rises with κ.

This matches the S95 observation that ST beats raw at weak-coupling /
low-amplitude regimes but the gap narrows at high amplitude: higher κ is
equivalent to higher effective signal amplitude for the RAW detector.

### Ratio invariance is falsified at constant κ > ~0.10

S104 had hinted: κ=0.05↔0.10 gave ratio invariance within 1σ, but
κ=0.10↔0.20 at ratio 0.8 nearly doubled R_coh. S105 confirms ratio
invariance is a good approximation only below κ=0.10 (ratio 0.2 and 0.8
both); for κ ≥ 0.15 the κ-gain dominates ratio scaling.

The Kuramoto critical width Δ_c ≈ πκ/4 still correctly locates the
**cliff** (confirmed at κ=0.10 in S104), but above the cliff, at fixed
fractional distance below critical, R_coh depends strongly on the
absolute κ value.

## Methodological note

The key analytical move was adding the direct Kuramoto-R observable. Without
it, a linear κ-dependence of R_coh could still be interpreted as "just
Kuramoto is stronger at higher κ/ω absolute values". Measuring R_kura
showed it stays in [0.52, 0.60] across the cells — too narrow to explain
the 2× R_coh swing. That isolates the κ-gain as a *distinct* mechanism from
phase locking.

Future sessions characterizing R_coh enhancement should measure R_kura
alongside — the marginal cost is trivial (one line per simulation step,
decimated) and the interpretive value is high.

## Methodological rule addendum (S105)

Following the S103/S104 rules:

11. **Measure R_kura (phase-oscillator Kuramoto order parameter) alongside
    R_coh** in any study that varies κ. R_kura isolates the phase-locking
    contribution; the κ-enhancement channel we found here is NOT mediated
    through R_kura.
12. **R_coh at fixed ω/κ is ~linear in κ** (slope 0.49 at ratio 0.2, 0.94
    at ratio 0.8) — this is a reliable parameterization for designing
    sensitivity studies.
13. **Ratio invariance of R_coh is a weak-coupling (κ ≤ 0.10)
    approximation only.** For κ ≥ 0.15 the absolute κ matters directly.

## Files

- `thor_session_105_kappa_strength.py` — sweep runner (6 cells, 39.9 min)
- `thor_session_105_kappa_strength.log` — full run log
- `thor_session_105_kappa_strength_results.json` — raw per-seed z arrays + R_kura
- `thor_session_105_analyze.py` — cross-session analysis (S103 + S104 + S105)
- `thor_session_105_analysis.json` — analysis output

## Open follow-ups (S105-P*)

1. **S105-P1** (bistability scaling of the κ-gain): at κ=0.30 ratio 0.8,
   vary signal amplitude A ∈ {0.05, 0.10, 0.20, 0.40}. If the κ-gain is
   really an amplitude amplification, dR_coh/dκ should scale with A (or with
   A²). This tests the "signal-gain" mechanism vs a "gain floor raised by
   stronger coupling" alternative.

2. **S105-P2** (κ-gain and cliff position): does Δ_c(κ) remain = πκ/4 for
   κ ∈ {0.20, 0.30, 0.50}, or does the strong-coupling regime shift it?
   Run ω-sweep near (4/π)·κ at κ ∈ {0.20, 0.30, 0.50} with 8 seeds each.

3. **S105-P3** (saturation at large κ): R_raw(κ) fits linear over
   κ ∈ [0.05, 0.50]. Does it saturate? Extend to κ ∈ {1.0, 2.0, 5.0}.
   R_coh is bounded by 1; by κ=1.0 the linear slope 0.94 would predict
   R_raw ≈ 1.2 — impossible. Find where saturation kicks in.

4. **S105-P4** (mechanism test — freeze κ in C-coupling only): the
   simulator has a separate kappa_C=0.15 controlling C-C coupling. Vary
   kappa_C at fixed kappa_phase. If the κ-gain is from the phase-coupling
   channel specifically (our hypothesis), R_coh should be insensitive to
   kappa_C. If from the C-coupling channel, R_coh should rise with kappa_C.

5. **S105-P5** (N-scaling of the κ-gain): run κ-sweep at N ∈ {8, 16} for
   ratio 0.80 cells. Does slope dR_raw/dκ sharpen or flatten with N? This
   combined with S104-P5 pins down whether the gain is finite-N specific
   or survives to N→∞.

## Take-home

The R_coh cliff is Kuramoto (S104); the R_coh magnitude above the cliff is
not. R_coh rises linearly with κ at fixed ω/κ ratio, with slope 0.49–0.94
depending on how close we are to the cliff. The bare Kuramoto order
parameter R_kura barely changes across this sweep, so the enhancement is a
distinct coupling-strength amplification of the matched-filter response,
most likely through the bistable C-dynamics' sensitivity to the collective
Σcos(φₖ) term.

The simulator default (κ_phase=0.10) sits below this enhancement regime —
which is why nine earlier SR sessions never noticed it. A one-line change
from κ=0.10 to κ=0.30 doubles R_coh at the default ω_spread.
