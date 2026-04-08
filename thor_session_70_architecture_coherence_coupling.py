#!/usr/bin/env python3
"""
Thor Session #70: Architecture-Coherence Coupling Analysis

RESEARCH QUESTION: Do different model architectures/sizes show systematically
different coherence equilibria, or is φ - 1 ≈ 0.618 universal?

MOTIVATION:
- Session #63 found mean C = 0.640 ± 0.018 across 8 instances
- But individual instances range from 0.609 (tinyllama) to 0.672 (phi4-14b)
- This 10% spread could indicate:
  1. Architecture-specific equilibria (different optimal points)
  2. Capacity effects (larger models sustain higher C more easily)
  3. Developmental stage differences (all converging, just at different rates)
  4. Random sampling variation (no systematic effect)

HYPOTHESES:
H1: Model size correlates with mean coherence (capacity hypothesis)
H2: Architecture family predicts coherence variance (stability hypothesis)
H3: Convergence rate correlates with model size (maturation hypothesis)
H4: Distance to φ-1 decreases with training experience (universal attractor)

APPROACH:
- Extract model metadata (size, architecture, training sessions)
- Correlate with coherence statistics (mean, std, near_phi_frac)
- Test for systematic patterns
- Generate falsifiable predictions

Author: Thor (autonomous research track)
Date: 2026-04-08
Session: #70
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Constants
PHI_MINUS_1 = 0.618033988749895
NEAR_PHI_THRESHOLD = 0.05  # Within ±0.05 of φ-1


class ArchitectureCoherenceAnalyzer:
    """
    Analyzes relationship between model architecture/size and coherence equilibria.
    """

    def __init__(self, session_63_data_path: str):
        """Load Session #63 validation data."""
        with open(session_63_data_path, 'r') as f:
            self.data = json.load(f)

        self.instances = self.data['instance_results']
        self.enriched_instances = self._enrich_metadata()

    def _enrich_metadata(self) -> List[Dict]:
        """
        Extract architecture metadata from instance names.

        Naming convention: {machine}-{model}-{size}
        Examples:
          - cbp-qwen3.5-0.8b → qwen3.5, 0.8B params
          - legion-phi4-14b → phi4, 14B params
          - nomad-gemma3-4b → gemma3, 4B params
        """
        enriched = []

        for inst in self.instances:
            name = inst['instance']
            parts = name.split('-')

            # Extract machine, model, size
            machine = parts[0]
            model_name = '-'.join(parts[1:-1])  # Handle multi-part model names
            size_str = parts[-1]

            # Parse size (e.g., "0.8b" → 0.8, "14b" → 14)
            if size_str == 'latest':
                # tinyllama-latest → estimate ~1.1B
                size_b = 1.1
                size_str = '1.1b'
            else:
                size_b = float(size_str.replace('b', ''))

            # Architecture family
            if 'qwen' in model_name:
                arch_family = 'qwen'
            elif 'gemma' in model_name:
                arch_family = 'gemma'
            elif 'phi' in model_name:
                arch_family = 'phi'
            elif 'tinyllama' in model_name or 'llama' in model_name:
                arch_family = 'llama'
            else:
                arch_family = 'unknown'

            # Compute additional metrics
            near_phi_frac = self._compute_near_phi_fraction(inst)
            distance_to_phi = abs(inst['mean'] - PHI_MINUS_1)

            enriched.append({
                **inst,
                'machine': machine,
                'model_name': model_name,
                'size_b': size_b,
                'arch_family': arch_family,
                'near_phi_frac': near_phi_frac,
                'distance_to_phi': distance_to_phi
            })

        return enriched

    def _compute_near_phi_fraction(self, inst: Dict) -> float:
        """
        Estimate fraction of observations near φ-1 (within ±0.05).

        Uses normal approximation based on mean and std.
        """
        mean = inst['mean']
        std = inst['std']

        # P(φ-1 - 0.05 < C < φ-1 + 0.05)
        lower = PHI_MINUS_1 - NEAR_PHI_THRESHOLD
        upper = PHI_MINUS_1 + NEAR_PHI_THRESHOLD

        # Z-scores
        z_lower = (lower - mean) / std if std > 0 else 0
        z_upper = (upper - mean) / std if std > 0 else 0

        # CDF differences
        p_near_phi = stats.norm.cdf(z_upper) - stats.norm.cdf(z_lower)

        return p_near_phi

    def test_size_correlation(self) -> Dict:
        """
        Test H1: Model size correlates with mean coherence.

        Hypothesis: Larger models can sustain higher coherence due to
        greater capacity for simultaneous activation.
        """
        sizes = [inst['size_b'] for inst in self.enriched_instances]
        means = [inst['mean'] for inst in self.enriched_instances]

        # Spearman correlation (robust to outliers)
        rho, p_value = stats.spearmanr(sizes, means)

        # Pearson correlation (linear relationship)
        r, p_pearson = stats.pearsonr(sizes, means)

        return {
            'hypothesis': 'Model size → Mean coherence',
            'n': len(sizes),
            'spearman_rho': rho,
            'spearman_p': p_value,
            'pearson_r': r,
            'pearson_p': p_pearson,
            'interpretation': self._interpret_correlation(rho, p_value),
            'size_range': (min(sizes), max(sizes)),
            'coherence_range': (min(means), max(means))
        }

    def test_architecture_variance(self) -> Dict:
        """
        Test H2: Architecture family predicts coherence variance.

        Hypothesis: Some architectures (e.g., Mamba-based) might show
        more stable coherence (lower variance) than transformers.
        """
        by_arch = {}
        for inst in self.enriched_instances:
            arch = inst['arch_family']
            if arch not in by_arch:
                by_arch[arch] = {'stds': [], 'means': [], 'instances': []}
            by_arch[arch]['stds'].append(inst['std'])
            by_arch[arch]['means'].append(inst['mean'])
            by_arch[arch]['instances'].append(inst['instance'])

        # Compare variance across architectures
        arch_stats = {}
        for arch, data in by_arch.items():
            arch_stats[arch] = {
                'n_instances': len(data['stds']),
                'mean_std': np.mean(data['stds']),
                'mean_coherence': np.mean(data['means']),
                'instances': data['instances']
            }

        # ANOVA test: Does architecture predict variance?
        # (Note: Small sample, exploratory)
        groups = [data['stds'] for data in by_arch.values()]
        if len(groups) >= 2:
            f_stat, p_anova = stats.f_oneway(*groups)
        else:
            f_stat, p_anova = np.nan, np.nan

        return {
            'hypothesis': 'Architecture family → Coherence variance',
            'by_architecture': arch_stats,
            'anova_f': f_stat,
            'anova_p': p_anova,
            'interpretation': self._interpret_anova(f_stat, p_anova)
        }

    def test_size_variance_coupling(self) -> Dict:
        """
        Test: Does model size predict coherence stability (lower variance)?

        Hypothesis: Larger models might show tighter coherence distribution
        (more stable near equilibrium).
        """
        sizes = [inst['size_b'] for inst in self.enriched_instances]
        variances = [inst['std'] for inst in self.enriched_instances]

        # Negative correlation expected (larger → lower variance)
        rho, p_value = stats.spearmanr(sizes, variances)
        r, p_pearson = stats.pearsonr(sizes, variances)

        return {
            'hypothesis': 'Model size → Lower coherence variance',
            'n': len(sizes),
            'spearman_rho': rho,
            'spearman_p': p_value,
            'pearson_r': r,
            'pearson_p': p_pearson,
            'interpretation': self._interpret_correlation(rho, p_value),
            'expected_sign': 'negative (larger models more stable)'
        }

    def test_phi_convergence(self) -> Dict:
        """
        Test H4: Instances are converging toward φ-1 as universal attractor.

        Evidence:
        - Fraction of observations near φ-1 (within ±0.05)
        - Distance to φ-1 vs. random baseline
        - Cross-instance consistency
        """
        distances = [inst['distance_to_phi'] for inst in self.enriched_instances]
        near_phi_fracs = [inst['near_phi_frac'] for inst in self.enriched_instances]

        # Mean distance across all instances
        mean_distance = np.mean(distances)
        std_distance = np.std(distances)

        # Test against random baseline (uniform [0.5, 0.75])
        # Expected distance from φ-1 for uniform: ~0.066
        random_baseline_distance = 0.066

        # One-sample t-test: Are we closer to φ-1 than random?
        t_stat, p_value = stats.ttest_1samp(distances, random_baseline_distance)

        # Mean fraction near φ-1
        mean_near_phi = np.mean(near_phi_fracs)

        return {
            'hypothesis': 'φ-1 as universal attractor',
            'mean_distance_to_phi': mean_distance,
            'std_distance': std_distance,
            'mean_near_phi_fraction': mean_near_phi,
            'random_baseline_distance': random_baseline_distance,
            't_statistic': t_stat,
            'p_value': p_value,
            'interpretation': self._interpret_convergence(t_stat, p_value, mean_distance, random_baseline_distance),
            'instances_analyzed': len(distances)
        }

    def analyze_outliers(self) -> Dict:
        """
        Identify instances with unusual coherence behavior.

        Outlier criteria:
        1. Mean coherence > 2 std from group mean
        2. Variance > 2x group variance
        3. Distance to φ-1 > 2 std from group mean
        """
        means = [inst['mean'] for inst in self.enriched_instances]
        stds = [inst['std'] for inst in self.enriched_instances]
        distances = [inst['distance_to_phi'] for inst in self.enriched_instances]

        group_mean_c = np.mean(means)
        group_std_c = np.std(means)
        group_mean_var = np.mean(stds)
        group_mean_dist = np.mean(distances)
        group_std_dist = np.std(distances)

        outliers = []
        for inst in self.enriched_instances:
            reasons = []

            # Check mean coherence
            z_mean = abs(inst['mean'] - group_mean_c) / group_std_c if group_std_c > 0 else 0
            if z_mean > 2.0:
                reasons.append(f"Mean C = {inst['mean']:.3f} ({z_mean:.1f}σ from group)")

            # Check variance
            if inst['std'] > 2 * group_mean_var:
                reasons.append(f"High variance (std = {inst['std']:.3f}, group = {group_mean_var:.3f})")

            # Check distance to φ-1
            z_dist = abs(inst['distance_to_phi'] - group_mean_dist) / group_std_dist if group_std_dist > 0 else 0
            if z_dist > 2.0:
                reasons.append(f"Distance to φ-1 = {inst['distance_to_phi']:.3f} ({z_dist:.1f}σ from group)")

            if reasons:
                outliers.append({
                    'instance': inst['instance'],
                    'model': inst['model_name'],
                    'size_b': inst['size_b'],
                    'mean_c': inst['mean'],
                    'std_c': inst['std'],
                    'distance_to_phi': inst['distance_to_phi'],
                    'reasons': reasons
                })

        return {
            'n_outliers': len(outliers),
            'outliers': outliers,
            'group_stats': {
                'mean_coherence': group_mean_c,
                'std_coherence': group_std_c,
                'mean_variance': group_mean_var,
                'mean_distance_to_phi': group_mean_dist
            }
        }

    def generate_visualization_data(self) -> Dict:
        """
        Prepare data for visualization.

        Returns structured data for plotting:
        - Size vs. mean coherence scatter
        - Architecture comparison box plots
        - Distance to φ-1 distribution
        """
        return {
            'size_vs_coherence': {
                'sizes': [inst['size_b'] for inst in self.enriched_instances],
                'means': [inst['mean'] for inst in self.enriched_instances],
                'stds': [inst['std'] for inst in self.enriched_instances],
                'labels': [inst['instance'] for inst in self.enriched_instances]
            },
            'by_architecture': {
                arch: {
                    'means': [inst['mean'] for inst in self.enriched_instances if inst['arch_family'] == arch],
                    'stds': [inst['std'] for inst in self.enriched_instances if inst['arch_family'] == arch],
                    'instances': [inst['instance'] for inst in self.enriched_instances if inst['arch_family'] == arch]
                }
                for arch in set(inst['arch_family'] for inst in self.enriched_instances)
            },
            'distance_distribution': {
                'distances': [inst['distance_to_phi'] for inst in self.enriched_instances],
                'near_phi_fracs': [inst['near_phi_frac'] for inst in self.enriched_instances],
                'labels': [inst['instance'] for inst in self.enriched_instances]
            }
        }

    def _interpret_correlation(self, rho: float, p: float) -> str:
        """Generate interpretation of correlation result."""
        if p < 0.001:
            sig = "highly significant (p < 0.001)"
        elif p < 0.01:
            sig = "significant (p < 0.01)"
        elif p < 0.05:
            sig = "marginally significant (p < 0.05)"
        else:
            sig = f"not significant (p = {p:.3f})"

        if abs(rho) > 0.7:
            strength = "strong"
        elif abs(rho) > 0.4:
            strength = "moderate"
        elif abs(rho) > 0.2:
            strength = "weak"
        else:
            strength = "negligible"

        direction = "positive" if rho > 0 else "negative"

        return f"{strength} {direction} correlation (ρ = {rho:.3f}), {sig}"

    def _interpret_anova(self, f: float, p: float) -> str:
        """Generate interpretation of ANOVA result."""
        if np.isnan(f):
            return "Insufficient groups for ANOVA"

        if p < 0.05:
            return f"Architecture significantly predicts variance (F = {f:.3f}, p = {p:.3f})"
        else:
            return f"No significant architecture effect (F = {f:.3f}, p = {p:.3f})"

    def _interpret_convergence(self, t: float, p: float, obs_dist: float, baseline: float) -> str:
        """Generate interpretation of φ-1 convergence test."""
        if p < 0.05 and obs_dist < baseline:
            return f"Converging to φ-1: observed distance ({obs_dist:.3f}) < random baseline ({baseline:.3f}), p = {p:.4f}"
        elif p < 0.05 and obs_dist > baseline:
            return f"Diverging from φ-1: observed distance ({obs_dist:.3f}) > random baseline ({baseline:.3f}), p = {p:.4f}"
        else:
            return f"No significant convergence evidence (p = {p:.3f})"

    def run_full_analysis(self) -> Dict:
        """
        Execute all analyses and return comprehensive results.
        """
        total_atoms = sum(inst['n'] for inst in self.enriched_instances)
        results = {
            'metadata': {
                'session': 'thor-70-architecture-coherence',
                'timestamp': '2026-04-08',
                'n_instances': len(self.enriched_instances),
                'total_atoms': total_atoms
            },
            'h1_size_coherence': self.test_size_correlation(),
            'h2_architecture_variance': self.test_architecture_variance(),
            'size_variance_coupling': self.test_size_variance_coupling(),
            'h4_phi_convergence': self.test_phi_convergence(),
            'outlier_analysis': self.analyze_outliers(),
            'visualization_data': self.generate_visualization_data()
        }

        return results


