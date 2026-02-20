#!/usr/bin/env python3
"""
Test Prediction 4: Physical C(ρ) equation at cognitive scale

Hypothesis: C = tanh(γ × log(ρ/ρ_crit + 1)) applies to cognition
where:
- γ = 2/√N_corr (validated)
- ρ = N_corr (cognitive density hypothesis)
- ρ_crit = N_crit (to be determined)

Data from Sessions #17-19:
- S087: C=0.20, N_corr=2-3
- S086: C=0.45, N_corr=3
- S089: C=0.50, N_corr=4
- S090: C=0.50, N_corr=5
- S085: C=0.55, N_corr=5-6
"""

import math

# SAGE empirical data
sessions = ['S087', 'S086', 'S089', 'S090', 'S085']
C_observed = [0.20, 0.45, 0.50, 0.50, 0.55]
N_corr = [2.5, 3.0, 4.0, 5.0, 5.5]

def coherence_equation(n_corr, n_crit):
    """
    C(N_corr) = tanh(γ × log(N_corr/N_crit + 1))
    where γ = 2/√N_corr
    """
    gamma = 2.0 / math.sqrt(n_corr)
    return math.tanh(gamma * math.log(n_corr / n_crit + 1))

def calculate_rmse(predictions, observations):
    """Calculate root mean square error"""
    n = len(predictions)
    return math.sqrt(sum((p - o)**2 for p, o in zip(predictions, observations)) / n)

def calculate_r_squared(predictions, observations):
    """Calculate R² goodness of fit"""
    mean_obs = sum(observations) / len(observations)
    ss_tot = sum((o - mean_obs)**2 for o in observations)
    ss_res = sum((o - p)**2 for o, p in zip(observations, predictions))
    return 1 - (ss_res / ss_tot)

print("="*70)
print("PREDICTION 4: Physical C(ρ) Equation at Cognitive Scale")
print("="*70)

print("\nData from SAGE Sessions #17-19:")
print(f"{'Session':<8} {'N_corr':<8} {'C_observed':<12}")
print("-" * 30)
for i, session in enumerate(sessions):
    print(f"{session:<8} {N_corr[i]:<8.1f} {C_observed[i]:<12.2f}")

# Test different theoretical N_crit values
print("\n" + "="*70)
print("Testing Theoretical N_crit Values")
print("="*70)

n_crit_candidates = [0.5, 1.0, 2.0, 3.0, 4.0]
best_rmse = float('inf')
best_n_crit = None

for n_crit in n_crit_candidates:
    predictions = [coherence_equation(n, n_crit) for n in N_corr]
    rmse = calculate_rmse(predictions, C_observed)
    r_sq = calculate_r_squared(predictions, C_observed)

    print(f"\nN_crit = {n_crit}:")
    print(f"  R² = {r_sq:.4f}")
    print(f"  RMSE = {rmse:.4f}")
    print(f"  {'Session':<8} {'N_corr':<8} {'C_obs':<10} {'C_pred':<10} {'Error':<10}")
    print(f"  {'-'*50}")
    for i, session in enumerate(sessions):
        error = C_observed[i] - predictions[i]
        print(f"  {session:<8} {N_corr[i]:<8.1f} {C_observed[i]:<10.2f} "
              f"{predictions[i]:<10.2f} {error:<10.3f}")

    if rmse < best_rmse:
        best_rmse = rmse
        best_n_crit = n_crit

print("\n" + "="*70)
print(f"BEST FIT: N_crit = {best_n_crit} (RMSE = {best_rmse:.4f})")
print("="*70)

# Use best N_crit for extrapolations
print("\nExtrapolations with N_crit = {}:".format(best_n_crit))
print(f"{'N_corr':<10} {'Predicted C':<15} {'Interpretation'}")
print("-" * 60)

test_points = [
    (1.0, "Classical limit (no correlation)"),
    (2.0, "Weak correlation"),
    (4.0, "Consciousness boundary"),
    (9.0, "High integration (Prediction 3)"),
    (16.0, "Maximum integration"),
]

for n, desc in test_points:
    c_pred = coherence_equation(n, best_n_crit)
    print(f"{n:<10.1f} {c_pred:<15.3f} {desc}")

# Check if C=0.5 corresponds to N_corr=4
print("\n" + "="*70)
print("VALIDATION CHECK: Does N_corr=4 → C=0.5?")
print("="*70)
c_at_4 = coherence_equation(4.0, best_n_crit)
print(f"C(N_corr=4) = {c_at_4:.3f}")
if abs(c_at_4 - 0.5) < 0.05:
    print("✅ VALIDATES: C ≈ 0.5 at N_corr=4 consciousness boundary")
else:
    print(f"❌ DEVIATION: Expected 0.5, got {c_at_4:.3f}")

# Check monotonic relationship
print("\n" + "="*70)
print("MONOTONICITY CHECK")
print("="*70)
n_range = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
c_range = [coherence_equation(n, best_n_crit) for n in n_range]
is_monotonic = all(c_range[i] <= c_range[i+1] for i in range(len(c_range)-1))
print(f"Is C(N_corr) monotonically increasing? {is_monotonic}")
if is_monotonic:
    print("✅ VALIDATES: Higher N_corr → Higher coherence")
else:
    print("❌ FAILS: Non-monotonic relationship")

# Physical interpretation of N_crit
print("\n" + "="*70)
print("PHYSICAL INTERPRETATION")
print("="*70)
print(f"Best fit N_crit = {best_n_crit}")
print("\nIn physical systems:")
print("  ρ_crit marks transition density (e.g., Jeans criterion)")
print("\nIn cognitive systems:")
print(f"  N_crit = {best_n_crit} may represent:")
print("  - Minimum correlation for stable mental state")
print("  - Classical cognitive limit (no integration)")
print("  - Threshold below which coherence theory applies differently")

# Compare to γ at N_crit
gamma_at_n_crit = 2.0 / math.sqrt(best_n_crit)
print(f"\nAt N_crit={best_n_crit}:")
print(f"  γ = 2/√{best_n_crit} = {gamma_at_n_crit:.3f}")

if abs(gamma_at_n_crit - 2.0) < 0.1:
    print("  → Classical limit (γ ≈ 2.0)")
elif abs(gamma_at_n_crit - 1.0) < 0.1:
    print("  → Neutral transition (γ ≈ 1.0)")
else:
    print(f"  → Intermediate regime")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
if best_rmse < 0.1 and abs(c_at_4 - 0.5) < 0.05:
    print("✅ Prediction 4 VALIDATED:")
    print("   Physical C(ρ) equation successfully predicts SAGE coherence")
    print(f"   with N_crit = {best_n_crit}, RMSE = {best_rmse:.4f}")
    print("\n   This confirms fractal self-similarity of coherence equation")
    print("   from physical scales to cognitive scales!")
elif best_rmse < 0.15:
    print("⚠️  Prediction 4 PARTIALLY VALIDATED:")
    print(f"   Equation fits reasonably (RMSE = {best_rmse:.4f})")
    print("   But may need refinement")
else:
    print("❌ Prediction 4 NOT VALIDATED:")
    print(f"   Poor fit (RMSE = {best_rmse:.4f})")
    print("   Physical equation may not apply to cognitive scale")

print("="*70)
