#! /usr/bin/gawk -f
#NR == 10 { print "0 32 #808080" }

/^2 / && int($5) == 4 { $5 = $6 = 0 }

# Fix gnuplot/xfig output to include symbols as xtics labels.
/^4 / && /\.png/ {
    name = $14
    x    = $12
    y    = $13
    gsub(/\\001/, "", name)
    print "2 5 0 1 0 -1 50 -1 -1 0.000 0 0 -1 0 0 5"
    print "\t" 0, name
    print "\t " x - 117, y - 117, x + 118, y - 117, x + 118, y + 118, x - 117, y + 118, x - 117, y - 117
    next
}

/^4 / { $3 = 0 }

{ print }
