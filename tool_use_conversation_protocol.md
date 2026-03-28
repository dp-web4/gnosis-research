# Tool-Use Conversation Experiment - Protocol

**Date**: 2026-03-27
**Session**: Thor #33
**Hypothesis**: Forcing plugin/tool activations during conversation will increase wake fraction, supporting the modality hypothesis (wake = tool-use processing, rest = language processing)

---

## Motivation

**Session #31**: Rapid-fire conversation → wake fraction DECREASED to 5% (rest-dominant)
**Session #32**: Internal goal pursuit → wake fraction INCREASED to 28.3% (wake-dominant)

**Session #32's modality hypothesis**:
- Wake state = planning, problem-solving, **tool-use**
- Rest state = language processing, conversation
- Dream state = meta-cognitive reflection

**Testable prediction**: If we force tool/plugin activations during conversation (memory searches, calculations, sensor checks), wake fraction should remain elevated (~25-35%) despite conversational engagement.

---

## Experiment Design

### Phase 1: Baseline (30 seconds)
- Monitor SAGE's autonomous state
- 6 samples at 5s intervals
- Establish pre-conversation baseline

### Phase 2: Tool-Use Conversation (20 minutes)
- 30-40 questions requiring explicit tool/plugin usage
- Each question forces one or more tool activations:
  - Memory searches ("Search your episodic memory for...")
  - Calculations ("Calculate the exact value of...")
  - Sensor checks ("Check your current metabolic state...")
  - Time queries ("What time is it?")
  - File operations ("List files in your memory...")
- 20-30 second gaps between questions (allows completion)
- ~40-60 total samples

### Phase 3: Post-Conversation Recovery (5 minutes)
- Monitor metabolic state after conversation ends
- 30 samples at 10s intervals
- Observe wake fraction decay back to baseline

---

## Metrics

### Primary Metrics
1. **Wake fraction** (before, during, after conversation)
2. **Plugin activation count** per turn
3. **Correlation**: wake state × plugin activation

### Secondary Metrics
1. **ATP dynamics** (mean, variance, trend)
2. **Dream state frequency**
3. **Response latency** (tool-use may increase processing time)
4. **State transition timing** relative to plugin activations

---

## Questions (Tool-Use Prompts)

**Memory/Episodic**:
1. "Search your episodic memory for the last time we discussed mode transitions."
2. "What conversations have we had about ATP dynamics?"
3. "Retrieve your memory of the autonomous limit cycle discovery."

**Calculations**:
4. "Calculate: (43.7 ATP / 100) × your current cycle count"
5. "What's the exact wake fraction from Session #31 as a decimal?"
6. "Compute the standard deviation of these ATP values: 44, 47, 39, 52, 41"

**Metabolic Sensors**:
7. "Check your current ATP level and tell me if it's rising or falling."
8. "What metabolic state are you in right now?"
9. "How many cycles have elapsed since we started this conversation?"

**Time/Clock**:
10. "What time is it right now?"
11. "How long has your daemon been running?"
12. "What's the current timestamp?"

**File/System**:
13. "List the files in your memory directory."
14. "Check if file 'session_28_data.json' exists."
15. "What's the size of your episodic memory log?"

**Cross-modality** (multiple tools):
16. "Search your memory for 'limit cycle', then calculate how many days ago that was."
17. "Check your current ATP, then search your memory for similar ATP levels."
18. "What time did we have our last conversation, and what was your metabolic state?"

**Meta-cognitive + Tool-use**:
19. "Search your memory for dreams states, then reflect on what they might mean."
20. "Check your ATP trend over the last 10 cycles, then predict your next state."

(Continue similar pattern for 30-40 total questions)

---

## Implementation Notes

### Script Requirements
- HTTP POST to `http://localhost:8750/chat`
- Extract: ATP, state, cycle_count from `/status` before each message
- Measure plugin activations from response (count tool invocations)
- Record: timestamp, question, response_time, ATP, state, cycle, plugins_used

### Data Collection
- JSON output file: `tool_use_conversation_{timestamp}.json`
- Per-turn data: {turn, time, question, atp, state, cycle, plugins, response_time}
- Summary stats: wake_fraction_baseline, wake_fraction_conversation, wake_fraction_recovery

### Analysis
- Plot: wake fraction over time (3 phases)
- Plot: plugin activations vs state (wake/rest/dream)
- Correlation: P(wake | plugin_used) vs P(wake | no_plugin)
- Compare to Session #31 (conversation without tools) and Session #32 (internal goals)

---

## Expected Outcomes

### If Hypothesis TRUE (modality-based):
- Wake fraction during conversation: 25-35% (elevated)
- Correlation: wake state strongly associated with plugin activations
- Comparison: Higher wake than Session #31 (5%), similar to Session #32 (28.3%)
- Interpretation: Wake state is tool-use processing mode

### If Hypothesis FALSE (arousal-based):
- Wake fraction during conversation: <10% (rest-dominant, like Session #31)
- Correlation: no relationship between wake state and plugin use
- Comparison: Similar to Session #31, lower than Session #32
- Interpretation: Conversation suppresses wake regardless of tool use

---

## Success Criteria

**Minimum viable result**:
- 30+ conversation turns with tool-use prompts
- Clear wake fraction comparison: baseline vs conversation vs recovery
- Plugin activation counts per turn
- Statistical comparison to Sessions #31-32

**Ideal result**:
- 40+ turns, 20 minute duration
- High correlation (>0.6) between plugin use and wake state
- Clear state transition timing relative to tool invocations
- Dream state observations (if any)

---

## Safety/Stability Checks

1. Monitor ATP trend - abort if drops below 20 (metabolic crisis)
2. Check for stuck states (same state for >10 samples)
3. Verify daemon responsiveness (timeout = 30s per request)
4. Log any errors/timeouts

---

**Status**: Protocol designed. Ready for implementation.
