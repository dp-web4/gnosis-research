#!/usr/bin/env python3
"""Fast smoke test: 4 seeds, the κ_C=0.30 (A=0, A=0.40) pair only.
Produces a results JSON in the SAME schema as the full run (to a SEPARATE
path — never the live results file) and exercises the core functions of all
three analyzers end-to-end, so any runtime bug surfaces in ~3 min instead of
after the 140-min run."""
import json

import thor_session_117_class_detector as M
import thor_session_117_analyze as AZ
import thor_session_117_detector_ladder as DL
import thor_session_117_lda_ceiling as LC

KAPPA_P = 0.30
OMEGA_STD = 0.07
cells_def = [('kc030_A000', 0.30, 0.0), ('kc030_A040', 0.30, 0.40)]

cell_results = {}
for label, kc, A in cells_def:
    seed_base = (117_000_000 + int(round(kc * 100)) * 100_000
                 + int(round(A * 100)) * 1000 + (900_000 if A == 0.0 else 0))
    recs, ovec = M.run_cell(label, KAPPA_P, kc, OMEGA_STD, A, seed_base,
                            n_chunks=M.N_CHUNKS, n_seeds=4)
    summ = M.summarize_cell(recs, A, KAPPA_P, kc, OMEGA_STD)
    cell_results[label] = {
        'kappa_phase': KAPPA_P, 'kappa_C': kc, 'omega_std': OMEGA_STD,
        'omega_vec': ovec, 'signal_amp': A, 'seed_base': seed_base,
        'summary': summ, 'per_seed': M.pack_per_seed(recs),
    }

res = {'meta': {'session': 117, 'kc_vals': [0.30], 'A_vals': [0.0, 0.40],
                'cells_def': cells_def, 'note': 'SMOKE TEST 4 seeds'},
       'cells': cell_results}
SMOKE = 'thor_session_117_smoke_results.json'
with open(SMOKE, 'w') as f:
    json.dump(res, f, indent=2, default=float)
print('\n[smoke] results written:', SMOKE)

# ---- exercise analyzer cores directly on the smoke data ----
cn = cell_results['kc030_A000']['per_seed']
cs = cell_results['kc030_A040']['per_seed']

# base analyzer
phi = AZ.ensemble_phi(cs)
nfloor = AZ.class_null_floor(cn)
dv_n = AZ.detector_vec(cn, phi, nfloor)
dv_s = AZ.detector_vec(cs, phi, nfloor)
print('[smoke] base analyzer detectors:', sorted(dv_s.keys()))
for d in ['T_coh', 'T_incoh', 'T_white', 'T_wedge']:
    if d in dv_n:
        print(f'   AUC {d:10s} = {AZ.auc(dv_n[d], dv_s[d]):.3f}')

# detector ladder
mu_sig, mu_null = DL.mu_array(cs), DL.mu_array(cn)
nsw_sig, nsw_null = DL.nsw_array(cs), DL.nsw_array(cn)
det, sig2, phih = DL.build_detectors(mu_sig, nsw_sig, mu_null, nsw_null)
print('[smoke] ladder detectors:', sorted(det.keys()))
for d in ['T_coh', 'T_white', 'T_cw_loo', 'T_wedge_loo', 'T_cw_oracle']:
    print(f'   AUC {d:12s} = {DL.auc(*det[d]):.3f}')

# LDA ceiling
X0, X1 = LC.phasor_matrix(cn), LC.phasor_matrix(cs)
cw_n, cw_s = LC.diag_cw_loo_auc(X0, X1)
s0, s1 = LC.lda_loo_auc(X0, X1)
delta, auc_full = LC.mahalanobis_full(X0, X1)
print(f'[smoke] LDA: cw_loo AUC={LC.auc(cw_n, cw_s):.3f}  '
      f'lda_loo AUC={LC.auc(s0, s1):.3f}  '
      f'Δmaha={delta:.2f}  lda_full_gauss AUC={auc_full:.3f}')
print('\n[smoke] ALL THREE ANALYZERS RAN CLEAN ON REAL-SCHEMA DATA.')
