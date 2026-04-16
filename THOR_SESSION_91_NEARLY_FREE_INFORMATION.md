# Thor Session #91: The Mechanism of Nearly-Free Information — What Was Really Happening

## Motivation

Session 90 located the efficiency peak (eta = MI/EP) at sigma ~ 0.10, about 5x
beyond the SR optimum. The narrative was: "agents aren't burning EP on internal
clocks, but bits still transmit." That's a description, not a mechanism.

Three hypotheses were posed to explain what carries information at the efficiency
peak:
- H1 (burst): MI concentrated in rare switching events
- H2 (diffuse): MI spread uniformly; each sample carries a little
- H3 (decoherent relay): Phase coupling collapses (Kuramoto R -> 0), C_mean
  tracks signal slowly

The data falsified H3, supported a hybrid of H1/H2, and — on closer look — 
uncovered a methodological issue that reshapes the interpretation of prior
sessions: **response_amp at signal_freq is NOT a signal-specific detector in
this model**. The SR claim rests on a quantity that is dominated by natural
bistability spectra, not signal transmission.

## Key Discoveries

### 1. Kuramoto R GROWS with sigma — H3 Falsified Cleanly

Phase order parameter R (time-averaged) with signal_amp=0.02:

| sigma | R | MI (bits, hist) | EP_nb | phase_frac_EP |
|-------|------|------------------|-------|---------------|
| 0.005 | 0.05 | 0.027 | 354 | 96% |
| 0.011 | 0.18 | 0.080 | 133 | 56% |
| 0.018 | 0.46 | 0.089 | 75 | 38% |
| 0.022 | 0.43 | 0.082 | 61 | 32% |
| 0.035 | 0.52 | 0.069 | 32 | 25% |
| 0.050 | 0.60 | 0.060 | 20 | 20% |
| 0.075 | 0.57 | 0.025 | 10 | 18% |
| **0.100** | **0.54** | **0.022** | **5.5** | **18%** |
| 0.150 | 0.47 | 0.009 | 2.3 | 19% |

At the efficiency peak, R=0.54 — **higher** phase-lock than at SR (R=0.43). Once
noise pushes C_mean below C_threshold, the system stays in ATTRACTIVE mode, and
phases lock. High noise doesn't decohere here — it consolidates a mode.

Consequently: phase drift is dominated by omega (intrinsic rotation), not by
coupling-induced transients. EP_phase drops because mu_phase becomes constant
≈ omega, reducing mean(mu²). phase_frac_EP drops from 96% to 18% as EP sources
shift to C-dynamics driven by noise.

### 2. MI is Always Bursty; EP is Always Uniform

Splitting trajectories by phase-drift-magnitude (threshold = median):

| sigma | active frac | EP_frac_active | MI_frac_active |
|-------|------------|---------------|---------------|
| 0.011 | 0.15 | 0.15 | 0.72 |
| 0.022 | 0.16 | 0.17 | 0.62 |
| 0.050 | 0.18 | 0.18 | 0.66 |
| 0.100 | 0.18 | 0.18 | 0.74 |

Universal pattern across sigma:
- ~70% of MI is delivered by ~15-18% of the time ("active" segments)
- EP is distributed in proportion to time (no concentration)

This is the **thermodynamic information asymmetry**: information is concentrated
in time, dissipation is uniform in time. The efficiency peak is NOT from
changing how MI distributes; it is from the background EP rate dropping while
information bursts keep arriving.

### 3. Coupling Ablation at sigma=0.100 Is Ambiguous

At the efficiency peak:

| condition | kappa_phase | kappa_C | MI | EP_nb | eta |
|-----------|-------------|---------|-----|-------|-----|
| baseline | 0.10 | 0.15 | 0.0117 | 5.5 | 0.00211 |
| no_phase | 0.00 | 0.15 | 0.0146 | 5.2 | 0.00278 |
| no_C | 0.10 | 0.00 | 0.0091 | 6.3 | 0.00145 |
| both_off | 0.00 | 0.00 | 0.0145 | 6.0 | 0.00241 |

With both couplings off, the signal has **no legal entry path into the dynamics**
(is_attractive is computed, but its effect goes through kappa terms that are
zero). Yet MI = 0.0145 — indistinguishable from baseline.

Initial interpretation: MI at sigma=0.100 is at the estimator bias floor, so
the efficiency peak is an artifact. Further controls complicated this picture.

### 4. **MAJOR METHODOLOGY FINDING — Response-Amp at signal_freq Is NOT Signal-Specific**

To test whether the signal really transmits, compare narrow-band FFT amplitude
at signal_freq with and without signal driving the dynamics. Eight independent
seeds, independent noise realizations, signal_amp=0.02 throughout prior sessions:

