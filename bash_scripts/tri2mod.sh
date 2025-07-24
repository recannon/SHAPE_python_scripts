#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check input
if [ $# -ne 2 ]; then
    echo "Usage: $0 input.tri output.mod"
    exit 1
fi

input_file="$1"
temp_obj="temp.obj"
temp_fac="temp.fac"
placeholder_mod="${SCRIPT_DIR}/example.mod"
output_file="$2"

# Read counts
read -r num_v num_f < "$input_file"

# Create temporary files
tmp_vertices=$(mktemp)
tmp_faces=$(mktemp)

# Extract vertex and face lines
tail -n +2 "$input_file" | head -n "$num_v" > "$tmp_vertices"
tail -n +"$((num_v + 2))" "$input_file" > "$tmp_faces"

while read -r x y z; do
    echo "v $x $y $z" >> "$temp_obj"
done < "$tmp_vertices"

while read -r i j k; do
    echo "f $((i)) $((j)) $((k))" >> "$temp_obj"
done < "$tmp_faces"

# Cleanup
rm "$tmp_vertices" "$tmp_faces"

wf2fac $temp_obj $temp_fac e
fac2mod $placeholder_mod $temp_fac $output_file

echo "Converted $input_file -> $output_file"

rm $temp_obj $temp_fac