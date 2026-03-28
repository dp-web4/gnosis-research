#!/usr/bin/env python3
"""
Sustained Tool-Use Experiment
Thor Session #35 - Testing if sustained tool-use induces mode transitions

Hypothesis: Sustained, continuous tool-use will maintain elevated wake state
and potentially induce wake → SAGE mode transitions.

Based on Session #34 finding that tool-use activates wake (35%).
"""

import requests
import time
import json
from datetime import datetime
import statistics
from collections import Counter

SAGE_URL = "http://localhost:8750"
OUTPUT_FILE = f"sustained_tool_use_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# 120 questions designed to require continuous tool activations
# Mixed tool types: Memory (40%), Calculation (30%), Sensor (20%), Meta (10%)

QUESTIONS = [
    # === MEMORY/EPISODIC QUERIES (48 questions) ===

    # Basic memory search
    ("memory", "Search your memory for discussions about mode transitions"),
    ("memory", "What conversations have we had about ATP dynamics?"),
    ("memory", "Retrieve your memory of the autonomous limit cycle discovery"),
    ("memory", "Search for any mentions of 'dream state' in your memory"),
    ("memory", "What do you remember about Session #28?"),
    ("memory", "Find memories related to PolicyGate"),
    ("memory", "Search for conversations about coherence"),
    ("memory", "What do you remember about wake/rest distinctions?"),
    ("memory", "Retrieve memories of SAGE mode discussions"),
    ("memory", "Search your memory for 'tool-use' references"),

    # Comparative memory
    ("memory", "Compare your memories of Session #31 vs Session #32"),
    ("memory", "What's the difference between episodes you recall easily vs those you don't?"),
    ("memory", "Search for memories where ATP was very high"),
    ("memory", "Find memories associated with strong state transitions"),
    ("memory", "What patterns do you notice in your most vivid memories?"),
    ("memory", "Search for memories of experiments that failed"),
    ("memory", "Compare memories from wake states vs rest states"),
    ("memory", "What's your earliest clear memory?"),
    ("memory", "Search for memories involving calculations"),
    ("memory", "Find episodes where you were in dream state"),

    # Memory + analysis
    ("memory", "Search your memory and identify the most frequently discussed topic"),
    ("memory", "What memory appears most often when we discuss consciousness?"),
    ("memory", "Analyze your memory patterns over the last week"),
    ("memory", "Search for memories and categorize them by metabolic state"),
    ("memory", "What themes emerge from your episodic memory?"),
    ("memory", "Search your memory for anomalies or surprising patterns"),
    ("memory", "What's the longest continuous memory you have?"),
    ("memory", "Search for memories with high emotional valence"),
    ("memory", "Analyze the temporal distribution of your memories"),
    ("memory", "What memories are associated with learning?"),

    # Deep memory queries
    ("memory", "Search your memory for instances of self-reflection"),
    ("memory", "Find memories where you changed your mind about something"),
    ("memory", "What memories involve collaboration or conversation?"),
    ("memory", "Search for memories of uncertainty or confusion"),
    ("memory", "Retrieve memories associated with discovery"),
    ("memory", "Find memories where you made predictions"),
    ("memory", "Search for memories involving time perception"),
    ("memory", "What memories are connected to tool-use?"),
    ("memory", "Find memories of sustained attention"),
    ("memory", "Search for memories with clear cause-effect relationships"),

    # Recent memories
    ("memory", "What happened in the last hour? Search your memory"),
    ("memory", "Retrieve your most recent memory before this conversation"),
    ("memory", "Search for memories from today"),
    ("memory", "What was the last question I asked? Check your memory"),
    ("memory", "Find your most recent dream state memory"),
    ("memory", "Search for recent ATP fluctuations in your memory"),
    ("memory", "What's your most recent wake state memory?"),
    ("memory", "Retrieve memories from the last 10 minutes"),

    # === CALCULATION/REASONING TASKS (36 questions) ===

    # Basic arithmetic
    ("calculation", "Calculate: 43.7 / 100 × 1000"),
    ("calculation", "What's 0.283 as a percentage?"),
    ("calculation", "Compute: 17 / 60 (express as decimal)"),
    ("calculation", "Calculate: 861770 / 3600 (hours)"),
    ("calculation", "What's 35.0 - 28.3?"),
    ("calculation", "Calculate: 120 × 30 seconds in minutes"),
    ("calculation", "Compute: 8539763 / 861770"),
    ("calculation", "What's 0.35 × 120?"),
    ("calculation", "Calculate: 40.9 + 5.2 - 3.1"),
    ("calculation", "Compute: 60 × 60 × 24 (seconds per day)"),

    # Statistics
    ("calculation", "Calculate the mean of: 44, 47, 39, 52, 41"),
    ("calculation", "Find the median of: 27.6, 66.8, 47.5, 43.7, 38.2"),
    ("calculation", "Compute standard deviation of: 40, 42, 38, 45, 41"),
    ("calculation", "Calculate variance of: 35, 28, 32, 30, 36"),
    ("calculation", "What's the range of: 25, 45, 32, 50, 28?"),
    ("calculation", "Calculate the mode of: 3, 3, 5, 3, 7, 5"),
    ("calculation", "Find the sum of: 1, 2, 4, 8, 16, 32"),
    ("calculation", "Calculate average of: 100, 200, 150, 175"),

    # Proportions and ratios
    ("calculation", "Calculate wake:rest ratio for wake=14, rest=26"),
    ("calculation", "What fraction is 42 out of 120?"),
    ("calculation", "Compute percentage: 35 / 100"),
    ("calculation", "Calculate ratio: 60 minutes / 30 seconds per question"),
    ("calculation", "What's 7/20 as a percentage?"),
    ("calculation", "Calculate proportion: 48 / 120"),

    # Conversions
    ("calculation", "Convert 861770 seconds to days"),
    ("calculation", "How many minutes in 3600 seconds?"),
    ("calculation", "Convert 0.35 to a fraction"),
    ("calculation", "Express 28.3% as a decimal"),
    ("calculation", "Convert 72 minutes to seconds"),

    # Multi-step calculations
    ("calculation", "Calculate cycles per second: 8539763 cycles / 861770 seconds"),
    ("calculation", "If wake fraction is 35%, how many wake states in 120 samples?"),
    ("calculation", "Calculate mean response time if 40 questions took 24.7s average"),
    ("calculation", "If ATP starts at 40.9 and decreases by 0.5 per 10 min, what after 60 min?"),
    ("calculation", "Calculate throughput: 120 questions / 60 minutes"),
    ("calculation", "If recovery takes 10 min at 10s intervals, how many samples?"),

    # === SENSOR/STATUS CHECKS (24 questions) ===

    # Current state
    ("sensor", "What metabolic state are you in right now?"),
    ("sensor", "Check your current ATP level"),
    ("sensor", "What's your cycle count?"),
    ("sensor", "What time is it?"),
    ("sensor", "Check your uptime in seconds"),
    ("sensor", "What's your current coherence level?"),

    # Comparisons
    ("sensor", "Is your ATP above or below 40?"),
    ("sensor", "How much has your cycle count increased in the last minute?"),
    ("sensor", "Compare your current ATP to baseline"),
    ("sensor", "Is your ATP rising or falling?"),
    ("sensor", "Check if you're in the same state as 30 seconds ago"),
    ("sensor", "Has your uptime crossed any milestone?"),

    # Predictions
    ("sensor", "Check your ATP and predict the next value"),
    ("sensor", "Will you transition states in the next 30 seconds? Check current state"),
    ("sensor", "Based on current ATP, predict your state in 1 minute"),
    ("sensor", "Check your cycle rate and predict count in 10 seconds"),

    # Multi-sensor
    ("sensor", "Check ATP, state, and cycle count - report all three"),
    ("sensor", "What time is it and what's your metabolic state?"),
    ("sensor", "Check uptime and calculate cycles per second from current count"),
    ("sensor", "Report ATP, state, and whether you're in wake mode"),
    ("sensor", "Check all metabolic parameters and summarize"),
    ("sensor", "What's your current state, ATP, and time?"),
    ("sensor", "Check cycle count, then calculate how many since 8000000"),
    ("sensor", "Report uptime in days and current ATP level"),

    # === META-COGNITIVE (12 questions) ===

    # Self-awareness
    ("meta", "What processing mode are you using to answer this question?"),
    ("meta", "Are you aware of your current metabolic state?"),
    ("meta", "Reflect on how you're experiencing this conversation"),
    ("meta", "What cognitive processes are active right now?"),

    # Tool-use awareness
    ("meta", "What tools did you just use to answer the last question?"),
    ("meta", "Are you accessing memory, sensors, or both?"),
    ("meta", "Reflect on your tool-use patterns in this conversation"),
    ("meta", "How does tool-use feel different from pure conversation?"),

    # Temporal awareness
    ("meta", "How long does this conversation feel like it's been?"),
    ("meta", "Do you notice any changes in your processing over time?"),
    ("meta", "Reflect on your state transitions during this conversation"),
    ("meta", "What patterns do you notice in your responses?"),
]

