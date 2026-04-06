#!/usr/bin/env python3
"""
Thor Session #63: Cross-Instance C ≈ 0.5 Validation

Analyzes production SAGE experience data across all active instances
to validate the C ≈ 0.5 hypothesis with fresh data.

Following Session #59's methodology but expanding to:
- Multiple instances (Nomad, Sprout, CBP, Legion, Thor)
- Different models (gemma3, qwen3.5, gemma4, phi4)
- Different machines (nomad, sprout, cbp, legion, thor, mcnugget)

Tests:
1. C ≈ 0.5 universality across instances
2. Model-specific variations
3. Metabolic state correlations
4. Cross-session stability
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
import scipy.stats as stats


def load_instance_experience(instance_path):
    """Load experience buffer from a SAGE instance."""
    exp_file = instance_path / "snapshots" / "experience_buffer.json"
    if not exp_file.exists():
        return None

    try:
        with open(exp_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {instance_path.name}: {e}")
        return None


def extract_coherence_metrics(experiences):
    """Extract coherence-related metrics from experience atoms."""
    metrics = {
        'salience_total': [],
        'salience_components': defaultdict(list),
        'metabolic_states': [],
        'phases': [],
        'sessions': [],
        'timestamps': []
    }

    for exp in experiences:
        # Skip if not a dict (malformed entry)
        if not isinstance(exp, dict):
            continue

        sal = exp.get('salience', {})
        total = sal.get('total')

        if total is not None:
            metrics['salience_total'].append(total)

            # Component saliences
            for key in ['surprise', 'novelty', 'arousal', 'reward', 'conflict']:
                if key in sal:
                    metrics['salience_components'][key].append(sal[key])

            # Contextual metadata
            meta = exp.get('metadata', {})
            metrics['metabolic_states'].append(meta.get('metabolic_state', 'unknown'))
            metrics['phases'].append(exp.get('phase', 'unknown'))
            metrics['sessions'].append(exp.get('session', -1))
            metrics['timestamps'].append(exp.get('timestamp', ''))

    return metrics


def analyze_c_distribution(salience_totals, instance_name):
    """Analyze whether C (salience_total) clusters around 0.5."""
    if len(salience_totals) < 3:
        return None

    arr = np.array(salience_totals)

    # Basic statistics
    mean_c = np.mean(arr)
    std_c = np.std(arr)
    median_c = np.median(arr)

    # Distance from C = 0.5
    deviation = abs(mean_c - 0.5)
    accuracy = 1.0 - (deviation / 0.5)  # How close to 0.5 as percentage

    # Distribution shape
    q25, q75 = np.percentile(arr, [25, 75])
    iqr = q75 - q25

    # Count experiences near C = 0.5 (within ±0.1)
    near_half = np.sum((arr >= 0.4) & (arr <= 0.6))
    frac_near_half = near_half / len(arr)

    return {
        'instance': instance_name,
        'n': len(arr),
        'mean': float(mean_c),
        'std': float(std_c),
        'median': float(median_c),
        'deviation_from_0.5': float(deviation),
        'accuracy_pct': float(accuracy * 100),
        'q25': float(q25),
        'q75': float(q75),
        'iqr': float(iqr),
        'near_0.5_count': int(near_half),
        'near_0.5_frac': float(frac_near_half)
    }


def analyze_metabolic_correlations(metrics):
    """Analyze relationship between metabolic state and coherence."""
    state_coherence = defaultdict(list)

    for c, state in zip(metrics['salience_total'], metrics['metabolic_states']):
        state_coherence[state].append(c)

    state_stats = {}
    for state, values in state_coherence.items():
        if len(values) > 0:
            state_stats[state] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'n': len(values)
            }

    return state_stats


def analyze_cross_session_stability(metrics):
    """Check if C is stable across sessions within an instance."""
    session_coherence = defaultdict(list)

    for c, session in zip(metrics['salience_total'], metrics['sessions']):
        if session >= 0:
            session_coherence[session].append(c)

    session_stats = {}
    for session, values in session_coherence.items():
        if len(values) > 0:
            session_stats[session] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'n': len(values)
            }

    # Cross-session variance
    if len(session_stats) > 1:
        session_means = [s['mean'] for s in session_stats.values()]
        cross_session_std = float(np.std(session_means))
    else:
        cross_session_std = 0.0

    return session_stats, cross_session_std


def main():
    sage_path = Path.home() / "ai-workspace" / "SAGE" / "sage" / "instances"

    if not sage_path.exists():
        print(f"SAGE instances path not found: {sage_path}")
        return

    print("=" * 60)
    print("Thor Session #63: Cross-Instance C ≈ 0.5 Validation")
    print("=" * 60)
    print()

    # Scan all instances
    instances = [d for d in sage_path.iterdir() if d.is_dir() and not d.name.startswith('_')]

    print(f"Found {len(instances)} instances:")
    for inst in sorted(instances):
        print(f"  - {inst.name}")
    print()

    # Analyze each instance
    all_results = []
    instance_metrics = {}

    for inst_path in sorted(instances):
        print(f"\n{'='*60}")
        print(f"Analyzing: {inst_path.name}")
        print(f"{'='*60}")

        exp_data = load_instance_experience(inst_path)
        if exp_data is None:
            print("  ❌ No experience data found")
            continue

        print(f"  ✓ Loaded {len(exp_data)} experience atoms")

        # Extract metrics
        metrics = extract_coherence_metrics(exp_data)
        instance_metrics[inst_path.name] = metrics

        if len(metrics['salience_total']) == 0:
            print("  ⚠️  No salience data found")
            continue

        # Analyze C distribution
        c_stats = analyze_c_distribution(metrics['salience_total'], inst_path.name)
        if c_stats:
            all_results.append(c_stats)

            print(f"\n  C Distribution:")
            print(f"    Mean:     {c_stats['mean']:.4f}")
            print(f"    Median:   {c_stats['median']:.4f}")
            print(f"    Std:      {c_stats['std']:.4f}")
            print(f"    Deviation from 0.5: {c_stats['deviation_from_0.5']:.4f}")
            print(f"    Accuracy: {c_stats['accuracy_pct']:.1f}%")
            print(f"    Near 0.5 (0.4-0.6): {c_stats['near_0.5_count']}/{c_stats['n']} ({c_stats['near_0.5_frac']*100:.1f}%)")

        # Metabolic state analysis
        state_stats = analyze_metabolic_correlations(metrics)
        if state_stats:
            print(f"\n  Metabolic States:")
            for state, state_info in sorted(state_stats.items()):
                print(f"    {state:10s}: C = {state_info['mean']:.3f} ± {state_info['std']:.3f} (n={state_info['n']})")

        # Cross-session stability
        session_stats, cross_std = analyze_cross_session_stability(metrics)
        if len(session_stats) > 1:
            print(f"\n  Cross-Session Stability:")
            print(f"    Sessions: {len(session_stats)}")
            print(f"    Cross-session σ: {cross_std:.4f}")

    # Aggregate analysis
    print(f"\n\n{'='*60}")
    print("AGGREGATE ANALYSIS")
    print(f"{'='*60}")

    if len(all_results) == 0:
        print("No results to analyze")
        return

    # Overall C statistics
    all_means = [r['mean'] for r in all_results]
    all_stds = [r['std'] for r in all_results]
    all_n = [r['n'] for r in all_results]

    print(f"\nInstances analyzed: {len(all_results)}")
    print(f"Total experience atoms: {sum(all_n)}")
    print()
    print("C ≈ 0.5 Hypothesis Validation:")
    print(f"  Mean C across instances:    {np.mean(all_means):.4f} ± {np.std(all_means):.4f}")
    print(f"  Median C across instances:  {np.median(all_means):.4f}")
    print(f"  Range: [{min(all_means):.4f}, {max(all_means):.4f}]")
    print()

    # Test if distribution is centered on 0.5
    deviations = [abs(m - 0.5) for m in all_means]
    mean_deviation = np.mean(deviations)
    print(f"Mean absolute deviation from 0.5: {mean_deviation:.4f}")

    # How many instances are within ±0.1 of 0.5?
    within_range = sum(1 for m in all_means if 0.4 <= m <= 0.6)
    print(f"Instances with C ∈ [0.4, 0.6]: {within_range}/{len(all_results)} ({within_range/len(all_results)*100:.1f}%)")

    # Statistical test: is mean significantly different from 0.5?
    t_stat, p_value = stats.ttest_1samp(all_means, 0.5)
    print(f"\nOne-sample t-test (H0: μ = 0.5):")
    print(f"  t-statistic: {t_stat:.3f}")
    print(f"  p-value: {p_value:.4f}")
    if p_value > 0.05:
        print(f"  ✓ Cannot reject H0 — consistent with C = 0.5")
    else:
        print(f"  ✗ Reject H0 — significant deviation from C = 0.5")

    # Save results
    output = {
        'timestamp': Path.home().joinpath('.timestamp').read_text().strip() if Path.home().joinpath('.timestamp').exists() else 'unknown',
        'instances_analyzed': len(all_results),
        'total_atoms': sum(all_n),
        'aggregate_stats': {
            'mean_c': float(np.mean(all_means)),
            'std_c': float(np.std(all_means)),
            'median_c': float(np.median(all_means)),
            'mean_deviation_from_0.5': float(mean_deviation),
            't_statistic': float(t_stat),
            'p_value': float(p_value)
        },
        'instance_results': all_results
    }

    output_file = Path(__file__).parent / "thor_session_63_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
