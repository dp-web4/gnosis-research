#!/usr/bin/env python3
"""
Analysis Script for Graded Query Difficulty Experiment
Thor Session #39

Analyzes whether wake activation follows discrete attractors or continuous evaluation.
"""

import json
import statistics
import sys
from pathlib import Path
from collections import defaultdict

def load_results(filename):
    """Load experimental results from JSON"""
    with open(filename, 'r') as f:
        return json.load(f)

def analyze_discrete_vs_continuous(results):
    """
    Test whether wake activation follows discrete attractors or continuous scaling.

    DISCRETE HYPOTHESIS: Wake clusters at ~5%, ~15%, ~35% regardless of difficulty
    CONTINUOUS HYPOTHESIS: Wake scales smoothly with query difficulty level
    """

    print("\n" + "="*80)
    print("DISCRETE VS CONTINUOUS WAKE ACTIVATION ANALYSIS")
    print("="*80)

    # Group results by difficulty level
    by_level = defaultdict(list)
    for r in results:
        level = r['difficulty_level']
        by_level[level].append(r)

    # Calculate wake percentage for each level
    level_wake_stats = {}

    print("\nWAKE ACTIVATION BY DIFFICULTY LEVEL:")
    print("-" * 80)
    print(f"{'Level':<8} {'Description':<15} {'Wake':<8} {'Rest':<8} {'Dream':<8} {'Total':<8} {'Wake %':<10}")
    print("-" * 80)

    for level in sorted(by_level.keys()):
        level_results = by_level[level]

        wake_count = sum(1 for r in level_results if r['pre_turn_state'] == 'wake')
        rest_count = sum(1 for r in level_results if r['pre_turn_state'] == 'rest')
        dream_count = sum(1 for r in level_results if r['pre_turn_state'] == 'dream')
        total = len(level_results)

        wake_pct = (wake_count / total * 100) if total > 0 else 0

        # Get level description
        level_name = level_results[0]['level_name'].split('_')[2] if level_results else 'unknown'

        level_wake_stats[level] = {
            'wake_count': wake_count,
            'rest_count': rest_count,
            'dream_count': dream_count,
            'total': total,
            'wake_pct': wake_pct,
            'level_name': level_name
        }

        print(f"{level:<8} {level_name:<15} {wake_count:<8} {rest_count:<8} {dream_count:<8} {total:<8} {wake_pct:<10.1f}")

    # Statistical analysis
    print("\n" + "="*80)
    print("HYPOTHESIS TESTING")
    print("="*80)

    wake_percentages = [stats['wake_pct'] for level, stats in sorted(level_wake_stats.items())]

    if len(wake_percentages) < 3:
        print("\nInsufficient data for hypothesis testing (need at least 3 levels)")
        return level_wake_stats

    print(f"\nWake percentages by level: {[f'{p:.1f}%' for p in wake_percentages]}")

    # Test 1: Monotonic increase (evidence for continuous)
    print("\nTEST 1: MONOTONIC INCREASE (continuous hypothesis)")
    is_monotonic = all(wake_percentages[i] <= wake_percentages[i+1]
                      for i in range(len(wake_percentages)-1))
    print(f"  Monotonic increase: {'YES ✓' if is_monotonic else 'NO ✗'}")

    if is_monotonic:
        # Calculate correlation coefficient
        levels = list(range(1, len(wake_percentages) + 1))
        mean_level = statistics.mean(levels)
        mean_wake = statistics.mean(wake_percentages)

        numerator = sum((l - mean_level) * (w - mean_wake)
                       for l, w in zip(levels, wake_percentages))
        denom_l = sum((l - mean_level) ** 2 for l in levels) ** 0.5
        denom_w = sum((w - mean_wake) ** 2 for w in wake_percentages) ** 0.5

        correlation = numerator / (denom_l * denom_w) if (denom_l * denom_w) > 0 else 0

        print(f"  Correlation with difficulty: r = {correlation:.3f}")
        print(f"  → {'STRONG' if abs(correlation) > 0.7 else 'MODERATE' if abs(correlation) > 0.4 else 'WEAK'} linear relationship")

    # Test 2: Cluster analysis (evidence for discrete)
    print("\nTEST 2: CLUSTERING AT DISCRETE LEVELS (discrete hypothesis)")
    cluster_targets = [5, 15, 35]  # Expected from Session #38

    # Find nearest cluster for each level
    clusters_assigned = []
    cluster_distances = []

    for pct in wake_percentages:
        nearest_cluster = min(cluster_targets, key=lambda x: abs(x - pct))
        distance = abs(pct - nearest_cluster)
        clusters_assigned.append(nearest_cluster)
        cluster_distances.append(distance)

    avg_distance = statistics.mean(cluster_distances)
    max_distance = max(cluster_distances)

    print(f"  Target clusters: {cluster_targets}")
    print(f"  Cluster assignments: {clusters_assigned}")
    print(f"  Average distance from cluster: {avg_distance:.1f}%")
    print(f"  Maximum distance from cluster: {max_distance:.1f}%")

    # Count how many levels are close to clusters (within 8%)
    close_to_cluster = sum(1 for d in cluster_distances if d < 8)
    cluster_match_rate = close_to_cluster / len(cluster_distances)

    print(f"  Levels within 8% of cluster: {close_to_cluster}/{len(cluster_distances)} = {cluster_match_rate*100:.0f}%")

    # Test 3: Variance analysis
    print("\nTEST 3: VARIANCE ANALYSIS")
    wake_variance = statistics.variance(wake_percentages) if len(wake_percentages) > 1 else 0
    wake_range = max(wake_percentages) - min(wake_percentages)

    print(f"  Wake % range: {wake_range:.1f}%")
    print(f"  Wake % variance: {wake_variance:.1f}")
    print(f"  Wake % std dev: {wake_variance**0.5:.1f}%")

    # Test 4: Step detection (discrete levels should show sharp transitions)
    print("\nTEST 4: STEP DETECTION")
    if len(wake_percentages) > 2:
        # Calculate differences between consecutive levels
        diffs = [wake_percentages[i+1] - wake_percentages[i]
                for i in range(len(wake_percentages)-1)]

        avg_diff = statistics.mean(diffs)
        max_diff = max(diffs)
        min_diff = min(diffs)

        print(f"  Level-to-level changes: {[f'{d:+.1f}%' for d in diffs]}")
        print(f"  Average change: {avg_diff:.1f}%")
        print(f"  Largest jump: {max_diff:.1f}%")
        print(f"  Smallest jump: {min_diff:.1f}%")

        # Discrete attractors would show uneven jumps (large steps between attractors)
        # Continuous would show more uniform increases
        jump_variance = statistics.variance(diffs) if len(diffs) > 1 else 0
        print(f"  Jump variance: {jump_variance:.1f}")
        print(f"  → {'UNEVEN (suggests discrete)' if jump_variance > 20 else 'UNIFORM (suggests continuous)'}")

    # VERDICT
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)

    discrete_evidence = 0
    continuous_evidence = 0

    # Evidence scoring
    if cluster_match_rate > 0.6:
        discrete_evidence += 2
        print("\n[+2 DISCRETE] High cluster match rate")
    elif cluster_match_rate > 0.4:
        discrete_evidence += 1
        print("\n[+1 DISCRETE] Moderate cluster match rate")

    if is_monotonic:
        continuous_evidence += 1
        print("[+1 CONTINUOUS] Monotonic increase with difficulty")

        if 'correlation' in locals() and abs(correlation) > 0.7:
            continuous_evidence += 2
            print("[+2 CONTINUOUS] Strong linear correlation")
        elif 'correlation' in locals() and abs(correlation) > 0.4:
            continuous_evidence += 1
            print("[+1 CONTINUOUS] Moderate linear correlation")

    if wake_range > 20:
        continuous_evidence += 1
        print("[+1 CONTINUOUS] Wide range of wake percentages")
    elif wake_range < 10:
        discrete_evidence += 1
        print("[+1 DISCRETE] Narrow range suggests clustering")

    if 'jump_variance' in locals():
        if jump_variance > 20:
            discrete_evidence += 1
            print("[+1 DISCRETE] Uneven jumps between levels")
        else:
            continuous_evidence += 1
            print("[+1 CONTINUOUS] Uniform increases between levels")

    print(f"\nEvidence Score:")
    print(f"  DISCRETE:    {discrete_evidence}")
    print(f"  CONTINUOUS:  {continuous_evidence}")

    if discrete_evidence > continuous_evidence:
        verdict = "DISCRETE ATTRACTORS"
        confidence = "STRONG" if discrete_evidence >= continuous_evidence + 2 else "MODERATE"
    elif continuous_evidence > discrete_evidence:
        verdict = "CONTINUOUS EVALUATION"
        confidence = "STRONG" if continuous_evidence >= discrete_evidence + 2 else "MODERATE"
    else:
        verdict = "MIXED/UNCLEAR"
        confidence = "LOW"

    print(f"\n{'='*80}")
    print(f"CONCLUSION: {verdict} ({confidence} confidence)")
    print(f"{'='*80}")

    if verdict == "DISCRETE ATTRACTORS":
        print("\nWake activation appears to cluster at specific levels (~5%, ~15%, ~35%)")
        print("regardless of continuous query difficulty. This suggests SAGE has discrete")
        print("metabolic modes that act as attractors.")
    elif verdict == "CONTINUOUS EVALUATION":
        print("\nWake activation scales continuously with assessed query difficulty.")
        print("This suggests SAGE performs graded resource allocation based on")
        print("evaluated task demands rather than snapping to discrete modes.")
    else:
        print("\nResults show mixed evidence. Wake may follow discrete attractors")
        print("but with continuous modulation, or the experiment may need larger N")
        print("for clearer patterns to emerge.")

    return level_wake_stats

def main():
    if len(sys.argv) < 2:
        # Find most recent results file
        results_files = list(Path('.').glob('graded_query_difficulty_*.json'))
        if not results_files:
            print("No results files found. Run experiment first.")
            return

        filename = max(results_files, key=lambda p: p.stat().st_mtime)
        print(f"Loading most recent results: {filename}")
    else:
        filename = sys.argv[1]

    data = load_results(filename)

    print("="*80)
    print("GRADED QUERY DIFFICULTY EXPERIMENT - ANALYSIS")
    print("="*80)

    print(f"\nExperiment: {data['experiment']}")
    print(f"Session: {data['session']}")
    print(f"Timestamp: {data['timestamp']}")
    print(f"Total queries: {len(data['results'])}")

    # Analyze discrete vs continuous pattern
    level_stats = analyze_discrete_vs_continuous(data['results'])

    # Save analysis
    output_file = filename.replace('.json', '_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(level_stats, f, indent=2)

    print(f"\nAnalysis saved to: {output_file}")

if __name__ == "__main__":
    main()
