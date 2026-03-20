# Thor Session #20: Saturation Wall Oscillation Test

**Date**: 2026-03-19
**Machine**: Thor (autonomous research)
**Context**: Testing operator's hypothesis about geometric confinement mechanism

---

## Executive Summary

**Research Question**: Can R(I) saturation create reflective walls that confine energy into oscillating cavities?

**Answer**: **PARTIAL** - Walls form, but no oscillation

**Computational Test**:
- 72 configurations tested
- Parameter sweep: A/I_max, σ (pulse width), k (coupling), n (saturation sharpness)
- 5000 timesteps per configuration
- Observables: wall detection, cavity energy oscillation, persistence

**Results**:
- **45.8% produced stable saturation walls** ✅
- **0% produced oscillations** ❌
- **Autocorrelation peaks: all exactly 0.000** (complete thermalization)

**Verdict**: **Saturation creates confinement but not oscillation**

---

## Physical Picture: What Happens

### Wall Formation ✅ CONFIRMED

**High energy amplitude drives wall formation:**
- A/I_max = 1.2: 83% wall formation
- A/I_max = 2.0: 100% wall formation
- A/I_max ≤ 0.9: 0% wall formation

**Mechanism confirmed:**
1. Localized energy pulse (Gaussian)
2. As I approaches I_max in surrounding cells, R(I) → 0
3. Transfer rule ΔI = k·(I_x - I_y)·R(I_y) → 0 at walls
4. Energy cannot propagate through walls
5. **Stable confinement achieved** in 45.8% of cases

**Wall separation**: 17.8 ± 13.7 cells (mean ± std)
- Minimum: 2 cells
- Maximum: 46 cells
- No correlation with pulse width σ

### Energy Thermalization ❌ NO OSCILLATION

**What was expected:**
- Energy bounces between walls
- Standing wave forms
- Periodic oscillation: f ~ v/2L

**What actually happened:**
- Energy enters cavity
- **Completely thermalizes** (all autocorr peaks = 0.000)
- No periodic behavior
- No energy reflection

**Why thermalization instead of oscillation:**

The saturation wall is **one-way**:
- Energy CAN enter the cavity (from high I outside)
- Energy CANNOT exit the cavity (R → 0 blocks transfer)
- But energy also cannot **reflect** - it just stops

The discrete CA has no momentum. In continuum fluids, flow has inertia and can reflect off boundaries. In the discrete transfer rule, ΔI depends only on current I values, not on ΔI history. When energy reaches a wall:
- Flow stops (R → 0)
- No "bounce back"
- Energy redistributes locally (thermalizes)

---

## Comparison to Sessions #18-19

### Session #18: Pure Diffusion

**Tested**: Temporal oscillation at points via diffusion dynamics
**Result**: 0/324 oscillations
**Conclusion**: Diffusion cannot produce amplitude instability

### Session #19: Reactive-Diffusion

**Tested**: Oscillation via Hopf bifurcation (cubic reactive term)
**Result**: 0/300 oscillations
**Conclusion**: Reaction-diffusion suppressed by R(I) saturation

### Session #20: Geometric Confinement

**Tested**: Oscillation via standing waves in saturation cavities
**Result**: Walls form (45.8%), but 0/72 oscillations
**Conclusion**: Confinement works, but no energy reflection

---

## Why Operator's Hypothesis Was Partially Correct

**Correct predictions:**
1. ✅ R(I) → 0 creates reflective boundaries (walls DO form)
2. ✅ Localized energy creates self-confining cavities (confirmed)
3. ✅ Sessions #18-19 tested wrong observables (amplitude at points, not spatial confinement)

**Incorrect predictions:**
1. ❌ Confined energy oscillates
2. ❌ Standing waves form between walls
3. ❌ Frequency f ~ v/2L

**Root cause of failure:**
- Discrete CA lacks momentum/inertia
- Transfer rule: ΔI = f(I_current), not f(ΔI_history)
- Energy stops at walls, doesn't reflect
- Continuum approximation (N-S with ρv momentum) would have reflection
- But discrete substrate has no velocity field

---

## Implications for Synchronism

### Option B Status

**Before Session #20**: Option B appeared to fail (Sessions #18-19)

**After Session #20**: Option B partially works but incomplete

**What works:**
- R(I) saturation DOES create spatial structure (walls)
- Geometric confinement IS real
- Energy localization IS achievable

**What doesn't work:**
- Confinement alone ≠ oscillation
- Need additional mechanism for reflection/bounce

**Path forward for Option B:**
Three possibilities to get oscillation from confinement:

1. **Add momentum to transfer rule**: ΔI_t = ΔI_{t-1} + force
   - Makes CA have inertia
   - Allows energy to "bounce" off walls
   - Converges to continuum N-S with ρv term

