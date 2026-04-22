#!/usr/bin/env python3
"""S110 deeper analysis:

  P1 lock-ratio test
  P2 gate-instantaneous test
  P3 nokC mechanism control
  P4 null cell flatness
  P5 switch-event clustering
  P6 matched-filter law from first principles:
      Predict |⟨z_st⟩| from switch-event signal-phase distribution
  P7 lock_mod_amp_at_fs predicts √ρ_sig

Reads thor_session_110_signal_locked_results.json,
emits thor_session_110_analysis.json + console summary.
"""
import json
import sys
import numpy as np

sys.stdout.reconfigure(line_buffering=True)


def load(path='thor_session_110_signal_locked_results.json'):
    with open(path) as f:
        return json.load(f)


def predicted_st_mu_from_switches(switch_all_per_bin, switch_up_per_bin,
                                   switch_dn_per_bin, bin_centers):
    """First-principles ST matched-filter prediction from binned switches.

    The switch-timing matched filter is:
        I_st = Σ_k direction_k · sin(2πf_s t_k)
        Q_st = Σ_k direction_k · cos(2πf_s t_k)
    where direction_k = sign of C_mean at the crossing.

    If switch events binned by signal phase have separate up/down counts,
    we can build the matched-filter sums analytically by treating each bin's
    contribution as (up_count − dn_count) · {sin, cos}(bin_center) (since
    "up" sign at the C-mean threshold crossing maps to direction +1 in
    switch_timing_IQ, and down to -1).

    Returns (I_pred, Q_pred, |z_pred|, arg_deg).
    """
    bc = np.array(bin_centers)
    up = np.array(switch_up_per_bin)
    dn = np.array(switch_dn_per_bin)
    net = up - dn
    I = float(np.sum(net * np.sin(bc)))
    Q = float(np.sum(net * np.cos(bc)))
    return I, Q, float(np.sqrt(I*I + Q*Q)), float(np.degrees(np.arctan2(Q, I)))


def per_seed_first_principles(seed_record):
    """Per-seed P6 prediction vs measurement comparison.

    Returns dict including z_pred (from binned switches), z_meas (=⟨z_st⟩
    over chunks), and their ratio.
    """
    bc = (np.linspace(0, 2*np.pi, 13)[:-1] + np.pi/12).tolist()
    up = seed_record['switch_up_per_bin']
    dn = seed_record['switch_dn_per_bin']
    all_b = seed_record['switch_all_per_bin']
    Ip, Qp, mod_pred, arg_pred = predicted_st_mu_from_switches(
        all_b, up, dn, bc)

    # Measured
    z_st = np.array([complex(z[0], z[1]) for z in seed_record['z_st']])
    n_sw_chunks = np.sum(seed_record['n_sw_chunks'])
    # ⟨z_st⟩ over chunks gives μ in I_st = ⟨I_st_chunk⟩.
    # Each chunk's I_st was computed as I_st = sum over events in chunk of
    #   direction · sin(2πf_s · t_event)
    # so summed across chunks: total over all events = I_st_chunk[0] + ... = N_chunks · ⟨I_st⟩
    # First-principles prediction sums over ALL events at once → matches
    #   Σ_chunks(I_st_chunk) = N_chunks · I_st_mean
    # So I_pred should match Σ_chunks(I_st_chunk) directly.
    I_meas_total = float(np.sum(z_st.real))
    Q_meas_total = float(np.sum(z_st.imag))
    mod_meas_total = float(np.sqrt(I_meas_total**2 + Q_meas_total**2))
    arg_meas_total = float(np.degrees(np.arctan2(Q_meas_total, I_meas_total)))

    return {
        'I_pred_from_bins': Ip, 'Q_pred_from_bins': Qp,
        'mod_pred_from_bins': mod_pred, 'arg_pred_from_bins_deg': arg_pred,
        'I_meas_total_chunks': I_meas_total,
        'Q_meas_total_chunks': Q_meas_total,
        'mod_meas_total_chunks': mod_meas_total,
        'arg_meas_total_deg': arg_meas_total,
        'mod_ratio_pred_over_meas':
            (mod_pred / mod_meas_total) if mod_meas_total > 1e-9 else 0.0,
        'angle_diff_deg': float(((arg_pred - arg_meas_total + 180) % 360) - 180),
        'n_switches_total': int(np.sum(all_b)),
    }


