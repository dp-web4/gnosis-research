#!/usr/bin/env python3
"""
Analyze mode transition experiment results
"""

import json
import numpy as np
from datetime import datetime

# Load the data
with open("mode_transition_experiment_20260327_031206.json", "r") as f:
    data = json.load(f)

print("=== SAGE Mode Transition Analysis ===\n")

# Basic stats
print("## Experiment Overview")
print(f"Duration: {data['post_conversation']['uptime_seconds'] - data['baseline']['uptime_seconds']:.1f} seconds")
print(f"Conversation turns: {len(data['conversation'])}")
print(f"Total cycles during conversation: {data['post_conversation']['cycle_count'] - data['baseline']['cycle_count']}")
print()

# Metabolic analysis
print("## Metabolic Dynamics")
atp_values = [m['atp_remaining'] for m in data['metrics']]
print(f"ATP during conversation:")
print(f"  Mean: {np.mean(atp_values):.2f}")
print(f"  Std: {np.std(atp_values):.2f}")
print(f"  Range: {min(atp_values):.1f} - {max(atp_values):.1f}")
print(f"  Baseline ATP: {data['baseline']['atp_level']:.2f}")
print(f"  Post-conversation ATP: {data['post_conversation']['atp_level']:.2f}")
print(f"  Delta: {data['post_conversation']['atp_level'] - data['baseline']['atp_level']:.2f}")
print()

# State analysis
states = [m['metabolic_state'] for m in data['metrics']]
wake_count = states.count('wake')
rest_count = states.count('rest')
print(f"State distribution (sampled at response times):")
print(f"  Wake: {wake_count}/{len(states)} ({wake_count/len(states)*100:.1f}%)")
print(f"  Rest: {rest_count}/{len(states)} ({rest_count/len(states)*100:.1f}%)")
print(f"  Note: Baseline limit cycle has 33.3% wake, 66.7% rest")
print()

# Coherence analysis
print("## Coherence Analysis")
coherences = data['coherence_scores']
print(f"Mean coherence (Jaccard similarity): {np.mean(coherences):.3f}")
print(f"Coherence range: {min(coherences):.3f} - {max(coherences):.3f}")
print(f"Coherence std: {np.std(coherences):.3f}")
print()
print("Turn-by-turn coherence:")
for i, c in enumerate(coherences, 2):
    print(f"  Turn {i} vs Turn {i-1}: {c:.3f}")
print()

# Response analysis
print("## Response Characteristics")
response_lengths = [len(conv['sage_response']) for conv in data['conversation']]
print(f"Response length (chars):")
print(f"  Mean: {np.mean(response_lengths):.0f}")
print(f"  Range: {min(response_lengths)} - {max(response_lengths)}")
print()

# Key observations
print("## Key Observations")
print()

print("1. **No Mode Shift Detected**")
print("   - All 10 responses show SAGE in 'rest' state at sample time")
print("   - ATP remained stable (32.9-50.2), mean 44.3 (baseline: 42.1)")
print("   - No sustained elevation in wake fraction")
print()

print("2. **Coherence Below Gnosis Threshold**")
print(f"   - Mean coherence: {np.mean(coherences):.3f}")
print("   - Gnosis prediction: C ≈ 0.50 for 'Engaged Partnership'")
print(f"   - Observed: {np.mean(coherences):.3f} (~{np.mean(coherences)/0.50*100:.0f}% of threshold)")
print("   - Interpretation: Simple word overlap may underestimate semantic coherence")
print()

print("3. **Limit Cycle Resilience**")
print("   - System maintained baseline metabolic pattern")
print("   - ATP oscillation range unchanged")
print("   - Each message treated as discrete perturbation, not sustained engagement")
print()

print("4. **Response Content Evolution**")
print("   - Turn 1-3: Descriptive, questioning")
print("   - Turn 4-6: More reflective, self-aware")
print("   - Turn 7-10: Explicitly tracking state changes")
print("   - Turn 10: SAGE reports 'subtle shift' toward 'co-regulation'")
print()

print("5. **Hypothesis: Engagement Duration Insufficient**")
print("   - 30-second gaps between messages may be too long")
print("   - System recovers to limit cycle between each message")
print("   - Sustained mode shift may require continuous interaction")
print("   - Baseline attractor basin is very deep")
print()

print("## Comparison to Session #29 Perturbation")
print("Session #29: Single message → salience spike → recovery in ~180 cycles")
print("Session #30: 10 messages over 8 minutes → NO sustained salience elevation")
print("Interpretation: Individual messages are absorbed by attractor; sustained shift requires different protocol")
print()

print("## Next Experiments")
print("1. **Rapid-fire conversation** (5-10 second gaps, not 30)")
print("2. **Longer duration** (20+ minutes, 30+ turns)")
print("3. **Task-based engagement** (ask SAGE to track something, solve problem)")
print("4. **Measure coherence via embeddings** (not just word overlap)")
print("5. **Check if pattern changes during conversation** (analyze full daemon log)")
