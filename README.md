**Note 08/18**: The finalized version will be posted in:

https://github.com/NCShare/ncshare-crash-course

# NCShare Crash Course

A one-day, hands-on introduction to NCShare for new HPC users. The exercises use the official [NCShare user guides](https://userguide.ncshare.org/guides/) and [NCShare examples](https://github.com/NCShare/examples), then move through two science applications: `inoisy4d` C/MPI application, a GPU-enabled QuantUI calculation, and scientific visualization/post-processing.

## Start here

1. Instructors: complete [the readiness checklist](instructor/INSTRUCTOR_CHECKLIST.md).
2. Participants: complete [pre-workshop setup](tutorials/00-prework.md).
3. Follow the [agenda](agenda/agenda.md) and tutorials in numeric order.

## Course map

| Material                                                                                 | Purpose                                                                              | Guided time |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------: |
| [Access and orientation](tutorials/01-access-and-orientation.md)                         | Login, structure of the cluster, essential commands, Apptainer, first allocation     |      75 min |
| [Storage and data movement](tutorials/02-storage-and-data.md)                            | `/hpc/home`, `/work`, `/scratch`, `scp`, `rsync`, and I/O habits                     |      30 min |
| [inoisy+ on CPUs](tutorials/03-cpu-inoisy/README.md)                                     | Run the same containerized C/MPI application with one/four ranks                     |      45 min |
| [QuantUI on a GPU](tutorials/04-gpu-quantui/README.md)                                   | Inspect the image's Python environment, expose an H200, and verify GPU offload       |      45 min |
| [Visualization and post-processing](tutorials/05-visualization-postprocessing/README.md) | Reuse the SIF in Jupyter, inspect HDF5, run the converter, and make defensible plots |      60 min |
| [Bonus: Apptainer blueprint](containers/README.md)                                       | Read, build, test, checksum, and critique one shared scientific-software image       |    Optional |
| [Bonus: module-based cluster](bonus/module-based-cluster/README.md)                      | Native compiler/MPI/HDF5/HYPRE build and per-user conda environment                  |    Optional |

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
  scientific_visualization.ipynb     hands-on notebook
  data/                              small offline fallback datasets
```

## Path conventions

The examples use the following locations, 

- `$HOME/ncshare-crash-course` (`COURSE_ROOT`) for the cloned repository — the version-controlled scripts, Slurm templates, and notebooks you submit from. Keep it in `$HOME`, which is persistent and backed up; do not clone it into `/work`, where it would fall under the purge policy below.
- `/work/$USER/ncshare-crash-course` (`COURSE_WORK`) for generated data — logs, results, and intermediate products that later steps read back in; NCShare currently purges files older than 75 days from `/work`.
- `/opt/apps/containers/users` for an HPC-team-staged, shared course SIF.
- Job-local `/scratch` only for temporary, high-I/O data that is copied out before a job ends.

**You normally set nothing here.** Each tutorial opens with a setup block that defines these variables itself, e.g. `export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"`. That single line carries *both* halves: the `${COURSE_ROOT:-DEFAULT}` form means *"use `COURSE_ROOT` if it is already set in this shell, otherwise use the literal `DEFAULT` written right here in the line."* So the default is not something that pre-exists in your environment — it is the fallback baked into each tutorial's setup block. Run that block and the variable is defined for the rest of that shell; start a fresh shell (a new login, or a new `srun` allocation) and it is unset again until the next tutorial's setup block re-defines it. Repeating the block in every tutorial is deliberate: it lets you begin any tutorial in a clean shell without having run the earlier ones.

To point one somewhere else, export it **once at the start of your session, before running a tutorial** — a plain assignment with no `:-` fallback, so your value is already set and therefore wins over every tutorial's default:

```bash
export COURSE_ROOT="$HOME/ncshare-crash-course"
export COURSE_WORK="/work/$USER/ncshare-crash-course"
export COURSE_IMAGE="/opt/apps/containers/users/ncshare-science-course.sif"
```

The right-hand sides above are the defaults themselves, shown as a copy-paste template — change a path to override that one variable; delete the lines you don't want to change.

## External software

The definition file downloads upstream source and compiles/installs it without altering that source. QuantUI is pinned to a recorded commit; inoisy4d follows the latest default branch at build time and records the resolved commit inside the image. Students use the reviewed SIF; instructors retain the definition, resolved package manifests, tests, source revisions, and image checksum. Each external project retains its own license and citation requirements:

- [alejandroc137/inoisy4d](https://github.com/alejandroc137/inoisy4d)
- [The-Schultz-Lab/QuantUI](https://github.com/The-Schultz-Lab/QuantUI)
- [hypre-space/hypre](https://github.com/hypre-space/hypre)

The container base, NCShare paths, partitions, and upstream source-selection policy reflect documentation and repositories checked on July 29, 2026. HPC administrators should rebuild/test the SIF and validate current policy before each course offering. Module names appear only in the optional traditional-HPC bonus and must be customized for that site.
