# Pre-workshop setup

Complete this before the workshop. Setup happens partly in a terminal on your
laptop and partly after connecting to NCShare. If a command fails, copy the
command and its complete error message; that evidence is more useful than
repeating setup attempts blindly.

## 1. Activate your NCShare account

Follow the official
[account registration guide](https://userguide.ncshare.org/guides/accountreg/).
GPU access is separate; request it through your institutional representative
before the workshop.

## 2. Configure SSH

Follow the official
[SSH guide](https://userguide.ncshare.org/guides/setupssh/). Keep the private
key on your computer and add only the `.pub` public key to your NCShare profile.

Test the connection:

```bash
ssh NCSHARE_UID@login.ncshare.org
hostname -A
exit
```

Open a terminal on your laptop, replace `NCSHARE_UID` with your account ID, and
type the commands one line at a time. `ssh` opens the remote session,
`hostname -A` asks the remote computer to identify itself, and `exit` closes
the session. The hostname should identify an NCShare login host. Session 1
introduces terminals, shell variables, paths, and command options in more
detail.

## 3. Confirm the course container path

The course uses a shared Apptainer image instead of a per-user compiler or conda
installation. The instructor will publish the final path and SHA-256 checksum.
After logging in, record:

```bash
export COURSE_IMAGE="/opt/apps/containers/user/ncshare-science-course.sif"
apptainer --version
ls -lh "$COURSE_IMAGE"
```

`export` gives the long image path the shorter variable name `COURSE_IMAGE`.
`apptainer --version` verifies that the container runtime is available, while
`ls -lh` verifies that the shared image exists and is readable. A SIF is a
read-only Apptainer image containing the course software.

Do not download or build the multi-gigabyte SIF individually unless the
instructor explicitly assigns the container-building exercise.

## 4. Clone the course

The instructor will replace the placeholder below before publishing:

```bash
cd "$HOME"
git clone <COURSE_REPOSITORY_URL> ncshare-crash-course
cd "$HOME/ncshare-crash-course"
```

These commands run on the NCShare login node. `cd` changes directory and
`git clone` downloads a working copy of the course files. Replace the
placeholder URL with the address published by the instructor; do not type the
angle brackets literally.

If the repository has already been cloned, use `git pull --ff-only` instead.

## 5. Optional preparation

Review the
[Getting Started Overview](https://userguide.ncshare.org/guides/overview/) and
the [NCShare FHI-aims Apptainer example](https://userguide.ncshare.org/examples/apptainer-fhiaims/).
Bring a laptop charger. No prior container, C/C++, MPI, quantum chemistry, or
astrophysics knowledge is required.
