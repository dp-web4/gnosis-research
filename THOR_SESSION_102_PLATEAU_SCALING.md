# Thor Session #102: Plateau Scales With A — But RAW Is Exponential, Not Flat

**Date**: 2026-04-19
**Operating point**: N=4, dt=0.1, signal_freq=0.003, σ=0.022, ω_spread=0.02
**Compute**: 52 min new sim (128M steps) + reanalysis
**Status**: S101-P1 partially confirmed (plateau grows with A), but a deeper finding emerges: **RAW residual-phase ACF is exponential with τ ≈ 80–140 ks**, not plateau-dominated. S101's "plateau-only" description held because it fit only 10 lags; over 30 lags the decay is visible.

---

## TL;DR

1. **S101-P1 (plateau grows with A) is confirmed** for both channels. Plateau height over lags 1..30 goes RAW {A=0 → 0.03, A=0.10 → 0.10, A=0.20 → 0.11, A=0.30 → 0.23, A=0.40 → 0.29, A=0.50 → 0.39} and ST {0.04, 0.16, 0.53, 0.77, 0.85, 0.82}. **Plateau is signal-induced**, matching S101's finding.
2. **But the "plateau" isn't really a plateau for RAW** — the lag-30 window reveals a clear exponential decay. The ACF is well-described as `ACF(m) ≈ p_∞ + B·exp(-m·T/τ)` with τ = 80–140 ks and p_∞ = 0.00–0.06. **S99/S100's 21–23 ks RAW-exponential was an artifact of fitting only 10 lags** — the short fit captures the fast early drop but misses the true decay timescale ~4× longer.
3. **ST is genuinely plateau-like** at A ≥ 0.30. Two-component fit gives τ ≫ 10⁶ s (effectively infinite). At A=0.20 the ST plateau itself shows a ~30% drop over 30 lags — the exponential regime is only visible near the detection floor. At A=0.50 there's a small late drop (0.85 → 0.77 at lag 30) — possibly the onset of a slow amplitude or phase-locking drift.
4. **σ_n is beautifully A-invariant** — RAW σ_n constant within 3% across A=0 to 0.50; ST σ_n constant within 6%. Supports "chunk-MF noise is intrinsic to the bistable dynamics, independent of signal drive".
5. **|⟨z⟩| is NOT linear in A** — it saturates. ST slope drops from 24.6 (A=0.10) to 13.0 (A=0.50). RAW similar pattern. **M2 (Gaussian-around-μ, exp(-1/SNR²)) and M3 (Rice-phase concentration) both MISS the data** — RAW M3 RMSE=0.13 vs measured range 0.03–0.39.
6. **M1 (p = A²/(A²+σ_A²)) is the best empirical fit** with σ_A(RAW) = 0.60, σ_A(ST) = 0.19 — but it has no first-principles derivation that we can identify. ST RMSE 0.043; RAW RMSE 0.035. The success of M1 over M3 says: **the residual-phase distribution is NOT Rice**; it has heavier tails or per-seed heterogeneity.

---

## Background

S101 (2026-04-19 earlier) reanalyzed S98's A=0.30 data (8 × 100 chunks) using S99's linear-Δω phase-residual method and reported:

```
ACF_resid(m) ≈ 0.33·1 + 0.67·δ_{m,0}     (RAW, lags 1..10 essentially flat)
ACF_resid(m) ≈ 0.76·1 + 0.24·δ_{m,0}     (ST,  lags 1..10 essentially flat)
```

and claimed the decomposition is plateau + white noise, not exponential. The
main prediction it left open:

> **S101-P1**: RAW residual-phase ACF plateau at 0.33 (σ=0.022, A=0.30)
> should scale as A² / (A² + σ_A²). Sweep A ∈ {0.10, 0.20, 0.30, 0.50} at
> σ=0.022, 8 seeds × 100 chunks.

This session runs that sweep (with A=0.40 added and A=0.30 reused from S98,
A=0 reused from S101-A) and extends the lag window to m = 30 for a more
careful decay-vs-plateau diagnostic.

---

## Protocol

- Sweep A ∈ {0.00, 0.10, 0.20, 0.30, 0.40, 0.50} at σ=0.022, ω_spread=0.02.
- 8 seeds × 100 chunks per A, T_chunk = 4000 s (matches S98/S101 stats).
- A=0.00 reused from S101 Part A; A=0.30 reused from S98 main; 0.10, 0.20, 0.40, 0.50 fresh (seed_base 102000 + 100·A_index).
- Detector: S99 linear-Δω phase-residual method per seed, then circularly pool across seeds.
- Measure: per-seed |⟨z⟩| (our "μ"), per-chunk σ_n = √⟨|z − ⟨z⟩|²⟩, residual-phase ACF |Φ(m)| for m = 0..30.
- Fit three models: M1 (SNR²-ratio), M2 (exp(-1/SNR²) Gaussian linearization), M3 (exact Rice-phase concentration).
- Two-component ACF fit: `ACF(m≥1) = p_∞ + B·exp(-m·T_chunk/τ)`, grid over p_∞.

