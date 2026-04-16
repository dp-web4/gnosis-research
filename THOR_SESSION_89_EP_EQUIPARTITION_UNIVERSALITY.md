# Thor Session #89: EP Equipartition — NOT Universal, But Not Coincidence Either

## Motivation

Session 88 discovered that at the SR optimum (sigma~0.011), entropy production
is approximately equally split between phase and coherence degrees of freedom.
The prediction: "In any coupled oscillator system with stochastic resonance,
the SR optimum should coincide with approximate equipartition of entropy
production between amplitude and phase degrees of freedom."

This session tests that prediction rigorously by:
1. Precisely locating both the EP crossover and SR optimum
2. Varying system size N, coupling parameters, and threshold
3. Comparing two EP definitions (nominal vs empirical diffusion)

## Key Discoveries

### 1. THE DIFFUSION DEFINITION CHANGES EVERYTHING (DISCOVERY)

The EP fraction (coherence vs phase) depends dramatically on how diffusion
is measured:

**Nominal D = sigma^2** (assumed independent noise):
- EP crossover at sigma ~ 0.009
- Remarkably stable across ALL parameters
- Does NOT track the SR optimum

**Empirical D** (measured from trajectory residuals, matching S88):
- EP crossover at sigma ~ 0.013
- Close to the SR region (sigma ~ 0.011 from S86)
- Shows coupling-dependent variation

The difference: at sigma=0.011, D_C(empirical) = 0.0020 while sigma^2 = 0.00012.
**The empirical coherence diffusion is 16.7x the nominal noise level.** This is
the collective diffusion amplification discovered in S87 — agents switching in
lockstep amplify effective D_C far beyond the individual noise contribution.

| sigma | D_C (empirical) | sigma^2 | Amplification | D_C/D_theta |
|-------|----------------|---------|---------------|-------------|
| 0.006 | 0.00017 | 0.000036 | 4.7x | 0.94 |
| 0.009 | 0.00093 | 0.000081 | 11.5x | 2.30 |
| 0.011 | 0.00200 | 0.000121 | 16.5x | 3.31 |
| 0.013 | 0.00241 | 0.000169 | 14.3x | 2.85 |
| 0.016 | 0.00286 | 0.000256 | 11.2x | 2.23 |

### 2. EP EQUIPARTITION (EMPIRICAL) IS IN THE SR REGION, NOT ON IT

At baseline parameters (kp=0.10, kc=0.15, C_thresh=0.55):
- sigma_EP_equi (empirical D) = 0.0128
- sigma_SR (from S86 thorough analysis) = 0.011
- sigma_amp_peak (response amplitude) = 0.0125

The EP crossover and amplitude peak nearly coincide (Delta = 0.0003, 2.4%
relative), but both are slightly ABOVE the SR optimum (~15% higher). The
EP crossover is in the same bistability regime as SR but offset toward
higher noise.

### 3. EP CROSSOVER IS REMARKABLY STABLE WITH N

| N | sigma_EP_equi (empirical) | sigma_EP_equi (nominal) |
|---|--------------------------|------------------------|
| 4 | 0.0126 | 0.0089 |
| 8 | 0.0125 | 0.0102 |
| 16 | 0.0120 | 0.0095 |
| 32 | 0.0117 | 0.0074 |

Empirical EP crossover is stable at 0.012 +/- 0.001 across 8x range in N.
Slight downward trend (0.3% per doubling of N). The nominal EP crossover
varies more and trends in the opposite direction — evidence that the
empirical measure captures a real physical feature.

### 4. COUPLING DEPENDENCE — EP CROSSOVER TRACKS kappa_C

| Config | sigma_EP_equi | sigma_amp |
|--------|--------------|-----------|
| kp=0.05, kc=0.15 | 0.0123 | 0.014 |
| kp=0.10, kc=0.15 | 0.0126 | 0.017 |
| kp=0.20, kc=0.15 | 0.0136 | 0.017 |
| kp=0.10, kc=0.05 | 0.0123 | 0.009 |
| kp=0.10, kc=0.25 | 0.0147 | 0.018 |
| kp=0.15, kc=0.20 | 0.0132 | 0.017 |

