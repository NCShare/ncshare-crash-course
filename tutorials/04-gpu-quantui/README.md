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
HBM3e)**, roughly 96 physical CPU cores (192 hardware threads), and 2 TB of
RAM — 32 H200s in total. The temporary `workshop` reservation used by this
course was reported as one of those eight-GPU nodes. That works out to about
12 physical CPU cores per GPU, which is why the verification job below asks
for four.

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

## Where each step runs: login node vs compute node

After `ssh`, you land on a **login node**. It is for navigation, editing, and
submitting jobs, not for computation. Anything that runs the container's Python
(importing QuantUI, `quantui gpu check`, a calculation, or a Jupyter kernel)
must run on a **compute node**, reached through an interactive `srun` shell, a
batch `sbatch` job, or an Open OnDemand session. The container's scientific
stack is built for compute-node CPUs and will not import on the login node.

Every step below is tagged **(login node)** or **(compute node)** so it is clear
where to run it. When in doubt: reading, editing, and submitting happen on the
login node; anything that imports the scientific stack happens on a compute node.

## Before the clock starts

- Complete [pre-workshop setup](../00-prework.md).
- Obtain GPU access through your institutional representative.
- Complete the [Apptainer blueprint tutorial](../../containers/README.md).
- The HPC team has tested the SIF on an NCShare H200.

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
mkdir -p "$COURSE_WORK"/{logs,quantui}
```

As in the CPU lab, these variables name the repository, mutable workspace, and
read-only image. The braces create separate `logs` and `quantui` directories.

## 0-8 min — Inspect the Python environment (compute node)

The container's Python only runs on a compute node, so grab a short CPU shell
first. Reading the environment needs no GPU, so this deliberately does **not**
request one:

```bash
srun -p workshop --cpus-per-task=2 --mem=4G --time=00:15:00 --pty bash -l
```

With the prompt now on a compute node, set the image path and inspect it:

```bash
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
apptainer exec "$COURSE_IMAGE" python --version
apptainer exec "$COURSE_IMAGE" python -c \
  "import quantui, pyscf; print('QuantUI:', quantui.__file__); print('PySCF:', pyscf.__version__)"
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/quantui-version.txt
apptainer exec "$COURSE_IMAGE" \
  cat /opt/course-build/quantui-commit.txt
apptainer exec "$COURSE_IMAGE" \
  sed -n '1,80p' /opt/course-build/conda-explicit.txt
apptainer exec "$COURSE_IMAGE" \
  grep -E 'gpu4pyscf|cupy|cutensor' /opt/course-build/pip-freeze.txt
```

All six commands execute inside the image:

- `python --version` confirms the interpreter version;
- `python -c "..."` runs a short Python statement without creating a script;
  it imports QuantUI and PySCF and prints where/version information;
- the first `cat` prints the installed QuantUI package version;
- the second `cat` prints the matching source-checkout commit retained for
  examples and inspection—the checkout is not the installed package;
- `sed -n '1,80p'` prints the first 80 lines of the resolved conda package
  manifest; and
- `grep -E` searches the pip manifest for any of three GPU package names. The
  `|` characters inside the quoted regular expression mean “or”; they are not
  shell pipes in this command.

The manifests describe the packages actually resolved during the build. The
definition file describes what the builder requested. Retaining both helps
explain why an image built months later might differ.

Release the CPU shell now with `exit`; the rest of this step reads repository
files and needs no allocation.

Then locate the environment-creation block in
[`ncshare-science-course.def`](../../containers/ncshare-science-course.def).
Discuss why it:

- fixes Python at 3.11;
- separates conda-resolved scientific packages from CUDA-specific pip wheels;
- installs CUDA-suffixed wheels instead of accidentally building bare CuPy or
  gpu4pyscf source packages; and
- records both the requested recipe and resolved package manifests.

## 8-15 min — Separate allocation from exposure (login node)

Two different mechanisms are required. The block below is a schematic of both —
read it, do not run it. `IMAGE.sif` and `COMMAND` are placeholders, and neither
line is something you type at the shell:

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
at the shell. You do not run the `apptainer exec --nv` line by hand either — the
verification script in the next section and the batch job both issue it for you
with the real image path. `--gres` means generic resource and requests one H200.
If the job does not receive a GPU, `--nv` cannot create one.

## 15-22 min — Verify interactively (compute node)

Request one short GPU allocation:

```bash
srun -p workshop \
  --gres=gpu:h200:1 \
  --time=00:10:00 \
  --cpus-per-task=4 \
  --mem=16G \
  --pty bash -l
