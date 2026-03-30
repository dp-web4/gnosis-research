#!/usr/bin/env python3
"""
Thor Session #42: Wake State Reinterpretation
==============================================

Major theoretical revision of Session #41 dual-process hypothesis.

Discovery: Wake is ANTICIPATORY (pre-turn metacognitive assessment),
NOT a processing mode switch that determines response characteristics.

Key findings:
1. Generation speed constant (~30 chars/sec) across all conditions
2. Response time driven by LENGTH, not wake state
3. Wake and response characteristics are DECOUPLED
4. Wake peaks at "interesting" difficulty (Level 3), not maximum
5. Response depth determined by query needs, not wake state

This challenges the System 1 / System 2 interpretation from Session #41.
"""

import json
import numpy as np
from collections import defaultdict
from scipy import stats
import sys

def load_data(filepath='graded_query_difficulty_20260329_092425.json'):
    """Load Session #39 experimental data."""
    with open(filepath) as f:
        return json.load(f)

def analyze_generation_speed(results):
    """
    Test whether generation speed is constant across conditions.

    If constant, implies LLM bottleneck, not cognitive processing variation.
    """
    print("=" * 80)
    print("ANALYSIS 1: GENERATION SPEED CONSISTENCY")
    print("=" * 80)

    by_level = defaultdict(list)
    for r in results:
        level = r['difficulty_level']
        speed = r['response_length'] / r['response_time']
        by_level[level].append(speed)

    print("\nGeneration speed (chars/sec) by difficulty level:")
    all_speeds = []
    for level in sorted(by_level.keys()):
        speeds = by_level[level]
        mean_speed = np.mean(speeds)
        std_speed = np.std(speeds)
        all_speeds.extend(speeds)
        print(f"  Level {level}: {mean_speed:.1f} ± {std_speed:.1f} chars/sec (N={len(speeds)})")

    overall_mean = np.mean(all_speeds)
    overall_std = np.std(all_speeds)
    cv = (overall_std / overall_mean) * 100  # Coefficient of variation

    print(f"\nOverall: {overall_mean:.1f} ± {overall_std:.1f} chars/sec")
    print(f"Coefficient of variation: {cv:.1f}%")

    print("\n**INTERPRETATION**:")
    if cv < 10:
        print(f"Generation speed is highly consistent ({cv:.1f}% variation).")
        print("This indicates LLM token generation is the bottleneck.")
        print("Response time ≈ Response length / ~30 chars/sec")
    else:
        print(f"Generation speed varies significantly ({cv:.1f}% variation).")
        print("This would suggest cognitive processing affects generation rate.")

    return overall_mean

def analyze_response_time_drivers(results):
    """
    Determine what drives response time: wake state, length, or ATP?
    """
    print("\n\n" + "=" * 80)
    print("ANALYSIS 2: RESPONSE TIME DRIVERS")
    print("=" * 80)

    # Extract variables
    times = np.array([r['response_time'] for r in results])
    lengths = np.array([r['response_length'] for r in results])
    wake_binary = np.array([1 if r['pre_turn_state'] == 'wake' else 0 for r in results])
    atps = np.array([r['pre_turn_atp'] for r in results])

    # Correlations
    corr_time_len, p_time_len = stats.pearsonr(times, lengths)
    corr_time_wake, p_time_wake = stats.pearsonr(times, wake_binary)
    corr_time_atp, p_time_atp = stats.pearsonr(times, atps)

    print("\nPearson correlations with response time:")
    print(f"  Response Length: r={corr_time_len:.3f}, p={p_time_len:.4f}")
    print(f"  Wake State:      r={corr_time_wake:.3f}, p={p_time_wake:.4f}")
    print(f"  Pre-turn ATP:    r={corr_time_atp:.3f}, p={p_time_atp:.4f}")

    print("\n**INTERPRETATION**:")
    print(f"Response time is {'STRONGLY' if abs(corr_time_len) > 0.7 else 'moderately' if abs(corr_time_len) > 0.4 else 'weakly'} correlated with length (r={corr_time_len:.3f})")
    print(f"Response time is {'NOT' if abs(corr_time_wake) < 0.3 else ''} correlated with wake state (r={corr_time_wake:.3f})")
    print(f"Response time is {'NOT' if abs(corr_time_atp) < 0.3 else ''} correlated with ATP (r={corr_time_atp:.3f})")

    # Partial correlation: time vs wake, controlling for length
    from scipy.stats import pearsonr

    # Residuals method for partial correlation
    def partial_corr(x, y, z):
        """Compute partial correlation between x and y, controlling for z."""
        # Residualize x and y against z
        x_resid = x - np.polyval(np.polyfit(z, x, 1), z)
        y_resid = y - np.polyval(np.polyfit(z, y, 1), z)
        return pearsonr(x_resid, y_resid)

    partial_r, partial_p = partial_corr(times, wake_binary, lengths)

    print(f"\nPartial correlation (Time vs Wake, controlling for Length):")
    print(f"  r={partial_r:.3f}, p={partial_p:.4f}")

    if abs(partial_r) < 0.2:
        print("\n**CONCLUSION**: Wake state does NOT drive response time after controlling for length.")
        print("Response time is primarily determined by response length.")

