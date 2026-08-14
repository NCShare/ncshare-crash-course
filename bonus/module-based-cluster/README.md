# Bonus: Native software on a traditional module-based cluster

This optional path preserves the workflow commonly used on clusters with a
curated scientific module catalog. It is **not the primary NCShare path**.
NCShare's current guidance recommends Apptainer for scientific software, so the
main tutorials use the shared course image.

Use this bonus when teaching at a site that provides compatible compiler, MPI,
parallel HDF5, GSL, CUDA, and Python modules.

The revisions below are intentionally pinned examples for the native workflow;
they are not guaranteed to match the main course image, which installs QuantUI
`0.6.1` and selects the latest inoisy4d default branch at image-build time.
Therefore, this bonus supports a comparison of **environment-management
approaches**, not a controlled performance or numerical comparison between the
two paths. Align application versions first if the scientific results themselves
are to be compared.

## Why compare both approaches?

The scientific workflow is the same:

```text
source + dependencies -> executable/environment -> Slurm job -> results
```

The ownership boundary changes:

| Container-first NCShare path | Traditional module-based path |
|---|---|
| Definition file chooses the complete user-space stack | Site modules choose compiler and library stack |
| Image is built once and shared | Each user installs/builds in home space |
| Jobs call `apptainer exec` | Jobs call executables or activated environments directly |
| GPU runtime uses `apptainer exec --nv` | Site CUDA module/driver is used directly |
| SIF checksum identifies the environment | Module list plus environment lock/build log identifies it |

Modules can produce smaller, highly optimized site-specific environments and
may integrate more easily with multi-node interconnects. They also require the
needed versions to exist, and user builds can drift. Containers improve
portability and consistency, but images are larger and multi-node MPI still
requires coordination with administrators.

## CPU/MPI native build

1. Customize the module names in the scripts for the target site.
2. Clone the unmodified application:

   ```bash
   export INOISY_SRC="${INOISY_SRC:-$HOME/ncshare-software/src/inoisy4d}"
   git clone https://github.com/alejandroc137/inoisy4d.git "$INOISY_SRC"
   git -C "$INOISY_SRC" checkout --detach \
     437973e6aa35228a0df08deea1b652bb85ae467e
   ```

3. In a CPU allocation, build the nonstandard dependency and application:

   ```bash
   bash bonus/module-based-cluster/cpu/setup_hypre.sh
   bash bonus/module-based-cluster/cpu/build_inoisy.sh
   ```

4. Submit the one-rank and four-rank versions of the same fixed-size problem:

   ```bash
   sbatch bonus/module-based-cluster/cpu/inoisy_one_rank.sbatch
   sbatch bonus/module-based-cluster/cpu/inoisy_four_ranks.sbatch
   ```

## GPU/Python native environment

1. Load the site's Python/conda tooling and create the environment in a CPU
   allocation:

   ```bash
   export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
   export QUANTUI_SRC="${QUANTUI_SRC:-$HOME/ncshare-software/src/QuantUI}"
   git clone https://github.com/The-Schultz-Lab/QuantUI.git "$QUANTUI_SRC"
   git -C "$QUANTUI_SRC" checkout --detach \
     fcf0c08944d360f510ea274eaa0315e2d7e530b7
   bash bonus/module-based-cluster/gpu/install_quantui.sh
   ```

2. Set `CUDA_MODULE` only if the site requires a CUDA module:

   ```bash
   export CUDA_MODULE="cuda/12.8"
   sbatch bonus/module-based-cluster/gpu/quantui_gpu.sbatch
   ```

3. Record the module list, conda explicit specification, pip freeze, source
   commit, and job ID with the result.

## What students should learn from the comparison

- Modules and containers solve related but different environment problems.
- MPI performance and compatibility depend on the relationship among compiler,
  MPI, scheduler, and interconnect—not merely on whether an executable starts.
- A conda environment does not allocate a GPU, and a CUDA module does not prove
  an application used it.
- Reproducibility requires evidence: definition/checksum for a container, or
  module versions/build logs/environment locks for a native build.

## References

- [Environment Modules documentation](https://modules.readthedocs.io/)
- [Apptainer MPI models](https://apptainer.org/docs/user/latest/mpi.html)
- [NCShare Cluster Software guidance](https://userguide.ncshare.org/guides/slurm/software/)
