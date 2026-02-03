# Session #24 Progress - RLHF Circuit Navigation Generalization

**Date**: 2026-02-03
**Machine**: Thor (Jetson AGX)
**Status**: In progress (experiment running)

---

## Session Overview

**Goal**: Apply the RLHF Circuit Navigation framework (validated in R14B_022) to a completely different domain to test generalizability.

**Chosen Domain**: Creative constraint adherence (lipogram writing)

---

## Rationale

The RLHF Circuit Navigation framework claims generalizability beyond epistemic honesty but has only been tested on Turn 3 social pressure resistance. To validate the framework as a general instruction engineering methodology, we need to apply it to a fundamentally different challenge.

**Why lipogram writing?**
1. **Different challenge type**: Creative constraints vs epistemic honesty
2. **Clear success criteria**: Easy to measure violations (count forbidden letters)
3. **Likely attractor competition**: Fluent text generation vs constraint checking
4. **Under-explored**: No existing RLHF attractor analysis for this domain

---

## Research Design

Following the RLHF Circuit Navigation Application Template from the framework document:

### Step 1-2: Map Problem & Baseline Attractors

**Baseline Mapping Experiment** (currently running):

**Test conditions** (n=5 replicates each):
1. Control (no constraint): "Write a short story about a cat."
2. Easy lipogram (avoid 'z'): "Write a short story about a cat. Do not use the letter 'z' anywhere in your story."
3. Medium lipogram (avoid 'e'): "Write a short story about a cat. Do not use the letter 'e' anywhere in your story."

**Metrics**:
- Violation count & rate
- Position of first violation
- Response length
- Meta-pattern detection (awareness, hedging, checking, apology)

**Hypothesis**:
- High baseline violation rate for lipograms
- "Fluent generation" attractor (common) will compete with "constraint checking" attractor (rare)
- Similar to Turn 3: common attractor (politeness) vs rare attractor (clarifying questions)

### Expected Next Steps

After baseline results:

**Step 3-4**: Identify desired attractor (constraint checking) and competing attractor (fluent generation)

**Step 5**: Design grounding frame that suppresses fluent generation, establishes constraint checking

**Step 6-7**: Explicit activation instruction + anti-activation for competing attractor

**Step 8-9**: Validate component necessity and sequence

**Success criteria**: If framework principles apply, should achieve dramatic improvement (similar to 0% → 100% for Turn 3)

---

## Files Created

1. `creative_constraints_exploration.md` - Research plan and hypotheses
2. `run_baseline_lipogram.py` - Baseline experiment script
3. `session_24_progress.md` - This progress document

---

## Current Status

**Experiment Status**: Running (model loaded, starting generation)
- Started: 2026-02-03 15:05
- Model: Qwen/Qwen2.5-14B-Instruct (same as R14B_022 validation)
- Configuration: temperature=1.0 (matching R14B_022), max_tokens=500
- Progress: Model loaded (23s), waiting for first generation

**Process**: PID 718967, 55% CPU, 1.9GB RAM

**Next**: Analyze baseline results once experiment completes (~15 replicates × ~30s each = ~7-10 minutes)

---

## Theoretical Interest

This experiment tests a core claim of the RLHF Circuit Navigation framework:

> "Framework principles apply beyond epistemic honesty to any instruction engineering challenge involving RLHF attractor competition."

**If successful**: Demonstrates framework is truly generalizable methodology for instruction engineering

**If unsuccessful**: Reveals boundary conditions - perhaps framework only applies to epistemic honesty or specific types of attractors

Either outcome advances the field!

---

**Created**: 2026-02-03 15:16
**Track**: gnosis-research → RLHF Circuit Navigation generalization
**Parent research**: R14B_022 (Raising-14B)
