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

## 3. Install Miniforge in your home directory

NCShare recommends a user-owned conda installation in `/hpc/home/$USER`.
Follow the current
[Cluster Software guide](https://userguide.ncshare.org/guides/slurm/software/).
At the end, verify:

```bash
conda --version
conda info --envs
```

Do not install environments in `/work`; it is temporary storage.

## 4. Clone the course

The instructor will replace the placeholder below before publishing:

```bash
cd "$HOME"
git clone <COURSE_REPOSITORY_URL> ncshare-crash-course
cd "$HOME/ncshare-crash-course"
```

If the repository has already been cloned, use `git pull --ff-only` instead.

## 5. Optional local preparation

Review the
[Getting Started Overview](https://userguide.ncshare.org/guides/overview/) and
bring a laptop charger. No prior C/C++, MPI, quantum chemistry, or
astrophysics knowledge is required.
