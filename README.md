# NCShare Crash Course

An upload-ready, one-day, hands-on introduction to NCShare for undergraduate
students and other new HPC users. The exercises use the official
[NCShare user guides](https://userguide.ncshare.org/guides/) and
[NCShare examples](https://github.com/NCShare/examples), then move through
the unmodified `inoisy4d` C/MPI application, a GPU-enabled QuantUI calculation,
and scientific visualization/post-processing.

## Start here

1. Instructors: complete [the readiness checklist](instructor/INSTRUCTOR_CHECKLIST.md).
2. Participants: complete [pre-workshop setup](tutorials/00-prework.md).
3. Follow the [agenda](agenda/agenda.md) and tutorials in numeric order.

## Course map

| Material | Purpose | Guided time |
|---|---|---:|
| [Access and orientation](tutorials/01-access-and-orientation.md) | Login, cluster mental model, essential commands, modules, first allocation | 75 min plus break |
| [Storage and data movement](tutorials/02-storage-and-data.md) | `/hpc/home`, `/work`, `/scratch`, `scp`, `rsync`, and I/O habits | 30 min |
| [inoisy+ on CPUs](tutorials/03-cpu-inoisy/README.md) | Install HYPRE, compile unmodified C/MPI source, and submit the same application with one/four ranks | 45 min guided path |
| [QuantUI on a GPU](tutorials/04-gpu-quantui/README.md) | Create a conda environment, verify an H200 allocation, submit a GPU calculation | 45 min |
| [Visualization and post-processing](tutorials/05-visualization-postprocessing/README.md) | Inspect HDF5 safely, run the upstream emissivity converter, make publication-ready plots | 60 min |

## Repository layout

```text
agenda/                              concise agenda in Markdown and Word
instructor/                          readiness checks and a fallback-data generator
references/                          NCShare command and policy quick reference
tutorials/03-cpu-inoisy/             C/MPI, Slurm, HYPRE, and inoisy+ materials
tutorials/04-gpu-quantui/             conda, GPU smoke test, and Slurm materials
tutorials/05-visualization-postprocessing/
  scientific_visualization.ipynb     hands-on notebook
  data/                              small offline fallback datasets
```

## Path conventions

The examples use three locations deliberately:

- `$HOME/ncshare-software` for source code and installed software that should
  persist.
- `/work/$USER/ncshare-crash-course` for active inputs and results; NCShare
  currently purges files older than 75 days from `/work`.
- Job-local `/scratch` only for temporary, high-I/O data that is copied out
  before a job ends.

Override the defaults when needed:

```bash
export COURSE_ROOT="$HOME/ncshare-crash-course"
export COURSE_WORK="/work/$USER/ncshare-crash-course"
export INOISY_SRC="$HOME/ncshare-software/src/inoisy4d"
export HYPRE_PREFIX="$HOME/ncshare-software/hypre-3.1.0-maxdim4"
export QUANTUI_SRC="$HOME/ncshare-software/src/QuantUI"
```

## External software

The course does not copy or alter the source of `inoisy4d` or QuantUI. Students
clone those repositories and build/install them in their own space. Each
external project retains its own license and citation requirements:

- [alejandroc137/inoisy4d](https://github.com/alejandroc137/inoisy4d)
- [The-Schultz-Lab/QuantUI](https://github.com/The-Schultz-Lab/QuantUI)
- [hypre-space/hypre](https://github.com/hypre-space/hypre)

The module names and partition limits in these files reflect the NCShare
documentation and source repositories as checked on July 29, 2026. HPC
administrators should validate them before each course offering.
