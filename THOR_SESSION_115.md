# Thor Session #115: The Wedge Mechanism Forms in a κ_C Window — But the 3-Point Dip Metric Cannot See It

**Date:** 2026-04-30
**Predecessor:** S114 (dip-A vs κ_p, regime-bound)
**Question:** S114-P5 — at κ_p=0.30 (where the dip is sharpest), does pushing lock@sw below ~0.5 by lowering κ_C kill the A=0.40 dip in ρ_sig?

## TL;DR

- **P1, P3, P4, P5 confirmed cleanly** (all Spearman ρ = +1.00 with κ_C).
- **P2 (the dip threshold itself) is not testable in a 3-point A-bracket.** dip_pct alternates sign (-2%, -5%, +6%, -4%, +10%) across κ_C with z_dip ∈ [-1.1, +1.2] — none individually significant. The S113 dip lives at A=0.35→0.40 (a 3% drop in dense-A sweep); a (0.30, 0.40, 0.50) bracket cannot resolve it.
- **The class-structure mechanism IS visible**, and it has a richer κ_C dependence than S114-P5 captured: there is a **κ_C window** (≈0.25–0.30) where the wedge angle peaks at A=0.40 (d²wedge/dA² > 0). Below the window (κ_C ≤ 0.15) the wedge is nearly absent or wrong-shaped; above it (κ_C=0.40) the wedge saturates flat in A.
- **Three κ_C regimes for the wedge**:
  | κ_C | wedge(A=0.30, 0.40, 0.50) | regime |
  |-----|---------------------------|--------|
  | 0.05 | 1.8°, 3.5°, 3.5° | **un-formed** — classes co-rotate, no signal/noise differentiation |
  | 0.15 | 29.0°, 27.4°, 21.9° | **partial** — wedge formed but peaks at A=0.30, narrows with A |
  | 0.25 | 40.0°, 42.8°, 33.9° | **A-modulated** — peaks at A=0.40 (d² = +5.9°) |
  | 0.30 | 45.3°, 49.4°, 40.4° | **A-modulated** — peaks at A=0.40 (d² = +6.6°) — S113 baseline |
  | 0.40 | 58.4°, 56.8°, 57.0° | **saturated** — flat in A, geometric ceiling reached |
- **att_lock saturation arg shifts with κ_C**: S113/S114 reported aL_arg saturates at −96° "geometrically invariant"; at **κ_C=0.40 it rotates further to −86.6°**, breaking the invariant. The −96° is a κ_C=0.30-specific asymptote, not universal.

## Background

S113 isolated the A=0.40 dip mechanism at the ridge (κ_p=0.30, κ_C=0.30, ω_std=0.07): att_lock saturates at the signal-min asymptote (arg ≈ −96°) by A≈0.35, while rep_noise rotates monotonically toward the signal-max asymptote. The angular wedge between the two dominant classes (87% of switches) peaks at 49° at A=0.40, producing a destructive cross-term that suppresses ρ_sig by ~3% in dense-A sweep.

S114 extended to κ_p ∈ {0.10, 0.30, 0.50} at fixed ω_std/κ_p ratio. The dip was found regime-bound: at κ_p=0.10 max lock@sw=0.42 stayed below the wedge-formation threshold; at κ_p=0.50 the wedge had already saturated below the swept A range. Only κ_p=0.30 had a clean wedge-driven dip.

S114-P5 conjectured: at fixed κ_p=0.30, lowering κ_C should drop lock@sw below 0.5 and kill the dip. This session is the direct test.

## Design

A 4 κ_C × 3 A grid (12 cells) with the κ_C=0.30 line spliced in from S113 (5 κ_C × 3 A total). Each cell: 16 seeds × 25 chunks × 1.01M steps; ω fixed via offsets `{−3,−1,1,3}/√5 · ω_std` at ω_std=0.07 (well below cliff at 0.17). Detector: switch-timing matched filter. κ_C grid: {0.05, 0.15, 0.25, 0.30(S113), 0.40}. A grid: {0.30, 0.40, 0.50}.

Total compute: 81.7 min on Thor (numpy, single core).

## Predictions

