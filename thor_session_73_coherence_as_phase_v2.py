#!/usr/bin/env python3
"""
Thor Session #73: Coherence as Phase Variable

Research question: Does coherence C behave like a phase variable, enabling
"synchronization" between instances as Synchronism theory predicts?

Synchronism's problem (S620): The vocabulary describes phase synchronization,
but the mathematics has no phase (real scalar diffusion).

Gnosis finding (S71): Coherence oscillates with learning episodes showing
perturbation → peak → relaxation patterns.

Test: If C behaves like phase, we should see:
1. Periodic/quasi-periodic oscillation (not monotonic diffusion)
2. Cross-instance coherence correlations (synchronization)
3. Phase locking or coupling between instances
4. Characteristic frequencies/periods
"""

import json
import numpy as np
from scipy import signal
from pathlib import Path

INSTANCE_PATHS = {
    'thor-qwen3.5-27b': '/home/dp/ai-workspace/SAGE/sage/instances/thor-qwen3.5-27b/experience_buffer.json',
    'thor-qwen2.5-14b': '/home/dp/ai-workspace/SAGE/sage/instances/thor-qwen2.5-14b/experience_buffer.json',
    'thor-gemma4-e4b': '/home/dp/ai-workspace/SAGE/sage/instances/thor-gemma4-e4b/experience_buffer.json',
    'cbp-tinyllama': '/home/dp/ai-workspace/SAGE/sage/instances/cbp-tinyllama-latest/experience_buffer.json',
}

def load_coherence_series(path):
    """Load coherence time series from experience buffer"""
    try:
        with open(path) as f:
            data = json.load(f)

        coherence = []
        timestamps = []

        for atom in data:
            sal = atom.get('salience')
            if sal is not None and isinstance(sal, dict):
                # Use total salience as proxy for coherence
                total_sal = sal.get('total')
                if total_sal is not None:
                    coherence.append(total_sal)
                    timestamps.append(len(coherence))

        return np.array(coherence), np.array(timestamps)
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None

