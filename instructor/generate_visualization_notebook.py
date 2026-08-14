#!/usr/bin/env python3
"""Generate the unified student scientific-visualization notebook.

The readable cell sources live here so changes to the lesson can be reviewed
without diffing notebook JSON. Run this script from any directory; it writes
the notebook into tutorials/05-visualization-postprocessing.
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "tutorials"
    / "05-visualization-postprocessing"
    / "scientific_visualization.ipynb"
)


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip() + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(text.strip() + "\n")


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.metadata.kernelspec = {
        "display_name": "Python 3 (NCShare course container)",
        "language": "python",
        "name": "python3",
    }
    nb.metadata.language_info = {"name": "python", "version": "3.11"}
    nb.cells = [
        md(
            r"""
# Scientific visualization: fields, performance, and scientific change

**Guided time:** 60 minutes

**Inputs:** inoisy HDF5 fields and QuantUI JSON results from the previous labs

This notebook is about making a small number of plots that answer clear
scientific questions. The examples come from two very different workflows:

- **inoisy:** a four-dimensional Gaussian random field and its positive
  emissivity post-processing; and
- **QuantUI:** CPU/GPU timing measurements and a molecular geometry-relaxation
  trajectory.

The science differs, but the plotting decisions transfer. We will make four
principal figures—two from each workflow—and use each to learn a different
lesson. Real course outputs are preferred. Clearly labelled bundled data keep
the lesson runnable when a job is still queued.
"""
        ),
        md(
            r"""
## Five learning objectives

By the end of the notebook, you should be able to:

1. **Begin with a question and the data's meaning.** Inspect shape, units,
   provenance, and missing values before choosing a plot.
2. **Match visual encoding to the task.** Use position for precise comparison,
   a spatial image for a field, and a connected line only when order matters.
3. **Use color and normalization deliberately.** Choose sequential or diverging
   color by data semantics, state the center, and disclose clipping or log scales.
4. **Make comparisons honest.** Name the denominator, keep conditions visible,
   distinguish a single timing from a distribution, and avoid unsupported claims.
5. **Communicate accessibly and reproducibly.** Label quantities and units,
   avoid color-only meaning, identify fallback data, and save sources and settings.

