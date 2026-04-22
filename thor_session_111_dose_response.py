#!/usr/bin/env python3
"""Thor Session #111: Dose-Response — How mod_amp_at_fs and ρ_sig Scale With A
================================================================================

Context (S110)
--------------
S110 established the 5-step mechanism chain at the ridge cell
(κ_p=0.30, κ_C=0.30, ratio 0.8, A=0.30):

  1. Signal modulates GATE: (C_mean + signal) ≷ threshold
  2. Gate flips sign of phase coupling κ_p (attractive ↔ repulsive)
  3. R_kura(t) becomes signal-phase locked (mod_amp ~0.12 at A=0.30)
  4. R_kura(t) couples back to C via cos(φ) in intrinsic drift
  5. κ_C concentrates C oscillators → switching clusters at signal-phase peaks

S110-P6 also confirmed the first-principles law: |⟨z_st⟩| equals the
discrete Fourier sum over signed switch density at f_s to within 1%.

Open questions S111 attacks
---------------------------
- S110-P4: does mod_amp_at_fs scale linearly with A in the small-A
  regime, and where does it saturate?
- S109/S111 corollary: does ρ_sig scale as A² (matched-filter law) or
  some other power? Saturation behavior?
- A-dependence of the matched-filter prediction (S110-P6 across A).
- Detection floor: at what A is ρ_sig indistinguishable from A=0?

Design
------
Single ridge cell (κ_p=0.30, κ_C=0.30, ratio 0.8) swept over
A ∈ {0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50}.

Per A: 10 seeds × 30 chunks × 40k steps + 10k warmup.

Modified simulator records (in addition to S110): mean_phase_dec =
arg(⟨e^{iφ}⟩) decimated every 10 steps. Useful for the S110-P3
rectifier test (cross-correlation of cos(⟨φ⟩(t)) and signal phase /
switch events) without per-oscillator phase storage.

Compute estimate: 7 cells × 10 seeds × 1.21M steps × 25µs/step ≈ 35 min.

Predictions (for verdict in analysis)
-------------------------------------
P1 (linearity of mod_amp_at_fs in small-A): for A ≤ 0.20, mod_amp_at_fs
   should be linear in A (small-signal coupling is first-order). Predict
   slope ≈ 0.12/0.30 ≈ 0.4 per unit A.
P2 (saturation onset): for A ≥ 0.30, mod_amp_at_fs should depart from
   linearity as the lock_per_bin shape approaches the binary toggle
   already observed in nokC. Predict ~25% saturation deficit at A=0.50.
P3 (ρ_sig power law): in low-A, ρ_sig ∝ A² (matched-filter / linear
   coupling chain → quadratic coherent power). Predict exponent
   2.0 ± 0.2 from log-log fit on A ∈ {0.10, 0.20, 0.30}.
P4 (R_inst² law): ρ_sig = γ · R_inst² with γ ≈ 0.4 (S109 within-ridge).
   Predict that γ is approximately A-invariant if R_inst itself absorbs
   the A-dependence; if not, γ should vary in a sign that reveals the
   missing factor.
P5 (matched-filter law across A): predicted/measured |z_st| ratio
   should stay within 1.05 across all A (already confirmed at A=0,
   0.30 in S110 to within 1.13).
P6 (detection floor): null cell (A=0) gives baseline ρ_sig and the
   z-detection scale. Threshold A such that z_det = 5σ should be
   ~0.04 from S110/S109 estimates. Concrete number from this run.
P7 (lock_frac vs A linearity): if R_inst is the smooth average and
   lock_frac is the time-fraction R_kura(t)>0.9, both should grow
   monotonically with A but lock_frac may saturate sooner (it is a
   binary indicator, hits ceiling as soon as gate-driven R_kura(t)
   reliably exceeds 0.9 in attractive half).
"""
import json
import sys
import time
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

