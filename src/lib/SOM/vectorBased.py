# coding: utf-8
"""Implementação de um SOM baseao do vetores, ou seja, os elementos apresentados
ao SOM são pontos em um espaço n dimensional. A distância entre os elementos é a
distância euclidiana entre os pontos.
"""

from __future__ import print_function

__author__ = "Giovani Melo Marzano"

from . import Config, AbstractSOMap, AbstractSOMNode
import graph as gr
import math
import sys

if sys.version_info.major < 3:
    from future_builtins import zip

def euclidDistSq(a, b):
    """Distancia euclidiana ao quadrado de dois vetores.
    """

    return sum((pow(ax-bx,2) for ax,bx in zip(a,b)))

class SOMNode(AbstractSOMNode):
    """Representa um nodo do SOM.
    """

    def __init__(self, nid, refElem, conf):
        """Inicializa a instancia.

        :param nid: Identificador do nodo.
        :param refElem: Vetor de referência do nodo.
        :param conf: Objeto de controle do som
        """
        AbstractSOMNode.__init__(self, nid, refElem, conf)

    def elemCopy(self, elem):
        return elem[:]

    def resetElements(self):
        """Esvazia a lista de elementos.
        """

        self._sumVect = [0.0 for x in self.refElem]
        self._sumSqVect = [0.0 for x in self.refElem]
        self._minVect = [float('inf') for x in self.refElem]
        self._maxVect = [float('-inf') for x in self.refElem]
        self._numElem = 0
        self._closestElem = None
        self._closestNonZeroDistSq = None
        self._sumDistSq = 0.0
        self._meanElement = None
        self._sumDistFromMeanSq = None

    def distSq(self, elem):
        """Quadrado da distancia de elem ao vetor de referencia do nodo.
        """
        return euclidDistSq(self.refElem, elem)

    def insert(self, elem, distSq=None):
        """Insere um elemento na lista de elementos.
        """

        if distSq == None:
            distSq = self.distSq(elem)

        self._sumDistSq += distSq

        if (distSq > self.conf.minChangeDistSq) \
           and (self._closestElem == None \
                or distSq < self._closestNonZeroDistSq):
           self._closestNonZeroDistSq = distSq
           self._closestElem = elem

        for i in range(len(elem)):
            self._sumVect[i] += elem[i]
            self._sumSqVect[i] += elem[i]*elem[i]
            if elem[i] < self._minVect[i]:
                self._minVect[i] = elem[i]
            if elem[i] > self._maxVect[i]:
                self._maxVect[i] = elem[i]

        self._numElem += 1

        self._meanElement = None
        self._sumDistFromMeanSq = None

    def _findMeanElement(self):
        """Encontra o elemento medio do conjunto de elementos.

        O método atualiza o campo _meanElement.
        """

        if self._numElem > 0:
            self._meanElement = [x/self._numElem for x in self._sumVect]
        else:
            self._meanElement = self.refElem[:]

    def _calcSumDistFromMeanSquared(self):
        if self._numElem > 0:
            self._sumDistFromMeanSq = sum((x - (y*y)/self._numElem for x,y in
                            zip(self._sumSqVect,self._sumVect)))
        else:
            self._sumDistFromMeanSq = 0

    def getNumElements(self):
        return self._numElem

    def updateRefElem(self):
        mean = self.getMeanElement()

        if mean != None:
            newRefSums = mean[:]
        else:
            newRefSums = self.refElem[:]

        newRefPesos = (self.getNumElements() + 1.0)
        for i in range(len(newRefSums)):
            newRefSums[i] *= newRefPesos

        for node, weight in self.iterNeighboors():
            nodeMean = node.getMeanElement()
            if nodeMean != None:
                peso = weight * (node.getNumElements() + 1.0)
                newRefPesos += peso
                for i in range(len(nodeMean)):
                    newRefSums[i] += nodeMean[i] * peso

        self.refElem = [x/newRefPesos for x in newRefSums]

    def _getClosestElem(self):
        return self._closestElem

    def getStdevVect(self):
        if self._numElem <= 1:
            return [0 for x in self.refElem]

        ret = []
        for s, s2 in zip(self._sumVect, self._sumSqVect):
            x = (s2 - (s*s)/self._numElem)/self._numElem
            # Erros de arrendondamento podem tornar x um número negativo proximo
            # de zero, o que faz math.sqrt falhar.
            if x < 0.0:
                print("WARN: Valor negativo! {0}".format(x))
                ret.append(0.0)
            else:
                ret.append(math.sqrt(x))

        return ret

    def getMinVect(self):
        if self._numElem < 1:
            return [0 for x in self.refElem]

        return self._minVect

    def getMaxVect(self):
        if self._numElem < 1:
            return [0 for x in self.refElem]

        return self._maxVect

