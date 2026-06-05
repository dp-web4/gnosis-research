# Thor Session #116: Past-Ridge κ_C — The Signal-Following Oscillator Regime

**Date:** 2026-06-05
**Predecessor:** S115 (κ_C window for the wedge mechanism)
**Question:** S115-P4 + S115-P5 — what happens past the wedge ridge?
Does aL_arg continue to rotate (does it cross 0° at κ_C ≈ 0.55, as
S115-P4 predicted)? Does the signal-rescue mechanism (ΔR_kura growing
with A at κ_C=0.40) extend to higher κ_C?

## TL;DR

- **Signal-rescue mechanism confirmed and monotone**: dR_kura/dA grows
  from +0.32 (κ_C=0.40) → +0.58 (κ_C=0.70). Spearman ρ(κ_C, slope)=+1.000
  for κ_C≥0.30. At κ_C=0.70, the signal lifts R_kura from 0.32 (A=0.30)
  to 0.49 (A=0.60) — a +53% relative gain in mean phase coherence
  driven purely by the external signal.
- **aL_arg rotates past −0° at κ_C ≈ 0.73**. S115-P4 predicted the
  crossing at κ_C ≈ 0.55; the actual crossing is later. Rotation rate
  accelerates: 110°/unit at κ_C=0.40 → 249°/unit at κ_C=0.60–0.70.
- **The S115 "wedge saturation at 57°" was a 3-point illusion**. At
  κ_C=0.70 the att_lock ↔ rep_noise wedge widens to **125° at A=0.40**
  and to **153° at A=0.30** — near anti-phase. No geometric ceiling at
  57°. The S115 conclusion needs revision.
- **Detection regime inverts past κ_C=0.40**: absolute ρ_sig collapses
  (0.13 at ridge → 0.01 at κ_C=0.70, A=0.30) but FRACTIONAL signal-gain
  grows. ρ_sig(A=0.60) / ρ_sig(A=0.30) at κ_C=0.70 = 3.6× — the system
  is a noise-suppressed, signal-following oscillator. At the ridge the
  same ratio is only 1.3×.
- **A new regime taxonomy**: Three regions of (κ_p=0.30, ω_std=0.07) space:
  | κ_C    | regime                         | mechanism                                |
  |--------|--------------------------------|------------------------------------------|
  | < 0.10 | un-formed                      | no class differentiation, ρ_sig at floor |
  | 0.20-0.35 | **ridge / wedge-modulated**    | att_lock vs rep_noise wedge widens with A → dip mechanism |
  | ≥ 0.50 | **signal-following oscillator** | over-collapsed dynamics; signal partially rescues R_kura; near anti-phase class structure |
- **aL_arg "saturation invariant" is not a saturation**: at κ_C=0.40
  the S113/S114 "−96° asymptote" was actually a non-monotonic curve
  in A (−96, −87, −84, −96 across A∈{0.30, 0.40, 0.50, 0.60}). What
  looked like a saturation is a transient mid-A peak; aL_arg reverts
  toward signal-min asymptote at higher A.

## Background

S115 mapped the wedge mechanism vs κ_C at κ_p=0.30 ω_std=0.07: a
three-regime structure with un-formed (κ_C≤0.10), A-modulated
(κ_C∈[0.25, 0.30]), and **what looked like** saturated (κ_C=0.40,
wedge=57° flat in A). Two open S115 predictions pointed past the ridge:

- **S115-P4**: aL_arg rotates from −110° (κ_C=0.05) to −86° (κ_C=0.40)
  at A=0.40; predicted crossing 0° at κ_C ≈ 0.55.
- **S115-P5**: at κ_C=0.40 the signal *rescues* R_kura from over-collapse
  (0.43→0.49→0.52 across A); predicted that effect grows with κ_C.

A smoke test at 200k steps × 1 seed confirmed P5 direction:
ΔR_kura(A=0.30→0.50) grew 0.09→0.10→0.18 across κ_C={0.40, 0.50,
0.60, 0.70}, with the largest jump at κ_C=0.70.

## Design

