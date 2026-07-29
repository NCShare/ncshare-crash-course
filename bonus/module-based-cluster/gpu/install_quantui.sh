#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
  echo "Create the environment inside a CPU Slurm allocation." >&2
  exit 2
fi

COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
QUANTUI_SRC="${QUANTUI_SRC:-$HOME/ncshare-software/src/QuantUI}"
CONDA_ROOT="${CONDA_ROOT:-$HOME/miniforge3}"
ENV_FILE="$COURSE_ROOT/bonus/module-based-cluster/gpu/environment.yml"
ENV_NAME="ncshare-quantui-native"

source "$CONDA_ROOT/etc/profile.d/conda.sh"

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda env update --name "$ENV_NAME" --file "$ENV_FILE" --prune
else
  conda env create --file "$ENV_FILE"
fi

conda activate "$ENV_NAME"
cd "$QUANTUI_SRC"

python -m pip install --upgrade pip
python -m pip install -e ".[pyscf,ase,app]"
python -m pip install gpu4pyscf-cuda12x cupy-cuda12x cutensor-cu12
conda list --explicit > native-conda-explicit.txt
python -m pip freeze > native-pip-freeze.txt

echo "Installed QuantUI commit $(git rev-parse --short HEAD) in $ENV_NAME"
