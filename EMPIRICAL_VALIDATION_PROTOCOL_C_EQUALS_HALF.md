# Empirical Validation Protocol: C ≈ 0.5 in SAGE

**Companion to Thor Session #51**
**Date**: 2026-04-03
**Purpose**: Concrete experiments to validate C ≈ 0.5 predictions in running SAGE instances

---

## Overview

Session #51 identified 8 subsystems where C ≈ 0.5 patterns manifest. This document provides specific measurement protocols to validate these predictions empirically.

**Goal**: Measure actual C values in running SAGE instances and confirm they cluster around 0.5.

---

## Experiment 1: Trust Weight Distribution

### Hypothesis
After PolicyGate learning, plugin trust weights should center around 0.5-0.7 with standard deviation ~0.2.

### Measurement Protocol

**Duration**: 1000 consciousness cycles (~1-2 hours at 1 Hz cycle rate)

**Data Collection**:
```python
# Add to sage_consciousness.py
def log_trust_distribution(self, cycle_num):
    weights = list(self.plugin_trust_weights.values())
    stats = {
        'cycle': cycle_num,
        'mean': np.mean(weights),
        'std': np.std(weights),
        'min': np.min(weights),
        'max': np.max(weights),
        'weights': dict(self.plugin_trust_weights)
    }
    with open('trust_distribution_log.jsonl', 'a') as f:
        f.write(json.dumps(stats) + '\n')
```

**Call every 100 cycles** in consciousness loop.

**Analysis**:
```python
import json
import numpy as np
import matplotlib.pyplot as plt

# Load data
data = [json.loads(line) for line in open('trust_distribution_log.jsonl')]

# Extract means over time
means = [d['mean'] for d in data]
stds = [d['std'] for d in data]

# Plot evolution
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(means, label='Mean trust')
plt.axhline(0.5, color='r', linestyle='--', label='C = 0.5')
plt.axhline(0.65, color='g', linestyle='--', label='Expected ~0.65')
plt.xlabel('Measurement (every 100 cycles)')
plt.ylabel('Mean Trust Weight')
plt.legend()
plt.title('Trust Weight Evolution')

plt.subplot(1, 2, 2)
plt.plot(stds, label='Std dev')
plt.axhline(0.2, color='r', linestyle='--', label='Expected ~0.2')
plt.xlabel('Measurement')
plt.ylabel('Standard Deviation')
plt.legend()
plt.title('Trust Weight Diversity')
plt.tight_layout()
plt.savefig('trust_distribution_validation.png')
```

**Success Criteria**:
- ✅ Mean converges to 0.5-0.7 range
- ✅ Std stabilizes around 0.15-0.25
- ✅ No collapse to extremes (all weights → 0.3 or all → 1.0)

**Failure Criteria**:
- ❌ Mean < 0.4 or > 0.8 (wrong operating regime)
- ❌ Std < 0.05 (too uniform, no diversity)
- ❌ Std > 0.3 (too variable, no stability)

---

## Experiment 2: Metabolic State Distribution

### Hypothesis
System should spend ~60-70% of time in WAKE state, with deviations for REST/DREAM/CRISIS averaging to C_system ≈ 0.5.

### Measurement Protocol

**Duration**: 2000 consciousness cycles (~2-3 hours)

**Data Collection**:
```python
# Add to sage_consciousness.py
def log_metabolic_state(self, cycle_num):
    state_log = {
        'cycle': cycle_num,
        'state': self.metabolic_controller.current_state.name,
        'atp': self.metabolic_controller.current_atp,
        'salience': getattr(self, 'last_salience_avg', 0.0)
    }
    with open('metabolic_state_log.jsonl', 'a') as f:
        f.write(json.dumps(state_log) + '\n')
```

**Call every cycle** in consciousness loop.