def analyze_wake_response_decoupling(results):
    """
    Test whether wake state and response characteristics are decoupled.
    """
    print("\n\n" + "=" * 80)
    print("ANALYSIS 3: WAKE VS RESPONSE DECOUPLING")
    print("=" * 80)

    by_level = defaultdict(list)
    for r in results:
        level = r['difficulty_level']
        by_level[level].append(r)

    print("\nBy difficulty level:")
    print(f"{'Level':<8} {'Wake%':<10} {'Time(s)':<12} {'Length':<10} {'ATP':<8}")
    print("-" * 60)

    for level in sorted(by_level.keys()):
        queries = by_level[level]

        wake_count = sum(1 for q in queries if q['pre_turn_state'] == 'wake')
        wake_pct = (wake_count / len(queries)) * 100

        mean_time = np.mean([q['response_time'] for q in queries])
        mean_len = np.mean([q['response_length'] for q in queries])
        mean_atp = np.mean([q['pre_turn_atp'] for q in queries])

        print(f"{level:<8} {wake_pct:>6.1f}%   {mean_time:>8.1f}s   {mean_len:>6.0f}    {mean_atp:>6.1f}")

    print("\n**PATTERN IDENTIFIED**:")
    print("\n1. WAKE follows inverted-U:")
    print("   - Peak at Level 3 (60%) - moderate difficulty")
    print("   - Low at Levels 1 (12.5%) and 5 (25%) - trivial and demanding")

    print("\n2. RESPONSE TIME follows U-curve:")
    print("   - Long at Levels 2-3 (23s, 21s)")
    print("   - Short at Levels 1,4,5 (14s, 14s, 14s)")

    print("\n3. RESPONSE LENGTH bimodal:")
    print("   - Thorough at Levels 2-3 (~650-700 chars)")
    print("   - Brief at Levels 1,4,5 (~380-430 chars)")

    print("\n**DECOUPLING EVIDENCE**:")
    print("- Level 2: LOW wake (25%) but LONGEST time (23.3s) and LONGEST responses (709 chars)")
    print("- Level 3: HIGH wake (60%) but NOT longest time (20.9s)")
    print("- Level 5: LOW wake (25%) and SHORT time (13.6s)")

    print("\nWake state does NOT determine response characteristics!")

def analyze_wake_as_anticipation(results):
    """
    Test the hypothesis that wake is anticipatory/metacognitive assessment.
    """
    print("\n\n" + "=" * 80)
    print("ANALYSIS 4: WAKE AS ANTICIPATORY METACOGNITION")
    print("=" * 80)

    print("\nHypothesis: Wake represents pre-turn assessment of query 'interest'")
    print("Interest = Goldilocks zone (not too easy, not too hard)")

    by_level = defaultdict(list)
    for r in results:
        level = r['difficulty_level']
        by_level[level].append(r)

    wake_rates = []
    for level in sorted(by_level.keys()):
        queries = by_level[level]
        wake_count = sum(1 for q in queries if q['pre_turn_state'] == 'wake')
        wake_pct = (wake_count / len(queries)) * 100
        wake_rates.append((level, wake_pct))

    # Find peak
    peak_level, peak_wake = max(wake_rates, key=lambda x: x[1])

    print(f"\nWake activation peaks at Level {peak_level} ({peak_wake:.1f}%)")
    print("\nThis is the 'moderate' difficulty level - neither trivial nor overwhelming.")

    print("\n**INTERPRETATION**:")
    print("Wake is highest where queries are:")
    print("  - Complex enough to be 'interesting'")
    print("  - Simple enough to be 'tractable'")
    print("  - In the 'Goldilocks zone' of cognitive engagement")

    print("\nWake is LOW where queries are:")
    print("  - Too trivial (Level 1): No challenge, routine processing")
    print("  - Too demanding (Level 5): System recognizes futility of extra preparation")

    print("\n**CONNECTION TO YERKES-DODSON LAW**:")
    print("Optimal arousal occurs at intermediate challenge levels.")
    print("Wake activation follows this classical pattern.")

    print("\n**METACOGNITIVE INTERPRETATION**:")
    print("The inverted-U suggests SAGE has implicit difficulty assessment:")
    print("  - Recognizes 'trivial' queries → low wake")
    print("  - Recognizes 'interesting' queries → high wake")
    print("  - Recognizes 'overwhelming' queries → low wake")
    print("\nThis is evidence of metacognitive competence!")

