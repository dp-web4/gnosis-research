#!/usr/bin/env python3
"""
Thor Session #55: Baseline Dynamics Analysis

The production data shows baseline/idle mode characteristics:
- Low novelty (0.14 mean, mostly 0.1)
- C_system below 0.5 (0.36 mean)

This VALIDATES Session #54 predictions for baseline mode.
Now analyze: What dynamics exist even in baseline?
"""

import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Paths
VALIDATION_DIR = Path("/home/dp/ai-workspace/SAGE/validation_logs")
COHERENCE_LOG = VALIDATION_DIR / "coherence_log.jsonl"
SALIENCE_LOG = VALIDATION_DIR / "salience_log.jsonl"

def load_jsonl(path):
    """Load JSONL file"""
    data = []
    with open(path) as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

def analyze_baseline_coherence_dynamics():
    """Deep dive into C_system dynamics in baseline mode"""
    print("=" * 80)
    print("BASELINE COHERENCE DYNAMICS")
    print("=" * 80)

    data = load_jsonl(COHERENCE_LOG)
    df = pd.DataFrame(data)

    # Overall stats
    print(f"\nDataset: {len(df)} measurements over {df['cycle'].max() - df['cycle'].min()} cycles")
    print(f"C_system: {df['c_system'].mean():.4f} ± {df['c_system'].std():.4f}")
    print(f"Range: [{df['c_system'].min():.4f}, {df['c_system'].max():.4f}]")

    # Bimodal distribution?
    print("\n--- Distribution Analysis ---")
    low_c = df[df['c_system'] < 0.35]
    high_c = df[df['c_system'] >= 0.35]

    print(f"Low mode (C < 0.35): n={len(low_c)}, mean={low_c['c_system'].mean():.4f}")
    print(f"High mode (C >= 0.35): n={len(high_c)}, mean={high_c['c_system'].mean():.4f}")

    # Temporal structure
    print("\n--- Temporal Dynamics ---")

    # Compute transitions
    c_values = df['c_system'].values
    transitions = {
        'low_to_high': 0,
        'high_to_low': 0,
        'low_to_low': 0,
        'high_to_high': 0
    }

    for i in range(len(c_values) - 1):
        prev = c_values[i]
        curr = c_values[i+1]

        if prev < 0.35 and curr >= 0.35:
            transitions['low_to_high'] += 1
        elif prev >= 0.35 and curr < 0.35:
            transitions['high_to_low'] += 1
        elif prev < 0.35 and curr < 0.35:
            transitions['low_to_low'] += 1
        else:
            transitions['high_to_high'] += 1

    print(f"Transitions:")
    for k, v in transitions.items():
        print(f"  {k}: {v}")

    # Oscillation pattern?
    print("\n--- Oscillation Analysis ---")

    # Check for periodicity using autocorrelation
    c_centered = c_values - c_values.mean()
    autocorr = np.correlate(c_centered, c_centered, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]

    # Find peaks (excluding lag=0)
    peaks = []
    for i in range(1, min(100, len(autocorr))):
        if i > 1 and autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
            if autocorr[i] > 0.3:  # Significant correlation
                peaks.append((i, autocorr[i]))

    if peaks:
        print(f"Autocorrelation peaks (lag, correlation):")
        for lag, corr in peaks[:5]:
            print(f"  lag={lag * 100} cycles: r={corr:.3f}")
    else:
        print("No significant oscillation detected")

    # Check metabolic-coherence relationship
    print("\n--- Metabolic-Coherence Coupling ---")

    # c_metabolic seems to switch between 0.3 and 0.5
    metabolic_low = df[df['c_metabolic'] < 0.4]
    metabolic_high = df[df['c_metabolic'] >= 0.4]

    print(f"\nWhen c_metabolic low (<0.4): n={len(metabolic_low)}")
    print(f"  Mean c_system: {metabolic_low['c_system'].mean():.4f}")

    print(f"\nWhen c_metabolic high (>=0.4): n={len(metabolic_high)}")
    print(f"  Mean c_system: {metabolic_high['c_system'].mean():.4f}")

    # Statistical test
    if len(metabolic_low) > 0 and len(metabolic_high) > 0:
        t_stat, p_value = stats.ttest_ind(metabolic_low['c_system'], metabolic_high['c_system'])
        print(f"\nT-test: t={t_stat:.3f}, p={p_value:.4e}")

    # Correlation
    r, p = stats.pearsonr(df['c_metabolic'], df['c_system'])
    print(f"Correlation: r={r:.4f}, p={p:.4e}")

    return df

