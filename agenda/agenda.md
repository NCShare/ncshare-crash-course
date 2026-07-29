# NCShare Crash Course

**Date:** August 19  
**Format:** One-day, in-person, hands-on workshop  
**Audience:** Undergraduate and graduate students, faculty, staff, and support
professionals with little or no HPC experience

## Purpose

Move participants from “I have access” to “I can choose resources, submit a
job, inspect its output, and continue my analysis.” The day uses the official
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
- load modules, install a user-space library, compile C/MPI code, and manage a
  conda environment;
- submit, monitor, diagnose, and cancel Slurm jobs;
- run the same MPI application with one and four ranks, then run one GPU
  workflow with reasonable resources; and
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
- 10:20-10:30: use the ten essential commands and the module system.

**HPC administrator contribution:** HPC admins provide workshop access and teach the NCShare login/compute boundary, storage lifetimes, partitions, and support path.

**10:30-10:45 — Break**

**10:45-11:30 — Guided practice**

- clone the course and `NCShare/examples` repositories;
- inspect files safely with `pwd`, `ls`, `cd`, `less`, `du`, and `find`;
- request a short interactive allocation and compare `hostname` before/after;
- run `module avail`, load a compiler/MPI stack, and inspect it; and
- complete a two-minute checkpoint: “where am I, what resources do I have,
  where will my output go?”

**Provided:** command card, annotated cluster workflow, access troubleshooting,
and a verified interactive-allocation command.

### 11:30-12:00 — Session 2: Storage, transfer, and I/O

Choose the right storage for code, active data, temporary I/O, and retained
results; practice `scp`/`rsync`; compare one large read with repeated small-file
reads; and plan the data lifecycle for the afternoon jobs.

### 12:00-1:00 — Lunch and discussion

### 1:00-3:30 — Session 3: From source code to CPU and GPU jobs

This merged block covers the complete cluster workflow: clone → environment →
compile/install → request resources → submit → monitor → inspect → improve.

**1:00-1:45 — CPU hands-on: unmodified inoisy+**

- clone a real scientific C/MPI repository and inspect its README/Makefile;
- load the compiler, MPI, parallel HDF5, and GSL modules;
- install a user-space, four-dimensional HYPRE build;
- compile the unmodified `inoisy4d` source without editing its Makefile; and
- submit the same tiny global problem with one and four MPI ranks to produce
  HDF5 output.

**1:45-2:15 — Scheduler and efficiency debrief**

Monitor with `squeue`, inspect logs and `sacct`, compare one-rank/four-rank
timing, and diagnose pending or failed jobs without requesting unneeded
resources.

**2:15-2:30 — Break**

**2:30-3:15 — GPU hands-on: QuantUI**

Create a dedicated conda environment, clone/install QuantUI and CUDA-specific
GPU wheels, verify the H200 allocation, submit a small RHF calculation, and
confirm from the result that GPU offload occurred.

**3:15-3:30 — CPU/GPU comparison**

Compare the CPU and GPU Slurm files, identify work that does not benefit from a
GPU, and record one resource change participants would make before scaling up.

**Provided:** build helpers, one-rank/four-rank/GPU Slurm files, pinned HYPRE
setup, low-resolution settings, expected outputs, and troubleshooting
checkpoints.

### 3:30-4:30 — Session 4: Scientific visualization and post-processing

Use the inoisy+ HDF5 result in Jupyter to inspect metadata without loading the
full 4D array, plot distributions and slices, select honest normalization and
color maps, run the upstream GRF-to-emissivity converter, compare raw and
emissivity fields, and export a reproducible PNG/PDF figure.

### 4:30-5:00 — Wrap-up and next steps

Review the end-to-end workflow, locate NCShare documentation and local support,
capture unresolved questions, and show how participants can contribute reusable
examples back to the course or NCShare community.
