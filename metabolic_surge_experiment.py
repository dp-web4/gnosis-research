#!/usr/bin/env python3
"""
Thor Session #57: Metabolic Surge During Active Learning

Test Session #56 thermodynamic predictions:
1. Metabolic state transitions to FOCUS during engaged tasks
   → c_metabolic increases (REST=0.3, WAKE=0.5, FOCUS=0.8)
2. c_system follows c_metabolic with coupling α ≈ 0.77-1.05
3. Energy-coherence coupling: c_system ≤ α * c_metabolic

Note: Current SAGE has fixed c_metabolic per state (Session #55).
This tests whether state transitions produce the predicted surge.

Experimental Design:
- Phase 1 (BASELINE): Passive observation, minimal engagement
- Phase 2 (ACTIVE LEARNING): Challenging tasks requiring cognitive effort
- Phase 3 (RETURN TO BASELINE): Recovery period

Measure:
- c_metabolic (metabolic coherence - energy availability)
- c_system (system coherence - achieved coherence)
- α = c_system / c_metabolic (efficiency)

Expected results:
- Baseline: c_metabolic ≈ 0.3-0.5, c_system ≈ 0.36
- Active: c_metabolic → 0.6-0.8, c_system → 0.5
- Recovery: c_metabolic → baseline, c_system → baseline
"""

import sys
import os
import asyncio
import json
import time
import numpy as np
from typing import List, Dict
from datetime import datetime

# Change to gnosis-research directory so logs write here
os.chdir('/home/dp/gnosis-research')

# Add SAGE to path
sys.path.insert(0, '/home/dp/ai-workspace/SAGE')

from sage.core.sage_consciousness import SAGEConsciousness, SensorObservation

