#!/usr/bin/env python3
"""Generate the student visualization notebook from readable cell sources."""

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
        "display_name": "Python (NCShare Visualization)",
        "language": "python",
        "name": "ncshare-viz",
    }
    nb.metadata.language_info = {"name": "python", "version": "3.11"}
    nb.cells = [
        md(
            r"""
# Scientific visualization and post-processing with inoisy+

**Guided time:** 60 minutes

This lab treats the inoisy+ result as a scientific data product: a four-dimensional
Gaussian random field (GRF) stored as `[time, x, y, z]`. We will inspect it lazily,
make diagnostic plots, run the unmodified upstream emissivity converter, and export
a figure whose scales and provenance are explicit.

The astrophysics is context, not a prerequisite. The computing habits transfer to
many simulations, images, volumes, and time series.

Helpful references:
[Matplotlib quick start](https://matplotlib.org/stable/users/explain/quick_start.html) ·
[Choosing colormaps](https://matplotlib.org/stable/users/explain/colors/colormaps.html) ·
[Seaborn palettes](https://seaborn.pydata.org/tutorial/color_palettes.html) ·
[Fundamentals of Data Visualization](https://clauswilke.com/dataviz/)
"""
        ),
        md(
            """
## Lab map

1. Find and inspect the HDF5 input.
2. Read one slice rather than the whole 4D field.
3. Match visual encodings and color maps to the data.
4. Run the GRF-to-emissivity post-processing code.
5. Compare raw, standardized, and positive emissivity fields.
6. Export and document a reproducible figure.
"""
        ),
        code(
            r"""
from pathlib import Path
import json
import os
import shlex
import subprocess
import sys

import h5py
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, TwoSlopeNorm
import numpy as np
import pandas as pd
import seaborn as sns

# One explicit style block makes notebook and exported figures consistent.
mpl.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "figure.dpi": 120,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    }
)
sns.set_palette("colorblind")

print("Python:", sys.version.split()[0])
print("NumPy:", np.__version__)
print("h5py:", h5py.__version__)
print("Matplotlib:", mpl.__version__)
"""
        ),
        md(
            """
## 1. Locate an input

The notebook prefers your newest four-rank solver result. Set `INOISY_H5` to
choose a specific file. If no cluster result exists, it uses a small synthetic,
schema-compatible fallback so the lesson can continue during a queue delay.
"""
        ),
        code(
            r"""
def find_course_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "README.md").exists() and (candidate / "tutorials").exists():
            return candidate
    raise FileNotFoundError("Open this notebook from inside the course repository.")


course_root = find_course_root(Path.cwd().resolve())
default_work = Path(f"/work/{os.environ.get('USER', 'student')}/ncshare-crash-course")
course_work = Path(os.environ.get("COURSE_WORK", default_work))
if not course_work.parent.exists():
    course_work = course_root / "artifacts"
course_work.mkdir(parents=True, exist_ok=True)

fallback_raw = (
    course_root
    / "tutorials"
    / "05-visualization-postprocessing"
    / "data"
    / "sample_inoisy4d_lowres.h5"
)
override = os.environ.get("INOISY_H5")
real_outputs = sorted(
    course_work.glob("inoisy/four-ranks/*.h5"),
    key=lambda path: path.stat().st_mtime,
    reverse=True,
)

if override:
    raw_path = Path(override).expanduser().resolve()
    source_kind = "explicit INOISY_H5"
elif real_outputs:
    raw_path = real_outputs[0].resolve()
    source_kind = "newest four-rank solver output"
else:
    raw_path = fallback_raw.resolve()
    source_kind = "synthetic queue-delay fallback"

if not raw_path.exists():
    raise FileNotFoundError(raw_path)

print("Input type:", source_kind)
print("Input file:", raw_path)
print(f"File size: {raw_path.stat().st_size / 1024**2:.3f} MiB")
"""
        ),
        md(
            """
## 2. Inspect structure before reading arrays

HDF5 datasets are lazy handles. Reading `dataset.shape`, `dataset.dtype`, or one
slice does not load the complete field. This distinction is essential when the
production dataset is much larger than memory.
"""
        ),
        code(
            r"""
def scalar(handle: h5py.File, path: str) -> float:
    return float(np.asarray(handle[path]))


with h5py.File(raw_path, "r") as handle:
    print("Top-level groups:", list(handle.keys()))
    print("/data datasets:", list(handle["/data"].keys()))
    print("/params entries (first 12):", list(handle["/params"].keys())[:12])

    raw_dataset = handle["/data/data_raw"]
    shape = tuple(raw_dataset.shape)
    dtype = raw_dataset.dtype
    fallback_flag = bool(handle["/params"].attrs.get("course_fallback", False))
    x_start = scalar(handle, "/params/x1start")
    y_start = scalar(handle, "/params/x2start")
    z_start = scalar(handle, "/params/x3start")
    dx = scalar(handle, "/params/dx1")
    dy = scalar(handle, "/params/dx2")
    dz = scalar(handle, "/params/dx3")
    t_start = scalar(handle, "/params/x0start")
    dt = scalar(handle, "/params/dx0")

print("Shape [time, x, y, z]:", shape)
print("dtype:", dtype)
print("Synthetic fallback:", fallback_flag)
print(f"On-disk raw array size: {np.prod(shape) * np.dtype(dtype).itemsize / 1024**2:.3f} MiB")

if len(shape) != 4:
    raise ValueError(f"Expected four dimensions; found {shape}")
"""
        ),
        code(
            r"""
nt, nx, ny, nz = shape
time_index = min(2, nt - 1)
z_index = nz // 2

# This reads one x-y plane, not the complete four-dimensional dataset.
with h5py.File(raw_path, "r") as handle:
    raw_xy = np.asarray(handle["/data/data_raw"][time_index, :, :, z_index])
    lightcurve = np.asarray(handle["/data/lc_raw"][:])

x_edges = x_start + dx * np.arange(nx + 1)
y_edges = y_start + dy * np.arange(ny + 1)
extent_xy = [x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]]
times = t_start + dt * np.arange(nt)

finite = raw_xy[np.isfinite(raw_xy)]
limits = np.percentile(finite, [2, 98])

print(f"Selected time index: {time_index} (t={times[time_index]:.3g})")
print(f"Selected z index: {z_index} (z≈{z_start + (z_index + 0.5) * dz:.3g})")
print(f"Slice min/median/max: {finite.min():.4g} / {np.median(finite):.4g} / {finite.max():.4g}")
print(f"Displayed 2nd–98th percentile limits: {limits[0]:.4g}, {limits[1]:.4g}")
"""
        ),
        md(
            """
### Start with diagnostics, not decoration

A histogram reveals skew and outliers before a color scale is chosen. A time
series reveals whether the selected frame is typical. Labels and units are
required even when units are dimensionless or arbitrary.
"""
        ),
        code(
            r"""
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), constrained_layout=True)

axes[0].hist(finite, bins=35, color="#4477AA", edgecolor="white")
axes[0].set(
    title="Distribution in the selected x-y slice",
    xlabel="Raw GRF value [arbitrary units]",
    ylabel="Cell count",
)

axes[1].plot(times, lightcurve, marker="o", color="#228833")
axes[1].axvline(times[time_index], color="#AA3377", linestyle="--", label="selected frame")
axes[1].set(
    title="Raw integrated field over time",
    xlabel="Source time [code units]",
    ylabel="Integrated raw field [arbitrary units]",
)
axes[1].legend(frameon=False)

plt.show()
"""
        ),
        md(
            """
## 3. Choose color by data meaning

- **Sequential** maps (`viridis`, `cividis`, `magma`) encode ordered low-to-high
  values.
- **Diverging** maps (`RdBu_r`) emphasize deviation around a meaningful center
  such as zero.
- **Cyclic** maps are for wrapped quantities such as phase or direction.
- **Qualitative** palettes distinguish categories, not magnitudes.

The two panels below use identical data and limits. Compare how evenly changes
in magnitude appear. `jet` has non-monotonic lightness and can create false
visual boundaries; a perceptually ordered map is usually a safer default.
"""
        ),
        code(
            r"""
fig, axes = plt.subplots(1, 2, figsize=(9.5, 4), constrained_layout=True, sharex=True, sharey=True)

for ax, cmap, label in zip(
    axes,
    ("jet", "cividis"),
    ("Rainbow map: visual boundaries can dominate", "Perceptually ordered sequential map"),
):
    image = ax.imshow(
        raw_xy.T,
        origin="lower",
        extent=extent_xy,
        cmap=cmap,
        vmin=limits[0],
        vmax=limits[1],
        aspect="equal",
    )
    ax.set(title=label, xlabel="x [code units]", ylabel="y [code units]")
    fig.colorbar(image, ax=ax, label="Raw GRF [arbitrary units]", shrink=0.82)

fig.suptitle("Same data and 2nd–98th percentile limits; only the color map changes")
plt.show()
"""
        ),
        md(
            """
For a signed field with a meaningful zero, a diverging map plus an explicit
center is more informative. We disclose percentile clipping in the title so
readers know extreme values are saturated.
"""
        ),
        code(
            r"""
bound = float(max(abs(limits[0]), abs(limits[1])))
norm_raw = TwoSlopeNorm(vmin=-bound, vcenter=0.0, vmax=bound)

good_fig, ax = plt.subplots(figsize=(6.2, 5), constrained_layout=True)
image = ax.imshow(
    raw_xy.T,
    origin="lower",
    extent=extent_xy,
    cmap="RdBu_r",
    norm=norm_raw,
    aspect="equal",
)
ax.set(
    title=f"Gaussian random field at t={times[time_index]:.3g}; limits use |2nd–98th percentile|",
    xlabel="x [code units]",
    ylabel="y [code units]",
)
good_fig.colorbar(image, ax=ax, label="Raw GRF [arbitrary units]")
plt.show()
"""
        ),
        md(
            r"""
## 4. Run the upstream GRF-to-emissivity converter

The unmodified `inoisy4d_to_visit_emissivity.py` script:

1. standardizes the raw field,
   \(\hat{F}=(F-\langle F\rangle)/\sqrt{\mathrm{Var}(F)}\);
2. applies positive lognormal fluctuations to deterministic disk and jet
   envelopes; and
3. writes an HDF5/XDMF pair for visualization.

The cell runs the upstream script when the inoisy+ clone is available. Otherwise
it uses the included processed fallback and says so explicitly.
"""
        ),
        code(
            r"""
inoisy_src = Path(
    os.environ.get(
        "INOISY_SRC",
        str(Path.home() / "ncshare-software" / "src" / "inoisy4d"),
    )
).expanduser()
upstream_converter = inoisy_src / "tools" / "inoisy4d_to_visit_emissivity.py"

post_dir = course_work / "inoisy" / "postprocessed"
post_dir.mkdir(parents=True, exist_ok=True)
post_prefix = post_dir / "notebook_emissivity"
fallback_processed = (
    course_root
    / "tutorials"
    / "05-visualization-postprocessing"
    / "data"
    / "sample_inoisy4d_emissivity.h5"
)

if upstream_converter.exists():
    command = [
        sys.executable,
        str(upstream_converter),
        str(raw_path),
        "--output-prefix",
        str(post_prefix),
        "--write-components",
        "--write-envelopes",
        "--compress",
        "--float32",
        "--force",
    ]
    print("Running:", shlex.join(command))
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    print("\n".join(completed.stdout.strip().splitlines()[-12:]))
    processed_path = post_prefix.with_suffix(".h5")
    processed_kind = "created now by the upstream converter"
else:
    processed_path = fallback_processed
    processed_kind = "included processed fallback (upstream clone not found)"

if not processed_path.exists():
    raise FileNotFoundError(processed_path)

print("Processed input:", processed_kind)
print("Processed file:", processed_path)
"""
        ),
        code(
            r"""
with h5py.File(processed_path, "r") as handle:
    names = sorted(handle["/data"].keys())
    emissivity_names = [name for name in names if name.startswith("emissivity_")]
    fhat_names = [name for name in names if name.startswith("Fhat_")]
    processed_times = np.asarray(handle["/data/time"][:])

processed_index = min(time_index, len(emissivity_names) - 1)
with h5py.File(processed_path, "r") as handle:
    # Processed arrays use [z, y, x] for XDMF/VisIt.
    emissivity_zyx = np.asarray(handle[f"/data/{emissivity_names[processed_index]}"])
    fhat_zyx = np.asarray(handle[f"/data/{fhat_names[processed_index]}"])

emissivity_yx = emissivity_zyx[min(z_index, emissivity_zyx.shape[0] - 1)]
fhat_yx = fhat_zyx[min(z_index, fhat_zyx.shape[0] - 1)]

table = pd.DataFrame(
    {
        "array": ["raw GRF", "standardized GRF", "emissivity"],
        "minimum": [raw_xy.min(), fhat_yx.min(), emissivity_yx.min()],
        "median": [np.median(raw_xy), np.median(fhat_yx), np.median(emissivity_yx)],
        "maximum": [raw_xy.max(), fhat_yx.max(), emissivity_yx.max()],
    }
)
table.style.format({"minimum": "{:.4g}", "median": "{:.4g}", "maximum": "{:.4g}"})
"""
        ),
        md(
            """
## 5. Match normalization to the transformed quantity

The raw and standardized fields have meaningful positive/negative deviations,
so the diverging maps are centered on zero. Emissivity is positive and can be
skewed, so a sequential map with logarithmic normalization reveals structure
across orders of magnitude. Each color bar states what it encodes.
"""
        ),
        code(
            r"""
raw_bound = np.percentile(np.abs(raw_xy[np.isfinite(raw_xy)]), 98)
fhat_bound = np.percentile(np.abs(fhat_yx[np.isfinite(fhat_yx)]), 98)
positive = emissivity_yx[np.isfinite(emissivity_yx) & (emissivity_yx > 0)]
em_limits = np.percentile(positive, [2, 98])

summary_fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True, sharex=True, sharey=True)

panels = [
    (
        raw_xy.T,
        "Raw GRF",
        "RdBu_r",
        TwoSlopeNorm(vmin=-raw_bound, vcenter=0, vmax=raw_bound),
        "Raw value [arbitrary units]",
    ),
    (
        fhat_yx,
        "Standardized GRF",
        "RdBu_r",
        TwoSlopeNorm(vmin=-fhat_bound, vcenter=0, vmax=fhat_bound),
        r"$\hat{F}$ [standard deviations]",
    ),
    (
        emissivity_yx,
        "Positive emissivity",
        "magma",
        LogNorm(vmin=max(em_limits[0], np.finfo(float).tiny), vmax=em_limits[1]),
        "Emissivity [arbitrary units, log scale]",
    ),
]

for ax, (array, title, cmap, norm, colorbar_label) in zip(axes, panels):
    image = ax.imshow(
        array,
        origin="lower",
        extent=extent_xy,
        cmap=cmap,
        norm=norm,
        aspect="equal",
    )
    ax.set(title=title, xlabel="x [code units]")
    fig_colorbar = summary_fig.colorbar(image, ax=ax, shrink=0.78)
    fig_colorbar.set_label(colorbar_label)

axes[0].set_ylabel("y [code units]")
summary_fig.suptitle(
    f"inoisy+ post-processing at t={processed_times[processed_index]:.3g}; "
    "display limits use 2nd–98th percentiles"
)
plt.show()
"""
        ),
        md(
            """
## 6. Export with provenance

Use a raster format such as PNG for slides/web and a vector format such as PDF
for scalable text and axes. The HDF5 source path, time index, and normalization
remain in code and metadata instead of being reconstructed by hand.
"""
        ),
        code(
            r"""
figure_dir = course_work / "visualization"
figure_dir.mkdir(parents=True, exist_ok=True)
png_path = figure_dir / "inoisy_emissivity_summary.png"
pdf_path = figure_dir / "inoisy_emissivity_summary.pdf"

summary_fig.savefig(
    png_path,
    metadata={
        "Title": "inoisy+ raw, standardized, and emissivity fields",
        "Source": str(raw_path),
        "Time index": str(time_index),
    },
)
summary_fig.savefig(
    pdf_path,
    metadata={
        "Title": "inoisy+ raw, standardized, and emissivity fields",
        "Author": os.environ.get("USER", "NCShare participant"),
        "Subject": f"Source={raw_path}; time_index={time_index}; percentile limits=2,98",
        "Creator": "NCShare scientific visualization notebook",
    },
)

print("Wrote:", png_path)
print("Wrote:", pdf_path)
"""
        ),
        md(
            """
## 7. Independent exercise

Change `exercise_time_index` below and make one figure that answers:
**How does the mid-plane emissivity structure change over time?**

Keep spatial extent and color limits fixed across frames so changes in color
represent changes in data, not rescaling. Add the selected time to the title.
"""
        ),
        code(
            r"""
exercise_time_index = min(processed_index + 1, len(emissivity_names) - 1)

with h5py.File(processed_path, "r") as handle:
    exercise_zyx = np.asarray(handle[f"/data/{emissivity_names[exercise_time_index]}"])
exercise_yx = exercise_zyx[min(z_index, exercise_zyx.shape[0] - 1)]

fig, ax = plt.subplots(figsize=(5.5, 4.5), constrained_layout=True)
image = ax.imshow(
    exercise_yx,
    origin="lower",
    extent=extent_xy,
    cmap="magma",
    norm=LogNorm(vmin=max(em_limits[0], np.finfo(float).tiny), vmax=em_limits[1]),
    aspect="equal",
)
ax.set(
    title=f"Emissivity at t={processed_times[exercise_time_index]:.3g}; fixed color scale",
    xlabel="x [code units]",
    ylabel="y [code units]",
)
fig.colorbar(image, ax=ax, label="Emissivity [arbitrary units, log scale]")
plt.show()
"""
        ),
        md(
            """
## Final check

- What question does your final figure answer?
- Which data did you omit by slicing or clipping?
- Is zero or a logarithmic scale scientifically meaningful here?
- Would the conclusion survive grayscale printing?
- Can another student rerun the figure from the recorded file and cell?

Further reading:
[Matplotlib colormap guidance](https://matplotlib.org/stable/users/explain/colors/colormaps.html) ·
[Colorcet](https://colorcet.holoviz.org/) ·
[Data-to-Viz caveats](https://www.data-to-viz.com/caveats.html) ·
[Ten Simple Rules for Better Figures](https://doi.org/10.1371/journal.pcbi.1003833)
"""
        ),
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
