#!/usr/bin/python3
# coding: utf-8

import os.path
import sys

# Acrescentando o diretorio lib ao path. Lembrando que sys.path[0] representa o
# diretório onde este script se encontra
sys.path.append(os.path.join(sys.path[0],'lib'))

import graph as gr
import random

if __name__ == '__main__':
    
    g = gr.loadGraphml('ctrl1k.graphml', relationAttr='relation')


    print('edges: {0}, nodes {1}', g.getNumEdges(), g.getNumNodes())
    
    numEdges = g.getNumEdges()
    edges = list(g.edges())
    for i in range(round(len(edges)*0.1)):
        e = random.choice(edges)
        g.removeEdge(*e)
        edges.remove(e)

    print('edges: {0}, nodes {1}', g.getNumEdges(), g.getNumNodes())

    nodes = list(g.nodes())
    while g.getNumEdges() < numEdges:
        n1 = random.choice(nodes)
        n2 = random.choice(nodes)
        g.addEdge(n1,n2,0)
        g.setEdgeAttr((n1,n2,0),'relation',0)

    print('edges: {0}, nodes {1}', g.getNumEdges(), g.getNumNodes())

    g.writeGraphml('ctrl1k_randomized.graphml')