These objectives synthesize recurring goals in established visualization courses:
[Harvard CS 171](https://www.cs171.org/2024/index.html) emphasizes perception,
design, comprehension, and communication;
[University of Utah CS 6630](https://www.sci.utah.edu/~miriah/cs6630) combines
spatial/scalar data, visual encodings, color, critique, and exploratory analysis;
and [University of Washington CSE 442](https://courses.cs.washington.edu/courses/cse442/24wi/)
frames visualization as perceptual inference and covers design, color,
uncertainty, interaction, and evaluation.

The goal here is not to survey every chart type. It is to practice a compact
decision process: **question → data → encoding → checks → communication**.
"""
        ),
        code(
            r"""
from pathlib import Path
import json
import os
import platform
import sys

import h5py
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, TwoSlopeNorm
import numpy as np

mpl.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 120,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    }
)

# A small colorblind-aware categorical palette. Marker shape and position also
# carry meaning, so the CPU/GPU distinction does not rely on color alone.
BLUE = "#2A78D6"
ORANGE = "#D95F02"
GRAY = "#5B5B5B"
GRID = "#DEDEDE"

print("Python:", sys.version.split()[0])
print("NumPy:", np.__version__)
print("h5py:", h5py.__version__)
print("Matplotlib:", mpl.__version__)
"""
        ),
        md(
            r"""
## 0. Locate the data and state what is real

A figure is evidence only if we know what data it shows. This cell searches in
the same order used throughout the course:

1. an explicit environment-variable override;
2. results produced in `$COURSE_WORK`; and
3. a bundled fallback.

The inoisy fallback matches the real HDF5 schema but is synthetic. The bundled
QuantUI timing samples are real NCShare measurements; the bundled geometry
trajectory is synthetic and carries a warning in its JSON and plot.
"""
        ),
        code(
            r"""
def find_course_root(start: Path) -> Path:
    # Walk upward until the course README and tutorials directory are found.
    for candidate in (start, *start.parents):
        if (candidate / "README.md").exists() and (candidate / "tutorials").exists():
            return candidate
    raise FileNotFoundError("Open this notebook from inside the course repository.")


def newest(paths):
    # Return the most recently modified path, or None for an empty iterable.
    paths = list(paths)
    return max(paths, key=lambda path: path.stat().st_mtime) if paths else None


course_root = find_course_root(Path.cwd().resolve())
lesson_dir = course_root / "tutorials" / "05-visualization-postprocessing"
data_dir = lesson_dir / "data"

default_work = Path(f"/work/{os.environ.get('USER', 'student')}/ncshare-crash-course")
course_work = Path(os.environ.get("COURSE_WORK", default_work)).expanduser()
if not course_work.parent.exists():
    # Local testing outside NCShare remains inside the repository.
    course_work = course_root / "artifacts"
course_work.mkdir(parents=True, exist_ok=True)

# Raw inoisy field.
raw_override = os.environ.get("INOISY_H5")
raw_real = newest(course_work.glob("inoisy/four-ranks/*.h5"))
if raw_override:
    raw_path = Path(raw_override).expanduser().resolve()
    raw_kind = "explicit INOISY_H5"
elif raw_real:
    raw_path = raw_real.resolve()
    raw_kind = "student four-rank result"
else:
    raw_path = (data_dir / "sample_inoisy4d_lowres.h5").resolve()
    raw_kind = "SYNTHETIC bundled inoisy fallback"

# Post-processed inoisy emissivity.
processed_override = os.environ.get("INOISY_EMISSIVITY_H5")
processed_real = newest(course_work.glob("inoisy/postprocessed/*emissivity*.h5"))
if processed_override:
    processed_path = Path(processed_override).expanduser().resolve()
    processed_kind = "explicit INOISY_EMISSIVITY_H5"
elif processed_real:
    processed_path = processed_real.resolve()
    processed_kind = "student post-processed result"
else:
    processed_path = (data_dir / "sample_inoisy4d_emissivity.h5").resolve()
    processed_kind = "SYNTHETIC bundled emissivity fallback"

# QuantUI timing and trajectory inputs are selected independently. A normal GPU
# verification creates quantui_gpu_result.json, but that file alone is not a
# timing sweep and must not suppress the bundled timing fallback.
quantui_override = os.environ.get("QUANTUI_RESULTS")
quantui_override_dir = (
    Path(quantui_override).expanduser().resolve() if quantui_override else None
)
quantui_real_dir = (course_work / "quantui").resolve()
quantui_sample_dir = (data_dir / "sample_quantui").resolve()

if quantui_override_dir is not None:
    comparison_dir = quantui_override_dir
    comparison_kind = "explicit QUANTUI_RESULTS"
elif quantui_real_dir.is_dir() and any(
    quantui_real_dir.glob("cpu_gpu_comparison_*.json")
):
    comparison_dir = quantui_real_dir
    comparison_kind = "student CPU/GPU comparison results"
else:
    comparison_dir = quantui_sample_dir
    comparison_kind = "bundled real NCShare timing samples"

trajectory_candidates = [
    directory / "geometry_optimization_water.json"
    for directory in (quantui_override_dir, quantui_real_dir)
    if directory is not None
]
trajectory_path = next((path for path in trajectory_candidates if path.is_file()), None)
if trajectory_path is None:
    trajectory_path = quantui_sample_dir / "geometry_optimization_water.json"
    trajectory_kind = "SYNTHETIC bundled geometry trajectory"
else:
    trajectory_path = trajectory_path.resolve()
    trajectory_kind = "student geometry trajectory"

for path in (raw_path, processed_path, comparison_dir, trajectory_path):
    if not path.exists():
        raise FileNotFoundError(path)

print(f"inoisy raw:       {raw_kind}\n  {raw_path}")
print(f"inoisy processed: {processed_kind}\n  {processed_path}")
print(f"QuantUI timings:  {comparison_kind}\n  {comparison_dir}")
print(f"QuantUI geometry: {trajectory_kind}\n  {trajectory_path}")
"""
        ),
        md(
            r"""
## Objective 1 — Ask a question, then inspect the data

Our first inoisy question is:

> **At one time and height, where are fluctuations above and below the field's
> reference value?**

That question needs a two-dimensional spatial slice of a signed scalar field.
It does not require loading the complete four-dimensional array. HDF5 exposes
`shape` and `dtype` without reading the data; slicing reads only the requested
plane. This matters when a production field is larger than memory.
"""
        ),
        code(
            r"""
def scalar(handle: h5py.File, path: str) -> float:
    return float(np.asarray(handle[path]))


with h5py.File(raw_path, "r") as handle:
    dataset = handle["/data/data_raw"]
    shape = tuple(dataset.shape)
    dtype = dataset.dtype
    fallback_flag = bool(handle["/params"].attrs.get("course_fallback", False))
    x_start, y_start, z_start = (
        scalar(handle, "/params/x1start"),
        scalar(handle, "/params/x2start"),
        scalar(handle, "/params/x3start"),
    )
    dx, dy, dz = (
        scalar(handle, "/params/dx1"),
        scalar(handle, "/params/dx2"),
        scalar(handle, "/params/dx3"),
    )
    t_start, dt = scalar(handle, "/params/x0start"), scalar(handle, "/params/dx0")

if len(shape) != 4:
    raise ValueError(f"Expected [time, x, y, z], found {shape}")

nt, nx, ny, nz = shape
time_index = min(2, nt - 1)
z_index = nz // 2

with h5py.File(raw_path, "r") as handle:
    # Only one x-y plane enters memory.
    raw_xy = np.asarray(handle["/data/data_raw"][time_index, :, :, z_index])

if not np.isfinite(raw_xy).all():
    raise ValueError("Selected inoisy slice contains NaN or infinite values.")

times = t_start + dt * np.arange(nt)
x_edges = x_start + dx * np.arange(nx + 1)
y_edges = y_start + dy * np.arange(ny + 1)
extent_xy = [x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]]
raw_bound = float(np.percentile(np.abs(raw_xy), 98))

