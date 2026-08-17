#!/usr/bin/env python3
"""Run the same QuantUI calculation on CPU and on GPU and compare wall times.

The point of this script is not "the GPU is faster". It is to let students
find the *crossover*: small systems are usually faster on the CPU because
kernel-launch and host/device transfer overhead dominates the arithmetic,
while larger basis sets tip the balance the other way.

Each leg runs in its own subprocess. That is required, not stylistic:
``quantui.gpu_offload.is_gpu_available()`` caches its probe on first use, so
``QUANTUI_DISABLE_GPU`` has to be set before QuantUI or gpu4pyscf is
imported. Setting it inside an already-running interpreter would be ignored.
This mirrors what ``quantui.benchmarks`` does internally.

Usage:
    python run_cpu_gpu_comparison.py --preset small
    python run_cpu_gpu_comparison.py --preset crossover
    python run_cpu_gpu_comparison.py --preset large
    python run_cpu_gpu_comparison.py --preset small --basis cc-pVDZ
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from importlib.metadata import version as package_version
from pathlib import Path

# Measured on an NCShare H200 (driver 580.126.20) on
# 2026-08-05, 1 GPU against 6 affinity-confirmed CPU cores:
#
#   H2O  / STO-3G    GPU 1.80 s   CPU  0.35 s   0.20x
#   C6H6 / 6-31G     GPU 2.69 s   CPU  0.77 s   0.29x
#   C6H6 / cc-pVDZ   GPU 2.86 s   CPU  2.74 s   0.96x  <- the crossover
#   C6H6 / cc-pVTZ   GPU 7.07 s   CPU 42.41 s   6.00x
#
# Note that the GPU wall time barely moves across the three pre-large presets:
# fixed launch and transfer overhead, and it is the whole point of the
# exercise. Only cc-pVTZ makes the arithmetic large enough for the device
# to win. "crossover" below is a near-tie by design -- it is where the two
# curves cross, not a GPU victory.
_BENZENE = (
    ["C"] * 6 + ["H"] * 6,
    [
        [0.0000, 1.3970, 0.0000],
        [1.2098, 0.6985, 0.0000],
        [1.2098, -0.6985, 0.0000],
        [0.0000, -1.3970, 0.0000],
        [-1.2098, -0.6985, 0.0000],
        [-1.2098, 0.6985, 0.0000],
        [0.0000, 2.4810, 0.0000],
        [2.1486, 1.2405, 0.0000],
        [2.1486, -1.2405, 0.0000],
        [0.0000, -2.4810, 0.0000],
        [-2.1486, -1.2405, 0.0000],
        [-2.1486, 1.2405, 0.0000],
    ],
)
_WATER = (
    ["O", "H", "H"],
    [
        [0.0000, 0.0000, 0.0000],
        [0.7570, 0.5870, 0.0000],
        [-0.7570, 0.5870, 0.0000],
    ],
)


def _preset(label, geom, basis):
    atoms, coords = geom
    return {
        "label": label,
        "atoms": atoms,
        "coordinates": coords,
        "method": "RHF",
        "basis": basis,
    }


PRESETS = {
    # CPU wins comfortably -- overhead dominates.
    "small": _preset("H2O  RHF/STO-3G", _WATER, "STO-3G"),
    # Still CPU, but the gap has narrowed.
    "medium": _preset("C6H6  RHF/6-31G", _BENZENE, "6-31G"),
    # Near-tie: this is the crossover, not a GPU win.
    "crossover": _preset("C6H6  RHF/cc-pVDZ", _BENZENE, "cc-pVDZ"),
    # GPU wins decisively.
    "large": _preset("C6H6  RHF/cc-pVTZ", _BENZENE, "cc-pVTZ"),
}


def run_leg(spec: dict, force_cpu: bool) -> dict:
    """Execute one leg in a child process and return its parsed result."""
    env = dict(os.environ)
    if force_cpu:
        # Must be set before the child imports quantui / gpu4pyscf.
        env["QUANTUI_DISABLE_GPU"] = "1"
    else:
        env.pop("QUANTUI_DISABLE_GPU", None)

    proc = subprocess.run(
        [sys.executable, __file__, "--_leg", json.dumps(spec)],
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": proc.stderr.strip()[-2000:],
        }
    # The child prints one JSON object on the final non-empty stdout line;
    # PySCF's own verbose output precedes it.
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return json.loads(lines[-1])


def _child(spec: dict) -> int:
    """Entry point for the subprocess: run one calculation, print JSON."""
    from quantui import Molecule, run_in_session

    molecule = Molecule(
        atoms=spec["atoms"],
        coordinates=spec["coordinates"],
        charge=0,
        multiplicity=1,
    )
    start = time.perf_counter()
    result = run_in_session(
        molecule,
        method=spec["method"],
        basis=spec["basis"],
        verbose=0,
    )
    elapsed = time.perf_counter() - start

    print(
        json.dumps(
            {
                "ok": True,
                "elapsed_seconds": elapsed,
                "gpu_used": bool(result.gpu_used),
                "gpu_name": result.gpu_name,
                "converged": bool(result.converged),
                "energy_hartree": float(result.energy_hartree),
                "n_iterations": result.n_iterations,
            }
        )
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="small")
    parser.add_argument("--basis", help="Override the preset's basis set.")
    parser.add_argument("--_leg", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args._leg:
        raise SystemExit(_child(json.loads(args._leg)))

    spec = dict(PRESETS[args.preset])
    if args.basis:
        spec["basis"] = args.basis
        spec["label"] = f"{spec['label'].split()[0]}  {spec['method']}/{args.basis}"

    print(f"System: {spec['label']}")
    print("Running GPU leg ...")
    gpu = run_leg(spec, force_cpu=False)
    print("Running CPU leg ...")
    cpu = run_leg(spec, force_cpu=True)

    for name, leg in (("GPU", gpu), ("CPU", cpu)):
        if not leg.get("ok"):
            print(f"\n{name} leg failed:\n{leg.get('error')}")
            raise SystemExit(1)

    # A GPU leg that silently fell back to the CPU would make the comparison
    # meaningless, so say so rather than reporting a suspiciously equal time.
    if not gpu["gpu_used"]:
        print(
            "\nWARNING: the GPU leg reported gpu_used=false, so it ran on the "
            "CPU. Check `quantui gpu check` and that this method is supported "
            "before drawing any conclusion from the timings below."
        )

    speedup = cpu["elapsed_seconds"] / gpu["elapsed_seconds"]
    faster = "GPU" if speedup > 1 else "CPU"

    # A speedup is meaningless without the CPU allocation it was measured
    # against, so print the allocation next to the number every time.
    cores = os.environ.get("SLURM_CPUS_PER_TASK", "?")
    try:
        affinity = len(os.sched_getaffinity(0))  # type: ignore[attr-defined]
    except AttributeError:  # not available on Windows
        affinity = None

    print("\n" + "=" * 60)
    print(f"  System        : {spec['label']}")
    print(f"  GPU device    : {gpu['gpu_name'] or 'n/a'}")
    print(f"  CPU allocation: {cores} core(s) requested"
          + (f", affinity mask shows {affinity}" if affinity is not None else ""))
    print(f"  CPU wall time : {cpu['elapsed_seconds']:.2f} s")
    print(f"  GPU wall time : {gpu['elapsed_seconds']:.2f} s")
    print(f"  CPU/GPU time  : {speedup:.2f}x  ({faster} faster)")
    print(f"  Energies agree: {abs(cpu['energy_hartree'] - gpu['energy_hartree']) < 1e-6}")
    print("=" * 60)

    # os.cpu_count() would report every core on the node, not the ones Slurm
    # granted. If the affinity mask disagrees with the request, OpenMP may
    # have oversubscribed and the CPU timing above is not trustworthy.
    if affinity is not None and cores != "?" and str(affinity) != cores:
        print(
            f"\nWARNING: requested {cores} cores but the affinity mask shows "
            f"{affinity}. The CPU leg may have been over- or under-subscribed, "
            "which distorts the ratio. Treat these timings as indicative only."
        )

    payload = {
        "system": spec["label"],
        "method": spec["method"],
        "basis": spec["basis"],
        "quantui_version": package_version("quantui"),
        "quantui_source_checkout_commit": (
            Path("/opt/course-build/quantui-commit.txt").read_text().strip()
            if Path("/opt/course-build/quantui-commit.txt").is_file()
            else None
        ),
        "course_image": os.environ.get("COURSE_IMAGE"),
        "cpu": cpu,
        "gpu": gpu,
        "cpu_over_gpu": speedup,
        "faster": faster,
        "cpus_requested": cores,
        "cpu_affinity": affinity,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    course_work = Path(
        os.environ.get(
            "COURSE_WORK", f"/work/{os.environ['USER']}/ncshare-crash-course"
        )
    )
    output = course_work / "quantui" / f"cpu_gpu_comparison_{args.preset}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
