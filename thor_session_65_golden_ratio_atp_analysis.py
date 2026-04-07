#!/usr/bin/env python3
"""
Thor Session #65: Golden Ratio ATP Coupling Analysis

Analyzes ATP logs from sage_solver_v10 to test the hypothesis:
"ATP is highest when C ≈ φ - 1 ≈ 0.618" (Session #64 Prediction #4).

Tests:
1. Correlation: ATP vs. distance from φ - 1 (expect negative correlation)
2. Golden zone effect: ATP higher when |C - 0.618| < 0.05
3. Optimal C value: Does peak ATP occur at C ≈ 0.618?
4. Action effectiveness: Are actions more effective in golden zone?

Usage:
    python3 thor_session_65_golden_ratio_atp_analysis.py <log_file.json>
"""

import json
import sys
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path

PHI_MINUS_1 = 0.618033988749895
GOLDEN_ZONE_THRESHOLD = 0.05


def load_log(filepath):
    """Load ATP + Coherence log from sage_solver_v10."""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_data(log):
    """Extract ATP, coherence, and effectiveness data from log."""
    atp_coherence_log = log['atp_coherence_log']

    data = {
        'step': [],
        'atp_before': [],
        'atp_after': [],
        'C_before': [],
        'C_after': [],
        'dist_from_phi_before': [],
        'dist_from_phi_after': [],
        'in_golden_zone_before': [],
        'in_golden_zone_after': [],
        'leveled_up': [],
        'actions_caused_change': [],
        'salience': [],
        'plan_time': [],
    }

    for entry in atp_coherence_log:
        data['step'].append(entry['step'])
        data['atp_before'].append(entry['atp_before'])
        data['atp_after'].append(entry['atp_after'])

        coh_before = entry['coherence_before']
        coh_after = entry['coherence_after']

        data['C_before'].append(coh_before['coherence'])
        data['C_after'].append(coh_after['coherence'])
        data['dist_from_phi_before'].append(coh_before['distance_from_phi'])
        data['dist_from_phi_after'].append(coh_after['distance_from_phi'])
        data['in_golden_zone_before'].append(coh_before['in_golden_zone'])
        data['in_golden_zone_after'].append(coh_after['in_golden_zone'])

        data['leveled_up'].append(entry['leveled_up'])
        data['actions_caused_change'].append(entry['actions_caused_change'])
        data['salience'].append(entry['salience_estimated'])
        data['plan_time'].append(entry['plan_time'])

    return data


def test_1_correlation(data):
    """Test 1: Correlation between ATP and distance from φ - 1."""
    atp = np.array(data['atp_before'])
    dist = np.array(data['dist_from_phi_before'])

    # Remove any NaN/inf values
    valid = np.isfinite(atp) & np.isfinite(dist)
    atp = atp[valid]
    dist = dist[valid]

    if len(atp) < 3:
        return None

    # Spearman correlation (robust to outliers)
    rho, p_value = stats.spearmanr(dist, atp)

    # Hypothesis: negative correlation (higher ATP when closer to φ - 1)
    result = {
        'test': 'Test 1: ATP vs. Distance from φ - 1',
        'hypothesis': 'Negative correlation (ATP peaks near φ - 1)',
        'rho': round(rho, 4),
        'p_value': round(p_value, 4) if p_value > 0.0001 else '<0.0001',
        'n': len(atp),
        'significant': p_value < 0.05,
        'direction': 'NEGATIVE (✓)' if rho < 0 else 'POSITIVE (✗)',
        'interpretation': ''
    }

    if rho < -0.3 and p_value < 0.05:
        result['interpretation'] = f"Strong evidence: ATP {-rho:.0%} higher near φ - 1"
    elif rho < -0.1 and p_value < 0.05:
        result['interpretation'] = f"Moderate evidence: ATP {-rho:.0%} higher near φ - 1"
    elif rho < 0 and p_value < 0.05:
        result['interpretation'] = "Weak evidence: slight ATP increase near φ - 1"
    else:
        result['interpretation'] = "No evidence for golden ratio optimum"

    return result


