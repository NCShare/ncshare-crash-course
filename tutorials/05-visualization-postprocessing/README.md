# Hands-on: Scientific visualization and post-processing

**Guided time:** 60 minutes  
**Inputs:** inoisy+ HDF5 output; a small fallback file is included  
**Tools:** JupyterLab, NumPy, h5py, Matplotlib, pandas, and the unmodified
inoisy+ emissivity converter

## Learning goals

By the end, you can:

- inspect HDF5 structure and metadata without loading a full 4D field;
- choose a slice or reduction that answers a specific question;
- match sequential, diverging, cyclic, and qualitative color encodings to data;
- label quantities, units, normalization, and provenance;
- avoid misleading limits and disclose percentile/log normalization;
- run the upstream GRF-to-emissivity post-processing code; and
- export a reproducible raster and vector figure.

The Gaussian random field models time-variable structure; the emissivity
converter standardizes that field and maps it to a positive lognormal
disk-plus-jet source. The notebook explains only the minimum scientific context
needed to understand the arrays.

## 1. Create the visualization environment

Use a CPU allocation:

```bash
srun -p workshop --time=00:20:00 --cpus-per-task=2 --mem=8G --pty bash -l
```

Inside it:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
source "$HOME/miniforge3/etc/profile.d/conda.sh"

conda env create \
  -f "$COURSE_ROOT/tutorials/05-visualization-postprocessing/environment.yml"
conda activate ncshare-viz
python -m ipykernel install --user \
  --name ncshare-viz \
  --display-name "Python (NCShare Visualization)"
exit
```

If the environment already exists:

```bash
conda env update \
  --name ncshare-viz \
  --file "$COURSE_ROOT/tutorials/05-visualization-postprocessing/environment.yml" \
  --prune
```

## 2. Run the upstream post-processor

The notebook can run it interactively, but a batch job is the reproducible
cluster pattern:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
mkdir -p "$COURSE_WORK/logs"

cd "$COURSE_ROOT/tutorials/05-visualization-postprocessing"
sbatch slurm/postprocess_emissivity.sbatch
```

The job calls this file from the cloned inoisy+ repository without altering it:

```text
tools/inoisy4d_to_visit_emissivity.py
```

It reads `/data/data_raw`, standardizes the GRF, computes disk and jet
components, and writes a visualization-oriented HDF5/XDMF pair under
`$COURSE_WORK/inoisy/postprocessed`.

## 3. Open the notebook

Launch an Open OnDemand JupyterLab CPU session with 2 CPUs, 8 GB RAM, and one
hour. Select the **Python (NCShare Visualization)** kernel, then open:

```text
tutorials/05-visualization-postprocessing/scientific_visualization.ipynb
```

The notebook searches in this order:

1. `INOISY_H5`, if you set it;
2. your newest four-rank output in
   `/work/$USER/ncshare-crash-course/inoisy/four-ranks`; and
3. the included tiny synthetic fallback file.

The fallback matches the inoisy+ HDF5 schema but is not a solver result. It
exists so queue delays do not stop the visualization lesson.

## A compact figure checklist

Before saving a scientific figure, check:

- **Question:** Does the figure answer one stated question?
- **Encoding:** Is the visual form appropriate for the quantity?
- **Scale:** Are limits, logarithms, percentiles, and normalization explicit?
- **Color:** Is the map perceptually ordered and suitable for the data type?
- **Labels:** Are quantity names and units on axes and color bars?
- **Context:** Is the selected time, slice, or aggregation stated?
- **Accessibility:** Does meaning survive grayscale/color-vision variation, and
  is color paired with labels or line styles?
- **Integrity:** Are missing values visible, and was no inconvenient data
  silently removed?
- **Reproducibility:** Can the plot be regenerated from code, inputs, and saved
  settings?
- **Export:** Is PNG used for slides/web and PDF/SVG for scalable line art?

## Recommended references

- [Matplotlib quick start](https://matplotlib.org/stable/users/explain/quick_start.html)
- [Choosing colormaps in Matplotlib](https://matplotlib.org/stable/users/explain/colors/colormaps.html)
- [Seaborn color-palette tutorial](https://seaborn.pydata.org/tutorial/color_palettes.html)
- [Colorcet perceptually uniform colormaps](https://colorcet.holoviz.org/)
- [Fundamentals of Data Visualization](https://clauswilke.com/dataviz/)
- [Data-to-Viz caveats](https://www.data-to-viz.com/caveats.html)
- [Ten Simple Rules for Better Figures](https://doi.org/10.1371/journal.pcbi.1003833)
