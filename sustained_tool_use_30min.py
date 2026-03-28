#!/usr/bin/env python3
"""
Sustained Tool-Use Experiment - 30 Minute Version
Thor Session #36 - Simpler, more robust version of Session #35 experiment

Tests: Does sustained tool-use maintain wake elevation over 25 minutes?
"""

import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

# SAGE daemon endpoint
SAGE_URL = "http://localhost:8108/metabolic"

def get_metabolic_state():
    """Query SAGE metabolic state"""
    try:
        response = requests.get(SAGE_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error querying SAGE: {e}")
        return None

def sample_baseline(duration_sec=60, interval_sec=5):
    """Sample metabolic state during baseline period"""
    print(f"\n[Phase 1] Baseline measurement ({duration_sec} seconds)...")
    samples = []
    start_time = time.time()
    sample_num = 0

    while time.time() - start_time < duration_sec:
        state = get_metabolic_state()
        if state:
            samples.append({
                'sample': sample_num,
                'time': time.time(),
                'atp': state.get('atp', 0),
                'state': state.get('current_state', 'unknown'),
                'cycle': state.get('cycle', 0)
            })
            print(f"  Sample {sample_num + 1}/{duration_sec // interval_sec}: ATP={state.get('atp', 0):.1f}, State={state.get('current_state', 'unknown')}")

        sample_num += 1
        time.sleep(interval_sec)

    print(f"  Baseline complete: {time.time() - start_time:.1f}s\n")
    return samples

def run_conversation(questions, interval_sec=50):
    """
    Run tool-use conversation phase

    NOTE: This is a SIMULATION - we can't actually force Claude to answer questions
    from within a Python script. This would require manual conversation or API integration.

    For a real experiment, this function would:
    1. Present questions to Claude via API
    2. Sample state before each response
    3. Record response time and detect tool use
    4. Wait for interval before next question
    """
    print(f"[Phase 2] Sustained tool-use conversation starting...")
    print(f"  {len(questions)} questions over ~{len(questions) * interval_sec / 60:.1f} minutes")
    print()

    # Sample pre-conversation state
    samples = []

    print("  ⚠ SIMULATION MODE: This script cannot automatically conduct conversations")
    print("  Real experiment requires:")
    print("    - Claude API integration OR")
    print("    - Manual conversation with state sampling OR")
    print("    - Integration with existing conversation framework")
    print()
    print("  For proof-of-concept, we'll sample states over the time period without conversation.")
    print()

    start_time = time.time()

    for i, question in enumerate(questions):
        turn_start = time.time()

        # Sample pre-turn state
        pre_state = get_metabolic_state()

        print(f"  === Turn {i + 1}/{len(questions)} ({(time.time() - start_time) / 60:.1f} min) ===")
        print(f"      Type: {question['type']}, State: {pre_state.get('current_state', 'unknown') if pre_state else 'error'}, ATP: {pre_state.get('atp', 0):.1f if pre_state else 0}")

        # Record sample
        if pre_state:
            samples.append({
                'turn': i + 1,
                'time': time.time(),
                'question_type': question['type'],
                'pre_state': pre_state.get('current_state', 'unknown'),
                'pre_atp': pre_state.get('atp', 0),
                'pre_cycle': pre_state.get('cycle', 0)
            })

        # In real experiment: Present question, wait for response, record
        # For simulation: Just wait interval
        time.sleep(interval_sec)

    print(f"\n  Conversation complete: {(time.time() - start_time) / 60:.1f} min\n")
    return samples

def sample_recovery(duration_sec=600, interval_sec=10):
    """Sample metabolic state during recovery period"""
    print(f"[Phase 3] Recovery measurement ({duration_sec // 60} minutes)...")
    samples = []
    start_time = time.time()
    sample_num = 0

    while time.time() - start_time < duration_sec:
        state = get_metabolic_state()
        if state:
            samples.append({
                'sample': sample_num,
                'time': time.time(),
                'atp': state.get('atp', 0),
                'state': state.get('current_state', 'unknown'),
                'cycle': state.get('cycle', 0)
            })

            # Print every 30 seconds
            if sample_num % 3 == 0:
                print(f"  Recovery t+{(time.time() - start_time) / 60:.1f} min: ATP={state.get('atp', 0):.1f}, State={state.get('current_state', 'unknown')}")

        sample_num += 1
        time.sleep(interval_sec)

    print(f"  Recovery complete: {time.time() - start_time:.1f}s\n")
    return samples

def generate_questions():
    """Generate 30 tool-use questions across 4 types"""

    questions = []

    # Memory/episodic (40% = 12 questions)
    memory_questions = [
        "What were the key findings from Thor Session #31?",
        "What hypothesis was falsified in Session #31?",
        "What was the wake fraction in Session #32?",
        "What experimental design did Session #34 use?",
        "What was the primary finding of Session #34?",
        "Why did Session #35 fail?",
        "What is the Gnosis C = 0.50 hypothesis?",
        "What are the three metabolic states in SAGE?",
        "What is PolicyGate in SAGE architecture?",
        "What were Sessions #28-29 about?",
        "What is the modality hypothesis for wake states?",
        "What is hysteresis in the context of wake states?"
    ]

    # Calculation/reasoning (30% = 9 questions)
    calculation_questions = [
        "Calculate the ratio of wake fraction between Sessions #34 and #31",
        "If Session #34 had 14 wake samples out of 40, what percentage is that?",
        "Compare Session #32's 28.3% wake to Session #34's 35% wake",
        "If wake decays from 35% to 26.7% in 5 minutes, what's the decay rate?",
        "Estimate how many samples would be needed for 60 minutes at 30-second intervals",
        "What is 7 times 5.0%? (the effect size calculation)",
        "If ATP averages 45 with std 11, what's the coefficient of variation?",
        "Compare 30 minute duration to 34 minute duration as a percentage",
        "Calculate expected wake count if 30 samples at 35% wake fraction"
    ]

    # Sensor/status (20% = 6 questions)
    sensor_questions = [
        "What is the current ATP level?",
        "What is the current metabolic state?",
        "What is the current cycle count?",
        "What is the current system time?",
        "How long has the current SAGE instance been running?",
        "What is the current PolicyGate threshold?"
    ]

    # Meta-cognitive (10% = 3 questions)
    meta_questions = [
        "Why did you choose to analyze Sessions #31-34 data?",
        "What is the most important finding from the tool-use research?",
        "What experiment should be run next and why?"
    ]

    # Combine and tag
    for q in memory_questions:
        questions.append({'type': 'memory', 'question': q})
    for q in calculation_questions:
        questions.append({'type': 'calculation', 'question': q})
    for q in sensor_questions:
        questions.append({'type': 'sensor', 'question': q})
    for q in meta_questions:
        questions.append({'type': 'meta', 'question': q})

    return questions

def main():
    """Run 30-minute sustained tool-use experiment"""

    print("=" * 70)
    print("SUSTAINED TOOL-USE EXPERIMENT - 30 Minute Version")
    print("Thor Session #36")
    print("=" * 70)
    print("Duration: ~35 minutes (1 min baseline + 25 min conversation + 10 min recovery)")
    print("Questions: 30")
    print("Hypothesis: Sustained tool-use maintains wake elevation (~30%)")
    print("=" * 70)
    print()

    # Check if SAGE is running
    initial_state = get_metabolic_state()
    if not initial_state:
        print("ERROR: Cannot connect to SAGE daemon at", SAGE_URL)
        print("Make sure SAGE is running: cd ~/ai-workspace/SAGE && python3 -m sage.gateway.sage_daemon")
        sys.exit(1)

    print(f"✓ SAGE daemon connected (ATP={initial_state.get('atp', 0):.1f}, State={initial_state.get('current_state', 'unknown')})")
    print()

    # Generate questions
    questions = generate_questions()
    print(f"✓ Generated {len(questions)} questions")
    print(f"  Memory: {sum(1 for q in questions if q['type'] == 'memory')}")
    print(f"  Calculation: {sum(1 for q in questions if q['type'] == 'calculation')}")
    print(f"  Sensor: {sum(1 for q in questions if q['type'] == 'sensor')}")
    print(f"  Meta: {sum(1 for q in questions if q['type'] == 'meta')}")
    print()

    # Run experiment
    experiment_start = time.time()

    # Phase 1: Baseline
    baseline_samples = sample_baseline(duration_sec=60, interval_sec=5)

    # Phase 2: Conversation
    print("⚠ NOTE: This is a SIMULATION")
    print("For real experiment, replace run_conversation() with actual Claude API integration")
    print()
    conversation_samples = run_conversation(questions, interval_sec=50)

    # Phase 3: Recovery
    recovery_samples = sample_recovery(duration_sec=600, interval_sec=10)

    experiment_duration = time.time() - experiment_start

    print("=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)
    print(f"Total duration: {experiment_duration / 60:.1f} minutes")
    print(f"Baseline samples: {len(baseline_samples)}")
    print(f"Conversation samples: {len(conversation_samples)}")
    print(f"Recovery samples: {len(recovery_samples)}")
    print()

    # Save results
    results = {
        'experiment': 'sustained_tool_use_30min',
        'date': datetime.now().isoformat(),
        'duration_minutes': experiment_duration / 60,
        'hypothesis': 'Sustained tool-use maintains wake elevation over 25 minutes',
        'phases': {
            'baseline': baseline_samples,
            'conversation': conversation_samples,
            'recovery': recovery_samples
        },
        'questions': questions,
        'summary': {
            'total_questions': len(questions),
            'baseline_samples': len(baseline_samples),
            'conversation_samples': len(conversation_samples),
            'recovery_samples': len(recovery_samples)
        }
    }

    # Compute basic statistics
    if baseline_samples:
        wake_baseline = sum(1 for s in baseline_samples if s.get('state') == 'wake')
        results['summary']['baseline_wake_fraction'] = wake_baseline / len(baseline_samples)

    if conversation_samples:
        wake_conv = sum(1 for s in conversation_samples if s.get('pre_state') == 'wake')
        results['summary']['conversation_wake_fraction'] = wake_conv / len(conversation_samples)

    if recovery_samples:
        wake_recovery = sum(1 for s in recovery_samples if s.get('state') == 'wake')
        results['summary']['recovery_wake_fraction'] = wake_recovery / len(recovery_samples)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"sustained_tool_use_30min_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()

    # Print summary statistics
    if 'baseline_wake_fraction' in results['summary']:
        print(f"Baseline wake: {results['summary']['baseline_wake_fraction']:.1%}")
    if 'conversation_wake_fraction' in results['summary']:
        print(f"Conversation wake: {results['summary']['conversation_wake_fraction']:.1%}")
    if 'recovery_wake_fraction' in results['summary']:
        print(f"Recovery wake: {results['summary']['recovery_wake_fraction']:.1%}")

    print()
    print("NOTE: This was a SIMULATION (state sampling without conversation)")
    print("For real experiment, integrate with Claude API or conduct manual conversation")
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
