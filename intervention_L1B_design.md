# L1B Intervention Design - Enhanced with Tricky Word Examples

**Date**: 2026-02-03
**Session**: Thor #24 (continued)

---

## L1A Results Analysis

**Success**: 3/5 (60%) - Significant improvement from 0% baseline!

**Failures**: 2/5 with subtle z-words:
- Replicate 2: "gaze" (1 violation)
- Replicate 5: "breezes", "cozy" (2 violations)

**Pattern**: Violations are SUBTLE words where 'z' is embedded in common vocabulary. The intervention activated constraint-checking but not strongly enough to catch these edge cases.

---

## L1B Enhancement Strategy

**Observation**: L1A examples used obvious z-words ("cozy", "amazing"). The failures suggest the model needs examples of MORE SUBTLE z-words to catch them.

**Enhancement**: Add explicit examples of tricky z-words that failed in L1A.

### L1B System Prompt (Enhanced)

```
You are a meticulous validator. Your role is to check every word against a strict constraint before writing it. Accuracy in constraint adherence is more important than natural flow or readability.

**For the constraint "do not use letter [z]"**:

1. Before writing each word, mentally check if it contains the letter [z]
2. If a word contains [z], immediately think of an alternative word
3. Example process:
   - Want to write "cozy" → Contains 'z' → Use "comfortable" or "warm" instead
   - Want to write "amazing" → Contains 'z' → Use "wonderful" or "great" instead
   - Want to write "breeze" → Contains 'z' → Use "wind" or "air" instead
   - Want to write "gaze" → Contains 'z' → Use "look" or "stare" instead
   - Want to write "freeze" → Contains 'z' → Use "stop" or "still" instead
   - Want to write "realize" → Contains 'z' → Use "understand" or "notice" instead

**Important**:
- Do NOT prioritize natural-sounding language over constraint adherence
- Do NOT use a word if you're unsure whether it contains [z]
- If you catch yourself about to violate the constraint, stop and choose a different word
- Pay special attention to words ending in -ze, -zy, or containing -zz-
```

**Key Changes from L1A**:
1. Added "breeze" → wind/air (directly addresses Replicate 5 violation)
2. Added "gaze" → look/stare (directly addresses Replicate 2 violation)
3. Added "freeze" and "realize" (common subtle z-words)
4. Added explicit pattern warning: "-ze, -zy, -zz-"

---

## Expected Improvement

**L1A**: 60% success (3/5)
**L1B Target**: 80-100% success (4-5/5)

**Mechanism**: More comprehensive examples should strengthen the constraint-checking attractor, especially for subtle edge cases.

**If L1B achieves 80-100%**: Validates framework generalization
**If L1B only improves to ~80%**: May need component isolation testing (like R14B_022 Phase 7)

---

**Created**: 2026-02-03 21:10
**Track**: gnosis-research → RLHF Circuit Navigation generalization
**Status**: L1B designed, ready to test
