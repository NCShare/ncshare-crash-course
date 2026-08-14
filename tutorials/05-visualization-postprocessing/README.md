# Hands-on: Scientific visualization and containerized post-processing

**Guided time:** 60 minutes  
**Inputs:** inoisy+ HDF5 fields and QuantUI JSON results from the previous labs
**Tools inside the course SIF:** JupyterLab, NumPy, h5py, Matplotlib, and the
unmodified inoisy+ emissivity converter

## Learning goals

By the end, you can:

- begin with a scientific question and inspect data meaning and provenance;
- match visual encoding to spatial fields, paired timings, and ordered change;
- choose color, normalization, clipping, and logarithmic scales deliberately;
- make a fair comparison whose denominator and limitations are visible; and
- export accessible figures with their inputs, settings, and software versions.

The unified notebook makes four principal figures: two from inoisy+ and two
from QuantUI. Each figure introduces a different plotting decision, so the
lesson does not repeat the same checklist for every dataset.

## Simulation, post-processing, and visualization

These are separate stages even though they use one container:

- the inoisy+ simulation produces a four-dimensional HDF5 field;
- a CPU post-processing job derives standardized and emissivity fields;
- the QuantUI lab produces paired CPU/GPU timings and, optionally, a CPU-only
  geometry-relaxation trajectory; and
- visualization selects meaningful slices or summaries and encodes them as
  figures.

Keeping the stages separate avoids rerunning an expensive simulation merely to
change a color map or figure label. It also makes the transformation from raw
data to figure explicit.

## 1. Use the course image—do not create another environment

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"

apptainer exec "$COURSE_IMAGE" python -c \
  "import h5py, matplotlib, numpy; print('visualization stack OK')"
```

The first three lines establish the same repository, workspace, and image paths
used earlier. `python -c` asks the image's Python interpreter to run the quoted
one-line program. If every import succeeds, it prints the confirmation. This
is a quick environment check, not a test of the input dataset or notebook.

The plotting stack is created in the same definition file as MPI, HYPRE,
inoisy4d, and QuantUI. This avoids a hidden post-processing environment that
cannot be reconstructed later.

For a module-based cluster, see the
[bonus native environment](../../bonus/module-based-cluster/README.md).

## 2. Run the upstream post-processor

Run the converter as a separate CPU batch job. Keeping this step outside the
notebook records the transformation in a Slurm log and prevents a plotting
rerun from silently recomputing scientific data:

```bash
mkdir -p "$COURSE_WORK/logs"
cd "$COURSE_ROOT/tutorials/05-visualization-postprocessing"
sbatch --export=ALL,COURSE_IMAGE="$COURSE_IMAGE" \
  slurm/postprocess_emissivity.sbatch
```

This submits a CPU batch job; post-processing does not need an H200. The job
looks for the newest four-rank `.h5` result unless the caller supplies a
`SOURCE_H5` variable. It stops with a clear error if no input exists rather
than silently analyzing the fallback dataset.

The job binds `/work/$USER` and calls the unmodified converter stored inside
the SIF:

```text
/opt/inoisy4d/tools/inoisy4d_to_visit_emissivity.py
```

It reads `/data/data_raw`, standardizes the GRF, computes disk and jet
components, and writes an HDF5/XDMF pair under
`$COURSE_WORK/inoisy/postprocessed`.

“Standardizes” means subtracting a mean and dividing by a standard deviation so
the field has a defined reference scale. HDF5 stores the numeric arrays. XDMF
is a small XML description that tells compatible visualization programs how
those arrays are arranged; it points to the HDF5 file rather than duplicating
the data.

## 3. Open the notebook through Open OnDemand

NCShare Open OnDemand can launch JupyterLab from a selected Apptainer image:

1. Open **Interactive Apps → Jupyter Lab Apptainer**.
2. Request 2 CPU threads, 8 GB RAM, and one hour.
3. Select the course SIF under **Apptainer Container File**.
4. Do **not** request a GPU; these plots and the post-processor are CPU work.
5. Launch, open the course repository, and select the image's Python 3 kernel.
6. Open:

   ```text
   tutorials/05-visualization-postprocessing/scientific_visualization.ipynb
   ```

Open OnDemand is a browser interface to cluster services. JupyterLab is an
interactive workspace, and a **notebook** is a document made of executable
code cells and explanatory Markdown cells. A **kernel** is the Python process
that runs the code. Selecting the image's kernel is important: a host or user
kernel may have different packages from the environment being taught.

Run notebook cells from top to bottom the first time. A cell's displayed output
may be old, so the visible figure alone does not prove that the current kernel
successfully ran its code.

For command-line testing inside a CPU allocation:

```bash
apptainer exec \
  --bind "$COURSE_ROOT:$COURSE_ROOT" \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  jupyter lab --no-browser
