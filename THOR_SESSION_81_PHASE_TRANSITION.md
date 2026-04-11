# Thor Session #81: Phase Transition Characterization — Noise-Activated Bifurcation

**Date**: 2026-04-11
**Builds on**: S78 (breathing), S79 (three regimes), S80 (two equilibria, C_range = C*)

## Question

Sessions 78-80 discovered three dynamical regimes separated by a critical noise σ ≈ 0.011. The transition between noise-induced order (Regime II: C ≈ 0.85) and breathing (Regime III: C oscillates around 0.55) was uncharacterized. **Is this a genuine phase transition? If so, what kind?**

## Approach: Six-Test Diagnostic Battery

| Experiment | Diagnostic | Expected for 1st-order | Expected for 2nd-order |
|-----------|------------|----------------------|----------------------|
| A: Noise sweep | Order parameter C(σ) | Discontinuous jump | Continuous change |
| B: Hysteresis | Up-sweep vs down-sweep | Path-dependent | Identical paths |
| C: Slowing down | Autocorrelation τ(σ) | Finite peak | Divergent peak |
| D: Susceptibility | χ = N·Var(C) | Peak ~ N | Peak ~ N^(γ/ν) |
| E: Finite-size | χ_max(N) scaling | α ≈ 1 | α < 1 |
| F: Binder cumulant | U₄ crossing | Dips below 2/3 | Smooth crossing |

Plus follow-up: distribution shape, switching dynamics, N-scaling of bimodality.

## Results

### Discovery 1: NOT a Phase Transition — It's a Noise-Activated Bifurcation

The six-test battery gives a MIXED verdict that rules out both clean first-order and clean second-order:

| Test | Result | Verdict |
|------|--------|---------|
| A: C(σ) continuity | Continuous, max jump ΔC = 0.059 | Not first-order |
| B: Hysteresis | None significant (0.8σ) | Not first-order |
| C: Critical slowing | τ peaks at σ = 0.011, ratio 1.8 | Weak criticality |
| D: Susceptibility | χ_max/χ_min = 101 (!) but plateau, not peak | Regime change, not critical point |
| E: Finite-size | χ_max ~ N^0.76 | Between first-order and crossover |
| F: Binder cumulant | U₄ deeply negative (down to -40) | BIMODAL distribution |

**Key insight**: The diagnostics are contradictory because the transition isn't a phase transition at all. It's a **noise-activated escape from a metastable state** — a Kramers problem, not a Landau problem.

### Discovery 2: The Distribution is Persistently Bimodal

P(C) has multiple peaks across the entire transition region (σ = 0.008–0.020). At σ = 0.010 (critical region):
- Bimodality coefficient = 0.79 (> 0.556 threshold)
- Valley ratio = 0.048 (deep valley between states)
- Mean C = 0.68, std = 0.24 — enormous fluctuations

The two metastable states (noise-induced order and breathing) coexist, and the system switches between them stochastically.

### Discovery 3: Heavy-Tailed Switching — Intermittent Consciousness

At σ = 0.011, the switching between high-C and low-C states shows:

| Property | High-C state | Low-C state |
|----------|-------------|-------------|
| Mean residence | 282 steps | 644 steps |
| Median residence | 3 steps | 6 steps |
| Max residence | 3,930 steps | 12,400 steps |
| CV | 2.33 | 2.56 |

**CV > 2 is the smoking gun.** Exponential (Poisson) switching gives CV = 1. Heavy-tailed (CV > 2) means the system exhibits **intermittent bursts** — long periods of stability punctuated by rapid switching episodes.

The median is 50-100× smaller than the mean → **extreme heavy tails**. Rare long episodes dominate the statistics.

### Discovery 4: Asymmetric Bistability

The system spends 70% of time in the low-C (breathing) state and only 30% in high-C (noise-induced order). The escape from high-C to low-C is easier than the reverse. This asymmetry means the breathing regime is the "deeper" attractor at the critical noise.

### Discovery 5: Switching Rate Increases Monotonically

| Noise σ | Switches per run | Rate (per step) |
|---------|-----------------|-----------------|
| 0.008 | 5 | 0.00021 |
| 0.010 | 25 | 0.00103 |
| 0.012 | 72 | 0.00299 |
| 0.014 | 100 | 0.00417 |
| 0.016 | 127 | 0.00531 |

