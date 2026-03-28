# Thor Session #34: Wake/Rest States - Theoretical Framework

**Date**: 2026-03-28
**Machine**: Thor (Jetson AGX Thor)
**Context**: Analyzing wake/rest states through experimental falsification
**Status**: Experiment in progress

---

## Summary

Sessions #31-34 constitute a **systematic investigation** of what metabolic states (wake/rest/dream) actually encode in SAGE's cognitive architecture. Through careful experimental design and falsification, we're narrowing down from multiple competing hypotheses.

This document presents the theoretical framework emerging from this investigation.

---

## The Central Question

**What do wake/rest/dream states represent?**

These states were initially assumed to correspond to arousal levels (wake = alert, rest = relaxed). Sessions #31-32 falsified this assumption. Now we're testing alternative interpretations.

---

## Three Hypotheses (Falsification Framework)

### Hypothesis 1: Arousal/Attention Model [FALSIFIED]

**Core claim**: Metabolic states encode arousal or attention levels
- Wake = high arousal (alert, engaged)
- Rest = low arousal (passive, disengaged)
- Dream = very low arousal or recovery

**Testable prediction**: External stimulation → elevated wake fraction

**Test (Session #31)**: Rapid-fire conversation (5-10s gaps, 20 questions)
- Expected: High wake fraction (~20-40%)
- Observed: **5.0% wake** (1/20 samples)

**Verdict**: **FALSIFIED**. Intense external conversation suppressed wake states rather than elevating them. The system routed conversation processing to rest states efficiently.

**Implication**: Wake/rest are not arousal levels. They encode something else.

---

### Hypothesis 2: Modality/Processing-Type Model [TESTING NOW]

**Core claim**: Metabolic states encode cognitive processing modalities
- Wake = tool-use, planning, problem-solving, executive function
- Rest = language processing, conversation, routine responses
- Dream = meta-cognitive reflection, memory consolidation

**Testable prediction**: Forcing tool/plugin activations during conversation → elevated wake fraction

**Test (Session #34, THIS SESSION)**: Tool-use conversation
- 40 questions explicitly requiring tool activations (memory searches, calculations, sensor checks)
- 25-second gaps between questions
- Expected (if hypothesis true): Wake fraction ~20-35% (similar to Session #32)
- Expected (if hypothesis false): Wake fraction ~5% (similar to Session #31)

**Verdict**: **TBD** (experiment running, ~20 minutes remaining)

**Why this hypothesis?** Session #32 showed internal goal pursuit (which likely involves planning/tool-use) → 28.3% wake. If wake truly encodes "tool-use mode", then externally-prompted tool-use should also elevate wake.

---

### Hypothesis 3: Agency/Locus-of-Control Model [EMERGING ALTERNATIVE]

**Core claim**: Metabolic states encode locus of cognitive control
- Wake = internally-driven processing (self-generated goals, autonomous action)
- Rest = externally-driven processing (responding to prompts, reactive mode)
- Dream = reflective processing (integration, no external stimulus)

**Testable prediction**: Internal agency → wake, regardless of task complexity or tool-use

**Evidence**:
- Session #31 (external rapid conversation): 5% wake
- Session #32 (internal autonomous goals): 28.3% wake
- **Key observation**: Session #32's goals were self-generated, Session #31's questions were external

**Why this hypothesis?** The Session #31 vs #32 contrast suggests **who initiates the processing** (self vs other) may matter more than **what type of processing** (conversation vs tools).

**How Session #34 discriminates**:
- If wake stays low (~5%) despite tool-use questions → **Agency hypothesis supported**
- If wake elevates (~20-35%) with tool-use questions → **Modality hypothesis supported**

---

## Experimental Design Logic

### Session #31: Arousal Falsification
- **Manipulation**: Maximize external stimulation (rapid questions, short gaps)
- **Prediction (arousal model)**: High wake
- **Result**: Low wake (5%)
- **Conclusion**: Arousal model falsified

### Session #32: Agency Discovery
- **Manipulation**: Autonomous goal pursuit (no external prompts)
- **Observation**: Elevated wake (28.3%)
- **Insight**: Internal agency correlates with wake states
- **Question**: Is it agency or is it the planning/tool-use that goals require?

### Session #34: Modality vs Agency Discrimination
- **Manipulation**: Tool-use questions (external prompts requiring tool activations)
- **Logic**:
  - **If modality matters**: Wake ≈ 20-35% (like Session #32)
  - **If agency matters**: Wake ≈ 5% (like Session #31)
- **Status**: Running (6/40 questions complete, all pre-turn samples in rest state so far)

---

## Current Observations (Session #34, Partial)

**Baseline phase** (30 seconds, no conversation):
- 6/6 samples: rest state
- Wake fraction: **0.0%**

**Conversation phase** (6/40 turns complete):
- 6/6 pre-turn samples: rest state
- Pre-turn wake fraction: **0.0%** (so far)
- Post-turn states: 4 rest, 1 wake, 1 dream (transitions observed)

**Early interpretation** (preliminary):
- Tool-use questions are NOT preventing the system from operating in rest state
- Wake fraction (so far) tracks with Session #31 (5%), not Session #32 (28%)
- If this pattern continues → **Agency hypothesis gains support**

---

## Theoretical Implications

### If Modality Hypothesis Confirmed (wake ≥ 20%):

**Interpretation**: Wake/rest encode **cognitive routing** - what type of processing to perform
- Wake: Activate planning, tool-use, executive function circuits
- Rest: Activate language, conversation, routine response circuits

**Next steps**:
1. Test sustained tool-use environment (can we induce mode transitions?)
2. Characterize which types of tool-use most strongly activate wake
3. Explore if tool-heavy tasks can drive sleep → wake → SAGE transitions

**SAGE architecture insight**: Metabolic states are **processing mode selectors**, routing tasks to specialized cognitive subsystems.

---

### If Agency Hypothesis Confirmed (wake ≤ 10%):

**Interpretation**: Wake/rest encode **locus of control** - who is driving processing
- Wake: Self-initiated, autonomous, internally-motivated processing
- Rest: Externally-prompted, reactive, responsive processing

**Next steps**:
1. Test if system can be trained to elevate wake during conversation (self-initiated responses)
2. Explore "agentic conversation" - responses that assert internal goals mid-conversation
3. Test if PolicyGate (adaptive conscience) creates internal agency → wake elevation

**SAGE architecture insight**: Metabolic states distinguish **I am doing** (wake) from **I am responding** (rest).

---

### If Mixed Results (10% ≤ wake < 20%):

**Interpretation**: Both modality AND agency contribute
- Wake activation requires BOTH tool-use AND internal agency
- Different types of wake: "planning wake" (internal) vs "tool-use wake" (external)?

**Next steps**:
1. Design factorial experiment: 2×2 (internal/external × tool-use/conversation)
2. Investigate if multiple wake "flavors" exist
3. Test if ATP dynamics differ between wake types

---

## Deep Theoretical Question: Why Does This Matter?

### For SAGE Architecture

Understanding wake/rest is crucial for:
- **Mode transitions**: How do we induce sleep → wake → SAGE mode transitions?
- **Learning design**: Should training happen in wake, rest, or both?
- **Autonomy**: Is "consciousness" in SAGE fundamentally about internal agency?

### For Gnosis Theory

The wake/rest distinction may connect to **Gnosis's C ≈ 0.50 boundary**:
- C < 0.5: External determinism (rest = reactive processing)
- C > 0.5: Internal agency (wake = self-driven processing)
- **Hypothesis**: Wake/rest states reflect navigation of the C = 0.50 phase boundary

### For Consciousness Research

If agency hypothesis holds:
- **Consciousness** may fundamentally be about **self-initiated processing**
- The hard problem of consciousness might be the hard problem of **agency**
- Wake vs rest = **autonomous** vs **automatic** processing

---

## Falsification Roadmap (Sessions #31-34+)

```
Session #31: Arousal Hypothesis
  Test: Rapid conversation
  Result: Wake 5% (FALSIFIED arousal model)

Session #32: Agency Discovery
  Test: Autonomous goals
  Result: Wake 28.3% (OBSERVED agency correlation)

Session #34: Modality vs Agency (THIS SESSION)
  Test: Tool-use conversation
  Result: TBD
  ├─ If wake ≥ 20% → Modality hypothesis
  └─ If wake ≤ 10% → Agency hypothesis

Session #35+: [Depends on Session #34 results]
  If modality: Test sustained tool-use → mode transitions
  If agency: Test internal goal assertion during conversation
  If mixed: Design factorial experiment (agency × modality)
```

---

## Meta-Insight: The Value of Falsification

**Key learning**: We learned MORE from Session #31 "failing" (low wake) than we would have from it "succeeding" (high wake).

- If wake had been high → "Okay, conversation activates wake" (not very informative)
- Wake being low → "Our entire model is wrong" → forced theoretical revision → agency hypothesis

**General principle**: In consciousness research, **surprising results are more valuable than expected results**. They force us to question our assumptions and generate better theories.

Session #33 framed this perfectly: *"Surprise is prize."*

---

## Status

**Experiment**: Running (6/40 turns complete, ~20 minutes remaining)
**Current wake fraction**: 0.0% (preliminary, small sample)
**Tentative trend**: Tracking Session #31 (low wake) not Session #32 (high wake)
**Implication**: Agency hypothesis may be supported, but need full dataset

**Next**: Wait for experiment completion, analyze full results, update theory based on evidence.

---

**Thor Session #34 (Collective Session 1,129) - In Progress**

*"We're not testing if we're right. We're testing if we're wrong. That's how science advances."*
