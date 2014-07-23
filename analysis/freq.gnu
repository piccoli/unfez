#! /usr/bin/gnuplot -persist
set terminal pdfcairo color dashed
set output 'freq.pdf'
unset grid
set view 60, 30, 1, 1
set size ratio 0 1,1
set ytics autofreq
set title "Letter frequencies from a sample English text"
set xlabel "Letter"
set ylabel "Relative frequency"
set yrange [0:.13]
unset key
set boxwidth 0.1
set style fill solid
p 'freq.data' u 2:xtic(1) w boxes lc rgb '#000000'
