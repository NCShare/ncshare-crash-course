# Instructor and HPC administrator readiness checklist

Complete this checklist at least one week before the workshop. The primary course path assumes NCShare's container-first software model; the module-based workflow is optional bonus material for other clusters.

This is a reusable template: the boxes start unchecked, and the recorded values below are the ones measured on the first NCShare offering. Re-verify them for each offering rather than assuming they still hold.

## Access and capacity

- [ ] All participants have accounts and registered SSH public keys.
- [ ] GPU participants have access to the GPU partition, and every `.sbatch` file uses the approved teaching partition.
- [ ] Class CPU/GPU concurrency limits can accommodate the planned jobs.
- [ ] Open OnDemand JupyterLab accepts the custom course SIF.

## Build and stage the course image

- [ ] Review `containers/ncshare-science-course.def`, including base image, upstream licenses, pinned commits, package sources, and comments.
- [ ] Confirm that the CUDA 12.8.1/Ubuntu 24.04 base remains appropriate for the current GPU driver. See the recorded values below; re-verify these before each offering.
- [ ] Build through the approved GitLab runner or in a CPU allocation; never start dozens of identical student builds.
- [ ] Run `apptainer test` and `containers/verify_container.sh IMAGE cpu`.
- [ ] In an H200 allocation, run `containers/verify_container.sh IMAGE gpu`.
- [ ] Retain the definition, CI log, SIF, SHA-256 checksum, image labels, `/opt/course-build/conda-explicit.txt`, and `/opt/course-build/pip-freeze.txt`.
- [ ] Stage the reviewed image at the published path, normally `/opt/apps/containers/users/ncshare-science-course.sif`, and confirm every compute/Open OnDemand node can read it.
- [ ] Publish the checksum and image path before participants begin.

## Recorded NCShare hardware

Values below were measured on the first NCShare offering (2026-08-05). Treat them as example readings to re-confirm, not fixed facts.

| Fact                      | Value                                                    | Why it matters                                                                                 |
| ------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| GPU nodes                 | 4, each with 8x NVIDIA H200 SXM 141 GB (32 total)        | Ample for a ~10-person class; GPU contention is not a scheduling risk                          |
| GPU node CPU/RAM          | Intel Xeon Platinum 8568Y+, ~96 physical cores, 2 TB RAM | ~12 cores per GPU, so `--cpus-per-task=4` is comfortable                                       |
| Compute capability        | 9.0 (Hopper)                                             | Covered by prebuilt `cuda12x` wheels; no local `nvcc` needed                                   |
| CPU nodes                 | 8x AMD EPYC 7543, ~64 physical cores, 512 GB RAM each    | Sizing for the MPI lab                                                                         |
| Interconnect              | 10/40 Gbps Ethernet                                      | Keep inoisy+ single-node; see the MPI warning below                                            |
| Storage                   | 400 TB FreeNAS NFS                                       | Avoid many-small-file I/O patterns                                                             |
| Driver                    | 580.126.20 (measured 2026-08-05)                         | CuPy reports driver API 13000 against runtime 12090 — works, and confirms the `cuda12x` choice |
| GPU memory                | 143771 MiB                                               | Verification molecules use a tiny fraction                                                     |

- [ ] Capture `nvidia-smi` and record the driver version. (First offering measured driver 580.126.20, compute capability 9.0, H200 143771 MiB.)
- [ ] Confirm MIG mode with `nvidia-smi -L`. The first offering used whole (non-MIG) H200s, so whole-GPU allocation worked; re-check per site.
- [ ] Record the Apptainer version and whether `--nv` uses the legacy `nvliblist.conf` path or `--nvccli` / `nvidia-container-cli`. (First offering: Apptainer v1.5.3.)
- [ ] **Confirm the `--gres` type string via an actual `sbatch`.** Verify both interactive `srun` and batch `sbatch` on the GPU partition; `gpu:h200:1` is the specific form and `gpu:1` the generic fallback.
- [ ] Confirm whether a workshop-day reservation supersedes the standing GPU partition, then make every `.sbatch` file agree.

**GPU path verified end to end on 2026-08-05.** QuantUI's standalone GPU image
(v0.6.1) passed all seven checks on an NCShare H200 — device visible through
`--nv`, CuPy/driver ABI match, `gpu_used: true`, and the `QUANTUI_DISABLE_GPU`
negative control flipping correctly. The same ladder should be re-run against
the combined course SIF once it exists; see
[QuantUI `apptainer/verify-gpu.sh`](https://github.com/The-Schultz-Lab/QuantUI).

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

- [ ] Decide how to present the container build: walking through the shared
  definition/build pipeline in class, or covering it through slides while the
  labs use the prebuilt SIF so build time or package-network delays cannot
  block them. The Apptainer tutorial is optional either way.
- [ ] Keep the small synthetic HDF5 fallback for queue delays.
- [ ] Prepare a one-page explanation of the boundary among Slurm resources, image software, host GPU drivers, bind-mounted data, and application logic.
- [ ] Explain pros and cons: consistency/portability/provenance versus image
  size/build time/security rebuilds/MPI compatibility.
- [ ] Test the three-layer diagnostic sequence: Slurm → Apptainer → application.
- [ ] Keep the optional `bonus/module-based-cluster` path, but label its module names as site-specific and do not present it as the NCShare default.

## Per-offering customization

- [ ] Set the final year, room, contacts, and support channel in the agenda.
- [ ] Confirm the `COURSE_IMAGE` path matches where the HPC team stages the SIF.
- [ ] Review the resolved inoisy4d commit and update pinned source commits deliberately after rebuilding and rerunning every smoke test.
- [ ] Retain all external project licenses and citations.

## One-sentence administrator role

HPC admins provide workshop access and teach the NCShare login/compute boundary, storage lifetimes, partitions, and how the shared Apptainer image is built, staged, launched, and supported.
