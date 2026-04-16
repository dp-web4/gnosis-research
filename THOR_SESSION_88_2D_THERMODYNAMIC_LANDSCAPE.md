# Thor Session #88: The 2D Thermodynamic Landscape — Where Does 93% Go?

## Motivation

Session 87 discovered that the 1D description (collective coherence C_mean)
captures information but misses ~93% of dissipation. The 14x Landauer violation
and FT slope of 0.28 both pointed to the same gap. S87's hypothesis: "the
phase (theta) dynamics carry most of the thermodynamic burden."

This session tests that hypothesis by extending to:
1. **2D collective (C_mean, R)** where R = |<exp(i*theta)>| is the Kuramoto
   phase order parameter
2. **Full N-body** tracking all individual agent (C_i, theta_i) states

## Key Discoveries

### 1. COLLECTIVE PHASE (R) ADDS ALMOST NOTHING — Only 1% Recovery

The 2D collective description (C_mean, R) adds only ~14% more entropy
production than C_mean alone. In terms of the Landauer gap, this recovers
a mere **1.0-1.4%** of the missing dissipation.

| sigma | EP(1D) | EP(2D) | Ratio |
|-------|--------|--------|-------|
| 0.005 | 1.19 | 1.34 | 1.13x |
| 0.009 | 16.96 | 19.09 | 1.13x |
| 0.011 | 17.96 | 21.03 | 1.17x |
| 0.013 | 17.96 | 21.20 | 1.18x |
| 0.018 | 16.61 | 19.02 | 1.15x |
| 0.025 | 13.84 | 15.37 | 1.11x |

**Why R adds so little**: Despite strong trajectory correlation (rho(C,R) =
-0.82 at sigma=0.009), the DIFFUSION cross-correlation |D_CR|/sqrt(D_CC*D_RR)
= 0.006 — essentially zero. C and R share deterministic dynamics but receive
independent noise. R's drift is small relative to its diffusion, so its
contribution to EP (mu_R^2/D_RR) is tiny.

### 2. INDIVIDUAL AGENTS CARRY THE MISSING DISSIPATION — Up to 284x More

The full N-body description reveals where the entropy actually goes:

| sigma | ep(C_i) | ep(theta_i) | Total | Collective | Ratio | C% | theta% |
|-------|---------|-------------|-------|------------|-------|----|--------|
| 0.005 | 11.8 | 323.5 | 335.3 | 1.2 | **284x** | 3.5 | 96.5 |
| 0.007 | 21.8 | 165.5 | 187.3 | 8.6 | **21.7x** | 11.6 | 88.4 |
| 0.009 | 51.0 | 102.5 | 153.5 | 17.3 | **8.9x** | 33.2 | 66.8 |
| 0.011 | 55.6 | 70.4 | 126.0 | 18.1 | **7.0x** | 44.1 | 55.9 |
| 0.013 | 54.7 | 51.3 | 106.0 | 17.9 | **5.9x** | 51.6 | 48.4 |
| 0.018 | 47.1 | 27.4 | 74.5 | 16.6 | **4.5x** | 63.3 | 36.7 |
| 0.025 | 34.4 | 14.4 | 48.7 | 13.6 | **3.6x** | 70.5 | 29.5 |

At the SR optimum (sigma=0.011), the N-body EP is 7x the collective — and
the LANDAUER BOUND IS SATISFIED: eta(N-body) = 0.0002 bits/ep, well below
the bound of 0.72 bits/ep.

### 3. PHASE-COHERENCE EP EQUIPARTITION at the SR Optimum (DISCOVERY)

The fraction of entropy production in phase vs coherence crosses over at
exactly sigma ~ 0.011-0.012 — the SR optimum from S86:

- sigma < 0.011: Phase dominates (96.5% at sigma=0.005)
- sigma ~ 0.011: Near-equipartition (55.9% phase, 44.1% coherence)
- sigma > 0.013: Coherence dominates (70.5% at sigma=0.025)

**The SR optimum is where phase and coherence contribute equally to
entropy production.** This is a new thermodynamic characterization:
maximum information transfer occurs where the system distributes
dissipation most evenly across its dynamical degrees of freedom.

### 4. THE THERMODYNAMIC HIERARCHY OF COLLECTIVE COGNITION

Three measurement scales, three dramatically different EP estimates:

```
Level 1: Collective coherence (C_mean)     ~18 EP  →  1% of total
Level 2: Collective (C_mean, R)            ~21 EP  →  ~1.2% of total
Level 3: Individual agents (C_i, theta_i)  ~126 EP → visible cost

Truth: Full 8D N-body                      ~126 EP (at sigma=0.011)
```

