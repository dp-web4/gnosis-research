#!/usr/bin/env python3
"""
Analyze novelty-coherence correlation from Session #53 validation logs.

Tests the hypothesis that optimal novelty ≈ 0.5 corresponds to C ≈ 0.5.
"""

import json
import numpy as np
from pathlib import Path

def load_salience_log(path):
    """Load and parse salience log."""
    data = []
    with open(path) as f:
        for line in f:
            entry = json.loads(line)
            data.append(entry)
    return data

def load_coherence_log(path):
    """Load and parse coherence log."""
    data = []
    with open(path) as f:
        for line in f:
            entry = json.loads(line)
            data.append(entry)
    return data

def extract_novelty_stats(salience_data):
    """Extract novelty statistics from salience log."""
    all_novelties = []

    for entry in salience_data:
        components = entry.get('salience_components', [])
        for comp in components:
            if 'novelty' in comp:
                all_novelties.append(comp['novelty'])

    if not all_novelties:
        return None

    return {
        'mean': np.mean(all_novelties),
        'std': np.std(all_novelties),
        'min': np.min(all_novelties),
        'max': np.max(all_novelties),
        'median': np.median(all_novelties),
        'count': len(all_novelties),
        'values': all_novelties
    }

def extract_all_salience_components(salience_data):
    """Extract all salience components for detailed analysis."""
    components = {
        'surprise': [],
        'novelty': [],
        'arousal': [],
        'reward': [],
        'conflict': []
    }

    for entry in salience_data:
        comps = entry.get('salience_components', [])
        for comp in comps:
            for key in components.keys():
                if key in comp:
                    components[key].append(comp[key])

    stats = {}
    for key, values in components.items():
        if values:
            stats[key] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values)
            }

    return stats