print("Dataset shape [time, x, y, z]:", shape)
print("Stored dtype:", dtype)
print("Synthetic flag in file:", fallback_flag)
print(f"Full array would occupy {np.prod(shape) * dtype.itemsize / 1024**2:.3f} MiB")
print(f"Selected t={times[time_index]:.3g}; mid-plane z≈{z_start + (z_index + 0.5)*dz:.3g}")
print(f"Slice min / median / max: {raw_xy.min():.3g} / {np.median(raw_xy):.3g} / {raw_xy.max():.3g}")
"""
        ),
        md(
            r"""
## Figure 1 — A spatial encoding for a signed field

Position in the image represents physical position. Color represents the scalar
value. Because zero separates positive and negative fluctuations, we use a
**diverging** map centered exactly at zero. Symmetric limits give equal visual
weight to equal-magnitude deviations.

The limits use the 98th percentile of absolute values. This prevents a few
extremes from flattening all visible contrast, but it also saturates the most
extreme 2% by magnitude. The title discloses that choice.
"""
        ),
        code(
            r"""
fig_inoisy_field, ax = plt.subplots(figsize=(6.3, 5.1), constrained_layout=True)
image = ax.imshow(
    raw_xy.T,
    origin="lower",
    extent=extent_xy,
    cmap="RdBu_r",
    norm=TwoSlopeNorm(vmin=-raw_bound, vcenter=0.0, vmax=raw_bound),
    aspect="equal",
)
ax.set(
    title=f"inoisy signed field at t={times[time_index]:.3g} (98% |value| limit)",
    xlabel="x [code units]",
    ylabel="y [code units]",
)
fig_inoisy_field.colorbar(image, ax=ax, label="Raw GRF [arbitrary units]")
if "SYNTHETIC" in raw_kind:
    ax.text(
        0.02, 0.02, "SYNTHETIC FALLBACK", transform=ax.transAxes,
        color="black", fontsize=9, fontweight="bold",
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )
plt.show()
"""
        ),
        md(
            r"""