```

This is one command split across lines with backslashes. It requests the
`workshop` partition, one H200, ten minutes, four CPU cores, 16 GB of
host memory, and an interactive Bash shell. GPU jobs still need CPU cores and
RAM to prepare inputs, launch kernels, and handle results. The request may
remain pending until a suitable node is free.

Inside it:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
bash "$COURSE_ROOT/containers/verify_container.sh" \
  "$COURSE_IMAGE" gpu
```

Read the output — it is intentionally left off the block above so pasting it
does not immediately end the allocation before you have seen it. Once you are
done, run `exit` on its own to release the allocation and return to the login
node:

```bash
exit
```

The verification script first runs the image's normal tests. In `gpu` mode it
also confirms that the command is inside a Slurm allocation, runs
`nvidia-smi` through `apptainer exec --nv`, and asks QuantUI to check its GPU
environment. `exit` releases the interactive allocation.

The CPU verification path does not use `--nv`; the GPU path does. This lets one
image serve both workflows without reserving a GPU for CPU-only work.

## 22-28 min — Read the batch job (login node)

Open [`quantui_gpu.sbatch`](slurm/quantui_gpu.sbatch) — a link to read here,
wherever you are reading this tutorial (e.g. on GitHub), or in your cluster
clone at `$COURSE_ROOT/tutorials/04-gpu-quantui/slurm/quantui_gpu.sbatch`; it
is not a shell command. Connect each layer to its responsibility:

| Layer | Evidence in the job |
|---|---|
| Scheduler | GPU partition, `--gres`, CPUs, memory, wall time |
| Container | SIF path, `--nv`, bind mounts, clean runtime environment |
| Application | `quantui gpu check`, water calculation, `gpu_used` assertion |
| Reproducibility | image labels, installed QuantUI version, source-checkout commit, JSON result, Slurm log |

The job requests one GPU because this example uses one. More GPUs would not
make this script multi-GPU.

The Python program [`run_quantui_gpu.py`](run_quantui_gpu.py) creates a
water molecule, calls QuantUI's `run_in_session` API with the RHF method and
STO-3G basis, and writes a JSON result. JSON is a text format of named values;
it is useful here because people and programs can both inspect it. The script
exits with an error if the calculation did not converge or if QuantUI reports
that GPU offload was not used.

## 28-33 min — Submit (login node)

```bash
cd "$COURSE_ROOT/tutorials/04-gpu-quantui"
JOB_ID=$(sbatch --parsable --export=ALL,COURSE_IMAGE="$COURSE_IMAGE" \
  slurm/quantui_gpu.sbatch)
echo "Submitted job: $JOB_ID"
```

`sbatch` submits the file to Slurm and returns a job ID. `--export` passes the
current variables and explicitly supplies the image path. `--parsable` makes
`sbatch` print just the numeric ID (instead of `Submitted batch job 12345`), so
`JOB_ID=$(...)` captures it into a shell variable you reuse in the commands
below. The shell script will run later on the assigned GPU node; closing the
terminal after submission does not cancel the batch job.

`JOB_ID` lives only in this shell session. If you open a new terminal or your
session drops, re-find it with `squeue -u "$USER"` and set it again, e.g.
`JOB_ID=709747`.

## 33-40 min — Monitor and verify (login node)

```bash
squeue -j "$JOB_ID" -o "%.18i %.9T %.10M %.6D %.30R"
sacct -j "$JOB_ID" --format=JobID,State,Elapsed,AllocCPUS,ReqMem,ExitCode
less "$COURSE_WORK/logs/quantui-gpu-$JOB_ID.out"

apptainer exec \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  "$COURSE_IMAGE" \
  python -m json.tool \
  "$COURSE_WORK/quantui/quantui_gpu_result.json"
```

These reuse the `$JOB_ID` you captured at submit, so nothing needs to be typed
in by hand. The `squeue` format is the same one decoded in the CPU tutorial:
job ID, state, elapsed time, node count, and assigned node or pending reason. `sacct` reports the final state,
resources, and exit code. `python -m json.tool FILE` parses and pretty-prints
the result, which also verifies that it is valid JSON.

