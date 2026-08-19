# Session 2: Storage and file management

## Goal

By the end of this session, you will be able to create and organize folders on NCShare, copy and move files with `cp` and `mv`, transfer data between your
laptop and the cluster with `scp` and `rsync`, and use job-local `/scratch` inside a Slurm script.

## 1. Where files live

| Location | Use it for | Notes |
|---|---|---|
| `/hpc/home/$USER` | Scripts, configuration, small files | 50 GB per user; persists |
| `/work/$USER` | Active datasets and job output | Temporary; files older than 75 days are purged |
| `/scratch` | Fast temporary I/O inside one job | Disappears when the job ends |

No sensitive or regulated data is allowed on NCShare. See the [storage overview](https://userguide.ncshare.org/guides/overview/#data-storage) for current limits.

## 2. Create a workspace

Run this on the NCShare login node,
```bash
mkdir -p /work/$USER/course/inputs
mkdir -p /work/$USER/course/outputs
cd /work/$USER/course
pwd
ls
```

- `mkdir` creates a directory; `-p` also creates missing parent directories and does not complain if it already exists.
- `cd` changes the working directory.
- `pwd` prints the working directory, so you can confirm where you are.
- `ls` lists what is there.

`$USER` is a shell variable holding your username, so `/work/$USER` expands to your own directory.

To see how much space you are using and how much the filesystem has left,
```bash
du -sh "$HOME"
df -h "$HOME" "/work/$USER"
```

- `du` estimates how much space your files consume. `-s` gives one summary rather than every subdirectory, and `-h` uses readable units such as MB and GB.
- `df` reports capacity and free space for the whole filesystem containing a path.

They answer different questions: `du` measures your files, `df` describes the filesystem you share with everyone else.

## 3. Copy and move files

Make a file to practice with,
```bash
cd /work/$USER/course
echo "hello NCShare" > note.txt
ls -l
```

Copy it, rename it, and move it into a folder,
```bash
cp note.txt note-backup.txt        # copy a file
mv note-backup.txt note-old.txt    # rename a file
mv note-old.txt inputs/            # move a file into a folder
ls inputs
```

Work with whole folders using `-r` (recursive),
```bash
cp -r inputs inputs-copy           # copy a folder and everything in it
mv inputs-copy archive             # rename the folder
ls
```

Delete what you no longer need,
```bash
rm note.txt                        # delete a file
rm -r archive                      # delete a folder and its contents
```

- `cp SOURCE DESTINATION` copies. The original stays.
- `mv SOURCE DESTINATION` moves or renames. The original is gone.
- If the destination is an existing directory, the file is placed inside it.
- `-r` means recursive and is required for directories.
- `rm` is permanent — there is no trash on the cluster. Check the path before pressing Enter.

Useful safety flags: `cp -i` and `mv -i` ask before overwriting an existing file.

## 4. Transfer files between your laptop and NCShare

These commands run in a terminal **on your laptop**, not in the SSH session. Replace `NCSHARE_UID` with your NCShare ID.

### One file, with `scp`

Upload (push),
```bash
scp jobs.txt NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/course/inputs/
```

Download (pull). This grabs `note-old.txt`, the file you moved into `inputs/` in section 3,
```bash
scp NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/course/inputs/note-old.txt .
```

- `scp` means secure copy, and takes a source then a destination.
- The colon in `HOST:/path` separates the remote machine from the path on it.
- The final `.` means "into the current directory on my laptop."
- Add `-r` to copy a whole folder: `scp -r mydata NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/course/inputs/`
- If you use a specific key: `scp -i ~/.ssh/ncs_key ...`

### Many files or a large transfer, with `rsync`

Upload,
```bash
rsync -rP mydata/ NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/course/inputs/
```

Download,
```bash
rsync -rP NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/course/inputs/ ./inputs/
```

- `-r` copies directories recursively.
- `-P` shows progress and lets an interrupted transfer resume where it stopped.
- The trailing slash on `mydata/` means "copy the contents of this folder." Without it, `rsync` creates another folder level.
- Rerunning the same command only sends what changed, so it is safe to repeat.
- With a specific key: `rsync -e "ssh -i ~/.ssh/ncs_key" -rP ...`

See the [NCShare data transfer guide](https://userguide.ncshare.org/guides/datatransfer/) for more.

## 5. Use job-local `/scratch` in a Slurm job

`/scratch` is local, fast NVMe storage on the compute node running your job. It is ideal for temporary files a program writes and rereads many times. It is
**deleted when the job ends**, so anything you want to keep must be copied back to `/work` before the script exits.

The pattern is: copy inputs in, compute in `/scratch`, copy results out.

Create `submit.sh` on NCShare,
```bash
#!/bin/bash
#SBATCH -J scratch_demo            # Job name
#SBATCH -p workshop                # Partition
#SBATCH --cpus-per-task=2          # CPUs
#SBATCH --mem=1G                   # Memory
#SBATCH -o /work/%u/course/slurm-%j.out   # Log file (%u=user, %j=job ID)

# Permanent locations on /work
WORKDIR=/work/$USER/course

# Private, job-specific folder on the node's local disk
SCRATCH=/scratch/$USER/$SLURM_JOB_ID

mkdir -p "$SCRATCH"
mkdir -p "$WORKDIR/outputs"

# 1. Copy inputs from /work to /scratch
cp "$WORKDIR/inputs/"* "$SCRATCH/"

# 2. Do the work in /scratch
cd "$SCRATCH"
echo "Running on $(hostname) in $SCRATCH"
python3 -c "open('result.dat','w').write('done\n')"

# 3. Copy results back to /work BEFORE the job ends
cp "$SCRATCH/result.dat" "$WORKDIR/outputs/"

# 4. Clean up the scratch folder
cd "$WORKDIR"
rm -rf "$SCRATCH"
```

Submit and check it,
```bash
sbatch submit.sh
squeue -u $USER
ls /work/$USER/course/outputs
```

- `$SLURM_JOB_ID` is set by Slurm, so each job gets its own scratch folder and jobs never overwrite each other.
- Step 3 is the step people forget. If the script exits before it, the results are gone.
- Step 4 is good practice; but clusters clean `/scratch` automatically.
- Anything valuable in `/work` should eventually be transferred back to your laptop or lab storage — `/work` is purged.

## 6. Bring the result back to your laptop

Now that the job has written `outputs/result.dat`, pull it down. Run this on your **laptop**,
```bash
scp NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/course/outputs/result.dat .
```

That completes the full round trip,

```text
laptop → /work/$USER → /scratch (job) → /work/$USER → laptop
```

## Checkpoint

1. Create `/work/$USER/course/test`, copy a file into it, rename the copy, then delete the folder.
2. Upload one file from your laptop to `/work/$USER/course/inputs` with `scp`, then download it back with `scp`.
3. In the script above, which line saves your results, and what happens if you delete it?
4. Which of `$HOME`, `/work`, `/scratch` survives after a job ends? Which survives after 75 days?
