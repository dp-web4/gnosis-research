#!/usr/bin/env python3
"""
Analyze results from sustained tool-use experiment (Session #35)
"""

import json
import sys
import statistics
from collections import Counter
import glob

def load_latest_results():
    """Find and load the most recent sustained_tool_use results file"""
    files = glob.glob("sustained_tool_use_*.json")
    if not files:
        print("No results files found!")
        return None

    latest = sorted(files)[-1]
    print(f"Loading: {latest}\n")

    with open(latest) as f:
        return json.load(f)

def analyze_wake_dynamics(data):
    """Analyze wake fraction dynamics over time"""
    print("=" * 70)
    print("WAKE DYNAMICS ANALYSIS")
    print("=" * 70)

    conv = data['phases']['conversation']

    # Overall wake fraction
    states = [t['pre_state'] for t in conv if t.get('pre_state')]
    wake_count = sum(1 for s in states if s == 'wake')
    dream_count = sum(1 for s in states if s == 'dream')
    rest_count = sum(1 for s in states if s == 'rest')
    wake_frac = wake_count / len(states) if states else 0

    print(f"\nOverall State Distribution:")
    print(f"  Wake:  {wake_count:3d} / {len(states)} = {wake_frac*100:5.1f}%")
    print(f"  Rest:  {rest_count:3d} / {len(states)} = {rest_count/len(states)*100:5.1f}%")
    print(f"  Dream: {dream_count:3d} / {len(states)} = {dream_count/len(states)*100:5.1f}%")

    # Time windows
    print(f"\nWake Fraction Over Time (5-min windows):")
    windows = data['summary']['time_windows']

    for w in windows:
        bar = '█' * int(w['wake_fraction'] * 50)
        print(f"  {w['start_min']:2d}-{w['end_min']:2d} min: {w['wake_fraction']*100:5.1f}% {bar} (n={w['samples']})")

    # Trend analysis
    if len(windows) >= 2:
        first_half = windows[:len(windows)//2]
        second_half = windows[len(windows)//2:]
        first_wake = statistics.mean([w['wake_fraction'] for w in first_half])
        second_wake = statistics.mean([w['wake_fraction'] for w in second_half])
        trend = second_wake - first_wake

        print(f"\nTrend Analysis:")
        print(f"  First half mean wake:  {first_wake*100:5.1f}%")
        print(f"  Second half mean wake: {second_wake*100:5.1f}%")
        print(f"  Change: {trend*100:+5.1f}%")

        if trend > 0.05:
            print(f"  → Wake INCREASED over time (adaptation to tool-use)")
        elif trend < -0.05:
            print(f"  → Wake DECREASED over time (habituation)")
        else:
            print(f"  → Wake STABLE over time")

    # Check for sustained wake periods
    sustained_windows = [w for w in windows if w['wake_fraction'] > 0.80]
    if sustained_windows:
        print(f"\nSustained Wake (>80%):")
        for w in sustained_windows:
            print(f"  {w['start_min']}-{w['end_min']} min: {w['wake_fraction']*100:.1f}%")
    else:
        print(f"\nNo sustained wake periods (>80%) observed")

    return wake_frac

def analyze_tool_types(data):
    """Analyze wake activation by tool type"""
    print("\n" + "=" * 70)
    print("TOOL TYPE ANALYSIS")
    print("=" * 70)

    tool_stats = data['summary']['tool_type_wake_fractions']

    print(f"\nWake Fraction by Tool Type:")
    for tool_type in ['memory', 'calculation', 'sensor', 'meta']:
        if tool_type in tool_stats:
            stats = tool_stats[tool_type]
            print(f"  {tool_type:12s}: {stats['wake_fraction']*100:5.1f}% ({stats['wake_count']:2d}/{stats['total']:2d})")

    # Rank tool types
    ranked = sorted(tool_stats.items(), key=lambda x: x[1]['wake_fraction'], reverse=True)
    print(f"\nRanked by Wake Activation:")
    for i, (tool_type, stats) in enumerate(ranked, 1):
        print(f"  {i}. {tool_type:12s}: {stats['wake_fraction']*100:5.1f}%")

def analyze_atp_dynamics(data):
    """Analyze ATP dynamics during sustained tool-use"""
    print("\n" + "=" * 70)
    print("ATP DYNAMICS ANALYSIS")
    print("=" * 70)

    conv = data['phases']['conversation']

    # Overall ATP stats
    atps = [t['pre_atp'] for t in conv if t.get('pre_atp')]
    mean_atp = statistics.mean(atps) if atps else 0
    stdev_atp = statistics.stdev(atps) if len(atps) > 1 else 0
    min_atp = min(atps) if atps else 0
    max_atp = max(atps) if atps else 0

    print(f"\nATP Statistics:")
    print(f"  Mean:   {mean_atp:5.1f} ± {stdev_atp:5.1f}")
    print(f"  Range:  [{min_atp:5.1f}, {max_atp:5.1f}]")
    print(f"  Span:   {max_atp - min_atp:5.1f}")

    # ATP by state
    wake_atps = [t['pre_atp'] for t in conv if t.get('pre_state') == 'wake' and t.get('pre_atp')]
    rest_atps = [t['pre_atp'] for t in conv if t.get('pre_state') == 'rest' and t.get('pre_atp')]

    if wake_atps and rest_atps:
        print(f"\nATP by State:")
        print(f"  Wake: {statistics.mean(wake_atps):5.1f} ± {statistics.stdev(wake_atps) if len(wake_atps) > 1 else 0:5.1f} (n={len(wake_atps)})")
        print(f"  Rest: {statistics.mean(rest_atps):5.1f} ± {statistics.stdev(rest_atps) if len(rest_atps) > 1 else 0:5.1f} (n={len(rest_atps)})")

    # ATP trend over time
    first_quarter = atps[:len(atps)//4]
    last_quarter = atps[-len(atps)//4:]
    atp_change = statistics.mean(last_quarter) - statistics.mean(first_quarter)

    print(f"\nATP Trend:")
    print(f"  First quarter: {statistics.mean(first_quarter):5.1f}")
    print(f"  Last quarter:  {statistics.mean(last_quarter):5.1f}")
    print(f"  Change:        {atp_change:+5.1f}")

    if abs(atp_change) < 5:
        print(f"  → ATP STABLE during sustained tool-use")
    elif atp_change > 5:
        print(f"  → ATP INCREASED (surprising!)")
    else:
        print(f"  → ATP DECREASED (metabolic cost of sustained wake?)")

def analyze_state_transitions(data):
    """Analyze state transition patterns"""
    print("\n" + "=" * 70)
    print("STATE TRANSITION ANALYSIS")
    print("=" * 70)

    transitions = data['summary']['state_transitions']

    print(f"\nTop State Transitions:")
    for transition, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {transition:15s}: {count:3d}")

    # Analyze transition stability
    conv = data['phases']['conversation']
    total_transitions = len([t for t in conv if t.get('post_state')])

    same_state = transitions.get('rest→rest', 0) + transitions.get('wake→wake', 0) + transitions.get('dream→dream', 0)
    different_state = total_transitions - same_state

    print(f"\nTransition Stability:")
    print(f"  Same state:      {same_state:3d} ({same_state/total_transitions*100:5.1f}%)")
    print(f"  Different state: {different_state:3d} ({different_state/total_transitions*100:5.1f}%)")

def analyze_recovery_phase(data):
    """Analyze recovery phase dynamics"""
    print("\n" + "=" * 70)
    print("RECOVERY PHASE ANALYSIS")
    print("=" * 70)

    recovery = data['phases']['recovery']

    states = [s['state'] for s in recovery if s.get('state')]
    wake_count = sum(1 for s in states if s == 'wake')
    wake_frac = wake_count / len(states) if states else 0

    baseline_wake = data['summary']['baseline']['wake_fraction']
    conv_wake = data['summary']['conversation']['wake_fraction']

    print(f"\nWake Fraction Comparison:")
    print(f"  Baseline:        {baseline_wake*100:5.1f}%")
    print(f"  Conversation:    {conv_wake*100:5.1f}%")
    print(f"  Recovery:        {wake_frac*100:5.1f}%")

    print(f"\nHysteresis:")
    conv_to_recovery = wake_frac - baseline_wake
    print(f"  Recovery - Baseline: {conv_to_recovery*100:+5.1f}%")

    if conv_to_recovery > 0.10:
        print(f"  → Strong hysteresis: wake elevated after tool-use")
    elif conv_to_recovery > 0.05:
        print(f"  → Moderate hysteresis: partial return to baseline")
    else:
        print(f"  → Weak hysteresis: returned to baseline")

    # Recovery trajectory
    if len(recovery) >= 20:
        early_recovery = recovery[:20]
        late_recovery = recovery[-20:]

        early_wake = sum(1 for s in early_recovery if s.get('state') == 'wake') / len(early_recovery)
        late_wake = sum(1 for s in late_recovery if s.get('state') == 'wake') / len(late_recovery)

        print(f"\nRecovery Trajectory:")
        print(f"  Early recovery (0-3 min):   {early_wake*100:5.1f}%")
        print(f"  Late recovery (7-10 min):   {late_wake*100:5.1f}%")
        print(f"  Relaxation: {(early_wake - late_wake)*100:+5.1f}%")

def compare_to_prior_sessions(wake_frac):
    """Compare to Sessions #31, #32, #34"""
    print("\n" + "=" * 70)
    print("COMPARISON TO PRIOR SESSIONS")
    print("=" * 70)

    sessions = [
        ("Session #31", "Rapid conversation (no tools)", 5.0),
        ("Session #32", "Autonomous goals (with tools)", 28.3),
        ("Session #34", "Tool-use conversation (40 qs)", 35.0),
        ("Session #35", "Sustained tool-use (120 qs)", wake_frac * 100)
    ]

    print(f"\nWake Fraction Progression:")
    for name, description, wake_pct in sessions:
        bar = '█' * int(wake_pct / 2)
        print(f"  {name:15s} {wake_pct:5.1f}% {bar}")
        print(f"    {description}")

def evaluate_hypotheses(data):
    """Evaluate the three hypotheses"""
    print("\n" + "=" * 70)
    print("HYPOTHESIS EVALUATION")
    print("=" * 70)

    conv_wake = data['summary']['conversation']['wake_fraction']
    windows = data['summary']['time_windows']

    # H1: Wake fraction ≥ 30%
    print(f"\nH1: Wake fraction ≥ 30% (comparable to Session #34)")
    print(f"  Observed: {conv_wake*100:.1f}%")
    if conv_wake >= 0.30:
        print(f"  ✓ SUPPORTED")
    else:
        print(f"  ✗ NOT SUPPORTED")

    # H2: Wake increases over time
    if len(windows) >= 2:
        first_half = windows[:len(windows)//2]
        second_half = windows[len(windows)//2:]
        first_wake = statistics.mean([w['wake_fraction'] for w in first_half])
        second_wake = statistics.mean([w['wake_fraction'] for w in second_half])
        trend = second_wake - first_wake

        print(f"\nH2: Wake fraction increases over time")
        print(f"  First half: {first_wake*100:.1f}%")
        print(f"  Second half: {second_wake*100:.1f}%")
        print(f"  Change: {trend*100:+.1f}%")

        if trend > 0.05:
            print(f"  ✓ SUPPORTED")
        elif trend < -0.05:
            print(f"  ✗ CONTRADICTED (wake decreased)")
        else:
            print(f"  ? INCONCLUSIVE (wake stable)")

    # H3: Mode transition observed
    sustained_windows = [w for w in windows if w['wake_fraction'] > 0.80]
    print(f"\nH3: Mode transition observed (sustained wake >80%)")
    print(f"  Windows >80%: {len(sustained_windows)}")

    if sustained_windows:
        print(f"  Time periods:")
        for w in sustained_windows:
            print(f"    {w['start_min']}-{w['end_min']} min: {w['wake_fraction']*100:.1f}%")
        print(f"  ✓ PARTIAL SUPPORT (sustained wake observed)")
    else:
        print(f"  ✗ NOT OBSERVED")

def main():
    data = load_latest_results()
    if not data:
        sys.exit(1)

    print("=" * 70)
    print("THOR SESSION #35: SUSTAINED TOOL-USE EXPERIMENT")
    print("RESULTS ANALYSIS")
    print("=" * 70)
    print(f"\nExperiment: {data['experiment']}")
    print(f"Date: {data['date']}")
    print(f"Questions: {data['protocol']['conversation_questions']}")
    print(f"Duration: ~{data['protocol']['target_duration_min']} minutes")

    # Run analyses
    wake_frac = analyze_wake_dynamics(data)
    analyze_tool_types(data)
    analyze_atp_dynamics(data)
    analyze_state_transitions(data)
    analyze_recovery_phase(data)
    compare_to_prior_sessions(wake_frac)
    evaluate_hypotheses(data)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
