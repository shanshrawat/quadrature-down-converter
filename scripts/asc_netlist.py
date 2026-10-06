"""
Extract a connectivity netlist from an LTspice .asc schematic.

LTspice schematics store wires, symbols and flags as plain-text geometry. This
script rebuilds the electrical nets with a union-find over wire endpoints
(including T-junctions that land mid-wire) and the rotated pin positions of
each symbol, then prints every component with the net on each of its pins.
It is how the schematics in media/schematics were checked against the designs.

    python scripts/asc_netlist.py simulation/qdc_full_system.asc
"""
import collections
import sys

# Pin offsets of the symbols used in this project, at rotation R0.
PINS = {
    "res": [("A", 16, 16), ("B", 16, 96)],
    "cap": [("A", 16, 0), ("B", 16, 64)],
    "voltage": [("+", 0, 16), ("-", 0, 96)],
    "diode": [("A", 16, 0), ("K", 16, 64)],
    "nmos4": [("D", 48, 0), ("G", 0, 80), ("S", 48, 96), ("B", 48, 48)],
    "UA741": [("IN+", -32, 80), ("IN-", -32, 48), ("V+", 0, 32), ("V-", 0, 96), ("OUT", 32, 64)],
}
ROT = {"R0": lambda x, y: (x, y), "R90": lambda x, y: (-y, x),
       "R180": lambda x, y: (-x, -y), "R270": lambda x, y: (y, -x)}


def parse(path):
    wires, flags, syms, cur = [], [], [], None
    for line in open(path, encoding="latin-1"):
        p = line.split()
        if not p:
            continue
        if p[0] == "WIRE":
            wires.append(tuple(map(int, p[1:5])))
        elif p[0] == "FLAG":
            flags.append((int(p[1]), int(p[2]), p[3]))
        elif p[0] == "SYMBOL":
            cur = {"type": p[1], "x": int(p[2]), "y": int(p[3]), "rot": p[4], "attr": {}}
            syms.append(cur)
        elif p[0] == "SYMATTR" and cur is not None:
            cur["attr"][p[1]] = " ".join(p[2:])
    return wires, flags, syms


def netlist(path):
    wires, flags, syms = parse(path)
    pts, pins = set(), []
    for w in wires:
        pts.update([w[:2], w[2:]])
    for s in syms:
        for name, dx, dy in PINS[s["type"]]:
            ox, oy = ROT[s["rot"]](dx, dy)
            pt = (s["x"] + ox, s["y"] + oy)
            pts.add(pt)
            pins.append((id(s), name, pt))
    pts.update(f[:2] for f in flags)

    parent = {p: p for p in pts}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for x1, y1, x2, y2 in wires:          # any point lying on a wire joins its net
        for p in pts:
            on_v = x1 == x2 == p[0] and min(y1, y2) <= p[1] <= max(y1, y2)
            on_h = y1 == y2 == p[1] and min(x1, x2) <= p[0] <= max(x1, x2)
            if on_v or on_h:
                parent[find(p)] = find((x1, y1))

    names = {find((x, y)): ("GND" if n == "0" else n) for x, y, n in flags}
    auto = collections.OrderedDict()

    def net(p):
        r = find(p)
        if r in names:
            return names[r]
        return auto.setdefault(r, f"N{len(auto) + 1}")

    rows = []
    for s in syms:
        conns = [(n, net(pt)) for sid, n, pt in pins if sid == id(s)]
        rows.append((s["attr"].get("InstName", "?"), s["type"], s["attr"].get("Value", ""),
                     s["attr"].get("Value2", ""), conns))
    return rows


if __name__ == "__main__":
    rows = netlist(sys.argv[1])
    for inst, typ, val, val2, conns in rows:
        pins = " ".join(f"{a}={b}" for a, b in conns)
        print(f"{inst:8s} {typ:8s} {val:20s} {pins}  {val2}")
    counts = collections.Counter(n for r in rows for _, n in r[4])
    dangling = [n for n, c in counts.items() if c == 1]
    print("\nsingle-connection nets:", dangling or "none")
