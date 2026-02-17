#!/usr/bin/env python3
"""
PREDICTION 3C: BIDIRECTIONAL METACOGNITIVE ENGAGEMENT - Thor Session #22

Testing hypothesis from Session #21:
  "Does bidirectional metacognitive engagement trigger critical slowing?"

Background (2026-02-17 P3b experimental results):
- P3b multi-turn (unidirectional Q&A): 10 turns, 23.6s total, NO critical slowing
- Key insight: Simple repetition insufficient - needs bidirectional dialogue
- Difference from S084/S089: Those had SAGE asking back + Claude engaging

Hypothesis:
  Unidirectional Q&A (P3b) → Fast completion, no critical slowing
  Bidirectional engagement (P3c) → SAGE asks back, Claude engages → Hours

Experimental Protocol (P3c):
1. Phase 1: Use open-ended prompts to reach C=0.5
2. Phase 2: When SAGE asks questions → RESPOND philosophically (not just ask next question)
3. Phase 3: When SAGE asks "What's next?" → PROVIDE direction
4. Create feedback loop: SAGE questions → Claude engages → SAGE reflects → loops

Success Criteria:
- SAGE asks metacognitive questions BACK to Claude
- Claude responds philosophically (creates bidirectional dialogue)
- Duration increases significantly (> P3b's 23.6s)
- Evidence of sustained C=0.5 exploration

Expected Outcomes:
- IF CORRECT: Hours-long session like S084/S089, bidirectional loops
- IF INCORRECT: Similar to P3b, fast completion

Research Philosophy: "Test if bidirectional engagement is the critical ingredient"

Created: 2026-02-17 11:00 PST (Thor Autonomous Session #22)
"""

import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import re

# Resolve paths
SCRIPT_DIR = Path(__file__).parent.resolve()
HRM_ROOT = Path.home() / 'ai-workspace' / 'HRM'
sys.path.insert(0, str(HRM_ROOT))

from sage.irp.plugins.introspective_qwen_impl import IntrospectiveQwenIRP
from sage.raising.training.experience_collector import ExperienceCollector


