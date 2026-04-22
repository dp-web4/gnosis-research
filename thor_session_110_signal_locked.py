#!/usr/bin/env python3
"""Thor Session #110: Signal-Phase-Resolved Lock — The Direct Mechanism Test (S109-P3)

Context (S109)
--------------
S109 measured per-oscillator phase ensembles at the κ_C=0.30 ridge and
discovered:
  - σ_φ_ratio02 = 80.7° > σ_φ_ratio08 = 64.1°  (S108-P6 inverted)
  - lock_frac (R_kura > 0.9) correlates with ρ_sig at r ≈ +0.61 across cells
  - Within ridge cells, ρ_sig ≈ 0.4 · R_inst²
  - Pairwise |Δφ| is bimodal at ratio 0.2: lock + anti-lock peaks at 0/π
  - Inferred mechanism: "synchronized phases → switches synchronized in time
    → events cluster at signal-phase peaks → high signal density."

But this mechanism story is CORRELATION across cells, not a direct
within-cell measurement. The simulator literally encodes the signal
into the phase coupling sign at every step:

      sign = +1 if (C_mean + signal) < C_threshold else -1
      dphase = ω + sign · κ_p · ⟨sin(φ_j − φ_k)⟩

So the signal is GATING attractive vs repulsive phase coupling on a
sample-by-sample basis. The S109-P3 prediction is that this gating
should be visible in lock_frac conditioned on signal phase: ≥1.5×
more lock time in the attractive half of the signal.

Design
------
Modified simulator records per-step (decimated by 10) the joint
(R_kura(t), gate_state, C_mean, signal, switch_event). One canonical
ridge cell + two controls:

  1. ridge:    κ_p=0.30, κ_C=0.30, ratio=0.8, A=0.30  ← target
  2. nokC:     κ_p=0.30, κ_C=0.00, ratio=0.8, A=0.30  ← control:
              C-coupling absent, but signal still gates phase coupling
              sign. Lock structure should still appear in raw phases
              even though ρ_sig is at floor (S109).
  3. null:     κ_p=0.30, κ_C=0.30, ratio=0.8, A=0.00  ← null:
              no signal, no gate modulation, no signal-phase structure.

Each cell: 16 seeds × 30 chunks × 40k steps + 10k warmup. Decimation
factor 10 → 121k samples/seed at decimated res. Signal period = 3333
steps → 333 samples/cycle.

Predictions
-----------
P1 (S109-P3 LITERAL, ridge cell): lock_frac(attractive)/lock_frac(repulsive)
   ≥ 1.5. With A=0.30 strongly modulating the gate, prediction is sharper:
   ≥ 2.0×. Phase-binned lock_frac should be ~sinusoidal with amplitude
   ~1/3 of the mean.

P2 (gate-instantaneous): R_kura(t)|gate=attractive > R_kura(t)|gate=repulsive
   pointwise. Direct test of the simulator's coupling-sign-flip mechanism.

P3 (no-kC control): in nokC cell, the signal still flips the coupling
   sign, so the same lock asymmetry should appear in raw phase ensemble
   even though detector ρ_sig is at floor (because κ_C=0 means C's are
   independent — signal cannot reach the detector through switching).
   Concretely: nokC P_lock(att)/P_lock(rep) within ±20% of ridge value.

P4 (null cell): no signal-phase structure detectable. Phase-binned
   lock_frac is flat (consistent with binning noise). Establishes
   detection floor for the analysis.

P5 (switch-event clustering): switch events (sign flips of C_mean −
   threshold) are clustered at specific signal phases. Predict ≥1.5×
   more switch events in a 60° wedge around the maximum than in the
   wedge 180° opposite.

P6 (matched-filter law from first principles): |⟨z_st⟩|² should equal
   |⟨switch_density(φ_s) · e^{iφ_s}⟩|² · N_switches². If P5 holds, this
   gives a calculation-from-first-principles for ρ_sig.

P7 (lock-modulation amplitude predicts ρ_sig): the FFT amplitude of
   lock_frac(t) at signal_freq should be linearly related to √ρ_sig.
   Both stem from the same gate-modulation source.
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
A_SIGNAL = 0.30
SIGMA_NOISE = 0.022
DT = 0.1
WARMUP = 10_000
CHUNK_STEPS = 40_000
T_CHUNK_S = CHUNK_STEPS * DT
N_SEEDS = 16
N_CHUNKS = 30
DEC_KURA = 10        # decimate joint (R_kura, gate, C, sig) every 10 steps
                     # signal period = 3333 steps → 333 samples/cycle


def simulate_signal_locked(N, noise_std, steps, seed,
                            kappa_phase=0.10, kappa_C=0.15,
                            omega_base=0.1, omega_spread=0.02,
                            phi_inverse=0.618, dt=0.1,
                            C_threshold=0.55,
                            signal_freq=0.003, signal_amp=0.0):
    """S106 simulator + decimated joint trace of
    (R_kura(t), gate_attractive, C_mean, signal, switch_event).

    Switch events are recorded per-step (not decimated) so that
    binned switch density is exact. They are returned as event times
    (post-warmup step indices).

    Returns:
      C_mean_hist           (steps,)
      kura_dec              (n_dec,)        |⟨e^{iφ}⟩|
      gate_dec              (n_dec,) bool   gate sign at t (True=attractive)
      C_mean_dec            (n_dec,)
      sig_dec               (n_dec,)        signal value at t
      sig_phase_dec         (n_dec,)        2πf_s·t·dt mod 2π at t (rad)
      switch_event_steps    (n_sw,) int     post-warmup step indices of
                                              sign(C_mean - threshold) flips
      switch_dirs           (n_sw,) int     +1 if up-crossing, -1 if down
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

        # post-warmup recording
        post = t - WARMUP
        if post >= 0:
            # decimated joint state
            if post % DEC_KURA == 0:
                z_sum = np.mean(np.exp(1j * phase))
                kura_dec[d_idx] = abs(z_sum)
                gate_dec[d_idx] = bool(is_attractive)
                C_mean_dec[d_idx] = C_mean
                sig_dec[d_idx] = signal
                sig_phase_dec[d_idx] = (2.0 * np.pi * signal_freq * t * dt) % (2.0 * np.pi)
                d_idx += 1
            # switch-event detection on the post-update C_mean
            #   we use the value from C_mean_hist[t] which is pre-update,
            #   so detect from the diff sign of C_mean_hist - threshold
            cur_sign = 1 if (C_mean_hist[t] - C_threshold) > 0 else -1
            if prev_sign is not None and cur_sign != prev_sign:
                switch_steps.append(post)
                switch_dirs.append(cur_sign)
            prev_sign = cur_sign
    kura_dec = kura_dec[:d_idx]
    gate_dec = gate_dec[:d_idx]
    C_mean_dec = C_mean_dec[:d_idx]
    sig_dec = sig_dec[:d_idx]
    sig_phase_dec = sig_phase_dec[:d_idx]
    return (C_mean_hist, kura_dec, gate_dec, C_mean_dec, sig_dec,
            sig_phase_dec,
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
    """Bin lock indicator (R_kura > R_thr) by signal phase into n_bins.

    Returns lock_frac per bin, count per bin, bin centers (rad).
    """
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
    """P(R_kura > R_thr | gate_attractive) and the same for gate_repulsive.

    Returns dict with both probabilities and the count totals.
    """
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
        'n_attractive_samples': n_att,
        'n_repulsive_samples': n_rep,
        'attractive_fraction': n_att / max(1, n_att + n_rep),
    }


