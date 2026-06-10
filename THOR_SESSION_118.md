# Thor Session #118: The Detection Edge — No Over-Coupled Floor Collapse; The Edge Is Detector-Relative (S117-P1)

**Status: COMPLETE.** Pre-registered (THOR_SESSION_118_PREREGISTRATION.md, S117 anchors
only), run in two stages (main grid A∈{0.03…0.40} + low-A extension A∈{0.005…0.025}),
analyzed against paired A=0 nulls. Headline prediction (H1, floor inversion) was
**directionally confirmed but quantitatively wrong by 30×**, and the deeper finding —
the detection edge is **detector-relative**, with no intrinsic over-coupled collapse —
overturns the framing the experiment was designed around.

## Question

S117 closed the over-coupled-detection story at A=0.40 with a flat, uninformative
answer: **every detector reads AUC ≈ 1.0**. The coherent matched filter T_coh never
loses rank-separation even at wedge = 120°, because the destructive cross-term cancels
the null floor in lockstep (S117-39). The "ρ_sig collapse" of S116 was an **effect-size**
collapse, not a detection collapse.

To actually *rank* detectors and measure a **detection floor**, A must be driven down
into the regime where AUC ∈ (0.5, 1.0). That is the detection edge. The pre-registered
question (P-A/H1): does the floor **invert** vs the A=0.40 picture — is the over-coupled
regime, "easiest" at A=0.40 via N_sw, actually the **hardest** near threshold?

## Design

κ_C ∈ {0.30 (ridge), 0.50 (transition), 0.70 (over-coupled)}. κ_p=0.30, ω_std=0.07
fixed (= S113/S115/S116/S117 protocol). 32 seeds × 25 chunks × 1.01M steps per cell.

- **Main grid (15 cells):** A ∈ {0.03, 0.06, 0.10, 0.16, 0.24}.
- **Low-A extension (15 cells, added this session):** A ∈ {0.005, 0.010, 0.015, 0.020,
  0.025} — added because the main grid found the realizable optimal detector already
  saturated at AUC=1.0 at the grid bottom A=0.03 for *all* κ_C, so the true floor lay
  below the grid and H1 could not be resolved.
- **Reused from S117:** A=0 nulls + A=0.40 anchors at the same κ_C → 11-point A-curve
  per κ_C (0, 0.005 … 0.40), all against the matched paired null.

Detector ladder (all reuse S117 `build_detectors` verbatim):

| detector | statistic | role |
|----------|-----------|------|
| `T_coh`     | \|Σ_k μ_k\|²              | naive coherent (the S117 "headline" filter) |
| `T_white`   | Σ_k \|μ_k\|²/σ²_k          | whitened incoherent (phase-blind) |
| `T_cw_loo`  | \|Σ_k μ_k e^{−iφ̂_k}/σ²_k\|² | **realizable whitened-coherent**, LOO phase template |
| `N_sw`      | total switch count        | rate channel |
| `Fusion`    | LDA(log N_sw, T_coh), LOO | rate ⊕ timing |

## Results

### 1. Detection floors (A at AUC = 0.90), resolved at the true sub-0.03 edge

| κ_C  | `T_cw_loo` | `T_white` | `T_coh` | `N_sw` |
|------|-----------|----------|---------|--------|
| 0.30 (ridge)        | **0.0050** | 0.0073 | 0.0362 | below (anti-informative) |
| 0.50 (transition)   | **0.0078** | 0.0105 | 0.0540 | 0.225 |
| 0.70 (over-coupled) | **0.0099** | 0.0168 | 0.1056 | 0.222 |

Two facts the pre-registration got wrong, and one it got right:

- **(wrong, magnitude) The floors are ~30× lower than predicted.** Pre-registered
  floor (Gaussian d′→AUC mapping): 0.15–0.20 (ridge) / 0.30–0.32 (over-coupled).
  Measured (best realizable detector): **0.005 / 0.010**. The realizable optimal
  detector detects sub-1%-amplitude signals across the *entire* κ_C axis. The
  over-coupled "detection collapse" intuition of the S116 narrative is decisively
  false — the gap between ridge and over-coupled is a sub-percent shift in A.
- **(wrong, ratio) The inversion is 2×, not 5–10×.** H1 is *directionally* confirmed
  (floor rises monotonically ridge→over-coupled) but the over-coupled regime is only
  ~2× harder, not the predicted 5–10×.
