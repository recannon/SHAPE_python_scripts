#Written by Richard Cannon 02/07/2024
# ConvInvSol_mkvertmod.sh [Command][NoVertices/NoHarmonics] [Basis/NoTheta]

#Define root file
root_dir=$PWD

# Define modfiles and obsfiles in lists
modfiles_list=($(ls "$root_dir/"modfiles))

cd modfiles

# Get the length of the lists
len=${#modfiles_list[@]}

# Loop through the lists using index
for (( i=0; i<$len; i++ )); do
    echo $i
    mod=${modfiles_list[$i]}

    $1 $mod $mod $2 $3

    done;