#!/usr/bin/python3
# coding: utf-8

import os.path
import sys

# Acrescentando o diretorio lib ao path. Lembrando que sys.path[0] representa o
# diretório onde este script se encontra
sys.path.append(os.path.join(sys.path[0],'lib'))

import graph as gr
import random

def randomizeEdges(gname, ePerc, relationAttr='relation'):
    """
    gname: Nome do arquivo que possui o grafo sem extensão.
    ePerc: Porcentagem do número de arestas a serem randomizadas.
    """
    g = gr.loadGraphml('{0}.graphml'.format(gname), relationAttr=relationAttr)

    print('edges: {0}, nodes {1}'.format(g.getNumEdges(), g.getNumNodes()))
    
    numEdges = g.getNumEdges()
    edges = list(g.edges())
    for i in range(round(len(edges)*ePerc)):
        e = random.choice(edges)
        g.removeEdge(*e)
        edges.remove(e)

    print('edges: {0}, nodes {1}'.format(g.getNumEdges(), g.getNumNodes()))

    nodes = list(g.nodes())
    while g.getNumEdges() < numEdges:
        n1 = random.choice(nodes)
        n2 = random.choice(nodes)
        g.addEdge(n1,n2,0)
        g.setEdgeAttr((n1,n2,0),'relation',0)

    print('edges: {0}, nodes {1}'.format(g.getNumEdges(), g.getNumNodes()))

    g.writeGraphml('{0}_rand_{1:02d}%.graphml'.format(gname,round(100*ePerc)))

def randomizeClass(gname, clasAttr, nClasses, relationAttr='relation'):
    g = gr.loadGraphml('{0}.graphml'.format(gname), relationAttr=relationAttr)

    with open('{0}_{1}.csv'.format(gname,clasAttr), 'w') as f:
        f.write('node\t{0}\n'.format(clasAttr))
        for node in g.nodes():
            c = random.randrange(nClasses)
            f.write('{0}\t{1}\n'.format(node, c))

if __name__ == '__main__':
    #randomizeEdges('ctr1k', 0.1)
    randomizeClass('ctr1k', 'randClass', 5)