from thor_session_93_phase_coherent import phase_coherent_IQ
from thor_session_95_switch_timing import switch_timing_IQ

C_THRESHOLD = 0.55
SIGNAL_FREQ = 0.003
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
T_CHUNK_S = CHUNK_STEPS * DT
N_SEEDS = 10
N_CHUNKS = 30
DEC_KURA = 10           # decimate joint state every 10 steps
N_BINS = 12             # signal-phase bins for lock-frac and switch density


def simulate_dose_response(N, noise_std, steps, seed,
                            kappa_phase=0.30, kappa_C=0.30,
                            omega_base=0.1, omega_spread=0.24,
                            phi_inverse=0.618, dt=0.1,
                            C_threshold=0.55,
                            signal_freq=0.003, signal_amp=0.0):
    """S110 simulator + decimated mean phase angle.

    Returns:
      C_mean_hist           (steps,)
      kura_dec              (n_dec,)        |⟨e^{iφ}⟩|
      mean_phase_dec        (n_dec,) rad    arg(⟨e^{iφ}⟩) ∈ [-π, π]
      gate_dec              (n_dec,) bool   gate-attractive at t
      C_mean_dec            (n_dec,)
      sig_dec               (n_dec,)        signal value at t
      sig_phase_dec         (n_dec,) rad    2πf_s·t·dt mod 2π
      switch_event_steps    (n_sw,) int     post-warmup step indices
      switch_dirs           (n_sw,) int     +1 up-crossing, -1 down
      kura_mean             float           time-average of kura_dec
    """
    np.random.seed(seed)
    C = np.clip(phi_inverse + np.random.normal(0, 0.05, N), 0.01, 0.99)
    phase = np.random.uniform(0, 2 * np.pi, N)
    omega = omega_base + np.random.uniform(-omega_spread, omega_spread, N)
    C_mean_hist = np.empty(steps)
    post_warm_len = max(0, steps - WARMUP)
    n_dec = post_warm_len // DEC_KURA + 1
    kura_dec = np.empty(n_dec)
    mean_phase_dec = np.empty(n_dec)
    gate_dec = np.empty(n_dec, dtype=bool)
    C_mean_dec = np.empty(n_dec)
    sig_dec = np.empty(n_dec)
    sig_phase_dec = np.empty(n_dec)
    d_idx = 0
    switch_steps = []
    switch_dirs = []
    prev_sign = None
    for t in range(steps):
        C_mean = np.mean(C)
        C_mean_hist[t] = C_mean
        signal = signal_amp * np.sin(2 * np.pi * signal_freq * t * dt)
        is_attractive = (C_mean + signal) < C_threshold
        sign = 1.0 if is_attractive else -1.0
        sin_diff = np.sin(phase[None, :] - phase[:, None])
        np.fill_diagonal(sin_diff, 0)
        dphase = omega + sign * kappa_phase * sin_diff.sum(axis=1) / (N - 1)
        phase = (phase + dt * dphase) % (2 * np.pi)
        R_func = 1 - C**2
        intrinsic = -R_func * (C - phi_inverse) * np.cos(phase)
        c_coupling = kappa_C * (C_mean - C) * R_func
        dC = intrinsic + c_coupling
        C = np.clip(C + dt * dC, 0, 1)
        if noise_std > 0:
            C = np.clip(C + np.random.normal(0, noise_std, N), 0, 1)
            phase = (phase + np.random.normal(0, noise_std, N)) % (2 * np.pi)

        post = t - WARMUP
        if post >= 0:
            if post % DEC_KURA == 0:
                z_sum = np.mean(np.exp(1j * phase))
                kura_dec[d_idx] = abs(z_sum)
                mean_phase_dec[d_idx] = float(np.angle(z_sum))
                gate_dec[d_idx] = bool(is_attractive)
                C_mean_dec[d_idx] = C_mean
                sig_dec[d_idx] = signal
                sig_phase_dec[d_idx] = (2.0 * np.pi * signal_freq * t * dt) % (2.0 * np.pi)
                d_idx += 1
            cur_sign = 1 if (C_mean_hist[t] - C_threshold) > 0 else -1
            if prev_sign is not None and cur_sign != prev_sign:
                switch_steps.append(post)
                switch_dirs.append(cur_sign)
            prev_sign = cur_sign
    kura_dec = kura_dec[:d_idx]
    mean_phase_dec = mean_phase_dec[:d_idx]
    gate_dec = gate_dec[:d_idx]
    C_mean_dec = C_mean_dec[:d_idx]
    sig_dec = sig_dec[:d_idx]
    sig_phase_dec = sig_phase_dec[:d_idx]
    return (C_mean_hist, kura_dec, mean_phase_dec, gate_dec, C_mean_dec,
            sig_dec, sig_phase_dec,
            np.array(switch_steps, dtype=int),
            np.array(switch_dirs, dtype=int),
            float(kura_dec.mean()) if d_idx > 0 else 0.0)


