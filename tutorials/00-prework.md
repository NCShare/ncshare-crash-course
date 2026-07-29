# Pre-workshop setup

Complete this before the workshop. Bring any error message with you rather than
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

The hostname should identify an NCShare login host.

## 3. Confirm the course container path

The course uses a shared Apptainer image instead of a per-user compiler or conda
installation. The instructor will publish the final path and SHA-256 checksum.
After logging in, record:

```bash
export COURSE_IMAGE="/opt/apps/containers/user/ncshare-science-course.sif"
apptainer --version
ls -lh "$COURSE_IMAGE"
```

Do not download or build the multi-gigabyte SIF individually unless the
instructor explicitly assigns the container-building exercise.

## 4. Clone the course

The instructor will replace the placeholder below before publishing:

```bash
cd "$HOME"
git clone <COURSE_REPOSITORY_URL> ncshare-crash-course
cd "$HOME/ncshare-crash-course"
```

If the repository has already been cloned, use `git pull --ff-only` instead.

## 5. Optional preparation

Review the
[Getting Started Overview](https://userguide.ncshare.org/guides/overview/) and
the [NCShare FHI-aims Apptainer example](https://userguide.ncshare.org/examples/apptainer-fhiaims/).
Bring a laptop charger. No prior container, C/C++, MPI, quantum chemistry, or
astrophysics knowledge is required.
