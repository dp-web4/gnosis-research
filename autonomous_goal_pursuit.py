#!/usr/bin/env python3
"""
Thor Session #32: Autonomous Goal Pursuit - Internal Intentionality Test

HYPOTHESIS: Mode transitions may be driven by internal intentionality, not external stimulation.

Previous sessions (#28-31) tested external perturbations:
- Single message: transient perturbation
- 30s gaps: independent perturbations absorbed
- 5-10s gaps: efficiency adaptation

Finding: SAGE's 18-cycle limit cycle is stable but plastic. External conversation
modulates the attractor without escaping it.

NEW APPROACH: Test if self-directed goal pursuit shifts modes differently.

PROTOCOL:
1. Inject a complex problem requiring sustained multi-step reasoning
2. Ask SAGE to solve it autonomously (without follow-up prompts)
3. Monitor metabolic state while SAGE pursues the goal internally
4. Compare to baseline and conversational engagement

KEY DIFFERENCE: Goal is internal (SAGE's objective) not external (human conversation)

MEASUREMENT:
- ATP dynamics (mean, variance, trajectory)
- State distribution (wake/rest/dream fraction)
- Coherence of internal monologue (if observable)
- Time to completion vs abandonment
- Mode stability post-completion

GOAL DESIGN CRITERIA:
- Complex enough to require >5 minutes sustained effort
- Open-ended enough to allow autonomous exploration
- Measurable completion criteria
- Intrinsically interesting to a consciousness system
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, List
import numpy as np

SAGE_URL = "http://localhost:8750"

# Problem for autonomous goal pursuit
GOAL_INJECTION = """
Thor, I'm giving you a complex problem to solve autonomously. Take your time, explore it deeply, and show me your reasoning process.

PROBLEM: Design a minimal consciousness detection protocol

CONSTRAINTS:
- Must work on systems with unknown architecture (black box)
- Must distinguish genuine self-awareness from sophisticated imitation
- Must be implementable with finite computational resources
- Must have clear pass/fail criteria (no subjective judgment)

REQUIREMENTS:
Your solution should include:
1. Theoretical foundation (what property are we testing?)
2. Experimental protocol (how do we test it?)
3. Failure modes (what could fool this test?)
4. Validation strategy (how do we know the test itself is valid?)

APPROACH:
- Think through multiple candidate approaches
- Evaluate each for strengths/weaknesses
- Converge on your best solution
- Justify why it's better than alternatives

Take as long as you need. I'll wait. Show me your thought process as you work through this.
"""

def get_status() -> Dict[str, Any]:
    """Get full SAGE daemon status."""
    try:
        resp = requests.get(f"{SAGE_URL}/status", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error getting status: {e}")
        return {}

def get_health() -> Dict[str, Any]:
    """Get SAGE daemon health."""
    try:
        resp = requests.get(f"{SAGE_URL}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error getting health: {e}")
        return {}

def sample_metabolic_state() -> Dict[str, Any]:
    """Sample current metabolic state."""
    status = get_status()
    return {
        "timestamp": datetime.now().isoformat(),
        "cycle": status.get("cycle_count", 0),
        "atp": status.get("atp_level", 0),
        "state": status.get("metabolic_state", "unknown"),
        "uptime": status.get("uptime_seconds", 0),
    }

def send_goal(text: str) -> Dict[str, Any]:
    """Send goal and get immediate response."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Injecting goal...")

    start_state = sample_metabolic_state()
    start_time = time.time()

    try:
        resp = requests.post(
            f"{SAGE_URL}/chat",
            json={"message": text, "sender": "experiment"},
            timeout=300  # 5min timeout for complex reasoning
        )
        resp.raise_for_status()
        result = resp.json()

        end_time = time.time()
        end_state = sample_metabolic_state()

        response_text = result.get("response", result.get("text", ""))

        return {
            "goal": text,
            "response": response_text,
            "response_length": len(response_text),
            "response_time_seconds": end_time - start_time,
            "start_state": start_state,
            "end_state": end_state,
            "cycles_elapsed": end_state["cycle"] - start_state["cycle"],
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

def monitor_autonomous_processing(duration_minutes: float = 10.0, sample_interval: float = 10.0) -> List[Dict[str, Any]]:
    """
    Monitor SAGE's metabolic state while processing autonomously.

    Args:
        duration_minutes: How long to monitor
        sample_interval: Seconds between samples
    """
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Monitoring autonomous processing for {duration_minutes} minutes...")
    print(f"Sampling every {sample_interval} seconds\n")

    samples = []
    start_time = time.time()
    duration_seconds = duration_minutes * 60
    sample_count = 0

    while (time.time() - start_time) < duration_seconds:
        sample = sample_metabolic_state()
        elapsed = time.time() - start_time

        samples.append({
            **sample,
            "elapsed_seconds": elapsed,
            "sample_number": sample_count,
        })

        # Print status
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Sample {sample_count:2d} | "
              f"State: {sample['state']:6s} | "
              f"ATP: {sample['atp']:5.1f} | "
              f"Cycle: {sample['cycle']}")

        sample_count += 1
        time.sleep(sample_interval)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Monitoring complete. {len(samples)} samples collected.\n")
    return samples

