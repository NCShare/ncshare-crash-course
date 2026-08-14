# Session 1: Access, cluster mental model, and essential tools

## Goal

By the end of this session, you will be able to connect to NCShare, tell whether you are on a login or compute node, move around the filesystem, and
start software from the shared course container.

This tutorial assumes that you are new to terminals and HPC. The official [NCShare SSH setup guide](https://userguide.ncshare.org/guides/setupssh/) contains the current connection instructions and troubleshooting information. Use that guide when the details here and the live service differ.

## Before typing commands: terminal, shell, and prompt

A **terminal** is the text-based application in which you type commands. On macOS, open Terminal; on Windows, use the terminal and SSH method recommended
in the NCShare guide. After you connect with SSH, the terminal displays a **shell prompt**, often ending in `$`. Type each command after that prompt and
press Enter. Do not type the prompt character itself.

For example,
```bash
ssh NCSHARE_UID@login.ncshare.org
```

Replace `NCSHARE_UID` with your NCShare user ID. `ssh` means Secure Shell: it opens an encrypted command-line session on the remote login service. Your
private SSH key stays on your laptop; NCShare uses the corresponding public key to recognize you.

## 1. Understand where you are

An HPC cluster is a group of computers with different roles:

- your **laptop** is where you start the connection;
- a **login node** is the cluster's front desk, used for editing files, transferring data, and submitting jobs; and
- a **compute node** supplies CPUs, memory, and sometimes GPUs for actual computation after Slurm allocates them.

Do not run a simulation or other sustained computation on a login node. The [NCShare cluster and Slurm guide](https://userguide.ncshare.org/guides/slurm/)
explains how work is assigned to compute nodes.

After connecting to NCShare, type these commands one at a time,
```bash
hostname -A
whoami
pwd
echo "$HOME"
```

What each command means:

- `hostname -A` asks the computer for its full hostname. This helps you tell whether the shell is on a login node or a compute node. `-A` is an **option** that asks for all fully qualified hostnames.
- `whoami` prints the user account under which the command is running.
- `pwd` means “print working directory.” The working directory is the folder where relative filenames are interpreted.
- `echo` prints text. Here it prints the value of the shell variable `HOME`.

A **shell variable** is a named value. `$HOME` means “substitute the value of the variable named `HOME` here.” The `$` is not part of the variable's name.
Double quotes keep the substituted path together if it ever contains spaces. Other variables used later include `$USER`, the current username, and `$SLURM_JOB_ID`, the identifier Slurm assigns to a job.

## 2. Inspect storage

Files are organized in a directory tree. NCShare provides different storage locations because small persistent files, active research data, and temporary
high-I/O files have different needs. The [NCShare storage overview](https://userguide.ncshare.org/guides/overview/#data-storage) is the authority for current limits, lifetimes, and permitted data.

Run,
```bash
ls -ld "$HOME" "/work/$USER"
du -sh "$HOME"
df -h "$HOME" "/work/$USER"
```

- `ls` lists files. `-l` requests details such as owner and permissions, and `-d` describes each directory itself instead of listing its contents.
- `du` estimates how much space files consume. `-s` gives one summary rather than every subdirectory, and `-h` uses readable units such as MB and GB.
- `df` reports capacity and free space for the filesystem containing a path; `-h` again requests readable units.

Use `$HOME` for small scripts, configuration, and the course repository. Use `/work/$USER` for active datasets and job output. Use `/scratch` only from
inside a job, and copy anything valuable out before the job ends. The HPC team stages the shared course image under `/opt/apps/containers/user`.

`du` and `df` answer different questions: `du` measures your files, while `df` describes the filesystem as a whole.

## 3. Practice the essential file commands

The following creates a safe practice directory in your home directory,
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

Read the sequence before running it:

- `mkdir` creates a directory. `-p` also creates missing parent directories and does not fail if the directory already exists.
- `cd` changes the working directory. The next commands therefore operate in `ncshare-practice`.
- `printf` produces the text `NCShare practice`. `\n` means a new line. The `>` redirects that output into `note.txt`; it creates or overwrites the file, so use redirection carefully.
- `cp SOURCE DESTINATION` copies a file.
- `mv SOURCE DESTINATION` moves or renames a file.
- `ls -lah` combines long format (`-l`), hidden files (`-a`), and readable sizes (`-h`).
- `less` opens a text file one screen at a time. Press `q` to quit.
- `.` means the current directory, so `du -sh .` summarizes the directory you are in.
- `find` searches below a path. Here `-maxdepth 1` prevents a deep recursive search and `-type f` selects ordinary files.

Commands usually follow the pattern `command options arguments`. In `cp note.txt note-copy.txt`, `cp` is the command and the two filenames are
arguments. Use `man COMMAND`, such as `man cp`, to open a command's manual; press `q` to leave it.

## 4. Clone and inspect official examples

Git records versions of a collection of files called a **repository**. The
command below downloads a working copy of NCShare's official examples from
GitHub:

```bash
cd "$HOME"
git clone https://github.com/NCShare/examples.git
cd examples
find . -maxdepth 2 -type f | sort
less README.md
less Apptainer-Recipe-for-FHI-aims/fhiaims.def
```

The vertical bar `|`, called a **pipe**, sends the output of `find` into
`sort`. It lets small commands be combined without creating an intermediate
file. `README.md` is a Markdown text file, while `.def` is an Apptainer
definition file discussed in the container session.

If the repository already exists, update it instead of cloning a second copy:

```bash
cd "$HOME/examples"
git pull --ff-only
```

`git pull` retrieves newer commits. `--ff-only` refuses to create an automatic
merge, which is helpful for a course copy that students are not expected to
edit.

## 5. Request a compute shell

Slurm is the cluster's scheduler. It decides when and where work runs based on
the resources requested by all users. An **interactive allocation** gives you
a shell on a compute node for a limited time:

```bash
srun -p workshop --time=00:10:00 --cpus-per-task=2 --mem=2G --pty bash -l
```

This asks Slurm to:

- use the `workshop` partition (`-p workshop`);
- reserve ten minutes (`--time=00:10:00`);
- provide two CPU cores to one task (`--cpus-per-task=2`);
- reserve 2 GB of memory (`--mem=2G`); and
- attach an interactive login-style Bash shell (`--pty bash -l`).

A **partition** is a named group or scheduling policy for compute resources.
Use the instructor-approved partition if `workshop` is not available. The job
may wait in the queue before the prompt changes.

Inside the allocation, compare the new environment with the login node:

```bash
hostname -A
echo "$SLURM_JOB_ID"
echo "$SLURM_CPUS_PER_TASK"
```

The hostname should now identify a compute node. Slurm created the two
variables and exported them into this shell.

## 6. Inspect and run the course container

An Apptainer **SIF image** is a read-only file containing an application and
its user-space software environment. It does not allocate CPUs or GPUs; Slurm
did that in the previous step. The
[NCShare software guide](https://userguide.ncshare.org/guides/slurm/software/)
explains why containers are the normal route for packaged scientific software
on NCShare.

```bash
export COURSE_IMAGE="/opt/apps/containers/user/ncshare-science-course.sif"
apptainer --version
apptainer inspect "$COURSE_IMAGE"
apptainer exec "$COURSE_IMAGE" python --version
apptainer exec "$COURSE_IMAGE" mpirun --version
exit
```

- `export NAME=value` creates a shell variable and makes it available to
  programs started from the shell. We store the long image path once in
  `COURSE_IMAGE` so later commands are easier to read.
- `apptainer --version` checks that Apptainer is installed on the host.
- `apptainer inspect IMAGE` prints labels and metadata stored in the image.
- `apptainer exec IMAGE COMMAND` runs one command using software from the
  image. Here it reports the packaged Python and MPI versions.
- `exit` leaves the compute shell and returns to the login node. The allocation
  also ends when its time limit expires.

## Checkpoint

Without looking back, answer:

1. Am I on my laptop, a login node, or a compute node? Which command proves it?
2. How many CPUs, how much memory, and how much time did I request?
3. Which parts came from Slurm and which came from the SIF?
4. What do `$HOME`, `$USER`, and `$SLURM_JOB_ID` mean?
5. Which files belong in `$HOME`, `/work/$USER`, and `/scratch`?
