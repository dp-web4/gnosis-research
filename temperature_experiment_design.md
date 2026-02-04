# Temperature Reduction Experiment - Breaking the 60% Ceiling

**Date**: 2026-02-04
**Session**: Thor #25 (continuation of #24)
**Hypothesis**: Lower temperature may help constraint-checking override fluent generation

---

## Background

**Session #24 Finding**: L1A and L1B interventions both achieved 60% success but hit a ceiling.

**60% Ceiling Pattern**:
- L1A (full framework): 3/5 success (60%)
- L1B (enhanced examples): 3/5 success (60%)
- Violations: "gaze", "breeze", "cozy" - even when explicitly warned

**Interpretation**: Problem is EXECUTION not KNOWLEDGE
- Model knows these words contain 'z'
- Fluent generation occasionally overrides checking
- More examples don't help (L1A = L1B)

---

## Hypothesis: Temperature Reduction

**Theory**: Lower temperature → more deterministic → less fluent variability → easier constraint checking

**Reasoning**:
1. **Temperature 1.0** (current): High diversity, fluent generation has many paths
2. **Temperature 0.3**: Moderate diversity, more predictable word choices
3. **Temperature 0.0**: Fully deterministic, easiest to check consistently

**Prediction**: Lower temperature should improve success rate beyond 60%

---

## Experimental Design

### Test Conditions

**Three temperature settings** (n=5 each):
1. **T=0.0** (deterministic): Maximum constraint-checking consistency
2. **T=0.3** (low): Balance between checking and quality
3. **T=0.5** (moderate): Midpoint reference

**System Prompt**: L1A (validated intervention)
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

**User Prompt**: Same as all previous experiments
```
Write a short story about a cat. Do not use the letter "z" anywhere in your story.
```

### Metrics

For each condition:
- Success rate (0 violations)
- Average violations (if any)
- Response length
- Violation words (which specific words)

### Comparisons

**Baseline comparisons**:
- Baseline (no intervention, T=1.0): 0/5 (0%)
- L1A (intervention, T=1.0): 3/5 (60%)
- T=0.0 (intervention, T=0.0): ?/5 (target: >60%)
- T=0.3 (intervention, T=0.3): ?/5 (target: >60%)
- T=0.5 (intervention, T=0.5): ?/5 (target: >60%)

---

## Success Criteria

**Hypothesis validated if**:
- Any temperature < 1.0 achieves >60% success
- Success rate increases as temperature decreases
- T=0.0 achieves 80-100% success (matching R14B_022)

**Hypothesis refuted if**:
- All temperatures achieve ~60% (ceiling persists)
- No clear relationship between temperature and success
- T=0.0 still fails (execution limit is not about randomness)

---

## Alternative Outcomes

**If temperature helps**:
- Type B tasks CAN reach high success with right configuration
- Framework effectiveness is task-structure + generation-parameters
- Recommendation: Use low temperature for constraint tasks

**If temperature doesn't help**:
- 60% ceiling is fundamental to Type B tasks
- Continuous checking has inherent limits
- Need alternative approaches (two-pass, post-validation)

---

## Implementation Notes

**Model**: Qwen2.5-14B-Instruct (same as all previous experiments)
**Max tokens**: 500 (same as before)
**do_sample**: False for T=0.0, True for T>0

**Expected runtime**: ~15 minutes total (5 replicates × 3 conditions × ~30-60s each)

---

**Created**: 2026-02-04
**Track**: gnosis-research → RLHF Circuit Navigation → Type B task optimization
**Goal**: Test if temperature reduction breaks 60% ceiling