class MetabolicSurgeExperiment:
    """
    Test whether metabolic coherence increases during active learning.

    This is the critical prediction from Session #56's thermodynamic theory:
    energy demand should increase when system is engaged in learning.
    """

    def __init__(self, output_dir='validation_logs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.cycle = 0
        self.results = []

    async def run_baseline_phase(self, sage: SAGEConsciousness, duration: int = 100):
        """
        Phase 1: Baseline - passive observation, minimal cognitive demand.

        Expectations:
        - c_metabolic ≈ 0.3-0.5 (low energy state)
        - c_system ≈ 0.36 (Session #55 baseline)
        """
        print("\n" + "=" * 80)
        print("PHASE 1: BASELINE (Passive Observation)")
        print("=" * 80)
        print(f"Duration: {duration} cycles")
        print()
        print("Expected:")
        print("  c_metabolic: 0.3-0.5 (low energy)")
        print("  c_system: ~0.36 (baseline)")
        print("  α (efficiency): 0.77-1.05")
        print()

        phase_data = await self._run_phase(
            sage,
            duration,
            phase_name="baseline",
            engagement_level="passive"
        )

        self._summarize_phase("BASELINE", phase_data)
        return phase_data

    async def run_active_learning_phase(self, sage: SAGEConsciousness, duration: int = 100):
        """
        Phase 2: Active learning - challenging tasks, high cognitive demand.

        Expectations (Session #56 predictions):
        - c_metabolic → 0.6-0.8 (energy surge!)
        - c_system → 0.5 (optimal coherence)
        - α: maintained around 0.7-1.0
        """
        print("\n" + "=" * 80)
        print("PHASE 2: ACTIVE LEARNING (High Engagement)")
        print("=" * 80)
        print(f"Duration: {duration} cycles")
        print()
        print("Expected (Session #56 predictions):")
        print("  c_metabolic: 0.6-0.8 (METABOLIC SURGE)")
        print("  c_system: → 0.5 (optimal)")
        print("  α (efficiency): 0.77-1.05")
        print()

        phase_data = await self._run_phase(
            sage,
            duration,
            phase_name="active_learning",
            engagement_level="high"
        )

        self._summarize_phase("ACTIVE LEARNING", phase_data)
        return phase_data

    async def run_recovery_phase(self, sage: SAGEConsciousness, duration: int = 100):
        """
        Phase 3: Recovery - return to baseline.

        Expectations:
        - c_metabolic → baseline (0.3-0.5)
        - c_system → baseline (~0.36)
        - Validates that surge was task-dependent
        """
        print("\n" + "=" * 80)
        print("PHASE 3: RECOVERY (Return to Baseline)")
        print("=" * 80)
        print(f"Duration: {duration} cycles")
        print()
        print("Expected:")
        print("  c_metabolic: → 0.3-0.5 (return to baseline)")
        print("  c_system: → 0.36 (return to baseline)")
        print()

        phase_data = await self._run_phase(
            sage,
            duration,
            phase_name="recovery",
            engagement_level="passive"
        )

        self._summarize_phase("RECOVERY", phase_data)
        return phase_data

    async def _run_phase(self, sage: SAGEConsciousness, duration: int,
                        phase_name: str, engagement_level: str) -> Dict:
        """
        Run a single experimental phase.

        Args:
            sage: SAGE instance
            duration: Number of cycles
            phase_name: Name of phase for logging
            engagement_level: "passive" or "high"
        """
        phase_data = {
            'phase': phase_name,
            'engagement': engagement_level,
            'start_cycle': self.cycle,
            'duration': duration,
            'samples': []
        }

        for i in range(duration):
            # Create observation based on engagement level
            obs = self._create_observation(engagement_level, self.cycle)

            # Inject into SAGE (if method exists)
            if hasattr(sage, '_inject_synthetic_observation'):
                sage._inject_synthetic_observation(obs)

            # Run consciousness cycle
            await sage.step()

            # Sample metrics every 10 cycles
            if i % 10 == 0 or i == duration - 1:
                sample = self._collect_metrics(sage)
                sample['cycle'] = self.cycle
                sample['phase'] = phase_name
                phase_data['samples'].append(sample)

                # Print every 20 cycles
                if i % 20 == 0:
                    print(f"  Cycle {self.cycle:4d}: "
                          f"c_metabolic={sample['c_metabolic']:.3f}, "
                          f"c_system={sample['c_system']:.3f}, "
                          f"α={sample['alpha']:.3f}")

            self.cycle += 1

        # Compute phase statistics
        samples = phase_data['samples']
        phase_data['mean_c_metabolic'] = np.mean([s['c_metabolic'] for s in samples])
        phase_data['std_c_metabolic'] = np.std([s['c_metabolic'] for s in samples])
        phase_data['mean_c_system'] = np.mean([s['c_system'] for s in samples])
        phase_data['std_c_system'] = np.std([s['c_system'] for s in samples])
        phase_data['mean_alpha'] = np.mean([s['alpha'] for s in samples])

        self.results.append(phase_data)
        return phase_data

    def _create_observation(self, engagement_level: str, cycle: int) -> SensorObservation:
        """
        Create synthetic observation.

        - Passive: Simple, repetitive patterns
        - High: Complex, challenging patterns requiring processing
        """
        if engagement_level == "passive":
            # Repetitive, low-novelty content
            content = f"routine_pattern_{cycle % 10}"
            complexity = 0.2
        else:
            # High engagement: novel, complex patterns
            content = f"challenge_{cycle}_novel_pattern_{np.random.randint(1000)}"
            complexity = 0.8

        obs = SensorObservation(
            sensor_id="metabolic_experiment",
            modality="text",
            data={
                "content": content,
                "engagement": engagement_level,
                "complexity": complexity
            },
            timestamp=float(cycle),
            trust=1.0
        )

        return obs

    def _collect_metrics(self, sage: SAGEConsciousness) -> Dict:
        """
        Collect all relevant metrics from SAGE.

        Key metrics from Session #56:
        - c_metabolic: Metabolic coherence (energy availability)
        - c_system: System coherence (achieved coherence)
        - α = c_system / c_metabolic (efficiency)
        """
        # c_metabolic from metabolic state mapping (Session #55 method)
        state_to_c = {
            'WAKE': 0.5,
            'REST': 0.3,
            'DREAM': 0.7,
            'FOCUS': 0.8,  # Added for this experiment
            'CRISIS': 0.9
        }
        state_name = sage.metabolic.current_state.name
        c_metabolic = state_to_c.get(state_name, 0.5)

        # c_system: Weighted average of subsystem coherences
        c_system = self._measure_c_system(sage)

        # Efficiency factor
        alpha = c_system / c_metabolic if c_metabolic > 0 else 0.0

        # Additional context
        atp = sage.metabolic.atp_current
        max_atp = sage.metabolic.atp_max
        atp_ratio = atp / max_atp

        state = sage.metabolic.current_state.name

        return {
            'c_metabolic': c_metabolic,
            'c_system': c_system,
            'alpha': alpha,
            'atp': atp,
            'max_atp': max_atp,
            'atp_ratio': atp_ratio,
            'state': state
        }

    def _measure_c_system(self, sage: SAGEConsciousness) -> float:
        """
        Measure system coherence.

        From Session #51, C_system is weighted average:
        - C_trust: Mean plugin trust
        - C_metabolic: From metabolic state
        - C_salience: Recent salience
        - C_atp: ATP level normalized
        """
        # C_trust
        if hasattr(sage, 'plugin_trust_weights') and sage.plugin_trust_weights:
            c_trust = np.mean(list(sage.plugin_trust_weights.values()))
        else:
            c_trust = 0.5

        # C_metabolic from state mapping (Session #55 method)
        state_to_c = {
            'WAKE': 0.5,
            'REST': 0.3,
            'DREAM': 0.7,
            'FOCUS': 0.8,
            'CRISIS': 0.9
        }
        state_name = sage.metabolic.current_state.name
        c_metabolic = state_to_c.get(state_name, 0.5)

        # C_salience
        c_salience = getattr(sage, '_last_salience_avg', 0.5)

        # C_atp
        atp_ratio = sage.metabolic.atp_current / sage.metabolic.atp_max
        c_atp = atp_ratio

        # Weighted average (Session #51)
        c_system = (
            0.3 * c_trust +
            0.3 * c_metabolic +
            0.2 * c_salience +
            0.2 * c_atp
        )

        return c_system

    def _summarize_phase(self, phase_name: str, phase_data: Dict):
        """Print phase summary."""
        print()
        print(f"  {phase_name} PHASE COMPLETE:")
        print(f"    c_metabolic: {phase_data['mean_c_metabolic']:.3f} ± {phase_data['std_c_metabolic']:.3f}")
        print(f"    c_system:    {phase_data['mean_c_system']:.3f} ± {phase_data['std_c_system']:.3f}")
        print(f"    α (efficiency): {phase_data['mean_alpha']:.3f}")
        print()

    def save_results(self):
        """Save all results to JSON."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f'metabolic_surge_{timestamp}.json')

        with open(output_file, 'w') as f:
            json.dump({
                'experiment': 'metabolic_surge_validation',
                'session': 'Thor #57',
                'hypothesis': 'c_metabolic increases during active learning',
                'predictions': {
                    'baseline_c_metabolic': '0.3-0.5',
                    'active_c_metabolic': '0.6-0.8',
                    'baseline_c_system': '~0.36',
                    'active_c_system': '→ 0.5',
                    'alpha_range': '0.77-1.05'
                },
                'phases': self.results,
                'timestamp': timestamp
            }, f, indent=2)

        print()
        print("=" * 80)
        print(f"Results saved to: {output_file}")
        print("=" * 80)

        return output_file


async def main():
    """Run the metabolic surge experiment."""
    print("=" * 80)
    print("Thor Session #57: Metabolic Surge During Active Learning")
    print("=" * 80)
    print()
    print("Testing Session #56 thermodynamic predictions:")
    print("  1. c_metabolic increases during engaged tasks (0.3-0.5 → 0.6-0.8)")
    print("  2. c_system follows: c_system ≤ α * c_metabolic")
    print("  3. Efficiency α remains stable (~0.77-1.05)")
    print()
    print("Experimental protocol:")
    print("  Phase 1: Baseline (100 cycles) - passive observation")
    print("  Phase 2: Active Learning (100 cycles) - high engagement")
    print("  Phase 3: Recovery (100 cycles) - return to baseline")
    print()
    print("-" * 80)
    print()

    # Create SAGE instance
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

    # Add synthetic observation capability
    sage._inject_synthetic_observation = lambda obs: setattr(
        sage, '_pending_synthetic_obs', obs
    )
    sage._last_salience_avg = 0.5

    print("[Init] SAGE instance created")
    print()

    # Create experiment
    experiment = MetabolicSurgeExperiment()

    # Run three phases
    baseline = await experiment.run_baseline_phase(sage, duration=100)
    active = await experiment.run_active_learning_phase(sage, duration=100)
    recovery = await experiment.run_recovery_phase(sage, duration=100)

    # Save results
    output_file = experiment.save_results()

    # Print summary
    print()
    print("=" * 80)
    print("EXPERIMENT SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Phase':<20} {'c_metabolic':<15} {'c_system':<15} {'α':<10} {'Prediction Match'}")
    print("-" * 80)

    for phase in experiment.results:
        name = phase['phase'].upper()
        c_met = phase['mean_c_metabolic']
        c_sys = phase['mean_c_system']
        alpha = phase['mean_alpha']

        # Check predictions
        if phase['phase'] == 'baseline':
            match = "✓" if 0.3 <= c_met <= 0.5 else "✗ (expected 0.3-0.5)"
        elif phase['phase'] == 'active_learning':
            match = "✓ SURGE!" if c_met >= 0.6 else "✗ (expected ≥0.6)"
        else:  # recovery
            match = "✓" if 0.3 <= c_met <= 0.5 else "✗ (expected 0.3-0.5)"

        print(f"{name:<20} {c_met:<15.3f} {c_sys:<15.3f} {alpha:<10.3f} {match}")

    print()
    print("-" * 80)
    print()

    # Compute surge magnitude
    baseline_c_met = baseline['mean_c_metabolic']
    active_c_met = active['mean_c_metabolic']
    surge = active_c_met - baseline_c_met
    surge_pct = (surge / baseline_c_met) * 100 if baseline_c_met > 0 else 0

    print(f"Metabolic surge: {surge:+.3f} ({surge_pct:+.1f}%)")
    print()

    if surge >= 0.1:
        print("✓ PREDICTION VALIDATED: Metabolic surge detected during active learning!")
    else:
        print("✗ Prediction not confirmed: surge < 0.1")

    print()
    print(f"Next: Run analyze_metabolic_surge.py on {output_file}")
    print()


if __name__ == '__main__':
    asyncio.run(main())