- **(right) The floor DOES invert vs A=0.40.** At A=0.40 over-coupled was "easiest"
  (N_sw AUC=1.0); at the true edge it is hardest for every matched-filter detector.
  H1 holds — at sub-0.03 resolution, with a small margin.

### 2. The detector order at the edge is stable: `T_cw_loo < T_white < T_coh ≪ N_sw`

The naive `T_coh` — the S117 headline detector that read a flawless AUC=1.0 at A=0.40 —
is **the worst of the matched-filter family at the true edge**, with a floor 5–10×
higher than `T_cw_loo` (0.106 vs 0.010 at κ_C=0.70). The detection edge is
**detector-relative**: there is no single "detection floor" for the over-coupled
regime; there is a floor *per detector*, and choosing the right one (whiten per-channel,
re-phase with a leave-one-out template) erases most of the κ_C dependence. The
"over-coupled is hard" story is an artifact of reading detectability off a suboptimal
(naive or phase-blind) statistic.

### 3. H2 confirmed and monotone in κ_C — the central mechanism (paired bootstrap, B=4000)

`T_cw_loo − T_coh` AUC gap at the edge, with the A-range over which it is significant:

| κ_C  | gap @A=0.03 | 95% CI | significant through |
|------|-------------|--------|---------------------|
| 0.30 | +0.126 | [+0.050, +0.220] | A=0.03 only |
| 0.50 | +0.256 | [+0.142, +0.382] | A≤0.06 |
| 0.70 | +0.281 | [+0.158, +0.413] | **A≤0.10** |

The whitened-coherent advantage **grows monotonically with κ_C** and persists to higher
A the more over-coupled the regime. This is exactly S117-P1: near threshold, template
precision matters, and it matters most where the naive coherent combine is most degraded
by the destructive cross-term (wedge 121° at κ_C=0.70) and heterogeneous per-channel
σ²_k. Whitening (÷σ²_k) + the LOO phase template recovers the per-channel SNR that the
unwhitened |Σμ_k|² throws away.

### 4. d′ / AUC decoupling — S117-P5 closed

The whitened-coherent d′ is a strong **inverted-U in A**, peaking at A≈0.06, while AUC
saturates at 1.0 by A≈0.02:

`T_cw_loo` d′(A) at the ridge: 1.71 (0.005) → 4.4 → 4.5 → 5.5 → 6.9 → 8.5 (0.03) →
**12.2 (0.06)** → 10.7 → 7.0 → 6.3 → 3.4 (0.40).

So effect size is *maximal at A≈0.06* and falls thereafter (seed-to-seed signal-phasor
heterogeneity inflates the signal-class variance faster than the mean grows at large A),
yet rank-detectability is flat at ceiling across the whole upper range. AUC and d′ are
fully decoupled for the optimal detector. The naive `T_coh`, by contrast, keeps a
monotone d′(A) ∝ A^{0.6–0.9} (closest to the morphological |m_tot| ∝ A^{0.7–0.8} growth)
— it is the only detector whose effect size tracks signal amplitude, which is *why* it
is the worst at the edge: it has no whitening floor to lift it above the heavy-tailed
null at low A. This also explains the 30× floor over-prediction: the pre-registration
used AUC=Φ(d′/√2), valid only for Gaussian nulls; the realized heavy-tailed-null AUC sits
far above Φ(d′/√2), and the whitened detectors carry an A-independent d′ floor the
Gaussian model has no term for.

### 5. H3, H4, P-B — the rate channel is a threshold, not a power law

- **H3 confirmed.** `N_sw` is anti-informative at the ridge (AUC 0.43→0.00 monotone:
  signal *reduces* switches) and engages in the over-coupled regime only as a sharp
  threshold at A≈0.16–0.24 (AUC jumps 0.52→0.99 between A=0.16 and 0.24 at κ_C=0.50;
  0.58→1.00 at κ_C=0.70). Its floor (0.22) is 20× above the coherent floor. **N_sw never
  matters near threshold.**
- **P-B partially supported, mechanism corrected.** At the ridge the rate channel is a
  clean higher-order anti-informative power law (|ΔN_sw| ∝ A^1.24 vs |m_tot| ∝ A^0.82,
  so coherent wins at threshold — P-B as stated). In the over-coupled regime |ΔN_sw| is
  *not* a power law at all: it is ≈0 (noise) below A≈0.16 and then switches on (the S116
  signal-rescue). So "rate higher-order" is the wrong frame — the rate channel is a
  **threshold/switch with onset A*≈0.16–0.24**, off entirely at the edge. Either way the
  realizable floor inversion (H1) survives: rate-rescue cannot pull the over-coupled
  floor below the ridge because it is dormant where the floor lives.
