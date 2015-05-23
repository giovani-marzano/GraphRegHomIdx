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

#---------------------------------------------------------------------
# Variaveis globais de configuração
#---------------------------------------------------------------------

# Configurações para controlar a geração de log pelo script
ARQ_LOG = 'simTempera.log'
LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'brief': {
            'format': '%(message)s'
        },
        'detail': {
            'format': '%(asctime)s|%(levelname)s:%(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'brief'
        },
        'arquivo': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detail',
            'filename': ARQ_LOG,
            'mode': 'w'
        }
    },
    'root': {
        'handlers': ['console', 'arquivo'],
        'level': 'DEBUG'
    }
}
logging.config.dictConfig(LOG_CONFIG)

CSV_OUT_CONFIG = {
    'delimiter': '\t',
    'lineterminator': '\n',
    'quotechar': '"',
    'escapechar': '\\',
    'doublequote': False,
    'quoting': csv.QUOTE_NONNUMERIC,
    'skipinitialspace': True
}
CSV_OUT_DIALECT='appcsvdialect'
csv.register_dialect(CSV_OUT_DIALECT, **CSV_OUT_CONFIG)

import math
import random
import itertools

import graph as gr

logger = logging.getLogger(__name__)

# Constantes para direção da aresta
IN = 0
OUT = 1

def normalizeVet(vet):
    """Normaliza o vetor fornecido, aterando-o.
    """
    s = math.sqrt(sum(map(lambda v: v**2, vet)))

    if s > 0:
        for i,v in enumerate(vet):
            vet[i] = v/s

    return vet

def vetDotProduct(v1, v2):
    return sum(map(lambda x: x[0]*x[1], zip(v1,v2)))

def createPatternToIdx(g, k):
    # Criando mapa de padrao de conexao para indice no vetor de padrao
    # Número de relações * 2 (entrada e saida) * número de classes (k)
    iterPatt = itertools.product(g.relations,(IN,OUT),range(k))
    return {p:i for i, p in enumerate(iterPatt)}

