# Tutorial: A Python environment and GPU job with QuantUI

**Guided time:** 45 minutes  
**Application:** [The-Schultz-Lab/QuantUI](https://github.com/The-Schultz-Lab/QuantUI)  
**Concepts:** conda environments, Python packaging, CUDA-specific wheels, GPU
resource requests, GPU verification, Slurm logs, and responsible GPU use

## What is different from the CPU tutorial?

The inoisy+ lab built a C/MPI application and a user-installed compiled
library. This lab uses a Python/conda software stack and requests one NVIDIA
H200 GPU. QuantUI places PySCF quantum-chemistry calculations behind a Jupyter
interface and can offload supported self-consistent-field calculations through
`gpu4pyscf`.

We use a tiny water calculation. The chemistry is only context; the learning
goal is to prove that the environment, CUDA runtime, scheduler request, and
application all agree about the GPU.

## Before the clock starts

- Complete [pre-workshop setup](../00-prework.md), including Miniforge.
- Obtain GPU access through your institutional representative.
- The instructor has verified current NCShare CUDA compatibility and package
  availability.
- Create `/work/$USER/ncshare-crash-course/logs` before submission.

## 0-5 min — Clone and inspect

On the login node:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export QUANTUI_SRC="${QUANTUI_SRC:-$HOME/ncshare-software/src/QuantUI}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"

mkdir -p "$HOME/ncshare-software/src" "$COURSE_WORK"/{logs,quantui}
git clone https://github.com/The-Schultz-Lab/QuantUI.git "$QUANTUI_SRC"
git -C "$QUANTUI_SRC" rev-parse --short HEAD
less "$QUANTUI_SRC/README.md"
less "$QUANTUI_SRC/pyproject.toml"
```

If the clone exists, use `git -C "$QUANTUI_SRC" pull --ff-only` rather than
cloning over it.

Find the GPU extras in `pyproject.toml`. QuantUI warns against installing bare
`gpu4pyscf` or `cupy` source packages; CUDA-suffixed wheels avoid an unnecessary
local CUDA-toolkit build.

## 5-20 min — Create the environment on CPUs

Do not occupy a GPU while downloading packages. Request a short CPU allocation:

```bash
srun -p workshop --time=00:25:00 --cpus-per-task=4 --mem=12G --pty bash -l
```

Inside the allocation:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export QUANTUI_SRC="${QUANTUI_SRC:-$HOME/ncshare-software/src/QuantUI}"
export CONDA_ROOT="${CONDA_ROOT:-$HOME/miniforge3}"

source "$CONDA_ROOT/etc/profile.d/conda.sh"
bash "$COURSE_ROOT/tutorials/04-gpu-quantui/scripts/install_quantui.sh"
conda activate ncshare-quantui

python --version
python -c "import quantui, pyscf; print('QuantUI:', quantui.__file__); print('PySCF:', pyscf.__version__)"
exit
```

The environment lives in `$HOME`, not `/work`, so it is not subject to the
75-day work-space purge. The installer:

1. creates/updates a Python 3.11 conda environment;
2. installs the cloned QuantUI package with its PySCF, ASE, and app extras; and
3. installs the CUDA 12.x `gpu4pyscf`, CuPy, and cuTENSOR wheels appropriate to
   the NCShare H200 driver documented for this course.

## 20-27 min — Read the GPU request

Open [`quantui_gpu.sbatch`](slurm/quantui_gpu.sbatch).

The essential requests are:

```bash
#SBATCH --partition=interactive-gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:10:00
```

Connect each line to a need in the application. We request one GPU because the
example uses only one. More GPUs would not make this script multi-GPU.

The job runs three checks:

1. `nvidia-smi` verifies the scheduled node exposes an H200;
2. `quantui gpu check` verifies the Python environment can see GPU offload; and
3. `run_quantui_gpu.py` verifies the actual QuantUI result reports
   `gpu_used: true`.

## 27-32 min — Submit

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
mkdir -p "$COURSE_WORK/logs"

cd "$COURSE_ROOT/tutorials/04-gpu-quantui"
sbatch slurm/quantui_gpu.sbatch
```

Record the job ID.

## 32-40 min — Monitor and verify

```bash
squeue -u "$USER"
squeue -j JOB_ID -o "%.18i %.9T %.10M %.6D %.30R"
```

After completion:

```bash
sacct -j JOB_ID --format=JobID,State,Elapsed,AllocCPUS,ReqMem,ExitCode
less "$COURSE_WORK/logs/quantui-gpu-JOB_ID.out"
python -m json.tool "$COURSE_WORK/quantui/quantui_gpu_result.json"
```

Expected result fields include:

```json
{
  "converged": true,
  "gpu_used": true,
  "method": "RHF",
  "basis": "STO-3G"
}
```

The elapsed time is not a meaningful GPU speed benchmark: this molecule is
intentionally small, so setup and transfer overhead dominate. The defensible
claim is only that the supported calculation ran through QuantUI's GPU-offload
path.

## 40-45 min — Explain the resource choice

With a partner, answer:

1. Which line in the Slurm file actually allocates a GPU?
2. Why does `torch.cuda.is_available()` or `nvidia-smi` alone not prove that
   QuantUI used the GPU?
3. Why should environment installation happen on a CPU node?
4. What would you change for a longer preemptible `gpu` job?

For longer work on NCShare's general `gpu` partition, checkpoint intermediate
state because jobs may be preempted. Do not place CPU-only work in a GPU
partition.

## Optional: open the QuantUI interface

In an Open OnDemand JupyterLab session configured for one GPU:

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate ncshare-quantui
cd "$QUANTUI_SRC"
jupyter lab notebooks/molecule_computations.ipynb
```

In the notebook, the Status view should identify GPU offload as active. Use
small molecules and `STO-3G` during the workshop.

## Diagnose before reinstalling

| Symptom | Check | Likely action |
|---|---|---|
| `conda` not found | `$CONDA_ROOT`, pre-work | source the correct `conda.sh` |
| package download fails | log, instructor mirror | use the staged cache; do not loop downloads |
| job pending with `QOS...` or access reason | `squeue ... %R` | contact the instructor/admin |
| `nvidia-smi` has no device | Slurm partition and `--gres` | do not run outside a GPU allocation |
| CuPy import error | installed CUDA suffix | use the verified CUDA 12.x wheels |
| `gpu_used` is false | `quantui gpu check`, `QUANTUI_DISABLE_GPU` | fix the environment; do not claim acceleration |
| preempted job | `sacct` state/log | resubmit this short lab; checkpoint real workloads |

## Sources

- [QuantUI README and GPU installation guidance](https://github.com/The-Schultz-Lab/QuantUI)
- [NCShare GPU Guide](https://userguide.ncshare.org/guides/gpu/)
- [NCShare Cluster Software guide](https://userguide.ncshare.org/guides/slurm/software/)
