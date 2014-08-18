# coding: utf-8

NEIGH_START_WEIGHT_DFLT = 0.6
NEIGH_WEIGHT_DECAY_DFLT = 0.2

class Control(object):
    """Classe de controle para fazer a comunicação entre o mapa e seus nodos.
    """

    def __init__(self, distFun):

        self.distFun = distFun
        self.startWeight = NEIGH_START_WEIGHT_DFLT
        self.weightDecay = NEIGH_WEIGHT_DECAY_DFLT
        self.neighWeight = self.startWeight

    def decNeighWeight(self):
        self.neighWeight -= self.weightDecay

        if self.neighWeight < 0.0:
            self.neighWeight = 0.0

    def resetNeighWeight(self):
        self.neighWeight = self.startWeight

class SOMNode(object):
    """Representa um nodo do SOM generico.
    """

    def __init__(self, nid, refElem, ctrl):
        """Inicializa a instancia.

        :param nid: Identificador do nodo.
        :param refElem: Elemento de referência do nodo.
        :param ctrl: Objeto de controle do som
        """

        self._id = nid
        self.refElem = refElem
        self.ctrl = ctrl

        self.neighbors = set()

        self.elements = []
        self.resetElements()

    def getID(self):
        """Recupera o ID do nodo.
        """

        return self._id

    def resetElements(self):
        """Esvazia a lista de elementos.
        """

        del self.elements[:]
        self._meanElement = None
        self._meanSumDist = None
        self._meanSumDistSq = None

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
            dist = self.ctrl.distFun(elem, e)
            sumDist += dist
            sumDistSq += dist * dist

        return (sumDist, sumDistSq)

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
        self._meanSumDistSq = sumDistSq

    def getMeanElement(self):
        if self._meanElement == None:
            self._findMeanElement()

        return self._meanElement

    def getSumDistFromMean(self):
        if self._meanSumDist == None:
            self._findMeanElement()

        return self._meanSumDist

    def getSumDistFromMeanSquared(self):
        if self._meanSumDistSq == None:
            self._findMeanElement()

        return self._meanSumDistSq

    def getNumElements(self):
        return len(self.elements)

    def insert(self, elem, dist=None):
        """Insere um elemento na lista de elementos."
        """

        if dist == None:
            dist = self.dist(elem)

        self.elements.append(elem)

    def dist(self, elem):
        return self.ctrl.distFun(self.refElem, elem)

    def _calcElemNetDist(self, elem):
        dist = self.ctrl.distFun(elem, self.getMeanElement())

        weightedSumDist = dist * self.getNumElements()
        sumWeigths = self.getNumElements()

        for node in self.neighbors:
            dist = self.ctrl.distFun(elem, node.getMeanElement())
            weight = self.ctrl.neighWeight * node.getNumElements()
            weightedSumDist += dist * weight
            sumWeigths += weight

        return weightedSumDist/sumWeigths

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

    def findClosestToMean(self):
        mean = self.getMeanElement()
        closest = None
        closestDist = None

        for elem in self.elements:
            dist = self.ctrl.distFun(elem, mean)
            if dist > 0 and (closestDist == None or dist < closestDist):
                closestDist = dist
                closest = elem

        return closest

    def divide(self, nid):
        """Divide este nodo em dois.

        :param nid: ID do nodo que dever ser criado

        :return: new node
        """

        mean = self.getMeanElement()
        closest = self.findClosestToMean()

        if mean == None or closest == None:
            return None

        m = SOMap(self.ctrl.distFun, str(self.getID()) + "-divide")
        m.elements = list(self.elements)

        self.refElem = mean
        n2 = SOMNode(nid, closest, m.ctrl)

        origCtrl = self.ctrl
        self.ctrl = m.ctrl

        origNeighbors = self.neighbors.copy()
        self.neighbors.add(n2)
        n2.neighbors.add(self)

        self.resetElements()

        m.nodes = [self, n2]
        m.train()

        # Reasigning neighbors
        self.neighbors.clear()
        self.neighbors.add(n2)
        for neigh in origNeighbors:
            neigh.neighbors.discard(self)
            dist1 = origCtrl.distFun(self.getMeanElement(), neigh.getMeanElement())
            dist2 = origCtrl.distFun(n2.getMeanElement(), neigh.getMeanElement())
            
            if dist1 < dist2:
                neigh.neighbors.add(self)
                self.neighbors.add(neigh)
            else:
                neigh.neighbors.add(n2)
                n2.neighbors.add(neigh)

        # Reseting nodes control to that of the original map
        self.ctrl = origCtrl
        n2.ctrl = origCtrl

        return n2


class SOMap(object):
    """Um mapa auto organizável.
    """

    def __init__(self, distFun, mID='top'):
        """Construtor de um SOM.

        :param distFun: Função de distancia a ser utilizada
        """
        self.ctrl = Control(distFun)
        self.ID = mID

        self.numSteps = 0

        self.nodes = []
        self.elements = []

    def _assignOneElement(self, elem):

        bestNode = self.nodes[0]
        bestDist = bestNode.dist(elem)

        for node in self.nodes:
            dist = node.dist(elem)
            if dist < bestDist:
                bestDist = dist
                bestNode = node

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
            oldRef = node.refElem
            node.updateRefElem()
            if oldRef != node.refElem:
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

    def train(self):

        self.ctrl.resetNeighWeight()

        cont = True
        while cont:
            cont = self._trainStep()
            self.ctrl.decNeighWeight()
                
    def _initializeMap(self):
        n0 = SOMNode(0, self.elements[0], self.ctrl)

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

        self.numSteps = 0
        self._initializeMap()

        while self.FVU > fvu and len(self.nodes) < maxNodes:
            if self._grow():
                self.train()
                self._updateFVU()
            else:
                break
