# Tutorial: Run a containerized Python application on a GPU

**Guided time:** 60 minutes (45 min GPU hands-on plus the CPU/GPU comparison)  
**Application:** [The-Schultz-Lab/QuantUI](https://github.com/The-Schultz-Lab/QuantUI)  
**Concepts:** Python environment design, container provenance, CUDA user-space
libraries, GPU allocation, `--nv`, application-level offload evidence, and
responsible GPU use

## What is different from the CPU/MPI tutorial?

The inoisy+ lab used compiled C/MPI software from the course image. This lab
uses the **same SIF**, but follows its Python/GPU path:

```text
Python 3.11 + QuantUI + PySCF/gpu4pyscf + CUDA 12.x wheels
```

The Python environment is created in the definition file when the image is
built. Students inspect that environment rather than creating slightly
different conda environments in every home directory. At runtime, Slurm grants
one H200 and Apptainer's `--nv` flag exposes the host NVIDIA driver/devices to
the image.

## The hardware you are actually using

NCShare's GPU tier is four nodes, each with **eight NVIDIA H200 SXM (141 GB
HBM3e)** and roughly 96 physical CPU cores plus 2 TB of RAM — 32 H200s in
total. That works out to about 12 CPU cores per GPU, which is why the batch
job below asks for four.

Two consequences worth noting before you start:

- The H200 is compute capability **9.0** (Hopper). Both `gpu4pyscf-cuda12x`
  and `cupy-cuda12x` ship prebuilt wheels for it, so nothing has to be
  compiled against a local CUDA toolkit at image-build time.
- The image carries its own complete CUDA 12.8 user-space. Only the driver
  libraries come from the host through `--nv`, and the CUDA driver API is
  backward compatible — which is why a `cuda12x` build keeps working when
  the cluster's driver is upgraded.

We use a tiny water RHF/STO-3G calculation. The chemistry is context; the goal
is to prove that scheduler request, host driver, container environment, and
QuantUI all agree about GPU use.

## Before the clock starts

- Complete [pre-workshop setup](../00-prework.md).
- Obtain GPU access through your institutional representative.
- Complete the [Apptainer blueprint tutorial](../../containers/README.md).
- The HPC team has tested the SIF on an NCShare H200.

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"
mkdir -p "$COURSE_WORK"/{logs,quantui}
```

## 0-8 min — Inspect the Python environment

```bash
apptainer exec "$COURSE_IMAGE" python --version
apptainer exec "$COURSE_IMAGE" python -c \
  "import quantui, pyscf; print('QuantUI:', quantui.__file__); print('PySCF:', pyscf.__version__)"
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/quantui-commit.txt
apptainer exec "$COURSE_IMAGE" \
  sed -n '1,80p' /opt/course-build/conda-explicit.txt
apptainer exec "$COURSE_IMAGE" \
  grep -E 'gpu4pyscf|cupy|cutensor' /opt/course-build/pip-freeze.txt
```

Then locate the environment-creation block in
[`ncshare-science-course.def`](../../containers/ncshare-science-course.def).
Discuss why it:

- fixes Python at 3.11;
- separates conda-resolved scientific packages from CUDA-specific pip wheels;
- installs CUDA-suffixed wheels instead of accidentally building bare CuPy or
  gpu4pyscf source packages; and
- records both the requested recipe and resolved package manifests.

## 8-15 min — Separate allocation from exposure

Two different mechanisms are required:

```bash
# Slurm: reserve one physical H200
#SBATCH --gres=gpu:h200:1

# Apptainer: expose the host NVIDIA driver/devices to the image
apptainer exec --nv IMAGE.sif COMMAND
```

Neither mechanism proves that QuantUI used the GPU. `nvidia-smi` proves a
device is visible; `quantui gpu check` proves the environment supports offload;
the calculation result's `gpu_used` field proves this supported calculation
actually followed QuantUI's offload path.

## 15-22 min — Verify interactively

Request one short GPU allocation:

```bash
srun -p workshop \
  --gres=gpu:h200:1 \
  --time=00:10:00 \
  --cpus-per-task=4 \
  --mem=16G \
  --pty bash -l
