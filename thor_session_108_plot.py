#!/usr/bin/env python3
"""S108 — plot ratio 0.2 vs ratio 0.8 R_coh(κ_C) curves with quadratic fits."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

d = json.load(open('thor_session_108_analysis.json'))
r02 = d['ratio_0.2']
r08 = d['ratio_0.8']

fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

def plot_slice(ax, slice_data, label, color_raw, color_st):
    cells = slice_data['cells']
    fit = slice_data['quadratic_fit']
    kC = np.array([c['kC'] for c in cells])
    Rr = np.array([c['R_raw'] for c in cells])
    Rs = np.array([c['R_st']  for c in cells])

    x_fit = np.linspace(0, 0.55, 200)

    # RAW
    coefs_r = np.polyfit(kC, Rr, 2)
    y_fit_r = np.polyval(coefs_r, x_fit)
    ax.plot(x_fit, y_fit_r, '-', color=color_raw, alpha=0.6)
    ax.plot(kC, Rr, 'o', color=color_raw, markersize=8, label=f"{label}: RAW")
    ax.axvline(fit['peak_raw_kC'], color=color_raw, ls=':', alpha=0.4)

    # ST
    coefs_s = np.polyfit(kC, Rs, 2)
    y_fit_s = np.polyval(coefs_s, x_fit)
    ax.plot(x_fit, y_fit_s, '-', color=color_st, alpha=0.6)
    ax.plot(kC, Rs, 's', color=color_st, markersize=8, label=f"{label}: ST")
    ax.axvline(fit['peak_st_kC'], color=color_st, ls=':', alpha=0.4)

    ax.annotate(f"RAW κ_C*={fit['peak_raw_kC']:.3f}\n"
                f"ST  κ_C*={fit['peak_st_kC']:.3f}",
                xy=(0.02, 0.95), xycoords='axes fraction', va='top',
                fontsize=9, family='monospace')

plot_slice(axes[0], r02, 'ratio 0.2', 'C0', 'C1')
axes[0].set_title("ratio ω/κ_p = 0.2 (deep coherent, ω=0.06)")
axes[0].set_xlabel("κ_C")
axes[0].set_ylabel("R_coh")
axes[0].legend(loc='lower center', fontsize=9)
axes[0].set_xlim(-0.02, 0.55)
axes[0].set_ylim(0, 1.0)
axes[0].grid(alpha=0.3)

plot_slice(axes[1], r08, 'ratio 0.8', 'C0', 'C1')
axes[1].set_title("ratio ω/κ_p = 0.8 (near desync, ω=0.24)  [S106]")
axes[1].set_xlabel("κ_C")
axes[1].set_ylabel("R_coh")
axes[1].legend(loc='lower center', fontsize=9)
axes[1].set_xlim(-0.02, 0.55)
axes[1].set_ylim(0, 1.0)
axes[1].grid(alpha=0.3)

plt.suptitle("S108: Ridge location at κ_p=0.30, A=0.30, σ=0.022", fontsize=12)
plt.tight_layout()
plt.savefig('thor_session_108_ridge_comparison.png', dpi=110)
print("Saved thor_session_108_ridge_comparison.png")

# Combined overlay
fig2, ax = plt.subplots(figsize=(8, 5))
for slice_data, label, c in [(r02, 'ratio 0.2', 'C0'),
                              (r08, 'ratio 0.8', 'C3')]:
    cells = slice_data['cells']
    fit = slice_data['quadratic_fit']
    kC = np.array([c_cell['kC'] for c_cell in cells])
    Rr = np.array([c_cell['R_raw'] for c_cell in cells])
    x_fit = np.linspace(0, 0.55, 200)
    coefs_r = np.polyfit(kC, Rr, 2)
    y_fit_r = np.polyval(coefs_r, x_fit)
    ax.plot(x_fit, y_fit_r, '-', color=c, alpha=0.5)
    ax.plot(kC, Rr, 'o-', color=c, markersize=8, label=f"{label} (RAW)")
    ax.axvline(fit['peak_raw_kC'], color=c, ls=':', alpha=0.5)

ax.set_xlabel("κ_C")
ax.set_ylabel("R_coh (RAW)")
ax.set_title(f"S108: RAW ridge — does κ_C* depend on ω/κ_p ratio?\n"
             f"(κ_p=0.30, A=0.30, σ=0.022)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('thor_session_108_ridge_overlay.png', dpi=110)
print("Saved thor_session_108_ridge_overlay.png")
