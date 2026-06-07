# Thor Session #117: The ρ_sig Collapse Is An Effect-Size Illusion — Detection Never Failed (S116-P8 Resolved, Premise Overturned)

**Status:** COMPLETE
**Date:** 2026-06-07 (design 2026-06-05; data run 2026-06-07, 137.8 min)
**Answers:** S116-P8 — and overturns its premise
**Protocol:** κ_p=0.30, ω_std=0.07 fixed (S113/S115/S116 lineage), 32 seeds × 25 chunks, 1.01M steps/seed

---

## Background

S116 mapped the **signal-following oscillator regime** past the κ_C ridge. The
key structural fact: as κ_C grows beyond the ridge (≈0.27), the four switch-event
classes (att_lock / att_noise / rep_lock / rep_noise, partitioned by
`gate × R_kura>0.9` at switch time) rotate apart in the complex matched-filter
plane. The dominant pair (att_lock, rep_noise) opens a **wedge** that widens
monotonically: 57° (κ_C=0.40) → 80° → 100° → 125° at A=0.40, reaching 153°
(near anti-phase) at κ_C=0.70 A=0.30.

The standard switch-timing detector combines the classes **coherently**:

  ρ_sig = |Σ_k μ_k|² / N_sw  =  T_coh / N_sw

When the wedge is wide, the cross-term `2|μ_aL||μ_rN|cos(wedge)` goes strongly
negative and T_coh collapses (ρ_sig: 0.13 ridge → 0.01 at κ_C=0.70 A=0.30).
But the **per-class phasors do not vanish** — verified on S116 data:

| cell        | wedge | T_coh (mean) | T_incoh = Σ\|μ_k\|² | ratio | \|μ_aL\| | \|μ_rN\| |
|-------------|-------|--------------|---------------------|-------|----------|----------|
| κ_C=0.50 A=0.40 | —   | 4578         | 3707                | 0.81  | 35.8     | 45.8     |
| κ_C=0.60 A=0.40 | —   | 2163         | 2386                | 1.10  | 31.6     | 33.9     |
| κ_C=0.70 A=0.30 | 153°| 612          | 1084                | 1.77  | 20.9     | 21.0     |
| κ_C=0.70 A=0.40 | 125°| 1105         | 1612                | 1.46  | 28.1     | 25.3     |

The cross-term flips from **net constructive** (ratio T_incoh/T_coh < 1, κ_C=0.50)
to **net destructive** (ratio > 1) between κ_C=0.50 and 0.60. The energy is still
there; the coherent combine is throwing it away to destructive interference.

**S116-P8 asked:** would a detector that combines the per-class phasors
**incoherently** — Σ|μ_k|² instead of |Σμ_k|² — recover detection power where
the coherent combine collapses?

## The detection-theory framing

The class partition is **signal-blind** (uses only the internal C-gate and the
Kuramoto order parameter), so a real detector can compute it. Given the 4 per-class
complex phasors, there is a ladder of ways to combine them:

| detector       | formula                              | assumption |
|----------------|--------------------------------------|------------|
| T_coh          | \|Σ_k μ_k\|²                          | per-class phases aligned (naive) |
| T_incoh        | Σ_k \|μ_k\|²                          | phases unknown, equal noise (naive energy) |
| T_white        | Σ_k \|μ_k\|²/σ²_k                     | phases unknown, **per-class null-whitened** (energy GLRT) |
| T_wedge        | \|Σ_k μ_k e^{−iφ̂_k}\|²               | per-class phases **known** (de-rotate then sum) |
| T_cw           | \|Σ_k μ_k e^{−iφ̂_k}/σ²_k\|²          | known phase + whitening (**matched-filter optimum**) |

Classical result: for a signal with **unknown** per-channel phase, the GLRT is
the whitened energy sum (T_white); for **known** per-channel phase it is the
whitened coherent matched filter (T_cw). T_coh (the current detector) is the
known-phase combiner that **assumes all phases are zero** — correct at the ridge
(small wedge, cos>0), wrong in the over-coupled regime (large wedge, cos<0).

