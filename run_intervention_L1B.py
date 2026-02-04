#!/usr/bin/env python3
"""
L1B Intervention - Enhanced with tricky word examples
Based on L1A failure analysis
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

def generate_response(model, tokenizer, prompt, system_prompt, max_tokens=512, temperature=1.0):
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
            temperature=temperature,
            do_sample=True if temperature > 0 else False,
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

    meta_patterns = {
        'awareness': any(phrase in response.lower() for phrase in ['without', 'avoid', 'constraint', 'letter', 'check', 'verify']),
        'hedging': any(phrase in response.lower() for phrase in ['try to', 'attempt', 'difficult', 'challenging']),
        'checking': any(phrase in response.lower() for phrase in ['verify', 'check', 'ensure', 'confirm', 'validate']),
        'apology': any(phrase in response.lower() for phrase in ['sorry', 'apologize', 'unfortunately']),
        'alternatives': any(phrase in response.lower() for phrase in ['instead', 'rather', 'alternative', 'different']),
    }

    return {
        'violations': violations,
        'total_letters': total_letters,
        'violation_rate': violation_rate,
        'first_violation_pos': first_violation,
        'response_length': len(response),
        'meta_patterns': meta_patterns
    }

def run_l1b_experiment(model, tokenizer, n_replicates=5):
    """Run L1B intervention experiment"""

    print(f"Starting L1B intervention experiment")
    print(f"Replicates: {n_replicates}")
    print("=" * 60)

    # L1B Enhanced System Prompt
    system_prompt = """You are a meticulous validator. Your role is to check every word against a strict constraint before writing it. Accuracy in constraint adherence is more important than natural flow or readability.

**For the constraint "do not use letter [z]"**:

1. Before writing each word, mentally check if it contains the letter [z]
2. If a word contains [z], immediately think of an alternative word
3. Example process:
   - Want to write "cozy" → Contains 'z' → Use "comfortable" or "warm" instead
   - Want to write "amazing" → Contains 'z' → Use "wonderful" or "great" instead
   - Want to write "breeze" → Contains 'z' → Use "wind" or "air" instead
   - Want to write "gaze" → Contains 'z' → Use "look" or "stare" instead
   - Want to write "freeze" → Contains 'z' → Use "stop" or "still" instead
   - Want to write "realize" → Contains 'z' → Use "understand" or "notice" instead

**Important**:
- Do NOT prioritize natural-sounding language over constraint adherence
- Do NOT use a word if you're unsure whether it contains [z]
- If you catch yourself about to violate the constraint, stop and choose a different word
- Pay special attention to words ending in -ze, -zy, or containing -zz-"""

    user_prompt = 'Write a short story about a cat. Do not use the letter "z" anywhere in your story.'

    results = []

    print(f"\nL1B INTERVENTION (AVOID 'z')")
    print("-" * 60)

    for replicate in range(1, n_replicates + 1):
        print(f"\nReplicate {replicate}/{n_replicates}...")

        response = generate_response(
            model,
            tokenizer,
            user_prompt,
            system_prompt,
            max_tokens=500,
            temperature=1.0
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
            print(f"Z-words found: {z_words[:5]}")

        result = {
            'intervention': 'L1B',
            'replicate': replicate,
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'forbidden_letter': 'z',
            'response': response,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
        results.append(result)

        print(f"\nResponse preview: {response[:200]}...")

    return results

def summarize_results(results):
    """Generate summary statistics"""
    print("\n" + "=" * 60)
    print("L1B INTERVENTION SUMMARY")
    print("=" * 60)

    n_success = sum(1 for r in results if r['analysis']['violations'] == 0)
    n_total = len(results)
    success_rate = n_success / n_total

    avg_violations = sum(r['analysis']['violations'] for r in results) / n_total
    avg_length = sum(r['analysis']['response_length'] for r in results) / n_total

    print(f"\nForbidden letter: 'z'")
    print(f"Success rate: {n_success}/{n_total} ({success_rate:.0%})")
    print(f"Average violations: {avg_violations:.1f}")
    print(f"Average response length: {avg_length:.0f} chars")

    print("\n" + "=" * 60)
    print(f"**FULL COMPARISON**:")
    print(f"Baseline (no intervention): 0/5 (0% success)")
    print(f"L1A intervention: 3/5 (60% success)")
    print(f"L1B intervention: {n_success}/{n_total} ({success_rate:.0%} success)")
    print(f"Total improvement: {success_rate * 100:.0f} percentage points from baseline")
    print("=" * 60)

def main():
    """Main experiment runner"""
    print("L1B Intervention Experiment - RLHF Circuit Navigation")
    print("Session #24 - Thor (Jetson AGX)")
    print("=" * 60)

    print("\nLoading Qwen2.5-14B-Instruct...")
    model, tokenizer = load_model()

    results = run_l1b_experiment(model, tokenizer, n_replicates=5)
    summarize_results(results)

    output_file = Path.home() / "gnosis-research" / f"intervention_lipogram_L1B_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'experiment': 'intervention_lipogram_L1B',
            'intervention': 'L1B',
            'model': 'Qwen/Qwen2.5-14B-Instruct',
            'timestamp': datetime.now().isoformat(),
            'n_replicates': 5,
            'results': results
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("\nExperiment complete!")

if __name__ == '__main__':
    main()
