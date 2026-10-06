"""
Post-process the LTspice simulations of the quadrature down converter.

Extracts frequency, amplitude, I/Q phase and harmonic content directly from the
.raw waveform data (rather than reading cursors by eye) and renders the figures
used in the README and docs.

    python scripts/analyze.py --osc simulation/oscillator.raw \
                              --system simulation/qdc_full_system.raw \
                              --out media/plots

Node map (from the netlist extracted out of the .asc files)
------------------------------------------------------------
Stand-alone oscillator (oscillator.asc)
    V(n001)  U1 output  -> quadrature LO, "sine" phase
    V(n004)  U2 output  -> quadrature LO, "cosine" phase
Full system (qdc_full_system.asc)
    V(n002)  LO-Q (U3 out)       V(n011)  LO-I (U4 out)
    V(n012)  RF input (175 kHz)
    V(n005)  mixer drain, Q      V(n020)  mixer drain, I
    V(n006)  LPF output, Q       V(n021)  LPF output, I
    V(n003)  final output, Q     V(n019)  final output, I
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ltspice_raw import RawFile

# ---------------------------------------------------------------- style ----
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
C_I, C_Q, C_NEUTRAL = "#2a78d6", "#eb6834", "#8a8984"   # validated slots 1, 2
plt.rcParams.update({
    "font.family": "Inter", "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 11, "axes.titleweight": "semibold", "axes.titlelocation": "left",
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2, "axes.axisbelow": True, "legend.frameon": False, "legend.labelcolor": INK,
})


# ------------------------------------------------------------ measurement --
def zero_cross_freq(t, v):
    """Mean frequency from rising zero crossings (linearly interpolated)."""
    v = v - v.mean()
    i = np.where((v[:-1] < 0) & (v[1:] >= 0))[0]
    tz = t[i] - v[i] * (t[i + 1] - t[i]) / (v[i + 1] - v[i])
    return 1.0 / np.mean(np.diff(tz))


def tone(raw, node, f0, t_end, n_cyc, pts_per_cyc=400, n_harm=5):
    """Coherent single-bin DFT over an integer number of cycles ending at t_end.

    Returns amplitude (V peak) and phase (deg) of the fundamental, harmonic levels
    in dBc and the DC value.
    """
    t = np.linspace(t_end - n_cyc / f0, t_end, n_cyc * pts_per_cyc, endpoint=False)
    x = raw.resample(node, t)
    X = np.fft.rfft(x) / len(x) * 2
    fund = X[n_cyc]
    harm = {k: 20 * np.log10(abs(X[k * n_cyc]) / abs(fund)) for k in range(2, n_harm + 1)}
    return {"amp_pk": abs(fund), "phase_deg": np.degrees(np.angle(fund)),
            "harm_dbc": harm, "dc": X[0].real / 2}


def phase_diff(a, b):
    """Phase of b relative to a, wrapped to (-180, 180]."""
    return (b["phase_deg"] - a["phase_deg"] + 180) % 360 - 180


def spectrum(raw, node, t0, t1, fs=50e6):
    """Hann-windowed amplitude spectrum in dB relative to its largest bin."""
    t = np.arange(t0, t1, 1 / fs)
    x = raw.resample(node, t)
    x = (x - x.mean()) * np.hanning(len(x))
    X = np.abs(np.fft.rfft(x))
    f = np.fft.rfftfreq(len(x), 1 / fs)
    return f, 20 * np.log10(X / X.max() + 1e-12)


# ---------------------------------------------------------------- figures --
def fig_lo(osc, f_lo, m, out):
    T = 1 / f_lo
    t0 = 0.9e-3
    t = np.linspace(t0, t0 + 3 * T, 1500)
    vi, vq = osc.resample("V(n004)", t), osc.resample("V(n001)", t)
    us = (t - t0) * 1e6

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(us, vq, color=C_Q, label="LO-Q  (U1 output)")
    ax.plot(us, vi, color=C_I, label="LO-I  (U2 output)")
    # annotate the lag between rising zero crossings
    def first_rise(v):
        i = np.where((v[:-1] < 0) & (v[1:] >= 0))[0][0]
        return us[i] - v[i] * (us[i + 1] - us[i]) / (v[i + 1] - v[i])
    tq, ti = first_rise(vq), first_rise(vi)
    if ti < tq:
        ti += T * 1e6
    y = -0.66
    for x0, col in ((tq, C_Q), (ti, C_I)):
        ax.axvline(x0, color=col, lw=1, ls=(0, (3, 3)))
    ax.annotate("", xy=(ti, y), xytext=(tq, y),
                arrowprops=dict(arrowstyle="<->", color=INK2, lw=1.2))
    ax.text(ti + 0.3, y, f"Δt = {ti - tq:.2f} µs  →  {m['lo_phase_deg']:.1f}°",
            ha="left", va="center", color=INK, fontsize=9.5)
    ax.axhline(0, color=GRID, lw=1)
    ax.set_ylim(-0.9, 0.85)
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title(f"Quadrature LO — {f_lo/1e3:.2f} kHz, I/Q separation {m['lo_phase_deg']:.1f}°")
    ax.legend(loc="upper right", ncols=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "lo_quadrature.png", dpi=200)
    plt.close(fig)


def fig_lo_spectrum(osc, f_lo, m, out):
    f, s = spectrum(osc, "V(n004)", 0.3e-3, 1.0e-3)
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    sel = f < 1.05e6
    ax.plot(f[sel] / 1e3, s[sel], color=C_I, lw=1.4)
    for k, lab in [(1, "f₀"), (3, "3f₀"), (5, "5f₀")]:
        lvl = 0 if k == 1 else m["lo_harm_dbc"][k]
        ax.annotate(f"{lab}\n{lvl:.0f} dBc" if k > 1 else f"{lab} = {f_lo/1e3:.1f} kHz",
                    xy=(k * f_lo / 1e3, lvl), xytext=(k * f_lo / 1e3 + 25, lvl + 6),
                    fontsize=9, color=INK)
    ax.set_ylim(-110, 12)
    ax.set_xlim(0, 1050)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Level (dB rel. fundamental)")
    ax.set_title("LO spectrum — odd harmonics from the diode amplitude limiter")
    fig.tight_layout()
    fig.savefig(out / "lo_spectrum.png", dpi=200)
    plt.close(fig)


def fig_signal_chain(sysr, f_if, out):
    t0 = 4.5e-3 - 2 / f_if
    t = np.linspace(t0, 4.5e-3, 6000)
    us = (t - t0) * 1e6
    panels = [
        ("V(n012)", "RF input — 175 kHz, 200 mVpp", C_NEUTRAL, 0),
        ("V(n020)", "I mixer output — IF + LO feedthrough + sum products", C_I, 0),
        ("V(n021)", "I after RC low-pass — 5.47 kHz IF", C_I, 0),
        ("V(n019)", "I final output — CS amplifier (AC component)", C_I, 1),
    ]
    fig, axs = plt.subplots(4, 1, figsize=(7.2, 7.6), sharex=True)
    for ax, (node, title, col, ac) in zip(axs, panels):
        v = sysr.resample(node, t)
        if ac:
            v = v - v.mean()
        ax.plot(us, v * 1e3, color=col, lw=1.1 if node in ("V(n012)", "V(n020)") else 2)
        ax.set_title(title, fontsize=10)
        ax.set_ylabel("mV")
    axs[-1].set_xlabel("Time (µs)")
    fig.tight_layout()
    fig.savefig(out / "signal_chain.png", dpi=200)
    plt.close(fig)


def fig_if_quadrature(sysr, f_if, m, out):
    t0 = 4.6e-3 - 2 / f_if
    t = np.linspace(t0, 4.6e-3, 4000)
    us = (t - t0) * 1e6
    vi = sysr.resample("V(n019)", t)
    vq = sysr.resample("V(n003)", t)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(us, (vi - vi.mean()) * 1e3, color=C_I, label="I output")
    ax.plot(us, (vq - vq.mean()) * 1e3, color=C_Q, label="Q output")
    ax.axhline(0, color=GRID, lw=1)
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("Voltage, AC (mV)")
    ax.set_ylim(-280, 330)
    ax.set_title(f"Final IF outputs — {f_if/1e3:.2f} kHz, "
                 f"{m['out_i_vpp']*1e3:.0f} / {m['out_q_vpp']*1e3:.0f} mVpp, "
                 f"I/Q separation {m['if_phase_deg']:.1f}°")
    ax.legend(loc="upper right", ncols=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "if_quadrature.png", dpi=200)
    plt.close(fig)


def fig_mixer_spectrum(sysr, f_lo, f_if, out):
    f, s = spectrum(sysr, "V(n020)", 1.5e-3, 5e-3)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    sel = (f > 1e3) & (f < 1.2e6)
    ax.semilogx(f[sel], s[sel], color=C_I, lw=1.2)
    marks = [(f_if, "IF = fRF − fLO", (1.15, 4)),
             (2 * f_if, "2·IF (even-order\ndistortion)", (1.15, 6)),
             (172e3, "RF + LO\nfeedthrough", (0.22, 6)),
             (175e3 + f_lo, "fRF + fLO", (1.12, 4))]
    for fx, lab, (mx, dy) in marks:
        k = np.argmin(abs(f - fx))
        w = max(3, int(0.03 * k))
        lvl = s[max(k - w, 0):k + w].max()
        ax.annotate(lab, xy=(fx, lvl), xytext=(fx * mx, lvl + dy), fontsize=8.5, color=INK,
                    arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.set_ylim(-100, 22)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Level (dB rel. peak)")
    ax.set_title("I-mixer output spectrum — what the low-pass filter has to remove")
    fig.tight_layout()
    fig.savefig(out / "mixer_spectrum.png", dpi=200)
    plt.close(fig)


def fig_level_budget(m, out):
    stages = ["RF input", "Mixer output\n(IF tone)", "After LPF", "Final output"]
    vals = [m["rf_vpp"], m["mix_i_vpp"], m["lpf_i_vpp"], m["out_i_vpp"]]
    vals = [v * 1e3 for v in vals]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    bars = ax.bar(stages, vals, color=C_I, width=0.55)
    gains = [None, m["mixer_gain_db"], m["lpf_gain_db"], m["amp_gain_db"]]
    for b, v, g in zip(bars, vals, gains):
        txt = f"{v:.0f} mVpp" + ("" if g is None else f"\n({g:+.1f} dB)")
        ax.text(b.get_x() + b.get_width() / 2, v + 8, txt, ha="center", va="bottom",
                fontsize=9, color=INK)
    ax.set_ylim(0, max(vals) * 1.3)
    ax.set_ylabel("Amplitude (mVpp)")
    ax.grid(axis="x", visible=False)
    ax.set_title("Signal-level budget along the I path (5.47 kHz component)")
    fig.tight_layout()
    fig.savefig(out / "level_budget.png", dpi=200)
    plt.close(fig)


# -------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--osc", required=True, help="stand-alone oscillator .raw")
    ap.add_argument("--system", required=True, help="full-system .raw")
    ap.add_argument("--out", default="media/plots")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    osc, sysr = RawFile(args.osc), RawFile(args.system)
    m = {}

    # --- oscillator
    tm = osc["time"] > 0.5e-3
    f_lo = zero_cross_freq(osc["time"][tm], osc["V(n001)"][tm])
    lo_q = tone(osc, "V(n001)", f_lo, 1.0e-3, 60)
    lo_i = tone(osc, "V(n004)", f_lo, 1.0e-3, 60)
    m.update(f_lo_hz=f_lo, lo_q_vpp=np.ptp(osc["V(n001)"][tm]), lo_i_vpp=np.ptp(osc["V(n004)"][tm]),
             lo_phase_deg=abs(phase_diff(lo_q, lo_i)), lo_harm_dbc=lo_i["harm_dbc"])

    # --- full system
    ts = sysr["time"] > 2.5e-3
    f_lo_sys = zero_cross_freq(sysr["time"][ts], sysr["V(n002)"][ts])
    f_if = 175e3 - f_lo_sys
    n_if = int(3.4e-3 * f_if)
    T_END = 5e-3 - 1e-7
    get = lambda node: tone(sysr, node, f_if, T_END, n_if)
    mix_i, mix_q = get("V(n020)"), get("V(n005)")
    lpf_i, lpf_q = get("V(n021)"), get("V(n006)")
    out_i, out_q = get("V(n019)"), get("V(n003)")
    m.update(
        f_lo_system_hz=f_lo_sys, f_if_hz=f_if, rf_vpp=0.2,
        mix_i_vpp=2 * mix_i["amp_pk"], mix_q_vpp=2 * mix_q["amp_pk"],
        lpf_i_vpp=2 * lpf_i["amp_pk"], lpf_q_vpp=2 * lpf_q["amp_pk"],
        out_i_vpp=2 * out_i["amp_pk"], out_q_vpp=2 * out_q["amp_pk"],
        if_phase_deg=abs(phase_diff(out_q, out_i)),
        mixer_gain_db=20 * np.log10(mix_i["amp_pk"] / 0.1),
        lpf_gain_db=20 * np.log10(lpf_i["amp_pk"] / mix_i["amp_pk"]),
        amp_gain_db=20 * np.log10(out_i["amp_pk"] / lpf_i["amp_pk"]),
        out_i_harm_dbc=out_i["harm_dbc"], mix_i_harm_dbc=mix_i["harm_dbc"],
        lpf_dc_offset_mv=lpf_i["dc"] * 1e3,
    )
    g, e = out_i["amp_pk"] / out_q["amp_pk"], np.radians(m["if_phase_deg"] - 90)
    c = g * np.cos(e)
    m["image_rejection_db"] = 10 * np.log10((1 + 2 * c + g * g) / (1 - 2 * c + g * g))

    fig_lo(osc, f_lo, m, out)
    fig_lo_spectrum(osc, f_lo, m, out)
    fig_signal_chain(sysr, f_if, out)
    fig_if_quadrature(sysr, f_if, m, out)
    fig_mixer_spectrum(sysr, f_lo_sys, f_if, out)
    fig_level_budget(m, out)

    clean = json.loads(json.dumps(m, default=float))
    (out / "measurements.json").write_text(json.dumps(clean, indent=2))
    for k, v in clean.items():
        print(f"{k:22s} {v}")


if __name__ == "__main__":
    main()
