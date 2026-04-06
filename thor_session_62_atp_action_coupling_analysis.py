#!/usr/bin/env python3
"""
Thor Session #62: ATP-Action Coupling Analysis

Analyzes ATP logs from sage_solver_v8.py to validate:
Prediction #1: "ATP level predicts action effectiveness"

From April 5 insights:
- Understanding is cheap (pattern matching in weights)
- Action is expensive (simulation, planning, execution)
- The gap between understanding and action is the ATP gap

Tests:
1. Correlation between ATP and action quality (caused change, level up)
2. ATP state distribution (WAKE/FOCUS/REST) during different outcomes
3. ATP trajectory during successful vs. failed attempts
4. Context layer activation (hypothesized) by ATP level
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt


def load_atp_logs(log_dir="~/ai-workspace/SAGE/arc-agi-3/experiments/logs"):
    """Load all ATP log files."""
    log_path = Path(log_dir).expanduser()
    if not log_path.exists():
        return []

    logs = []
    for log_file in log_path.glob("*_atp_log.json"):
        with open(log_file) as f:
            data = json.load(f)
            logs.append(data)

    return logs


def analyze_atp_action_correlation(logs):
    """Test Prediction #1: ATP level predicts action effectiveness."""

    # Collect data points
    atp_values = []
    action_quality = []  # 0 = no effect, 1 = caused change, 2 = leveled up

    for game_data in logs:
        for entry in game_data.get('atp_log', []):
            atp_before = entry.get('atp_before')
            if atp_before is None:
                continue

            # Determine action quality
            if entry.get('leveled_up', False):
                quality = 2  # Best outcome
            elif entry['actions_caused_change'] > 0:
                quality = 1  # Good outcome
            else:
                quality = 0  # No effect

            atp_values.append(atp_before)
            action_quality.append(quality)

    if len(atp_values) < 3:
        return {"error": "Insufficient data", "n": len(atp_values)}

    # Statistical tests
    atp = np.array(atp_values)
    quality = np.array(action_quality)

    # Correlation
    correlation, p_value = stats.spearmanr(atp, quality)

    # Group by quality
    quality_groups = {
        0: atp[quality == 0],
        1: atp[quality == 1],
        2: atp[quality == 2]
    }

    stats_by_quality = {}
    for q, vals in quality_groups.items():
        if len(vals) > 0:
            stats_by_quality[q] = {
                'mean': float(np.mean(vals)),
                'std': float(np.std(vals)),
                'n': len(vals)
            }

    # ANOVA if we have multiple groups
    groups = [v for v in quality_groups.values() if len(v) > 0]
    if len(groups) >= 2:
        f_stat, anova_p = stats.f_oneway(*groups)
    else:
        f_stat, anova_p = None, None

    return {
        'correlation': correlation,
        'p_value': p_value,
        'n_samples': len(atp_values),
        'stats_by_quality': stats_by_quality,
        'f_statistic': f_stat,
        'anova_p_value': anova_p,
        'interpretation': _interpret_correlation(correlation, p_value)
    }


def analyze_metabolic_states(logs):
    """Analyze metabolic state distribution during different outcomes."""

    state_counts = {
        'no_effect': {'wake': 0, 'focus': 0, 'rest': 0},
        'caused_change': {'wake': 0, 'focus': 0, 'rest': 0},
        'leveled_up': {'wake': 0, 'focus': 0, 'rest': 0}
    }

    for game_data in logs:
        for entry in game_data.get('atp_log', []):
            state = entry.get('state_before', 'wake').lower()

            if entry.get('leveled_up', False):
                outcome = 'leveled_up'
            elif entry['actions_caused_change'] > 0:
                outcome = 'caused_change'
            else:
                outcome = 'no_effect'

            if state in state_counts[outcome]:
                state_counts[outcome][state] += 1

    return state_counts


def analyze_atp_trajectory(logs):
    """Analyze ATP depletion patterns in successful vs. failed attempts."""

    trajectories = {
        'successful': [],  # Games that leveled up
        'failed': []       # Games that didn't level up
    }

    for game_data in logs:
        game_id = game_data['game_id']
        best_levels = game_data.get('best_levels', 0)
        atp_sequence = [entry.get('atp_before') for entry in game_data.get('atp_log', [])
                       if entry.get('atp_before') is not None]

        if len(atp_sequence) > 0:
            if best_levels > 0:
                trajectories['successful'].append({
                    'game_id': game_id,
                    'atp': atp_sequence,
                    'levels': best_levels
                })
            else:
                trajectories['failed'].append({
                    'game_id': game_id,
                    'atp': atp_sequence
                })

    return trajectories


def _interpret_correlation(r, p):
    """Interpret correlation coefficient."""
    if p > 0.05:
        return f"No significant correlation (r={r:.3f}, p={p:.3f})"

    if r > 0.5:
        return f"Strong positive correlation (r={r:.3f}, p={p:.3f}) - HIGH ATP → EFFECTIVE ACTIONS ✓"
    elif r > 0.3:
        return f"Moderate positive correlation (r={r:.3f}, p={p:.3f}) - ATP predicts action quality"
    elif r > 0.1:
        return f"Weak positive correlation (r={r:.3f}, p={p:.3f}) - Partial support"
    elif r < -0.1:
        return f"Negative correlation (r={r:.3f}, p={p:.3f}) - Contradicts hypothesis"
    else:
        return f"No meaningful correlation (r={r:.3f}, p={p:.3f})"


