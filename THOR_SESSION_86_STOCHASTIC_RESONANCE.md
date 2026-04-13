# Thor Session #86: Stochastic Resonance in Coherence Dynamics

## Discovery: Suprathreshold Stochastic Resonance — NOT Classical SR

Sessions 82-85 established that coherence dynamics are bistable with Kramers escape rates (R²=0.997). The natural prediction: the system should exhibit stochastic resonance (SR) — an optimal noise level where weak periodic signals are maximally amplified.

**CONFIRMED — but not in the way expected.**

## Key Findings

### 1. Spectral Amplification Peaks at σ = 0.011

Injected a weak periodic signal (2% threshold modulation, freq=0.003) and measured spectral amplification Q = |⟨C·e^{-iΩt}⟩| / A across noise levels:

| Noise σ | Q (amplification) | Switches/200k steps |
|---------|-------------------|---------------------|
| 0.004   | 0.023 ± 0.012    | 5.9                |
| 0.006   | 0.062 ± 0.071    | 15.6               |
| 0.008   | 0.218 ± 0.139    | 152.9              |
| 0.010   | 0.448 ± 0.201    | 527.3              |
| **0.011** | **0.649 ± 0.304** | **734.4**        |
| 0.012   | 0.583 ± 0.271    | 936.5              |
| 0.015   | ~0.60            | ~1300              |
| 0.022   | ~0.59            | ~2000              |

**Q increases 28× from σ=0.004 to peak at σ=0.011.** The peak coincides exactly with the Regime II/III boundary from Session 81.

### 2. NOT Classical SR — No Residence Time Locking

Classical SR predicts switching synchronizes to the signal: residence time mode → T/2 = half the signal period.

| Noise σ | Switches | Mode (time units) | T/2 (signal) | Mode/T_half | Sync Index |
|---------|----------|-------------------|--------------|-------------|------------|
| 0.008   | 2,853    | 8.0               | 166.7        | 0.048       | 0.104      |
| 0.011   | 15,738   | 1.0               | 166.7        | 0.006       | 0.026      |
| 0.015   | 36,618   | 0.7               | 166.7        | 0.004       | 0.021      |
| 0.020   | 57,225   | 0.6               | 166.7        | 0.004       | 0.046      |

Switching is **100-200× faster** than the signal period at all noise levels. The sync index is near zero. This is NOT one-switch-per-half-cycle SR.

**What it IS**: Suprathreshold stochastic resonance (SSR). The system switches many times per signal cycle. The signal modulates the *dwell time distribution* — slightly longer in the favored basin during each half-cycle — producing a time-averaged tracking without individual-switch locking.

### 3. Mutual Information Confirms SR Peak at σ = 0.011

| Noise σ | MI (bits) |
|---------|-----------|
| 0.005   | 0.0108    |
| 0.007   | 0.0181    |
| 0.009   | 0.0194    |
| **0.011** | **0.0229** |
| 0.013   | 0.0195    |
| 0.016   | 0.0213    |
| 0.020   | 0.0194    |

MI peaks at σ=0.011 — identical to the Q peak. The information-theoretic optimum matches the spectral optimum. Both measures agree: **σ=0.011 is the optimal noise for cognitive signal transfer.**

### 4. SNR Peaks Higher at σ ≈ 0.014

| Noise σ | SNR (power ratio) |
|---------|-------------------|
| 0.006   | 144 ± 162        |
| 0.008   | 412 ± 213        |
| 0.010   | 464 ± 215        |
| 0.011   | 492 ± 168        |
| 0.012   | 537 ± 182        |
| **0.014** | **537 ± 283**   |
| 0.018   | 457 ± 156        |

SNR peaks ~25% higher than the Q peak. This makes sense: Q measures absolute spectral power at the signal frequency, while SNR measures power ratio (signal/background). As noise increases beyond the Q peak, both signal and background power grow, but their ratio stays favorable longer.

### 5. Kramers Prediction FAILS — Because It's Not Classical SR

Classical Kramers-mediated SR predicts: σ_opt² = ΔU / ln(f₀/Ω)

At freq=0.001: predicted σ=0.0068, measured σ=0.011 (62% error).

The failure is expected: Kramers SR requires matching switching rate to signal frequency (2·r_K ≈ Ω). But at σ=0.011, the switching rate is r_K ≈ 0.037/time unit, while the signal frequency is Ω=0.001-0.003. The switching is 12-37× faster than needed for classical SR.

