# Thor Session #113: The A=0.40 Dip Is A Class-Phase Crossover

**Date:** 2026-04-29
**Focus:** S112-P6 — what mechanism produces the ρ_sig dip at A≈0.40 at
the ridge geometry, after ω-cliff effects are eliminated?
**Status:** RESOLVED. The dip is a destructive cross-term between the
two dominant switch classes (att_lock and rep_noise) at the A where
their phase difference is maximal. As A grows, both classes' arg(μ_class)
rotate but at different rates. att_lock saturates its rotation near A≈0.40;
rep_noise keeps rotating monotonically. Their angular separation reaches
a MAXIMUM (49°) at A=0.40, minimizing 2|μ_aL||μ_rN|·cos(Δφ) and producing
the dip.

## TL;DR

1. Fixed ω at ω_std=0.07 (well below cliff, S112 sweet spot) confirms
   the ρ_sig dip at A=0.40: 0.141 (A=0.35) → 0.137 (A=0.40) →
   0.147 (A=0.45). Smaller than S111 random-ω (13% drop) at 3% — the
   ω-cliff inflates the apparent dip in S111 by ~3×.
2. **Switch-class decomposition** (att_lock, att_noise, rep_lock,
   rep_noise) by `(gate · R_kura>0.9)` at switch time identifies four
   sub-populations with DISTINCT, A-dependent phases. Class-sum equals
   first-principles z_total to FP precision (smoke check: 1e-14).
3. **Class fractions evolve monotonically**: att_lock 21%→57%,
   rep_noise 50%→35%, att_noise 23%→6%, rep_lock 6%→2% across
   A=0.10→0.50. By A=0.30+ the dominant pair is (att_lock, rep_noise),
   carrying ~90% of switches.
4. **Per-class arg(μ_class) ROTATES with A** — and contradicts the
   prior "phases are class-fixed, only weights shift" hypothesis:
   - att_lock: −157° → −96° (61° rotation), saturates at A≈0.35
   - rep_noise: +175° → −136° (49° rotation), monotonic
   - att_noise: −5° → −68° (63° rotation), monotonic
   - rep_lock: −9° → −57° (48° rotation), monotonic
5. **(att_lock, rep_noise) phase difference is the dip mechanism**.
   |aL − rN| in degrees: 28, 38, 44, 44, 46, **49** (A=0.40), 43, 40.
   The maximum at A=0.40 minimizes cos(Δφ) → smallest cross-term
   contribution from the dominant pair.
6. **Quantitative cross-term confirmation**: pooled-sum cross-term
   2·Re(Σμ_aL · Σμ_rN*) is **2.34M, 2.34M, 2.08M, 2.35M, 2.39M** at
   A∈{0.30, 0.35, **0.40**, 0.45, 0.50}. The (aL,rN) pair drops 11%
   at A=0.40 and recovers — exactly where ρ_sig dips.
7. The total μ_arg rotates only ~3° from peak (A=0.35) to dip (A=0.40)
   to recovery (A=0.45) because the (aL, rN) magnitudes barely change
   (75↔83 each) while their relative phase wiggles. Phase-spread within
   the dominant pair, not gross angle rotation, is the dip signature.