class SimTempora(object):
    def __init__(self, g, k, maxTime, iniTemp=1, endTemp=0, iniTime=0,
            endTime=None, refClassAttr=None):
        self.g = g
        self.k = k
        self.maxTime = maxTime
        self.iniTemp = iniTemp
        self.iniTime = iniTime
        self.endTemp = endTemp
        self.endTime = endTime or maxTime
        self.temp = self.calcTemperature(0)

        self.bestEnergy = float('inf')
        self.bestNodeCls = None

        if refClassAttr:
            refClassSet = g.getNodeAttrValueSet(refClassAttr)
            numClassRef = len(refClassSet)
            refClassToClass = {r:c for c,r in enumerate(refClassSet)}
            def nodeRefClassF(nodeClass, node):
                return refClassToClass[g.getNodeAttr(node, refClassAttr)]
        else:
            numClassRef = k
            def nodeRefClassF(nodeClass, node):
                return nodeClass[node]

        self.nodeRefClassF = nodeRefClassF

        self.patternToIdx = createPatternToIdx(g,numClassRef)

        self.clsPatterns = []
        for cls in range(k):
            pattVet = [0.0 for _ in self.patternToIdx]
            self.clsPatterns.append(pattVet)

    def calcRI(self, nodeCls):
        stats = gr.fullMorphismStats(self.g,
                lambda n: nodeCls[n], lambda e: e[2])
        edgeStats = gr.calcPreRegIdxStats(*stats)
        graphRI = gr.calcGraphRegIdx(edgeStats)
        ri = graphRI.ri
        return ri

    def _calcRawClassPatterns(self, nodeCls):
        for vet in self.clsPatterns:
            for i in range(len(vet)):
                vet[i] = 0.0

        nodeCount = [0 for c in self.clsPatterns]

        for node in self.g.nodes():
            cls = nodeCls[node]
            nodeCount[cls] += 1

            for tgt, rel in self.g.outNeighboors(node):
                tgtClass = self.nodeRefClassF(nodeCls, tgt)
                pat = (rel, OUT, tgtClass)
                idx = self.patternToIdx[pat]
                self.clsPatterns[cls][idx] += 1

            for src, rel in self.g.inNeighboors(node):
                srcClass = self.nodeRefClassF(nodeCls, src)
                pat = (rel, IN, srcClass)
                idx = self.patternToIdx[pat]
                self.clsPatterns[cls][idx] += 1

        for cls, vet in enumerate(self.clsPatterns):
            if nodeCount[cls] > 0:
                for i, v in enumerate(vet):
                    vet[i] = v/nodeCount[cls]

    def actualizeClassPatterns(self, nodeCls):
        self._calcRawClassPatterns(nodeCls)

        for vet in self.clsPatterns:
            self._processRawPatternVet(vet)

    def _processRawPatternVet(self, vet):
        """Um vetor de padrão de conexão bruto possui componentes variando de 0
        a um. Este metodo processa o vetor primeiro colocando as componentes no
        intervalo de -1 a 1 e depois normalizando o vetor.
        """

        for i,v in enumerate(vet):
            vet[i] = 2*v - 1

        normalizeVet(vet)

    def getNodeBestClassMatch(self, node, nodeCls):
        vet, hasEdge = self.getNodePattern(node, nodeCls)
        self._processRawPatternVet(vet)

        bestCls = nodeCls[node]
        bestSim = float('-inf')
        oldSim = 0
        for cls, pat in enumerate(self.clsPatterns):
            sim = vetDotProduct(vet, pat)
            if cls == nodeCls[node]:
                oldSim = sim
            elif sim > bestSim:
                bestSim = sim
                bestCls = cls

        # A energia total do sistema será medida como a diferença entre a
        # similaridade máxima esperada (1) e a média das similaridades de cada
        # nodo do grafo. Sendo assim a diferença de energia causada pela mudança
        # deste classe deste nodo consegue-se assim:
        #   E_total = Sum_i{ 1 - s_i }
        #           = Sum_i{1} - Sum_i{s_i}
        #           = N - Sum_i{ s_i }
        # Para atualizar a energia total com base na modificação da classe de um
        # nodo k devemos retirar a contribuição que o nodo k dava e acrescentar
        # a que ele passa a dar:
        #   E_total[t+1] = Etotal[t] + s_k[t] - s_k[t+1]
        # O delta de energia é a energia nova menos a anterior:
        #   deltaE = E_total[t+1] - Etotal[t]
        #          = E_total[t] + s_k[t] - s_k[t+1] - E_total[t]
        #          = s_k[t] - s_k[t+1]
        deltaE = oldSim - bestSim

        return bestCls, deltaE

    def _calcTotalEnergy(self, nodeCls):

        totalE = self.g.getNumNodes()

        for node, vet, hasEdge in self._genNodesPatterns(nodeCls):
            self._processRawPatternVet(vet)
            cls = nodeCls[node]
            clsVet = self.clsPatterns[cls]
            sim = vetDotProduct(vet, clsVet)
            totalE -= sim

        return totalE

    def search(self):
        nodeCls = {}
        for node in g.nodes():
            nodeCls[node] = random.randrange(self.k)
        nodes = list(g.nodes())

        self.actualizeClassPatterns(nodeCls)
        totalE = self._calcTotalEnergy(nodeCls)
        self.setBest(nodeCls, totalE)

        logger.info('Iniciando %f', totalE)

        for time in range(self.maxTime):
            random.shuffle(nodes)
            temp = self.calcTemperature(time)
            changed = False
            for node in nodes:
                bestChangeCls, delta = self.getNodeBestClassMatch(node, nodeCls)

                if self.doMove(temp, delta):
                    nodeCls[node] = bestChangeCls
                    changed = True
                    self.actualizeClassPatterns(nodeCls)
                    totalE += delta
                    self.setBest(nodeCls, totalE)

                logger.info('%d %f %f %f', time, temp, totalE, delta)

            if not changed and temp == 0:
                break

    def getNodePattern(self, node, nodeClass):
        myClass = nodeClass[node]
        hasEdge = False
        vet = [0.0 for _ in self.patternToIdx]

        pattValues = {}
        for nei, rel in self.g.outNeighboors(node):
            hasEdge = True
            neiClass = self.nodeRefClassF(nodeClass, nei)
            pat = (rel, OUT, neiClass)
            pattValues[pat] = 1

        for nei, rel in self.g.inNeighboors(node):
            hasEdge = True
            neiClass = self.nodeRefClassF(nodeClass, nei)
            pat = (rel, IN, neiClass)
            pattValues[pat] = 1

        for pat, v in pattValues.items():
            idx = self.patternToIdx[pat]
            vet[idx] = max(vet[idx], v)

        return vet, hasEdge

    def _genNodesPatterns(self, nodeClass):
        for node in nodeClass.keys():
            vet, hasEdge = self.getNodePattern(node, nodeClass)

            yield (node, vet, hasEdge)

    def setBest(self, nodeCls, totalE):
        if totalE <= self.bestEnergy:
            self.bestNodeCls = dict(nodeCls)
            self.bestEnergy = totalE

    def calcTemperature(self, time):
        if time <= self.iniTime:
            temp = self.iniTemp
        elif time >= self.endTime:
            temp = self.endTemp
        else:
            a = (self.endTemp - self.iniTemp)
            a = a/(self.endTime - self.iniTime)
            temp = self.iniTemp + a*(time-self.iniTime)
        return temp

    def calcMoveProbability(self, temp, deltaE):
        if deltaE <= 0:
            prob = 1.0
        elif temp > 0:
            prob = math.exp(-deltaE/temp)
        else:
            prob = 0.0

        return prob

    def doMove(self, temp, deltaRI):
        prob = self.calcMoveProbability(temp, deltaRI)
        return random.random() < prob

if __name__ == '__main__':
    g = gr.loadGraphml('teste.graphml', relationAttr='relation')

    sim = SimTempora(g, 7, 15,
        iniTemp=0.2, endTemp=0.0,
        iniTime=0, endTime=10, refClassAttr='regCls_1')

    sim.search()

    with open('teste.csv', 'w', newline='') as f:
        writer = csv.writer(f, CSV_OUT_DIALECT)
        row = ['node','class']
        writer.writerow(row)
        for n,c in sim.bestNodeCls.items():
            row = [n,c]
            writer.writerow(row)

    logging.shutdown()
