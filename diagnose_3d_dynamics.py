#!/usr/bin/env python3
"""
Quick diagnostic: Run 3D CA and track what's actually happening to the energy.
"""

import torch
import numpy as np
from intent_grid_3d import IntentGrid3D

def run_diagnostic():
    """Run short 3D sim with detailed diagnostics."""
    print("="*80)
    print("3D CA DIAGNOSTIC")
    print("="*80)
    print()

    # Small grid for speed
    size = 32
    amplitude = 1.5
    sigma = 6.0
    k = 0.1
    n = 4
    n_steps = 1000

    print(f"Grid: {size}³")
    print(f"Parameters: A={amplitude:.2f}, σ={sigma:.1f}, k={k:.3f}, n={n}")
    print(f"Steps: {n_steps}")
    print()

    # Initialize
    grid = IntentGrid3D(size=size, device='cuda')
    grid.initialize_gaussian_pulse(amplitude=amplitude, sigma=sigma)

    print("\nInitial state:")
    E0 = grid.measure_total_energy()
    I_max_init = torch.max(grid.I).item()
    I_mean_init = torch.mean(grid.I).item()
    I_std_init = torch.std(grid.I).item()

    print(f"  E_total: {E0:.2f}")
    print(f"  I_max: {I_max_init:.4f}")
    print(f"  I_mean: {I_mean_init:.4f}")
    print(f"  I_std: {I_std_init:.4f}")

    # Track how energy spreads vs concentrates
    print("\nEvolution snapshots:")
    print(f"{'Step':>6} {'E_total':>10} {'I_max':>8} {'I_mean':>8} {'I_std':>8} {'%>0.5':>6}")
    print("-"*60)

    for step in range(n_steps):
        grid.step(k=k, n=n)

        if step % 100 == 0 or step == n_steps - 1:
            E = grid.measure_total_energy()
            I_max = torch.max(grid.I).item()
            I_mean = torch.mean(grid.I).item()
            I_std = torch.std(grid.I).item()
            frac_high = (grid.I > 0.5).sum().item() / (size**3) * 100

            print(f"{step:6d} {E:10.2f} {I_max:8.4f} {I_mean:8.4f} {I_std:8.4f} {frac_high:6.2f}%")

    print()

    # Analyze final distribution
    print("Final distribution analysis:")
    I_final = grid.I.cpu().numpy()

    percentiles = [0, 25, 50, 75, 90, 95, 99, 100]
    values = np.percentile(I_final, percentiles)

    print(f"  Percentiles:")
    for p, v in zip(percentiles, values):
        print(f"    {p:3d}%: {v:.6f}")

    print()

    # Check for structure vs uniform spread
    above_half = (grid.I > 0.5).sum().item()
    above_one = (grid.I > 1.0).sum().item()

    print(f"  Cells above I=0.5: {above_half} ({100*above_half/(size**3):.2f}%)")
    print(f"  Cells above I=1.0: {above_one} ({100*above_one/(size**3):.2f}%)")
    print()

    # Interpretation
    retention = grid.measure_total_energy() / E0

    if I_max < 0.1:
        print("INTERPRETATION: Energy dispersed uniformly (thermalized)")
    elif I_std / I_mean < 0.5:
        print("INTERPRETATION: Energy spread thin across grid")
    elif above_one > 0:
        print("INTERPRETATION: Some concentration remains (possible cavity)")
    else:
        print("INTERPRETATION: Energy partially concentrated but below saturation")

    print(f"  Energy retention: {100*retention:.1f}%")


if __name__ == "__main__":
    run_diagnostic()
