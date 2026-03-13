#!/usr/bin/env python3
"""
Experiment: 60/40 Gradient Flow Convergence Validation
Tests if 60/40 weighting converges faster than 50/50 and other splits.

Gnosis Session #21
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/ai-workspace/web4/implementation/reference"))

from trust_gradient_flows import (
    TrustLandscape, gradient_descent, adam_optimizer, multi_objective_trust_loss
)
import statistics


def run_convergence_experiment():
    """
    Test convergence rate across different security/usability weight combinations.

    Hypothesis: 60/40 converges faster and to better optimum than 50/50 or other splits.
    """

    print("=" * 80)
    print("60/40 Gradient Flow Convergence Validation")
    print("Gnosis Session #21")
    print("=" * 80)

    # Test configurations
    weight_combinations = [
        (0.5, 0.5, "50/50 (symmetric)"),
        (0.6, 0.4, "60/40 (predicted optimal)"),
        (0.7, 0.3, "70/30 (conservative)"),
        (0.8, 0.2, "80/20 (very conservative)"),
        (0.4, 0.6, "40/60 (flexible-biased)"),
    ]

    initial_params = [0.7, 3.0]  # threshold, attestation_count
    lr = 0.01
    max_iter = 500

    print(f"\nConfiguration:")
    print(f"  Initial params: {initial_params}")
    print(f"  Learning rate: {lr}")
    print(f"  Max iterations: {max_iter}")
    print(f"\nTesting weight combinations:\n")

    results = []

    for sec_weight, use_weight, label in weight_combinations:
        # Create landscape with these weights
        def loss_fn(params):
            return multi_objective_trust_loss(params, sec_weight, use_weight)

        def grad_fn(params):
            # Numerical gradient
            eps = 1e-5
            grad = []
            for i in range(len(params)):
                p_plus = list(params)
                p_minus = list(params)
                p_plus[i] += eps
                p_minus[i] -= eps
                grad.append((loss_fn(p_plus) - loss_fn(p_minus)) / (2 * eps))
            return grad

        landscape = TrustLandscape(
            dim=2,
            loss_fn=loss_fn,
            grad_fn=grad_fn,
            name=f"multi_objective_{sec_weight}_{use_weight}"
        )

        # Run gradient descent
        result = gradient_descent(landscape, initial_params, lr=lr, max_iter=max_iter)

        results.append({
            "label": label,
            "sec_weight": sec_weight,
            "use_weight": use_weight,
            "iterations": result.iterations,
            "final_loss": result.loss,
            "converged": result.converged,
            "final_params": result.params,
        })

        status = "✓ CONVERGED" if result.converged else "✗ DID NOT CONVERGE"
        print(f"  {label:30s}: {result.iterations:4d} iter, loss={result.loss:8.4f}  {status}")

    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    # Find best by iterations (among converged)
    converged = [r for r in results if r["converged"]]
    if converged:
        best_iterations = min(converged, key=lambda r: r["iterations"])
        best_loss = min(converged, key=lambda r: r["final_loss"])

        print(f"\nFastest convergence: {best_iterations['label']}")
        print(f"  Iterations: {best_iterations['iterations']}")
        print(f"  Final loss: {best_iterations['final_loss']:.4f}")

        print(f"\nLowest final loss: {best_loss['label']}")
        print(f"  Iterations: {best_loss['iterations']}")
        print(f"  Final loss: {best_loss['final_loss']:.4f}")

        # Test prediction
        is_60_40_fastest = best_iterations["label"] == "60/40 (predicted optimal)"
        is_60_40_best_loss = best_loss["label"] == "60/40 (predicted optimal)"

        print("\n" + "=" * 80)
        print("PREDICTION VALIDATION")
        print("=" * 80)

        print(f"\nHypothesis 1: 60/40 converges fastest")
        print(f"  Result: {'✓ CONFIRMED' if is_60_40_fastest else '✗ REJECTED'}")
        if not is_60_40_fastest:
            print(f"  Fastest was: {best_iterations['label']} ({best_iterations['iterations']} iter vs {[r for r in results if r['label']=='60/40 (predicted optimal)'][0]['iterations']} iter)")

        print(f"\nHypothesis 2: 60/40 achieves lowest loss")
        print(f"  Result: {'✓ CONFIRMED' if is_60_40_best_loss else '✗ REJECTED'}")
        if not is_60_40_best_loss:
            print(f"  Best loss was: {best_loss['label']} ({best_loss['final_loss']:.4f} vs {[r for r in results if r['label']=='60/40 (predicted optimal)'][0]['final_loss']:.4f})")

        # Overall assessment
        if is_60_40_fastest and is_60_40_best_loss:
            print(f"\n{'='*80}")
            print("STRONG VALIDATION: 60/40 is both fastest AND achieves best loss!")
            print(f"{'='*80}")
        elif is_60_40_fastest or is_60_40_best_loss:
            print(f"\n{'='*80}")
            print("PARTIAL VALIDATION: 60/40 excels in one metric")
            print(f"{'='*80}")
        else:
            print(f"\n{'='*80}")
            print("PREDICTION NOT CONFIRMED: Other weights performed better")
            print(f"{'='*80}")

    else:
        print("\nNo configurations converged - experiment inconclusive")

    # Detailed results table
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    print(f"\n{'Label':<30} {'Sec':>5} {'Use':>5} {'Iter':>6} {'Loss':>10} {'Conv':>6}")
    print("-" * 80)
    for r in results:
        conv = "Yes" if r["converged"] else "No"
        print(f"{r['label']:<30} {r['sec_weight']:>5.1f} {r['use_weight']:>5.1f} "
              f"{r['iterations']:>6d} {r['final_loss']:>10.4f} {conv:>6}")

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_convergence_experiment()