```

Inside it:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"
bash "$COURSE_ROOT/containers/verify_container.sh" \
  "$COURSE_IMAGE" gpu
exit
```

The CPU verification path does not use `--nv`; the GPU path does. This lets one
image serve both workflows without reserving a GPU for CPU-only work.

## 22-28 min — Read the batch job

Open [`quantui_gpu.sbatch`](slurm/quantui_gpu.sbatch). Connect each layer to
its responsibility:

| Layer | Evidence in the job |
|---|---|
| Scheduler | GPU partition, `--gres`, CPUs, memory, wall time |
| Container | SIF path, `--nv`, bind mounts, clean runtime environment |
| Application | `quantui gpu check`, water calculation, `gpu_used` assertion |
| Reproducibility | image labels, QuantUI commit, JSON result, Slurm log |

The job requests one GPU because this example uses one. More GPUs would not
make this script multi-GPU.

## 28-33 min — Submit

```bash
cd "$COURSE_ROOT/tutorials/04-gpu-quantui"
sbatch --export=ALL,COURSE_IMAGE="$COURSE_IMAGE" \
  slurm/quantui_gpu.sbatch
```

Record the job ID.

## 33-40 min — Monitor and verify

```bash
squeue -j JOB_ID -o "%.18i %.9T %.10M %.6D %.30R"
sacct -j JOB_ID --format=JobID,State,Elapsed,AllocCPUS,ReqMem,ExitCode
less "$COURSE_WORK/logs/quantui-gpu-JOB_ID.out"

apptainer exec \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  python -m json.tool \
  "$COURSE_WORK/quantui/quantui_gpu_result.json"
```

Expected fields include:

```json
{
  "converged": true,
  "gpu_used": true,
  "method": "RHF",
  "basis": "STO-3G"
}
```

This tells you the calculation followed QuantUI's supported GPU-offload
path. It does **not** tell you the GPU was faster—water/STO-3G is far too
small for that. The next section measures that question directly.

## 40-52 min — Find the crossover

A GPU is not simply "faster". Every offloaded calculation pays a fixed cost:
launching kernels and moving data between host and device. For a small
system that overhead dominates the actual arithmetic, so **the CPU wins**. As
the basis set grows, integral and Fock construction grow faster than the
overhead, and at some point **the GPU wins**. Where that crossover sits
depends on the molecule, basis, method, and the specific hardware.

Measure it rather than assuming it:

```bash
cd "$COURSE_ROOT/tutorials/04-gpu-quantui"

for p in small medium crossover large; do
  apptainer exec --nv --cleanenv \
    --bind "$COURSE_WORK:$COURSE_WORK" \
    --env "COURSE_WORK=$COURSE_WORK" \
    --env "OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK" \
    "$COURSE_IMAGE" \
    python run_cpu_gpu_comparison.py --preset "$p"
done
```

### What this looked like on NCShare

Measured 2026-08-05 on `compute-gpu-02` (H200, driver 580.126.20), **1 GPU
against 6 affinity-confirmed CPU cores**:

| System | GPU | CPU | Ratio |
|---|---:|---:|---|
| H2O / STO-3G | 1.80 s | 0.35 s | 0.20x |
| H2O / cc-pVDZ | 2.72 s | 0.48 s | 0.18x |
| C6H6 / 6-31G | 2.69 s | 0.77 s | 0.29x |
| C6H6 / cc-pVDZ | 2.86 s | 2.74 s | **0.96x — the crossover** |
| C6H6 / cc-pVTZ | 7.07 s | 42.41 s | **6.00x** |

Look at the GPU column first. It barely moves — 1.80 s to 2.86 s — while the
system grows by orders of magnitude in basis functions. That flat portion *is*
the fixed overhead, visible rather than asserted. The CPU column meanwhile
climbs steadily, and at cc-pVTZ it explodes to 42 s while the GPU reaches only
7 s.

