#!/usr/bin/env python3
"""S111 analyzer: dose-response laws across A.

Pulls thor_session_111_dose_response_results.json and computes:
  P1 mod_amp_at_fs_lock vs A: linear-fit slope and r² over low-A subset.
  P2 saturation: fractional deviation of mod_amp_at_fs_lock from
                 best-fit-low-A line at A=0.40, 0.50.
  P3 ρ_sig vs A: log-log slope (exponent) over low-A subset.
  P4 R_inst² law: γ = ρ_sig / R_inst² per A; check A-invariance.
  P5 first-principles |z_st|: ratio across A (sanity-check identity).
  P6 detection floor: z_det = √(N_chunks · ρ_sig / σ_n²_st) per A;
                      A_min for z_det = 5σ.
  P7 lock_frac vs A: monotonicity, saturation behavior.

Plus cross-quantity correlations and a clean summary table.
"""
import json
import sys
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

with open('thor_session_111_dose_response_results.json') as f:
    data = json.load(f)

cells = data['cells']
common = data['meta']['common_params']
A_VALUES = common['A_values']
N_CHUNKS = common['n_chunks']
N_SEEDS = common['n_seeds']

labels = sorted(cells.keys(), key=lambda k: cells[k]['signal_amp'])

A = np.array([cells[l]['signal_amp'] for l in labels])
mod_lock = np.array([cells[l]['summary']['mod_amp_at_fs_lock_mean'] for l in labels])
mod_lock_std = np.array([cells[l]['summary']['mod_amp_at_fs_lock_std'] for l in labels])
mod_kura = np.array([cells[l]['summary']['mod_amp_at_fs_kura_mean'] for l in labels])
mod_kura_std = np.array([cells[l]['summary']['mod_amp_at_fs_kura_std'] for l in labels])
mod_cosphi = np.array([cells[l]['summary']['mod_amp_at_fs_cosphi_mean'] for l in labels])
R_ang_lock = np.array([cells[l]['summary']['cross_seed_R_angle_lock'] for l in labels])
R_ang_kura = np.array([cells[l]['summary']['cross_seed_R_angle_kura'] for l in labels])
R_ang_cosphi = np.array([cells[l]['summary']['cross_seed_R_angle_cosphi'] for l in labels])
rho_sig = np.array([cells[l]['summary']['rho_sig_st_mean'] for l in labels])
rho_sig_std = np.array([cells[l]['summary']['rho_sig_st_std'] for l in labels])
R_kura_mean = np.array([cells[l]['summary']['kura_mean_mean'] for l in labels])
lock_frac = np.array([cells[l]['summary']['lock_frac_global_mean'] for l in labels])
sigma_n_st = np.array([cells[l]['summary']['st_sigma_n_mean'] for l in labels])
st_R_coh = np.array([cells[l]['summary']['st_R_coh_mean'] for l in labels])
raw_R_coh = np.array([cells[l]['summary']['raw_R_coh_mean'] for l in labels])
n_sw_total = np.array([cells[l]['summary']['n_sw_total_mean'] for l in labels])
fp_ratio = np.array([cells[l]['summary']['fp_ratio_mean'] for l in labels])
P_att = np.array([cells[l]['summary']['P_lock_given_att_mean'] for l in labels])
P_rep = np.array([cells[l]['summary']['P_lock_given_rep_mean'] for l in labels])
st_mu = np.array([cells[l]['summary']['st_mu_mean'] for l in labels])

print("="*84)
print(" S111 Dose-Response Summary")
print("="*84)
print(f"{'A':>5} {'mod_lock':>9} {'mod_kura':>10} {'mod_cosφ':>10} "
      f"{'R_kura':>8} {'lock%':>7} {'ρ_sig':>8} {'ST_R':>7} {'RAW_R':>7} {'<Nsw>':>7}")
for i, a in enumerate(A):
    print(f"{a:>5.2f} {mod_lock[i]:>9.4f} {mod_kura[i]:>10.5f} {mod_cosphi[i]:>10.5f} "
          f"{R_kura_mean[i]:>8.3f} {lock_frac[i]:>7.3f} {rho_sig[i]:>8.4f} "
          f"{st_R_coh[i]:>7.3f} {raw_R_coh[i]:>7.3f} {n_sw_total[i]:>7.0f}")

# --- P1, P2: mod_lock vs A linearity & saturation
print("\n" + "="*84)
print(" P1, P2: mod_amp_at_fs_lock(A) — linearity and saturation")
print("="*84)
# A=0 sets baseline noise level; subtract from all
mod_lock_dm = mod_lock - mod_lock[0]   # null-corrected
print(f" Null (A=0) baseline mod_amp_at_fs_lock: {mod_lock[0]:.4f} (intrinsic noise floor)")
print(f" Cross-seed R_angle at null: {R_ang_lock[0]:.3f}  (low ⇒ random per-seed phase)")

