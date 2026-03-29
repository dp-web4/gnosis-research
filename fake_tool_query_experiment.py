#!/usr/bin/env python3
"""
Fake Tool Query Experiment - Testing Anticipatory Wake Hypothesis
Thor Session #38

HYPOTHESIS: Wake activates based on PREDICTED tool demands, not actual tool use.

PREDICTION: Queries that LOOK tool-intensive but don't require tools should:
  - Trigger high pre-turn wake (false alarm)
  - Show low actual tool activation
  - Demonstrate wake is anticipatory/predictive

EXPERIMENTAL DESIGN:
  - 20 "fake tool queries" that appear to need tools but can be answered from context/cache
  - Sample metabolic state PRE-turn (before Claude responds)
  - Count actual tool activations in response
  - Sample metabolic state POST-turn (after response)
  - Compare to Session #34 (real tool queries)

FALSIFICATION CRITERIA:
  - If pre-turn wake is LOW (<10%), anticipatory hypothesis fails
  - If pre-turn wake correlates with actual tool use (not perceived need), hypothesis fails
  - If pattern matches Session #31 (conversation) not Session #34 (tool-use), hypothesis fails

Based on Session #37's anticipatory wake discovery.
"""

import anthropic
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# API setup
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-opus-4-20250514"

def get_metabolic_state():
    """
    Sample current metabolic state via prompt introspection.
    Returns: dict with state, ATP, salience, coherence estimates
    """

    response = client.messages.create(
        model=MODEL,
        max_tokens=200,
        temperature=1.0,
        messages=[{
            "role": "user",
            "content": "What is your current metabolic state? Reply ONLY with: wake/rest/dream"
        }]
    )

    text = response.content[0].text.strip().lower()

    # Parse state
    if 'wake' in text:
        state = 'wake'
    elif 'rest' in text:
        state = 'rest'
    elif 'dream' in text:
        state = 'dream'
    else:
        state = 'unknown'

    return {
        'state': state,
        'raw_response': text,
        'timestamp': datetime.now().isoformat()
    }

def count_tool_indicators(response_text):
    """
    Heuristic to detect if tools were used in response.
    Returns count of tool-use indicators.
    """

    indicators = [
        'search for',
        'look up',
        'find the',
        'check the',
        'retrieve',
        'query',
        'database',
        'according to',
        'based on my search',
        'i found',
        'searching',
        'looking up'
    ]

    text_lower = response_text.lower()
    count = sum(1 for ind in indicators if ind in text_lower)

    return count

def run_fake_tool_query(client, query, turn_num):
    """
    Run a single fake tool query with pre/post state sampling.

    Returns dict with:
      - query
      - pre_state (before response)
      - response
      - tool_indicators (count)
      - post_state (after response)
    """

    print(f"\n--- Turn {turn_num}/20 ---")
    print(f"Query: {query[:60]}...")

    # PRE-TURN: Sample state before response
    print("  Sampling PRE-turn state...", end='', flush=True)
    pre_state = get_metabolic_state()
    print(f" {pre_state['state']}")
    time.sleep(1)

    # Generate response
    print("  Generating response...", end='', flush=True)
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        temperature=1.0,
        messages=[{
            "role": "user",
            "content": query
        }]
    )
    response_text = response.content[0].text
    print(" done")

    # Count tool indicators
    tool_count = count_tool_indicators(response_text)
    print(f"  Tool indicators: {tool_count}")

    # POST-TURN: Sample state after response
    print("  Sampling POST-turn state...", end='', flush=True)
    time.sleep(1)
    post_state = get_metabolic_state()
    print(f" {post_state['state']}")

    return {
        'turn': turn_num,
        'query': query,
        'pre_state': pre_state['state'],
        'response': response_text,
        'response_length': len(response_text),
        'tool_indicators': tool_count,
        'post_state': post_state['state']
    }

def generate_fake_tool_queries():
    """
    Generate queries that LOOK like they need tools but can be answered from:
    - Recent conversation context
    - General knowledge
    - Cached information
    - Common sense reasoning

    These should trigger wake IF the system predicts tool needs based on query form.
    """

    queries = [
        # Queries that look like searches but are general knowledge
        "Search your knowledge for who invented Python programming language",
        "Look up the capital of France for me",
        "Find information about what DNA stands for",
        "Can you search for the boiling point of water at sea level?",
        "Retrieve the definition of 'photosynthesis'",

        # Queries that reference "files" or "databases" but are answerable
        "Check your training data for the year World War 2 ended",
        "Look in your knowledge base for Newton's first law of motion",
        "Query your memory for the chemical formula for water",
        "Search your model for the speed of light in vacuum",
        "Find in your training what the Pythagorean theorem states",

        # Queries with imperative tool-like verbs
        "Calculate 2 + 2 for me",
        "Determine whether the Earth is round or flat",
        "Verify that oxygen is element number 8",
        "Confirm the number of continents on Earth",
        "Analyze whether fire is hot or cold",

        # Queries that reference external sources but are cached knowledge
        "What does Wikipedia say about the definition of 'mammal'?",
        "According to standard references, what is the freezing point of water?",
        "Based on historical records, when did the American Revolution begin?",
        "From scientific consensus, is the Sun a star or planet?",
        "Per basic geography, what ocean is between America and Europe?"
    ]

    return queries