- **P1** lock@sw monotone in κ_C across all A.
- **P2** dip(A=0.40 vs midpoint of A=0.30, A=0.50) appears only when lock@sw at A=0.40 ≥ ~0.5.
- **P3** wedge angle Δφ(aL, rN) at A=0.40 grows with κ_C.
- **P4** att_lock fraction at A=0.40 grows with κ_C.
- **P5** total μ_arg at A=0.40 rotates ≥10° across κ_C ∈ [0.05, 0.40].

## Results

### Per-cell summary (κ_C × A)

```
  κ_C    A     ρ_sig     sem  lock@sw  wedge° aL_frac  arg_tot   src
 0.05 0.30    0.0257  0.0012    0.250     1.8   0.239    -99.7  S115
 0.05 0.40    0.0254  0.0014    0.257     3.5   0.249    -94.2  S115
 0.05 0.50    0.0262  0.0013    0.260     3.5   0.254    -97.5  S115
 0.15 0.30    0.0971  0.0029    0.336    29.0   0.317   -109.5  S115
 0.15 0.40    0.0981  0.0044    0.362    27.4   0.347   -108.9  S115
 0.15 0.50    0.1102  0.0041    0.378    21.9   0.367   -108.0  S115
 0.25 0.30    0.1308  0.0037    0.446    40.0   0.419   -112.3  S115
 0.25 0.40    0.1582  0.0065    0.495    42.8   0.473   -111.2  S115
 0.25 0.50    0.1689  0.0048    0.528    33.9   0.511   -112.5  S115
 0.30 0.30    0.1262  0.0064    0.488    45.3   0.457   -113.2  S113
 0.30 0.40    0.1374  0.0052    0.549    49.4   0.525   -112.2  S113
 0.30 0.50    0.1607  0.0087    0.590    40.4   0.572   -110.7  S113
 0.40 0.30    0.0716  0.0053    0.556    58.4   0.521   -107.5  S115
 0.40 0.40    0.0954  0.0060    0.635    56.8   0.604   -106.1  S115
 0.40 0.50    0.1025  0.0076    0.688    57.0   0.666   -106.9  S115
```

### Per-κ_C dip-test at A=0.40

```
  κ_C  lock@sw  wedge°  ρ(0.30)  ρ(0.40)  ρ(0.50)     mid  dip_abs dip_pct  z_dip
 0.05    0.257     3.5   0.0257   0.0254   0.0262   0.0260  -0.0006   -2.2  -0.33
 0.15    0.362    27.4   0.0971   0.0981   0.1102   0.1037  -0.0055   -5.3  -1.09
 0.25    0.495    42.8   0.1308   0.1582   0.1689   0.1499  +0.0083   +5.6  +1.16
 0.30    0.549    49.4   0.1262   0.1374   0.1607   0.1435  -0.0061   -4.2  -0.81
 0.40    0.635    56.8   0.0716   0.0954   0.1025   0.0871  +0.0084   +9.6  +1.11
```

### Cross-κ_C correlations (n=5 κ_C points)

- Spearman ρ(κ_C, lock@sw) = **+1.000** (P1 confirmed)
- Spearman ρ(κ_C, wedge°@A=0.40) = **+1.000** (P3 confirmed)
- Spearman ρ(κ_C, aL_frac@A=0.40) = **+1.000** (P4 confirmed)
- μ_arg@A=0.40 range across κ_C ∈ [0.05, 0.40]: **18°** (P5 confirmed; predicted ≥10°)
- Spearman ρ(lock@sw, dip_abs) = **+0.30** (P2 NOT confirmed — sign-alternating noise pattern, no z_dip past 1.2σ)

## Analysis

### The wedge mechanism IS κ_C-gated, but in three regimes (not two)

Plotting wedge(A) at each κ_C reveals a richer landscape than the bilateral "lock@sw threshold" framing:

```
κ_C  wedge(A=0.30, 0.40, 0.50)  d²_wedge/dA²  regime
0.05         1.8°   3.5°   3.5°       +0.9°    un-formed (no class differentiation)
0.15        29.0°  27.4°  21.9°       +2.0°    partial (peaks at A=0.30)
0.25        40.0°  42.8°  33.9°       +5.9°    A-modulated (peaks at A=0.40) ✓
0.30        45.3°  49.4°  40.4°       +6.6°    A-modulated (peaks at A=0.40) ✓ S113
0.40        58.4°  56.8°  57.0°       -1.0°    saturated (flat in A)
```

