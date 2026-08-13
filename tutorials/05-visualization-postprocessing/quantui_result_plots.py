"""Plot the QuantUI results produced in the GPU session.

The GPU session (tutorials/04-gpu-quantui) writes two kinds of JSON into
``$COURSE_WORK/quantui``:

* ``cpu_gpu_comparison_<preset>.json`` -- wall times for the CPU/GPU crossover,
  from ``run_cpu_gpu_comparison.py``; and
* ``geometry_optimization_<preset>.json`` -- an energy-per-step relaxation
  trajectory, from ``run_geometry_optimization.py``.

This module turns those into two figures: a grouped **bar chart** comparing CPU
and GPU wall time by system, and a **line plot** of the relaxation trajectory.

All of the real logic lives here rather than in the notebook, so it can be
diff-reviewed and reused. The companion notebook is only imports and calls.

Design notes (why the plots look the way they do):

* Two series (CPU, GPU) get a fixed two-colour categorical palette -- blue for
  GPU, orange for CPU -- validated colourblind-safe (OKLab CVD deltaE ~25).
* The bar chart stays on a **linear** axis with a value label on every bar.
  Wall times here span two orders of magnitude (sub-second to ~40 s); a log
  axis would break the "bar length = magnitude" reading, so the labels carry
  the small bars instead. The visual story -- the GPU bars barely grow while
  the CPU bar for the largest basis towers -- is the whole lesson.
* The trajectory is one series, so it needs no legend; the title names it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np

# --- House style (from the course data-viz palette) -------------------------
# Categorical slots 1 and 2; validated colourblind-safe as an adjacent pair.
GPU_COLOR = "#2a78d6"   # blue
CPU_COLOR = "#eb6834"   # orange
INK = "#0b0b0b"         # primary text
SECONDARY = "#52514e"   # secondary text
MUTED = "#898781"       # axes / ticks
GRID = "#e1e0d9"        # hairline gridlines
WARN = "#d03b3b"        # synthetic-sample warning

# The preset order is also the size order, left to right on the bar chart.
COMPARISON_PRESETS: tuple[str, ...] = ("small", "medium", "crossover", "large")

_THIS_DIR = Path(__file__).resolve().parent
_SAMPLE_DIR = _THIS_DIR / "data" / "sample_quantui"


# --- Data location ----------------------------------------------------------


def find_result_source(explicit: Optional[os.PathLike | str] = None) -> tuple[Path, bool]:
    """Return ``(directory, is_sample)`` to read QuantUI result JSON from.

    Resolution order mirrors the visualization notebook's own fallback logic:

    1. an explicit path, if given;
    2. ``$COURSE_WORK/quantui`` (where the GPU session wrote real results); and
    3. the bundled sample directory, so the lesson still runs after a queue
       delay -- exactly as the inoisy+ fallback dataset does.

    ``is_sample`` is ``True`` only for case 3, so callers can label the figure.
    """
    if explicit is not None:
        return Path(explicit), False

    course_work = os.environ.get("COURSE_WORK")
    if course_work:
        candidate = Path(course_work) / "quantui"
        has_real = candidate.is_dir() and (
            any(candidate.glob("cpu_gpu_comparison_*.json"))
            or any(candidate.glob("geometry_optimization_*.json"))
        )
        if has_real:
            return candidate, False

    return _SAMPLE_DIR, True


# --- CPU vs GPU wall-time bar chart -----------------------------------------


def load_comparison_results(
    source: Optional[os.PathLike | str] = None,
    presets: Sequence[str] = COMPARISON_PRESETS,
) -> list[dict]:
    """Load the ``cpu_gpu_comparison_<preset>.json`` files that exist, in order."""
    directory = Path(source) if source is not None else find_result_source()[0]
    results: list[dict] = []
    for preset in presets:
        path = directory / f"cpu_gpu_comparison_{preset}.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_preset"] = preset
            results.append(data)
    if not results:
        raise FileNotFoundError(
            f"No cpu_gpu_comparison_*.json found in {directory}. Run "
            "run_cpu_gpu_comparison.py in the GPU session first, or point at "
            "the bundled sample directory."
        )
    return results


def _style_axes(ax: plt.Axes) -> None:
    """Recessive spines, muted ticks, hairline horizontal grid."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=SECONDARY)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _short_system_label(system: str) -> str:
    """'C6H6  RHF/cc-pVDZ' -> 'C6H6\\nRHF/cc-pVDZ' for a two-line tick."""
    parts = system.split()
    if len(parts) >= 2:
        return f"{parts[0]}\n{' '.join(parts[1:])}"
    return system