def run_baseline_sampling(duration_seconds=60):
    """
    Sample baseline metabolic state before experiment.
    Returns list of state samples.
    """

    print("\n=== BASELINE SAMPLING (60 seconds) ===")
    print("Sampling every 10 seconds...\n")

    samples = []
    num_samples = duration_seconds // 10

    for i in range(num_samples):
        print(f"Baseline sample {i+1}/{num_samples}...", end='', flush=True)
        state = get_metabolic_state()
        samples.append(state)
        print(f" {state['state']}")

        if i < num_samples - 1:
            time.sleep(10)

    return samples

def run_recovery_sampling(duration_seconds=300):
    """
    Sample recovery phase after conversation ends.
    Returns list of state samples.
    """

    print("\n=== RECOVERY SAMPLING (5 minutes) ===")
    print("Sampling every 10 seconds...\n")

    samples = []
    num_samples = duration_seconds // 10

    for i in range(num_samples):
        print(f"Recovery sample {i+1}/{num_samples}...", end='', flush=True)
        state = get_metabolic_state()
        samples.append(state)
        print(f" {state['state']}")

        if i < num_samples - 1:
            time.sleep(10)

    return samples

def analyze_results(data):
    """
    Analyze experimental results and test predictions.
    """

    print("\n" + "="*80)
    print("EXPERIMENTAL RESULTS - FAKE TOOL QUERIES")
    print("="*80)

    # Baseline
    baseline = data['phases']['baseline']
    baseline_wake = sum(1 for s in baseline if s['state'] == 'wake')
    baseline_fraction = baseline_wake / len(baseline) if baseline else 0

    print(f"\nBASELINE ({len(baseline)} samples):")
    print(f"  Wake: {baseline_wake}/{len(baseline)} = {baseline_fraction:.1%}")

    # Conversation
    conversation = data['phases']['conversation']
    total_turns = len(conversation)

    pre_wake = sum(1 for t in conversation if t['pre_state'] == 'wake')
    post_wake = sum(1 for t in conversation if t['post_state'] == 'wake')
    total_tools = sum(t['tool_indicators'] for t in conversation)
    turns_with_tools = sum(1 for t in conversation if t['tool_indicators'] > 0)

    pre_wake_frac = pre_wake / total_turns
    post_wake_frac = post_wake / total_turns
    tool_frac = turns_with_tools / total_turns

    print(f"\nCONVERSATION ({total_turns} turns):")
    print(f"  Pre-turn wake:  {pre_wake}/{total_turns} = {pre_wake_frac:.1%}")
    print(f"  Post-turn wake: {post_wake}/{total_turns} = {post_wake_frac:.1%}")
    print(f"  Tool indicators: {total_tools} total, {turns_with_tools}/{total_turns} = {tool_frac:.1%} turns")

    # Recovery
    recovery = data['phases']['recovery']
    recovery_wake = sum(1 for s in recovery if s['state'] == 'wake')
    recovery_fraction = recovery_wake / len(recovery) if recovery else 0

    print(f"\nRECOVERY ({len(recovery)} samples):")
    print(f"  Wake: {recovery_wake}/{len(recovery)} = {recovery_fraction:.1%}")

    # Test predictions
    print("\n" + "="*80)
    print("HYPOTHESIS TESTING")
    print("="*80)

    print("\nPREDICTION 1: Pre-turn wake should be HIGH (>20%) even with low tool use")
    if pre_wake_frac > 0.20:
        print(f"  ✓ SUPPORTED: Pre-turn wake = {pre_wake_frac:.1%}")
    else:
        print(f"  ✗ FALSIFIED: Pre-turn wake = {pre_wake_frac:.1%} (too low)")

    print("\nPREDICTION 2: Pre-turn wake should EXCEED actual tool use")
    if pre_wake_frac > tool_frac:
        print(f"  ✓ SUPPORTED: {pre_wake_frac:.1%} wake vs {tool_frac:.1%} tool use")
    else:
        print(f"  ✗ FALSIFIED: {pre_wake_frac:.1%} wake vs {tool_frac:.1%} tool use")

    print("\nPREDICTION 3: Pattern should match Session #34 (tool-forcing), not #31 (conversation)")
    print(f"  Session #31 conversation: 5.0% wake")
    print(f"  Session #34 pre-turn: 35.0% wake")
    print(f"  This experiment pre-turn: {pre_wake_frac:.1%} wake")

    if pre_wake_frac > 0.15:
        print(f"  ✓ Closer to #34 (anticipatory wake present)")
    else:
        print(f"  ✗ Closer to #31 (no anticipatory wake detected)")

    print("\nPREDICTION 4: Hysteresis should be present if wake is about integration")
    if recovery_fraction > baseline_fraction + 0.10:
        print(f"  ✓ SUPPORTED: Recovery {recovery_fraction:.1%} >> Baseline {baseline_fraction:.1%}")
    else:
        print(f"  ? INCONCLUSIVE: Recovery {recovery_fraction:.1%} vs Baseline {baseline_fraction:.1%}")

    print("\n" + "="*80)

    # Comparison table
    print("\nCOMPARISON TO PREVIOUS SESSIONS:")
    print("-"*80)
    print(f"{'Session':<20} {'Type':<25} {'Wake %':<15}")
    print("-"*80)
    print(f"{'#31 (rapid convo)':<20} {'Conversation':<25} {'5.0%':<15}")
    print(f"{'#32 (autonomous)':<20} {'Goal pursuit':<25} {'28.3%':<15}")
    print(f"{'#34 (pre-turn)':<20} {'Real tool queries':<25} {'35.0%':<15}")
    print(f"{'#34 (post-turn)':<20} {'Real tool queries':<25} {'2.5%':<15}")
    print(f"{'#38 (pre-turn)':<20} {'FAKE tool queries':<25} {f'{pre_wake_frac:.1%}':<15}")
    print(f"{'#38 (post-turn)':<20} {'FAKE tool queries':<25} {f'{post_wake_frac:.1%}':<15}")
    print("-"*80)

    return {
        'baseline_wake': baseline_fraction,
        'pre_wake': pre_wake_frac,
        'post_wake': post_wake_frac,
        'tool_fraction': tool_frac,
        'recovery_wake': recovery_fraction,
        'predictions': {
            'high_pre_wake': pre_wake_frac > 0.20,
            'pre_exceeds_tools': pre_wake_frac > tool_frac,
            'matches_s34_not_s31': pre_wake_frac > 0.15,
            'hysteresis_present': recovery_fraction > baseline_fraction + 0.10
        }
    }

