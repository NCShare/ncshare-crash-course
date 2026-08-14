# NCShare Crash Course

**Date:** August 19  
**Format:** One-day, in-person, hands-on workshop  
**Audience:** Undergraduate and graduate students, faculty, staff, and support professionals with little or no HPC experience

## Purpose

Move participants from “I have access” to “I can inspect a reproducible environment, choose resources, submit a job, and continue my analysis.” The day uses the official [NCShare guides](https://userguide.ncshare.org/guides/) and [NCShare examples](https://github.com/NCShare/examples) throughout.

## Before the workshop

Participants need an active NCShare account, SSH key-based login, a laptop with an SSH client, and the course repository.

## Learning outcomes

By the end of the workshop, participants can:

- distinguish login, compute, CPU, and GPU nodes;
- choose among `/hpc/home`, `/work`, and job-local `/scratch`;
- explain what belongs in Slurm, an Apptainer SIF, a bind mount, and the host GPU driver;
- read a definition file and identify how MPI, HYPRE, inoisy4d, Python, QuantUI, and Jupyter were packaged and tested;
- submit, monitor, diagnose, and cancel Slurm jobs;
- run the same MPI application with one and four ranks, then run one GPU workflow with reasonable resources;
- measure the same calculation on CPU and GPU, locate the crossover where the GPU starts to win, and explain why a speedup is meaningless without the CPU allocation it was measured against; and
- inspect HDF5 output, post-process a Gaussian random field, and make an accessible scientific figure.

## Agenda

### 9:00-10:00 — Welcome and introduction

Introduce NCShare and the day's goals and outcomes.

### 10:00-11:00 —  Access, cluster mental model, and essential tools

HPC admins provide and introduction to the cluster and let participants explore the hands-on session.

### 11:00-12:00 — Storage, transfer, and I/O

Choose the right storage for code, active data, temporary I/O, and retained results; practice `scp`/`rsync`.

### 12:00-1:00 — Lunch

### 1:00-1:30 — Application containers 

Introduction to Apptainer containers.

### 1:30-2:30 — CPU hands-on: containerized inoisy+

Inspect the source/build provenance inside the SIF, bind `/work/$USER`, submit the same tiny global problem with one and four MPI ranks, monitor it, compare
timing, and diagnose Slurm → Apptainer → application layers.

### 2:30-3:30 — GPU hands-on: QuantUI, and when a GPU is worth it

Inspect the Python environment and CUDA-specific wheels recorded in the SIF, separate Slurm's GPU allocation from Apptainer's `--nv` exposure, submit a small RHF calculation, and confirm `gpu_used=true` in the result — three independent mechanisms that must all agree before an offloaded calculation is
real.

Then measure the question that actually matters. Run the same calculation on CPU and GPU across a series of growing basis sets and find the **crossover**: small systems run faster on the CPU because kernel-launch and transfer overhead dominates the arithmetic, while larger ones tip decisively to the GPU. Participants record their own timings, compare results across different CPU allocations, and leave able to state why a speedup quoted without its CPU
denominator is not a result.

**Provided:** commented Apptainer definition, build/test/CI blueprints, image checksum, one-rank/four-rank/GPU Slurm files, low-resolution settings,
expected outputs, and troubleshooting checkpoints.

### 3:30-4:30 — Scientific visualization and post-processing

Launch Jupyter from the same SIF and use the previous sessions' inoisy+ and QuantUI products to make four focused figures. Students inspect HDF5 without loading the full 4D array, choose color and normalization from data meaning, compare CPU/GPU timings with an explicit denominator, show ordered scientific change, and export figures plus a reproducibility manifest. The upstream GRF-to-emissivity converter remains a separate, recorded CPU post-processing
step.

### 4:30-5:00 — Wrap-up 

Review the end-to-end workflow, locate NCShare documentation and local support, capture unresolved questions, and show how participants can contribute reusable examples back to the course or NCShare community.

**Bonus material:** repeat the build natively on a traditional cluster with a compiler/MPI/HDF5/GSL module stack and per-user conda environments, then compare
the provenance and maintenance trade-offs.