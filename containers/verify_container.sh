#!/usr/bin/env bash
set -euo pipefail

COURSE_IMAGE="${1:-${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}}"
MODE="${2:-cpu}"

# Open MPI inside the image is not built against this cluster's Slurm PMI. An
# MPI binary exec'd directly (no mpirun) inherits the host SLURM_* variables,
# concludes it was direct launched by srun, and aborts in MPI_Init. Dropping the
# whole SLURM_* block restores the singleton path; unsetting only part of it
# trips a different Open MPI failure branch. Everything else, including
# CUDA_VISIBLE_DEVICES from the GPU allocation, is preserved.
without_slurm_env() {
  env $(env | sed -n 's/^\(SLURM[A-Z_]*\)=.*/-u \1/p') "$@"
}

if [[ ! -f "$COURSE_IMAGE" ]]; then
  echo "Container image not found: $COURSE_IMAGE" >&2
  exit 2
fi

echo "Image: $COURSE_IMAGE"
apptainer inspect "$COURSE_IMAGE"
apptainer test "$COURSE_IMAGE"
apptainer run "$COURSE_IMAGE"
apptainer exec "$COURSE_IMAGE" python -c \
  "import quantui, pyscf, h5py, matplotlib; print('Python imports: OK')"
without_slurm_env apptainer exec "$COURSE_IMAGE" inoisy4d --help >/dev/null
apptainer exec "$COURSE_IMAGE" h5pcc.openmpi -showconfig \
  | grep -i "Parallel HDF5"

if [[ "$MODE" == "gpu" ]]; then
  if [[ -z "${SLURM_JOB_ID:-}" ]]; then
    echo "GPU verification must run inside a GPU allocation." >&2
    exit 3
  fi
  apptainer exec --nv "$COURSE_IMAGE" nvidia-smi \
    --query-gpu=name,driver_version,memory.total --format=csv,noheader
  apptainer exec --nv "$COURSE_IMAGE" quantui gpu check
fi

echo "Verification complete ($MODE mode)."
