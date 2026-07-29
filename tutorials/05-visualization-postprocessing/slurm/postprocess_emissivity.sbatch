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

COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
INOISY_SRC="${INOISY_SRC:-$HOME/ncshare-software/src/inoisy4d}"
CONDA_ROOT="${CONDA_ROOT:-$HOME/miniforge3}"

source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate ncshare-viz

if [[ -z "${SOURCE_H5:-}" ]]; then
  SOURCE_H5="$(find "$COURSE_WORK/inoisy/four-ranks" \
    -maxdepth 1 -type f -name '*.h5' -print | sort | tail -n 1)"
fi

if [[ -z "$SOURCE_H5" || ! -f "$SOURCE_H5" ]]; then
  echo "No inoisy+ HDF5 input found; set SOURCE_H5 and resubmit." >&2
  exit 2
fi

POSTPROCESS="$INOISY_SRC/tools/inoisy4d_to_visit_emissivity.py"
if [[ ! -f "$POSTPROCESS" ]]; then
  echo "Cannot find the upstream converter at $POSTPROCESS" >&2
  exit 3
fi

OUTDIR="$COURSE_WORK/inoisy/postprocessed"
mkdir -p "$OUTDIR"

python "$POSTPROCESS" "$SOURCE_H5" \
  --output-prefix "$OUTDIR/inoisy_lowres_emissivity" \
  --write-components \
  --write-envelopes \
  --compress \
  --float32 \
  --force

echo "Input: $SOURCE_H5"
echo "Output: $OUTDIR/inoisy_lowres_emissivity.h5"
echo "XDMF: $OUTDIR/inoisy_lowres_emissivity.xmf"