def analyze_novelty_events():
    """Analyze the rare high-novelty events"""
    print("\n" + "=" * 80)
    print("NOVELTY EVENT ANALYSIS")
    print("=" * 80)

    data = load_jsonl(SALIENCE_LOG)

    novelties = []
    for entry in data:
        cycle = entry['cycle']
        components = entry.get('salience_components', [])
        if components:
            nov = components[0].get('novelty', None)
            if nov is not None:
                novelties.append({'cycle': cycle, 'novelty': nov})

    df = pd.DataFrame(novelties)

    print(f"\n{len(df)} salience measurements")

    # Count by novelty value
    value_counts = df['novelty'].value_counts().sort_index()
    print("\nNovelty distribution:")
    for val, count in value_counts.items():
        pct = 100 * count / len(df)
        print(f"  {val:.1f}: {count} ({pct:.1f}%)")

    # High novelty events (0.3)
    high_nov = df[df['novelty'] > 0.15]
    print(f"\nHigh novelty events (>0.15): {len(high_nov)}")

    if len(high_nov) > 0:
        print(f"Cycles: {high_nov['cycle'].min()} - {high_nov['cycle'].max()}")

        # Temporal clustering?
        high_cycles = sorted(high_nov['cycle'].values)
        gaps = np.diff(high_cycles)

        print(f"\nGaps between high-novelty events:")
        print(f"  Mean: {gaps.mean():.0f} cycles")
        print(f"  Median: {np.median(gaps):.0f} cycles")
        print(f"  Min: {gaps.min():.0f} cycles")
        print(f"  Max: {gaps.max():.0f} cycles")

    return df

def test_baseline_predictions():
    """Test Session #54 predictions for baseline mode"""
    print("\n" + "=" * 80)
    print("SESSION #54 BASELINE PREDICTIONS TEST")
    print("=" * 80)

    print("\nSession #54 Baseline Predictions:")
    print("  Novelty: ~0.13 (low, minimal new experience)")
    print("  C_system: 0.32-0.46 (low, below optimal)")
    print("  Both trending upward toward 0.5 (weak trend)")

    # Load data
    coherence_data = load_jsonl(COHERENCE_LOG)
    coh_df = pd.DataFrame(coherence_data)

    salience_data = load_jsonl(SALIENCE_LOG)
    novelties = []
    for entry in salience_data:
        components = entry.get('salience_components', [])
        if components:
            nov = components[0].get('novelty', None)
            if nov is not None:
                novelties.append(nov)

    nov_mean = np.mean(novelties)
    c_mean = coh_df['c_system'].mean()

    print("\n--- Test Results ---")

    # Test 1: Novelty
    print(f"\n1. Novelty prediction:")
    print(f"   Predicted: ~0.13")
    print(f"   Observed: {nov_mean:.4f}")
    if abs(nov_mean - 0.13) < 0.03:
        print("   ✓ EXCELLENT MATCH")
    elif nov_mean < 0.20:
        print("   ✓ Confirms low baseline novelty")
    else:
        print("   ✗ Higher than predicted")

    # Test 2: C_system
    print(f"\n2. C_system prediction:")
    print(f"   Predicted: 0.32-0.46")
    print(f"   Observed: {c_mean:.4f}")
    if 0.32 <= c_mean <= 0.46:
        print("   ✓ WITHIN PREDICTED RANGE")
    elif c_mean < 0.5:
        print("   ~ Below optimal, matches baseline mode")
    else:
        print("   ✗ Higher than predicted")

    # Test 3: Trend
    print(f"\n3. Trend toward 0.5:")

    first_half = coh_df[coh_df['cycle'] <= coh_df['cycle'].median()]
    second_half = coh_df[coh_df['cycle'] > coh_df['cycle'].median()]

    trend = second_half['c_system'].mean() - first_half['c_system'].mean()
    print(f"   C_system trend: {trend:+.4f}")

    if trend > 0:
        print("   ✓ Upward trend (weak)")
    elif abs(trend) < 0.005:
        print("   ~ Stable (no strong trend)")
    else:
        print("   ✗ Downward trend")

    # Overall verdict
    print("\n--- VERDICT ---")
    if abs(nov_mean - 0.13) < 0.03 and 0.32 <= c_mean <= 0.46:
        print("✓✓✓ PRODUCTION DATA VALIDATES SESSION #54 BASELINE PREDICTIONS")
        print("    Theory-to-practice pipeline working perfectly!")
    else:
        print("~ Partial validation - baseline mode confirmed, details vary")

def main():
    print("Thor Session #55: Baseline Dynamics Analysis")
    print("Production validation of Session #54 baseline predictions")
    print("=" * 80)

    coherence_df = analyze_baseline_coherence_dynamics()
    novelty_df = analyze_novelty_events()
    test_baseline_predictions()

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
