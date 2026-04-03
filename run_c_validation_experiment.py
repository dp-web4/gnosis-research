#!/usr/bin/env python3
"""
Thor Session #53: First C ≈ 0.5 Empirical Data Collection

Run SAGE consciousness loop for a limited number of cycles to collect
validation data for the C ≈ 0.5 predictions from Sessions #1-51.

This is the FIRST empirical data collection after 51 sessions of pure theory.
"""

import sys
import os
import asyncio

# Change to gnosis-research directory so logs write here
os.chdir('/home/dp/gnosis-research')

# Add SAGE to path
sys.path.insert(0, '/home/dp/ai-workspace/SAGE')

from sage.core.sage_consciousness import SAGEConsciousness

async def main():
    print("=" * 80)
    print("Thor Session #53: C ≈ 0.5 Empirical Validation")
    print("=" * 80)
    print()
    print("Theory complete (Sessions #1-51): C ≈ 0.5 is optimal coherence boundary")
    print("Implementation complete (Session #52): Logging infrastructure in SAGE")
    print("THIS SESSION: Collect first empirical data")
    print()
    print("Experiment parameters:")
    print("  - Cycles: 300 (3 coherence measurements at cycle 100, 200, 300)")
    print("  - Metabolic state logged every cycle")
    print("  - Salience scores logged every cycle")
    print("  - Trust distribution + coherence logged every 100 cycles")
    print()
    print("Expected validation_logs output:")
    print("  - trust_distribution_log.jsonl (3 entries)")
    print("  - metabolic_state_log.jsonl (~300 entries)")
    print("  - salience_log.jsonl (~300 entries)")
    print("  - coherence_log.jsonl (3 entries)")
    print()
    print("-" * 80)
    print()

    # Minimal SAGE configuration for consciousness loop testing
    config = {
        'simulation_mode': True,  # Run in simulation mode (faster, no hardware deps)
        'base_path': '/home/dp/ai-workspace/SAGE',
        'plugins': [],  # No plugins needed for basic validation
        'vision_source': '',  # No vision needed
        'metabolic_config': {
            'initial_state': 'WAKE',
            'atp_recharge_rate': 10.0
        }
    }

    print("[Init] Creating SAGE consciousness instance...")
    sage = SAGEConsciousness(config)
    print("[Init] SAGE instance created")
    print()

    # Ensure validation_logs directory exists
    os.makedirs('validation_logs', exist_ok=True)
    print(f"[Init] Validation logs will be written to: {os.path.abspath('validation_logs')}")
    print()

    print("[Run] Starting 300-cycle consciousness loop...")
    print("      This will take ~30-60 seconds in simulation mode")
    print()

    try:
        await sage.run(max_cycles=300)
    except Exception as e:
        print(f"\n[ERROR] Consciousness loop error: {e}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 80)
    print("Data collection complete!")
    print("=" * 80)
    print()
    print("Next step: Run analyze_validation_logs.py to validate predictions")
    print()

if __name__ == '__main__':
    asyncio.run(main())