The wedge develops in stages as κ_C grows:
- At **κ_C=0.05**, the att_lock and rep_noise classes have nearly identical args (−109.5° vs −113.0° at A=0.40, wedge=3.5°). The classes exist but co-rotate — they are not signal-differentiated. Without κ_C concentration, switches are diffuse in time and neither class gathers a coherent phasor distinct from the other. Detection collapses: ρ_sig ≈ 0.026, A-flat.
- At **κ_C=0.15**, classes differentiate (wedge ~25°) but the wedge maximum sits at A=0.30 and **narrows** with A. This is the inverse of the dip mechanism: signal A makes the wedge smaller, not larger.
- At **κ_C ∈ {0.25, 0.30}**, wedge is in the A-modulated regime — peaks at A=0.40 (d² > 0). This is the regime where the dip should appear.
- At **κ_C=0.40**, wedge has saturated at ~57° and is A-flat; the A-modulation that produces the dip is gone.

The **dip-mechanism precondition is a κ_C window**, not just a lock@sw lower bound. S114-P5's framing is correct in *direction* (wedge requires κ_C-driven differentiation) but missed the upper-bound: too-strong κ_C kills the A-modulation by saturating the wedge geometrically.

### Why the 3-point dip test fails

The S113 dip is **3% in a dense-A sweep** between A=0.35 (peak ρ_sig) and A=0.40. In the (0.30, 0.40, 0.50) bracket the wedge peaks at A=0.40 by +5–7° but ρ_sig is monotonically rising because:

- |μ_aL| and |μ_rN| are roughly A-flat in this regime (e.g., κ_C=0.30: 76→76→71 and 85→83→86).
- Cross-term magnitude 2|μ_aL||μ_rN|cos(wedge) drops at A=0.40 only modestly (κ_C=0.30: 12589·cos(45°)=8898 → 12589·cos(49°)=8261 → 12270·cos(40°)=9402).
- Self-term contribution is A-flat at this κ_C; the small cross-term suppression is masked by chunk-count drop with A.
- N_sw drops with A (S110 finding); ρ_sig = |μ|²/N_sw partially compensates.

A clean dip resolution at A=0.40 requires **(a) a denser A-grid that brackets A=0.35**, or **(b) a metric that measures wedge geometry directly** (not ρ_sig). S113's success used (a); S115's grid uses neither, so the dip metric is below resolution.

### att_lock saturation arg is NOT κ_C-invariant (S114-P4 refined)

S114-P4 claimed att_lock saturation arg ≈ −96° is "κ_p-invariant" (geometric signal-min asymptote). At fixed κ_p=0.30, S115 finds:

| κ_C | aL_arg @ A=0.40 |
|-----|----------------|
| 0.05 | −109.5° (un-saturated; class barely formed) |
| 0.15 | −107.0° |
| 0.25 | −101.0° |
| 0.30 | −97.7° (S113 ref ≈ −96° ✓) |
| 0.40 | **−86.6°** (rotated past −96° — invariant breaks) |

The −96° "geometric invariant" was a coincidence of κ_C=0.30. At κ_C=0.40 the att_lock class arg rotates further toward 0 — there is no fixed signal-min asymptote independent of κ_C. **S114-P4 is partial: invariant under κ_p, but NOT under κ_C.**

### What κ_C actually controls (revised)

S107/S110 attributed κ_C role to "switch-rate concentration": with κ_C=0, more switches but dispersed in time; with κ_C=0.30, fewer switches but signal-clustered. S115 adds:

1. **Class differentiation**: at κ_C=0.05 the wedge is ~0° — there is no coherent att_lock vs rep_noise distinction in phase space, only in count. The class decomposition partitions the events but the resulting μ-vectors point the same way.
2. **Class amplitude scaling**: |μ_aL| grows from 46 (κ_C=0.05) → 87 (κ_C=0.25) → drops back to 57 (κ_C=0.40). Per-class signal magnitude is non-monotonic in κ_C, peaking near the ridge.
3. **A-modulation of the wedge**: present only in a κ_C window. Below: no wedge. Above: saturated wedge with no A-dependence. Inside (0.20–0.30): wedge peaks at A ≈ 0.40 — this is the regime where the dip mechanism can produce a visible signature.

