#!/usr/bin/env python3
"""Inspect inoisy+ HDF5 output without loading the full 4D field."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np


def inspect(path: Path) -> None:
    with h5py.File(path, "r") as handle:
        dataset = handle["/data/data_raw"]
        first = np.asarray(dataset[0], dtype=np.float64)
        expected = tuple(
            int(np.asarray(handle[f"/params/{name}"]))
            for name in ("npk", "npl", "npj", "npi")
        )
        local = tuple(
            int(np.asarray(handle[f"/params/{name}"]))
            for name in ("nk", "nl", "nj", "ni")
        )
        reconstructed = tuple(a * b for a, b in zip(expected, local))

        print(f"\n{path}")
        print(f"  dataset: /data/data_raw")
        print(f"  shape: {dataset.shape}")
        print(f"  dtype: {dataset.dtype}")
        print(f"  processor grid × local grid: {reconstructed}")
        print(f"  first-slice mean/std: {first.mean():.6g} / {first.std():.6g}")
        print(f"  file size: {path.stat().st_size / 1024**2:.3f} MiB")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.files:
        inspect(path.resolve())


if __name__ == "__main__":
    main()
