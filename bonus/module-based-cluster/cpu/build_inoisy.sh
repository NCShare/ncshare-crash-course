#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
  echo "Compile inside a Slurm allocation, not on the login node." >&2
  exit 2
fi

INOISY_SRC="${INOISY_SRC:-$HOME/ncshare-software/src/inoisy4d}"
HYPRE_PREFIX="${HYPRE_PREFIX:-$HOME/ncshare-software/hypre-3.1.0-maxdim4}"
BUILD_CPUS="${SLURM_CPUS_PER_TASK:-4}"

module purge
module load compilers/gcc/12.3.0
module load libs/gsl/2.7.1
module load mpi/openmpi/4.1.6
module load libs/hdf5/1.14.6

if [[ ! -f "$HYPRE_PREFIX/lib/libHYPRE.so" && ! -f "$HYPRE_PREFIX/lib/libHYPRE.a" ]]; then
  echo "No HYPRE library found under $HYPRE_PREFIX." >&2
  exit 3
fi

cd "$INOISY_SRC"
make -j "$BUILD_CPUS" HYPRE_DIR="$HYPRE_PREFIX" CC=h5pcc

module list 2>&1 | tee "$INOISY_SRC/native-build-modules.txt"
echo "Built $INOISY_SRC/inoisy4d"
echo "inoisy4d commit: $(git rev-parse --short HEAD)"