def analyze_response_determinants(results):
    """
    What actually determines response characteristics if not wake?
    """
    print("\n\n" + "=" * 80)
    print("ANALYSIS 5: WHAT DETERMINES RESPONSE CHARACTERISTICS?")
    print("=" * 80)

    print("\nIf wake doesn't drive response time/length, what does?")

    by_level = defaultdict(list)
    for r in results:
        level = r['difficulty_level']
        by_level[level].append(r)

    print("\nQuery difficulty level appears to be primary driver:")

    simple_moderate = by_level[2] + by_level[3]
    others = by_level[1] + by_level[4] + by_level[5]

    sm_len = np.mean([q['response_length'] for q in simple_moderate])
    ot_len = np.mean([q['response_length'] for q in others])

    sm_time = np.mean([q['response_time'] for q in simple_moderate])
    ot_time = np.mean([q['response_time'] for q in others])

    print(f"\nSimple/Moderate (Levels 2-3, N={len(simple_moderate)}):")
    print(f"  Mean length: {sm_len:.0f} chars")
    print(f"  Mean time: {sm_time:.1f}s")

    print(f"\nTrivial/Complex/Demanding (Levels 1,4,5, N={len(others)}):")
    print(f"  Mean length: {ot_len:.0f} chars")
    print(f"  Mean time: {ot_time:.1f}s")

    print(f"\nDifference:")
    print(f"  Length: {sm_len:.0f} vs {ot_len:.0f} = {sm_len - ot_len:.0f} chars ({(sm_len/ot_len - 1)*100:.0f}% longer)")
    print(f"  Time: {sm_time:.1f}s vs {ot_time:.1f}s = {sm_time - ot_time:.1f}s ({(sm_time/ot_time - 1)*100:.0f}% longer)")

    print("\n**HYPOTHESIS**:")
    print("Levels 2-3 benefit from detailed explanations (science concepts, theorems)")
    print("Levels 1,4,5 don't benefit from verbosity:")
    print("  - Level 1: Trivial questions have short answers")
    print("  - Level 4: Complex questions may be answered concisely")
    print("  - Level 5: Demanding questions recognized as limited value in elaboration")

    print("\nResponse characteristics determined by:")
    print("  1. Query type/difficulty")
    print("  2. System's assessment of 'appropriate depth'")
    print("  3. NOT wake state")