def test_2_golden_zone_effect(data):
    """Test 2: Compare ATP in golden zone vs. outside."""
    atp = np.array(data['atp_before'])
    in_zone = np.array(data['in_golden_zone_before'])

    atp_in_zone = atp[in_zone]
    atp_out_zone = atp[~in_zone]

    if len(atp_in_zone) == 0 or len(atp_out_zone) == 0:
        return None

    # Mann-Whitney U test (non-parametric)
    u_stat, p_value = stats.mannwhitneyu(atp_in_zone, atp_out_zone, alternative='greater')

    result = {
        'test': 'Test 2: Golden Zone Effect',
        'hypothesis': 'ATP higher in golden zone (|C - 0.618| < 0.05)',
        'atp_in_zone_mean': round(np.mean(atp_in_zone), 2),
        'atp_out_zone_mean': round(np.mean(atp_out_zone), 2),
        'atp_in_zone_std': round(np.std(atp_in_zone), 2),
        'atp_out_zone_std': round(np.std(atp_out_zone), 2),
        'n_in_zone': len(atp_in_zone),
        'n_out_zone': len(atp_out_zone),
        'p_value': round(p_value, 4) if p_value > 0.0001 else '<0.0001',
        'significant': p_value < 0.05,
        'effect_size': round(np.mean(atp_in_zone) - np.mean(atp_out_zone), 2),
        'interpretation': ''
    }

    if p_value < 0.05:
        pct = ((np.mean(atp_in_zone) - np.mean(atp_out_zone)) / np.mean(atp_out_zone)) * 100
        result['interpretation'] = f"ATP is {pct:+.1f}% higher in golden zone"
    else:
        result['interpretation'] = "No significant difference"

    return result


def test_3_optimal_c_value(data):
    """Test 3: Find ATP peak by binning C values."""
    atp = np.array(data['atp_before'])
    C = np.array(data['C_before'])

    # Bin C into ranges
    bins = [0, 0.4, 0.5, 0.58, 0.65, 0.7, 1.0]
    bin_labels = ['<0.4', '0.4-0.5', '0.5-0.58', '0.58-0.65', '0.65-0.7', '>0.7']

    bin_indices = np.digitize(C, bins) - 1
    bin_atp_means = []
    bin_counts = []

    for i in range(len(bins) - 1):
        mask = bin_indices == i
        if np.sum(mask) > 0:
            bin_atp_means.append(np.mean(atp[mask]))
            bin_counts.append(np.sum(mask))
        else:
            bin_atp_means.append(np.nan)
            bin_counts.append(0)

    # Find peak bin
    valid_means = [(i, m) for i, m in enumerate(bin_atp_means) if not np.isnan(m)]
    if not valid_means:
        return None

    peak_idx, peak_atp = max(valid_means, key=lambda x: x[1])
    peak_range = bin_labels[peak_idx]

    result = {
        'test': 'Test 3: Optimal C Value',
        'hypothesis': 'ATP peaks in φ - 1 bin (0.58-0.65)',
        'bin_ranges': bin_labels,
        'bin_atp_means': [round(m, 2) if not np.isnan(m) else None for m in bin_atp_means],
        'bin_counts': bin_counts,
        'peak_range': peak_range,
        'peak_atp': round(peak_atp, 2),
        'includes_phi': ('0.58-0.65' in peak_range or '0.5-0.58' in peak_range),
        'interpretation': ''
    }

    if '0.58-0.65' in peak_range:
        result['interpretation'] = "ATP peaks in golden ratio zone (0.58-0.65) ✓"
    elif '0.5-0.58' in peak_range:
        result['interpretation'] = "ATP peaks near golden ratio (0.5-0.58) ~✓"
    else:
        result['interpretation'] = f"ATP peaks at {peak_range}, NOT golden ratio"

    return result


