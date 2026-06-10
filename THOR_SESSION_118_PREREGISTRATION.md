# S118 Pre-Registration — Detection-Floor Prediction (recorded before low-A data)

Written while the S118 detection-edge run (15 cells, A ∈ {0.03,0.06,0.10,0.16,0.24}
× κ_C ∈ {0.30,0.50,0.70}, 32 seeds × 25 chunks) is still computing. These
predictions are derived from the **S117 A=0.40 anchors only** — the low-A cells
that test them did not exist when this was written.

## Anchor measurement (S117, A=0.40, per-seed T_coh = |Σ_k μ_k|²)

Per-seed total phasor m = mean over 32 signal seeds; σ_n = per-component null std.

| κ_C  | \|m_tot\| | σ_n   | ρ_seed=\|m\|²/2σ_n² | d′(T_coh) | AUC(T_coh) | AUC(N_sw) |
|------|-----------|-------|---------------------|-----------|------------|-----------|
| 0.30 | 156.3     | 13.77 | 64.4                | **9.46**  | 1.000      | 0.000     |
| 0.50 | 62.5      | 6.98  | 40.1                | 3.11      | 1.000      | 1.000     |
| 0.70 | 33.4      | 4.91  | 23.1                | 3.04      | 1.000      | 1.000     |

The ridge coherent channel is ~3× stronger in d′ than the over-coupled cells,
even though all three read AUC=1.0 at A=0.40 (saturation hides it). N_sw is
**anti-informative at the ridge** (AUC=0.000: signal *reduces* switches) and
**perfect in the over-coupled regime** (AUC=1.0: signal-rescue raises N_sw).

## Predicted detection floors (coherent channel only)

Model: |m(A)| = |m(0.40)|·(A/0.40)^q, σ_n ≈ A-independent (noise floor), so the
Gaussianised d′ ∝ A^{2q}. Floor = A where d′ crosses 1.81 (≈ AUC 0.90 if
Gaussian). S117 showed the energy statistics are heavy-tailed, so AUC stays
**above** Φ(d′/√2) — these predicted floors are therefore an **UPPER bound** on
the true (measured) floor.

| κ_C  | floor @ q=1.21 (S111) | floor @ q=1.0 |
|------|------------------------|----------------|
| 0.30 | 0.202                  | 0.175          |
| 0.50 | 0.320                  | 0.305          |
| 0.70 | 0.323                  | 0.309          |

## Pre-registered claims

- **P-A (H1, coherent-only): ridge floor ≪ over-coupled floor.** Predict
  A_min(κ_C=0.30) ≈ 0.15–0.20 vs A_min(κ_C=0.50/0.70) ≈ 0.30–0.32 for the
  best *coherent/whitened* detector. Inversion vs the A=0.40 picture (where
  over-coupled was "easiest" via N_sw).
- **P-B (the N_sw question, settles H3/H4): does the rate channel rescue the
  over-coupled floor?** N_sw is AUC=1.0 at κ_C=0.70 A=0.40 but only because the
  signal-rescue ΔN_sw is large there. If ΔN_sw(A) is higher-order in A (rescue
  vanishes faster than the coherent channel as A→0), then the **realizable**
  floor (best of all detectors incl. N_sw / Fusion) still inverts — over-coupled
  stays hardest near threshold. If ΔN_sw persists to low A, κ_C=0.70's realizable
  floor could drop below the ridge and H1 fails for the *realizable* ladder.
  **Prediction: rescue is higher-order; H1 holds for the realizable ladder too,
  but with a smaller margin than the coherent-only gap.**
- **P-C (measured < predicted): every measured floor lands below its tabulated
  upper bound**, because of the heavy-tailed-null AUC>Φ(d′/√2) effect (S117-P5).

## Design caveat noted pre-data

Predicted floors (0.18–0.32) sit at or above the top of the *dense* A-grid
(0.24). The over-coupled floors will be resolved only by the coarse 0.24→0.40
interpolation segment, so their numeric floor estimates are low-resolution. The
**qualitative inversion** (ridge much lower) should still be unambiguous. If the
over-coupled floor needs pinning down, a follow-up needs A ∈ {0.28, 0.32, 0.36}.
