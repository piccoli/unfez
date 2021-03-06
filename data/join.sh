#! /usr/bin/env bash
readonly INDEXFILE=sym.index
readonly TILESIZE=18x18

set -e
shopt -s nullglob

join() {
    local -r cols=$1 rows=$2 output=$3
    shift 3
    montage $@ -mode Concatenate -tile ${cols}x$rows ${output}.png
}

declare -A tiles
for i in $(find . -mindepth 1 -type d -iname '[0-9]*'); do
    d=$(basename $i)
    a=($d/*)
    n=${#a[@]}
    tiles[$d]=$n
    if (( n > 0 )); then
        join $n "" $d ${a[@]}
    else
        convert -geometry $TILESIZE xc:white ${d}.png
    fi
done

echo -n "${tiles[0]}" > $INDEXFILE
for (( i = 1; i < 25; ++i )); do
    echo -n " ${tiles[$i]}"
done >> $INDEXFILE

shopt -u nullglob

a=($(ls -1 [0-9]*.png | sort -n))
n=${#a[@]}
join "" $n sym ${a[@]}
rm -f ${a[@]}
