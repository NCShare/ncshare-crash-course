# NCShare quick reference

## Where commands run

| Place | Use it for | Do not use it for |
|---|---|---|
| Login node | edit files, submit/monitor jobs, light file management | compilation or computation |
| Interactive allocation | compile, debug, test, inspect GPUs | work after the allocation ends |
| Batch job | reproducible CPU/GPU runs | interactive editing |

## Storage

| Path | Intended use | Important behavior |
|---|---|---|
| `/hpc/home/$USER` | scripts, source, conda environments, user software | 50 GB; removed when the account expires |
| `/work/$USER` | active inputs and generated results | files older than 75 days are purged |
| `/data/projectname` | requested shared project allocation | limited duration; request through institutional contacts |
| `/scratch` | job-local high-performance temporary I/O | copy results out before the job ends |

Sensitive data is not permitted on NCShare storage, and NCShare storage is not
long-term archival storage.

## Ten commands to know

```bash
pwd
ls -lah
cd path
mkdir -p directory
cp source destination
mv old new
less file
du -sh path
find path -maxdepth 2 -type f
man command
```

## Modules

```bash
module avail
module spider openmpi
module load compilers/gcc/12.3.0
module load mpi/openmpi/4.1.6
module list
module purge
```

## Slurm

```bash
sbatch job.sbatch
squeue -u "$USER"
scontrol show job JOB_ID
sacct -j JOB_ID --format=JobID,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
scancel JOB_ID
```

## Data transfer

Run these on your laptop, not from the NCShare login node:

```bash
scp local-file NCSHARE_UID@login.ncshare.org:/hpc/home/NCSHARE_UID/
rsync -rP local-directory/ NCSHARE_UID@login.ncshare.org:/work/NCSHARE_UID/project/
```

Use `scp` for individual files and `rsync -rP` for directories or restartable
transfers.

## Official references

- [NCShare guides](https://userguide.ncshare.org/guides/)
- [Cluster Computing and Slurm](https://userguide.ncshare.org/guides/slurm/)
- [Cluster Software](https://userguide.ncshare.org/guides/slurm/software/)
- [GPU Guide](https://userguide.ncshare.org/guides/gpu/)
- [Data Transfer](https://userguide.ncshare.org/guides/datatransfer/)
- [NCShare examples](https://github.com/NCShare/examples)