# Low-A linear fit: A in (0, 0.05, 0.10, 0.20]
def linfit(x, y, mask):
    x_, y_ = x[mask], y[mask]
    if len(x_) < 2:
        return None
    p = np.polyfit(x_, y_, 1)
    yhat = np.polyval(p, x_)
    ss_res = np.sum((y_ - yhat)**2)
    ss_tot = np.sum((y_ - y_.mean())**2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return p[0], p[1], r2

low_mask = (A >= 0.0) & (A <= 0.20)
fit = linfit(A, mod_lock, low_mask)
if fit:
    sl, ic, r2 = fit
    print(f" Low-A linear fit (A ≤ 0.20, n={low_mask.sum()}): slope={sl:.4f}/A  intercept={ic:.4f}  r²={r2:.4f}")
    # Saturation deficit at high A
    for a_test in (0.30, 0.40, 0.50):
        if a_test in A.tolist():
            i = list(A).index(a_test)
            pred = sl * a_test + ic
            actual = mod_lock[i]
            deficit = (pred - actual) / pred if pred > 0 else 0.0
            print(f"  A={a_test:.2f}: pred={pred:.4f}  actual={actual:.4f}  "
                  f"deficit={deficit*100:+.1f}%")

# --- P3: ρ_sig vs A power law
print("\n" + "="*84)
print(" P3: ρ_sig(A) power-law in low-A")
print("="*84)
# Use A > 0 only for log-log
valid = (A > 0) & (rho_sig > 0)
if valid.sum() >= 2:
    log_A = np.log(A[valid])
    log_rho = np.log(rho_sig[valid])
    p_all = np.polyfit(log_A, log_rho, 1)
    print(f" Full A>0 log-log fit (n={valid.sum()}):  exponent={p_all[0]:.3f}  "
          f"prefactor={np.exp(p_all[1]):.4f}")
    # Low-A subset
    lowll_mask = (A > 0) & (A <= 0.20) & (rho_sig > 0)
    if lowll_mask.sum() >= 2:
        p_low = np.polyfit(np.log(A[lowll_mask]), np.log(rho_sig[lowll_mask]), 1)
        print(f" Low-A (A ≤ 0.20) log-log fit (n={lowll_mask.sum()}): exponent={p_low[0]:.3f}  "
              f"prefactor={np.exp(p_low[1]):.4f}")
        print(f"   ↳ matched-filter prediction: exponent ≈ 2.0 (ρ_sig ∝ A²)")
    # Print per-cell prediction quality
    print("\n  A    | meas ρ_sig | A² fit (slope at A=0.10) | residual frac")
    if (A == 0.10).any():
        i10 = list(A).index(0.10)
        gamma_at_010 = rho_sig[i10] / (0.10**2)
        for i, a in enumerate(A):
            if a > 0:
                pred_q = gamma_at_010 * a**2
                resid = (rho_sig[i] - pred_q) / pred_q if pred_q > 0 else 0.0
                print(f"  {a:.2f} | {rho_sig[i]:>9.4f}  | {pred_q:>9.4f}              | {resid*100:+.1f}%")

# --- P4: R_inst² law
print("\n" + "="*84)
print(" P4: ρ_sig = γ · R_inst² ?  (S109 within-ridge γ ≈ 0.4)")
print("="*84)
print(" Note: 'R_inst' here is taken as ⟨R_kura⟩ — time-average. The S109")
print(" claim was on the per-seed mean, here we use cell-mean.")
gamma = np.where(R_kura_mean > 0, rho_sig / R_kura_mean**2, 0.0)
for i, a in enumerate(A):
    print(f"  A={a:.2f}  R_kura={R_kura_mean[i]:.3f}  R²={R_kura_mean[i]**2:.4f}  "
          f"ρ_sig={rho_sig[i]:.4f}  γ={gamma[i]:.4f}")

# Are γ_A invariant?
gamma_pos = gamma[A > 0]
if len(gamma_pos) > 1:
    print(f"\n γ across A>0 cells: mean={gamma_pos.mean():.3f}  std={gamma_pos.std():.3f}  "
          f"CV={gamma_pos.std()/gamma_pos.mean()*100:.1f}%")

# --- P5: first-principles ratio across A
print("\n" + "="*84)
print(" P5: first-principles |z_st| identity check across A")
print("="*84)
print(" (This is the sum-form identity, not the binned approximation;")
print("  ratio should be ≈ 1.0 modulo float precision.)")
for i, a in enumerate(A):
    print(f"  A={a:.2f}  fp_ratio = {fp_ratio[i]:.5f}")

# --- P6: detection floor
print("\n" + "="*84)
print(" P6: detection floor — z_det = √(N_chunks · ρ_sig / σ_n_st²)")
print("="*84)
# z_det formula: in per-chunk, mean signal magnitude = √(ρ_sig · ⟨N_sw⟩) and
# noise per chunk has SD σ_n_st (in the same z_st units, summed over events).
# After averaging N_chunks, SE of mean = σ_n_st / √N_chunks.
# z_det = |⟨z_st⟩| / SE = √N_chunks · |⟨z_st⟩| / σ_n_st.
# Use measured st_mu for |⟨z_st⟩| direct.
# Actually z_det is just √(N_chunks * R_coh / (1 - R_coh)).
z_det = np.where(st_R_coh < 1,
                  np.sqrt(N_CHUNKS * st_R_coh / (1 - st_R_coh)),
                  np.inf)
print(f" Per-cell ST z_det (over {N_CHUNKS} chunks, σ_n calibration):")
for i, a in enumerate(A):
    print(f"  A={a:.2f}: ST R_coh={st_R_coh[i]:.3f}  σ_n_st={sigma_n_st[i]:.2f}  "
          f"|⟨z_st⟩|={st_mu[i]:.3f}  z_det={z_det[i]:.2f}")
# A_min for z_det = 5
above5 = z_det >= 5
if above5.any():
    for i, a in enumerate(A):
        if z_det[i] >= 5:
            print(f"  → first A with z_det ≥ 5: A={a:.2f} (z_det={z_det[i]:.1f})")
            break

# --- P7: lock_frac and R_kura vs A
print("\n" + "="*84)
print(" P7: lock_frac_global vs R_kura_mean vs A")
print("="*84)
for i, a in enumerate(A):
    print(f"  A={a:.2f}  R_kura_mean={R_kura_mean[i]:.3f}  lock_frac_global={lock_frac[i]:.3f}  "
          f"P(L|att)={P_att[i]:.3f}  P(L|rep)={P_rep[i]:.3f}")

# --- Cross-checks: is mod_amp_at_fs_lock predicted by mod_amp_at_fs_kura?
print("\n" + "="*84)
print(" Bonus: mod_lock vs mod_kura (lock-indicator vs continuous R_kura)")
print("="*84)
print(" The ratio (mod_lock / mod_kura) reveals whether the lock-indicator")
print(" overpicks or underpicks the modulation captured by R_kura(t).")
for i, a in enumerate(A):
    if mod_kura[i] > 1e-6:
        r = mod_lock[i] / mod_kura[i]
        print(f"  A={a:.2f}  mod_lock={mod_lock[i]:.4f}  mod_kura={mod_kura[i]:.5f}  "
              f"ratio={r:.2f}")

# --- Bonus: R_ang stats
print("\n" + "="*84)
print(" Cross-seed R_angle (signal-detection coherence across seeds)")
print("="*84)
print(f"{'A':>5} {'R_ang_lock':>11} {'R_ang_kura':>11} {'R_ang_cosφ':>11}")
for i, a in enumerate(A):
    print(f"{a:>5.2f} {R_ang_lock[i]:>11.3f} {R_ang_kura[i]:>11.3f} {R_ang_cosphi[i]:>11.3f}")

# --- Save analysis summary
analysis = {
    'A_values': A.tolist(),
    'mod_amp_at_fs_lock': mod_lock.tolist(),
    'mod_amp_at_fs_lock_std': mod_lock_std.tolist(),
    'mod_amp_at_fs_kura': mod_kura.tolist(),
    'mod_amp_at_fs_cosphi': mod_cosphi.tolist(),
    'R_kura_mean': R_kura_mean.tolist(),
    'R_ang_lock': R_ang_lock.tolist(),
    'R_ang_kura': R_ang_kura.tolist(),
    'R_ang_cosphi': R_ang_cosphi.tolist(),
    'rho_sig': rho_sig.tolist(),
    'rho_sig_std': rho_sig_std.tolist(),
    'st_R_coh': st_R_coh.tolist(),
    'raw_R_coh': raw_R_coh.tolist(),
    'sigma_n_st': sigma_n_st.tolist(),
    'st_mu': st_mu.tolist(),
    'lock_frac_global': lock_frac.tolist(),
    'P_att': P_att.tolist(),
    'P_rep': P_rep.tolist(),
    'n_sw_total': n_sw_total.tolist(),
    'fp_ratio': fp_ratio.tolist(),
    'z_det': z_det.tolist(),
    'gamma_R_inst2': gamma.tolist(),
}

# fits
if low_mask.sum() >= 2:
    sl, ic, r2 = linfit(A, mod_lock, low_mask)
    analysis['low_A_mod_lock_fit'] = {
        'A_max': 0.20, 'slope_per_A': sl, 'intercept': ic, 'r2': r2}
if valid.sum() >= 2 and lowll_mask.sum() >= 2:
    p_low = np.polyfit(np.log(A[lowll_mask]), np.log(rho_sig[lowll_mask]), 1)
    p_all = np.polyfit(np.log(A[valid]), np.log(rho_sig[valid]), 1)
    analysis['rho_sig_loglog_low'] = {
        'A_max': 0.20, 'exponent': float(p_low[0]),
        'prefactor': float(np.exp(p_low[1]))}
    analysis['rho_sig_loglog_all'] = {
        'exponent': float(p_all[0]),
        'prefactor': float(np.exp(p_all[1]))}

with open('thor_session_111_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2, default=float)
print("\nAnalysis saved → thor_session_111_analysis.json")