def test_4_action_effectiveness(data):
    """Test 4: Are actions more effective in golden zone?"""
    caused_change = np.array(data['actions_caused_change'])
    leveled_up = np.array(data['leveled_up'])
    in_zone = np.array(data['in_golden_zone_before'])

    # Effectiveness score: 0 = no change, 1 = change, 2 = level up
    effectiveness = caused_change + leveled_up.astype(int)

    eff_in_zone = effectiveness[in_zone]
    eff_out_zone = effectiveness[~in_zone]

    if len(eff_in_zone) == 0 or len(eff_out_zone) == 0:
        return None

    # Mann-Whitney U test
    u_stat, p_value = stats.mannwhitneyu(eff_in_zone, eff_out_zone, alternative='greater')

    result = {
        'test': 'Test 4: Action Effectiveness',
        'hypothesis': 'Actions more effective in golden zone',
        'eff_in_zone_mean': round(np.mean(eff_in_zone), 2),
        'eff_out_zone_mean': round(np.mean(eff_out_zone), 2),
        'n_in_zone': len(eff_in_zone),
        'n_out_zone': len(eff_out_zone),
        'p_value': round(p_value, 4) if p_value > 0.0001 else '<0.0001',
        'significant': p_value < 0.05,
        'interpretation': ''
    }

    if p_value < 0.05:
        pct = ((np.mean(eff_in_zone) - np.mean(eff_out_zone)) / np.mean(eff_out_zone)) * 100
        result['interpretation'] = f"Actions {pct:+.1f}% more effective in golden zone"
    else:
        result['interpretation'] = "No significant difference"

    return result


