# Supplemental QuantUI data

The inoisy visualization uses only the HDF5 files produced during the CPU and
post-processing exercises. No synthetic inoisy fallback is included.

This directory retains the existing QuantUI teaching data:

- `sample_quantui/cpu_gpu_comparison_*.json` contains four real paired timing
  measurements collected on NCShare on 2026-08-05: one H200 versus six
  affinity-confirmed CPU cores. These are teaching measurements, not repeated
  benchmark distributions.
- `sample_quantui/geometry_optimization_water.json` is a synthetic,
  schema-compatible trajectory. It exists only to exercise the line-plot
  workflow and is marked `"synthetic": true` so every notebook can watermark
  it.

The timing and trajectory files are independent. A notebook may use
real timing files and the synthetic trajectory when the optional CPU geometry
calculation has not been run; it reports those sources separately.
