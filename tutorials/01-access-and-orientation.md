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

## 2. See where you can write

Files are organized in a directory tree. You have two places of your own on NCShare,
```bash
ls -ld "$HOME" "/work/$USER"
```

- `ls` lists files. `-l` requests details such as owner and permissions, and `-d` describes each directory itself instead of listing its contents.
- `$HOME` is your home directory, for scripts and small files.
- `/work/$USER` is for active datasets and job output.

The HPC team stages the shared course image under `/opt/apps/containers/users`. Session 2 covers what belongs in each location, how much space you get,
and how long files survive.

## 3. Read the shape of a command

Commands usually follow the pattern `command options arguments`. In `ls -ld "$HOME"`, `ls` is the command, `-ld` combines two options, and the path is the
argument. Options are usually a single letter after one dash, and several can be combined: `-l -d` and `-ld` mean the same thing.

To read a command's manual,
```bash
man ls
```

Press `q` to leave the manual. `man` works for nearly every command in this course, and is faster than searching the web for what a flag does.

## 4. Clone and inspect official examples

Git records versions of a collection of files called a **repository**. The command below downloads a working copy of NCShare's official examples from GitHub:

```bash
cd "$HOME"
git clone https://github.com/NCShare/examples.git
cd examples
find . -maxdepth 2 -type f | sort
less README.md
less Apptainer-Recipe-for-FHI-aims/fhiaims.def
```

- `find` searches below a path. Here `-maxdepth 2` prevents a deep recursive search and `-type f` selects ordinary files.
- The vertical bar `|`, called a **pipe**, sends the output of `find` into `sort`. It lets small commands be combined without creating an intermediate file.
- `less` opens a text file one screen at a time. Press `q` to quit.

`README.md` is a Markdown text file, while `.def` is an Apptainer definition file discussed in the container session.

If the repository already exists, update it instead of cloning a second copy:
```bash
cd "$HOME/examples"
git pull 
```

`git pull` retrieves newer commits. 

## 5. Request a compute shell

Slurm is the cluster's scheduler. It decides when and where work runs based on the resources requested by all users. An **interactive allocation** gives you
a shell on a compute node for a limited time,

```bash
srun -p workshop --time=00:10:00 --cpus-per-task=2 --mem=1G --pty bash -i
```

This asks Slurm to,

- use the `workshop` partition (`-p workshop`);
- reserve ten minutes (`--time=00:10:00`);
- provide two CPU cores to one task (`--cpus-per-task=2`);
- reserve 1 GB of memory (`--mem=1G`); and
- attach an interactive login-style Bash shell (`--pty bash -i`).

A **partition** is a named group or scheduling policy for compute resources.
Use the instructor-approved partition if `workshop` is not available. The job
may wait in the queue before the prompt changes.

Inside the allocation, compare the new environment with the login node,
```bash
hostname -A
echo "$SLURM_JOB_ID"
echo "$SLURM_CPUS_PER_TASK"
```

The hostname should now identify a compute node. Slurm created the two variables and exported them into this shell.

## Checkpoint

Without looking back, answer:

1. Am I on my laptop, a login node, or a compute node? Which command proves it?
2. How many CPUs, how much memory, and how much time did I request?
3. What do `$HOME`, `$USER`, and `$SLURM_JOB_ID` mean?
4. How would I find out what the `-h` option does for a command I have not seen before?
