# 6. Simulation and Measurement Methodology

How every number in this repository was produced, and the simulation pitfalls that were handled along the way.

## 6.1 Models

| Model | Source | Notes |
|---|---|---|
| `CMOSN` / `CMOSP` | TSMC 0.18 µm BSIM3v3.2 card (MOSIS run T64H, LTspice `LEVEL=8`) | V<sub>TH0</sub> = 0.38 V / −0.39 V, T<sub>OX</sub> = 4.1 nm. LTspice ignores the `XL`/`XW` parameters — harmless. |
| `UA741` | Boyle-type macromodel (PSpice parts release, 1989) | GBW ≈ 1.1 MHz, SR ≈ 0.51 V/µs, output within ~2.6 V of the rails |
| `1N4148` | LTspice standard diode library | |

Every MOSFET instance specifies W, L, AD, AS, PD and PS so that BSIM computes junction capacitances from real geometry rather than defaults. AD = W × 0.6 µm and PD = 2(W + 0.6 µm) for both device sizes.

## 6.2 Analyses

| Analysis | Used for |
|---|---|
| `.op` | Bias points — CS amplifier I<sub>D</sub>, V<sub>D</sub>, mixer gate bias |
| `.tran` | Oscillator start-up and steady state; full-system waveforms |
| `.ac` | Low-pass filter frequency response |
| FFT (waveform viewer and Python) | Harmonics, mixing products, LO purity |

## 6.3 Extracting results from the waveform data

Cursor readings are imprecise for phase and distortion, so the `.raw` files are processed directly in Python:

1. **Parse the binary file.** [`scripts/ltspice_raw.py`](../scripts/ltspice_raw.py) reads LTspice's UTF-16 header and binary payload: float64 time and float32 signals for transient data, complex128 for AC/FFT data. It also clears the sign bit LTspice uses as a flag on the time axis.
2. **Resample uniformly.** LTspice uses adaptive timesteps, so signals are interpolated onto a uniform grid before any spectral analysis.
3. **Measure frequency** from linearly interpolated rising zero crossings, averaged over many cycles.
4. **Measure amplitude and phase with a coherent single-bin DFT.** The analysis window holds an exact integer number of cycles, so the tone falls on one bin with no spectral leakage. Phase differences come from the bin phases. The same result is cross-checked by zero-crossing timing: 102.7° ± 0.04° over 60+ cycles for the LO.
5. **Harmonics** are read at integer multiples of that bin, in dBc.
6. **Spectra for display** use a Hann window to suppress leakage from the non-coherent tones (LO, RF, sum products).
7. **Image rejection** is computed from the measured amplitude ratio and phase error using the expression in [§1.5](01-theory.md#15-how-good-must-the-quadrature-be).

Node mapping (which `V(nXXX)` is which signal) was established by extracting the netlist from the `.asc` schematic and confirmed by correlating each mixer's output with an ideal software mix of its LO and the RF input.

## 6.4 Simulation pitfalls handled

| Issue | What happened | Handling |
|---|---|---|
| **Operating point of an oscillator** | Direct Newton iteration and Gmin stepping both fail — an oscillator has no stable DC point by design | LTspice falls back to source stepping, which succeeds; the transient then starts from that point |
| **Start-up resolution** | With no maximum timestep, LTspice's first step jumped 0 → 72 µs, skipping the oscillator's build-up | Steady-state measurements use data after 0.5 ms (oscillator) or 1.5 ms (system). For start-up studies, set a maximum step, e.g. `.tran 0 5m 0 20n` |
| **FFT noise floor** | LTspice compresses saved waveforms by default, raising the FFT noise floor | Add `.options plotwinsize=0` to save every point, or analyse in Python as above |
| **Junction geometry on wide devices** | LTspice warned `Pd < W` on the 20 µm amplifier devices, whose diffusion parameters had been copied from the 2 µm mixer devices | Corrected to AD = AS = 12 p, PD = PS = 41.2 µ. The effect on results is negligible: femtofarads at kHz |
| **Model includes** | Schematics reference model files by bare filename | Model files live next to the schematics; see [`simulation/README.md`](../simulation/README.md) |
