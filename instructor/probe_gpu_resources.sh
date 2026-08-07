#!/usr/bin/env bash
# probe_gpu_resources.sh -- find the partition and --gres string this cluster
# actually accepts, without needing a container image.
#
#   bash instructor/probe_gpu_resources.sh              # read-only, safe
#   bash instructor/probe_gpu_resources.sh --submit     # also runs one tiny job
#
# Why not just use the course .sbatch? Because it would fail for reasons that
# have nothing to do with gres: it points at a container image that may not be
# built, and at an --output directory that may not exist (Slurm rejects a job
# whose output directory is missing, before it ever looks at your gres string).
# A failure there tells you nothing. This script isolates one question.
#
# Deliberately does NOT use `set -e`: several commands below are *expected* to
# fail, and the whole point is to report which ones did.

set -uo pipefail

CANDIDATE_PARTITIONS=(workshop gpu interactive-gpu)
CANDIDATE_GRES=(gpu:h200:1 gpu:1 gpu:H200:1 gpu:h200_141gb:1)
DO_SUBMIT=0
[[ "${1:-}" == "--submit" ]] && DO_SUBMIT=1

hr() { printf '%s\n' "------------------------------------------------------------"; }

if ! command -v sinfo >/dev/null 2>&1; then
  echo "ERROR: sinfo not found. Run this on an NCShare login node." >&2
  exit 2
fi

# Run this from a LOGIN node, not from inside salloc/srun. Everything here is a
# scheduler query, so it belongs on the login node -- but more importantly,
# sbatch propagates the submitting environment by default. Inside an existing
# allocation, SLURM_* variables from the parent job (SLURM_CPUS_PER_TASK,
# SLURM_JOB_GRES, ...) leak into the probe and can mask the very values being
# tested. Some sites also restrict nested submission outright.
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  echo
  echo "WARNING: you appear to be inside allocation ${SLURM_JOB_ID}."
  echo "         Parent SLURM_* variables can contaminate these results."
  echo "         Exit the allocation (or open a second session) and re-run"
  echo "         from a login node."
  echo
  read -r -p "         Continue anyway? [y/N] " reply
  [[ "${reply,,}" == "y" ]] || exit 3
fi

# ---------------------------------------------------------------------------
# 1. Ask Slurm directly. This answers the question with no submission at all.
# ---------------------------------------------------------------------------
hr; echo "1. CONFIGURED PARTITIONS AND GRES"; hr
echo "-- sinfo: partition / gres / nodes / cpus --"
sinfo -o "%20P %30G %12N %5c %8m" 2>&1 | head -40

echo
echo "-- GPU-capable nodes and their exact Gres= string --"
# The Gres= line in `scontrol show node` is authoritative: it is the string
# Slurm parses your --gres against.
# -N gives one node per line, so no compressed "node-[01-04]" ranges to expand.
for n in $(sinfo -hN -o "%N" 2>/dev/null | sort -u | head -20); do
  g=$(scontrol show node "$n" 2>/dev/null | grep -oE 'Gres=[^ ]+' | head -1)
  [[ -n "$g" && "$g" != "Gres=(null)" ]] && printf '  %-22s %s\n' "$n" "$g"
done

echo
echo "-- partitions that advertise a GRES --"
sinfo -h -o "%P|%G" 2>/dev/null | awk -F'|' '$2 != "(null)" && $2 != "" {print "  " $0}' | sort -u

# ---------------------------------------------------------------------------
# 2. Validate candidates WITHOUT queueing anything.
#    `sbatch --test-only` runs the full submission check -- partition exists,
#    gres parses, limits allow it -- then discards the job.
# ---------------------------------------------------------------------------
hr; echo "2. VALIDATING COMBINATIONS (--test-only, nothing is queued)"; hr
printf '%-18s %-22s %s\n' "PARTITION" "GRES" "RESULT"
ACCEPTED=()
for p in "${CANDIDATE_PARTITIONS[@]}"; do
  for g in "${CANDIDATE_GRES[@]}"; do
    out=$(sbatch --test-only \
            --partition="$p" --gres="$g" \
            --cpus-per-task=4 --mem=4G --time=00:05:00 \
            --wrap="true" 2>&1)
    if [[ $? -eq 0 ]]; then
      printf '%-18s %-22s %s\n' "$p" "$g" "ACCEPTED"
      ACCEPTED+=("$p|$g")
    else
      reason=$(echo "$out" | tr '\n' ' ' | sed -E 's/.*error: ?//' | cut -c1-60)
      printf '%-18s %-22s %s\n' "$p" "$g" "rejected: ${reason:-unknown}"
    fi
  done
done

# ---------------------------------------------------------------------------
# 3. Report
# ---------------------------------------------------------------------------
hr; echo "3. RESULT"; hr
if [[ ${#ACCEPTED[@]} -eq 0 ]]; then
  echo "No candidate combination was accepted."
  echo "Read section 1 above -- the exact Gres= strings are printed there,"
  echo "and the right value is almost certainly one of them."
  exit 1
fi

echo "Working combinations:"
for a in "${ACCEPTED[@]}"; do
  echo "    --partition=${a%%|*}  --gres=${a##*|}"
done
BEST_P="${ACCEPTED[0]%%|*}"; BEST_G="${ACCEPTED[0]##*|}"
echo
echo "Put these in tutorials/04-gpu-quantui/slurm/quantui_gpu.sbatch:"
echo "    #SBATCH --partition=$BEST_P"
echo "    #SBATCH --gres=$BEST_G"

# --test-only proves the scheduler ACCEPTS the request. It does not prove a
# GPU actually appears in the job. Only a real job does that.
if [[ $DO_SUBMIT -eq 1 ]]; then
  hr; echo "4. SUBMITTING ONE REAL JOB (~seconds)"; hr
  log="gres-probe-%j.out"
  jid=$(sbatch --parsable \
          --job-name=gres-probe \
          --partition="$BEST_P" --gres="$BEST_G" \
          --cpus-per-task=4 --mem=4G --time=00:05:00 \
          --output="$log" \
          --wrap='echo "node=$(hostname)"; echo "gres=${SLURM_JOB_GRES:-unset}"; echo "cpus=${SLURM_CPUS_PER_TASK:-unset}"; echo "affinity=$(taskset -cp $$ 2>/dev/null || echo n/a)"; nvidia-smi -L; nvidia-smi --query-gpu=name,driver_version,compute_cap,mig.mode.current --format=csv' \
          2>&1)
  if [[ "$jid" =~ ^[0-9]+$ ]]; then
    echo "Submitted job $jid. Watch it with:"
    echo "    squeue -j $jid"
    echo "Then read the output:"
    echo "    cat gres-probe-$jid.out"
    echo
    echo "That output answers the remaining open questions at once:"
    echo "  - nvidia-smi -L          -> whether MIG is on (slices vs whole GPUs)"
    echo "  - driver_version         -> confirms 580.126.20"
    echo "  - compute_cap            -> confirms 9.0"
    echo "  - affinity               -> whether Slurm uses a cpuset or a quota"
  else
    echo "Submission failed: $jid"
    exit 1
  fi
else
  echo
  echo "Re-run with --submit to queue one tiny job that also reports MIG mode,"
  echo "driver version, compute capability, and the CPU affinity mask."
fi
