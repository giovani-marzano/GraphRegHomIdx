import sys
import itertools
import os

dataDir = 'data'
#filePrefix='circulosVet'
filePrefix='seedsVet'
numNodes=8
listaAtribs = [1,2,3,4,5,6,7]
#listaAtribs = [1,2]

imgDir = 'img'

fout = sys.stdout

fout.write("set terminal svg size 800,550\n")
fout.write("set key off\n")
#fout.write("set xrange [-2:4]\n")
#fout.write("set yrange [-2:4]\n")

params = {'prefix': filePrefix, 'fimIdx': numNodes - 1,
    'dataFilePre': os.path.join(dataDir, filePrefix),
    'imgFilePre': os.path.join(imgDir, filePrefix)}
for (a1,a2) in itertools.combinations(listaAtribs,2):
    params['a1'] = a1
    params['a2'] = a2
    fout.write("set output '")
    fout.write("{imgFilePre}_{a1}_{a2}.svg'\n".format(**params))
    fout.write("plot ")
    fout.write(
        "for [i=0:{fimIdx}] '{dataFilePre}Res.txt' index i u {a1}:{a2} w p ".format(
            **params))
    fout.write(", '{dataFilePre}Nodes.txt' u {a1}:{a2} w lp lc 'black' pt 7 ".format(
        **params))
    fout.write("\n")
    fout.write("\n")