**Analysis**:
```python
import json
from collections import Counter
import matplotlib.pyplot as plt

# Load data
data = [json.loads(line) for line in open('metabolic_state_log.jsonl')]

# Count state occurrences
states = [d['state'] for d in data]
state_counts = Counter(states)
total = len(states)

# Compute percentages
state_pcts = {s: count/total for s, count in state_counts.items()}

# Map states to coherence values (from Session #51)
state_coherence = {
    'WAKE': 0.5,
    'REST': 0.3,
    'DREAM': 0.7,
    'CRISIS': 0.9
}

# Compute average system coherence
avg_coherence = sum(state_pcts.get(s, 0) * c for s, c in state_coherence.items())

print(f"State distribution: {state_pcts}")
print(f"Average system coherence: {avg_coherence:.3f}")
print(f"Expected: ~0.5")

# Visualize
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.bar(state_pcts.keys(), state_pcts.values())
plt.ylabel('Fraction of Time')
plt.title('Metabolic State Distribution')
plt.axhline(0.65, color='r', linestyle='--', alpha=0.5, label='Expected WAKE ~65%')
plt.legend()

plt.subplot(1, 2, 2)
plt.bar(['Measured', 'Expected'], [avg_coherence, 0.5])
plt.ylabel('System Coherence')
plt.ylim(0, 1)
plt.title('Average System Coherence')
plt.tight_layout()
plt.savefig('metabolic_state_validation.png')
```

**Success Criteria**:
- ✅ WAKE: 60-70%
- ✅ REST: 15-25%
- ✅ DREAM: 10-20%
- ✅ CRISIS: <5%
- ✅ Average C: 0.45-0.55

**Failure Criteria**:
- ❌ WAKE < 50% (too much time in non-optimal states)
- ❌ CRISIS > 10% (system unstable)
- ❌ Average C < 0.4 or > 0.6 (wrong operating point)

---

## Experiment 3: SNARC Salience Distribution

### Hypothesis
Salience scores should peak around 0.4-0.6 (moderate salience), not at extremes (0.0 or 1.0).

### Measurement Protocol

**Duration**: 1000 cycles with varied input stimuli

**Data Collection**:
```python
# Add to sage_consciousness.py
def log_salience_scores(self, cycle_num, salience_scores):
    log_entry = {
        'cycle': cycle_num,
        'salience_total': [s.total for s in salience_scores],
        'salience_components': [
            {
                'surprise': s.surprise,
                'novelty': s.novelty,
                'arousal': s.arousal,
                'reward': s.reward,
                'conflict': s.conflict
            } for s in salience_scores
        ]
    }
    with open('salience_log.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
```

**Analysis**:
```python
import json
import numpy as np
import matplotlib.pyplot as plt

# Load data
data = [json.loads(line) for line in open('salience_log.jsonl')]

# Flatten all salience values
all_salience = []
for entry in data:
    all_salience.extend(entry['salience_total'])

# Compute statistics
mean_sal = np.mean(all_salience)
std_sal = np.std(all_salience)

print(f"Mean salience: {mean_sal:.3f} (expected: ~0.5)")
print(f"Std salience: {std_sal:.3f}")

# Histogram
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.hist(all_salience, bins=50, density=True, alpha=0.7)
plt.axvline(mean_sal, color='r', linestyle='--', label=f'Mean: {mean_sal:.2f}')
plt.axvline(0.5, color='g', linestyle='--', label='Expected: 0.5')
plt.xlabel('Salience Score')
plt.ylabel('Density')
plt.legend()
plt.title('Salience Distribution')

# Check for bimodality (bad sign)
from scipy.stats import normaltest
stat, p_value = normaltest(all_salience)
plt.subplot(1, 2, 2)
plt.text(0.5, 0.5, f'Normality test p-value: {p_value:.3f}\n'
                    f'Mean: {mean_sal:.3f}\n'
                    f'Std: {std_sal:.3f}\n'
                    f'Range: [{min(all_salience):.2f}, {max(all_salience):.2f}]',
         ha='center', va='center', fontsize=12)
plt.axis('off')
plt.tight_layout()
plt.savefig('salience_distribution_validation.png')
```

