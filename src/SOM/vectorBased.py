# coding: utf-8
"""Implementação de um SOM de crescimento dinâmico ( growing SOM ) baseao do em
vetores, ou seja, os elementos apresentados ao SOM são pontos em um espaço n
dimensional. A distância entre os elementos é a distância euclidiana entre os
pontos.
"""

__author__ = "Giovani Melo Marzano"

from . import Config, AbstractSOMap, AbstractSOMNode

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
            self._meanElement = self.refElem

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

        for node in self.neighbors:
            nodeMean = node.getMeanElement()
            if nodeMean != None:
                peso = self.conf.neighWeight * (node.getNumElements() + 1.0)
                newRefPesos += peso
                for i in range(len(nodeMean)):
                    newRefSums[i] += nodeMean[i] * peso

        self.refElem = [x/newRefPesos for x in newRefSums]

    def _getClosestElem(self):
        return self._closestElem


class SOMap(AbstractSOMap):
    """Um mapa auto organizável.
    """

    def __init__(self, mID='top'):
        """Construtor de um SOM.

        :param distFun: Função de distancia a ser utilizada
        """

        self.conf = Config()

        AbstractSOMap.__init__(self, mID)

    def _createSOMNode(self, nid, elem):
        return SOMNode(nid, elem, self.conf)

