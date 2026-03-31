#!/usr/bin/env python3
"""
Thor Session #47: Integration-Flexibility Tradeoff Experiment

Tests hypothesis from Session #46: Beyond C = 0.5, integration increases
while flexibility decreases, creating a tradeoff.

Measures:
- Flexibility: Response diversity, structural variance, semantic novelty
- Integration: State integration measure (SIM), response consistency

Expected: Flexibility peaks at C ≈ 0.5, Integration monotonic increase
"""

import json
import time
import random
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import re

# Try to import optional NLP libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    print("Warning: scikit-learn not available. Using fallback metrics.")
    SKLEARN_AVAILABLE = False


class IntegrationFlexibilityExperiment:
    """Measures integration-flexibility tradeoff across difficulty levels"""

    def __init__(self, output_dir="./"):
        self.output_dir = Path(output_dir)
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Prompt sets for each difficulty level
        self.prompts = self._design_prompts()

    def _design_prompts(self) -> Dict[str, List[str]]:
        """Design 5 similar prompts for each difficulty level"""
        return {
            "level_1_c015": [
                "What is the capital of France?",
                "Name the largest ocean on Earth.",
                "How many days are in a week?",
                "What color is the sky on a clear day?",
                "Who wrote Romeo and Juliet?"
            ],
            "level_2_c035": [
                "Explain what causes rain.",
                "How does a refrigerator keep food cold?",
                "Why do leaves change color in autumn?",
                "What makes a rainbow appear in the sky?",
                "How does a battery store energy?"
            ],
            "level_3_c050": [
                "Explain how photosynthesis works in plants.",
                "Describe the process of cellular respiration in organisms.",
                "How do plants convert sunlight into chemical energy?",
                "Explain how trees produce oxygen through their biological processes.",
                "What is the relationship between chlorophyll, sunlight, and plant growth?"
            ],
            "level_4_c065": [
                "Compare and contrast aerobic and anaerobic respiration, explaining when each occurs.",
                "Analyze the role of ATP in cellular energy transfer and explain its molecular structure.",
                "Evaluate the efficiency of different photosynthetic pathways (C3, C4, CAM).",
                "Synthesize information about the Calvin cycle and light reactions in photosynthesis.",
                "Critique the relationship between mitochondrial function and cellular metabolism."
            ],
            "level_5_c075": [
                "Write a 150-word explanation of climate change that includes causes, effects, and solutions, avoiding the letter 'e' where possible.",
                "Compose a coherent 140-word argument about renewable energy using only words with 2 syllables or fewer.",
                "Create a 160-word essay on ocean acidification that alternates between technical and simple language every sentence.",
                "Develop a 150-word analysis of deforestation incorporating exactly 5 metaphors and 3 statistics.",
                "Construct a 145-word treatise on biodiversity loss that rhymes every other sentence."
            ]
        }

    def _simulate_sage_response(self, prompt: str, difficulty: str, trial: int) -> Dict:
        """
        Simulate SAGE response to prompt.

        In real experiment, this would call actual SAGE API.
        For now, simulate with controlled variability based on difficulty.
        """
        # Extract C value from difficulty label
        c_value = float(difficulty.split('_c')[1]) / 100.0

        # Simulate state variables with realistic patterns from Session #39
        # Wake: inverted-U pattern peaking at C=0.5
        if c_value <= 0.5:
            wake_prob = c_value * 1.2  # Increases to 0.6 at C=0.5
        else:
            wake_prob = 1.2 * 0.5 - (c_value - 0.5) * 0.7  # Decreases after
        wake = random.random() < wake_prob

        # ATP: moderate increase with difficulty
        atp_base = 30 + c_value * 20  # 30 to 50 range
        atp = atp_base + random.gauss(0, 5)

        # Response generation - simulate different patterns by difficulty
        # Low C: Short, variable fragments
        # C~0.5: Moderate length, high creativity
        # High C: Long, constrained, similar across trials

        if c_value < 0.3:
            # Low integration: Short, fragmented
            responses = [
                f"Response to '{prompt[:20]}...' - approach {trial+1}. "
                f"Simple answer: {random.choice(['A', 'B', 'C'])}. "
                f"Additional note: {random.choice(['detail X', 'detail Y', 'detail Z'])}.",

                f"Brief reply: {random.choice(['option 1', 'option 2', 'option 3'])}. "
                f"Context: {random.choice(['factor P', 'factor Q'])}.",

                f"Direct answer for trial {trial}: {random.choice(['Yes', 'No', 'Maybe'])}. "
                f"Reasoning: {random.choice(['because A', 'because B'])}."
            ]
            response_text = random.choice(responses)

        elif c_value < 0.6:
            # Critical: High flexibility, moderate integration
            approaches = [
                f"One way to understand '{prompt[:30]}...' is through {random.choice(['mechanism A', 'process X', 'framework 1'])}. "
                f"This involves {random.choice(['step 1: analyze', 'phase 1: observe', 'stage 1: identify'])} followed by "
                f"{random.choice(['step 2: synthesize', 'phase 2: integrate', 'stage 2: combine'])}. "
                f"The key insight is {random.choice(['pattern alpha', 'structure beta', 'relationship gamma'])}.",

                f"Approaching '{prompt[:30]}...' from {random.choice(['perspective A', 'angle X', 'viewpoint 1'])} reveals "
                f"{random.choice(['dynamic P', 'interaction Q', 'cycle R'])}. "
                f"This {random.choice(['suggests', 'indicates', 'implies'])} that "
                f"{random.choice(['component M', 'element N', 'factor O'])} plays a crucial role.",

                f"Considering '{prompt[:30]}...', we can {random.choice(['analyze', 'examine', 'investigate'])} "
                f"the {random.choice(['underlying', 'fundamental', 'core'])} {random.choice(['mechanism', 'process', 'principle'])}. "
                f"This {random.choice(['demonstrates', 'shows', 'reveals'])} "
                f"{random.choice(['property 1', 'characteristic 2', 'feature 3'])}."
            ]
            response_text = random.choice(approaches)

        else:
            # Supercritical: High integration, low flexibility (rigid)
            # Similar structure across trials, highly constrained
            base_template = (
                f"Analysis of '{prompt[:25]}...': "
                f"First, establish foundational context via systematic decomposition. "
                f"Second, integrate primary components through structured synthesis. "
                f"Third, coordinate secondary elements via hierarchical organization. "
                f"Fourth, consolidate insights through comprehensive evaluation. "
                f"Conclusion: {random.choice(['framework complete', 'analysis concluded', 'synthesis finalized'])}."
            )
            # Very similar across trials (low flexibility)
            response_text = base_template

        # Simulate response time (length-dependent from Session #42)
        chars_per_sec = 30  # Constant from Session #42
        response_time = len(response_text) / chars_per_sec

        return {
            "prompt": prompt,
            "difficulty": difficulty,
            "c_value": c_value,
            "trial": trial,
            "response_text": response_text,
            "response_length": len(response_text),
            "response_time": response_time,
            "wake": wake,
            "atp": atp,
            "mode": random.choice(["EPISTEMIC", "EXECUTE", "OBSERVE"])
        }

    def _compute_response_diversity_score(self, responses: List[str]) -> float:
        """
        Compute Response Diversity Score (RDS).

        Measures semantic distance between responses to same prompt.
        High RDS = flexible (different approaches)
        Low RDS = rigid (same approach repeatedly)
        """
        if len(responses) < 2:
            return 0.0

        if SKLEARN_AVAILABLE:
            # TF-IDF + cosine similarity
            vectorizer = TfidfVectorizer()
            try:
                tfidf = vectorizer.fit_transform(responses)
                similarity_matrix = cosine_similarity(tfidf)

                # Average pairwise distance (1 - similarity)
                n = len(responses)
                total_distance = 0
                count = 0
                for i in range(n):
                    for j in range(i+1, n):
                        total_distance += (1 - similarity_matrix[i, j])
                        count += 1

                return total_distance / count if count > 0 else 0.0
            except:
                # Fallback if TF-IDF fails
                pass

        # Fallback: Simple lexical diversity
        # Measure unique word ratio differences
        diversity_scores = []
        for r in responses:
            words = r.lower().split()
            unique_ratio = len(set(words)) / len(words) if words else 0
            diversity_scores.append(unique_ratio)

        # Variance in diversity (higher = more different approaches)
        return np.std(diversity_scores) if len(diversity_scores) > 1 else 0.0

    def _compute_structural_variance(self, responses: List[Dict]) -> float:
        """
        Compute Structural Variance (SV).

        Variance in response length, complexity.
        Measures exploration of solution space.
        """
        lengths = [r["response_length"] for r in responses]
        if len(lengths) < 2:
            return 0.0

        # Coefficient of variation (normalized variance)
        mean_len = np.mean(lengths)
        std_len = np.std(lengths)

        return std_len / mean_len if mean_len > 0 else 0.0

    def _compute_semantic_novelty(self, responses: List[str]) -> float:
        """
        Compute Semantic Novelty (SN).

        Lexical diversity across responses.
        High SN = creative language use
        Low SN = repetitive language
        """
        all_words = []
        for r in responses:
            words = re.findall(r'\w+', r.lower())
            all_words.extend(words)

        if not all_words:
            return 0.0

        # Type-token ratio
        unique_words = len(set(all_words))
        total_words = len(all_words)

        return unique_words / total_words

    def _compute_state_integration_measure(self, responses: List[Dict]) -> float:
        """
        Compute State Integration Measure (SIM).

        Mutual information between state variables (ATP, wake, mode).
        From Session #46.
        """
        if len(responses) < 2:
            return 0.0

        # Extract state variables
        atp_values = [r["atp"] for r in responses]
        wake_values = [1 if r["wake"] else 0 for r in responses]
        mode_values = [r["mode"] for r in responses]

        # Discretize ATP for MI calculation
        atp_bins = np.digitize(atp_values, bins=[30, 35, 40, 45, 50])

        # Simple mutual information estimate
        # For small N, use correlation-based proxy

        # Convert mode to numeric
        mode_map = {"EPISTEMIC": 0, "EXECUTE": 1, "OBSERVE": 2}
        mode_numeric = [mode_map.get(m, 0) for m in mode_values]

        # Compute correlations (proxy for MI)
        try:
            corr_atp_wake = abs(np.corrcoef(atp_values, wake_values)[0, 1])
            corr_atp_mode = abs(np.corrcoef(atp_values, mode_numeric)[0, 1])
            corr_wake_mode = abs(np.corrcoef(wake_values, mode_numeric)[0, 1])

            # Average correlation as integration proxy
            # Scale to bits (rough approximation)
            avg_corr = (corr_atp_wake + corr_atp_mode + corr_wake_mode) / 3

            # Convert to bits (MI ≈ -log2(1 - r²) for Gaussian)
            if avg_corr < 0.999:
                mi_estimate = -np.log2(1 - avg_corr**2)
            else:
                mi_estimate = 10.0  # Cap at high value

            return mi_estimate
        except:
            return 0.0

    def _compute_response_consistency_index(self, responses: List[Dict]) -> float:
        """
        Compute Response Consistency Index (RCI).

        How predictable is response from pre-turn state?
        High RCI = deterministic (integrated)
        Low RCI = unpredictable (fragmented)
        """
        if len(responses) < 3:
            return 0.0

        # Use ATP as predictor, response_length as target
        atp = np.array([r["atp"] for r in responses])
        length = np.array([r["response_length"] for r in responses])

        # R² = 1 - (SS_res / SS_tot)
        try:
            # Linear regression (simple)
            mean_length = np.mean(length)

            # Slope
            slope = np.cov(atp, length)[0, 1] / np.var(atp)
            intercept = mean_length - slope * np.mean(atp)

            # Predictions
            pred_length = slope * atp + intercept

            # R²
            ss_res = np.sum((length - pred_length)**2)
            ss_tot = np.sum((length - mean_length)**2)

            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

            return max(0.0, r_squared)  # Clamp to [0, 1]
        except:
            return 0.0

    def run_experiment(self, trials_per_prompt: int = 3) -> Dict:
        """Run full experiment across all difficulty levels"""

        print(f"Starting Integration-Flexibility Tradeoff Experiment")
        print(f"Timestamp: {self.timestamp}")
        print(f"Trials per prompt: {trials_per_prompt}")
        print("=" * 60)

        all_results = []
        metrics_by_level = defaultdict(lambda: {
            "rds": [],
            "sv": [],
            "sn": [],
            "sim": [],
            "rci": []
        })

        for difficulty_label, prompts in self.prompts.items():
            print(f"\n{difficulty_label.upper()}")
            print("-" * 60)

            c_value = float(difficulty_label.split('_c')[1]) / 100.0

            for prompt_idx, prompt in enumerate(prompts):
                print(f"  Prompt {prompt_idx+1}/5: '{prompt[:40]}...'")

                # Generate multiple responses to same prompt
                responses = []
                for trial in range(trials_per_prompt):
                    response = self._simulate_sage_response(
                        prompt, difficulty_label, trial
                    )
                    responses.append(response)
                    all_results.append(response)
                    time.sleep(0.01)  # Small delay

                # Compute metrics for this prompt
                response_texts = [r["response_text"] for r in responses]

                rds = self._compute_response_diversity_score(response_texts)
                sv = self._compute_structural_variance(responses)
                sn = self._compute_semantic_novelty(response_texts)
                sim = self._compute_state_integration_measure(responses)
                rci = self._compute_response_consistency_index(responses)

                print(f"    RDS={rds:.3f} SV={sv:.3f} SN={sn:.3f} SIM={sim:.3f} RCI={rci:.3f}")

                # Store metrics
                metrics_by_level[difficulty_label]["rds"].append(rds)
                metrics_by_level[difficulty_label]["sv"].append(sv)
                metrics_by_level[difficulty_label]["sn"].append(sn)
                metrics_by_level[difficulty_label]["sim"].append(sim)
                metrics_by_level[difficulty_label]["rci"].append(rci)

        # Aggregate metrics per level
        print("\n" + "=" * 60)
        print("AGGREGATE METRICS BY DIFFICULTY LEVEL")
        print("=" * 60)

        summary = []
        for difficulty_label in sorted(self.prompts.keys()):
            c_value = float(difficulty_label.split('_c')[1]) / 100.0
            metrics = metrics_by_level[difficulty_label]

            level_summary = {
                "difficulty": difficulty_label,
                "c_value": c_value,
                "rds_mean": np.mean(metrics["rds"]),
                "rds_std": np.std(metrics["rds"]),
                "sv_mean": np.mean(metrics["sv"]),
                "sv_std": np.std(metrics["sv"]),
                "sn_mean": np.mean(metrics["sn"]),
                "sn_std": np.std(metrics["sn"]),
                "sim_mean": np.mean(metrics["sim"]),
                "sim_std": np.std(metrics["sim"]),
                "rci_mean": np.mean(metrics["rci"]),
                "rci_std": np.std(metrics["rci"])
            }
            summary.append(level_summary)

            print(f"\n{difficulty_label} (C={c_value:.2f}):")
            print(f"  Flexibility metrics:")
            print(f"    RDS: {level_summary['rds_mean']:.3f} ± {level_summary['rds_std']:.3f}")
            print(f"    SV:  {level_summary['sv_mean']:.3f} ± {level_summary['sv_std']:.3f}")
            print(f"    SN:  {level_summary['sn_mean']:.3f} ± {level_summary['sn_std']:.3f}")
            print(f"  Integration metrics:")
            print(f"    SIM: {level_summary['sim_mean']:.3f} ± {level_summary['sim_std']:.3f}")
            print(f"    RCI: {level_summary['rci_mean']:.3f} ± {level_summary['rci_std']:.3f}")

        # Test predictions
        print("\n" + "=" * 60)
        print("HYPOTHESIS TESTS")
        print("=" * 60)

        self._test_predictions(summary)

        # Save results
        output = {
            "timestamp": self.timestamp,
            "experiment": "integration_flexibility_tradeoff",
            "trials_per_prompt": trials_per_prompt,
            "raw_responses": all_results,
            "summary": summary
        }

        output_file = self.output_dir / f"tradeoff_results_{self.timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n{'='*60}")
        print(f"Results saved to: {output_file}")

        return output

    def _test_predictions(self, summary: List[Dict]):
        """Test the 5 falsifiable predictions"""

        c_values = [s["c_value"] for s in summary]
        rds_values = [s["rds_mean"] for s in summary]
        sv_values = [s["sv_mean"] for s in summary]
        sn_values = [s["sn_mean"] for s in summary]
        sim_values = [s["sim_mean"] for s in summary]
        rci_values = [s["rci_mean"] for s in summary]

        # Prediction 1: Flexibility Inverted-U
        print("\nPrediction 1: Flexibility peaks at C ≈ 0.5")
        rds_peak_idx = np.argmax(rds_values)
        rds_peak_c = c_values[rds_peak_idx]
        print(f"  RDS peaks at C = {rds_peak_c:.2f}")
        print(f"  Expected: C = 0.50")
        print(f"  Result: {'✓ CONFIRMED' if abs(rds_peak_c - 0.5) < 0.15 else '✗ FALSIFIED'}")

        # Prediction 2: Integration Monotonic
        print("\nPrediction 2: Integration increases monotonically")
        sim_increasing = all(sim_values[i] <= sim_values[i+1]
                            for i in range(len(sim_values)-1))
        print(f"  SIM monotonic increase: {sim_increasing}")
        print(f"  Result: {'✓ CONFIRMED' if sim_increasing else '✗ FALSIFIED'}")

        # Prediction 3: Tradeoff at C > 0.5
        print("\nPrediction 3: Negative correlation SIM-RDS for C > 0.5")
        high_c_indices = [i for i, c in enumerate(c_values) if c > 0.5]
        if len(high_c_indices) >= 2:
            high_c_sim = [sim_values[i] for i in high_c_indices]
            high_c_rds = [rds_values[i] for i in high_c_indices]
            corr = np.corrcoef(high_c_sim, high_c_rds)[0, 1]
            print(f"  Correlation (C > 0.5): r = {corr:.3f}")
            print(f"  Expected: r < 0 (negative)")
            print(f"  Result: {'✓ CONFIRMED' if corr < 0 else '✗ FALSIFIED'}")
        else:
            print(f"  Not enough data points for C > 0.5")

        # Prediction 4: Optimal Balance at C = 0.5
        print("\nPrediction 4: Adaptive capacity maximized at C ≈ 0.5")
        max_sim = max(sim_values) if sim_values else 1.0
        adaptive_capacity = [rds * (sim / max_sim)
                            for rds, sim in zip(rds_values, sim_values)]
        ac_peak_idx = np.argmax(adaptive_capacity)
        ac_peak_c = c_values[ac_peak_idx]
        print(f"  Adaptive capacity peaks at C = {ac_peak_c:.2f}")
        print(f"  Expected: C = 0.50")
        print(f"  Result: {'✓ CONFIRMED' if abs(ac_peak_c - 0.5) < 0.15 else '✗ FALSIFIED'}")

        # Prediction 5: Rigidity Beyond Critical Point
        print("\nPrediction 5: Low diversity at C = 0.75")
        c75_idx = min(range(len(c_values)), key=lambda i: abs(c_values[i] - 0.75))
        c75_rds = rds_values[c75_idx]
        c75_sim = sim_values[c75_idx]
        print(f"  At C = {c_values[c75_idx]:.2f}:")
        print(f"    RDS = {c75_rds:.3f} (expected < 0.3)")
        print(f"    SIM = {c75_sim:.3f} (expected > 1.0)")
        rigid = c75_rds < 0.3 and c75_sim > 1.0
        print(f"  Result: {'✓ CONFIRMED' if rigid else '✗ FALSIFIED'}")


def main():
    """Run the experiment"""

    print("Thor Session #47: Integration-Flexibility Tradeoff")
    print("=" * 60)
    print()

    # Create experiment
    exp = IntegrationFlexibilityExperiment(output_dir="./")

    # Run with 3 trials per prompt (3 repeats × 5 prompts × 5 levels = 75 responses)
    results = exp.run_experiment(trials_per_prompt=3)

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