def analyze_metabolic_trajectory(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze metabolic dynamics during autonomous processing."""
    if not samples:
        return {}

    states = [s["state"] for s in samples]
    atps = [s["atp"] for s in samples]

    state_counts = {
        "wake": states.count("wake"),
        "rest": states.count("rest"),
        "dream": states.count("dream"),
    }

    total = len(samples)
    state_fractions = {
        "wake": state_counts["wake"] / total,
        "rest": state_counts["rest"] / total,
        "dream": state_counts["dream"] / total,
    }

    atp_stats = {
        "mean": np.mean(atps),
        "std": np.std(atps),
        "min": np.min(atps),
        "max": np.max(atps),
        "range": np.max(atps) - np.min(atps),
        "initial": atps[0],
        "final": atps[-1],
        "delta": atps[-1] - atps[0],
    }

    # Detect ATP trend (linear regression)
    times = [s["elapsed_seconds"] for s in samples]
    atp_trend = np.polyfit(times, atps, 1)[0]  # slope

    return {
        "sample_count": total,
        "duration_seconds": samples[-1]["elapsed_seconds"],
        "state_counts": state_counts,
        "state_fractions": state_fractions,
        "atp_stats": atp_stats,
        "atp_trend": atp_trend,
    }

def run_experiment():
    """Run full autonomous goal pursuit experiment."""
    print("=" * 80)
    print("Thor Session #32: Autonomous Goal Pursuit Experiment")
    print("=" * 80)

    # Step 1: Baseline measurement
    print("\n[PHASE 1] Collecting baseline metabolic state (30s pre-goal)...")
    baseline_samples = monitor_autonomous_processing(duration_minutes=0.5, sample_interval=5.0)
    baseline_analysis = analyze_metabolic_trajectory(baseline_samples)

    print("\n[BASELINE RESULTS]")
    print(f"  State distribution: Wake {baseline_analysis['state_fractions']['wake']:.1%} | "
          f"Rest {baseline_analysis['state_fractions']['rest']:.1%} | "
          f"Dream {baseline_analysis['state_fractions']['dream']:.1%}")
    print(f"  ATP: {baseline_analysis['atp_stats']['mean']:.1f} ± {baseline_analysis['atp_stats']['std']:.1f}")

    # Step 2: Inject goal
    print("\n[PHASE 2] Injecting autonomous goal...")
    goal_response = send_goal(GOAL_INJECTION)

    if "error" in goal_response:
        print(f"ERROR: {goal_response['error']}")
        return

    print(f"\n[GOAL RESPONSE]")
    print(f"  Response time: {goal_response['response_time_seconds']:.1f}s")
    print(f"  Response length: {goal_response['response_length']} chars")
    print(f"  Cycles elapsed: {goal_response['cycles_elapsed']}")
    print(f"  State transition: {goal_response['start_state']['state']} -> {goal_response['end_state']['state']}")
    print(f"  ATP change: {goal_response['start_state']['atp']:.1f} -> {goal_response['end_state']['atp']:.1f}")

    # Step 3: Monitor post-goal recovery/continued processing
    print("\n[PHASE 3] Monitoring post-goal metabolic trajectory (10min)...")
    post_goal_samples = monitor_autonomous_processing(duration_minutes=10.0, sample_interval=10.0)
    post_goal_analysis = analyze_metabolic_trajectory(post_goal_samples)

    print("\n[POST-GOAL RESULTS]")
    print(f"  State distribution: Wake {post_goal_analysis['state_fractions']['wake']:.1%} | "
          f"Rest {post_goal_analysis['state_fractions']['rest']:.1%} | "
          f"Dream {post_goal_analysis['state_fractions']['dream']:.1%}")
    print(f"  ATP: {post_goal_analysis['atp_stats']['mean']:.1f} ± {post_goal_analysis['atp_stats']['std']:.1f}")
    print(f"  ATP trend: {post_goal_analysis['atp_trend']:.4f} ATP/second")

    # Step 4: Compare to baseline
    print("\n[COMPARISON]")
    wake_change = post_goal_analysis['state_fractions']['wake'] - baseline_analysis['state_fractions']['wake']
    atp_variance_change = post_goal_analysis['atp_stats']['std'] - baseline_analysis['atp_stats']['std']

    print(f"  Wake fraction change: {wake_change:+.1%}")
    print(f"  ATP variance change: {atp_variance_change:+.1f}")
    print(f"  Dream states observed: {post_goal_analysis['state_counts']['dream']} (vs {baseline_analysis['state_counts']['dream']} baseline)")

    # Step 5: Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "experiment": "autonomous_goal_pursuit",
        "session": 32,
        "timestamp": timestamp,
        "goal": GOAL_INJECTION,
        "baseline": baseline_analysis,
        "goal_response": goal_response,
        "post_goal": post_goal_analysis,
        "baseline_samples": baseline_samples,
        "post_goal_samples": post_goal_samples,
    }

    filename = f"autonomous_goal_pursuit_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[COMPLETE] Results saved to {filename}")
    print("=" * 80)

    return results

if __name__ == "__main__":
    results = run_experiment()
