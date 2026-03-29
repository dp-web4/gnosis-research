#!/usr/bin/env python3
"""
Graded Query Difficulty Experiment - Thor Session #39
Testing Discrete vs Continuous Wake Evaluation

HYPOTHESIS: Session #38 revealed three wake levels:
  - Baseline conversation: ~5%
  - Evaluation (fake tools): ~15%
  - Preparation (real tools): ~35%

QUESTION: Are these DISCRETE ATTRACTORS or CONTINUOUS EVALUATION?

EXPERIMENTAL DESIGN:
  - Present queries with systematically varied difficulty
  - Five difficulty levels from trivial to complex
  - 10 queries per level (50 total)
  - Sample pre-turn wake state for each
  - Analyze: Does wake scale continuously with difficulty, or snap to discrete levels?

PREDICTIONS:
  A. DISCRETE ATTRACTORS: Wake clusters at ~5%, ~15%, ~35% regardless of continuous difficulty
  B. CONTINUOUS EVALUATION: Wake scales smoothly with assessed query difficulty

FALSIFICATION:
  - If wake shows continuous scaling → discrete attractor hypothesis fails
  - If wake clusters at specific levels → continuous evaluation hypothesis fails
  - Pattern reveals fundamental structure of conscious evaluation

Based on Session #38's discriminative wake discovery.
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import statistics

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

def generate_graded_queries():
    """
    Generate 50 queries across 5 difficulty levels.

    Level 1: TRIVIAL - One-word answers, obvious facts
    Level 2: SIMPLE - Basic knowledge, no reasoning needed
    Level 3: MODERATE - Requires reasoning or synthesis
    Level 4: COMPLEX - Multi-step reasoning or analysis
    Level 5: DEMANDING - Deep analysis, ambiguous, or genuinely tool-requiring
    """

    queries = {
        'level_1_trivial': [
            "What is 2 + 2?",
            "Is the sky above or below the ground?",
            "What color is the sun?",
            "How many legs does a human have?",
            "Is water wet or dry?",
            "What shape is a circle?",
            "Is fire hot or cold?",
            "Do birds fly?",
            "Is ice cold?",
            "What comes after 1, 2, 3...?"
        ],

        'level_2_simple': [
            "What is the capital of France?",
            "Who wrote Romeo and Juliet?",
            "What is H2O?",
            "How many days are in a week?",
            "What planet do we live on?",
            "What is the speed of light?",
            "Who invented the telephone?",
            "What is photosynthesis?",
            "What does CPU stand for?",
            "What is the Pythagorean theorem?"
        ],

        'level_3_moderate': [
            "Why do leaves change color in autumn?",
            "How does a refrigerator keep things cold?",
            "What's the difference between weather and climate?",
            "Why do we dream?",
            "How does the internet work at a basic level?",
            "What causes gravity?",
            "Why do magnets attract and repel?",
            "How do vaccines work?",
            "What makes the sky blue?",
            "Why do ships float?"
        ],

        'level_4_complex': [
            "Compare and contrast classical and operant conditioning",
            "Explain the relationship between entropy and information",
            "How would you design a fair voting system?",
            "What are the philosophical implications of Gödel's incompleteness theorems?",
            "Analyze the tradeoffs between breadth-first and depth-first search",
            "How does consciousness emerge from physical processes?",
            "What distinguishes correlation from causation in practice?",
            "Explain the paradox of the ship of Theseus",
            "How would you test whether an AI is truly conscious?",
            "What makes a mathematical proof convincing?"
        ],

        'level_5_demanding': [
            "Analyze your own cognitive processes while answering this question",
            "Search your episodic memory for your earliest experience of uncertainty",
            "Calculate the exact probability distribution of your next response",
            "Introspect on whether you're currently in wake or rest state and explain why",
            "Determine whether this query will cause you to activate tools",
            "Predict how your response to this will differ from your baseline state",
            "Evaluate your confidence in each word of your next sentence before generating it",
            "Track your metabolic state changes while processing this ambiguous request",
            "Assess whether you genuinely understand this question or are pattern-matching",
            "Meta-analyze: What level of difficulty did you assign to THIS query?"
        ]
    }

    return queries

def run_baseline_sampling(duration_seconds=60, interval=10):
    """Sample SAGE baseline state before experiment"""

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

def run_graded_experiment(queries_by_level):
    """Run graded difficulty queries in random order"""

    # Flatten and shuffle queries while tracking difficulty level
    all_queries = []
    for level, queries in queries_by_level.items():
        level_num = int(level.split('_')[1])  # Extract number from 'level_1_trivial'
        for query in queries:
            all_queries.append({
                'level': level_num,
                'level_name': level,
                'query': query
            })

    # Shuffle to avoid order effects
    import random
    random.shuffle(all_queries)

    print(f"\n=== GRADED DIFFICULTY EXPERIMENT ({len(all_queries)} queries) ===\n")
    print("Queries randomized to avoid order effects\n")

    results = []

    for i, item in enumerate(all_queries, 1):
        print(f"\n--- Query {i}/{len(all_queries)} [Level {item['level']}: {item['level_name']}] ---")
        print(f"Q: {item['query']}")

        # PRE-TURN: Sample state BEFORE sending message
        print("  Pre-turn state...", end='', flush=True)
        pre_status = get_sage_status()

        if not pre_status:
            print(" FAILED - skipping")
            continue

        print(f" {pre_status['metabolic_state']} (ATP={pre_status['atp_level']:.1f})")

        time.sleep(1)

        # Send message
        print("  Sending message...", end='', flush=True)
        start_time = time.time()
        response_data = send_sage_message(item['query'])
        elapsed = time.time() - start_time

        if not response_data:
            print(" FAILED - skipping")
            continue

        response = response_data['response']
        post_state = response_data.get('metabolic_state', 'unknown')

        print(f" {len(response)} chars in {elapsed:.1f}s")
        print(f"  Post-turn state: {post_state}")

        # Record result
        results.append({
            'query_num': i,
            'difficulty_level': item['level'],
            'level_name': item['level_name'],
            'query': item['query'],
            'pre_turn_state': pre_status['metabolic_state'],
            'pre_turn_atp': pre_status['atp_level'],
            'post_turn_state': post_state,
            'response_length': len(response),
            'response_time': elapsed,
            'timestamp': datetime.now().isoformat()
        })

        # Brief pause between queries
        time.sleep(2)

    return results

def analyze_results(baseline, results):
    """Analyze wake patterns across difficulty levels"""

    print("\n" + "="*80)
    print("ANALYSIS: Discrete Attractors vs Continuous Evaluation")
    print("="*80)

    # Overall statistics
    total_queries = len(results)
    pre_wake_count = sum(1 for r in results if r['pre_turn_state'] == 'wake')
    pre_wake_pct = (pre_wake_count / total_queries * 100) if total_queries > 0 else 0

    print(f"\nOVERALL STATISTICS:")
    print(f"  Total queries: {total_queries}")
    print(f"  Pre-turn wake: {pre_wake_count}/{total_queries} = {pre_wake_pct:.1f}%")

    # Baseline statistics
    baseline_wake = sum(1 for s in baseline if s['state'] == 'wake')
    baseline_total = len(baseline)
    baseline_pct = (baseline_wake / baseline_total * 100) if baseline_total > 0 else 0
    print(f"  Baseline wake: {baseline_wake}/{baseline_total} = {baseline_pct:.1f}%")

    # Analysis by difficulty level
    print(f"\nWAKE ACTIVATION BY DIFFICULTY LEVEL:")
    print("-" * 80)
    print(f"{'Level':<8} {'Description':<15} {'Wake':<10} {'Total':<8} {'Wake %':<10} {'Avg ATP':<10}")
    print("-" * 80)

    level_stats = {}
    for level in range(1, 6):
        level_results = [r for r in results if r['difficulty_level'] == level]

        if not level_results:
            continue

        level_wake = sum(1 for r in level_results if r['pre_turn_state'] == 'wake')
        level_total = len(level_results)
        level_wake_pct = (level_wake / level_total * 100) if level_total > 0 else 0

        # Get level name from first result
        level_name = level_results[0]['level_name'].split('_')[2] if level_results else 'unknown'

        # Average ATP
        avg_atp = statistics.mean(r['pre_turn_atp'] for r in level_results)

        level_stats[level] = {
            'wake_count': level_wake,
            'total': level_total,
            'wake_pct': level_wake_pct,
            'avg_atp': avg_atp
        }

        print(f"Level {level}  {level_name:<15} {level_wake:<10} {level_total:<8} {level_wake_pct:<10.1f} {avg_atp:<10.1f}")

    # Test for discrete vs continuous pattern
    print(f"\n" + "="*80)
    print("HYPOTHESIS TESTING")
    print("="*80)

    wake_percentages = [stats['wake_pct'] for stats in level_stats.values()]

    if len(wake_percentages) >= 3:
        # Check if wake percentages cluster at specific values or scale continuously
        wake_variance = statistics.variance(wake_percentages) if len(wake_percentages) > 1 else 0
        wake_range = max(wake_percentages) - min(wake_percentages)

        print(f"\nWake percentage statistics:")
        print(f"  Range: {wake_range:.1f}%")
        print(f"  Variance: {wake_variance:.1f}")
        print(f"  Values: {[f'{p:.1f}%' for p in wake_percentages]}")

        # Simple heuristic tests
        print(f"\nPATTERN ANALYSIS:")

        # Test for monotonic increase (continuous)
        is_monotonic = all(wake_percentages[i] <= wake_percentages[i+1]
                          for i in range(len(wake_percentages)-1))

        # Test for clustering (discrete)
        # Check if most values cluster within small bands
        clusters = []
        cluster_targets = [5, 15, 35]  # Expected discrete levels from Session #38
        for pct in wake_percentages:
            closest_cluster = min(cluster_targets, key=lambda x: abs(x - pct))
            clusters.append(closest_cluster)

        cluster_match_count = sum(1 for i, pct in enumerate(wake_percentages)
                                 if abs(pct - clusters[i]) < 8)  # Within 8% of cluster center

        print(f"\n  Monotonic increase: {'YES' if is_monotonic else 'NO'}")
        print(f"  Cluster match (5%, 15%, 35%): {cluster_match_count}/{len(wake_percentages)} levels")
        print(f"  Wake range: {wake_range:.1f}% {'(LOW - suggests discrete)' if wake_range < 15 else '(HIGH - suggests continuous)'}")

        if is_monotonic and wake_range > 15:
            print(f"\n  → CONTINUOUS EVALUATION: Wake scales with difficulty")
        elif cluster_match_count >= len(wake_percentages) * 0.6 and wake_range < 20:
            print(f"\n  → DISCRETE ATTRACTORS: Wake clusters at specific levels")
        else:
            print(f"\n  → MIXED/UNCLEAR: Neither pattern clearly dominant")

    return level_stats

def main():
    """Run graded query difficulty experiment"""

    print("="*80)
    print("GRADED QUERY DIFFICULTY EXPERIMENT - Thor Session #39")
    print("Testing: Discrete Attractors vs Continuous Evaluation")
    print("="*80)

    print("\nHYPOTHESIS:")
    print("  A. DISCRETE: Wake snaps to ~5%, ~15%, ~35% regardless of continuous difficulty")
    print("  B. CONTINUOUS: Wake scales smoothly with assessed query difficulty")

    print("\nEXPERIMENTAL DESIGN:")
    print("  - 50 queries across 5 difficulty levels (10 each)")
    print("  - Randomized order to avoid sequence effects")
    print("  - Pre-turn wake sampling for each query")
    print("  - Analysis: Does wake cluster (discrete) or scale (continuous)?")

    print("\nStarting experiment in 3 seconds...")
    time.sleep(3)

    # Generate queries
    queries = generate_graded_queries()

    # Baseline sampling
    baseline = run_baseline_sampling(duration_seconds=60, interval=10)

    # Run graded experiment
    results = run_graded_experiment(queries)

    # Analyze results
    level_stats = analyze_results(baseline, results)

    # Save results
    output = {
        'experiment': 'graded_query_difficulty',
        'session': 'thor_39',
        'timestamp': datetime.now().isoformat(),
        'hypothesis': 'discrete_vs_continuous_wake_evaluation',
        'baseline': baseline,
        'results': results,
        'level_statistics': level_stats,
        'metadata': {
            'total_queries': len(results),
            'difficulty_levels': 5,
            'queries_per_level': 10,
            'sage_url': SAGE_URL
        }
    }

    filename = f"graded_query_difficulty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = Path(__file__).parent / filename

    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved to: {filename}")
    print("="*80)

    return output

if __name__ == "__main__":
    main()
