#!/usr/bin/env bash
#SBATCH --job-name=inoisy-post
#SBATCH --partition=workshop
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/work/%u/ncshare-crash-course/logs/%x-%j.out

set -e

COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"

# The four-rank exercise creates one small HDF5 file. If the exercise was run
# more than once, use the newest file.
SOURCE_H5=$(ls -t "$COURSE_WORK"/inoisy/four-ranks/*.h5 | head -n 1)

OUTDIR="$COURSE_WORK/inoisy/postprocessed"
mkdir -p "$OUTDIR"

apptainer exec --cleanenv \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  python /opt/inoisy4d/tools/inoisy4d_to_visit_emissivity.py \
  "$SOURCE_H5" \
  --output-prefix "$OUTDIR/inoisy_lowres_emissivity" \
  --force

echo "Input: $SOURCE_H5"
echo "Image: $COURSE_IMAGE"
echo "Output: $OUTDIR/inoisy_lowres_emissivity.h5"
echo "XDMF: $OUTDIR/inoisy_lowres_emissivity.xmf"