def cell_summary(cell_dict, label, verbose=True):
    summary = cell_dict['summary']
    per_seed = cell_dict['per_seed']

    p_att = np.array([s['gate_cond']['P_lock_given_attractive']
                      for s in per_seed])
    p_rep = np.array([s['gate_cond']['P_lock_given_repulsive']
                      for s in per_seed])
    ratios = np.array([a/r for a, r in zip(p_att, p_rep) if r > 1e-12])
    lock_ratio_mean = float(ratios.mean()) if ratios.size > 0 else float('inf')
    lock_ratio_se = float(ratios.std()/np.sqrt(len(ratios))) if ratios.size > 1 else float('nan')

    # Lock per bin
    lock_per_bin = np.array(summary['lock_per_bin_mean'])
    lock_per_bin_std = np.array(summary['lock_per_bin_std'])
    lpb_max = float(lock_per_bin.max())
    lpb_min = float(lock_per_bin.min())
    lpb_swing = lpb_max - lpb_min
    lpb_mean = float(lock_per_bin.mean())
    # Sinusoid fit: project onto sin/cos
    bc = np.array(summary['bin_centers'])
    A_proj = float(np.mean(lock_per_bin * np.sin(bc)) * 2)
    B_proj = float(np.mean(lock_per_bin * np.cos(bc)) * 2)
    sin_amp = float(np.sqrt(A_proj**2 + B_proj**2))
    sin_arg_deg = float(np.degrees(np.arctan2(B_proj, A_proj)))
    sin_amp_over_mean = sin_amp / lpb_mean if lpb_mean > 1e-9 else 0.0

    # Switches per bin
    sw_all = np.array(summary['switch_all_per_bin_mean'])
    sw_up = np.array(summary['switch_up_per_bin_mean'])
    sw_dn = np.array(summary['switch_dn_per_bin_mean'])
    sw_net = sw_up - sw_dn

    # P6: first-principles matched-filter prediction per seed
    fp_records = [per_seed_first_principles(s) for s in per_seed]
    pred_mods = np.array([r['mod_pred_from_bins'] for r in fp_records])
    meas_mods = np.array([r['mod_meas_total_chunks'] for r in fp_records])
    angle_diffs = np.array([r['angle_diff_deg'] for r in fp_records])
    n_sw_per_seed = np.array([r['n_switches_total'] for r in fp_records])

    # Per-seed ρ_sig from measurement: ρ_sig = |⟨z_st⟩|² / ⟨N_sw⟩
    # mod_meas_total / N_chunks = |⟨z_st⟩|, then ⟨N_sw⟩ = total / N_chunks
    n_chunks = len(per_seed[0]['z_st'])
    rho_sig_seed = []
    for s in per_seed:
        z_st = np.array([complex(z[0], z[1]) for z in s['z_st']])
        mu_z = z_st.mean()
        n_mean = float(np.mean(s['n_sw_chunks']))
        rho_sig_seed.append(abs(mu_z)**2 / n_mean if n_mean > 0 else 0.0)
    rho_sig_seed = np.array(rho_sig_seed)

    # P7: mod_amp_at_fs vs sqrt(rho_sig)
    mod_amp_seed = np.array([s['mod_amp_at_fs'] for s in per_seed])
    sq_rho = np.sqrt(rho_sig_seed)
    if mod_amp_seed.std() > 0 and sq_rho.std() > 0:
        corr_mod_rho = float(np.corrcoef(mod_amp_seed, sq_rho)[0, 1])
    else:
        corr_mod_rho = float('nan')

    # Switch clustering metric: max-bin / opposite-bin
    if sw_all.sum() > 0:
        sw_max_idx = int(np.argmax(sw_all))
        opp_idx = (sw_max_idx + 6) % 12
        switch_max = float(sw_all[sw_max_idx])
        switch_opp = float(sw_all[opp_idx])
        switch_clust = switch_max / switch_opp if switch_opp > 0 else float('inf')
    else:
        switch_clust = float('nan')

    if verbose:
        print(f"\n=== {label} ===")
        print(f"  κ_p={cell_dict['kappa_phase']}  κ_C={cell_dict['kappa_C']}  "
              f"ω_spread={cell_dict['omega_spread']}  A={cell_dict['signal_amp']}  "
              f"n_seeds={len(per_seed)}")
        print(f"  P(L|att)={summary['P_lock_given_att_mean']:.3f} ± "
              f"{summary['P_lock_given_att_std']/np.sqrt(len(per_seed)):.4f}")
        print(f"  P(L|rep)={summary['P_lock_given_rep_mean']:.3f} ± "
              f"{summary['P_lock_given_rep_std']/np.sqrt(len(per_seed)):.4f}")
        print(f"  lock_ratio per-seed mean: {lock_ratio_mean:.2f} ± {lock_ratio_se:.2f}")
        print(f"  lock_per_bin range: {lpb_min:.3f} → {lpb_max:.3f}  "
              f"(mean {lpb_mean:.3f}, swing {lpb_swing:.3f})")
        print(f"  sin-fit amplitude: {sin_amp:.3f} (= {sin_amp_over_mean:.2f} × mean), "
              f"phase {sin_arg_deg:.1f}°")
        print(f"  mod_amp_at_fs (per seed mean): {summary['mod_amp_at_fs_mean']:.4f} ± "
              f"{summary['mod_amp_at_fs_std']/np.sqrt(len(per_seed)):.5f}")
        print(f"  cross-seed R_angle (mod): {summary['cross_seed_R_angle_mod']:.3f}")
        print(f"  switch clustering max/opp: {switch_clust:.2f}  "
              f"(max bin: {sw_all.max():.0f}, opp: {sw_all[opp_idx]:.0f})")
        print(f"  switches/seed total: {n_sw_per_seed.mean():.0f} ± {n_sw_per_seed.std()/np.sqrt(len(per_seed)):.1f}")
        print(f"  P6 first-principles vs measured |z_st_total|:")
        print(f"     pred (per seed mean): {pred_mods.mean():.2f}  "
              f"meas (per seed mean): {meas_mods.mean():.2f}  "
              f"ratio: {(pred_mods.mean()/meas_mods.mean()) if meas_mods.mean() > 1e-9 else float('nan'):.3f}")
        print(f"     angle diff |pred − meas| per seed mean: "
              f"{np.abs(angle_diffs).mean():.1f}° ± {np.abs(angle_diffs).std()/np.sqrt(len(per_seed)):.1f}°")
        print(f"  P7 corr(mod_amp_at_fs, √ρ_sig) across seeds: {corr_mod_rho:.3f}")
        print(f"  ρ_sig_st: {rho_sig_seed.mean():.4f} ± {rho_sig_seed.std()/np.sqrt(len(per_seed)):.5f}")

    return {
        'label': label,
        'kappa_phase': cell_dict['kappa_phase'],
        'kappa_C': cell_dict['kappa_C'],
        'omega_spread': cell_dict['omega_spread'],
        'signal_amp': cell_dict['signal_amp'],
        'n_seeds': len(per_seed),
        'P_lock_given_attractive_mean': summary['P_lock_given_att_mean'],
        'P_lock_given_repulsive_mean': summary['P_lock_given_rep_mean'],
        'lock_ratio_per_seed_mean': lock_ratio_mean,
        'lock_ratio_per_seed_se':   lock_ratio_se,
        'lock_per_bin_mean': lock_per_bin.tolist(),
        'lock_per_bin_std': lock_per_bin_std.tolist(),
        'lock_per_bin_max': lpb_max,
        'lock_per_bin_min': lpb_min,
        'lock_per_bin_swing': lpb_swing,
        'lock_per_bin_avg': lpb_mean,
        'lock_sin_fit_amp': sin_amp,
        'lock_sin_fit_amp_over_mean': sin_amp_over_mean,
        'lock_sin_fit_arg_deg': sin_arg_deg,
        'mod_amp_at_fs_mean': summary['mod_amp_at_fs_mean'],
        'mod_amp_at_fs_std':  summary['mod_amp_at_fs_std'],
        'cross_seed_R_angle_mod': summary['cross_seed_R_angle_mod'],
        'switch_clustering_max_over_opp': switch_clust,
        'switches_per_seed_total_mean': float(n_sw_per_seed.mean()),
        'first_principles_pred_mod_mean': float(pred_mods.mean()),
        'first_principles_meas_mod_mean': float(meas_mods.mean()),
        'first_principles_pred_over_meas': float(pred_mods.mean()/meas_mods.mean()) if meas_mods.mean() > 1e-9 else float('nan'),
        'first_principles_angle_diff_abs_mean_deg': float(np.abs(angle_diffs).mean()),
        'P7_corr_mod_amp_with_sqrt_rho_sig': corr_mod_rho,
        'rho_sig_st_seed_mean': float(rho_sig_seed.mean()),
        'switch_all_per_bin_mean': sw_all.tolist(),
        'switch_up_per_bin_mean': sw_up.tolist(),
        'switch_dn_per_bin_mean': sw_dn.tolist(),
        'switch_net_per_bin_mean': sw_net.tolist(),
        'bin_centers_rad': summary['bin_centers'],
    }


