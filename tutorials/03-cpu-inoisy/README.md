# Tutorial: Run a containerized C/MPI scientific application

**Guided time:** 45 minutes  
**Application:** [inoisy+ (`inoisy4d`)](https://github.com/alejandroc137/inoisy4d)  
**Concepts:** immutable environments, bind mounts, MPI ranks, Slurm, fixed-size
comparisons, logs, HDF5, and provenance

## What changed from a traditional HPC tutorial?

On a cluster with a large module catalog, each participant might load a
compiler/MPI/HDF5 stack, install HYPRE, and compile inoisy4d. NCShare instead
recommends Apptainer for scientific software. The shared course image already
contains the reviewed build:

```text
Open MPI + parallel HDF5 + GSL + HYPRE(maxdim=4) + unmodified inoisy4d
```

The build is still part of the lesson—it is visible in the
[definition-file tutorial](../../containers/README.md)—but it happens once
when the image is created, not once per user or job.

`inoisy+` generates a four-dimensional Gaussian random field. The science is
context rather than the learning objective. We run the same tiny global grid
with one and four MPI ranks and retain HDF5 results for the visualization lab.
In prose we call the application **inoisy+**; `inoisy4d` is the upstream
repository and executable name that appears in commands.

## How the program reaches a compute node

The application does not run when you read this page or edit the Slurm file.
The sequence is:

```text
login-node shell
  → sbatch sends a job description to Slurm
  → Slurm assigns one compute node and the requested CPU/memory/time
  → the job starts Apptainer on that node
  → Apptainer starts the image's MPI launcher
  → MPI starts one or four copies (ranks) of inoisy4d
  → the ranks write HDF5 output through a bind mount to /work/$USER
```

An **MPI rank** is one process participating in a parallel MPI program. Four
ranks are four cooperating processes; they are not four separate Slurm jobs.
The Slurm request, MPI rank count, and application's processor grid must agree.

## Before the clock starts

- Complete [pre-workshop setup](../00-prework.md).
- The HPC team has staged and checksummed the course SIF.
- The instructor has confirmed the teaching partition.
- Complete the [Apptainer blueprint tutorial](../../containers/README.md).

Set the shared paths:

```bash
export COURSE_ROOT="$HOME/ncshare-crash-course"
export COURSE_WORK="/work/$USER/ncshare-crash-course"
export COURSE_IMAGE="/opt/apps/containers/users/ncshare-science-course.sif"
mkdir -p "$COURSE_WORK/logs" "$COURSE_WORK/inoisy"
```

These exported variables give short names to the repository, active workspace,
and SIF. `mkdir -p` creates the log and result directories before Slurm tries to
use them.

## 0-8 min — Inspect the application environment

The SIF is read-only. Explore it without installing anything:

```bash
apptainer inspect "$COURSE_IMAGE"
apptainer exec "$COURSE_IMAGE" which inoisy4d
apptainer exec "$COURSE_IMAGE" mpirun --version
apptainer exec "$COURSE_IMAGE" h5pcc.openmpi -showconfig \
  | grep -i "Parallel HDF5"
apptainer exec "$COURSE_IMAGE" cat /opt/course-build/inoisy4d-commit.txt
```

Read these as `apptainer exec IMAGE COMMAND [OPTIONS]`:

- `which inoisy4d` reports the executable selected from the image's `PATH`;
- `mpirun --version` identifies the packaged MPI implementation;
- `h5pcc.openmpi -showconfig` prints the parallel HDF5 build configuration;
- the pipe sends that text to `grep -i`, which selects lines containing
  “Parallel HDF5” without regard to capitalization; and
- `cat` prints the recorded Git commit for the inoisy4d source used in this
  particular SIF.

These checks answer different questions. Finding an executable does not prove
which source revision or HDF5 configuration created it.

Inspect the upstream source and Makefile stored in the image:

```bash
apptainer exec "$COURSE_IMAGE" \
  sed -n '1,100p' /opt/inoisy4d/Makefile
apptainer exec "$COURSE_IMAGE" \
  sed -n '110,190p' /opt/inoisy4d/README.md
```

The backslash `\` continues one shell command onto the next display line.
`sed -n '1,100p' FILE` prints only lines 1–100; the second command prints lines
110–190. This is a way to inspect selected portions of source documentation
without opening an editor. The files are read from `/opt/inoisy4d` inside the
image.

Notice the difference between inspecting a build and modifying it. To change a
dependency or source commit, edit the definition and build a **new** SIF; do
not patch the shared image during a job.

## 8-15 min — Connect host data to container software

Apptainer automatically exposes some host paths, but the jobs bind the active
course workspace explicitly:

```bash
apptainer exec \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  ls -ld "$COURSE_WORK"
```

Each backslash means the command continues. `--bind HOST_PATH:CONTAINER_PATH`
makes a host directory visible inside the container. This course uses the same
path on both sides, which makes logs and scripts easier to interpret. The final
`ls -ld` runs inside the image and proves that the directory is visible there.

The same pathname is used on both sides of the bind. The executable and
libraries come from the image; inputs and outputs remain in `/work/$USER`.
Deleting the image would not delete the results.

## 15-22 min — Compare the Slurm files

Open:

- [`inoisy_one_rank.sbatch`](slurm/inoisy_one_rank.sbatch)
- [`inoisy_four_ranks.sbatch`](slurm/inoisy_four_ranks.sbatch)

Both jobs:

- request one node, modest memory, and ten minutes;
- bind the host work directory;
- start the MPI launcher **inside** the image, following NCShare's documented
  single-node container pattern; and
- call the same unmodified executable.

A Slurm batch file is a shell script. Lines beginning with `#SBATCH` are read
by Slurm when `sbatch` submits the file; they request resources and name the
log. Other `#` lines are ordinary comments, while the remaining commands run
on the assigned compute node. In these files:

- `--nodes=1` keeps all ranks on one machine;
- `--ntasks` is the number of MPI ranks;
- `--cpus-per-task=1` gives each rank one CPU core;
- `--mem=4G` is memory for the whole job;
- `--time=00:10:00` is a ten-minute limit, not an estimate; and
- `%u`, `%x`, and `%j` in the output path become the username, job name, and
  job ID.

The global grid is fixed:

| Job | MPI ranks | Local time cells per rank | Processor grid | Global shape |
|---|---:|---:|---|---|
| One rank | 1 | 16 | `1 1 1 1` | `(16,16,16,16)` |
| Four ranks | 4 | 4 | `1 1 1 4` | `(16,16,16,16)` |

This is a small strong-scaling comparison. Four ranks may be slower because
container startup, MPI startup, and communication dominate such a tiny problem.
That is a useful measurement, not a reason to request more CPUs.

## 22-28 min — Submit

Slurm opens the log before the job body starts, so create the directory first:

```bash
mkdir -p "$COURSE_WORK/logs"
cd "$COURSE_ROOT/tutorials/03-cpu-inoisy"
sbatch --parsable --export=ALL,COURSE_IMAGE="$COURSE_IMAGE" \
  slurm/inoisy_one_rank.sbatch
sbatch --parsable --export=ALL,COURSE_IMAGE="$COURSE_IMAGE" \
  slurm/inoisy_four_ranks.sbatch
```

`sbatch FILE` submits a batch script and returns immediately with a numeric job
ID. It does not run the program in the login shell. `--export=ALL` passes the
current environment variables to the job, and the comma-separated assignment
explicitly passes `COURSE_IMAGE`. `--parsable` makes `sbatch` print only the job
ID. Write down the two IDs; the first belongs to the one-rank job and the second
to the four-rank job. The trailing backslash only wraps a long command onto the
next display line.

## 28-35 min — Monitor and diagnose

```bash
squeue -u "$USER"
scontrol show job JOB_ID
```

- `squeue -u "$USER"` lists all of your queued and running jobs.
- `scontrol show job JOB_ID` prints the detailed scheduler record for one job.
  Replace `JOB_ID` with either number printed by `sbatch`.

Common states are `PENDING` (waiting), `RUNNING`, `COMPLETED`, `FAILED`, and
`CANCELLED`. A pending job is not necessarily broken; the final `squeue` column
normally explains what it is waiting for.

After completion:

```bash
sacct -j JOB_ID --format=JobID,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
less "$COURSE_WORK/logs/inoisy-one-JOB_ID.out"
less "$COURSE_WORK/logs/inoisy-four-JOB_ID.out"
```

`sacct` reads accounting information for current or completed jobs. Its
`--format` value is a comma-separated list of columns: job ID, final state,
elapsed time, allocated CPUs, peak resident memory, and exit status. An exit
code of `0:0` normally indicates that the batch script and its Slurm step
exited successfully. Use the one-rank ID with the `inoisy-one` log and the
four-rank ID with the `inoisy-four` log. `less` opens a text log; press `/` to
search and `q` to quit.

Separate three failure layers:

1. **Slurm:** pending reason, allocation, wall time, memory, exit code.
2. **Apptainer:** image path, bind path, permissions, image integrity.
3. **Application:** MPI/process-grid agreement, parameters, HDF5 output.

Rebuilding the image is not the first response to a bad resource request or a
missing host output directory.

## 35-42 min — Verify the HDF5 results

```bash
find "$COURSE_WORK/inoisy" -maxdepth 2 -name '*.h5' -ls

apptainer exec \
  --bind "$COURSE_ROOT:$COURSE_ROOT" \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  python "$COURSE_ROOT/tutorials/03-cpu-inoisy/scripts/inspect_inoisy_output.py" \
    "$COURSE_WORK"/inoisy/one-rank/*.h5 \
    "$COURSE_WORK"/inoisy/four-ranks/*.h5
```

The `find` command lists HDF5 files (`-name '*.h5'`) no more than two levels
below the result directory; `-ls` includes size and ownership details. The
inspection command binds both the repository (where the Python script lives)
and workspace (where the HDF5 files live). The shell expands `*.h5` to matching
filenames before Python starts.

HDF5 is a structured binary format: one file can contain named groups,
datasets, shapes, numeric types, and attributes. It is not meant to be opened
with `less`. The provided Python script uses `h5py` to read the structure,
metadata, and a small slice.

Confirm that both files contain `/data/data_raw` with shape
`(16, 16, 16, 16)`. The inspection script reads metadata and one slice rather
than loading a production-scale four-dimensional array.

## 42-45 min — Record provenance

```bash
apptainer inspect "$COURSE_IMAGE" \
  | grep -E 'BaseImage|HYPREVersion|inoisy4dSelection|BlueprintVersion'
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/inoisy4d-commit.txt
sha256sum "$COURSE_IMAGE"
```

`grep -E` selects any label matching the alternatives separated by `|`.
`sha256sum` prints a checksum that identifies the exact SIF file.

The image label states the source-selection policy; the file printed by `cat`
contains the exact commit resolved when this SIF was built. Record that commit
with the image path/checksum, definition version, job IDs, Slurm resources,
command-line parameters, and output paths. The source commit alone is
insufficient: it does not identify the MPI, HDF5, HYPRE, compiler, or Python
stack used to produce the result.

## Diagnose before resubmitting

| Symptom | Check | Likely action |
|---|---|---|
| image not found | `ls -l "$COURSE_IMAGE"` | use the instructor-published path |
| bind error | host directory exists | create it before `apptainer exec` |
| process-grid error | task count and `-pgrid` product | make them agree |
| job pending | final `squeue` column | read the scheduler reason |
| no log | log directory and `#SBATCH --output` | create the directory first |
| no HDF5 | application log and output bind | fix the first application error |
| multi-node launch fails | MPI compatibility model | return to one node; consult admins |

## Takeaways

1. The definition file documents how the executable was created; the SIF is
   what the job actually runs.
2. A container packages software, while Slurm allocates resources.
3. Bind mounts keep mutable data outside the immutable image.
4. Start with a tiny fixed problem, prove the workflow, then scale.

## Bonus

See [the module-based cluster workflow](../../bonus/module-based-cluster/README.md)
for the earlier per-user HYPRE build and native MPI/conda approach.

## Sources

- [inoisy+ repository](https://github.com/alejandroc137/inoisy4d)
- [NCShare Cluster Software guide](https://userguide.ncshare.org/guides/slurm/software/)
- [NCShare FHI-aims MPI container example](https://userguide.ncshare.org/examples/apptainer-fhiaims/)
- [Apptainer MPI guidance](https://apptainer.org/docs/user/latest/mpi.html)
