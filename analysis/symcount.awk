#! /usr/bin/gawk -f
BEGIN { RS = "[^[:digit:]]+"; PROCINFO["sorted_in"] = "@val_num_asc" }

{ ++t[$0]; ++n }

END {
    for(x in t) t[x] /= n
    for(x in t) print "../data/avg/" x ".png", t[x]
}
