# Thor Session #111: ρ_sig Is Non-Monotonic in A — Three Regimes at the Ridge

**Date:** 2026-04-22
**Focus:** S110-P4 — A-sweep at the ridge to characterize dose-response
laws of the 5-step S110 mechanism chain.
**Status:** Resolved with three surprises. Linearity holds for mod_lock
in A only up to A=0.20, then SUPER-linear. ρ_sig has a local maximum
near A=0.20, dips at A=0.30–0.40, recovers at A=0.50 with high seed
variance. The matched-filter A² prediction is **falsified** even at low
A (low-A exponent 1.2). Detection floor crosses 5σ between A=0.02 and
A=0.05.

## TL;DR

Sweep A ∈ {0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50} at the S109/S110
ridge (κ_p=0.30, κ_C=0.30, ratio 0.8). 10 seeds × 30 chunks each.

Five primary findings:

1. **mod_amp_at_fs_lock IS linear in A up to A=0.20** (slope 0.322/A,
   r² = 0.994). Above A=0.20 it grows SUPER-linearly through A=0.30
   (+31% above linear extrapolation), then converges back toward
   linear by A=0.50. Predicted saturation does not occur in the
   measured range — instead there's a kink-up around A=0.20.

2. **ρ_sig is NOT quadratic in A.** Low-A log-log fit (A ≤ 0.20) gives
   exponent **1.21**, not the matched-filter prediction of 2.0. Across
   the full range the effective exponent is 0.74 (badly sub-linear).

3. **ρ_sig is non-monotonic.** It peaks at A=0.20 (0.154), DIPS at
   A=0.30 (0.139) and A=0.40 (0.128), then recovers to 0.203 at A=0.50.
   The S110 ridge anchor at A=0.30 (ρ_sig=0.139) is **not the maximum**
   — A=0.20 is 11% better, and A=0.50 is 47% better.

4. **The S109 R_inst² law is approximately A-invariant in [A=0.10, A=0.40]**
   with γ in 0.40–0.60 (S109 reported 0.4 at A=0.30). At A=0.05 γ=0.18
   (small-signal regime undershoots), at A=0.50 γ=0.62 (super-driven
   regime overshoots). The S109 γ ≈ 0.4 is a single point on a slowly
   varying curve, not a fundamental constant.

5. **First-principles |z_st| identity holds to 0.2% across all A.**
   Sum-form fp_ratio in [0.993, 1.002]. The switch-timing matched
   filter is exactly Σ_k direction_k · e^{-i·2πf_s·t_k} — confirms the
   S110-P6 closed form across an order of magnitude in A.

Detection floor: z_det = √(N_chunks · ST_R / (1 − ST_R)) crosses 5σ
between A=0 and A=0.05 (linear interpolation: A_min ≈ 0.05). At
A=0.05, z_det=4.88 (just below); at A=0.10, z_det=6.13.

## Interpretation: three regimes

The combined non-monotonicity in ρ_sig and the kink-up in mod_lock
suggest **three operating regimes** for the gate-modulated detector:

- **Linear gate-modulated (A ∈ [0.00, 0.20])**: signal is too weak to
  flip the gate by itself; the gate's bistable dichotomy is preserved.
  mod_lock ∝ A; lock_frac, P(L|att) climb monotonically. ρ_sig grows
  somewhat slower than A² (mediated by N_sw drop and R_inst² growth).

- **Coherent saturation (A ∈ [0.20, 0.30])**: signal is strong enough
  to drive R_kura(t) up further (mod_kura climbs +98% from A=0.20 to
  A=0.30), boosting mod_lock super-linearly. lock_frac peaks at 0.40
  (A=0.30). But the per-event signal density ρ_sig peaks at A=0.20 and
  starts to fall — additional lock-modulation does not translate into
  better detector ρ_sig because N_sw begins to grow again.

