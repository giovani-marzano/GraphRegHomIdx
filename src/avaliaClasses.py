#!/usr/bin/python3
# coding: utf-8

import os.path
import sys
import logging
import logging.config
import csv

# Acrescentando o diretorio lib ao path. Lembrando que sys.path[0] representa o
# diretório onde este script se encontra
sys.path.append(os.path.join(sys.path[0],'lib'))

import graph as gr

from collections import Counter

def aggregateSymbols(g, clsAttr, symbolAttr):
    clsSet = g.getNodeAttrValueSet(clsAttr)

    clsCounters = {c: Counter() for c in clsSet}

    for node in g.nodes():
        cls = g.getNodeAttr(node, clsAttr)
        symbol = g.getNodeAttr(node, symbolAttr)
        clsCounters[cls][symbol] += 1

    return clsCounters

def printCounters(g, symbolAttr, clsCounters):
    symbolSet = sorted(g.getNodeAttrValueSet(symbolAttr))

    for cls, counter in clsCounters.items():
        print('Class {0}:'.format(cls))
        for symb in symbolSet:
            print('    {0}:{1}'.format(symb, counter[symb]))

if __name__ == '__main__':
    g = gr.loadGraphml('teste.graphml', relationAttr='relation')

    counters = aggregateSymbols(g, 'class2', 'baseClass')
    printCounters(g, 'baseClass', counters)