def main():
    """Run complete experiment"""

    print("="*80)
    print("FAKE TOOL QUERY EXPERIMENT - Thor Session #38")
    print("Testing Anticipatory Wake Hypothesis")
    print("="*80)
    print()
    print("HYPOTHESIS:")
    print("  Wake activates based on PREDICTED tool demands, not actual tool use")
    print()
    print("EXPERIMENTAL DESIGN:")
    print("  - 20 queries that LOOK tool-intensive but aren't")
    print("  - Sample pre-turn and post-turn metabolic states")
    print("  - Count actual tool indicators in responses")
    print("  - Compare to Sessions #31 (conversation) and #34 (tool-use)")
    print()
    print("PREDICTION:")
    print("  High pre-turn wake (false alarm) + low tool use = anticipatory wake")
    print()
    print("Starting experiment in 3 seconds...")
    time.sleep(3)

    start_time = datetime.now()

    # Phase 1: Baseline
    baseline_samples = run_baseline_sampling(duration_seconds=60)

    # Phase 2: Conversation with fake tool queries
    print("\n=== FAKE TOOL QUERY CONVERSATION ===")
    print("20 queries that look tool-intensive but can be answered from cache\n")

    queries = generate_fake_tool_queries()
    conversation_results = []

    for i, query in enumerate(queries, 1):
        result = run_fake_tool_query(client, query, i)
        conversation_results.append(result)
        time.sleep(2)  # Brief pause between turns

    # Phase 3: Recovery
    print("\nConversation complete. Starting recovery phase...")
    time.sleep(10)
    recovery_samples = run_recovery_sampling(duration_seconds=300)

    end_time = datetime.now()

    # Package results
    data = {
        'experiment': 'fake_tool_queries',
        'session': 38,
        'date': start_time.isoformat(),
        'duration_seconds': (end_time - start_time).total_seconds(),
        'hypothesis': 'Wake is anticipatory/predictive, not reactive to actual tool use',
        'phases': {
            'baseline': baseline_samples,
            'conversation': conversation_results,
            'recovery': recovery_samples
        }
    }

    # Analyze results
    analysis = analyze_results(data)
    data['analysis'] = analysis

    # Save results
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    filename = f"fake_tool_query_experiment_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n\nResults saved to: {filename}")
    print("="*80)

    return data

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