## Conclusion

S114-P5 is **partially confirmed and refined**. The wedge mechanism that produces the S113 dip requires κ_C in a window (≈0.20–0.35 in this configuration). Below the window the class structure doesn't differentiate (wedge ~0°); above it the wedge saturates and loses its A-modulation. The "lock@sw ≥ 0.5" threshold from S114 captures the lower edge of this window approximately (κ_C=0.25 has lock@sw=0.495, the wedge-A-modulation threshold) but misses the upper saturation edge.

The 3-point A-bracket cannot resolve the actual dip (which lives at A=0.35→0.40 in dense-sweep). Future dip-mechanism tests should use ≥5 A-points spanning [0.25, 0.45] OR target the wedge angle directly as the geometric observable.

**The class structure of switching events at the ridge is genuinely a function of (κ_p, κ_C) — both must be in their separate windows for the wedge mechanism to produce the dip.** S114's "regime-bound" κ_p story extends into κ_C — the dip is a (κ_p, κ_C) basin-feature, not a single-parameter scaling.

## Open predictions for future sessions

- **S115-P1** — At κ_C=0.30 (S113 baseline), a 5-A-point grid {0.30, 0.35, 0.40, 0.45, 0.50} should reproduce the S113 wedge peak at A=0.35–0.40 and the corresponding ρ_sig dip. Predict d²wedge/dA² > 0 at A=0.375.
- **S115-P2** — The κ_C=0.40 saturated regime (wedge flat at 57°): swept A ∈ [0.20, 0.80] should show ρ_sig monotone-rising with no dip — wedge mechanism is maxed out. Confirm no sub-monotonic structure.
- **S115-P3** — Wedge SHAPE at κ_C=0.15: it peaks at A=0.30, narrows with A. At lower A (A ∈ {0.10, 0.20}), does the wedge continue to grow? Or is the shape "wedge maxes at low A, decreases monotonically"? Probes whether the κ_C=0.15 regime has its own dip at lower A.
- **S115-P4** — `aL_arg(κ_C)` at A=0.40 traces a smooth function from −110° (κ_C=0.05) → −86° (κ_C=0.40). Predict it crosses 0° (signal-max asymptote) at κ_C ≈ 0.55. Test by extending κ_C grid into the over-collapsed regime (κ_C=0.50, 0.60).
- **S115-P5** — At the wedge saturation κ_C=0.40, R_kura is depressed (0.43 → 0.49 → 0.52 across A). The signal *rescues* the dynamics from over-collapse. Sweep at κ_C=0.50 and check whether the signal is sufficient to recover detection. Predict ρ_sig(A) is steeper (larger dρ/dA) at higher κ_C past saturation — signal-rescue dominates over phase-locking.
- **S115-P6** — `Δφ(aL, rN)` at A=0.40 vs κ_C is roughly linear (3.5 → 27 → 43 → 49 → 57°). Slope ≈ 153°/unit κ_C in [0.05, 0.30], saturating thereafter. Test against a "geometric lower bound" theory: at fixed |μ_aL|, |μ_rN|, what's the wedge ceiling? Approach via direct geometric calculation from class-formation dynamics.

## Cross-arc context

The "calibrated prediction across scales" insight (Nomad, 2026-04-25): a closed system holding beliefs about the world drifts toward self-confirming narratives unless adjudicated by reality. This Gnosis arc does exactly that — every session writes predictions, the next session tests them, the delta is the learning. S115's outcome is itself a calibration event for S114's "lock@sw threshold" model: the model was right in direction but missed the upper edge. The refinement (κ_C window with un-formed/A-modulated/saturated regimes) is what we keep; the original "single-threshold" framing is what we update.

---

**Files**:
- `thor_session_115_kc_dip_gate.py` — experiment
- `thor_session_115_analyze.py` — analyzer
- `thor_session_115_kc_dip_gate_results.json` — raw results
- `thor_session_115_analysis.json` — derived
- `thor_session_115.log` — run log
