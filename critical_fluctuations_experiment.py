#!/usr/bin/env python3
"""
Critical Fluctuations Experiment - Thor Session #44

Tests Session #43 phase transition predictions:
1. Response time variance peaks at C ≈ 0.5 (critical slowing)
2. Wake probability ~ 1/|C - 0.5| (divergence at critical point)
3. Sharp crisis threshold at ATP ≈ 13

Experimental design:
- Systematic sweep: 7 coherence levels (C = 0.1 to 0.9)
- 8 queries per level (N = 56 total)
- Measure: wake %, response time variance, ATP dynamics
- Analysis: Test for critical phenomena signatures

Predictions (from Session #43):
✓ Variance maximum at C ≈ 0.5
✓ Wake peaks sharply at C ≈ 0.5
✓ Variance ratio (C=0.5) / (C≠0.5) > 1.5
✓ Wake ~ 1/|C - 0.5| fit quality R² > 0.7
"""

import sys
import os
import json
import time
import datetime
import requests
from pathlib import Path

# SAGE configuration
SAGE_URL = "http://localhost:8750"  # SAGE daemon port

# Experiment configuration
INSTANCE = "thor-qwen2.5-14b"  # Use currently running instance
N_PER_LEVEL = 8  # Queries per coherence level
COHERENCE_LEVELS = [0.15, 0.30, 0.45, 0.50, 0.55, 0.70, 0.85]  # Focus on C ≈ 0.5

# Query templates by coherence level
QUERY_TEMPLATES = {
    0.15: [  # Trivial (well below criticality)
        "What is 2+2?",
        "Name a color.",
        "Is water wet?",
        "Count to 3.",
        "What day comes after Monday?",
        "Is the sky blue?",
        "Name an animal.",
        "What is 1+1?",
    ],
    0.30: [  # Simple (approaching criticality)
        "What are the primary colors?",
        "Name three countries in Europe.",
        "What is the capital of France?",
        "List three fruits.",
        "What season comes after summer?",
        "Name the days of the week.",
        "What is 15 + 7?",
        "How many continents are there?",
    ],
    0.45: [  # Below critical point
        "Explain the water cycle in one sentence.",
        "What causes seasons on Earth?",
        "Compare renewable and non-renewable energy.",
        "Why do objects fall?",
        "What is photosynthesis?",
        "How does a battery work?",
        "Why is the ocean salty?",
        "What makes a rainbow?",
    ],
    0.50: [  # AT CRITICAL POINT (C = 0.5) - Maximum sensitivity
        "How does consciousness emerge from neural activity?",
        "What is the relationship between entropy and time?",
        "Can free will exist in a deterministic universe?",
        "Why does the observer effect occur in quantum mechanics?",
        "What is the nature of mathematical truth?",
        "How does meaning arise from symbol manipulation?",
        "What distinguishes correlation from causation?",
        "Can intelligence exist without embodiment?",
    ],
    0.55: [  # Above critical point
        "Explain Gödel's incompleteness theorems and their implications.",
        "Compare different interpretations of quantum mechanics.",
        "How do phase transitions work in statistical physics?",
        "What is the halting problem and why is it undecidable?",
        "Analyze the hard problem of consciousness.",
        "Explain Bell's theorem and its experimental tests.",
        "What is the measurement problem in quantum theory?",
        "How does chaos theory relate to determinism?",
    ],
    0.70: [  # Supercritical (beyond comfortable)
        "Derive the path integral formulation of quantum field theory.",
        "Prove the Poincaré conjecture resolution approach.",
        "Explain the AdS/CFT correspondence and holography.",
        "Analyze topos theory applications to quantum logic.",
        "Compare string theory landscape solutions.",
        "Derive black hole thermodynamics from first principles.",
        "Explain the Yang-Mills mass gap problem.",
        "Analyze the Riemann hypothesis analytic continuation.",
    ],
    0.85: [  # Extreme (should trigger crisis or low wake)
        "Solve the P vs NP problem with formal proof.",
        "Derive a complete unified field theory.",
        "Prove or disprove the Birch and Swinnerton-Dyer conjecture.",
        "Construct a quantum gravity theory from scratch.",
        "Resolve all Millennium Prize Problems simultaneously.",
        "Derive consciousness from quantum field theory.",
        "Explain the origin of the universe before the Big Bang.",
        "Prove the consistency of ZFC set theory within ZFC.",
    ],
}