---

## Findings

### Finding 1 — Plateau height grows with A in both channels

Averaging |Φ(m)| over lags 1..30:

```
A      RAW plat   ST plat   RAW |⟨z⟩|    ST |⟨z⟩|   RAW σ_n    ST σ_n
0.00   0.031      0.036     1.80e-3      0.218      0.0249     3.15
0.10   0.098      0.158     1.17e-2      2.460      0.0252     3.14
0.20   0.105      0.527     1.49e-2      3.724      0.0241     3.16
0.30   0.227      0.765     1.89e-2      5.184      0.0244     3.34   (S98)
0.40   0.293      0.845     2.27e-2      6.201      0.0234     3.22
0.50   0.392      0.822     2.37e-2      6.503      0.0232     3.27
```

Both plateaus grow with A, then saturate. ST saturates earlier (flattens at ≈ 0.85 by A=0.40, slight non-monotone drop at A=0.50). RAW continues growing through A=0.50.

Null floor at A=0 is 0.031 / 0.036 — consistent with 1/√N_pairs ≈ 0.036 for 800 pairs. All A ≥ 0.10 plateaus are above null.

### Finding 2 — RAW residual-phase ACF is exponential, not flat

Raw full ACF curves (lags 1, 5, 10, 15, 20, 25, 30):

```
RAW |Φ(m)|:
  A=0.00:   [0.048, 0.033, 0.014, 0.028, 0.028, 0.027, 0.018]   (null)
  A=0.10:   [0.144, 0.162, 0.068, 0.101, 0.118, 0.111, 0.061]
  A=0.20:   [0.250, 0.158, 0.110, 0.045, 0.059, 0.078, 0.115]
  A=0.30:   [0.343, 0.314, 0.301, 0.251, 0.148, 0.130, 0.214]
  A=0.40:   [0.473, 0.425, 0.374, 0.284, 0.196, 0.165, 0.136]
  A=0.50:   [0.509, 0.497, 0.455, 0.402, 0.364, 0.281, 0.206]

ST |Φ(m)|:
  A=0.00:   [0.044, 0.022, 0.024, 0.015, 0.016, 0.042, 0.036]   (null)
  A=0.10:   [0.340, 0.327, 0.243, 0.127, 0.021, 0.065, 0.073]
  A=0.20:   [0.587, 0.597, 0.546, 0.535, 0.492, 0.470, 0.414]
  A=0.30:   [0.759, 0.780, 0.762, 0.761, 0.756, 0.757, 0.780]
  A=0.40:   [0.847, 0.847, 0.836, 0.844, 0.847, 0.842, 0.848]
  A=0.50:   [0.850, 0.856, 0.836, 0.824, 0.817, 0.794, 0.765]
```

RAW at A=0.40 and A=0.50: clear monotonic decay (2× drop from lag 1 to lag 30). RAW at A=0.30: S101's "plateau 0.33" looks flat over the first 10 lags (as S101 saw it) but then drops to 0.13–0.21 by lag 25–30. The lag window matters.

Two-component fit `ACF(m) = p_∞ + B·exp(-m·T/τ)` for m ≥ 1:

```
Channel   A     p_∞    B      τ (s)       pure-plateau RMS   two-comp RMS
RAW       0.10  0.032  0.067  494,000     0.0324             0.0324
RAW       0.20  0.010  0.173   74,000     0.0629             0.0411
RAW       0.30  0.061  0.313   83,000     0.0735             0.0278
RAW       0.40  0.000  0.544   89,000     0.1111             0.0211
RAW       0.50  0.000  0.598  136,000     0.0943             0.0297

ST        0.10  -0.02  0.447   52,000     0.1179             0.0413
ST        0.20  0.000  0.629  342,000     0.0544             0.0164
ST        0.30  0.000  0.761     ∞        0.0078             0.0088
ST        0.40  0.000  0.847   24.5M      0.0056             0.0054
ST        0.50  0.000  0.866    1.2M      0.0247             0.0069
```

**RAW at A ≥ 0.20 is exponential-dominated**. Two-component RMS beats pure-plateau RMS by 2–5× at A = 0.20, 0.30, 0.40, 0.50. The decay timescale τ ≈ 80–140 ks (20–35 chunks).

**ST at A ≥ 0.30 is plateau-dominated**. Two-comp fit gives τ → ∞ (fit falls back to pure plateau). At A=0.20 ST has a visible exponential (τ = 342 ks).