```

This alternative is for testing from a terminal inside a CPU allocation. Both
host directories are bound so Jupyter can read the notebook and data. The
`--no-browser` option prevents a compute node from trying to open its own web
browser; in normal class use, Open OnDemand handles the browser connection.

For each input type, the notebook checks an explicit environment-variable
override, then the expected location under `$COURSE_WORK`, and finally the
appropriate bundled fallback:

| Input | Override | Normal result pattern |
|---|---|---|
| Raw inoisy+ field | `INOISY_H5` | `inoisy/four-ranks/*.h5` |
| Processed inoisy+ field | `INOISY_EMISSIVITY_H5` | `inoisy/postprocessed/*emissivity*.h5` |
| QuantUI JSON directory | `QUANTUI_RESULTS` | `quantui/cpu_gpu_comparison_*.json` and `quantui/geometry_optimization_water.json` |

The two inoisy+ figures declare their raw or processed source independently;
the notebook never claims independently selected files are the same run. The
inoisy+ fallbacks are synthetic. Bundled QuantUI timings are real NCShare
measurements, while the geometry trajectory is synthetic and visibly
watermarked.

Environment variables can select specific inputs before Jupyter starts:

```bash
export INOISY_H5="/work/$USER/ncshare-crash-course/inoisy/four-ranks/FILE.h5"
export INOISY_EMISSIVITY_H5="/work/$USER/ncshare-crash-course/inoisy/postprocessed/FILE.h5"
export QUANTUI_RESULTS="/work/$USER/ncshare-crash-course/quantui"
```

Replace each `FILE.h5` with an existing filename. Set only the overrides you
need. The notebook reports every selected input; read that report before
interpreting a plot.

## Plot the QuantUI results from the GPU session

The GPU and follow-up CPU work can produce two kinds of JSON under
`$COURSE_WORK/quantui/`. The same
[`scientific_visualization.ipynb`](scientific_visualization.ipynb) used for the
inoisy field turns them into figures. Keeping both scientific workflows in one
notebook lets each plot teach a distinct lesson without repeating setup,
plotting principles, or export steps.

Two figures:

1. **CPU vs GPU wall time** — a connected-dot plot on a logarithmic time axis.
   It makes the paired calculation and `CPU time / GPU time` comparison explicit
   without implying that the unordered calculation categories form a trend.
2. **Geometry-relaxation trajectory** — energy above the final recorded value
   at each ordered optimization step. Generate the data from the CPU-only Open
   OnDemand allocation already running this notebook:

   ```bash
   apptainer exec --cleanenv \
     --bind "$COURSE_WORK:$COURSE_WORK" \
     --env "COURSE_WORK=$COURSE_WORK" \
     "$COURSE_IMAGE" \
     python "$COURSE_ROOT/tutorials/04-gpu-quantui/run_geometry_optimization.py" \
     --preset water
   ```

If a job is still queued, the unified notebook falls back by data type to
bundled samples under
[`data/sample_quantui/`](data/sample_quantui/) so the plotting lesson still runs
— the notebook reports which source each figure uses. The timing samples are
real NCShare measurements; the trajectory is a clearly labeled synthetic
placeholder until you generate a real one.

### Optional focused QuantUI notebook

The preserved [`plot_quantui_results.ipynb`](plot_quantui_results.ipynb) and
[`quantui_result_plots.py`](quantui_result_plots.py) provide a shorter QuantUI-
only path. Its grouped bars on a linear axis are an intentional alternative to
the unified notebook's connected dots on a log axis. Comparing the two is a
useful critique exercise: bars emphasize absolute magnitude from a zero
baseline, while the log-axis design emphasizes ratios across a wide range.
The unified notebook remains the primary Session 4 path.

## Container-specific reproducibility check

Before exporting the final figure, record:

```bash
apptainer inspect "$COURSE_IMAGE" \
  | grep -E 'BaseImage|inoisy4dSelection|QuantUIVersion|BlueprintVersion'
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/inoisy4d-commit.txt
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/quantui-version.txt
cat "$COURSE_IMAGE.sha256" 2>/dev/null || sha256sum "$COURSE_IMAGE"
```

The first command selects recipe labels. The next two commands record the exact
inoisy4d revision and installed QuantUI release. The final command uses a
published checksum file when available and computes the checksum directly
otherwise. Record the resulting value; do not paste the fallback operator
itself into a methods section.

Keep that identity with the input HDF5 path, time/slice selection, percentile
limits, plotting code, and exported figure.

## A compact figure checklist

- **Question:** Does the figure answer one stated question?
- **Encoding:** Is the visual form appropriate for the quantity?
- **Scale:** Are logarithms, percentiles, limits, and normalization explicit?
- **Color:** Is the map perceptually ordered and suitable for the data type?
- **Labels:** Are quantity names and units on axes and color bars?
- **Context:** Is the selected time, slice, or aggregation stated?
- **Accessibility:** Does meaning survive grayscale/color-vision variation?
- **Integrity:** Are missing values visible, and was no inconvenient data
  silently removed?
- **Reproducibility:** Can the plot be regenerated from the SIF, input, and
  notebook?
- **Export:** Is PNG used for slides/web and PDF/SVG for scalable line art?

## Recommended references

- [Matplotlib quick start](https://matplotlib.org/stable/users/explain/quick_start.html)
- [Choosing colormaps in Matplotlib](https://matplotlib.org/stable/users/explain/colors/colormaps.html)
- [Seaborn color-palette tutorial](https://seaborn.pydata.org/tutorial/color_palettes.html)
- [Colorcet perceptually uniform colormaps](https://colorcet.holoviz.org/)
- [Fundamentals of Data Visualization](https://clauswilke.com/dataviz/)
- [Data-to-Viz caveats](https://www.data-to-viz.com/caveats.html)
- [Ten Simple Rules for Better Figures](https://doi.org/10.1371/journal.pcbi.1003833)
- [NCShare Open OnDemand JupyterLab guide](https://userguide.ncshare.org/guides/ondemand/jupyter/)
