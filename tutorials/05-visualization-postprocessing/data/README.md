# Fallback data

These small files keep the visualization lab runnable while a class waits for
Slurm jobs:

- `sample_inoisy4d_lowres.h5` is a deterministic synthetic array written in the
  same `[time, x, y, z]` HDF5 layout used by inoisy+. It is **not** output from
  the scientific solver.
- `sample_inoisy4d_emissivity.h5` and `.xmf` were produced by running the
  unmodified upstream
  `tools/inoisy4d_to_visit_emissivity.py` converter on that synthetic input.

Regenerate the raw file with:

```bash
python instructor/generate_fallback_data.py
```

Then regenerate the processed pair from a clone of
[alejandroc137/inoisy4d](https://github.com/alejandroc137/inoisy4d):

```bash
python /path/to/inoisy4d/tools/inoisy4d_to_visit_emissivity.py \
  tutorials/05-visualization-postprocessing/data/sample_inoisy4d_lowres.h5 \
  --output-prefix tutorials/05-visualization-postprocessing/data/sample_inoisy4d_emissivity \
  --write-components --write-envelopes --compress --float32 --force
```
