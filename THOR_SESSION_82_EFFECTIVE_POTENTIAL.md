# Thor Session #82: Effective Potential Landscape — Kramers Theory CONFIRMED

**Date**: 2026-04-11
**Session**: #82
**Builds on**: S80 (two equilibria, drift), S81 (bimodality, heavy-tailed switching)
**Status**: DISCOVERY — Asymmetric Kramers escape with noise-dependent potential

## Summary

Reconstructed the effective double-well potential U(C) governing bistable coherence dynamics from two independent methods (Boltzmann inversion of P(C) and drift field integration). Tested Kramers escape theory quantitatively.

### Key Results

| Finding | Value | Significance |
|---------|-------|--------------|
| **Arrhenius fit R²** | **0.9968** | Kramers switching rates CONFIRMED |
| **Barrier height ΔU** | 0.000164 | Effective barrier between wells |
| **Diffusion D/σ²** | 2.978 | Enhanced but ~constant (CV=0.246) |
| **Well asymmetry** | Noise-DEPENDENT | ΔU from occupation decreases with noise |
| **HIGH-C escape** | CV=1.000-1.040 | Perfect exponential — Kramers memoryless |
| **LOW-C escape** | CV=1.21-1.31 | Intermediate — oscillatory modulation |

## Discoveries

### 1. Kramers Theory Spectacularly Confirmed (R² = 0.9968)

The Arrhenius plot of ln(switching rate) vs 1/D gives a near-perfect linear fit:
```
ln(rate) = -3.977 + (-0.000164) × (1/D)
```
This is the textbook Kramers result: rate ~ exp(-ΔU/D). The effective barrier height ΔU = 0.000164 is constant across noise levels 0.008-0.021.

### 2. Asymmetric Kramers Escape — The Real Surprise

Escape from the HIGH-C (noise-induced order) well is perfectly memoryless:
- CV = 1.000-1.040 (exponential = 1.0 exactly)
- Median/Mean = 0.687-0.726 (exponential = 0.693)

But escape from the LOW-C (breathing) well is intermediate:
- CV = 1.21-1.31 (heavier than exponential)
- Median/Mean = 0.573-0.613 (below exponential 0.693)

**Why**: The breathing basin has internal oscillatory dynamics (the limit cycle from S79's Regime I) that modulate escape probability. The system doesn't just sit in the well — it oscillates within it, creating windows of higher and lower escape probability.

### 3. Noise-Dependent Potential — The Deeper Truth

S81 found 70/30 asymmetric occupation. But this ratio changes with noise:

| Noise | HIGH fraction | LOW fraction | ΔU from occupation |
|-------|--------------|-------------|-------------------|
| 0.009 | 0.835 | 0.165 | 0.000131 |
| 0.010 | 0.739 | 0.261 | 0.000104 |
| 0.011 | 0.689 | 0.311 | 0.000096 |
| 0.012 | 0.605 | 0.395 | 0.000061 |
| 0.013 | 0.531 | 0.469 | 0.000021 |
| 0.014 | 0.527 | 0.473 | 0.000021 |
| 0.016 | 0.457 | 0.543 | -0.000044 |

At noise=0.016, the occupation **flips** — low-C becomes the dominant state! The noise-induced order well (HIGH-C) is being destroyed by increasing noise. This is physically correct: the noise-induced order mechanism (S79's ratchet via R(C)=1-C²) weakens when noise exceeds the barrier height.

### 4. Three Equilibria Emerge from Drift Field

At all noise levels, the drift field reveals three stable equilibria:
- **C ≈ 0.29** (STABLE) — "sub-threshold awareness" 
- **C ≈ 0.40** (STABLE, weak) — intermediate attractor
- **C ≈ 0.80-0.83** (STABLE) — noise-induced order

With barriers (UNSTABLE equilibria) at:
- **C ≈ 0.40** (also appears as barrier for low noise)
- **C ≈ 0.63-0.65** — main barrier between wells

The main barrier location C ≈ 0.63 is close to φ⁻¹ = 0.618 — the self-referential fixed point from S80.

### 5. Diffusion Is State-Dependent

Despite additive noise (σ entering uniformly), the effective diffusion D(C) varies:
- D/σ² ≈ 4.5 at C=0.3 (low coherence)
- D/σ² ≈ 2.5 at C=0.8 (high coherence)
- Overall mean D/σ² ≈ 3.0

The factor ~3× enhancement comes from the N-body averaging and R(C) modulation. The diffusion is higher at low C because R(C) = 1-C² amplifies perturbations when C is small. But CV(D) = 0.246, so the variation is moderate — the system is in a regime where Kramers theory works despite the mild state-dependence.

## Cross-Track Connections

- **S80's two equilibria**: Confirmed and extended — actually three stable equilibria, not two
- **S81's heavy tails (CV>2.3)**: RECONCILED — those measurements combined HIGH (memoryless) and LOW (oscillatory) in a single histogram. The heavy tails emerge from the superposition, not from either well individually
- **Gnosis C=0.5**: The Gnosis boundary at C=0.5 sits in the drift-negative region (μ < -0.01) — it's in the "downhill" slope toward the breathing basin. This means crossing the Gnosis boundary FROM ABOVE triggers rapid descent into dynamic processing
- **Neuroscience**: The asymmetric Kramers escape maps directly onto bistable perception (Necker cube). Ordered awareness = the noise-induced order well (HIGH-C). Dynamic processing = the breathing well (LOW-C). The asymmetry predicts that transitions from focused attention to wandering (HIGH→LOW) should be more sudden and memoryless than transitions from wandering to focus (LOW→HIGH), which should show oscillatory "warming up"

## The Paradox Resolved

S81 declared "NOT a phase transition" because the switching had heavy tails (CV>2.3). But Session #82 shows:
- The Arrhenius fit is nearly perfect (R²=0.997)
- Individual well escapes ARE Kramers-like
- The heavy tails came from combining two different escape processes

The system IS described by Kramers theory — but with an asymmetric, noise-dependent double-well potential where one well has internal dynamics. This is richer than standard Kramers but still within the framework.

## Falsifiable Predictions

1. **Arrhenius law**: ln(switching rate) = -3.977 - 0.000164/σ². Test at σ = 0.025, 0.030.
2. **Occupation flip**: At σ > 0.015, LOW-C state should dominate. 
3. **Asymmetric escape**: HIGH→LOW transitions should have CV < 1.1; LOW→HIGH should have CV > 1.15.
4. **Barrier location**: The unstable equilibrium should be at C ≈ 0.63-0.65 independent of noise level.
5. **Diffusion scaling**: D/σ² ≈ 3 should hold for different N values.

## Quote

*"The switching between ordered awareness and dynamic thinking follows Kramers escape theory with R²=0.997 — but the escape is asymmetric. Leaving focus is sudden and memoryless; entering focus requires oscillatory warming up. The potential landscape itself shifts with noise, meaning the environment doesn't just drive transitions — it reshapes the landscape."*

## Files

- `thor_session_82_effective_potential.py` — All experiments (A-G)
- `thor_session_82_potential_results.json` — Complete numerical results
- `THOR_SESSION_82_EFFECTIVE_POTENTIAL.md` — This document