class SOMap(AbstractSOMap):
    """Um mapa auto organizável que opera sobre vetores numéricos.

    Atributos:

    - conf: Objeto de configuração que pode ser ajustado antes do treinamento para
        controlar parâmetros do treinamento. Veja documentação para a classe Config.

    - nodes: Lista dos nodos do SOM. Começa vazia e é preenchida durante o
        treinamento.
    """

    def __init__(self, mID='top'):
        """Construtor de um SOM.

        :param distFun: Função de distancia a ser utilizada
        """

        self.conf = Config()

        AbstractSOMap.__init__(self, mID)

    def _createSOMNode(self, nid, elem):
        return SOMNode(nid, elem, self.conf)

    def _initializeHexGrid(self, nrows, ncols):
        self.nodes = []

        for r in range(nrows):
            for c in range(ncols):
                i = c + (r*ncols)
                k = i % len(self.elements)
                node = self._createSOMNode(i, self.elements[k])
                self.nodes.append(node)
                node.y = r
                node.x = c + (r%2)*0.5

        idxs = [(0,0) for x in range(6)]
        for r in range(nrows):
            for c in range(ncols):
                i = (r*ncols) + c
                idxs[0] = (r-1, c + (r % 2)-1)
                idxs[1] = (r-1, c + (r % 2))
                idxs[2] = (r, c - 1)
                idxs[3] = (r, c + 1)
                idxs[4] = (r+1, c + (r % 2)-1)
                idxs[5] = (r+1, c + (r % 2))
                node = self.nodes[i]
                for rl, cl in idxs:
                    idx = (rl*ncols) + cl
                    if 0 <= idx < len(self.nodes) \
                        and 0 <= rl < nrows \
                        and 0 <= cl < ncols:
                        n = self.nodes[idx]
                        node.neighbors.add(n)
                        n.neighbors.add(node)

    def _printGridSumary(self, fase, depth, minDepth):
        m = {
            'fase': fase,
            'nSteps': self.numSteps,
            'nTrainSt': self.numLastTrainSteps,
            'depth': depth,
            'minDepth': minDepth
        }
        print( "{fase}: stTot {nSteps} stLT {nTrainSt} depth {depth} minDepth {minDepth}".format(
            **m
        ))

    def trainHexGrid(self, nrows, ncols):
        """Inicializa e treina um SOM com a topologia de uma grade hexagonal.
        Cada nodo, excetuando os das bordas, possuem 6 vizinhos.

        :param nrows: Número de linhas da grade.
        :param ncols: Número de colunas da grade.
        """

        self.doMST = False
        self.numSteps = 0

        self._initializeHexGrid(nrows, ncols)
        neighDepth = max(nrows, ncols)
        neighDepthMin = self.conf.calcMaxDepthForWeight(
                self.conf.neighWeightTrain)

        while neighDepth >= neighDepthMin:
            self.conf.applyMaxDepthWeight(neighDepth)
            self.train()
            self._printGridSumary("Train",neighDepth,neighDepthMin)
            neighDepth -= 1

        self.conf.applyRefineWeight()
        self.train()
        self._printGridSumary("Refine",neighDepth, neighDepthMin)


