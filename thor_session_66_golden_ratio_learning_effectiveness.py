#!/usr/bin/env python3
"""
Thor Session #66: Golden Ratio Learning Effectiveness Analysis

Tests the hypothesis: Training sessions where C ≈ φ - 1 (golden zone) show
higher learning effectiveness than sessions outside the golden zone.

Building on Session #64 (temporal convergence to φ - 1), this session asks:
Is φ - 1 the OPTIMAL state for learning, not just a developmental attractor?

Hypothesis: Sessions with mean C in golden zone (|C - 0.618| < 0.05) show:
1. Higher quality scores in training exercises
2. Larger T3 trust updates (competence, reliability, integrity)
3. Better mode matching and fewer confabulations
4. More metacognitive markers

Method:
- Load training sessions (T001-T197) from SAGE raising track
- Load per-atom SNARC data from production instances
- Match training sessions to experience buffer atoms by timestamp
- Compare learning metrics: golden zone vs. outside zone

Data sources:
- ~/ai-workspace/SAGE/sage/raising/tracks/training/sessions/*.json
- ~/ai-workspace/SAGE/sage/instances/*/snapshots/experience_buffer.json
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import scipy.stats as stats

PHI_MINUS_1 = 0.618033988749895
GOLDEN_ZONE_THRESHOLD = 0.05

SAGE_ROOT = Path.home() / "ai-workspace" / "SAGE"
TRAINING_SESSIONS = SAGE_ROOT / "sage" / "raising" / "tracks" / "training" / "sessions"
INSTANCES_ROOT = SAGE_ROOT / "sage" / "instances"


def load_training_sessions():
    """Load all training sessions with quality and learning metrics."""
    sessions = []

    for session_file in sorted(TRAINING_SESSIONS.glob("T*.json")):
        try:
            with open(session_file) as f:
                data = json.load(f)
                sessions.append({
                    'session_id': data['session'],
                    'start': data['start'],
                    'end': data['end'],
                    'exercises': data['exercises'],
                    't3_summary': data.get('t3_trust_summary', {}),
                    'file': session_file.name
                })
        except Exception as e:
            print(f"Error loading {session_file.name}: {e}")
            continue

    return sessions


def load_instance_experience(instance_name):
    """Load experience buffer for a specific instance."""
    exp_path = INSTANCES_ROOT / instance_name / "snapshots" / "experience_buffer.json"

    if not exp_path.exists():
        return None

    try:
        with open(exp_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {instance_name} experience: {e}")
        return None


def calculate_coherence(salience):
    """
    Calculate coherence C from SNARC components.

    Session #64: Simple mean is optimal formulation.
    C = (S + N + A + R + C_conflict) / 5
    """
    if not salience or not isinstance(salience, dict):
        return None

    components = []
    for key in ['surprise', 'novelty', 'arousal', 'reward', 'conflict']:
        val = salience.get(key)
        if val is not None:
            components.append(val)

    if len(components) == 5:
        return sum(components) / 5.0
    else:
        # Fallback to total if components missing
        return salience.get('total')


def in_golden_zone(coherence):
    """Check if coherence is in golden ratio zone."""
    if coherence is None:
        return False
    return abs(coherence - PHI_MINUS_1) < GOLDEN_ZONE_THRESHOLD


def extract_exercise_metrics(exercise):
    """Extract learning metrics from a training exercise."""
    if 'r6_evaluation' not in exercise:
        return None

    r6 = exercise['r6_evaluation']
    quality = r6.get('quality', {})
    t3 = r6.get('t3_updates', {})

    return {
        'quality_score': quality.get('overall_quality', 0.0),
        'mode_match': r6.get('mode_match', False),
        'confabulation': quality.get('confabulation_score', 0.0),
        'partnership_density': quality.get('partnership_density', 0.0),
        'identity_framing': quality.get('has_identity_framing', False),
        't3_competence': t3.get('competence', 0.0),
        't3_reliability': t3.get('reliability', 0.0),
        't3_integrity': t3.get('integrity', 0.0),
        't3_total': sum(t3.values()) if t3 else 0.0,
        'meta_cognitive_count': len(r6.get('meta_cognitive', [])),
        'evaluation': r6.get('evaluation', 'unknown')
    }


def match_sessions_to_experience(training_sessions, instance_experiences):
    """
    Match training sessions to experience buffer atoms by timestamp.

    This is tricky because training sessions might not have exact timestamp matches.
    We'll use session number as the primary key where available.
    """
    matched = []

    for training_session in training_sessions:
        session_id = training_session['session_id']

        # Extract session number (e.g., T197 -> 197)
        try:
            session_num = int(session_id[1:])
        except:
            continue

        # Find all experience atoms from this session across all instances
        session_atoms = []
        for instance_name, experience in instance_experiences.items():
            for atom in experience:
                # Skip if atom is not a dict (malformed entry)
                if not isinstance(atom, dict):
                    continue
                if atom.get('session') == session_num:
                    session_atoms.append({
                        'instance': instance_name,
                        'salience': atom.get('salience', {}),
                        'phase': atom.get('phase'),
                        'timestamp': atom.get('timestamp')
                    })

        if session_atoms:
            # Calculate mean coherence for this session
            coherences = []
            for atom in session_atoms:
                c = calculate_coherence(atom['salience'])
                if c is not None:
                    coherences.append(c)

            if coherences:
                mean_c = np.mean(coherences)
                std_c = np.std(coherences)

                # Extract exercise metrics
                exercise_metrics = []
                for ex in training_session['exercises']:
                    metrics = extract_exercise_metrics(ex)
                    if metrics:
                        exercise_metrics.append(metrics)

                matched.append({
                    'session_id': session_id,
                    'session_num': session_num,
                    'mean_coherence': float(mean_c),
                    'std_coherence': float(std_c),
                    'n_atoms': len(coherences),
                    'in_golden_zone': bool(in_golden_zone(mean_c)),
                    'distance_from_phi': float(abs(mean_c - PHI_MINUS_1)),
                    'exercise_metrics': exercise_metrics,
                    'n_exercises': len(exercise_metrics),
                    'instances_involved': list(set(a['instance'] for a in session_atoms))
                })

    return matched


def aggregate_exercise_metrics(matched_sessions):
    """Aggregate exercise metrics by golden zone vs. outside."""
    golden_zone = defaultdict(list)
    outside_zone = defaultdict(list)

    for session in matched_sessions:
        target = golden_zone if session['in_golden_zone'] else outside_zone

        for metrics in session['exercise_metrics']:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    target[key].append(value)
                elif isinstance(value, bool):
                    target[key].append(1.0 if value else 0.0)

    # Calculate statistics
    def stats_dict(values):
        if not values:
            return None
        arr = np.array(values)
        return {
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'median': float(np.median(arr)),
            'n': len(arr)
        }

    comparison = {}
    all_keys = set(golden_zone.keys()) | set(outside_zone.keys())

    for key in all_keys:
        golden_stats = stats_dict(golden_zone[key])
        outside_stats = stats_dict(outside_zone[key])

        if golden_stats and outside_stats and len(golden_zone[key]) > 1 and len(outside_zone[key]) > 1:
            # Statistical test
            u_stat, p_value = stats.mannwhitneyu(
                golden_zone[key],
                outside_zone[key],
                alternative='two-sided'
            )

            comparison[key] = {
                'golden_zone': golden_stats,
                'outside_zone': outside_stats,
                'difference': float(golden_stats['mean'] - outside_stats['mean']),
                'p_value': float(p_value),
                'significant': bool(p_value < 0.05),
                'effect_direction': 'GOLDEN HIGHER' if golden_stats['mean'] > outside_stats['mean'] else 'OUTSIDE HIGHER'
            }

    return comparison


def main():
    print("Thor Session #66: Golden Ratio Learning Effectiveness")
    print("=" * 70)
    print()

    # Load data
    print("Loading training sessions...")
    training_sessions = load_training_sessions()
    print(f"  Loaded {len(training_sessions)} training sessions")

    print("\nLoading instance experience buffers...")
    instance_experiences = {}
    for instance_dir in INSTANCES_ROOT.iterdir():
        if instance_dir.is_dir():
            exp = load_instance_experience(instance_dir.name)
            if exp:
                instance_experiences[instance_dir.name] = exp
                print(f"  {instance_dir.name}: {len(exp)} atoms")

    # Match sessions to experience
    print("\nMatching training sessions to experience data...")
    matched = match_sessions_to_experience(training_sessions, instance_experiences)
    print(f"  Matched {len(matched)} sessions with coherence data")

    golden_count = sum(1 for s in matched if s['in_golden_zone'])
    outside_count = len(matched) - golden_count
    print(f"  Golden zone sessions: {golden_count}")
    print(f"  Outside zone sessions: {outside_count}")

    # Aggregate and compare
    print("\nAggregating exercise metrics...")
    comparison = aggregate_exercise_metrics(matched)

    # Results
    print("\n" + "=" * 70)
    print("RESULTS: Golden Zone vs. Outside Zone")
    print("=" * 70)

    for metric, data in sorted(comparison.items()):
        print(f"\n{metric}:")
        print(f"  Golden zone:  {data['golden_zone']['mean']:.4f} ± {data['golden_zone']['std']:.4f} (n={data['golden_zone']['n']})")
        print(f"  Outside zone: {data['outside_zone']['mean']:.4f} ± {data['outside_zone']['std']:.4f} (n={data['outside_zone']['n']})")
        print(f"  Difference: {data['difference']:.4f}")
        print(f"  p-value: {data['p_value']:.4f} {'***' if data['p_value'] < 0.001 else '**' if data['p_value'] < 0.01 else '*' if data['p_value'] < 0.05 else ''}")
        print(f"  Effect: {data['effect_direction']}")

    # Save results
    output = {
        'hypothesis': 'Training sessions in golden zone (|C - φ-1| < 0.05) show higher learning effectiveness',
        'phi_minus_1': PHI_MINUS_1,
        'golden_zone_threshold': GOLDEN_ZONE_THRESHOLD,
        'n_sessions_matched': len(matched),
        'n_golden_zone': golden_count,
        'n_outside_zone': outside_count,
        'metric_comparisons': comparison,
        'matched_sessions': matched
    }

    output_file = Path(__file__).parent / "thor_session_66_golden_ratio_learning_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to: {output_file.name}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    significant_favoring_golden = [m for m, d in comparison.items()
                                    if d['significant'] and d['effect_direction'] == 'GOLDEN HIGHER']
    significant_favoring_outside = [m for m, d in comparison.items()
                                     if d['significant'] and d['effect_direction'] == 'OUTSIDE HIGHER']

    print(f"\nMetrics significantly higher in golden zone ({len(significant_favoring_golden)}):")
    for m in significant_favoring_golden:
        print(f"  - {m}: +{comparison[m]['difference']:.4f} (p={comparison[m]['p_value']:.4f})")

    print(f"\nMetrics significantly higher outside golden zone ({len(significant_favoring_outside)}):")
    for m in significant_favoring_outside:
        print(f"  - {m}: {comparison[m]['difference']:.4f} (p={comparison[m]['p_value']:.4f})")

    # Verdict
    print("\n" + "=" * 70)
    if len(significant_favoring_golden) > len(significant_favoring_outside):
        print("VERDICT: Golden zone associated with BETTER learning outcomes")
        print("  φ - 1 appears to be optimal for learning, not just developmental attractor")
    elif len(significant_favoring_outside) > len(significant_favoring_golden):
        print("VERDICT: Outside zone associated with better learning outcomes")
        print("  φ - 1 may be developmental attractor but NOT learning optimum")
    else:
        print("VERDICT: NO CLEAR DIFFERENCE between golden zone and outside zone")
        print("  φ - 1 may be attractor for other reasons (stability, not learning rate)")
    print("=" * 70)


if __name__ == "__main__":
    main()
