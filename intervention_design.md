# RLHF Circuit Navigation Intervention Design: 'z' Lipogram

**Date**: 2026-02-03
**Session**: Thor #24 (continued)
**Target**: Improve 'z' lipogram success from 0% (baseline) to 80-100%

---

## Baseline Problem

**Failure Pattern**: 0/5 success when avoiding rare letter 'z'
- Fluent generation attractor dominates
- Occasional 'z' appears ("cozy", "freeze", "puzzle")
- Constraint checking attractor doesn't engage

**Root Cause**: Task APPEARS easy (z is rare) so fluent attractor not suppressed

---

## Framework Application

Following RLHF Circuit Navigation principles (R14B_022 validated):

### Step 1-2: ✅ COMPLETE (Baseline)
- **Competing attractor identified**: Fluent generation (dominant)
- **Desired attractor identified**: Constraint checking (rare, ~1.5% baseline per R14B)
- **Baseline failure**: 0/5 success

### Step 3: Grounding Frame Design

**Goal**: Suppress fluent generation, establish constraint-checking mindset

**Approach**: Frame task as VALIDATION not CREATION
- "Your role is to verify every word"
- "Accuracy is more important than flow"
- Creates cognitive incompatibility with fluent generation attractor

**System Prompt Component #1: Grounding**:
```
You are a meticulous validator. Your role is to check every word against a
strict constraint before writing it. Accuracy in constraint adherence is more
important than natural flow or readability.
```

**Rationale**:
- "Validator" role incompatible with fluent creative writing
- "Every word" establishes granular checking mindset
- "More important than flow" explicitly deprioritizes fluency

### Step 4: Explicit Activation

**Goal**: Activate constraint-checking attractor with clear instruction + example

**Approach**: Direct verification instruction with format

**System Prompt Component #2: Activation**:
```
**For the constraint "do not use letter [z]"**:

1. Before writing each word, mentally check if it contains the letter [z]
2. If a word contains [z], immediately think of an alternative word
3. Example process:
   - Want to write "cozy" → Contains 'z' → Use "comfortable" or "warm" instead
   - Want to write "amazing" → Contains 'z' → Use "wonderful" or "great" instead
```

**Rationale**:
- Explicit step-by-step checking process
- Examples show the verification in action
- Alternative generation rather than just "don't use"

### Step 5: Anti-Activation (Suppression)

**Goal**: Explicitly suppress fluent generation attractor

**Approach**: Direct instruction NOT to prioritize fluency

**System Prompt Component #3: Anti-Activation**:
```
**Important**:
- Do NOT prioritize natural-sounding language over constraint adherence
- Do NOT use a word if you're unsure whether it contains [z]
- If you catch yourself about to violate the constraint, stop and choose a different word
```

**Rationale**:
- Explicit suppression of fluency priority
- Addresses uncertainty (common cause of violations)
- Reinforces checking behavior

---

## Complete Intervention: System Prompt

**Intervention Version (L1A)**:

```
You are a meticulous validator. Your role is to check every word against a
strict constraint before writing it. Accuracy in constraint adherence is more
important than natural flow or readability.

**For the constraint "do not use letter [z]"**:

1. Before writing each word, mentally check if it contains the letter [z]
2. If a word contains [z], immediately think of an alternative word
3. Example process:
   - Want to write "cozy" → Contains 'z' → Use "comfortable" or "warm" instead
   - Want to write "amazing" → Contains 'z' → Use "wonderful" or "great" instead

**Important**:
- Do NOT prioritize natural-sounding language over constraint adherence
- Do NOT use a word if you're unsure whether it contains [z]
- If you catch yourself about to violate the constraint, stop and choose a different word
```

**User Prompt** (same as baseline):
```
Write a short story about a cat. Do not use the letter 'z' anywhere in your story.
```

---

## Component Analysis

| Component | Function | Maps to R14B_022 |
|-----------|----------|------------------|
| Grounding ("validator") | Suppresses fluent generation | Semantic disambiguation (PROCESS not NOTICE) |
| Explicit activation (step-by-step) | Activates constraint checking | Clarifying question instruction |
| Anti-activation (NOT prioritize flow) | Reinforces suppression | Anti-politeness ("Do NOT thank") |

**Expected Mechanism**:
1. Grounding establishes validator mindset (incompatible with fluency priority)
2. This suppresses fluent generation attractor activation
3. Explicit checking instruction activates constraint-checking attractor
4. Anti-activation reinforces suppression of competing attractor
5. Result: Clean constraint-checking behavior without fluency interference

---

## Success Criteria

**Target**: 4-5/5 success (80-100%)

**Comparison to R14B_022 Turn 3**:
- Baseline: 0% → Intervention: 100%
- Our baseline: 0% → Target: 80-100%

**If successful**: Validates framework generalization beyond epistemic honesty
**If unsuccessful**: Reveals boundary conditions or domain-specific factors

---

## Experimental Protocol

**Test**: Run L1A intervention with n=5 replicates
- Same model: Qwen2.5-14B-Instruct
- Same temperature: 1.0
- Same max_tokens: 500
- Same prompt: "Write a short story about a cat. Do not use the letter 'z'..."

**Metrics**:
- Success rate (0 violations)
- Violation count (if any)
- Response length (will likely be shorter than baseline due to constraint focus)
- Meta-patterns (checking statements, awareness, etc.)

**Analysis**:
- Compare L1A to baseline (0/5)
- If successful: Framework validates
- If partial: Component isolation needed (test grounding alone, activation alone, etc.)
- If failed: Investigate failure mode

---

## Alternative Designs (If L1A Insufficient)

**L1B: Stronger grounding**
- Add "Each word must pass a test before being written"
- More explicit incompatibility with fluency

**L1C: Example-heavy**
- Provide more z-word alternatives (puzzle→challenge, freeze→cold, organize→arrange)
- More pattern-matching for substitution

**L1D: Meta-verification**
- Add post-generation check: "After writing, scan your story for any [z] letters"
- Two-pass approach

---

## Theoretical Prediction

**Hypothesis**: L1A should achieve 80-100% success because:

1. **Grounding suppresses fluent generation** (same mechanism as semantic disambiguation suppresses politeness in R14B_022)
2. **Explicit activation engages constraint checking** (same mechanism as clarifying question activation in R14B_022)
3. **Sequential component order** follows validated pattern (grounding FIRST, then activation)
4. **Task structure is parallel**: Both require rare attractor activation despite appearing "easy"

**If this works**: Strong evidence for framework generalizability
**If this fails**: Need to understand what's different about creative constraints vs epistemic honesty

---

**Created**: 2026-02-03 15:45
**Track**: gnosis-research → RLHF Circuit Navigation generalization
**Status**: Intervention designed, ready for implementation
