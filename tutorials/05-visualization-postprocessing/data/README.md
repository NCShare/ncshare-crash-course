# Fallback data

These small files keep the visualization lab runnable while a class waits for
Slurm jobs:

- `sample_inoisy4d_lowres.h5` is a deterministic synthetic array written in the
  same `[time, x, y, z]` HDF5 layout used by inoisy+. It is **not** output from
  the scientific solver.
- `sample_inoisy4d_emissivity.h5` and `.xmf` were produced by running the
  unmodified upstream
  `tools/inoisy4d_to_visit_emissivity.py` converter on that synthetic input.
- `sample_quantui/cpu_gpu_comparison_*.json` contains four real paired timing
  measurements collected on NCShare on 2026-08-05: one H200 versus six
  affinity-confirmed CPU cores. These are teaching measurements, not repeated
  benchmark distributions.
- `sample_quantui/geometry_optimization_water.json` is a synthetic,
  schema-compatible trajectory. It exists only to exercise the line-plot
  workflow and is marked `"synthetic": true` so every notebook can watermark
  it.

The timing and trajectory files are independent fallbacks. A notebook may use
real timing files and the synthetic trajectory when the optional CPU geometry
calculation has not been run; it reports those sources separately.

Regenerate the raw file with:

```bash
export COURSE_IMAGE="/opt/apps/containers/users/ncshare-science-course.sif"
apptainer exec \
  --bind "$PWD:$PWD" \
  "$COURSE_IMAGE" \
  python instructor/generate_fallback_data.py
```

Then regenerate the processed pair with the unmodified converter packaged from
[alejandroc137/inoisy4d](https://github.com/alejandroc137/inoisy4d):

```bash
apptainer exec \
  --bind "$PWD:$PWD" \
  "$COURSE_IMAGE" \
  python /opt/inoisy4d/tools/inoisy4d_to_visit_emissivity.py \
  tutorials/05-visualization-postprocessing/data/sample_inoisy4d_lowres.h5 \
  --output-prefix tutorials/05-visualization-postprocessing/data/sample_inoisy4d_emissivity \
  --write-components --write-envelopes --compress --float32 --force
```