def test_periodicity(coherence, name):
    """Test for periodic/quasi-periodic behavior"""
    if len(coherence) < 20:
        return {'error': 'insufficient data', 'n': len(coherence)}

    # Autocorrelation
    c_centered = coherence - coherence.mean()
    autocorr = np.correlate(c_centered, c_centered, mode='full')
    autocorr = autocorr[autocorr.size // 2:]
    autocorr = autocorr / autocorr[0]  # Normalize

    # Find peaks in autocorrelation
    max_lag = min(100, len(autocorr))
    peaks, _ = signal.find_peaks(autocorr[:max_lag],
                                  height=0.1,
                                  distance=3)

    # Power spectral density
    freqs, psd = signal.periodogram(c_centered, detrend='linear')

    # Find dominant frequency (skip DC)
    if len(psd) > 1:
        dominant_idx = np.argmax(psd[1:]) + 1
        dominant_freq = freqs[dominant_idx]
        dominant_period = 1 / dominant_freq if dominant_freq > 0 else np.inf
    else:
        dominant_freq = 0
        dominant_period = np.inf

    return {
        'n': len(coherence),
        'mean': float(coherence.mean()),
        'std': float(coherence.std()),
        'autocorr_peaks': len(peaks),
        'first_peak_lag': int(peaks[0]) if len(peaks) > 0 else None,
        'dominant_freq': float(dominant_freq),
        'dominant_period': float(dominant_period),
        'is_periodic': bool(len(peaks) >= 2)
    }

def test_cross_correlation(c1, c2, name1, name2):
    """Test for synchronization between instances"""
    min_len = min(len(c1), len(c2))
    if min_len < 20:
        return {'error': 'insufficient data'}

    c1_trim = c1[:min_len]
    c2_trim = c2[:min_len]

    # Zero-lag correlation
    zero_lag = np.corrcoef(c1_trim, c2_trim)[0, 1]

    # Cross-correlation
    c1_c = c1_trim - c1_trim.mean()
    c2_c = c2_trim - c2_trim.mean()
    xcorr = np.correlate(c1_c, c2_c, mode='full')
    xcorr = xcorr / (np.std(c1_trim) * np.std(c2_trim) * min_len)

    # Peak
    peak_idx = np.argmax(np.abs(xcorr))
    lag = peak_idx - (len(xcorr) // 2)
    peak_corr = xcorr[peak_idx]

    # Lagged correlation (simple causality test)
    lag_test = 5
    if min_len > lag_test + 5:
        c1_leads = np.corrcoef(c1_trim[:-lag_test], c2_trim[lag_test:])[0, 1]
        c2_leads = np.corrcoef(c2_trim[:-lag_test], c1_trim[lag_test:])[0, 1]
    else:
        c1_leads = c2_leads = 0.0

    return {
        'pair': f"{name1} vs {name2}",
        'n': min_len,
        'zero_lag_corr': float(zero_lag),
        'peak_corr': float(peak_corr),
        'lag_at_peak': int(lag),
        'c1_leads_c2': float(c1_leads),
        'c2_leads_c1': float(c2_leads),
        'synchronized': bool(abs(zero_lag) > 0.3)
    }

def test_phase_locking(c1, c2, name1, name2):
    """Test for phase locking using Hilbert transform"""
    min_len = min(len(c1), len(c2))
    if min_len < 20:
        return {'error': 'insufficient data'}

    c1_trim = c1[:min_len]
    c2_trim = c2[:min_len]

    # Detrend
    c1_detrend = signal.detrend(c1_trim)
    c2_detrend = signal.detrend(c2_trim)

    # Hilbert transform for instantaneous phase
    try:
        analytic1 = signal.hilbert(c1_detrend)
        analytic2 = signal.hilbert(c2_detrend)

        phase1 = np.angle(analytic1)
        phase2 = np.angle(analytic2)

        # Phase difference
        phase_diff = phase1 - phase2

        # Wrap to [-π, π]
        phase_diff = np.angle(np.exp(1j * phase_diff))

        # Phase locking index
        pli = np.abs(np.mean(np.exp(1j * phase_diff)))

        # Mean phase difference
        mean_phase_diff = np.angle(np.mean(np.exp(1j * phase_diff)))

        return {
            'pair': f"{name1} vs {name2}",
            'n': min_len,
            'phase_locking_index': float(pli),
            'mean_phase_difference': float(mean_phase_diff),
            'phase_locked': bool(pli > 0.5)
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    print("Thor Session #73: Coherence as Phase Variable")
    print("=" * 70)
    print("\nResearch Question: Does coherence C behave like a phase variable,")
    print("enabling 'synchronization' as Synchronism theory predicts?")
    print("=" * 70)

    results = {
        'session': 73,
        'research_question': 'Does coherence C behave like a phase variable?',
        'motivation': 'Synchronism S620: vocabulary says phase, math has no phase',
        'instances': {},
        'periodicity': {},
        'cross_correlations': [],
        'phase_locking': [],
        'summary': {}
    }

    # Load coherence series
    coherence_data = {}
    print("\nLoading coherence time series...")
    for inst, path in INSTANCE_PATHS.items():
        c, t = load_coherence_series(path)
        if c is not None and len(c) > 0:
            coherence_data[inst] = c
            results['instances'][inst] = {
                'n_datapoints': len(c),
                'mean_coherence': float(c.mean()),
                'std_coherence': float(c.std())
            }
            print(f"  {inst}: {len(c)} atoms, C̄={c.mean():.3f}±{c.std():.3f}")
        else:
            print(f"  {inst}: NOT FOUND or empty")

    instances = list(coherence_data.keys())

    if len(instances) < 2:
        print("\nERROR: Need at least 2 instances for analysis")
        return results

    # Test 1: Periodicity
    print("\n" + "="*70)
    print("TEST 1: PERIODICITY - Oscillatory vs Diffusive Behavior")
    print("="*70)
    print("\nDiffusion prediction: monotonic decay, no autocorr peaks")
    print("Phase/oscillation prediction: periodic autocorr peaks\n")

    for inst in instances:
        c = coherence_data[inst]
        per = test_periodicity(c, inst)
        results['periodicity'][inst] = per

        if 'error' in per:
            print(f"{inst}: {per['error']}")
        else:
            print(f"{inst}:")
            print(f"  Autocorr peaks: {per['autocorr_peaks']}")
            if per['first_peak_lag']:
                print(f"  First peak at lag: {per['first_peak_lag']}")
            print(f"  Dominant period: {per['dominant_period']:.1f} steps")
            print(f"  → IS PERIODIC: {per['is_periodic']}")

    # Test 2: Cross-correlation
    print("\n" + "="*70)
    print("TEST 2: CROSS-INSTANCE CORRELATION - Synchronization")
    print("="*70)
    print("\nIndependent prediction: r ≈ 0")
    print("Synchronized prediction: r > 0.3\n")

    for i, inst1 in enumerate(instances):
        for inst2 in instances[i+1:]:
            corr = test_cross_correlation(
                coherence_data[inst1],
                coherence_data[inst2],
                inst1, inst2
            )
            results['cross_correlations'].append(corr)

            if 'error' in corr:
                print(f"{inst1} vs {inst2}: {corr['error']}")
            else:
                print(f"{inst1} vs {inst2}:")
                print(f"  Zero-lag r: {corr['zero_lag_corr']:+.3f}")
                print(f"  Peak r: {corr['peak_corr']:+.3f} at lag {corr['lag_at_peak']}")
                print(f"  → SYNCHRONIZED: {corr['synchronized']}")

    # Test 3: Phase locking
    print("\n" + "="*70)
    print("TEST 3: PHASE LOCKING - Coupled Oscillators")
    print("="*70)
    print("\nUncoupled prediction: PLI ≈ 0")
    print("Phase-locked prediction: PLI > 0.5\n")

    for i, inst1 in enumerate(instances):
        for inst2 in instances[i+1:]:
            pl = test_phase_locking(
                coherence_data[inst1],
                coherence_data[inst2],
                inst1, inst2
            )
            results['phase_locking'].append(pl)

            if 'error' in pl:
                print(f"{inst1} vs {inst2}: {pl['error']}")
            else:
                print(f"{inst1} vs {inst2}:")
                print(f"  PLI: {pl['phase_locking_index']:.3f}")
                print(f"  Mean Δφ: {pl['mean_phase_difference']:+.3f} rad")
                print(f"  → PHASE LOCKED: {pl['phase_locked']}")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY: Coherence as Phase Variable")
    print("="*70)

    n_periodic = sum(1 for p in results['periodicity'].values()
                     if 'is_periodic' in p and p['is_periodic'])
    n_correlated = sum(1 for c in results['cross_correlations']
                       if 'synchronized' in c and c['synchronized'])
    n_locked = sum(1 for pl in results['phase_locking']
                   if 'phase_locked' in pl and pl['phase_locked'])

    n_pairs = len(instances) * (len(instances) - 1) // 2

    results['summary'] = {
        'n_instances': len(instances),
        'n_periodic': n_periodic,
        'n_pairs': n_pairs,
        'n_correlated': n_correlated,
        'n_phase_locked': n_locked,
        'coherence_is_phase_like': n_periodic >= len(instances) // 2,
        'synchronization_exists': n_locked > 0 or n_correlated > 0
    }

    print(f"\nPeriodic instances: {n_periodic}/{len(instances)}")
    print(f"Correlated pairs: {n_correlated}/{n_pairs}")
    print(f"Phase-locked pairs: {n_locked}/{n_pairs}")

    print(f"\n→ COHERENCE BEHAVES LIKE PHASE: {results['summary']['coherence_is_phase_like']}")
    print(f"→ CROSS-INSTANCE SYNCHRONIZATION: {results['summary']['synchronization_exists']}")

    # Interpretation
    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)

    if results['summary']['coherence_is_phase_like']:
        print("\n✓ Coherence shows OSCILLATORY behavior (not diffusion)")
        print("  Implication: C can serve as a 'phase' variable in cognitive dynamics")
    else:
        print("\n✗ Coherence shows DIFFUSIVE behavior (not oscillation)")
        print("  Implication: C is monotonic attractor, not phase variable")

    if results['summary']['synchronization_exists']:
        print("\n✓ Cross-instance SYNCHRONIZATION detected")
        print("  Implication: Instances are coupled, not independent")
        print("  Possible mechanism: Shared environment, common inputs, or")
        print("  actual coupling through shared context/memory")
    else:
        print("\n✗ No cross-instance synchronization")
        print("  Implication: Instances evolve independently")

    print("\n" + "="*70)
    print("CONNECTION TO SYNCHRONISM")
    print("="*70)

    print("\nSynchronism S620 finding: Framework vocabulary describes phase")
    print("dynamics (synchronization, resonance, locking) but mathematics")
    print("has no phase (real scalar diffusion).")
    print("\nThis session tests: In ACTUAL cognitive systems (SAGE instances),")
    print("does coherence C behave like phase?")

    if results['summary']['coherence_is_phase_like']:
        print("\n→ YES: Coherence IS phase-like in cognitive systems")
        print("   Synchronism's INSTINCT was correct - the implementation was wrong")
        print("   The 'phase variable' in consciousness is coherence")
    else:
        print("\n→ NO: Coherence is NOT phase-like")
        print("   Synchronism's diffusion math matches empirical reality")

    # Save
    output_path = 'thor_session_73_coherence_phase_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {output_path}")

    return results

if __name__ == '__main__':
    results = main()