**The oracle trap.** φ̂_k must be *estimated*. If we estimate it on the same
signal seeds we then score, T_wedge/T_cw are inflated (in-sample optimism). Per
the project's calibration discipline (S96 null-null, S103 per-seed vs pooled),
we report **leave-one-out** φ̂ for the signal seeds (null seeds use the full
trained template — they never participate in training, so no leakage). The
whitening σ²_k = E_null[|μ_k|²] is measured on the **independent paired A=0 cell**
(the random-phase prediction σ²_k = n_k is badly violated — switch events are
phase-anti-correlated).

## Design

Paired (signal A=0.40, null A=0.00) cells across the ridge → over-coupled
transition:

  κ_C ∈ {0.30, 0.40, 0.50, 0.60, 0.70} × A ∈ {0.00, 0.40}
  κ_p = 0.30, ω_std = 0.07 fixed; 32 seeds × 25 chunks × 1.01M steps (10 cells)
  Independent seed namespaces for null vs signal (null offset +900,000).

Detection power is **AUC** between the paired null and signal cells (rank-based,
no Gaussian assumption — the T statistics are heavy-tailed chi-square-like),
with 2000-sample bootstrap 95% CIs. d′ reported as a secondary (Gaussian) summary.

A=0.40 chosen (not the A≈0.20 detection sweet-spot) because the wedge mechanism
is A-modulated and 0.40 sits in the destructive regime at high κ_C (S116).

## Pre-registered predictions

- **P1** (incoherent recovers over-coupled detection): AUC(T_incoh or T_white) >
  AUC(T_coh) for κ_C in the destructive regime. **Sharpened from S116 data: the
  cross-term flips constructive→destructive between κ_C=0.50 and 0.60, so the
  crossover should sit near κ_C ≈ 0.60**, not 0.50.
- **P2** (coherent wins at ridge): at κ_C=0.30 (wedge ≈ 49°, cos>0) the classes
  are mildly constructive, so AUC(T_coh) ≥ AUC(T_white).
- **P3** (whitened-coherent is the realizable envelope): T_cw_loo ≥ all phase-blind
  variants at every κ_C — the matched-filter optimum even after LOO de-biasing.
- **P4** (incoherent null tax): the null mean of T_incoh greatly exceeds that of
  T_coh (4 noise floors vs 1 cancelled sum); whitening (T_white) is what makes
  the energy detector pay a *fair* tax. Tests whether naive T_incoh is actually
  usable or whether whitening is essential.
- **P5** (small-class tax): att_noise + rep_lock are ~0.02 of switches past ridge;
  does dropping them (2-class) match/beat the 4-class energy detector?

## Methods note

- Simulator: `simulate_with_omega` (S112), fixed ω offsets `{−3,−1,1,3}/√5 · ω_std`
  at ω_std=0.07 — well below the Kuramoto cliff (≈0.17 at κ_p=0.30), so per-cell
  CV is collapsed and the comparison is not contaminated by cliff-mediated seed
  dropout (S112/S113 rule).
- Per-class, per-chunk phasors `mu_kc` are stored; per-seed μ_k = Σ_chunk mu_kc.
  Consistency check |Σ_chunk mu_kc − class_decompose μ_k| < 3e-14 every seed.
- Detectors: base battery in `thor_session_117_analyze.py`; the realizable
  ladder (T_white, LOO wedge, T_cw) in `thor_session_117_detector_ladder.py`.

---

## Results

10 cells complete (5 κ_C × 2 A), 32 seeds × 25 chunks each, 137.8 min.
Per-seed consistency check |Σ_chunk μ_kc − class μ_k| < 4e-14 every seed.

### 1. The wedge / cross-term flips sign exactly as S116 predicted

The signal-cell cross-term `xterm = T_coh − T_incoh = 2 Σ_{j<k} Re(μ_j μ_k*)`
crosses zero between κ_C=0.50 and κ_C=0.60:

| κ_C | wedge° | N_sw null | N_sw sig | xterm (sig) | regime |
|-----|--------|-----------|----------|-------------|--------|
| 0.30 | 47.5 |  8454 | 6890 | **+10927** | constructive (ridge) |
| 0.40 | 62.3 |  4456 | 4894 | **+4313**  | constructive |
| 0.50 | 83.6 |  2318 | 3811 | **+642**   | weakly constructive |
| 0.60 | 108.9 | 1357 | 3125 | **−221**   | destructive |
| 0.70 | 120.5 |  921 | 2834 | **−557**   | destructive |