The `squeue`, `sacct`, and `less` commands are ordinary login-node tools. The
`json.tool` line runs container Python but imports only the standard library, so
it is fine on the login node too, unlike the scientific-stack commands, which
need a compute node.

Expected fields include:

```json
{
  "converged": true,
  "gpu_used": true,
  "method": "RHF",
  "basis": "STO-3G"
}
```

The other fields need context too: `converged` means the iterative
self-consistent-field procedure reached its stopping criterion; `RHF` names
the electronic-structure method; and `STO-3G` names the intentionally small
basis set. They demonstrate a workflow, not a research-quality calculation.

This tells you the calculation followed QuantUI's supported GPU-offload
path. It does **not** tell you the GPU was faster—water/STO-3G is far too
small for that. The next section measures that question directly.

## 40-52 min — Find the crossover (compute node)

A GPU is not simply "faster". Every offloaded calculation pays a fixed cost:
launching kernels and moving data between host and device. For a small
system that overhead dominates the actual arithmetic, so **the CPU wins**. As
the basis set grows, integral and Fock construction grow faster than the
overhead, and at some point **the GPU wins**. Where that crossover sits
depends on the molecule, basis, method, and the specific hardware.

Measure it rather than assuming it. This timing loop needs a GPU allocation of
its own — request one now that the earlier verification shell has been
released:

```bash
srun -p workshop \
  --gres=gpu:h200:1 \
  --time=00:10:00 \
  --cpus-per-task=12 \
  --mem=16G \
  --pty bash -l
```

With the prompt now on the allocated GPU node, run the sweep:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
cd "$COURSE_ROOT/tutorials/04-gpu-quantui"

for p in small medium crossover large; do
  apptainer exec --nv --cleanenv \
    --bind "$COURSE_WORK:$COURSE_WORK" \
    --env "COURSE_WORK=$COURSE_WORK" \
    --env "COURSE_IMAGE=$COURSE_IMAGE" \
    --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}" \
    --env "SLURM_CPUS_PER_TASK=$SLURM_CPUS_PER_TASK" \
    --env "OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK" \
    "$COURSE_IMAGE" \
    python run_cpu_gpu_comparison.py --preset "$p"
