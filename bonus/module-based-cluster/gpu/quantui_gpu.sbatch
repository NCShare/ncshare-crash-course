#!/usr/bin/env bash
#SBATCH --job-name=quantui-native-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:h200:1
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=/work/%u/ncshare-crash-course/logs/%x-%j.out

set -euo pipefail

if [[ -n "${CUDA_MODULE:-}" ]]; then
  module load "$CUDA_MODULE"
fi

COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
QUANTUI_SRC="${QUANTUI_SRC:-$HOME/ncshare-software/src/QuantUI}"
CONDA_ROOT="${CONDA_ROOT:-$HOME/miniforge3}"

source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate ncshare-quantui-native

export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export QUANTUI_SOURCE_CHECKOUT_COMMIT="$(git -C "$QUANTUI_SRC" rev-parse --short HEAD)"

nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
quantui gpu check
python "$COURSE_ROOT/tutorials/04-gpu-quantui/run_quantui_gpu.py"