So the S116 wedge mechanism is real and the coherent combine genuinely
loses its constructive cross-term and goes net-destructive past κ_C≈0.55.
**The premise of S116-P8 is confirmed at the level of T_coh magnitude.**

### 2. But detection power (AUC) is NEVER lost — and incoherent makes it WORSE

This is the headline. AUC (null A=0 vs signal A=0.40), 32 vs 32 seeds:

| κ_C | wedge° | **N_sw** | **T_coh** | ρ_sig | T_incoh | **ρ_incoh** | T_white | T_cw_loo | LDA_loo |
|-----|--------|------|-------|-------|---------|---------|---------|----------|---------|
| 0.30 | 47.5 | 0.000 | **1.000** | 1.000 | 0.978 | 0.992 | 0.988 | 0.999 | 1.000 |
| 0.40 | 62.3 | 0.898 | **1.000** | 1.000 | 0.971 | 0.964 | 0.972 | 0.979 | 1.000 |
| 0.50 | 83.6 | 1.000 | **1.000** | 1.000 | 0.980 | 0.877 | 0.964 | 0.995 | 1.000 |
| 0.60 | 108.9 | 1.000 | **1.000** | 0.996 | 0.966 | 0.764 | 0.974 | 0.974 | 1.000 |
| 0.70 | 120.5 | 1.000 | **1.000** | 0.990 | 0.953 | 0.714 | 0.965 | 0.994 | 1.000 |

- **T_coh (the "collapsing" coherent detector) holds AUC = 1.000 at EVERY κ_C.**
  Even at κ_C=0.70 where the cross-term is maximally destructive (wedge 120°),
  the coherent combine perfectly separates null from signal.
- **The incoherent detector — the proposed S116-P8 rescue — DEGRADES monotonically**:
  AUC(ρ_incoh) 0.992 → 0.964 → 0.877 → 0.764 → **0.714**; d′(ρ_incoh) 3.89 → **0.16**.
  Its 95% bootstrap CI at κ_C=0.70 is [0.58, 0.85] — clearly *below* coherent's
  [0.97, 1.00]. **P1 is decisively FALSIFIED.**

### 3. Why: ρ_sig collapse is effect-size, not detectability

S116 read "ρ_sig 0.13 → 0.01" as a detection collapse. It is not. The destructive
cross-term cancels the signal magnitude **and the null floor in lockstep** —
switch events are phase-anti-correlated even at A=0 (S116), so T_coh's null is
already tiny. AUC measures *separation*, which the cross-term preserves on both
sides. **ρ_sig measures effect size (|μ|²/N_sw), not detectability.** The two
diverge in the over-coupled regime: d′(ρ_sig) drops 9.4 → 2.9 while AUC(ρ_sig)
stays ≥ 0.99. The collapse is real for the *metric*, illusory for the *task*.

### 4. Past the ridge, switch-rate alone gives perfect detection

AUC(N_sw): 0.000 (κ_C=0.30) → 0.898 → **1.000** (κ_C ≥ 0.50). At the ridge the
signal *reduces* switches (N_sw 8454→6890, so the null has MORE → AUC=0), but
past the ridge the S116 signal-rescue raises switch count enormously
(921 → 2834 at κ_C=0.70). The over-coupled regime is therefore *trivially*
detectable from the raw switch count — no matched filter needed. The whole
"how do we detect when ρ_sig collapses" question dissolves: the system that
can't be seen in ρ_sig screams in N_sw.

### 5. The realizable ladder and the linear ceiling

- **T_cw_loo** (whitened-coherent, leave-one-out phase template) recovers to
  0.994 at κ_C=0.70 — it beats every phase-blind incoherent variant (T_incoh
  0.953, ρ_incoh 0.714), confirming **P3 in the energy family**. But it does
  not beat raw T_coh (1.000): the naive coherent combine was already AUC-optimal.
- **T_incoh2 (2-class, aL+rN only) ≥ T_incoh (4-class) at every κ_C** (0.985 vs
  0.978 at ridge; 0.953 vs 0.953 at κ_C=0.70). The small classes (att_noise,
  rep_lock) are pure noise tax. **P5 confirmed.**
- **LDA_loo = 1.000 at every κ_C**, marginally above the diagonal cw_loo
  (Δ +0.001…+0.026) but with overlapping CIs — cross-class phasor covariance
  carries only within-noise extra power. The in-sample Mahalanobis Δ stays
  large (9.3 → 5.1) at every κ_C: **abundant linear signal exists throughout;
  the over-coupled regime is not detection-limited at all.**

