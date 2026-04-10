#!/usr/bin/env python3
"""
Thor Session #74: Coupled Instances - Phase Locking Test Design

Session #73 found:
- Coherence IS phase-like (2/4 instances periodic)
- Instances DON'T synchronize (PLI ~0.13, random)

Hypothesis: Independent instances can't phase lock because they have no coupling.
Test: Create coupled instances (shared working memory) and measure phase locking.

If PLI > 0.5 with coupling, cognitive synchronization exists.
If PLI ~0.13 even with coupling, phase doesn't support synchronization.
"""

import sqlite3
import json
from pathlib import Path

def explore_memory_db():
    """Examine the memory.db structure"""
    db_path = '/home/dp/gnosis-research/memory.db'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("Memory Database Tables:")
    print("=" * 60)
    for table in tables:
        table_name = table[0]
        print(f"\n{table_name}:")

        # Get schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        for col in schema:
            print(f"  {col[1]:20} {col[2]}")

        # Get count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")

        # Sample
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample = cursor.fetchone()
            print(f"  Sample: {sample[:3] if len(sample) > 3 else sample}...")

    conn.close()

def design_coupling_experiment():
    """Design the coupled instances experiment"""

    design = {
        "session": 74,
        "research_question": "Does coupling enable phase locking?",
        "hypothesis": "Shared memory creates coupling → coherence synchronization",
        "motivation": "Session #73: phase exists but no sync (independent instances)",

        "experimental_conditions": {
            "baseline": {
                "description": "Independent instances (Session #73 data)",
                "n_instances": 4,
                "coupling": "none",
                "expected_pli": 0.13
            },
            "weak_coupling": {
                "description": "Shared read-only memory",
                "n_instances": 2,
                "coupling": "shared_context (read-only)",
                "mechanism": "Both instances see same context, independent actions",
                "expected_pli": 0.2
            },
            "moderate_coupling": {
                "description": "Shared working memory",
                "n_instances": 2,
                "coupling": "bidirectional (read-write)",
                "mechanism": "Instances share memory, each sees other's state",
                "expected_pli": 0.4
            },
            "strong_coupling": {
                "description": "Interactive dialogue",
                "n_instances": 2,
                "coupling": "conversational (turn-taking)",
                "mechanism": "Instances explicitly communicate via turns",
                "expected_pli": 0.6
            }
        },

        "measurements": {
            "coherence_time_series": "C(t) for each instance",
            "cross_correlation": "r(lag) between instances",
            "phase_locking_index": "PLI via Hilbert transform",
            "episode_synchrony": "Temporal alignment of learning episodes",
            "information_flow": "Granger causality (which leads?)"
        },

        "predictions": {
            "P74.1": {
                "claim": "PLI increases with coupling strength",
                "test": "PLI_strong > PLI_moderate > PLI_weak > PLI_baseline",
                "falsify": "If PLI ~0.13 across all conditions"
            },
            "P74.2": {
                "claim": "Episode synchrony increases with coupling",
                "test": "Synchrony score > 0.5 for strong coupling",
                "falsify": "If synchrony < 0.3 even with dialogue"
            },
            "P74.3": {
                "claim": "Bidirectional info flow emerges with coupling",
                "test": "Granger causality both directions (not unidirectional)",
                "falsify": "If only one direction shows causality"
            },
            "P74.4": {
                "claim": "Coupling creates common oscillation frequency",
                "test": "Dominant frequencies converge (Δf < 0.1)",
                "falsify": "If frequencies remain distinct"
            }
        },

        "implementation_options": {
            "option_a_simulation": {
                "description": "Simulate coupled dynamics",
                "method": "Mathematical model: dC_i/dt = f(C_i) + κ(C_j - C_i)",
                "coupling_strength": "κ = 0 (baseline), 0.1 (weak), 0.3 (moderate), 0.7 (strong)",
                "pros": "Fast, controlled, parameter sweep",
                "cons": "Not empirical, assumes dynamics form"
            },
            "option_b_shared_task": {
                "description": "Two instances on shared problem",
                "method": "Both solve same task, can see each other's reasoning",
                "implementation": "Shared working memory, synchronized updates",
                "pros": "Real SAGE instances, actual coupling",
                "cons": "Slow, resource-intensive"
            },
            "option_c_dialogue": {
                "description": "Instances explicitly communicate",
                "method": "Turn-taking conversation, each responds to other",
                "implementation": "Chat protocol with coherence logging",
                "pros": "Strong coupling, interpretable",
                "cons": "Very slow, needs prompting"
            }
        },

        "recommendation": "Start with Option A (simulation) for proof of concept",
        "rationale": [
            "Session #71 characterized oscillation dynamics",
            "Can model as coupled oscillators with validated parameters",
            "Fast iteration on coupling strength",
            "If simulation shows PLI > 0.5, validates feasibility",
            "Then pursue Option B/C for empirical validation"
        ]
    }

    return design

def main():
    print("Thor Session #74: Coupled Instances Experiment Design")
    print("=" * 60)

    # Explore database
    print("\n1. MEMORY DATABASE EXPLORATION")
    print("=" * 60)
    try:
        explore_memory_db()
    except Exception as e:
        print(f"Database exploration failed: {e}")
        print("(Proceeding with experiment design anyway)")

    # Design experiment
    print("\n\n2. COUPLING EXPERIMENT DESIGN")
    print("=" * 60)
    design = design_coupling_experiment()

    print("\nResearch Question:")
    print(f"  {design['research_question']}")
    print(f"\nHypothesis:")
    print(f"  {design['hypothesis']}")

    print("\n\nExperimental Conditions:")
    for name, cond in design['experimental_conditions'].items():
        print(f"\n  {name.upper()}:")
        print(f"    Coupling: {cond['coupling']}")
        print(f"    Expected PLI: {cond['expected_pli']}")

    print("\n\nPredictions:")
    for pid, pred in design['predictions'].items():
        print(f"\n  {pid}: {pred['claim']}")
        print(f"    Test: {pred['test']}")
        print(f"    Falsify: {pred['falsify']}")

    print("\n\nRecommendation:")
    print(f"  {design['recommendation']}")
    for reason in design['rationale']:
        print(f"    - {reason}")

    # Save design
    with open('thor_session_74_coupled_instances_design.json', 'w') as f:
        json.dump(design, f, indent=2)

    print("\n\nDesign saved to: thor_session_74_coupled_instances_design.json")

    return design

if __name__ == '__main__':
    design = main()