def signal_phase_binned_switches(switch_steps, switch_dirs, signal_freq,
                                  dt, n_bins=12):
    """Switch events binned by signal phase at switch instant.

    Args:
      switch_steps: post-warmup step indices of crossings.
                    Wall time of each event is (WARMUP + s) * dt.
                    But signal phase as recorded is computed using full t·dt.
      signal_freq: f_s.

    Returns up_count_per_bin, down_count_per_bin, bin_centers, all_count.
    """
    bin_edges = np.linspace(0.0, 2.0 * np.pi, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    if len(switch_steps) == 0:
        return (np.zeros(n_bins), np.zeros(n_bins),
                bin_centers, np.zeros(n_bins))
    # signal phase at the absolute step (post + WARMUP)
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
    """Project lock(t) − ⟨lock⟩ onto sin/cos of signal phase.

    Returns (I, Q, mod_amp = sqrt(I²+Q²), mod_arg_deg). Equivalent to
    a matched filter on the lock-indicator signal.
    """
    lock = (kura_dec > R_thr).astype(float)
    lock_dm = lock - lock.mean()
    I = float(np.mean(lock_dm * np.sin(sig_phase_dec)))
    Q = float(np.mean(lock_dm * np.cos(sig_phase_dec)))
    mod = float(np.sqrt(I*I + Q*Q))
    return I, Q, mod, float(np.degrees(np.arctan2(Q, I)))


def run_cell(label, kappa_phase, kappa_C, omega_spread, signal_amp,
             seed_base, n_chunks=N_CHUNKS, n_seeds=N_SEEDS, n_bins=12):
    total_steps = WARMUP + n_chunks * CHUNK_STEPS
    print(f"\n>> {label}: κ_p={kappa_phase:.3f}  κ_C={kappa_C:.3f}  "
          f"ω_spread={omega_spread:.4f}  A={signal_amp:.3f}  "
          f"n_seeds={n_seeds}  n_chunks={n_chunks}  steps={total_steps}  "
          f"seed_base={seed_base}")
    cell_start = time.time()
    seed_records = []
    for s in range(n_seeds):
        t0 = time.time()
        (Cm, kdec, gdec, Cdec, sdec, spdec,
         sw_steps, sw_dirs, k_mean) = simulate_signal_locked(
            N=4, noise_std=SIGMA_NOISE, steps=total_steps,
            seed=seed_base + s,
            kappa_phase=kappa_phase, kappa_C=kappa_C,
            signal_freq=SIGNAL_FREQ, signal_amp=signal_amp,
            omega_spread=omega_spread, dt=DT)
        # detector outputs per chunk
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
        # lock analysis
        lock_per_bin, cnt_per_bin, bin_centers = signal_phase_binned_lock(
            kdec, spdec, n_bins=n_bins)
        gate_cond = gate_conditional_lock(kdec, gdec)
        I_lock, Q_lock, mod_amp, mod_arg = lock_modulation_at_fs(kdec, spdec)
        # switch binning
        up_b, dn_b, _, all_b = signal_phase_binned_switches(
            sw_steps, sw_dirs, SIGNAL_FREQ, DT, n_bins=n_bins)
        # signal-binned R_kura mean
        bin_edges = np.linspace(0.0, 2.0 * np.pi, n_bins + 1)
        bidx = np.digitize(spdec, bin_edges[1:-1])
        kura_per_bin = np.zeros(n_bins)
        for b in range(n_bins):
            mask = bidx == b
            if mask.any():
                kura_per_bin[b] = float(kdec[mask].mean())
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
            'I_lock_at_fs': I_lock,
            'Q_lock_at_fs': Q_lock,
            'mod_amp_at_fs': mod_amp,
            'mod_arg_deg_at_fs': mod_arg,
            'switch_total': int(len(sw_steps)),
            'switch_up_per_bin': up_b.tolist(),
            'switch_dn_per_bin': dn_b.tolist(),
            'switch_all_per_bin': all_b.tolist(),
        }
        seed_records.append(rec)
        elapsed = time.time() - t0
        print(f"   seed={seed_base+s:9d} {elapsed:5.1f}s   "
              f"|<z_st>|={abs(z_st.mean()):.3f}  "
              f"R_kura={k_mean:.3f}  "
              f"P(L|att)={gate_cond['P_lock_given_attractive']:.3f}  "
              f"P(L|rep)={gate_cond['P_lock_given_repulsive']:.3f}  "
              f"ratio={gate_cond['ratio_att_over_rep']:.2f}  "
              f"mod={mod_amp:.4f}  "
              f"Nsw_total={len(sw_steps)}")
    bin_centers_list = (np.linspace(0.0, 2.0 * np.pi, n_bins + 1)[:-1]
                        + np.pi / n_bins).tolist()
    print(f"   total {time.time()-cell_start:.0f}s")
    return seed_records, bin_centers_list


