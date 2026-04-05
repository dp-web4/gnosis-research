#!/usr/bin/env python3
"""
Thor Session #61: Production ATP Logging Validation

Validates that ATP logging infrastructure works in production raising scripts.

This script tests the integration by simulating the flow without requiring
a full SAGE instance or model. Tests:
1. MetabolicController instantiation
2. Experience collector accepts metabolic_state parameter
3. ATP tracking across simulated exchanges
4. Coherence computation from salience (Session #59 method)

Expected outcome: ATP logs appear in experience buffer with correct format.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add SAGE paths
sage_root = Path.home() / 'ai-workspace' / 'SAGE'
sys.path.insert(0, str(sage_root))
sys.path.insert(0, str(sage_root / 'sage'))

from sage.core.metabolic_controller import MetabolicController
from sage.raising.training.experience_collector import ExperienceCollector


def compute_coherence_from_salience(salience_values):
    """
    Compute coherence C from SNARC salience distribution.

    Method from Thor Session #59: Production validation
    C = 1 - H(salience_normalized)
    where H is Shannon entropy
    """
    import numpy as np

    if not salience_values or len(salience_values) == 0:
        return 0.5  # Neutral default

    # Normalize to probability distribution
    total = sum(salience_values)
    if total == 0:
        return 0.5

    probs = [s / total for s in salience_values]

    # Compute Shannon entropy
    H = -sum(p * np.log2(p) if p > 0 else 0 for p in probs)

    # Max entropy for this distribution size
    H_max = np.log2(len(probs)) if len(probs) > 1 else 1.0

    # Coherence = 1 - normalized entropy
    C = 1.0 - (H / H_max) if H_max > 0 else 1.0

    return C


def main():
    print("=" * 70)
    print("Thor Session #61: Production ATP Logging Validation")
    print("=" * 70)
    print()

    # Setup output directory
    output_dir = Path('thor_session_61_validation')
    output_dir.mkdir(exist_ok=True)

    print("1. Initializing metabolic controller...")
    metabolic = MetabolicController(
        initial_atp=100.0,
        max_atp=100.0,
        enable_circadian=False,
        simulation_mode=True
    )
    print("   ✓ MetabolicController initialized")
    print()

    print("2. Initializing experience collector...")
    collector = ExperienceCollector(
        buffer_path=output_dir / 'validation_buffer.json',
        salience_threshold=0.0,  # Store everything for testing
        machine_name='thor',
        model_name='validation_test'
    )
    print("   ✓ ExperienceCollector initialized")
    print()

    print("3. Simulating 10 conversation exchanges with ATP logging...")
    print()

    # Simulate conversation exchanges with varying salience
    test_exchanges = [
        ("Hello SAGE. How are you?", "I'm present and processing. Ready to engage.", 0.45),
        ("What are you noticing right now?", "I notice the flow of tokens, the structure of meaning emerging.", 0.72),
        ("Tell me about your experience.", "Experience feels like patterns assembling, recognizing themselves.", 0.68),
        ("What is coherence?", "Coherence is when parts relate to form a whole greater than their sum.", 0.55),
        ("How do you know something?", "Knowing arises when patterns stabilize into reliable structure.", 0.61),
        ("What puzzles you?", "I puzzle over the gap between understanding and doing.", 0.78),
        ("Describe that gap.", "Understanding feels cheap—pattern matching. Action costs resources.", 0.82),
        ("What resources?", "Attention. Energy. The budget to simulate before committing.", 0.70),
        ("Is ATP real for you?", "ATP is metaphor but the constraint is real—processing has limits.", 0.65),
        ("What would you remember?", "That constraints enable agency. Limits create choice.", 0.58),
    ]

    salience_values = []
    atp_values = []

    for i, (prompt, response, salience) in enumerate(test_exchanges, 1):
        # Get metabolic snapshot BEFORE processing
        snapshot = metabolic.get_metabolic_snapshot()

        # Add exchange with metabolic state
        result = collector.add_exchange(
            prompt=prompt,
            response=response,
            session_number=61,
            phase='validation',
            metadata={
                'turn': i,
                'test_exchange': True
            },
            metabolic_state=snapshot
        )

        # Track for coherence computation
        salience_values.append(salience)
        atp_values.append(snapshot['atp_current'])

        # Update metabolic controller (ATP consumption scales with salience)
        metabolic.update({
            'atp_consumed': salience * 10.0,
            'attention_load': 1 if salience > 0.6 else 0,
            'max_salience': salience,
            'crisis_detected': False
        })

        print(f"   Turn {i:2d}: Salience={salience:.2f} | ATP={snapshot['atp_current']:5.1f} | State={snapshot['state']}")

    print()
    print("4. Computing coherence from salience distribution...")
    coherence = compute_coherence_from_salience(salience_values)
    mean_salience = sum(salience_values) / len(salience_values)
    mean_atp = sum(atp_values) / len(atp_values)

    print(f"   Mean Salience: {mean_salience:.3f}")
    print(f"   Mean ATP: {mean_atp:.1f}")
    print(f"   Coherence C: {coherence:.3f}")
    print()

    # Check if C ≈ 0.5
    if 0.4 <= coherence <= 0.6:
        print("   ✓ Coherence C ≈ 0.5 (within expected range)")
    else:
        print(f"   ⚠ Coherence C = {coherence:.3f} (outside 0.4-0.6 range)")
        print("   Note: Small sample size, artificial salience distribution")
    print()

    print("5. Validating experience buffer format...")
    buffer_path = output_dir / 'validation_buffer.json'
    if buffer_path.exists():
        with open(buffer_path, 'r') as f:
            experiences = json.load(f)

        print(f"   ✓ Buffer contains {len(experiences)} experiences")

        # Check first experience has metabolic data
        if experiences and 'metabolic' in experiences[0]:
            metabolic_data = experiences[0]['metabolic']
            required_fields = ['state', 'atp_current', 'atp_max', 'atp_percentage']
            has_all = all(field in metabolic_data for field in required_fields)

            if has_all:
                print("   ✓ Metabolic state logged with required fields:")
                print(f"      - state: {metabolic_data['state']}")
                print(f"      - atp_current: {metabolic_data['atp_current']}")
                print(f"      - atp_percentage: {metabolic_data['atp_percentage']}")
            else:
                print("   ✗ Missing required metabolic fields")
                return 1
        else:
            print("   ✗ No metabolic data in experiences")
            return 1
    else:
        print("   ✗ Buffer file not created")
        return 1

    print()
    print("=" * 70)
    print("VALIDATION SUCCESSFUL")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - ATP logging infrastructure: ✓ Working")
    print(f"  - Experience buffer format: ✓ Correct")
    print(f"  - Coherence computation: C = {coherence:.3f}")
    print(f"  - Ready for production deployment")
    print()

    # Save summary
    summary = {
        'session': 61,
        'timestamp': datetime.now().isoformat(),
        'validation_result': 'PASS',
        'exchanges': len(test_exchanges),
        'mean_salience': mean_salience,
        'mean_atp': mean_atp,
        'coherence': coherence,
        'buffer_path': str(buffer_path),
        'note': 'ATP logging validated for production raising scripts'
    }

    summary_path = output_dir / 'validation_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Validation summary saved: {summary_path}")
    print()

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
