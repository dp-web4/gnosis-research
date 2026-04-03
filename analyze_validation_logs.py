#!/usr/bin/env python3
"""
Analysis script for C ≈ 0.5 empirical validation logs

Processes logs from SAGE consciousness experiments and validates
predictions from Thor Session #51.

Usage:
    python analyze_validation_logs.py [--log-dir VALIDATION_LOGS_PATH]
"""

import json
import argparse
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt


def load_jsonl(filepath):
    """Load JSONL file into list of dicts."""
    if not Path(filepath).exists():
        return []
    with open(filepath) as f:
        return [json.loads(line) for line in f]


def analyze_trust_distribution(data):
    """Analyze Experiment 1: Trust weight distribution."""
    if not data:
        print("⚠️  No trust distribution data found")
        return

    print("\n" + "="*80)
    print("EXPERIMENT 1: Trust Weight Distribution")
    print("="*80)

    cycles = [d['cycle'] for d in data]
    means = [d['mean'] for d in data]
    stds = [d['std'] for d in data]

    # Statistics
    avg_mean = np.mean(means)
    avg_std = np.mean(stds)

    print(f"Measurements: {len(data)}")
    print(f"Cycle range: {min(cycles)} - {max(cycles)}")
    print(f"\nMean trust weight: {avg_mean:.3f}")
    print(f"  Expected: 0.5-0.7")
    print(f"  ✅ PASS" if 0.5 <= avg_mean <= 0.7 else f"  ❌ FAIL")

    print(f"\nStd trust weight: {avg_std:.3f}")
    print(f"  Expected: 0.15-0.25")
    print(f"  ✅ PASS" if 0.15 <= avg_std <= 0.25 else f"  ❌ FAIL")

    # Plot
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    plt.plot(cycles, means, label='Mean trust', linewidth=2)
    plt.axhline(0.5, color='r', linestyle='--', alpha=0.5, label='C = 0.5')
    plt.axhline(0.65, color='g', linestyle='--', alpha=0.5, label='Expected ~0.65')
    plt.fill_between(cycles, 0.5, 0.7, alpha=0.1, color='g', label='Expected range')
    plt.xlabel('Cycle')
    plt.ylabel('Mean Trust Weight')
    plt.legend()
    plt.title('Trust Weight Evolution')
    plt.grid(alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(cycles, stds, label='Std dev', linewidth=2, color='orange')
    plt.axhline(0.2, color='r', linestyle='--', alpha=0.5, label='Expected ~0.2')
    plt.fill_between(cycles, 0.15, 0.25, alpha=0.1, color='g', label='Expected range')
    plt.xlabel('Cycle')
    plt.ylabel('Standard Deviation')
    plt.legend()
    plt.title('Trust Weight Diversity')
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('validation_trust_distribution.png', dpi=150)
    print(f"\n📊 Plot saved: validation_trust_distribution.png")


def analyze_metabolic_states(data):
    """Analyze Experiment 2: Metabolic state distribution."""
    if not data:
        print("⚠️  No metabolic state data found")
        return

    print("\n" + "="*80)
    print("EXPERIMENT 2: Metabolic State Distribution")
    print("="*80)

    cycles = [d['cycle'] for d in data]
    states = [d['state'] for d in data]

    # Count states
    state_counts = Counter(states)
    total = len(states)
    state_pcts = {s: count/total * 100 for s, count in state_counts.items()}

    # Map states to coherence values
    state_coherence = {
        'wake': 0.5,
        'rest': 0.3,
        'dream': 0.7,
        'crisis': 0.9
    }

    # Compute average coherence
    avg_coherence = sum(
        state_pcts.get(s.lower(), 0)/100 * c
        for s, c in state_coherence.items()
    )

    print(f"Total cycles: {total}")
    print(f"Cycle range: {min(cycles)} - {max(cycles)}")
    print(f"\nState distribution:")
    for state, pct in sorted(state_pcts.items()):
        print(f"  {state:8s}: {pct:5.1f}%")

    print(f"\nWAKE percentage: {state_pcts.get('wake', state_pcts.get('WAKE', 0)):.1f}%")
    print(f"  Expected: 60-70%")
    wake_pct = state_pcts.get('wake', state_pcts.get('WAKE', 0))
    print(f"  ✅ PASS" if 60 <= wake_pct <= 70 else f"  ❌ FAIL")

    print(f"\nAverage system coherence: {avg_coherence:.3f}")
    print(f"  Expected: ~0.5")
    print(f"  ✅ PASS" if 0.45 <= avg_coherence <= 0.55 else f"  ❌ FAIL")

    # Plot
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    plt.bar(state_pcts.keys(), state_pcts.values(), alpha=0.7)
    plt.axhline(65, color='r', linestyle='--', alpha=0.5, label='Expected WAKE ~65%')
    plt.ylabel('Percentage (%)')
    plt.title('Metabolic State Distribution')
    plt.legend()
    plt.grid(alpha=0.3, axis='y')

    plt.subplot(1, 2, 2)
    plt.bar(['Measured', 'Expected'], [avg_coherence, 0.5], alpha=0.7)
    plt.ylabel('System Coherence')
    plt.ylim(0, 1)
    plt.axhline(0.5, color='r', linestyle='--', alpha=0.5)
    plt.title('Average System Coherence')
    plt.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('validation_metabolic_states.png', dpi=150)
    print(f"\n📊 Plot saved: validation_metabolic_states.png")


def analyze_coherence(data):
    """Analyze Experiment 6: Direct coherence measurement."""
    if not data:
        print("⚠️  No coherence data found")
        return

    print("\n" + "="*80)
    print("EXPERIMENT 6: Direct Coherence Measurement")
    print("="*80)

    cycles = [d['cycle'] for d in data]
    c_system = [d['c_system'] for d in data]
    c_trust = [d['c_trust'] for d in data]
    c_metabolic = [d['c_metabolic'] for d in data]
    c_salience = [d['c_salience'] for d in data]
    c_atp = [d['c_atp'] for d in data]

    # Statistics
    mean_c = np.mean(c_system)
    std_c = np.std(c_system)

    print(f"Measurements: {len(data)}")
    print(f"Cycle range: {min(cycles)} - {max(cycles)}")
    print(f"\nMean C_system: {mean_c:.3f}")
    print(f"  Expected: 0.45-0.55")
    print(f"  ✅ PASS" if 0.45 <= mean_c <= 0.55 else f"  ❌ FAIL")

    print(f"\nStd C_system: {std_c:.3f}")
    print(f"  Expected: 0.05-0.15")
    print(f"  ✅ PASS" if 0.05 <= std_c <= 0.15 else f"  ❌ FAIL")

    print(f"\nComponent coherences:")
    print(f"  C_trust:     {np.mean(c_trust):.3f}")
    print(f"  C_metabolic: {np.mean(c_metabolic):.3f}")
    print(f"  C_salience:  {np.mean(c_salience):.3f}")
    print(f"  C_atp:       {np.mean(c_atp):.3f}")

    # Plot
    fig = plt.figure(figsize=(12, 10))

    # Overall coherence evolution
    ax1 = plt.subplot(3, 1, 1)
    ax1.plot(cycles, c_system, label='C_system (weighted avg)', linewidth=2)
    ax1.axhline(0.5, color='r', linestyle='--', alpha=0.5, label='C = 0.5')
    ax1.fill_between(cycles, 0.4, 0.6, alpha=0.1, color='g', label='Expected range')
    ax1.set_ylabel('System Coherence')
    ax1.set_title('Overall System Coherence Over Time')
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Component coherences
    ax2 = plt.subplot(3, 1, 2)
    ax2.plot(cycles, c_trust, label='C_trust', alpha=0.7)
    ax2.plot(cycles, c_metabolic, label='C_metabolic', alpha=0.7)
    ax2.plot(cycles, c_salience, label='C_salience', alpha=0.7)
    ax2.plot(cycles, c_atp, label='C_atp', alpha=0.7)
    ax2.axhline(0.5, color='r', linestyle='--', alpha=0.3)
    ax2.set_ylabel('Component Coherence')
    ax2.set_title('Component Coherence Signals')
    ax2.legend()
    ax2.grid(alpha=0.3)

    # Distribution
    ax3 = plt.subplot(3, 1, 3)
    ax3.hist(c_system, bins=30, density=True, alpha=0.7, edgecolor='black')
    ax3.axvline(mean_c, color='r', linestyle='--', linewidth=2,
                label=f'Mean: {mean_c:.2f}')
    ax3.axvline(0.5, color='g', linestyle='--', linewidth=2, label='Expected: 0.5')
    ax3.set_xlabel('C_system')
    ax3.set_ylabel('Density')
    ax3.set_title('System Coherence Distribution')
    ax3.legend()
    ax3.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('validation_coherence_measurement.png', dpi=150)
    print(f"\n📊 Plot saved: validation_coherence_measurement.png")


def analyze_salience(data):
    """Analyze Experiment 3: SNARC salience distribution."""
    if not data:
        print("⚠️  No salience data found")
        return

    print("\n" + "="*80)
    print("EXPERIMENT 3: SNARC Salience Distribution")
    print("="*80)

    # Flatten all salience values
    all_salience = []
    for entry in data:
        all_salience.extend(entry['salience_total'])

    if not all_salience:
        print("⚠️  No salience scores in data")
        return

    mean_sal = np.mean(all_salience)
    std_sal = np.std(all_salience)

    print(f"Total salience scores: {len(all_salience)}")
    print(f"From {len(data)} cycles")

    print(f"\nMean salience: {mean_sal:.3f}")
    print(f"  Expected: 0.4-0.6")
    print(f"  ✅ PASS" if 0.4 <= mean_sal <= 0.6 else f"  ❌ FAIL")

    print(f"\nStd salience: {std_sal:.3f}")
    print(f"  Expected: 0.15-0.25")
    print(f"  ✅ PASS" if 0.15 <= std_sal <= 0.25 else f"  ❌ FAIL")

    # Plot
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.hist(all_salience, bins=50, density=True, alpha=0.7, edgecolor='black')
    plt.axvline(mean_sal, color='r', linestyle='--', linewidth=2,
                label=f'Mean: {mean_sal:.2f}')
    plt.axvline(0.5, color='g', linestyle='--', linewidth=2, label='Expected: 0.5')
    plt.xlabel('Salience Score')
    plt.ylabel('Density')
    plt.legend()
    plt.title('Salience Distribution')
    plt.grid(alpha=0.3, axis='y')

    plt.subplot(1, 2, 2)
    info_text = f"""
    Statistics:

    Mean: {mean_sal:.3f}
    Std:  {std_sal:.3f}
    Min:  {min(all_salience):.3f}
    Max:  {max(all_salience):.3f}

    Samples: {len(all_salience):,}
    Cycles:  {len(data):,}
    """
    plt.text(0.5, 0.5, info_text, ha='center', va='center',
             fontsize=11, family='monospace')
    plt.axis('off')

    plt.tight_layout()
    plt.savefig('validation_salience_distribution.png', dpi=150)
    print(f"\n📊 Plot saved: validation_salience_distribution.png")


def generate_summary_report(args):
    """Generate comprehensive validation summary."""
    log_dir = Path(args.log_dir)

    print("\n" + "="*80)
    print("C ≈ 0.5 EMPIRICAL VALIDATION ANALYSIS")
    print("Thor Session #52 - SAGE Consciousness Validation")
    print("="*80)

    # Load all logs
    trust_data = load_jsonl(log_dir / 'trust_distribution_log.jsonl')
    metabolic_data = load_jsonl(log_dir / 'metabolic_state_log.jsonl')
    coherence_data = load_jsonl(log_dir / 'coherence_log.jsonl')
    salience_data = load_jsonl(log_dir / 'salience_log.jsonl')

    # Analyze each experiment
    analyze_trust_distribution(trust_data)
    analyze_metabolic_states(metabolic_data)
    analyze_salience(salience_data)
    analyze_coherence(coherence_data)

    # Overall summary
    print("\n" + "="*80)
    print("OVERALL VALIDATION SUMMARY")
    print("="*80)

    experiments_run = sum([
        bool(trust_data),
        bool(metabolic_data),
        bool(coherence_data),
        bool(salience_data)
    ])

    print(f"\nExperiments with data: {experiments_run}/4")
    print(f"\nNext steps:")
    if experiments_run < 4:
        print("  - Continue running SAGE to collect more data")
        print("  - Ensure validation logging is enabled")
    else:
        print("  - Review all plots for pattern validation")
        print("  - Run longer collection periods for higher confidence")
        print("  - Compare results to Session #51 predictions")

    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze C ≈ 0.5 validation logs from SAGE')
    parser.add_argument(
        '--log-dir',
        default='validation_logs',
        help='Directory containing validation log files')

    args = parser.parse_args()

    generate_summary_report(args)


if __name__ == '__main__':
    main()