**Success Criteria**:
- ✅ Mean: 0.4-0.6
- ✅ Distribution unimodal (not collapsed to extremes)
- ✅ Std: 0.15-0.25 (moderate variability)

**Failure Criteria**:
- ❌ Bimodal distribution (peaks at 0 and 1)
- ❌ Mean < 0.3 or > 0.7
- ❌ Std < 0.1 (too uniform) or > 0.3 (too chaotic)

---

## Experiment 4: ARC-AGI Exploration Budget

### Hypothesis
Solve rate should peak with exploration budget e ≈ 0.25-0.33 (25-33% of actions).

### Measurement Protocol

**Test Suite**: 20 solvable ARC-AGI games

**Sweep Parameter**: Exploration budget from 0% to 50% in 5% increments

**Data Collection**:
```python
# Modify arc_sage_agent.py
exploration_budgets = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

results = []
for e_budget in exploration_budgets:
    solve_count = 0
    for game_id in test_games:
        solved = run_arc_agent(game_id, exploration_fraction=e_budget)
        solve_count += int(solved)

    results.append({
        'exploration_budget': e_budget,
        'solve_rate': solve_count / len(test_games),
        'games_solved': solve_count
    })

with open('exploration_budget_sweep.json', 'w') as f:
    json.dump(results, f, indent=2)
```

**Analysis**:
```python
import json
import matplotlib.pyplot as plt

# Load results
data = json.load(open('exploration_budget_sweep.json'))

budgets = [d['exploration_budget'] for d in data]
solve_rates = [d['solve_rate'] for d in data]

# Find peak
peak_idx = solve_rates.index(max(solve_rates))
optimal_budget = budgets[peak_idx]

print(f"Optimal exploration budget: {optimal_budget:.2f}")
print(f"Expected: 0.25-0.33")
print(f"Max solve rate: {max(solve_rates):.2%}")

# Plot
plt.figure(figsize=(8, 5))
plt.plot(budgets, solve_rates, 'o-', linewidth=2)
plt.axvline(optimal_budget, color='r', linestyle='--', label=f'Peak: {optimal_budget:.2f}')
plt.axvspan(0.25, 0.33, alpha=0.2, color='g', label='Expected range')
plt.xlabel('Exploration Budget (fraction)')
plt.ylabel('Solve Rate')
plt.title('ARC-AGI Performance vs Exploration Budget')
plt.legend()
plt.grid(alpha=0.3)
plt.savefig('exploration_budget_validation.png')
```

**Success Criteria**:
- ✅ Peak in range 0.20-0.35
- ✅ Clear inverted-U shape (not monotonic)
- ✅ Solve rate drops for e < 0.15 and e > 0.40

**Failure Criteria**:
- ❌ Peak at e = 0.0 (no exploration needed - too easy)
- ❌ Peak at e = 0.5 (equal exploration/exploitation - wrong balance)
- ❌ Monotonic relationship (no optimal point)

---

## Experiment 5: Membot Retrieval Top-K

### Hypothesis
Task performance should peak with k ≈ 3-5 retrieved experiences.

### Measurement Protocol

**Test Tasks**: 50 ARC-AGI games with Membot enabled

**Sweep Parameter**: k (number of retrieved experiences) from 1 to 10

**Data Collection**:
```python
# Modify arc_sage_agent.py membot retrieval
top_k_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

results = []
for k in top_k_values:
    solve_count = 0
    total_time = 0

    for game_id in test_games:
        start = time.time()
        solved = run_arc_agent_with_membot(game_id, top_k=k)
        elapsed = time.time() - start

        solve_count += int(solved)
        total_time += elapsed

    results.append({
        'top_k': k,
        'solve_rate': solve_count / len(test_games),
        'avg_time_per_game': total_time / len(test_games)
    })

with open('membot_topk_sweep.json', 'w') as f:
    json.dump(results, f, indent=2)
```