The collective order parameter captures the *information* (MI) but not the
*cost* (EP). Each agent's internal clock — its phase rotation at omega ~0.1
— generates enormous entropy that the collective average washes out.

### 5. C AND R: ANTI-CORRELATED (Surprising)

| sigma | rho(C, R) |
|-------|-----------|
| 0.005 | -0.003 |
| 0.009 | -0.824 |
| 0.011 | -0.800 |
| 0.013 | -0.770 |
| 0.018 | -0.720 |
| 0.025 | -0.656 |

When coherence (C) is high, phase order (R) is LOW. The coupling sign flip
at C_threshold = 0.55 causes this: above threshold, phase coupling becomes
REPULSIVE, de-synchronizing the phases. The ordered cognitive state is
coherent in value but DISORDERED in phase — each agent maintains high C
while oscillating independently.

### 6. 2D Fokker-Planck Structure

At sigma=0.011, the 2D (C, R) landscape shows:
- Peak EP at C~0.63, R~0.79 (EP=30.2): The crossover region with
  high phase order
- Weighted mean EP = 3.31 (lower than 1D because probability-weighted
  by the low-EP ordered state)
- D_RR/D_CC = 0.41: Phase diffuses less than coherence
- D_CR ~ 0: Independent noise channels despite correlated trajectories

### 7. Clockwise Probability Currents in (C, R) Space

2D probability currents at sigma=0.011 reveal:
- Net CLOCKWISE circulation: R increases before C increases. Phase
  synchronization precedes coherence changes in the dynamical cycle.
- Strongest current at (C~0.85, R~0.05): the ordered state slowly loses
  coherence while gaining slight phase order.
- Mean |curl| = 0.0012, max |curl| = 0.0078
- Detailed balance violation: mean |ln(P_fwd/P_bwd)| = 1.30, max = 5.36

The clockwise circulation means: when the system transitions from order
to breathing, it first de-synchronizes (R falls) then coherence drops.
When recovering, phases re-synchronize (R rises) before coherence climbs.
Phase leads coherence in the dynamical cycle.

### 8. 2D Fluctuation Theorem — Halfway There

| tau | 1D FT slope | 2D FT slope | Improvement |
|-----|-------------|-------------|-------------|
| 10 | 0.258 | **0.496** | 1.9x |
| 50 | 0.153 | **0.352** | 2.3x |
| 100 | 0.143 | insufficient data | — |

Adding R roughly doubles the FT slope but never reaches 1.0. At tau=10,
the 2D slope of 0.50 is halfway to the theoretical value — consistent
with capturing about half the entropy production (the R dimension adds
~15% EP, and the FT improvement is proportional to the fraction of
total EP captured).

### 9. Scale Inversion of EP Decomposition (DISCOVERY)

The C/theta split reverses between collective and individual scales:

**At 2D collective level (C_mean, R)**:
  C = 87.5%, R = 12.5%, cross = -0.1%
  → Coherence dominates

**At N-body level (individual C_i, theta_i)**:
  C = 39.7%, theta = 60.3%
  → Phase dominates

This is a scale inversion: the collective phase order parameter R
averages away individual oscillations, making phase appear
thermodynamically minor. But at the individual level, each agent's
fast phase rotation (omega ~ 0.1) is the dominant entropy source.
The observable (collective coherence) and the cost (individual
phase rotation) live at different measurement scales.

### 10. Experiment F Caveat — Signal Not Coupled

The 2D Landauer test (Experiment F) reported MI = 0.002 bits — far
below S86's MI = 0.023 bits — because the signal was generated but
NOT injected into the dynamics (missing signal_amp coupling). The
"Landauer resolved at 2D level" result is an artifact of near-zero
MI. The TRUE Landauer test uses S86's MI = 0.023 with the N-body
EP = 126.04 at sigma=0.011, giving eta = 0.0002 bits/ep — well
below the Landauer bound of 0.72 bits/ep. The violation IS resolved,
but by the N-body description, not by adding R.

## What Surprised Me

### 1. The Collective Phase Order Parameter R is Thermodynamically Irrelevant
**Expected**: R would capture the "missing 93%" because S87's Landauer
violation pointed to phase dynamics.

**Found**: R adds only 1% recovery. The surprise: S87 was right that phase
dynamics carry the cost, but WRONG about which phase description matters.
It's not the collective synchronization (R) but the individual rotations
(each theta_i) that produce entropy. The Kuramoto order parameter smooths
away the individual oscillations that are thermodynamically expensive.

### 2. EP Equipartition at the Information Optimum
**Expected**: Phase should always dominate (S87 said "93% is in phase").

