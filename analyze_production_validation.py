#!/usr/bin/env python3
"""
Thor Session #55: Production Validation of Novelty-Coherence Coupling

Analyzes real SAGE validation logs to test Session #54 hypothesis:
- Novelty and C_system should be strongly correlated
- Both should trend toward 0.5 in active learning
- Validates whether C ≈ 0.5 is observed in production

Data:
- 2,432 coherence measurements (c_system, c_trust, c_metabolic, c_salience, c_atp)
- 782 salience measurements (novelty, surprise, arousal, reward, conflict)
- 253,000 cycles of SAGE operation
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
METABOLIC_LOG = VALIDATION_DIR / "metabolic_state_log.jsonl"
TRUST_LOG = VALIDATION_DIR / "trust_distribution_log.jsonl"

def load_jsonl(path):
    """Load JSONL file into list of dicts"""
    data = []
    with open(path) as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

def extract_novelty_from_salience(salience_data):
    """Extract novelty values from salience log"""
    novelties = []
    for entry in salience_data:
        cycle = entry.get('cycle')
        components = entry.get('salience_components', [])
        if components:
            novelty = components[0].get('novelty', None)
            if novelty is not None:
                novelties.append({'cycle': cycle, 'novelty': novelty})
    return pd.DataFrame(novelties)

def analyze_coherence_evolution():
    """Analyze how C_system evolves over time"""
    print("=" * 80)
    print("COHERENCE EVOLUTION ANALYSIS")
    print("=" * 80)

    coherence_data = load_jsonl(COHERENCE_LOG)
    df = pd.DataFrame(coherence_data)

    print(f"\n{len(df)} coherence measurements")
    print(f"Cycle range: {df['cycle'].min()} - {df['cycle'].max()}")

    print("\nCoherence Statistics:")
    print(df[['c_system', 'c_trust', 'c_metabolic', 'c_salience', 'c_atp']].describe())

    # Test if C_system converges toward 0.5
    print("\n--- C_system Convergence Test ---")
    print(f"Mean C_system: {df['c_system'].mean():.4f}")
    print(f"Std C_system: {df['c_system'].std():.4f}")
    print(f"Min C_system: {df['c_system'].min():.4f}")
    print(f"Max C_system: {df['c_system'].max():.4f}")

    # Temporal trend
    first_half = df[df['cycle'] <= df['cycle'].median()]
    second_half = df[df['cycle'] > df['cycle'].median()]

    print(f"\nFirst half mean: {first_half['c_system'].mean():.4f}")
    print(f"Second half mean: {second_half['c_system'].mean():.4f}")
    print(f"Change: {second_half['c_system'].mean() - first_half['c_system'].mean():.4f}")

    # Correlation with cycle number
    r_cycle, p_cycle = stats.pearsonr(df['cycle'], df['c_system'])
    print(f"\nCorrelation with cycle: r = {r_cycle:.4f}, p = {p_cycle:.4e}")

    return df

def analyze_novelty_distribution():
    """Analyze novelty distribution from salience log"""
    print("\n" + "=" * 80)
    print("NOVELTY DISTRIBUTION ANALYSIS")
    print("=" * 80)

    salience_data = load_jsonl(SALIENCE_LOG)
    df = extract_novelty_from_salience(salience_data)

    print(f"\n{len(df)} novelty measurements")
    print(f"Cycle range: {df['cycle'].min()} - {df['cycle'].max()}")

    print("\nNovelty Statistics:")
    print(df['novelty'].describe())

    # Count distinct values
    unique_novelties = df['novelty'].unique()
    print(f"\nDistinct novelty values: {len(unique_novelties)}")
    print(f"Most common: {df['novelty'].value_counts().head()}")

    return df

def align_and_correlate(coherence_df, novelty_df):
    """Align coherence and novelty by cycle and compute correlation"""
    print("\n" + "=" * 80)
    print("NOVELTY-COHERENCE CORRELATION ANALYSIS")
    print("=" * 80)

    # Merge on cycle
    merged = pd.merge(coherence_df, novelty_df, on='cycle', how='inner')

    print(f"\n{len(merged)} aligned measurements")

    if len(merged) == 0:
        print("WARNING: No aligned measurements! Coherence and novelty logs have different cycle sampling.")

        # Try nearest-neighbor alignment
        print("\nAttempting nearest-neighbor alignment...")
        coherence_cycles = set(coherence_df['cycle'])

        aligned = []
        for _, nov_row in novelty_df.iterrows():
            cycle = nov_row['cycle']
            # Find nearest coherence measurement
            nearest = min(coherence_cycles, key=lambda x: abs(x - cycle))
            if abs(nearest - cycle) <= 100:  # Within 100 cycles
                coh_row = coherence_df[coherence_df['cycle'] == nearest].iloc[0]
                aligned.append({
                    'cycle': cycle,
                    'novelty': nov_row['novelty'],
                    'c_system': coh_row['c_system'],
                    'c_salience': coh_row['c_salience']
                })

        if aligned:
            merged = pd.DataFrame(aligned)
            print(f"Aligned {len(merged)} measurements via nearest neighbor")
        else:
            print("ERROR: Could not align data")
            return None

    print("\nCorrelation Analysis:")

    # Novelty vs C_system
    if merged['novelty'].std() > 0 and merged['c_system'].std() > 0:
        r_system, p_system = stats.pearsonr(merged['novelty'], merged['c_system'])
        print(f"Novelty vs C_system: r = {r_system:.4f}, p = {p_system:.4e}")
    else:
        print("Novelty vs C_system: No variance (constant values)")
        r_system = np.nan

    # Novelty vs C_salience
    if merged['novelty'].std() > 0 and merged['c_salience'].std() > 0:
        r_salience, p_salience = stats.pearsonr(merged['novelty'], merged['c_salience'])
        print(f"Novelty vs C_salience: r = {r_salience:.4f}, p = {p_salience:.4e}")
    else:
        print("Novelty vs C_salience: No variance (constant values)")

    print("\nDescriptive Statistics:")
    print(merged[['novelty', 'c_system', 'c_salience']].describe())

    return merged

def analyze_temporal_windows(merged_df):
    """Analyze correlation in temporal windows"""
    print("\n" + "=" * 80)
    print("TEMPORAL WINDOW ANALYSIS")
    print("=" * 80)

    if merged_df is None or len(merged_df) == 0:
        print("No data to analyze")
        return

    # Split into windows
    n_windows = 10
    window_size = len(merged_df) // n_windows

    print(f"\nSplitting into {n_windows} windows of ~{window_size} measurements each")

    results = []
    for i in range(n_windows):
        start = i * window_size
        end = start + window_size if i < n_windows - 1 else len(merged_df)
        window = merged_df.iloc[start:end]

        if window['novelty'].std() > 0 and window['c_system'].std() > 0:
            r, p = stats.pearsonr(window['novelty'], window['c_system'])
        else:
            r, p = np.nan, np.nan

        results.append({
            'window': i,
            'start_cycle': window['cycle'].min(),
            'end_cycle': window['cycle'].max(),
            'n': len(window),
            'mean_novelty': window['novelty'].mean(),
            'mean_c_system': window['c_system'].mean(),
            'correlation': r
        })

    results_df = pd.DataFrame(results)
    print("\n", results_df.to_string(index=False))

    return results_df

def test_session_54_hypothesis(merged_df):
    """Test specific predictions from Session #54"""
    print("\n" + "=" * 80)
    print("SESSION #54 HYPOTHESIS TEST")
    print("=" * 80)

    if merged_df is None or len(merged_df) == 0:
        print("No data to test")
        return

    print("\nSession #54 Predictions:")
    print("1. Novelty and C_system should be strongly correlated")
    print("2. Both should trend toward 0.5 in active learning")
    print("3. Baseline (low activity) → low novelty (~0.13), low C_system (~0.32-0.46)")

    print("\n--- Test Results ---")

    # Prediction 1: Correlation
    if merged_df['novelty'].std() > 0 and merged_df['c_system'].std() > 0:
        r, p = stats.pearsonr(merged_df['novelty'], merged_df['c_system'])
        print(f"\n1. Correlation: r = {r:.4f}, p = {p:.4e}")
        if abs(r) > 0.5 and p < 0.01:
            print("   ✓ Strong correlation confirmed")
        elif abs(r) > 0.3 and p < 0.05:
            print("   ~ Moderate correlation observed")
        else:
            print("   ✗ Weak or no correlation")
    else:
        print("\n1. Correlation: Cannot compute (no variance)")
        print("   ℹ This suggests constant values - likely baseline/idle mode")

    # Prediction 2: Values near 0.5
    mean_novelty = merged_df['novelty'].mean()
    mean_c_system = merged_df['c_system'].mean()

    print(f"\n2. Mean values:")
    print(f"   Novelty: {mean_novelty:.4f}")
    print(f"   C_system: {mean_c_system:.4f}")

    if 0.4 <= mean_novelty <= 0.6:
        print(f"   ✓ Novelty near 0.5 (active learning range)")
    elif mean_novelty < 0.2:
        print(f"   ℹ Low novelty ({mean_novelty:.2f}) - suggests baseline/idle mode")
    else:
        print(f"   ~ Novelty outside expected range")

    if 0.4 <= mean_c_system <= 0.6:
        print(f"   ✓ C_system near 0.5 (optimal range)")
    elif mean_c_system < 0.4:
        print(f"   ℹ C_system = {mean_c_system:.2f} - below optimal (matches low novelty)")
    else:
        print(f"   ~ C_system outside expected range")

    # Prediction 3: Check if this is baseline
    if mean_novelty < 0.15 and mean_c_system < 0.45:
        print("\n3. Data Classification: BASELINE/IDLE MODE")
        print("   Matches Session #53 baseline characteristics")
    elif mean_novelty > 0.35 and mean_c_system > 0.4:
        print("\n3. Data Classification: ACTIVE LEARNING MODE")
        print("   New data - first observation of active mode!")
    else:
        print("\n3. Data Classification: INTERMEDIATE/MIXED MODE")

def main():
    print("Thor Session #55: Production Validation of Novelty-Coherence Coupling")
    print("=" * 80)

    # Load and analyze data
    coherence_df = analyze_coherence_evolution()
    novelty_df = analyze_novelty_distribution()

    # Align and correlate
    merged_df = align_and_correlate(coherence_df, novelty_df)

    # Temporal analysis
    if merged_df is not None and len(merged_df) > 0:
        window_results = analyze_temporal_windows(merged_df)

    # Test Session #54 hypothesis
    test_session_54_hypothesis(merged_df)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    # Save results
    output = {
        'coherence_stats': coherence_df[['c_system', 'c_trust', 'c_metabolic', 'c_salience']].describe().to_dict(),
        'novelty_stats': novelty_df['novelty'].describe().to_dict() if len(novelty_df) > 0 else {},
        'n_coherence': len(coherence_df),
        'n_novelty': len(novelty_df),
        'n_aligned': len(merged_df) if merged_df is not None else 0
    }

    output_path = Path("/home/dp/gnosis-research/production_validation_results.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    main()