**Analysis**:
```python
import json
import matplotlib.pyplot as plt

data = json.load(open('membot_topk_sweep.json'))

ks = [d['top_k'] for d in data]
solve_rates = [d['solve_rate'] for d in data]
avg_times = [d['avg_time_per_game'] for d in data]

# Find optimal k
peak_idx = solve_rates.index(max(solve_rates))
optimal_k = ks[peak_idx]

print(f"Optimal k: {optimal_k}")
print(f"Expected: 3-5")

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.plot(ks, solve_rates, 'o-', linewidth=2, color='blue')
ax1.axvline(optimal_k, color='r', linestyle='--', label=f'Peak: k={optimal_k}')
ax1.axvspan(3, 5, alpha=0.2, color='g', label='Expected range')
ax1.set_xlabel('Top-K Retrieved Experiences')
ax1.set_ylabel('Solve Rate')
ax1.set_title('Performance vs Retrieval Count')
ax1.legend()
ax1.grid(alpha=0.3)

ax2.plot(ks, avg_times, 'o-', linewidth=2, color='orange')
ax2.set_xlabel('Top-K Retrieved Experiences')
ax2.set_ylabel('Avg Time per Game (s)')
ax2.set_title('Computation Cost vs Retrieval Count')
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('membot_topk_validation.png')
```

**Success Criteria**:
- ✅ Peak solve rate at k = 3-5
- ✅ Solve rate decreases for k = 1 (insufficient context)
- ✅ Solve rate decreases for k > 7 (information overload)
- ✅ Time increases linearly with k (expected)

**Failure Criteria**:
- ❌ Peak at k = 1 (Membot not helping)
- ❌ Peak at k > 8 (no overload effect)
- ❌ Monotonic increase (more is always better - contradicts theory)

---

## Experiment 6: Direct Coherence Measurement

### Hypothesis
Can compute C directly from system state and confirm C_system ≈ 0.5.

### Measurement Protocol

**Approach**: Combine multiple C estimates

**Data Collection**:
```python
# Add to sage_consciousness.py
def compute_system_coherence(self):
    """Estimate overall system coherence from multiple subsystems."""

    # C1: Trust weights (mean of weights)
    c_trust = np.mean(list(self.plugin_trust_weights.values()))

    # C2: Metabolic state (mapped value)
    state_to_c = {
        MetabolicState.WAKE: 0.5,
        MetabolicState.REST: 0.3,
        MetabolicState.DREAM: 0.7,
        MetabolicState.CRISIS: 0.9
    }
    c_metabolic = state_to_c.get(self.metabolic_controller.current_state, 0.5)

    # C3: Salience (1 - avg_salience, high salience = low coherence with expectations)
    if hasattr(self, 'last_salience_scores') and self.last_salience_scores:
        avg_sal = np.mean([s.total for s in self.last_salience_scores])
        c_salience = 1.0 - avg_sal  # Invert: high salience = surprising = low coherence
    else:
        c_salience = 0.5

    # C4: ATP allocation diversity (std of allocations / mean)
    # Higher diversity = more flexibility = closer to C=0.5
    if hasattr(self, 'last_atp_allocations'):
        allocs = list(self.last_atp_allocations.values())
        if len(allocs) > 1:
            cv = np.std(allocs) / (np.mean(allocs) + 1e-6)  # Coefficient of variation
            # Map CV to coherence: CV=0 → C=1 (rigid), CV=high → C=0.5 (diverse)
            c_atp = max(0.3, 1.0 - cv)  # Rough mapping
        else:
            c_atp = 0.5
    else:
        c_atp = 0.5

    # Weighted average (trust and metabolic most reliable)
    c_system = (
        0.35 * c_trust +
        0.35 * c_metabolic +
        0.15 * c_salience +
        0.15 * c_atp
    )

    return {
        'c_system': c_system,
        'c_trust': c_trust,
        'c_metabolic': c_metabolic,
        'c_salience': c_salience,
        'c_atp': c_atp
    }

# Log every 100 cycles
def log_coherence(self, cycle_num):
    c_vals = self.compute_system_coherence()
    c_vals['cycle'] = cycle_num
    with open('coherence_log.jsonl', 'a') as f:
        f.write(json.dumps(c_vals) + '\n')
```

