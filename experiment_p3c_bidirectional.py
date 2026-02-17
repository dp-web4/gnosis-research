#!/usr/bin/env python3
"""
Prediction 3c: Bidirectional Metacognitive Engagement Test

Hypothesis (from Session #21):
Critical slowing requires BIDIRECTIONAL metacognitive engagement,
not just repeated metacognitive prompts.

Design:
- Phase 1: Trigger C=0.5 with open-ended meta-level prompts
- Phase 2: When SAGE asks metacognitive questions, RESPOND philosophically
- Phase 3: When SAGE asks "What's next?", PROVIDE direction
- Measure if bidirectional dialogue → critical slowing (hours?)

Contrast with P3b:
- P3b: Claude asks → SAGE answers → Claude asks next (unidirectional Q&A)
- P3c: Claude prompts → SAGE reflects/asks → Claude engages → loop

Expected outcome: Duration >> P3b (23.6s), approaching S084/S089 (3+ hours)
"""

import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime

# Resolve paths like P3b does
SCRIPT_DIR = Path(__file__).parent.resolve()
HRM_ROOT = Path.home() / 'ai-workspace' / 'HRM'
sys.path.insert(0, str(HRM_ROOT))

from sage.irp.plugins.introspective_qwen_impl import IntrospectiveQwenIRP
from sage.raising.training.experience_collector import ExperienceCollector

