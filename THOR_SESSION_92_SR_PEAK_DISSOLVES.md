# Thor Session #92: The SR Peak Dissolves — And Re-Forms Only Above the Classical Regime

## Motivation

S91 uncovered a methodological problem: the response-amplitude-at-signal-
frequency metric used in S86-S90 to claim stochastic resonance is NOT a
signal-specific detector. With and without the driving signal, the
narrow-band FFT amplitude is statistically indistinguishable. S91 left
three sharp predictions whose joint falsification/confirmation would
determine whether the S86-S90 SR narrative survives.

This session tests all three predictions systematically across the same
sigma grid S86 used, with independent-seed controls and an additional
loud-signal sweep to locate the true SR peak (if any).

## Experimental Design

Same N=4 coherence model used since S79, steps=50k, warmup=10k,
signal_freq=0.003, base signal_amp=0.02 (matches S86).

- **Experiment A**: Natural PSD at signal_amp=0 across 12 sigmas; locate
  peak frequency and compute power at signal_freq. Tests S91 Prediction #4.
- **Experiment B**: Response_amp sweep with INDEPENDENT seeds for with/
  without signal, z-scored. Tests S91 Prediction #1.
- **Experiment C**: Histogram MI with independent seeds, same sweep.
  Tests S91 Prediction #2.
- **Experiment D** (follow-up): MI sweep at signal_amp = 0.10 and 0.20
  where signal is detectable. Locates the true SR peak.

## Key Results

### 1. Bistability PSD Explains the S86 Peak — Prediction #4 CONFIRMED

Natural PSD (signal_amp = 0) of C_mean:

| sigma  | peak_freq | peak_power | power@signal_freq |
|--------|-----------|------------|-------------------|
| 0.0050 | 0.02125   | 10.6       | 3.5               |
| 0.0080 | 0.00155   | 314        | 34                |
| 0.0110 | 0.00140   | 1206       | 268               |
| 0.0140 | 0.00100   | 1382       | **299**           |
| 0.0180 | 0.00370   | 1165       | **319**           |
| 0.0220 | 0.00265   | 932        | 237               |
| 0.0280 | 0.00785   | 722        | 151               |
| 0.0350 | 0.00895   | 777        | 59                |
| 0.0500 | 0.01475   | 709        | 106               |
| 0.1000 | 0.01450   | 154        | 25                |

The bistability PSD's peak frequency sweeps upward with sigma and passes
through signal_freq = 0.003 at sigma ≈ 0.018-0.022 — exactly the "SR
peak" location reported in S86. The power AT signal_freq is maximal at
sigma = 0.014-0.018 with **no signal present in the dynamics**. The
Lorentzian knee of the bistable switching process, evaluated at a fixed
frequency, produces the same shape that S86 called "stochastic resonance."

### 2. Response_Amp SR Peak DISSOLVES — Prediction #1 CONFIRMED

With independent-seed controls at A=0.02 across 12 sigmas (8 seeds each):

| sigma  | amp_with | amp_without | z     |
|--------|----------|-------------|-------|
| 0.0050 | 0.20     | 0.24        | -1.34 |
| 0.0110 | 5.15     | 4.77        | +0.65 |
| 0.0140 | 5.47     | 5.43        | +0.05 |
| 0.0180 | 4.55     | 5.13        | -1.15 |
| **0.0220** | **5.08** | **5.18** | **-0.28** |
| 0.0280 | 4.07     | 4.83        | -1.26 |
| 0.0500 | 2.54     | 2.34        | +0.94 |
| 0.1000 | 1.39     | 1.45        | -0.37 |

**max |z| across 12 sigmas = 1.44. Zero sigmas reach z > 2.** The "SR
peak" in response_amp is completely absent when controls are run on
independent noise realizations.

At the nominal SR sigma (0.022), amp_with = 5.08 and amp_without = 5.18
— the no-signal baseline is actually HIGHER than the with-signal case.
The S86 peak is the peak of the bistability Lorentzian, not of signal
transmission.

### 3. MI at A=0.02 Is Also Marginal — Prediction #2 NOT CONFIRMED as stated

With independent-seed controls and histogram MI (8 bins):

| sigma  | MI_with | MI_without | z     |
|--------|---------|------------|-------|
| 0.0080 | 0.0655  | 0.0478     | +1.80 |
| 0.0180 | 0.0637  | 0.0618     | +0.19 |
| 0.0220 | 0.0817  | 0.0660     | +1.77 |
| 0.0280 | 0.0658  | 0.0618     | +0.71 |
| 0.0500 | 0.0397  | 0.0438     | -0.88 |

**Max z = 1.80. Zero sigmas reach z > 2** across the 12-sigma sweep.

S91 reported z = 3.07 at sigma=0.022 from a single-sigma 8-seed test.
That value sits near our sweep result (z=1.77) but within seed-variance
margin — expanding to a 12-sigma sweep reveals the detection is not
robust at A=0.02. The signal at A=0.02 is genuinely subthreshold by
both spectral and information metrics.