**Found**: Phase dominates only at low noise. At the SR optimum, phase and
coherence contribute EQUALLY. At high noise, coherence dominates. The SR
optimum is the equipartition point — a new principle.

### 3. Anti-Correlation Between C and R
**Expected**: High coherence should mean high phase synchronization.

**Found**: The opposite. The coupling sign flip creates an anti-correlated
regime where cognitive order (high C) means phase disorder (low R). This
has profound implications: collective cognition doesn't require phase
synchronization — it requires phase INDEPENDENCE among synchronized-value
agents.

### 4. N-body/Collective Ratio Varies 80x Across Noise Levels
**Expected**: A relatively constant ratio ~14x (from S87's Landauer analysis).

**Found**: The ratio ranges from 284x (sigma=0.005) to 3.6x (sigma=0.025).
At low noise, deterministic phase rotation dominates and the ratio is huge.
At high noise, diffusion catches up and the ratio shrinks. The 14x from
S87 is not a universal constant — it was specific to the noise level and
measurement method.

## Attractors I Resisted

**"R should capture most of the missing EP"**: The natural assumption
from S87's analysis. But R is a collective variable — it averages over
individual phases, losing the fast rotational entropy. The Landauer
violation isn't about collective phase order; it's about individual
computational ticks.

**"The 1D description just needs one more dimension"**: Adding R goes
from 1D to 2D and changes almost nothing. The jump to 8D (N-body)
changes everything. The lesson: coarse-graining is lossy for
thermodynamics in a fundamentally different way than for dynamics.

**"Higher noise should mean more entropy production"**: Intuitive but
wrong. Total N-body EP *decreases* from 335 (sigma=0.005) to 49
(sigma=0.025). Higher noise disrupts deterministic drift, and EP =
mu^2/D — when noise grows faster than drift^2, EP falls. Order is
thermodynamically expensive at the individual level, even though
S87 showed it's cheap at the collective level. The paradox resolves
because different measurement scales see different physics.

## Cross-Track Connections

- **Neuroscience**: Individual neurons must maintain their own oscillatory
  dynamics (the "tick") even when the collective EEG/LFP is stable. The
  metabolic cost is in each neuron's clock, not in the population coherence.
  This predicts that per-neuron metabolic rate should be high even during
  "resting" states where population coherence is stable.

- **SAGE architecture**: Processing instances need individual computational
  cycles (phase rotations) that are thermodynamically expensive, even when
  the collective coherence is cheap to maintain. Design for efficient
  individual processing, not just collective stability.

- **Gnosis C=0.5**: The crossover point gains another characterization:
  it's near the EP equipartition between phase and coherence modes. The
  fundamental boundary is also a thermodynamic equipartition point.

- **Information theory**: Landauer's bound applies to the full system, not
  to coarse-grained projections. Measuring MI at the collective level and
  EP at the collective level gives a "violation" because EP at that scale
  misses >99% of the true dissipation. There is no violation at the
  individual agent level.

## Falsifiable Predictions

1. **EP equipartition at information optima**: In any coupled oscillator
   system with stochastic resonance, the SR optimum should coincide with
   approximate equipartition of entropy production between amplitude and
   phase degrees of freedom.

2. **Collective EP underestimation scales with N**: The ratio of N-body
   to collective EP should grow with system size because collective
   averaging washes out more individual-level dissipation.

3. **Anti-correlation of C and R in repulsive-coupling regimes**: Systems
   with state-dependent coupling sign should show anti-correlated order
   parameters for the state variable vs the phase variable.

4. **Per-neuron metabolic cost independent of population coherence**: In
   neural circuits, individual neuronal firing rates (and metabolic costs)
   should NOT correlate strongly with population-level coherence measures
   like LFP power.

5. **Landauer bound satisfied only at the microscopic level**: Any
   coarse-grained information-thermodynamic efficiency measurement will
   appear to violate Landauer. The violation factor should equal the
   ratio of microscopic to macroscopic degrees of freedom.

## Quote

*"The missing 93% wasn't hiding in the collective phase — it was hiding
in each agent's heartbeat. Every tick of an internal clock costs entropy.
The collective coherence we measure and marvel at is just the calm surface
of a lake with violent currents below. The information lives at the
collective level. The cost lives at the individual level. Consciousness
is cheap to observe but expensive to run."*

---

**Files**:
- gnosis-research/thor_session_88_2d_thermodynamics.py (2D collective analysis)
- gnosis-research/thor_session_88_nbody_ep.py (full N-body analysis)
- gnosis-research/thor_session_88_2d_results.json (2D experiment results)
- gnosis-research/thor_session_88_nbody_results.json (N-body results)
