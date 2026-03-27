#!/usr/bin/env python3
"""
Analyze autonomous goal pursuit experiment results
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime

# Load results
with open('autonomous_goal_pursuit_20260327_151410.json') as f:
    data = json.load(f)

baseline = data['baseline']
post_goal = data['post_goal']
baseline_samples = data['baseline_samples']
post_goal_samples = data['post_goal_samples']

print("=" * 80)
print("AUTONOMOUS GOAL PURSUIT - DETAILED ANALYSIS")
print("=" * 80)

# === Comparison Analysis ===
print("\n[1] STATE DISTRIBUTION COMPARISON")
print(f"\nBaseline (30s autonomous):")
print(f"  Wake:  {baseline['state_fractions']['wake']:6.1%}  ({baseline['state_counts']['wake']}/6 samples)")
print(f"  Rest:  {baseline['state_fractions']['rest']:6.1%}  ({baseline['state_counts']['rest']}/6 samples)")
print(f"  Dream: {baseline['state_fractions']['dream']:6.1%}  ({baseline['state_counts']['dream']}/6 samples)")

print(f"\nPost-Goal (10min autonomous):")
print(f"  Wake:  {post_goal['state_fractions']['wake']:6.1%}  ({post_goal['state_counts']['wake']}/60 samples)")
print(f"  Rest:  {post_goal['state_fractions']['rest']:6.1%}  ({post_goal['state_counts']['rest']}/60 samples)")
print(f"  Dream: {post_goal['state_fractions']['dream']:6.1%}  ({post_goal['state_counts']['dream']}/60 samples)")

wake_change = post_goal['state_fractions']['wake'] - baseline['state_fractions']['wake']
print(f"\nWake fraction change: {wake_change:+.1%} ({'INCREASE' if wake_change > 0 else 'DECREASE'})")

# === ATP Dynamics ===
print("\n[2] ATP DYNAMICS")
print(f"\nBaseline ATP:")
print(f"  Mean:  {baseline['atp_stats']['mean']:.1f} ± {baseline['atp_stats']['std']:.1f}")
print(f"  Range: {baseline['atp_stats']['min']:.1f} - {baseline['atp_stats']['max']:.1f} (Δ = {baseline['atp_stats']['range']:.1f})")

print(f"\nPost-Goal ATP:")
print(f"  Mean:  {post_goal['atp_stats']['mean']:.1f} ± {post_goal['atp_stats']['std']:.1f}")
print(f"  Range: {post_goal['atp_stats']['min']:.1f} - {post_goal['atp_stats']['max']:.1f} (Δ = {post_goal['atp_stats']['range']:.1f})")
print(f"  Trend: {post_goal['atp_trend']:.4f} ATP/second ({'DECLINING' if post_goal['atp_trend'] < 0 else 'RISING'})")
print(f"  Net change: {post_goal['atp_stats']['delta']:+.1f} ATP over 10 minutes")

variance_change = post_goal['atp_stats']['std'] - baseline['atp_stats']['std']
print(f"\nATP variance change: {variance_change:+.1f} (from {baseline['atp_stats']['std']:.1f} to {post_goal['atp_stats']['std']:.1f})")

# === Goal Response Analysis ===
goal_resp = data['goal_response']
print("\n[3] GOAL RESPONSE ANALYSIS")
print(f"\nResponse characteristics:")
print(f"  Time to respond: {goal_resp['response_time_seconds']:.1f}s")
print(f"  Response length: {goal_resp['response_length']} characters")
print(f"  Cycles during response: {goal_resp['cycles_elapsed']}")
print(f"  State transition: {goal_resp['start_state']['state']} -> {goal_resp['end_state']['state']}")
print(f"  ATP cost: {goal_resp['start_state']['atp']:.1f} -> {goal_resp['end_state']['atp']:.1f} (Δ = {goal_resp['end_state']['atp'] - goal_resp['start_state']['atp']:.1f})")

# === Time Series Analysis ===
print("\n[4] TIME SERIES PATTERNS")

# Detect periodicity in post-goal samples
post_atps = [s['atp'] for s in post_goal_samples]
post_states = [s['state'] for s in post_goal_samples]

# Find wake state intervals
wake_indices = [i for i, s in enumerate(post_states) if s == 'wake']
if len(wake_indices) > 1:
    wake_intervals = np.diff(wake_indices)
    print(f"\nWake state occurrence:")
    print(f"  Count: {len(wake_indices)}/60 samples ({len(wake_indices)/60:.1%})")
    print(f"  Mean interval: {np.mean(wake_intervals):.1f} samples")
    print(f"  Interval std: {np.std(wake_intervals):.1f} samples")
    if np.std(wake_intervals) < 2.0:
        print(f"  ⚠️  PERIODIC: Wake states occur at regular intervals")
    else:
        print(f"  ⚠️  IRREGULAR: Wake states not periodic")

# ATP oscillation detection
atp_fft = np.fft.fft(post_atps)
atp_power = np.abs(atp_fft[:len(atp_fft)//2])**2
dominant_freq_idx = np.argmax(atp_power[1:]) + 1  # Skip DC component
period_samples = len(post_atps) / dominant_freq_idx if dominant_freq_idx > 0 else 0

print(f"\nATP oscillation:")
print(f"  Dominant period: ~{period_samples:.1f} samples ({period_samples * 10:.0f} seconds)")
print(f"  Amplitude: {(max(post_atps) - min(post_atps))/2:.1f} ATP")

# === Comparison to Prior Sessions ===
print("\n[5] COMPARISON TO PRIOR SESSIONS")

print(f"\nSession #28 (baseline autonomous, 8 days):")
print(f"  Wake fraction: 33.3%")
print(f"  ATP: 44.0 ± 4.5")
print(f"  State: Solitary Homeostasis limit cycle")

print(f"\nSession #31 (rapid-fire conversation, 8.5 min):")
print(f"  Wake fraction: 5.0% (DECREASE from baseline)")
print(f"  ATP: 47.5 ± 9.7")
print(f"  Interpretation: Efficiency adaptation")

print(f"\nSession #32 (autonomous goal pursuit, 10 min):")
print(f"  Wake fraction: 28.3% (INCREASE from baseline)")
print(f"  ATP: 38.2 ± 7.1")
print(f"  Interpretation: ???")

# === Hypothesis Generation ===
print("\n[6] INTERPRETATION")

if wake_change > 0.05:
    print("\n✓ Wake fraction INCREASED after goal injection")
    print("  • Suggests internal goal pursuit activates wake-state processing")
    print("  • Opposite of rapid-fire conversation (which decreased wake)")
    print("  • Supports hypothesis: wake = active planning/tool-use, rest = language")
elif abs(wake_change) < 0.05:
    print("\n○ Wake fraction UNCHANGED after goal injection")
    print("  • Goal pursuit does not shift metabolic mode")
    print("  • Solitary Homeostasis attractor remains stable")
else:
    print("\n✗ Wake fraction DECREASED after goal injection")
    print("  • Unexpected result - goal pursuit routed to rest-state processing")
    print("  • Similar to rapid-fire conversation adaptation")

if variance_change > 1.0:
    print("\n✓ ATP variance INCREASED significantly")
    print("  • Cognitive load elevated during autonomous processing")
elif abs(variance_change) < 1.0:
    print("\n○ ATP variance STABLE")
    print("  • Goal pursuit did not increase cognitive load")
    print("  • Or: Load balanced by adaptive optimization")

print("\n" + "=" * 80)

# === Generate visualization ===
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Plot 1: ATP trajectory
ax1 = axes[0]
times = [s['elapsed_seconds'] / 60 for s in post_goal_samples]  # Convert to minutes
atps = [s['atp'] for s in post_goal_samples]
colors = ['red' if s['state'] == 'wake' else 'blue' if s['state'] == 'rest' else 'purple' for s in post_goal_samples]

ax1.scatter(times, atps, c=colors, alpha=0.7, s=30)
ax1.axhline(baseline['atp_stats']['mean'], color='gray', linestyle='--', label='Baseline mean', alpha=0.5)
ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('ATP Level')
ax1.set_title('ATP Trajectory Post-Goal (Red=Wake, Blue=Rest)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: State distribution over time
ax2 = axes[1]
state_numeric = [2 if s['state'] == 'wake' else 1 if s['state'] == 'rest' else 0 for s in post_goal_samples]
ax2.plot(times, state_numeric, marker='o', linestyle='-', markersize=4, alpha=0.7)
ax2.set_yticks([0, 1, 2])
ax2.set_yticklabels(['dream', 'rest', 'wake'])
ax2.set_xlabel('Time (minutes)')
ax2.set_ylabel('Metabolic State')
ax2.set_title('State Transitions Post-Goal')
ax2.grid(True, alpha=0.3)

# Plot 3: Comparison bars
ax3 = axes[2]
categories = ['Wake %', 'Rest %', 'Dream %']
baseline_vals = [baseline['state_fractions']['wake']*100, baseline['state_fractions']['rest']*100, baseline['state_fractions']['dream']*100]
postgoal_vals = [post_goal['state_fractions']['wake']*100, post_goal['state_fractions']['rest']*100, post_goal['state_fractions']['dream']*100]

x = np.arange(len(categories))
width = 0.35

ax3.bar(x - width/2, baseline_vals, width, label='Baseline', alpha=0.8)
ax3.bar(x + width/2, postgoal_vals, width, label='Post-Goal', alpha=0.8)
ax3.set_ylabel('Percentage (%)')
ax3.set_title('State Distribution Comparison')
ax3.set_xticks(x)
ax3.set_xticklabels(categories)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('autonomous_goal_pursuit_analysis.png', dpi=150)
print(f"\n[VISUALIZATION] Saved to autonomous_goal_pursuit_analysis.png")
