# Pre-workshop setup

Complete this before the workshop. Setup happens partly in a terminal on your
laptop and partly after connecting to NCShare.

> **Tip:** If a command fails, copy the command and its complete error message
> and bring it to the workshop rather than repeating setup attempts blindly.

---

## Contents

1. [Activate your NCShare account](#1-activate-your-ncshare-account)
2. [Configure SSH](#2-configure-ssh)
   - [2b. Windows users: pick an SSH client](#2b-windows-users-pick-an-ssh-client)
     - [Generating a key with built-in OpenSSH](#generating-a-key-with-built-in-openssh)
     - [Using Bitvise instead](#using-bitvise-instead)
     - [Check it worked](#check-it-worked)
   - [2c. No-install alternative: Open OnDemand](#2c-no-install-alternative-open-ondemand)
3. [Confirm the course container path](#3-confirm-the-course-container-path)
4. [Clone the course](#4-clone-the-course)
5. [Optional preparation](#5-optional-preparation)

---

## 1. Activate your NCShare account

Follow the official
[account registration guide](https://userguide.ncshare.org/guides/accountreg/).

> **Important:** GPU access is separate; request it through your institutional
> representative before the workshop.

---

## 2. Configure SSH

Follow the official
[SSH guide](https://userguide.ncshare.org/guides/setupssh/).

> **Important:** Keep the private key on your computer and add only the `.pub`
> public key to your NCShare profile.

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

> **Note:** On macOS and Linux, run the command above in Terminal. On Windows,
> see the next section first — the NCShare guide assumes a Unix-style
> terminal.

### 2b. Windows users: pick an SSH client

The official NCShare SSH guide is the authority on *what* to configure. This
section only covers *where* to do it on Windows, which the guide does not
address. Any of these work; you do not need more than one.

| Option | Install needed? | Notes |
| :--- | :---: | :--- |
| **Windows OpenSSH** (built in) | No | `ssh` works in PowerShell or Terminal exactly as written above. Keys live in `C:\Users\<you>\.ssh\`. Simplest if you are comfortable at a command line. |
| **Bitvise SSH Client** | Yes (free for individual use) | Graphical. Terminal plus a drag-and-drop file-transfer pane and a point-and-click port forwarding tab. |
| **MobaXterm** | Yes (free tier) | Graphical, bundles a terminal and SFTP browser. |
| **PuTTY** | Yes (free) | Long-established, minimal. Uses its own `.ppk` key format via PuTTYgen. |
| **WSL** | Yes (Windows feature) | Gives you a real Linux shell; then follow the macOS/Linux instructions unchanged. |
| **Open OnDemand** | No | Browser only, no SSH client at all. See section 2c. |

> **Tip:** If you have no preference, **built-in OpenSSH** is the smallest
> step, and **Bitvise** is the most forgiving if you would rather click than
> type.

#### Generating a key with built-in OpenSSH

In PowerShell:

```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

Paste the output of the second command into your NCShare profile.

> **Warning:** That is the `.pub` public key; the file without `.pub` is your
> private key and never leaves your machine.

#### Using Bitvise instead

1. Install from [bitvise.com/ssh-client](https://bitvise.com/ssh-client) and
   open it.
2. On the **Login** tab set Host `login.ncshare.org`, Port `22`, your NCShare
   username, and Initial method `publickey`.
3. Open **Client key manager**. Either **Generate New** (Ed25519), or
   **Import** an existing key you already created with `ssh-keygen`.
4. Export the **public** key and paste it into your NCShare profile.
5. Save the profile so you do not retype any of this, then click **Log in**.

Two panes open: a terminal, and an SFTP window for dragging files between
your laptop and NCShare. Both are useful later in the course — the SFTP pane
makes the difference between `/hpc/home`, `/work`, and `/scratch` easy to see,
and the port-forwarding tab is one route to a browser-based notebook.

#### Check it worked

Whichever client you chose, you should be able to reach a login node and run:

```bash
hostname -A
exit
```

If you cannot connect, bring the exact error message to the workshop rather
than retrying blindly. The most common causes are:

- pasting the private key instead of the `.pub`,
- a username typo, or
- the key not yet being registered.

### 2c. No-install alternative: Open OnDemand

If you cannot install software on your machine — a managed institutional
laptop, for example — you can reach NCShare through Open OnDemand in a
browser instead. You will still need an account and a registered SSH key, but
no local client. Bring your laptop either way; we will have people on hand at
check-in for both paths.

---

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

> **Note:** `apptainer --version` should report **1.1 or newer**. The GPU
> exercise relies on `--nv`, which older releases handle differently. Run this
> on an NCShare login node, not on your laptop — Apptainer is provided by the
> cluster.

> **Warning:** Do not download or build the multi-gigabyte SIF individually
> unless the instructor explicitly assigns the container-building exercise.

---

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

---

## 5. Optional preparation

Review the
[Getting Started Overview](https://userguide.ncshare.org/guides/overview/) and
the [NCShare FHI-aims Apptainer example](https://userguide.ncshare.org/examples/apptainer-fhiaims/).
Bring a laptop charger.

> **Note:** No prior container, C/C++, MPI, quantum chemistry, or astrophysics
> knowledge is required.
