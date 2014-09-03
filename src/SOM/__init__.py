# coding: utf-8
__author__='Giovani Melo Marzano'

import heap

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

    - MSTPeriod: De quantas em quantas iteracoes realizar o calculo da arvore
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
        self._mstHnd = None
        self._mstParent = None

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

    def _getNodeOldRefElem(self, node):
        raise NotImplementedError()

    def _updateNodes(self):
        """Atualiza os nodos com base nos elementos distribuídos.

        :return: Se houve atualização de algum nodo
        """

        changed = False
        maxUpdDist = 0
        updtDist = 0

        for node in self.nodes:
            oldRef = self._getNodeOldRefElem(node)
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

        trainSteps = 0

        cont = True
        while cont:
            trainSteps += 1
            cont = self._trainStep()
            if trainSteps > self.conf.maxStepsPerGeneration:
                cont = False
            if self.numSteps % self.conf.MSTPeriod == 0:
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

    def trainAndGrow(self):
        """Realiza o processo de treinar e aumentar o SOM.
        """

        print("\n---- " + self.ID +" ----")

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

