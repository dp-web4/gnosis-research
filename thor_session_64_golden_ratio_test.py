#!/usr/bin/env python3
"""
Thor Session #64: Golden Ratio Hypothesis Test
===============================================

Test alternative C formulations to see if any yield φ - 1 ≈ 0.618

Session #63 found C ≈ 0.64 using simple average of SNARC components.
This session tests:
1. Weighted average (using snarc_scorer.py weights)
2. Geometric mean
3. Harmonic mean
4. Median
5. Max of components
6. Custom combinations

Goal: Determine if C → φ - 1 ≈ 0.618 with refined measurement
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from scipy.stats import trim_mean, ttest_rel
from collections import defaultdict

# Golden ratio constants
PHI = (1 + np.sqrt(5)) / 2  # ≈ 1.618
PHI_MINUS_1 = PHI - 1  # ≈ 0.618
TWO_THIRDS = 2/3  # ≈ 0.667

# SNARC weights from snarc_scorer.py line 251
# [surprise, novelty, arousal, reward, conflict]
RAW_WEIGHTS = np.array([1.0, 0.8, 0.6, 1.2, 0.7])
NORMALIZED_WEIGHTS = RAW_WEIGHTS / RAW_WEIGHTS.sum()  # Softmax approximation

def load_experience_buffer(instance_dir: Path) -> List[Dict]:
    """Load experience atoms from instance directory"""
    exp_file = instance_dir / "snapshots" / "experience_buffer.json"
    if not exp_file.exists():
        return []

    with open(exp_file) as f:
        return json.load(f)

def extract_snarc_components(atom: Dict) -> np.ndarray:
    """Extract SNARC 5-vector from experience atom"""
    # Handle both dict and string atoms (some buffers contain strings)
    if not isinstance(atom, dict):
        return None

    sal = atom.get("salience", {})
    if not isinstance(sal, dict):
        return None

    return np.array([
        sal.get("surprise", 0),
        sal.get("novelty", 0),
        sal.get("arousal", 0),
        sal.get("reward", 0),
        sal.get("conflict", 0)
    ])

def compute_c_variants(snarc_vector: np.ndarray) -> Dict[str, float]:
    """Compute different C formulations from SNARC components"""

    # Guard against zero/invalid values
    snarc_safe = np.maximum(snarc_vector, 1e-8)

    return {
        # Current formulation (Session #63)
        "simple_mean": np.mean(snarc_vector),

        # Weighted formulations
        "weighted_mean": np.average(snarc_vector, weights=NORMALIZED_WEIGHTS),
        "weighted_raw": np.dot(snarc_vector, NORMALIZED_WEIGHTS),

        # Alternative means
        "geometric_mean": np.exp(np.mean(np.log(snarc_safe))),
        "harmonic_mean": len(snarc_vector) / np.sum(1.0 / snarc_safe),

        # Robust statistics
        "median": np.median(snarc_vector),
        "trimmed_mean": trim_mean(snarc_vector, 0.2),  # Remove top/bottom 20%

        # Extrema
        "max": np.max(snarc_vector),
        "min": np.min(snarc_vector),

        # Component-specific combinations
        "exploration_bias": np.mean([snarc_vector[0], snarc_vector[1]]),  # surprise + novelty
        "exploitation_bias": np.mean([snarc_vector[2], snarc_vector[3]]),  # arousal + reward
        "coherence_proxy": 1 - snarc_vector[4],  # inverse conflict

        # Golden ratio inspired combinations
        "phi_weighted": (
            PHI * np.mean([snarc_vector[2], snarc_vector[3]]) +  # exploitation
            1.0 * np.mean([snarc_vector[0], snarc_vector[1]])     # exploration
        ) / (PHI + 1.0),

        # Information-theoretic
        "entropy_weighted": np.sum(snarc_vector * (-np.log(snarc_safe + 1e-8))),

        # Quadratic mean (RMS)
        "quadratic_mean": np.sqrt(np.mean(snarc_vector**2)),
    }

def analyze_instance(instance_dir: Path) -> Tuple[str, Dict[str, Dict]]:
    """Analyze all C variants for a single instance"""

    instance_name = instance_dir.name
    atoms = load_experience_buffer(instance_dir)

    if not atoms:
        return instance_name, {}

    # Collect all variant values across atoms
    all_variants = defaultdict(list)

    for atom in atoms:
        snarc = extract_snarc_components(atom)
        if snarc is None:
            continue

        variants = compute_c_variants(snarc)

        for variant_name, value in variants.items():
            if np.isfinite(value):  # Filter out NaN/inf
                all_variants[variant_name].append(value)

    # Compute statistics for each variant
    results = {}
    for variant_name, values in all_variants.items():
        if not values:
            continue

        arr = np.array(values)
        results[variant_name] = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "median": float(np.median(arr)),
            "n": len(arr),

            # Distances to key values
            "dist_to_phi_minus_1": abs(np.mean(arr) - PHI_MINUS_1),
            "dist_to_two_thirds": abs(np.mean(arr) - TWO_THIRDS),
            "dist_to_half": abs(np.mean(arr) - 0.5),
        }

    return instance_name, results

def find_best_phi_approximation(all_results: Dict[str, Dict[str, Dict]]) -> None:
    """Find which C variant best approximates φ - 1 across all instances"""

    # Aggregate across instances for each variant
    variant_aggregates = defaultdict(list)

    for instance_name, results in all_results.items():
        for variant_name, stats in results.items():
            variant_aggregates[variant_name].append(stats["mean"])

    # Compute cross-instance statistics
    print("\n" + "="*80)
    print("GOLDEN RATIO HYPOTHESIS TEST: Which C formulation yields φ - 1 ≈ 0.618?")
    print("="*80)

    print(f"\nTarget: φ - 1 = {PHI_MINUS_1:.6f}")
    print(f"Session #63 found: C ≈ 0.640 (simple_mean)")
    print(f"\nTesting {len(variant_aggregates)} C formulations across {len(all_results)} instances...")

    # Rank variants by closeness to φ - 1
    rankings = []
    for variant_name, means in variant_aggregates.items():
        if not means:
            continue

        cross_instance_mean = np.mean(means)
        cross_instance_std = np.std(means)
        dist_to_phi = abs(cross_instance_mean - PHI_MINUS_1)

        rankings.append({
            "variant": variant_name,
            "mean": cross_instance_mean,
            "std": cross_instance_std,
            "dist_phi": dist_to_phi,
            "dist_2_3": abs(cross_instance_mean - TWO_THIRDS),
            "dist_0_5": abs(cross_instance_mean - 0.5),
        })

    # Sort by distance to φ - 1
    rankings.sort(key=lambda x: x["dist_phi"])

    print("\n" + "-"*80)
    print("TOP 10 CLOSEST TO φ - 1 ≈ 0.618:")
    print("-"*80)
    print(f"{'Rank':<5} {'Variant':<25} {'Mean':<10} {'Std':<10} {'Δφ-1':<10} {'Δ2/3':<10} {'Δ0.5':<10}")
    print("-"*80)

    for i, r in enumerate(rankings[:10], 1):
        print(f"{i:<5} {r['variant']:<25} {r['mean']:<10.4f} {r['std']:<10.4f} "
              f"{r['dist_phi']:<10.4f} {r['dist_2_3']:<10.4f} {r['dist_0_5']:<10.4f}")

    # Highlight the winner
    winner = rankings[0]
    print("\n" + "="*80)
    print(f"WINNER: {winner['variant']}")
    print(f"  Mean: {winner['mean']:.6f}")
    print(f"  Distance to φ - 1: {winner['dist_phi']:.6f} ({winner['dist_phi']/PHI_MINUS_1*100:.2f}% error)")
    print(f"  Cross-instance std: {winner['std']:.6f}")
    print("="*80)

    # Statistical test: Is winner significantly closer to φ - 1 than simple_mean?
    simple_means = variant_aggregates.get("simple_mean", [])
    winner_means = variant_aggregates.get(winner["variant"], [])

    if len(simple_means) > 0 and len(winner_means) > 0:
        print("\n" + "-"*80)
        print("COMPARISON: Winner vs Session #63 (simple_mean)")
        print("-"*80)

        print(f"Simple mean: {np.mean(simple_means):.6f} ± {np.std(simple_means):.6f}")
        print(f"  Distance to φ - 1: {abs(np.mean(simple_means) - PHI_MINUS_1):.6f}")

        print(f"\n{winner['variant']}: {winner['mean']:.6f} ± {winner['std']:.6f}")
        print(f"  Distance to φ - 1: {winner['dist_phi']:.6f}")

        improvement = abs(np.mean(simple_means) - PHI_MINUS_1) - winner['dist_phi']
        print(f"\nImprovement: {improvement:.6f} ({improvement/abs(np.mean(simple_means) - PHI_MINUS_1)*100:.1f}%)")

        # Paired t-test
        if len(simple_means) == len(winner_means):
            t_stat, p_value = ttest_rel(
                [abs(m - PHI_MINUS_1) for m in simple_means],
                [abs(m - PHI_MINUS_1) for m in winner_means]
            )
            print(f"\nPaired t-test (distances to φ - 1):")
            print(f"  t = {t_stat:.3f}, p = {p_value:.6f}")
            if p_value < 0.05:
                print(f"  ✓ Significantly different (p < 0.05)")
            else:
                print(f"  ✗ Not significantly different (p ≥ 0.05)")

    # Check if ANY variant is within 1% of φ - 1
    print("\n" + "-"*80)
    print("VARIANTS WITHIN 1% OF φ - 1:")
    print("-"*80)

    close_variants = [r for r in rankings if r['dist_phi'] / PHI_MINUS_1 < 0.01]
    if close_variants:
        for r in close_variants:
            print(f"  {r['variant']}: {r['mean']:.6f} (error: {r['dist_phi']/PHI_MINUS_1*100:.3f}%)")
    else:
        print("  None found.")
        print(f"\n  Closest: {rankings[0]['variant']} at {rankings[0]['dist_phi']/PHI_MINUS_1*100:.2f}% error")

    return rankings

def main():
    sage_dir = Path.home() / "ai-workspace" / "SAGE" / "sage" / "instances"

    if not sage_dir.exists():
        print(f"Error: {sage_dir} not found")
        return

    # Find all instance directories with experience data
    instance_dirs = [d for d in sage_dir.iterdir()
                    if d.is_dir() and (d / "snapshots" / "experience_buffer.json").exists()]

    print(f"Found {len(instance_dirs)} instances with experience data")

    # Analyze each instance
    all_results = {}
    for instance_dir in sorted(instance_dirs):
        print(f"Analyzing {instance_dir.name}...")
        instance_name, results = analyze_instance(instance_dir)
        if results:
            all_results[instance_name] = results

    print(f"\nAnalyzed {len(all_results)} instances with valid data")

    # Find best φ approximation
    rankings = find_best_phi_approximation(all_results)

    # Save detailed results
    output_file = Path(__file__).parent / "thor_session_64_golden_ratio_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "target_phi_minus_1": PHI_MINUS_1,
            "target_two_thirds": TWO_THIRDS,
            "instances_analyzed": len(all_results),
            "rankings": rankings[:20],  # Top 20
            "detailed_results": all_results,
        }, f, indent=2)

    print(f"\n✓ Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
