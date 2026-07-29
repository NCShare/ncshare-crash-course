# Hands-on: Scientific visualization and containerized post-processing

**Guided time:** 60 minutes  
**Inputs:** containerized inoisy+ HDF5 output; a small fallback is included  
**Tools inside the course SIF:** JupyterLab, NumPy, h5py, Matplotlib, pandas,
Seaborn, and the unmodified inoisy+ emissivity converter

## Learning goals

By the end, you can:

- launch a reproducible Jupyter environment from the same SIF as the simulation;
- inspect HDF5 structure and metadata without loading a full 4D field;
- choose a slice or reduction that answers a specific question;
- match sequential, diverging, cyclic, and qualitative colors to data meaning;
- label quantities, units, normalization, and provenance;
- run the upstream GRF-to-emissivity post-processor through Apptainer; and
- export reproducible raster and vector figures.

The Gaussian random field models time-variable structure; the converter
standardizes that field and maps it to a positive lognormal disk-plus-jet
emissivity. Only the minimum scientific context needed to understand the arrays
is included.

## 1. Use the course image—do not create another environment

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"

apptainer exec "$COURSE_IMAGE" python -c \
  "import h5py, matplotlib, numpy, pandas, seaborn; print('visualization stack OK')"
```

The plotting stack is created in the same definition file as MPI, HYPRE,
inoisy4d, and QuantUI. This avoids a hidden post-processing environment that
cannot be reconstructed later.

For a module-based cluster, see the
[bonus native environment](../../bonus/module-based-cluster/README.md).

## 2. Run the upstream post-processor

The notebook can run it interactively, but a batch job records a clearer
cluster workflow:

```bash
mkdir -p "$COURSE_WORK/logs"
cd "$COURSE_ROOT/tutorials/05-visualization-postprocessing"
sbatch --export=ALL,COURSE_IMAGE="$COURSE_IMAGE" \
  slurm/postprocess_emissivity.sbatch
```

The job binds `/work/$USER` and calls the unmodified converter stored inside
the SIF:

```text
/opt/inoisy4d/tools/inoisy4d_to_visit_emissivity.py
```

It reads `/data/data_raw`, standardizes the GRF, computes disk and jet
components, and writes an HDF5/XDMF pair under
`$COURSE_WORK/inoisy/postprocessed`.

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

For command-line testing inside a CPU allocation:

```bash
apptainer exec \
  --bind "$COURSE_ROOT:$COURSE_ROOT" \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  jupyter lab --no-browser
```

The notebook searches for input in this order:

1. `INOISY_H5`, if set;
2. the newest four-rank result under
   `/work/$USER/ncshare-crash-course/inoisy/four-ranks`; and
3. the included tiny synthetic fallback.

The fallback matches the inoisy+ HDF5 schema but is not a solver result. It
exists so queue delays do not stop the visualization lesson.

## Container-specific reproducibility check

Before exporting the final figure, record:

```bash
apptainer inspect "$COURSE_IMAGE" \
  | grep -E 'BaseImage|inoisy4dCommit|QuantUICommit|BlueprintVersion'
cat "$COURSE_IMAGE.sha256" 2>/dev/null || sha256sum "$COURSE_IMAGE"
```

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
