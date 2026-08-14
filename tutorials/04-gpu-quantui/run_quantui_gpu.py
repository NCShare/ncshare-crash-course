#!/usr/bin/env python3
"""Run a tiny QuantUI calculation and record whether GPU offload occurred."""

from __future__ import annotations

import json
import os
import time
from importlib.metadata import version as package_version
from pathlib import Path

from quantui import Molecule, run_in_session


def main() -> None:
    molecule = Molecule(
        atoms=["O", "H", "H"],
        coordinates=[
            [0.0000, 0.0000, 0.0000],
            [0.7570, 0.5870, 0.0000],
            [-0.7570, 0.5870, 0.0000],
        ],
        charge=0,
        multiplicity=1,
    )

    start = time.perf_counter()
    result = run_in_session(
        molecule,
        method="RHF",
        basis="STO-3G",
        verbose=3,
    )
    elapsed = time.perf_counter() - start

    payload = {
        "formula": result.formula,
        "method": result.method,
        "basis": result.basis,
        "converged": bool(result.converged),
        "energy_hartree": float(result.energy_hartree),
        "homo_lumo_gap_ev": (
            None
            if result.homo_lumo_gap_ev is None
            else float(result.homo_lumo_gap_ev)
        ),
        "elapsed_seconds": elapsed,
        "gpu_used": bool(result.gpu_used),
        "gpu_name": result.gpu_name,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "course_image": os.environ.get("COURSE_IMAGE"),
        "quantui_version": package_version("quantui"),
        "quantui_source_checkout_commit": os.environ.get(
            "QUANTUI_SOURCE_CHECKOUT_COMMIT"
        ),
        "cpus_requested": os.environ.get("SLURM_CPUS_PER_TASK"),
    }

    course_work = Path(
        os.environ.get(
            "COURSE_WORK",
            f"/work/{os.environ['USER']}/ncshare-crash-course",
        )
    )
    output = course_work / "quantui" / "quantui_gpu_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(result.summary())
    print(json.dumps(payload, indent=2))
    print(f"Wrote {output}")

    if not result.converged:
        raise SystemExit("The SCF calculation did not converge.")
    if not result.gpu_used:
        raise SystemExit(
            "QuantUI completed without GPU offload; inspect `quantui gpu check`."
        )


if __name__ == "__main__":
    main()