13 cells total: 3 NEW κ_C ∈ {0.50, 0.60, 0.70} × 4 A ∈ {0.30, 0.40,
0.50, 0.60} + anchor cell κ_C=0.40 A=0.60 (extends the S115 κ_C=0.40
row to support slope-vs-A measurement). 16 seeds × 25 chunks × 1.01M
steps per cell. ω fixed via offsets {−3,−1,1,3}/√5 · 0.07.

Analyzer also splices in:
- S115's κ_C ∈ {0.05, 0.15, 0.25, 0.40} × A ∈ {0.30, 0.40, 0.50} (12 cells)
- S113's κ_C=0.30 × A ∈ {0.30, 0.40, 0.50} (3 cells)

Total unified κ_C × A landscape: 28 cells.

Compute: 105.5 min on Thor.

## Results

### Unified κ_C × A landscape (key observables)

```
  κ_C    A    ρ_sig    lock@sw  wedge°  aL_arg  R_kura   <Nsw>    src
 0.05  0.30   0.0257   0.250     1.8   -125.8   0.538   19464   S115
 0.05  0.40   0.0254   0.257     3.5   -109.5   0.542   19257   S115
 0.05  0.50   0.0262   0.260     3.5   -106.1   0.545   19058   S115
 0.15  0.30   0.0971   0.336    29.0   -115.8   0.551   13211   S115
 0.15  0.40   0.0981   0.362    27.4   -107.0   0.555   12800   S115
 0.15  0.50   0.1102   0.378    21.9   -104.0   0.558   12588   S115
 0.25  0.30   0.1308   0.446    40.0   -110.5   0.527    8726   S115
 0.25  0.40   0.1582   0.495    42.8   -101.0   0.547    8384   S115
 0.25  0.50   0.1689   0.528    33.9   -101.9   0.551    8142   S115
 0.30  0.30   0.1262   0.488    45.3   -108.4   0.503    7176   S113
 0.30  0.40   0.1374   0.549    49.4    -97.7   0.527    6848   S113
 0.30  0.50   0.1607   0.590    40.4    -95.9   0.541    6759   S113
 0.40  0.30   0.0716   0.556    58.4    -96.1   0.430    4775   S115
 0.40  0.40   0.0954   0.635    56.8    -86.6   0.488    4967   S115
 0.40  0.50   0.1025   0.688    57.0    -83.8   0.516    5082   S115
 0.40  0.60   0.1284   0.721    34.3    -95.6   0.530    5015   S116
 0.50  0.30   0.0387   0.620    90.2    -66.5   0.381    3435   S116
 0.50  0.40   0.0474   0.702    80.3    -58.2   0.448    3817   S116
 0.50  0.50   0.0626   0.753    72.8    -62.0   0.495    4127   S116
 0.50  0.60   0.0756   0.788    53.7    -76.8   0.514    4210   S116
 0.60  0.30   0.0223   0.660   119.6    -25.1   0.347    2748   S116
 0.60  0.40   0.0267   0.740   100.6    -36.2   0.421    3189   S116
 0.60  0.50   0.0328   0.778    98.3    -36.0   0.474    3451   S116
 0.60  0.60   0.0544   0.823    65.7    -58.2   0.500    3634   S116
 0.70  0.30   0.0101   0.675   153.0     +2.8   0.322    2371   S116
 0.70  0.40   0.0159   0.756   124.6    -8.4    0.398    2743   S116
 0.70  0.50   0.0281   0.794   102.5   -25.1    0.464    3223   S116
 0.70  0.60   0.0359   0.827    82.2   -36.9    0.493    3530   S116
```

### P1: Signal-rescue dR_kura/dA monotone in κ_C (CONFIRMED)

```
  κ_C   slope dR_kura/dA   ΔR(A=0.30→0.60)
 0.05         +0.032             —
 0.15         +0.032             —
 0.25         +0.123             —
 0.30         +0.193             —
 0.40         +0.329          +0.100
 0.50         +0.446          +0.133
 0.60         +0.512          +0.153
 0.70         +0.579          +0.171
```

