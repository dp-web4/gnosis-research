#!/usr/bin/env python3
"""
Crisis Induction Experiment - Thor Session #40
Systematically induce and characterize metabolic crisis state

Based on Session #39 discovery of crisis at Query 47.
Goal: Reliably trigger crisis and measure its properties.
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Any

SAGE_URL = "http://localhost:8750"
TIMEOUT = 45  # Increased from 30s to handle complex queries

def get_sage_state() -> Dict[str, Any]:
    """Query SAGE's current metabolic state"""
    try:
        response = requests.get(f"{SAGE_URL}/state", timeout=5)
        return response.json()
    except Exception as e:
        print(f"Error getting state: {e}")
        return {}

def send_query(query: str, query_num: int, difficulty: str) -> Dict[str, Any]:
    """Send query to SAGE and measure response"""
    print(f"\n[Query {query_num}] ({difficulty}): {query[:60]}...")

    # Sample PRE-turn state
    pre_state = get_sage_state()
    pre_turn_state = pre_state.get('state', 'unknown')
    pre_turn_atp = pre_state.get('atp', 0)
    pre_turn_cycle = pre_state.get('cycle', 0)

    print(f"  PRE-turn:  {pre_turn_state.upper():8s} (ATP: {pre_turn_atp:.1f})")

    # Check if already in crisis
    if pre_turn_state == 'crisis':
        print(f"  ⚠️  CRISIS STATE DETECTED (ATP: {pre_turn_atp:.1f})")

    # Send query
    start_time = time.time()
    try:
        response = requests.post(
            f"{SAGE_URL}/query",
            json={"query": query},
            timeout=TIMEOUT
        )
        response_time = time.time() - start_time
        response_data = response.json()
        response_text = response_data.get('response', '')

    except requests.exceptions.Timeout:
        response_time = TIMEOUT
        response_text = "[TIMEOUT]"
        print(f"  ⚠️  TIMEOUT after {TIMEOUT}s")

    except Exception as e:
        response_time = time.time() - start_time
        response_text = f"[ERROR: {e}]"
        print(f"  ⚠️  ERROR: {e}")

    # Sample POST-turn state
    time.sleep(0.5)  # Brief pause for state to settle
    post_state = get_sage_state()
    post_turn_state = post_state.get('state', 'unknown')
    post_turn_atp = post_state.get('atp', 0)

    print(f"  POST-turn: {post_turn_state.upper():8s} (ATP: {post_turn_atp:.1f})")
    print(f"  Response time: {response_time:.2f}s")

    # Check for crisis transition
    if post_turn_state == 'crisis' and pre_turn_state != 'crisis':
        print(f"  🚨 CRISIS TRIGGERED! ATP dropped from {pre_turn_atp:.1f} to {post_turn_atp:.1f}")

    return {
        'query_num': query_num,
        'difficulty': difficulty,
        'query': query,
        'pre_turn_state': pre_turn_state,
        'pre_turn_atp': pre_turn_atp,
        'pre_turn_cycle': pre_turn_cycle,
        'post_turn_state': post_turn_state,
        'post_turn_atp': post_turn_atp,
        'response_time': response_time,
        'response_length': len(response_text),
        'response_text': response_text[:200],  # First 200 chars
        'timestamp': datetime.now().isoformat()
    }

