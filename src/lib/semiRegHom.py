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

#---------------------------------------------------------------------
# Definições
#---------------------------------------------------------------------

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

    """
    def __init__(self, logger, bestClassFileName=None, classFileName=None):
        if (bestClassFileName and classFileName
                and bestClassFileName == classFileName):
            bestClassFileName = 'best_' + bestClassFileName

        self.logger = logger
        self.classFileName = classFileName
        self.bestClassFileName = bestClassFileName
        self._classFile = None
        self._bestClassFile = None

        self.bestRegIdx = 0.0
        self.bestNodeClass = {}

    def begining(self, g, k, iMax):
        self.logger.info(
            "BEGIN ksemiRegularClass: {0} classes {1} iterations".format(
                k, iMax))

    def iteration(self, i, nodeClass, graphRegIdx, clsPatterns):
        self.logger.info("Iter {0} {1:.4f} {2:.4f} {3:.4f}".format(i,
                    graphRegIdx.ri, graphRegIdx.sri, graphRegIdx.tri))
        self._writeClasses(i, nodeClass)

        if graphRegIdx.ri >= self.bestRegIdx:
            self.bestRegIdx = graphRegIdx.ri
            self.bestNodeClass = nodeClass

    def ending(self):
        self.logger.info(
            'END ksemiRegularClass: best {0:.4f}'.format(self.bestRegIdx))
        self._writeBestClasses()

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
            self._bestClassFile.write('node\tclass\n')
            for node, cls in self.bestNodeClass.items():
                self._bestClassFile.write('{0}\t{1}\n'.format(node, cls))

def _createNodeClsF(nodeClass):
    def nodeClsF(node):
        return nodeClass[node]

    return nodeClsF

def _edgeClsF(edge):
    return edge[2]

def _actualizeClassPatterns(clsPatterns, patternToIdx, edgeRegIdx):
    for cls, vet in clsPatterns.items():
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

    for cls, vet in clsPatterns.items():
        normalizeVet(vet)

def _calcEdgeAndGraphRegIdx(g, nodeClass):
    regStats = gr.fullMorphismStats(g, _createNodeClsF(nodeClass), _edgeClsF)
    edgeStats = gr.calcPreRegIdxStats(*regStats)
    edgeRegIdx = gr.calcEdgeRegIdx(edgeStats)
    graphRegIdx = gr.calcGraphRegIdx(edgeStats)

    return edgeRegIdx, graphRegIdx

def ksemiRegularClass(g, k, iMax, visitor):
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
    pattIter = list(itertools.product(g.relations,(IN,OUT),range(1,k+1)))
    patternToIdx = {p:i for i, p in enumerate(pattIter)}

    # Criando classificação inicial
    nodeClass = {n: random.randint(1,k) for n in g.nodes()}

    # Criando vetores de padrao de conexão para as classes
    clsPatterns = {}
    for cls in range(1,k+1):
        pattVet = [0.0 for _ in patternToIdx]
        clsPatterns[cls] = pattVet

    visitor.begining(g, k, iMax)

    for iNum in range(iMax):
        # Atualizando os vetores de padrao de conexão das classes
        edgeRegIdx, graphRegIdx = _calcEdgeAndGraphRegIdx(g, nodeClass)
        _actualizeClassPatterns(clsPatterns, patternToIdx, edgeRegIdx)

        visitor.iteration(iNum, nodeClass, graphRegIdx, clsPatterns)

        newNodeClass = {}

        for node in nodeClass.keys():
            hasEdge = False
            vet = [0.0 for _ in patternToIdx]

            for nei, rel in g.outNeighboors(node):
                pat = (rel, OUT, nodeClass[nei])
                idx = patternToIdx[pat]
                vet[idx] += 1
                hasEdge = True

            for nei, rel in g.inNeighboors(node):
                pat = (rel, IN, nodeClass[nei])
                idx = patternToIdx[pat]
                vet[idx] += 1
                hasEdge = True

            # escolhendo nova classe para o nodo
            newCls = 0
            if hasEdge:
                maxRank = float('-inf')
                for cls, clsVet in clsPatterns.items():
                    # produto vetorial
                    rank = sum(map(lambda x: x[0]*x[1], zip(vet, clsVet)))
                    if rank > maxRank:
                        maxRank = rank
                        newCls = cls

            newNodeClass[node] = newCls

        nodeClass = newNodeClass

    # Estatisticas finais
    edgeRegIdx, graphRegIdx = _calcEdgeAndGraphRegIdx(g, nodeClass)
    visitor.iteration(iMax, nodeClass, graphRegIdx, clsPatterns)

    visitor.ending()

