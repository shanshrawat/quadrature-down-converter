# LTspice Simulations

| File | What it is | Analysis |
|---|---|---|
| [`oscillator.asc`](oscillator.asc) | Stand-alone quadrature oscillator (2 × UA741, ±12 V) | `.tran 1m` |
| [`oscillator.plt`](oscillator.plt) | Saved plot settings: both LO outputs, zoomed to a few cycles | — |
| [`qdc_full_system.asc`](qdc_full_system.asc) | Complete receiver: oscillator, two NMOS mixers, two RC filters, two CS amplifiers | `.tran 0 5m` (an `.ac` directive for the filter is included, commented out) |
| [`UA741.asy`](UA741.asy) | Op-amp symbol used by both schematics (pin order In+, In−, V+, V−, Out) | — |

Rendered versions of the schematics are in [`media/schematics`](../media/schematics).

## Model files

Both schematics load their models by bare filename, so the model files must sit **in this folder**. They are third-party files and are not redistributed here:

| File | Contents | Where to get it |
|---|---|---|
| `TSMC_180nm.txt` | BSIM3v3.2 cards `CMOSN` and `CMOSP` (TSMC 0.18 µm, MOSIS run T64H) | MOSIS parametric test results for TSMC 180 nm, or a course/PDK distribution |
| `UA741.301` | UA741 op-amp macromodel (subcircuit `UA741`) | Texas Instruments' UA741 product page → SPICE model |

## Running

1. Copy `TSMC_180nm.txt` and `UA741.301` into this folder.
2. Open a schematic in LTspice and press **Run**.
3. Post-process with the scripts in [`scripts/`](../scripts) to reproduce every number and plot in the README:

```bash
python scripts/analyze.py --osc simulation/oscillator.raw --system simulation/qdc_full_system.raw
```

## Device instances

Every MOSFET specifies its full geometry, so BSIM computes junction capacitance from real diffusion dimensions:

```spice
* mixer switches (M1 = I, M2 = Q)
CMOSN l=180n w=2u  ad=1.2p as=1.2p pd=5.2u  ps=5.2u
* CS amplifier devices (M3 = Q, M4 = I)
CMOSN l=180n w=20u ad=12p  as=12p  pd=41.2u ps=41.2u
```

## Tips

- Add `.options plotwinsize=0` before running an FFT in LTspice. This disables waveform compression and lowers the noise floor.
- To study oscillator start-up, give the transient a maximum timestep (e.g. `.tran 0 5m 0 20n`); otherwise LTspice takes a very large first step.
- To list every component with its connected nets: `python scripts/asc_netlist.py simulation/qdc_full_system.asc`.