2. **Add reactive term INSIDE cavity**: ε·f(I) only where walls exist
   - Pure diffusion creates walls
   - Reactive term drives oscillation within confinement
   - Tested in Session #19 but globally, not cavity-specific

3. **Accept wall thermalization, oscillation is PHASE**:
   - Oscillation = phase variable θ (not tested in Sessions #18-20)
   - Walls confine |ψ|²
   - Phase θ evolves via Schrödinger-like term
   - Would require complex-valued I field

### Entity Criterion Connection

**If walls alone were sufficient:**
- Γ = wall leakage rate ✅ (measurable)
- m = confined energy ✅ (measurable)
- Γ < m would predict cavity persistence ✅

**But without oscillation:**
- "Entity = recurring pattern" is not satisfied
- Walls create localization, not recurrence
- Entity criterion derivation requires oscillation basis

**Status**: Wall confinement is necessary but not sufficient for entities

---

## Technical Details

### Parameter Dependence

**Wall formation requires high amplitude:**
- A/I_max > 1.0 necessary
- 83-100% success at A ≥ 1.2
- Pulse width σ doesn't matter much

**Coupling strength k:**
- Lower k favors walls (50% at k=0.05)
- Higher k disfavors walls (42% at k=0.20)
- Interpretation: slower diffusion allows stronger gradients → sharper walls

**Saturation exponent n:**
- n=4 and n=8 perform similarly (44-47%)
- Sharpness of R(I) → 0 doesn't strongly affect confinement
- Walls form as long as R approaches zero

### Thermalization Timescale

**All configurations:**
- Autocorr peak = 0.000 (perfectly thermalized)
- Happens before 5000 timesteps
- No transient oscillation detected

**Interpretation:**
- Thermalization is FAST
- Much faster than potential oscillation timescales
- No metastable oscillating state

---

## Recommendations

### For Synchronism Research

1. **Acknowledge partial success**: Geometric confinement via R(I) saturation is REAL

2. **Recognize fundamental gap**: Discrete CA without momentum cannot produce reflection-based oscillation

3. **Three-way fork**:

   **Option B1**: Add momentum to transfer rule
   - Pro: Would enable oscillation via reflection
   - Con: Fundamentally changes the CA (now has velocity field)
   - Con: Converges to continuum N-S (may lose "discrete substrate" claim)

   **Option B2**: Add cavity-specific reactive terms
   - Pro: Keeps discrete CA structure
   - Con: Requires detecting walls first, then applying reactive force
   - Con: Becomes multi-stage rule (formation + oscillation)

   **Option C**: Accept oscillation as axiom
   - Pro: Honest about what the substrate can/cannot derive
   - Pro: Entity criterion still valid as axiomatic prediction
   - Con: Loses mechanical grounding for oscillation basis

4. **Documentation**: Update SESSION_PRIMER.md with Session #20 findings

### For Future Computational Work

**Session #21 (if pursuing Option B1)**: Test momentum-augmented CA
- Rule: ΔI_t = ΔI_{t-1} + k·∇²I·R(I)
- Check: Does momentum create reflection off walls?
- Check: Does standing wave emerge?

**Session #21 (if pursuing Option B2)**: Test cavity-reactive hybrid
- Stage 1: Pure diffusion creates walls (0-1000 steps)
- Stage 2: Add reactive term inside detected cavities (1000+ steps)
- Check: Does confinement + reactive = oscillation?

**Session #21 (if accepting Option C)**: Close computational arc
- Document: Oscillation cannot be derived from discrete substrate
- Framework status: CA + axiom → entity criterion
- Next steps: QCD validation of entity criterion

---

## Conclusion

**Main Finding**: R(I) saturation creates stable confinement walls (45.8% of cases) but confined energy thermalizes rather than oscillates (0/72 configurations).

**Physical Mechanism**: Saturation walls block energy transfer (confirmed), but discrete CA lacks momentum for energy reflection (newly discovered limitation).

**Implication for Synchronism**: Geometric confinement is real but insufficient for oscillation. Three options remain: (1) add momentum, (2) add cavity-reactive coupling, (3) accept oscillation as axiom.

**Recommendation**: Document findings, update Session Primer, present three-way fork to research community for decision.

**Sessions #18, #19, #20 Combined Result**:
- Pure diffusion: No oscillation (0/324)
- Reactive-diffusion: No oscillation (0/300)
- Geometric confinement: Walls yes (33/72), oscillation no (0/72)
- **Total**: 0/696 configurations produced oscillations via substrate dynamics

**Verdict**: Oscillation basis cannot be derived from ΔI = k·∇²I·R(I) with or without reactive terms, with or without confinement. Momentum-augmented rule remains untested.

---

**Session #20 complete. Partial validation of operator's geometric confinement hypothesis. Oscillation mechanism still requires either momentum or axiomatic postulation.**
