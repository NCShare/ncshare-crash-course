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
definition file + pinned source commits
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

## How the blueprint was created

Open [`ncshare-science-course.def`](ncshare-science-course.def) and map each
section to a requirement:

1. **Base image:** NCShare documents CUDA 12.8 for its H200 environment, so the
   recipe begins with its example CUDA 12.8.1/Ubuntu 24.04 base. CPU jobs use
   the same image without GPU exposure.
2. **Compiled stack:** Ubuntu packages supply Open MPI, parallel HDF5, and GSL.
   The recipe builds HYPRE `v3.1.0` with four-dimensional SStruct support.
3. **Scientific application:** the unmodified inoisy4d repository is checked
   out at a recorded commit and compiled against those libraries.
4. **Python stack:** a Python 3.11 environment supplies Jupyter and plotting
   libraries. QuantUI is checked out at a recorded commit and installed with
   CUDA 12.x `gpu4pyscf`, CuPy, and cuTENSOR wheels.
5. **Evidence:** labels, source commit files, resolved conda/pip manifests,
   `%test`, and a SHA-256 checksum make the built artifact inspectable.

The definition file is the human-readable blueprint. The SIF is the built
artifact. Both matter: the recipe explains intent, while the checksum identifies
the exact image that ran a job.

## 0-10 min — Read a definition file

Find the standard Apptainer sections:

```bash
less containers/ncshare-science-course.def
```

- `Bootstrap` and `From` select a trusted base.
- `%labels` record provenance that `apptainer inspect` can display.
- `%post` installs and compiles software at build time.
- `%environment` defines the runtime paths.
- `%runscript` defines `apptainer run`.
- `%test` rejects an image whose basic tools cannot be imported or found.

Build-time commands do not run again when a student submits a job.

## 10-18 min — Build once

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

The script places cache, temporary build data, the image, and its checksum
under `/work/$USER` by default. A first build can take tens of minutes, so the
course uses the prebuilt result while the demonstration build continues.

### Route B: use the NCShare GitLab runner

The file [`gitlab-ci.yml`](gitlab-ci.yml) follows NCShare's documented runner
pattern. Create the project as `ncshare-science-course` so its deployed
filename matches the tutorials, then copy this file to `.gitlab-ci.yml`. The
runner builds, tests, checksums, and deploys the image. Coordinate access and
the final global image location with the HPC team.

## 18-23 min — Inspect and verify

```bash
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"
apptainer inspect "$COURSE_IMAGE"
apptainer run "$COURSE_IMAGE"
bash containers/verify_container.sh "$COURSE_IMAGE" cpu
```

Record:

```bash
sha256sum "$COURSE_IMAGE"
apptainer inspect "$COURSE_IMAGE" | grep -E 'BaseImage|HYPRE|Commit|Blueprint'
```

The instructor publishes the expected checksum. A mismatch is not automatically
malicious, but it means the class is not using the same artifact and should
stop to identify why.

## 23-30 min — Explain the trade-offs

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
  `mpirun` pattern.
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
