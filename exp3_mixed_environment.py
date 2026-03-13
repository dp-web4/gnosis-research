#!/usr/bin/env python3
"""
EXP3 Mixed Environment Experiment
Tests revised prediction: optimal γ correlates with environment stationarity.

Gnosis Session #20, Experiment 2
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/ai-workspace/web4/implementation/reference"))

from adversarial_bandit_trust import (
    EXP3, oblivious_adversary, switching_adversary, compute_regret
)
import random
import statistics


def mixed_adversary(K, T, stationary_fraction, seed=42):
    """
    Create a mixed adversary environment.

    Args:
        stationary_fraction: Fraction of rounds that use stationary rewards
    """
    rng = random.Random(seed)

    # Generate both reward streams
    oblivious_rewards = oblivious_adversary(K, T, best_arm=2, rng=random.Random(seed))
    switching_rewards = switching_adversary(K, T, switch_period=100, rng=random.Random(seed + 1))

    # Mix them based on stationary_fraction
    mixed_rewards = []
    for t in range(T):
        if rng.random() < stationary_fraction:
            mixed_rewards.append(oblivious_rewards[t])
        else:
            mixed_rewards.append(switching_rewards[t])

    return mixed_rewards


def run_mixed_environment_experiment():
    """
    Test EXP3 performance with varying environment stationarity.

    Key prediction: optimal γ correlates with stationary_fraction.
    Specifically: stationary_fraction = 0.5 → optimal γ ≈ 0.5
    """

    print("=" * 80)
    print("EXP3 Mixed Environment Experiment")
    print("Gnosis Session #20, Experiment 2")
    print("=" * 80)

    K = 5
    T = 500
    trials = 15
    gammas = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    stationary_fractions = [0.0, 0.25, 0.5, 0.75, 1.0]

    results = {sf: {g: [] for g in gammas} for sf in stationary_fractions}

    print(f"\nConfiguration: K={K} arms, T={T} rounds, {trials} trials")
    print(f"Testing stationary_fractions: {stationary_fractions}")
    print(f"Testing gammas: {gammas}\n")

    # Run experiments
    for sf in stationary_fractions:
        print(f"\n{'='*80}")
        print(f"Stationary Fraction = {sf:.2f}")
        print(f"{'='*80}\n")

        for gamma in gammas:
            rewards = []

            for trial in range(trials):
                seed = trial + int(sf * 1000) + int(gamma * 100)
                reward_matrix = mixed_adversary(K, T, sf, seed=seed)

                exp3 = EXP3(K, gamma=gamma)
                for t in range(T):
                    arm = exp3.select_arm(random.Random(seed + t))
                    exp3.update(arm, reward_matrix[t][arm])

                result = compute_regret(reward_matrix, exp3.history)
                rewards.append(result["algorithm_reward"])

            avg_reward = statistics.mean(rewards)
            std_reward = statistics.stdev(rewards) if len(rewards) > 1 else 0
            results[sf][gamma] = {"mean": avg_reward, "std": std_reward}

            print(f"  γ={gamma:.1f}: reward={avg_reward:7.2f} ± {std_reward:5.2f}")

        # Find best gamma for this stationary fraction
        best_gamma = max(gammas, key=lambda g: results[sf][g]["mean"])
        print(f"\n  → Best γ for stationary_fraction={sf:.2f}: {best_gamma:.1f}")

    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS: Optimal γ vs Stationary Fraction")
    print("=" * 80)

    best_gammas = {}
    for sf in stationary_fractions:
        best_gamma = max(gammas, key=lambda g: results[sf][g]["mean"])
        best_gammas[sf] = best_gamma
        print(f"  Stationary fraction {sf:.2f} → Best γ = {best_gamma:.1f}")

    # Test key prediction: sf = 0.5 → γ ≈ 0.5
    print("\n" + "=" * 80)
    print("KEY PREDICTION VALIDATION")
    print("=" * 80)

    key_prediction_sf = 0.5
    predicted_gamma = 0.5
    observed_gamma = best_gammas[key_prediction_sf]

    print(f"\nHypothesis: stationary_fraction = {key_prediction_sf} → optimal γ ≈ {predicted_gamma}")
    print(f"Result: Optimal γ = {observed_gamma}")

    tolerance = 0.2
    prediction_validated = abs(observed_gamma - predicted_gamma) <= tolerance

    print(f"Validation: {'✓ CONFIRMED' if prediction_validated else '✗ REJECTED'}")
    print(f"  (tolerance = ±{tolerance})")

    if prediction_validated:
        print(f"\n✓ The revised prediction is VALIDATED!")
        print(f"  When environment is 50% stationary / 50% non-stationary,")
        print(f"  optimal γ ≈ {observed_gamma} (within {tolerance} of predicted {predicted_gamma})")
    else:
        print(f"\n✗ The revised prediction is NOT validated.")
        print(f"  Expected γ ≈ {predicted_gamma}, observed γ = {observed_gamma}")

    # Test monotonicity: does optimal γ increase with non-stationarity?
    print("\n" + "=" * 80)
    print("MONOTONICITY TEST")
    print("=" * 80)

    print("\nHypothesis: Optimal γ increases as environment becomes less stationary")
    print("  (i.e., optimal γ should increase as stationary_fraction decreases)\n")

    # Check if there's a general trend
    sf_sorted = sorted(stationary_fractions)
    gamma_sequence = [best_gammas[sf] for sf in sf_sorted]

    print(f"Stationary fraction sequence: {[f'{sf:.2f}' for sf in sf_sorted]}")
    print(f"Optimal γ sequence:           {[f'{g:.1f}' for g in gamma_sequence]}")

    # Check for general increasing trend (allowing some noise)
    # We expect: sf increases → optimal γ should generally decrease
    inversely_related = True
    for i in range(len(sf_sorted) - 1):
        if sf_sorted[i] < sf_sorted[i+1]:  # sf increased
            # We expect gamma to decrease (or stay similar)
            if gamma_sequence[i+1] > gamma_sequence[i] + 0.2:
                inversely_related = False
                break

    print(f"\nMonotonicity (inverse relationship): {'✓ CONFIRMED' if inversely_related else '✗ REJECTED'}")

    # Correlation analysis
    print("\n" + "=" * 80)
    print("CORRELATION ANALYSIS")
    print("=" * 80)

    # Compute correlation between sf and optimal gamma
    mean_sf = statistics.mean(sf_sorted)
    mean_gamma = statistics.mean(gamma_sequence)

    numerator = sum((sf - mean_sf) * (g - mean_gamma)
                    for sf, g in zip(sf_sorted, gamma_sequence))
    denom_sf = sum((sf - mean_sf) ** 2 for sf in sf_sorted)
    denom_g = sum((g - mean_gamma) ** 2 for g in gamma_sequence)

    if denom_sf > 0 and denom_g > 0:
        correlation = numerator / (denom_sf * denom_g) ** 0.5
        print(f"\nPearson correlation(stationary_fraction, optimal_γ) = {correlation:.3f}")
        print(f"  < 0: Inverse relationship (as expected)")
        print(f"  > 0: Direct relationship (unexpected)")

        if correlation < -0.3:
            print(f"\n✓ Moderate to strong inverse correlation confirmed")
        elif correlation > 0.3:
            print(f"\n✗ Unexpected positive correlation!")
        else:
            print(f"\n~ Weak or no correlation detected")
    else:
        print(f"\nInsufficient variance for correlation analysis")

    # Performance table
    print("\n" + "=" * 80)
    print("DETAILED PERFORMANCE TABLE")
    print("=" * 80)

    print(f"\n{'Stat.Frac':<12}", end="")
    for gamma in gammas:
        print(f"γ={gamma:.1f:>4}  ", end="")
    print()

    print("-" * 80)

    for sf in stationary_fractions:
        print(f"{sf:>10.2f}  ", end="")
        best_for_sf = max(gammas, key=lambda g: results[sf][g]["mean"])
        for gamma in gammas:
            reward = results[sf][gamma]["mean"]
            marker = " *" if gamma == best_for_sf else "  "
            print(f"{reward:>6.1f}{marker}", end=" ")
        print()

    print("\n(* marks best γ for each stationary fraction)")

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)

    return {
        "best_gammas": best_gammas,
        "key_prediction_validated": prediction_validated,
        "monotonicity_validated": inversely_related,
        "results": results,
    }


if __name__ == "__main__":
    run_mixed_environment_experiment()
