# Thor Session #114: Dip-A vs κ_p — Linear Scaling Holds at Mid κ_p, Breaks at the Extremes

## TL;DR

Tested S113-P1 — does the att_lock-saturation dip scale linearly with κ_p? Held ratio ω_std/κ_p = 0.233 fixed; swept κ_p ∈ {0.10, 0.50} (recycling S113 for κ_p=0.30). Findings:

- **κ_p=0.50**: dip observed at A=0.70 (predicted 0.67). Linear-scaling slope (κ_p=0.30→0.50) is 1.5, vs predicted 1.33. **Approximately confirmed within grid resolution**, but the dip is only ~1σ deep (peak 0.205, dip 0.192, recovery 0.201; flank-vs-dip z≈0.88).
- **κ_p=0.10**: ρ_sig **monotone-rising** through A=0.30 (0.0023 → 0.0102 → 0.0137 → 0.0218 → 0.0339 → 0.0523). **No dip in sampled range.** Predicted dip-A=0.13 absent. The linear scaling **fails** at low κ_p.
- **Mechanism diagnostic**: at κ_p=0.10, the att_lock and rep_noise classes co-rotate in near-lockstep — pairwise wedge stays < 6° across the entire A grid. Lock@sw maxes at 0.42, well below the ~0.55 lock fraction at which the wedge mechanism engaged in S113.
- **At κ_p=0.50**, att_lock has already saturated by A=0.40 (arg=−94°, very close to S113's saturation locus −96°). The visible dip at A=0.70 is NOT a wedge-max event — wedge is monotone-narrowing through the sweep. It's a multi-pair cross-term reorganization: 6 of the 6 pair cross-terms drop simultaneously at A=0.70.
- **P4 (saturation arg κ_p-invariant)** confirmed: −96.6° at κ_p=0.30, −100.5° at κ_p=0.50. The geometric "signal-min asymptote" survives the κ_p change to within ~5°.

**Net**: the att_lock saturation locus IS κ_p-independent (geometric invariant, P4 ✓), but **dip-A is NOT a clean linear function of κ_p**. The dip is a regime-bound phenomenon, not a universal scaling.

## Background

S113 closed the A=0.40 ρ_sig dip at the ridge geometry (κ_p=0.30, κ_C=0.30, ω_std=0.07, ratio=0.233):
- ρ_sig peaks at A=0.35 (0.141), dips at A=0.40 (0.137, 3% drop), recovers at A=0.45 onward.
- Switches partition into 4 classes by `(gate × R_kura > 0.9)` at switch time. By A ≥ 0.30, (att_lock, rep_noise) carries ≥87% of events.
- Per-class arg(μ) rotates with A but at different rates:
  - att_lock: −157° → −96° (saturates near A=0.35 at the geometric "signal-min asymptote")
  - rep_noise: +175° → −136° (monotone toward signal-max asymptote)
- The wedge between dominant pair maxes at 49° at A=0.40, driving an 11% drop in `2|μ_aL||μ_rN|cos(Δφ)`.

S113-P1 prediction: dip-A ∝ κ_p. Argument: att_lock saturation A_sat sets where the wedge maximum lives, and A_sat is gated by the Kuramoto coupling K=κ_p (K-coupled lock phase saturates at Δφ ~ A/K → π/2). Predicted dip-A: 0.13 (κ_p=0.10), 0.40 (κ_p=0.30, S113), 0.67 (κ_p=0.50).

## Design

Held ratio ω_std/κ_p = 0.233 fixed (S113 baseline) so phase-locking quality is matched across κ_p (and well below the Kuramoto cliff at πK/4):

| κ_p   | ω_std    | πK/4 cliff | predicted dip-A |
|-------|----------|------------|-----------------|
| 0.10  | 0.0233   | 0.0785     | 0.13            |
| 0.30  | 0.07     | 0.236      | 0.40 (S113)     |
| 0.50  | 0.117    | 0.392      | 0.67            |

A grids per κ_p (each cell = 16 seeds × 25 chunks × 4000s):
- **κ_p=0.10**: A ∈ {0.05, 0.10, 0.13, 0.16, 0.20, 0.30}
- **κ_p=0.30**: recycled S113 — A ∈ {0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50}
- **κ_p=0.50**: A ∈ {0.40, 0.55, 0.65, 0.70, 0.80, 0.95}

Run-time on Thor: 4899 s = 81.6 min for the 12 new cells.

## Results

### A-sweep curves (per κ_p)

**κ_p = 0.10  (ω_std=0.0233):**

| A    | ρ_sig  | \|μ_st\|  | arg(μ_st) | R_kura | lock@sw | aL_arg | rN_arg | wedge |
|------|--------|---------|-----------|--------|---------|--------|--------|-------|
| 0.05 | 0.0023 |  0.74   | −125.7°   | 0.358  |  0.232  | +178° |  −178° |  0.4° |
| 0.10 | 0.0102 |  1.68   | −127.1°   | 0.361  |  0.272  | −178° |  −173° |  5.4° |
| 0.13 | 0.0137 |  1.93   | −133.4°   | 0.366  |  0.304  | −173° |  −176° |  3.5° |
| 0.16 | 0.0218 |  2.48   | −128.1°   | 0.380  |  0.314  | −171° |  −171° |  0.2° |
| 0.20 | 0.0339 |  3.04   | −124.9°   | 0.387  |  0.342  | −162° |  −166° |  3.6° |
| 0.30 | 0.0523 |  3.75   | −125.5°   | 0.447  |  0.415  | −152° |  −153° |  0.9° |

ρ_sig monotone-rising. att_lock and rep_noise classes co-rotate (wedge < 6° throughout).

**κ_p = 0.30  (ω_std=0.07, S113):**

| A    | ρ_sig  | \|μ_st\|  | arg(μ_st) | R_kura | lock@sw | aL_arg | rN_arg | wedge |
|------|--------|---------|-----------|--------|---------|--------|--------|-------|
| 0.10 | 0.0393 |  3.50   | −120.0°   | 0.324  |  0.269  | −157° |  +175° | 27.9° |
| 0.20 | 0.0902 |  5.13   | −114.2°   | 0.401  |  0.370  | −131° |  −169° | 38.4° |
| 0.25 | 0.1060 |  5.52   | −113.5°   | 0.460  |  0.442  | −119° |  −162° | 43.5° |
| 0.30 | 0.1262 |  5.99   | −113.2°   | 0.503  |  0.488  | −108° |  −154° | 45.3° |
| 0.35 | 0.1410 |  6.31   | −114.7°   | 0.515  |  0.517  | −106° |  −152° | 45.7° |
| **0.40** | **0.1374** | 6.11 | −112.2° | 0.527 | 0.549  | **−98°**  | **−147°** | **49.4°** |
| 0.45 | 0.1465 |  6.36   | −110.8°   | 0.537  |  0.561  |  −96° |  −140° | 44.2° |
| 0.50 | 0.1607 |  6.54   | −110.7°   | 0.541  |  0.590  |  −96° |  −136° | 40.4° |

S113 baseline: peak A=0.35 (recovery 0.45+), dip at A=0.40, wedge max at A=0.40 (49°).

**κ_p = 0.50  (ω_std=0.117):**

| A    | ρ_sig  | \|μ_st\|  | arg(μ_st) | R_kura | lock@sw | aL_arg | rN_arg | wedge |
|------|--------|---------|-----------|--------|---------|--------|--------|-------|
| 0.40 | 0.1335 |  5.97   | −108.9°   | 0.540  |  0.573  |  −94° |  −147° | 53.3° |
| 0.55 | 0.1422 |  6.13   | −111.6°   | 0.558  |  0.624  |  −98° |  −138° | 40.1° |
| 0.65 | 0.2045 |  7.25   | −109.3°   | 0.566  |  0.651  | −100° |  −131° | 30.8° |
| **0.70** | **0.1922** | 7.03 | −109.3° | 0.564 | 0.643  | **−99°** | **−129°** | **29.9°** |
| 0.80 | 0.2006 |  7.15   | −109.2°   | 0.565  |  0.662  | −100° |  −126° | 25.3° |
| 0.95 | 0.2117 |  7.43   | −109.9°   | 0.567  |  0.678  | −102° |  −123° | 21.4° |

By A=0.40, att_lock has already saturated (−94°, near the S113 −96° asymptote). Wedge is monotone-narrowing through the sweep. Dip at A=0.70 (peak A=0.65), wedge there is only 30°.

### P1: dip-A linear scaling

Observed dip-A:
- κ_p=0.30: 0.40 (S113 reference)
- κ_p=0.50: **0.70** (predicted 0.67) — within grid resolution (0.05 step)
- κ_p=0.10: **NONE in [0.05, 0.30]** — predicted 0.13 not seen

Two-point linear fit (excluding κ_p=0.10 which has no dip):
- dip-A = **1.50 · κ_p − 0.05**, r²=1.000 (only 2 points)
- Predicted slope: **4/3 = 1.33** (linear scaling through origin)

The slope is 13% higher than predicted, intercept slightly negative, but the prediction is approximately correct over [0.30, 0.50]. The bigger story is **at κ_p=0.10 the dip is absent**.

Why does dip-A scaling break at low κ_p? **Lock fraction**:

| κ_p   | A grid covers   | max lock@sw | S113 dip lock@sw |
|-------|-----------------|-------------|-------------------|
| 0.10  | 0.05–0.30       | 0.42        |  ~0.55 (S113)     |
| 0.30  | 0.10–0.50       | 0.59        |   0.55            |
| 0.50  | 0.40–0.95       | 0.68        |   0.65            |

At κ_p=0.10, lock@sw never reaches the ~0.55 threshold at which S113's dip emerged. The wedge mechanism needs a sufficiently dominant att_lock class to drive the destructive cross-term — and that requires lock fraction above some floor (empirically ~0.5).

At κ_p=0.10, the system is in a **weak-lock regime** where neither att_lock nor rep_noise dominates strongly enough to set up the differential-rotation wedge. Both classes co-rotate slowly (per-A att_lock rate ~+128°/A, rep_noise ~+101°/A — large rates but **small differential**). This keeps the wedge < 6° everywhere.

### P4: att_lock saturation arg ≈ −96° invariant across κ_p

| κ_p   | sat_arg (top-3 high-A) | R (cross-A) |
|-------|------------------------|-------------|
| 0.10  | −161.6°                | 0.991       |
| 0.30  | −96.6°                 | 1.000       |
| 0.50  | −100.5°                | 1.000       |

At κ_p=0.30 and 0.50: sat_arg agrees to within 4° with the S113 reference −96°. The geometric "signal-min asymptote" **is approximately κ_p-independent** as predicted.

At κ_p=0.10, the "saturation arg" of −161.6° is **misleading**: the system has not reached saturation in the sampled range. att_lock arg is still rotating at +128°/A through A=0.30 and would only reach −96° at A ~ 1.5 (extrapolating the rotation rate). What we measure as "top-3 plateau" is actually the in-rotation value.

So **P4 is supported in regimes where saturation is reachable** (κ_p=0.30 and κ_p=0.50). At κ_p=0.10 the test is moot — we're nowhere near saturation.

### P5b: wedge max ≈ dip A — broken at κ_p=0.50

| κ_p   | wedge max @ A | wedge max value | dip A   | match? |
|-------|---------------|-----------------|---------|--------|
| 0.10  |  0.10  (5.4°) | tiny            | NONE    | n/a    |
| 0.30  |  0.40 (49.4°) | 49°             | 0.40    | ✓ exact|
| 0.50  |  0.40 (53.2°) | 53°             | 0.70    | ✗      |

At κ_p=0.50, the wedge is monotone narrowing across the sweep — it must have peaked at A < 0.40 (outside our grid). The dip at A=0.70 is **not a wedge-maximum event**.

To check what causes the κ_p=0.50 dip, decompose the cross-term sum across all 6 pairs at A=0.65 (peak), A=0.70 (dip), and A=0.80 (recovery):

| pair       | A=0.65 | A=0.70 | A=0.80 | Δ(0.65→0.70) | Δ(0.70→0.80) |
|------------|--------|--------|--------|--------------|--------------|
| aL_aN      | +2588  | +1978  | +1746  |   −610       |   −232       |
| aL_rL      | +1304  | +1143  |  +990  |   −161       |   −153       |
| aL_rN      |+12048  |+11769  |+12862  |   −279       |  +1093       |
| aN_rL      |  +220  |  +180  |  +122  |    −40       |    −58       |
| aN_rN      | +1410  | +1093  | +1107  |   −317       |    +14       |
| rL_rN      |  +696  |  +627  |  +672  |    −69       |    +45       |
| **total**  |+18267  |+16789  |+17499  |   **−1478**  |   **+710**   |

All 6 pairs drop simultaneously at A=0.70. The **dominant aL_rN pair contributes only 19% of the total cross-term drop** at the dip. So at κ_p=0.50, the dip is NOT explained by the att_lock/rep_noise wedge mechanism — multiple pairs reorganize together. This is a different (less understood) mechanism.

Statistical significance: peak-A=0.65 ρ_sig=0.205 ± 0.008; dip-A=0.70 ρ_sig=0.192 ± 0.010; recovery-A=0.80 ρ_sig=0.201 ± 0.007. Flank-avg minus dip = 0.011 ± 0.012. **z ≈ 0.88**. Not statistically significant in single-cell terms — could be noise blip.

### P3: rep_noise rotation rate

| κ_p   | rN rate (deg/A) | κ_p · rate |
|-------|-----------------|------------|
| 0.10  |  +101  ± 16     |  +10       |
| 0.30  |  +118  ±  7     |  +35       |
| 0.50  |   +45  ±  7     |  +22       |

The κ_p · rate "constant" varies 2–3×, so **rep_noise rotation rate is not cleanly inverse in κ_p**. At κ_p=0.50 the rotation is much slower (+45°/A) — consistent with both att_lock and rep_noise being near saturation (att_lock already saturated, rep_noise also slowing). At κ_p=0.10 the rate is +101°/A but only over the 6 sampled A's (most of which are pre-saturation). The rate in the pre-saturation regime depends on rotation dynamics that are not captured by a single 1/κ_p scaling.

## Mechanism status

The S113 wedge-cross-term mechanism is **valid as a description of the κ_p=0.30 ridge** but does not generalize cleanly to other κ_p:

- **At κ_p=0.10** (weak-lock regime): att_lock and rep_noise classes never differentiate enough; wedge stays < 6°. No dip emerges in observable A range. The mechanism **doesn't engage**.
- **At κ_p=0.30** (S113 ridge): att_lock saturates near A=0.40, wedge maxes there, classic dip mechanism works.
- **At κ_p=0.50** (stronger lock): att_lock saturated by A=0.40 (below grid). Wedge is post-max, monotone-narrowing. The visible "dip" at A=0.70 is small (6%, z≈0.9), spread across all pair-cross-terms — looks like a different (multi-pair) reorganization, not the wedge mechanism.

What IS preserved across κ_p:
- **The att_lock saturation arg ≈ −96° to −100°** — geometric invariant (signal-min asymptote).
- ρ_sig peaks scale with κ_p (consistent with S107: R_peak grows linearly with κ_p).
- The presence of a dip at all in the κ_p=0.50 sweep, even if small.

What IS NOT preserved:
- Linear dip-A ∝ κ_p scaling — fails at κ_p=0.10 (mechanism doesn't engage).
- Single-mechanism (wedge) explanation — at κ_p=0.50 it's a multi-pair reorganization.

## Predictions

- **S114-P1**: at κ_p=0.10, extending A grid to A ∈ {0.40, 0.60, 1.0, 1.5} should eventually reveal a dip when lock@sw clears ~0.5. Predicted dip-A in the range [0.5, 1.5] — a non-linear (likely much-larger) shift relative to the S113 reference scaling.
- **S114-P2**: at κ_p=0.50, the wedge **maximum** is presumably at some A in [0.20, 0.40] outside our grid. A finer A-sweep at κ_p=0.50 over [0.05, 0.40] should show the rising-wedge / pre-saturation regime that we missed.
- **S114-P3**: the multi-pair cross-term dip at κ_p=0.50 A=0.70 should reproduce in a 32-seed (4× compute) re-run if it's real. If it dissolves to noise, the κ_p=0.50 dip was a statistical artifact and only κ_p=0.30 has a true wedge dip.
- **S114-P4**: at κ_p=0.50, fix A in the saturated regime (e.g., A=0.50, where att_lock is fully saturated), and probe the dynamics on different ω_std (within-cliff). The att_lock saturation arg should be ω_std-independent (geometric invariant).
- **S114-P5**: the dip mechanism requires lock@sw ≥ ~0.5 at the dip A. This is testable: at lower κ_C (where lock fraction is reduced), even κ_p=0.30 should lose the dip.

## Closed predictions

- **S113-P1 (dip-A vs κ_p)**: **PARTIALLY RESOLVED — refined**. Linear scaling holds approximately at κ_p=0.50 (within grid; predicted 0.67, observed 0.70; slope 1.5 vs predicted 1.33). **FAILS at κ_p=0.10** (no dip in observable range; the mechanism requires lock@sw above ~0.5, which doesn't happen in the κ_p=0.10 / [0.05, 0.30] domain). Conclusion: dip-A is not a clean linear function of κ_p; it's regime-bound to where lock@sw clears the saturation threshold.
- **S113-P4 (att_lock saturation arg κ_p-invariant)**: **CONFIRMED** at κ_p ∈ {0.30, 0.50}. Saturation arg = −96° (κ_p=0.30) and −100° (κ_p=0.50), agreeing within 5°. Geometric invariance survives across κ_p in the regime where saturation is reachable. Test moot at κ_p=0.10 (system not saturated).

## Method footnotes

- Simulator: `thor_session_112_omega_cliff.simulate_with_omega` (S111 simulator + ω override). N=4, dt=0.1, σ_n=0.022, signal_freq=0.003, C_threshold=0.55, phi_inverse=0.618. Decimation every 10 steps.
- ω vector built as `omega_base + ω_std · (-3,-1,1,3)/√5` with ω_base=0.1 (fixed offsets, no random ω draw).
- Switch-class decomposition: `thor_session_113_dip_decomposition.{per_switch_state, class_decompose}`. Each switch indexed against decimated `kura/gate` snapshots.
- ρ_sig(seed) = |⟨z_st⟩|² / ⟨N_sw⟩ where z_st is per-chunk switch-timing matched-filter sum.
- Per-class μ_arg circular mean across seeds.
- "att_lock plateau arg" = circular mean of arg(μ_aL) over the top-3 highest-A cells per κ_p sweep.
- All cells: 16 seeds × 25 chunks × 40,000 steps + 10,000 warmup.

## Dataset
- `thor_session_114_dip_kp_scaling_results.json` (12 cells × 16 seeds full per-seed records; 12 MB)
- `thor_session_114_analysis.json` (cross-κ_p summary)
- `s114_run.log` (run-time progress)
- `s114_analysis.log` (analyzer output)

---

*Session 114 — 2026-04-29*
