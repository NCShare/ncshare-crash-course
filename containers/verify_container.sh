#!/usr/bin/env bash
set -euo pipefail

COURSE_IMAGE="${1:-${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}}"
MODE="${2:-cpu}"

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
apptainer exec "$COURSE_IMAGE" inoisy4d --help >/dev/null
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