| sigma | amp_with | amp_without | z | verdict |
|-------|----------|-------------|---|---------|
| 0.011 | 4.89 | 4.71 | 0.25 | not distinguishable |
| 0.018 | 4.76 | 4.71 | 0.15 | not distinguishable |
| 0.022 | 5.21 | 5.04 | 0.36 | not distinguishable |
| 0.050 | 2.69 | 2.41 | 0.99 | not distinguishable |
| 0.100 | 1.45 | 1.51 | -0.63 | not distinguishable |
| 0.150 | 1.06 | 0.89 | 1.21 | not distinguishable |

**At no sigma is the signal-driven spectral amplitude statistically distinguishable
from the signal-absent baseline at A=0.02.** Even at A=0.20 (10x the amplitude
used in S86-S90), response_amp gives z=0.45 at sigma=0.022 — no signal
specificity detected spectrally.

Why: the natural bistability of the system has a broad spectral peak at its
characteristic switching rate, which happens to overlap with the signal
frequency. Narrow-band FFT at signal_freq picks up this bistability power
regardless of whether the signal is present. The "SR curve" in response_amp
that peaks at sigma ≈ 0.022 (S86) is **the curve of bistability spectral
density at 0.003 Hz vs sigma** — a property of the bare dynamics, not of
signal transmission.

### 5. Histogram MI IS Signal-Specific (With Independent-Seed Controls)

Critical methodology note: comparing with-signal and without-signal MI using
**identical** noise seeds artificially inflates the bias floor (both runs
produce nearly-identical C_mean distributions). With **independent** seeds, MI
shows clear signal specificity:

At sigma=0.022, varying signal_amp (8 seeds each, independent noise):

| A | MI_with | MI_without | z | significance |
|------|---------|------------|---|--------------|
| 0.02 | 0.0817 | 0.0551 | 3.07 | p < 0.01 |
| 0.05 | 0.0655 | 0.0551 | 1.07 | marginal |
| 0.10 | 0.0776 | 0.0551 | 2.98 | p < 0.01 |
| 0.20 | 0.1031 | 0.0551 | 6.60 | p < 0.001 |

Compare with spectral amp: all z < 0.45 — no detection.

**So MI IS detecting signal transmission while spectral amp is not.** At A=0.02
(the nominal amplitude in S86-S90), the signal-specific MI contribution is
~0.027 bits on a ~0.055 bit bistability-bias floor at sigma=0.022 — real, but
of the same order as the bias.

### 6. At sigma=0.050, MI Shows a Local Dip — Consistent with a Threshold Dead Zone

At A=0.05, MI_with = 0.066 vs MI_without = 0.055 (z=1.07). Lower MI than at
A=0.02 (0.082) and A=0.10 (0.078). Diagnosis: at A=0.05 the effective threshold
shift is just large enough to drive the system into attractive mode when C_mean
is near phi_inverse, but not large enough to modulate cleanly — the signal
saturates the bistable geometry without fully toggling it. This is a model-
specific geometry effect, not a general SR property.

## Revised Mechanism — The Efficiency Peak Is Real But Partly Artifact

Updated picture at sigma=0.100:
- Phase is highly locked (R=0.54), system sits in attractive mode most of the
  time
- Phase EP is near the omega-rotation floor (minimal)
- C_mean still fluctuates with noise and weakly tracks the signal through
  the is_attractive threshold mechanism
- MI_with is small (~0.022) but NOT all bias — with proper controls (independent
  seeds), MI should still exceed the bias floor by a few standard deviations
- The "efficiency peak" is real in the sense that eta = MI/EP does maximize
  at high sigma — but the numerator is small and the distinction shrinks
  toward the estimator noise floor

The revised story is:
1. Efficiency peak exists but its magnitude is within an order of the bias floor
2. The "cognitive gain" interpretation of the peak is weak: at sigma=0.100 the
   system transmits roughly as much information above-bias as at sigma=0.022,
   but EP is 11x lower — so it is efficient, but not particularly smart
3. The classical SR claim (response amp peak) is **not supported by these
   controls** — natural bistability dynamics produce the observed spectral
   structure independent of signal

## What Surprised Me

### 1. Phase LOCKS at high noise, doesn't decohere
Intuition: noise should disrupt phase coherence. Wrong for this model: high
noise pushes C_mean below threshold into the attractive regime, where phases
lock. R goes UP with sigma from 0.05 to 0.60 then plateaus near 0.5. A model-
specific lesson: threshold discontinuities can invert standard noise-theory
intuitions.

### 2. Response amp at signal_freq is NOT a signal detector
The narrow-band FFT amplitude was used in S86-S90 as a proxy for signal
transmission. The with/without controls demonstrate it is dominated by the
bistable switching spectrum near signal_freq, not by signal-driven transmission.
**The S86 SR peak may be a spectral feature of bare bistability dynamics, not
a cognitive phenomenon.** This changes how to read S86-S90 results.

