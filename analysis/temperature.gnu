#! /usr/bin/gnuplot -persist
set terminal gif animate optimize delay 2
set output 'temperature.gif'
set border 4095
unset key
set view 71, 35, 1, 1
set isosamples 70, 70
set contour
set xlabel "absolute error difference"
set xlabel rotate parallel
set xrange [0:10]
set ylabel "scaled temperature"
set ylabel rotate parallel
set yrange [0:10]
set zlabel "probability of acceptance"
set zlabel rotate parallel
set pm3d
#set pm3d map
#i = 100
#load 'temperature_i.gnu'

do for [i=100:500] {
    set label 1 sprintf('temperature scaled by %f', i/100.) at 5,5,-1
    sp exp(-x / y * (i / 100.))
}
#i = i + 1
#if(i <= 500) reread
