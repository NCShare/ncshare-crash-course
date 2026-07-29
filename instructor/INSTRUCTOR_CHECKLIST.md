# Instructor and HPC administrator readiness checklist

Complete this checklist at least one week before the workshop.

## Access and capacity

- [ ] All participants have NCShare accounts and have registered an SSH public
  key.
- [ ] GPU participants have access to `gpu` or `interactive-gpu`.
- [ ] A temporary `workshop` partition/reservation is available, or the
  tutorials have been changed to the approved teaching partition.
- [ ] The class concurrency limit can accommodate the planned CPU and GPU jobs.
- [ ] Open OnDemand JupyterLab is working for the visualization session.

## Validate the documented platform

Run these checks in a test allocation, not only on a login node:

```bash
module avail
module load compilers/gcc/12.3.0
module load mpi/openmpi/4.1.6
module load libs/hdf5/1.14.6
module load libs/gsl/2.7.1

mpicxx --version
h5pcc -showconfig | grep -i "Parallel HDF5"
srun -p interactive --time=00:05:00 --pty bash -l
```

- [ ] Replace module names in the course if NCShare has changed them.
- [ ] Confirm that `h5pcc` links to the same MPI family loaded for HYPRE.
- [ ] Confirm that parallel HDF5 reports `yes`.
- [ ] Confirm GitHub and Python-package downloads are permitted from the
  teaching allocation.

## Pre-stage fallbacks

- [ ] Run `setup_hypre.sh` in a fresh user account and record build time.
- [ ] If the build exceeds 15 minutes, provide a read-only class HYPRE prefix
  built with `--enable-bigint --enable-maxdim=4`; still walk through the
  student-owned install script.
- [ ] Pre-warm or mirror Miniforge, PySCF, and CUDA 12.x wheels if external
  downloads are rate-limited.
- [ ] Run both one-rank and four-rank inoisy+ jobs and verify the expected global dataset shape is
  `(16, 16, 16, 16)`.
- [ ] Run the QuantUI job and verify that `gpu_used` is `true`.
- [ ] Execute every cell of the visualization notebook against a real inoisy+
  output.

## Course-repository edits before publishing

- [ ] Replace `<COURSE_REPOSITORY_URL>` in `tutorials/00-prework.md`.
- [ ] Add the final year, room, contacts, and support channel to the agenda.
- [ ] Choose and add a license for the new course material; retain external
  project licenses and citations.
- [ ] Keep the small fallback HDF5 files so students can complete the notebook
  during a queue delay.

## One-sentence administrator role

HPC admins provide workshop access and teach the NCShare login/compute boundary, storage lifetimes, partitions, and support path.
