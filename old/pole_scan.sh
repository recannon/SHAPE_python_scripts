#!/bin/bash
#Last modified 05/06/2025

#E.G. bash path/to/pole_scan_mass.sh -90 90 10 0 360 10 mod.template obs.template angle2_list
#If multiple angle2 values given, produces the following file structure:
# PSX
# -psX < this is dir to call the script. Requires template files and par dir
# -psX-000 < creates these and runs pole scans within them
# -psX-045
# -etc
#Otherwise performs polescan in PSX/psX

set -euo pipefail

# === Function to run the Python script ===
run_make_batch() {
    local run_dir=$1
    local angle2=$2

    echo "Running for angle2=$angle2 in $run_dir"

    mkdir -p "$run_dir"/{modfiles,obsfiles,logfiles,waction/logs}

    cd "$run_dir"
    python "${SCRIPT_DIR}/pyshape/make_batch_shape_mod.py" \
        "$BET_MIN" "$BET_MAX" "$BET_STEP" \
        "$LAM_MIN" "$LAM_MAX" "$LAM_STEP" \
        "--angle-2" "$angle2" \
        "--mod-template" "$MOD_TEMPLATE" \
        "--obs-template" "$OBS_TEMPLATE"
    
    cd "$WORKING_DIR"
}

# === Function to check number of jobs ===
file_count=""
check_number_of_jobs() {
    local namecores_path=$1

    if [ ! -f "$namecores_path" ]; then
        echo "Error: namecores.txt not found at $namecores_path"
        exit 1
    fi

    file_count=$(wc -l < "$namecores_path")

    local confirm
    echo "This will submit $file_count SLURM job(s)."
    read -r -p "Do you want to continue? [y/N] " confirm
    if [[ "$confirm" != [yY] && "$confirm" != [yY][eE][sS] ]]; then
        echo "Aborting SLURM job submission."
        exit 0
    fi
}

# === Default values ===
USE_STEPS=false
STEP_SIZE=0
POSITIONAL_ARGS=()

# === Parse long options ===
while [[ $# -gt 0 ]]; do
    case "$1" in
        --steps|-s)
            if [[ -z "${2:-}" || "$2" == -* ]]; then
                echo "Error: --steps requires a numeric argument" >&2
                exit 1
            fi
            USE_STEPS=true
            STEP_SIZE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--steps N] -- bet-min bet-max bet-step lam-min lam-max lam-step mod-template obs-template angle2..."
            echo "Use '--' before positional args to allow negatives like -90."
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            # Assume start of positional args if no `--` is used
            break
            ;;
    esac
done

# === Collect positional arguments ===
POSITIONAL_ARGS+=("$@")

# === Validate number of positional arguments ===
if $USE_STEPS; then
    if [ "${#POSITIONAL_ARGS[@]}" -lt 8 ]; then
        echo "Error: When using --steps, you must provide at least 8 positional arguments:"
        echo "  bet-min bet-max bet-step lam-min lam-max lam-step mod-template obs-template"
        exit 1
    fi
else
    if [ "${#POSITIONAL_ARGS[@]}" -lt 9 ]; then
        echo "Error: When not using --steps, you must provide at least 9 positional arguments:"
        echo "  bet-min bet-max bet-step lam-min lam-max lam-step mod-template obs-template angle2 [angle2...]"
        exit 1
    fi
fi

# === Script and working directories ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKING_DIR="$(pwd)"

# === Extract fixed positional arguments ===
BET_MIN=${POSITIONAL_ARGS[0]}
BET_MAX=${POSITIONAL_ARGS[1]}
BET_STEP=${POSITIONAL_ARGS[2]}
LAM_MIN=${POSITIONAL_ARGS[3]}
LAM_MAX=${POSITIONAL_ARGS[4]}
LAM_STEP=${POSITIONAL_ARGS[5]}
MOD_TEMPLATE=${POSITIONAL_ARGS[6]}
OBS_TEMPLATE=${POSITIONAL_ARGS[7]}
shift 8
ANGLE2_VALUES=("${POSITIONAL_ARGS[@]:8}")

# === Generate angle2 values if --steps was set ===
if $USE_STEPS; then
    ANGLE2_VALUES=()
    for ((a=0; a<360; a+=STEP_SIZE)); do
        ANGLE2_VALUES+=("$a")
    done
fi

# === Check par and template files exist ===
if [ ! -d "${WORKING_DIR}/par" ]; then
    echo "Error: par directory not found in ${WORKING_DIR}" >&2
    exit 1
fi
for file in "$MOD_TEMPLATE" "$OBS_TEMPLATE"; do
    if [ ! -f "${WORKING_DIR}/$file" ]; then
        echo "Error: $file not found in ${WORKING_DIR}" >&2
        exit 1
    fi
done

# === Run loop ===
if [ "${#ANGLE2_VALUES[@]}" -eq 1 ]; then
    run_make_batch "$WORKING_DIR" "${ANGLE2_VALUES[0]}"
else
    for angle2 in "${ANGLE2_VALUES[@]}"; do
        angle2_padded=$(printf "%03d" "$angle2")
        mkdir "${WORKING_DIR}-${angle2_padded}"
        cp -r "${WORKING_DIR}/par" "${WORKING_DIR}-${angle2_padded}"
        cp "${WORKING_DIR}/${MOD_TEMPLATE}" "${WORKING_DIR}/${OBS_TEMPLATE}" "${WORKING_DIR}-${angle2_padded}/"
        run_make_batch "${WORKING_DIR}-${angle2_padded}" "$angle2"
    done
fi

# === Run slurm scripts after check ===
cd "$WORKING_DIR"
if [ "${#ANGLE2_VALUES[@]}" -eq 1 ]; then
    # Single case – launch fitting directly
    check_number_of_jobs "${WORKING_DIR}/namecores.txt"
    sbatch --array=1-"$file_count" "${SCRIPT_DIR}/launch_fitting.sbatch"
else
    first_angle2="${ANGLE2_VALUES[0]}"
    angle2_padded=$(printf "%03d" "$first_angle2")
    check_number_of_jobs "${WORKING_DIR}-${angle2_padded}/namecores.txt"
    sbatch --array=1-"$file_count" "${SCRIPT_DIR}/launch_fitting.sbatch" "${ANGLE2_VALUES[@]}"
fi