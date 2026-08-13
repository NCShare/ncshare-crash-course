#!/usr/bin/env python3
"""Relax a molecule with QuantUI and record the energy-per-step trajectory.

This is the *second* dataset the GPU session hands to the visualization
session. Where ``run_cpu_gpu_comparison.py`` produces wall-time numbers for a
bar chart, this produces a geometry-optimization trajectory for a line plot:
the SCF energy at each BFGS step as the structure relaxes toward its minimum.

It is a **CPU** calculation. QuantUI's ``optimize_geometry`` drives PySCF's
SCF + analytical nuclear gradients on the host, not gpu4pyscf, so this job does
*not* need an H200 and should not hold one — run it in a CPU allocation (for
example the same one used for the visualization session), leaving the eight
workshop GPUs for the timing comparison.

Usage:
    python run_geometry_optimization.py --preset water
    python run_geometry_optimization.py --preset ethanol --basis 6-31G
    python run_geometry_optimization.py --preset water --steps 100 --fmax 0.03

The result is written to
``$COURSE_WORK/quantui/geometry_optimization_<preset>.json`` for the plotting
notebook in tutorials/05-visualization-postprocessing.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

# Starting geometries (Angstrom). These are deliberately a little off their
# minimum so the optimizer takes several visible steps -- a one-step relaxation
# makes a boring line. Coordinates are plain lists so this file needs no numpy.
_WATER_PERTURBED = (
    ["O", "H", "H"],
    [
        [0.000, 0.000, 0.000],
        [1.050, 0.350, 0.000],   # O-H stretched and bent from equilibrium
        [-0.850, 0.750, 0.050],
    ],
)
# A slightly stretched ethanol (C-O and O-H pulled long) -- a richer, more
# research-like relaxation. Heavier than water; test it on the cluster before
# relying on it, and keep water as the safe default.
_ETHANOL_PERTURBED = (
    ["C", "C", "O", "H", "H", "H", "H", "H", "H"],
    [
        [1.1879, -0.3829, 0.0000],
        [0.0000, 0.5526, 0.0000],
        [-1.3500, -0.3000, 0.0000],   # C-O lengthened
        [-2.1000, 0.4500, 0.0000],    # O-H lengthened
        [2.0985, 0.2306, 0.0000],
        [1.1184, -1.0093, 0.8869],
        [1.1184, -1.0093, -0.8869],
        [-0.0227, 1.1812, 0.8852],
        [-0.0227, 1.1812, -0.8852],
    ],
)


def _preset(label, geom, basis):
    atoms, coords = geom
    return {"label": label, "atoms": atoms, "coordinates": coords, "basis": basis}


PRESETS = {
    # Fast and robust: a handful of BFGS steps, always converges. The default.
    "water": _preset("H2O  RHF/STO-3G", _WATER_PERTURBED, "STO-3G"),
    # Richer trajectory; heavier. Verify on the cluster before teaching from it.
    "ethanol": _preset("C2H6O  RHF/STO-3G", _ETHANOL_PERTURBED, "STO-3G"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="water")
    parser.add_argument("--basis", help="Override the preset's basis set.")
    parser.add_argument("--method", default="RHF", help="SCF method (RHF/UHF/DFT).")
    parser.add_argument(
        "--fmax",
        type=float,
        default=0.05,
        help="Force convergence threshold in eV/Angstrom (default 0.05).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=200,
        help="Maximum BFGS optimizer steps (default 200).",
    )
    args = parser.parse_args()

    # Imported here (not at module top) so --help works even where PySCF/ASE
    # are unavailable, and so the import cost is only paid on a real run.
    from quantui import Molecule, optimize_geometry

    spec = PRESETS[args.preset]
    basis = args.basis or spec["basis"]
    label = spec["label"]
    if args.basis:
        label = f"{label.split()[0]}  {args.method}/{args.basis}"

    molecule = Molecule(
        atoms=spec["atoms"],
        coordinates=spec["coordinates"],
        charge=0,
        multiplicity=1,
    )

    print(f"System        : {label}")
    print(f"Starting from : {len(spec['atoms'])} atoms, {basis} basis")
    print("Relaxing geometry (CPU) ...")

    start = time.perf_counter()
    result = optimize_geometry(
        molecule,
        method=args.method,
        basis=basis,
        fmax=args.fmax,
        steps=args.steps,
    )
    elapsed = time.perf_counter() - start

    print()
    print(result.summary())

    energies = [float(e) for e in result.energies_hartree]
    payload = {
        "system": label,
        "formula": result.formula,
        "method": result.method,
        "basis": result.basis,
        "converged": bool(result.converged),
        "n_steps": int(result.n_steps),
        "energies_hartree": energies,
        "energy_change_hartree": float(result.energy_change_hartree),
        "rmsd_angstrom": float(result.rmsd_angstrom),
        "fmax_ev_per_angstrom": float(args.fmax),
        "elapsed_seconds": elapsed,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        # Real optimizer output, not the bundled fallback. The plotting code
        # keys its "synthetic sample" warning off this flag.
        "synthetic": False,
    }

    course_work = Path(
        os.environ.get(
            "COURSE_WORK", f"/work/{os.environ['USER']}/ncshare-crash-course"
        )
    )
    output = course_work / "quantui" / f"geometry_optimization_{args.preset}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {output}")

    if not result.converged:
        raise SystemExit(
            "Optimization did not converge within the step budget; increase "
            "--steps or loosen --fmax."
        )


if __name__ == "__main__":
    main()
