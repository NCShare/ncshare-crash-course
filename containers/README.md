# Hands-on: Build one reproducible environment with Apptainer

**Guided time:** 30 minutes  
**Output used in later labs:** `ncshare-science-course.sif`  
**Reference model:** [NCShare's FHI-aims workshop container](https://userguide.ncshare.org/examples/apptainer-fhiaims/)

## Why the course now starts with a container

NCShare provides basic system software but does not offer the traditional
scientific module catalog assumed by many HPC tutorials. Its current guidance
recommends containers for scientific software beyond simple user-space
installs. Therefore, students should not independently rebuild MPI, HYPRE,
inoisy+, QuantUI, and the Python stack before every exercise.

Instead, the class creates one reviewed **definition file** and turns it into
one immutable **SIF image**. The image is built once by the instructors or CI,
tested, checksummed, and reused by every participant. Slurm still chooses the
CPU, memory, time, and GPU resources; Apptainer supplies the application
environment.

```text
definition file + reviewed source selections
                |
                v
        one tested SIF image
          /             \
         v               v
  CPU/MPI job       GPU/Python job
  inoisy4d          QuantUI + --nv
         \               /
          v             v
       HDF5 results and Jupyter analysis
```

## What is inside—and what remains outside

| Inside the image | Supplied by NCShare or the user at runtime |
|---|---|
| Ubuntu/CUDA user-space libraries | Slurm scheduler and allocation |
| Open MPI and parallel HDF5 | Physical CPUs, memory, and network |
| GSL and HYPRE built with `maxdim=4` | NVIDIA driver and devices, exposed with `--nv` |
| Unmodified inoisy4d executable and tools | Course repository and research data bind mounts |
| Python 3.11, QuantUI, PySCF/gpu4pyscf | Output directories under `/work/$USER` |
| JupyterLab and visualization libraries | Authentication, accounts, quotas, and policy |

This boundary is central to the lesson: a container packages software; it does
not bypass Slurm, create a GPU, increase memory, or make a poor resource request
efficient.

## The two files involved

The container lesson uses two different kinds of files:

- [`ncshare-science-course.def`](ncshare-science-course.def) is the
  **definition file**: a text recipe describing the desired image.
- [`build_container.sh`](build_container.sh) is a **shell script**: a sequence
  of commands that chooses build locations, checks that the build is running
  in an approved place, invokes Apptainer, runs the tests, and writes a
  checksum.

The definition is input and the `.sif` is output. Editing a definition does
not modify an already-built SIF. A SIF is an immutable artifact, so any change
to source code, dependencies, build options, labels, or tests requires a new
build.

## How the blueprint was created

Open [`ncshare-science-course.def`](ncshare-science-course.def) and map each
section to a requirement:

1. **Base image:** NCShare documents CUDA 12.8 for its H200 environment, so the
   recipe begins with its example CUDA 12.8.1/Ubuntu 24.04 base. CPU jobs use
   the same image without GPU exposure.
2. **Compiled stack:** Ubuntu packages supply Open MPI, parallel HDF5, and GSL.
   The recipe builds HYPRE `v3.1.0` with four-dimensional SStruct support.
3. **Scientific application:** the unmodified inoisy4d default branch is
   downloaded and compiled against those libraries. The exact commit selected
   during that build is recorded inside the image. This “latest at build time”
   policy is convenient for this actively developed course application, but
   two builds on different dates may contain different source revisions.
4. **Python stack:** a Python 3.11 environment supplies Jupyter and plotting
   libraries. QuantUI `0.6.1` is installed from PyPI with its CUDA 12.x
   `gpu4pyscf`, CuPy, and cuTENSOR dependencies. A matching tagged source
   checkout is retained separately for examples and source inspection.
5. **Evidence:** labels, source commit files, resolved conda/pip manifests,
   `%test`, and a SHA-256 checksum make the built artifact inspectable.

The definition file is the human-readable blueprint. The SIF is the built
artifact. Both matter: the recipe explains intent, while the checksum identifies
the exact image that ran a job.

## 0-10 min — Read a definition file

An Apptainer definition is divided into a short header followed by `%sections`.
Not every definition needs every section, and the order below is a useful
reading order rather than a requirement to memorize syntax.

Open this course's definition with:

```bash
less containers/ncshare-science-course.def
```

- `Bootstrap: docker` tells Apptainer to begin from a Docker/OCI image.
- `From:` names that base image. It supplies Ubuntu and CUDA user-space
  libraries; it does not supply an NCShare GPU allocation or host driver.
- `%labels` stores short metadata such as dependency versions and the blueprint
  version. `apptainer inspect` displays these labels later.
- `%help` becomes built-in usage text available from the finished image.
- `%environment` sets variables such as `PATH` whenever the image runs.
  `PATH` is the ordered list of directories searched for commands.
- `%post` is the main build stage. Its commands run inside a temporary,
  writable build filesystem: install Ubuntu packages, compile HYPRE, compile
  inoisy4d, create the Python environment, and install QuantUI.
- `%runscript` defines what happens for `apptainer run IMAGE.sif`.
- `%test` contains fast checks that must pass before the image is accepted.

Indented lines belong to the section above them. Lines beginning with `#` are
comments for human readers. Build-time commands in `%post` do not run again
when a student submits a job.

### Where is the code compiled?

During `apptainer build`, Apptainer constructs a temporary writable filesystem
using the base image. Inside that build environment:

- HYPRE source is cloned below `/opt/src/hypre`, compiled with `make`, and
  installed into `/opt/hypre`;
- inoisy4d source is cloned into `/opt/inoisy4d` and compiled there against the
  packaged MPI, parallel HDF5, GSL, and HYPRE; and
- the Python environment is created at `/opt/course-env`, while a QuantUI
  source checkout is retained at `/opt/QuantUI`. The installed QuantUI package
  comes from PyPI rather than from that checkout.

Those `/opt/...` paths are paths **inside the image**, not directories students
should create in their NCShare home directories. The completed filesystem is
sealed into the SIF. Runtime jobs execute the compiled `inoisy4d` binary from
that image and write mutable results through a bind mount to `/work/$USER`.

### What if source code changes?

Changing a GitHub repository does not alter an existing image. To use changed
source, an instructor must:

1. decide which revision the definition should obtain;
2. edit the definition if its source URL, branch, commit, dependencies, or
   build command must change;
3. run a new image build in an approved allocation or CI runner;
4. rerun CPU and GPU verification plus the course jobs; and
5. publish the new SIF path or checksum so students know which artifact to use.

Because this definition selects the latest inoisy4d default branch, rebuilding
is sufficient to obtain a newer revision, but the resulting commit and SIF
checksum must be reviewed. QuantUI is pinned to a released package version;
selecting a newer release requires changing `QUANTUI_VERSION` in the
definition, rebuilding, and rerunning the GPU checks. For a student experiment,
the optional module-based lesson is often quicker than rebuilding the shared
class image.

## 10-18 min — Understand the build script

Read the wrapper before executing it:

```bash
less containers/build_container.sh
```

The first line, `#!/usr/bin/env bash`, selects Bash as the interpreter.
`set -euo pipefail` makes the script stop on failed commands, unset variables,
or failed commands hidden inside pipelines. The assignments that follow use
the form `${NAME:-default}`: use `NAME` if the caller set it, otherwise use the
displayed default.

The script then:

1. chooses the definition, output image, cache, and temporary directories;
2. refuses to build on a login node by requiring a Slurm job or CI context;
3. verifies that `apptainer` and the definition file exist;
4. creates the needed `/work/$USER` directories;
5. runs `apptainer build OUTPUT.sif INPUT.def`;
6. runs the definition's `%test` section with `apptainer test`; and
7. writes a SHA-256 checksum beside the SIF.

The cache and temporary build data are placed under `/work` because they can
be large. The checksum is a compact identity for the exact bytes of the image;
it is not a substitute for testing or reviewing the recipe.

## Build once

For a workshop, the HPC team should build and test the image before class.
Students inspect the recipe and watch or trigger one shared build rather than
launching dozens of identical downloads.

NCShare supports two routes.

### Route A: build in a compute allocation

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
srun -p workshop --time=01:00:00 --cpus-per-task=8 --mem=24G --pty bash -l
bash "$COURSE_ROOT/containers/build_container.sh"
exit
```

The `srun` options request a one-hour interactive CPU allocation with eight
cores and 24 GB of memory. `bash SCRIPT` asks Bash to execute the wrapper. The
script prints the chosen definition, cache, temporary directory, and output
image so the build record can be checked.

The script places cache, temporary build data, the image, and its checksum
under `/work/$USER` by default. A first build can take tens of minutes, so the
course uses the prebuilt result while the demonstration build continues.

### Route B: use the NCShare GitLab runner

The file [`gitlab-ci.yml`](gitlab-ci.yml) follows NCShare's documented runner
pattern. Create the project as `ncshare-science-course` so its deployed
filename matches the tutorials, then copy this file to `.gitlab-ci.yml`. The
runner builds, tests, checksums, and deploys the image. Coordinate access and
the final global image location with the HPC team.

## Inspect and verify

```bash
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
apptainer inspect "$COURSE_IMAGE"
apptainer run "$COURSE_IMAGE"
bash containers/verify_container.sh "$COURSE_IMAGE" cpu
```

`inspect` shows stored metadata, `run` invokes `%runscript`, and the verification
script invokes `%test` plus CPU-specific import, executable, MPI, and parallel
HDF5 checks. Its optional `gpu` mode must run inside a GPU allocation because
it also uses `--nv`, `nvidia-smi`, and `quantui gpu check`.

Record:

```bash
sha256sum "$COURSE_IMAGE"
apptainer inspect "$COURSE_IMAGE" \
  | grep -E 'BaseImage|HYPREVersion|inoisy4dSelection|QuantUIVersion|BlueprintVersion'
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/inoisy4d-commit.txt
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/quantui-version.txt
```

The instructor publishes the expected checksum. A mismatch is not automatically
malicious, but it means the class is not using the same artifact and should
stop to identify why. Labels describe the build recipe; the files under
`/opt/course-build` record the exact inoisy4d revision and installed QuantUI
version resolved in the finished image.

## Run MPI from the image

Open MPI in the image is the Ubuntu package: it is *not* built against this
cluster's Slurm PMI. That choice keeps the image portable, but it means the
launch pattern matters. Three cases:

**Single-rank checks (no launcher).** Exec'ing an MPI binary directly inside a
Slurm allocation fails: the inherited `SLURM_*` variables convince Open MPI it
was direct launched by `srun`, and `MPI_Init` aborts with
`OPAL ERROR: Unreachable in file ext3x_client.c`. Drop the `SLURM_*` block:

```bash
env $(env | sed -n 's/^\(SLURM[A-Z_]*\)=.*/-u \1/p') \
  apptainer exec "$COURSE_IMAGE" inoisy4d --help
```

`verify_container.sh` wraps its `inoisy4d` check this way. `--cleanenv` is a
second way to remove inherited variables. In a GPU job, it also removes useful
Slurm variables such as `CUDA_VISIBLE_DEVICES` unless the job deliberately
passes them back with `--env`. The course GPU job does this explicitly; do not
assume that `--nv` recreates scheduler metadata.

**Single node (the workshop pattern).** Use the image's own `mpirun`. Open MPI
is its own launcher here, never touches Slurm PMI, and still reads the
allocation for its slot count, so no environment surgery is needed:

```bash
apptainer exec "$COURSE_IMAGE" mpirun -n "$SLURM_NTASKS" \
  inoisy4d -n 64 -nk 128 -pgrid 1 1 1 4 -solver 0 -o output/
```

`SLURM_NTASKS` is the number of MPI ranks. `SLURM_CPUS_PER_TASK` is the number
of CPU cores assigned to each rank; substituting it for the rank count would
launch the wrong number of processes whenever those values differ.

**Multiple nodes.** `mpirun` cannot start ranks on other nodes from inside the
container, so hand the launch to Slurm's PMIx plugin and let each rank attach to
the local `slurmstepd`:

```bash
export APPTAINERENV_PMIX_MCA_gds=hash
srun --mpi=pmix apptainer exec "$COURSE_IMAGE" inoisy4d ...
```

`PMIX_MCA_gds=hash` is required. Without it the PMIx client in the container
tries to map the host `slurmstepd` shared-memory segment, cannot open it across
the mount namespace (`PMIX_ERR_FILE_OPEN_FAILURE`), and segfaults in
`pmix_gds_shmem_fetch`. This path also depends on the container's PMIx and the
host's `mpi/pmix` plugin staying compatible, which is why it is validated per
cluster rather than assumed.

## Explain the trade-offs

### Advantages

- Every student receives the same reviewed MPI, HDF5, HYPRE, Python, and CUDA
  user-space stack.
- Installation happens once, not during every job or account setup.
- The definition, labels, package manifests, and checksum improve
  reproducibility and debugging.
- The same image works from Slurm batch jobs and NCShare Open OnDemand
  JupyterLab.
- An immutable SIF is easy to distribute and difficult to modify accidentally.

### Limitations and responsibilities

- Images are large and take time, storage, and network access to build.
- A definition is not fully reproducible when upstream package repositories
  change; pin sources, retain the SIF/checksum, and rebuild deliberately.
- Security updates require a new image. Immutability does not make old software
  safe.
- `--nv` exposes compatible host NVIDIA components; CUDA does not create GPU
  access without a Slurm GPU request.
- Multi-node MPI needs a deliberate host/container MPI compatibility strategy.
  This workshop stays on one node and follows NCShare's container-internal
  `mpirun` pattern; see "Run MPI from the image" for the launch rules and the
  validated multi-node fallback.
- Containerization does not remove the need to cite, license, validate, profile,
  and understand scientific software.

## Checkpoint

With a partner, identify:

1. one dependency installed at image build time;
2. one resource still requested from Slurm;
3. the command that exposes the GPU;
4. the evidence that identifies the exact image; and
5. one reason the image should be rebuilt.

## Sources

- [NCShare Cluster Software guide](https://userguide.ncshare.org/guides/slurm/software/)
- [NCShare FHI-aims Apptainer example](https://userguide.ncshare.org/examples/apptainer-fhiaims/)
- [Apptainer definition files](https://apptainer.org/docs/user/latest/definition_files.html)
- [Apptainer MPI guidance](https://apptainer.org/docs/user/latest/mpi.html)
- [Apptainer GPU guidance](https://apptainer.org/docs/user/latest/gpu.html)
