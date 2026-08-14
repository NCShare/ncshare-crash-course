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

9:00 – 10:00    Welcome and introduction
10:00 – 11:00    Access and orientation
11:00 – 12:00  Storage and data movement
12:00 – 1:00     Lunch
1:00 – 1:30     Application containers
1:30 – 2:30     inoisy+ on CPUs
2:30 – 3:30     QuantUI on GPUs
3:30 – 4:30     Scientific visualization and post-processing
4:30 – 5:00     Wrap-up
