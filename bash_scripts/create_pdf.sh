#!/bin/bash

# Check usage
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 output.pdf image1.jpg [image2.jpg ... imageN.jpg]"
    exit 1
fi

# Get output PDF and shift args
output_pdf="$1"
shift

# Create a temporary directory
temp_dir=$(mktemp -d)

# Set target width in pixels (e.g. 842px for A4 at 72 DPI)
target_width=842

# Resize all images to the same width, preserving aspect ratio
i=0
for img in "$@"; do
    convert "$img" -resize "${target_width}" "$temp_dir/resized_$i.jpg"
    i=$((i + 1))
done

# Stack images vertically into one long image
convert "$temp_dir"/resized_*.jpg -append "$temp_dir/combined.jpg"

# Convert the long image to a single-page PDF
convert "$temp_dir/combined.jpg" "$output_pdf"

# Clean up
rm -rf "$temp_dir"

echo "Created single-page PDF: $output_pdf"