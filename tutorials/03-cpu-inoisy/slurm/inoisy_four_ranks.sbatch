#!/usr/bin/env bash
#SBATCH --job-name=inoisy-four
#SBATCH --partition=workshop
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/work/%u/ncshare-crash-course/logs/%x-%j.out

set -e

COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
OUTDIR="$COURSE_WORK/inoisy/four-ranks"

mkdir -p "$OUTDIR"

echo "job_id=$SLURM_JOB_ID host=$(hostname) ranks=$SLURM_NTASKS"

# This single-node workshop job uses the MPI launcher packaged in the image.
apptainer exec --cleanenv \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  mpirun -n "$SLURM_NTASKS" inoisy4d \
  -nl 16 -nj 16 -ni 16 -nk 4 \
  -pgrid 1 1 1 4 \
  -solver 0 \
  -nrecur 1 \
  -timer \
  -output "$OUTDIR"
