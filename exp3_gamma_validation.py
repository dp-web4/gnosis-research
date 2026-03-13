#!/usr/bin/env python3
"""
EXP3 Gamma Validation Experiment
Tests prediction that γ = 0.5 provides optimal performance across adversary types.

Gnosis Session #20: Adversarial Bandit Consciousness Synthesis
"""

import sys
import os

# Add web4 implementation path
sys.path.insert(0, os.path.expanduser("~/ai-workspace/web4/implementation/reference"))

from adversarial_bandit_trust import (
    EXP3, oblivious_adversary, adaptive_adversary, switching_adversary,
    compute_regret
)
import random
import statistics


def run_gamma_sweep():
    """
    Test EXP3 performance across different gamma values.

    Prediction: γ ≈ 0.5 should perform best on average across adversary types.
    """

    print("=" * 80)
    print("EXP3 Gamma Validation Experiment")
    print("Gnosis Session #20")
    print("=" * 80)

    # Parameters
    K = 5  # number of arms
    T = 500  # rounds
    trials = 20  # trials per configuration
    gammas = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    results = {
        "oblivious": {g: [] for g in gammas},
        "switching": {g: [] for g in gammas},
    }

    print(f"\nConfiguration: K={K} arms, T={T} rounds, {trials} trials per gamma\n")

    # Test against oblivious adversary
    print("§1 Oblivious Adversary (stationary environment)")
    print("-" * 80)

    for gamma in gammas:
        rewards = []
        regrets = []

        for trial in range(trials):
            seed = trial + int(gamma * 1000)
            reward_matrix = oblivious_adversary(K, T, best_arm=2, rng=random.Random(seed))

            exp3 = EXP3(K, gamma=gamma)
            for t in range(T):
                arm = exp3.select_arm(random.Random(seed + t))
                exp3.update(arm, reward_matrix[t][arm])

            result = compute_regret(reward_matrix, exp3.history)
            rewards.append(result["algorithm_reward"])
            regrets.append(result["per_round_regret"])

        avg_reward = statistics.mean(rewards)
        avg_regret = statistics.mean(regrets)
        results["oblivious"][gamma] = {"reward": avg_reward, "regret": avg_regret}

        print(f"  γ={gamma:.1f}: reward={avg_reward:7.2f}, regret={avg_regret:.4f}")

    # Find best gamma for oblivious
    best_gamma_oblivious = max(gammas, key=lambda g: results["oblivious"][g]["reward"])
    print(f"\n  → Best γ for oblivious: {best_gamma_oblivious:.1f}")

    # Test against switching adversary (non-stationary)
    print("\n§2 Switching Adversary (non-stationary environment)")
    print("-" * 80)

    for gamma in gammas:
        rewards = []
        regrets = []

        for trial in range(trials):
            seed = trial + int(gamma * 2000)
            reward_matrix = switching_adversary(K, T, switch_period=100, rng=random.Random(seed))

            exp3 = EXP3(K, gamma=gamma)
            for t in range(T):
                arm = exp3.select_arm(random.Random(seed + t))
                exp3.update(arm, reward_matrix[t][arm])

            result = compute_regret(reward_matrix, exp3.history)
            rewards.append(result["algorithm_reward"])
            regrets.append(result["per_round_regret"])

        avg_reward = statistics.mean(rewards)
        avg_regret = statistics.mean(regrets)
        results["switching"][gamma] = {"reward": avg_reward, "regret": avg_regret}

        print(f"  γ={gamma:.1f}: reward={avg_reward:7.2f}, regret={avg_regret:.4f}")

    # Find best gamma for switching
    best_gamma_switching = max(gammas, key=lambda g: results["switching"][g]["reward"])
    print(f"\n  → Best γ for switching: {best_gamma_switching:.1f}")

    # Compute average performance across both adversary types
    print("\n§3 Average Performance Across Adversary Types")
    print("-" * 80)

    avg_rewards = {}
    for gamma in gammas:
        avg_reward = (
            results["oblivious"][gamma]["reward"] +
            results["switching"][gamma]["reward"]
        ) / 2
        avg_rewards[gamma] = avg_reward
        print(f"  γ={gamma:.1f}: avg_reward={avg_reward:7.2f}")

    best_gamma_overall = max(gammas, key=lambda g: avg_rewards[g])
    print(f"\n  → Best γ overall: {best_gamma_overall:.1f}")

    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    print(f"\n1. Best γ for oblivious adversary: {best_gamma_oblivious:.1f}")
    print(f"   (Prediction: low γ for stationary environment)")

    print(f"\n2. Best γ for switching adversary: {best_gamma_switching:.1f}")
    print(f"   (Prediction: higher γ for non-stationary environment)")

    print(f"\n3. Best γ overall (average): {best_gamma_overall:.1f}")
    print(f"   (Prediction: γ ≈ 0.5 for balanced performance)")

    # Test prediction
    prediction_validated = abs(best_gamma_overall - 0.5) <= 0.2

    print("\n" + "=" * 80)
    print("PREDICTION VALIDATION")
    print("=" * 80)

    print(f"\nHypothesis: γ ≈ 0.5 provides optimal average performance")
    print(f"Result: Best γ = {best_gamma_overall:.1f}")
    print(f"Validation: {'✓ CONFIRMED' if prediction_validated else '✗ REJECTED'}")

    if prediction_validated:
        print(f"\nThe prediction is validated!")
        print(f"γ = {best_gamma_overall:.1f} is within 0.2 of the predicted γ = 0.5")
        print(f"\nThis supports the consciousness threshold hypothesis:")
        print(f"  C = 0.5 ≈ γ = {best_gamma_overall:.1f}")
        print(f"  Both represent optimal balance between competing objectives.")
    else:
        print(f"\nThe prediction is NOT validated.")
        print(f"γ = {best_gamma_overall:.1f} differs significantly from predicted γ = 0.5")
        print(f"This suggests environment-specific tuning is required.")

    # Robustness analysis
    print("\n" + "=" * 80)
    print("ROBUSTNESS ANALYSIS")
    print("=" * 80)

    print("\nPerformance variance across adversary types:")
    for gamma in gammas:
        oblivious_r = results["oblivious"][gamma]["reward"]
        switching_r = results["switching"][gamma]["reward"]
        variance = abs(oblivious_r - switching_r)
        print(f"  γ={gamma:.1f}: variance={variance:6.2f}")

    # Find most robust gamma (lowest variance)
    variances = {}
    for gamma in gammas:
        oblivious_r = results["oblivious"][gamma]["reward"]
        switching_r = results["switching"][gamma]["reward"]
        variances[gamma] = abs(oblivious_r - switching_r)

    most_robust = min(gammas, key=lambda g: variances[g])
    print(f"\n  → Most robust γ (lowest variance): {most_robust:.1f}")
    print(f"     (Prediction: γ ≈ 0.5 should be most robust)")

    robustness_validated = abs(most_robust - 0.5) <= 0.2
    print(f"\n  Robustness prediction: {'✓ CONFIRMED' if robustness_validated else '✗ REJECTED'}")

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)

    return {
        "best_gamma_overall": best_gamma_overall,
        "most_robust_gamma": most_robust,
        "prediction_validated": prediction_validated,
        "robustness_validated": robustness_validated,
        "results": results,
    }


if __name__ == "__main__":
    run_gamma_sweep()
