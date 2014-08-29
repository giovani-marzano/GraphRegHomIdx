# coding: utf-8

import gv
import graphHom
import os

ClusterColors = {
    1: '#ff0000',
    2: '#00ff00',
    3: '#0000ff',
    4: '#ffff00',
    5: '#00ffff',
    6: '#ff00ff',
    7: '#739276',
    8: '#000000',
}

data_dir = "data"

def geraGrafoExemplo():

    V = {1,2,3,4,5,6,7,8}
    V_Clust = {1:1,2:2,3:3,4:2,5:1,6:2,7:3,8:1}
    # arestas: (src, tgt, cluster)
    E = {(1,6,2),(1,4,2)
         ,(2,1,1),(2,3,1),(2,4,2)
         ,(4,5,2),(4,8,1)
         ,(5,2,2),(5,3,2)
         ,(6,1,1),(6,4,2),(6,8,2)
         ,(7,4,1)
         ,(8,7,2)
        }

    def src(e):
        return e[0]

    def tgt(e):
        return e[1]

    def clusterE(e):
        return e[2]

    def clusterV(v):
        return V_Clust[v]

    G = (V, E, src, tgt)

    return (G, clusterV, clusterE)

def writeDotFile(G, clusterV, clusterE, fileName):
    (V, E, src, tgt) = G

    gh = gv.digraph(fileName)

    vh = gv.protonode(gh)
    gv.setv(vh, 'shape', 'circle')
    gv.setv(vh, 'style', 'filled')

    for e in E:
        eh = gv.edge(gh, str(src(e)), str(tgt(e)))
        gv.setv(eh, 'color', ClusterColors[clusterE(e)])

    for v in V:
        vh = gv.findnode(gh, str(v))
        gv.setv(vh, 'fillcolor', ClusterColors[clusterV(v)])

    gv.write(gh, os.path.join(data_dir,fileName+'.dot'))


(G, clusterV, clusterE) = geraGrafoExemplo()
writeDotFile(G, clusterV, clusterE, 'grafoExemplo')
(GIm, mapEdgIm, clusterEIm) = graphHom.createImageEdges(G, clusterV, clusterE)
writeDotFile(GIm, clusterV, clusterEIm, 'grafoClusExemplo')