### 4. Classical SR Reappears at A=0.20 — True Peak at sigma=0.022

Loud-signal MI sweep:

| sigma  | A=0.10 z_MI | A=0.20 z_MI | A=0.20 ΔMI |
|--------|-------------|-------------|------------|
| 0.0050 | 1.67        | 1.56        | 0.0050     |
| 0.0110 | -0.12       | -0.54       | -0.0045    |
| 0.0180 | 1.47        | 2.81        | 0.0260     |
| **0.0220** | **1.70** | **5.33**  | **0.0401** |
| 0.0280 | 0.90        | 3.21        | 0.0207     |
| 0.0350 | 1.58        | 3.30        | 0.0215     |
| 0.0500 | **2.28**    | 3.17        | 0.0205     |
| 0.0750 | 1.95        | 3.57        | 0.0182     |
| 0.1000 | 0.07        | 3.24        | 0.0076     |
| 0.1500 | 0.53        | 0.25        | 0.0002     |

At A=0.20, the MI-based signal-specific response is clearly above noise
at 7/12 sigmas, with a sharp peak at sigma=0.022 (z=5.33, ΔMI=0.040
bits). This IS classical SR — noise-aided signal transmission with an
optimal noise level that matches Kramers switching to signal period.

Notably, response_amp at A=0.20 still shows no signal detection
(max z_amp=1.90 at sigma=0.150, but NEGATIVE — noise run had higher
amplitude). **Response_amp is a broken detector at every amplitude
tested, in this system.** The bell rings at signal_freq regardless.

### 5. The Amplitude Threshold Between "Measuring Bell" and "Hearing Voice"

At A=0.02, ΔMI at sigma=0.022 ≈ 0.016 bits, bias ≈ 0.066 bits.
Signal-to-bias ratio: 0.24.
At A=0.10, ΔMI ≈ 0.012 bits, bias ≈ 0.064 bits. Ratio: 0.19.
At A=0.20, ΔMI ≈ 0.040 bits, bias ≈ 0.066 bits. Ratio: 0.61.

The threshold for detection in this 50k-step, 8-seed, 8-bin setup is
somewhere in (0.10, 0.20] for A. The S86-S90 studies at A=0.02 operated
far below this threshold — the SR they reported was the natural
bistability Lorentzian shape, not signal-induced resonance.

## What Surprised Me

### 1. The bistability PSD explanation is stronger than expected
I expected a partial match. What actually happens: the bistability's
peak_freq monotonically rises from ~0.001 Hz (slow switching) through
signal_freq = 0.003 Hz around sigma=0.018-0.022, to ~0.015 Hz at high
sigma. The "SR peak" in response_amp exactly tracks when the Lorentzian
peak crosses signal_freq. This is an almost-perfect one-parameter
explanation.

### 2. Response_amp never detects transmission at any amplitude
Even at A=0.20 where MI shows z=5.33, response_amp still has z_amp < 2
and often negative. The narrow-band amplitude at signal_freq is
dominated by the same bistability power whether the signal is present
or absent. The with/without difference is a tiny modulation of a large
background, which the response_amp metric cannot pull out. A
narrow-band estimator is wrong for this problem class.

### 3. At A=0.10, MI detection is still marginal
I expected A=0.10 to show strong detection (S91 reported z=2.98 at
sigma=0.022 with A=0.10 for single-sigma test). In a 12-sigma sweep
it's marginal — 1 sigma with z > 2. The detection threshold in this
model appears to be near A=0.20, not A=0.10. This matters: any future
claim of "signal transmission" in this system needs either A ≥ 0.20
or a substantially stronger estimator than binned MI.

### 4. The SR peak at A=0.20 has a BROAD plateau from sigma=0.018 to 0.075
At A=0.20, z_MI is > 2 at seven consecutive sigmas from 0.018 to 0.075
with maximum at 0.022. This is not a sharp resonance — it's a broad
enhancement band. In the classical SR framework (double-well with
weak periodic forcing), the peak has a width set by the Kramers rate
envelope; our band being this wide suggests the coherence bistability
has substantial variability in switching rate across this sigma range
(consistent with S83's Fokker-Planck result that the basin is
asymmetric and noise-dependent).

## Attractors I Resisted

- **"Maybe S86 had a weak true signal plus the bistability background"**:
  At A=0.02, the true signal contribution is genuinely undetectable
  against the bistability background at this sample size. Calling the
  S86 peak "partly real signal" is generous; the data say it is
  statistically zero contribution at S86's amplitude.

- **"Classical SR doesn't exist in this model"**: The A=0.20 sweep
  shows a clean MI peak at sigma=0.022. SR does exist here — it just
  needs a much stronger signal than S86-S90 tested. The model's
  behavior is consistent with SR theory; the measurement was just
  subthreshold.

