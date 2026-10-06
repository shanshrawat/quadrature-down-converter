# 1. Theory — Why Quadrature (I/Q) Down-Conversion?

## 1.1 Mixing is multiplication

A mixer multiplies the incoming RF signal by a local oscillator (LO). With $v_{in} = A_1\cos\omega_{in}t$ and $v_{LO} = A_2\cos\omega_{LO}t$:

$$
v_{in}\,v_{LO} = \frac{A_1A_2}{2}\Big[\cos(\omega_{in}-\omega_{LO})t + \cos(\omega_{in}+\omega_{LO})t\Big]
$$

The difference term is the **intermediate frequency (IF)**; the sum term is removed by a low-pass filter. In this design $f_{in} = 175$ kHz and the LO runs at 169.53 kHz, so the IF is 5.47 kHz and the sum product sits at 344.5 kHz.

## 1.2 The image problem with a single mixer

Cosine is even: $\cos(+\omega_{IF}t) = \cos(-\omega_{IF}t)$. An input at $f_{LO} + f_{IF}$ (wanted) and one at $f_{LO} - f_{IF}$ (the **image**) both produce the same IF from a single real mixer. Once they overlap, no filter can separate them.

```
   RF spectrum                         After a single real mixer
   ───────────                         ─────────────────────────
     image    wanted                        image + wanted
       │        │                                 │
  ─────┴───┬────┴─────► f        ────────────────┴──────────► f
         f_LO                                   f_IF
   (f_LO − f_IF) (f_LO + f_IF)          both fold onto the same bin
```

## 1.3 Receiver architectures

| Architecture | How it handles the image | Cost |
|---|---|---|
| **Superheterodyne** | A sharp RF filter removes the image *before* mixing; IF chosen high so the image is far away | Bulky off-chip SAW/ceramic filters, extra LO and mixer stages |
| **Direct conversion (zero-IF)** | IF = 0; the "image" is the mirror half of the wanted channel itself, so I/Q mixing is mandatory | DC offsets from LO self-mixing, flicker noise, even-order distortion land in-band |
| **Low-IF** | Small non-zero IF; I/Q mixing plus a complex (polyphase) filter or digital processing rejects the nearby image | Image rejection limited by I/Q matching |

This project is a low-IF front-end: a 5.47 kHz IF, separated into I and Q.

## 1.4 Two LO phases recover the sign of the frequency

Mixing with both $\cos\omega_{LO}t$ (I) and $\sin\omega_{LO}t$ (Q) and low-pass filtering gives

$$
I(t) = \tfrac{A_1A_2}{2}\cos\omega_{IF}t, \qquad Q(t) = -\tfrac{A_1A_2}{2}\sin\omega_{IF}t \qquad (\omega_{IF} = \omega_{in}-\omega_{LO})
$$

so the pair forms a single complex (analytic) signal:

$$
I(t) + jQ(t) = \tfrac{A_1A_2}{2}\,e^{-j\omega_{IF}t}.
$$

An input above the LO and one below it now map to *opposite signs* of frequency. Whether Q leads or lags I tells the receiver which side of the LO the signal came from. This is what enables image rejection, I/Q demodulation (QPSK, QAM, OFDM) and zero-IF operation.

A useful consequence for measurement: the IF phase is $\phi_{IF} = \phi_{RF} - \phi_{LO}$, so **whatever phase separation the two LO outputs have is copied one-for-one onto the I and Q outputs**. This is exactly what the simulation shows — 102.8° between the LOs, 103.0° between the IF outputs.

## 1.5 How good must the quadrature be?

With an amplitude ratio $g$ between paths and a phase error $\theta$ from 90°, the image-rejection ratio (IRR) is

$$
\text{IRR} = \frac{1 + 2g\cos\theta + g^2}{1 - 2g\cos\theta + g^2}.
$$

| Case | Amplitude ratio | Phase error | IRR |
|---|---|---|---|
| Gain mismatch only, 1 % (0.1 dB) | 1.01 | 0° | 46 dB |
| 0.1 dB and 1° together | 1.012 | 1° | 39.6 dB |
| This design — simulation | 405 / 411 mV | 13.0° | 18.8 dB |
| This design — hardware | 385 / 378 mV | 4° | 28.8 dB |

Abidi [1] notes that a 1 % gain mismatch alone limits sideband suppression to roughly 45 dB, and that integrated receivers typically aim for a quadrature error below 1°. The last two rows are computed from this project's own data and show why I/Q **matching** — not absolute accuracy — is what a quadrature receiver depends on.

## References

1. A. A. Abidi, "Direct-conversion radio transceivers for digital communications," *IEEE JSSC*, vol. 30, no. 12, 1995.
2. B. Razavi, *RF Microelectronics*, 2nd ed., ch. 4.