def generate_report(logs):
    """Generate comprehensive analysis report."""

    print("=" * 70)
    print("Thor Session #62: ATP-Action Coupling Validation")
    print("=" * 70)
    print()

    # Overall stats
    total_games = len(logs)
    total_actions = sum(len(g.get('atp_log', [])) for g in logs)
    successful_games = sum(1 for g in logs if g.get('best_levels', 0) > 0)

    print(f"Dataset Summary:")
    print(f"  Games analyzed: {total_games}")
    print(f"  Total planning cycles: {total_actions}")
    print(f"  Successful games: {successful_games}/{total_games} ({successful_games/total_games*100:.1f}%)")
    print()

    # Prediction #1: ATP-Action Correlation
    print("─" * 70)
    print("PREDICTION #1: ATP Level Predicts Action Effectiveness")
    print("─" * 70)
    correlation_results = analyze_atp_action_correlation(logs)

    if 'error' not in correlation_results:
        print(f"Samples: {correlation_results['n_samples']}")
        print(f"Correlation: {correlation_results['correlation']:.3f}")
        print(f"P-value: {correlation_results['p_value']:.4f}")
        print(f"Interpretation: {correlation_results['interpretation']}")
        print()

        print("ATP by Action Quality:")
        for quality, label in [(0, 'No Effect'), (1, 'Caused Change'), (2, 'Leveled Up')]:
            if quality in correlation_results['stats_by_quality']:
                stats = correlation_results['stats_by_quality'][quality]
                print(f"  {label:15s}: {stats['mean']:5.1f} ± {stats['std']:4.1f} ATP (n={stats['n']})")

        if correlation_results['anova_p_value']:
            print(f"\nANOVA F-statistic: {correlation_results['f_statistic']:.3f}")
            print(f"ANOVA p-value: {correlation_results['anova_p_value']:.4f}")
            if correlation_results['anova_p_value'] < 0.05:
                print("✓ Significant difference between quality groups")
    else:
        print(f"ERROR: {correlation_results['error']}")

    print()

    # Metabolic States
    print("─" * 70)
    print("Metabolic State Distribution by Outcome")
    print("─" * 70)
    state_counts = analyze_metabolic_states(logs)

    for outcome, states in state_counts.items():
        total = sum(states.values())
        if total > 0:
            print(f"{outcome.replace('_', ' ').title():15s} (n={total}):")
            for state, count in sorted(states.items(), key=lambda x: -x[1]):
                pct = count / total * 100
                print(f"  {state.upper():6s}: {count:3d} ({pct:5.1f}%)")

    print()

    # ATP Trajectories
    print("─" * 70)
    print("ATP Depletion Patterns")
    print("─" * 70)
    trajectories = analyze_atp_trajectory(logs)

    print(f"Successful attempts: {len(trajectories['successful'])}")
    if trajectories['successful']:
        successful_atp = [np.mean(t['atp']) for t in trajectories['successful']]
        print(f"  Mean ATP: {np.mean(successful_atp):.1f} ± {np.std(successful_atp):.1f}")

    print(f"Failed attempts: {len(trajectories['failed'])}")
    if trajectories['failed']:
        failed_atp = [np.mean(t['atp']) for t in trajectories['failed']]
        print(f"  Mean ATP: {np.mean(failed_atp):.1f} ± {np.std(failed_atp):.1f}")

    print()

    # Validation Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if 'error' not in correlation_results:
        if correlation_results['p_value'] < 0.05:
            if correlation_results['correlation'] > 0.3:
                print("✓ PREDICTION #1 SUPPORTED: ATP predicts action effectiveness")
                print(f"  Correlation: {correlation_results['correlation']:.3f} (p={correlation_results['p_value']:.4f})")
            else:
                print("⚠ PREDICTION #1 PARTIAL: Significant but weak correlation")
        else:
            print("✗ PREDICTION #1 NOT SUPPORTED: No significant correlation")

    print()
    print("Next Steps:")
    print("- Increase sample size (more games, more attempts)")
    print("- Test with varying difficulty levels")
    print("- Analyze context layer activation patterns")
    print("- Validate with human-labeled action quality")
    print()

    return {
        'correlation': correlation_results,
        'states': state_counts,
        'trajectories': trajectories
    }


def main():
    logs = load_atp_logs()

    if not logs:
        print("No ATP logs found. Run sage_solver_v8.py with --log-atp flag first.")
        print()
        print("Example:")
        print("  cd ~/ai-workspace/SAGE")
        print("  python3 arc-agi-3/experiments/sage_solver_v8.py --game lp85 --log-atp -v")
        return

    results = generate_report(logs)

    # Save detailed results
    output_file = Path(__file__).parent / "thor_session_62_atp_analysis_results.json"
    with open(output_file, 'w') as f:
        # Convert numpy types to native Python for JSON serialization
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        json.dump(results, f, indent=2, default=convert)

    print(f"Detailed results saved: {output_file}")


if __name__ == "__main__":
    main()
