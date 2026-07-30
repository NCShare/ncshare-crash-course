#!/usr/bin/env bash
#SBATCH --job-name=quantui-gpu
#SBATCH --partition=workshop
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:h200:1
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=/work/%u/ncshare-crash-course/logs/%x-%j.out

# TODO (confirm before the workshop): partition name and --gres string.
# TODO (confirm before the workshop): resource allocation
#   NCShare GPU nodes carry 8 H200s alongside ~96 physical cores, so roughly
#   12 cores per GPU. Four is a comfortable share for this single-GPU example.

set -euo pipefail

COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"
COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"

if [[ ! -f "$COURSE_IMAGE" ]]; then
  echo "Course image not found: $COURSE_IMAGE" >&2
  exit 2
fi

mkdir -p "$COURSE_WORK/quantui"
QUANTUI_COMMIT="$(
  apptainer exec "$COURSE_IMAGE" \
    cat /opt/course-build/quantui-commit.txt
)"

echo "job_id=$SLURM_JOB_ID host=$(hostname)"
echo "course_image=$COURSE_IMAGE"
echo "quantui_commit=$QUANTUI_COMMIT"

# --gres allocates the GPU; --nv exposes the host NVIDIA driver and devices
# inside the container. Both are required, and neither alone proves offload.
apptainer exec --nv --cleanenv \
  "$COURSE_IMAGE" \
  nvidia-smi --query-gpu=name,driver_version,memory.total \
    --format=csv,noheader

apptainer exec --nv --cleanenv \
  "$COURSE_IMAGE" \
  quantui gpu check

apptainer exec --nv --cleanenv \
  --bind "$COURSE_ROOT:$COURSE_ROOT" \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  --env "COURSE_WORK=$COURSE_WORK" \
  --env "COURSE_IMAGE=$COURSE_IMAGE" \
  --env "QUANTUI_COMMIT=$QUANTUI_COMMIT" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --env "OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK" \
  "$COURSE_IMAGE" \
  python "$COURSE_ROOT/tutorials/04-gpu-quantui/run_quantui_gpu.py"