done
```

Both legs of each preset print a wall time and energy to the terminal as the
loop runs — that live output is what you copy into the table below, so `exit`
is deliberately left off this block. Fill in your numbers first, then release
the GPU:

```bash
exit
```

### What this looked like on NCShare

Measured 2026-08-18 on the workshop partition's own H200 node, **1 GPU
against 12 affinity-confirmed CPU cores** — the proportional share NCShare
confirms for this node (96 cores across 8 GPUs, so 12 cores per GPU, not an
estimate). Two earlier measurements — one on a less generous CPU allocation,
one on different hardware entirely — are kept in the appendix at the end of
this file, together with a full walk-through of what each change did to the
numbers:

| System | GPU | CPU | CPU time / GPU time |
|---|---:|---:|---|
| H2O / STO-3G | 6.89 s | 0.37 s | 0.05x |
| C6H6 / 6-31G | 7.65 s | 0.85 s | 0.11x |
| C6H6 / cc-pVDZ | 7.87 s | 2.96 s | 0.38x |
| C6H6 / cc-pVTZ | 11.84 s | 24.46 s | **2.07x — GPU wins** |

The CPU column responds unevenly to the allocation: the small presets are
dominated by fixed overhead (container start, import, a handful of SCF
iterations) rather than parallelizable work, so more cores barely help, while
cc-pVTZ's cost is genuinely parallel and drops accordingly. The GPU column
stays in a fairly narrow band — 6.89 s to 11.84 s — without a clean monotonic
climb; that noise is real, and the appendix says more about where it comes
from. The crossover falls somewhere **between cc-pVDZ and cc-pVTZ**: the CPU
still wins at cc-pVDZ, and the GPU has already won by cc-pVTZ, rather than
either preset landing near parity.

> **Note:** We chose 12 cores to make a proportional comparison: 12 cores per
> GPU is what NCShare's workshop node actually allocates. Thus, we want to
> use this ratio when comparing performance. A less generous CPU allocation
> may (and does - check out the Appendix below for extra testing we did) look
> meaningfully different. A key takeaway is that, when comparing hardware
> speeds, always quote the hardware numbers your comparison is based upon.

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

| System | CPU (s) | GPU (s) | CPU time / GPU time |
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
Slurm had granted **12**.

That was safe only because Slurm used a *cpuset*, so the affinity mask also
showed 12 and threading libraries saw the real allocation. Under a cgroup CPU
*quota* instead, the mask would have reported 192, OpenMP would have spawned
192 threads onto 12 cores' worth of time, and every CPU timing would have been
inflated — making the GPU look better than it is.

Same request, same `cpu_count()`, opposite consequences. Whenever you
benchmark on a shared cluster, confirm what you were actually given rather
than what the machine says it has.

### Carry the numbers into the visualization session

Each comparison writes a small JSON file to `$COURSE_WORK/quantui/`. You will
plot these in [Session 4](../05-visualization-postprocessing/README.md). The
primary notebook uses a connected-dot plot on a logarithmic time axis; the
preserved focused QuantUI notebook offers a grouped-bar alternative. Both read
the JSON directly, so there is no need to copy numbers by hand.

**Optional — a geometry-relaxation trajectory to plot.** This adds
energy-at-each-optimization-step data to the visualization session. Skip it
if you are short on time: without it, the notebook falls back to a clearly
marked synthetic trajectory and the rest of the course is unaffected.

This is CPU-only work — QuantUI's optimizer runs on the host, not the GPU —
so it needs its **own** short CPU allocation, separate from anything else.
Do **not** run it on the login node. Do **not** try to run it from a terminal
inside the visualization session's Open OnDemand JupyterLab either: that
session is itself launched through Apptainer, and a terminal inside it does
not have the `apptainer` command available to nest another container call.
Request a plain CPU shell instead:

```bash
srun -p workshop --cpus-per-task=2 --mem=4G --time=00:10:00 --pty bash -l
```

A good time to do this is around when you launch
[Session 4](../05-visualization-postprocessing/README.md)'s Open OnDemand
job, so the two queue waits overlap instead of stacking.

With the prompt now on a compute node, run the calculation:

```bash
export COURSE_ROOT="${COURSE_ROOT:-$HOME/ncshare-crash-course}"
export COURSE_WORK="${COURSE_WORK:-/work/$USER/ncshare-crash-course}"
export COURSE_IMAGE="${COURSE_IMAGE:-/opt/apps/containers/users/ncshare-science-course.sif}"
apptainer exec --cleanenv \
  --bind "$COURSE_WORK:$COURSE_WORK" \
  --env "COURSE_WORK=$COURSE_WORK" \
  "$COURSE_IMAGE" \
  python "$COURSE_ROOT/tutorials/04-gpu-quantui/run_geometry_optimization.py" \
  --preset water
