# coding: utf-8
"""Implementação de um SOM de crescimento dinâmico ( growing SOM ) baseao do em
vetores, ou seja, os elementos apresentados ao SOM são pontos em um espaço n
dimensional. A distância entre os elementos é a distância euclidiana entre os
pontos.
"""

import sys

def diffSquared(a, b):
    """Diferença ao quadrado dos argumentos.
    """

    return pow(a-b, 2)

def euclidDistSq(a, b):
    """Distancia euclidiana ao quadrado de dois vetores.
    """

    c = map(diffSquared, a, b)
    return sum(c)

class Config(object):
    """Classe de configuração para o SOM

    Atributos configuraveis:

    - maxStepsPerGeneration: Número máximo de iterações que o SOM será treinado
      antes de tentar gerar mais um nodo.

    - neighWeightTrain: Peso dos nodos vizinhos na fase de treinamento.
      Determina o quanto os nodos vizinhos influenciam na atualização do vetor
      de referência de um nodo.

    - neighWeightRefine: Peso dos nodos vizinhos na fase de refinamento.
      Determina o quanto os nodos vizinhos influenciam na atualização do vetor
      de referência de um nodo.

    - minChangeDistSq: Valor minimo para a distância ao quadrado entre o novo
      vetor de referência de um nodo e o vetor de referencia original para que
      se considere que houve mudança no vetor de referência.

    Constantes:
    
    - MAX_STEPS_PER_GENERATION_DFLT: Valor default para o número máximo de
      iteracoes em uma geração do SOM.

    - NEIGH_WEIGHT_TRAIN_DFLT: Valor default para o peso dos nodos vizinhos na
      fase de treinamento.

    - NEIGH_WEIGHT_REFINE_DFLT: Valor default para o peso dos nodos vizinhos na
      fase de refinamento.

    - MIN_CHANGE_DIST_SQ_DFLT: Valor default para minChangeDistSq.
    """

    MAX_STEPS_PER_GENERATION_DFLT = 100
    NEIGH_WEIGHT_TRAIN_DFLT = 0.25
    NEIGH_WEIGHT_REFINE_DFLT = 0.0
    MIN_CHANGE_DIST_SQ_DFLT = 0.000001

    def __init__(self):

        self.maxStepsPerGeneration = Config.MAX_STEPS_PER_GENERATION_DFLT
        self.neighWeightTrain = Config.NEIGH_WEIGHT_TRAIN_DFLT
        self.neighWeightRefine = Config.NEIGH_WEIGHT_REFINE_DFLT
        self.minChangeDistSq = Config.MIN_CHANGE_DIST_SQ_DFLT

        self.neighWeight = self.neighWeightTrain

    def applyTraingWeight(self):
        self.neighWeight = self.neighWeightTrain

    def applyRefineWeight(self):
        self.neighWeight = self.neighWeightRefine

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

        self._sumVect = map(lambda x: 0.0, self.refElem)
        self._sumSqVect = self._sumVect[:]
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

        self._sumVect = map(lambda x,y: x + y, self._sumVect, elem)
        self._sumSqVect = map(lambda x,y: x + (y*y), self._sumSqVect, elem)
        self._numElem += 1

        self._meanElement = None
        self._sumDistFromMeanSq = None

    def distSq(self, elem):
        """Quadrado da distancia de elem ao vetor de referencia do nodo.
        """
        return euclidDistSq(self.refElem, elem)

    def _findMeanElement(self):
        """Encontra o elemento medio do conjunto de elementos.

        O método atualiza o campo _meanElement.
        """

        if self._numElem > 0:
            self._meanElement = map(lambda x: x/self._numElem, self._sumVect)

    def getMeanElement(self):
        """Recupera o ponto medio dos pontos atribuidos a este nodo.
        """
        if self._meanElement == None:
            self._findMeanElement()

        return self._meanElement

    def _calcSumDistFromMeanSquared(self):
        if self._numElem > 0:
            vetDistSq = map(lambda x,y: x - ((y*y)/self._numElem), self._sumSqVect,
                    self._sumVect)

            self._sumDistFromMeanSq = sum(vetDistSq)
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

        self.refElem = map(lambda x: x/newRefPesos, newRefSums)

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


