# Thor Session #119: The d′ Inverted-U Is a Reproducibility Limit Set (Mostly) by ω-Detuning

**Status: COMPLETE.** Three parts: (1) closed-form decomposition of the inverted-U on
existing data, (2) a 2-point ω_std causal series (10 NEW cells, 32 seeds × 25 chunks),
(3) seed anatomy locating the irreproducibility in the dynamics.

## Question

S118 closed the detection-floor story but left its strangest artifact unexplained
(S118 §4, S117-P5): the realizable optimal detector `T_cw_loo` (whitened-coherent,
LOO phase template) has an **inverted-U effect size** — d′ rises to ≈12 at A≈0.06,
then *falls* to ≈3.4 at A=0.40 — while AUC sits at 1.0 across the whole range. S118
attributed the fall to "signal-phasor heterogeneity inflating signal-class variance"
without pinning a mechanism. This session decomposes the inverted-U exactly (Part 1),
tests a causal driver (Part 2: within-array frequency detuning ω_std), and locates the
irreproducibility in the dynamics (Part 3).

## Part 1 — The closed form: d′ ≈ √2 / CV_sig

Decomposing d′(A) = ΔT/√(var_null + ½·β·ΔT²) with β = (var_sig−var_null)/ΔT² on the
existing κ_C∈{0.30, 0.70} ladders (S117+S118 data, no new sim;
`thor_session_119_dprime_decomp.py`):

- **var_sig overtakes 2·var_null already at the lowest measured A** (var_sig/2·var_null
  = 8.2 at A=0.005, peaking at 130× near A=0.06 at the ridge). Above the floor, the null
  variance is irrelevant — d′ is set entirely by the *signal class's own seed-to-seed
  spread*.
- The closed form collapses to **d′ ≈ √(2/β) ≈ √2/CV_sig** wherever AUC has saturated.
  Measured vs predicted at the ridge: 4.44 vs 4.56 (A=0.01), 12.15 vs 12.27 (A=0.06),
  7.01 vs 7.23 (A=0.16). The approximation degrades only at A=0.40 (3.45 vs 4.76) where
  var_sig has fallen back to 1.7× var_null and the null mean/variance re-enter.
- **The d′ inverted-U is exactly the CV_sig U-shape, inverted.** Ridge CV: 0.655
  (A=0.005) → 0.115 (A=0.06, bottom) → 0.297 (A=0.40). Over-coupled (κ_C=0.70) CV
  bottoms at 0.336 (A=0.06) — same shape, same A_peak, 3× shallower d′ because
  per-channel SNR is lower.
- Striking: **d′(A=0.40) is κ_C-independent** — 3.45 (ridge) vs 3.38 (over-coupled).
  The high-A reproducibility limit does not care about coupling regime, suggesting a
  common driver upstream of κ_C.