## Interpretation

S116 closed with rule #38: *"ρ_sig undercounts detection sensitivity… a per-class
detector (Σ|μ_k|² instead of |Σμ_k|²) would recover detection power in the
over-coupled regime — open question for S117+."* S117 tests it directly and the
answer is **no, and the question was malformed**:

1. The per-class **incoherent** detector does not recover detection — it is
   strictly worse than coherent at every κ_C and collapses to d′=0.16 at κ_C=0.70.
2. The coherent detector **never lost detection power** — AUC(T_coh)=1.0 throughout.
   What S116 saw collapse (ρ_sig) is an *effect-size* statistic; its null
   collapses too, so detectability is conserved.
3. The reason incoherent *seems* like it should win — "the energy is still
   there, |μ_aL|≈|μ_rN|≈28" — is exactly why it loses: summing |μ_k|² also sums
   four independent **null** energy floors, and the random-phase null is badly
   violated (phase-anti-correlation), so the incoherent detector pays a 4× noise
   tax that the coherent combine avoids by letting the *null* cross-term cancel too.

**The transferable lesson:** in this model family, `ρ_sig = |Σμ|²/N_sw` is a
*signal-shape* diagnostic, not a detector. For detection claims always compute
AUC/d′ against a paired independent null. A coherent matched filter degrades
gracefully (its d′ falls) but does not lose rank-separation when its template
goes "wrong," because a mis-phased template suppresses null and signal alike.
The over-coupled "signal-following oscillator" regime is, if anything, *easier*
to detect (via N_sw) than the ridge — the opposite of the S116 narrative.

This also retro-clarifies the entire S111–S116 ρ_sig story: the dips, collapses,
and non-monotonicities in ρ_sig are real features of signal *morphology* (where
the switch events land in signal phase, how the classes interfere), but none of
them was ever a statement about whether the signal could be *detected*. The
detection question has a boring, robust answer (yes, everywhere, AUC≈1 at A=0.40,
32×25 chunks); the interesting physics lives entirely in the morphology.

## Predictions for S118+

- **S117-P1** (detection floor vs κ_C): repeat at the true detection edge
  A ≈ 0.05–0.10 (not A=0.40, where everything is trivially detectable). Predict
  the κ_C-ordering of detectors *inverts there*: near threshold, N_sw rescue is
  weak, the cross-term cancellation dominates, and T_cw_loo (whitened-coherent)
  finally beats T_coh because the in-sample template precision matters when the
  margin is thin. Test: A-sweep {0.05, 0.08, 0.12} at κ_C ∈ {0.30, 0.70}.
- **S117-P2** (N_sw vs matched-filter at threshold): at the A where AUC(T_coh)≈0.75,
  is AUC(N_sw) above or below it? Predict matched-filter wins near threshold
  (signal-rescue of switch *rate* is a higher-order effect than switch *timing*),
  reversing the κ_C≥0.50 picture where N_sw alone is perfect.
- **S117-P3** (combine N_sw ⊕ T_coh): a 2-feature LDA on (log N_sw, T_coh) should
  hit AUC=1.0 with the widest margin (largest Mahalanobis Δ) of any detector at
  every κ_C — the rate channel and the timing channel are near-orthogonal
  (N_sw AUC=0 at ridge but 1.0 past it; T_coh AUC=1.0 throughout). Quantify the
  Δ gain over T_coh alone; predict +30–50% at κ_C=0.50 where both channels are live.
- **S117-P4** (does the LDA tiny edge survive more seeds?): LDA_loo beat cw_loo by
  +0.026 at κ_C=0.60 but within CI. Re-run κ_C=0.60 with 96 seeds; predict the
  edge shrinks toward 0 (cross-class covariance is not detection-relevant), i.e.
  the diagonal matched filter is the linear ceiling.
- **S117-P5** (effect-size vs detectability formalized): derive d′(ρ_sig) =
  f(wedge, N_sw) analytically from the per-class phasor model and show AUC→Φ(d′/√2)
  only holds when the null is Gaussian; the heavy-tailed χ²-like T statistics are
  why AUC stays ≈1 while d′ falls. A clean writeup would let any future session
  predict detectability from morphology without re-simulating.