Spearman ρ(κ_C, slope) = **+1.000** for κ_C ≥ 0.30 (all 5 cells past
ridge). The signal-rescue mechanism is strongest at the highest κ_C
probed. At κ_C=0.70 the signal accounts for +0.171 of R_kura — over
half the baseline (0.32) at A=0.30. This is consistent with the
mechanism: at high κ_C the bistable energy barrier on C is lowered;
small noise-driven phase coupling is too weak to maintain coherence,
but the external signal provides a periodic kick that synchronizes
the phases.

### P2: aL_arg(κ_C) at A=0.40 — crosses 0° at κ_C ≈ 0.73 (S115-P4 partial)

```
  κ_C    aL_arg    rotation rate
 0.05    -109.5    —
 0.15    -107.0    +25°/unit
 0.25    -101.0    +60°/unit
 0.30     -97.7    +66°/unit
 0.40     -86.6    +111°/unit
 0.50     -58.2    +284°/unit  ← rate acceleration
 0.60     -36.2    +220°/unit
 0.70     -8.4     +278°/unit
```

S115-P4 predicted crossing 0° at κ_C ≈ 0.55. Actual crossing is at
**κ_C ≈ 0.73** (linear extrapolation from κ_C ∈ {0.50, 0.60, 0.70}
slope = +249°/unit). At κ_C=0.70 the att_lock class μ-vector points
at +2.8° (A=0.30) to −8.4° (A=0.40) — extremely close to the signal
"positive" direction.

S115-P4 was qualitatively correct (the rotation continues) but missed
the κ_C of crossing by a factor of 1.33×. The rotation rate accelerates
through κ_C∈[0.40, 0.50] (factor 2.5× speedup) — consistent with a
nonlinear "lock-strength → arg shift" relationship.

### P3: ρ_sig recovery with A in over-collapsed regime — refined

The S115-P5 prediction "ρ_sig(A) is STEEPER at higher κ_C past
saturation" is **falsified in absolute terms but CONFIRMED in
fractional terms**.

```
  κ_C   slope(ρ_sig)   ρ(A=0.60)/ρ(A=0.30)   relative gain%
 0.40   +0.177         1.79×                 +79%
 0.50   +0.126         1.95×                 +95%
 0.60   +0.102         2.44×                 +144%
 0.70   +0.090         3.55×                 +256%
```

Absolute dρ/dA *decreases* with κ_C — because base ρ_sig collapses. But
the *fractional* amplification grows dramatically. At κ_C=0.70 the
signal multiplies ρ_sig by 3.55× across A∈[0.30, 0.60]; at the ridge
the same range only gives 1.3×.

This is the signal-following oscillator signature: in the over-coupled
regime the system is detection-dead in the absence of strong signal,
but extremely responsive to signal amplitude. At κ_C=0.70 the system
acts as a near-linear coherent oscillator following the signal phase.

### P4: lock@sw approaches but does not reach 1.0

```
  κ_C   lock@sw(A=0.40)
 0.40    0.635
 0.50    0.702
 0.60    0.740
 0.70    0.756
```

Lock@sw grows from 0.64 (κ_C=0.40) to 0.76 (κ_C=0.70) — saturating but
not reaching 1.0. The asymptote appears to be near 0.80–0.85; full
phase lock at switch time is not reached in the probed range. The
~0.20 gap is residual noise-driven switching events outside the
R_kura(t) > 0.9 windows; this is the "rep_noise" class that maintains
~20% of switches even at κ_C=0.70.

### P5: Wedge widens past S115's "57° ceiling" — DRAMATIC FINDING

```
  κ_C   wedge°(A=0.40)   wedge°(A=0.30)
 0.40    56.8             58.4
 0.50    80.3             90.2
 0.60   100.6            119.6
 0.70   124.6            153.0
```

S115 reported wedge at κ_C=0.40 was 56.8° ≈ 58.4° ≈ 57.0° across
A∈{0.30, 0.40, 0.50} and concluded "saturated at geometric ceiling".
This was a 3-point illusion: at higher κ_C the wedge continues to
widen to **125° at κ_C=0.70 A=0.40** — and **153° at κ_C=0.70 A=0.30**.
The latter is within 27° of perfect anti-phase.