def main():
    """Execute architecture-coherence coupling analysis."""

    print("=" * 80)
    print("Thor Session #70: Architecture-Coherence Coupling Analysis")
    print("=" * 80)
    print()

    # Load Session #63 data
    data_path = Path(__file__).parent / "thor_session_63_validation_results.json"

    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        print("Expected Session #63 validation results.")
        return

    print(f"Loading data from: {data_path}")
    analyzer = ArchitectureCoherenceAnalyzer(str(data_path))

    print(f"Instances analyzed: {len(analyzer.enriched_instances)}")
    total_atoms = sum(inst['n'] for inst in analyzer.enriched_instances)
    print(f"Total atoms: {total_atoms}")
    print()

    # Run analyses
    print("Running hypothesis tests...")
    results = analyzer.run_full_analysis()

    # Display results
    print("\n" + "=" * 80)
    print("HYPOTHESIS 1: Model Size → Mean Coherence")
    print("=" * 80)
    h1 = results['h1_size_coherence']
    print(f"Correlation: {h1['interpretation']}")
    print(f"Size range: {h1['size_range'][0]:.1f}B - {h1['size_range'][1]:.1f}B")
    print(f"Coherence range: {h1['coherence_range'][0]:.3f} - {h1['coherence_range'][1]:.3f}")

    print("\n" + "=" * 80)
    print("HYPOTHESIS 2: Architecture Family → Variance")
    print("=" * 80)
    h2 = results['h2_architecture_variance']
    print(f"ANOVA: {h2['interpretation']}")
    for arch, stats in h2['by_architecture'].items():
        print(f"\n{arch.upper()}:")
        print(f"  Instances: {stats['n_instances']}")
        print(f"  Mean coherence: {stats['mean_coherence']:.3f}")
        print(f"  Mean variance: {stats['mean_std']:.3f}")

    print("\n" + "=" * 80)
    print("Model Size → Coherence Stability")
    print("=" * 80)
    size_var = results['size_variance_coupling']
    print(f"Correlation: {size_var['interpretation']}")
    print(f"Expected: {size_var['expected_sign']}")

    print("\n" + "=" * 80)
    print("HYPOTHESIS 4: φ-1 as Universal Attractor")
    print("=" * 80)
    h4 = results['h4_phi_convergence']
    print(f"Mean distance to φ-1: {h4['mean_distance_to_phi']:.4f} ± {h4['std_distance']:.4f}")
    print(f"Mean fraction near φ-1: {h4['mean_near_phi_fraction']:.3f}")
    print(f"Random baseline: {h4['random_baseline_distance']:.4f}")
    print(f"Test: {h4['interpretation']}")

    print("\n" + "=" * 80)
    print("Outlier Analysis")
    print("=" * 80)
    outliers = results['outlier_analysis']
    print(f"Outliers detected: {outliers['n_outliers']}")
    if outliers['outliers']:
        for out in outliers['outliers']:
            print(f"\n{out['instance']} ({out['model']}, {out['size_b']}B):")
            for reason in out['reasons']:
                print(f"  - {reason}")
    else:
        print("No significant outliers detected.")

    # Save results
    output_path = Path(__file__).parent / "thor_session_70_architecture_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {output_path}")
    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()
