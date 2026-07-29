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

module purge
module load compilers/gcc/12.3.0
module load libs/gsl/2.7.1
module load mpi/openmpi/4.1.6
module load libs/hdf5/1.14.6

INOISY_SRC="${INOISY_SRC:-$HOME/ncshare-software/src/inoisy4d}"
HYPRE_PREFIX="${HYPRE_PREFIX:-$HOME/ncshare-software/hypre-3.1.0-maxdim4}"
COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
OUTDIR="$COURSE_WORK/inoisy/one-rank"

export LD_LIBRARY_PATH="$HYPRE_PREFIX/lib:${LD_LIBRARY_PATH:-}"
mkdir -p "$OUTDIR"
cd "$INOISY_SRC"

echo "job_id=$SLURM_JOB_ID host=$(hostname) ranks=$SLURM_NTASKS"
echo "inoisy_commit=$(git rev-parse --short HEAD)"

srun --ntasks=1 ./inoisy4d \
  -nl 16 -nj 16 -ni 16 -nk 16 \
  -pgrid 1 1 1 1 \
  -solver 0 \
  -nrecur 1 \
  -timer \
  -output "$OUTDIR"
