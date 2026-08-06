# Tutorial: Run a containerized Python application on a GPU

**Guided time:** 45 minutes  
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

We use a tiny water RHF/STO-3G calculation. The chemistry is context; the goal
is to prove that scheduler request, host driver, container environment, and
QuantUI all agree about GPU use.

## The four layers involved

A GPU application crosses several boundaries:

```text
Slurm allocation → physical H200 and host driver → Apptainer --nv
                 → CUDA/Python packages in the SIF → QuantUI calculation
```

Slurm grants access to hardware. The NCShare host supplies the kernel-level
NVIDIA driver. Apptainer's `--nv` option exposes that driver and the allocated
device inside the container. CUDA-aware Python packages inside the SIF can then
use the device. A check at each layer makes failures easier to locate.

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

As in the CPU lab, these variables name the repository, mutable workspace, and
read-only image. The braces create separate `logs` and `quantui` directories.

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

All five commands execute inside the image:

- `python --version` confirms the interpreter version;
- `python -c "..."` runs a short Python statement without creating a script;
  it imports QuantUI and PySCF and prints where/version information;
- `cat` prints the recorded QuantUI source commit;
- `sed -n '1,80p'` prints the first 80 lines of the resolved conda package
  manifest; and
- `grep -E` searches the pip manifest for any of three GPU package names. The
  `|` characters inside the quoted regular expression mean “or”; they are not
  shell pipes in this command.

The manifests describe the packages actually resolved during the build. The
definition file describes what the builder requested. Retaining both helps
explain why an image built months later might differ.

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

`#SBATCH` lines are directives inside a batch file; they are not typed directly
at the shell. `--gres` means generic resource and requests one H200. If the job
does not receive a GPU, `--nv` cannot create one.

## 15-22 min — Verify interactively

Request one short GPU allocation:

```bash
srun -p interactive-gpu \
  --gres=gpu:h200:1 \
  --time=00:10:00 \
  --cpus-per-task=4 \
  --mem=16G \
  --pty bash -l
```

This is one command split across lines with backslashes. It requests the
`interactive-gpu` partition, one H200, ten minutes, four CPU cores, 16 GB of
host memory, and an interactive Bash shell. GPU jobs still need CPU cores and
RAM to prepare inputs, launch kernels, and handle results. The request may
remain pending until a suitable node is free.

Inside it:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/user/ncshare-science-course.sif}"
bash "$COURSE_ROOT/containers/verify_container.sh" \
  "$COURSE_IMAGE" gpu
exit
```

The verification script first runs the image's normal tests. In `gpu` mode it
also confirms that the command is inside a Slurm allocation, runs
`nvidia-smi` through `apptainer exec --nv`, and asks QuantUI to check its GPU
environment. `exit` releases the interactive allocation.

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

The Python program [`run_quantui_gpu.py`](run_quantui_gpu.py) creates a
water molecule, calls QuantUI's `run_in_session` API with the RHF method and
STO-3G basis, and writes a JSON result. JSON is a text format of named values;
it is useful here because people and programs can both inspect it. The script
exits with an error if the calculation did not converge or if QuantUI reports
that GPU offload was not used.

## 28-33 min — Submit

```bash
cd "$COURSE_ROOT/tutorials/04-gpu-quantui"
sbatch --export=ALL,COURSE_IMAGE="$COURSE_IMAGE" \
  slurm/quantui_gpu.sbatch
```

`sbatch` submits the file to Slurm and prints a job ID. `--export` passes the
current variables and explicitly supplies the image path. The shell script
will run later on the assigned GPU node; closing the terminal after submission
does not cancel the batch job.

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

Replace `JOB_ID` with the number returned by `sbatch`. The `squeue` format is
the same one decoded in the CPU tutorial: job ID, state, elapsed time, node
count, and assigned node or pending reason. `sacct` reports the final state,
resources, and exit code. `python -m json.tool FILE` parses and pretty-prints
the result, which also verifies that it is valid JSON.

Expected fields include:

```json
{
  "converged": true,
  "gpu_used": true,
  "method": "RHF",
  "basis": "STO-3G"
}
```

This molecule is too small for a meaningful speed benchmark. The defensible
claim is that the calculation used QuantUI's supported GPU-offload path—not
that it was faster than a CPU calculation.

The other fields need context too: `converged` means the iterative
self-consistent-field procedure reached its stopping criterion; `RHF` names
the electronic-structure method; and `STO-3G` names the intentionally small
basis set. They demonstrate a workflow, not a research-quality calculation.

## 40-45 min — Explain and improve the design

With a partner, answer:

1. Which line allocates a GPU, and which option exposes it in the SIF?
2. Why does `nvidia-smi` alone not prove application offload?
3. Why is the image built once on CPUs instead of being rebuilt inside a GPU
   job?
4. What evidence would you retain with a published result?
5. When must the definition/SIF be rebuilt rather than merely resubmitting?

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