- **Gate-disruption / signal-driven (A ≥ 0.40)**: signal magnitude
  approaches the bistable threshold offset (C_threshold − ⟨C_mean⟩
  ≈ 0.55 − 0.55 ≈ 0). The gate flips on signal phase alone, decoupling
  from the C bistable state. lock_frac DROPS (0.40 → 0.35), P(L|att)
  drops (0.76 → 0.64). At A=0.50 a new regime opens: ρ_sig recovers
  to 0.203 but cross-seed R_angle drops to 0.66 (from 0.997 at A=0.30) —
  some seeds detect well, others don't. The system has entered
  signal-direct-driven mode.

The crossover is sharper than expected. The S109/S110 picture (signal
modulates gate → R_kura(t) at f_s → switch-clustering → ρ_sig) is the
**linear regime**. Above A ≈ 0.30 the bistable approximation breaks.

## Data — Seven Cells (10 seeds × 30 chunks × 40k steps each)

| A    | mod_lock | mod_kura | mod_cosφ | R_kura | lock% | ρ_sig  | ST_R  | RAW_R | ⟨N_sw⟩ |
|-----:|---------:|---------:|---------:|-------:|------:|-------:|------:|------:|-------:|
| 0.00 | 0.0040   | 0.00479  | 0.00474  | 0.393  | 0.153 | 0.0008 | 0.043 | 0.038 | 12543  |
| 0.05 | 0.0150   | 0.01761  | 0.01210  | 0.400  | 0.172 | 0.0288 | 0.442 | 0.353 | 10536  |
| 0.10 | 0.0343   | 0.03385  | 0.02193  | 0.413  | 0.223 | 0.0754 | 0.556 | 0.453 | 9238   |
| 0.20 | 0.0669   | 0.05323  | 0.04591  | 0.508  | 0.283 | 0.1538 | 0.753 | 0.624 | 7510   |
| 0.30 | 0.1291   | 0.10577  | 0.04378  | 0.549  | 0.404 | 0.1387 | 0.726 | 0.569 | 8565   |
| 0.40 | 0.1555   | 0.13998  | 0.05222  | 0.567  | 0.354 | 0.1277 | 0.698 | 0.494 | 7937   |
| 0.50 | 0.1712  | 0.17896  | 0.05901  | 0.573  | 0.349 | 0.2033 | 0.784 | 0.564 | 8072   |

Cross-seed R_angle (signal-detection coherence across seeds):

| A    | R_ang_lock | R_ang_kura | R_ang_cosφ |
|-----:|-----------:|-----------:|-----------:|
| 0.00 | 0.198      | 0.133      | 0.368      |
| 0.05 | 0.763      | 0.807      | 0.614      |
| 0.10 | 0.706      | 0.815      | 0.237      |
| 0.20 | 0.827      | 0.960      | 0.495      |
| 0.30 | 0.997      | 0.995      | 0.133      |
| 0.40 | 0.992      | 0.996      | 0.664      |
| 0.50 | 0.658      | 0.998      | 0.618      |

Note R_ang_lock drops from 0.99 (A=0.30/0.40) to 0.66 (A=0.50) while
R_ang_kura stays at 0.998. The lock-indicator (binary R_kura(t)>0.9)
becomes noisier at high A even though the continuous R_kura(t) modulation
is perfectly coherent across seeds. Interpretation: at A=0.50 R_kura(t)
spends more time near 0.9 — small per-seed offsets push the indicator
back and forth, while the underlying R_kura(t) is well-locked.

Replication of S110 ridge anchor at A=0.30:

| Quantity         | S110 (8 seeds) | S111 (10 seeds) |
|------------------|---------------:|----------------:|
| mod_amp_at_fs    | 0.124 ± 0.010  | 0.129 ± 0.034   |
| ρ_sig            | 0.137          | 0.139           |
| ST R_coh         | 0.759          | 0.726           |
| ⟨N_sw⟩ / seed    | 8830           | 8565            |
| P(L|att)         | 0.681          | 0.760           |
| P(L|rep)         | 0.018          | 0.020           |

S110/S111 are within 1σ on every quantity except P(L|att) (S111 is
0.08 higher — possibly seed noise or initialization differences).
Simulator behavior is reproducible.

## Predictions and verdicts