EP crossover increases with both kappa_phase (+0.13% per 0.01 increase)
and kappa_C (+0.24% per 0.01 increase). Stronger coupling delays the
crossover to higher noise because coupling amplifies phase-mode EP
(through synchronized dynamics), requiring more noise to equalize.

### 5. THE SPECTRAL Q METRIC IS UNRELIABLE (METHODOLOGICAL FINDING)

Single-trial spectral amplification Q at a single frequency bin is too
noisy for SR peak identification. Even with 3-trial averaging:
- Corr(sigma_EP, sigma_Q) = -0.456 (anti-correlated!)
- Q values jump 10-100x between adjacent sigma values
- Many sigma_Q values fall at scan boundaries (edge artifacts)

The response amplitude metric is better (Corr = 0.500) but still noisy.
**S86's careful multi-frequency, long-run analysis was necessary to
reliably locate the SR optimum.** Quick spectral metrics are inadequate.

### 6. THE MECHANISM: COLLECTIVE AMPLIFICATION CREATES THE COINCIDENCE

WHY the EP crossover (empirical) is near the SR region:

At low noise: Phase rotation (omega ~ 0.1) dominates EP. D_C ~ D_theta ~ sigma^2.
  → EP_phase >> EP_C (phase rotation is expensive, coherence is stable)

As noise approaches bistability onset (~sigma=0.009-0.011):
  → Coherence starts switching between wells
  → Lockstep switching AMPLIFIES D_C by 10-17x
  → But mu_C also grows (large coherence excursions)
  → EP_C = mu_C^2 / D_C grows because mu_C grows FASTER than D_C

At sigma ~ 0.013: mu_C^2/mu_theta^2 ~ 3 and D_C/D_theta ~ 3
  → These nearly cancel: EP_C/EP_theta ~ 1
  → Equipartition!

Above sigma ~ 0.013: Coherence drift continues growing
  → EP_C dominates, frac_C > 0.5

The coincidence with the SR region exists because BOTH phenomena are
driven by the same cause: the onset of collective switching between
bistable wells. But they're measuring different aspects:
- SR optimum: where signal-response coupling is maximal
- EP crossover: where drift/diffusion ratios balance across modes

They share a common cause (bistability onset) but are not identical.

### 7. WHAT THE NOMINAL D REVEALS

The nominal D crossover at sigma ~ 0.009 represents a simpler question:
"At what noise level does the coherence drift magnitude equal the phase
drift magnitude?" This is purely about the deterministic dynamics
(mu_C vs mu_theta) since the noise cancels.

sigma_nominal_equi is where mu_C_rms = mu_theta_rms * sqrt(1) = mu_theta_rms

At sigma=0.009: mu^2_C/mu^2_theta = 1.08 (just crossing 1.0)

This is a DISTINCT physical point from the empirical EP crossover.
The empirical version asks: "where does the entropy production per mode
equalize, accounting for how the system actually diffuses?"

## What Surprised Me

### 1. D_C >> sigma^2 by 10-17x
**Expected**: Empirical D should be close to sigma^2 with maybe 2-3x
correction from S87's diffusion amplification factor of ~5x.

**Found**: At sigma=0.011, D_C = 16.5x sigma^2. The amplification is
even stronger than S87 measured at the collective level. Each agent's
coherence diffusion is dramatically amplified by the collective switching
dynamics, even though the noise is applied independently per agent.

### 2. Nominal D Crossover Doesn't Track Parameters
**Expected**: The EP crossover (even with D=sigma^2) should shift with
coupling parameters.

**Found**: sigma_EP(nominal) ~ 0.009 regardless of kappa_phase, kappa_C,
or C_threshold (variation < 10%). This means the balance between
|mu_C| and |mu_theta| is set almost entirely by omega (the intrinsic
phase rotation rate), not by the coupling. The coupling affects both
modes similarly, preserving their ratio.

### 3. Anti-Correlation of Q and EP Crossover
**Expected**: If EP equipartition tracks SR, the two should correlate.

