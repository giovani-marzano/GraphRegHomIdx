# coding: utf-8
"""Implementação de algoritmo que encontra uma classificação de vértices com um
número de classes fornecido que induz um homomorfismo cheio que seja
aproximadamente regular.
"""
#---------------------------------------------------------------------
# Importações
#---------------------------------------------------------------------
import graph as gr
import math
import random
import itertools
import logging
import heapq

#---------------------------------------------------------------------
# Definições
#---------------------------------------------------------------------

# Logger utilizado pelo modulo
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

def zeroVet(vet):
    for i in range(len(vet)):
        vet[i] = 0.0

def addIntoVet1(v1, v2):
    for i in range(len(v1)):
        v1[i] += v2[i]

class KSemiRegClassVisitor(object):
    """Implementação de um visitante para o algoritmo ksemiRegularClass.

    Funcionalidades:

    - Loga o progresso do algoritmo através do logger (modulo logging)
      fornecido.
    - Mantém a melhor classificação encontrada durante a execução.
    - Permite a persistência da melhor classificação em arquivo se o parâmetro
      bestClassFileName for configurado.
    - Permite a persistência de cada classificação encontrada em arquivo se o
      parâmetro classFileName for configurado.
    - É um context manager, podendo ser utilizado em um bloco with. Exemplo::

        with KSemiRegClassVisitor(logger, 'bestClass.csv') as visitor:
            ksemiRegularClass(g, k, iMax, visitor)

    Atributos:

    - bestRegIdxNodeClass: Dicionário com a melhor classificação de nodos
      encontrada de acordo com o índice de regularidade. É None se o algoritmo
      não tiver rodado ainda.
    - bestRankNodeClass: Dicionário com a melhor classificação de nodos
      encontrada de acordo com o rank. É None se o algoritmo não tiver rodado
      ainda.
    - bestRegIdx: Índice de regularidade de grafo da melhor classificação.

    """
    def __init__(self, logger=logger, bestClassFileName=None, classFileName=None):
        if (bestClassFileName and classFileName
                and bestClassFileName == classFileName):
            bestClassFileName = 'best_' + bestClassFileName

        self.logger = logger
        self.classFileName = classFileName
        self.bestClassFileName = bestClassFileName
        self._classFile = None
        self._bestClassFile = None

        self.bestRegIdx = 0.0
        self.bestRegIdxRank = 0.0
        self.bestRegIdxNodeClass = {}

        self.bestRank = 0.0
        self.bestRankRegIdx = 0.0
        self.bestRankNodeClass = {}

    def begining(self, g, k, iMax):
        self.logger.info(
            "BEGIN ksemiRegularClass: {0} classes {1} iterations".format(
                k, iMax))

    def iteration(self, g, i, nodeClass, clsPatterns, rank):
        regStats = gr.fullMorphismStats(g, _createNodeClsF(nodeClass), _edgeClsF)
        edgeStats = gr.calcPreRegIdxStats(*regStats)
        graphRegIdx = gr.calcGraphRegIdx(edgeStats)
        self.logger.info("Iter {0} {1:.4f} {2:.4f} {3:.4f} {4:.4f}".format(i,
                    graphRegIdx.ri, graphRegIdx.sri, graphRegIdx.tri, rank))
        self._writeClasses(i, nodeClass)

        if i == 0:
            self.logClassSimilarities(clsPatterns)

        if graphRegIdx.ri >= self.bestRegIdx:
            self.bestRegIdx = graphRegIdx.ri
            self.bestRegIdxNodeClass = nodeClass
            self.bestRegIdxRank = rank

        if rank >= self.bestRank:
            self.bestRank = rank
            self.bestRankRegIdx = graphRegIdx.ri
            self.bestRankNodeClass = nodeClass

    def ending(self):
        msg = 'Best by RI  : RI {0:.4f} Rank {1:.4f}'.format(self.bestRegIdx,
                self.bestRegIdxRank)
        self.logger.info(msg)
        msg = 'Best by Rank: RI {0:.4f} Rank {1:.4f}'.format(
                self.bestRankRegIdx, self.bestRank)
        self.logger.info(msg)
        self._writeBestClasses()

    def logClassSimilarities(self, clsPatterns):
        self.logger.debug('Class similarities:')
        for c1, v1 in enumerate(clsPatterns):
            sim = []
            for c2, v2 in enumerate(clsPatterns):
                sim.append(round(vetDotProduct(v1,v2),2))
            self.logger.debug('  %s: %s', str(c1), str(sim))

    def __enter__(self):
        """Context manager enter function.
        """
        self.openFiles()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.closeFiles()
        return False

    def openFiles(self):
        self.closeFiles()
        if self.classFileName:
            self._classFile = open(self.classFileName, 'w')
        if self.bestClassFileName:
            self._bestClassFile = open(self.bestClassFileName, 'w')

    def closeFiles(self):
        if self._classFile:
            self._classFile.close()
            self._classFile = None
        if self._bestClassFile:
            self._bestClassFile.close()
            self._bestClassFile = None

    def _writeClasses(self, i, nodeClass):
        if self._classFile:
            self._classFile.write('\n# ---- Iteration {0} ----\n\n'.format(i))
            for node, cls in nodeClass.items():
                self._classFile.write('{0}\t{1}\n'.format(node, cls))

    def _writeBestClasses(self):
        if self._bestClassFile:
            self._bestClassFile.write('node\tclass_regIdx\tclass_rank\n')
            for node, cls in self.bestRegIdxNodeClass.items():
                self._bestClassFile.write('{0}\t{1}\t{2}\n'.format(node, cls,
                    self.bestRankNodeClass[node]))

