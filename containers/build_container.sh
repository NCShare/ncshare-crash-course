#!/usr/bin/env bash
set -euo pipefail

COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
DEF_FILE="${DEF_FILE:-$COURSE_ROOT/containers/ncshare-science-course.def}"
IMAGE_DIR="${IMAGE_DIR:-/work/$USER/ncshare-crash-course/images}"
COURSE_IMAGE="${COURSE_IMAGE:-$IMAGE_DIR/ncshare-science-course.sif}"
APPTAINER_CACHEDIR="${APPTAINER_CACHEDIR:-/work/$USER/ncshare-apptainer-cache}"
APPTAINER_TMPDIR="${APPTAINER_TMPDIR:-/work/$USER/ncshare-apptainer-tmp}"

export APPTAINER_CACHEDIR APPTAINER_TMPDIR

if [[ -z "${SLURM_JOB_ID:-}" && -z "${CI:-}" ]]; then
  echo "Run this build in a Slurm allocation or the approved NCShare CI runner." >&2
  echo "For example: srun -p workshop --time=01:00:00 --cpus-per-task=8 --mem=24G --pty bash -l" >&2
  exit 2
fi

if ! command -v apptainer >/dev/null 2>&1; then
  echo "Apptainer is not available on PATH." >&2
  exit 3
fi

if [[ ! -f "$DEF_FILE" ]]; then
  echo "Definition file not found: $DEF_FILE" >&2
  exit 4
fi

mkdir -p "$IMAGE_DIR" "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"

echo "Building $COURSE_IMAGE"
echo "Definition: $DEF_FILE"
echo "Cache: $APPTAINER_CACHEDIR"
echo "Temporary build data: $APPTAINER_TMPDIR"

apptainer build "$COURSE_IMAGE" "$DEF_FILE"
apptainer test "$COURSE_IMAGE"
sha256sum "$COURSE_IMAGE" > "$COURSE_IMAGE.sha256"

echo "Built and tested: $COURSE_IMAGE"
echo "Checksum: $COURSE_IMAGE.sha256"
