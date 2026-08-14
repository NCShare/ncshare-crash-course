#!/usr/bin/env bash
#SBATCH --job-name=inoisy-post
#SBATCH --partition=workshop
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/work/%u/ncshare-crash-course/logs/%x-%j.out

set -euo pipefail

COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"

if [[ ! -f "$COURSE_IMAGE" ]]; then
  echo "Course image not found: $COURSE_IMAGE" >&2
  exit 2
fi

if [[ -z "${SOURCE_H5:-}" ]]; then
  SOURCE_DIR="$COURSE_WORK/inoisy/four-ranks"
  SOURCE_H5=""
  if [[ -d "$SOURCE_DIR" ]]; then
    while IFS= read -r -d '' candidate; do
      if [[ -z "$SOURCE_H5" || "$candidate" -nt "$SOURCE_H5" ]]; then
        SOURCE_H5="$candidate"
      fi
    done < <(find "$SOURCE_DIR" -maxdepth 1 -type f -name '*.h5' -print0)
  fi
fi

if [[ -z "$SOURCE_H5" || ! -f "$SOURCE_H5" ]]; then
  echo "No inoisy+ HDF5 input found; set SOURCE_H5 and resubmit." >&2
  exit 3
fi

OUTDIR="$COURSE_WORK/inoisy/postprocessed"
mkdir -p "$OUTDIR"

apptainer exec --cleanenv \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  python /opt/inoisy4d/tools/inoisy4d_to_visit_emissivity.py \
  "$SOURCE_H5" \
  --output-prefix "$OUTDIR/inoisy_lowres_emissivity" \
  --write-components \
  --write-envelopes \
  --compress \
  --float32 \
  --force

echo "Input: $SOURCE_H5"
echo "Image: $COURSE_IMAGE"
echo "Output: $OUTDIR/inoisy_lowres_emissivity.h5"
echo "XDMF: $OUTDIR/inoisy_lowres_emissivity.xmf"
