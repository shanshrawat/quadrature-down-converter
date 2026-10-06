"""
Minimal reader for LTspice binary .raw files (transient, AC and FFT outputs).

LTspice stores a UTF-16 header followed by binary data:
  * transient ("real")    : time as float64, every other variable as float32
  * "double" flag         : every variable as float64
  * AC / FFT ("complex")  : every variable as complex128

Usage
-----
    from ltspice_raw import RawFile
    raw = RawFile("Combined.raw")
    t   = raw["time"]
    vout = raw["V(n019)"]
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

_BINARY_MARKER = "Binary:\n".encode("utf-16le")


class RawFile:
    def __init__(self, path: str | Path):
        blob = Path(path).read_bytes()
        split = blob.find(_BINARY_MARKER)
        if split < 0:
            raise ValueError(f"{path}: not a binary LTspice .raw file")

        self.header = blob[:split].decode("utf-16le")
        payload = blob[split + len(_BINARY_MARKER):]

        n_vars = int(re.search(r"No\. Variables:\s*(\d+)", self.header).group(1))
        n_pts = int(re.search(r"No\. Points:\s*(\d+)", self.header).group(1))
        flags = re.search(r"Flags:\s*(.*)", self.header).group(1)
        var_block = self.header.split("Variables:\n", 1)[1].strip("\n").splitlines()
        self.names = [line.split("\t")[2] for line in var_block]

        if "complex" in flags:
            data = np.frombuffer(payload, np.complex128, n_vars * n_pts).reshape(n_pts, n_vars)
        elif "double" in flags:
            data = np.frombuffer(payload, np.float64, n_vars * n_pts).reshape(n_pts, n_vars)
        else:
            rec = np.dtype([("t", "<f8")] + [(f"v{k}", "<f4") for k in range(n_vars - 1)])
            r = np.frombuffer(payload, rec, n_pts)
            data = np.empty((n_pts, n_vars))
            data[:, 0] = np.abs(r["t"])  # LTspice uses the sign bit as a flag
            for k in range(n_vars - 1):
                data[:, k + 1] = r[f"v{k}"]
        self.data = data

    def __getitem__(self, name: str) -> np.ndarray:
        return self.data[:, self.names.index(name)]

    def resample(self, name: str, t_new: np.ndarray) -> np.ndarray:
        """Linear interpolation onto a uniform grid (LTspice uses adaptive steps)."""
        return np.interp(t_new, self.data[:, 0], self[name])