def plot_compute_time_bars(
    results: Sequence[dict],
    ax: Optional[plt.Axes] = None,
    is_sample: bool = False,
) -> tuple[plt.Figure, plt.Axes]:
    """Grouped bar chart: CPU vs GPU wall time for each system."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(8.2, 4.8))
    else:
        fig = ax.figure

    systems = [r["system"] for r in results]
    cpu_times = [float(r["cpu"]["elapsed_seconds"]) for r in results]
    gpu_times = [float(r["gpu"]["elapsed_seconds"]) for r in results]

    x = np.arange(len(systems))
    width = 0.38
    gpu_bars = ax.bar(
        x - width / 2, gpu_times, width, label="GPU (1x H200)", color=GPU_COLOR
    )
    cpu_bars = ax.bar(
        x + width / 2, cpu_times, width, label="CPU", color=CPU_COLOR
    )

    # A value label on every bar: the small (fast) bars stay readable next to
    # the large-basis CPU bar, without resorting to a log axis.
    ax.bar_label(gpu_bars, fmt="%.2f", padding=2, color=SECONDARY, fontsize=8)
    ax.bar_label(cpu_bars, fmt="%.2f", padding=2, color=SECONDARY, fontsize=8)

    # Name the CPU allocation, since a speedup is meaningless without it.
    cores = str(results[0].get("cpus_requested", "?"))
    cpu_series_label = f"CPU ({cores} core{'s' if cores != '1' else ''})"
    ax.legend(
        [gpu_bars, cpu_bars],
        ["GPU (1x H200)", cpu_series_label],
        frameon=False,
        loc="upper left",
        labelcolor=SECONDARY,
    )

    ax.set_xticks(x)
    ax.set_xticklabels([_short_system_label(s) for s in systems], fontsize=8.5)
    ax.set_ylabel("Wall time (s)", color=SECONDARY)
    ax.set_ylim(0, max(cpu_times + gpu_times) * 1.18)
    title = "CPU vs GPU wall time by system"
    if is_sample:
        title += "   [SAMPLE DATA]"
    ax.set_title(title, color=INK, fontsize=13, fontweight="bold", loc="left")
    _style_axes(ax)
    fig.tight_layout()
    return fig, ax


# --- Geometry relaxation trajectory -----------------------------------------


def load_trajectory(
    source: Optional[os.PathLike | str] = None,
    preset: str = "water",
) -> Optional[dict]:
    """Load ``geometry_optimization_<preset>.json`` if present, else ``None``."""
    directory = Path(source) if source is not None else find_result_source()[0]
    path = directory / f"geometry_optimization_{preset}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def plot_relaxation_trajectory(
    traj: dict,
    ax: Optional[plt.Axes] = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Line plot: SCF energy at each BFGS step of a geometry relaxation."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
    else:
        fig = ax.figure

    energies = [float(e) for e in traj["energies_hartree"]]
    steps = np.arange(len(energies))

    ax.plot(
        steps,
        energies,
        color=GPU_COLOR,
        linewidth=2.0,
        marker="o",
        markersize=6,
        markerfacecolor=GPU_COLOR,
        markeredgecolor="white",
        markeredgewidth=1.0,
    )
    # Emphasise the converged endpoint.
    ax.plot(steps[-1], energies[-1], marker="o", markersize=9, color=GPU_COLOR)
    ax.annotate(
        f"{energies[-1]:.5f} Ha",
        (steps[-1], energies[-1]),
        textcoords="offset points",
        xytext=(-6, 10),
        ha="right",
        color=SECONDARY,
        fontsize=9,
    )

    ax.set_xlabel("Optimization step (BFGS)", color=SECONDARY)
    ax.set_ylabel("SCF energy (Hartree)", color=SECONDARY)
    ax.set_xticks(steps)

    formula = traj.get("formula", "?")
    method = traj.get("method", "?")
    basis = traj.get("basis", "?")
    de = traj.get("energy_change_hartree")
    rmsd = traj.get("rmsd_angstrom")
    subtitle_bits = [f"{formula}  {method}/{basis}"]
    if de is not None:
        subtitle_bits.append(f"deltaE = {de:+.4f} Ha")
    if rmsd is not None:
        subtitle_bits.append(f"RMSD = {rmsd:.3f} A")
    ax.set_title(
        "Geometry relaxation: energy vs step",
        color=INK,
        fontsize=13,
        fontweight="bold",
        loc="left",
        pad=26,
    )
    ax.text(
        0.0,
        1.015,
        "   ".join(subtitle_bits),
        transform=ax.transAxes,
        color=SECONDARY,
        fontsize=9.5,
    )
    _style_axes(ax)

    # The bundled sample is structurally valid but not a real optimizer run
    # (same role as the inoisy+ synthetic fallback). Say so, loudly.
    if traj.get("synthetic"):
        ax.text(
            0.5,
            0.5,
            "SYNTHETIC SAMPLE\nreplace with a real run",
            transform=ax.transAxes,
            color=WARN,
            fontsize=15,
            fontweight="bold",
            ha="center",
            va="center",
            alpha=0.35,
            rotation=18,
        )
    fig.tight_layout()
    return fig, ax


# --- Export helper ----------------------------------------------------------


def save_figure(fig: plt.Figure, path: os.PathLike | str) -> Path:
    """Save PNG (raster, for slides) and PDF (vector) next to each other."""
    path = Path(path)
    fig.savefig(path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    return path
