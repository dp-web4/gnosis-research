#!/usr/bin/env python3
"""
3D Synchronous Intent Grid - Phase 1

Implements the 3D parallel cellular automaton on GPU as specified in
Research/proposals/3D_parallel_grid_and_MRH_abstraction.md

Key differences from Sessions #18-25:
- 3D grid (not 1D) - can form closed cavities
- Synchronous update (not sequential) - preserves isotropy
- GPU parallel (not CPU serial) - scales to millions of cells

Physics: Each cell computes simultaneously based on neighbors
I_next[x,y,z] = I[x,y,z] + k · Σ_neighbors (I[n] - I[x,y,z]) · R(I[n])

Author: Thor autonomous session
Date: 2026-03-21
Directive: 3D_parallel_grid_and_MRH_abstraction.md
"""

import torch
import numpy as np
import json
from typing import Tuple, Optional, List
import time


class IntentGrid3D:
    """3D synchronous cellular automaton on GPU."""

    def __init__(self, size: int = 32, I_max: float = 1.0, dt: float = 0.01, device: str = 'cuda'):
        """
        Initialize 3D grid.

        Args:
            size: Grid dimension (size × size × size)
            I_max: Maximum intent density (saturation threshold)
            dt: Timestep size
            device: 'cuda' or 'cpu'
        """
        self.size = size
        self.I_max = I_max
        self.dt = dt
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')

        # Create grid (synchronous double-buffer)
        self.I = torch.zeros((size, size, size), device=self.device, dtype=torch.float32)

        print(f"Initialized {size}³ grid on {self.device}")
        print(f"Total cells: {size**3:,}")
        print(f"Memory: ~{(size**3 * 4) / 1024**2:.2f} MB per buffer")

    def R(self, I: torch.Tensor, n: int = 4) -> torch.Tensor:
        """
        Saturation resistance function.

        R(I) = [1 - (I/I_max)^n]

        As I → I_max, R → 0 (saturation boundary forms).
        """
        ratio = torch.clamp(I / self.I_max, 0, 1)
        return 1 - ratio**n

    def initialize_gaussian_pulse(self, amplitude: float, sigma: float,
                                   center: Optional[Tuple[int, int, int]] = None):
        """
        Initialize with 3D Gaussian energy pulse.

        Args:
            amplitude: Pulse amplitude (relative to I_max)
            sigma: Pulse width (cells)
            center: (x, y, z) center position (default: grid center)
        """
        if center is None:
            center = (self.size // 2, self.size // 2, self.size // 2)

        # Create coordinate grids
        x = torch.arange(self.size, device=self.device, dtype=torch.float32)
        y = torch.arange(self.size, device=self.device, dtype=torch.float32)
        z = torch.arange(self.size, device=self.device, dtype=torch.float32)

        # Meshgrid for 3D coordinates
        X, Y, Z = torch.meshgrid(x, y, z, indexing='ij')

        # 3D Gaussian
        cx, cy, cz = center
        r_squared = (X - cx)**2 + (Y - cy)**2 + (Z - cz)**2
        self.I = amplitude * self.I_max * torch.exp(-r_squared / (2 * sigma**2))

        total_energy = torch.sum(self.I).item()
        print(f"Initialized Gaussian pulse: A={amplitude:.2f}, σ={sigma:.1f}, center={center}")
        print(f"Total energy: {total_energy:.2f}")

    def step(self, k: float, n: int = 4):
        """
        Single synchronous timestep.

        ALL cells update simultaneously based on current state.
        Uses double-buffering: read from self.I, write to I_next, then swap.

        Transfer rule: I_next = I + k · Σ_neighbors (I_n - I) · R(I_n)

        Args:
            k: Coupling strength
            n: Saturation exponent
        """
        # For synchronous update, need to compute:
        # Σ_neighbors (I[neighbor] - I[center]) · R(I[neighbor])
        #
        # Can't use simple convolution because R(I) is nonlinear.
        # Need to apply R to each neighbor's value separately.

        # Pad grid for periodic boundary
        I_padded = torch.nn.functional.pad(
            self.I.unsqueeze(0).unsqueeze(0),
            (1, 1, 1, 1, 1, 1),
            mode='circular'
        ).squeeze(0).squeeze(0)

        # Extract 6 neighbors for each cell
        # Neighbors at offsets: (-1,0,0), (+1,0,0), (0,-1,0), (0,+1,0), (0,0,-1), (0,0,+1)
        I_xm = I_padded[:-2, 1:-1, 1:-1]  # x-1
        I_xp = I_padded[2:,  1:-1, 1:-1]  # x+1
        I_ym = I_padded[1:-1, :-2, 1:-1]  # y-1
        I_yp = I_padded[1:-1, 2:,  1:-1]  # y+1
        I_zm = I_padded[1:-1, 1:-1, :-2]  # z-1
        I_zp = I_padded[1:-1, 1:-1, 2:]   # z+1

        # Apply R to each neighbor
        R_xm = self.R(I_xm, n)
        R_xp = self.R(I_xp, n)
        R_ym = self.R(I_ym, n)
        R_yp = self.R(I_yp, n)
        R_zm = self.R(I_zm, n)
        R_zp = self.R(I_zp, n)

        # Compute contribution from each neighbor: (I_n - I_center) · R(I_n)
        delta_I = (
            (I_xm - self.I) * R_xm +
            (I_xp - self.I) * R_xp +
            (I_ym - self.I) * R_ym +
            (I_yp - self.I) * R_yp +
            (I_zm - self.I) * R_zm +
            (I_zp - self.I) * R_zp
        )

        # Update rule
        I_next = self.I + self.dt * k * delta_I

        # Enforce physical constraints
        I_next = torch.clamp(I_next, 0, None)  # No negative intent

        # Swap buffers (synchronous update complete)
        self.I = I_next

    def detect_saturation_surface(self, threshold: float = 0.01, n: int = 4) -> Tuple[int, float]:
        """
        Detect cells where saturation occurs (R < threshold).

        Returns:
            count: Number of saturated cells
            fraction: Fraction of total grid
        """
        R_grid = self.R(self.I, n)
        saturated = (R_grid < threshold).sum().item()
        fraction = saturated / (self.size ** 3)
        return int(saturated), fraction

    def measure_total_energy(self) -> float:
        """Total energy in grid."""
        return torch.sum(self.I).item()

    def measure_cavity_energy(self, threshold: float = 0.01, n: int = 4) -> Optional[float]:
        """
        Measure energy inside detected saturation boundary.

        This is approximate - a full cavity detection would require
        connected component analysis in 3D.
        """
        R_grid = self.R(self.I, n)
        inside_cavity = R_grid < threshold  # Saturated regions

        if inside_cavity.sum() > 0:
            # Energy in saturated regions
            cavity_energy = torch.sum(self.I[inside_cavity]).item()
            return cavity_energy
        return None

    def get_state_stats(self, n: int = 4) -> dict:
        """Get current grid statistics."""
        total_energy = self.measure_total_energy()
        max_I = torch.max(self.I).item()
        mean_I = torch.mean(self.I).item()
        saturated_count, saturated_frac = self.detect_saturation_surface(n=n)
        cavity_energy = self.measure_cavity_energy(n=n)

        return {
            'total_energy': total_energy,
            'max_I': max_I,
            'mean_I': mean_I,
            'saturated_cells': saturated_count,
            'saturated_fraction': saturated_frac,
            'cavity_energy': cavity_energy
        }


def detect_oscillation_3d(energy_history: List[float], min_period: int = 5,
                          max_period: int = 500) -> Tuple[bool, Optional[float], float]:
    """
    Detect periodic oscillation via autocorrelation.

    Same method as 1D tests, but applied to 3D cavity energy.
    """
    if len(energy_history) < 2 * max_period:
        return False, None, 0.0

    # Use second half to avoid transients
    start = len(energy_history) // 2
    signal = np.array(energy_history[start:])

    # Center and normalize
    mean = np.mean(signal)
    signal_centered = signal - mean

    if np.std(signal_centered) < 1e-10:
        return False, None, 0.0

    # Autocorrelation
    autocorr = np.correlate(signal_centered, signal_centered, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]

    # Find peaks
    peaks = []
    for lag in range(min_period, min(len(autocorr), max_period)):
        if autocorr[lag] > 0.5:
            if lag > 0 and lag < len(autocorr) - 1:
                if autocorr[lag] > autocorr[lag-1] and autocorr[lag] > autocorr[lag+1]:
                    peaks.append((lag, autocorr[lag]))

    if not peaks:
        return False, None, np.max(autocorr[1:]) if len(autocorr) > 1 else 0.0

    best_peak = max(peaks, key=lambda p: p[1])
    period, corr = best_peak

    is_oscillating = corr > 0.7
    return is_oscillating, float(period) if is_oscillating else None, corr


def run_3d_simulation(size: int = 32, amplitude: float = 1.5, sigma: float = 6.0,
                      k: float = 0.1, n: int = 4, n_steps: int = 5000,
                      record_interval: int = 10) -> dict:
    """
    Run 3D synchronous CA simulation.

    Args:
        size: Grid size (size³ cells)
        amplitude: Initial pulse amplitude (× I_max)
        sigma: Pulse width (cells)
        k: Coupling strength
        n: Saturation exponent
        n_steps: Number of timesteps
        record_interval: Record state every N steps

    Returns:
        Dictionary with results
    """
    print("=" * 80)
    print(f"3D SYNCHRONOUS INTENT GRID SIMULATION")
    print("=" * 80)
    print(f"Grid: {size}³ = {size**3:,} cells")
    print(f"Parameters: A={amplitude:.2f}, σ={sigma:.1f}, k={k:.3f}, n={n}")
    print(f"Timesteps: {n_steps:,} (recording every {record_interval})")
    print()

    # Initialize
    grid = IntentGrid3D(size=size, device='cuda')
    grid.initialize_gaussian_pulse(amplitude=amplitude, sigma=sigma)

    # Storage
    energy_history = []
    cavity_energy_history = []
    saturated_fraction_history = []

    # Initial state
    stats = grid.get_state_stats(n=n)
    print(f"Initial state:")
    print(f"  Total energy: {stats['total_energy']:.2f}")
    print(f"  Max I: {stats['max_I']:.3f}")
    print(f"  Saturated: {stats['saturated_cells']} cells ({100*stats['saturated_fraction']:.2f}%)")
    print()

    # Evolution
    print("Running simulation...")
    start_time = time.time()

    for step in range(n_steps):
        grid.step(k=k, n=n)

        if step % record_interval == 0:
            stats = grid.get_state_stats(n=n)
            energy_history.append(stats['total_energy'])

            if stats['cavity_energy'] is not None:
                cavity_energy_history.append(stats['cavity_energy'])
            else:
                cavity_energy_history.append(0.0)

            saturated_fraction_history.append(stats['saturated_fraction'])

            if (step + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                steps_per_sec = (step + 1) / elapsed
                print(f"  Step {step+1}/{n_steps} ({100*(step+1)/n_steps:.1f}%) - "
                      f"{steps_per_sec:.1f} steps/sec - "
                      f"E={stats['total_energy']:.2f}, "
                      f"sat={100*stats['saturated_fraction']:.2f}%")

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f}s ({n_steps/elapsed:.1f} steps/sec)")
    print()

    # Final state
    final_stats = grid.get_state_stats(n=n)
    print("Final state:")
    print(f"  Total energy: {final_stats['total_energy']:.2f}")
    print(f"  Energy retention: {100*final_stats['total_energy']/energy_history[0]:.1f}%")
    print(f"  Saturated cells: {final_stats['saturated_cells']} ({100*final_stats['saturated_fraction']:.2f}%)")
    print()

    # Analyze oscillation
    print("Analyzing oscillations...")

    # Total energy oscillation
    is_osc_total, period_total, peak_total = detect_oscillation_3d(energy_history)
    print(f"  Total energy: {'OSCILLATING' if is_osc_total else 'NOT oscillating'}")
    if period_total:
        print(f"    Period: {period_total:.1f} steps")
        print(f"    Autocorr peak: {peak_total:.3f}")
    else:
        print(f"    Max autocorr: {peak_total:.3f}")

    # Cavity energy oscillation (if cavity detected)
    if any(e > 0 for e in cavity_energy_history):
        is_osc_cavity, period_cavity, peak_cavity = detect_oscillation_3d(cavity_energy_history)
        print(f"  Cavity energy: {'OSCILLATING' if is_osc_cavity else 'NOT oscillating'}")
        if period_cavity:
            print(f"    Period: {period_cavity:.1f} steps")
            print(f"    Autocorr peak: {peak_cavity:.3f}")
        else:
            print(f"    Max autocorr: {peak_cavity:.3f}")
    else:
        is_osc_cavity = False
        period_cavity = None
        peak_cavity = 0.0
        print(f"  Cavity energy: No cavity detected")

    print()

    # Results
    results = {
        'config': {
            'size': size,
            'amplitude': amplitude,
            'sigma': sigma,
            'k': k,
            'n': n,
            'n_steps': n_steps
        },
        'initial': {
            'total_energy': energy_history[0],
            'saturated_cells': saturated_fraction_history[0] * size**3
        },
        'final': final_stats,
        'oscillation': {
            'total_energy': {
                'detected': is_osc_total,
                'period': period_total,
                'autocorr_peak': peak_total
            },
            'cavity_energy': {
                'detected': is_osc_cavity,
                'period': period_cavity,
                'autocorr_peak': peak_cavity
            }
        },
        'history': {
            'energy': energy_history,
            'cavity_energy': cavity_energy_history,
            'saturated_fraction': saturated_fraction_history
        },
        'performance': {
            'elapsed_seconds': elapsed,
            'steps_per_second': n_steps / elapsed
        }
    }

    return results


def main():
    """Run 3D synchronous CA test - Phase 1."""
    print("=" * 80)
    print("3D SYNCHRONOUS INTENT GRID - PHASE 1")
    print("=" * 80)
    print()
    print("Directive: 3D_parallel_grid_and_MRH_abstraction.md")
    print()
    print("Testing whether 3D synchronous parallel CA can produce oscillations")
    print("that 1D sequential CA could not (Sessions #18-25: 0/808).")
    print()
    print("Key differences:")
    print("  - 3D geometry: Can form closed cavities with mode structure")
    print("  - Synchronous update: Preserves isotropy, all cells compute simultaneously")
    print("  - GPU parallel: Scales to millions of cells")
    print()

    # Phase 1: 64³ cavity search
    print("PHASE 1: 64³ Grid (Cavity Search)")
    print("-" * 80)
    results_64 = run_3d_simulation(
        size=64,
        amplitude=1.5,  # Above saturation threshold
        sigma=12.0,     # Pulse width (scaled with grid)
        k=0.1,          # Coupling
        n=4,            # Saturation sharpness
        n_steps=5000,
        record_interval=10
    )

    # Save results
    with open('intent_grid_3d_results_64.json', 'w') as f:
        # Convert to JSON-serializable
        json_results = {
            'config': results_64['config'],
            'initial': results_64['initial'],
            'final': results_64['final'],
            'oscillation': results_64['oscillation'],
            'performance': results_64['performance']
        }
        json.dump(json_results, f, indent=2)

    print(f"Results saved to: intent_grid_3d_results_64.json")
    print()

    # Verdict
    print("=" * 80)
    print("VERDICT (64³ Grid)")
    print("=" * 80)

    osc_total = results_64['oscillation']['total_energy']['detected']
    osc_cavity = results_64['oscillation']['cavity_energy']['detected']

    if osc_total or osc_cavity:
        print("✅ OSCILLATION DETECTED IN 3D SYNCHRONOUS CA")
        if osc_total:
            print(f"   Total energy oscillates (period: {results_64['oscillation']['total_energy']['period']:.1f})")
        if osc_cavity:
            print(f"   Cavity energy oscillates (period: {results_64['oscillation']['cavity_energy']['period']:.1f})")
        print()
        print("   This validates the directive:")
        print("   - 1D tests (0/808) were wrong dimensionality")
        print("   - 3D geometry enables resonant cavities")
        print("   - Synchronous update preserves oscillation")
    else:
        print("❌ NO OSCILLATION DETECTED (64³ Grid)")
        print()
        print("   32³: No oscillation")
        print("   64³: No oscillation")
        print()
        print("   Next: Try 128³ or reconsider parameters")

    print()


if __name__ == "__main__":
    main()