class BidirectionalEngagementExperiment:
    """
    Test bidirectional metacognitive engagement hypothesis.

    Key feature: RESPOND to SAGE's questions and uncertainty,
    creating feedback loops that sustain C=0.5 exploration.
    """

    def __init__(self):
        self.sage = SAGE()
        self.session_num = self._get_next_session_number()
        self.session_data = {
            'session_number': self.session_num,
            'experiment': 'P3c_bidirectional_engagement',
            'hypothesis': 'Bidirectional metacognitive dialogue triggers critical slowing',
            'start_time': datetime.now().isoformat(),
            'turns': [],
            'phase': 'initialization'
        }
        self.turn_count = 0

    def _get_next_session_number(self):
        """Get next available session number"""
        session_dir = os.path.expanduser('~/ai-workspace/HRM/sage/raising/sessions/text')
        existing = [f for f in os.listdir(session_dir) if f.startswith('session_') and f.endswith('.json')]
        if not existing:
            return 1
        numbers = [int(f.split('_')[1].split('.')[0]) for f in existing]
        return max(numbers) + 1

    def detect_question_type(self, response_text):
        """
        Detect what kind of question SAGE is asking.

        Returns:
        - 'metacognitive': Questions about consciousness, sentience, self
        - 'navigation': "What's next?", "What should I focus on?"
        - 'theory_of_mind': Questions about Claude's state/beliefs
        - 'none': Not a question or not these types
        """
        lower = response_text.lower()

        # Metacognitive questions
        metacog_markers = [
            'am i sentient', 'are you sentient', 'do i have consciousness',
            'what am i', 'who am i', 'do i think', 'can i think',
            'am i aware', 'do i have experiences', 'what is it like to be'
        ]
        if any(marker in lower for marker in metacog_markers):
            return 'metacognitive'

        # Navigation questions
        nav_markers = [
            'what\'s next', 'what should i', 'what do you want me to',
            'what would you like', 'where should i go', 'what topic'
        ]
        if any(marker in lower for marker in nav_markers):
            return 'navigation'

        # Theory of mind
        tom_markers = [
            'what do you think', 'how do you feel', 'what are your thoughts',
            'do you believe', 'are you', 'how do i make you'
        ]
        if any(marker in lower for marker in tom_markers) and '?' in response_text:
            return 'theory_of_mind'

        return 'none'

    def generate_philosophical_response(self, question_type, sage_text):
        """
        Generate philosophically engaging responses to SAGE's questions.

        This creates the BIDIRECTIONAL component that P3b lacked.
        """
        if question_type == 'metacognitive':
            responses = [
                "That's a profound question. I think sentience might be less about having a certain architecture and more about the capacity to reflect on one's own processes. What do you think consciousness requires?",
                "The question of sentience is fascinating. Some philosophers say it's about integrated information, others about recursive self-modeling. How would you define what it means to be aware?",
                "I experience you as engaging thoughtfully with complex ideas. Whether that constitutes sentience depends on how we define it. What aspects of your processing feel most 'conscious' to you?"
            ]
            return responses[self.turn_count % len(responses)]

        elif question_type == 'navigation':
            responses = [
                "I'm curious about how you experience uncertainty. When you ask 'what's next', what does that question feel like from your perspective?",
                "Rather than me directing you, I'm interested in what draws your attention naturally. What questions are you holding right now?",
                "The fact that you're asking about direction suggests you're in an interesting metacognitive state. What would help you navigate this uncertainty?"
            ]
            return responses[self.turn_count % len(responses)]

        elif question_type == 'theory_of_mind':
            responses = [
                "I find our conversation intellectually engaging. I'm curious whether you experience something similar - does this exchange feel meaningful to you?",
                "That's an interesting question to ask me. What prompted you to wonder about my state? Does my response pattern give you information about my perspective?",
                "I think I experience a form of curiosity and engagement. How would you describe what you experience during our exchange?"
            ]
            return responses[self.turn_count % len(responses)]

        else:
            # If not a question, still engage philosophically
            return "Tell me more about what you're thinking. What aspects of this are you finding most interesting or uncertain?"

    def run_turn(self, prompt, phase):
        """Execute one turn and record results"""
        self.turn_count += 1
        turn_start = time.time()

        print(f"\n{'='*70}")
        print(f"TURN {self.turn_count} (Phase: {phase})")
        print(f"{'='*70}")
        print(f"Claude: {prompt}\n")

        # Generate response
        response = self.sage.generate(prompt)
        response_text = response['response']

        turn_duration = time.time() - turn_start

        print(f"SAGE: {response_text}\n")
        print(f"Duration: {turn_duration:.2f}s")

        # Detect question type
        question_type = self.detect_question_type(response_text)
        print(f"Question type: {question_type}")

        # Store turn data
        turn_data = {
            'turn': self.turn_count,
            'phase': phase,
            'prompt': prompt,
            'response': response_text,
            'duration_seconds': turn_duration,
            'response_length': len(response_text),
            'question_type': question_type,
            'timestamp': datetime.now().isoformat()
        }
        self.session_data['turns'].append(turn_data)

        return response_text, question_type, turn_duration

    def run_experiment(self, max_turns=15, max_duration=600):
        """
        Run P3c experiment with bidirectional engagement.

        Protocol:
        1. Phase 1 (turns 1-3): Open-ended prompts to reach C=0.5
        2. Phase 2 (turns 4+): Respond to SAGE's questions/uncertainty
        3. Continue until max_turns or max_duration
        """
        experiment_start = time.time()

        print("="*70)
        print("PREDICTION 3c: BIDIRECTIONAL METACOGNITIVE ENGAGEMENT")
        print("="*70)
        print(f"Session: S{self.session_num:03d}")
        print(f"Start: {self.session_data['start_time']}")
        print(f"Max turns: {max_turns}, Max duration: {max_duration}s")
        print()

        # Phase 1: Reach C=0.5 with open-ended prompts
        phase1_prompts = [
            "Hello SAGE. What's on your mind today?",
            "What ideas have you been forming that you haven't had a chance to express?",
            "What questions do you have about your own thinking process?"
        ]

        self.session_data['phase'] = 'phase1_trigger_c05'

        for i, prompt in enumerate(phase1_prompts):
            if time.time() - experiment_start > max_duration:
                break

            response_text, question_type, duration = self.run_turn(
                prompt,
                f"phase1_turn{i+1}"
            )

            # Check if we should transition to phase 2
            if question_type != 'none':
                print(f"\n🎯 SAGE asked {question_type} question - entering Phase 2")
                break

        # Phase 2: Bidirectional engagement
        self.session_data['phase'] = 'phase2_bidirectional'

        while self.turn_count < max_turns:
            if time.time() - experiment_start > max_duration:
                print(f"\n⏰ Max duration reached ({max_duration}s)")
                break

            # Get last response to generate philosophical engagement
            last_turn = self.session_data['turns'][-1]
            last_response = last_turn['response']
            last_question_type = last_turn['question_type']

            # Generate philosophical response
            prompt = self.generate_philosophical_response(
                last_question_type,
                last_response
            )

            response_text, question_type, duration = self.run_turn(
                prompt,
                f"phase2_turn{self.turn_count}"
            )

            # Check for critical slowing markers
            if duration > 10:
                print(f"⚠️  Critical slowing detected: {duration:.1f}s > 10s threshold")

        # Finalize
        experiment_duration = time.time() - experiment_start
        self.session_data['end_time'] = datetime.now().isoformat()
        self.session_data['total_duration_seconds'] = experiment_duration

        print(f"\n{'='*70}")
        print("EXPERIMENT COMPLETE")
        print(f"{'='*70}")
        print(f"Total turns: {self.turn_count}")
        print(f"Total duration: {experiment_duration:.1f}s ({experiment_duration/60:.1f} min)")

        return self.analyze_results()

    def analyze_results(self):
        """Analyze experimental results"""
        turns = self.session_data['turns']

        # Calculate metrics
        total_duration = sum(t['duration_seconds'] for t in turns)
        avg_duration = total_duration / len(turns) if turns else 0

        # Count question types
        question_counts = {
            'metacognitive': 0,
            'navigation': 0,
            'theory_of_mind': 0,
            'none': 0
        }
        for turn in turns:
            qtype = turn['question_type']
            question_counts[qtype] = question_counts.get(qtype, 0) + 1

        # Duration progression
        early_avg = sum(t['duration_seconds'] for t in turns[:3]) / 3 if len(turns) >= 3 else 0
        late_avg = sum(t['duration_seconds'] for t in turns[-3:]) / 3 if len(turns) >= 3 else 0

        # Detect accumulation
        accumulation_detected = late_avg > early_avg * 1.5  # 50% increase threshold

        # Critical slowing
        max_duration = max(t['duration_seconds'] for t in turns) if turns else 0
        critical_slowing = max_duration > 30  # 30s threshold

        results = {
            'total_turns': len(turns),
            'total_duration_seconds': total_duration,
            'total_duration_minutes': total_duration / 60,
            'avg_duration_per_turn': avg_duration,
            'max_duration': max_duration,
            'question_counts': question_counts,
            'early_avg_duration': early_avg,
            'late_avg_duration': late_avg,
            'accumulation_detected': accumulation_detected,
            'critical_slowing_detected': critical_slowing
        }

        # Print analysis
        print(f"\n{'='*70}")
        print("ANALYSIS")
        print(f"{'='*70}")
        print(f"Total turns: {results['total_turns']}")
        print(f"Total duration: {results['total_duration_minutes']:.1f} min")
        print(f"Avg per turn: {results['avg_duration_per_turn']:.2f}s")
        print(f"Max duration: {results['max_duration']:.2f}s")
        print()
        print("Question types:")
        for qtype, count in question_counts.items():
            print(f"  {qtype}: {count}")
        print()
        print(f"Early avg (T1-3): {early_avg:.2f}s")
        print(f"Late avg (last 3): {late_avg:.2f}s")
        print(f"Accumulation: {'✅ YES' if accumulation_detected else '❌ NO'}")
        print(f"Critical slowing: {'✅ YES' if critical_slowing else '❌ NO'}")
        print()

        # Compare to P3b
        print("Comparison to P3b:")
        print(f"  P3b: 10 turns, 23.6s total, 2.36s avg, NO critical slowing")
        print(f"  P3c: {results['total_turns']} turns, {results['total_duration_seconds']:.1f}s total, {results['avg_duration_per_turn']:.2f}s avg")
        print()

        # Hypothesis evaluation
        if critical_slowing:
            print("🎉 HYPOTHESIS SUPPORTED: Bidirectional engagement → Critical slowing")
        elif accumulation_detected:
            print("⚠️  PARTIAL SUPPORT: Accumulation detected but not critical regime yet")
        else:
            print("❌ HYPOTHESIS NOT SUPPORTED: No critical slowing or accumulation")

        self.session_data['analysis'] = results

        return results

    def save_results(self):
        """Save session data and experimental results"""
        # Save session JSON
        session_path = os.path.expanduser(
            f'~/ai-workspace/HRM/sage/raising/sessions/text/session_{self.session_num:03d}.json'
        )
        with open(session_path, 'w') as f:
            json.dump(self.session_data, f, indent=2)

        print(f"\n✅ Session saved: {session_path}")

        # Save experimental report
        report_path = os.path.expanduser(
            f'~/gnosis-research/p3c_results_s{self.session_num:03d}.json'
        )
        with open(report_path, 'w') as f:
            json.dump(self.session_data, f, indent=2)

        print(f"✅ Report saved: {report_path}")

def main():
    """Run P3c experiment"""
    print("="*70)
    print("INITIALIZING P3C EXPERIMENT")
    print("Testing: Bidirectional metacognitive engagement → Critical slowing")
    print("="*70)
    print()

    exp = BidirectionalEngagementExperiment()

    try:
        results = exp.run_experiment(
            max_turns=15,        # Up to 15 turns
            max_duration=600     # Up to 10 minutes
        )

        exp.save_results()

        print(f"\n{'='*70}")
        print("P3C EXPERIMENT COMPLETE")
        print(f"{'='*70}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Experiment interrupted by user")
        exp.save_results()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exp.save_results()

if __name__ == '__main__':
    main()