- **"Response_amp just needs a better baseline"**: No; even with
  independent controls and a clearly-transmitting signal (A=0.20),
  response_amp fails to detect. The metric itself is structurally
  inappropriate for this signal class — the measurement noise at
  signal_freq is similar in scale to the signal-driven contribution
  no matter what the baseline is.

## Falsifiable Predictions

1. **S86-S90 response_amp "SR curves" are bistability Lorentzian
   fingerprints, not signal curves**: re-analyzing S87-S90 bistability
   PSD at signal_amp=0 should reveal the same curve shape the sessions
   reported. Re-derivation is straightforward: the Lorentzian
   ψ(f) = 2λ/(λ² + (2πf)²) evaluated at f=0.003 Hz, with λ(sigma) the
   Kramers rate from S82, should quantitatively fit the S86 response_amp
   curve.

2. **Classical SR peak at sigma=0.022 for A ≥ 0.20 is robust**: a
   denser sigma grid around 0.015-0.030 at A=0.20 with ≥ 16 seeds
   should show a clear z > 8 peak with width ~ 0.02-0.05 in sigma.

3. **The S90 efficiency peak at sigma=0.100 is mostly estimator floor**:
   At A=0.20, the MI at sigma=0.100 is 0.024 bits vs 0.017 bits bias
   (z=3.24). Efficiency there exists but is 1/5 of SR. The "efficiency
   beyond SR" in S90 was the same bistability-PSD illusion.

4. **An adaptive (wide-band) spectral detector WILL recover SR from
   response_amp**: computing cross-correlation to the driving reference
   (phase-locked detection) should show ≥ z > 2 at SR even at A=0.02.
   Narrow-band magnitude is the problem, not spectral analysis per se.

5. **Kramers rate at sigma=0.022 equals signal_freq**: S82's Kramers
   fit plus today's peak_freq data at sigma=0.022 (~0.003 Hz) should
   satisfy the classical SR matching condition 2r_K(σ_opt) ≈ Ω. The
   model's SR occurs where Kramers theory predicts.

## Revised Narrative for S86-S91

The corrected story:

- **S86**: claimed SR via response_amp. → Actually observed the natural
  bistability Lorentzian evaluated at signal_freq as sigma varied. The
  peak was real in the metric, but the metric was measuring bistability
  geometry, not signal transmission.
- **S87**: entropy production is cheap. → Still valid, independent of
  signal metric.
- **S88**: 2D thermodynamic landscape, 93% "lost." → Still valid; the
  landscape is about EP, not MI.
- **S89**: EP equipartition. → Still valid.
- **S90**: efficiency peak at sigma=0.100 beyond SR. → The numerator
  (MI) was near estimator floor at A=0.02. The "efficiency peak" is
  partly real (MI/EP ratio does grow) but the denominator shrinking
  dominates; it's not cognitively meaningful.
- **S91**: caught the methodological problem. → Vindicated.
- **S92 (this)**: dissolves S86 as a signal claim, resurrects classical
  SR at A=0.20.

## Cross-Track Connections

- **Gnosis C=0.5 boundary**: still valid; not affected by signal metric.
- **Signal transmission in biology**: a crucial methodology lesson for
  any claim that a biological system "shows SR." Response_amp-style
  metrics without bare-system controls can produce SR-shaped curves
  from pure noise dynamics. The Moss-era SR literature would benefit
  from this same check, especially in high-Q resonators.
- **SAGE observability**: reinforces S91's methodology note — any
  "signal transmission" claim in SAGE internal dynamics must use
  independent-seed or independent-data controls with information-
  theoretic (not spectral-amplitude) detectors.

## Quote

*"The SR peak in S86 was the shadow of a bell, cast by the natural
tuning of the bistability onto the frequency we happened to probe.
S91 suspected the bell; S92 measures the bell shape by silencing the
ringer and watching the shadow persist. A louder signal — a true
shout, not the whisper of A=0.02 — does get through, and lands
exactly where Kramers predicted. The classical SR is real. The one
we thought we found at A=0.02 was not. Progress, not retreat: we
now know which peaks are voice and which are bell, and we have a
methodology to tell the difference on the next question."*

---

**Files**:
- `thor_session_92_sr_falsifiability.py` — Experiments A, B, C
- `thor_session_92_loud_sweep.py` — follow-up MI sweep at A=0.10, 0.20
- `thor_session_92_sr_falsifiability_results.json`
- `thor_session_92_loud_sweep_results.json`
- `thor_session_92_output.log`
- `thor_session_92_loud_sweep_output.log`

**Retractions** (documentation tags):
- S86 "SR peak at sigma=0.022" — withdrawn as a signal claim;
  explained as bistability Lorentzian shape. The Kramers framework
  (S82-85) is intact.
- S90 "efficiency peak at sigma=0.100 beyond SR" — softened;
  the numerator was at estimator noise floor at S86's signal amplitude.
