# Project Report

[`QDC_Report.pdf`](QDC_Report.pdf) is the IEEE two-column report submitted for the course (written in LaTeX). It covers the design reasoning and the full hardware prototype.

## Errata

After submission, the simulations were re-analysed directly from the LTspice waveform data (see [`docs/06`](../docs/06-simulation-methodology.md)). That analysis corrected or sharpened several statements in the report. **Where they differ, this repository is authoritative.**

| Report says | Corrected | Details |
|---|---|---|
| The oscillator is a "Wien-bridge" (conclusion) | It is TI's three-RC quadrature oscillator | [docs/02](../docs/02-quadrature-oscillator.md) |
| Oscillator values R = 736 / 750 Ω, C = 1 nF | Also includes the U1 integrator: **1.7 kΩ / 0.1 nF** | [`simulation/oscillator.asc`](../simulation/oscillator.asc) |
| Frequency follows $1/2\pi RC$; R tuned empirically | With unequal time constants the ideal loop would run at ~448 kHz; the 741's phase lag sets ~170 kHz | [docs/02 §2.3](../docs/02-quadrature-oscillator.md#23-why-the-741-sets-the-frequency) |
| Simulated I/Q phase 90° (LO), 88° (final outputs) | **102.8° (LO), 103.0° (final)** — finite op-amp gain in U2 | [docs/02 §2.4](../docs/02-quadrature-oscillator.md#24-where-the-90-goes) |
| Simulated IF of 5.46 kHz attributed to drift and tolerances | The LO settles at 169.53 kHz; the IF is exactly 175 − 169.53 = 5.47 kHz | [docs/05](../docs/05-system-results.md) |
| CS amplifier: R<sub>D</sub> = 30 kΩ, divider 2.7 MΩ / 1 MΩ, gain ≈ 3 | Simulated design: **R<sub>D</sub> = 133 kΩ, divider 330 kΩ / 100 kΩ, W = 20 µm, gain 11.9 V/V** | [docs/04 §4.4](../docs/04-filter-and-amplifier.md#44-common-source-amplifier) |
| Dominant distortion: 3rd harmonic at −28 dB | **2nd harmonic dominates (−20 to −22 dBc)**; 3rd is −40 dBc | [docs/03 §3.4](../docs/03-nmos-switching-mixer.md#34-non-idealities-seen-in-the-data) |
| LPF cut-off 4.82 kHz (abstract) | 5.3 kHz nominal (30 kΩ, 1 nF) | [docs/04](../docs/04-filter-and-amplifier.md) |
| Drain/source area 1.2 pm² | **1.2 µm²** (`ad=1.2p` in LTspice is 1.2 × 10⁻¹² m²) | [docs/03 §3.3](../docs/03-nmos-switching-mixer.md#33-device-sizing-tsmc-180-nm-bsim3v3) |
| W/L chosen to limit parasitic capacitance at 170 kHz | Device parasitics are femtofarads (≈ 190 MΩ at 170 kHz); W/L matters for R<sub>ON</sub> | [docs/03 §3.3](../docs/03-nmos-switching-mixer.md#33-device-sizing-tsmc-180-nm-bsim3v3) |
| 1° and 0.1 dB give image rejection "exceeding 40 dB" | 39.6 dB; 0.1 dB gain mismatch alone gives ~46 dB | [docs/01 §1.5](../docs/01-theory.md#15-how-good-must-the-quadrature-be) |
| Figs. 13 and 14 (171 kHz and 172 kHz transients) | The same screenshot was inserted twice; only the 171 kHz transient is reproduced here | [docs/03 §3.5](../docs/03-nmos-switching-mixer.md#35-frequency-sweep) |

Hardware measurements in the report are unchanged.
