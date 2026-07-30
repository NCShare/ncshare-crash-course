# Instructor and HPC administrator readiness checklist

Complete this checklist at least one week before the workshop. The primary
course path assumes NCShare's container-first software model; the module-based
workflow is optional bonus material for other clusters.

## Access and capacity

- [ ] All participants have NCShare accounts and registered SSH public keys.
- [ ] GPU participants have access to `gpu` or `interactive-gpu`.
- [ ] A temporary `workshop` partition/reservation is available, or all Slurm
  files use the approved teaching partition.
- [ ] Class CPU/GPU concurrency limits can accommodate the planned jobs.
- [ ] Open OnDemand JupyterLab accepts the custom course SIF.

## Build and stage the course image

- [ ] Review `containers/ncshare-science-course.def`, including base image,
  upstream licenses, pinned commits, package sources, and comments.
- [x] Confirm that the CUDA 12.8.1/Ubuntu 24.04 base remains appropriate for
  the NCShare H200 driver. **Confirmed.** See the recorded values below;
  re-verify these before each offering rather than assuming they still hold.
- [ ] Build through the approved NCShare GitLab runner or in a CPU allocation;
  never start dozens of identical student builds.
- [ ] Run `apptainer test` and `containers/verify_container.sh IMAGE cpu`.
- [ ] In an H200 allocation, run
  `containers/verify_container.sh IMAGE gpu`.
- [ ] Retain the definition, CI log, SIF, SHA-256 checksum, image labels,
  `/opt/course-build/conda-explicit.txt`, and
  `/opt/course-build/pip-freeze.txt`.
- [ ] Stage the reviewed image at the published path, normally
  `/opt/apps/containers/user/ncshare-science-course.sif`, and confirm every
  compute/Open OnDemand node can read it.
- [ ] Publish the checksum and image path before participants begin.

## Recorded NCShare hardware

Observed values, not assumptions. Re-capture these before each offering — a
driver upgrade or a MIG reconfiguration changes what the GPU lab does.

| Fact | Value | Why it matters |
|---|---|---|
| GPU nodes | 4, each with 8x NVIDIA H200 SXM 141 GB (32 total) | Ample for a ~10-person class; GPU contention is not a scheduling risk |
| GPU node CPU/RAM | Intel Xeon Platinum 8568Y+, ~96 physical cores, 2 TB RAM | ~12 cores per GPU, so `--cpus-per-task=4` is comfortable |
| Compute capability | 9.0 (Hopper) | Covered by prebuilt `cuda12x` wheels; no local `nvcc` needed |
| CPU nodes | 8x AMD EPYC 7543, ~64 physical cores, 512 GB RAM each | Sizing for the MPI lab |
| Interconnect | **10/40 Gbps Ethernet, not InfiniBand** | Keep inoisy+ single-node; see the MPI warning below |
| Storage | 400 TB FreeNAS NFS | Avoid many-small-file I/O patterns |
| Driver / CUDA | Recently upgraded; capture `nvidia-smi` output at build time | Does not change the wheel choice — see below |
| MIG mode | Not confirmed | If enabled, `--gres=gpu:h200:1` yields a slice, changing what students see in `nvidia-smi` |

- [ ] Capture current `nvidia-smi` output and record the driver version here.
- [ ] Confirm MIG mode with `nvidia-smi -L`.
- [ ] Record the Apptainer version and whether `--nv` uses the legacy
  `nvliblist.conf` path or `--nvccli` / `nvidia-container-cli`.
- [ ] Confirm the exact partition name and `--gres` type string, then make
  every `.sbatch` file agree with it.

**On CUDA versions:** the image pins `cuda12x` wheels deliberately. CUDA's
driver API is backward compatible, so `cuda12x` runs on both the older 570.x
driver line and a 580+/CUDA 13 driver, whereas `cuda13x` requires >= 580 and
would fail on 570.x. `cuda12x` also matches the image's CUDA 12.8.1 base.
Do not "upgrade" to `cuda13x` without confirming every GPU node's driver.

## Validate both scientific workflows

- [ ] Submit the one-rank and four-rank inoisy+ jobs from the staged SIF.
- [ ] Verify both use one node and produce `/data/data_raw` with global shape
  `(16, 16, 16, 16)`.
- [ ] Confirm the MPI launch pattern matches current NCShare guidance. Do not
  extend the class example to multiple nodes without administrator validation
  of host/container MPI compatibility. **NCShare's interconnect is 10/40 Gbps
  Ethernet, not InfiniBand**, so multi-node MPI would be latency-bound even if
  it worked; keep every rank on one node and say why in class.
- [ ] Submit the QuantUI job and verify the JSON result contains
  `"gpu_used": true`.
- [ ] Confirm every GPU invocation includes both a Slurm GPU request and
  `apptainer exec --nv`.
- [ ] Run the upstream inoisy4d emissivity converter from the SIF.
- [ ] Execute every visualization-notebook cell against a real solver result
  using the SIF's Python kernel.

## Teaching and failure fallbacks

- [ ] Walk through one shared definition/build pipeline during class, but use
  the prebuilt SIF so build time or package-network delays cannot block labs.
- [ ] Keep the small synthetic HDF5 fallback for queue delays.
- [ ] Prepare a one-page explanation of the boundary among Slurm resources,
  image software, host GPU drivers, bind-mounted data, and application logic.
- [ ] Explain pros and cons: consistency/portability/provenance versus image
  size/build time/security rebuilds/MPI compatibility.
- [ ] Test the three-layer diagnostic sequence: Slurm → Apptainer → application.
- [ ] Keep the optional `bonus/module-based-cluster` path, but label its module
  names as site-specific and do not present it as the NCShare default.

## Course-repository edits before publishing

- [ ] Replace `<COURSE_REPOSITORY_URL>` in `tutorials/00-prework.md`.
- [ ] Add the final year, room, contacts, and support channel to the agenda.
- [ ] Choose a license for the new course material; retain all external
  project licenses and citations.
- [ ] Replace the default `COURSE_IMAGE` path if the HPC team stages the SIF
  elsewhere.
- [ ] Update the pinned source commits deliberately after rebuilding and
  rerunning every smoke test.

## One-sentence administrator role

HPC admins provide workshop access and teach the NCShare login/compute boundary,
storage lifetimes, partitions, and how the shared Apptainer image is built,
staged, launched, and supported.