```

Review the output, then release the allocation:

```bash
exit
```

## 52-60 min — Explain and improve the design (login node)

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

## Appendix: two changes to the crossover measurement, and what each one did

The table in "Find the crossover" above did not arrive at its final form in
one step. Two independent things changed on the way there — which physical
node the job ran on, and how many CPU cores it was compared against — and
each moved the numbers for a different, identifiable reason. Walking through
all three measurements side by side, instead of quietly discarding the
earlier ones, is itself a short lesson in what "the GPU is N times faster"
actually depends on.

### Measurement 1 — an earlier run, on different hardware

Measured 2026-08-05, **1 GPU against 6 affinity-confirmed CPU cores**, before
NCShare had finalized which node the workshop's `workshop` partition would
use:

| System | GPU | CPU | CPU time / GPU time |
|---|---:|---:|---|
| H2O / STO-3G | 1.80 s | 0.35 s | 0.20x |
| C6H6 / 6-31G | 2.69 s | 0.77 s | 0.29x |
| C6H6 / cc-pVDZ | 2.86 s | 2.74 s | **0.96x — the crossover** |
| C6H6 / cc-pVTZ | 7.07 s | 42.41 s | **6.00x** |

### Measurement 2 — the workshop's own node, still at 6 cores

Measured 2026-08-18, **1 GPU against 6 affinity-confirmed CPU cores** — the
same allocation shape as measurement 1, but on the node the workshop
actually uses:

| System | GPU | CPU | CPU time / GPU time |
|---|---:|---:|---|
| H2O / STO-3G | 6.95 s | 0.62 s | 0.09x |
| C6H6 / 6-31G | 10.30 s | 0.92 s | 0.09x |
| C6H6 / cc-pVDZ | 8.10 s | 3.28 s | 0.40x |
| C6H6 / cc-pVTZ | 12.33 s | 42.14 s | **3.42x** |

This is a genuinely different physical GPU from the one behind measurement 1
— not the same hardware measured twice.

### Why the GPU column moved between 1 and 2, and the CPU column mostly didn't

| System | Measurement 1 GPU | Measurement 2 GPU | Difference |
|---|---:|---:|---:|
| H2O / STO-3G | 1.80 s | 6.95 s | +5.15 s |
| C6H6 / 6-31G | 2.69 s | 10.30 s | +7.61 s |
| C6H6 / cc-pVDZ | 2.86 s | 8.10 s | +5.24 s |
| C6H6 / cc-pVTZ | 7.07 s | 12.33 s | +5.26 s |

Three of the four differences cluster tightly around **+5.2 s** — roughly
constant, not proportional to the size of the calculation. A proportional
slowdown would mean the GPU itself computed more slowly; a constant one
points instead at something added *around* the calculation on both runs
alike — most plausibly contention on a shared GPU node: PCIe/NVLink
bandwidth, host-memory bandwidth, or CUDA context/kernel-launch scheduling
delay from other jobs sharing the same GPUs at the same time. The CPU column,
by contrast, barely moved at its largest value — 42.41 s then, 42.14 s now —
because Slurm's CPU allocation is more strictly isolated by the scheduler
than a GPU's shared memory and interconnect paths are.

### Measurement 3 — the same node, at the proportional 12-core share (the main text)

Measured the same day as measurement 2, same node, **1 GPU against 12
affinity-confirmed CPU cores** — the proportional share NCShare confirms for
this node (96 cores across 8 GPUs). This is the table shown in the main
text, repeated here for direct comparison:

| System | GPU | CPU | CPU time / GPU time |
|---|---:|---:|---|
| H2O / STO-3G | 6.89 s | 0.37 s | 0.05x |
| C6H6 / 6-31G | 7.65 s | 0.85 s | 0.11x |
| C6H6 / cc-pVDZ | 7.87 s | 2.96 s | 0.38x |
| C6H6 / cc-pVTZ | 11.84 s | 24.46 s | **2.07x** |

### Why doubling the cores mattered for one preset and not the others

Doubling the CPU allocation from measurement 2 to measurement 3 barely
touches the small presets — H2O's CPU leg drops from 0.62 s to 0.37 s, not
half — because those runs are dominated by fixed overhead (container start,
import, a handful of SCF iterations), not by parallelizable work extra cores
can speed up. cc-pVTZ tells a different story: its CPU leg drops from 42.14 s
to 24.46 s, a real ~1.7x speedup from twice the cores, and the GPU's margin
at that preset shrinks from **3.42x to 2.07x** as a direct result. The
crossover point itself stays inside the same cc-pVDZ–cc-pVTZ bracket in both
cases — cc-pVDZ still favors the CPU either way — but the *size* of the
GPU's eventual win depends heavily on what it is being compared against.

### The lesson, not just the numbers

None of this changes the mechanism the exercise teaches: small systems lose
to fixed launch/transfer overhead, large systems eventually win on raw
arithmetic. What changed, twice, was the *size* of the numbers around that
mechanism — once because of which physical hardware and how much contention
it carried, once because of how generous a CPU allocation the GPU was being
compared against. Neither is a flaw in the measurement; both are real
properties of shared clusters and honest benchmarking worth teaching
directly. A speed number without its measurement conditions — which node,
how much contention, which CPU allocation — is not reproducible. These three
tables, side by side, are a concrete demonstration of exactly that point, and
a fair prompt for discussion: what would you need to report alongside a
timing number for someone else to trust it?

## Sources

- [QuantUI repository and GPU guidance](https://github.com/The-Schultz-Lab/QuantUI)
- [NCShare GPU guide](https://userguide.ncshare.org/guides/gpu/)
- [NCShare Cluster Software guide](https://userguide.ncshare.org/guides/slurm/software/)
- [Apptainer GPU support](https://apptainer.org/docs/user/latest/gpu.html)
