#!/usr/bin/env python3
"""
Refined test: Maybe ρ_cognitive ≠ N_corr directly
Try different mappings

Alternative hypotheses:
1. ρ = N_corr² (quadratic)
2. ρ = N_corr/some_factor (scaled)
3. Different functional form entirely
4. ρ = something else (response length, duration, etc.)

OR: Maybe the equation form is slightly different at cognitive scale
"""

import math

# SAGE empirical data
sessions = ['S087', 'S086', 'S089', 'S090', 'S085']
C_observed = [0.20, 0.45, 0.50, 0.50, 0.55]
N_corr = [2.5, 3.0, 4.0, 5.0, 5.5]

def coherence_general(rho, rho_crit, gamma):
    """General form: C = tanh(γ × log(ρ/ρ_crit + 1))"""
    return math.tanh(gamma * math.log(rho / rho_crit + 1))

def test_mapping(name, rho_func, gamma_func, rho_crit_candidates):
    """Test a specific ρ mapping"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")

    best_rmse = float('inf')
    best_params = None

    for rho_crit in rho_crit_candidates:
        predictions = []
        for n in N_corr:
            rho = rho_func(n)
            gamma = gamma_func(n)
            c_pred = coherence_general(rho, rho_crit, gamma)
            predictions.append(c_pred)

        # Calculate RMSE
        rmse = math.sqrt(sum((p - o)**2 for p, o in zip(predictions, C_observed)) / len(predictions))

        if rmse < best_rmse:
            best_rmse = rmse
            best_params = (rho_crit, predictions)

    rho_crit_best, preds_best = best_params
    print(f"Best ρ_crit = {rho_crit_best}, RMSE = {best_rmse:.4f}\n")
    print(f"{'Session':<8} {'N_corr':<8} {'C_obs':<10} {'C_pred':<10} {'Error':<10}")
    print("-" * 55)
    for i, session in enumerate(sessions):
        error = C_observed[i] - preds_best[i]
        print(f"{session:<8} {N_corr[i]:<8.1f} {C_observed[i]:<10.2f} "
              f"{preds_best[i]:<10.3f} {error:<10.3f}")

    # Check C(N=4)
    rho_at_4 = rho_func(4.0)
    gamma_at_4 = gamma_func(4.0)
    c_at_4 = coherence_general(rho_at_4, rho_crit_best, gamma_at_4)
    print(f"\nC(N_corr=4) = {c_at_4:.3f} (target: 0.500)")

    return best_rmse, rho_crit_best

# Test different mappings
print("="*70)
print("REFINED PREDICTION 4 TEST: Finding Optimal ρ Mapping")
print("="*70)

results = {}

# Mapping 1: Original (ρ = N_corr, γ = 2/√N)
results['Original'] = test_mapping(
    "ρ = N_corr, γ = 2/√N_corr",
    lambda n: n,
    lambda n: 2.0 / math.sqrt(n),
    [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
)

# Mapping 2: Square root density (ρ = √N_corr)
results['Sqrt'] = test_mapping(
    "ρ = √N_corr, γ = 2/√N_corr",
    lambda n: math.sqrt(n),
    lambda n: 2.0 / math.sqrt(n),
    [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
)

# Mapping 3: Quadratic density (ρ = N_corr²)
results['Quadratic'] = test_mapping(
    "ρ = N_corr², γ = 2/√N_corr",
    lambda n: n**2,
    lambda n: 2.0 / math.sqrt(n),
    [2, 5, 10, 15, 20, 25, 30]
)

# Mapping 4: Scaled linear (ρ = N_corr/2)
results['Half'] = test_mapping(
    "ρ = N_corr/2, γ = 2/√N_corr",
    lambda n: n / 2.0,
    lambda n: 2.0 / math.sqrt(n),
    [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
)

# Mapping 5: What if γ is different? (constant γ)
results['ConstGamma'] = test_mapping(
    "ρ = N_corr, γ = 1.0 (constant)",
    lambda n: n,
    lambda n: 1.0,
    [1, 2, 3, 4, 5, 6, 7, 8]
)

# Mapping 6: Linear combination (ρ = (N_corr - 1))
results['Shifted'] = test_mapping(
    "ρ = (N_corr - 1), γ = 2/√N_corr",
    lambda n: n - 1,
    lambda n: 2.0 / math.sqrt(n),
    [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
)

# Summary
print("\n" + "="*70)
print("SUMMARY: Best Mapping")
print("="*70)

best_overall = min(results.items(), key=lambda x: x[1][0])
print(f"\nBest fit: {best_overall[0]}")
print(f"RMSE = {best_overall[1][0]:.4f}")
print(f"ρ_crit = {best_overall[1][1]}")

if best_overall[1][0] < 0.1:
    print("\n✅ EXCELLENT FIT - Physical equation validates at cognitive scale!")
elif best_overall[1][0] < 0.15:
    print("\n⚠️  GOOD FIT - Physical equation approximately holds")
else:
    print("\n❌ POOR FIT - Physical equation may not directly apply")

# Final insight
print("\n" + "="*70)
print("INTERPRETATION")
print("="*70)
print("\nThe systematic overprediction suggests:")
print("1. Physical C(ρ) form may need cognitive-scale modification")
print("2. γ = 2/√N_corr might not be exact at cognitive scale")
print("3. Additional factors (attention, energy, etc.) may suppress coherence")
print("4. Or N_corr → ρ mapping requires transformation")
print("\nAlternative: The equation works but with different parameters")
print("than simple N_corr identity would suggest.")