class SOMap(object):
    """Um mapa auto organizável.
    """

    def __init__(self, mID='top', conf=None):
        """Construtor de um SOM.

        :param distFun: Função de distancia a ser utilizada
        """

        self.conf = conf or Config()
        self.ID = mID

        self.numSteps = 0

        self.nodes = []
        self.elements = []
        self.FVU = 1.0

    def findNodeForElem(self, elem):
        bestNode = self.nodes[0]
        bestDist = bestNode.distSq(elem)

        for node in self.nodes:
            distSq = node.distSq(elem)
            if distSq < bestDist:
                bestDist = distSq
                bestNode = node

        return (bestNode, bestDist)

    def _assignOneElement(self, elem):
        (bestNode, bestDist) = self.findNodeForElem(elem)
        bestNode.insert(elem, bestDist)

    def _assignElements(self):

        for elem in self.elements:
            self._assignOneElement(elem)

    def _resetNodes(self):
        for node in self.nodes:
            node.resetElements()

    def _updateNodes(self):
        """Atualiza os nodos com base nos elementos distribuídos.

        :return: Se houve atualização de algum nodo
        """

        changed = False

        for node in self.nodes:
            oldRef = node.refElem[:]
            node.updateRefElem()
            if node.distSq(oldRef) > self.conf.minChangeDistSq:
                changed = True
        
        return changed

    def _trainStep(self):
        """Realiza um passo de treinamento.

        :return: Se hounve mudanca em algum nodo.
        """

        self.numSteps += 1
        
        self._resetNodes()
        self._assignElements()
        return self._updateNodes()

    def _printMap(self):
        sys.stdout.write("Info: {0}\t{1}\t{2}\n".format(
            self.numSteps, len(self.nodes), self.FVU
            ))
        for node in self.nodes:
            sys.stdout.write("Node: {0}\t{1}".format(
                self.numSteps, node.getID()
            ))
            for d in node.refElem:
                sys.stdout.write("\t{0}".format(d))
            sys.stdout.write("\n")
        sys.stdout.write("\n")

    def train(self):

        trainSteps = 0

        cont = True
        while cont:
            trainSteps += 1
            cont = self._trainStep()
            if trainSteps > self.conf.maxStepsPerGeneration:
                cont = False
            self._printMap()
                
    def _initializeMap(self):
        n0 = SOMNode(0, self.elements[0], self.conf)

        self.nodes = [n0]

        self.train()

        self.variance = (1.0 * n0.getSumDistFromMeanSquared())
        self.variance = self.variance/len(self.elements)

        # factor of variance unexplained
        self.FVU = 1.0

    def _updateFVU(self):
        sumDistSq = 0.0
        for node in self.nodes:
            sumDistSq += node.getSumDistFromMeanSquared()

        self.FVU = (sumDistSq/len(self.elements))/self.variance

    def _grow(self):
        maxVariance = 0.0
        growNode = None

        for node in self.nodes:
            if node.getNumElements() <= 0:
                continue
            var = node.getSumDistFromMeanSquared()/node.getNumElements()
            if var > maxVariance:
                maxVariance = var
                growNode = node
        
        if growNode == None:
            return False

        newNode = growNode.divide(len(self.nodes))

        if newNode == None:
            return False

        self.nodes.append(newNode)        
        return True

    def trainAndGrow(self, fvu, maxNodes):
        """Realiza o processo de treinar e aumentar o SOM.

        :param fvu: Valor limite para o fator de variancia não explicada.
        :param maxNodes: Número máximo de nodos que devem ser gerados.
        """

        self.numSteps = 0
        self._initializeMap()

        self.conf.applyTraingWeight()
        while self.FVU > fvu and len(self.nodes) < maxNodes:
            if self._grow():
                self.train()
                self._updateFVU()
            else:
                break

        sys.stdout.write("\nrefinamento\n")
        self.conf.applyRefineWeight()
        self.train()
