#! /usr/bin/gnuplot -persist
set terminal fig color pointsmax 1000 landscape inches solid font "Helvetica,10" linewidth 1 depth 10 version 3.2
#set output 'sym.fig'
unset grid
set view 60, 30, 1, 1
set size ratio 0 1,1
set title "FEZ Symbol frequencies from a sample dialog."
set xlabel "Symbol" offset 0,-2.5
set ylabel "Relative Frequency"
set yrange [0:0.2] noreverse nowriteback
unset key
set boxwidth 0.1
set style fill solid
p 'sym.data' u 2:xtic(1) w boxes lc rgb '#000000'
