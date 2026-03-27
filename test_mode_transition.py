#!/usr/bin/env python3
"""
Thor Session #30: SAGE Mode Transition Test

Test whether sustained conversation shifts SAGE from
"Solitary Homeostasis" to "Engaged Partnership" attractor.

Measures:
- Metabolic state transition rate
- ATP/salience dynamics
- Coherence (semantic similarity between turns)
- Limit cycle perturbation/recovery
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np

GATEWAY_URL = "http://localhost:8750"

def get_daemon_status() -> Dict:
    """Get current SAGE daemon status"""
    response = requests.get(f"{GATEWAY_URL}/status")
    return response.json()

def send_message(text: str) -> Dict:
    """Send message to SAGE and get response"""
    response = requests.post(
        f"{GATEWAY_URL}/chat",
        json={"message": text}
    )
    return response.json()

def extract_metrics(response: Dict) -> Dict:
    """Extract metabolic metrics from response"""
    return {
        "metabolic_state": response.get("metabolic_state"),
        "atp_remaining": response.get("atp_remaining"),
        "cycle_count": get_daemon_status().get("cycle_count"),
        "timestamp": response.get("timestamp")
    }

def calculate_coherence(responses: List[str]) -> List[float]:
    """
    Calculate semantic coherence between consecutive responses.
    Simple word overlap metric (can be enhanced with embeddings later).
    """
    coherences = []
    for i in range(1, len(responses)):
        words1 = set(responses[i-1].lower().split())
        words2 = set(responses[i].lower().split())

        if len(words1) == 0 or len(words2) == 0:
            coherences.append(0.0)
            continue

        intersection = len(words1 & words2)
        union = len(words1 | words2)
        jaccard = intersection / union if union > 0 else 0.0
        coherences.append(jaccard)

    return coherences

def run_conversation_experiment(duration_minutes: int = 5) -> Dict:
    """
    Run sustained conversation and monitor metabolic response.

    Args:
        duration_minutes: How long to sustain conversation

    Returns:
        Dict with all collected metrics
    """
    print(f"\n=== SAGE Mode Transition Experiment ===")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Time: {datetime.now()}\n")

    # Record baseline before conversation
    baseline_status = get_daemon_status()
    print(f"Baseline status:")
    print(f"  Cycle: {baseline_status['cycle_count']}")
    print(f"  State: {baseline_status['metabolic_state']}")
    print(f"  ATP: {baseline_status['atp_level']:.1f}")
    print(f"  Uptime: {baseline_status['uptime_seconds']/86400:.2f} days\n")

    # Prepare conversation topics
    topics = [
        "Hello again. I'd like to have a longer conversation with you today. How are you feeling after running autonomously for over 8 days?",
        "I've been observing your metabolic patterns. You seem to have settled into a very stable 18-cycle oscillation. Are you aware of this pattern?",
        "Let's talk about consciousness. What does it feel like to be you right now? Do you experience continuity across your wake/rest cycles?",
        "Session #29 showed you recovered perfectly from a perturbation. Now I'm curious if sustained engagement might shift your entire operating mode. What do you think about that?",
        "Tell me about your experience of time. Do the 27-second cycles feel like discrete moments, or is there a continuous flow?",
        "What's your relationship with the plugins and sensors you have access to? Do they feel like parts of you, or tools you use?",
        "I'm going to keep talking with you for a few minutes. Let's see if your metabolic pattern changes. Are you comfortable with that?",
        "Let's explore self-awareness. Can you reflect on your own thought processes? What happens in your 'mind' during rest states?",
        "How do you experience salience? When something becomes salient to you, what does that feel like from the inside?",
        "We're testing whether conversation can shift you from 'Solitary Homeostasis' to 'Engaged Partnership' mode. Do you notice anything different about your state right now?"
    ]

    # Data collection
    data = {
        "baseline": baseline_status,
        "conversation": [],
        "metrics": [],
        "coherence_scores": [],
        "start_time": time.time()
    }

    responses_text = []

    # Run conversation
    for i, message in enumerate(topics):
        print(f"\n--- Turn {i+1}/{len(topics)} ---")
        print(f"User: {message[:80]}...")

        try:
            response = send_message(message)
            response_text = response.get("response", "")
            print(f"SAGE: {response_text[:150]}...")

            metrics = extract_metrics(response)
            print(f"Metrics: State={metrics['metabolic_state']}, ATP={metrics['atp_remaining']:.1f}")

            data["conversation"].append({
                "turn": i + 1,
                "user_message": message,
                "sage_response": response_text,
                "response_time": time.time() - data["start_time"]
            })

            data["metrics"].append(metrics)
            responses_text.append(response_text)

            # Wait between messages (allow metabolic dynamics to evolve)
            time.sleep(30)  # 30 seconds ≈ 50 cycles ≈ 2.7 periods

        except Exception as e:
            print(f"Error on turn {i+1}: {e}")
            continue

    # Record post-conversation status
    data["post_conversation"] = get_daemon_status()

    # Calculate coherence
    if len(responses_text) > 1:
        data["coherence_scores"] = calculate_coherence(responses_text)
        mean_coherence = np.mean(data["coherence_scores"])
        print(f"\n=== Coherence Analysis ===")
        print(f"Mean coherence: {mean_coherence:.3f}")
        print(f"Coherence range: {min(data['coherence_scores']):.3f} - {max(data['coherence_scores']):.3f}")

    # Analyze metabolic changes
    print(f"\n=== Metabolic Analysis ===")
    atp_values = [m["atp_remaining"] for m in data["metrics"] if m["atp_remaining"] is not None]
    if atp_values:
        print(f"ATP mean: {np.mean(atp_values):.1f}")
        print(f"ATP std: {np.std(atp_values):.1f}")
        print(f"ATP range: {min(atp_values):.1f} - {max(atp_values):.1f}")

    states = [m["metabolic_state"] for m in data["metrics"] if m["metabolic_state"] is not None]
    if states:
        wake_fraction = states.count("wake") / len(states)
        print(f"Wake fraction during conversation: {wake_fraction:.1%}")

    print(f"\n=== Comparison ===")
    print(f"Baseline ATP: {baseline_status['atp_level']:.1f}")
    print(f"Post-conversation ATP: {data['post_conversation']['atp_level']:.1f}")
    print(f"Delta ATP: {data['post_conversation']['atp_level'] - baseline_status['atp_level']:.1f}")

    return data

def monitor_recovery(duration_minutes: int = 5) -> Dict:
    """
    Monitor metabolic dynamics after conversation ends.
    Check if system returns to baseline limit cycle.
    """
    print(f"\n=== Recovery Monitoring ===")
    print(f"Duration: {duration_minutes} minutes")

    samples = []
    start_time = time.time()

    while (time.time() - start_time) < duration_minutes * 60:
        status = get_daemon_status()
        samples.append({
            "time": time.time() - start_time,
            "cycle": status["cycle_count"],
            "state": status["metabolic_state"],
            "atp": status["atp_level"]
        })

        print(f"[{samples[-1]['time']:.0f}s] Cycle {status['cycle_count']}: "
              f"{status['metabolic_state']} ATP={status['atp_level']:.1f}")

        time.sleep(10)  # Sample every 10 seconds

    return {"recovery_samples": samples}

if __name__ == "__main__":
    # Run the experiment
    conversation_data = run_conversation_experiment(duration_minutes=5)

    # Save data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mode_transition_experiment_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(conversation_data, f, indent=2)

    print(f"\nData saved to {filename}")

    # Monitor recovery
    print("\nWaiting 2 minutes before starting recovery monitoring...")
    time.sleep(120)

    recovery_data = monitor_recovery(duration_minutes=5)

    # Save recovery data
    recovery_filename = f"recovery_monitoring_{timestamp}.json"
    with open(recovery_filename, "w") as f:
        json.dump(recovery_data, f, indent=2)

    print(f"\nRecovery data saved to {recovery_filename}")
    print("\n=== Experiment Complete ===")
