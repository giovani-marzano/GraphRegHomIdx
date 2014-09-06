# coding: utf-8
"""Implementação de um SOM de crescimento dinâmico ( growing SOM ) baseao do em
vetores, ou seja, os elementos apresentados ao SOM são pontos em um espaço n
dimensional. A distância entre os elementos é a distância euclidiana entre os
pontos.
"""

__author__ = "Giovani Melo Marzano"

from . import Config, AbstractSOMap

import math

def euclidDistSq(a, b):
    """Distancia euclidiana ao quadrado de dois vetores.
    """

    return sum((pow(ax-bx,2) for ax,bx in zip(a,b)))

class SOMNode(object):
    """Representa um nodo do SOM.
    """

    def __init__(self, nid, refElem, conf):
        """Inicializa a instancia.

        :param nid: Identificador do nodo.
        :param refElem: Vetor de referência do nodo.
        :param conf: Objeto de controle do som
        """

        self._id = nid
        self.refElem = refElem
        self.conf = conf

        self.neighbors = set()

        self.resetElements()

    def getID(self):
        """Recupera o ID do nodo.
        """

        return self._id

    def resetElements(self):
        """Esvazia a lista de elementos.
        """

        self._sumVect = [0.0 for x in self.refElem]
        self._sumSqVect = [0.0 for x in self.refElem]
        self._numElem = 0
        self._closestElem = None
        self._closestNonZeroDistSq = None
        self._sumDistSq = 0.0
        self._meanElement = None
        self._sumDistFromMeanSq = None

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

        self._numElem += 1

        self._meanElement = None
        self._sumDistFromMeanSq = None

    def dist(self, elem):
        return math.sqrt(self.distSq(elem))

    def distSq(self, elem):
        """Quadrado da distancia de elem ao vetor de referencia do nodo.
        """
        return euclidDistSq(self.refElem, elem)

    def _findMeanElement(self):
        """Encontra o elemento medio do conjunto de elementos.

        O método atualiza o campo _meanElement.
        """

        if self._numElem > 0:
            self._meanElement = [x/self._numElem for x in self._sumVect]
        else:
            self._meanElement = self.refElem

    def getMeanElement(self):
        """Recupera o ponto medio dos pontos atribuidos a este nodo.
        """
        if self._meanElement == None:
            self._findMeanElement()

        return self._meanElement

    def _calcSumDistFromMeanSquared(self):
        if self._numElem > 0:
            self._sumDistFromMeanSq = sum((x - (y*y)/self._numElem for x,y in
                            zip(self._sumSqVect,self._sumVect)))
        else:
            self._sumDistFromMeanSq = 0

    def getSumDistFromMeanSquared(self):
        if self._sumDistFromMeanSq == None:
            self._calcSumDistFromMeanSquared()

        return self._sumDistFromMeanSq

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

        for node in self.neighbors:
            nodeMean = node.getMeanElement()
            if nodeMean != None:
                peso = self.conf.neighWeight * (node.getNumElements() + 1.0)
                newRefPesos += peso
                for i in range(len(nodeMean)):
                    newRefSums[i] += nodeMean[i] * peso

        self.refElem = [x/newRefPesos for x in newRefSums]

    def divide(self, nid):
        """Divide este nodo em dois.

        :param nid: ID do nodo que dever ser criado

        :return: new node
        """

        mean = self.getMeanElement()
        closest = self._closestElem

        if mean == None or closest == None:
            return None

        if self.distSq(mean) > self.conf.minChangeDistSq:
            newNodeRef = mean[:]
        elif self.distSq(closest) > self.conf.minChangeDistSq:
            newNodeRef = closest[:]
        else:
            return None

        n2 = SOMNode(nid, newNodeRef, self.conf)

        origNeighbors = self.neighbors
        self.neighbors = set()
        self.neighbors.add(n2)
        n2.neighbors.add(self)

        # Reasigning neighbors
        for neigh in origNeighbors:
            neigh.neighbors.discard(self)
            dist1 = neigh.distSq(self.refElem)
            dist2 = neigh.distSq(n2.refElem)

            if dist1 < dist2:
                neigh.neighbors.add(self)
                self.neighbors.add(neigh)
            else:
                neigh.neighbors.add(n2)
                n2.neighbors.add(neigh)

        return n2


class SOMap(AbstractSOMap):
    """Um mapa auto organizável.
    """

    def __init__(self, mID='top'):
        """Construtor de um SOM.

        :param distFun: Função de distancia a ser utilizada
        """

        self.conf = Config()

        AbstractSOMap.__init__(self, mID)

    def _getNodeOldRefElem(self, node):
        return node.refElem[:]

    def _createSOMNode(self, nid, elem):
        return SOMNode(nid, elem, self.conf)

