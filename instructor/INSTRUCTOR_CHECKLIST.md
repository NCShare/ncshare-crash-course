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
- [ ] Confirm that the CUDA 12.8.1/Ubuntu 24.04 base remains appropriate for
  the NCShare H200 driver.
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

## Validate both scientific workflows

- [ ] Submit the one-rank and four-rank inoisy+ jobs from the staged SIF.
- [ ] Verify both use one node and produce `/data/data_raw` with global shape
  `(16, 16, 16, 16)`.
- [ ] Confirm the MPI launch pattern matches current NCShare guidance. Do not
  extend the class example to multiple nodes without administrator validation
  of host/container MPI compatibility.
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
- [ ] Review the resolved inoisy4d commit and update pinned source commits
  deliberately after rebuilding and rerunning every smoke test.

## One-sentence administrator role

HPC admins provide workshop access and teach the NCShare login/compute boundary,
storage lifetimes, partitions, and how the shared Apptainer image is built,
staged, launched, and supported.