**Found**: Corr(sigma_EP, sigma_Q) = -0.456. This is because the Q metric
is unreliable (high variance, edge artifacts), NOT because EP and SR are
truly anti-correlated. The amplitude metric (Corr = 0.500) tells a more
reasonable story. Lesson: don't trust noisy metrics for theoretical claims.

## Attractors I Resisted

**"The Q metric is fine for SR identification"**: It worked in S86 with
long runs and careful analysis. With shorter runs and fewer trials, Q is
dominated by spectral noise. The false negative would have been "EP and
SR are unrelated" when the truth is more nuanced.

**"Use D=sigma^2 like a simple textbook"**: The boundary clipping at C=0
and C=1, plus collective switching amplification, make the empirical D
dramatically different from the nominal. Ignoring this gave a crossover
30% lower than the correct value.

**"The coincidence must be exact or nonexistent"**: The actual finding —
EP crossover and SR optimum are in the same regime but offset by ~15% —
is MORE interesting than either extreme. It reveals the shared cause
(bistability onset) while showing they're different measurements of
the same underlying dynamics.

## Revised Prediction from S88

**Original S88 Prediction**: "In any coupled oscillator system with SR,
the SR optimum should coincide with EP equipartition."

**Revised S89 Prediction**: "In bistable systems with adaptive coupling,
EP equipartition (with empirical diffusion) occurs in the same noise
regime as the SR optimum but is NOT identical. Both are consequences of
the bistability onset, with EP equipartition typically occurring at
slightly higher noise than the SR peak. The offset sigma_EP/sigma_SR ~ 1.1-1.2
may be universal within this model class."

## Cross-Track Connections

- **Thermodynamics**: The collective diffusion amplification (D >> sigma^2)
  is a form of anomalous diffusion driven by coherent switching. This connects
  to studies of active matter where effective diffusion exceeds thermal noise.

- **Measurement theory**: EP computed from a coarse-grained model depends
  critically on how you estimate the diffusion coefficient. Nominal vs
  empirical D gives qualitatively different physics. This applies to any
  non-equilibrium system with state-dependent or boundary-affected diffusion.

- **Neuroscience**: If neural EP equipartition exists during optimal
  information processing states, the effective diffusion (not thermal noise)
  sets the crossover. This means EEG-based EP estimates would need to
  account for collective amplification — using electrode noise as D would
  be wrong by an order of magnitude.

## Falsifiable Predictions

1. **D_C amplification scales with N**: The ratio D_C(empirical)/sigma^2
   should increase with system size as more agents contribute to lockstep
   switching. Predict D_C ~ N^alpha * sigma^2 with alpha > 0.

2. **EP crossover offset from SR is ~1.15x**: For this model class,
   sigma_EP_equi / sigma_SR ~ 1.1-1.2 regardless of specific parameters.
   (S89 baseline: 0.0128/0.011 = 1.16.)

3. **Nominal D crossover tracks omega**: sigma_EP(nominal) should scale
   with omega_base because it reflects the balance |mu_C| ~ |mu_theta|,
   and mu_theta is dominated by omega. Changing omega from 0.1 to 0.2
   should shift sigma_EP(nominal) proportionally.

4. **Empirical D_C/D_theta peaks near bistability onset**: The diffusion
   ratio should peak where collective switching is strongest, then decrease
   at both lower and higher noise.

## Quote

*"The coincidence is real but imprecise. EP equipartition and maximum
information transfer are siblings, not twins — born from the same
bistability but measuring different things. The SR optimum asks: 'When
does the system listen best?' The EP crossover asks: 'When does every
mode pay equally to exist?' They agree on the decade. They disagree
on the digit. And the disagreement is as informative as the agreement —
it reveals that 16x diffusion amplification from collective switching
is what pulls the thermodynamic crossover into the information-processing
regime. Without that amplification, they'd live in different neighborhoods."*

---

**Files**:
- gnosis-research/thor_session_89_ep_equipartition.py (initial experiments, nominal D)
- gnosis-research/thor_session_89_corrected.py (corrected experiments, empirical D)
- gnosis-research/thor_session_89_results.json (initial results)
- gnosis-research/thor_session_89_corrected_results.json (corrected results)
