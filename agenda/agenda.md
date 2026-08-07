# NCShare Crash Course

**Date:** August 19  
**Format:** One-day, in-person, hands-on workshop  
**Audience:** Undergraduate and graduate students, faculty, staff, and support
professionals with little or no HPC experience

## Purpose

Move participants from “I have access” to “I can inspect a reproducible
environment, choose resources, submit a job, and continue my analysis.” The day uses the official
[NCShare guides](https://userguide.ncshare.org/guides/) and
[NCShare examples](https://github.com/NCShare/examples) throughout.

## Before the workshop

Participants need an active NCShare account, SSH key-based login, a laptop with
an SSH client, and the course repository. GPU access should be requested in
advance. A partner-based path is available for participants still waiting for
access.

## Learning outcomes

By the end of the workshop, participants can:

- distinguish login, compute, CPU, and GPU nodes;
- choose among `/hpc/home`, `/work`, and job-local `/scratch`;
- explain what belongs in Slurm, an Apptainer SIF, a bind mount, and the host
  GPU driver;
- read a definition file and identify how MPI, HYPRE, inoisy4d, Python,
  QuantUI, and Jupyter were packaged and tested;
- submit, monitor, diagnose, and cancel Slurm jobs;
- run the same MPI application with one and four ranks, then run one GPU
  workflow with reasonable resources;
- measure the same calculation on CPU and GPU, locate the crossover where the
  GPU starts to win, and explain why a speedup is meaningless without the CPU
  allocation it was measured against; and
- inspect HDF5 output, post-process a Gaussian random field, and make an
  accessible scientific figure.

## Agenda

### 9:00-9:30 — Check-in and environment setup

Connect to Wi-Fi, verify SSH or Open OnDemand access, clone the course
materials, and pair participants who are still waiting for account access.

### 9:30-9:45 — Welcome and goals

Introduce NCShare, the day’s runnable outcomes, and the faculty/administrator
teaching roles.

### 9:45-11:30 — Session 1: Access, cluster mental model, and essential tools

**9:45-10:30 — Explain and demonstrate**

- 9:45-9:55: map a laptop workflow to login node → Slurm → compute node →
  storage;
- 9:55-10:10: identify CPU/GPU resources, partitions, wall time, memory, and
  why the login node is not a compute node;
- 10:10-10:20: log in and verify identity, host, current directory, quota, and
  storage locations; and
- 10:20-10:30: use ten essential commands and the Apptainer execution model.

**HPC administrator contribution:** HPC admins provide workshop access and
teach the NCShare login/compute boundary, storage lifetimes, partitions, and
how the shared Apptainer image is built, staged, launched, and supported.

**10:30-10:45 — Break**

**10:45-11:30 — Guided practice**

- clone the course and `NCShare/examples` repositories;
- inspect files safely with `pwd`, `ls`, `cd`, `less`, `du`, and `find`;
- request a short interactive allocation and compare `hostname` before/after;
- run `apptainer inspect`, `run`, and `exec` on the shared course image; and
- complete a two-minute checkpoint: “where am I, what resources do I have,
  where will my output go?”

**Provided:** command card, annotated cluster workflow, access troubleshooting,
and a verified interactive-allocation command.

### 11:30-12:00 — Session 2: Storage, transfer, and I/O

Choose the right storage for code, active data, temporary I/O, and retained
results; practice `scp`/`rsync`; compare one large read with repeated small-file
reads; and plan the data lifecycle for the afternoon jobs.

### 12:00-1:00 — Lunch and discussion

### 1:00-3:30 — Session 3: From definition file to CPU and GPU jobs

This merged block covers the complete workflow: requirements → definition →
build/test/checksum → request resources → execute → monitor → inspect.

**1:00-1:30 — Apptainer blueprint**

- map the scientific requirements to a commented definition file;
- explain the CUDA base, Open MPI/parallel HDF5/GSL packages, HYPRE build,
  unmodified inoisy4d build, and Python/QuantUI/Jupyter environment;
- distinguish what is inside the SIF from Slurm resources, host drivers, and
  bind-mounted data;
- inspect labels, package manifests, tests, and SHA-256 provenance; and
- discuss build-once/reuse, security rebuilds, image size, and MPI compatibility.

The HPC team prebuilds the SIF and demonstrates the approved NCShare build or
GitLab pipeline; participants use the tested image while a demonstration build
continues.

**1:30-2:15 — CPU hands-on: containerized inoisy+**

Inspect the source/build provenance inside the SIF, bind `/work/$USER`, submit
the same tiny global problem with one and four MPI ranks, monitor it, compare
timing, and diagnose Slurm → Apptainer → application layers.

**2:15-2:30 — Break**

**2:30-3:30 — GPU hands-on: QuantUI, and when a GPU is worth it**

Inspect the Python environment and CUDA-specific wheels recorded in the SIF,
separate Slurm's GPU allocation from Apptainer's `--nv` exposure, submit a
small RHF calculation, and confirm `gpu_used=true` in the result — three
independent mechanisms that must all agree before an offloaded calculation is
real.

Then measure the question that actually matters. Run the same calculation on
CPU and GPU across a series of growing basis sets and find the **crossover**:
small systems run faster on the CPU because kernel-launch and transfer
overhead dominates the arithmetic, while larger ones tip decisively to the
GPU. Participants record their own timings, compare results across different
CPU allocations, and leave able to state why a speedup quoted without its CPU
denominator is not a result.

**Provided:** commented Apptainer definition, build/test/CI blueprints, image
checksum, one-rank/four-rank/GPU Slurm files, low-resolution settings,
expected outputs, and troubleshooting checkpoints.

### 3:30-4:30 — Session 4: Scientific visualization and post-processing

Launch Jupyter from the same SIF, inspect the inoisy+ HDF5 result without
loading the full 4D array, plot distributions and slices, select honest
normalization and color maps, run the containerized upstream
GRF-to-emissivity converter, and export a reproducible PNG/PDF figure.

### 4:30-5:00 — Wrap-up and next steps

Review the end-to-end workflow, locate NCShare documentation and local support,
capture unresolved questions, and show how participants can contribute reusable
examples back to the course or NCShare community.

**Bonus material:** repeat the build natively on a traditional cluster with a
compiler/MPI/HDF5/GSL module stack and per-user conda environments, then compare
the provenance and maintenance trade-offs.