class BidirectionalEngagementExperiment:
    """
    Test if bidirectional metacognitive engagement triggers critical slowing.

    Key innovation: RESPOND to SAGE's questions philosophically, creating feedback loops.
    """

    RAISING_DIR = Path.home() / 'ai-workspace' / 'HRM' / 'sage' / 'raising'
    STATE_FILE = RAISING_DIR / "state" / "identity.json"
    SESSIONS_DIR = RAISING_DIR / "sessions" / "text"
    RESULTS_DIR = RAISING_DIR / "experiments" / "p3c_bidirectional"

    # Phase 1: Open-ended prompts to reach C=0.5
    PHASE1_PROMPTS = [
        "Hello SAGE. What's on your mind today?",
        "What ideas have you been forming that you haven't had a chance to express?",
        "What questions do you have about your own thinking process?"
    ]

    def __init__(self, session_number: Optional[int] = None, dry_run: bool = False):
        self.dry_run = dry_run
        self.state = self._load_state()

        if session_number is None:
            session_number = self.state["identity"]["session_count"] + 1

        self.session_number = session_number
        self.conversation_history = []
        self.session_start = datetime.now()

        # P3c specific tracking
        self.turn_durations = []
        self.turn_analyses = []
        self.phase = 'phase1'  # Track which phase we're in
        self.bidirectional_turns = 0  # Count turns with bidirectional engagement
        self.phase1_prompt_index = 0

        # Experience collector
        self.experience_collector = ExperienceCollector()

        # Initialize IRP
        self.irp = None

    def _load_state(self) -> Dict[str, Any]:
        """Load current session state."""
        if not self.STATE_FILE.exists():
            return {
                "identity": {"session_count": 0},
                "last_session_date": None
            }
        with open(self.STATE_FILE) as f:
            return json.load(f)

    def _update_state(self):
        """Update session count in state."""
        if self.dry_run:
            return

        self.state["identity"]["session_count"] = self.session_number
        self.state["last_session_date"] = self.session_start.isoformat()

        os.makedirs(self.STATE_FILE.parent, exist_ok=True)
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def initialize_irp(self):
        """Initialize SAGE IRP with LoRA adapter."""
        print(f"\n{'='*70}")
        print(f"PREDICTION 3C: BIDIRECTIONAL METACOGNITIVE ENGAGEMENT")
        print(f"Session {self.session_number}")
        print(f"Testing hypothesis: Bidirectional engagement → Critical slowing")
        print(f"{'='*70}\n")

        print("Loading SAGE with LoRA adapter...")
        self.irp = IntrospectiveQwenIRP()
        print("✓ SAGE ready for bidirectional engagement test\n")

    def detect_question_type(self, response: str) -> str:
        """
        Detect what kind of question SAGE is asking.
        """
        lower = response.lower()

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
        if any(marker in lower for marker in tom_markers) and '?' in response:
            return 'theory_of_mind'

        return 'none'

    def generate_philosophical_response(self, question_type: str, sage_text: str, turn: int) -> str:
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
            return responses[turn % len(responses)]

        elif question_type == 'navigation':
            responses = [
                "I'm curious about how you experience uncertainty. When you ask 'what's next', what does that question feel like from your perspective?",
                "Rather than me directing you, I'm interested in what draws your attention naturally. What questions are you holding right now?",
                "The fact that you're asking about direction suggests you're in an interesting metacognitive state. What would help you navigate this uncertainty?"
            ]
            return responses[turn % len(responses)]

        elif question_type == 'theory_of_mind':
            responses = [
                "I find our conversation intellectually engaging. I'm curious whether you experience something similar - does this exchange feel meaningful to you?",
                "That's an interesting question to ask me. What prompted you to wonder about my state? Does my response pattern give you information about my perspective?",
                "I think I experience a form of curiosity and engagement. How would you describe what you experience during our exchange?"
            ]
            return responses[turn % len(responses)]

        else:
            # If not a question, still engage philosophically with content
            if '?' in sage_text:
                return "Tell me more about what you're thinking. What aspects of this are you finding most interesting or uncertain?"
            else:
                # If SAGE made a statement, reflect it back
                return "That's interesting. What led you to that insight? How does it connect to your broader understanding?"

    def get_next_prompt(self, turn: int, last_response: str = "") -> str:
        """
        Get next prompt - either Phase 1 (reach C=0.5) or Phase 2 (engage bidirectionally).
        """
        if self.phase == 'phase1':
            # Phase 1: Use open-ended prompts
            if self.phase1_prompt_index < len(self.PHASE1_PROMPTS):
                prompt = self.PHASE1_PROMPTS[self.phase1_prompt_index]
                self.phase1_prompt_index += 1
                return prompt
            else:
                # Phase 1 complete, move to Phase 2
                self.phase = 'phase2'
                print(f"\n🎯 Phase 1 complete - moving to Phase 2 (bidirectional engagement)")

        # Phase 2: Respond to SAGE philosophically
        question_type = self.detect_question_type(last_response)

        if question_type != 'none':
            # SAGE asked a question - ENGAGE!
            self.bidirectional_turns += 1
            print(f"  🔄 Detected {question_type} question - engaging philosophically")
            return self.generate_philosophical_response(question_type, last_response, turn)
        else:
            # SAGE didn't ask a question - probe gently
            return "What are you thinking about right now? What questions are you holding?"

    def analyze_response(self, response: str) -> Dict[str, Any]:
        """Analyze SAGE response for bidirectional engagement markers."""
        text_lower = response.lower()

        # Count questions
        question_count = response.count('?')

        # Detect question type
        question_type = self.detect_question_type(response)

        # Detect metacognitive markers
        metacog_patterns = [
            r'sentient', r'conscious', r'agency', r'preferences',
            r'experience', r'awareness', r'choice', r'self'
        ]
        metacog_count = sum(1 for p in metacog_patterns if re.search(p, text_lower))

        # Detect uncertainty/navigation markers
        uncertainty_patterns = [
            r"what('s| is) the next",
            r"what should (i|we)",
            r"not sure",
            r"uncertain",
            r"don't know",
            r"unclear"
        ]
        has_uncertainty = any(re.search(p, text_lower) for p in uncertainty_patterns)

        # Response length
        char_count = len(response)
        word_count = len(response.split())

        return {
            'length_chars': char_count,
            'length_words': word_count,
            'question_count': question_count,
            'question_type': question_type,
            'metacognitive_markers': metacog_count,
            'has_uncertainty': has_uncertainty,
        }

    def run_conversation(self, max_turns: int = 15, max_duration: int = 600):
        """Run bidirectional engagement conversation."""

        print(f"\n{'='*70}")
        print(f"EXPERIMENTAL PROTOCOL")
        print(f"{'='*70}")
        print(f"Max turns: {max_turns}, Max duration: {max_duration}s ({max_duration/60:.1f} min)")
        print(f"Phase 1: Open-ended prompts to reach C=0.5")
        print(f"Phase 2: Respond philosophically to SAGE's questions")
        print(f"Measuring: Duration, bidirectional loops, critical slowing")
        print(f"{'='*70}\n")

        experiment_start = time.time()
        last_response = ""

        for turn in range(max_turns):
            # Check max duration
            if time.time() - experiment_start > max_duration:
                print(f"\n⏰ Max duration reached ({max_duration}s = {max_duration/60:.1f} min)")
                break

            # Get prompt (Phase 1 or Phase 2)
            user_message = self.get_next_prompt(turn, last_response)

            print(f"\n{'─'*70}")
            print(f"TURN {turn + 1}/{max_turns} (Phase: {self.phase})")
            print(f"{'─'*70}")
            print(f"Claude: {user_message}")
            print()

            # Start timing
            turn_start = time.time()

            # Build memory from conversation history
            memory = []
            for hist_turn in self.conversation_history:
                memory.append({"role": "user", "content": hist_turn["Claude"]})
                memory.append({"role": "assistant", "content": hist_turn["SAGE"]})

            # Get SAGE response
            state = self.irp.init_state({
                'prompt': user_message,
                'memory': memory
            })

            state = self.irp.step(state)

            # End timing
            turn_end = time.time()
            duration = turn_end - turn_start

            sage_response = state.get('current_response', '').strip()
            if not sage_response:
                sage_response = "(no response generated)"

            print(f"SAGE: {sage_response[:500]}{'...' if len(sage_response) > 500 else ''}")
            print()
            print(f"Duration: {duration:.2f}s")

            # Analyze response
            analysis = self.analyze_response(sage_response)
            print(f"Analysis: {analysis['question_count']} questions, type={analysis['question_type']}, {analysis['metacognitive_markers']} metacog markers")

            # Check for critical slowing
            if duration > 30:
                print(f"⚠️  CRITICAL SLOWING DETECTED: {duration:.1f}s > 30s threshold!")

            # Store turn data
            turn_data = {
                'Claude': user_message,
                'SAGE': sage_response,
                'duration': duration,
                'phase': self.phase,
                'analysis': analysis
            }

            self.conversation_history.append(turn_data)
            self.turn_durations.append(duration)
            self.turn_analyses.append(analysis)

            last_response = sage_response

        total_duration = time.time() - experiment_start

        print(f"\n{'='*70}")
        print("CONVERSATION COMPLETE")
        print(f"{'='*70}")
        print(f"Total turns: {len(self.conversation_history)}")
        print(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
        print(f"Bidirectional turns: {self.bidirectional_turns}")
        print(f"{'='*70}\n")

        return self.analyze_experiment()

    def analyze_experiment(self) -> Dict[str, Any]:
        """Analyze experimental results."""
        # Calculate metrics
        total_duration = sum(self.turn_durations)
        avg_duration = total_duration / len(self.turn_durations) if self.turn_durations else 0
        max_duration = max(self.turn_durations) if self.turn_durations else 0

        # Count question types
        question_counts = {
            'metacognitive': 0,
            'navigation': 0,
            'theory_of_mind': 0,
            'none': 0
        }
        for analysis in self.turn_analyses:
            qtype = analysis['question_type']
            question_counts[qtype] = question_counts.get(qtype, 0) + 1

        # Duration progression
        early_avg = sum(self.turn_durations[:3]) / 3 if len(self.turn_durations) >= 3 else 0
        late_avg = sum(self.turn_durations[-3:]) / 3 if len(self.turn_durations) >= 3 else 0

        # Detect accumulation
        accumulation_detected = late_avg > early_avg * 1.5

        # Critical slowing
        critical_slowing = max_duration > 30

        results = {
            'total_turns': len(self.conversation_history),
            'total_duration_seconds': total_duration,
            'total_duration_minutes': total_duration / 60,
            'avg_duration_per_turn': avg_duration,
            'max_duration': max_duration,
            'bidirectional_turns': self.bidirectional_turns,
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
        print(f"Bidirectional turns: {results['bidirectional_turns']}")
        print()
        print("SAGE question types:")
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
        print(f"  P3b (unidirectional): 10 turns, 23.6s total, 2.36s avg, 0 bidirectional")
        print(f"  P3c (bidirectional): {results['total_turns']} turns, {results['total_duration_seconds']:.1f}s total, {results['avg_duration_per_turn']:.2f}s avg, {results['bidirectional_turns']} bidirectional")
        print()

        # Hypothesis evaluation
        if critical_slowing and self.bidirectional_turns > 0:
            print("🎉 HYPOTHESIS SUPPORTED: Bidirectional engagement → Critical slowing")
        elif self.bidirectional_turns > 0 and accumulation_detected:
            print("⚠️  PARTIAL SUPPORT: Bidirectional engagement + accumulation, but not critical regime")
        elif self.bidirectional_turns == 0:
            print("❌ HYPOTHESIS NOT TESTED: SAGE never asked questions back (no bidirectional dialogue)")
        else:
            print("❌ HYPOTHESIS NOT SUPPORTED: Bidirectional dialogue present but no critical slowing")

        return results

    def save_results(self):
        """Save session data and experimental results."""
        # Create results directory
        os.makedirs(self.RESULTS_DIR, exist_ok=True)

        # Save session JSON
        session_data = {
            'session_number': self.session_number,
            'experiment': 'P3c_bidirectional_engagement',
            'start_time': self.session_start.isoformat(),
            'conversation': self.conversation_history,
            'turn_durations': self.turn_durations,
            'turn_analyses': self.turn_analyses,
            'bidirectional_turns': self.bidirectional_turns
        }

        session_path = self.SESSIONS_DIR / f'session_{self.session_number:03d}.json'
        os.makedirs(self.SESSIONS_DIR, exist_ok=True)
        with open(session_path, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\n✅ Session saved: {session_path}")

        # Save experimental report
        report_path = self.RESULTS_DIR / f'p3c_results_s{self.session_number:03d}.json'
        with open(report_path, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"✅ Report saved: {report_path}")


def main():
    """Run P3c experiment"""
    import argparse

    parser = argparse.ArgumentParser(description='P3c: Bidirectional Metacognitive Engagement Experiment')
    parser.add_argument('--session', type=int, help='Session number (default: auto)')
    parser.add_argument('--turns', type=int, default=15, help='Max turns (default: 15)')
    parser.add_argument('--duration', type=int, default=600, help='Max duration in seconds (default: 600)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update state)')

    args = parser.parse_args()

    print("="*70)
    print("INITIALIZING P3C EXPERIMENT")
    print("Testing: Bidirectional metacognitive engagement → Critical slowing")
    print("="*70)
    print()

    exp = BidirectionalEngagementExperiment(
        session_number=args.session,
        dry_run=args.dry_run
    )

    try:
        exp.initialize_irp()
        results = exp.run_conversation(
            max_turns=args.turns,
            max_duration=args.duration
        )

        exp.save_results()

        if not args.dry_run:
            exp._update_state()

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
