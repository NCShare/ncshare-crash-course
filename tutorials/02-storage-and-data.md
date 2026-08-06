# Session 2: Storage, transfer, and I/O

## Goal

By the end of this session, you will be able to choose storage based on how
long a file must live, move data between your laptop and NCShare, and recognize
an inefficient small-file workflow.

Storage is part of the computational design, not an afterthought. A job can
finish correctly and still lose its useful output if it was left in temporary
storage. Review the current NCShare policies in the
[storage overview](https://userguide.ncshare.org/guides/overview/#data-storage) and transfer
methods in the
[data-transfer guide](https://userguide.ncshare.org/guides/datatransfer/).

## 1. Create the active workspace

Run this after connecting to the NCShare login node:

```bash
mkdir -p "/work/$USER/ncshare-crash-course"/{inputs,outputs,logs}
```

The shell expands the braces into three paths, so this one command creates
`inputs`, `outputs`, and `logs`. Quoting the fixed part protects the pathname;
`$USER` is replaced with your username. The result is equivalent to three
separate `mkdir -p` commands.

Use the subdirectories consistently:

- `inputs` for data copied to NCShare;
- `outputs` for results that jobs must preserve; and
- `logs` for Slurm's text record of what each job printed.

## 2. Choose storage by lifetime and purpose

For each item, choose a location before revealing the suggested answer:

| Item | Suggested location | Why |
|---|---|---|
| Course repository and small configuration | `/hpc/home/$USER` | Small user files that must persist between sessions |
| Shared course SIF | `/opt/apps/containers/user` | One reviewed image readable from cluster nodes |
| Temporary image-build cache | `/work/$USER/...` | Large, replaceable build data |
| Input for the current analysis | `/work/$USER/.../inputs` | Active data used by scheduled jobs |
| Large intermediate arrays | Job-local `/scratch` | Fast temporary I/O during one job |
| Result needed after the job | `/work/$USER/.../outputs`, then transfer off NCShare | Survives the job but is not archival storage |
| Sensitive or regulated data | Nowhere on NCShare | Not permitted |

A useful lifecycle is:

```text
laptop/archive → /work input → job-local /scratch → /work output → laptop/archive
```

`/scratch` is local to a job and may disappear when that job ends. If a job
stages data there, its script must copy the final result back to `/work` before
exiting. `/work` itself has a purge policy, so it is active storage rather than
a permanent archive.

## 3. Transfer one file

The next command runs on your **laptop**, not in the SSH session:

```bash
scp local-file NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/ncshare-crash-course/inputs/
```

Replace both occurrences of `NCSHARE_UID` with your NCShare ID and replace
`local-file` with a real path on your laptop.

`scp` means secure copy. Its two main arguments are the source and destination.
The colon in `HOST:/remote/path` separates the remote computer name from the
path on that computer. This example uploads a file; reverse the arguments to
download one:

```bash
scp NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/ncshare-crash-course/outputs/result.dat .
```

The final `.` means “the current directory on my laptop.”

## 4. Transfer a directory or resume a transfer

For directories and transfers that may need to resume, run on your laptop:

```bash
rsync -rP local-directory/ NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/ncshare-crash-course/inputs/
```

- `rsync` compares source and destination and transfers what is needed.
- `-r` recursively includes files below the directory.
- `-P` shows progress and keeps partially transferred files so the command can
  continue later.
- The trailing slash in `local-directory/` means “copy the directory's
  contents.” Without it, `rsync` may create another directory level.

Rerunning the same command is normally safe: unchanged files do not need to be
sent again. Read the displayed source and destination carefully before adding
deletion options; this course does not use them.

## 5. Understand the I/O rule of thumb

Opening a file requires metadata work before its contents can be read. A
workflow that repeatedly opens thousands of tiny files can burden a shared
filesystem more than one that reads the same number of bytes from a few large
files.

When practical:

- store related arrays in a structured format such as HDF5;
- open a file once and reuse the data already in memory;
- bundle many tiny inputs; or
- stage temporary high-I/O data to job-local `/scratch`, then copy back only
  the results.

These are design guidelines, not a command to load an entire production
dataset into memory. The visualization tutorial demonstrates inspecting HDF5
metadata and one slice without loading a complete four-dimensional array.

## Checkpoint

On the NCShare login node, inspect the workspace:

```bash
du -sh "/work/$USER/ncshare-crash-course"
find "/work/$USER/ncshare-crash-course" -maxdepth 2 -type f
```

The first command summarizes disk use. The second lists ordinary files no more
than two directory levels below the course workspace. Before continuing,
identify which outputs you will transfer off NCShare and which files can be
recreated.