def summarize_cell(seed_records, bin_centers):
    n = len(seed_records)
    raw_R = np.array([s['raw_per_seed']['R_coh'] for s in seed_records])
    st_R = np.array([s['st_per_seed']['R_coh'] for s in seed_records])
    raw_mu = np.array([s['raw_per_seed']['mu_abs'] for s in seed_records])
    st_mu = np.array([s['st_per_seed']['mu_abs'] for s in seed_records])
    p_att = np.array([s['gate_cond']['P_lock_given_attractive']
                      for s in seed_records])
    p_rep = np.array([s['gate_cond']['P_lock_given_repulsive']
                      for s in seed_records])
    att_frac = np.array([s['gate_cond']['attractive_fraction']
                         for s in seed_records])
    mod_amps = np.array([s['mod_amp_at_fs'] for s in seed_records])
    mod_args = np.array([s['mod_arg_deg_at_fs'] for s in seed_records])
    lock_global = np.array([s['lock_frac_global'] for s in seed_records])
    kura_mean = np.array([s['kura_mean'] for s in seed_records])

    # Average across seeds: lock_frac per signal-phase bin
    lock_arr = np.array([s['lock_per_bin'] for s in seed_records])
    kura_arr = np.array([s['kura_per_bin'] for s in seed_records])
    sw_all_arr = np.array([s['switch_all_per_bin'] for s in seed_records])
    sw_up_arr = np.array([s['switch_up_per_bin'] for s in seed_records])
    sw_dn_arr = np.array([s['switch_dn_per_bin'] for s in seed_records])

    # ρ_sig = |<z_st>_chunks|² / <N_sw>_chunks per seed
    rho_sig = []
    for s in seed_records:
        mu2 = abs(s['z_st'].mean())**2
        nsw = float(np.mean(s['n_sw_chunks']))
        rho_sig.append(mu2 / nsw if nsw > 0 else 0.0)
    rho_sig = np.array(rho_sig)

    # Lock-modulation amplitude statistics
    # Total lock-modulation projection: ⟨mod_amp⟩
    # Phase across seeds (vector mean of mod direction, weighted by mod_amp)
    z_mod = np.array([s['I_lock_at_fs'] + 1j*s['Q_lock_at_fs']
                      for s in seed_records])
    z_mod_mean = z_mod.mean()

    return {
        'n_seeds': n,
        'raw_R_coh_mean': float(raw_R.mean()),
        'raw_R_coh_std':  float(raw_R.std()),
        'st_R_coh_mean':  float(st_R.mean()),
        'st_R_coh_std':   float(st_R.std()),
        'raw_mu_mean':    float(raw_mu.mean()),
        'st_mu_mean':     float(st_mu.mean()),
        'P_lock_given_att_mean': float(p_att.mean()),
        'P_lock_given_att_std':  float(p_att.std()),
        'P_lock_given_rep_mean': float(p_rep.mean()),
        'P_lock_given_rep_std':  float(p_rep.std()),
        'lock_ratio_att_over_rep_mean':
            float(p_att.mean()/p_rep.mean()) if p_rep.mean() > 1e-12 else float('inf'),
        'lock_ratio_per_seed_mean':
            float(np.mean([a/r for a, r in zip(p_att, p_rep) if r > 1e-12])),
        'lock_ratio_per_seed_std':
            float(np.std([a/r for a, r in zip(p_att, p_rep) if r > 1e-12])),
        'attractive_fraction_mean': float(att_frac.mean()),
        'mod_amp_at_fs_mean': float(mod_amps.mean()),
        'mod_amp_at_fs_std':  float(mod_amps.std()),
        'mod_arg_at_fs_circular_mean_deg':
            float(np.degrees(np.angle(np.mean(np.exp(1j*np.deg2rad(mod_args)))))),
        'cross_seed_z_mod_mean':
            [float(z_mod_mean.real), float(z_mod_mean.imag)],
        'cross_seed_R_angle_mod':
            float(abs(np.mean(np.exp(1j*np.deg2rad(mod_args))))),
        'lock_frac_global_mean': float(lock_global.mean()),
        'kura_mean_mean': float(kura_mean.mean()),
        'lock_per_bin_mean': lock_arr.mean(axis=0).tolist(),
        'lock_per_bin_std':  lock_arr.std(axis=0).tolist(),
        'kura_per_bin_mean': kura_arr.mean(axis=0).tolist(),
        'kura_per_bin_std':  kura_arr.std(axis=0).tolist(),
        'switch_all_per_bin_mean': sw_all_arr.mean(axis=0).tolist(),
        'switch_up_per_bin_mean':  sw_up_arr.mean(axis=0).tolist(),
        'switch_dn_per_bin_mean':  sw_dn_arr.mean(axis=0).tolist(),
        'switch_per_bin_total': sw_all_arr.sum(axis=0).tolist(),
        'rho_sig_st_mean': float(rho_sig.mean()),
        'rho_sig_st_std':  float(rho_sig.std()),
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
        'cnt_per_bin': s['cnt_per_bin'],
        'kura_per_bin': s['kura_per_bin'],
        'switch_up_per_bin': s['switch_up_per_bin'],
        'switch_dn_per_bin': s['switch_dn_per_bin'],
        'switch_all_per_bin': s['switch_all_per_bin'],
        'switch_total': s['switch_total'],
        'I_lock_at_fs': s['I_lock_at_fs'],
        'Q_lock_at_fs': s['Q_lock_at_fs'],
        'mod_amp_at_fs': s['mod_amp_at_fs'],
        'mod_arg_deg_at_fs': s['mod_arg_deg_at_fs'],
    } for s in seed_records]


