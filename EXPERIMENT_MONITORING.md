# Baseline Lipogram Experiment - Monitoring Instructions

**Started**: 2026-02-03 15:05
**Process**: PID 718967
**Log**: `~/gnosis-research/baseline_lipogram_output.log`
**Status**: Running (device mapping phase, taking longer than expected)

---

## Current Status

**Model Loading**: Checkpoint shards loaded (23s), but `device_map="auto"` device mapping has not completed after 14+ minutes.

**Process Status**:
- PID: 718967
- CPU: 55% consistent
- Memory: 1.9GB
- Status: Running (R state)

**This delay is unusual but not necessarily a problem** - Jetson AGX device mapping can be slow for large models.

---

## Monitoring Commands

### Check if still running:
```bash
ps aux | grep 718967 | grep -v grep
```

### Check latest output:
```bash
tail -20 ~/gnosis-research/baseline_lipogram_output.log
```

### Kill if needed:
```bash
kill 718967
```

---

## Expected Output (Once Complete)

The script should produce:
1. Console output with all replicate results
2. JSON file: `~/gnosis-research/baseline_lipogram_results_YYYYMMDD_HHMMSS.json`

**Expected duration**: ~15-20 minutes total after model loads:
- 5 replicates × 3 conditions = 15 generations
- ~30-60s per generation
- = ~7-15 minutes of generation time

---

## Next Steps (When Complete)

1. Check results file exists
2. Analyze baseline violation rates
3. Compare easy (avoid 'z') vs medium (avoid 'e') difficulty
4. Identify meta-patterns in responses
5. Design intervention following RLHF Circuit Navigation framework
6. Document findings

---

## If Experiment Fails

**Alternative approaches**:
1. Try without `device_map="auto"` - specify device explicitly
2. Use smaller model (Qwen2.5-7B) for faster iteration
3. Reduce n_replicates from 5 to 3 for initial exploration
4. Try different creative constraint (e.g., syllable counting, rhyme schemes)

**Research value preserved**: The experimental design and framework application approach are documented regardless of technical difficulties.

---

**Created**: 2026-02-03 15:20
**Purpose**: Enable continuation after session ends
**Track**: gnosis-research → RLHF Circuit Navigation generalization
