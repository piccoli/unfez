#! /usr/bin/gawk -bf
# freq.awk: Count relative letter frequency from a sample input text
BEGIN { RS = "[^[:alpha:]]+"; PROCINFO["sorted_in"] = "@val_num_asc" }

{
    n = split(tolower($0), v, //)
    for(i = 1; i <= n; ++i) {
        ++t
        ++a[v[i]]
    }
}

END {
    for(x in a) a[x] /= t
    for(x in a) print x, a[x]
}