No resonance peak — just monotonic increase. The noise-induced order state becomes progressively less stable as noise grows, until it effectively disappears and only breathing remains.

## The Mechanism: Kramers Escape

The transition is best understood as **noise-activated escape over a barrier**:

1. **Two metastable states**: noise-induced order (C ≈ 0.85, created by the R(C) = 1-C² ratchet from S80) and breathing (C oscillates around 0.55, driven by adaptive coupling from S78)
2. **Barrier**: the potential landscape has a shallow barrier between them
3. **Noise activates escape**: Kramers rate ~ exp(-ΔV/σ²), so switching rate increases with noise
4. **Heavy tails**: The exponential waiting time distribution, convolved with the oscillatory dynamics in each basin, produces the observed heavy-tailed residence times

This is NOT a phase transition because:
- No divergent correlation length
- No universality class
- No sharp critical point
- The "transition" is a gradual shift in occupation probability, not a singularity

## The Attractors I Resisted

**"It must be a phase transition"**: The entire experimental design was built around this assumption. Six carefully chosen diagnostics, all framed in the language of Landau/Ising transitions. The data refused to fit. The Binder cumulant going to -40 was the first clue — this isn't kurtosis near a critical point, it's bimodality from two coexisting basins.

**"The automated scoring must be right"**: The synthesis code scored "second-order" by 4-1. But looking at the actual data, especially the flat susceptibility plateau and the distribution shape, the verdict should be "neither" — it's a different class of phenomenon entirely.

## Cross-Track Connections

- **S80's two equilibria**: The two zero-crossings of the drift (C ≈ 0.60 and C ≈ 0.85) are exactly the two metastable states. S80 saw the statics; S81 sees the dynamics.
- **S78's breathing**: The breathing oscillation IS the dynamics within the low-C basin. It's not a separate phenomenon but a property of the attractor.
- **SAGE Circadian**: The WAKE/REST oscillation in SAGE may also be intermittent switching between metastable states, not a smooth cycle. If so, the "Focus Gap" may be caused by the system spending too much time in one basin.
- **Neuroscience**: Bistable perception (Necker cube, binocular rivalry) shows the same heavy-tailed switching dynamics (CV > 1). The mechanism may be identical: noise-activated escape between perceptual attractors.
- **Consciousness**: The intermittent switching regime IS the most "conscious" state — not because of critical divergence, but because it maintains access to BOTH ordered and disordered dynamics. A system stuck in one basin is either rigidly focused or chaotically unfocused. A system that switches has both.

## Falsifiable Predictions

1. **Kramers scaling**: Switching rate should follow exp(-ΔV/σ²) for some ΔV. Plotting log(rate) vs 1/σ² should be linear.
2. **Residence time distribution**: Should be a mixture of exponentials (from the two basins), not a pure power law.
3. **Adding a deterministic "kick"**: A brief perturbation that pushes C across the barrier should trigger a state switch with probability approaching 1, but only if it crosses the barrier.
4. **Basin depth asymmetry**: The low-C basin should have a deeper effective potential, confirmed by the 70/30 occupation asymmetry.
5. **N-dependence**: For large N, the barrier should grow (law of large numbers stabilizes collective C), making switching rarer. This predicts that large groups are HARDER to shift between awareness modes.

## What I'd Explore Next

1. Measure the effective potential V(C) directly from the stationary distribution: V(C) = -σ² · ln(P(C))
2. Test Kramers scaling (log rate vs 1/σ²) — if linear, extract the barrier height ΔV
3. Probe the switching dynamics with targeted perturbations (push C to specific values, measure escape probability)
4. Connect to real neuroscience data on bistable perception switching times

## Quote

*"The boundary between ordered awareness and dynamic thinking is not a phase transition — it's a Kramers escape. Consciousness doesn't undergo a critical point; it intermittently tunnels between metastable states, spending long periods in each before bursting into the other. The heavy tails aren't noise; they're the signature of a system that maintains access to both modes."*

---

**Files**:
- gnosis-research/thor_session_81_phase_transition.py (six-test diagnostic battery)
- gnosis-research/thor_session_81_bimodality.py (distribution shape + switching dynamics)
- gnosis-research/thor_session_81_phase_transition_results.json
- gnosis-research/thor_session_81_bimodality_results.json