def per_seed_R_coh(z_arr):
    mu = z_arr.mean()
    dev = z_arr - mu
    sigma_n2 = float(np.mean(np.abs(dev)**2))
    mu2 = float(abs(mu)**2)
    return {
        'mu_abs': float(abs(mu)),
        'mu_arg_deg': float(np.degrees(np.angle(mu))),
        'sigma_n': float(np.sqrt(sigma_n2)),
        'R_coh': mu2 / (mu2 + sigma_n2) if (mu2 + sigma_n2) > 0 else 0.0,
    }


def signal_phase_binned_lock(kura_dec, sig_phase_dec, n_bins=12, R_thr=0.9):
    lock = (kura_dec > R_thr).astype(float)
    bin_edges = np.linspace(0.0, 2.0 * np.pi, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    lock_per_bin = np.zeros(n_bins)
    cnt_per_bin = np.zeros(n_bins, dtype=int)
    bidx = np.digitize(sig_phase_dec, bin_edges[1:-1])
    for b in range(n_bins):
        mask = bidx == b
        cnt_per_bin[b] = int(mask.sum())
        if mask.any():
            lock_per_bin[b] = float(lock[mask].mean())
    return lock_per_bin, cnt_per_bin, bin_centers


def gate_conditional_lock(kura_dec, gate_dec, R_thr=0.9):
    lock = kura_dec > R_thr
    n_att = int(gate_dec.sum())
    n_rep = int((~gate_dec).sum())
    p_att = float(lock[gate_dec].mean()) if n_att > 0 else 0.0
    p_rep = float(lock[~gate_dec].mean()) if n_rep > 0 else 0.0
    ratio = p_att / p_rep if p_rep > 1e-12 else float('inf')
    return {
        'P_lock_given_attractive': p_att,
        'P_lock_given_repulsive': p_rep,
        'ratio_att_over_rep': ratio,
        'attractive_fraction': n_att / max(1, n_att + n_rep),
    }


def signal_phase_binned_switches(switch_steps, switch_dirs, signal_freq, dt,
                                  n_bins=12):
    bin_edges = np.linspace(0.0, 2.0 * np.pi, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    if len(switch_steps) == 0:
        return (np.zeros(n_bins), np.zeros(n_bins),
                bin_centers, np.zeros(n_bins))
    abs_t_seconds = (switch_steps + WARMUP) * dt
    sig_phase_at_sw = (2.0 * np.pi * signal_freq * abs_t_seconds) % (2.0 * np.pi)
    bidx = np.digitize(sig_phase_at_sw, bin_edges[1:-1])
    up_per_bin = np.zeros(n_bins)
    dn_per_bin = np.zeros(n_bins)
    all_per_bin = np.zeros(n_bins)
    for b in range(n_bins):
        mask = bidx == b
        all_per_bin[b] = int(mask.sum())
        if mask.any():
            dirs = switch_dirs[mask]
            up_per_bin[b] = int((dirs > 0).sum())
            dn_per_bin[b] = int((dirs < 0).sum())
    return up_per_bin, dn_per_bin, bin_centers, all_per_bin


def lock_modulation_at_fs(kura_dec, sig_phase_dec, R_thr=0.9):
    lock = (kura_dec > R_thr).astype(float)
    lock_dm = lock - lock.mean()
    I = float(np.mean(lock_dm * np.sin(sig_phase_dec)))
    Q = float(np.mean(lock_dm * np.cos(sig_phase_dec)))
    mod = float(np.sqrt(I*I + Q*Q))
    return I, Q, mod, float(np.degrees(np.arctan2(Q, I)))


def kura_modulation_at_fs(kura_dec, sig_phase_dec):
    """Project R_kura(t) (continuous, not thresholded) onto sig phase."""
    k_dm = kura_dec - kura_dec.mean()
    I = float(np.mean(k_dm * np.sin(sig_phase_dec)))
    Q = float(np.mean(k_dm * np.cos(sig_phase_dec)))
    mod = float(np.sqrt(I*I + Q*Q))
    return I, Q, mod, float(np.degrees(np.arctan2(Q, I)))


def first_principles_z_st(switch_steps, switch_dirs, signal_freq, dt):
    """Closed form: I_st = Σ_k direction_k · sin(2πf_s · t_k),
                    Q_st = Σ_k direction_k · cos(2πf_s · t_k)
       where t_k = (switch_steps[k] + WARMUP) * dt.

    Returns (I_pred, Q_pred, |z|_pred). N.B. this is the SUM, not the
    mean — to compare with measured |⟨z_st⟩| over chunks, we divide
    by N_chunks at the call site (since the measured value is an
    average of per-chunk SUMS divided by chunk_steps, see
    switch_timing_IQ which uses np.sum(direction · sin(..))).
    """
    if len(switch_steps) == 0:
        return 0.0, 0.0, 0.0
    abs_t_seconds = (switch_steps + WARMUP) * dt
    arg = 2.0 * np.pi * signal_freq * abs_t_seconds
    s_dirs = switch_dirs.astype(float)
    I = float(np.sum(s_dirs * np.sin(arg)))
    Q = float(np.sum(s_dirs * np.cos(arg)))
    return I, Q, float(np.sqrt(I*I + Q*Q))


def run_cell(label, kappa_phase, kappa_C, omega_spread, signal_amp,
             seed_base, n_chunks=N_CHUNKS, n_seeds=N_SEEDS, n_bins=N_BINS):
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> {label}: κ_p={kappa_phase:.3f}  κ_C={kappa_C:.3f}  "
          f"ω_spread={omega_spread:.4f}  A={signal_amp:.4f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  steps={total_steps}  "
          f"seed_base={seed_base}")
    cell_start = time.time()
    seed_records = []
    for s in range(n_seeds):
        t0 = time.time()
        (Cm, kdec, mphdec, gdec, Cdec, sdec, spdec,
         sw_steps, sw_dirs, k_mean) = simulate_dose_response(
            N=4, noise_std=SIGMA_NOISE, steps=total_steps,
            seed=seed_base + s,
            kappa_phase=kappa_phase, kappa_C=kappa_C,
            signal_freq=SIGNAL_FREQ, signal_amp=signal_amp,
            omega_spread=omega_spread, dt=DT)
        xp = Cm[WARMUP:]
        z_raw = np.zeros(n_chunks, dtype=complex)
        z_st = np.zeros(n_chunks, dtype=complex)
        n_sw = np.zeros(n_chunks, dtype=int)
        for c in range(n_chunks):
            chunk = xp[c*CHUNK_STEPS:(c+1)*CHUNK_STEPS]
            t_off = WARMUP + c * CHUNK_STEPS
            Ir, Qr = phase_coherent_IQ(chunk, DT, SIGNAL_FREQ, t_offset=t_off)
            Is, Qs, n = switch_timing_IQ(chunk, DT, SIGNAL_FREQ,
                                          t_offset=t_off,
                                          threshold=C_THRESHOLD)
            z_raw[c] = Ir + 1j * Qr
            z_st[c] = Is + 1j * Qs
            n_sw[c] = n
        raw_st = per_seed_R_coh(z_raw)
        st_st = per_seed_R_coh(z_st)
        lock_per_bin, cnt_per_bin, bin_centers = signal_phase_binned_lock(
            kdec, spdec, n_bins=n_bins)
        gate_cond = gate_conditional_lock(kdec, gdec)
        I_lock, Q_lock, mod_amp_lock, mod_arg_lock = lock_modulation_at_fs(
            kdec, spdec)
        I_kura, Q_kura, mod_amp_kura, mod_arg_kura = kura_modulation_at_fs(
            kdec, spdec)
        up_b, dn_b, _, all_b = signal_phase_binned_switches(
            sw_steps, sw_dirs, SIGNAL_FREQ, DT, n_bins=n_bins)
        # First-principles |z_st| from the WHOLE seed event list (sum form)
        # Compare to per-chunk-sum: each chunk contributes Σ_chunk direction*sin(...)
        # and switch_timing_IQ returns those sums (no mean). The measured
        # per-chunk |z_st| is then averaged over chunks. Whole-seed sum equals
        # sum-over-chunks of per-chunk sums.
        Ip, Qp, fp_z_total = first_principles_z_st(
            sw_steps, sw_dirs, SIGNAL_FREQ, DT)
        # Measured equivalent: sum of per-chunk z_st (real and imag), absolute value.
        meas_z_total = float(abs(z_st.sum()))
        # Per-bin mean R_kura
        bin_edges = np.linspace(0.0, 2.0 * np.pi, n_bins + 1)
        bidx = np.digitize(spdec, bin_edges[1:-1])
        kura_per_bin = np.zeros(n_bins)
        for b in range(n_bins):
            mask = bidx == b
            if mask.any():
                kura_per_bin[b] = float(kdec[mask].mean())
        # cos(<φ>) modulation at f_s — for S110-P3 rectifier test
        cosphi = np.cos(mphdec)
        cphi_dm = cosphi - cosphi.mean()
        I_cp = float(np.mean(cphi_dm * np.sin(spdec)))
        Q_cp = float(np.mean(cphi_dm * np.cos(spdec)))
        mod_amp_cosphi = float(np.sqrt(I_cp*I_cp + Q_cp*Q_cp))
        mod_arg_cosphi = float(np.degrees(np.arctan2(Q_cp, I_cp)))
        rec = {
            'seed': seed_base + s,
            'z_raw': z_raw, 'z_st': z_st, 'n_sw_chunks': n_sw,
            'raw_per_seed': raw_st, 'st_per_seed': st_st,
            'kura_mean': k_mean,
            'kura_dec_len': int(len(kdec)),
            'lock_frac_global': float((kdec > 0.9).mean()),
            'lock_per_bin': lock_per_bin.tolist(),
            'cnt_per_bin': cnt_per_bin.tolist(),
            'kura_per_bin': kura_per_bin.tolist(),
            'gate_cond': gate_cond,
            'mod_amp_at_fs_lock': mod_amp_lock,
            'mod_arg_at_fs_lock_deg': mod_arg_lock,
            'mod_amp_at_fs_kura': mod_amp_kura,
            'mod_arg_at_fs_kura_deg': mod_arg_kura,
            'mod_amp_at_fs_cosphi': mod_amp_cosphi,
            'mod_arg_at_fs_cosphi_deg': mod_arg_cosphi,
            'switch_total': int(len(sw_steps)),
            'switch_up_per_bin': up_b.tolist(),
            'switch_dn_per_bin': dn_b.tolist(),
            'switch_all_per_bin': all_b.tolist(),
            'fp_z_total_pred': fp_z_total,
            'meas_z_total': meas_z_total,
        }
        seed_records.append(rec)
        elapsed = time.time() - t0
        print(f"   seed={seed_base+s:9d} {elapsed:5.1f}s   "
              f"|<z_st>|={abs(z_st.mean()):.3f}  "
              f"R_kura={k_mean:.3f}  "
              f"lock_frac={float((kdec>0.9).mean()):.3f}  "
              f"mod_lock={mod_amp_lock:.4f}  "
              f"mod_kura={mod_amp_kura:.4f}  "
              f"mod_cosφ={mod_amp_cosphi:.4f}  "
              f"Nsw={len(sw_steps)}")
    bin_centers_list = (np.linspace(0.0, 2.0 * np.pi, n_bins + 1)[:-1]
                        + np.pi / n_bins).tolist()
    print(f"   total {time.time()-cell_start:.0f}s")
    return seed_records, bin_centers_list


def summarize_cell(seed_records, bin_centers, signal_amp):
    n = len(seed_records)
    raw_R = np.array([s['raw_per_seed']['R_coh'] for s in seed_records])
    st_R = np.array([s['st_per_seed']['R_coh'] for s in seed_records])
    raw_mu = np.array([s['raw_per_seed']['mu_abs'] for s in seed_records])
    st_mu = np.array([s['st_per_seed']['mu_abs'] for s in seed_records])
    st_sigma_n = np.array([s['st_per_seed']['sigma_n'] for s in seed_records])
    p_att = np.array([s['gate_cond']['P_lock_given_attractive']
                      for s in seed_records])
    p_rep = np.array([s['gate_cond']['P_lock_given_repulsive']
                      for s in seed_records])
    att_frac = np.array([s['gate_cond']['attractive_fraction']
                         for s in seed_records])
    mod_lock = np.array([s['mod_amp_at_fs_lock'] for s in seed_records])
    mod_kura = np.array([s['mod_amp_at_fs_kura'] for s in seed_records])
    mod_cosphi = np.array([s['mod_amp_at_fs_cosphi'] for s in seed_records])
    mod_lock_arg = np.array([s['mod_arg_at_fs_lock_deg'] for s in seed_records])
    mod_kura_arg = np.array([s['mod_arg_at_fs_kura_deg'] for s in seed_records])
    mod_cosphi_arg = np.array([s['mod_arg_at_fs_cosphi_deg'] for s in seed_records])
    lock_global = np.array([s['lock_frac_global'] for s in seed_records])
    kura_mean_arr = np.array([s['kura_mean'] for s in seed_records])
    n_sw_total = np.array([s['switch_total'] for s in seed_records])

    rho_sig = []
    for s in seed_records:
        mu2 = abs(s['z_st'].mean())**2
        nsw = float(np.mean(s['n_sw_chunks']))
        rho_sig.append(mu2 / nsw if nsw > 0 else 0.0)
    rho_sig = np.array(rho_sig)

    z_lock = np.array([
        np.exp(1j * np.deg2rad(s['mod_arg_at_fs_lock_deg']))
        for s in seed_records])
    z_kura = np.array([
        np.exp(1j * np.deg2rad(s['mod_arg_at_fs_kura_deg']))
        for s in seed_records])

    fp_z_total = np.array([s['fp_z_total_pred'] for s in seed_records])
    meas_z_total = np.array([s['meas_z_total'] for s in seed_records])
    fp_ratio = np.where(meas_z_total > 0, fp_z_total / meas_z_total, 0.0)

    lock_arr = np.array([s['lock_per_bin'] for s in seed_records])
    kura_arr = np.array([s['kura_per_bin'] for s in seed_records])
    sw_all_arr = np.array([s['switch_all_per_bin'] for s in seed_records])

    return {
        'signal_amp': signal_amp,
        'n_seeds': n,
        'raw_R_coh_mean': float(raw_R.mean()),
        'raw_R_coh_std':  float(raw_R.std()),
        'st_R_coh_mean':  float(st_R.mean()),
        'st_R_coh_std':   float(st_R.std()),
        'raw_mu_mean':    float(raw_mu.mean()),
        'st_mu_mean':     float(st_mu.mean()),
        'st_sigma_n_mean': float(st_sigma_n.mean()),
        'P_lock_given_att_mean': float(p_att.mean()),
        'P_lock_given_rep_mean': float(p_rep.mean()),
        'attractive_fraction_mean': float(att_frac.mean()),
        'mod_amp_at_fs_lock_mean': float(mod_lock.mean()),
        'mod_amp_at_fs_lock_std':  float(mod_lock.std()),
        'mod_amp_at_fs_kura_mean': float(mod_kura.mean()),
        'mod_amp_at_fs_kura_std':  float(mod_kura.std()),
        'mod_amp_at_fs_cosphi_mean': float(mod_cosphi.mean()),
        'mod_amp_at_fs_cosphi_std':  float(mod_cosphi.std()),
        'cross_seed_R_angle_lock': float(abs(z_lock.mean())),
        'cross_seed_R_angle_kura': float(abs(z_kura.mean())),
        'cross_seed_R_angle_cosphi':
            float(abs(np.exp(1j*np.deg2rad(mod_cosphi_arg)).mean())),
        'lock_frac_global_mean': float(lock_global.mean()),
        'lock_frac_global_std':  float(lock_global.std()),
        'kura_mean_mean': float(kura_mean_arr.mean()),
        'kura_mean_std':  float(kura_mean_arr.std()),
        'rho_sig_st_mean': float(rho_sig.mean()),
        'rho_sig_st_std':  float(rho_sig.std()),
        'n_sw_total_mean': float(n_sw_total.mean()),
        'fp_z_total_mean':  float(fp_z_total.mean()),
        'meas_z_total_mean': float(meas_z_total.mean()),
        'fp_ratio_mean':    float(fp_ratio.mean()),
        'fp_ratio_std':     float(fp_ratio.std()),
        'lock_per_bin_mean': lock_arr.mean(axis=0).tolist(),
        'kura_per_bin_mean': kura_arr.mean(axis=0).tolist(),
        'switch_per_bin_mean': sw_all_arr.mean(axis=0).tolist(),
        'bin_centers': bin_centers,
    }


def pack_per_seed(seed_records):
    return [{
        'seed': s['seed'],
        'z_raw': [[float(z.real), float(z.imag)] for z in s['z_raw']],
        'z_st':  [[float(z.real), float(z.imag)] for z in s['z_st']],
        'n_sw_chunks': s['n_sw_chunks'].tolist(),
        'raw_per_seed': s['raw_per_seed'],
        'st_per_seed': s['st_per_seed'],
        'kura_mean': s['kura_mean'],
        'lock_frac_global': s['lock_frac_global'],
        'gate_cond': s['gate_cond'],
        'lock_per_bin': s['lock_per_bin'],
        'kura_per_bin': s['kura_per_bin'],
        'switch_all_per_bin': s['switch_all_per_bin'],
        'switch_total': s['switch_total'],
        'mod_amp_at_fs_lock': s['mod_amp_at_fs_lock'],
        'mod_arg_at_fs_lock_deg': s['mod_arg_at_fs_lock_deg'],
        'mod_amp_at_fs_kura': s['mod_amp_at_fs_kura'],
        'mod_arg_at_fs_kura_deg': s['mod_arg_at_fs_kura_deg'],
        'mod_amp_at_fs_cosphi': s['mod_amp_at_fs_cosphi'],
        'mod_arg_at_fs_cosphi_deg': s['mod_arg_at_fs_cosphi_deg'],
        'fp_z_total_pred': s['fp_z_total_pred'],
        'meas_z_total': s['meas_z_total'],
    } for s in seed_records]


def main():
    start = datetime.now()
    print("Thor Session #111: Dose-Response Sweep at the Ridge")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"chunk={CHUNK_STEPS} steps  T_chunk={T_CHUNK_S}s  "
          f"warmup={WARMUP}  decimate={DEC_KURA}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks")

    # All cells: ridge geometry. Sweep A.
    A_VALUES = [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50]
    RIDGE_KP = 0.30
    RIDGE_KC = 0.30
    RIDGE_OMEGA = 0.24

    cells = []
    for i, A in enumerate(A_VALUES):
        # Seed scheme: 111_AA_K, where AA is A*100 zero-padded.
        # E.g. A=0.05 → 11105800; A=0.30 → 11130800
        seed_base = 111_00_000 + int(A * 100) * 1000 + 800
        cells.append((f'A{A:.2f}', RIDGE_KP, RIDGE_KC, RIDGE_OMEGA,
                      A, seed_base,
                      f'A={A:.2f} ridge dose-response point'))

    cell_results = {}
    for label, kp, kC, omega, A, sb, notes in cells:
        seed_records, bin_centers = run_cell(label, kp, kC, omega, A, sb)
        summary = summarize_cell(seed_records, bin_centers, signal_amp=A)
        print(f"\n   ⇒ {label}: "
              f"R_kura={summary['kura_mean_mean']:.3f}  "
              f"lock_frac={summary['lock_frac_global_mean']:.3f}  "
              f"mod_lock={summary['mod_amp_at_fs_lock_mean']:.4f}±{summary['mod_amp_at_fs_lock_std']:.4f}  "
              f"mod_kura={summary['mod_amp_at_fs_kura_mean']:.5f}  "
              f"mod_cosφ={summary['mod_amp_at_fs_cosphi_mean']:.4f}  "
              f"R_ang(lock)={summary['cross_seed_R_angle_lock']:.3f}  "
              f"ρ_sig={summary['rho_sig_st_mean']:.4f}±{summary['rho_sig_st_std']:.4f}  "
              f"ST_R={summary['st_R_coh_mean']:.3f}  "
              f"<Nsw>={summary['n_sw_total_mean']:.0f}  "
              f"fp_ratio={summary['fp_ratio_mean']:.3f}±{summary['fp_ratio_std']:.3f}")
        cell_results[label] = {
            'kappa_phase': kp, 'kappa_C': kC, 'omega_spread': omega,
            'signal_amp': A, 'seed_base': sb, 'notes': notes,
            'summary': summary,
            'per_seed': pack_per_seed(seed_records),
        }

    out = {
        'meta': {
            'session': 111,
            'title': 'Dose-Response Sweep at the Ridge',
            'started': start.isoformat(),
            'common_params': {
                'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'dec_kura': DEC_KURA, 'n_bins': N_BINS,
                'kappa_phase_ridge': RIDGE_KP,
                'kappa_C_ridge': RIDGE_KC,
                'omega_spread_ridge': RIDGE_OMEGA,
                'A_values': A_VALUES,
            },
            'design_notes': {
                'P1_mod_lock_linear_in_A_small': 'small-A: mod_amp_at_fs_lock ∝ A.',
                'P2_saturation_high_A': 'High-A: deviation from linearity.',
                'P3_rho_sig_quadratic_low_A': 'Low-A: ρ_sig ∝ A^2.',
                'P4_R_inst2_law_A_invariance': 'γ in ρ_sig=γ·R_inst² approximately A-invariant.',
                'P5_fp_law_across_A': 'first-principles |z_st| within ±5% across A.',
                'P6_detection_floor': 'min A for z_det > 5σ.',
                'P7_lock_frac_global_vs_A': 'lock_frac monotonic in A; possibly saturates earlier than R_inst.',
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_111_dose_response_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_111_dose_response_results.json")


if __name__ == '__main__':
    main()