The wedge is also strongly A-modulated past ridge, but in the OPPOSITE
direction from the dip-A regime: high A *narrows* the wedge. At
κ_C=0.70: 153° (A=0.30) → 82° (A=0.60). This is consistent with the
signal-rescue mechanism: as A grows, the system regains phase
coherence and the class arg-difference shrinks toward the original
ridge-regime ~50° wedge.

**S115 conclusion needs revision**: the wedge has NO geometric ceiling
at 57°. What S115 measured at κ_C=0.40 was a transient plateau in the
A∈[0.30, 0.50] window where the att_lock arg passed through −86° on
its way back toward −96° (signal-min asymptote) at higher A. The
S115 "saturated regime" is actually a special A-region where the
wedge happens to be flat in A.

Looking at the κ_C=0.40 row in the unified table:
- A=0.30: wedge=58° aL_arg=−96°
- A=0.40: wedge=57° aL_arg=−87°
- A=0.50: wedge=57° aL_arg=−84°
- A=0.60: wedge=34° aL_arg=−96° ← reverts to −96° at high A; wedge collapses

The att_lock arg has a non-monotonic dependence on A at κ_C=0.40:
−96° → −87° → −84° → −96°. The plateau S115 read as "saturation" is
actually the peak of an inverted U; at A=0.60 it has returned to the
geometric signal-min asymptote.

### P6: mod_amp_at_fs_lock(A) slope grows with κ_C

```
  κ_C   slope(mod_amp vs A)   mod_amp(A=0.30)   mod_amp(A=0.60)
 0.05   +0.239                0.247              —
 0.15   +0.399                0.203              —
 0.25   +0.529                0.163              —
 0.30   +0.569                0.149              —
 0.40   +0.536                0.124              0.279
 0.50   +0.577                0.108              0.275
 0.60   +0.591                0.101              0.272
 0.70   +0.603                0.097              0.271
```

mod_amp(A=0.30) decreases with κ_C (0.25 → 0.10): in the over-coupled
regime, intrinsic phase-coupling can no longer drive R_kura modulation
at f_s without signal help. mod_amp(A=0.60) is nearly κ_C-INVARIANT at
~0.27: at high A the signal dominates the R_kura(t) modulation
regardless of κ_C. This converges with the signal-following oscillator
picture.

## Analysis

### Three-regime taxonomy of the (κ_p=0.30, ω_std=0.07) landscape

Combining S107–S116, the κ_C axis has three operationally distinct
regimes:

```
κ_C       regime               det. mechanism           wedge° (A=0.40)   ρ_sig(A=0.40)
≤ 0.10   un-formed             diffuse noise switches    < 5°              ~0.025 (floor)
0.20-0.35  ridge / wedge-A    att_lock vs rep_noise     40-50°             0.13-0.16 (peak)
≥ 0.50   signal-following     external signal drives    80-125°            0.03-0.05 (collapsed)
```

The ridge regime (S107-S114) is the "detection sweet spot" — switching
is concentrated by κ_C, classes differentiate, wedge mechanism
operates. The signal-following regime (S116) is a new operating point:
intrinsic switching is suppressed (N_sw drops 5000 → 2700 from
κ_C=0.40 to 0.70 at A=0.40), the system has weak baseline dynamics,
but external signal can drive coherent switching at f_s with the
class structure approaching anti-phase.

The wedge angle is a continuous geometric marker of the transition.
The "saturation at 57°" S115 reported was a near-coincidence of the
A=0.40 wedge measurement being insensitive to κ_C in [0.30, 0.40].
The actual wedge behavior is monotone-growing in κ_C through 125°.

### Why aL_arg crosses 0° at κ_C ≈ 0.73 (not 0.55)

The aL_arg rotation rate accelerates with κ_C:
- 0.05–0.30: ~25-66°/unit (slow drift)
- 0.30–0.40: ~110°/unit
- 0.50–0.70: ~250°/unit

The rotation is not linear in κ_C. The S115-P4 prediction extrapolated
linearly from κ_C ∈ [0.05, 0.40] where the average rate was ~70°/unit;
that extrapolation predicted κ_C ≈ 0.55 for 0° crossing. The actual
crossing at κ_C ≈ 0.73 is consistent with a nonlinear acceleration
(perhaps quadratic in κ_C-κ_C_ridge).

