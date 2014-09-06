# coding: utf-8
"""Implementação de um SOM de crescimento dinâmico ( growing SOM ) baseao do em
distancias, ou seja, os elementos apresentados ao SOM são opacos para o
algoritmo e a distancia entre eles é dada pela funcão fornecida.
"""

__author__ = "Giovani Melo Marzano"

from . import Config, AbstractSOMap, AbstractSOMNode

class DistBasedConfig(Config):
    """Classe de configuração para o SOM
    """

    def __init__(self, distFun):
        Config.__init__(self)
        self.distFun = distFun

class SOMNode(AbstractSOMNode):
    """Representa um nodo do SOM.
    """

    def __init__(self, nid, refElem, conf):
        """Inicializa a instancia.

        :param nid: Identificador do nodo.
        :param refElem: Elemento de referência do nodo.
        :param conf: Objeto de controle do som
        """
        self.elements = []
        AbstractSOMNode.__init__(self,nid,refElem,conf)

    def elemCopy(self, elem):
        # O elemento é opaco, não fazemos sua cópia
        return elem

    def resetElements(self):
        """Esvazia a lista de elementos.
        """

        del self.elements[:]
        self._meanElement = None
        self._meanSumDist = None
        self._sumDistFromMeanSq = None

    def dist(self, elem):
        return self.conf.distFun(self.refElem, elem)

    def distSq(self, elem):
        """Quadrado da distancia de elem ao vetor de referencia do nodo.
        """
        dist = self.dist(elem)
        return dist * dist

    def insert(self, elem, distSq=None):
        """Insere um elemento na lista de elementos.
        """
        self.elements.append(elem)

    def _findMeanElement(self):
        """Encontra o elemento medio do conjunto de elementos.

        O Elemento médio está aqui definido como o elemento que possui a menor
        soma das distâncias ao quadrado aos outros elementos do conjunto.

        O método atualiza o campo _meanElement.
        """
        mean = None
        sumDist = float('inf')
        sumDistSq = float('inf')

        for candidate in self.elements:
            (candSumDist, candSumDistSq) = self.calcSumDistToElements(candidate)

            if candSumDistSq < sumDistSq:
                mean = candidate
                sumDist = candSumDist
                sumDistSq = candSumDistSq

        self._meanElement = mean
        self._meanSumDist = sumDist
        self._sumDistFromMeanSq = sumDistSq

    def _calcSumDistFromMeanSquared(self):
        self._findMeanElement()

    def getNumElements(self):
        return len(self.elements)

    def updateRefElem(self):
        newRef = None
        newRefDist = float('inf')

        for elem in self.elements:
            dist = self._calcElemNetDist(elem)

            if dist < newRefDist:
                newRef = elem
                newRefDist = dist

        if newRef != None:
            self.refElem = newRef

    def _getClosestElem(self):
        mean = self.getMeanElement()
        closest = None
        closestDist = None

        for elem in self.elements:
            dist = self.conf.distFun(elem, mean)
            if dist > 0 and (closestDist == None or dist < closestDist):
                closestDist = dist
                closest = elem

        return closest

    def calcSumDistToElements(self, elem):
        """Calcula a soma das distancias do elemento fornecido aos
        elementos atribuídos a este nodo.

        :param elem: Elemento que sera comparado

        :return: (Soma das distancias, soma dos quadrados das distancias)
        """

        sumDist = 0.0
        sumDistSq = 0.0
        dist = 0.0
        for e in self.elements:
            dist = self.conf.distFun(elem, e)
            sumDist += dist
            sumDistSq += dist * dist

        return (sumDist, sumDistSq)

    def _calcElemNetDist(self, elem):
        dist = self.conf.distFun(elem, self.getMeanElement())

        weightedSumDist = dist * self.getNumElements()
        sumWeigths = self.getNumElements()

        for node in self.neighbors:
            dist = self.conf.distFun(elem, node.getMeanElement())
            weight = self.conf.neighWeight * node.getNumElements()
            weightedSumDist += dist * weight
            sumWeigths += weight

        return weightedSumDist/sumWeigths


class SOMap(AbstractSOMap):
    """Um mapa auto organizável.
    """

    def __init__(self, distFun, mID='top'):
        """Construtor de um SOM.

        :param distFun: Função de distancia a ser utilizada
        """

        self.conf = DistBasedConfig(distFun)

        AbstractSOMap.__init__(self, mID)

    def _createSOMNode(self, nid, elem):
        return SOMNode(nid, elem, self.conf)