def main():
    data = load()
    cells = data['cells']
    out = {'meta': data['meta'], 'analysis': {}}
    for label in ['ridge', 'nokC', 'null']:
        if label not in cells:
            print(f"  (cell {label} not found in results)")
            continue
        out['analysis'][label] = cell_summary(cells[label], label)

    # Cross-cell summary
    print("\n=== CROSS-CELL SUMMARY ===")
    for label in ['ridge', 'nokC', 'null']:
        if label not in out['analysis']:
            continue
        s = out['analysis'][label]
        print(f"  {label:6s}: lock_ratio={s['lock_ratio_per_seed_mean']:6.2f}  "
              f"lock_sin_amp/mean={s['lock_sin_fit_amp_over_mean']:.3f}  "
              f"mod_amp_fs={s['mod_amp_at_fs_mean']:.4f}  "
              f"R_angle_mod={s['cross_seed_R_angle_mod']:.3f}  "
              f"sw_clust={s['switch_clustering_max_over_opp']:5.2f}  "
              f"FP_ratio={s['first_principles_pred_over_meas']:.3f}  "
              f"|angle_diff|={s['first_principles_angle_diff_abs_mean_deg']:.1f}°  "
              f"ρ_sig={s['rho_sig_st_seed_mean']:.4f}")

    with open('thor_session_110_analysis.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print("\nWrote thor_session_110_analysis.json")


if __name__ == '__main__':
    main()