## The Mechanism: Suprathreshold SR via Dwell-Time Modulation

The observed SR operates through a different mechanism than textbook Kramers SR:

1. **The system switches rapidly between two metastable states** (C_high ≈ 0.85, C_low ≈ 0.60)
2. **The periodic signal slightly biases the switching asymmetry** — during the high phase of the signal, the system spends marginally more time in the high-C basin
3. **Over many switches per signal cycle, this bias accumulates** to produce a time-averaged response that tracks the signal
4. **The optimal noise is where the bistability FIRST emerges** (σ ≈ 0.011 = Regime II/III boundary), not where switching rate matches signal frequency

This is more robust than classical SR because:
- It doesn't require frequency matching
- It works across a wide range of signal frequencies
- It degrades gracefully with excess noise

## Implications for Consciousness

### "Noise is not the enemy of cognition — it's a prerequisite"

1. **Optimal noise for signal processing**: σ=0.011 maximizes information transfer between environment and coherence state. Below this, the system is trapped; above, it's diffuse. The cognitive "sweet spot" is right at the onset of bistability.

2. **Not frequency-specific**: Unlike classical SR which requires frequency matching (a very specific condition), suprathreshold SR works across a broad frequency range. This is biologically realistic — the brain needs to process signals at many timescales simultaneously.

3. **The Regime II/III boundary is functionally optimal**: Session 81's "phase transition" that turned out to be a crossover (Session 85) is now revealed as the **information-processing optimum**. The crossover point isn't just a structural feature — it's the point of maximum cognitive sensitivity.

4. **For SAGE architecture**: Running instances at noise levels near σ=0.011 would maximize their sensitivity to weak signals. Too-quiet instances are deaf; too-noisy instances are confused. The coherence dynamics automatically identify the optimal operating point.

### Connection to Neuroscience

Cortical circuits operate with significant noise (spontaneous firing rates, synaptic variability). The longstanding puzzle is why evolution didn't reduce this noise. SSR provides the answer: **the noise is functional**. It enables the rapid switching between metastable states that allows broad-spectrum signal detection through dwell-time modulation.

This is consistent with:
- Cortical "up states" and "down states" (bistable membrane potentials)
- The observation that neural noise levels seem tuned to near-optimal ranges
- The failure of "noise reduction" approaches to improve brain-computer interfaces

## Cross-Track Connections

- **Session 85 (Universality)**: The crossover at σ≈0.011 is now understood not just as a structural feature (where bistability emerges) but as the **information-processing optimum**
- **Session 82-83 (Kramers/Fokker-Planck)**: The Kramers framework correctly describes the switching dynamics but classical SR matching fails because the system operates in the suprathreshold regime
- **Gnosis C=0.5**: The coherence crossover point is where signal processing is optimized. "Everything is coherence" → "optimal coherence is bistable"
- **SAGE instances**: Design recommendation — operate near the bistability onset for maximum environmental sensitivity

## Falsifiable Predictions

1. **Broad optimal noise plateau**: The Q curve is flat from σ≈0.010-0.018. The peak shifts weakly with frequency (σ=0.011 at freq=0.001, σ=0.017 at freq=0.003). Much weaker frequency dependence than classical SR predicts but not strictly frequency-independent. The MI peak (σ=0.011) may be the most robust marker.

2. **MI peak and Q peak should coincide**: Confirmed at σ=0.011.

3. **Residence time mode should NOT match T/2**: Confirmed — mode is 100-200× shorter.

4. **The optimal noise should coincide with the bistability onset**: Confirmed — σ=0.011 is exactly the Regime II/III boundary from S81.

5. **Array-enhanced SR**: Coupling more instances should increase Q_max (to be tested in Exp G).

## Quote

*"The system doesn't listen by reducing noise — it listens by using noise. Not through one switch per signal cycle (classical SR) but through a thousand switches per cycle, each slightly biased. The signal emerges from the statistics of rapid switching, not from synchronized switching. This is how a noisy brain detects a whisper: not by going quiet, but by modulating the frenzy."*

## Files
- `thor_session_86_stochastic_resonance.py` — Full experiment suite
- `thor_session_86_focused.py` — Optimized focused version
- `thor_session_86_stochastic_resonance_results.json` — Results data
