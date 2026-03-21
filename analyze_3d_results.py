#!/usr/bin/env python3
"""
Analyze 3D synchronous CA results to understand why oscillation isn't occurring.
"""

import json
import numpy as np

def load_results(filename):
    """Load results JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def analyze_dynamics(results, title):
    """Analyze energy dynamics."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")

    config = results['config']
    print(f"Grid: {config['size']}³ = {config['size']**3:,} cells")
    print(f"Parameters: A={config['amplitude']:.2f}, σ={config['sigma']:.1f}, "
          f"k={config['k']:.3f}, n={config['n']}")
    print(f"Steps: {config['n_steps']:,}")
    print()

    # Energy conservation
    E_initial = results['initial']['total_energy']
    E_final = results['final']['total_energy']
    retention = 100 * E_final / E_initial

    print(f"Energy:")
    print(f"  Initial: {E_initial:.2f}")
    print(f"  Final: {E_final:.2f}")
    print(f"  Retention: {retention:.1f}%")

    if retention > 100.5:
        print("  ⚠️  Energy INCREASING (non-physical)")
    elif retention < 99.5:
        print("  ⚠️  Energy DECREASING (dissipation)")
    else:
        print("  ✓ Energy conserved")
    print()

    # Saturation
    sat_initial = results['initial']['saturated_cells']
    sat_final = results['final']['saturated_cells']
    sat_frac = results['final']['saturated_fraction']

    print(f"Saturation:")
    print(f"  Initial: {sat_initial:.0f} cells")
    print(f"  Final: {sat_final} cells ({100*sat_frac:.2f}%)")
    print(f"  Change: {sat_final - sat_initial:.0f} cells")
    print()

    # Oscillation
    osc_total = results['oscillation']['total_energy']['detected']
    osc_cavity = results['oscillation']['cavity_energy']['detected']

    print(f"Oscillation:")
    print(f"  Total energy: {'YES' if osc_total else 'NO'}")
    if osc_total:
        print(f"    Period: {results['oscillation']['total_energy']['period']:.1f} steps")
    else:
        peak = results['oscillation']['total_energy']['autocorr_peak']
        print(f"    Max autocorr: {peak:.4f} (threshold: 0.5)")

    print(f"  Cavity energy: {'YES' if osc_cavity else 'NO'}")
    if osc_cavity:
        print(f"    Period: {results['oscillation']['cavity_energy']['period']:.1f} steps")
    else:
        peak = results['oscillation']['cavity_energy']['autocorr_peak']
        print(f"    Max autocorr: {peak:.4f} (threshold: 0.5)")

    print()

    return osc_total or osc_cavity


def main():
    """Analyze both 32³ and 64³ results."""

    # Load results
    try:
        results_32 = load_results('intent_grid_3d_results_32.json')
        has_32 = True
    except FileNotFoundError:
        has_32 = False

    try:
        results_64 = load_results('intent_grid_3d_results_64.json')
        has_64 = True
    except FileNotFoundError:
        has_64 = False

    if not (has_32 or has_64):
        print("No results files found")
        return

    # Analyze
    oscillations = []

    if has_32:
        osc_32 = analyze_dynamics(results_32, "32³ GRID ANALYSIS")
        oscillations.append(("32³", osc_32))

    if has_64:
        osc_64 = analyze_dynamics(results_64, "64³ GRID ANALYSIS")
        oscillations.append(("64³", osc_64))

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    for grid_size, has_osc in oscillations:
        status = "✅ OSCILLATES" if has_osc else "❌ NO OSCILLATION"
        print(f"  {grid_size}: {status}")

    print()

    if not any(has_osc for _, has_osc in oscillations):
        print("CONCLUSION:")
        print()
        print("  Zero oscillations detected across all tested 3D grid sizes.")
        print()
        print("  This suggests:")
        print("  1. The directive's hypothesis may be wrong")
        print("     (3D + synchronous not sufficient)")
        print("  2. Parameters may need tuning")
        print("  3. Physics gap remains (as in Sessions #18-25)")
        print()
        print("  Observations:")
        if has_32 and has_64:
            E_gain_32 = 100 * results_32['final']['total_energy'] / results_32['initial']['total_energy']
            E_gain_64 = 100 * results_64['final']['total_energy'] / results_64['initial']['total_energy']
            print(f"  - Energy increasing: 32³ = {E_gain_32:.1f}%, 64³ = {E_gain_64:.1f}%")
            print("    → May indicate numerical instability or wrong physics")

        print("  - Saturation cavities form (~2% of grid)")
        print("  - But no temporal oscillation in cavity energy")
        print("  - Same behavior as 1D (Sessions #18-25)")
        print()
        print("  Next steps:")
        print("  - Check if 128³ changes anything (2M cells, slower)")
        print("  - Or: recognize that dimensionality isn't the issue")
        print("  - Return to physics: why doesn't saturation + confinement → oscillation?")


if __name__ == "__main__":
    main()