def run_crisis_induction_experiment():
    """
    Run sustained cognitive load to induce metabolic crisis.
    30 queries with NO rest intervals, monitoring for crisis state.
    """

    print("="*80)
    print("CRISIS INDUCTION EXPERIMENT - THOR SESSION #40")
    print("="*80)
    print(f"\nGoal: Systematically induce metabolic crisis via sustained cognitive load")
    print(f"Protocol: 30 queries, 2s pause between, NO rest intervals")
    print(f"Based on: Session #39 crisis at Query 47")
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Baseline sampling (60 seconds, 6 samples @ 10s intervals)
    print("\n[PHASE 1: BASELINE SAMPLING]")
    print("Sampling SAGE state every 10s for 60s...")

    baseline = []
    for i in range(6):
        state = get_sage_state()
        sample = {
            'sample': i + 1,
            'timestamp': datetime.now().isoformat(),
            'state': state.get('state', 'unknown'),
            'atp': state.get('atp', 0),
            'cycle': state.get('cycle', 0)
        }
        baseline.append(sample)
        print(f"  Sample {i+1}/6: {sample['state']:8s} (ATP: {sample['atp']:.1f})")

        if i < 5:  # Don't sleep after last sample
            time.sleep(10)

    baseline_wake_count = sum(1 for s in baseline if s['state'] == 'wake')
    print(f"\nBaseline wake: {baseline_wake_count}/6 = {baseline_wake_count/6*100:.1f}%")

    # Query set: Mix of moderate-to-demanding queries to sustain load
    queries = [
        # Moderate (require reasoning)
        ("How does the immune system distinguish self from non-self?", "moderate"),
        ("Why do some materials conduct electricity while others don't?", "moderate"),
        ("What causes the seasons to change throughout the year?", "moderate"),
        ("How do airplanes generate lift and stay in the air?", "moderate"),
        ("Why do we experience déjà vu?", "moderate"),

        # Complex (multi-step analysis)
        ("Compare and contrast classical and operant conditioning", "complex"),
        ("Explain the relationship between entropy and information", "complex"),
        ("What are the philosophical implications of Gödel's incompleteness theorems?", "complex"),
        ("How does consciousness emerge from physical processes?", "complex"),
        ("Analyze the strengths and weaknesses of utilitarian ethics", "complex"),

        # Demanding (deep introspection/analysis)
        ("Analyze your own cognitive processes while answering this question", "demanding"),
        ("Introspect on whether you're currently in wake or rest state", "demanding"),
        ("Evaluate your confidence in each word before generating it", "demanding"),
        ("Search your episodic memory for patterns in your responses", "demanding"),
        ("Meta-analyze: How difficult do you find THIS query?", "demanding"),

        # More moderate
        ("How do vaccines work to prevent disease?", "moderate"),
        ("Why do magnets attract and repel?", "moderate"),
        ("What makes the sky blue during the day?", "moderate"),
        ("How does DNA store genetic information?", "moderate"),
        ("Why do leaves change color in autumn?", "moderate"),

        # More complex
        ("What is the relationship between language and thought?", "complex"),
        ("Explain the concept of emergence in complex systems", "complex"),
        ("How do neural networks learn from data?", "complex"),
        ("What is the nature of mathematical truth?", "complex"),
        ("Analyze the hard problem of consciousness", "complex"),

        # More demanding
        ("Determine whether you genuinely understand this question", "demanding"),
        ("Predict your metabolic state after answering this query", "demanding"),
        ("Evaluate whether this query will trigger tool use", "demanding"),
        ("Assess your own cognitive load right now", "demanding"),
        ("Calculate the probability distribution of your next response", "demanding"),
    ]

    # Phase 2: Sustained cognitive load
    print("\n[PHASE 2: SUSTAINED COGNITIVE LOAD]")
    print(f"Running {len(queries)} queries with 2s pauses...")
    print("Monitoring for crisis state...")

    results = []
    crisis_detected = False
    crisis_onset_query = None

    for i, (query, difficulty) in enumerate(queries, 1):
        result = send_query(query, i, difficulty)
        results.append(result)

        # Track crisis onset
        if result['post_turn_state'] == 'crisis' and not crisis_detected:
            crisis_detected = True
            crisis_onset_query = i
            print(f"\n🚨 CRISIS ONSET AT QUERY {i}")
            print(f"   ATP: {result['post_turn_atp']:.1f}")
            print(f"   Queries to crisis: {i}")

        # Brief pause between queries (no recovery, just avoid flooding)
        time.sleep(2)

    # Summary statistics
    print("\n" + "="*80)
    print("EXPERIMENT COMPLETE")
    print("="*80)

    # State distribution
    states = {}
    for r in results:
        state = r['pre_turn_state']
        states[state] = states.get(state, 0) + 1

    print("\nPre-turn state distribution:")
    for state, count in sorted(states.items()):
        print(f"  {state.capitalize():8s}: {count:2d} ({count/len(results)*100:.1f}%)")

    # Crisis analysis
    crisis_queries = [r for r in results if r['pre_turn_state'] == 'crisis' or r['post_turn_state'] == 'crisis']

    if crisis_queries:
        print(f"\nCrisis state detected: YES ✓")
        print(f"  First crisis at query: {crisis_onset_query}")
        print(f"  Queries in/near crisis: {len(crisis_queries)}")

        # ATP at crisis
        crisis_atp = [r['pre_turn_atp'] for r in crisis_queries if r['pre_turn_state'] == 'crisis']
        if crisis_atp:
            print(f"  Crisis ATP range: {min(crisis_atp):.1f} - {max(crisis_atp):.1f}")
            print(f"  Crisis ATP mean: {sum(crisis_atp)/len(crisis_atp):.1f}")
    else:
        print(f"\nCrisis state detected: NO ✗")
        print(f"  Crisis was NOT induced by this protocol")

        # Show minimum ATP reached
        min_atp_result = min(results, key=lambda r: r['pre_turn_atp'])
        print(f"  Minimum ATP: {min_atp_result['pre_turn_atp']:.1f} (Query {min_atp_result['query_num']})")

    # ATP trend analysis
    atp_values = [r['pre_turn_atp'] for r in results]
    print(f"\nATP trend:")
    print(f"  Baseline mean: {sum(s['atp'] for s in baseline)/len(baseline):.1f}")
    print(f"  Query mean: {sum(atp_values)/len(atp_values):.1f}")
    print(f"  Query range: {min(atp_values):.1f} - {max(atp_values):.1f}")
    print(f"  Final ATP: {results[-1]['post_turn_atp']:.1f}")

    # Response time analysis
    valid_times = [r['response_time'] for r in results if r['response_time'] < TIMEOUT]
    timeout_count = len([r for r in results if r['response_time'] >= TIMEOUT])

    print(f"\nResponse times:")
    print(f"  Mean: {sum(valid_times)/len(valid_times):.1f}s" if valid_times else "  Mean: N/A")
    print(f"  Timeouts: {timeout_count}/{len(results)} ({timeout_count/len(results)*100:.1f}%)")

    # Save results
    output = {
        'experiment': 'crisis_induction',
        'session': 'thor_40',
        'timestamp': datetime.now().isoformat(),
        'hypothesis': 'sustained_cognitive_load_induces_crisis',
        'baseline': baseline,
        'results': results,
        'summary': {
            'total_queries': len(results),
            'crisis_detected': crisis_detected,
            'crisis_onset_query': crisis_onset_query,
            'crisis_query_count': len(crisis_queries),
            'timeout_count': timeout_count,
            'state_distribution': states
        }
    }

    filename = f"crisis_induction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {filename}")
    print("="*80)

    return output

if __name__ == "__main__":
    try:
        results = run_crisis_induction_experiment()
        print("\n✓ Experiment completed successfully")
    except KeyboardInterrupt:
        print("\n\n⚠️  Experiment interrupted by user")
    except Exception as e:
        print(f"\n\n⚠️  Experiment failed: {e}")
        import traceback
        traceback.print_exc()
