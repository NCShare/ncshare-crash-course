#!/usr/bin/env bash
#SBATCH --job-name=inoisy-one
#SBATCH --partition=workshop
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/work/%u/ncshare-crash-course/logs/%x-%j.out

set -euo pipefail

COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"
COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
OUTDIR="$COURSE_WORK/inoisy/one-rank"

if [[ ! -f "$COURSE_IMAGE" ]]; then
  echo "Course image not found: $COURSE_IMAGE" >&2
  exit 2
fi

mkdir -p "$OUTDIR"

echo "job_id=$SLURM_JOB_ID host=$(hostname) ranks=$SLURM_NTASKS"
echo "course_image=$COURSE_IMAGE"
apptainer inspect "$COURSE_IMAGE" \
  | grep -E 'BaseImage|HYPREVersion|inoisy4dCommit|BlueprintVersion' || true

# NCShare's documented single-node pattern runs mpirun inside the image.
apptainer exec --cleanenv \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  mpirun -n 1 inoisy4d \
  -nl 16 -nj 16 -ni 16 -nk 16 \
  -pgrid 1 1 1 1 \
  -solver 0 \
  -nrecur 1 \
  -timer \
  -output "$OUTDIR"