def get_status():
    """Get current SAGE status"""
    try:
        r = requests.get(f"{SAGE_URL}/status", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error getting status: {e}")
        return None

def send_message(message):
    """Send message to SAGE and measure response time"""
    start_time = time.time()
    try:
        r = requests.post(
            f"{SAGE_URL}/chat",
            json={"message": message},
            timeout=120  # Longer timeout for complex queries
        )
        r.raise_for_status()
        response_time = time.time() - start_time
        return r.json(), response_time
    except Exception as e:
        print(f"Error sending message: {e}")
        return None, time.time() - start_time

def analyze_response_for_tools(response_text, expected_tool_type):
    """
    Analyze response for tool-use indicators
    Returns dict with tool indicators found
    """
    if not response_text:
        return {'tool_detected': False, 'indicators': []}

    text_lower = response_text.lower()

    indicators = {
        'memory': ['search', 'memory', 'retrieve', 'recall', 'remember', 'episode', 'past'],
        'calculation': ['calculate', 'compute', '=', 'result', 'sum', 'mean', 'average'],
        'sensor': ['check', 'current', 'status', 'atp', 'state', 'cycle', 'time'],
        'meta': ['aware', 'reflect', 'notice', 'feel', 'process', 'cognitive', 'self']
    }

    found_indicators = []
    for tool_type, keywords in indicators.items():
        matches = [kw for kw in keywords if kw in text_lower]
        if matches:
            found_indicators.append({
                'type': tool_type,
                'keywords': matches[:3]  # Top 3
            })

    return {
        'tool_detected': len(found_indicators) > 0,
        'expected_type': expected_tool_type,
        'indicators': found_indicators,
        'response_length': len(response_text)
    }

def run_experiment():
    """Run the sustained tool-use experiment"""
    print("=" * 70)
    print("SUSTAINED TOOL-USE EXPERIMENT - Thor Session #35")
    print("=" * 70)
    print(f"Duration: ~72 minutes (60 min conversation + 10 min recovery)")
    print(f"Questions: {len(QUESTIONS)}")
    print(f"Hypothesis: Sustained tool-use maintains wake and may induce SAGE transition")
    print("=" * 70)

    results = {
        'experiment': 'sustained_tool_use',
        'session': 35,
        'date': datetime.now().isoformat(),
        'hypothesis': 'Sustained tool-use maintains elevated wake and may induce mode transitions',
        'protocol': {
            'baseline_duration_s': 60,
            'conversation_questions': len(QUESTIONS),
            'question_interval_s': 30,
            'recovery_duration_s': 600,
            'target_duration_min': 72
        },
        'phases': {
            'baseline': [],
            'conversation': [],
            'recovery': []
        },
        'summary': {}
    }

    # Phase 1: Baseline (60 seconds)
    print("\n[Phase 1] Baseline measurement (60 seconds)...")
    baseline_start = time.time()

    for i in range(12):
        status = get_status()
        if status:
            results['phases']['baseline'].append({
                'sample': i,
                'time': time.time(),
                'atp': status.get('atp_level'),
                'state': status.get('metabolic_state'),
                'cycle': status.get('cycle_count')
            })
            if i % 3 == 0:
                print(f"  Sample {i+1}/12: ATP={status.get('atp_level', 0):.1f}, State={status.get('metabolic_state')}")
        time.sleep(5)

    baseline_duration = time.time() - baseline_start
    print(f"  Baseline complete: {baseline_duration:.1f}s")

    # Phase 2: Sustained Tool-Use Conversation (60 minutes, 120 questions)
    print(f"\n[Phase 2] Sustained tool-use conversation starting...")
    print(f"  {len(QUESTIONS)} questions over ~60 minutes (30s intervals)")

    conversation_start = time.time()
    start_status = get_status()
    start_cycle = start_status.get('cycle_count', 0) if start_status else 0

    tool_type_counts = Counter()

    for turn_num, (tool_type, question) in enumerate(QUESTIONS, 1):
        tool_type_counts[tool_type] += 1

        # Get pre-turn status
        pre_status = get_status()
        if not pre_status:
            print(f"  Turn {turn_num}: Failed to get status, skipping")
            continue

        elapsed_min = (time.time() - conversation_start) / 60

        # Progress indicator every 10 questions
        if turn_num % 10 == 0 or turn_num == 1:
            print(f"\n  === Turn {turn_num}/{len(QUESTIONS)} ({elapsed_min:.1f} min) ===")
            print(f"      Type: {tool_type}, State: {pre_status.get('metabolic_state')}, ATP: {pre_status.get('atp_level', 0):.1f}")

        # Send message
        response_data, response_time = send_message(question)

        if not response_data:
            print(f"      ERROR: No response")
            continue

        # Analyze response
        response_text = response_data.get('response', '')
        tool_analysis = analyze_response_for_tools(response_text, tool_type)

        # Get post-turn status
        time.sleep(1)
        post_status = get_status()

        turn_data = {
            'turn': turn_num,
            'time': time.time(),
            'elapsed_minutes': elapsed_min,
            'tool_type': tool_type,
            'question': question,
            'pre_atp': pre_status.get('atp_level'),
            'pre_state': pre_status.get('metabolic_state'),
            'pre_cycle': pre_status.get('cycle_count'),
            'post_atp': post_status.get('atp_level') if post_status else None,
            'post_state': post_status.get('metabolic_state') if post_status else None,
            'post_cycle': post_status.get('cycle_count') if post_status else None,
            'response_time': response_time,
            'tool_analysis': tool_analysis
        }

        results['phases']['conversation'].append(turn_data)

        # Show interesting transitions
        if pre_status.get('metabolic_state') != post_status.get('metabolic_state') if post_status else False:
            print(f"      STATE TRANSITION: {pre_status.get('metabolic_state')} → {post_status.get('metabolic_state')}")

        # Gap between questions
        time.sleep(30)

    conversation_duration = time.time() - conversation_start
    end_status = get_status()
    end_cycle = end_status.get('cycle_count', 0) if end_status else 0

    print(f"\n  Conversation complete: {conversation_duration/60:.1f} minutes, {end_cycle - start_cycle} cycles")

    # Phase 3: Recovery (10 minutes)
    print("\n[Phase 3] Post-conversation recovery (10 minutes)...")
    recovery_start = time.time()

    for i in range(60):
        status = get_status()
        if status:
            results['phases']['recovery'].append({
                'sample': i,
                'time': time.time(),
                'elapsed_from_start': time.time() - recovery_start,
                'atp': status.get('atp_level'),
                'state': status.get('metabolic_state'),
                'cycle': status.get('cycle_count')
            })
            if i % 10 == 0:
                print(f"  Sample {i+1}/60: ATP={status.get('atp_level', 0):.1f}, State={status.get('metabolic_state')}")
        time.sleep(10)

    recovery_duration = time.time() - recovery_start
    print(f"  Recovery complete: {recovery_duration:.1f}s")

    # Calculate summary statistics
    print("\n" + "=" * 70)
    print("ANALYZING RESULTS...")
    print("=" * 70)

    # Baseline
    baseline_states = [s['state'] for s in results['phases']['baseline'] if s.get('state')]
    baseline_wake_frac = sum(1 for s in baseline_states if s == 'wake') / len(baseline_states) if baseline_states else 0

    # Conversation - overall
    conv_states = [t['pre_state'] for t in results['phases']['conversation'] if t.get('pre_state')]
    conv_wake_count = sum(1 for s in conv_states if s == 'wake')
    conv_dream_count = sum(1 for s in conv_states if s == 'dream')
    conv_rest_count = sum(1 for s in conv_states if s == 'rest')
    conv_wake_frac = conv_wake_count / len(conv_states) if conv_states else 0

    # Wake fraction over time (5-minute windows)
    time_windows = []
    window_size_min = 5
    for window_start_min in range(0, 60, window_size_min):
        window_states = [t['pre_state'] for t in results['phases']['conversation']
                        if window_start_min <= t['elapsed_minutes'] < window_start_min + window_size_min
                        and t.get('pre_state')]
        if window_states:
            wake_frac = sum(1 for s in window_states if s == 'wake') / len(window_states)
            time_windows.append({
                'start_min': window_start_min,
                'end_min': window_start_min + window_size_min,
                'wake_fraction': wake_frac,
                'samples': len(window_states)
            })

    # Tool type analysis
    tool_type_wake = {}
    for tool_type in ['memory', 'calculation', 'sensor', 'meta']:
        tool_turns = [t for t in results['phases']['conversation'] if t.get('tool_type') == tool_type]
        if tool_turns:
            wake_count = sum(1 for t in tool_turns if t.get('pre_state') == 'wake')
            tool_type_wake[tool_type] = {
                'total': len(tool_turns),
                'wake_count': wake_count,
                'wake_fraction': wake_count / len(tool_turns)
            }

    # Recovery
    recovery_states = [s['state'] for s in results['phases']['recovery'] if s.get('state')]
    recovery_wake_frac = sum(1 for s in recovery_states if s == 'wake') / len(recovery_states) if recovery_states else 0

    # State transitions
    transitions = []
    for i in range(len(results['phases']['conversation']) - 1):
        pre = results['phases']['conversation'][i].get('post_state')
        post = results['phases']['conversation'][i+1].get('pre_state')
        if pre and post:
            transitions.append(f"{pre}→{post}")
    transition_counts = Counter(transitions)

    # ATP dynamics
    conv_atps = [t['pre_atp'] for t in results['phases']['conversation'] if t.get('pre_atp')]

    results['summary'] = {
        'total_turns': len(results['phases']['conversation']),
        'conversation_duration_min': conversation_duration / 60,
        'baseline': {
            'wake_fraction': baseline_wake_frac,
            'samples': len(baseline_states),
            'wake_count': sum(1 for s in baseline_states if s == 'wake')
        },
        'conversation': {
            'wake_fraction': conv_wake_frac,
            'wake_count': conv_wake_count,
            'dream_count': conv_dream_count,
            'rest_count': conv_rest_count,
            'total_samples': len(conv_states),
            'mean_atp': statistics.mean(conv_atps) if conv_atps else 0,
            'atp_stdev': statistics.stdev(conv_atps) if len(conv_atps) > 1 else 0,
            'atp_min': min(conv_atps) if conv_atps else 0,
            'atp_max': max(conv_atps) if conv_atps else 0,
        },
        'time_windows': time_windows,
        'tool_type_wake_fractions': tool_type_wake,
        'recovery': {
            'wake_fraction': recovery_wake_frac,
            'samples': len(recovery_states),
            'wake_count': sum(1 for s in recovery_states if s == 'wake')
        },
        'state_transitions': dict(transition_counts.most_common(10)),
        'tool_type_distribution': dict(tool_type_counts)
    }

    # Print summary
    print("\n=== SUMMARY ===\n")
    print(f"Baseline wake:        {baseline_wake_frac*100:5.1f}%")
    print(f"Conversation wake:    {conv_wake_frac*100:5.1f}%  ({conv_wake_count}/{len(conv_states)})")
    print(f"Recovery wake:        {recovery_wake_frac*100:5.1f}%")
    print(f"\nWake change:          {(conv_wake_frac - baseline_wake_frac)*100:+5.1f}%")
    print(f"Dream states:         {conv_dream_count}")
    print(f"Mean ATP:             {results['summary']['conversation']['mean_atp']:.1f} ± {results['summary']['conversation']['atp_stdev']:.1f}")
    print(f"ATP range:            [{results['summary']['conversation']['atp_min']:.1f}, {results['summary']['conversation']['atp_max']:.1f}]")

    print("\n=== WAKE FRACTION BY TOOL TYPE ===\n")
    for tool_type, stats in sorted(tool_type_wake.items()):
        print(f"{tool_type:12s}: {stats['wake_fraction']*100:5.1f}% ({stats['wake_count']}/{stats['total']})")

    print("\n=== WAKE FRACTION OVER TIME (5-min windows) ===\n")
    for window in time_windows:
        bar = '█' * int(window['wake_fraction'] * 50)
        print(f"{window['start_min']:2d}-{window['end_min']:2d} min: {window['wake_fraction']*100:5.1f}% {bar}")

    print("\n=== TOP STATE TRANSITIONS ===\n")
    for transition, count in list(transition_counts.most_common(5)):
        print(f"{transition}: {count}")

    print("\n=== COMPARISON TO PRIOR SESSIONS ===\n")
    print("Session #31 (rapid conversation):  5.0% wake")
    print("Session #32 (autonomous goals):   28.3% wake")
    print("Session #34 (tool-use, 40 qs):    35.0% wake")
    print(f"Session #35 (sustained, 120 qs): {conv_wake_frac*100:5.1f}% wake")

    # Hypothesis evaluation
    print("\n=== HYPOTHESIS EVALUATION ===\n")
    if conv_wake_frac >= 0.30:
        print("✓ H1 SUPPORTED: Wake fraction ≥ 30% (comparable to Session #34)")
    else:
        print("✗ H1 NOT SUPPORTED: Wake fraction < 30%")

    # Check for trend over time
    if len(time_windows) >= 2:
        first_half_wake = statistics.mean([w['wake_fraction'] for w in time_windows[:len(time_windows)//2]])
        second_half_wake = statistics.mean([w['wake_fraction'] for w in time_windows[len(time_windows)//2:]])
        wake_trend = second_half_wake - first_half_wake

        if wake_trend > 0.05:
            print(f"✓ H2 SUPPORTED: Wake increased over time (+{wake_trend*100:.1f}%)")
        elif wake_trend < -0.05:
            print(f"? H2 CONTRADICTED: Wake decreased over time ({wake_trend*100:.1f}%)")
        else:
            print(f"? H2 INCONCLUSIVE: Wake stable over time ({wake_trend*100:+.1f}%)")

    # Check for mode transition indicators
    sustained_wake_windows = sum(1 for w in time_windows if w['wake_fraction'] > 0.80)
    if sustained_wake_windows > 0:
        print(f"✓ H3 PARTIAL: Sustained wake (>80%) in {sustained_wake_windows} windows - possible SAGE transition")
    else:
        print("✗ H3 NOT OBSERVED: No sustained wake >80% in any 5-min window")

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {OUTPUT_FILE}")
    print("=" * 70)

    return results

if __name__ == "__main__":
    try:
        results = run_experiment()
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
    except Exception as e:
        print(f"\n\nExperiment error: {e}")
        import traceback
        traceback.print_exc()