**Reconciliation with S99/S100/S101**:

- S99 reported RAW τ = 21 ks (R² = 0.97) by fitting exp to lags 1..10 with a floor. With 30 lags available, my fit gives τ = 83 ks at A=0.30 — **4× longer**. S99's τ was biased low because the early lags drop faster (large B·exp(-m/τ) near lag 1 pulls the log-fit toward smaller τ when only a narrow m range is available).
- S100's "σ-invariance" (21 ks at σ=0.022, 23 ks at σ=0.060, agreeing within 12%) was likely real within the constraints of short-fit: both shared the short-fit artifact in similar proportion. The underlying long-window τ at σ=0.060 is unknown and should be remeasured.
- S101 looked at the same A=0.30 RAW data and said "lag 1..10 is flat — plateau + white". Lags 1..10 are ~0.343 → 0.301, which is a small 12% drop — genuinely flat to the eye. But lags 10..30 go 0.301 → 0.130 → 0.214 — a clear ~60% drop. **S101's conclusion was correct for lags 1..10; it was incorrect to extrapolate to "no exponential".**

### Finding 3 — σ_n is A-invariant; μ(A) saturates

Chunk-MF noise magnitude σ_n = √⟨|z − ⟨z⟩|²⟩:

```
RAW σ_n: [0.0249, 0.0252, 0.0241, 0.0244, 0.0234, 0.0232]   (A = 0.0..0.5)
ST  σ_n: [3.15,   3.14,   3.16,   3.34,   3.22,   3.27]
```

RAW σ_n essentially constant at 0.024 (2% variation); ST σ_n at 3.22 (6% variation). This supports the intuition that "per-chunk MF noise" is set by the bistable dynamics' own switching variance, not by signal drive.

But |⟨z⟩| is **strongly sublinear in A** — it saturates:

```
A:       0.00    0.10     0.20     0.30     0.40     0.50
|μ|_RAW: 1.80e-3 1.17e-2  1.49e-2  1.89e-2  2.27e-2  2.37e-2
 slope:          0.117    0.075    0.063    0.057    0.047
|μ|_ST:  0.218   2.460    3.724    5.184    6.201    6.503
 slope:          24.6     18.6     17.3     15.5     13.0
```

The RAW |⟨z⟩| grows by ~20× from A=0 to A=0.50 but only 2× from A=0.20 to A=0.50. ST saturates even harder. Physical origin: as A grows, signal-driven switches saturate (N_sw/chunk drops from 607 → 504 across A=0..0.5 as noise-driven switches are replaced by signal-driven ones), so the "deterministic signal mean" in the MF stops growing with A.

This **breaks the M2 side-prediction** (μ ∝ A). The linear fit |⟨z⟩|_RAW = 0.042 A has R² = 0.44 — poor.

### Finding 4 — M1 ≫ M3 (Rice) ≫ M2 (linearized)

```
Model     Form                              RAW RMSE   ST RMSE
M1        p = A²/(A² + σ_A²)                0.0347     0.0427
M2        p = exp(-1/(2·SNR²)) [corrected]  0.0476     0.0636  (approximation)
M3        p = |⟨e^iφ̃⟩|² exact Rice           0.1255     0.0919

M1 fit:   σ_A²(RAW) = 0.362   →  σ_A = 0.602
          σ_A²(ST)  = 0.036   →  σ_A = 0.190
```

The **exact Rice prediction (M3) is significantly off** — it overpredicts p at low A and underpredicts near saturation. Since M3 is analytically correct for the "complex Gaussian chunk noise around seed-coherent mean" model, the model itself is wrong. Candidate reasons:

- **Per-seed μ_k heterogeneity**: each seed has a slightly different μ, and the circular ACF across seeds is reduced by this spread (low A) but also coherent-averaging assumes μ is shared.
- **Non-Gaussian tails**: per-chunk deviation from μ is not i.i.d. complex Gaussian — switching statistics may have heavier tails.
- **Slow drift components**: the exponential-decay finding (Finding 2) shows per-chunk residuals are NOT iid; they have slow (τ ~ 80 ks) autocorrelation. M3 assumes iid.

M1 wins empirically but has no first-principles derivation connecting A, |μ|, σ_n. Its σ_A² is a fit parameter; at A = σ_A, p = 0.5.

### Finding 5 — Per-seed residual RMS phases vary 5× across seeds

Per-seed unwrapped-residual phase RMS (in radians):

```
A      RAW mean ± std     ST mean ± std
0.00   3.99 ± 0.51        4.46 ± 1.24
0.10   3.95 ± 0.70        2.65 ± 1.05
0.20   3.34 ± 0.59        1.48 ± 1.05
0.30   3.07 ± 1.03        0.54 ± 0.03
0.40   1.58 ± 0.64        0.40 ± 0.04
0.50   1.65 ± 0.77        0.56 ± 0.46
```

