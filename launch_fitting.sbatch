#!/bin/bash
#SBATCH --job-name=SHAPE
#SBATCH --time=36:00:00               # Time limit in the format hr:min:sec​
#SBATCH --output=./faction/job_output_%j.log    # Output file (with job ID in the filename)​
#SBATCH --error=./faction/job_error_%j.log      # Error file (with job ID in the filename)​
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --mem=4G

NCORES=8

module purge
module load compiler mpi

namecore=$(awk 'NR=='$SLURM_ARRAY_TASK_ID' {print $1}' ./namecores.txt)

echo ""
echo "Starting SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"
echo $namecore

# If script is called with arguments, assume multi-angle mode
if [ "$#" -ge 1 ]; then
    echo "Running in multi-angle mode with angles: $@"

    par_file="$(realpath ./par/fpar)" #Global par file for all the subscans

    for angle2 in $@; do
        angle2_padded=$(printf "%03d" "$angle2")
        # DIR="${PWD}-${angle2_padded}"
        DIR="${PWD}/subscans/${angle2_padded}"

        echo "Running pshape for $namecore in $DIR"
        cd "$DIR" || continue #If can't find it, skips to next item in loop
        mpirun -n "$NCORES" pshape "${par_file}" ./modfiles/${namecore}.mod ./obsfiles/${namecore}.obs > ./logfiles/${namecore}.log
        cd - >/dev/null
    done

else
    # Single-directory mode
    echo "Running in single-directory mode"
    echo "Running pshape for $namecore"
    mpirun -n "$NCORES" pshape ./par/fpar ./modfiles/${namecore}.mod ./obsfiles/${namecore}.obs > ./logfiles/${namecore}.log
fi

echo "Done with SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"