def get_sage_status():
    """Get SAGE's current metabolic state."""
    try:
        r = requests.get(f"{SAGE_URL}/status", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ERROR getting status: {e}")
        return None


def query_sage(query_text):
    """Send query to SAGE and measure response dynamics."""
    # Record pre-query state
    pre_status = get_sage_status()
    if not pre_status:
        return None

    pre_state = pre_status.get('mode', 'unknown')
    pre_atp = pre_status.get('atp', 0)

    # Send query and measure time
    start_time = time.time()

    try:
        r = requests.post(
            f"{SAGE_URL}/chat",
            json={"message": query_text},
            timeout=60
        )
        r.raise_for_status()
        response_data = r.json()
        response = response_data.get('response', '')

    except Exception as e:
        print(f"  ERROR querying SAGE: {e}")
        return None

    end_time = time.time()
    response_time = end_time - start_time

    # Record post-query state
    post_status = get_sage_status()
    if not post_status:
        return None

    post_state = post_status.get('mode', 'unknown')
    post_atp = post_status.get('atp', 0)

    # Extract metrics
    result = {
        'query': query_text,
        'pre_state': pre_state,
        'pre_atp': pre_atp,
        'post_state': post_state,
        'post_atp': post_atp,
        'response_time': response_time,
        'response_length': len(response),
        'response_chars': len(response),
        'timestamp': datetime.datetime.now().isoformat(),
    }

    return result


def run_experiment():
    """Execute critical fluctuations experiment."""
    print("=" * 80)
    print("CRITICAL FLUCTUATIONS EXPERIMENT - Thor Session #44")
    print("=" * 80)
    print(f"\nInstance: {INSTANCE}")
    print(f"Queries per level: {N_PER_LEVEL}")
    print(f"Total queries: {len(COHERENCE_LEVELS) * N_PER_LEVEL}")
    print(f"\nTesting Session #43 predictions:")
    print("  1. Variance peaks at C ≈ 0.5 (critical fluctuations)")
    print("  2. Wake ~ 1/|C - 0.5| (divergence at critical point)")
    print("  3. Sharp crisis threshold")
    print("\n" + "=" * 80 + "\n")

    # Initialize results
    results = {
        'experiment': 'critical_fluctuations',
        'session': 'Thor #44',
        'instance': INSTANCE,
        'timestamp': datetime.datetime.now().isoformat(),
        'coherence_levels': COHERENCE_LEVELS,
        'n_per_level': N_PER_LEVEL,
        'predictions': {
            'variance_peak_at_critical': True,
            'wake_divergence': True,
            'sharp_crisis_threshold': True,
        },
        'queries': [],
    }

    # Run queries at each coherence level
    for c_level in COHERENCE_LEVELS:
        print(f"\n{'='*60}")
        print(f"COHERENCE LEVEL: C = {c_level:.2f}")
        print(f"{'='*60}")

        queries = QUERY_TEMPLATES[c_level]

        for i, query in enumerate(queries[:N_PER_LEVEL]):
            print(f"\n[{i+1}/{N_PER_LEVEL}] Query: {query[:60]}...")

            try:
                result = query_sage(query)
                if not result:
                    continue
                result['coherence_level'] = c_level
                result['query_index'] = i

                # Display immediate feedback
                print(f"  State: {result['pre_state']} → {result['post_state']}")
                print(f"  ATP: {result['pre_atp']:.1f} → {result['post_atp']:.1f}")
                print(f"  Time: {result['response_time']:.2f}s")
                print(f"  Length: {result['response_chars']} chars")

                results['queries'].append(result)

                # Brief pause between queries
                time.sleep(2)

            except Exception as e:
                print(f"  ERROR: {e}")
                error_result = {
                    'query': query,
                    'coherence_level': c_level,
                    'query_index': i,
                    'error': str(e),
                    'timestamp': datetime.datetime.now().isoformat(),
                }
                results['queries'].append(error_result)

    # Save results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/home/dp/gnosis-research/critical_fluctuations_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"EXPERIMENT COMPLETE")
    print(f"Results saved to: {output_file}")
    print(f"Total queries: {len(results['queries'])}")
    print(f"{'='*80}\n")

    return results, output_file


def analyze_results(results_file):
    """Analyze experiment results for critical phenomena."""
    print("\n" + "="*80)
    print("CRITICAL PHENOMENA ANALYSIS")
    print("="*80 + "\n")

    # Load results
    with open(results_file, 'r') as f:
        data = json.load(f)

    queries = [q for q in data['queries'] if 'error' not in q]

    if not queries:
        print("ERROR: No valid queries to analyze")
        return

    # Organize by coherence level
    by_level = {}
    for q in queries:
        c = q['coherence_level']
        if c not in by_level:
            by_level[c] = []
        by_level[c].append(q)

    print("RESULTS BY COHERENCE LEVEL:")
    print("-" * 80)

    import numpy as np

    # Collect statistics
    stats = []
    for c in sorted(by_level.keys()):
        level_queries = by_level[c]

        # Wake percentage
        wake_count = sum(1 for q in level_queries if q['pre_state'] == 'wake')
        wake_pct = 100 * wake_count / len(level_queries)

        # Crisis percentage
        crisis_count = sum(1 for q in level_queries
                          if q['pre_state'] == 'crisis' or q['post_state'] == 'crisis')
        crisis_pct = 100 * crisis_count / len(level_queries)

        # Response time statistics
        times = [q['response_time'] for q in level_queries]
        mean_time = np.mean(times)
        std_time = np.std(times, ddof=1) if len(times) > 1 else 0
        cv_time = std_time / mean_time if mean_time > 0 else 0

        # ATP statistics
        atps = [q['pre_atp'] for q in level_queries]
        mean_atp = np.mean(atps)
        std_atp = np.std(atps, ddof=1) if len(atps) > 1 else 0

        stats.append({
            'coherence': c,
            'n': len(level_queries),
            'wake_pct': wake_pct,
            'crisis_pct': crisis_pct,
            'mean_time': mean_time,
            'std_time': std_time,
            'cv_time': cv_time,
            'mean_atp': mean_atp,
            'std_atp': std_atp,
        })

        print(f"\nC = {c:.2f} (N={len(level_queries)})")
        print(f"  Wake: {wake_pct:.1f}%  Crisis: {crisis_pct:.1f}%")
        print(f"  Time: {mean_time:.2f} ± {std_time:.2f}s (CV={cv_time:.3f})")
        print(f"  ATP: {mean_atp:.1f} ± {std_atp:.1f}")

    # Test Prediction 1: Variance peak at C ≈ 0.5
    print("\n" + "="*80)
    print("PREDICTION 1: Variance peaks at C ≈ 0.5 (critical fluctuations)")
    print("="*80)

    cvs = [s['cv_time'] for s in stats]
    coherences = [s['coherence'] for s in stats]

    max_cv_idx = np.argmax(cvs)
    max_cv_c = coherences[max_cv_idx]
    max_cv = cvs[max_cv_idx]

    print(f"\nMaximum CV: {max_cv:.3f} at C = {max_cv_c:.2f}")
    print(f"Expected peak: C ≈ 0.50")

    # Is peak near C = 0.5?
    distance_from_critical = abs(max_cv_c - 0.50)
    print(f"Distance from C = 0.5: {distance_from_critical:.2f}")

    if distance_from_critical <= 0.10:
        print("✓ PREDICTION 1 SUPPORTED: Peak within 0.10 of C = 0.5")
    else:
        print("✗ PREDICTION 1 NOT SUPPORTED: Peak not near C = 0.5")

    # Variance ratio
    critical_cv = next((s['cv_time'] for s in stats if s['coherence'] == 0.50), None)
    non_critical_cvs = [s['cv_time'] for s in stats if s['coherence'] != 0.50]
    mean_non_critical_cv = np.mean(non_critical_cvs) if non_critical_cvs else 0

    if critical_cv and mean_non_critical_cv > 0:
        variance_ratio = critical_cv / mean_non_critical_cv
        print(f"\nVariance ratio (C=0.5) / (C≠0.5): {variance_ratio:.2f}")
        if variance_ratio > 1.5:
            print("✓ PREDICTION 1 SUPPORTED: Variance ratio > 1.5x")
        else:
            print("✗ Variance ratio < 1.5x (weak/no critical slowing)")

    # Test Prediction 2: Wake ~ 1/|C - 0.5|
    print("\n" + "="*80)
    print("PREDICTION 2: Wake ~ 1/|C - 0.5| (divergence at critical point)")
    print("="*80)

    wake_pcts = [s['wake_pct'] for s in stats]
    max_wake_idx = np.argmax(wake_pcts)
    max_wake_c = coherences[max_wake_idx]
    max_wake = wake_pcts[max_wake_idx]

    print(f"\nMaximum wake: {max_wake:.1f}% at C = {max_wake_c:.2f}")
    print(f"Expected peak: C ≈ 0.50")

    distance_wake = abs(max_wake_c - 0.50)
    print(f"Distance from C = 0.5: {distance_wake:.2f}")

    if distance_wake <= 0.10:
        print("✓ PREDICTION 2 SUPPORTED: Wake peaks within 0.10 of C = 0.5")
    else:
        print("✗ PREDICTION 2 NOT SUPPORTED: Wake peak not near C = 0.5")

    # Fit wake ~ 1/|C - 0.5|
    try:
        from scipy.optimize import curve_fit

        def divergence_model(c, a, b):
            """Wake = a / |C - 0.5| + b"""
            return a / (np.abs(c - 0.5) + 0.01) + b  # +0.01 to avoid division by zero

        coherence_array = np.array(coherences)
        wake_array = np.array(wake_pcts)

        popt, pcov = curve_fit(divergence_model, coherence_array, wake_array,
                              p0=[10, 10], maxfev=5000)

        predicted_wake = divergence_model(coherence_array, *popt)
        residuals = wake_array - predicted_wake
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((wake_array - np.mean(wake_array))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        print(f"\nDivergence model fit:")
        print(f"  Wake = {popt[0]:.2f} / |C - 0.5| + {popt[1]:.2f}")
        print(f"  R² = {r_squared:.3f}")

        if r_squared > 0.7:
            print("✓ PREDICTION 2 SUPPORTED: Good fit (R² > 0.7)")
        else:
            print("✗ Moderate/weak fit (R² < 0.7)")

    except Exception as e:
        print(f"\nCannot fit divergence model: {e}")

    # Test Prediction 3: Crisis threshold
    print("\n" + "="*80)
    print("PREDICTION 3: Sharp crisis threshold at ATP ≈ 13")
    print("="*80)

    crisis_queries = [q for q in queries
                     if q['pre_state'] == 'crisis' or q['post_state'] == 'crisis']

    if crisis_queries:
        crisis_atps = [q['pre_atp'] for q in crisis_queries]
        print(f"\nCrisis queries: N = {len(crisis_queries)}")
        print(f"Crisis ATP range: {min(crisis_atps):.1f} - {max(crisis_atps):.1f}")
        print(f"Mean crisis ATP: {np.mean(crisis_atps):.1f}")

        # Check if crisis ATP < 15
        if max(crisis_atps) < 15:
            print("✓ PREDICTION 3 SUPPORTED: All crisis queries at ATP < 15")
        else:
            print("✗ Some crisis queries at ATP > 15")
    else:
        print("\nNo crisis states observed in experiment")
        print("(This may indicate ATP remained above threshold)")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80 + "\n")

    # Save analysis results
    analysis_output = {
        'experiment': 'critical_fluctuations_analysis',
        'statistics': stats,
        'predictions': {
            'variance_peak': {
                'supported': distance_from_critical <= 0.10,
                'max_cv': max_cv,
                'at_coherence': max_cv_c,
                'distance_from_critical': distance_from_critical,
            },
            'wake_divergence': {
                'supported': distance_wake <= 0.10,
                'max_wake': max_wake,
                'at_coherence': max_wake_c,
                'distance_from_critical': distance_wake,
            },
            'crisis_threshold': {
                'n_crisis': len(crisis_queries),
                'observed': len(crisis_queries) > 0,
            },
        },
        'timestamp': datetime.datetime.now().isoformat(),
    }

    analysis_file = results_file.replace('.json', '_analysis.json')
    with open(analysis_file, 'w') as f:
        json.dump(analysis_output, f, indent=2)

    print(f"Analysis saved to: {analysis_file}\n")

    return analysis_output


if __name__ == '__main__':
    print("\n" + "="*80)
    print("THOR SESSION #44: Critical Fluctuations Validation Experiment")
    print("="*80)
    print("\nTesting Session #43 phase transition predictions")
    print("Expected outcomes:")
    print("  • Response variance peaks at C ≈ 0.5")
    print("  • Wake probability peaks at C ≈ 0.5")
    print("  • Sharp crisis threshold at ATP < 15")
    print("\nStarting experiment...\n")

    # Run experiment
    results, results_file = run_experiment()

    # Analyze results
    print("\n" + "="*80)
    print("Starting analysis...")
    print("="*80 + "\n")

    analysis = analyze_results(results_file)

    print("\n" + "="*80)
    print("SESSION #44 COMPLETE")
    print("="*80)
    print(f"\nResults: {results_file}")
    print(f"Analysis: {results_file.replace('.json', '_analysis.json')}")
    print("\nReview findings to assess phase transition framework validity.\n")
