# 5. System Results — Simulation vs. Hardware

## 5.1 Full-system simulation

The complete receiver — quadrature oscillator, two mixers, two filters and two amplifiers — was simulated in [`simulation/qdc_full_system.asc`](../simulation/qdc_full_system.asc) (`.tran 0 5m`, RF = `SINE(0 100m 175k)`). Every number below was extracted from the waveform data by [`scripts/analyze.py`](../scripts/analyze.py) over the last 3.4 ms (≈ 18 IF cycles), after start-up.

![Waveforms along the I path](../media/plots/signal_chain.png)

| Quantity | I path | Q path |
|---|---|---|
| LO frequency (in system) | 169.53 kHz | — |
| IF frequency | 5.469 kHz = 175 − 169.53 kHz | same |
| Mixer IF amplitude | 59.0 mV<sub>pp</sub> (−10.6 dB) | 59.9 mV<sub>pp</sub> (−10.5 dB) |
| After low-pass | 34.1 mV<sub>pp</sub> (−4.8 dB) | 34.6 mV<sub>pp</sub> (−4.8 dB) |
| Final output | **404.8 mV<sub>pp</sub>** (+21.5 dB) | **411.2 mV<sub>pp</sub>** (+21.5 dB) |
| Output 2·IF / 3·IF | −19.9 / −40.4 dBc | −20.2 / −42.8 dBc |
| **I/Q separation** | **103.0°** | |
| Implied image rejection | **18.8 dB** | |

The IF sits at 5.47 kHz rather than 5.00 kHz simply because the free-running oscillator settles at 169.53 kHz, not 170 kHz. The IF is the exact difference.

![Final I and Q outputs](../media/plots/if_quadrature.png)

The ripple riding on both outputs is residual LO feedthrough at ~170 kHz. A first-order filter gives only ~30 dB there, and the CS stage then amplifies what is left by 21.5 dB.

## 5.2 Hardware prototype

![Breadboard prototype](../media/hardware/breadboard_prototype.jpg)

The full system was built on breadboard (see [`hardware/`](../hardware)) and measured on a Keysight EDUX1052A:

- The oscillator settled at **168.5 kHz**. The RF generator was retuned to **173.5 kHz** to hold the IF at **5.0 kHz**.
- Final outputs: **385 mV<sub>pp</sub> (I)** and **378 mV<sub>pp</sub> (Q)**, within 6 % of the 400 mV<sub>pp</sub> target.
- I/Q separation: **86°**.

## 5.3 Comparison

| Parameter | Simulation | Hardware |
|---|---|---|
| Oscillator frequency | 169.6 kHz (169.5 kHz in system) | 168.5 kHz |
| Oscillator amplitude, I / Q | 1.00 / 1.07 V<sub>pp</sub> | 0.98 / 0.95 V<sub>pp</sub> |
| Input frequency | 175 kHz | 173.5 kHz |
| IF frequency | 5.47 kHz | 5.0 kHz |
| Mixer conversion gain | −10.6 dB | −13 dB |
| Low-pass corner (nominal) | 5.3 kHz | 5.2 kHz |
| Final output, I / Q | 405 / 411 mV<sub>pp</sub> | 385 / 378 mV<sub>pp</sub> |
| Final I/Q separation | 103.0° | 86° |
| Image rejection implied | 18.8 dB | 28.8 dB |
| Op-amp supply | ±12 V | ±12 V |
| MOSFET-stage supply | 1.8 V | 1.8 V |
| Mixer V<sub>BIAS</sub> / R<sub>BIAS</sub> / C<sub>C</sub> | 0.5 V / 470 kΩ / 10 nF | same |
| Mixer load | 10 kΩ | 10 kΩ |
| Oscillator R2, R3 | 736 Ω, 750 Ω | 750 Ω, 750 Ω |
| Oscillator capacitors | 1 nF | 1 nF |
| Mixer MOSFET | TSMC 180 nm, W/L = 2 µm / 0.18 µm | discrete lab NMOS, fixed geometry |

## 5.4 Understanding the differences

| Difference | Explanation |
|---|---|
| Oscillator frequency, −0.6 % | The frequency is set by the op-amps' phase lag (see [§2.3](02-quadrature-oscillator.md#23-why-the-741-sets-the-frequency)); a real 741's bandwidth differs from the 1989 macromodel, plus resistor and capacitor tolerances |
| I/Q separation, 103° vs. 86° | The quadrature error is entirely an op-amp-bandwidth effect, so it is the quantity most sensitive to the macromodel-vs-silicon gap. Both differ from 90° by a similar order (13° and 4°), in opposite directions |
| Mixer gain, −2.4 dB | The lab NMOS has higher R<sub>ON</sub> (≈ 0.8–1 kΩ) than the 180 nm device; breadboard capacitance adds feedthrough |
| Output amplitude, −5 % | Lower mixer gain, partly offset by the CS stage's bias sensitivity near threshold |

The key engineering takeaway: in this design the **oscillator's op-amp is the single most important component**. It sets both the LO frequency and the quadrature accuracy, and those carry straight through to the IF outputs.
