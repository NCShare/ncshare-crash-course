# NCShare quick reference

## Where commands run

| Place                  | Use it for                                             | Do not use it for              |
| ---------------------- | ------------------------------------------------------ | ------------------------------ |
| Login node             | edit files, submit/monitor jobs, light file management | compilation or computation     |
| Interactive allocation | compile, debug, test, inspect GPUs                     | work after the allocation ends |
| Batch job              | reproducible CPU/GPU runs                              | interactive editing            |

## Storage

| Path | Intended use | Important behavior |
|---|---|---|
| `/hpc/home/$USER` | scripts, source, course repository, small user setup | 50 GB; removed when the account expires |
| `/work/$USER` | active inputs and generated results | files older than 75 days are purged |
| `/opt/apps/containers/users` | shared Apptainer images staged with the HPC team | available across cluster nodes |
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

## Apptainer

```bash
export COURSE_IMAGE="/opt/apps/containers/users/ncshare-science-course.sif"
apptainer inspect "$COURSE_IMAGE"
apptainer run "$COURSE_IMAGE"
apptainer exec "$COURSE_IMAGE" python --version
apptainer shell "$COURSE_IMAGE"
apptainer exec --bind /host/path:/container/path "$COURSE_IMAGE" COMMAND
apptainer exec --nv "$COURSE_IMAGE" nvidia-smi
```

`--gres=gpu:h200:1` allocates a GPU through Slurm; `--nv` exposes it inside
the container. Use both for GPU jobs. Single-node MPI examples in this course
call the image's `mpirun` from `apptainer exec`; multi-node MPI requires an
administrator-validated host/container compatibility strategy.

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
- [FHI-aims Apptainer example](https://userguide.ncshare.org/examples/apptainer-fhiaims/)
- [Data Transfer](https://userguide.ncshare.org/guides/datatransfer/)
- [NCShare examples](https://github.com/NCShare/examples)