**Analysis**:
```python
import json
import numpy as np
import matplotlib.pyplot as plt

data = [json.loads(line) for line in open('coherence_log.jsonl')]

cycles = [d['cycle'] for d in data]
c_system = [d['c_system'] for d in data]
c_trust = [d['c_trust'] for d in data]
c_metabolic = [d['c_metabolic'] for d in data]
c_salience = [d['c_salience'] for d in data]
c_atp = [d['c_atp'] for d in data]

print(f"Mean C_system: {np.mean(c_system):.3f}")
print(f"Std C_system: {np.std(c_system):.3f}")
print(f"Expected: 0.5 ± 0.1")

# Plot evolution
plt.figure(figsize=(12, 8))

plt.subplot(3, 1, 1)
plt.plot(cycles, c_system, label='C_system (weighted avg)', linewidth=2)
plt.axhline(0.5, color='r', linestyle='--', alpha=0.5, label='C = 0.5')
plt.fill_between(cycles, 0.4, 0.6, alpha=0.2, color='g', label='Expected range')
plt.ylabel('System Coherence')
plt.legend()
plt.title('Overall System Coherence Over Time')
plt.grid(alpha=0.3)

plt.subplot(3, 1, 2)
plt.plot(cycles, c_trust, label='C_trust', alpha=0.7)
plt.plot(cycles, c_metabolic, label='C_metabolic', alpha=0.7)
plt.plot(cycles, c_salience, label='C_salience', alpha=0.7)
plt.plot(cycles, c_atp, label='C_atp', alpha=0.7)
plt.axhline(0.5, color='r', linestyle='--', alpha=0.3)
plt.ylabel('Component Coherence')
plt.legend()
plt.title('Component Coherence Signals')
plt.grid(alpha=0.3)

plt.subplot(3, 1, 3)
plt.hist(c_system, bins=30, density=True, alpha=0.7)
plt.axvline(np.mean(c_system), color='r', linestyle='--',
            label=f'Mean: {np.mean(c_system):.2f}')
plt.axvline(0.5, color='g', linestyle='--', label='Expected: 0.5')
plt.xlabel('C_system')
plt.ylabel('Density')
plt.legend()
plt.title('System Coherence Distribution')

plt.tight_layout()
plt.savefig('direct_coherence_measurement.png')
```

**Success Criteria**:
- ✅ Mean C_system: 0.45-0.55
- ✅ Std C_system: 0.05-0.15 (stable but not rigid)
- ✅ Component signals vary but average to ~0.5
- ✅ No long-term drift (homeostasis)

**Failure Criteria**:
- ❌ Mean < 0.4 or > 0.6
- ❌ Large drift over time (no homeostasis)
- ❌ Component signals all locked together (no independence)

---

## Integrated Dashboard

### Real-Time Monitoring

