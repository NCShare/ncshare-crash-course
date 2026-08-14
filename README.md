# NCShare Crash Course

This repository contains a one-day, hands-on introduction to NCShare for new
HPC users. The exercises use the official
[NCShare user guides](https://userguide.ncshare.org/guides/) and
[NCShare examples](https://github.com/NCShare/examples), then move through
a reproducible Apptainer build and two science applications: the inoisy+
C/MPI application and a GPU-enabled QuantUI calculation. The final session
uses outputs from both applications for scientific visualization and
post-processing.

## Start here

1. Instructors: complete [the readiness checklist](instructor/INSTRUCTOR_CHECKLIST.md).
2. Participants: complete [pre-workshop setup](tutorials/00-prework.md).
3. Follow the [agenda](agenda/agenda.md) and tutorials in numeric order.

## Course map

| Material | Purpose | Guided time |
|---|---|---:|
| [Access and orientation](tutorials/01-access-and-orientation.md) | Login, cluster mental model, essential commands, Apptainer, first allocation | 75 min plus break |
| [Storage and data movement](tutorials/02-storage-and-data.md) | `/hpc/home`, `/work`, `/scratch`, `scp`, `rsync`, and I/O habits | 30 min |
| [Apptainer blueprint](containers/README.md) | Read, build, test, checksum, and critique one shared scientific-software image | 30 min |
| [inoisy+ on CPUs](tutorials/03-cpu-inoisy/README.md) | Run the same containerized C/MPI application with one/four ranks | 45 min |
| [QuantUI on a GPU](tutorials/04-gpu-quantui/README.md) | Inspect the image's Python environment, expose an H200, verify offload, and measure a CPU/GPU crossover | 60 min |
| [Visualization and post-processing](tutorials/05-visualization-postprocessing/README.md) | Reuse the SIF in Jupyter, post-process inoisy+ output, and make four defensible plots from both applications | 60 min |
| [Bonus: module-based cluster](bonus/module-based-cluster/README.md) | Native compiler/MPI/HDF5/HYPRE build and per-user conda environment | Optional |

## Repository layout

```text
agenda/                              concise agenda in Markdown and Word
containers/                          commented definition, build/test scripts, CI blueprint
bonus/module-based-cluster/          optional native/module workflow
instructor/                          readiness checks and a fallback-data generator
references/                          NCShare command and policy quick reference
tutorials/03-cpu-inoisy/             containerized MPI Slurm and inoisy+ materials
tutorials/04-gpu-quantui/            containerized GPU verification and Slurm materials
tutorials/05-visualization-postprocessing/
  scientific_visualization.ipynb     primary, unified hands-on notebook
  plot_quantui_results.ipynb          optional focused QuantUI plotting notebook
  quantui_result_plots.py             plotting functions used by that optional notebook
  data/                              small offline fallback datasets
```

## Course vocabulary

The materials use a few related names deliberately:

- **inoisy+** is the scientific application name used in explanatory prose;
  `inoisy4d` is its upstream repository and executable name; and `inoisy` is
  the course's result-directory name under `$COURSE_WORK`.
- **QuantUI version** means the installed Python-package release. A separately
  recorded **source-checkout commit** identifies the retained example notebooks
  and source tree; it does not identify the installed package by itself.
- **CPU/GPU speedup** always means `CPU wall time / GPU wall time` for the same
  calculation. A value above 1 means the GPU was faster, and the CPU-core count
  is part of the result.

## Path conventions

The examples use four locations deliberately:

- `$HOME/ncshare-crash-course` for the small course repository.
- `/work/$USER/ncshare-crash-course` for active inputs and results; NCShare
  currently purges files older than 75 days from `/work`.
- `/opt/apps/containers/user` for an HPC-team-staged, shared course SIF.
- Job-local `/scratch` only for temporary, high-I/O data that is copied out
  before a job ends.

Override the defaults when needed:

```bash
export COURSE_ROOT="$HOME/ncshare-crash-course"
export COURSE_WORK="/work/$USER/ncshare-crash-course"
export COURSE_IMAGE="/opt/apps/containers/user/ncshare-science-course.sif"
```

## External software

The definition file downloads upstream source and compiles/installs it without
altering that source. QuantUI is installed from a pinned PyPI release; its
matching source tag is retained separately for examples and inspection.
inoisy4d follows the latest default branch at build time and records the
resolved commit inside the image. Students use the reviewed SIF; instructors
retain the definition, resolved package manifests, tests, source revisions,
and image checksum.
Each external project retains its own license and citation requirements:

- [alejandroc137/inoisy4d](https://github.com/alejandroc137/inoisy4d)
- [The-Schultz-Lab/QuantUI](https://github.com/The-Schultz-Lab/QuantUI)
- [hypre-space/hypre](https://github.com/hypre-space/hypre)

The container base, NCShare paths, partitions, and upstream source-selection
policy reflect documentation and repositories checked on August 13, 2026. HPC
administrators should rebuild/test the SIF and validate current policy before
each course offering. Module names appear only in the optional traditional-HPC
bonus and must be customized for that site.