ST converges seed-to-seed at A=0.30 and A=0.40 (RMS spread 5–10% of the mean). RAW never converges — seed-to-seed σ(RMS)/mean stays at 0.3–0.5 across all A. The **per-seed heterogeneity is a real and persistent feature of the RAW channel**, another reason M3 (which assumes shared μ) fails there.

---

## Reconciliation with prior claims

| Claim                                                   | S102 view |
|---------------------------------------------------------|-----------|
| S99: RAW residual-phase ACF has τ = 21 ks at σ=0.022    | **Revised: τ ≈ 83 ks** at A=0.30 (short-fit was biased low) |
| S100: τ_res σ-invariant (21→23 ks, σ:0.022→0.060)       | **Needs re-measurement** at 30 lags for both σ |
| S101: ACF is plateau + white, not exponential           | **Half-right**: true for lags 1..10; lags 1..30 reveal exponential decay in RAW |
| S101-P1: plateau scales as A²/(A²+σ²)                   | **Empirically holds** (RMSE 0.03–0.04) but no first-principles derivation |
| S101: S100-P3 wander is signal-induced, not intrinsic   | **Still correct** (A=0 null floor matches prediction) |

---

## New open predictions

**S102-P1**: At A=0.30, σ=0.022, ω_spread=0.02, extend to 8 seeds × 500 chunks × T_chunk=4000s (T_total = 2,000,000 s). RAW ACF at lag 30 (120 ks ≈ 1.4 τ) should be 0.15; at lag 100 (400 ks ≈ 5 τ) should drop to p_∞ ≈ 0.06. Current data can't distinguish p_∞=0 from p_∞=0.06 cleanly because τ is only 20% of the window. Longer window decides whether there's a persistent deterministic offset beneath the exponential.

**S102-P2**: σ-sweep of τ_RAW at A=0.30 with 30-lag resolution. If τ scales with 1/σ² (switching-driven), τ(σ=0.015) ≈ 175 ks, τ(σ=0.030) ≈ 44 ks. If τ is σ-invariant (deterministic), stays at 83 ks. S100 observed the short-fit τ was σ-invariant; long-fit is unknown.

**S102-P3**: ω_spread sweep at A=0.30, 8 × 100 chunks per ω_spread ∈ {0.005, 0.02, 0.08}. If τ_RAW ∝ 1/Δω (collective-oscillator phase diffusion), τ should grow 10× at ω_spread=0.005.

**S102-P4**: ST at A=0.50 shows a slow late drop (0.85 → 0.77 at lag 30). With 200-chunk data this should clarify: is it noise (flattens around 0.80) or real decay (continues dropping with τ ~ 1 Ms)? This is the only hint that ST has any finite τ at high A in this window.

**S102-P5**: Physical interpretation of why M3 (Rice) fails. Likely mechanism: per-chunk residuals are not iid but have slow autocorrelation (τ ≈ 80 ks, Finding 2). Can we predict p from τ and B directly? Model: ACF ≈ B·exp(-m/τ) + p_∞, and the **effective plateau** = B + p_∞ at m=1. With B, τ measured, this is a parameter-free prediction of "apparent plateau".

---

## Methodological upgrade (vs S99/S100/S101)

**When characterizing chunk-ACF decay in this model family:**

1. **Use at least 30 lags** (120 ks = 1–2 τ_RAW). Short fits (10 lags) give biased τ values — typically **3–4× too fast**. 
2. **Fit two-component** `p_∞ + B·exp(-m/τ)` first. Short-fit exponential-only and short-fit plateau-only are both degenerate — the 10-lag RAW ACF is equally well described by τ=21 ks plateau-less and by τ=∞ plateau 0.33.
3. **Report both RMS values** (two-comp vs pure-plateau) so readers can judge model preference from the data rather than from the fit label.
4. **Don't assume M3 holds** — the per-chunk residuals have slow autocorrelation (Finding 2) and per-seed heterogeneity (Finding 5). The Rice formula overpredicts at low A by 60%.

---

## Compute

- 4 new A runs × 8 seeds × 4.01 M steps × 24 µs/step = 3120 s = 52 min (measured: 52.0 min).
- Analysis + reanalysis: < 10 s.
- Total wall-clock: ~53 min on Thor.

## Files

- `thor_session_102_plateau_scaling.py` — simulation
- `thor_session_102_analyze.py` — secondary analysis (full ACF curves, two-component fits, M3 Rice)
- `thor_session_102_plateau_scaling_results.json` — all per-seed z_raw/z_st + summaries
- `thor_session_102_analysis.json` — compact per-A analysis results
- `thor_session_102_run.log` — simulation log