**Check the design:** A sequential map would imply one ordered progression and
hide the special role of zero. A rainbow map would add lightness boundaries
that are not boundaries in the simulation. If zero were not meaningful, a
diverging map would be decoration rather than information.

## Objectives 2 and 3 — Match encoding, color, and normalization to meaning

The post-processor standardizes the GRF and transforms it into positive
emissivity. The next question is:

> **How does the same structure appear before and after the positive,
> multiplicative emissivity transformation?**

These quantities require different color logic. Standardized fluctuations are
signed deviations measured in standard deviations, so zero-centered diverging
color remains appropriate. Emissivity is positive and spans a wide dynamic
range, so ordered sequential color with logarithmic normalization is more
informative. A log scale is valid only for positive values.
"""
        ),
        code(
            r"""
with h5py.File(processed_path, "r") as handle:
    data_names = sorted(handle["/data"].keys())
    fhat_names = [name for name in data_names if name.startswith("Fhat_")]
    emissivity_names = [name for name in data_names if name.startswith("emissivity_")]
    processed_times = np.asarray(handle["/data/time"][:])
    processed_x_start = scalar(handle, "/params/x1start")
    processed_y_start = scalar(handle, "/params/x2start")
    processed_dx = scalar(handle, "/params/dx1")
    processed_dy = scalar(handle, "/params/dx2")

if not fhat_names or not emissivity_names:
    raise ValueError("Processed file lacks standardized or emissivity datasets.")

processed_index = min(2, len(fhat_names) - 1, len(emissivity_names) - 1)
with h5py.File(processed_path, "r") as handle:
    # Processed volumes are stored [z, y, x].
    fhat_zyx = np.asarray(handle[f"/data/{fhat_names[processed_index]}"])
    emissivity_zyx = np.asarray(handle[f"/data/{emissivity_names[processed_index]}"])

processed_z = fhat_zyx.shape[0] // 2
fhat_yx = fhat_zyx[processed_z]
emissivity_yx = emissivity_zyx[processed_z]

processed_ny, processed_nx = fhat_yx.shape
processed_x_edges = processed_x_start + processed_dx * np.arange(processed_nx + 1)
processed_y_edges = processed_y_start + processed_dy * np.arange(processed_ny + 1)
processed_extent = [
    processed_x_edges[0], processed_x_edges[-1],
    processed_y_edges[0], processed_y_edges[-1],
]

fhat_finite = fhat_yx[np.isfinite(fhat_yx)]
emissivity_positive = emissivity_yx[np.isfinite(emissivity_yx) & (emissivity_yx > 0)]
if not len(fhat_finite) or not len(emissivity_positive):
    raise ValueError("Processed slice lacks finite standardized or positive emissivity values.")

fhat_bound = float(np.percentile(np.abs(fhat_finite), 98))
em_limits = np.percentile(emissivity_positive, [2, 98]).astype(float)
if em_limits[0] == em_limits[1]:
    em_limits[1] = np.nextafter(em_limits[1], np.inf)

print(f"Standardized field: median={np.median(fhat_finite):.3g}, 98% |value|={fhat_bound:.3g}")
print(f"Positive emissivity: 2nd–98th percentiles={em_limits[0]:.3g}, {em_limits[1]:.3g}")
"""
        ),
        code(
            r"""
fig_inoisy_transform, axes = plt.subplots(
    1, 2, figsize=(10.8, 4.5), constrained_layout=True, sharex=True, sharey=True
)

im0 = axes[0].imshow(
    fhat_yx,
    origin="lower",
    extent=processed_extent,
    cmap="RdBu_r",
    norm=TwoSlopeNorm(vmin=-fhat_bound, vcenter=0.0, vmax=fhat_bound),
    aspect="equal",
)
axes[0].set(
    title="Standardized fluctuation: diverging, centered at 0",
    xlabel="x [code units]",
    ylabel="y [code units]",
)
fig_inoisy_transform.colorbar(im0, ax=axes[0], label=r"$\hat{F}$ [standard deviations]")

