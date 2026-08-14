# Instructor and HPC administrator readiness checklist

Complete this checklist at least one week before the workshop. The primary
course path assumes NCShare's container-first software model; the module-based
workflow is optional bonus material for other clusters.

## Access and capacity

- [ ] All participants have NCShare accounts and registered SSH public keys.
- [ ] GPU participants have access to the temporary `workshop` partition for
  the event. If that reservation is unavailable, choose one documented
  alternative (`interactive-gpu` for short interactive work or `gpu` for
  preemptible batch work) and update every teaching command consistently.
- [ ] Class CPU/GPU concurrency limits can accommodate the planned jobs.
- [ ] Open OnDemand JupyterLab accepts the custom course SIF.

## Build and stage the course image

- [ ] Review `containers/ncshare-science-course.def`, including base image,
  upstream licenses, the pinned QuantUI release, the inoisy4d source-selection
  policy, package sources, and comments.
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
| GPU nodes | 4, each with 8x NVIDIA H200 SXM 141 GB (32 total) | The temporary `workshop` reservation was reported as one 8-GPU node; plan at most eight simultaneous one-GPU jobs unless the reservation changes |
| GPU node CPU/RAM | Intel Xeon Platinum 8568Y+, ~96 physical cores / 192 schedulable CPU threads, 2 TB RAM | About 12 physical cores per GPU; keep CPU requests proportional and record the allocated count |
| Compute capability | 9.0 (Hopper) | Covered by prebuilt `cuda12x` wheels; no local `nvcc` needed |
| CPU nodes | 8x AMD EPYC 7543, ~64 physical cores, 512 GB RAM each | Sizing for the MPI lab |
| Interconnect | **10/40 Gbps Ethernet, not InfiniBand** | Keep inoisy+ single-node; see the MPI warning below |
| Storage | 400 TB FreeNAS NFS | Avoid many-small-file I/O patterns |
| Driver | **580.126.20** (measured 2026-08-05) | CuPy reports driver API 13000 against runtime 12090 — works, and confirms the `cuda12x` choice |
| GPU memory | 143771 MiB | Verification molecules use a tiny fraction |
| Verified general path | `compute-gpu-02` / partition `gpu` on 2026-08-05 | General interactive allocation confirmed working |
| Reported workshop path | partition `workshop`, `--gres=gpu:h200:1` on 2026-08-12 | Reconfirm the temporary reservation immediately before class |

- [x] Capture `nvidia-smi` and record the driver version. **Done:** 580.126.20,
  compute capability 9.0, H200 143771 MiB.
- [ ] Confirm MIG mode with `nvidia-smi -L` (whole-GPU allocation worked, so
  not blocking).
- [ ] Record the Apptainer version and whether `--nv` uses the legacy
  `nvliblist.conf` path or `--nvccli` / `nvidia-container-cli`.
- [x] Confirm the requested GPU type as `--gres=gpu:h200:1`. This is also the
  current form in the official NCShare GPU guide.
- [ ] Reconfirm that the temporary `workshop` reservation is active on the
  teaching date. The tracked `.sbatch` files consistently use `workshop`.

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

- [x] Publish the course clone URL in `tutorials/00-prework.md`.
- [ ] Add the final year, room, contacts, and support channel to the agenda.
- [x] Retain the repository's MIT `LICENSE` for the course material and keep
  all external project licenses and citations.
- [ ] Replace the default `COURSE_IMAGE` path if the HPC team stages the SIF
  elsewhere.
- [ ] Review the resolved inoisy4d commit and update pinned source commits
  deliberately after rebuilding and rerunning every smoke test.

## One-sentence administrator role

HPC admins provide workshop access and teach the NCShare login/compute boundary,
storage lifetimes, partitions, and how the shared Apptainer image is built,
staged, launched, and supported.
