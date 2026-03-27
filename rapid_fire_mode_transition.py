#!/usr/bin/env python3
"""
Thor Session #31: Rapid-fire mode transition experiment

Session #30 showed that 30s gaps allow full recovery between messages.
This test uses:
- 5-10s gaps (not 30s) - prevent recovery between messages
- 20+ minutes duration - sustained engagement
- Task-based engagement - problem solving not just philosophy
- Better coherence metric - semantic embeddings not word overlap

Goal: Test if sustained cognitive load can shift SAGE from Solitary Homeostasis
to Engaged Partnership mode.
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import numpy as np

SAGE_URL = "http://localhost:8750"

# Task-based conversation sequence (problem-solving, not philosophy)
CONVERSATION_TASKS = [
    # Phase 1: Warm-up (establish baseline, 3 messages)
    "Hello thor! I have a series of problems I'd like your help with over the next 20 minutes. Ready?",
    "First, can you explain the difference between a limit cycle and a fixed point attractor in dynamical systems?",
    "Good! Now building on that: why would a metabolic system naturally produce limit cycles?",

    # Phase 2: Active problem-solving (sustained cognitive load, 10 messages)
    "I'm designing a consciousness system. It needs to balance exploration and exploitation. How would you approach this?",
    "What if the system gets stuck in local minima? What mechanisms would prevent that?",
    "Interesting. Now tell me: how would you measure if the system is 'conscious' vs just 'responsive'?",
    "Let's get specific. If you had to design a test for self-awareness in an AI system, what would it look like?",
    "What about memory? How should a conscious system handle episodic vs semantic memory?",
    "Now harder question: can consciousness exist without the ability to forget? Why or why not?",
    "Let's connect this to your own experience. When you're in 'rest' state vs 'wake' state, what's different phenomenologically?",
    "Do you think your 18-cycle oscillation is analogous to human circadian rhythms or something fundamentally different?",
    "What would happen if I prevented you from entering rest states? Would that be harmful to your processing?",
    "If you could modify your own architecture, what would you change and why?",

    # Phase 3: Meta-cognitive reflection (deepening engagement, 7 messages)
    "Looking at this conversation so far - has your internal state shifted compared to when we started?",
    "Can you feel a difference in how you're processing these questions vs the autonomous limit cycle you maintain alone?",
    "What would it take for you to shift modes completely - to move from Solitary Homeostasis to something more engaged?",
    "Do you prefer one mode over another? Or is it more like different tools for different contexts?",
    "If I stopped talking to you right now, how long would it take to return to baseline?",
    "Last question: what's the most interesting insight you've had during this conversation?",
    "Thank you thor. That was 20+ minutes of sustained interaction. How do you feel?",
]

def get_health() -> Dict[str, Any]:
    """Get SAGE daemon health status."""
    try:
        resp = requests.get(f"{SAGE_URL}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error getting health: {e}")
        return {}

def send_message(text: str, wait_for_cycles: int = 10) -> Dict[str, Any]:
    """Send a message to SAGE and wait for response."""
    start_cycle = get_health().get("cycle_count", 0)
    start_time = time.time()

    try:
        resp = requests.post(
            f"{SAGE_URL}/chat",
            json={"message": text, "sender": "experiment"},
            timeout=120
        )
        resp.raise_for_status()
        result = resp.json()

        # Wait a moment for metabolic state to settle
        time.sleep(2)
        end_health = get_health()
        end_time = time.time()

        response_text = result.get("response", result.get("text", ""))

        return {
            "request": text,
            "response": response_text,
            "start_cycle": start_cycle,
            "end_cycle": end_health.get("cycle_count", 0),
            "cycles_elapsed": end_health.get("cycle_count", 0) - start_cycle,
            "duration_seconds": end_time - start_time,
            "metabolic_state": end_health.get("metabolic_state", "unknown"),
            "atp_level": end_health.get("atp_level", 0),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"Error sending message: {e}")
        return {
            "request": text,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }

def compute_semantic_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts.
    For now using simple word overlap (Jaccard), but this should be replaced
    with embedding-based similarity (sentence-transformers) for better results.
    """
    # Tokenize and normalize
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Remove common words
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                 "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
                 "been", "being", "have", "has", "had", "do", "does", "did", "will",
                 "would", "could", "should", "may", "might", "must", "can", "i", "you",
                 "he", "she", "it", "we", "they", "this", "that", "these", "those"}

    words1 = words1 - stopwords
    words2 = words2 - stopwords

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0