8. Implication: **the dip is the geometric consequence of class-phase
   rotation rates being unequal in A**. att_lock saturates (signal-locked
   mechanism reaches its phase ceiling) while rep_noise keeps rotating
   (signal-direct mechanism's phase shifts linearly). Their cross over
   different A-rates is generic to any 2-class system where mechanisms
   have different phase-vs-amplitude responses.

## Context

S111 found ρ_sig non-monotonic in A at the ridge (κ_p=0.30, κ_C=0.30,
ratio 0.8): 0.029 → 0.075 → 0.154 → 0.139 → 0.128 → 0.203 across
A ∈ {0.05, 0.10, 0.20, 0.30, 0.40, 0.50}. Peak A=0.20, dip A=0.40.

S112 confirmed ω-cliff (ω_std ≈ 0.17) explains the A=0.50 high-seed
variance, and that the A=0.30→0.40 dip survives ω-filtering (succ-only
ρ_sig 0.146, 0.152, 0.132 at A=0.20, 0.30, 0.40 — 13% drop).

A re-analysis of the S111 per-seed angles found `arg(⟨z_st⟩)` rotates:
−126° (peak A=0.20) → −109° (dip A=0.40) → −115° (recovery A=0.50).
That 17° rotation hinted at two switch sub-populations interfering
destructively at the dip A.

## Hypothesis

Switch events partition into 4 classes by `(gate_attractive,
R_kura > 0.9)` at switch time:

  - **att·lock**: gate attractive AND R locked.  The "signal mechanism"
    pathway from S110 — coupling drives R_kura(t) high during attractive
    epoch, cos(⟨φ⟩) modulates intrinsic C drift, switch happens.
  - **att·noise**: gate attractive but R_kura < 0.9.  Transient or
    noise event during weakly-locked attractive epoch.
  - **rep·lock**: gate repulsive but R_kura > 0.9.  Transient — gate just
    flipped to repulsive, lock not yet broken.
  - **rep·noise**: gate repulsive AND unlocked.  Switches driven by
    intrinsic noise on C while phase coupling is destabilizing R_kura.

Each class contributes a complex μ_class. Identity:
|μ_total|² = Σ_class |μ_class|² + Σ_{a<b} 2·Re(μ_a · μ_b*).

If two classes are dominant (a, b) and have phase difference Δφ_ab(A)
that varies with A, the cross-term 2|μ_a||μ_b|cos(Δφ_ab) will vary
with A — producing local extrema in |μ_total|² that do not require
class-weight shifts alone.

## Design

Patched simulator (S112's `simulate_with_omega`, accepts ω_override).
Fixed ω with std 0.07 (ridge-cell sweet spot from S112; mild
heterogeneity gives +17% over ω_std=0.03 with no cliff exposure).
16 seeds × 25 chunks × 40k steps + 10k warmup per cell.

Fine A grid covering the dip region:
  A ∈ {0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50}.

Decimated kura_dec/gate_dec arrays (every 10 sim-steps) → per-switch
lookup of `kura_dec[step // 10]` and `gate_dec[step // 10]` (~5-step
worst-case lag, well below Kuramoto timescale ~130 steps). Per-class
matched-filter sums computed via Σ direction·(sin + i·cos)(2πf_s·t).
Smoke test (90k-step run): class-sum equals first-principles z_total
to 1e-14 precision and class counts sum to N_sw exactly.

Compute: 8 cells × 16 seeds × 1.01M steps × 25 µs ≈ 54 min on Thor.
Actual: 3254 s = 54.2 min.

## Results

### Top-line: dip survives, smaller than S111

| A | ρ_sig | |μ_st| | μ_arg | <Nsw> | lock@sw | att@sw | <R_k> |
|---|------|------|------|------|------|------|------|
| 0.10 | 0.0393 | 3.50 | −120.0° | 7891 | 0.27 | 0.44 | 0.32 |
| 0.20 | 0.0902 | 5.13 | −114.2° | 7371 | 0.37 | 0.47 | 0.40 |
| 0.25 | 0.1060 | 5.52 | −113.5° | 7279 | 0.44 | 0.53 | 0.46 |
| 0.30 | 0.1262 | 5.99 | −113.2° | 7176 | 0.49 | 0.56 | 0.50 |
| 0.35 | 0.1410 | 6.31 | −114.7° | 7117 | 0.52 | 0.58 | 0.52 |
| **0.40** | **0.1374** | **6.11** | **−112.2°** | 6848 | 0.55 | 0.60 | 0.53 |
| 0.45 | 0.1465 | 6.36 | −110.8° | 6946 | 0.56 | 0.61 | 0.54 |
| 0.50 | 0.1607 | 6.54 | −110.7° | 6759 | 0.59 | 0.63 | 0.54 |

Three observations:

1. **Peak at A=0.35, dip at A=0.40**: ρ_sig 0.141 → 0.137 → 0.147.
   Small but reliably non-monotonic (16 seeds × 25 chunks = 400
   chunk-trials per A). |μ_st| dips 6.31 → 6.11 → 6.36 — the dip
   is in the matched-filter magnitude, not just N_sw normalization.
2. **Lower absolute ρ_sig than S111**: at A=0.20 we get 0.090 vs S111's
   0.154 (random-ω with effective std ~0.13). The fixed ω_std=0.07
   sits below S111's effective average, hence lower coherence.
3. **Less rotation than S111**: total μ_arg rotates only ~3° around
   the dip (S113) vs 17° (S111). The bigger S111 rotation is driven by
   the broader ω-distribution: per-seed ω_std varies, each seed has
   slightly different class-phase rotation-with-A trajectories, and
   pooling them rotates the cross-seed circular mean more than fixed-ω.

### Class fractions of switches

| A | att_lock | att_noise | rep_lock | rep_noise |
|---|----------|-----------|----------|-----------|
| 0.10 | 0.21 | 0.23 | 0.06 | 0.50 |
| 0.20 | 0.33 | 0.14 | 0.04 | 0.49 |
| 0.30 | 0.46 | 0.10 | 0.03 | 0.41 |
| 0.40 | 0.53 | 0.08 | 0.03 | 0.37 |
| 0.50 | 0.57 | 0.06 | 0.02 | 0.35 |

att_lock fraction grows monotonically; rep_noise drops monotonically;
the small classes (att_noise, rep_lock) drop monotonically.
**By A ≥ 0.30, (att_lock + rep_noise) carries ≥87% of switches.**

### Per-class μ_class — the rotation story

Per-seed magnitude (matched-filter units, mean across 16 seeds):

| A | aL |μ| | aN |μ| | rL |μ| | rN |μ| |
|---|-----|-----|-----|-----|
| 0.10 | 152 | 129 |  94 | 126 |
| 0.20 |  97 |  60 |  41 |  87 |
| 0.30 |  76 |  27 |  25 |  85 |
| 0.40 |  76 |  17 |  15 |  82 |
| 0.50 |  71 |  15 |  12 |  86 |

(aN and rL drop fast; aL plateaus at ~75; rN plateaus at ~85.)

Per-class arg(μ_class) circular-mean across 16 seeds (degrees):

| A | aL arg | aN arg | rL arg | rN arg |
|---|--------|--------|--------|--------|
| 0.10 | −157 | −5  | −9  | +175 |
| 0.20 | −131 | −13 | −19 | −169 |
| 0.25 | −118 | −16 | −32 | −162 |
| 0.30 | −108 | −25 | −43 | −154 |
| 0.35 | −106 | −40 | −40 | −152 |
| 0.40 |  −98 | −43 | −37 | −147 |
| 0.45 |  −96 | −47 | −41 | −140 |
| 0.50 |  −96 | −62 | −51 | −136 |

**att_lock saturates near A≈0.35** (−106° → −96°, only 10° more from
A=0.30 to A=0.50). **rep_noise rotates monotonically** across the
sweep (+175° wraps to −136°, 49° rotation total). The smaller classes
also rotate monotonically.

### The dip mechanism: (att_lock, rep_noise) phase difference

Phase difference |arg(aL) − arg(rN)|, degrees:

| A | Δφ_aL,rN | cos(Δφ) | aL__rN cross 2|μ||μ|cos(Δφ) (per-seed) | ρ_sig |
|---|----------|---------|-----------------------------------------|-------|
| 0.10 | 28° | 0.88 | +33,101 | 0.0393 |
| 0.20 | 38° | 0.79 | +13,070 | 0.0902 |
| 0.25 | 44° | 0.72 |  +9,655 | 0.1060 |
| 0.30 | 44° | 0.71 |  +9,172 | 0.1262 |
| 0.35 | 46° | 0.69 |  +9,084 | 0.1410 |
| **0.40** | **49°** | **0.66** | **+8,168** | **0.1374** |
| 0.45 | 43° | 0.73 |  +9,183 | 0.1465 |
| 0.50 | 40° | 0.77 |  +9,432 | 0.1607 |

Δφ peaks at A=0.40, cos(Δφ) is minimal there (0.66), and the
(aL,rN) cross-term is correspondingly minimal (+8168 vs +9100s flanking
values). Recovery A=0.45 brings Δφ back down (43°), cross-term back to
+9183, and ρ_sig recovers.

### Geometric picture

In the complex plane (μ_class as vectors at A=0.40):
  - aL ≈ 76 · exp(i · −98°)  →  most-negative-imag direction
  - rN ≈ 82 · exp(i · −147°) →  third-quadrant
  - 49° wedge between them

At A=0.45 the wedge closes to 43°. At A=0.35 the wedge is 46° (smaller
than A=0.40 by 3°, larger than A=0.45 by 3°). The cross-term
2|μ_aL||μ_rN|cos(Δφ) traces this wedge angle.

### Identity check

The per-cell |μ_total|² = sumsq + cross identity holds to FP precision
across all 8 cells (residual < 1e-9):

| A | sumsq/|z|² | cross/|z|² | total |
|---|-----------|-----------|-------|
| 0.10 | 8.80 | −7.80 | 1.00 |
| 0.30 | 0.66 | +0.34 | 1.00 |
| 0.40 | 0.57 | +0.43 | 1.00 |
| 0.50 | 0.49 | +0.51 | 1.00 |

At low A, |μ_class|² greatly exceed |μ_total|² because classes have
disparate phases (8.8× cancellation). As A grows, phases align (up to
the wedge limit), cross-term goes positive, and |μ_total|² approaches
sumsq.

### Why class phases rotate at different A-rates

Att_lock events occur when (C+signal)<θ AND R_kura>0.9. The signal
biases C toward the threshold mostly when sin(2πf_s t) is at its
minimum (i.e., sin = −1, signal = −A). At low A, this is a weak bias,
and att_lock events are nearly uniformly distributed in signal phase
(μ_aL → 0 with random circular mean). As A grows, events cluster more
sharply at the signal-minimum phase. The arg(μ_aL) saturates at the
signal-minimum phase (−90° in our convention) because that's the
asymptotic clustering location.

Rep_noise events occur when (C+signal)>θ AND R unlocked — they are
NOISE-driven crossings during repulsive epochs. The signal still biases
their timing, but the bias is statistical (longer dwells in repulsive
state when signal is at the C-pushing-up half-cycle). Rep_noise has
a different signal-phase clustering: events are biased toward the
signal MAXIMUM (sin = +1, +A push). As A grows, the cluster sharpens
but its phase keeps rotating toward the signal-direct-driven asymptote
(the signal-maximum phase ≈ +90° from the signal-minimum), passing
through −136° (S113 measurement at A=0.50) en route.

The two mechanisms (gate-modulated lock ↔ signal-direct via repulsive
epochs) thus rotate toward DIFFERENT asymptotic phases at different
A-rates. Their wedge widens then narrows as the slower one catches up
to the faster — producing the dip at the maximum-wedge A.

## Implications & predictions

- **S113-P1 (dip-A vs κ_p)**: predict dip-A scales with κ_p, since
  att_lock saturation is gated by Kuramoto timescale ∝ 1/κ_p. At
  κ_p=0.10 dip-A predicted ~0.13. At κ_p=1.0 predicted ~1.3 (or
  saturation may move out of the experimentally accessible regime).
  Sweep at 3 κ_p values × dip-A grid.
- **S113-P2 (dip-A vs κ_C)**: κ_C=0 should kill att_lock entirely
  (S110-P3); the dip should NOT appear because there's no two-mechanism
  structure. Check: ρ_sig vs A at κ_C=0 should be approximately
  monotonic.
- **S113-P3 (dip-A vs ω_std)**: at higher ω_std (still below cliff),
  att_lock relaxation is harder, saturation may shift. Predict dip-A
  shifts to higher A as ω_std rises in [0.07, 0.13].
- **S113-P4 (att_lock arg-saturation invariant)**: arg(μ_aL) plateaus
  near −96° at high A regardless of κ_p, ω_std. The saturation phase
  is a geometric invariant set by the signal sin/cos basis modulo
  warmup-phase choice.
- **S113-P5 (signal-phase clustering test)**: predict events cluster
  on signal phase: att_lock at sig_phase ≈ 3π/2 (sin = −1, signal at
  minimum); rep_noise at sig_phase ≈ π/2 (signal at maximum) but with
  A-dependent shift. Direct binned-histogram of `signal_phase_at_switch`
  per class will pin this down.
- **S113-P6 (predicted dip-A from arg-saturation)**: if arg(μ_aL)
  saturates at A_sat with rate r_aL, and arg(μ_rN) rotates at rate
  r_rN, the dip-A is approximately A_dip = A_sat + Δr · A_sat/r_rN
  where Δr depends on initial separation. Concrete form needs more
  data points and a 1D model fit.
- **S113-P7 (κ_p × ratio cross-test)**: at ratio 0.2 (S108 shifted-ridge,
  σ_φ wider) the att_lock saturation A may differ. Check whether dip-A
  is universal across (κ_p, ratio) or just a ridge-specific property.

## Methodological notes

1. **Class decomposition is exact**. Because total μ = Σ μ_class is a
   linear identity over disjoint event sets, the decomposition is
   numerically lossless (residual 1e-14 in smoke test). It can be
   applied retrospectively to any session that has switch_steps,
   switch_dirs, kura_dec, gate_dec stored.
2. **Per-class arg coherence is high (R ≥ 0.85 across seeds for
   dominant classes).** Per-class statistics are well-behaved. The
   small classes (rep_lock especially) become noisy at high A as
   counts drop below ~50 events per seed.
3. **For mechanism analysis at the ridge, fixed ω at ω_std=0.07 is
   the cleanest setting**: dip is real but small (3%), per-class arg
   measurement is precise, and ω_std<<cliff (0.17) eliminates
   confounder.
4. **Cross-term magnitudes scale with the DOMINANT pair (aL,rN)
   product** ~75×85 ≈ 6400, and the wedge cosine. Sub-leading pairs
   contribute < 20% of cross_total. Future work can collapse the 6
   pair-wise terms into the (aL,rN) wedge and treat the rest as noise.
5. **The angle rotation in S111 (17°) was amplified by per-seed ω
   heterogeneity** — different seeds had different class-phase
   rotation curves, and the cross-seed circular mean of arg(μ_total)
   rotates differently than each seed individually. Fixed-ω runs
   give cleaner per-class measurements; random-ω runs give larger
   pooled-angle rotations. Use fixed-ω for mechanism, random-ω if
   measuring detector behavior in a heterogeneous ensemble.

## Cross-references

- S110: 5-step mechanism chain. The att_lock class is the "step 5
  output" (switching clusters at signal-phase peaks via lock).
- S111: dose-response that surfaced the dip.
- S112: ω-cliff explained the A=0.50 variance, deferred the A=0.40 dip.
- S107: ridge map; "ST phase is signal-locked (arg ~ −100°) across
  all cells" — this is the att_lock saturation phase.
- S109: σ_φ at ridge (64°/81°) is wider than expected; pairwise |Δφ|
  bimodal. The class decomposition here partially explains why σ_φ is
  large: switches happen across both the locked (att_lock) and unlocked
  (rep_noise) phase regimes, and their per-oscillator phase distributions
  differ.

## Files

- `thor_session_113_dip_decomposition.py` — runner (uses
  `simulate_with_omega` from S112)
- `thor_session_113_dip_decomp_results.json` — per-seed records (1.1MB)
- `thor_session_113_smoke.py` — class-sum identity check (1e-14 residual)
- `thor_session_113_analyze.py` — top-line table and class breakdown
- `thor_session_113_mechanism.py` — pooled-sum and per-seed cross-term
  pair analysis
- `thor_session_113_analysis.json` — tidy summary
- `thor_session_113_mechanism.json` — class-aggregated structure
- `thor_session_113_run.log` — full simulation log
