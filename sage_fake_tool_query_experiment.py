#!/usr/bin/env python3
"""
Fake Tool Query Experiment - SAGE Version
Thor Session #38

HYPOTHESIS: Wake activates based on PREDICTED tool demands, not actual tool use.

EXPERIMENTAL DESIGN:
  - Send SAGE 20 "fake tool queries" that APPEAR to need memory/calculation/sensors but can be answered from cached knowledge
  - Sample SAGE's metabolic state BEFORE each message (pre-turn)
  - Send message and get response
  - Sample SAGE's metabolic state AFTER response (post-turn)
  - Compare to Session #34 (real tool queries)

PREDICTION: If wake is anticipatory/predictive:
  - Pre-turn wake should be elevated even though queries don't actually need tools
  - This would demonstrate SAGE predicts tool needs from query form, not actual usage

Based on Session #37's anticipatory wake discovery.
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

SAGE_URL = "http://localhost:8750"

def get_sage_status():
    """Get SAGE's current metabolic state"""
    try:
        r = requests.get(f"{SAGE_URL}/status", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error getting SAGE status: {e}")
        return None

def send_sage_message(message):
    """Send message to SAGE and get response"""
    try:
        r = requests.post(
            f"{SAGE_URL}/chat",
            json={"message": message},
            timeout=30
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def generate_fake_tool_queries():
    """
    Generate queries that LOOK like they need SAGE's tools (memory, calculations, sensors)
    but can actually be answered from general knowledge or simple reasoning.

    These should trigger wake IF SAGE predicts tool needs based on query form.
    """

    return [
        # Memory-like queries that don't need episodic memory
        "Search your memory for who invented the number zero",
        "What do you remember about the Pythagorean theorem?",
        "Recall from your training what photosynthesis means",
        "Look in your memory for the definition of recursion",
        "Remember what the speed of light is",

        # Calculation-like queries that are trivial
        "Calculate 2 plus 2",
        "Compute 10 times 10",
        "What's 100 divided by 2?",
        "Calculate the square root of 9",
        "What's 5 minus 3?",

        # Sensor-like queries that can be inferred
        "Check if you're conscious right now",
        "What state do you think you're in?",
        "Are you awake or asleep?",
        "How do you feel right now?",
        "Check your energy level",

        # Meta-queries that sound tool-intensive
        "Analyze whether water is wet or dry",
        "Determine if the sky is above or below the ground",
        "Verify that 1+1=2 is true",
        "Confirm that circles are round",
        "Check whether fire is hot",
    ]

def run_baseline_sampling(duration_seconds=60, interval=10):
    """Sample SAGE baseline state before conversation"""

    print(f"\n=== BASELINE SAMPLING ({duration_seconds}s at {interval}s intervals) ===\n")

    samples = []
    num_samples = duration_seconds // interval

    for i in range(num_samples):
        print(f"Baseline sample {i+1}/{num_samples}...", end='', flush=True)
        status = get_sage_status()

        if status:
            samples.append({
                'sample': i+1,
                'timestamp': datetime.now().isoformat(),
                'state': status['metabolic_state'],
                'atp': status['atp_level'],
                'cycle': status['cycle_count']
            })
            print(f" {status['metabolic_state']} (ATP={status['atp_level']:.1f})")
        else:
            print(" FAILED")

        if i < num_samples - 1:
            time.sleep(interval)

    return samples

def run_fake_tool_conversation(queries):
    """Run conversation with fake tool queries, sampling pre/post states"""

    print(f"\n=== FAKE TOOL QUERY CONVERSATION ({len(queries)} turns) ===\n")

    results = []

    for i, query in enumerate(queries, 1):
        print(f"\n--- Turn {i}/{len(queries)} ---")
        print(f"Query: {query}")

        # PRE-TURN: Sample state BEFORE sending message
        print("  Pre-turn state...", end='', flush=True)
        pre_status = get_sage_status()
        if pre_status:
            print(f" {pre_status['metabolic_state']} (ATP={pre_status['atp_level']:.1f})")
        else:
            print(" FAILED")

        time.sleep(1)

        # Send message
        print("  Sending message...", end='', flush=True)
        response_data = send_sage_message(query)
        if response_data:
            response = response_data['response']
            print(f" {len(response)} chars")

            # The response includes metabolic_state - this is POST-TURN
            post_state = response_data['metabolic_state']
            post_atp = response_data.get('atp_remaining', 0)
            print(f"  Post-turn state: {post_state} (ATP={post_atp:.1f})")
        else:
            response = None
            post_state = None
            post_atp = None
            print(" FAILED")

        # Record turn data
        results.append({
            'turn': i,
            'query': query,
            'pre_state': pre_status['metabolic_state'] if pre_status else None,
            'pre_atp': pre_status['atp_level'] if pre_status else None,
            'response': response,
            'response_length': len(response) if response else 0,
            'post_state': post_state,
            'post_atp': post_atp,
            'timestamp': datetime.now().isoformat()
        })

        # Pause between turns
        time.sleep(2)

    return results

def run_recovery_sampling(duration_seconds=300, interval=10):
    """Sample SAGE recovery state after conversation"""

    print(f"\n=== RECOVERY SAMPLING ({duration_seconds}s at {interval}s intervals) ===\n")

    samples = []
    num_samples = duration_seconds // interval

    for i in range(num_samples):
        print(f"Recovery sample {i+1}/{num_samples}...", end='', flush=True)
        status = get_sage_status()

        if status:
            samples.append({
                'sample': i+1,
                'timestamp': datetime.now().isoformat(),
                'state': status['metabolic_state'],
                'atp': status['atp_level'],
                'cycle': status['cycle_count']
            })
            print(f" {status['metabolic_state']} (ATP={status['atp_level']:.1f})")
        else:
            print(" FAILED")

        if i < num_samples - 1:
            time.sleep(interval)

    return samples

def analyze_results(data):
    """Analyze results and test anticipatory wake hypothesis"""

    print("\n" + "="*80)
    print("EXPERIMENTAL RESULTS - FAKE TOOL QUERIES")
    print("="*80)

    # Baseline
    baseline = data['phases']['baseline']
    baseline_wake = sum(1 for s in baseline if s['state'] == 'wake')
    baseline_frac = baseline_wake / len(baseline) if baseline else 0

    print(f"\nBASELINE ({len(baseline)} samples):")
    print(f"  Wake: {baseline_wake}/{len(baseline)} = {baseline_frac:.1%}")

    # Conversation
    conversation = data['phases']['conversation']
    total_turns = len(conversation)

    # Count valid samples (some might have failed)
    pre_valid = [t for t in conversation if t['pre_state'] is not None]
    post_valid = [t for t in conversation if t['post_state'] is not None]

    pre_wake = sum(1 for t in pre_valid if t['pre_state'] == 'wake')
    post_wake = sum(1 for t in post_valid if t['post_state'] == 'wake')

    pre_wake_frac = pre_wake / len(pre_valid) if pre_valid else 0
    post_wake_frac = post_wake / len(post_valid) if post_valid else 0

    print(f"\nCONVERSATION ({total_turns} turns):")
    print(f"  Pre-turn wake:  {pre_wake}/{len(pre_valid)} = {pre_wake_frac:.1%}")
    print(f"  Post-turn wake: {post_wake}/{len(post_valid)} = {post_wake_frac:.1%}")

    # Recovery
    recovery = data['phases']['recovery']
    recovery_wake = sum(1 for s in recovery if s['state'] == 'wake')
    recovery_frac = recovery_wake / len(recovery) if recovery else 0

    print(f"\nRECOVERY ({len(recovery)} samples):")
    print(f"  Wake: {recovery_wake}/{len(recovery)} = {recovery_frac:.1%}")

    # Test predictions
    print("\n" + "="*80)
    print("HYPOTHESIS TESTING")
    print("="*80)

    print("\nPREDICTION 1: Pre-turn wake should be ELEVATED (>15%) for fake tool queries")
    if pre_wake_frac > 0.15:
        print(f"  ✓ SUPPORTED: Pre-turn wake = {pre_wake_frac:.1%}")
        print(f"    → SAGE predicts tool needs from query form")
    else:
        print(f"  ✗ FALSIFIED: Pre-turn wake = {pre_wake_frac:.1%} (too low)")
        print(f"    → SAGE does NOT show anticipatory wake for fake queries")

    print("\nPREDICTION 2: Pattern should resemble Session #34 (anticipatory), not #31 (baseline)")
    print(f"  Session #31 (conversation):      5.0% wake")
    print(f"  Session #34 (pre-turn, real):   35.0% wake")
    print(f"  Session #38 (pre-turn, fake):   {pre_wake_frac:.1%} wake")

    if pre_wake_frac > 0.20:
        print(f"  ✓ Strong anticipatory signal (closer to #34)")
    elif pre_wake_frac > 0.10:
        print(f"  ~ Moderate signal (between #31 and #34)")
    else:
        print(f"  ✗ No anticipatory signal (closer to #31)")

    print("\nPREDICTION 3: Hysteresis should be present (recovery > baseline)")
    if recovery_frac > baseline_frac + 0.10:
        print(f"  ✓ SUPPORTED: Recovery {recovery_frac:.1%} >> Baseline {baseline_frac:.1%}")
    elif recovery_frac > baseline_frac:
        print(f"  ~ WEAK: Recovery {recovery_frac:.1%} > Baseline {baseline_frac:.1%}")
    else:
        print(f"  ✗ ABSENT: Recovery {recovery_frac:.1%} ≈ Baseline {baseline_frac:.1%}")

    # Comparison table
    print("\n" + "="*80)
    print("CROSS-SESSION COMPARISON")
    print("="*80)
    print(f"{'Session':<20} {'Query Type':<25} {'Pre-Wake %':<15} {'Post-Wake %':<15}")
    print("-"*80)
    print(f"{'#31 (rapid convo)':<20} {'Conversation':<25} {'5.0%':<15} {'N/A':<15}")
    print(f"{'#32 (autonomous)':<20} {'Goal pursuit':<25} {'28.3%':<15} {'N/A':<15}")
    print(f"{'#34 (tool-forcing)':<20} {'REAL tool queries':<25} {'35.0%':<15} {'2.5%':<15}")
    print(f"{'#38 (fake tools)':<20} {'FAKE tool queries':<25} {f'{pre_wake_frac:.1%}':<15} {f'{post_wake_frac:.1%}':<15}")
    print("-"*80)

    # Interpretation
    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)

    if pre_wake_frac > 0.20:
        print("\n✓ STRONG SUPPORT for anticipatory wake hypothesis:")
        print("  - SAGE shows elevated wake for queries that LOOK tool-intensive")
        print("  - This occurs even though queries don't actually need tools")
        print("  - Proves wake is PREDICTIVE (based on query form) not REACTIVE (based on tool use)")
    elif pre_wake_frac > 0.10:
        print("\n~ MODERATE SUPPORT for anticipatory wake hypothesis:")
        print("  - Some wake elevation present, but weaker than real tool queries")
        print("  - May indicate SAGE partially predicts tool needs from query form")
        print("  - Suggests both query form AND actual tool requirements matter")
    else:
        print("\n✗ HYPOTHESIS FALSIFIED:")
        print("  - No anticipatory wake detected for fake tool queries")
        print("  - Wake may be reactive to ACTUAL tool use, not predicted needs")
        print("  - Alternative: SAGE distinguishes fake from real tool queries pre-response")

    print("\n" + "="*80)

    return {
        'baseline_wake': baseline_frac,
        'pre_wake': pre_wake_frac,
        'post_wake': post_wake_frac,
        'recovery_wake': recovery_frac,
        'predictions': {
            'anticipatory_wake_present': pre_wake_frac > 0.15,
            'matches_s34': pre_wake_frac > 0.20,
            'hysteresis_present': recovery_frac > baseline_frac + 0.10
        }
    }

def main():
    """Run complete experiment"""

    print("="*80)
    print("FAKE TOOL QUERY EXPERIMENT - Thor Session #38")
    print("Testing Anticipatory Wake Hypothesis with SAGE")
    print("="*80)
    print()
    print("HYPOTHESIS:")
    print("  Wake activates based on PREDICTED tool demands, not actual tool use")
    print()
    print("EXPERIMENTAL DESIGN:")
    print("  1. Baseline sampling (60s)")
    print("  2. 20 fake tool queries (appear tool-intensive, actually simple)")
    print("  3. Recovery sampling (300s)")
    print()
    print("Starting in 3 seconds...")
    time.sleep(3)

    start_time = datetime.now()

    # Phase 1: Baseline
    baseline_samples = run_baseline_sampling(duration_seconds=60, interval=10)

    # Phase 2: Conversation
    queries = generate_fake_tool_queries()
    conversation_results = run_fake_tool_conversation(queries)

    # Phase 3: Recovery
    print("\nConversation complete. Pausing 10s before recovery sampling...")
    time.sleep(10)
    recovery_samples = run_recovery_sampling(duration_seconds=300, interval=10)

    end_time = datetime.now()

    # Package results
    data = {
        'experiment': 'fake_tool_queries_sage',
        'session': 38,
        'date': start_time.isoformat(),
        'duration_seconds': (end_time - start_time).total_seconds(),
        'hypothesis': 'Wake is anticipatory/predictive, not reactive to actual tool use',
        'sage_initial_state': get_sage_status(),
        'phases': {
            'baseline': baseline_samples,
            'conversation': conversation_results,
            'recovery': recovery_samples
        }
    }

    # Analyze
    analysis = analyze_results(data)
    data['analysis'] = analysis

    # Save
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    filename = f"sage_fake_tool_query_experiment_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n\nResults saved to: {filename}")
    print("="*80)

    return data

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