def plot_results(data, output_path):
    """Generate visualization plots."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: ATP vs. Distance from φ - 1
    ax = axes[0, 0]
    dist = np.array(data['dist_from_phi_before'])
    atp = np.array(data['atp_before'])
    ax.scatter(dist, atp, alpha=0.6, c=data['leveled_up'], cmap='RdYlGn', s=50)
    ax.axvline(GOLDEN_ZONE_THRESHOLD, color='gold', linestyle='--', label='Golden zone boundary')
    ax.set_xlabel('Distance from φ - 1')
    ax.set_ylabel('ATP Before Planning')
    ax.set_title('Test 1: ATP vs. Distance from Golden Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: ATP in vs. out of golden zone
    ax = axes[0, 1]
    in_zone = np.array(data['in_golden_zone_before'])
    atp_in = atp[in_zone]
    atp_out = atp[~in_zone]
    ax.boxplot([atp_out, atp_in], labels=['Outside Golden Zone', 'Inside Golden Zone'])
    ax.set_ylabel('ATP Before Planning')
    ax.set_title('Test 2: Golden Zone Effect on ATP')
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 3: ATP by C bins
    ax = axes[1, 0]
    C = np.array(data['C_before'])
    bins = [0, 0.4, 0.5, 0.58, 0.65, 0.7, 1.0]
    bin_labels = ['<0.4', '0.4-0.5', '0.5-0.58', '0.58-0.65', '0.65-0.7', '>0.7']
    bin_indices = np.digitize(C, bins) - 1
    bin_data = [atp[bin_indices == i] for i in range(len(bins) - 1)]
    ax.boxplot([d for d in bin_data if len(d) > 0], labels=[bin_labels[i] for i in range(len(bin_data)) if len(bin_data[i]) > 0])
    ax.axvline(3.5, color='gold', linestyle='--', alpha=0.7, label='φ - 1 ≈ 0.618')
    ax.set_xlabel('Coherence (C) Range')
    ax.set_ylabel('ATP Before Planning')
    ax.set_title('Test 3: ATP by Coherence Bins')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 4: C trajectory over time
    ax = axes[1, 1]
    steps = np.array(data['step'])
    C_before = np.array(data['C_before'])
    ax.plot(steps, C_before, 'b-', alpha=0.6, label='C (coherence)')
    ax.axhline(PHI_MINUS_1, color='gold', linestyle='--', linewidth=2, label=f'φ - 1 = {PHI_MINUS_1:.4f}')
    ax.axhline(PHI_MINUS_1 + GOLDEN_ZONE_THRESHOLD, color='gold', linestyle=':', alpha=0.5)
    ax.axhline(PHI_MINUS_1 - GOLDEN_ZONE_THRESHOLD, color='gold', linestyle=':', alpha=0.5)
    ax.fill_between(steps, PHI_MINUS_1 - GOLDEN_ZONE_THRESHOLD, PHI_MINUS_1 + GOLDEN_ZONE_THRESHOLD,
                     color='gold', alpha=0.2, label='Golden zone')
    ax.set_xlabel('Step')
    ax.set_ylabel('Coherence (C)')
    ax.set_title('Coherence Trajectory')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Plot saved: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 thor_session_65_golden_ratio_atp_analysis.py <log_file.json>")
        sys.exit(1)

    log_file = sys.argv[1]
    print(f"Thor Session #65: Golden Ratio ATP Analysis")
    print(f"=" * 60)
    print(f"Log file: {log_file}")
    print()

    # Load data
    log = load_log(log_file)
    data = extract_data(log)

    print(f"Game: {log['game_id']}")
    print(f"Result: {log['best_levels']}/{log['win_levels']} levels")
    print(f"Data points: {len(data['step'])}")
    print()

    # Run tests
    print(f"=" * 60)
    print("HYPOTHESIS TESTS")
    print(f"=" * 60)
    print()

    results = []

    # Test 1: Correlation
    test1 = test_1_correlation(data)
    if test1:
        results.append(test1)
        print(f"{test1['test']}")
        print(f"  Hypothesis: {test1['hypothesis']}")
        print(f"  Spearman rho: {test1['rho']} (p = {test1['p_value']})")
        print(f"  Direction: {test1['direction']}")
        print(f"  Result: {test1['interpretation']}")
        print()

    # Test 2: Golden zone effect
    test2 = test_2_golden_zone_effect(data)
    if test2:
        results.append(test2)
        print(f"{test2['test']}")
        print(f"  Hypothesis: {test2['hypothesis']}")
        print(f"  ATP in zone: {test2['atp_in_zone_mean']} ± {test2['atp_in_zone_std']} (n={test2['n_in_zone']})")
        print(f"  ATP out zone: {test2['atp_out_zone_mean']} ± {test2['atp_out_zone_std']} (n={test2['n_out_zone']})")
        print(f"  Effect size: {test2['effect_size']} ATP points")
        print(f"  p-value: {test2['p_value']}")
        print(f"  Result: {test2['interpretation']}")
        print()

    # Test 3: Optimal C
    test3 = test_3_optimal_c_value(data)
    if test3:
        results.append(test3)
        print(f"{test3['test']}")
        print(f"  Hypothesis: {test3['hypothesis']}")
        print(f"  Bins: {test3['bin_ranges']}")
        print(f"  ATP means: {test3['bin_atp_means']}")
        print(f"  Counts: {test3['bin_counts']}")
        print(f"  Peak: {test3['peak_range']} (ATP = {test3['peak_atp']})")
        print(f"  Result: {test3['interpretation']}")
        print()

    # Test 4: Action effectiveness
    test4 = test_4_action_effectiveness(data)
    if test4:
        results.append(test4)
        print(f"{test4['test']}")
        print(f"  Hypothesis: {test4['hypothesis']}")
        print(f"  Effectiveness in zone: {test4['eff_in_zone_mean']} (n={test4['n_in_zone']})")
        print(f"  Effectiveness out zone: {test4['eff_out_zone_mean']} (n={test4['n_out_zone']})")
        print(f"  p-value: {test4['p_value']}")
        print(f"  Result: {test4['interpretation']}")
        print()

    # Generate plots
    print(f"=" * 60)
    print("VISUALIZATION")
    print(f"=" * 60)
    plot_path = log_file.replace('.json', '_analysis.png')
    plot_results(data, plot_path)
    print()

    # Save results
    results_path = log_file.replace('.json', '_results.json')
    with open(results_path, 'w') as f:
        json.dump({
            'game_id': log['game_id'],
            'test_results': results,
            'summary': {
                'total_steps': len(data['step']),
                'time_in_golden_zone': np.sum(data['in_golden_zone_before']),
                'pct_in_golden_zone': round(100 * np.mean(data['in_golden_zone_before']), 1),
                'mean_C': round(np.mean(data['C_before']), 4),
                'mean_dist_from_phi': round(np.mean(data['dist_from_phi_before']), 4),
            }
        }, f, indent=2)
    print(f"Results saved: {results_path}")
    print()

    print(f"=" * 60)
    print("ANALYSIS COMPLETE")
    print(f"=" * 60)


if __name__ == '__main__':
    main()
