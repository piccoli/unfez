#! /usr/bin/env bash
set -e

readonly TS=20

cut() {
    local -r img=$1 r=$2 c=$3
    local i j
    for (( i = 0; i < r * TS - 1; i += TS + 1 )); do
        for (( j = 0; j < c * TS; j += TS )); do
            convert -crop ${TS}x${TS}+$j+$i "$img" "${img%.png}_$(((i / (TS + 1)) * c + (j / TS))).png"
        done
    done
}

# Extract sample characters from a1...a6.png.
readonly -a files=(a[1-6].png)
readonly -a rows=(20 17 17 20 18 17)
readonly -a cols=(6  6  6  3  5  4 )

declare i
for (( i = 0; i < ${#files[@]}; ++i )); do
    cut ${files[i]} ${rows[i]} ${cols[i]}
done

# Spaces (represented by blank images) are discarded.
identify -ping -format '%k %f\n' *_*.png  |\
               awk '$1 == 1 { print $2 }' |\
               xargs rm -f

# Remove useless edges for thinner templates.
mogrify -trim +repage *_*.png

# Eliminate duplicates.
fdupes -f -1 . | xargs rm -f

# Cluster samples by similarity.
./group.py

# We can add spaces back now in order to generate the final template index.
mkdir 24/
convert -geometry 18x18 xc:white 24/a_space.png

# Now some user intervention is needed before running join.sh, as clustering is still imperfect.
