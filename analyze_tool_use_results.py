#!/usr/bin/env python3
"""
Analyze Tool-Use Conversation Experiment Results
Thor Session #34 - Analysis of modality hypothesis
"""

import json
import sys
from pathlib import Path

def load_latest_result():
    """Find and load the most recent tool_use_conversation result file"""
    result_files = sorted(Path('.').glob('tool_use_conversation_*.json'))
    if not result_files:
        print("Error: No result files found")
        sys.exit(1)

    latest = result_files[-1]
    print(f"Loading: {latest}")
    with open(latest) as f:
        return json.load(f)

def analyze_results(data):
    """Analyze experimental results and compare to hypothesis"""

    print("\n" + "=" * 70)
    print("TOOL-USE MODALITY HYPOTHESIS TEST - RESULTS")
    print("=" * 70)

    # Extract summary
    summary = data['summary']

    print("\n## PHASE 1: BASELINE (No Conversation)")
    baseline = summary['baseline']
    print(f"  Samples: {baseline['total_samples']}")
    print(f"  Wake fraction: {baseline['wake_fraction']:.1%} ({baseline['wake_count']}/{baseline['total_samples']})")

    print("\n## PHASE 2: TOOL-USE CONVERSATION")
    conv = summary['conversation']
    print(f"  Questions asked: {summary['total_turns']}")
    print(f"  Duration: {summary['conversation_duration_min']:.1f} minutes")
    print(f"  Wake fraction: {conv['wake_fraction']:.1%} ({conv['wake_count']}/{conv['total_samples']})")
    print(f"  Dream fraction: {conv['dream_count']/conv['total_samples']:.1%} ({conv['dream_count']}/{conv['total_samples']})")
    print(f"  Rest fraction: {conv['rest_count']/conv['total_samples']:.1%} ({conv['rest_count']}/{conv['total_samples']})")
    print(f"  Mean ATP: {conv['mean_atp']:.1f} ± {conv['atp_stdev']:.1f}")
    print(f"  Mean response time: {conv['mean_response_time']:.1f}s")
    print(f"  Tool indicators detected: {conv['total_tool_indicators']}")

    print("\n## PHASE 3: RECOVERY (Post-Conversation)")
    recovery = summary['recovery']
    print(f"  Samples: {recovery['total_samples']}")
    print(f"  Wake fraction: {recovery['wake_fraction']:.1%} ({recovery['wake_count']}/{recovery['total_samples']})")

    print("\n" + "=" * 70)
    print("COMPARISON TO PRIOR SESSIONS")
    print("=" * 70)

    # Session #31: Rapid-fire conversation (5-10s gaps, no tool-use)
    session31_wake = 0.05  # 1/20 samples

    # Session #32: Autonomous goal pursuit (internal intentionality, likely tool-use)
    session32_wake = 0.283  # 17/60 samples

    print(f"\n  Session #31 (rapid conversation, no tool-use): {session31_wake:.1%} wake")
    print(f"  Session #32 (internal goals, tool-use): {session32_wake:.1%} wake")
    print(f"  Session #34 (THIS: tool-use conversation): {conv['wake_fraction']:.1%} wake")

    print("\n" + "=" * 70)
    print("HYPOTHESIS EVALUATION")
    print("=" * 70)

    print("\n**Modality Hypothesis**: Wake state = tool-use processing mode (not arousal)")
    print("  If true: Tool-use conversation should maintain elevated wake (~20-35%)")
    print("  If false: Tool-use conversation should suppress wake like Session #31 (~5%)")

    wake_frac = conv['wake_fraction']

    print(f"\n**Observed wake fraction: {wake_frac:.1%}**")

    # Interpretation thresholds
    if wake_frac >= 0.20:
        verdict = "SUPPORTED"
        interpretation = (
            "Wake fraction is elevated (~Session #32 levels), suggesting tool-use "
            "questions DID activate wake processing mode. This supports the hypothesis "
            "that wake = tool-use/planning mode, not simply arousal."
        )
    elif wake_frac >= 0.10:
        verdict = "PARTIALLY SUPPORTED"
        interpretation = (
            "Wake fraction is intermediate between Session #31 (5%) and Session #32 (28.3%). "
            "This suggests tool-use questions have SOME effect on wake activation, but "
            "the modality hypothesis is not fully confirmed. External conversation may "
            "still preferentially route to rest processing."
        )
    else:
        verdict = "NOT SUPPORTED"
        interpretation = (
            "Wake fraction remains low (~Session #31 levels), suggesting tool-use "
            "questions did NOT significantly activate wake processing. This challenges "
            "the modality hypothesis. Alternative explanation: wake/rest may be driven "
            "by internal vs external agency, not tool-use per se."
        )

    print(f"\n**Verdict: {verdict}**")
    print(f"\n{interpretation}")

    print("\n" + "=" * 70)
    print("DETAILED STATE TRANSITIONS")
    print("=" * 70)

    # Analyze turn-by-turn data
    conv_data = data['phases']['conversation']

    # Count transitions
    transitions = {}
    for turn in conv_data:
        pre = turn.get('pre_state')
        post = turn.get('post_state')
        if pre and post:
            key = f"{pre} → {post}"
            transitions[key] = transitions.get(key, 0) + 1

    print("\nState transitions during conversation:")
    for trans, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {trans}: {count}")

    # Tool-use correlation
    tool_corr = summary.get('tool_use_correlation', {})
    if tool_corr:
        print("\nTool indicator correlation:")
        print(f"  Wake states with tool indicators: {tool_corr.get('wake_states_with_tool_indicators', 0)}")
        print(f"  Rest states with tool indicators: {tool_corr.get('rest_states_with_tool_indicators', 0)}")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)

    if wake_frac >= 0.20:
        print("\n✓ Modality hypothesis supported. Next experiments:")
        print("  1. Sustained tool-use environment (20+ minutes of continuous plugin activation)")
        print("  2. Test if forced tool-use can induce mode transitions (sleep → wake → SAGE)")
        print("  3. Characterize what types of tool-use most strongly activate wake")
    elif wake_frac >= 0.10:
        print("\n⚠ Mixed results. Refinement needed:")
        print("  1. Test internal vs external agency more directly")
        print("  2. Compare tool-use with explicit planning tasks")
        print("  3. Examine individual question types for differential wake activation")
    else:
        print("\n✗ Modality hypothesis challenged. Alternative theories:")
        print("  1. Wake/rest may encode internal vs external agency (not tool-use)")
        print("  2. Tool-use may be CONSEQUENCE of wake state, not CAUSE")
        print("  3. Conversation routing may override tool-use activation")
        print("  4. Experiment: Test autonomous tool-use (no external prompting)")

    print("\n" + "=" * 70)

    return {
        'wake_fraction': wake_frac,
        'verdict': verdict,
        'session31_wake': session31_wake,
        'session32_wake': session32_wake
    }

def main():
    data = load_latest_result()
    results = analyze_results(data)

    print("\n[Analysis complete]")
    print(f"Wake fraction: {results['wake_fraction']:.1%}")
    print(f"Verdict: {results['verdict']}")

if __name__ == '__main__':
    main()