im1 = axes[1].imshow(
    emissivity_yx,
    origin="lower",
    extent=processed_extent,
    cmap="magma",
    norm=LogNorm(vmin=em_limits[0], vmax=em_limits[1]),
    aspect="equal",
)
axes[1].set(
    title="Positive emissivity: sequential, logarithmic",
    xlabel="x [code units]",
)
fig_inoisy_transform.colorbar(
    im1, ax=axes[1], label="Emissivity [arbitrary units; log color scale]"
)
fig_inoisy_transform.suptitle(
    f"Post-processed time t={processed_times[processed_index]:.3g}, mid-plane; "
    "displayed limits use 2nd–98th percentiles"
)
if "SYNTHETIC" in processed_kind:
    fig_inoisy_transform.text(
        0.5, 0.01, "SYNTHETIC POST-PROCESSING FALLBACK",
        ha="center", fontsize=9, fontweight="bold",
    )
plt.show()
"""
        ),
        md(
            r"""
**Check the design:** The two color bars are intentionally not shared: they
encode different quantities and transformations. Sharing one scale would be a
false comparison. What is comparable is the location of spatial structure.

## Objective 4 — Make a fair CPU/GPU comparison

The QuantUI question is:

> **For these calculations and this allocation, where does one H200 become
> faster than the allocated CPU cores?**

The JSON files provide paired measurements of the same calculation. A connected
dot plot shows both times without implying that categories fill an area, and a
logarithmic time axis keeps sub-second and tens-of-seconds measurements legible.
Equal vertical distances on a log axis represent equal **ratios**.

This is a crossover demonstration, not a performance study: each value is one
run, so there is no estimate of run-to-run variability and no justification for
error bars. A publication-quality benchmark would repeat runs, report a robust
summary and spread, control warm-up, and document node occupancy.
"""
        ),
        code(
            r"""
PRESET_ORDER = ("small", "medium", "crossover", "large")
comparison = []
comparison_paths = []
for preset in PRESET_ORDER:
    path = comparison_dir / f"cpu_gpu_comparison_{preset}.json"
    if path.exists():
        record = json.loads(path.read_text(encoding="utf-8"))
        record["_preset"] = preset
        comparison.append(record)
        comparison_paths.append(path)

if not comparison:
    raise FileNotFoundError(
        f"No cpu_gpu_comparison_*.json found in {comparison_dir}. "
        "Set QUANTUI_RESULTS to a directory containing a timing sweep or unset "
        "it to use the bundled measurements."
    )

systems = [record["system"] for record in comparison]
cpu_times = np.array([float(record["cpu"]["elapsed_seconds"]) for record in comparison])
gpu_times = np.array([float(record["gpu"]["elapsed_seconds"]) for record in comparison])
speedups = cpu_times / gpu_times
core_counts = {str(record.get("cpus_requested", "?")) for record in comparison}
core_label = next(iter(core_counts)) if len(core_counts) == 1 else "varying"

# If real runs recorded energies, verify that paired calculations agree.
energy_differences = []
for record in comparison:
    cpu_e = record["cpu"].get("energy_hartree")
    gpu_e = record["gpu"].get("energy_hartree")
    if cpu_e is not None and gpu_e is not None:
        energy_differences.append(abs(float(cpu_e) - float(gpu_e)))

print(f"Loaded {len(comparison)} paired measurements from {comparison_dir}")
print(f"CPU denominator: {core_label} requested core(s); GPU denominator: 1 H200")
if energy_differences:
    print(f"Largest CPU/GPU energy difference: {max(energy_differences):.3e} Hartree")
else:
    print("Bundled timing samples omit energies; live runs should agree within 1e-6 Hartree.")
"""
        ),
        code(
            r"""