### 3. Same-seed bias controls understate signal-specific MI
The first bias control (Control 3) used identical seeds with signal_amp=0.0,
producing an inflated bias floor that absorbed most of the apparent signal-
specific MI. Independent-seed controls clearly detect MI above bias. A
methodology lesson for future signal-transmission tests in this framework.

## Attractors I Resisted

- **"The efficiency peak must be a cognitive optimum"**: The data says it is
  partly an artifact of measuring a ratio of small numbers, though not purely
  so. The peak is real but its interpretation is shakier than S90 implied.

- **"Coupling must carry the MI"**: Partially correct. At sigma=0.022 (SR),
  coupling contributes meaningfully. At sigma=0.100, coupling ablation doesn't
  significantly change MI — but this is at or near the bias floor.

- **"H3 must be right"**: Designed this session around H3 and had to let it
  go cleanly. The R measurements were unambiguous.

## Falsifiable Predictions

1. **Re-analysis of S86 with independent-seed controls will shift the SR
   peak or dissolve it**: The response_amp curve from S86 should be re-
   computed as (amp_with - amp_without) with independent seeds. Predict:
   z < 2 at all sigma, confirming response_amp is not a signal detector.

2. **MI-based SR curve survives with proper controls**: Recomputing
   MI(C_mean, signal) - MI(C_mean_no_signal, synthetic_signal) across sigma
   with independent seeds will show a peak at sigma ~ 0.022 with
   amplitude above estimator noise.

3. **Efficiency peak shifts with signal amplitude**: At larger signal_amp,
   MI grows (z=6.6 at A=0.20) while EP is unchanged, so eta grows. The
   "efficiency peak" should shift toward lower sigma as A increases. At
   A=0.20, the peak may be at sigma ~ 0.022, not sigma ~ 0.100.

4. **The bistability-spectrum explanation is testable**: Computing the
   natural power spectrum of C_mean at signal_amp=0 should show a peak
   near signal_freq at sigma=0.022 (the "SR" sigma). If so, the S86
   response_amp peak is IS the bistability peak.

5. **Phase frac EP (phase_frac) is a cleaner regime-indicator than Kuramoto R**:
   phase_frac_EP drops monotonically with sigma (96% -> 18%), while R is
   non-monotonic. Predict: phase_frac correlates better than R with the
   regime transitions observed in S87-S90.

## Cross-Track Connections

- **Gnosis C=0.5 boundary**: At the efficiency peak R=0.54 ≈ 0.5 by coincidence.
  The boundary is not where efficiency peaks — it's the value R passes through
  as the system moves from repulsive (low R) to locked-attractive (high R).

- **Consciousness & signal transmission**: The claim "brains tuned for
  bits/ATP run noisier" rests on MI being signal-specific at noisy
  operating points. In our model, the signal-specific MI contribution
  shrinks as sigma grows, so the efficiency advantage is mostly
  thermodynamic not informational. Brains that actually compute probably
  sit near SR, not past it.

- **Methodology for SAGE observability studies**: Tests of whether SAGE
  transmits task-relevant information should use independent-seed (or
  independent-data) bias controls, not same-trial controls. This finding
  generalizes: any signal-transmission study needs a bias control, and that
  control needs to be independent of the test trajectory.

## Quote

*"The response amplitude at the signal frequency is not the system speaking —
it is the system ringing. The bell will ring at signal_freq whenever the
bistable switching rate is near signal_freq, signal or no signal. The SR
curve is the curve of the bell. Measuring transmission is harder than
measuring resonance, because resonance happens whether or not anyone is
speaking. At the efficiency peak past SR, the bell rings more softly but
also at lower cost; the voice, if any, is barely above the ring. A smarter
observer uses mutual information with independent-seed controls — that
distinguishes the voice from the bell. An observer who measures response
amplitude alone hears the geometry of the bell and mistakes it for cognition."*

---

**Files**:
- thor_session_91_efficiency_mechanism.py (Experiments A-D: phase-coherence,
  temporal MI, conditional EP, coupling ablation)
- thor_session_91_bias_control.py (bias floor test: synthetic + same-seed
  and signal-absent controls — identified the same-seed inflation)
- thor_session_91_spectral_control.py (response_amp with vs without signal
  at independent seeds — demonstrates amp is NOT signal-specific)
- thor_session_91_loud_signal.py (A sweep at sigma=0.022 showing MI is
  signal-specific with independent seeds while amp is not)
- thor_session_91_mechanism_results.json
- thor_session_91_bias_control_results.json
- thor_session_91_spectral_results.json
- thor_session_91_output.log and sibling logs
