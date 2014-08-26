import sys
import itertools

filePrefix='seedsVet'
numNodes=6
#listaAtribs = [1,2,3,4,5,6,7]
listaAtribs = [1,2]

imgDir = './img'

fout = sys.stdout

fout.write("set terminal svg size 800,600\n")
fout.write("set key off\n")

params = {'prefix': filePrefix, 'fimIdx': numNodes - 1}
for (a1,a2) in itertools.combinations(listaAtribs,2):
    params['a1'] = a1
    params['a2'] = a2
    fout.write("set output '")
    fout.write(imgDir+'/')
    fout.write("{prefix}_{a1}_{a2}.svg'\n".format(**params))
    fout.write("plot ")
    fout.write(
        "for [i=0:{fimIdx}] '{prefix}Res.txt' index i u {a1}:{a2} w p ".format(
            **params))
    fout.write(", '{prefix}Nodes.txt' u {a1}:{a2} w lp lt 1 pt 7 ps 2 ".format(
        **params))
    fout.write("\n")
    fout.write("\n")
