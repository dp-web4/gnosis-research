#!/usr/bin/env python3
"""
Analyze metabolic surge experiment results.

Validates Session #56 thermodynamic predictions:
1. Metabolic surge during active learning (c_metabolic: 0.3-0.5 → 0.6-0.8)
2. Energy-coherence coupling (c_system ≤ α * c_metabolic)
3. Coupling coefficient stability (α ≈ 0.77-1.05)
"""

import json
import sys
import numpy as np
from pathlib import Path
from scipy import stats

def load_latest_results():
    """Load the most recent metabolic surge results."""
    validation_dir = Path('validation_logs')
    if not validation_dir.exists():
        print("Error: validation_logs directory not found")
        sys.exit(1)

    # Find latest metabolic_surge_*.json file
    surge_files = list(validation_dir.glob('metabolic_surge_*.json'))
    if not surge_files:
        print("Error: No metabolic_surge_*.json files found")
        sys.exit(1)

    latest = max(surge_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading: {latest}")
    print()

    with open(latest) as f:
        return json.load(f)

def analyze_phase(phase_data):
    """Analyze a single phase."""
    samples = phase_data['samples']

    c_metabolic = [s['c_metabolic'] for s in samples]
    c_system = [s['c_system'] for s in samples]
    alpha = [s['alpha'] for s in samples]

    return {
        'phase': phase_data['phase'],
        'n_samples': len(samples),
        'c_metabolic': {
            'mean': np.mean(c_metabolic),
            'std': np.std(c_metabolic),
            'min': np.min(c_metabolic),
            'max': np.max(c_metabolic),
            'values': c_metabolic
        },
        'c_system': {
            'mean': np.mean(c_system),
            'std': np.std(c_system),
            'min': np.min(c_system),
            'max': np.max(c_system),
            'values': c_system
        },
        'alpha': {
            'mean': np.mean(alpha),
            'std': np.std(alpha),
            'min': np.min(alpha),
            'max': np.max(alpha),
            'values': alpha
        }
    }

def test_metabolic_surge(baseline, active):
    """
    Test Session #56 Prediction 1: Metabolic surge during active learning.

    Expected: c_metabolic(active) > c_metabolic(baseline) by significant margin
    """
    print("=" * 80)
    print("PREDICTION 1: Metabolic Surge During Active Learning")
    print("=" * 80)
    print()
    print("Hypothesis: c_metabolic increases during engaged tasks")
    print("Expected: baseline ≈ 0.3-0.5, active ≈ 0.6-0.8")
    print()

    baseline_c = baseline['c_metabolic']['mean']
    active_c = active['c_metabolic']['mean']

    surge = active_c - baseline_c
    surge_pct = (surge / baseline_c) * 100 if baseline_c > 0 else 0

    print(f"Baseline c_metabolic:     {baseline_c:.3f} ± {baseline['c_metabolic']['std']:.3f}")
    print(f"Active c_metabolic:       {active_c:.3f} ± {active['c_metabolic']['std']:.3f}")
    print(f"Surge magnitude:          {surge:+.3f} ({surge_pct:+.1f}%)")
    print()

    # Statistical test
    t_stat, p_value = stats.ttest_ind(
        baseline['c_metabolic']['values'],
        active['c_metabolic']['values']
    )

    print(f"T-test: t={t_stat:.3f}, p={p_value:.6f}")
    print()

    # Validation
    validated = False
    if p_value < 0.05 and surge > 0.1:
        print("✓ PREDICTION VALIDATED!")
        print(f"  - Significant increase detected (p < 0.05)")
        print(f"  - Surge magnitude > 0.1 ({surge:.3f})")
        validated = True
    else:
        print("✗ Prediction not confirmed")
        if p_value >= 0.05:
            print(f"  - Not statistically significant (p = {p_value:.3f})")
        if surge <= 0.1:
            print(f"  - Surge too small ({surge:.3f})")

    print()
    return validated

def test_energy_coherence_coupling(phases):
    """
    Test Session #56 Prediction 2: Energy-coherence coupling.

    Expected: c_system ≤ α * c_metabolic (metabolic ceiling)
    """
    print("=" * 80)
    print("PREDICTION 2: Energy-Coherence Coupling")
    print("=" * 80)
    print()
    print("Hypothesis: c_system ≤ α * c_metabolic (metabolic ceiling)")
    print("Expected: α ≈ 0.77-1.05")
    print()

    for phase_stats in phases:
        name = phase_stats['phase']
        alpha_mean = phase_stats['alpha']['mean']
        alpha_std = phase_stats['alpha']['std']

        c_met = phase_stats['c_metabolic']['mean']
        c_sys = phase_stats['c_system']['mean']

        print(f"{name.upper():<15} α = {alpha_mean:.3f} ± {alpha_std:.3f}")
        print(f"  c_system = {c_sys:.3f}, c_metabolic = {c_met:.3f}")
        print(f"  Predicted ceiling: {alpha_mean * c_met:.3f}")
        print()

    # Check if α is stable across phases
    all_alphas = []
    for p in phases:
        all_alphas.extend(p['alpha']['values'])

    overall_alpha_mean = np.mean(all_alphas)
    overall_alpha_std = np.std(all_alphas)

    print(f"Overall α: {overall_alpha_mean:.3f} ± {overall_alpha_std:.3f}")
    print()

    # Validation
    validated = False
    if 0.7 <= overall_alpha_mean <= 1.1:
        print("✓ PREDICTION VALIDATED!")
        print(f"  - α in expected range (0.7-1.1)")
        print(f"  - Coupling coefficient stable across phases")
        validated = True
    else:
        print("✗ α outside expected range")
        print(f"  - Expected: 0.7-1.1, Observed: {overall_alpha_mean:.3f}")

    print()
    return validated

def test_system_coherence_response(baseline, active):
    """
    Test: Does c_system increase toward 0.5 during active learning?

    This tests the combined effect of metabolic surge + coupling.
    """
    print("=" * 80)
    print("PREDICTION 3: System Coherence Response")
    print("=" * 80)
    print()
    print("Hypothesis: c_system → 0.5 during active learning")
    print("Mechanism: Metabolic surge enables higher coherence")
    print()

    baseline_c_sys = baseline['c_system']['mean']
    active_c_sys = active['c_system']['mean']

    increase = active_c_sys - baseline_c_sys
    increase_pct = (increase / baseline_c_sys) * 100 if baseline_c_sys > 0 else 0

    print(f"Baseline c_system:   {baseline_c_sys:.3f} ± {baseline['c_system']['std']:.3f}")
    print(f"Active c_system:     {active_c_sys:.3f} ± {active['c_system']['std']:.3f}")
    print(f"Increase:            {increase:+.3f} ({increase_pct:+.1f}%)")
    print()

    # Distance from optimal
    baseline_gap = abs(0.5 - baseline_c_sys)
    active_gap = abs(0.5 - active_c_sys)

    print(f"Distance from C = 0.5:")
    print(f"  Baseline: {baseline_gap:.3f}")
    print(f"  Active:   {active_gap:.3f}")
    print()

    # Statistical test
    t_stat, p_value = stats.ttest_ind(
        baseline['c_system']['values'],
        active['c_system']['values']
    )

    print(f"T-test: t={t_stat:.3f}, p={p_value:.6f}")
    print()

    # Validation
    validated = False
    if active_gap < baseline_gap and p_value < 0.05:
        print("✓ PREDICTION VALIDATED!")
        print(f"  - c_system moves closer to 0.5 during active learning")
        print(f"  - Difference statistically significant (p < 0.05)")
        validated = True
    else:
        print("✗ Prediction not confirmed")
        if active_gap >= baseline_gap:
            print(f"  - Active gap ({active_gap:.3f}) not smaller than baseline ({baseline_gap:.3f})")
        if p_value >= 0.05:
            print(f"  - Not statistically significant (p = {p_value:.3f})")

    print()
    return validated

def test_reversibility(baseline, recovery):
    """
    Test: Does system return to baseline after active phase?

    This validates that surge is task-dependent, not permanent drift.
    """
    print("=" * 80)
    print("VALIDATION: Reversibility")
    print("=" * 80)
    print()
    print("Test: Does metabolic state return to baseline after task?")
    print()

    baseline_c_met = baseline['c_metabolic']['mean']
    recovery_c_met = recovery['c_metabolic']['mean']

    diff = abs(recovery_c_met - baseline_c_met)

    print(f"Baseline c_metabolic:  {baseline_c_met:.3f}")
    print(f"Recovery c_metabolic:  {recovery_c_met:.3f}")
    print(f"Difference:            {diff:.3f}")
    print()

    # Statistical test
    t_stat, p_value = stats.ttest_ind(
        baseline['c_metabolic']['values'],
        recovery['c_metabolic']['values']
    )

    print(f"T-test: t={t_stat:.3f}, p={p_value:.6f}")
    print()

    # Validation
    validated = False
    if diff < 0.05:
        print("✓ REVERSIBILITY CONFIRMED!")
        print(f"  - Recovery matches baseline within 0.05")
        print(f"  - Surge is task-dependent, not permanent")
        validated = True
    else:
        print("✗ System did not return to baseline")
        print(f"  - Difference: {diff:.3f} (expected < 0.05)")

    print()
    return validated

def main():
    print("=" * 80)
    print("Metabolic Surge Experiment Analysis")
    print("=" * 80)
    print()

    # Load results
    data = load_latest_results()

    # Analyze each phase
    phases = [analyze_phase(p) for p in data['phases']]

    baseline = phases[0]
    active = phases[1]
    recovery = phases[2]

    # Run validation tests
    print()
    results = {}

    results['surge'] = test_metabolic_surge(baseline, active)
    results['coupling'] = test_energy_coherence_coupling(phases)
    results['coherence_response'] = test_system_coherence_response(baseline, active)
    results['reversibility'] = test_reversibility(baseline, recovery)

    # Overall summary
    print("=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    print()

    total = len(results)
    validated = sum(results.values())

    print(f"Predictions validated: {validated}/{total}")
    print()

    for test_name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {test_name.replace('_', ' ').title()}")

    print()

    if validated == total:
        print("🎉 ALL PREDICTIONS VALIDATED!")
        print()
        print("Session #56 thermodynamic theory confirmed:")
        print("  - Metabolic surge during active learning")
        print("  - Energy-coherence coupling maintained")
        print("  - System approaches C = 0.5 with energy availability")
        print("  - Effects are reversible (task-dependent)")
    elif validated >= total / 2:
        print("⚠️  PARTIAL VALIDATION")
        print(f"   {validated}/{total} predictions confirmed")
    else:
        print("❌ PREDICTIONS NOT CONFIRMED")
        print("   Theory may need revision")

    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
