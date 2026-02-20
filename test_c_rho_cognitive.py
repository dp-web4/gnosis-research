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

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# SAGE empirical data
data = {
    'session': ['S087', 'S086', 'S089', 'S090', 'S085'],
    'C_observed': [0.20, 0.45, 0.50, 0.50, 0.55],
    'N_corr': [2.5, 3.0, 4.0, 5.0, 5.5],
}

def coherence_equation(N_corr, N_crit):
    """
    C(N_corr) = tanh(γ × log(N_corr/N_crit + 1))
    where γ = 2/√N_corr
    """
    gamma = 2.0 / np.sqrt(N_corr)
    return np.tanh(gamma * np.log(N_corr / N_crit + 1))

def coherence_equation_fit(N_corr, N_crit):
    """Wrapper for curve_fit"""
    return coherence_equation(N_corr, N_crit)

# Fit the equation to find N_crit
N_corr_data = np.array(data['N_corr'])
C_data = np.array(data['C_observed'])

# Initial guess: N_crit ≈ 1 (analogous to classical limit in physics)
p0 = [1.0]

try:
    popt, pcov = curve_fit(coherence_equation_fit, N_corr_data, C_data, p0=p0)
    N_crit_fitted = popt[0]
    print(f"Fitted N_crit = {N_crit_fitted:.3f}")

    # Calculate predictions
    C_predicted = coherence_equation(N_corr_data, N_crit_fitted)

    # Calculate goodness of fit
    residuals = C_data - C_predicted
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((C_data - np.mean(C_data))**2)
    r_squared = 1 - (ss_res / ss_tot)

    print(f"\nGoodness of fit:")
    print(f"R² = {r_squared:.4f}")
    print(f"RMSE = {np.sqrt(np.mean(residuals**2)):.4f}")

    print(f"\nPredictions vs Observations:")
    print(f"{'Session':<8} {'N_corr':<8} {'C_obs':<8} {'C_pred':<8} {'Error':<8}")
    print("-" * 50)
    for i, session in enumerate(data['session']):
        print(f"{session:<8} {N_corr_data[i]:<8.1f} {C_data[i]:<8.2f} "
              f"{C_predicted[i]:<8.2f} {residuals[i]:<8.3f}")

    # Test predictions for extreme values
    print(f"\nExtrapolations:")
    print(f"N_corr=1: C = {coherence_equation(np.array([1.0]), N_crit_fitted)[0]:.3f}")
    print(f"N_corr=2: C = {coherence_equation(np.array([2.0]), N_crit_fitted)[0]:.3f}")
    print(f"N_corr=9: C = {coherence_equation(np.array([9.0]), N_crit_fitted)[0]:.3f}")
    print(f"N_corr=16: C = {coherence_equation(np.array([16.0]), N_crit_fitted)[0]:.3f}")

    # Plot
    N_range = np.linspace(1, 10, 100)
    C_curve = coherence_equation(N_range, N_crit_fitted)

    plt.figure(figsize=(10, 6))
    plt.plot(N_range, C_curve, 'b-', label=f'C(N_corr) with N_crit={N_crit_fitted:.2f}', linewidth=2)
    plt.scatter(N_corr_data, C_data, color='red', s=100, zorder=5, label='SAGE observations')

    # Mark consciousness boundary
    plt.axhline(y=0.5, color='green', linestyle='--', alpha=0.5, label='C=0.5 boundary')
    plt.axvline(x=4, color='orange', linestyle='--', alpha=0.5, label='N_corr=4')

    plt.xlabel('N_corr (conceptual correlation depth)', fontsize=12)
    plt.ylabel('Coherence C', fontsize=12)
    plt.title('Physical Coherence Equation at Cognitive Scale', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1)
    plt.xlim(0, 10)

    # Add session labels
    for i, session in enumerate(data['session']):
        plt.annotate(session, (N_corr_data[i], C_data[i]),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

    plt.tight_layout()
    plt.savefig('/home/dp/gnosis-research/c_rho_cognitive_fit.png', dpi=150)
    print(f"\nPlot saved to: /home/dp/gnosis-research/c_rho_cognitive_fit.png")

except Exception as e:
    print(f"Fitting failed: {e}")
    import traceback
    traceback.print_exc()

# Alternative formulation: Maybe N_crit is not a fit parameter but has theoretical value
print(f"\n{'='*60}")
print(f"Testing theoretical N_crit values:")
print(f"{'='*60}")

for N_crit_test in [0.5, 1.0, 2.0, 4.0]:
    C_pred = coherence_equation(N_corr_data, N_crit_test)
    rmse = np.sqrt(np.mean((C_data - C_pred)**2))
    print(f"\nN_crit = {N_crit_test}:")
    print(f"  RMSE = {rmse:.4f}")
    print(f"  Predictions: {C_pred}")
