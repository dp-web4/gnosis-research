#!/usr/bin/env python3
"""
Thor Session #56: Active Learning Validation - C ≈ 0.5 Under Engagement

Test the central hypothesis:
- BASELINE (rest): C_system ≈ 0.36, novelty ≈ 0.14
- ACTIVE LEARNING (engaged): C_system → 0.5, novelty → 0.5

Experimental Design:
1. Run SAGE with synthetic observations at varying novelty levels
2. Measure C_system response
3. Validate that optimal novelty (≈0.5) produces C_system ≈ 0.5

This tests the theory from Sessions #51-54 that C ≈ 0.5 is the learning optimum.
"""

import sys
import os
import asyncio
import json
import numpy as np
from typing import List, Dict

# Change to gnosis-research directory so logs write here
os.chdir('/home/dp/gnosis-research')

# Add SAGE to path
sys.path.insert(0, '/home/dp/ai-workspace/SAGE')

from sage.core.sage_consciousness import SAGEConsciousness, SensorObservation, SalienceScore

class ActiveLearningExperiment:
    """
    Controlled experiment to validate C ≈ 0.5 under active learning.

    We create synthetic observations with controlled novelty levels and
    measure how C_system responds.
    """

    def __init__(self, output_dir='validation_logs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Results storage
        self.results = []

    async def run_experiment(self, sage: SAGEConsciousness,
                            novelty_schedule: List[float],
                            cycles_per_level: int = 50):
        """
        Run SAGE through a novelty schedule and measure C_system response.

        Args:
            sage: SAGEConsciousness instance
            novelty_schedule: List of target novelty values to test
            cycles_per_level: How many cycles to run at each novelty level
        """
        print("=" * 80)
        print("Active Learning Validation Experiment")
        print("=" * 80)
        print()
        print("Hypothesis:")
        print("  Baseline (novelty ≈ 0.1): C_system ≈ 0.36")
        print("  Optimal (novelty ≈ 0.5): C_system → 0.5")
        print("  High (novelty ≈ 0.9): C_system → ?")
        print()
        print(f"Schedule: {novelty_schedule}")
        print(f"Cycles per level: {cycles_per_level}")
        print()
        print("-" * 80)
        print()

        cycle = 0

        for target_novelty in novelty_schedule:
            print(f"\n[Phase {len(self.results) + 1}] Target novelty: {target_novelty:.2f}")
            print(f"  Running {cycles_per_level} cycles...")

            phase_data = {
                'target_novelty': target_novelty,
                'cycles': [],
                'c_system_samples': [],
                'c_metabolic_samples': [],
                'actual_novelty_samples': []
            }

            for i in range(cycles_per_level):
                # Create synthetic observation with target novelty
                obs = self._create_synthetic_observation(target_novelty, cycle)

                # Inject observation into SAGE
                # (In real SAGE this would come from sensors)
                sage._inject_synthetic_observation(obs)

                # Run one consciousness cycle
                await sage.step()

                # Measure coherence every 10 cycles
                if i % 10 == 0 or i == cycles_per_level - 1:
                    c_system = self._measure_c_system(sage)
                    c_metabolic = sage.metabolic_controller.get_metabolic_coherence()
                    actual_novelty = self._get_actual_novelty(sage)

                    phase_data['cycles'].append(cycle)
                    phase_data['c_system_samples'].append(c_system)
                    phase_data['c_metabolic_samples'].append(c_metabolic)
                    phase_data['actual_novelty_samples'].append(actual_novelty)

                    if i % 10 == 0:
                        print(f"    Cycle {cycle}: C_system={c_system:.3f}, "
                              f"C_metabolic={c_metabolic:.3f}, "
                              f"novelty={actual_novelty:.3f}")

                cycle += 1

            # Compute phase summary
            phase_data['mean_c_system'] = np.mean(phase_data['c_system_samples'])
            phase_data['std_c_system'] = np.std(phase_data['c_system_samples'])
            phase_data['mean_c_metabolic'] = np.mean(phase_data['c_metabolic_samples'])
            phase_data['mean_novelty'] = np.mean(phase_data['actual_novelty_samples'])

            self.results.append(phase_data)

            print(f"  Phase complete:")
            print(f"    Mean C_system: {phase_data['mean_c_system']:.3f} ± {phase_data['std_c_system']:.3f}")
            print(f"    Mean C_metabolic: {phase_data['mean_c_metabolic']:.3f}")
            print(f"    Mean novelty: {phase_data['mean_novelty']:.3f}")

        # Save results
        self._save_results()

        print()
        print("=" * 80)
        print("Experiment Complete!")
        print("=" * 80)

        return self.results

    def _create_synthetic_observation(self, target_novelty: float, cycle: int) -> SensorObservation:
        """
        Create a synthetic observation with controlled novelty.

        Strategy:
        - Low novelty (0.1): Repeat same observation
        - Mid novelty (0.5): Mix of familiar and novel patterns
        - High novelty (0.9): Always novel/random
        """
        # Use cycle number to create deterministic but varying content
        if target_novelty < 0.3:
            # Low novelty - high repetition
            content = f"pattern_A_{cycle % 5}"
        elif target_novelty < 0.7:
            # Medium novelty - balanced
            content = f"pattern_B_{cycle % 20}"
        else:
            # High novelty - always changing
            content = f"pattern_C_{cycle}"

        obs = SensorObservation(
            sensor_id="synthetic_novelty_source",
            modality="text",
            data={"content": content, "target_novelty": target_novelty},
            timestamp=float(cycle),
            trust=1.0
        )

        return obs

    def _measure_c_system(self, sage: SAGEConsciousness) -> float:
        """
        Measure system coherence from SAGE state.

        From Session #51, C_system is weighted average of component coherences:
        - C_trust: Mean of plugin trust weights
        - C_metabolic: From metabolic state
        - C_salience: From salience field
        - C_atp: ATP level normalized
        """
        # C_trust: Mean trust weights
        if hasattr(sage, 'plugin_trust_weights') and sage.plugin_trust_weights:
            c_trust = np.mean(list(sage.plugin_trust_weights.values()))
        else:
            c_trust = 0.5  # Neutral default

        # C_metabolic: From metabolic controller
        c_metabolic = sage.metabolic_controller.get_metabolic_coherence()

        # C_salience: Recent salience average (if available)
        c_salience = getattr(sage, '_last_salience_avg', 0.5)

        # C_atp: Normalized ATP level
        current_atp = sage.metabolic_controller.current_atp
        max_atp = sage.metabolic_controller.max_atp
        c_atp = current_atp / max_atp

        # Weighted average (from Session #51)
        c_system = (
            0.3 * c_trust +
            0.3 * c_metabolic +
            0.2 * c_salience +
            0.2 * c_atp
        )

        return c_system

    def _get_actual_novelty(self, sage: SAGEConsciousness) -> float:
        """Get actual novelty from last salience computation."""
        if hasattr(sage, '_last_salience_scores') and sage._last_salience_scores:
            # Average novelty across recent observations
            novelties = [score.novelty for score in sage._last_salience_scores]
            return np.mean(novelties)
        return 0.5  # Default

    def _save_results(self):
        """Save experiment results to JSON."""
        output_file = os.path.join(self.output_dir, 'active_learning_results.json')

        with open(output_file, 'w') as f:
            json.dump({
                'experiment': 'active_learning_validation',
                'hypothesis': 'C_system → 0.5 when novelty → 0.5',
                'phases': self.results,
                'timestamp': os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip()
            }, f, indent=2)

        print(f"\nResults saved to: {output_file}")


async def main():
    """
    Run the active learning validation experiment.

    Novelty schedule:
    1. Baseline (0.1) - confirm Session #55 baseline
    2. Low-mid (0.3) - transition
    3. Optimal (0.5) - test main hypothesis
    4. High-mid (0.7) - post-optimal
    5. High (0.9) - novelty saturation
    6. Return to optimal (0.5) - validate reproducibility
    """
    print("=" * 80)
    print("Thor Session #56: Active Learning Validation")
    print("=" * 80)
    print()
    print("Testing: Does C_system → 0.5 when novelty → 0.5?")
    print()
    print("Predictions:")
    print("  Session #55 baseline: novelty=0.14, C_system=0.36")
    print("  Theory (Sessions #1-54): novelty=0.5 → C_system≈0.5 (optimal learning)")
    print()
    print("-" * 80)
    print()

    # Novelty schedule
    novelty_schedule = [0.1, 0.3, 0.5, 0.7, 0.9, 0.5]
    cycles_per_level = 50

    # Create SAGE instance in simulation mode
    config = {
        'simulation_mode': True,
        'base_path': '/home/dp/ai-workspace/SAGE',
        'plugins': [],
        'vision_source': '',
        'metabolic_config': {
            'initial_state': 'WAKE',
            'atp_recharge_rate': 10.0
        }
    }

    print("[Init] Creating SAGE consciousness instance...")
    sage = SAGEConsciousness(config)

    # Add synthetic observation injection capability
    sage._inject_synthetic_observation = lambda obs: setattr(
        sage, '_pending_synthetic_obs', obs
    )
    sage._last_salience_scores = []
    sage._last_salience_avg = 0.5

    print("[Init] SAGE instance created")
    print()

    # Create experiment
    experiment = ActiveLearningExperiment()

    # Run experiment
    results = await experiment.run_experiment(
        sage,
        novelty_schedule,
        cycles_per_level
    )

    # Summary
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Target Novelty':<15} {'Mean C_system':<15} {'Std C_system':<15} {'Prediction'}")
    print("-" * 80)

    for phase in results:
        target = phase['target_novelty']
        mean_c = phase['mean_c_system']
        std_c = phase['std_c_system']

        # Predicted C based on theory
        if target < 0.25:
            prediction = "~0.36 (baseline)"
        elif 0.4 <= target <= 0.6:
            prediction = "→ 0.5 (optimal!)"
        else:
            prediction = "TBD"

        print(f"{target:<15.2f} {mean_c:<15.3f} {std_c:<15.3f} {prediction}")

    print()
    print("-" * 80)
    print()
    print("Next step: Run analyze_active_learning.py to validate predictions")
    print()


if __name__ == '__main__':
    asyncio.run(main())