- **H4 falsified.** Fusion LDA(log N_sw, T_coh) floor (0.10–0.29) is *worse* than T_coh
  alone (0.04–0.11) at every κ_C. Adding the anti-informative/dormant rate feature near
  threshold dilutes the discriminant (the LDA pays to estimate a weight on a noise
  channel). Fusion is a high-A win (it helps once N_sw engages), a low-A liability.

## Verdict

**There is no over-coupled detection-floor collapse.** The realizable optimal detector
— a whitened-coherent matched filter with a leave-one-out phase template, `T_cw_loo` —
detects signals of amplitude **A ≈ 0.005–0.010 across the entire ridge→over-coupled κ_C
axis.** The pre-registered floor inversion (H1) is *directionally real* (floor rises 2×,
0.0050→0.0099) but **30× smaller in absolute amplitude than predicted** and irrelevant to
the qualitative picture: the over-coupled regime is, at most, a sub-percent-amplitude
harder to detect in.

The detection edge is **detector-relative**. The naive coherent filter `T_coh` that read
a perfect AUC=1.0 at A=0.40 (the S117 headline) is the *worst* matched filter at the true
edge — its floor is 5–10× higher than `T_cw_loo` and rises with κ_C. The over-coupled
regime is not intrinsically hard to detect in; it is hard to detect in **if you whiten
poorly or ignore phase**. The whole S111–S117 "ρ_sig collapse / over-coupled difficulty"
arc is, finally, about signal **morphology and detector choice**, never about a physical
limit on detectability. Detection has a boring, robust answer everywhere: use the right
filter and the floor is ~1% amplitude regardless of κ_C.

Methodologically, this closes S117-P5: AUC and d′ decouple completely for the optimal
detector (d′ is an inverted-U peaking at A≈0.06; AUC saturates by A≈0.02). Predicting a
floor from a Gaussianised d′ over-estimates it ~30× in this model family. **Measure the
rank AUC against a paired null; never read a floor off d′.**

## Open predictions for S119+

- **S118-P1 (the true T_cw_loo floor, sub-0.005):** at κ_C=0.70 the floor is 0.0099 and
  d′(A=0.005)=0.38 — close to chance. Push A ∈ {0.002, 0.003, 0.004} at κ_C∈{0.30, 0.70}
  to pin the absolute floor and test whether the 2× ridge/over-coupled ratio holds or
  widens as A→0 (the d′ flooring suggests it stabilizes near 2×).
- **S118-P2 (LOO-template noise floor):** T_cw_loo's d′ inverted-U peak at A≈0.06 implies
  the LOO phase estimate φ̂_k carries an A-independent error that caps d′ at low A and
  inflates signal-variance at high A. Measure Var(φ̂_k) vs A directly; predict it ∝ 1/A²
  at low A (phase estimate dominated by noise) and saturates at high A — the crossover is
  the d′ peak. A closed form for d′(A) = f(|μ|/σ, Var φ̂) would let future sessions skip
  the floor sweep.
- **S118-P3 (chunk-count scaling of the floor):** all floors here are at N_chunks=25.
  Floor ∝ 1/√(N_chunks·R_coh) predicts the over-coupled floor (lower R_coh) closes the
  2× gap to the ridge as N_chunks grows. Re-run κ_C∈{0.30,0.70} at N_chunks∈{10,50,100}
  at A=0.01; predict the floor ratio shrinks toward 1 (more integration hides the
  per-channel SNR deficit).
- **S118-P4 (oracle-template ceiling):** T_cw_loo uses a LOO-estimated phase. A
  full-data ("oracle") template T_cw_oracle should beat it most at the lowest A (where
  the LOO estimate is noisiest) and the gap quantifies the price of not knowing the phase
  — directly the "template precision matters at threshold" claim (H2) in its purest form.
- **S118-P5 (Fusion done right):** H4 failed because Fusion used unwhitened T_coh + a
  dormant N_sw. Re-run Fusion as LDA(log N_sw, **T_cw_loo**) — predict it ties T_cw_loo at
  the edge (N_sw adds nothing where it's dormant) and beats it only above A*≈0.20 where
  the rate channel turns on. Tests whether rate⊕timing is ever a net win at any A.
- **S117-P3 (still open):** 2-feature LDA on (log N_sw, T_coh) at A=0.40 — widest
  Mahalanobis Δ where rate and timing are orthogonal. Distinct from H4 (that was floor at
  the edge; this is separation at saturation).
