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
    python run_cpu_gpu_comparison.py --preset large
    python run_cpu_gpu_comparison.py --preset small --preset-large-basis 6-31G*
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Two contrasting systems. "small" should favour the CPU; "large" is the
# candidate for showing a GPU win. The exact crossover depends on the
# molecule, basis, method and hardware, so treat these as starting points
# and re-measure on the target GPU before teaching from them.
PRESETS = {
    "small": {
        "label": "H2O  RHF/STO-3G",
        "atoms": ["O", "H", "H"],
        "coordinates": [
            [0.0000, 0.0000, 0.0000],
            [0.7570, 0.5870, 0.0000],
            [-0.7570, 0.5870, 0.0000],
        ],
        "method": "RHF",
        "basis": "STO-3G",
    },
    "large": {
        # Benzene: enough basis functions at cc-pVDZ that the integral and
        # Fock work should outweigh transfer overhead on an H200.
        "label": "C6H6  RHF/cc-pVDZ",
        "atoms": ["C"] * 6 + ["H"] * 6,
        "coordinates": [
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
        "method": "RHF",
        "basis": "cc-pVDZ",
    },
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

    print("\n" + "=" * 60)
    print(f"  System        : {spec['label']}")
    print(f"  GPU device    : {gpu['gpu_name'] or 'n/a'}")
    print(f"  CPU wall time : {cpu['elapsed_seconds']:.2f} s")
    print(f"  GPU wall time : {gpu['elapsed_seconds']:.2f} s")
    print(f"  Ratio         : {speedup:.2f}x  ({faster} faster)")
    print(f"  Energies agree: {abs(cpu['energy_hartree'] - gpu['energy_hartree']) < 1e-6}")
    print("=" * 60)

    payload = {
        "system": spec["label"],
        "method": spec["method"],
        "basis": spec["basis"],
        "cpu": cpu,
        "gpu": gpu,
        "cpu_over_gpu": speedup,
        "faster": faster,
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