**Create Streamlit dashboard**:
```python
import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("SAGE C ≈ 0.5 Validation Dashboard")

# Load all logs
trust_data = [json.loads(line) for line in open('trust_distribution_log.jsonl')]
metabolic_data = [json.loads(line) for line in open('metabolic_state_log.jsonl')]
coherence_data = [json.loads(line) for line in open('coherence_log.jsonl')]

# Current system coherence
if coherence_data:
    current_c = coherence_data[-1]['c_system']
    st.metric("Current System Coherence", f"{current_c:.3f}",
              delta=f"{current_c - 0.5:+.3f} from optimal")

# Trust distribution
col1, col2 = st.columns(2)
with col1:
    if trust_data:
        latest_trust = trust_data[-1]
        st.metric("Mean Trust", f"{latest_trust['mean']:.3f}")
        st.metric("Trust Diversity (std)", f"{latest_trust['std']:.3f}")

with col2:
    if metabolic_data:
        from collections import Counter
        states = [d['state'] for d in metabolic_data[-1000:]]  # Last 1000 cycles
        state_dist = Counter(states)
        wake_pct = state_dist.get('WAKE', 0) / len(states) * 100
        st.metric("WAKE % (last 1k)", f"{wake_pct:.1f}%")

# Coherence evolution plot
if coherence_data:
    df = pd.DataFrame(coherence_data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['cycle'], y=df['c_system'],
                             mode='lines', name='C_system'))
    fig.add_hline(y=0.5, line_dash="dash", line_color="red",
                  annotation_text="C = 0.5")
    fig.add_hrect(y0=0.4, y1=0.6, fillcolor="green", opacity=0.1,
                  annotation_text="Expected range")
    st.plotly_chart(fig)

# Health check
st.subheader("Validation Health Check")
checks = []
if coherence_data:
    avg_c = sum(d['c_system'] for d in coherence_data) / len(coherence_data)
    checks.append(("System coherence ≈ 0.5", 0.45 <= avg_c <= 0.55, f"{avg_c:.3f}"))
if trust_data:
    avg_trust = sum(d['mean'] for d in trust_data) / len(trust_data)
    checks.append(("Mean trust 0.5-0.7", 0.5 <= avg_trust <= 0.7, f"{avg_trust:.3f}"))

for check_name, passed, value in checks:
    st.write(f"{'✅' if passed else '❌'} {check_name}: {value}")
```

**Run**: `streamlit run validation_dashboard.py`

---

## Summary: Complete Validation Suite

### Experiments Overview

| Exp | Subsystem | Prediction | Measurement | Duration |
|-----|-----------|------------|-------------|----------|
| 1 | Trust weights | Mean 0.5-0.7, std 0.15-0.25 | Plugin trust log | 1000 cycles |
| 2 | Metabolic states | WAKE 60-70%, avg C ≈ 0.5 | State distribution | 2000 cycles |
| 3 | SNARC salience | Mean 0.4-0.6, unimodal | Salience histogram | 1000 cycles |
| 4 | ARC exploration | Peak at e=0.25-0.33 | Game solve rate sweep | 20 games × 11 budgets |
| 5 | Membot top-k | Peak at k=3-5 | Retrieval count sweep | 50 games × 10 k values |
| 6 | Direct C measure | C_system ≈ 0.5 ± 0.1 | Combined coherence | 1000 cycles |

### Expected Timeline

**Week 1**: Implement logging (Exp 1, 2, 3, 6)
**Week 2**: Run continuous collection (1000-2000 cycles)
**Week 3**: ARC sweeps (Exp 4, 5)
**Week 4**: Analysis and dashboard

### Success Signature

If C ≈ 0.5 theory is correct, we should see:
- ✅ All 6 experiments confirm predictions
- ✅ Multiple subsystems independently cluster around 0.5
- ✅ Homeostatic stability (returns to 0.5 after perturbations)
- ✅ No subsystem collapsed to extremes (C → 0 or C → 1)

**This would constitute EXTRAORDINARY validation of theoretical predictions.**

---

## Future Extensions

### Cross-System Validation

Apply same protocols to:
- Other LLM architectures (GPT-4, Claude)
- Biological data (EEG, neural recordings)
- Social systems (team dynamics, markets)

### Perturbation Experiments

Deliberately push C away from 0.5:
- Force high coherence: Reduce plugin diversity, increase coupling
- Force low coherence: Random plugin selection, ignore trust weights
- Measure: Performance degradation, recovery time to C ≈ 0.5

### Optimization Experiments

Use C as optimization target:
- Monitor C_system in real-time
- Apply control: If C < 0.4 → increase integration, if C > 0.6 → increase diversity
- Test: Does explicit C-targeting improve performance?

---

**Document Status**: **COMPLETE**

**Purpose**: Provides concrete experimental protocols to validate Session #51 predictions

**Next Action**: Implement logging in SAGE consciousness loop and begin data collection

---