def _createNodeClsF(nodeClass):
    def nodeClsF(node):
        return nodeClass[node]

    return nodeClsF

def _edgeClsF(edge):
    return edge[2]

def _actualizeClassPatterns(clsPatterns, patternToIdx, edgeRegIdx):
    for vet in clsPatterns:
        for i in range(len(vet)):
            vet[i] = 0.0

    for (src, tgt, rel), regIdx in edgeRegIdx.items():
        # Padrao da classe origem para a de destino
        pat = (rel, OUT, tgt)
        idx = patternToIdx[pat]
        clsPatterns[src][idx] = regIdx.sri

        # Padrao da classe destino em relação à de origem
        pat = (rel, IN, src)
        idx = patternToIdx[pat]
        clsPatterns[tgt][idx] = regIdx.tri

    for vet in clsPatterns:
        normalizeVet(vet)

def _spreadPatterns(clsPatterns, alfa):
    spreadPatterns = []
    for pat in clsPatterns:
        spreadPatterns.append(list(pat))
        
    for c1, v1 in enumerate(spreadPatterns):
        for c2 in range(c1):
            v2 = spreadPatterns[c2]
            wp = vetDotProduct(v1,v2)
            vp = map(lambda x: wp*x, v2)
            for i, x in enumerate(vp):
                v1[i] = v1[i] - x
            normalizeVet(v1)

    for c, pat in enumerate(clsPatterns):
        for k, v in enumerate(spreadPatterns[c]):
            pat[k] = alfa*v + (1-alfa)*pat[k]
        normalizeVet(pat)

def _genNodesPatterns(g, nodeClass, patternToIdx):
    for node in nodeClass.keys():
        hasEdge = False
        vet = [0.0 for _ in patternToIdx]

        # OBS: Nas contabilizações abaixo estamos apenas setando com 1 os
        # padrões de conexão do nodo ao invés de acumular. Isto porque em testes
        # parece que desta forma (sem levar em conta o número de arestas) o
        # grafo resultante ficava mais limpo.
        pattValues = {}
        for nei, rel in g.outNeighboors(node):
            hasEdge = True
            pat = (rel, OUT, nodeClass[nei])
            v = pattValues.get(pat, 0)
            pattValues[pat] = v + 1
            # pattValues[pat] = 1

        for nei, rel in g.inNeighboors(node):
            hasEdge = True
            pat = (rel, IN, nodeClass[nei])
            v = pattValues.get(pat, 0)
            pattValues[pat] = v + 1
            # pattValues[pat] = 1

        for pat, v in pattValues.items():
            idx = patternToIdx[pat]
            vet[idx] = max(vet[idx], v)

        yield (node, vet, hasEdge)