**Interpretation.** At the detection edge and beyond, the optimal detector's effect
size is not a signal-to-noise ratio at all — it is a **reproducibility ratio**: how
consistently the dynamical system converts the same drive into the same phasor across
noise realizations. d′ falls past A≈0.06 because the *response* becomes less
reproducible, not because the signal gets weaker (it doesn't) or the noise stronger
(it doesn't).

## Part 1b — The CV U-shape is two regimes (existing data, S118-P2 test)

Measuring the dominant-class (`rep_lock`) phasor scatter across seeds on the full
existing A ladder (ω_std=0.07, both κ_C; `thor_session_119_phase_scatter.py`):

| | σ_φ slope, A ≤ 0.06 | σ_φ slope, A ≥ 0.06 | σ_φ minimum |
|---|---|---|---|
| κ_C=0.30 | −0.64 | +0.79 | A≈0.06–0.10 |
| κ_C=0.70 | −0.57 | +0.56 | A≈0.06 |

- **The CV_sig U is two distinct power-law regimes** meeting exactly at the d′ peak:
  a falling noise-limited branch (template phase scatter shrinks as drive grows) and a
  rising dynamics-limited branch (response phasor wanders more as drive grows).
- **S118-P2 partially confirmed**: the low-A branch exists and the crossover sits at
  the d′ peak as predicted, but the scaling is σ_φ ∝ A^−0.6, much shallower than the
  matched-filter prediction σ_φ ∝ 1/A. The phase estimate is noise-*influenced*, not
  noise-*dominated*, even at A=0.005 — consistent with the whitened floor being
  A-independent (S118 §4).
- **Amplitude and phase scatter rise together** on the high-A branch (cv_amp 0.077→0.296,
  σ_φ 0.067→0.276 at the ridge): the whole phasor, not just its angle, becomes
  irreproducible. The high-A mechanism is not a pure phase-diffusion effect.

## Part 2 — ω-detuning is the dominant driver (NEW: 10 cells)

Causal test: the simulator's ω is a FIXED 4-element vector (identical across seeds,
offsets {−3,−1,1,3}/√5·ω_std), so the high-A irreproducibility is NOT a seed-draw
artifact (unlike S112's random-ω cliff). It can only come from the *within-array
frequency detuning* ω_std interacting with the gate-modulated dynamics. New cells at the
ridge (κ_C=0.30, κ_p=0.30): ω_std ∈ {0.00, 0.13} × A ∈ {0.00, 0.02, 0.06, 0.16, 0.40},
32 seeds × 25 chunks; ω_std=0.07 stitched from S117/S118
(`thor_session_119_omega_heterogeneity.py`, `_analyze.py`).

| ω_std | ω-vector | d′_peak | A_peak | d′@A=0.40 | depth = pk/hi | CV@0.40 | AUC@0.40 |
|---|---|---|---|---|---|---|---|
| 0.00 | [0.1,0.1,0.1,0.1] | 13.36 | **0.16** | 8.44 | **1.58** | 0.158 | 1.000 |
| 0.07 | [0.01,0.07,0.13,0.19] | 12.15 | 0.06 | 3.45 | 3.53 | 0.297 | 0.999 |
| 0.13 | [−0.07,0.04,0.16,0.27] | 8.22 | 0.06 | **2.04** | **4.03** | 0.476 | 0.954 |

- **H2 CONFIRMED cleanly (Spearman +1.00):** inverted-U depth orders monotone in ω_std
  (1.58 < 3.53 < 4.03); d′@A=0.40 falls monotone (8.44 > 3.45 > 2.04); CV@0.40 rises
  monotone (0.158 < 0.297 < 0.476). **The peak left-shifts** from A=0.16 (identical
  oscillators) to A=0.06 (detuned) — detuning makes the response start to decohere at
  lower drive.
- **H1 PARTIAL (the honest result).** ω_std=0 does NOT flatten the inverted-U to
  depth≈1: a residual fall survives (d′ 13.36 → 8.44, depth 1.58), with the peak shifted
  right to A=0.16. So ω-detuning is the **dominant amplifier and left-shifter** of the
  inverted-U, but not its sole cause. A residual dynamics-limited fall persists even for
  identical oscillators — the Part-1b high-A branch is intrinsic to gate-modulated
  bistable switching, and ω-detuning multiplies it.
- **H3 CONFIRMED:** AUC stays ≈1.000 across the edge for ω_std∈{0, 0.07} and only dips to
  0.954 at the most extreme cell (ω_std=0.13, A=0.40). Rank-detectability is a margin
  property, robust to reproducibility; d′ and AUC decouple MORE as ω_std grows but the
  rank floor barely moves. The closed form d′≈√2/CV holds at every ω_std except the
  A=0.40 column (var_null re-entry, Part 1).
- **A separate ω-detuning effect on the rate channel:** ⟨N_sw⟩ and R_kura both rise with
  ω_std at fixed A (R_kura@A=0.40: 0.483 → 0.528 → 0.541), consistent with detuning
  adding noise-driven switching even as it degrades phasor reproducibility. The two
  effects are distinct: detuning helps the count channel, hurts the timing channel.

## Part 3 — Anatomy: the irreproducibility is stochastic class-redistribution

For each cell, per-seed T_cw_loo vs per-seed dynamical covariates (Spearman) and a
per-class whitened-weight / amplitude-CV / phase-scatter decomposition
(`thor_session_119_seed_anatomy.py`):

| ω_std | A | CV_T | dominant class (share) | cv_amp | circ_std | top covariate |
|---|---|---|---|---|---|---|
| 0.00 | 0.16 | 0.105 | rep_lock (0.71) | 0.061 | 0.06 | kura +0.61 |
| 0.00 | 0.40 | 0.158 | rep_lock (0.63) | 0.087 | 0.13 | kura +0.46 |
| 0.07 | 0.16 | 0.196 | rep_lock (0.65) | 0.140 | 0.13 | kura +0.70 |
| 0.07 | 0.40 | 0.297 | rep_lock (0.51) | 0.296 | 0.28 | lock@sw +0.35 |
| 0.13 | 0.16 | 0.156 | att_lock (0.43) | 0.084 | 0.08 | lock@sw +0.23 |
| 0.13 | 0.40 | 0.476 | att_lock (0.40) | 0.252 | 0.10 | lock@sw +0.25 |

- **The high-A CV rise is class-share redistribution.** At A=0.40 the dominant class's
  whitened share collapses with ω_std: 0.63 → 0.51 → 0.40, and at ω_std=0.13 the
  dominant class *flips* from rep_lock to att_lock. The four matched-filter classes
  trade weight seed-to-seed; the combined statistic inherits that scatter.
- **The seed scatter is governed by locking.** Per-seed T correlates positively with
  kura_mean / lock_frac_global / lock_at_switch_frac at every cell — high-response seeds
  are the seeds whose 4-oscillator array happened to lock harder under that noise
  realization. With ω-detuning, the array's locked configuration is more
  noise-sensitive, so the response is less reproducible.
- **At ω_std=0 the dominant class stays dominant and reproducible** (rep_lock share 0.63,
  cv_amp 0.087, circ_std 0.13 at A=0.40) — the residual H1 fall is mild and lives mostly
  in amplitude, not phase. At ω_std=0.07 BOTH amplitude (cv_amp 0.30) and phase
  (circ_std 0.28) of the dominant class blow up. At ω_std=0.13 the scatter has moved into
  class-share and amplitude (cv_amp 0.25) while the surviving dominant class's phase stays
  tight (circ_std 0.10) — the irreproducibility migrates from phase to class-identity as
  detuning grows.

**Mechanism (closed).** At high drive A the gate-modulation pushes the bistable
C-dynamics harder; with frequency-detuned oscillators each noise realization locks the
array into a different configuration, redistributing switch events across the
signal-blind classes. The whitened-coherent matched filter sums those classes, so its
per-seed value tracks the realized locking — a *reproducibility* quantity, not an SNR.
d′ = √2/CV_sig falls because CV_sig rises; CV_sig rises because the response, not the
drive or the noise, becomes irreproducible; the response becomes irreproducible because
ω-detuning makes high-drive locking stochastic. The rank-AUC survives because a noisy
response is still almost always larger than a no-signal null — the margin is robust
even when the effect size is not.

## Net

The S118 d′ inverted-U is fully explained. It is a **reproducibility limit**, not a
detectability limit (AUC stays ≈1). Closed form: **d′_T_cw_loo ≈ √2/CV_sig** above the
floor, where CV_sig is the seed-to-seed coefficient of variation of the detector's own
statistic. The high-A fall is driven primarily by **within-array frequency detuning
ω_std** (depth 1.58 → 4.03 across ω_std 0 → 0.13, monotone), which makes high-drive
phase-locking stochastic and redistributes matched-filter weight across switch classes
seed-to-seed. A residual, milder fall persists even for identical oscillators — an
intrinsic property of hard-driven gate-modulated bistable switching. The single most
useful takeaway for the track: **for the optimal detector past the floor, report CV of
the statistic, not d′** — d′ is a derived reproducibility ratio that conflates the
margin question (already answered by AUC) with a dynamics-reproducibility question that
is really about how cleanly the model locks.

## Predictions

- **S119-P1** (residual H1 fall is gate-modulation depth): the ω_std=0 residual depth
  (1.58) should grow with the gate-modulation strength (the C-threshold proximity /
  signal-to-gate coupling). At a shallower gate (higher C_threshold or weaker signal→C
  path) predict depth→1 at ω_std=0. Direct test: sweep C_threshold ∈ {0.50, 0.55, 0.60}
  at ω_std=0, A∈{0.06, 0.40}.
- **S119-P2** (peak-A vs ω_std closed form): A_peak shifts 0.16 → 0.06 as ω_std 0 → 0.07
  then saturates. Predict A_peak ≈ A_peak^0 · (1 − c·ω_std) with a floor at the
  noise-limited/dynamics-limited crossover. Fill ω_std ∈ {0.03, 0.10} to pin the curve.
- **S119-P3** (CV closed form for design): since d′≈√2/CV and AUC≈Φ-free (rank), the
  *chunk-count* scaling of CV_sig sets achievable d′. Predict CV_sig ∝ 1/√N_chunks on
  the noise-limited branch (A<A_peak) but **N_chunks-INVARIANT** on the dynamics-limited
  branch (A>A_peak) — because the high-A scatter is between-seed configuration, not
  within-seed integration noise. Re-run ridge A∈{0.06, 0.40} at N_chunks∈{10, 50, 100}.
  This is the practical payoff: more integration buys d′ only below the peak.
- **S119-P4** (class-redistribution detector): if the high-A irreproducibility is class
  weight trading seed-to-seed, a detector that is invariant to class identity — e.g.
  T_white = Σ_k|μ_k|²/σ²_k WITHOUT the LOO coherent re-phasing — should have a FLATTER
  d′(A) at high A (no inverted-U collapse) at the cost of a lower peak. Test whether the
  whitened-incoherent statistic trades peak d′ for high-A reproducibility. (Connects to
  S118's detector ladder: T_white < T_cw_loo at threshold, but maybe T_white > T_cw_loo
  in *reproducibility* at high A.)
- **S119-P5** (does ω-detuning help the FUSED detector?): Part 2 found ω_std raises N_sw
  and R_kura even as it hurts T_cw_loo reproducibility. At high A the rate channel turns
  on (S118-P5). Predict Fusion(log N_sw, T_cw_loo) recovers part of the ω-detuning d′
  loss at A=0.40 because the rate channel's reproducibility is *improved* by detuning —
  the two channels' reproducibility limits are anti-correlated in ω_std.
