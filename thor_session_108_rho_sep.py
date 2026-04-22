#!/usr/bin/env python3
"""Side finding for S108: does ρ_sig(κ_p, κ_C) factorize as f(κ_p)·g(κ_C)? (S107-P4)

Uses the S107 ridge grid (3 κ_p × 5 κ_C at ratio 0.8).
"""
import json
import numpy as np
import sys
sys.path.insert(0, '.')
from thor_session_108_analyze import cell_stats_from_results_file, rho_sig_from_summary


def build_grid():
    """Return ρ_sig_st grid: rows=κ_p, cols=κ_C, at ratio 0.8."""
    kp_list = [0.15, 0.30, 0.50]
    kC_list = [0.00, 0.05, 0.15, 0.30, 0.50]
    # Map (kp, kC) -> (path, label) for each cell.
    recipe = {
        (0.15, 0.00): ('thor_session_107_ridge_map_results.json', 'kp015_kC000'),
        (0.15, 0.05): ('thor_session_107_ridge_map_results.json', 'kp015_kC005'),
        (0.15, 0.15): ('thor_session_105_kappa_strength_results.json', 'r08_k015'),
        (0.15, 0.30): ('thor_session_107_ridge_map_results.json', 'kp015_kC030'),
        (0.15, 0.50): ('thor_session_107_ridge_map_results.json', 'kp015_kC050'),

        (0.30, 0.00): ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC000'),
        (0.30, 0.05): ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC005'),
        (0.30, 0.15): ('thor_session_105_kappa_strength_results.json', 'r08_k030'),
        (0.30, 0.30): ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC030'),
        (0.30, 0.50): ('thor_session_106_kappa_c_channel_results.json', 'kp030_kC050'),

        (0.50, 0.00): ('thor_session_107_ridge_map_results.json', 'kp050_kC000'),
        (0.50, 0.05): ('thor_session_107_ridge_map_results.json', 'kp050_kC005'),
        (0.50, 0.15): ('thor_session_105_kappa_strength_results.json', 'r08_k050'),
        (0.50, 0.30): ('thor_session_107_ridge_map_results.json', 'kp050_kC030'),
        (0.50, 0.50): ('thor_session_107_ridge_map_results.json', 'kp050_kC050'),
    }
    rho_grid = np.zeros((len(kp_list), len(kC_list)))
    mu_grid = np.zeros_like(rho_grid)
    N_grid = np.zeros_like(rho_grid)
    for i, kp in enumerate(kp_list):
        for j, kC in enumerate(kC_list):
            path, label = recipe[(kp, kC)]
            c = cell_stats_from_results_file(path, label)
            rho_grid[i, j] = rho_sig_from_summary(c)
            mu_grid[i, j]  = c['mu_st']
            N_grid[i, j]   = c['N_sw_mean']
    return kp_list, kC_list, rho_grid, mu_grid, N_grid


def test_factorization(rho_grid):
    """Least-squares rank-1 approximation: rho ≈ f_kp[i] * g_kC[j].

    Compute via log-domain additive model: log(rho) = log(f) + log(g) + ε.
    Then check residual.
    """
    # Avoid log(0): add small floor.
    eps = 1e-6
    L = np.log(rho_grid + eps)
    # Least-squares: L[i,j] = a[i] + b[j] + c (anchor by forcing sum(a)=sum(b)=0).
    I, J = L.shape
    mean_total = L.mean()
    a = L.mean(axis=1) - mean_total
    b = L.mean(axis=0) - mean_total
    L_hat = mean_total + a[:, None] + b[None, :]
    residual = L - L_hat
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((L - mean_total)**2))
    r2_log = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0

    # In linear domain: fit rho ~ f_kp · g_kC with a small additive model.
    rho_hat = np.exp(L_hat)
    lin_ss_res = float(np.sum((rho_grid - rho_hat)**2))
    lin_ss_tot = float(np.sum((rho_grid - rho_grid.mean())**2))
    r2_lin = 1 - lin_ss_res / lin_ss_tot if lin_ss_tot > 0 else 1.0

    return {
        'L': L, 'L_hat': L_hat, 'residual': residual,
        'a_kp': a, 'b_kC': b, 'c_const': mean_total,
        'r2_log': r2_log, 'r2_linear': r2_lin,
        'residual_max_abs': float(np.max(np.abs(residual))),
    }


def main():
    kp_list, kC_list, rho, mu, N = build_grid()

    print("\nρ_sig_st grid (rows = κ_p, cols = κ_C):")
    print(f"{'κ_p\\κ_C':<8}", *[f"{kC:.2f}" for kC in kC_list], sep="   ")
    for i, kp in enumerate(kp_list):
        print(f"{kp:<8.2f}", *[f"{rho[i,j]:.4f}" for j in range(len(kC_list))], sep="   ")

    print("\nN_sw grid (rows = κ_p, cols = κ_C):")
    print(f"{'κ_p\\κ_C':<8}", *[f"{kC:.2f}" for kC in kC_list], sep="   ")
    for i, kp in enumerate(kp_list):
        print(f"{kp:<8.2f}", *[f"{N[i,j]:.0f}" for j in range(len(kC_list))], sep="    ")

    # Factorization test
    fit = test_factorization(rho)
    print(f"\nRank-1 factorization (log-additive model):")
    print(f"  R² on log(ρ):    {fit['r2_log']:.3f}")
    print(f"  R² on linear ρ:  {fit['r2_linear']:.3f}")
    print(f"  max|residual| on log scale: {fit['residual_max_abs']:.3f}")
    print(f"  a[κ_p]:  {dict(zip(kp_list, [round(v,3) for v in fit['a_kp']]))}")
    print(f"  b[κ_C]:  {dict(zip(kC_list, [round(v,3) for v in fit['b_kC']]))}")

    print("\nρ_sig row-ratios (test: should be κ_C-independent if separable):")
    print(f"  ρ(κ_p=0.50) / ρ(κ_p=0.30):")
    for j, kC in enumerate(kC_list):
        r = rho[2, j] / rho[1, j] if rho[1, j] > 0 else np.nan
        print(f"    κ_C={kC:.2f}:  {r:.3f}")
    print(f"  ρ(κ_p=0.15) / ρ(κ_p=0.30):")
    for j, kC in enumerate(kC_list):
        r = rho[0, j] / rho[1, j] if rho[1, j] > 0 else np.nan
        print(f"    κ_C={kC:.2f}:  {r:.3f}")

    out = {
        'kp_grid': kp_list, 'kC_grid': kC_list,
        'rho_sig_st': rho.tolist(),
        'N_sw': N.tolist(),
        'mu_st': mu.tolist(),
        'factorization_fit': {
            'r2_log':   fit['r2_log'],
            'r2_linear': fit['r2_linear'],
            'residual_max_abs': fit['residual_max_abs'],
            'a_kp':  fit['a_kp'].tolist(),
            'b_kC':  fit['b_kC'].tolist(),
            'c_const': fit['c_const'],
        },
        'interpretation': (
            "If ρ_sig = f(κ_p)·g(κ_C) then log(ρ) is rank-1 + noise. "
            "High R² indicates separability; low R² or large residual "
            "indicates κ_p·κ_C interaction beyond pure multiplication."
        ),
    }
    with open('thor_session_108_rho_separability.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nWrote thor_session_108_rho_separability.json")


if __name__ == '__main__':
    main()
