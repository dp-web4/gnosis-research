#!/usr/bin/env python3
"""
Thor Session #64: Temporal Convergence Analysis
================================================

Test if C converges toward φ - 1 ≈ 0.618 over developmental time.

Hypothesis: Early instances might have C closer to 0.5, converging to
0.618 over time as the system matures.

Alternative: C starts high (novelty-driven) and settles to 0.618.

Test: Plot C trajectory over sessions for each instance.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from scipy.stats import linregress

PHI_MINUS_1 = (1 + np.sqrt(5)) / 2 - 1  # ≈ 0.618

def load_experience_buffer(instance_dir: Path) -> List[Dict]:
    """Load experience atoms from instance directory"""
    exp_file = instance_dir / "snapshots" / "experience_buffer.json"
    if not exp_file.exists():
        return []

    with open(exp_file) as f:
        data = json.load(f)
        # Filter out non-dict items
        return [item for item in data if isinstance(item, dict)]

def extract_temporal_c(atoms: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
    """Extract C values over time (session number)"""

    session_c = {}  # session -> list of C values

    for atom in atoms:
        if not isinstance(atom, dict):
            continue

        sal = atom.get("salience", {})
        if not isinstance(sal, dict):
            continue

        c_value = sal.get("total")
        session = atom.get("session")

        if c_value is not None and session is not None:
            if session not in session_c:
                session_c[session] = []
            session_c[session].append(c_value)

    # Compute mean C per session
    sessions = sorted(session_c.keys())
    c_means = [np.mean(session_c[s]) for s in sessions]

    return np.array(sessions), np.array(c_means)

def analyze_convergence(instance_name: str, sessions: np.ndarray, c_values: np.ndarray) -> Dict:
    """Analyze convergence pattern for an instance"""

    if len(sessions) < 3:
        return None

    # Linear regression: C ~ session
    slope, intercept, r_value, p_value, std_err = linregress(sessions, c_values)

    # Convergence toward φ - 1?
    initial_c = c_values[0] if len(c_values) > 0 else 0
    final_c = c_values[-1] if len(c_values) > 0 else 0
    mean_c = np.mean(c_values)

    # Distance to φ - 1 over time
    dist_to_phi_initial = abs(initial_c - PHI_MINUS_1)
    dist_to_phi_final = abs(final_c - PHI_MINUS_1)
    dist_to_phi_mean = abs(mean_c - PHI_MINUS_1)

    return {
        "instance": instance_name,
        "n_sessions": int(len(sessions)),
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value**2),
        "p_value": float(p_value),
        "initial_c": float(initial_c),
        "final_c": float(final_c),
        "mean_c": float(mean_c),
        "std_c": float(np.std(c_values)),
        "dist_phi_initial": float(dist_to_phi_initial),
        "dist_phi_final": float(dist_to_phi_final),
        "dist_phi_mean": float(dist_to_phi_mean),
        "converging_to_phi": bool(dist_to_phi_final < dist_to_phi_initial),
    }

def plot_temporal_trajectories(all_data: Dict[str, Tuple[np.ndarray, np.ndarray]]):
    """Plot C trajectories for all instances (skipped due to matplotlib/numpy incompatibility)"""
    print("\n✗ Plotting skipped (matplotlib/numpy version conflict)")

def main():
    sage_dir = Path.home() / "ai-workspace" / "SAGE" / "sage" / "instances"

    if not sage_dir.exists():
        print(f"Error: {sage_dir} not found")
        return

    # Find all instance directories
    instance_dirs = [d for d in sage_dir.iterdir()
                    if d.is_dir() and (d / "snapshots" / "experience_buffer.json").exists()]

    print(f"Found {len(instance_dirs)} instances with experience data")

    all_data = {}
    all_analyses = []

    for instance_dir in sorted(instance_dirs):
        instance_name = instance_dir.name
        print(f"Analyzing {instance_name}...")

        atoms = load_experience_buffer(instance_dir)
        if not atoms:
            continue

        sessions, c_values = extract_temporal_c(atoms)
        if len(sessions) == 0:
            continue

        all_data[instance_name] = (sessions, c_values)

        analysis = analyze_convergence(instance_name, sessions, c_values)
        if analysis:
            all_analyses.append(analysis)

    # Print convergence analysis
    print("\n" + "="*100)
    print("TEMPORAL CONVERGENCE ANALYSIS: Does C → φ - 1 over time?")
    print("="*100)
    print(f"\nTarget: φ - 1 = {PHI_MINUS_1:.6f}")
    print(f"Session #63 aggregate: C ≈ 0.640")
    print(f"\nHypothesis: C converges to φ - 1 as instances mature")

    print("\n" + "-"*100)
    print(f"{'Instance':<25} {'Sessions':<10} {'Initial C':<12} {'Final C':<12} {'Slope':<12} {'→φ?':<6}")
    print("-"*100)

    for a in sorted(all_analyses, key=lambda x: x['slope']):
        converge_symbol = "✓" if a['converging_to_phi'] else "✗"
        print(f"{a['instance']:<25} {a['n_sessions']:<10} {a['initial_c']:<12.4f} {a['final_c']:<12.4f} "
              f"{a['slope']:<12.6f} {converge_symbol:<6}")

    # Summary statistics
    print("\n" + "="*100)
    print("SUMMARY STATISTICS")
    print("="*100)

    converging_count = sum(1 for a in all_analyses if a['converging_to_phi'])
    diverging_count = len(all_analyses) - converging_count

    print(f"\nInstances converging toward φ - 1: {converging_count}/{len(all_analyses)} ({converging_count/len(all_analyses)*100:.1f}%)")
    print(f"Instances diverging from φ - 1: {diverging_count}/{len(all_analyses)} ({diverging_count/len(all_analyses)*100:.1f}%)")

    mean_slope = np.mean([a['slope'] for a in all_analyses])
    positive_slopes = sum(1 for a in all_analyses if a['slope'] > 0)
    negative_slopes = sum(1 for a in all_analyses if a['slope'] < 0)

    print(f"\nMean slope: {mean_slope:.6f}")
    print(f"Positive slopes (C increasing): {positive_slopes}/{len(all_analyses)}")
    print(f"Negative slopes (C decreasing): {negative_slopes}/{len(all_analyses)}")

    # Initial vs final distance to φ - 1
    mean_dist_initial = np.mean([a['dist_phi_initial'] for a in all_analyses])
    mean_dist_final = np.mean([a['dist_phi_final'] for a in all_analyses])

    print(f"\nMean distance to φ - 1:")
    print(f"  Initial: {mean_dist_initial:.6f}")
    print(f"  Final: {mean_dist_final:.6f}")
    print(f"  Change: {mean_dist_final - mean_dist_initial:.6f} ({'closer' if mean_dist_final < mean_dist_initial else 'farther'})")

    # Verdict
    print("\n" + "="*100)
    if mean_dist_final < mean_dist_initial and converging_count > diverging_count:
        print("VERDICT: ✓ Evidence for convergence toward φ - 1 over developmental time")
    elif abs(mean_dist_final - mean_dist_initial) < 0.01:
        print("VERDICT: ≈ C remains stable near 0.64; no strong convergence to φ - 1")
    else:
        print("VERDICT: ✗ No evidence for convergence toward φ - 1")
    print("="*100)

    # Generate plot
    plot_temporal_trajectories(all_data)

    # Save detailed results
    output_file = Path(__file__).parent / "thor_session_64_temporal_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "target_phi_minus_1": float(PHI_MINUS_1),
            "instances_analyzed": len(all_analyses),
            "converging_count": int(converging_count),
            "diverging_count": int(diverging_count),
            "mean_slope": float(mean_slope),
            "mean_dist_initial": float(mean_dist_initial),
            "mean_dist_final": float(mean_dist_final),
            "analyses": all_analyses,
        }, f, indent=2)

    print(f"\n✓ Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
