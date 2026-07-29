# Tutorial: A scientific C/MPI application from clone to queue

**Guided time:** 45 minutes  
**Application:** [inoisy+ (`inoisy4d`)](https://github.com/alejandroc137/inoisy4d)  
**Concepts:** modules, a user-installed library, compilation, MPI, Slurm,
resource requests, logs, HDF5, and reproducibility

## What are we running?

`inoisy+` generates a four-dimensional Gaussian random field for
time-dependent astrophysical source models. The science is not the focus here:
the repository is useful because it is a realistic C/MPI application that
depends on a compiler, MPI, parallel HDF5, GSL, and HYPRE.

We do **not** edit or simplify its source. We install one dependency in user
space, pass paths to its existing Makefile, and make the runtime problem tiny:
`16 × 16 × 16 × 16 = 65,536` values (about 0.5 MiB for the raw double-precision
array). The one-rank and four-rank jobs solve the same global grid. They are not
expected to be bit-for-bit identical because parallel random-number generation
and solver ordering may differ.

## Before the clock starts

- Complete [pre-workshop setup](../00-prework.md).
- The instructor has confirmed the module names and an approved teaching
  partition.
- Run commands in an interactive allocation whenever they compile or compute.
- If the first HYPRE build takes longer than 15 minutes, use the instructor's
  verified read-only HYPRE prefix and continue; the install script remains the
  reproducibility record.

## 0-5 min — Clone and inspect

On the login node:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
export INOISY_SRC="${INOISY_SRC:-$HOME/ncshare-software/src/inoisy4d}"
export HYPRE_PREFIX="${HYPRE_PREFIX:-$HOME/ncshare-software/hypre-3.1.0-maxdim4}"

mkdir -p "$HOME/ncshare-software/src" "$COURSE_WORK"/{logs,inoisy}
git clone https://github.com/alejandroc137/inoisy4d.git "$INOISY_SRC"
cd "$INOISY_SRC"
git rev-parse --short HEAD
less README.md
less Makefile
```

If the clone already exists, do not clone over it:

```bash
git -C "$INOISY_SRC" status --short
git -C "$INOISY_SRC" pull --ff-only
```

Notice that the existing Makefile uses `h5pcc` and links HYPRE and GSL. We will
override `HYPRE_DIR` at the command line; no source or Makefile edit is needed.

## 5-18 min — Load modules and install HYPRE

Request a build allocation:

```bash
srun -p workshop --time=00:25:00 --cpus-per-task=4 --mem=8G --pty bash -l
```

Inside the allocation:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export HYPRE_PREFIX="${HYPRE_PREFIX:-$HOME/ncshare-software/hypre-3.1.0-maxdim4}"

module purge
module load compilers/gcc/12.3.0
module load mpi/openmpi/4.1.6
module load libs/hdf5/1.14.6
module load libs/gsl/2.7.1
module list

mpicc --version
h5pcc -showconfig | grep -i "Parallel HDF5"
bash "$COURSE_ROOT/tutorials/03-cpu-inoisy/scripts/setup_hypre.sh"
```

Why this matters:

- Modules select a mutually compatible compiler/MPI/library stack.
- HYPRE is not assumed to be centrally installed, so it goes under
  `/hpc/home/$USER`, where it persists.
- `--enable-maxdim=4` is essential because `inoisy+` uses a four-dimensional
  HYPRE SStruct grid.
- The script pins HYPRE `v3.1.0` and prints the exact configuration.

## 18-23 min — Compile the unmodified application

Still inside the build allocation:

```bash
bash "$COURSE_ROOT/tutorials/03-cpu-inoisy/scripts/build_inoisy.sh"
"$INOISY_SRC/inoisy4d" --help | head -n 25
exit
```

The helper runs the repository's existing Makefile with:

```bash
make HYPRE_DIR="$HYPRE_PREFIX" CC=h5pcc
```

Object files and the executable are normal build products; no `.c`, `.h`, or
Makefile source is changed.

## 23-30 min — Read the Slurm files

Compare:

- [`inoisy_one_rank.sbatch`](slurm/inoisy_one_rank.sbatch)
- [`inoisy_four_ranks.sbatch`](slurm/inoisy_four_ranks.sbatch)

Both request one node, modest memory, and ten minutes. The global grid is held
fixed:

| Job | MPI ranks | Local time cells per rank | Processor grid | Global shape |
|---|---:|---:|---|---|
| One rank | 1 | 16 | `1 1 1 1` | `(16,16,16,16)` |
| Four ranks | 4 | 4 | `1 1 1 4` | `(16,16,16,16)` |

This is a simple strong-scaling comparison: more ranks, same total problem.
For such a tiny grid, the parallel job may be slower because startup and
communication dominate. That is a useful result, not a failure.

## 30-35 min — Submit

Create the log directory **before** `sbatch` because Slurm opens the output file
before the job body begins:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
mkdir -p "$COURSE_WORK/logs"

cd "$COURSE_ROOT/tutorials/03-cpu-inoisy"
sbatch slurm/inoisy_one_rank.sbatch
sbatch slurm/inoisy_four_ranks.sbatch
```

Each `sbatch` command prints a job ID. Record both.

## 35-40 min — Monitor and inspect

```bash
squeue -u "$USER"
scontrol show job JOB_ID
```

When a job finishes:

```bash
sacct -j JOB_ID --format=JobID,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
less "$COURSE_WORK/logs/inoisy-one-JOB_ID.out"
less "$COURSE_WORK/logs/inoisy-four-JOB_ID.out"
find "$COURSE_WORK/inoisy" -maxdepth 2 -name '*.h5' -ls
```

Expected success signals:

- final job state `COMPLETED`;
- exit code `0:0`;
- solver-stage and timing messages in the log; and
- one `.h5` file in each output directory.

## 40-45 min — Verify the scientific output

Activate the visualization environment if it already exists, or save this check
for Session 4:

```bash
conda activate ncshare-viz
python "$COURSE_ROOT/tutorials/03-cpu-inoisy/scripts/inspect_inoisy_output.py" \
  "$COURSE_WORK"/inoisy/one-rank/*.h5 \
  "$COURSE_WORK"/inoisy/four-ranks/*.h5
```

Confirm that both files contain `/data/data_raw` with shape
`(16, 16, 16, 16)`. The script reads metadata and one slice at a time; it does
not load a production-size 4D field into memory.

## Diagnose before resubmitting

| Symptom | Check | Likely action |
|---|---|---|
| `Invalid account or partition` | `sinfo`, instructor directions | use the approved teaching partition |
| `h5pcc: command not found` | `module list` | load the verified HDF5 module |
| HDF5 says parallel support is `no` | `h5pcc -showconfig` | load the parallel HDF5/MPI stack |
| `libHYPRE.so` not found | `echo "$LD_LIBRARY_PATH"` | export `$HYPRE_PREFIX/lib` as in the Slurm files |
| job stays `PENDING` | `squeue -j JOB_ID -o "%.18i %.9T %.30R"` | read the reason; do not inflate resources |
| no log file | log directory and `#SBATCH --output` | create the directory before submission |
| nonzero exit | log plus `sacct ... ExitCode` | fix the first error, then resubmit |

## Takeaways

1. A real application is a chain of compatible software choices, not just a
   source file.
2. The Slurm file is part of the experiment and should be version controlled.
3. Start with a tiny fixed problem, prove the workflow, then scale deliberately.
4. Record versions, job IDs, resource requests, and output paths for
   reproducibility.

## Sources

- [inoisy+ repository and build/run documentation](https://github.com/alejandroc137/inoisy4d)
- [NCShare Cluster Computing guide](https://userguide.ncshare.org/guides/slurm/)
- [NCShare Cluster Software guide](https://userguide.ncshare.org/guides/slurm/software/)
- [HYPRE releases](https://github.com/hypre-space/hypre/releases)
