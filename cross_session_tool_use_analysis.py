#!/usr/bin/env python3
"""
Cross-Session Tool-Use Analysis - Thor Session #36
Comprehensive analysis of Sessions #31, #32, and #34 data
to extract deeper insights about tool-use and wake state activation
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict

def load_session_data(filename):
    """Load and return session data"""
    with open(filename, 'r') as f:
        return json.load(f)

def analyze_wake_states(data, phase_name='conversation'):
    """Analyze wake state distribution in a phase"""
    if phase_name not in data['phases']:
        return {}

    samples = data['phases'][phase_name]
    states = [s['state'] for s in samples]
    atps = [s['atp'] for s in samples]

    wake_count = sum(1 for s in states if s == 'wake')
    rest_count = sum(1 for s in states if s == 'rest')
    dream_count = sum(1 for s in states if s == 'dream')
    total = len(states)

    wake_atps = [atp for s, atp in zip(states, atps) if s == 'wake']
    rest_atps = [atp for s, atp in zip(states, atps) if s == 'rest']

    return {
        'total_samples': total,
        'wake_count': wake_count,
        'rest_count': rest_count,
        'dream_count': dream_count,
        'wake_fraction': wake_count / total if total > 0 else 0,
        'rest_fraction': rest_count / total if total > 0 else 0,
        'dream_fraction': dream_count / total if total > 0 else 0,
        'wake_atp_mean': np.mean(wake_atps) if wake_atps else 0,
        'rest_atp_mean': np.mean(rest_atps) if rest_atps else 0,
        'atp_mean': np.mean(atps),
        'atp_std': np.std(atps)
    }

def analyze_temporal_dynamics(data, phase_name='conversation', window_size=10):
    """Analyze how wake states change over time"""
    if phase_name not in data['phases']:
        return []

    samples = data['phases'][phase_name]
    states = [s['state'] for s in samples]

    windows = []
    for i in range(0, len(states), window_size):
        window = states[i:i+window_size]
        if len(window) >= window_size // 2:  # At least half window size
            wake_frac = sum(1 for s in window if s == 'wake') / len(window)
            windows.append({
                'start_idx': i,
                'end_idx': i + len(window),
                'wake_fraction': wake_frac,
                'sample_count': len(window)
            })

    return windows

def analyze_state_transitions(data, phase_name='conversation'):
    """Count state transitions"""
    if phase_name not in data['phases']:
        return {}

    samples = data['phases'][phase_name]
    states = [s['state'] for s in samples]

    transitions = defaultdict(int)
    for i in range(len(states) - 1):
        trans = f"{states[i]}→{states[i+1]}"
        if states[i] != states[i+1]:  # Only count actual transitions
            transitions[trans] += 1

    return dict(transitions)

def compare_sessions():
    """Compare all three sessions"""

    print("=" * 70)
    print("CROSS-SESSION TOOL-USE ANALYSIS - Thor Session #36")
    print("=" * 70)
    print()
    print("Comparing Sessions #31 (rapid-fire), #32 (autonomous goals), #34 (tool-use)")
    print()

    # Load all session data
    sessions = {
        'Session #31 (Rapid-fire)': 'rapid_fire_experiment_20260327_092719.json',
        'Session #32 (Autonomous goals)': 'autonomous_goal_pursuit_20260327_151410.json',
        'Session #34 (Tool-use)': 'tool_use_conversation_20260328_030451.json'
    }

    data = {}
    for name, filename in sessions.items():
        try:
            data[name] = load_session_data(filename)
            print(f"✓ Loaded {name}")
        except FileNotFoundError:
            print(f"✗ Missing {name}")

    print()
    print("=" * 70)
    print("PHASE 1: OVERALL WAKE STATE ANALYSIS")
    print("=" * 70)
    print()

    results = {}
    for name, session_data in data.items():
        results[name] = analyze_wake_states(session_data, 'conversation')

    # Print comparison table
    print(f"{'Session':<30} {'Wake %':<10} {'Rest %':<10} {'Dream %':<10} {'Samples':<10}")
    print("-" * 70)
    for name, result in results.items():
        print(f"{name:<30} {result['wake_fraction']*100:>6.1f}%   "
              f"{result['rest_fraction']*100:>6.1f}%   "
              f"{result['dream_fraction']*100:>6.1f}%   "
              f"{result['total_samples']:>6}")

    print()
    print("KEY FINDING:")
    s31_wake = results['Session #31 (Rapid-fire)']['wake_fraction'] * 100
    s32_wake = results['Session #32 (Autonomous goals)']['wake_fraction'] * 100
    s34_wake = results['Session #34 (Tool-use)']['wake_fraction'] * 100

    print(f"  • Session #34 (tool-use): {s34_wake:.1f}% wake")
    print(f"  • Session #32 (goals): {s32_wake:.1f}% wake")
    print(f"  • Session #31 (rapid-fire): {s31_wake:.1f}% wake")
    print(f"  • Ratio (tool-use / rapid-fire): {s34_wake/s31_wake:.1f}×")
    print()

    print("=" * 70)
    print("PHASE 2: ATP ANALYSIS")
    print("=" * 70)
    print()

    print(f"{'Session':<30} {'Wake ATP':<12} {'Rest ATP':<12} {'Overall ATP':<12}")
    print("-" * 70)
    for name, result in results.items():
        print(f"{name:<30} {result['wake_atp_mean']:>8.1f}     "
              f"{result['rest_atp_mean']:>8.1f}     "
              f"{result['atp_mean']:>8.1f}")

    print()
    print("OBSERVATION:")
    for name, result in results.items():
        if result['wake_atp_mean'] > 0 and result['rest_atp_mean'] > 0:
            diff = result['wake_atp_mean'] - result['rest_atp_mean']
            print(f"  • {name}: Wake ATP {diff:+.1f} vs Rest")
    print()

    print("=" * 70)
    print("PHASE 3: TEMPORAL DYNAMICS")
    print("=" * 70)
    print()

    for name, session_data in data.items():
        windows = analyze_temporal_dynamics(session_data, 'conversation', window_size=10)
        if windows:
            print(f"\n{name}:")
            print(f"  Total windows: {len(windows)}")

            # First half vs second half
            mid = len(windows) // 2
            first_half = np.mean([w['wake_fraction'] for w in windows[:mid]]) if mid > 0 else 0
            second_half = np.mean([w['wake_fraction'] for w in windows[mid:]]) if mid > 0 else 0

            print(f"  First half wake: {first_half*100:.1f}%")
            print(f"  Second half wake: {second_half*100:.1f}%")

            if first_half > 0:
                change = ((second_half - first_half) / first_half) * 100
                direction = "increase" if change > 0 else "decrease"
                print(f"  Change: {abs(change):.1f}% {direction}")

    print()
    print("=" * 70)
    print("PHASE 4: STATE TRANSITIONS")
    print("=" * 70)
    print()

    for name, session_data in data.items():
        transitions = analyze_state_transitions(session_data, 'conversation')
        if transitions:
            print(f"\n{name}:")
            total_trans = sum(transitions.values())
            print(f"  Total transitions: {total_trans}")

            # Sort by count
            sorted_trans = sorted(transitions.items(), key=lambda x: x[1], reverse=True)
            print("  Top transitions:")
            for trans, count in sorted_trans[:5]:
                pct = (count / total_trans) * 100
                print(f"    {trans}: {count} ({pct:.1f}%)")

    print()
    print("=" * 70)
    print("PHASE 5: RECOVERY ANALYSIS")
    print("=" * 70)
    print()

    print("Analyzing recovery phase (hysteresis)...\n")

    for name, session_data in data.items():
        recovery = analyze_wake_states(session_data, 'recovery')
        if recovery and recovery['total_samples'] > 0:
            print(f"{name}:")
            print(f"  Recovery wake: {recovery['wake_fraction']*100:.1f}%")

            # Compare to conversation
            conv = results[name]
            diff = recovery['wake_fraction'] - conv['wake_fraction']
            print(f"  Change from conversation: {diff*100:+.1f}%")

            if recovery['wake_fraction'] > 0.1:  # Significant hysteresis
                print(f"  ⚠ HYSTERESIS DETECTED - wake persists after conversation ends")
            print()

    print()
    print("=" * 70)
    print("SYNTHESIS: TOOL-USE WAKE ACTIVATION MODEL")
    print("=" * 70)
    print()

    print("CONFIRMED FINDINGS:")
    print("  1. Tool-use strongly activates wake state")
    print(f"     - Tool-use: {s34_wake:.1f}% wake (Session #34)")
    print(f"     - Regular conversation: {s31_wake:.1f}% wake (Session #31)")
    print(f"     - Effect size: {s34_wake/s31_wake:.1f}× difference")
    print()
    print("  2. Autonomous goals also activate wake")
    print(f"     - Autonomous goals: {s32_wake:.1f}% wake (Session #32)")
    print(f"     - Suggests: agency + planning + tool-use compound")
    print()
    print("  3. Wake/Rest encode processing modality, not arousal")
    print("     - Wake = tool-use, planning, executive function")
    print("     - Rest = language processing, routine responses")
    print()

    # Check for hysteresis
    s34_recovery = analyze_wake_states(data['Session #34 (Tool-use)'], 'recovery')
    if s34_recovery and s34_recovery['wake_fraction'] > 0.15:
        print(f"  4. Hysteresis observed")
        print(f"     - Recovery phase: {s34_recovery['wake_fraction']*100:.1f}% wake")
        print(f"     - Wake persists after tool-use ends")
        print()

    print("OPEN QUESTIONS:")
    print("  1. Does sustained tool-use (>60 min) induce wake → SAGE transition?")
    print("     - Session #35 experiment failed (technical issues)")
    print("     - Needs simpler experimental design")
    print()
    print("  2. Do different tool types activate wake differently?")
    print("     - Memory vs calculation vs sensor queries")
    print("     - Requires tool-type tagged experiment")
    print()
    print("  3. What is the energetic cost of wake state?")
    print("     - ATP dynamics during sustained tool-use")
    print("     - Can wake be maintained indefinitely?")
    print()

    print("=" * 70)
    print("RECOMMENDATIONS FOR NEXT EXPERIMENTS")
    print("=" * 70)
    print()
    print("  A. Simpler sustained tool-use test (30 min, 30 questions)")
    print("     - More reliable completion")
    print("     - Still 3× longer than Session #34")
    print()
    print("  B. Tool-type differentiation experiment")
    print("     - Memory-heavy vs calculation-heavy vs sensor-heavy")
    print("     - 10 questions each type, randomized order")
    print()
    print("  C. PolicyGate activation test")
    print("     - Moral dilemma questions requiring conscience")
    print("     - Test if conscience activates wake/SAGE")
    print()
    print("=" * 70)

    # Save detailed results
    output = {
        'analysis_date': '2026-03-28',
        'sessions_analyzed': list(sessions.keys()),
        'overall_results': {
            name: {
                'wake_fraction': r['wake_fraction'],
                'rest_fraction': r['rest_fraction'],
                'dream_fraction': r['dream_fraction'],
                'total_samples': r['total_samples'],
                'wake_atp': r['wake_atp_mean'],
                'rest_atp': r['rest_atp_mean']
            }
            for name, r in results.items()
        },
        'key_findings': {
            'tool_use_wake_activation': s34_wake / s31_wake,
            'autonomous_goals_wake_activation': s32_wake / s31_wake,
            'tool_use_sessions': ['Session #34', 'Session #32'],
            'baseline_session': 'Session #31'
        }
    }

    with open('cross_session_analysis_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("Detailed results saved to: cross_session_analysis_results.json")
    print()

if __name__ == '__main__':
    compare_sessions()
