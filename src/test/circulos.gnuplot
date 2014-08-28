
set key off

set xrange [-3:3]
set yrange [-3:3]

#plot for [i=0:7] 'data/circulosRes.txt' index i u 1:2 \
#, 'data/circulosNodes.txt' u 1:2 w linesp lt 1 pointsize 2
#
#pause -1

plot for [i=0:7] 'data/circulosVetRes.txt' index i u 1:2 w points \
, 'data/circulosVetNodes.txt' u 1:2 w linesp lt 1 pt 5 pointsize 2

pause -1
