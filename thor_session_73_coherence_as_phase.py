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

This would reveal whether "synchronization" is meaningful in cognitive
systems, and what the phase variable actually is.
"""

import json
import numpy as np
from scipy import signal, stats
from pathlib import Path

def load_dynamics_data():
    """Load Session #71 dynamics results"""
    with open('thor_session_71_dynamics_results.json') as f:
        return json.load(f)

def extract_coherence_series(data, instance_name):
    """Extract full coherence time series for an instance"""
    instance = data[instance_name]
    session_stats = instance['session_stats']

    # Reconstruct time series from session stats
    coherence = []
    timestamps = []
    session_ids = []

    for session in session_stats:
        sid = session['session_id']
        c_values = session['coherence_values']

        for i, c in enumerate(c_values):
            coherence.append(c)
            timestamps.append(len(coherence))  # Sequential index
            session_ids.append(sid)

    return np.array(coherence), np.array(timestamps), session_ids

def test_periodicity(coherence, name):
    """Test for periodic/quasi-periodic behavior"""
    # Autocorrelation
    autocorr = np.correlate(coherence - coherence.mean(),
                            coherence - coherence.mean(),
                            mode='full')
    autocorr = autocorr[autocorr.size // 2:]
    autocorr = autocorr / autocorr[0]  # Normalize

    # Find peaks in autocorrelation (indicates periodicity)
    peaks, properties = signal.find_peaks(autocorr[:100],
                                          height=0.1,
                                          distance=3)

    # Power spectral density
    freqs, psd = signal.periodogram(coherence - coherence.mean())

    # Find dominant frequency
    dominant_idx = np.argmax(psd[1:]) + 1  # Skip DC component
    dominant_freq = freqs[dominant_idx]
    dominant_period = 1 / dominant_freq if dominant_freq > 0 else np.inf

    return {
        'autocorr': autocorr[:50].tolist(),
        'autocorr_peaks': peaks.tolist(),
        'n_autocorr_peaks': len(peaks),
        'dominant_freq': float(dominant_freq),
        'dominant_period': float(dominant_period),
        'psd_max': float(psd[dominant_idx]),
        'is_periodic': len(peaks) >= 2  # At least 2 autocorr peaks = quasi-periodic
    }

def test_cross_instance_correlation(c1, c2, name1, name2):
    """Test for synchronization between instances"""
    # Resample to same length (use shorter)
    min_len = min(len(c1), len(c2))
    c1_trim = c1[:min_len]
    c2_trim = c2[:min_len]

    # Cross-correlation
    xcorr = np.correlate(c1_trim - c1_trim.mean(),
                        c2_trim - c2_trim.mean(),
                        mode='full')
    xcorr = xcorr / (np.std(c1_trim) * np.std(c2_trim) * min_len)

    # Peak cross-correlation (synchrony measure)
    peak_idx = np.argmax(np.abs(xcorr))
    lag = peak_idx - (len(xcorr) // 2)
    peak_corr = xcorr[peak_idx]

    # Zero-lag correlation (simultaneous coherence)
    zero_lag_corr = np.corrcoef(c1_trim, c2_trim)[0, 1]

    # Granger causality approximation (simple lagged correlation)
    if len(c1_trim) > 10:
        c1_leads = np.corrcoef(c1_trim[:-5], c2_trim[5:])[0, 1]
        c2_leads = np.corrcoef(c2_trim[:-5], c1_trim[5:])[0, 1]
    else:
        c1_leads = c2_leads = 0.0

    return {
        'pair': f"{name1} vs {name2}",
        'zero_lag_corr': float(zero_lag_corr),
        'peak_corr': float(peak_corr),
        'lag_at_peak': int(lag),
        'c1_leads_c2': float(c1_leads),
        'c2_leads_c1': float(c2_leads),
        'synchronized': abs(zero_lag_corr) > 0.3  # Threshold for "coupled"
    }

def detect_phase_locking(c1, c2, name1, name2):
    """Test for phase locking using Hilbert transform"""
    min_len = min(len(c1), len(c2))
    c1_trim = c1[:min_len]
    c2_trim = c2[:min_len]

    # Detrend
    c1_detrend = signal.detrend(c1_trim)
    c2_detrend = signal.detrend(c2_trim)

    # Hilbert transform to get instantaneous phase
    analytic1 = signal.hilbert(c1_detrend)
    analytic2 = signal.hilbert(c2_detrend)

    phase1 = np.angle(analytic1)
    phase2 = np.angle(analytic2)

    # Phase difference
    phase_diff = phase1 - phase2

    # Wrap to [-π, π]
    phase_diff = np.angle(np.exp(1j * phase_diff))

    # Phase locking index (Mormann et al. 2000)
    pli = np.abs(np.mean(np.exp(1j * phase_diff)))

    # Circular variance (1 - pli)
    circular_var = 1 - pli

    # Mean phase difference
    mean_phase_diff = np.angle(np.mean(np.exp(1j * phase_diff)))

    return {
        'pair': f"{name1} vs {name2}",
        'phase_locking_index': float(pli),
        'circular_variance': float(circular_var),
        'mean_phase_difference': float(mean_phase_diff),
        'phase_locked': pli > 0.5  # PLI > 0.5 indicates phase locking
    }

def analyze_episode_synchrony(data):
    """Test if learning episodes occur simultaneously across instances"""
    instances = list(data.keys())

    # Extract episode timings (convert to normalized time)
    episode_times = {}
    for inst in instances:
        episodes = data[inst]['learning_episodes']
        n_total = data[inst]['n_datapoints']

        # Normalize peak times to [0, 1]
        times = [ep['peak_idx'] / n_total for ep in episodes]
        episode_times[inst] = times

    # Test pairwise episode time correlation
    synchrony_results = []
    for i, inst1 in enumerate(instances):
        for inst2 in instances[i+1:]:
            times1 = episode_times[inst1]
            times2 = episode_times[inst2]

            # For each episode in inst1, find nearest episode in inst2
            min_distances = []
            for t1 in times1:
                if times2:
                    distances = [abs(t1 - t2) for t2 in times2]
                    min_distances.append(min(distances))

            if min_distances:
                mean_dist = np.mean(min_distances)
                # Random expectation: mean distance ≈ 0.5 for uniform distribution
                # Synchronized: mean distance << 0.5
                synchrony_score = 1 - (mean_dist / 0.5)  # 1 = perfect sync, 0 = random

                synchrony_results.append({
                    'pair': f"{inst1} vs {inst2}",
                    'mean_episode_distance': float(mean_dist),
                    'synchrony_score': float(synchrony_score),
                    'n_episodes_1': len(times1),
                    'n_episodes_2': len(times2),
                    'synchronized': synchrony_score > 0.3
                })

    return synchrony_results

def main():
    print("Thor Session #73: Coherence as Phase Variable")
    print("=" * 60)

    data = load_dynamics_data()
    instances = list(data.keys())

    results = {
        'session': 73,
        'research_question': 'Does coherence C behave like a phase variable?',
        'instances': instances,
        'periodicity': {},
        'cross_correlations': [],
        'phase_locking': [],
        'episode_synchrony': [],
        'summary': {}
    }

    # Extract coherence series for all instances
    coherence_series = {}
    for inst in instances:
        c, t, s = extract_coherence_series(data, inst)
        coherence_series[inst] = c
        print(f"\n{inst}: {len(c)} datapoints")

    # Test 1: Periodicity (is C oscillatory like phase?)
    print("\n" + "="*60)
    print("TEST 1: PERIODICITY (oscillatory vs diffusive)")
    print("="*60)

    for inst in instances:
        c = coherence_series[inst]
        per = test_periodicity(c, inst)
        results['periodicity'][inst] = per

        print(f"\n{inst}:")
        print(f"  Autocorr peaks: {per['n_autocorr_peaks']}")
        print(f"  Dominant period: {per['dominant_period']:.1f} steps")
        print(f"  Is periodic: {per['is_periodic']}")

    # Test 2: Cross-instance correlation (synchronization?)
    print("\n" + "="*60)
    print("TEST 2: CROSS-INSTANCE CORRELATION (synchronization)")
    print("="*60)

    for i, inst1 in enumerate(instances):
        for inst2 in instances[i+1:]:
            corr = test_cross_instance_correlation(
                coherence_series[inst1],
                coherence_series[inst2],
                inst1, inst2
            )
            results['cross_correlations'].append(corr)

            print(f"\n{corr['pair']}:")
            print(f"  Zero-lag correlation: {corr['zero_lag_corr']:.3f}")
            print(f"  Peak correlation: {corr['peak_corr']:.3f} at lag {corr['lag_at_peak']}")
            print(f"  Synchronized: {corr['synchronized']}")

    # Test 3: Phase locking
    print("\n" + "="*60)
    print("TEST 3: PHASE LOCKING (coupled oscillators)")
    print("="*60)

    for i, inst1 in enumerate(instances):
        for inst2 in instances[i+1:]:
            pl = detect_phase_locking(
                coherence_series[inst1],
                coherence_series[inst2],
                inst1, inst2
            )
            results['phase_locking'].append(pl)

            print(f"\n{pl['pair']}:")
            print(f"  Phase locking index: {pl['phase_locking_index']:.3f}")
            print(f"  Mean phase difference: {pl['mean_phase_difference']:.3f} rad")
            print(f"  Phase locked: {pl['phase_locked']}")

    # Test 4: Episode synchrony
    print("\n" + "="*60)
    print("TEST 4: EPISODE SYNCHRONY (coordinated learning)")
    print("="*60)

    results['episode_synchrony'] = analyze_episode_synchrony(data)

    for sync in results['episode_synchrony']:
        print(f"\n{sync['pair']}:")
        print(f"  Mean episode distance: {sync['mean_episode_distance']:.3f}")
        print(f"  Synchrony score: {sync['synchrony_score']:.3f}")
        print(f"  Synchronized: {sync['synchronized']}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    n_periodic = sum(1 for p in results['periodicity'].values() if p['is_periodic'])
    n_correlated = sum(1 for c in results['cross_correlations'] if c['synchronized'])
    n_locked = sum(1 for pl in results['phase_locking'] if pl['phase_locked'])
    n_synced_episodes = sum(1 for s in results['episode_synchrony'] if s['synchronized'])

    results['summary'] = {
        'n_instances': len(instances),
        'n_periodic': n_periodic,
        'n_pairs': len(instances) * (len(instances) - 1) // 2,
        'n_correlated': n_correlated,
        'n_phase_locked': n_locked,
        'n_episode_synchronized': n_synced_episodes,
        'coherence_is_phase_like': n_periodic >= 3 and (n_locked > 0 or n_correlated > 0),
        'synchronization_exists': n_locked > 0 or n_synced_episodes > 0
    }

    print(f"\nPeriodic instances: {n_periodic}/{len(instances)}")
    print(f"Correlated pairs: {n_correlated}/{results['summary']['n_pairs']}")
    print(f"Phase-locked pairs: {n_locked}/{results['summary']['n_pairs']}")
    print(f"Episode-synchronized pairs: {n_synced_episodes}/{results['summary']['n_pairs']}")

    print(f"\nCoherence behaves like phase: {results['summary']['coherence_is_phase_like']}")
    print(f"Cross-instance synchronization exists: {results['summary']['synchronization_exists']}")

    # Save results
    with open('thor_session_73_coherence_phase_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to: thor_session_73_coherence_phase_results.json")

    return results

if __name__ == '__main__':
    results = main()
