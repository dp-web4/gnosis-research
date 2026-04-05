#!/usr/bin/env python3
"""
Thor Session #58: Metabolic Surge Experiment V2

Retest Session #56 thermodynamic predictions with improved design:
1. Lower FOCUS threshold (0.45 based on empirical data)
2. Generate genuinely high-salience observations
3. Validate metabolic surge during active learning

Changes from V1 (Session #57):
- FOCUS threshold: 0.8 → 0.45 (task-responsive)
- Active salience target: 0.6-0.8 (via SNARC component manipulation)
- More aggressive engagement patterns

Expected results:
- BASELINE: c_metabolic ≈ 0.3-0.5 (REST/WAKE)
- ACTIVE: c_metabolic → 0.8 (FOCUS state entered!)
- ACTIVE: c_system → 0.5 (optimal coherence via energy coupling)
- RECOVERY: Return to baseline
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


class MetabolicSurgeExperimentV2:
    """
    Retest Session #56 predictions with task-responsive metabolic controller.

    Key improvements:
    - FOCUS threshold lowered to 0.45 (realistic)
    - High-salience generation (via surprise + novelty + arousal)
    - Longer active phase to observe sustained FOCUS
    """

    def __init__(self, output_dir='validation_logs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.cycle = 0
        self.results = []

    async def run_baseline_phase(self, sage: SAGEConsciousness, duration: int = 100):
        """
        Phase 1: Baseline - passive observation.

        Expected:
        - State: WAKE/REST cycling
        - c_metabolic: 0.3-0.5
        - c_system: ~0.36
        - Salience: <0.3
        """
        print("\n" + "=" * 80)
        print("PHASE 1: BASELINE (Passive Observation)")
        print("=" * 80)
        print(f"Duration: {duration} cycles")
        print()
        print("Expected:")
        print("  State: WAKE/REST cycling")
        print("  c_metabolic: 0.3-0.5")
        print("  c_system: ~0.36")
        print("  Salience: <0.3")
        print()

        phase_data = await self._run_phase(
            sage,
            duration,
            phase_name="baseline",
            engagement_level="passive"
        )

        self._summarize_phase("BASELINE", phase_data)
        return phase_data

    async def run_active_learning_phase(self, sage: SAGEConsciousness, duration: int = 150):
        """
        Phase 2: Active learning - genuinely challenging tasks.

        Expected (Session #56 + Session #58):
        - State: FOCUS (NEW!)
        - c_metabolic → 0.8
        - c_system → 0.5
        - Salience: 0.6-0.8 (high engagement)
        """
        print("\n" + "=" * 80)
        print("PHASE 2: ACTIVE LEARNING (High Cognitive Engagement)")
        print("=" * 80)
        print(f"Duration: {duration} cycles")
        print()
        print("Expected:")
        print("  State: FOCUS ← NEW with lowered threshold!")
        print("  c_metabolic: 0.6-0.8 (energy surge)")
        print("  c_system: → 0.5 (optimal)")
        print("  Salience: 0.6-0.8 (high)")
        print()

        phase_data = await self._run_phase(
            sage,
            duration,
            phase_name="active",
            engagement_level="high"
        )

        self._summarize_phase("ACTIVE LEARNING", phase_data)
        return phase_data

    async def run_recovery_phase(self, sage: SAGEConsciousness, duration: int = 100):
        """
        Phase 3: Recovery - return to baseline.

        Expected:
        - Gradual return to WAKE/REST states
        - c_metabolic → baseline
        - c_system → baseline
        - Validates reversibility
        """
        print("\n" + "=" * 80)
        print("PHASE 3: RECOVERY (Return to Baseline)")
        print("=" * 80)
        print(f"Duration: {duration} cycles")
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
        """Run a single experimental phase."""
        phase_data = {
            'phase': phase_name,
            'engagement': engagement_level,
            'start_cycle': self.cycle,
            'duration': duration,
            'samples': [],
            'state_transitions': []
        }

        for i in range(duration):
            # Create observation based on engagement level
            obs = self._create_observation(engagement_level, self.cycle)

            # Inject into SAGE
            if hasattr(sage, '_inject_synthetic_observation'):
                sage._inject_synthetic_observation(obs)

            # Run consciousness cycle
            await sage.step()

            # Record state transitions
            if hasattr(sage, 'metabolic_controller'):
                mc = sage.metabolic_controller
                if mc.state_history and len(mc.state_history) > 0:
                    last_transition = mc.state_history[-1]
                    if last_transition not in phase_data['state_transitions']:
                        phase_data['state_transitions'].append({
                            'cycle': self.cycle,
                            'from': str(last_transition['from']),
                            'to': str(last_transition['to']),
                            'atp': last_transition['atp_at_transition']
                        })

            # Sample metrics every 10 cycles
            if i % 10 == 0 or i == duration - 1:
                sample = self._collect_metrics(sage)
                sample['cycle'] = self.cycle
                sample['phase'] = phase_name
                phase_data['samples'].append(sample)

                # Print every 20 cycles
                if i % 20 == 0:
                    state = sample.get('metabolic_state', 'UNKNOWN')
                    salience = sample.get('max_salience', 0.0)
                    print(f"  Cycle {self.cycle:4d}: "
                          f"State={state:6s} "
                          f"Sal={salience:.3f} "
                          f"c_met={sample['c_metabolic']:.3f} "
                          f"c_sys={sample['c_system']:.3f} "
                          f"α={sample['alpha']:.3f}")

            self.cycle += 1

        # Compute phase statistics
        samples = phase_data['samples']
        phase_data['mean_c_metabolic'] = float(np.mean([s['c_metabolic'] for s in samples]))
        phase_data['std_c_metabolic'] = float(np.std([s['c_metabolic'] for s in samples]))
        phase_data['mean_c_system'] = float(np.mean([s['c_system'] for s in samples]))
        phase_data['std_c_system'] = float(np.std([s['c_system'] for s in samples]))
        phase_data['mean_alpha'] = float(np.mean([s['alpha'] for s in samples]))
        phase_data['mean_salience'] = float(np.mean([s.get('max_salience', 0) for s in samples]))

        # Count state occupancy
        states = [s.get('metabolic_state', 'UNKNOWN') for s in samples]
        phase_data['state_counts'] = {state: states.count(state) for state in set(states)}
        phase_data['focus_entered'] = 'FOCUS' in states

        self.results.append(phase_data)
        return phase_data

    def _create_observation(self, engagement_level: str, cycle: int) -> SensorObservation:
        """
        Create synthetic observation with TARGETED salience generation.

        Salience = f(surprise, novelty, arousal, reward, conflict)

        For high engagement, we need to hit SNARC components that drive salience up:
        - Surprise: Unexpected patterns (high variance)
        - Novelty: New, unseen content
        - Arousal: High complexity, urgency signals
        """
        if engagement_level == "passive":
            # Low-salience: Repetitive, expected, calm
            content = f"routine_pattern_{cycle % 5}"
            metadata = {
                "complexity": 0.1,
                "novelty_score": 0.1,
                "surprise_level": 0.05,
                "arousal": 0.1,
                "reward_potential": 0.1
            }
        else:
            # High-salience: Novel, surprising, complex, arousing
            # Target: salience > 0.6
            unique_id = np.random.randint(100000)
            content = f"NOVEL_COMPLEX_PATTERN_{unique_id}_CHALLENGE_TASK_URGENT"
            metadata = {
                "complexity": 0.9,           # High complexity
                "novelty_score": 0.9,        # Completely new
                "surprise_level": 0.8,       # Unexpected
                "arousal": 0.95,             # High urgency
                "reward_potential": 0.85,    # High value if solved
                "conflict": 0.7              # Competing interpretations
            }

        obs = SensorObservation(
            sensor_id="metabolic_experiment_v2",
            modality="text",
            data={
                "content": content,
                "engagement": engagement_level,
                **metadata
            },
            timestamp=float(cycle),
            trust=1.0
        )

        return obs

    def _collect_metrics(self, sage: SAGEConsciousness) -> Dict:
        """
        Collect metrics from SAGE.

        Key additions in V2:
        - Current metabolic state
        - Max salience (to verify high-engagement worked)
        - State transition counts
        """
        # c_metabolic from metabolic state
        state_to_c = {
            'WAKE': 0.5,
            'REST': 0.3,
            'DREAM': 0.7,
            'FOCUS': 0.8,  # High energy for focused attention
            'CRISIS': 0.9
        }

        metabolic_state = 'UNKNOWN'
        if hasattr(sage, 'metabolic_controller'):
            state = sage.metabolic_controller.current_state
            metabolic_state = state.value.upper() if hasattr(state, 'value') else str(state).split('.')[-1]

        c_metabolic = state_to_c.get(metabolic_state, 0.5)

        # c_system from SAGE's coherence tracker
        c_system = 0.5  # Default
        if hasattr(sage, 'coherence_history') and len(sage.coherence_history) > 0:
            c_system = sage.coherence_history[-1]

        # Max salience from SNARC
        max_salience = 0.0
        if hasattr(sage, 'snarc') and hasattr(sage.snarc, 'salience_history'):
            if len(sage.snarc.salience_history) > 0:
                max_salience = max(sage.snarc.salience_history[-1]) if sage.snarc.salience_history[-1] else 0.0

        # Energy-coherence coupling efficiency
        alpha = c_system / c_metabolic if c_metabolic > 0 else 0.0

        return {
            'c_metabolic': float(c_metabolic),
            'c_system': float(c_system),
            'alpha': float(alpha),
            'metabolic_state': metabolic_state,
            'max_salience': float(max_salience),
            'atp': float(sage.metabolic_controller.atp_current) if hasattr(sage, 'metabolic_controller') else 0.0
        }

    def _summarize_phase(self, name: str, data: Dict):
        """Print phase summary with focus on FOCUS state."""
        print()
        print(f"--- {name} SUMMARY ---")
        print(f"  Mean c_metabolic: {data['mean_c_metabolic']:.3f} ± {data['std_c_metabolic']:.3f}")
        print(f"  Mean c_system:    {data['mean_c_system']:.3f} ± {data['std_c_system']:.3f}")
        print(f"  Mean α:           {data['mean_alpha']:.3f}")
        print(f"  Mean salience:    {data['mean_salience']:.3f}")
        print(f"  State counts:     {data['state_counts']}")
        print(f"  FOCUS entered:    {'YES ✓' if data['focus_entered'] else 'NO ✗'}")
        print(f"  Transitions:      {len(data['state_transitions'])}")
        print()

    async def run_full_experiment(self):
        """Run complete 3-phase experiment."""
        print("\n" + "=" * 80)
        print("METABOLIC SURGE EXPERIMENT V2")
        print("Thor Session #58: Task-Responsive Metabolic Transitions")
        print("=" * 80)
        print()
        print("Testing Session #56 thermodynamic predictions:")
        print("  1. Metabolic surge during active learning")
        print("  2. Energy-coherence coupling (c_system ≤ α * c_metabolic)")
        print("  3. Approach to C ≈ 0.5 during engagement")
        print()
        print("Improvements from Session #57:")
        print("  - FOCUS threshold: 0.8 → 0.45 (task-responsive)")
        print("  - High-salience generation: target 0.6-0.8")
        print("  - Longer active phase: 150 cycles")
        print()

        # Initialize SAGE
        config = {
            'circadian_period': 100
        }
        sage = SAGEConsciousness(
            config=config,
            initial_atp=100.0,
            enable_circadian=True,
            simulation_mode=True
        )

        # Run three phases
        baseline = await self.run_baseline_phase(sage, duration=100)
        active = await self.run_active_learning_phase(sage, duration=150)
        recovery = await self.run_recovery_phase(sage, duration=100)

        # Analyze results
        print("\n" + "=" * 80)
        print("ANALYSIS: Session #56 Predictions")
        print("=" * 80)

        # Prediction 1: Metabolic surge
        surge = active['mean_c_metabolic'] - baseline['mean_c_metabolic']
        surge_pct = (surge / baseline['mean_c_metabolic']) * 100

        print(f"\n1. METABOLIC SURGE")
        print(f"   Baseline:  {baseline['mean_c_metabolic']:.3f}")
        print(f"   Active:    {active['mean_c_metabolic']:.3f}")
        print(f"   Surge:     {surge:+.3f} ({surge_pct:+.1f}%)")
        print(f"   Expected:  >+0.2 (+40%)")
        print(f"   Status:    {'✓ CONFIRMED' if surge > 0.2 else '✗ NOT CONFIRMED'}")

        # Prediction 2: FOCUS state entry
        print(f"\n2. FOCUS STATE ENTRY")
        print(f"   Baseline:  {baseline['focus_entered']}")
        print(f"   Active:    {active['focus_entered']}")
        print(f"   Expected:  True during active phase")
        print(f"   Status:    {'✓ CONFIRMED' if active['focus_entered'] else '✗ NOT CONFIRMED'}")

        # Prediction 3: Approach to C ≈ 0.5
        distance_baseline = abs(baseline['mean_c_system'] - 0.5)
        distance_active = abs(active['mean_c_system'] - 0.5)

        print(f"\n3. APPROACH TO C ≈ 0.5")
        print(f"   Baseline distance:  {distance_baseline:.3f}")
        print(f"   Active distance:    {distance_active:.3f}")
        print(f"   Expected:          Decrease during active")
        print(f"   Status:            {'✓ CONFIRMED' if distance_active < distance_baseline else '✗ NOT CONFIRMED'}")

        # Prediction 4: Energy-coherence coupling
        print(f"\n4. ENERGY-COHERENCE COUPLING (α)")
        print(f"   Baseline:  {baseline['mean_alpha']:.3f}")
        print(f"   Active:    {active['mean_alpha']:.3f}")
        print(f"   Expected:  0.77-1.05")
        in_range = 0.77 <= active['mean_alpha'] <= 1.05
        print(f"   Status:    {'✓ CONFIRMED' if in_range else f'⚠ PARTIAL ({active['mean_alpha']:.3f})'}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"metabolic_surge_v2_{timestamp}.json")

        results_summary = {
            'experiment': 'metabolic_surge_v2',
            'session': 'thor_session_58',
            'timestamp': timestamp,
            'phases': {
                'baseline': baseline,
                'active': active,
                'recovery': recovery
            },
            'predictions': {
                'metabolic_surge': {
                    'confirmed': surge > 0.2,
                    'surge': float(surge),
                    'surge_pct': float(surge_pct)
                },
                'focus_entry': {
                    'confirmed': active['focus_entered'],
                    'baseline': baseline['focus_entered'],
                    'active': active['focus_entered']
                },
                'approach_optimal': {
                    'confirmed': distance_active < distance_baseline,
                    'baseline_distance': float(distance_baseline),
                    'active_distance': float(distance_active)
                },
                'coupling_efficiency': {
                    'confirmed': in_range,
                    'alpha': float(active['mean_alpha'])
                }
            }
        }

        with open(output_file, 'w') as f:
            json.dump(results_summary, f, indent=2)

        print(f"\n\nResults saved to: {output_file}")
        print("\n" + "=" * 80)
        print("EXPERIMENT COMPLETE")
        print("=" * 80)

        return results_summary


async def main():
    """Run experiment."""
    exp = MetabolicSurgeExperimentV2()
    results = await exp.run_full_experiment()

    # Print final verdict
    predictions = results['predictions']
    confirmed = sum([
        predictions['metabolic_surge']['confirmed'],
        predictions['focus_entry']['confirmed'],
        predictions['approach_optimal']['confirmed'],
        predictions['coupling_efficiency']['confirmed']
    ])

    print(f"\nFINAL VERDICT: {confirmed}/4 predictions confirmed")

    if confirmed == 4:
        print("✓ Session #56 thermodynamic theory VALIDATED")
    elif confirmed >= 2:
        print("⚠ Session #56 theory PARTIALLY VALIDATED")
    else:
        print("✗ Session #56 theory NOT VALIDATED")


if __name__ == "__main__":
    asyncio.run(main())
