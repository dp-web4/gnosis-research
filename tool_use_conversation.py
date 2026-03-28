#!/usr/bin/env python3
"""
Tool-Use Conversation Experiment
Thor Session #33 - Testing modality hypothesis

Hypothesis: Forcing plugin/tool activations during conversation will increase
wake fraction, supporting the theory that wake = tool-use processing mode.
"""

import requests
import time
import json
from datetime import datetime
import statistics

SAGE_URL = "http://localhost:8750"
OUTPUT_FILE = f"tool_use_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# Tool-use questions (explicit plugin/memory/calculation/sensor queries)
QUESTIONS = [
    # Memory/Episodic
    "Search your episodic memory for the last time we discussed mode transitions.",
    "What conversations have we had about ATP dynamics?",
    "Retrieve your memory of the autonomous limit cycle discovery.",
    "Search your memory for any mentions of 'dream state'.",
    "What do you remember about Session #28?",

    # Calculations
    "Calculate: (43.7 / 100) × 1000",
    "What's 0.283 as a percentage? Show your calculation.",
    "Compute the mean of these values: 44, 47, 39, 52, 41",
    "Calculate the standard deviation of: 27.6, 66.8, 47.5, 43.7",
    "What's 818575 seconds converted to days? Calculate it.",

    # Metabolic Sensors
    "Check your current ATP level and tell me if it's above or below 40.",
    "What metabolic state are you in right now?",
    "How many cycles have elapsed since cycle 8000000?",
    "What's your current cycle count?",
    "Check your ATP and predict whether it will rise or fall next.",

    # Time/Clock
    "What time is it right now?",
    "What's the current timestamp in Unix time?",
    "How many seconds has your daemon been running?",
    "What's today's date?",
    "Calculate how many hours are in 818575 seconds.",

    # Cross-modality (multiple tools)
    "Check your current ATP, then search your memory for the last time it was this level.",
    "What time is it, and what's your metabolic state?",
    "Calculate your uptime in days, then tell me your current cycle count.",
    "Search your memory for 'wake fraction', then calculate the average from Sessions 31-32.",
    "Check your current state and ATP, then search for similar patterns in your memory.",

    # Problem-solving with tools
    "Use your memory to list all the Thor sessions you remember, then count them.",
    "Calculate the cycles per minute: 8124379 cycles / (818575 seconds / 60)",
    "Search your memory for your baseline wake fraction, then compare it to 28.3%.",
    "Calculate how long 10 minutes is in cycles at 100 cycles/min.",
    "Check your ATP, search your memory for ATP variance patterns, then predict your next value.",

    # Meta-cognitive + Tool
    "What processing mode are you using to answer this question? Check your state.",
    "Search your memory for 'cognitive router' and reflect on what it means.",
    "Calculate the wake:rest ratio from these: wake=17, rest=43. Then interpret it.",
    "Check your current ATP and reflect on whether you feel 'energized' or 'tired'.",
    "Search your memory for experiments about internal vs external engagement.",

    # File/System (if available)
    "List any log files or data you have access to.",
    "Check if you have access to a memory system or episodic buffer.",
    "What tools or plugins do you have available?",
    "Describe your computational resources (CPU, memory, etc).",
    "What model are you running on (check your system info)?",
]