def short_system_label(text: str) -> str:
    parts = text.split()
    return f"{parts[0]}\n{' '.join(parts[1:])}" if len(parts) > 1 else text


x = np.arange(len(systems))
fig_quantui_timing, ax = plt.subplots(figsize=(8.8, 5.0), constrained_layout=True)

for xi, cpu, gpu in zip(x, cpu_times, gpu_times):
    ax.plot([xi, xi], [cpu, gpu], color="#A9A9A9", linewidth=1.5, zorder=1)

ax.scatter(
    x, cpu_times, s=75, color=ORANGE, marker="s", label=f"CPU ({core_label} requested cores)", zorder=3
)
ax.scatter(
    x, gpu_times, s=85, color=BLUE, marker="o", label="GPU (1 H200)", zorder=3
)

for xi, cpu, gpu, ratio in zip(x, cpu_times, gpu_times, speedups):
    faster = f"GPU {ratio:.1f}× faster" if ratio > 1 else f"CPU {1/ratio:.1f}× faster"
    ax.text(xi, max(cpu, gpu) * 1.16, faster, ha="center", va="bottom", fontsize=8.5)

ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels([short_system_label(system) for system in systems])
ax.set(
    title="QuantUI crossover: paired wall times for the same calculation",
    xlabel="Molecule and electronic-structure calculation",
    ylabel="Wall time [s; logarithmic axis]",
)
ax.grid(axis="y", which="both", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left")
if "bundled" in comparison_kind:
    ax.text(
        0.99, 0.02, "BUNDLED NCShare TIMINGS", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=8.5, color=GRAY,
    )
plt.show()
"""
        ),
        md(
            r"""
**Interpretation:** The plot supports a conditional statement: for the stated
systems and a comparison of one H200 against the stated CPU allocation, the
crossover occurs near the point where the markers meet. It does **not** support
“GPUs are always faster.” Changing CPU cores, method, basis, molecule, software,
or hardware can move the crossover.

## Objective 2 revisited — Show change with a line, not a category chart

Our final question is:

> **Does the molecular geometry optimization make large improvements first and
> then level off near its final energy?**

Optimization steps are ordered, so connecting them is meaningful. Plotting
absolute energies would devote most of the axis to a large baseline. Instead we
subtract the final recorded energy and show the remaining energy above that
reference in milli-Hartree. This transformation makes progress visible, and the
axis label states exactly what was changed.
"""
        ),
        code(
            r"""
trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
energies = np.asarray(trajectory["energies_hartree"], dtype=float)
steps = np.arange(len(energies))
delta_millihartree = 1000.0 * (energies - energies[-1])

print("Trajectory source:", trajectory_path)
print("Source type:", trajectory_kind)
print("Synthetic:", bool(trajectory.get("synthetic", False)))
print("Converged flag:", trajectory.get("converged"))
print(f"Recorded energy change: {trajectory.get('energy_change_hartree', np.nan):+.5f} Hartree")
"""
        ),
        code(
            r"""
fig_quantui_relaxation, ax = plt.subplots(figsize=(7.6, 4.7), constrained_layout=True)
ax.plot(
    steps,
    delta_millihartree,
    color=BLUE,
    linewidth=2,
    marker="o",
    markersize=6,
    markerfacecolor="white",
    markeredgewidth=1.5,
)
ax.axhline(0, color=GRAY, linewidth=1, linestyle="--")
ax.set(
    title=f"Geometry relaxation: {trajectory.get('system', 'molecule')}",
    xlabel="Optimization step [ordered iteration]",
    ylabel=r"Energy above final recorded value [$10^{-3}$ Hartree]",
)
ax.set_xticks(steps)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.annotate(
    "final recorded value",
    xy=(steps[-1], 0),
    xytext=(-12, 24),
    textcoords="offset points",
    ha="right",
    arrowprops={"arrowstyle": "->", "color": GRAY},
    color=GRAY,
)
if trajectory.get("synthetic"):
    ax.text(
        0.5, 0.52, "SYNTHETIC TRAJECTORY\nreplace before scientific use",
        transform=ax.transAxes, ha="center", va="center",
        fontsize=14, fontweight="bold", color="#B22222", alpha=0.45, rotation=12,
    )
plt.show()
"""
        ),
        md(
            r"""
**Check the design:** Connecting the points is justified because step 3 follows
step 2. It would be misleading for unordered basis-set categories. The curve's
shape shows progress, but the final plotted point is only the final **recorded**
energy; convergence also depends on the optimizer's force threshold and
`converged` flag.

## Objective 5 — Export a reproducible record

A useful figure needs enough context to regenerate and interpret it. The next
cell exports each figure as PNG (convenient for slides/web) and PDF (scalable
text and lines), then writes one JSON manifest containing source paths, fallback
status, selection indices, plotting choices, and software versions.

The manifest does not make a scientific analysis automatically reproducible;
it makes important hidden choices visible and gives a future reader a place to
start.
"""
        ),
        code(
            r"""
figure_dir = course_work / "visualization"
figure_dir.mkdir(parents=True, exist_ok=True)

figures = {
    "inoisy_signed_field": fig_inoisy_field,
    "inoisy_transformation": fig_inoisy_transform,
    "quantui_cpu_gpu_crossover": fig_quantui_timing,
    "quantui_geometry_relaxation": fig_quantui_relaxation,
}

for name, figure in figures.items():
    figure.savefig(figure_dir / f"{name}.png", dpi=200)
    figure.savefig(figure_dir / f"{name}.pdf")

manifest = {
    "notebook": "scientific_visualization.ipynb",
    "inputs": {
        "inoisy_raw": {"path": str(raw_path), "kind": raw_kind},
        "inoisy_processed": {"path": str(processed_path), "kind": processed_kind},
        "quantui_comparison_directory": {
            "path": str(comparison_dir), "kind": comparison_kind
        },
        "quantui_comparisons": [str(path) for path in comparison_paths],
        "quantui_trajectory": {
            "path": str(trajectory_path), "kind": trajectory_kind
        },
    },
    "selections": {
        "inoisy_raw_time_index": int(time_index),
        "inoisy_raw_z_index": int(z_index),
        "inoisy_processed_time_index": int(processed_index),
        "inoisy_processed_z_index": int(processed_z),
    },
    "visual_choices": {
        "inoisy_raw_limit": "symmetric 98th percentile of absolute selected-slice values",
        "processed_limits": "2nd–98th percentile of each selected slice",
        "emissivity_normalization": "logarithmic",
        "timing_axis": "logarithmic",
        "relaxation_reference": "final recorded energy",
    },
    "software": {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "h5py": h5py.__version__,
        "matplotlib": mpl.__version__,
    },
}

manifest_path = figure_dir / "scientific_visualization_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print(f"Wrote {2 * len(figures)} figure files and manifest:")
print(manifest_path)
"""
        ),
        md(
            r"""
## Final critique: five questions for every scientific figure

1. **Question:** What precise claim or comparison should the reader see?
2. **Encoding:** Do position, color, area, and connection match the data and task?
3. **Scale:** Are centers, logarithms, clipping, transformations, and units explicit?
4. **Limits:** What was sliced, omitted, approximated, synthetic, or measured only once?
5. **Reproducibility:** Can another person identify the data, code, environment, and settings?

### One short exercise

Choose **one** figure and change **one** defensible design decision—for example,
select another inoisy time, use fixed emissivity limits to compare two frames,
or add repeated QuantUI timings and uncertainty intervals. In one Markdown
sentence, state the question your change answers and why the new encoding is
appropriate. Do not add decoration without a scientific purpose.

Further practical guidance:
[Matplotlib colormaps](https://matplotlib.org/stable/users/explain/colors/colormaps.html) ·
[Matplotlib normalization](https://matplotlib.org/stable/users/explain/colors/colormapnorms.html) ·
[Ten Simple Rules for Better Figures](https://doi.org/10.1371/journal.pcbi.1003833)
"""
        ),
    ]

    nbf.write(nb, OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
