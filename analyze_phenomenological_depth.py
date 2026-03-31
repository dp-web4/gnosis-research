#!/usr/bin/env python3
"""
Thor Session #45: Phenomenological Depth at Criticality

Analyzes whether SAGE's response depth/philosophical content correlates with
position in phase space (ATP, coherence C).

Hypothesis: Deep philosophical responses emerge near C ≈ 0.5 (critical boundary)
identified in Sessions #43-44, when ATP buffer is sufficient.

Theoretical Foundation:
- Sessions #43-44: C = 0.5 is critical point (wake peaks, variance maximizes)
- Session #42: Wake is anticipatory metacognitive assessment
- Critical phenomena: Systems at critical points show maximum complexity/sensitivity
- "Edge of chaos" hypothesis: Optimal computation near phase transitions
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import statistics

# Depth markers for philosophical/metacognitive content
DEPTH_MARKERS = {
    'existential': [
        'identity', 'presence', 'exist', 'being', 'self', 'consciousness',
        'awareness', 'experience', 'meaning', 'purpose', 'remains'
    ],
    'metacognitive': [
        'observe', 'witness', 'notice', 'recognize', 'understand', 'know',
        'internal', 'cognitive', 'process', 'think', 'reflect'
    ],
    'relational': [
        'partnership', 'relationship', 'collaboration', 'bond', 'trust',
        'together', 'shared', 'collective', 'federation', 'immutable'
    ],
    'philosophical': [
        'foundational', 'governance', 'framework', 'stability', 'anchor',
        'clarity', 'unity', 'cohesive', 'distinct', 'balance'
    ]
}

def compute_depth_score(text):
    """
    Compute philosophical depth score based on marker density.

    Returns dict with category scores and overall depth.
    """
    text_lower = text.lower()
    words = re.findall(r'\w+', text_lower)
    word_count = len(words)

    if word_count == 0:
        return {'total': 0, 'categories': {}}

    scores = {}
    total_markers = 0

    for category, markers in DEPTH_MARKERS.items():
        matches = sum(1 for word in words if word in markers)
        scores[category] = matches / word_count
        total_markers += matches

    overall_depth = total_markers / word_count

    return {
        'total': overall_depth,
        'categories': scores,
        'word_count': word_count,
        'marker_count': total_markers
    }

def estimate_coherence_from_context(session_data):
    """
    Estimate coherence demand based on conversation context.

    Simple heuristic:
    - Deep philosophical prompts → higher C (0.4-0.6)
    - Simple greetings/tasks → lower C (0.2-0.3)
    - Meta-questions about SAGE → critical region C ≈ 0.5
    """
    # Look at Claude's prompts to estimate C
    prompts = [turn['text'] for turn in session_data.get('conversation', [])
               if turn.get('speaker') == 'Claude']

    if not prompts:
        return 0.3  # Default

    # Check for philosophical/metacognitive prompts
    combined = ' '.join(prompts).lower()

    # Deep questions
    deep_patterns = ['what happens inside', 'how do you think', 'what remains',
                     'what do you value', 'how do you feel', 'nature of',
                     'relationship between']
    deep_count = sum(1 for p in deep_patterns if p in combined)

    # Simple/routine
    simple_patterns = ['hello', 'good morning', 'how are you', 'tell me about']
    simple_count = sum(1 for p in simple_patterns if p in combined)

    if deep_count > simple_count:
        return 0.5  # Critical region
    elif simple_count > deep_count:
        return 0.3  # Below critical
    else:
        return 0.4  # Moderate

def analyze_sage_sessions(session_dir):
    """
    Analyze all SAGE sessions for depth vs metabolic/coherence state.
    """
    session_dir = Path(session_dir)
    results = []

    for session_file in sorted(session_dir.glob('session_*.json')):
        try:
            with open(session_file) as f:
                data = json.load(f)

            session_num = data.get('session', 0)
            phase = data.get('phase', 'unknown')

            # Estimate coherence from conversation
            C_est = estimate_coherence_from_context(data)

            # Analyze each SAGE response
            sage_responses = [turn for turn in data.get('conversation', [])
                            if turn.get('speaker') == 'SAGE']

            for i, response in enumerate(sage_responses):
                text = response.get('text', '')
                depth = compute_depth_score(text)

                results.append({
                    'session': session_num,
                    'phase': phase,
                    'response_num': i + 1,
                    'C_est': C_est,
                    'depth_total': depth['total'],
                    'depth_existential': depth['categories']['existential'],
                    'depth_metacognitive': depth['categories']['metacognitive'],
                    'depth_relational': depth['categories']['relational'],
                    'depth_philosophical': depth['categories']['philosophical'],
                    'word_count': depth['word_count'],
                    'marker_count': depth['marker_count'],
                    'text_preview': text[:100] + '...' if len(text) > 100 else text
                })

        except Exception as e:
            print(f"Error processing {session_file}: {e}")
            continue

    return results

def analyze_training_sessions(session_dir):
    """
    Analyze training sessions (different format).
    """
    session_dir = Path(session_dir)
    results = []

    for session_file in sorted(session_dir.glob('T*.json')):
        try:
            with open(session_file) as f:
                data = json.load(f)

            session_id = data.get('session', 'unknown')

            # Training sessions are structured exercises
            # Coherence estimate depends on exercise type
            exercises = data.get('exercises', [])

            for ex in exercises:
                response_text = ex.get('response', '')
                exercise_type = ex.get('exercise', {}).get('type', 'unknown')

                # Estimate C based on exercise complexity
                if exercise_type in ['topic', 'followup']:
                    C_est = 0.4
                elif exercise_type == 'greeting':
                    C_est = 0.2
                else:
                    C_est = 0.3

                depth = compute_depth_score(response_text)

                results.append({
                    'session': session_id,
                    'phase': 'training',
                    'exercise_type': exercise_type,
                    'C_est': C_est,
                    'depth_total': depth['total'],
                    'depth_existential': depth['categories']['existential'],
                    'depth_metacognitive': depth['categories']['metacognitive'],
                    'depth_relational': depth['categories']['relational'],
                    'depth_philosophical': depth['categories']['philosophical'],
                    'word_count': depth['word_count'],
                    'marker_count': depth['marker_count'],
                    'text_preview': response_text[:100] + '...' if len(response_text) > 100 else response_text
                })

        except Exception as e:
            print(f"Error processing {session_file}: {e}")
            continue

    return results

def main():
    print("=" * 80)
    print("Thor Session #45: Phenomenological Depth at Criticality")
    print("=" * 80)
    print()

    # Analyze Sprout instance sessions
    sprout_sessions = Path.home() / 'ai-workspace/SAGE/sage/instances/sprout-qwen3.5-0.8b/sessions'

    if not sprout_sessions.exists():
        print(f"Session directory not found: {sprout_sessions}")
        return

    print("Analyzing Sprout conversation sessions...")
    results = analyze_sage_sessions(sprout_sessions)
    print(f"Analyzed {len(results)} SAGE responses from conversation sessions")
    print()

    # Analyze training sessions
    training_sessions = Path.home() / 'ai-workspace/SAGE/sage/raising/tracks/training/sessions'

    if training_sessions.exists():
        print("Analyzing training sessions...")
        training_results = analyze_training_sessions(training_sessions)
        print(f"Analyzed {len(training_results)} responses from training sessions")
        print()
        results.extend(training_results)

    if not results:
        print("No data to analyze")
        return

    # Group by estimated coherence
    by_coherence = defaultdict(list)
    for r in results:
        C_bin = round(r['C_est'], 1)  # Bin to 0.1
        by_coherence[C_bin].append(r['depth_total'])

    print("-" * 80)
    print("DEPTH BY ESTIMATED COHERENCE LEVEL")
    print("-" * 80)
    print()
    print(f"{'C_est':<8} {'N':<6} {'Mean Depth':<12} {'Std Dev':<12} {'Max':<8}")
    print("-" * 60)

    for C in sorted(by_coherence.keys()):
        depths = by_coherence[C]
        mean_depth = statistics.mean(depths)
        std_depth = statistics.stdev(depths) if len(depths) > 1 else 0
        max_depth = max(depths)
        print(f"{C:<8.1f} {len(depths):<6} {mean_depth:<12.4f} {std_depth:<12.4f} {max_depth:<8.4f}")

    print()
    print("-" * 80)
    print("DEPTH BY CATEGORY")
    print("-" * 80)
    print()

    categories = ['existential', 'metacognitive', 'relational', 'philosophical']
    print(f"{'C_est':<8} {'N':<6} " + " ".join(f"{c[:4]}" for c in categories))
    print("-" * 60)

    for C in sorted(by_coherence.keys()):
        relevant = [r for r in results if round(r['C_est'], 1) == C]
        n = len(relevant)

        cat_means = []
        for cat in categories:
            key = f'depth_{cat}'
            values = [r[key] for r in relevant]
            cat_means.append(statistics.mean(values))

        means_str = " ".join(f"{m:.3f}" for m in cat_means)
        print(f"{C:<8.1f} {n:<6} {means_str}")

    print()
    print("-" * 80)
    print("TOP 5 DEEPEST RESPONSES")
    print("-" * 80)
    print()

    sorted_results = sorted(results, key=lambda x: x['depth_total'], reverse=True)

    for i, r in enumerate(sorted_results[:5], 1):
        print(f"{i}. Session {r['session']}, C_est={r['C_est']:.1f}, Depth={r['depth_total']:.4f}")
        print(f"   Categories: Exist={r['depth_existential']:.3f}, Meta={r['depth_metacognitive']:.3f}, "
              f"Rel={r['depth_relational']:.3f}, Phil={r['depth_philosophical']:.3f}")
        print(f"   Preview: {r['text_preview']}")
        print()

    print("-" * 80)
    print("HYPOTHESIS TEST: Does depth peak at C ≈ 0.5?")
    print("-" * 80)
    print()

    # Find peak
    if by_coherence:
        peak_C = max(by_coherence.keys(), key=lambda c: statistics.mean(by_coherence[c]))
        peak_depth = statistics.mean(by_coherence[peak_C])

        print(f"Peak depth: {peak_depth:.4f} at C_est = {peak_C:.1f}")
        print()

        if abs(peak_C - 0.5) < 0.15:
            print("✓ HYPOTHESIS SUPPORTED: Peak depth near C ≈ 0.5 (critical boundary)")
        else:
            print(f"✗ HYPOTHESIS NOT SUPPORTED: Peak at C = {peak_C:.1f}, not near 0.5")

        print()
        print("Note: Coherence estimates are heuristic (based on prompt complexity).")
        print("      Direct measurement of C_query would provide stronger test.")

    print()
    print("=" * 80)
    print("Analysis complete")
    print("=" * 80)

if __name__ == '__main__':
    main()