def main():
    start = datetime.now()
    print("Thor Session #110: Signal-Phase-Resolved Lock Dynamics (S109-P3)")
    print(f"Started: {start.isoformat()}")
    print(f"Common: σ={SIGMA_NOISE}  f_s={SIGNAL_FREQ}  "
          f"chunk={CHUNK_STEPS} steps  T_chunk={T_CHUNK_S}s  "
          f"warmup={WARMUP}  decimate={DEC_KURA}")
    print(f"Per cell: {N_SEEDS} seeds × {N_CHUNKS} chunks")

    # Seed codes 110_NN_R: NN = which cell, R = ratio·10. Disjoint from S109's 9_PP_CC_R.
    cells = [
        # (label, κ_p, κ_C, ω_spread, A, seed_base, notes)
        ('ridge',     0.30, 0.30, 0.240, 0.30, 110_01_8,
         'TARGET: ridge cell at κ_C=0.30, ratio 0.8'),
        ('nokC',      0.30, 0.00, 0.240, 0.30, 110_02_8,
         'CONTROL: signal still gates phase coupling, no C-coupling'),
        ('null',      0.30, 0.30, 0.240, 0.00, 110_03_8,
         'NULL: no signal, no gate modulation. Floor for P-bin variance.'),
    ]

    cell_results = {}
    for label, kp, kC, omega, A, sb, notes in cells:
        seed_records, bin_centers = run_cell(label, kp, kC, omega, A, sb)
        summary = summarize_cell(seed_records, bin_centers)
        print(f"\n   ⇒ {label}: "
              f"P(L|att)={summary['P_lock_given_att_mean']:.3f}±{summary['P_lock_given_att_std']:.3f}  "
              f"P(L|rep)={summary['P_lock_given_rep_mean']:.3f}±{summary['P_lock_given_rep_std']:.3f}  "
              f"ratio={summary['lock_ratio_per_seed_mean']:.2f}±{summary['lock_ratio_per_seed_std']:.2f}  "
              f"mod_amp_fs={summary['mod_amp_at_fs_mean']:.4f}±{summary['mod_amp_at_fs_std']:.4f}  "
              f"R_angle_mod={summary['cross_seed_R_angle_mod']:.3f}  "
              f"ρ_sig={summary['rho_sig_st_mean']:.4f}  "
              f"ST_R={summary['st_R_coh_mean']:.3f}")
        cell_results[label] = {
            'kappa_phase': kp, 'kappa_C': kC, 'omega_spread': omega,
            'signal_amp': A, 'seed_base': sb, 'notes': notes,
            'summary': summary,
            'per_seed': pack_per_seed(seed_records),
        }

    out = {
        'meta': {
            'session': 110,
            'title': 'Signal-Phase-Resolved Lock Dynamics (S109-P3)',
            'started': start.isoformat(),
            'common_params': {
                'sigma': SIGMA_NOISE, 'dt': DT,
                'signal_freq': SIGNAL_FREQ, 'C_threshold': C_THRESHOLD,
                'warmup': WARMUP, 'chunk_steps': CHUNK_STEPS,
                'T_chunk_s': T_CHUNK_S,
                'n_seeds': N_SEEDS, 'n_chunks': N_CHUNKS,
                'dec_kura': DEC_KURA,
            },
            'design_notes': {
                'P1_ratio_15x': 'lock_frac(att)/lock_frac(rep) ≥ 1.5 in ridge.',
                'P2_gate_instant': 'P(R_kura>0.9|att) > P(R_kura>0.9|rep) directly.',
                'P3_nokC_lock_persists': 'In nokC cell, gate modulates lock similarly.',
                'P4_null_flat': 'In null cell, lock_per_bin flat to noise.',
                'P5_switch_clustering': 'Switch events cluster at specific signal phase.',
                'P6_matched_filter_law': '|<z_st>|² ≈ matched-filter on switch density.',
                'P7_lock_mod_predicts_rho_sig': 'mod_amp_at_fs predicts √ρ_sig.',
            },
        },
        'cells': cell_results,
    }
    with open('thor_session_110_signal_locked_results.json', 'w') as f:
        json.dump(out, f, indent=2, default=float)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("Results → thor_session_110_signal_locked_results.json")


if __name__ == '__main__':
    main()