class Toolbox(object):
    def __init__(self):

        self.doClassSpread = True

        # Probabilidade de escolher a melhor classe
        self._initPb = 1.0
        self._finalPb = 1.0
        self._incStartT = 0
        self._incStopT = 1

        # Taxas de atualização dos vetores das classes
        self.nodeAlfa = 0.10
        self.spreadAlfa = 0.10

    def configPbSchedule(self, initPb, finalPb, incStartT, incStopT):
        """Configure the propability change schedule.

        Args:

        - initPb: Initial probability.
        - finalPb: Final probability.
        - incStartT: Time (iteration) to start a linear increasing of the
          probability toward finalPb.
        - incStopT: Time (iteration) that the probability should reach the
          finalPb.
        """
        if initPb < 0.0 or initPb > 1.0:
            raise ValueError(
                'initPb ({0}) must be in [0.0, 1.0] interval.'.format(finalPb))

        if finalPb < 0.0 or finalPb > 1.0:
            raise ValueError(
                'finalPb ({0}) must be in [0.0, 1.0] interval.'.format(finalPb))

        if finalPb < initPb:
            raise ValueError(
                'finalPb ({0}) smaller then initPb ({1})'.format(finalPb,
                    initPb))

        if incStopT <= incStartT:
            raise ValueError(
                'incStopT ({0}) must be greater then incStartT ({1})'.format(
                    incStopT, incStartT))

        self._initPb = initPb
        self._finalPb = initPb
        self._incStartT = incStartT
        self._incStopT = incStopT

    def calcChoicePb(self, iNum):
        if iNum < self._incStartT:
            choicePb = self._initPb
        elif iNum > self._incStopT:
            choicePb = self._finalPb
        else:
            a = (self._finalPb - self._initPb)
            a = a/(self._incStopT - self._incStartT)
            choicePb = self._initPb + a*iNum
        return choicePb

    def generateInitialNodeClass(self, g, k):
        return {n: random.randrange(k) for n in g.nodes()}

    def actualizeClassPatterns(self, g, iNum, nodeClass, clsPatterns,
            patternToIdx):
        alfa = self.nodeAlfa

        newClsPat = []
        for clsPat in clsPatterns:
            newClsPat.append([0.0 for v in clsPat])

        for node, vet, hasEdge in _genNodesPatterns(g, nodeClass, patternToIdx):
            if hasEdge:
                normalizeVet(vet)
                cls = nodeClass[node]
                clsPat = newClsPat[cls]
                addIntoVet1(clsPat, vet)

        for cls, clsPat in enumerate(clsPatterns):
            normalizeVet(newClsPat[cls])
            for k, v in enumerate(newClsPat[cls]):
                clsPat[k] = alfa*v + (1-alfa)*clsPat[k]
            normalizeVet(clsPat)

        if self.doClassSpread:
            # Diferenciando um pouco os vetores das classes entre si
            _spreadPatterns(clsPatterns, self.spreadAlfa)


    def generateNewNodeClass(self, g, iNum, nodeClass, clsPatterns,
            patternToIdx):

        choicePb = self.calcChoicePb(iNum)

        newNodeClass = {}
        totalRank = 0.0
        countNodes = 0
        for node, vet, hasEdge in _genNodesPatterns(g, nodeClass, patternToIdx):
            # escolhendo nova classe para o nodo
            newCls = -1
            if hasEdge:
                normalizeVet(vet)
                rankHeap = []
                for cls, clsVet in enumerate(clsPatterns):
                    # produto vetorial
                    rank = vetDotProduct(vet, clsVet)
                    heapq.heappush(rankHeap,(-rank, cls))
                while len(rankHeap) > 1:
                    rank, cls = heapq.heappop(rankHeap)
                    if random.random() < choicePb:
                        newCls = cls
                        break
                if newCls < 0:
                    rank, newCls = heapq.heappop(rankHeap)

                # Acumulando os ranks, estamos subtraindo pois o rank foi
                # invertido para servir de chave na heap mínima
                totalRank -= rank

                # Contabilizamos apenas os nodos que possuem arestas, os que não
                # possuem serão agrupados no grupo -1
                countNodes += 1

            newNodeClass[node] = newCls

        if countNodes > 0:
            totalRank = totalRank/countNodes

        return newNodeClass, totalRank

toolbox = Toolbox()

def ksemiRegularClass(g, k, iMax, visitor, toolbox=toolbox):
    """Algoritmo que encontra uma classificação com *k* classes para os vértices
    do grafo *g* de forma que o homomorfismo induzido por esta classificação
    seja aproximadamente regular.

    Args:

    - g: Grafo cujos vértices serão classificados.
    - k: Número de classes que deverão ser geradas.
    - iMax: Número de iterações do algoritmo a serem realizadas.
    - visitor: Objeto visitante que possui métodos que serão chamados durante a
      execução do algoritmo. Ver classe KSemiRegClassVisitor para exemplo de
      implementação. Os métodos que devem existir no objeto são:
        - begining(g, k, iMax): Chamada antes do início do loop principal do
          algoritmo.
        - iteration(iNum, nodeClasses, graphRegIdx, edgeRegIdx): Chamada a cada
          iteração do algoritmo. Onde:
            - iNum: Número da iteração corrente.
            - nodeClasses: Dicionário com a atribuição de classes para os nodos.
            - graphRegIdx: tupla GraphRegIdx com os índices de regularidade de
              grafo induzidos pela classificação de nodos.
            - edgeRegIdx: dicionário de tuplas EdgeRegIdx com os índices de
              regularidade de aresta induzidos pela classificação de nodos.
        - ending(): Chamada ao final do algoritmo.
    """
    # Criando mapa de padrao de conexao para indice no vetor de padrao
    # Número de relações * 2 (entrada e saida) * número de classes (k)
    iterPatt = itertools.product(g.relations,(IN,OUT),range(k))
    patternToIdx = {p:i for i, p in enumerate(iterPatt)}

    # Criando classificação inicial
    nodeClass = toolbox.generateInitialNodeClass(g, k)

    # Criando vetores de padrao de conexão para as classes
    clsPatterns = []
    for cls in range(k):
        pattVet = [0.0 for _ in patternToIdx]
        clsPatterns.append(pattVet)

    visitor.begining(g, k, iMax)
    for iNum in range(iMax):
        # Atualizando os vetores de padrao de conexão das classes
        toolbox.actualizeClassPatterns(g, iNum, nodeClass, clsPatterns,
                patternToIdx)

        nodeClass, rank = toolbox.generateNewNodeClass(g, iNum, nodeClass,
                clsPatterns, patternToIdx)

        visitor.iteration(g, iNum, nodeClass, clsPatterns, rank)

    visitor.ending()