def correlate_novelty_coherence(salience_data, coherence_data):
    """Correlate mean novelty with C_system."""
    # Group by cycle windows
    windows = {}

    # Extract novelty by cycle
    for entry in salience_data:
        cycle = entry.get('cycle', 0)
        components = entry.get('salience_components', [])
        novelties = [c['novelty'] for c in components if 'novelty' in c]

        if novelties:
            window = (cycle // 100) * 100  # Group into 100-cycle windows
            if window not in windows:
                windows[window] = {'novelties': [], 'c_system': None}
            windows[window]['novelties'].extend(novelties)

    # Add C_system values
    for entry in coherence_data:
        cycle = entry.get('cycle', 0)
        c_system = entry.get('c_system')

        if c_system is not None:
            window = (cycle // 100) * 100
            if window in windows:
                windows[window]['c_system'] = c_system

    # Compute correlation
    valid_windows = [(np.mean(w['novelties']), w['c_system'])
                     for w in windows.values()
                     if w['novelties'] and w['c_system'] is not None]

    if len(valid_windows) < 2:
        return None

    novelties, c_systems = zip(*valid_windows)
    correlation = np.corrcoef(novelties, c_systems)[0, 1]

    return {
        'correlation': correlation,
        'n_windows': len(valid_windows),
        'windows': valid_windows
    }

def main():
    base_dir = Path('validation_logs')

    print("=" * 60)
    print("Novelty-Coherence Analysis: Session #53 Data")
    print("=" * 60)
    print()

    # Load data
    print("Loading validation logs...")
    salience_data = load_salience_log(base_dir / 'salience_log.jsonl')
    coherence_data = load_coherence_log(base_dir / 'coherence_log.jsonl')
    print(f"  Salience entries: {len(salience_data)}")
    print(f"  Coherence entries: {len(coherence_data)}")
    print()

    # Analyze novelty
    print("Analyzing novelty distribution...")
    novelty_stats = extract_novelty_stats(salience_data)

    if novelty_stats:
        print(f"  Mean novelty: {novelty_stats['mean']:.3f}")
        print(f"  Std dev:      {novelty_stats['std']:.3f}")
        print(f"  Range:        [{novelty_stats['min']:.3f}, {novelty_stats['max']:.3f}]")
        print(f"  Median:       {novelty_stats['median']:.3f}")
        print(f"  Count:        {novelty_stats['count']}")
        print()

        # Test prediction: mean ≈ 0.5 ± 0.15
        in_range = 0.35 <= novelty_stats['mean'] <= 0.65
        print(f"  Prediction Test: Mean novelty in [0.35, 0.65]")
        print(f"  Result: {'✅ PASS' if in_range else '❌ FAIL'}")
        print()
    else:
        print("  No novelty data found!")
        print()

    # Analyze all components
    print("Analyzing all salience components...")
    all_stats = extract_all_salience_components(salience_data)

    for component, stats in sorted(all_stats.items()):
        print(f"  {component.capitalize():10s} - Mean: {stats['mean']:.3f}, Std: {stats['std']:.3f}, Range: [{stats['min']:.3f}, {stats['max']:.3f}]")
    print()

    # Correlate with C_system
    print("Correlating novelty with C_system...")
    corr_result = correlate_novelty_coherence(salience_data, coherence_data)

    if corr_result:
        print(f"  Correlation coefficient: {corr_result['correlation']:.3f}")
        print(f"  Number of windows: {corr_result['n_windows']}")
        print()
        print("  Window-by-window:")
        for i, (nov, c_sys) in enumerate(corr_result['windows']):
            print(f"    Window {i}: Novelty = {nov:.3f}, C_system = {c_sys:.3f}")
        print()

        # Test prediction: r > 0.4
        strong_correlation = corr_result['correlation'] > 0.4
        print(f"  Prediction Test: Correlation > 0.4")
        if strong_correlation:
            print(f"  Result: ✅ PASS")
        else:
            print(f"  Result: ⚠️  WEAK (but expected with n={corr_result['n_windows']})")
        print()
    else:
        print("  Insufficient data for correlation")
        print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if novelty_stats:
        print(f"\n1. Novelty Distribution:")
        print(f"   Mean novelty = {novelty_stats['mean']:.3f}")
        print(f"   Target range = [0.35, 0.65] (C ≈ 0.5 ± 0.15)")
        print(f"   Status: {'✅ Within target' if 0.35 <= novelty_stats['mean'] <= 0.65 else '❌ Outside target'}")

    if corr_result and corr_result['n_windows'] >= 2:
        print(f"\n2. Novelty-Coherence Correlation:")
        print(f"   Correlation = {corr_result['correlation']:.3f}")
        print(f"   Sample size = {corr_result['n_windows']} windows")
        print(f"   Note: Small sample (n={corr_result['n_windows']}) limits statistical power")

    # Insights
    print("\n3. Key Insights:")

    if novelty_stats and all_stats:
        # Compare novelty to other components
        print(f"   - Novelty mean ({novelty_stats['mean']:.3f}) vs other components:")
        for comp, stats in sorted(all_stats.items()):
            if comp != 'novelty':
                diff = novelty_stats['mean'] - stats['mean']
                print(f"     {comp.capitalize():10s}: {stats['mean']:.3f} (diff: {diff:+.3f})")

    if corr_result and len(corr_result['windows']) == 2:
        # Show evolution
        nov_0, c_0 = corr_result['windows'][0]
        nov_1, c_1 = corr_result['windows'][1]
        print(f"\n   - Evolution over 200 cycles:")
        print(f"     Novelty: {nov_0:.3f} → {nov_1:.3f} ({nov_1-nov_0:+.3f})")
        print(f"     C_system: {c_0:.3f} → {c_1:.3f} ({c_1-c_0:+.3f})")

        # Check if both trending toward 0.5
        if abs(nov_1 - 0.5) < abs(nov_0 - 0.5) and abs(c_1 - 0.5) < abs(c_0 - 0.5):
            print(f"     Both trending toward 0.5 ✅")
        else:
            print(f"     Mixed trends")

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