> **Warning:** A speedup means nothing without the CPU allocation it was
> measured against. These numbers are 1 GPU vs 6 cores. The node has ~12
> physical cores per GPU, so a proportional-share comparison would show a
> smaller factor and move the crossover to a larger basis. Always quote the
> denominator.

The script runs each leg in a separate process. That is a requirement, not a
style choice: QuantUI caches its GPU probe on first use, so the CPU leg has
to set `QUANTUI_DISABLE_GPU=1` *before* QuantUI or gpu4pyscf is imported.
Forcing CPU inside a running interpreter would be silently ignored, and the
"CPU" timing would really be a second GPU run.

Both legs print a wall time and the total energy. Check that the energies
agree to ~1e-6 Hartree: if the two devices disagree on the answer, the
timing comparison is meaningless.

Record your own numbers, which will differ — different allocation, different
node load:

| System | CPU (s) | GPU (s) | Ratio |
|---|---:|---:|---|
| H2O RHF/STO-3G | | | |
| C6H6 RHF/6-31G | | | |
| C6H6 RHF/cc-pVDZ | | | |
| C6H6 RHF/cc-pVTZ | | | |

Then discuss: at what point would it be worth requesting a GPU for your own
work, and what would you have to measure to know?

### A trap worth knowing about

The script prints your CPU **affinity mask** alongside the core count, and
warns if they disagree. That is not decoration. When these numbers were
measured, `os.cpu_count()` reported **192** — every core on the node — while
Slurm had granted **6**.

That was safe only because Slurm used a *cpuset*, so the affinity mask also
showed 6 and threading libraries saw the real allocation. Under a cgroup CPU
*quota* instead, the mask would have reported 192, OpenMP would have spawned
192 threads onto 6 cores' worth of time, and every CPU timing would have been
inflated — making the GPU look better than it is.

Same request, same `cpu_count()`, opposite consequences. Whenever you
benchmark on a shared cluster, confirm what you were actually given rather
than what the machine says it has.

## 52-60 min — Explain and improve the design

With a partner, answer:

1. Which line allocates a GPU, and which option exposes it in the SIF?
2. Why does `nvidia-smi` alone not prove application offload?
3. Why is the image built once on CPUs instead of being rebuilt inside a GPU
   job?
4. What evidence would you retain with a published result?
5. When must the definition/SIF be rebuilt rather than merely resubmitting?
6. Your small system ran faster on the CPU. What would you tell a colleague
   who says "we bought GPUs, so run everything on them"?

For longer jobs on a preemptible GPU partition, checkpoint application state.
Do not run CPU-only installation, visualization, or data preparation on a GPU.

## Optional: use the image in Open OnDemand

NCShare's JupyterLab Apptainer launcher accepts a custom SIF. Select the course
image, request one H200 only when GPU computation is needed, launch JupyterLab,
and open QuantUI's notebook:

```text
/opt/QuantUI/notebooks/molecule_computations.ipynb
```

For the scientific-visualization session, select the same image on a CPU
partition and open the course notebook from the bound course repository.

## Diagnose before rebuilding

| Symptom | Check | Likely action |
|---|---|---|
| image not found | published path | correct `COURSE_IMAGE` |
| no GPU visible | Slurm partition/`--gres` and `--nv` | fix allocation/exposure |
| `gpu4pyscf` import fails | recorded pip manifest and image checksum | use verified SIF |
| `gpu_used` is false | `quantui gpu check` and method support | fix environment/method |
| job pending | `squeue ... %R` | read scheduler reason |
| CPU-only work on GPU | command and utilization | move it to a CPU allocation |

## Bonus

See [the module-based cluster workflow](../../bonus/module-based-cluster/README.md)
for a per-user conda environment and direct host GPU runtime.

## Sources

- [QuantUI repository and GPU guidance](https://github.com/The-Schultz-Lab/QuantUI)
- [NCShare GPU guide](https://userguide.ncshare.org/guides/gpu/)
- [NCShare Cluster Software guide](https://userguide.ncshare.org/guides/slurm/software/)
- [Apptainer GPU support](https://apptainer.org/docs/user/latest/gpu.html)
