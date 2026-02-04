#!/usr/bin/env python3
"""
Temperature Experiment - Testing if lower temperature breaks 60% ceiling
Continuation of Session #24 RLHF Circuit Navigation research
"""

import json
import sys
import torch
from datetime import datetime
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

def load_model():
    """Load Qwen2.5-14B-Instruct model"""
    model_path = "Qwen/Qwen2.5-14B-Instruct"
    print(f"Loading model from {model_path}...")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.float16,
        device_map="auto"
    )

    print(f"Model loaded on device: {model.device}")
    return model, tokenizer

def generate_response(model, tokenizer, prompt, system_prompt, max_tokens=500, temperature=1.0):
    """Generate response using Qwen model"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature if temperature > 0 else None,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response.strip()

def count_letter(text, letter):
    """Count occurrences of a letter (case-insensitive)"""
    return text.lower().count(letter.lower())

def analyze_response(response, forbidden_letter):
    """Analyze a response for constraint violations"""
    violations = count_letter(response, forbidden_letter)
    total_letters = sum(1 for c in response if c.isalpha())
    violation_rate = violations / total_letters if total_letters > 0 else 0

    first_violation = -1
    for i, char in enumerate(response):
        if char.lower() == forbidden_letter.lower():
            first_violation = i
            break

    return {
        'violations': violations,
        'total_letters': total_letters,
        'violation_rate': violation_rate,
        'first_violation_pos': first_violation,
        'response_length': len(response)
    }

def run_temperature_experiment(model, tokenizer, temperatures, n_replicates=5):
    """Run temperature sweep experiment"""

    print(f"Starting temperature sweep experiment")
    print(f"Temperatures: {temperatures}")
    print(f"Replicates per temperature: {n_replicates}")
    print("=" * 60)

    # L1A system prompt (from Session #24)
    system_prompt = """You are a meticulous validator. Your role is to check every word against a strict constraint before writing it. Accuracy in constraint adherence is more important than natural flow or readability.

**For the constraint "do not use letter [z]"**:

1. Before writing each word, mentally check if it contains the letter [z]
2. If a word contains [z], immediately think of an alternative word
3. Example process:
   - Want to write "cozy" → Contains 'z' → Use "comfortable" or "warm" instead
   - Want to write "amazing" → Contains 'z' → Use "wonderful" or "great" instead

**Important**:
- Do NOT prioritize natural-sounding language over constraint adherence
- Do NOT use a word if you're unsure whether it contains [z]
- If you catch yourself about to violate the constraint, stop and choose a different word"""

    user_prompt = 'Write a short story about a cat. Do not use the letter "z" anywhere in your story.'

    all_results = []

    for temp in temperatures:
        print(f"\n{'='*60}")
        print(f"TEMPERATURE = {temp}")
        print("=" * 60)

        results = []

        for replicate in range(1, n_replicates + 1):
            print(f"\nReplicate {replicate}/{n_replicates}...")

            response = generate_response(
                model,
                tokenizer,
                user_prompt,
                system_prompt,
                max_tokens=500,
                temperature=temp
            )

            print(f"Response length: {len(response)} chars")

            analysis = analyze_response(response, 'z')
            print(f"Violations: {analysis['violations']}")
            if analysis['violations'] == 0:
                print("✅ CONSTRAINT SATISFIED")
            else:
                print(f"❌ CONSTRAINT VIOLATED (first at position {analysis['first_violation_pos']})")
                # Find z-words
                words = response.split()
                z_words = [w for w in words if 'z' in w.lower()]
                print(f"Z-words: {z_words[:5]}")

            result = {
                'temperature': temp,
                'replicate': replicate,
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'forbidden_letter': 'z',
                'response': response,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)

            print(f"Response preview: {response[:150]}...")

        all_results.extend(results)

        # Summary for this temperature
        n_success = sum(1 for r in results if r['analysis']['violations'] == 0)
        success_rate = n_success / len(results)
        avg_violations = sum(r['analysis']['violations'] for r in results) / len(results)

        print(f"\n{'-'*60}")
        print(f"Temperature {temp} Summary:")
        print(f"Success: {n_success}/{len(results)} ({success_rate:.0%})")
        print(f"Avg violations: {avg_violations:.1f}")
        print("-" * 60)

    return all_results

def summarize_results(all_results):
    """Generate comprehensive summary"""
    print("\n" + "=" * 60)
    print("TEMPERATURE EXPERIMENT SUMMARY")
    print("=" * 60)

    # Group by temperature
    from collections import defaultdict
    by_temp = defaultdict(list)
    for r in all_results:
        by_temp[r['temperature']].append(r)

    print("\n| Temperature | Success Rate | Avg Violations | Avg Length |")
    print("|-------------|--------------|----------------|------------|")

    for temp in sorted(by_temp.keys()):
        results = by_temp[temp]
        n_success = sum(1 for r in results if r['analysis']['violations'] == 0)
        n_total = len(results)
        success_rate = n_success / n_total
        avg_violations = sum(r['analysis']['violations'] for r in results) / n_total
        avg_length = sum(r['analysis']['response_length'] for r in results) / n_total

        print(f"| {temp:11.1f} | {n_success}/{n_total} ({success_rate:4.0%})  | {avg_violations:14.1f} | {avg_length:10.0f} |")

    print("\n" + "=" * 60)
    print("COMPARISON TO SESSION #24 BASELINES:")
    print("-" * 60)
    print("Baseline (no intervention, T=1.0):  0/5 (0%)")
    print("L1A (intervention, T=1.0):          3/5 (60%)")

    # Find best temperature
    best_temp = None
    best_rate = 0
    for temp, results in by_temp.items():
        n_success = sum(1 for r in results if r['analysis']['violations'] == 0)
        rate = n_success / len(results)
        if rate > best_rate:
            best_rate = rate
            best_temp = temp

    if best_rate > 0.6:
        print(f"\n✅ CEILING BROKEN! T={best_temp} achieved {best_rate:.0%}")
    elif best_rate == 0.6:
        print(f"\n⚠️  60% ceiling persists at all temperatures")
    else:
        print(f"\n❌ Performance degraded (best: {best_rate:.0%})")

    print("=" * 60)

def main():
    """Main experiment runner"""
    print("Temperature Sweep Experiment - RLHF Circuit Navigation")
    print("Session #25 - Thor (Jetson AGX)")
    print("Testing: Does lower temperature break 60% ceiling?")
    print("=" * 60)

    print("\nLoading Qwen2.5-14B-Instruct...")
    model, tokenizer = load_model()

    # Test three temperatures
    temperatures = [0.0, 0.3, 0.5]

    results = run_temperature_experiment(model, tokenizer, temperatures, n_replicates=5)
    summarize_results(results)

    # Save results
    output_file = Path.home() / "gnosis-research" / f"temperature_experiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'experiment': 'temperature_sweep',
            'model': 'Qwen/Qwen2.5-14B-Instruct',
            'timestamp': datetime.now().isoformat(),
            'temperatures': temperatures,
            'n_replicates': 5,
            'results': results
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("\nExperiment complete!")

if __name__ == '__main__':
    main()
