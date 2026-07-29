# Session 1: Access, cluster mental model, and essential tools

## Goal

End with a shell on a compute node, a clear storage choice, and the ability to
inspect and execute the shared course container.

## 1. Identify where you are

After connecting to NCShare:

```bash
hostname -A
whoami
pwd
echo "$HOME"
```

The login node is the cluster's front desk: edit, move files, and submit jobs
there. Computation belongs in a Slurm allocation.

## 2. Inspect storage

```bash
ls -ld "$HOME" "/work/$USER"
du -sh "$HOME"
df -h "$HOME" "/work/$USER"
```

Use `$HOME` for scripts and the course repository, `/work/$USER` for active
datasets and outputs, and `/scratch` only inside a job. The HPC team stages the
shared course SIF under `/opt/apps/containers/user`.

## 3. Practice the essential commands

```bash
mkdir -p "$HOME/ncshare-practice"
cd "$HOME/ncshare-practice"
printf "NCShare practice\n" > note.txt
cp note.txt note-copy.txt
mv note-copy.txt renamed.txt
ls -lah
less note.txt
du -sh .
find . -maxdepth 1 -type f
```

## 4. Clone and inspect official examples

```bash
cd "$HOME"
git clone https://github.com/NCShare/examples.git
cd examples
find . -maxdepth 2 -type f | sort
less README.md
less Apptainer-Recipe-for-FHI-aims/fhiaims.def
```

If it already exists:

```bash
cd "$HOME/examples"
git pull --ff-only
```

## 5. Request a compute shell and enter the environment

Use the instructor-provided workshop partition when available:

```bash
srun -p workshop --time=00:10:00 --cpus-per-task=2 --mem=2G --pty bash -l
```

Otherwise, use the partition approved by the instructor. Inside the allocation:

```bash
hostname -A
echo "$SLURM_JOB_ID"
echo "$SLURM_CPUS_PER_TASK"
export COURSE_IMAGE="/opt/apps/containers/user/ncshare-science-course.sif"
apptainer --version
apptainer inspect "$COURSE_IMAGE"
apptainer exec "$COURSE_IMAGE" python --version
apptainer exec "$COURSE_IMAGE" mpirun --version
exit
```

## Checkpoint

Without looking back, answer:

1. Am I on a login node or a compute node?
2. How many CPUs and how much time did I request?
3. Which parts of the workflow come from Slurm, the SIF, and bind-mounted data?
4. Which files belong in `$HOME`, `/work/$USER`, and `/scratch`?