def convertSOMapToMultiGraph(som, attrNames=[], nodeIDAttr='ID'):
    """Cria um MultiGraph a partir de um SOM baseado em vetores.

    OBS: O SOM é um grafo não direcionado, mas a classe MultiGraph considera que
    as arestas são direcionadas. A convensão que utilizaremos aqui será a de
    criar a aresta apenas no sentido do nodo de menor ID para o de maior ID. Um
    MultiGraph possui o método 'neighboors' que permite iterar por todos os
    vizinhos de um nodo independente do sentido das arestas. Utilizando-se este
    método pode-se recuperar a vizinhança não direcionada do SOM original.

    :param som: SOM a ser convertido em grafo
    :param attrNames: Lista com o nome de cada atributo que compõe o espaço
        vetorial.
    :param nodeIDAttr: Nome do atributo que conterá o ID de cada nodo do SOM.

    :return: Instancia de MultiGraph
    """


    g = gr.MultiGraph()

    # Criando atributos de grafo
    dimensionSpec = gr.AttrSpec('inSpaceDim', 'int', 0)
    g.addGraphAttrSpec(dimensionSpec)

    dimension = len(som.nodes[0].refElem)
    g.setGraphAttr(dimensionSpec.name, dimension)

    # Criando atributos de nodos
    attrNameFmt = '{{0:{}}}'.format(int(math.floor(math.log10(dimension))) + 1)

    for i in range(len(attrNames),dimension):
        attrNames.append(attrNameFmt.format(i))

    meanSpecs = []
    stdevSpecs = []
    refSpecs = []
    minSpecs = []
    maxSpecs = []
    for attr in attrNames:
        spec = gr.AttrSpec(attr+'_mean', 'double', 0)
        meanSpecs.append(spec)
        g.addNodeAttrSpec(spec)
        spec = gr.AttrSpec(attr+'_stdev', 'double', 0)
        stdevSpecs.append(spec)
        g.addNodeAttrSpec(spec)
        spec = gr.AttrSpec(attr+'_ref', 'double', 0)
        refSpecs.append(spec)
        g.addNodeAttrSpec(spec)
        spec = gr.AttrSpec(attr+'_min', 'double', 0)
        minSpecs.append(spec)
        g.addNodeAttrSpec(spec)
        spec = gr.AttrSpec(attr+'_max', 'double', 0)
        maxSpecs.append(spec)
        g.addNodeAttrSpec(spec)

    numElemSpec = gr.AttrSpec('numElem', 'int', 0)
    g.addNodeAttrSpec(numElemSpec)

    sseSpec = gr.AttrSpec('sse', 'double', 0)
    g.addNodeAttrSpec(sseSpec)

    dispSpec = gr.AttrSpec('disp', 'double', 0)
    g.addNodeAttrSpec(dispSpec)

    idSpec = gr.AttrSpec(nodeIDAttr, 'int', 0)
    g.addNodeAttrSpec(idSpec)

    # Criando atributos de aresta
    distSpec = gr.AttrSpec('dist', 'double', 0)
    g.addEdgeAttrSpec(distSpec)

    for node in som.nodes:
        n = node.getID()
        g.addNode(n)
        g.setNodeAttr(n, numElemSpec.name, node.getNumElements())
        g.setNodeAttr(n, sseSpec.name, node.getSumDistFromMeanSquared())
        if node.getNumElements() > 0:
            disp = math.sqrt(
                node.getSumDistFromMeanSquared()/node.getNumElements())
        else:
            disp = 0.0
        g.setNodeAttr(n, dispSpec.name, disp)

        g.setNodeAttr(n, idSpec.name, n)
        mean = node.getMeanElement()
        stdev = node.getStdevVect()
        minVect = node.getMinVect()
        maxVect = node.getMaxVect()
        for i in range(dimension):
            g.setNodeAttr(n, refSpecs[i].name, node.refElem[i])
            g.setNodeAttr(n, meanSpecs[i].name, mean[i])
            g.setNodeAttr(n, stdevSpecs[i].name, stdev[i])
            g.setNodeAttr(n, minSpecs[i].name, minVect[i])
            g.setNodeAttr(n, maxSpecs[i].name, maxVect[i])

    for n1 in som.nodes:
        n1id = n1.getID()
        for n2 in n1.neighbors:
            n2id = n2.getID()
            if n1id < n2id:
                g.addEdge(n1id, n2id, 1)
                g.setEdgeAttr((n1id, n2id, 1), distSpec.name,
                    n1.dist(n2.refElem))

    return g