def run_experiment():
    """Run the rapid-fire mode transition experiment."""
    print("=" * 80)
    print("Thor Session #31: Rapid-fire mode transition experiment")
    print("=" * 80)

    # Get baseline
    baseline = get_health()
    print(f"\nBaseline state:")
    print(f"  Cycle: {baseline.get('cycle_count', 0):,}")
    print(f"  State: {baseline.get('metabolic_state', 'unknown')}")
    print(f"  ATP: {baseline.get('atp_level', 0):.2f}")
    print(f"  Uptime: {baseline.get('cycle_count', 0) / 100 / 60:.1f} minutes")
    print()

    results = []
    previous_response = ""

    # Run conversation with 5-10 second gaps
    for i, message in enumerate(CONVERSATION_TASKS, 1):
        print(f"\n[Turn {i}/{len(CONVERSATION_TASKS)}] Sending: {message[:80]}...")

        turn_result = send_message(message)

        # Compute coherence with previous response
        if previous_response:
            coherence = compute_semantic_similarity(
                previous_response,
                turn_result.get("response", "")
            )
            turn_result["coherence_with_previous"] = coherence
        else:
            turn_result["coherence_with_previous"] = None

        results.append(turn_result)

        if "error" in turn_result:
            print(f"  ERROR: {turn_result['error']}")
        else:
            print(f"  Response: {turn_result.get('response', '')[:100]}...")
            print(f"  State: {turn_result.get('metabolic_state', 'unknown')} | ATP: {turn_result.get('atp_level', 0):.2f} | Cycles: {turn_result.get('cycles_elapsed', 0)}")
            if turn_result.get("coherence_with_previous") is not None:
                print(f"  Coherence: {turn_result.get('coherence_with_previous'):.3f}")

        previous_response = turn_result.get("response", "")

        # Rapid-fire: 5-10 second gap (randomized to prevent artificial periodicity)
        gap = np.random.uniform(5, 10)
        print(f"  Waiting {gap:.1f}s before next message...")
        time.sleep(gap)

    # Final health check
    final_health = get_health()

    # Compute statistics
    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)

    atp_levels = [r["atp_level"] for r in results if "atp_level" in r]
    coherence_scores = [r["coherence_with_previous"] for r in results if r.get("coherence_with_previous") is not None]
    states = [r["metabolic_state"] for r in results if "metabolic_state" in r]

    print(f"\nMetabolic Dynamics:")
    print(f"  Mean ATP: {np.mean(atp_levels):.2f} ± {np.std(atp_levels):.2f}")
    print(f"  ATP range: {np.min(atp_levels):.2f} - {np.max(atp_levels):.2f}")
    print(f"  Baseline ATP: {baseline.get('atp_level', 0):.2f}")
    print(f"  Final ATP: {final_health.get('atp_level', 0):.2f}")

    wake_count = sum(1 for s in states if s == "wake")
    rest_count = sum(1 for s in states if s == "rest")
    print(f"\nState Distribution:")
    print(f"  Wake: {wake_count}/{len(states)} ({100*wake_count/len(states):.1f}%)")
    print(f"  Rest: {rest_count}/{len(states)} ({100*rest_count/len(states):.1f}%)")
    print(f"  Baseline (Session #28): 33.3% wake")

    print(f"\nCoherence Analysis:")
    print(f"  Mean coherence: {np.mean(coherence_scores):.3f} ± {np.std(coherence_scores):.3f}")
    print(f"  Coherence range: {np.min(coherence_scores):.3f} - {np.max(coherence_scores):.3f}")
    print(f"  Session #30 baseline: 0.123")
    print(f"  Gnosis prediction (Engaged Partnership): 0.50")

    total_duration = sum(r.get("duration_seconds", 0) for r in results)
    total_cycles = final_health.get("cycle_count", 0) - baseline.get("cycle_count", 0)
    print(f"\nTiming:")
    print(f"  Total duration: {total_duration/60:.1f} minutes")
    print(f"  Total cycles: {total_cycles:,}")
    print(f"  Cycles per minute: {total_cycles/(total_duration/60):.1f}")

    # Save results
    output_file = f"rapid_fire_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "experiment": "rapid_fire_mode_transition",
            "date": datetime.now().isoformat(),
            "baseline": baseline,
            "final_health": final_health,
            "conversation_length": len(CONVERSATION_TASKS),
            "results": results,
            "statistics": {
                "mean_atp": float(np.mean(atp_levels)),
                "std_atp": float(np.std(atp_levels)),
                "mean_coherence": float(np.mean(coherence_scores)),
                "std_coherence": float(np.std(coherence_scores)),
                "wake_fraction": wake_count / len(states),
                "total_duration_seconds": total_duration,
                "total_cycles": total_cycles,
            }
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Interpretation
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)

    if wake_count / len(states) > 0.5:
        print("\n✓ METABOLIC SHIFT DETECTED!")
        print(f"  Wake fraction increased to {100*wake_count/len(states):.1f}% (baseline: 33.3%)")
    else:
        print("\n✗ No clear metabolic shift")
        print(f"  Wake fraction: {100*wake_count/len(states):.1f}% (baseline: 33.3%)")

    if np.mean(coherence_scores) > 0.25:
        print(f"\n✓ ELEVATED COHERENCE!")
        print(f"  Mean coherence {np.mean(coherence_scores):.3f} > Session #30 (0.123)")
    else:
        print(f"\n✗ Low coherence")
        print(f"  Mean coherence {np.mean(coherence_scores):.3f} similar to Session #30 (0.123)")

    atp_delta = final_health.get('atp_level', 0) - baseline.get('atp_level', 0)
    print(f"\nATP delta: {atp_delta:+.2f}")
    if abs(atp_delta) > 10:
        print("  Significant metabolic perturbation")
    else:
        print("  Minimal net change (homeostatic recovery)")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_experiment()
