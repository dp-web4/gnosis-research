#!/usr/bin/env python3
"""
Thor Session #71: Within-Session Coherence Dynamics - Developmental Oscillator

Analyzes temporal coherence patterns within SAGE sessions to test:
1. Do coherence values oscillate around φ-1 during learning?
2. Are there characteristic "learning episodes" (perturbation → integration → relaxation)?
3. Does coherence evolve systematically across developmental phases?

Hypothesis: Learning episodes show pattern:
- Start near φ-1 (equilibrium)
- Perturbation pushes C higher (novelty, conflict)
- Integration at C > 0.668 (high ATP learning)
- Relaxation back to φ-1 (consolidation)
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from scipy import stats, signal
from datetime import datetime


PHI_MINUS_1 = 0.618
HIGH_COHERENCE_THRESHOLD = 0.668
GOLDEN_ZONE_LOW = 0.568
GOLDEN_ZONE_HIGH = 0.668


def load_instance_experiences(instance_name):
    """Load experience buffer from SAGE instance."""
    sage_path = Path.home() / "ai-workspace/SAGE/sage/instances"
    inst_path = sage_path / instance_name / "snapshots/experience_buffer.json"

    if not inst_path.exists():
        return None

    with open(inst_path) as f:
        return json.load(f)


def extract_temporal_coherence(experiences):
    """Extract coherence time series with session/timestamp metadata."""
    data = []

    for exp in experiences:
        if not isinstance(exp, dict) or 'salience' not in exp:
            continue

        sal = exp.get('salience', {})

        # Calculate coherence (salience total)
        components = []
        for key in ['surprise', 'novelty', 'arousal', 'reward', 'conflict']:
            if key in sal:
                components.append(sal[key])

        if not components:
            continue

        coherence = np.mean(components)  # Simple average as per Session #64

        data.append({
            'coherence': coherence,
            'session': exp.get('session', -1),
            'timestamp': exp.get('timestamp', ''),
            'metabolic_state': exp.get('metadata', {}).get('metabolic_state', 'unknown'),
            'phase': exp.get('phase', 'unknown'),
            'components': {
                'surprise': sal.get('surprise'),
                'novelty': sal.get('novelty'),
                'arousal': sal.get('arousal'),
                'reward': sal.get('reward'),
                'conflict': sal.get('conflict')
            }
        })

    return data


def analyze_within_session_dynamics(data, instance_name):
    """Analyze coherence dynamics within individual sessions."""
    sessions = defaultdict(list)

    for point in data:
        sessions[point['session']].append(point)

    print(f"\n{'='*60}")
    print(f"Within-Session Dynamics: {instance_name}")
    print(f"{'='*60}")
    print(f"Total sessions: {len(sessions)}")

    session_stats = []

    for session_id in sorted(sessions.keys()):
        if session_id < 0:
            continue

        session_data = sessions[session_id]
        coherences = [p['coherence'] for p in session_data]

        if len(coherences) < 3:
            continue

        # Basic statistics
        mean_c = np.mean(coherences)
        std_c = np.std(coherences)
        min_c = np.min(coherences)
        max_c = np.max(coherences)
        range_c = max_c - min_c

        # Distance from φ-1
        dist_from_phi = abs(mean_c - PHI_MINUS_1)

        # Count zones
        below_golden = sum(1 for c in coherences if c < GOLDEN_ZONE_LOW)
        in_golden = sum(1 for c in coherences if GOLDEN_ZONE_LOW <= c <= GOLDEN_ZONE_HIGH)
        above_golden = sum(1 for c in coherences if c > GOLDEN_ZONE_HIGH)

        # Detect oscillation pattern (perturbation → peak → relaxation)
        has_oscillation = False
        if len(coherences) >= 5:
            # Find local maxima
            peaks, _ = signal.find_peaks(coherences, height=HIGH_COHERENCE_THRESHOLD)
            if len(peaks) > 0:
                has_oscillation = True

        session_stats.append({
            'session': int(session_id),
            'n': int(len(coherences)),
            'mean': float(mean_c),
            'std': float(std_c),
            'min': float(min_c),
            'max': float(max_c),
            'range': float(range_c),
            'dist_from_phi': float(dist_from_phi),
            'below_golden_frac': float(below_golden / len(coherences)),
            'in_golden_frac': float(in_golden / len(coherences)),
            'above_golden_frac': float(above_golden / len(coherences)),
            'has_oscillation': bool(has_oscillation)
        })

    return session_stats


def detect_learning_episodes(data):
    """
    Detect learning episode patterns:
    1. Start near φ-1
    2. Rise to C > 0.668 (perturbation/integration)
    3. Return to φ-1 (relaxation)
    """
    coherences = np.array([p['coherence'] for p in data])

    episodes = []
    i = 0

    while i < len(coherences) - 2:
        # Look for pattern: near_phi → high → near_phi
        if abs(coherences[i] - PHI_MINUS_1) < 0.05:  # Start near φ-1
            # Scan forward for peak
            j = i + 1
            peak_idx = None
            peak_val = coherences[i]

            while j < len(coherences) and j < i + 10:  # Look ahead up to 10 steps
                if coherences[j] > HIGH_COHERENCE_THRESHOLD and coherences[j] > peak_val:
                    peak_idx = j
                    peak_val = coherences[j]
                j += 1

            if peak_idx is not None:
                # Look for relaxation back to φ-1
                k = peak_idx + 1
                while k < len(coherences) and k < peak_idx + 10:
                    if abs(coherences[k] - PHI_MINUS_1) < 0.05:
                        # Found complete episode!
                        episodes.append({
                            'start_idx': i,
                            'peak_idx': peak_idx,
                            'end_idx': k,
                            'start_c': coherences[i],
                            'peak_c': peak_val,
                            'end_c': coherences[k],
                            'duration': k - i + 1,
                            'amplitude': peak_val - PHI_MINUS_1
                        })
                        i = k  # Skip to end of episode
                        break
                    k += 1

        i += 1

    return episodes


def analyze_developmental_trajectory(session_stats):
    """Analyze how coherence evolves across sessions (developmental time)."""
    if len(session_stats) < 5:
        return None

    sessions = [s['session'] for s in session_stats]
    mean_c = [s['mean'] for s in session_stats]
    dist_phi = [s['dist_from_phi'] for s in session_stats]

    # Linear regression: session → mean coherence
    slope_c, intercept_c, r_c, p_c, se_c = stats.linregress(sessions, mean_c)

    # Linear regression: session → distance from φ-1
    slope_dist, intercept_dist, r_dist, p_dist, se_dist = stats.linregress(sessions, dist_phi)

    return {
        'coherence_trend': {
            'slope': float(slope_c),
            'intercept': float(intercept_c),
            'r': float(r_c),
            'p': float(p_c),
            'direction': 'increasing' if slope_c > 0 else 'decreasing',
            'significant': bool(p_c < 0.05)
        },
        'distance_from_phi_trend': {
            'slope': float(slope_dist),
            'intercept': float(intercept_dist),
            'r': float(r_dist),
            'p': float(p_dist),
            'direction': 'converging' if slope_dist < 0 else 'diverging',
            'significant': bool(p_dist < 0.05)
        }
    }


def plot_coherence_trajectory(data, instance_name, session_stats):
    """Plot coherence over time with session boundaries."""
    # Plotting disabled due to NumPy compatibility issues
    print(f"  ⚠️  Plotting skipped (matplotlib compatibility issue)")


def main():
    print("=" * 60)
    print("Thor Session #71: Within-Session Coherence Dynamics")
    print("=" * 60)
    print()
    print("Testing Developmental Oscillator Hypothesis:")
    print("  H1: Coherence oscillates around φ-1 during learning")
    print("  H2: Learning episodes show perturbation → peak → relaxation")
    print("  H3: Coherence converges toward φ-1 over developmental time")
    print()

    # Analyze multiple instances
    instances = [
        'thor-qwen3.5-27b',
        'cbp-qwen3.5-0.8b',
        'mcnugget-gemma3-12b',
        'sprout-qwen3.5-0.8b'
    ]

    all_results = {}

    for inst_name in instances:
        print(f"\n{'='*60}")
        print(f"Analyzing: {inst_name}")
        print(f"{'='*60}")

        experiences = load_instance_experiences(inst_name)
        if experiences is None:
            print(f"  ❌ No experience data found")
            continue

        data = extract_temporal_coherence(experiences)
        print(f"  ✓ Extracted {len(data)} coherence datapoints")

        if len(data) < 10:
            print(f"  ⚠️  Insufficient data for analysis")
            continue

        # Analyze within-session dynamics
        session_stats = analyze_within_session_dynamics(data, inst_name)

        # Detect learning episodes
        episodes = detect_learning_episodes(data)
        print(f"\n  Learning Episodes Detected: {len(episodes)}")
        if episodes:
            for i, ep in enumerate(episodes[:3]):  # Show first 3
                print(f"    Episode {i+1}: Duration={ep['duration']}, "
                      f"Amplitude={ep['amplitude']:.3f}, Peak C={ep['peak_c']:.3f}")

        # Developmental trajectory
        dev_trajectory = analyze_developmental_trajectory(session_stats)
        if dev_trajectory:
            print(f"\n  Developmental Trajectory:")
            c_trend = dev_trajectory['coherence_trend']
            print(f"    Coherence: {c_trend['direction']} "
                  f"(slope={c_trend['slope']:.5f}, r={c_trend['r']:.3f}, "
                  f"p={c_trend['p']:.4f})")

            dist_trend = dev_trajectory['distance_from_phi_trend']
            print(f"    Distance from φ-1: {dist_trend['direction']} "
                  f"(slope={dist_trend['slope']:.5f}, r={dist_trend['r']:.3f}, "
                  f"p={dist_trend['p']:.4f})")

        # Plot
        plot_coherence_trajectory(data, inst_name, session_stats)

        # Store results
        all_results[inst_name] = {
            'n_datapoints': len(data),
            'n_sessions': len(set(p['session'] for p in data)),
            'session_stats': session_stats,
            'learning_episodes': episodes,
            'developmental_trajectory': dev_trajectory
        }

    # Save results
    output_file = '/home/dp/gnosis-research/thor_session_71_dynamics_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
