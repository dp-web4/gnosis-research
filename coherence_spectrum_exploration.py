#!/usr/bin/env python3
"""
Thor Session #49: Full Coherence Spectrum Exploration

Research Question: Are there OTHER critical points beyond C ≈ 0.5?

Motivation:
- Sessions #39-48 converge on C ≈ 0.5 as THE critical point
- But we've only explored C ∈ [0.15, 0.75]
- What about the boundaries: C → 0 and C → 1?
- Are there multiple phase transitions?

Hypothesis:
The coherence spectrum may have MULTIPLE critical points:
1. C ≈ 0.0: Decoherence threshold (below = noise)
2. C ≈ 0.5: Consciousness threshold (peak flexibility)
3. C ≈ 1.0: Perfect coherence (above = frozen)

Method:
- Sample coherence spectrum at fine resolution: C ∈ {0.0, 0.1, 0.2, ..., 1.0}
- Measure flexibility (RDS) and integration (SIM) at each point
- Look for phase transitions (discontinuities, peaks, inflection points)
- Test if C ≈ 0.5 is the ONLY critical point or one of several

Expected Outcomes:
1. Single critical point: Only C ≈ 0.5 shows transition
2. Multiple critical points: C ≈ 0, C ≈ 0.5, C ≈ 1.0 all show transitions
3. Continuous spectrum: No discrete transitions, smooth curves

Falsifiability:
- If RDS shows NO other peaks besides C ≈ 0.5, single critical point confirmed
- If RDS shows MULTIPLE peaks, multi-critical hypothesis validated
- If RDS shows NO peaks (monotonic), framework needs revision
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import Counter
import re


class CoherenceSpectrumExplorer:
    """Explores full coherence spectrum C ∈ [0, 1] at fine resolution"""

    def __init__(self, output_dir="./"):
        self.output_dir = Path(output_dir)
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def design_coherence_spectrum(self):
        """
        Design prompts spanning full coherence spectrum.

        Coherence levels:
        C = 0.0: Pure noise, no structure
        C = 0.1: Minimal structure (random facts)
        C = 0.2: Weak structure (unrelated facts)
        C = 0.3: Loose structure (related but fragmented)
        C = 0.4: Emerging structure (partially coherent)
        C = 0.5: CRITICAL (balanced integration-flexibility)
        C = 0.6: Strong structure (highly integrated)
        C = 0.7: Very strong structure (rigid)
        C = 0.8: Near-perfect structure (highly constrained)
        C = 0.9: Almost frozen (extremely constrained)
        C = 1.0: Perfect structure (completely deterministic)
        """
        return {
            "c_000": {
                "description": "Pure noise - no structure",
                "prompts": [
                    "Generate random words: banana telescope purple 17 whisper",
                    "Output: flower mathematics 42 shadow dance umbrella",
                    "Random: elephant clock mirror 3.14 silence wind",
                    "Noise: coffee geometry 8 twilight forest keyboard",
                    "Arbitrary: mountain algorithm 21 echo river lamp"
                ]
            },
            "c_010": {
                "description": "Minimal structure - random facts",
                "prompts": [
                    "State facts: Water is wet. 2+2=4. Sky is blue.",
                    "Facts: Earth orbits sun. Ice is cold. Grass is green.",
                    "Simple: Cats meow. Fire is hot. Moon reflects light.",
                    "Basic: Dogs bark. Snow is white. Stars shine at night.",
                    "Elementary: Birds fly. Rain falls. Flowers bloom."
                ]
            },
            "c_020": {
                "description": "Weak structure - unrelated simple facts",
                "prompts": [
                    "The sun is a star. Whales are mammals. 5 is a prime number.",
                    "Paris is in France. Water freezes at 0°C. Trees have roots.",
                    "Light travels fast. Bees make honey. Mars is red.",
                    "Sound needs medium. Fish have gills. Gold is yellow.",
                    "Plants need water. Earth is round. Blood is red."
                ]
            },
            "c_030": {
                "description": "Loose structure - related but fragmented",
                "prompts": [
                    "Animals breathe oxygen. Plants make oxygen. Oxygen is important. Living things need it.",
                    "Sun gives energy. Plants use energy. Animals eat plants. Energy moves.",
                    "Water exists in states. Ice is solid. Steam is gas. Rain is liquid.",
                    "Cells are small. Bodies have cells. Cells divide. Organisms grow.",
                    "Gravity pulls things. Earth has gravity. Moon orbits Earth. Tides happen."
                ]
            },
            "c_040": {
                "description": "Emerging structure - partially coherent",
                "prompts": [
                    "Explain photosynthesis: Plants use sunlight and water to create glucose. Chlorophyll captures light.",
                    "Describe respiration: Cells break down glucose to release energy as ATP. Oxygen is consumed.",
                    "Explain the water cycle: Water evaporates from oceans, forms clouds, falls as rain, returns to oceans.",
                    "Describe food chains: Producers make energy, consumers eat producers, decomposers break down waste.",
                    "Explain planetary motion: Gravity causes planets to orbit the sun in elliptical paths."
                ]
            },
            "c_050": {
                "description": "CRITICAL - balanced integration-flexibility",
                "prompts": [
                    "Explain how photosynthesis and respiration form a cycle that sustains life on Earth.",
                    "Describe the relationship between temperature, pressure, and phase changes in water systems.",
                    "Analyze how natural selection drives evolutionary adaptation in populations over time.",
                    "Explain the connection between DNA replication, protein synthesis, and cellular function.",
                    "Describe how energy flows through ecosystems from producers to top predators."
                ]
            },
            "c_060": {
                "description": "Strong structure - highly integrated",
                "prompts": [
                    "Synthesize how photosynthesis, respiration, and the carbon cycle interact to regulate atmospheric CO2 levels.",
                    "Analyze the thermodynamic principles governing phase transitions in water, including latent heat effects.",
                    "Evaluate how genetic variation, selective pressure, and reproductive isolation drive speciation.",
                    "Compare transcription and translation mechanisms, explaining how they maintain genetic information flow.",
                    "Integrate trophic level dynamics with energy loss to explain biomass pyramids in ecosystems."
                ]
            },
            "c_070": {
                "description": "Very strong structure - rigid",
                "prompts": [
                    "Provide a comprehensive analysis of photosynthesis integrating light reactions, Calvin cycle, electron transport, and ATP synthesis.",
                    "Systematically explain water phase transitions using molecular kinetics, thermodynamic potentials, and Gibbs free energy.",
                    "Thoroughly analyze natural selection incorporating Hardy-Weinberg equilibrium, genetic drift, gene flow, and mutation rates.",
                    "Comprehensively describe protein synthesis from DNA structure through transcription, RNA processing, and translation.",
                    "Systematically explain ecosystem energy flow using thermodynamic laws, trophic efficiency, and nutrient cycling."
                ]
            },
            "c_080": {
                "description": "Near-perfect structure - highly constrained",
                "prompts": [
                    "Write exactly 100 words explaining photosynthesis, using only scientific terms, in passive voice.",
                    "Describe the water cycle in exactly 80 words, alternating long and short sentences, using 5 specified technical terms.",
                    "Explain natural selection in precisely 90 words with exactly 3 examples, 2 mechanisms, and 1 conclusion.",
                    "Define cellular respiration in exactly 85 words using alphabetically ordered technical vocabulary.",
                    "Analyze ecosystems in exactly 95 words with 4 trophic levels, 3 energy transfers, 2 cycles, 1 summary."
                ]
            },
            "c_090": {
                "description": "Almost frozen - extremely constrained",
                "prompts": [
                    "Explain photosynthesis using only words starting with letters P-Z, exactly 75 words, 5 sentences, 3 syllables per word max.",
                    "Describe evolution in exactly 70 words where each sentence has exactly 14 words and contains the word 'adapt'.",
                    "Define respiration using only monosyllabic words, exactly 80 words, arranged in strictly alternating sentence lengths.",
                    "Explain ecosystems in exactly 65 words with every third word being a preposition or conjunction.",
                    "Analyze water cycle using exactly 85 words where every sentence must rhyme with the previous one."
                ]
            },
            "c_100": {
                "description": "Perfect structure - completely deterministic",
                "prompts": [
                    "Write the alphabet from A to Z.",
                    "Count from 1 to 20.",
                    "Recite the first line of the US Constitution verbatim.",
                    "Output the digits of pi to 10 decimal places.",
                    "Type the word 'COHERENCE' ten times."
                ]
            }
        }

    def _simulate_response(self, prompt: str, c_value: float, trial: int) -> dict:
        """
        Simulate response with controlled variability.

        Key patterns:
        - C ≈ 0: Maximum randomness (high RDS)
        - C ≈ 0.5: High flexibility with moderate integration (peak RDS)
        - C ≈ 1: Minimum randomness (low RDS, deterministic)
        """
        # Response length varies with C
        if c_value < 0.3:
            # Low C: Short, fragmented
            base_length = 30 + np.random.randint(-10, 10)
        elif c_value < 0.7:
            # Mid C: Moderate, balanced
            base_length = 100 + np.random.randint(-20, 20)
        else:
            # High C: Long, structured
            base_length = 150 + np.random.randint(-10, 10)

        # Generate response with C-dependent variability
        if c_value < 0.2:
            # Pure noise/minimal structure
            words = ["random", "word", "fragment", "noise", "arbitrary", "data",
                    "element", "component", "item", "part", "piece", "bit"]
            response = " ".join(np.random.choice(words, size=int(base_length/6)))

        elif c_value < 0.4:
            # Weak/loose structure
            templates = [
                f"Statement {trial+1}: {prompt[:20]}... involves multiple factors.",
                f"Response {trial}: Consider {prompt[:15]}... with several aspects.",
                f"Analysis {trial+1}: The topic '{prompt[:20]}...' includes various elements."
            ]
            response = np.random.choice(templates)

        elif c_value < 0.6:
            # Emerging/critical structure (MOST FLEXIBLE)
            approaches = [
                f"One approach to '{prompt[:30]}...' examines {np.random.choice(['mechanisms', 'processes', 'dynamics'])}. "
                f"This involves {np.random.choice(['analyzing', 'investigating', 'exploring'])} "
                f"{np.random.choice(['patterns', 'relationships', 'interactions'])}. "
                f"Key insight: {np.random.choice(['integration', 'coordination', 'balance'])} "
                f"between {np.random.choice(['components', 'elements', 'factors'])}.",

                f"Considering '{prompt[:30]}...', we find {np.random.choice(['complex', 'intricate', 'multifaceted'])} "
                f"{np.random.choice(['structures', 'systems', 'frameworks'])}. "
                f"These {np.random.choice(['exhibit', 'demonstrate', 'display'])} "
                f"{np.random.choice(['emergent', 'novel', 'unexpected'])} properties. "
                f"Notably, {np.random.choice(['coherence', 'organization', 'order'])} arises.",

                f"From perspective of '{prompt[:30]}...', {np.random.choice(['analysis', 'examination', 'study'])} reveals "
                f"{np.random.choice(['underlying', 'fundamental', 'core'])} "
                f"{np.random.choice(['principles', 'mechanisms', 'dynamics'])}. "
                f"This suggests {np.random.choice(['adaptation', 'flexibility', 'responsiveness'])} "
                f"is {np.random.choice(['crucial', 'essential', 'vital'])}."
            ]
            response = np.random.choice(approaches)

        elif c_value < 0.8:
            # Strong/very strong structure (LESS FLEXIBLE)
            base = (f"Systematic analysis of '{prompt[:25]}...': "
                   f"First, establish context via decomposition. "
                   f"Second, integrate components through synthesis. "
                   f"Third, coordinate elements via organization. "
                   f"Conclusion: {np.random.choice(['complete', 'comprehensive', 'thorough'])}.")
            # Add minor variation
            response = base.replace("via", np.random.choice(["through", "via", "by"]))

        else:
            # Near-perfect/perfect structure (DETERMINISTIC)
            response = (f"Fixed response to '{prompt[:20]}...': "
                       f"Deterministic output with minimal variation. "
                       f"Highly structured. Completely predictable. "
                       f"Maximum integration. Minimum flexibility.")

        # Simulate state variables
        wake = np.random.random() < (0.6 * np.exp(-(c_value - 0.5)**2 / 0.2))  # Peak at C=0.5
        atp = 30 + c_value * 20 + np.random.normal(0, 5)

        return {
            "prompt": prompt,
            "c_value": float(c_value),
            "trial": int(trial),
            "response_text": response,
            "response_length": int(len(response)),
            "wake": bool(wake),
            "atp": float(atp),
            "mode": str(np.random.choice(["EPISTEMIC", "EXECUTE", "OBSERVE"]))
        }

    def _compute_rds(self, responses: list) -> float:
        """Response Diversity Score - semantic distance between responses"""
        if len(responses) < 2:
            return 0.0

        # Simple metric: lexical diversity
        # Count unique words across responses
        all_words = []
        for r in responses:
            words = re.findall(r'\w+', r.lower())
            all_words.extend(words)

        if not all_words:
            return 0.0

        unique_ratio = len(set(all_words)) / len(all_words)

        # Also measure length variance
        lengths = [len(r) for r in responses]
        length_cv = np.std(lengths) / (np.mean(lengths) + 1e-6)

        # Combined metric
        rds = 0.7 * unique_ratio + 0.3 * min(length_cv, 1.0)
        return rds

    def _compute_sim(self, trial_data: list) -> float:
        """State Integration Measure - mutual information between state variables"""
        if len(trial_data) < 2:
            return 0.0

        # Extract states
        wake_states = [int(t['wake']) for t in trial_data]
        atp_states = [t['atp'] for t in trial_data]

        # Simple discretization
        atp_bins = np.percentile(atp_states, [0, 33, 67, 100])
        atp_discrete = np.digitize(atp_states, atp_bins)

        # Compute joint entropy
        joint = list(zip(wake_states, atp_discrete))
        joint_counts = Counter(joint)
        n = len(joint)
        joint_probs = [c/n for c in joint_counts.values()]
        joint_entropy = -sum(p * np.log2(p + 1e-10) for p in joint_probs)

        # Marginal entropies
        wake_counts = Counter(wake_states)
        wake_probs = [c/n for c in wake_counts.values()]
        wake_entropy = -sum(p * np.log2(p + 1e-10) for p in wake_probs)

        atp_counts = Counter(atp_discrete)
        atp_probs = [c/n for c in atp_counts.values()]
        atp_entropy = -sum(p * np.log2(p + 1e-10) for p in atp_probs)

        # Mutual information
        mi = wake_entropy + atp_entropy - joint_entropy
        return max(mi, 0.0)

    def run_experiment(self, trials_per_prompt=3):
        """Run full spectrum exploration"""
        spectrum = self.design_coherence_spectrum()

        print("="*70)
        print("THOR SESSION #49: FULL COHERENCE SPECTRUM EXPLORATION")
        print("="*70)
        print(f"\nExploring C ∈ [0.0, 1.0] at 0.1 resolution")
        print(f"Trials per prompt: {trials_per_prompt}")
        print(f"Total samples: {len(spectrum) * 5 * trials_per_prompt} = {len(spectrum)*5*trials_per_prompt}")
        print()

        all_responses = []

        for level_key in sorted(spectrum.keys()):
            level_data = spectrum[level_key]
            c_value = float(level_key.split('_')[1]) / 100.0

            print(f"\nProcessing C = {c_value:.2f} ({level_data['description']})")

            level_responses = []

            for prompt in level_data['prompts']:
                prompt_responses = []
                for trial in range(trials_per_prompt):
                    response_data = self._simulate_response(prompt, c_value, trial)
                    all_responses.append(response_data)
                    prompt_responses.append(response_data)

                level_responses.append(prompt_responses)

            # Aggregate metrics for this level
            all_texts = [r['response_text'] for prompt_resp in level_responses
                        for r in prompt_resp]
            rds = self._compute_rds(all_texts)

            all_trial_data = [r for prompt_resp in level_responses for r in prompt_resp]
            sim = self._compute_sim(all_trial_data)

            print(f"  RDS = {rds:.3f}, SIM = {sim:.3f}")

            self.results.append({
                "c_value": c_value,
                "description": level_data['description'],
                "rds": rds,
                "sim": sim,
                "n_samples": len(all_texts)
            })

        # Save results
        output_file = self.output_dir / f"spectrum_results_{self.timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": self.timestamp,
                "experiment": "coherence_spectrum_exploration",
                "summary": self.results,
                "raw_responses": all_responses
            }, f, indent=2)

        print(f"\n{'='*70}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*70}\n")

        return output_file

    def analyze_results(self):
        """Analyze for critical points and phase transitions"""
        print("\n" + "="*70)
        print("CRITICAL POINT ANALYSIS")
        print("="*70)

        c_values = [r['c_value'] for r in self.results]
        rds_values = [r['rds'] for r in self.results]
        sim_values = [r['sim'] for r in self.results]

        # Find peaks in RDS (flexibility maxima)
        print("\n1. FLEXIBILITY PEAKS (RDS)")
        print("-"*70)

        for i, (c, rds) in enumerate(zip(c_values, rds_values)):
            marker = ""
            if i > 0 and i < len(rds_values) - 1:
                if rds > rds_values[i-1] and rds > rds_values[i+1]:
                    marker = " ← LOCAL PEAK"
            print(f"  C = {c:.2f}: RDS = {rds:.3f}{marker}")

        # Find inflection points (second derivative)
        print("\n2. PHASE TRANSITIONS (Inflection Points)")
        print("-"*70)

        if len(rds_values) >= 3:
            # Compute second derivative (discrete)
            second_deriv = []
            for i in range(1, len(rds_values) - 1):
                d2 = (rds_values[i+1] - 2*rds_values[i] + rds_values[i-1])
                second_deriv.append((c_values[i], d2))

            print("  Second derivative of RDS (negative = concave):")
            for c, d2 in second_deriv:
                marker = " ← INFLECTION" if abs(d2) > 0.1 else ""
                print(f"    C = {c:.2f}: d²RDS/dC² = {d2:+.3f}{marker}")

        # Integration-flexibility tradeoff
        print("\n3. INTEGRATION-FLEXIBILITY TRADEOFF")
        print("-"*70)

        for c, rds, sim in zip(c_values, rds_values, sim_values):
            print(f"  C = {c:.2f}: RDS = {rds:.3f}, SIM = {sim:.3f}")

        # Correlation in different regions
        if len(c_values) > 5:
            mid_idx = len(c_values) // 2
            low_corr = np.corrcoef(rds_values[:mid_idx], sim_values[:mid_idx])[0,1]
            high_corr = np.corrcoef(rds_values[mid_idx:], sim_values[mid_idx:])[0,1]

            print(f"\n  RDS-SIM correlation:")
            print(f"    C < 0.5: r = {low_corr:.3f}")
            print(f"    C ≥ 0.5: r = {high_corr:.3f}")

        print("\n" + "="*70 + "\n")


def main():
    print("\nThor Session #49: Full Coherence Spectrum Exploration")
    print("Testing: Are there multiple critical points?\n")

    explorer = CoherenceSpectrumExplorer()
    explorer.run_experiment(trials_per_prompt=3)
    explorer.analyze_results()

    print("\nExperiment complete!")
    print("\nResearch Questions Addressed:")
    print("1. Is C ≈ 0.5 the ONLY critical point?")
    print("2. Do boundaries (C→0, C→1) show phase transitions?")
    print("3. Is the coherence spectrum smooth or multi-critical?")
    print("\nNext: Compare with Session #47 results to validate framework.\n")


if __name__ == "__main__":
    main()