Physical interpretation: at the ridge κ_C ≈ 0.27-0.30 the att_lock
class points roughly at the signal-min asymptote (~−96°). As κ_C
grows past saturation, the signal becomes the dominant driver of
switching events: att_lock events shift away from the signal-min
asymptote toward the signal-max asymptote (0°). The rotation rate
accelerates because each unit of κ_C contributes more to lowering
the bistable barrier, and the signal's relative influence over each
crossing event grows nonlinearly.

### Class-structure anti-phase signature at κ_C=0.70

At κ_C=0.70 A=0.30, the wedge between att_lock (+2.8°) and rep_noise
(−150°) is 153° — within 27° of perfect anti-phase. This is a
qualitatively new regime: the two dominant classes are nearly
opposite phasors. Their cross-term 2|μ_aL||μ_rN|cos(Δφ) is strongly
NEGATIVE (cos(153°) = −0.89), so the two classes are interfering
destructively.

This explains why ρ_sig collapses past the ridge: the per-class
phasors do not vanish (|μ_aL|=28, |μ_rN|=25), but their near-anti-
phase orientation cancels their coherent sum. The total |μ_st|=1.50
at this cell is much smaller than the per-class magnitudes — the
destructive cross-term dominates.

This is the "Big Wedge" version of the S113 dip mechanism. At the
ridge the wedge is 49° (cos = 0.66, mild destructive); past ridge it
grows to 125-153° (cos = −0.57 to −0.89, strongly destructive). The
SAME mechanism — phase-incoherent class structure — produces both
the small dip at the ridge AND the collapse past ridge.

The signal-rescue acts on the wedge: at high A, the wedge narrows
toward 50° (κ_C=0.70 A=0.60 wedge = 82°). This brings the classes
closer to coherent and recovers detection.

### Updated mechanism story

The unified picture across S107–S116:

1. **κ_p sets the gain on per-event signal coupling** (S105's linear
   slope, refined by S107).
2. **κ_C sets the switch-rate concentrator AND drives class
   differentiation** (S106 ridge, S107 universal κ_C* ≈ 0.27,
   S110 mechanism revision).
3. **Class structure** (att_lock / rep_noise wedge angle) is monotone
   in κ_C: 0° at κ_C=0.05 (no classes) → 50° at ridge → 125° at
   over-coupled → 180° anti-phase at unreachable limit (S116).
4. **Signal coupling** modulates the wedge: at the ridge, A=0.40
   widens it by ~5° producing the S113 dip; past ridge, A *narrows*
   it from 153° back toward 50°, producing signal-rescue.
5. **Detection** ρ_sig = |⟨z_st⟩|² / N_sw. Two competing effects:
   N_sw drops with κ_C (less data) and the cross-term cos(wedge) can
   be destructive. At ridge κ_C N_sw is moderate AND wedge is mildly
   constructive → peak ρ_sig. At over-coupled κ_C N_sw drops AND
   cross-term is destructive → ρ_sig collapses, but signal can
   partially restore both.

The system has a *signal-driven phase regime change*: at sufficient A,
the over-coupled regime transitions back to a ridge-like configuration.
This is a previously-uncharacterized signature of the model.

## Conclusion

S115-P4 and S115-P5 are both confirmed *in direction* but refined in
magnitude. The "saturated wedge at 57°" S115 reported at κ_C=0.40 was
not a geometric ceiling but a flat plateau in a 3-point A window; the
wedge continues to widen to 125° at κ_C=0.70 A=0.40 and to 153° at
κ_C=0.70 A=0.30 (near anti-phase).

A new regime — the **signal-following oscillator** — was characterized
at κ_C ≥ 0.50. In this regime intrinsic dynamics is over-coupled and
weak; the external signal becomes the primary driver of R_kura(t)
modulation and switch concentration. ρ_sig collapses in absolute terms
but its fractional response to A grows to 3.55× — the system becomes
a sensitive but low-baseline signal follower.

This adds a third axis to the regime taxonomy on κ_C. The wedge angle
turns out to be a continuous order parameter for the (un-formed →
ridge → signal-following) transition, with the κ_C ridge sitting at
the special value where the wedge happens to be mild-constructive
(~50°) and ρ_sig is maximized.

