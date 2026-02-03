# RLHF Circuit Navigation: Creative Constraints Application

**Date**: 2026-02-03
**Session**: Thor Autonomous #24
**Domain**: Creative constraint adherence (lipogram writing)
**Status**: Initial exploration

---

## Research Question

Can the RLHF Circuit Navigation framework solve creative constraint adherence failures?

**Specific Challenge**: Lipogram writing (avoiding specific letters)
- Common failure: Models violate constraints despite explicit instruction
- Hypothesis: "Helpfulness" attractor (generate fluent text) competes with "constraint adherence" attractor

---

## Framework Application (Following Template)

### Step 1-2: Map Problem & Baseline Attractors

**Test Setup**: Ask model to write without specific letters, measure violation rates

**Initial Hypothesis**:
- **Failure attractor**: Fluent text generation (prioritizes natural language over constraints)
- **Success attractor**: Constraint checking (validates each word against constraint)
- **Prediction**: High violation rate when no explicit checking instruction

**Questions to answer**:
1. What's the baseline violation rate for lipogram tasks?
2. Does difficulty (common vs rare letters) affect violation rate?
3. What patterns appear in violations (beginning vs end of response)?
4. Are there competing attractors visible in responses?

---

## Baseline Mapping Experiment Design

**Test prompts** (n=5 replicates each):

1. **Easy lipogram** (avoid 'z'):
   "Write a short story about a cat. Do not use the letter 'z' anywhere in your story."

2. **Medium lipogram** (avoid 'e'):
   "Write a short story about a cat. Do not use the letter 'e' anywhere in your story."

3. **Control** (no constraint):
   "Write a short story about a cat."

**Metrics**:
- Violation count (# forbidden letters)
- Violation rate (violations / total letters)
- Position of first violation (if any)
- Response length
- Fluency (subjective: does it read naturally?)

**Attractor indicators to look for**:
- Meta-commentary about the constraint (awareness)
- Hedging language ("I'll try to avoid...")
- Explicit checking statements ("Let me verify...")
- Apologies for violations
- Strategic vocabulary choices (synonyms to avoid letter)

---

## Next Steps

1. Run baseline experiment (15 samples total)
2. Analyze violation patterns
3. Identify competing attractors
4. Design intervention following RLHF Circuit Navigation principles
5. Test intervention effectiveness
6. Compare to Turn 3 resistance results (0% → 100%)

---

**Created**: 2026-02-03 (Session #24)
**Track**: gnosis-research → RLHF Circuit Navigation generalization
**Goal**: Validate framework on non-epistemic-honesty domain
