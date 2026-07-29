# Session 2: Storage, transfer, and I/O

## Goal

Place each file according to its lifetime and access pattern, then transfer data
with a restartable command.

## Data-lifecycle exercise

Create the active course workspace:

```bash
mkdir -p "/work/$USER/ncshare-crash-course"/{inputs,outputs,logs}
```

For each item, choose a location before revealing the suggested answer:

| Item | Suggested location | Why |
|---|---|---|
| Git repositories and conda environments | `/hpc/home/$USER` | small, persistent user setup |
| Input copied in for this analysis | `/work/$USER/.../inputs` | active data |
| Large intermediate arrays | job-local `/scratch` | fast temporary I/O |
| Result needed after the job | `/work/$USER/.../outputs`, then transfer out | survives job, but not archival |
| Sensitive or regulated data | nowhere on NCShare | not permitted |

## Transfer a file

On your laptop:

```bash
scp local-file NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/ncshare-crash-course/inputs/
```

For a directory or restartable transfer:

```bash
rsync -rP local-directory/ NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/ncshare-crash-course/inputs/
```

## I/O rule of thumb

Many tiny reads create more metadata traffic than one contiguous read. When a
workflow repeatedly opens thousands of small files, consider bundling them,
reading once and reusing memory, or staging them to job-local `/scratch`.

## Checkpoint

```bash
du -sh "/work/$USER/ncshare-crash-course"
find "/work/$USER/ncshare-crash-course" -maxdepth 2 -type f
```

State which outputs you will transfer off NCShare after the workshop.