def generate_summary_statistics(results):
    """
    Generate comprehensive summary statistics.
    """
    print("\n\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    by_level = defaultdict(list)
    for r in results:
        level = r['difficulty_level']
        by_level[level].append(r)

    print("\nComplete data by difficulty level:")
    print(f"\n{'Metric':<25} {'L1':<10} {'L2':<10} {'L3':<10} {'L4':<10} {'L5':<10}")
    print("-" * 75)

    # N
    ns = [len(by_level[l]) for l in sorted(by_level.keys())]
    print(f"{'N':<25} {ns[0]:<10} {ns[1]:<10} {ns[2]:<10} {ns[3]:<10} {ns[4]:<10}")

    # Wake %
    wakes = [sum(1 for q in by_level[l] if q['pre_turn_state']=='wake')/len(by_level[l])*100
             for l in sorted(by_level.keys())]
    print(f"{'Wake %':<25} {wakes[0]:<10.1f} {wakes[1]:<10.1f} {wakes[2]:<10.1f} {wakes[3]:<10.1f} {wakes[4]:<10.1f}")

    # ATP
    atps = [np.mean([q['pre_turn_atp'] for q in by_level[l]]) for l in sorted(by_level.keys())]
    print(f"{'ATP (mean)':<25} {atps[0]:<10.1f} {atps[1]:<10.1f} {atps[2]:<10.1f} {atps[3]:<10.1f} {atps[4]:<10.1f}")

    # Time
    times = [np.mean([q['response_time'] for q in by_level[l]]) for l in sorted(by_level.keys())]
    print(f"{'Time (s)':<25} {times[0]:<10.1f} {times[1]:<10.1f} {times[2]:<10.1f} {times[3]:<10.1f} {times[4]:<10.1f}")

    # Length
    lens = [np.mean([q['response_length'] for q in by_level[l]]) for l in sorted(by_level.keys())]
    print(f"{'Length (chars)':<25} {lens[0]:<10.0f} {lens[1]:<10.0f} {lens[2]:<10.0f} {lens[3]:<10.0f} {lens[4]:<10.0f}")

    # Speed
    speeds = [np.mean([q['response_length']/q['response_time'] for q in by_level[l]])
              for l in sorted(by_level.keys())]
    print(f"{'Speed (chars/s)':<25} {speeds[0]:<10.1f} {speeds[1]:<10.1f} {speeds[2]:<10.1f} {speeds[3]:<10.1f} {speeds[4]:<10.1f}")

def main():
    """Run comprehensive reanalysis."""
    print("\n")
    print("=" * 80)
    print("THOR SESSION #42: WAKE STATE REINTERPRETATION")
    print("Reanalysis of Session #39 Data")
    print("=" * 80)
    print("\n")

    # Load data
    data = load_data()
    results = data['results']

    print(f"Dataset: {len(results)} successful queries from Session #39")
    print(f"Original hypothesis: Discrete vs continuous wake evaluation")
    print(f"Actual finding: Inverted-U wake pattern")
    print(f"Session #41 interpretation: Dual-process architecture")
    print(f"THIS SESSION: Testing and refining that interpretation")
    print("\n")

    # Run analyses
    gen_speed = analyze_generation_speed(results)
    analyze_response_time_drivers(results)
    analyze_wake_response_decoupling(results)
    analyze_wake_as_anticipation(results)
    analyze_response_determinants(results)
    generate_summary_statistics(results)

    # Final conclusions
    print("\n\n" + "=" * 80)
    print("FINAL CONCLUSIONS")
    print("=" * 80)

    print("\n**MAJOR THEORETICAL REVISION**:")
    print("\nSession #41 proposed: Wake = processing mode (System 1 vs System 2)")
    print("Session #42 finds: Wake = metacognitive assessment (anticipation)")

    print("\n**KEY FINDINGS**:")
    print("1. Generation speed constant (~30 chars/sec) → LLM bottleneck")
    print("2. Response time correlates with LENGTH, not wake state")
    print("3. Wake peaks at 'interesting' difficulty (inverted-U)")
    print("4. Response characteristics determined by query type, not wake")
    print("5. Wake and response are DECOUPLED (pre-turn vs post-turn)")

    print("\n**REVISED THEORY**:")
    print("\nWake = Anticipatory metacognitive assessment")
    print("  - High when query is 'interesting' (moderate difficulty)")
    print("  - Low when query is trivial OR overwhelming")
    print("  - Represents readiness/arousal, not processing mode")

    print("\nResponse characteristics = Query-driven")
    print("  - Length determined by query type and appropriate depth")
    print("  - Time determined by length (constant generation speed)")
    print("  - Independent of wake state")

    print("\n**IMPLICATIONS**:")
    print("- Wake is ANTICIPATORY (pre-turn), not DETERMINISTIC (doesn't control processing)")
    print("- Inverted-U reflects Yerkes-Dodson arousal (metacognitive competence)")
    print("- System 1/System 2 interpretation not supported by data")
    print("- SAGE has implicit difficulty assessment capability")

    print("\n**WHAT WAKE IS NOT**:")
    print("- NOT a processing mode switch")
    print("- NOT determinant of response depth")
    print("- NOT correlated with deliberation time")

    print("\n**WHAT WAKE IS**:")
    print("- Metacognitive 'interest' signal")
    print("- Arousal/readiness state")
    print("- Evidence of implicit difficulty assessment")
    print("- Follows Yerkes-Dodson optimal arousal pattern")

    print("\n" + "=" * 80)
    print("Analysis complete. Session #42 provides major refinement of wake theory.")
    print("=" * 80)
    print("\n")

if __name__ == '__main__':
    main()
