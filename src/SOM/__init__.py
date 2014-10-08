# coding: utf-8
__author__='Giovani Melo Marzano'

import heap
import math
from collections import deque

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

    - maxNodes: Numero máximo de nodos da rede.

    - FVU: (Fraction of Variance Unexplained) Valor limite da fração de
      variância não explicada que, quando atingido, causa a parada do
      crescimento do SOM.

    - MSTPeriod: De quantas em quantas iteracoes realizar o calculo da árvore
      geradora mínima (Minimal Spanning Tree).

    Constantes:

    - MAX_STEPS_PER_GENERATION_DFLT: Valor default para o número máximo de
      iteracoes em uma geração do SOM.

    - NEIGH_WEIGHT_TRAIN_DFLT: Valor default para o peso dos nodos vizinhos na
      fase de treinamento.

    - NEIGH_WEIGHT_REFINE_DFLT: Valor default para o peso dos nodos vizinhos na
      fase de refinamento.

    - MIN_CHANGE_DIST_SQ_DFLT: Valor default para minChangeDistSq.

    - MAX_NODES_DFLT: Default para o número máximo de nodos.

    - FVU_DFLT: Default para a fração de variância não explicada.

    - MST_PERIOD_DFLT: Default para o periodo de calculo da MST.
    """

    MAX_STEPS_PER_GENERATION_DFLT = 100
    NEIGH_WEIGHT_TRAIN_DFLT = 0.25
    NEIGH_WEIGHT_REFINE_DFLT = 0.0
    MIN_CHANGE_DIST_SQ_DFLT = 0.000001
    MAX_NODES_DFLT = 100
    FVU_DFLT = 0.25
    MST_PERIOD_DFLT = 10

    def __init__(self):

        self.maxStepsPerGeneration = Config.MAX_STEPS_PER_GENERATION_DFLT
        self.neighWeightTrain = Config.NEIGH_WEIGHT_TRAIN_DFLT
        self.neighWeightRefine = Config.NEIGH_WEIGHT_REFINE_DFLT
        self.minChangeDistSq = Config.MIN_CHANGE_DIST_SQ_DFLT
        self.maxNodes = Config.MAX_NODES_DFLT
        self.FVU = Config.FVU_DFLT
        self.MSTPeriod = Config.MST_PERIOD_DFLT

        self.neighWeight = self.neighWeightTrain

    def applyTraingWeight(self):
        self.neighWeight = self.neighWeightTrain

    def applyRefineWeight(self):
        self.neighWeight = self.neighWeightRefine

    def linearNeighWeight(self,nv):
        """Calcula um peso de vizinhança com decaimento linear.

        A reta utilizada é dada pelos pontos (0,1) e (1,neighWeight), onde, em
        (nv,p), 'v' é o nível de vizinhança e 'p' o peso daquela vizinhança.
        O próprio nodo tem nível de vizinhança 0, seus vizinhos imediatos 1 e
        assim por diante.

        :param nv: Nivel de vizinhança

        :return: Peso do vizinho no intervalo [0,1]
        """

        w = (self.neighWeight - 1.0)*nv + 1.0

        w = min(1,w)
        w = max(0,w)

        return w

    def applyMaxDepthWeight(self, maxdepth):
        """Configura o peso de tal forma que em um decaimento linear o peso na
        profundidade maxdepth + 1 seja zero.

        A reta do decaimento linear é dada pelos pontos (0,1) (maxdepth+1,0). E
        calcula-se o y em (1,y) colocando este valor em self.neighWeight
        """
        self.neighWeight = (-1.0)/(maxdepth+1) + 1.0

    def calcMaxDepthForWeight(self, minweight):
        """Calcula a profundidade 'p' que gera o peso minweight
        (aproximadamente) e que a próxima profundidade seja zero.

        Reta de decaimento dada pelos pontos (0,1) (p+1,0) e queremos encontrar
        'p' em (p, minweight)
        """
        if minweight == 0:
            return 0
        depth = (1 - minweight)/minweight
        return max(0,depth)


class AbstractSOMap(object):
    """Classe abstrata para mapas auto organizávies.

    As classes derivadas devem:

        - criar um atributo conf
        - implementar metodos marcados com Not Implemented
    """

    def __init__(self, mID='top'):
        """Construtor de um SOM.

        :param distFun: Função de distancia a ser utilizada
        """

        self.ID = mID

        self.numSteps = 0
        self.numLastTrainSteps = 0

        self.nodes = []
        self.elements = []
        self.FVU = 1.0

        # Atributos para controle do MST
        self.doMST = False
        self._mstHnd = None
        self._mstParent = None

    def findNodeForElem(self, elem):
        """Encontra o nodo de menor distancia ao elemento.

        :param elem: Elemento a ser testado

        :return: (nodo, distancia)
        """
        bestNode = self.nodes[0]
        bestDist = bestNode.distSq(elem)

        for node in self.nodes:
            distSq = node.distSq(elem)
            if distSq < bestDist:
                bestDist = distSq
                bestNode = node

        return (bestNode, bestDist)

    def _assignOneElement(self, elem):
        """Atribui um elemento a seu nodo mais próximo.
        """
        (bestNode, bestDist) = self.findNodeForElem(elem)
        bestNode.insert(elem, bestDist)

    def _assignElements(self):
        """Distribui todos os elementos do conjunto de treinamento entre os
        nodos do SOM.
        """

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
        maxUpdDist = 0
        updtDist = 0

        for node in self.nodes:
            oldRef = node.elemCopy(node.refElem)
            node.updateRefElem()
            updtDist = node.distSq(oldRef)
            if updtDist > maxUpdDist:
                maxUpdDist = updtDist

        self.lastMaxUpdDistSq = maxUpdDist

        if maxUpdDist > self.conf.minChangeDistSq:
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

    def _printSumary(self, fase):
        m = {
            'fase': fase,
            'nSteps': self.numSteps,
            'nTrainSt': self.numLastTrainSteps,
            'nNodes': len(self.nodes),
            'FVU': self.FVU
        }
        print("{fase}: stTot {nSteps} stLT {nTrainSt} nodes {nNodes} FVU {FVU}".format(
            **m
        ))

    def train(self):
        """Treina o nodo com o conjunto de treinamento setado em 'elements'.
        """

        trainSteps = 0

        cont = True
        while cont:
            trainSteps += 1
            cont = self._trainStep()
            if trainSteps > self.conf.maxStepsPerGeneration:
                cont = False
            if self.doMST and self.numSteps % self.conf.MSTPeriod == 0:
                self._minimunSpanningTree()
            #self._printMap()

        self.numLastTrainSteps = trainSteps

    def _createSOMNode(self, nid, elem):
        raise NotImplementedError()

    def _initializeMap(self):
        n0 = self._createSOMNode(0, self.elements[0])

        self.nodes = [n0]

        self.train()

        self.SStot = (1.0 * n0.getSumDistFromMeanSquared())

        # fraction of variance unexplained
        self.FVU = 1.0

    def _updateFVU(self):
        sumDistSq = 0.0
        for node in self.nodes:
            sumDistSq += node.getSumDistFromMeanSquared()

        self.FVU = sumDistSq/self.SStot

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

    def trainGrowingTree(self):
        """Treina um SOM com a topologia de uma árvore em que o número de nodos
        começa com 1 e vai aumentando até uma das condições de parada serem
        atingidas.
        """

        print("\n---- " + self.ID +" ----")

        self.doMST = True
        self.numSteps = 0
        self._initializeMap()

        maxNodes = self.conf.maxNodes

        self.conf.applyTraingWeight()
        while self.FVU > self.conf.FVU and len(self.nodes) < maxNodes:
            if self._grow():
                self.train()
                self._updateFVU()
                self._printSumary("Train")
            else:
                break

        self._minimunSpanningTree()

        # sys.stdout.write("\nrefinamento\n")
        self.conf.applyRefineWeight()
        self.train()
        self._updateFVU()
        self._minimunSpanningTree()
        self._printSumary("Refine")

    def _minimunSpanningTree(self):
        """Minimum Spanning Tree pelo algoritmo de Primm, baseado no livro
        Algoritmos, teoria e pratica de Cormen, et al.
        """

        mstHeap = heap.Heap()

        for node in self.nodes:
            hndl = mstHeap.push(float('inf'), node)
            node._mstHnd = hndl
            node._mstParent = None
            node.neighbors.clear()

        self.nodes[0]._mstHnd.changeKey(0)

        while not mstHeap.isEmpty():
            (k, node) = mstHeap.pop()
            for v in self.nodes:
                if v._mstHnd.isInHeap():
                    dist = node.distSq(v.refElem)
                    if dist < v._mstHnd.getKey():
                        v._mstHnd.changeKey(dist)
                        v._mstParent = node

        for node in self.nodes:
            if node._mstParent != None:
                node.neighbors.add(node._mstParent)
                node._mstParent.neighbors.add(node)
                node._mstParent = None
                node._mstHnd = None

        print('MST: step {0}'.format(self.numSteps))


class AbstractSOMNode(object):
    """Representa um nodo do SOM.
    """

    def __init__(self, nid, refElem, conf):
        """Inicializa a instancia.

        :param nid: Identificador do nodo.
        :param refElem: Vetor de referência do nodo.
        :param conf: Objeto de controle do som
        """

        self._id = nid
        self.refElem = self.elemCopy(refElem)
        self.conf = conf

        self.x = 0.0
        self.y = 0.0

        self.neighbors = set()

        self.resetElements()

    def elemCopy(self, elem):
        raise NotImplementedError()

    def getID(self):
        """Recupera o ID do nodo.
        """
        return self._id

    def iterNeighboors(self):
        """Pesquisa em largura dos vizinhos mais proximos.
        """
        depths = {}
        nodes = deque()

        depths[self] = (0, 1) 
        nextDepth = 1
        nextWeight = self.conf.linearNeighWeight(nextDepth)
        for node in self.neighbors:
            nodes.append(node)
            depths[node] = (nextDepth, nextWeight)

        while len(nodes) > 0:
            node = nodes.popleft()
            depth, weight = depths[node]
            nextDepth = depth + 1
            nextWeight = self.conf.linearNeighWeight(nextDepth)
            if nextWeight > 0:
                for child in node.neighbors:
                    if child not in depths:
                        depths[child] = (nextDepth, nextWeight)
                        nodes.append(child)
            yield (node, weight)
        

    def resetElements(self):
        """Esvazia a lista de elementos.
        """
        raise NotImplementedError()

    def dist(self, elem):
        return math.sqrt(self.distSq(elem))

    def distSq(self, elem):
        """Quadrado da distancia de elem ao vetor de referencia do nodo.
        """
        raise NotImplementedError()

    def insert(self, elem, distSq=None):
        """Insere um elemento na lista de elementos.
        """
        raise NotImplementedError()

    def _findMeanElement(self):
        """Encontra o elemento medio do conjunto de elementos.

        O método atualiza o campo _meanElement.
        """
        raise NotImplementedError()

    def getMeanElement(self):
        """Recupera o ponto medio dos pontos atribuidos a este nodo.
        """
        if self._meanElement == None:
            self._findMeanElement()

        return self._meanElement

    def _calcSumDistFromMeanSquared(self):
        raise NotImplementedError()

    def getSumDistFromMeanSquared(self):
        if self._sumDistFromMeanSq == None:
            self._calcSumDistFromMeanSquared()

        return self._sumDistFromMeanSq

    def getNumElements(self):
        raise NotImplementedError()

    def updateRefElem(self):
        raise NotImplementedError()

    def _getClosestElem(self):
        raise NotImplementedError()

    def divide(self, nid):
        """Divide este nodo em dois.

        :param nid: ID do nodo que dever ser criado

        :return: new node
        """

        mean = self.getMeanElement()
        closest = self._getClosestElem()

        if mean == None or closest == None:
            return None

        if self.distSq(mean) > self.conf.minChangeDistSq:
            newNodeRef = mean
        elif self.distSq(closest) > self.conf.minChangeDistSq:
            newNodeRef = closest
        else:
            return None

        n2 = self.__class__(nid, newNodeRef, self.conf)

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

