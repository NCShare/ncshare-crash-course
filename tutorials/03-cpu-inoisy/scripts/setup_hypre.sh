#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
  echo "Run this build inside a Slurm allocation, not on the login node." >&2
  exit 2
fi

HYPRE_VERSION="${HYPRE_VERSION:-v3.1.0}"
HYPRE_PREFIX="${HYPRE_PREFIX:-$HOME/ncshare-software/hypre-3.1.0-maxdim4}"
HYPRE_SOURCE="${HYPRE_SOURCE:-$HOME/ncshare-software/src/hypre-${HYPRE_VERSION}}"
BUILD_CPUS="${SLURM_CPUS_PER_TASK:-4}"

module purge
module load compilers/gcc/12.3.0
module load mpi/openmpi/4.1.6

if [[ -f "$HYPRE_PREFIX/lib/libHYPRE.so" || -f "$HYPRE_PREFIX/lib/libHYPRE.a" ]]; then
  echo "HYPRE is already installed at $HYPRE_PREFIX"
  exit 0
fi

mkdir -p "$(dirname "$HYPRE_SOURCE")" "$HYPRE_PREFIX"

if [[ ! -d "$HYPRE_SOURCE/.git" ]]; then
  git clone --depth 1 --branch "$HYPRE_VERSION" \
    https://github.com/hypre-space/hypre.git "$HYPRE_SOURCE"
fi

cd "$HYPRE_SOURCE/src"

./configure \
  --prefix="$HYPRE_PREFIX" \
  --enable-bigint \
  --enable-maxdim=4 \
  CC=mpicc \
  CXX=mpicxx

make -j "$BUILD_CPUS"
make install

echo "Installed HYPRE $HYPRE_VERSION at $HYPRE_PREFIX"
echo "Source commit: $(git -C "$HYPRE_SOURCE" rev-parse --short HEAD)"