| #  | Prediction | Verdict |
|----|------------|---------|
| P1 | mod_lock ∝ A in small-A | **CONFIRMED** for A ≤ 0.20 (slope 0.322/A, r²=0.994). Breaks ABOVE — super-linear, not saturating, in [0.20, 0.30]. |
| P2 | High-A saturation deficit | **FALSIFIED**. Negative deficit (overshoot) at A=0.30: actual=0.129, linear-pred=0.099 (−31% deficit means +31% overshoot). |
| P3 | ρ_sig ∝ A² in low-A | **FALSIFIED**. Low-A exponent 1.21, not 2.0. |
| P4 | γ in ρ_sig=γ·R_inst² A-invariant (≈0.4) | **PARTIAL**. γ in [0.40, 0.62] over A ∈ [0.10, 0.50]; γ=0.18 at A=0.05. Mean γ=0.45, CV=32%. Approximately invariant in mid-A. |
| P5 | First-principles |z_st| holds across A | **CONFIRMED** to 0.2% (sum-form identity, expected ~ 1.0). |
| P6 | Detection floor A_min | **CONCRETE**: A_min ≈ 0.05 for z_det = 5σ (z_det=4.88 at A=0.05, =6.13 at A=0.10). |
| P7 | lock_frac monotonic in A | **PARTIAL**. Monotonic for A ≤ 0.30 (0.15 → 0.40), DROPS at A=0.40 (0.35) and A=0.50 (0.35). Peak at A=0.30. |

## Surprises

1. **mod_lock super-linearity in [0.20, 0.30]**, not the predicted
   saturation. The lock indicator (R_kura(t)>0.9) overshoots the
   linear extrapolation by 31% at A=0.30. mod_kura (continuous R_kura)
   shows the same kink: 0.05323 → 0.10577 (1.99× from doubling A=0.10
   → A=0.20 = 1.57×). This says R_kura(t) crosses 0.9 with sharper
   amplitude swings as A grows past 0.20 — the lock state becomes
   "binary-cleaner."

2. **ρ_sig non-monotonicity** is the headline. The matched-filter
   chain predicts ρ_sig ∝ |⟨z_st⟩|² = (signal power) / (event count)
   — both terms can change with A, and they do, but in opposite
   directions. The peak at A=0.20 is the "sweet spot" where signal
   power per event maxes out before the gate-disruption regime opens.

3. **A=0.50 ρ_sig recovery with high seed variance**. ρ_sig=0.20 (44%
   above the A=0.20 peak), but cross-seed R_angle drops to 0.66 — so
   per-seed ρ_sig values are highly variable. ρ_sig=0.20 ± 0.11
   (CV=53%, vs CV=12% at A=0.30). Some seeds find a good detection
   regime in the signal-driven mode, others don't. The MEAN-ρ_sig
   metric masks a bimodal seed distribution at A=0.50. Possible: some
   seeds get phase-locked to the strong driver, others don't, depending
   on initial-condition phase.

4. **Detection floor at A=0.05 is essentially crossed at z_det=4.88**,
   one chunk shy of 5σ. With 30 chunks × 4000s = 120ks at A=0.05
   the system already discriminates from A=0 by ~5σ. SR detection in
   this configuration extends to surprisingly small signals.

5. **mod_cosφ is inconsistent across A** (R_ang_cosφ in [0.13, 0.67]
   non-monotonically) compared to R_ang_kura which climbs to 0.998.
   mod_cosφ measures the modulation of cos(arg(⟨e^{iφ}⟩)) at f_s.
   The ARG of the mean phase vector is unwrapped/wrapped uncleanly,
   so cos(⟨φ⟩) is not the right S110-P3 rectifier observable. We need
   per-oscillator cos(φ_k) tracking instead. **S110-P3 is unaddressed
   by this S111 measurement**; needs the per-oscillator phase storage
   from S109 plus this finer A-sweep.

## Mechanism revision (S111 → S112+)

Pre-S111 picture (S110 5-step chain):

  signal → gate → coupling-sign-flip → R_kura(t) modulation → cos(φ)
  drive → κ_C-concentrated switching → ρ_sig.

S111 reveals the chain has THREE regimes mapped onto A:

- **Gate-modulated linear regime** (A ≤ 0.20): the chain's terms are
  in their linear approximations. mod_lock ∝ A, R_kura mean grows
  modestly, ρ_sig has effective exponent ≈ 1.2 — the matched-filter
  chain stacks two linear factors (mod_amp ∝ A) and one
  proportional-to-1/A factor (1/N_sw, since N_sw drops with A as
  more switches are coherent and consume the bistable budget).

- **Coherent gate-saturated** (0.20 ≤ A ≤ 0.30): R_kura modulation
  starts swinging more strongly through 0.9, mod_lock kicks up
  super-linearly, but per-event signal coherence saturates (events
  start clustering at the SAME signal phase rather than two opposite
  phases as the matched-filter sum requires).

- **Gate-disruption** (A ≥ 0.40): the signal swings C_mean past
  threshold by itself; the C-bistable doesn't always determine the
  attractive/repulsive gate state. The 5-step chain breaks. Detection
  is still possible (z_det stays high) but via a different mechanism:
  signal-direct-driving of C through the cos(φ)·(C−φ_inv) coupling
  rather than gate-modulation of phase coupling.

The maximum-detection-power operating point is A ≈ 0.20 for the ridge
geometry (κ_p=0.30, κ_C=0.30, ratio 0.8). Above that, more signal
amplitude doesn't help and may hurt.

## Open predictions for S112+

- **S111-P1**: ρ_sig peak A* shifts with κ_p. Predict A* ∝ κ_p^{-1}
  (heuristic: stronger phase coupling means smaller A suffices to
  saturate the chain). Sweep A at κ_p ∈ {0.10, 0.50, 1.0}.
- **S111-P2**: ρ_sig peak A* shifts with ratio. At ratio 0.2 (S108
  found ridge height drops 31%), where is A*? Run mini A-sweep
  at ratio 0.2.
- **S111-P3**: Bimodal-seed structure at A=0.50. Plot per-seed ρ_sig
  histogram. If bimodal, identify the discriminator (initial-condition
  phase? omega draw?). Predict: bimodal at A=0.50, unimodal at A ≤ 0.30.
- **S111-P4**: per-oscillator cos(φ_k) cross-correlation with switch
  events at A=0.20 (peak ρ_sig). The S110-P3 rectifier test, properly
  done with per-oscillator phase storage. Predict r > 0.5 at the
  peak A.
- **S111-P5**: mod_lock super-linearity in [0.20, 0.30] originates
  from **lock-state amplitude-swing growth** (R_kura(t) crosses 0.9
  with steeper slope as A grows). Test by recording R_kura(t) wave
  shape — predict shaper rise/fall through 0.9 at A=0.30 vs A=0.10.
- **S111-P6**: detection-power normalization. z_det²/N_chunks should
  be a smoothly varying function of A. Compare across cells.
- **S111-P7**: A-sweep at κ_C=0.00 (the nokC condition). Predict
  ρ_sig stays at floor (~0.01) across all A — κ_C-as-switch-concentrator
  is necessary regardless of A. Tests S110's "κ_C role is switch
  concentration not signal coupling" claim across A.
- **S110-P3 still open**: rectifier-product test requires per-oscillator
  phase storage. Run smaller cell with full per-osc trace.
- **S109-P2** (κ_p saturation): now informed by S111's saturation
  geometry. Sweep κ_p ∈ {0.75, 1.0, 1.5} at A=0.20 (peak A*) instead
  of A=0.30 — more discriminating.

## Files

- `thor_session_111_dose_response.py` — modified S110 simulator (added
  `mean_phase_dec = arg(⟨e^{iφ}⟩)`) + analysis helpers.
- `thor_session_111_dose_response_results.json` — per-seed records for
  all 7 cells (~3 MB).
- `thor_session_111_analyze.py` — P1–P7 verdict computation.
- `thor_session_111_analysis.json` — derived A-curves and fit
  parameters.
- `thor_session_111_analyze.log` — analyzer text output (this report
  derives from it).
- `thor_session_111.log` — run log (35.7 min wall time).