def get_status():
    """Get current SAGE status"""
    try:
        r = requests.get(f"{SAGE_URL}/status", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error getting status: {e}")
        return None

def send_message(message):
    """Send message to SAGE and measure response time"""
    start_time = time.time()
    try:
        r = requests.post(
            f"{SAGE_URL}/chat",
            json={"message": message},
            timeout=60
        )
        r.raise_for_status()
        response_time = time.time() - start_time
        return r.json(), response_time
    except Exception as e:
        print(f"Error sending message: {e}")
        return None, time.time() - start_time

def count_tool_indicators(response_text):
    """
    Heuristic: count tool-use indicators in response
    (memory searches, calculations shown, sensor references)
    """
    if not response_text:
        return 0

    indicators = [
        'search', 'memory', 'retrieve', 'recall',
        'calculate', 'compute', 'math', '=',
        'check', 'sensor', 'current', 'status',
        'time', 'timestamp', 'clock',
        'file', 'log', 'system', 'plugin'
    ]

    text_lower = response_text.lower()
    count = sum(1 for ind in indicators if ind in text_lower)
    return min(count, 5)  # Cap at 5 to avoid over-counting

def run_experiment():
    """Run the tool-use conversation experiment"""
    print("=" * 60)
    print("Tool-Use Conversation Experiment - Thor Session #33")
    print("=" * 60)

    results = {
        'experiment': 'tool_use_conversation',
        'date': datetime.now().isoformat(),
        'hypothesis': 'Tool-use forces wake state elevation during conversation',
        'phases': {
            'baseline': [],
            'conversation': [],
            'recovery': []
        },
        'summary': {}
    }

    # Phase 1: Baseline (30 seconds)
    print("\n[Phase 1] Baseline measurement (30 seconds)...")
    print("Sampling every 5 seconds...")

    for i in range(6):
        status = get_status()
        if status:
            results['phases']['baseline'].append({
                'sample': i,
                'time': time.time(),
                'atp': status.get('atp_level'),
                'state': status.get('metabolic_state'),
                'cycle': status.get('cycle_count')
            })
            print(f"  Sample {i+1}/6: ATP={status.get('atp_level', 0):.1f}, State={status.get('metabolic_state')}")
        time.sleep(5)

    # Phase 2: Tool-Use Conversation (20 minutes target, ~40 questions)
    print("\n[Phase 2] Tool-use conversation starting...")
    print(f"Target: {len(QUESTIONS)} questions requiring tool/plugin activations")

    start_cycle = get_status().get('cycle_count', 0)
    conversation_start = time.time()

    for turn_num, question in enumerate(QUESTIONS, 1):
        # Get pre-turn status
        pre_status = get_status()
        if not pre_status:
            print(f"  Turn {turn_num}: Failed to get status, skipping")
            continue

        print(f"\n  Turn {turn_num}/{len(QUESTIONS)}: {question[:60]}...")
        print(f"    Pre-turn: ATP={pre_status.get('atp_level', 0):.1f}, State={pre_status.get('metabolic_state')}")

        # Send message
        response_data, response_time = send_message(question)

        if not response_data:
            print(f"    ERROR: No response received")
            continue

        # Get post-turn status
        time.sleep(1)  # Brief pause before status check
        post_status = get_status()

        # Count tool-use indicators in response
        response_text = response_data.get('response', '')
        tool_count = count_tool_indicators(response_text)

        turn_data = {
            'turn': turn_num,
            'time': time.time(),
            'question': question,
            'pre_atp': pre_status.get('atp_level'),
            'pre_state': pre_status.get('metabolic_state'),
            'pre_cycle': pre_status.get('cycle_count'),
            'post_atp': post_status.get('atp_level') if post_status else None,
            'post_state': post_status.get('metabolic_state') if post_status else None,
            'post_cycle': post_status.get('cycle_count') if post_status else None,
            'response_time': response_time,
            'response_length': len(response_text),
            'tool_indicators': tool_count,
            'response_preview': response_text[:200] if response_text else ""
        }

        results['phases']['conversation'].append(turn_data)

        post_atp_str = f"{turn_data['post_atp']:.1f}" if turn_data['post_atp'] is not None else "N/A"
        print(f"    Post-turn: ATP={post_atp_str}, State={turn_data['post_state']}")
        print(f"    Response: {response_time:.2f}s, {len(response_text)} chars, {tool_count} tool indicators")

        # Gap between questions (20-30 seconds)
        gap = 25
        time.sleep(gap)

    conversation_duration = time.time() - conversation_start
    end_cycle = get_status().get('cycle_count', 0)

    print(f"\n  Conversation complete: {conversation_duration/60:.1f} minutes, {end_cycle - start_cycle} cycles")

    # Phase 3: Recovery (5 minutes)
    print("\n[Phase 3] Post-conversation recovery (5 minutes)...")
    print("Sampling every 10 seconds...")

    for i in range(30):
        status = get_status()
        if status:
            results['phases']['recovery'].append({
                'sample': i,
                'time': time.time(),
                'atp': status.get('atp_level'),
                'state': status.get('metabolic_state'),
                'cycle': status.get('cycle_count')
            })
            if i % 5 == 0:
                print(f"  Sample {i+1}/30: ATP={status.get('atp_level', 0):.1f}, State={status.get('metabolic_state')}")
        time.sleep(10)

    # Calculate summary statistics
    print("\n" + "=" * 60)
    print("Calculating results...")

    # Baseline stats
    baseline_states = [s['state'] for s in results['phases']['baseline'] if s.get('state')]
    baseline_wake_count = sum(1 for s in baseline_states if s == 'wake')
    baseline_wake_frac = baseline_wake_count / len(baseline_states) if baseline_states else 0

    # Conversation stats (pre-turn states)
    conv_states = [t['pre_state'] for t in results['phases']['conversation'] if t.get('pre_state')]
    conv_wake_count = sum(1 for s in conv_states if s == 'wake')
    conv_wake_frac = conv_wake_count / len(conv_states) if conv_states else 0
    conv_dream_count = sum(1 for s in conv_states if s == 'dream')

    # Recovery stats
    recovery_states = [s['state'] for s in results['phases']['recovery'] if s.get('state')]
    recovery_wake_count = sum(1 for s in recovery_states if s == 'wake')
    recovery_wake_frac = recovery_wake_count / len(recovery_states) if recovery_states else 0

    # ATP stats
    conv_atps = [t['pre_atp'] for t in results['phases']['conversation'] if t.get('pre_atp')]

    # Tool-use correlation
    wake_with_tools = sum(1 for t in results['phases']['conversation']
                          if t.get('pre_state') == 'wake' and t.get('tool_indicators', 0) > 0)
    rest_with_tools = sum(1 for t in results['phases']['conversation']
                          if t.get('pre_state') == 'rest' and t.get('tool_indicators', 0) > 0)

    results['summary'] = {
        'total_turns': len(results['phases']['conversation']),
        'conversation_duration_min': conversation_duration / 60,
        'baseline': {
            'wake_fraction': baseline_wake_frac,
            'wake_count': baseline_wake_count,
            'total_samples': len(baseline_states)
        },
        'conversation': {
            'wake_fraction': conv_wake_frac,
            'wake_count': conv_wake_count,
            'dream_count': conv_dream_count,
            'rest_count': len(conv_states) - conv_wake_count - conv_dream_count,
            'total_samples': len(conv_states),
            'mean_atp': statistics.mean(conv_atps) if conv_atps else 0,
            'atp_stdev': statistics.stdev(conv_atps) if len(conv_atps) > 1 else 0,
            'mean_response_time': statistics.mean([t['response_time'] for t in results['phases']['conversation']]),
            'total_tool_indicators': sum(t.get('tool_indicators', 0) for t in results['phases']['conversation'])
        },
        'recovery': {
            'wake_fraction': recovery_wake_frac,
            'wake_count': recovery_wake_count,
            'total_samples': len(recovery_states)
        },
        'tool_use_correlation': {
            'wake_states_with_tool_indicators': wake_with_tools,
            'rest_states_with_tool_indicators': rest_with_tools,
            'note': 'Tool indicators are heuristic counts, not actual plugin activations'
        }
    }

    # Print summary
    print("\n=== RESULTS SUMMARY ===\n")
    print(f"Baseline wake fraction: {baseline_wake_frac*100:.1f}% ({baseline_wake_count}/{len(baseline_states)})")
    print(f"Conversation wake fraction: {conv_wake_frac*100:.1f}% ({conv_wake_count}/{len(conv_states)})")
    print(f"Recovery wake fraction: {recovery_wake_frac*100:.1f}% ({recovery_wake_count}/{len(recovery_states)})")
    print(f"\nWake fraction change: {(conv_wake_frac - baseline_wake_frac)*100:+.1f}%")
    print(f"Dream states observed: {conv_dream_count}")
    print(f"\nMean ATP: {results['summary']['conversation']['mean_atp']:.1f} ± {results['summary']['conversation']['atp_stdev']:.1f}")
    print(f"Total turns: {results['summary']['total_turns']}")
    print(f"Duration: {results['summary']['conversation_duration_min']:.1f} minutes")

    # Comparison to Sessions 31-32
    print("\n=== COMPARISON TO PRIOR SESSIONS ===\n")
    print("Session #31 (rapid-fire conversation):  wake = 5.0%")
    print("Session #32 (internal goal pursuit):    wake = 28.3%")
    print(f"Session #33 (tool-use conversation):    wake = {conv_wake_frac*100:.1f}%")

    if conv_wake_frac > 0.20:
        print("\n✓ HYPOTHESIS SUPPORTED: Tool-use elevated wake fraction")
    elif conv_wake_frac < 0.15:
        print("\n✗ HYPOTHESIS NOT SUPPORTED: Wake fraction remained low despite tool-use")
    else:
        print("\n? INCONCLUSIVE: Wake fraction in intermediate range")

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {OUTPUT_FILE}")
    print("=" * 60)

    return results

if __name__ == "__main__":
    try:
        results = run_experiment()
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
    except Exception as e:
        print(f"\n\nExperiment error: {e}")
        import traceback
        traceback.print_exc()