## Open predictions for future sessions

- **S116-P1** — Within the signal-following regime (κ_C=0.70), is
  there an A* where the wedge collapses to the ridge value (~50°)
  and ρ_sig recovers to the ridge value (~0.13)? Probe A ∈ {0.80,
  1.0, 1.5}: predict ρ_sig recovers to 0.10-0.15 at A ≈ 1.0.
- **S116-P2** — At κ_C ≥ 0.80, does the wedge cross 180° and start
  to *shrink* from the other side (would imply the classes overshoot
  anti-phase)? Direct test of geometric vs continuous interpretation
  of the wedge angle.
- **S116-P3** — Is the signal-rescue dR_kura/dA bounded? Sweep κ_C
  to 1.0 and beyond at A=0.40. Predict slope saturates at ≈ +0.6-0.7
  (signal contributes a fixed maximum) OR keeps growing if dynamics
  is fully signal-driven.
- **S116-P4** — The aL_arg(κ_C) rotation rate acceleration: does the
  curve have a closed form? Predict aL_arg(κ_C) ≈ −96 + B·(κ_C - 0.27)²
  for some B around 5000–7000°/unit². Test with fine κ_C ∈ {0.45, 0.55,
  0.65, 0.75} at A=0.40.
- **S116-P5** — At ω_std variation (within cliff): does the over-
  coupled regime shift earlier (smaller κ_C*) or later with ω_std?
  Tests whether the "signal-following" regime is set by κ_C alone
  or by the ratio κ_C / (some baseline switching rate).
- **S116-P6** — Class anti-phase configuration: is the cross-term
  2|μ_aL||μ_rN|cos(wedge) really driving ρ_sig collapse? Direct test
  by setting cos(wedge)=−1 hypothetically: would ρ_sig reach 0 if
  |μ_aL| = |μ_rN|? Compute the "minimum-cross-term" cell from data.
- **S116-P7** — The four-class decomposition: what do att_noise and
  rep_lock look like in the signal-following regime? S116 data shows
  their fractions drop to ~0.02 each at κ_C=0.70. Are they becoming
  a separate cross-term that contributes to the collapse, or are
  they becoming negligible?
- **S116-P8** — Detection floor: does ρ_sig at κ_C=0.70 A=0.30 cross
  the per-seed detection threshold? z_det = √(N_chunks · R_coh / (1
  − R_coh)) at ρ_sig=0.010, R_coh≈0.07, 25 chunks → z ≈ 1.4. Below
  5σ detection. The signal-following regime is in detection-dead
  territory at low A; reasonable that's the operational limit.

## Cross-arc context

The S116 finding reinforces a recurring theme in the SR saga: what
looks like a "saturation" or "geometric ceiling" in a few-point sweep
often turns out to be a transient plateau or a special A-region. S113
found a dip the original "weights-only" model couldn't predict. S114
found the dip is regime-bound, not a universal scaling. S115 found
the dip mechanism requires κ_C in a window. S116 finds the κ_C window
upper boundary is also not a ceiling but a transition into a distinct
regime with its own internal structure.

The continuous geometric order parameter (wedge angle) is more
informative than any of the derived detection metrics (ρ_sig, mod_amp).
Future analyses should foreground the wedge angle directly as the
primary observable, with ρ_sig as a downstream consequence of the
wedge geometry × signal amplitude.

The "signal-following oscillator" regime is interesting in its own
right: it's a state where the system can detect a signal in absolute
terms (R_coh measurable) but the standard ρ_sig metric undercounts
its sensitivity because the per-class phasors interfere destructively.
A future direction is to define an alternative detector that operates
on per-class phasors directly — sum of |μ_class|² instead of |Σμ_class|² —
which would reveal the per-class detection power in the over-coupled
regime.

---

**Files**:
- `thor_session_116_past_ridge.py` — experiment
- `thor_session_116_analyze.py` — analyzer
- `thor_session_116_past_ridge_results.json` — raw results
- `thor_session_116_analysis.json` — derived
- `thor_session_116.log` — run log
