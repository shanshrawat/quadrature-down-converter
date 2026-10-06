"""
Render the circuit schematics in media/schematics/ from the netlists of the
LTspice designs (simulation/*.asc). Requires `schemdraw` (pip install schemdraw).

    python scripts/draw_schematics.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import schemdraw
import schemdraw.elements as elm

OUT = Path(__file__).resolve().parents[1] / "media" / "schematics"
OUT.mkdir(parents=True, exist_ok=True)
INK, ACCENT_I, ACCENT_Q, MUTED = "#0b0b0b", "#2a78d6", "#eb6834", "#52514e"
schemdraw.config(font="Inter", fontsize=11, color=INK, lw=1.4, bgcolor="#fcfcfb")


def save(d, name):
    for ext in ("svg", "png"):
        d.save(str(OUT / f"{name}.{ext}"), dpi=220)


def limiter(d, x_left, x_right, y, top_first_res=True):
    """Two anti-parallel 1N4148 + 100 Ω branches between x_left and x_right.

    Branch at y      : R (left) → diode pointing right (anode at R side)
    Branch at y + h  : R (left) ← diode pointing left (anode at right side)
    """
    w = x_right - x_left
    h = 1.3
    # branch 1: N1 -R- -|>|- OUT  (anode toward resistor, cathode at output)
    d.add(elm.Resistor(l=w / 2).at((x_left, y)).right().label("100 Ω", fontsize=9))
    d.add(elm.Diode(l=w / 2).right().label("1N4148", fontsize=9))
    # branch 2: anode at output, cathode toward resistor (anti-parallel)
    d.add(elm.Resistor(l=w / 2).at((x_left, y + h)).right().label("100 Ω", fontsize=9))
    d.add(elm.Diode(l=w / 2).right().reverse().label("1N4148", fontsize=9))
    return y + h


# ------------------------------------------------------------------ oscillator
def oscillator():
    d = schemdraw.Drawing(unit=2.4)
    # ---- U1: inverting integrator (R1, C3)
    start = (0, 0)
    r1 = d.add(elm.Resistor().at(start).right().label("R1\n1.7 kΩ"))
    n1 = r1.end
    d.add(elm.Line().right(0.6))
    op1 = d.add(elm.Opamp(leads=True).anchor("in1").label("U1\nUA741", loc="center", ofst=(-0.35, 0), fontsize=10))
    d.add(elm.Line().at(op1.in2).down(0.4))
    d.add(elm.Ground())
    xo1 = op1.out[0] + 0.6
    d.add(elm.Line().at(op1.out).right(0.6))
    n4 = (xo1, op1.out[1])
    d.add(elm.Dot().at(n4))
    # feedback ladder above U1
    y_c = n1[1] + 2.2
    d.add(elm.Dot().at(n1))
    d.add(elm.Line().at(n1).up(y_c - n1[1]))
    d.add(elm.Capacitor(l=xo1 - n1[0]).right().label("C3  0.1 nF"))
    d.add(elm.Line().down(y_c - n4[1]))
    d.add(elm.Line().at((n1[0], y_c)).up(1.3))
    d.add(elm.Line().at((xo1, y_c)).up(1.3))
    y_top = limiter(d, n1[0], xo1, y_c + 1.3)
    d.add(elm.Line().at((n1[0], y_c + 1.3)).up(1.3))
    d.add(elm.Line().at((xo1, y_c + 1.3)).up(1.3))
    d.add(elm.Dot().at((n1[0], y_c)))
    d.add(elm.Dot().at((xo1, y_c)))
    d.add(elm.Dot().at((n1[0], y_c + 1.3)))
    d.add(elm.Dot().at((xo1, y_c + 1.3)))
    d.add(elm.Label().at((n4[0] + 0.15, n4[1] - 0.5)).label("LO-Q → Q mixer", color=ACCENT_Q, fontsize=11, halign="left"))

    # ---- U2: non-inverting integrator (R2-C1 at +, R3-C2 around -)
    d.add(elm.Line().at(n4).right(1.2))
    r2 = d.add(elm.Resistor().right().label("R2\n736 Ω"))
    n5 = r2.end
    d.add(elm.Dot().at(n5))
    d.add(elm.Capacitor().at(n5).down(1.6).label("C1\n1 nF", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Line().at(n5).right(3.4))
    op2 = d.add(elm.Opamp(leads=True).flip().anchor("in2").label("U2\nUA741", loc="center", ofst=(-0.35, 0), fontsize=10))
    xo2 = op2.out[0] + 2.6
    d.add(elm.Line().at(op2.out).right(2.6))
    n7 = (xo2, op2.out[1])
    d.add(elm.Dot().at(n7))
    # inverting node N6 (bottom input after flip)
    n6x = op2.in1[0] - 0.6
    d.add(elm.Line().at(op2.in1).left(0.6))
    n6 = (n6x, op2.in1[1])
    d.add(elm.Dot().at(n6))
    y_c2 = n6[1] - 1.6
    d.add(elm.Line().at(n6).down(1.6))
    d.add(elm.Capacitor(l=xo2 - n6x).right().label("C2  1 nF", loc="bottom"))
    d.add(elm.Line().up(y_c2 - n7[1] if False else n7[1] - y_c2))
    d.add(elm.Dot().at((n6x, y_c2)))
    d.add(elm.Dot().at((xo2, y_c2)))
    yl = y_c2 - 1.3 * 2
    d.add(elm.Line().at((n6x, y_c2)).down(2.6))
    d.add(elm.Line().at((xo2, y_c2)).down(2.6))
    limiter(d, n6x, xo2, yl)
    # R3 to ground from N6
    d.add(elm.Line().at(n6).left(1.5))
    d.add(elm.Resistor().down(2.0).label("R3\n750 Ω", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Label().at((op2.out[0] + 0.15, n7[1] + 0.4)).label("LO-I → I mixer", color=ACCENT_I, fontsize=11, halign="left"))

    # ---- loop closure: U2 output back to R1
    y_bot = yl - 1.4
    d.add(elm.Line().at(n7).right(0.8))
    d.add(elm.Line().down(n7[1] - y_bot))
    d.add(elm.Line().left(xo2 + 0.8 - (start[0] - 0.8)))
    d.add(elm.Line().up(0 - y_bot))
    d.add(elm.Line().right(0.8))
    d.add(elm.Label().at((start[0] - 0.8, y_bot - 0.6)).label(
        "U1, U2: UA741 on ±12 V    •    limiter = 1N4148 + 100 Ω, anti-parallel",
        fontsize=9.5, color=MUTED, halign="left"))
    save(d, "quadrature_oscillator")


# ------------------------------------------------- mixer -> LPF -> amplifier
def signal_path():
    """I path of Combined.asc: M1 mixer -> R13/C7 low-pass -> M4 CS amplifier."""
    d = schemdraw.Drawing(unit=2.4)
    G = 1.37                                   # FET gate offset (schemdraw geometry)

    # ---- (1) NMOS pass-switch mixer, drain on top, source at the bottom
    m1 = d.add(elm.NFet().reverse().anchor("drain").at((4, 1.5))
               .label("M1", loc="right", ofst=(0.5, 0.15), fontsize=11))
    d.add(elm.Label().at((4.3, 0.45)).label("2 µm / 0.18 µm", fontsize=9, color=MUTED, halign="left"))
    # RF source below the switch
    d.add(elm.Line().at(m1.source).down(0.9))
    ns = (4, m1.source[1] - 0.9)
    d.add(elm.Dot().at(ns))
    d.add(elm.Line().at(ns).right(0.8))
    d.add(elm.Label().label("to Q mixer", fontsize=9, color=MUTED, loc="right", halign="left"))
    src = d.add(elm.SourceSin().down(2.2).at(ns).label("v_RF\n100 mV\n175 kHz", loc="bottom", fontsize=10))
    d.add(elm.Ground())
    # gate: LO through C4, DC bias through R9
    d.add(elm.Line().at(m1.gate).left(0.7))
    gn = (m1.gate[0] - 0.7, m1.gate[1])
    d.add(elm.Dot().at(gn))
    d.add(elm.Capacitor().at(gn).left(2.0).label("C4  10 nF", fontsize=10))
    d.add(elm.Dot(open=True))
    d.add(elm.Label().label("LO-I", color=ACCENT_I, fontsize=12, loc="left", halign="right"))
    d.add(elm.Resistor().at(gn).up(2.4).label("R9\n470 kΩ", loc="top", fontsize=10))
    d.add(elm.Vdd().label("V_BIAS  0.5 V", fontsize=10))

    # ---- drain node, load resistor
    d.add(elm.Line().at(m1.drain).up(0.6))
    d.add(elm.Line().right(3.4))
    n1 = (7.4, m1.drain[1] + 0.6)
    d.add(elm.Dot().at(n1))
    d.add(elm.Resistor().at(n1).down(2.4).label("R_L\n10 kΩ", loc="bottom", fontsize=10))
    d.add(elm.Ground())

    # ---- (2) RC low-pass
    r13 = d.add(elm.Resistor().at(n1).right(2.6).label("R13  30 kΩ", fontsize=10))
    n11 = r13.end
    d.add(elm.Dot().at(n11))
    d.add(elm.Capacitor().at(n11).down(2.4).label("C7\n1 nF", loc="bottom", fontsize=10))
    d.add(elm.Ground())

    # ---- (3) AC-coupled common-source amplifier
    cc = d.add(elm.Capacitor().at(n11).right(2.6).label("C_C  10 µF", loc="bottom", fontsize=10))
    ng = cc.end
    d.add(elm.Dot().at(ng))
    d.add(elm.Resistor().at(ng).up(2.4).label("R_G1\n330 kΩ", loc="top", fontsize=10))
    d.add(elm.Vdd().label("1.8 V", fontsize=10))
    d.add(elm.Resistor().at(ng).down(2.4).label("R_G2\n100 kΩ", loc="bottom", fontsize=10))
    d.add(elm.Ground())
    d.add(elm.Line().at(ng).right(1.0))
    m4 = d.add(elm.NFet().reverse().anchor("gate").label("M4", loc="right", ofst=(0.5, 0.15), fontsize=11))
    d.add(elm.Label().at((m4.source[0] + 0.25, m4.gate[1] - 0.2)).label("20 µm / 0.18 µm", fontsize=9, color=MUTED, halign="left"))
    d.add(elm.Line().at(m4.source).down(0.6))
    d.add(elm.Ground())
    d.add(elm.Line().at(m4.drain).up(0.6))
    nd = (m4.drain[0], m4.drain[1] + 0.6)
    d.add(elm.Dot().at(nd))
    d.add(elm.Resistor().at(nd).up(2.4).label("R_D\n133 kΩ", loc="bottom", fontsize=10))
    d.add(elm.Vdd().label("1.8 V", fontsize=10))
    d.add(elm.Line().at(nd).right(2.0))
    d.add(elm.Dot(open=True))
    d.add(elm.Label().label("I_FINAL", color=ACCENT_I, fontsize=12, loc="right", halign="left"))

    # ---- captions
    y_cap = 7.6
    for x, txt in [(3.2, "① NMOS switching mixer"), (9.8, "② RC low-pass"), (14.8, "③ common-source amplifier")]:
        d.add(elm.Label().at((x, y_cap)).label(txt, fontsize=11, color=MUTED, halign="center"))
    d.add(elm.Label().at((-0.6, -4.6)).label(
        "Q path identical, driven by LO-Q   •   TSMC 180 nm CMOSN, all bodies tied to ground",
        fontsize=9.5, color=MUTED, halign="left"))
    save(d, "signal_path")


if __name__ == "__main__":
    oscillator()
    signal_path()
