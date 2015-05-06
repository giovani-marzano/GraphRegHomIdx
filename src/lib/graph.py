# coding: utf-8

import os.path
import math
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from itertools import chain
from aggregate import NumericAggregator

EDGE_RELATION_ATTR='_relation'

# Tipos de equivalencia regular
REGULAR_TOTAL='total'
REGULAR_SOURCE='source'
REGULAR_TARGET='target'
REGULAR_TYPES = (REGULAR_TOTAL, REGULAR_SOURCE, REGULAR_TARGET)

def _trueFunc(*argv, **argd):
    """Função que só retorna True"""
    return True

def regularEquivalence(graph, preClassAttr=None, edgeClassAttr=None,
    regularType=REGULAR_TOTAL, ctrlFunc=_trueFunc):
    """Cria um mapeamento dos nodos do grafo a uma classe de equivalência
    regular.

    Args:
        - graph: Grafo a ser processado
        - [preClassAttr]: Atributo de nodo que indica uma pré classificação dos
              nodos. O algoritmo considera esta classificação como classificação
              inicial.
        - [edgeClassAttr]: Atributo de aresta que indica a classe da aresta. Se
              'None', a relação da aresta será utilizada.
        - [regularType]: Tipo de equivalência regular a ser obtida:
            - REGULAR_TOTAL: Regularidade total
            - REGULAR_SOURCE: Regularidade parcial por origem das arestas
            - REGULAR_TARGET: Regularidade parcial por destino das arestas
        - [ctrlFunc]: Função que permite o acompanhamento e a interrupção
              prematura do algoritmo.

              ctrlFunc(itCount, classesNow, done) -> continue

                Args:
                    - itCount: Número da iteração atual começãndo em 1
                    - classesNow: Classificação dos nodos até o momento
                    - done: True se já se atingiu a classificação final
                    - newClassesParents: Mapa que associa a cada classe criada
                      nesta iteração à classe da iteração anterior a qual
                      pertencia.

                Return:
                    True: para que o algoritmo continue com a próxima iteração
                    False: para interromper o algoritmo

    Return:
        mapa de nodos a um inteiro que representa a classe de equivalência a que
        pertence.
    """

    # Determinando como obter a relação da aresta
    if edgeClassAttr is None:
        def edgeRel(src,tgt,rel):
            return rel
    else:
        def edgeRel(src,tgt,rel):
            return graph.getEdgeAttr((src, tgt, rel), edgeClassAttr)

    # Determinando se vai levar em conta arestas de saída e de entrada
    ignoreIn = False
    ignoreOut = False
    if regularType == REGULAR_SOURCE:
        ignoreIn = True
    elif regularType == REGULAR_TARGET:
        ignoreOut = True

    # Lista de tuplas (n, node) onde n é um numero único associado ao nodo.
    # Iremos processar os nodos em sequência numérica e atribuiremos as
    # clases de tal forma que o número de uma classe seja igual ao número do
    # nodo de menor número pertencente àquela classe.
    nodes = [(n+1, node) for n, node in enumerate(graph.nodes())]

    if preClassAttr is None:
        # Todos os nodos começam na classe de equivalência do primeiro nodo.
        classesAnt = {node:nodes[0][0] for _, node in nodes}
    else:
        # Dicionário que mapeia o valor do atributo de pre classificação para o
        # número do primeiro nodo que possui este valor de atributo. Isto é
        # feito pois o algoritmo utiliza os números dos nodos como
        # identificadores das classes geradas.
        attrClassNum = {}
        classesAnt = {}
        for num, node in nodes:
            attr = graph.getNodeAttr(node, preClassAttr)
            nodeClass = attrClassNum.setdefault(attr, num)
            classesAnt[node] = nodeClass

        # o mapeamento de atributos em classes não é mais necessário
        del attrClassNum

    classesNow = {node:None for _, node in nodes}
    changed = True
    keepGoing = True
    itCount = 1

    while keepGoing:
        # Mantem para esta iteração a classe de origem de cada nova classe
        # criada.
        newClassesParents = {}

        changed = False
        for nodeNumber, n1 in nodes:
            if classesNow[n1] is not None:
                continue

            classesNow[n1] = nodeNumber
            if classesNow[n1] != classesAnt[n1]:
                changed = True
                newClassesParents[classesNow[n1]] = classesAnt[n1]

            # Conjuntos das classes de equivalencia que possuem arestas
            # entrando e saindo de n1
            classesInN1 = {(classesAnt[v], edgeRel(v,n1,r)) for v, r in graph.inNeighboors(n1)}
            classesOutN1 = {(classesAnt[v], edgeRel(n1,v,r)) for v, r in graph.outNeighboors(n1)}

            for _, n2 in nodes:
                if classesAnt[n2] != classesAnt[n1]:
                    # Se dois vertices nao estavam na mesma classe é porque já
                    # foram considerados incompatíveis.
                    continue
                if classesNow[n2] is not None:
                    # O nodo n2 já foi atribuido a uma classe, portanto não
                    # precisa ser processado
                    continue

                # Conjuntos das classes de equivalencia que possuem arestas
                # entrando e saindo de n2
                classesInN2 = {(classesAnt[v], edgeRel(v,n2,r)) for v, r in graph.inNeighboors(n2)}
                classesOutN2 = {(classesAnt[v], edgeRel(n2,v,r)) for v, r in graph.outNeighboors(n2)}

                if ((ignoreIn or classesInN1 == classesInN2)
                        and ( ignoreOut or classesOutN1 == classesOutN2)):
                    classesNow[n2] = classesNow[n1]
                    if classesNow[n2] != classesAnt[n2]:
                        changed = True
        # end for n1
        keepGoing = ctrlFunc(itCount, classesNow, not changed, newClassesParents)

        keepGoing = keepGoing and changed
        itCount += 1

        # Preparando os vetores de classes para a próxima iteração
        classesAnt = classesNow
        classesNow = {node:None for _, node in nodes}

    return classesAnt

def fullMorphismStats(g, nodeClassF, edgeClassF):
    """Calcula as estatísticas do homomorfismo de grafo cheio induzido pelo
    grafo 'g' e as funções de mapeamento de nodos e arestas em classes de nodos
    e arestas respectivamente.

    Args:

    - g: Grafo domínio do homomorfismo
    - nodeClassF: Função que mapeia cada nodo do grafo em uma classe de nodos.
    - edgeClassF: Função que mapeia cada aresta do grafo em uma classe de
      aresta.

    Ret:

    - nodeHits: Dicionário que mapeia cada classe de nodos na imagem do
      homomorfismo à quantidade de nodos mapeadas nela.
    - edgeHits: Dicionário em que as chaves são as tuplas que representam as
      arestas geradas pelo homomorfismo e os valores são o número de arestas do
      grafo domínio mapeadas em cada aresta gerada.
    - edgeSrcHits: Dicionário que mapeia cada aresta criada pelo homomorfismo no
      número de nodos do grafo domínio que se mapeia em sua origem.
    - edgeTgtHits: Dicionário que mapeia cada aresta criada pelo homomorfismo no
      número de nodos do grafo domínio que se mapeia em seu destino.
    """

    nodeHits = {}
    edgeHits = {}
    edgeSrcSets = defaultdict(set)
    edgeTgtSets = defaultdict(set)

    for node in g.nodes():
        newNode = nodeClassF(node)
        hits = nodeHits.get(newNode,0)
        hits += 1
        nodeHits[newNode] = hits

    for edge in g.edges():
        src, tgt, rel = edge
        newEdge = (nodeClassF(src), nodeClassF(tgt), edgeClassF(edge))

        hits = edgeHits.get(newEdge,0)
        hits += 1
        edgeHits[newEdge] = hits

        edgeSrcSets[newEdge].add(src)
        edgeTgtSets[newEdge].add(tgt)

    edgeSrcHits = {e:len(s) for e,s in edgeSrcSets.items()}
    edgeTgtHits = {e:len(s) for e,s in edgeTgtSets.items()}

    return nodeHits, edgeHits, edgeSrcHits, edgeTgtHits

def calcEdgeRegIdx(nodeHits, edgeHits, edgeSrcHits, edgeTgtHits):
    edgeIdx = {}

    for edge, ec in edgeHits.items():
        ds = nodeHits[edge[0]]
        dt = nodeHits[edge[1]]
        ns = edgeSrcHits[edge]
        nt = edgeTgtHits[edge]

        edgeIdx[edge] = (ns + nt)/(ds + dt)

    return edgeIdx

def calcNodeRegIdx(nodeHits, edgeHits, edgeSrcHits, edgeTgtHits):
    nodeSumEC = {}
    nodeSumN = {}

    for edge, ec in edgeHits.items():
        ns = edgeSrcHits[edge]
        nt = edgeTgtHits[edge]

        s = nodeSumEC.get(edge[0],0)
        s += ec
        nodeSumEC[edge[0]] = s

        s = nodeSumEC.get(edge[1],0)
        s += ec
        nodeSumEC[edge[1]] = s

        s = nodeSumN.get(edge[0],0)
        s += ec*ns
        nodeSumN[edge[0]] = s

        s = nodeSumN.get(edge[1],0)
        s += ec*nt
        nodeSumN[edge[1]] = s

    nodeRegIdx = {}
    for node, d in nodeHits.items():
        ec = nodeSumEC.get(node, 0)
        n = nodeSumN.get(node,0)

        if ec > 0:
            # O nodo tem aresta incidente
            nodeRegIdx[node] = n/(d*ec)
        else:
            nodeRegIdx[node] = 1.0

    return nodeRegIdx

def calcGraphRegIdx(nodeHits, edgeHits, edgeSrcHits, edgeTgtHits):
    """Calcula o índice de regularidade de grafo para as estatísticas de
    homomorfismo cheio fornecidas.
    """

    edgeSumN = 0.0
    edgeSumD = 0.0

    for edge in edgeHits.keys():
        ec = edgeHits[edge]
        ns = edgeSrcHits[edge]
        nt = edgeTgtHits[edge]

        # edge = (src, tgt, rel)
        ds = nodeHits[edge[0]]
        dt = nodeHits[edge[1]]

        edgeSumN += ec*(ns+nt)
        edgeSumD += ec*(ds+dt)

    if edgeSumD <= 0:
        print('WARN: edgeSumD <= 0', edgeSumD)
        return 0.0
    else:
        return edgeSumN/edgeSumD

class MultiGraph(object):
    SCOPE_NODE = 'node'
    SCOPE_EDGE = 'edge'

    def __init__(self):
        self._adjOut = {}
        self._adjIn = {}
        self._numNodes = 0
        self._numEdges = 0
        self.nodeAttrs = {}
        self.edgeAttrs = {}
        self.relations = set()
        self.nodeAttrSpecs = {}
        self.edgeAttrSpecs = {}
        self.graphAttrSpecs = {}
        self.graphAttrs = {}

        self.attrs = {
            MultiGraph.SCOPE_NODE: self.nodeAttrs,
            MultiGraph.SCOPE_EDGE: self.edgeAttrs
        }

        self.attrSpecs = {
            MultiGraph.SCOPE_NODE: self.nodeAttrSpecs,
            MultiGraph.SCOPE_EDGE: self.edgeAttrSpecs
        }

        self.aggregators = {
            MultiGraph.SCOPE_NODE: {},
            MultiGraph.SCOPE_EDGE: {}
        }

    def addNode(self, node):
        if node not in self._adjOut:
            self._adjOut[node] = set()
            self._adjIn[node] = set()
            self._numNodes += 1

    def removeNode(self, node):
        if not self.hasNode(node):
            return

        edgesToRemove = []
        for v, r in self.outNeighboors(node):
            edgesToRemove.append((node, v, r))
        for v, r in self.inNeighboors(node):
            edgesToRemove.append((v, node, r))
        for s,t,r in edgesToRemove:
            self.removeEdge(s,t,r)

        if node in self._adjOut:
            del self._adjOut[node]
            self._numNodes -= 1
        if node in self._adjIn:
            del self._adjIn[node]

        for attrDict in self.nodeAttrs.values():
            if node in attrDict:
                del attrDict[node]

    def removeNodeByAttr(self, attrName, attrValue):
        def filterNodes(node):
            return self.getNodeAttr(node, attrName) == attrValue

        toRemove = list(filter(filterNodes, self.nodes()))
        for node in toRemove:
            self.removeNode(node)

    def addEdge(self, source, target, relation):
        if self.hasEdge(source, target, relation):
            # Aresta já existe
            return

        if source not in self._adjOut:
            self.addNode(source)
        if target not in self._adjOut:
            self.addNode(target)
        self._adjOut[source].add( (target, relation) )
        self._adjIn[target].add( (source, relation) )
        self._numEdges += 1
        self.relations.add(relation)

    def removeEdge(self, source, target, relation):
        if self.hasEdge(source, target, relation):
            self._adjOut[source].discard((target, relation))
            self._adjIn[target].discard((source, relation))
            self._numEdges -= 1
            edge = (source, target, relation)
            for attrDict in self.edgeAttrs.values():
                if edge in attrDict:
                    del attrDict[edge]

    def removeEdgeByAttr(self, attrName, attrValue):
        def filterEdges(edge):
            return self.getEdgeAttr(edge, attrName) == attrValue

        toRemove = list(filter(filterEdges, self.edges()))
        for src, tgt, rel in toRemove:
            self.removeEdge(src, tgt, rel)

    def nodes(self):
        return self._adjOut.keys()

    def getNumNodes(self):
        return self._numNodes

    def edges(self):
        for src in self._adjOut.keys():
            for tgt, rel in self._adjOut[src]:
                yield (src, tgt, rel)

    def getNumEdges(self):
        return self._numEdges

    def outNeighboors(self, node):
        """outNeighboors(node) -> (tgt1, rel), (tgt2, rel), ...
        """
        return iter(self._adjOut[node])

    def inNeighboors(self, node):
        """inNeighboors(node) -> (src1, rel), (src2, rel), ...
        """
        return iter(self._adjIn[node])

    def neighboors(self, node):
        """Retorna um iterador para todos os vizinhos de um nodo, tanto os de
        entrada como os de saída. É equivalente a considerar que as arestas não
        possuem direção.
        """
        return chain(self.outNeighboors(node), self.inNeighboors(node))

    def hasNode(self, node):
        return node in self._adjOut

    def hasEdge(self, src, tgt, rel):
        if src in self._adjOut:
            return (tgt, rel) in self._adjOut[src]
        else:
            return False

    def addGraphAttrSpec(self, attrSpec):
        self.graphAttrSpecs[attrSpec.name] = attrSpec

    def getGraphAttrSpec(self, attrName):
        return self.graphAttrSpecs.get(attrName)

    def removeGraphAttr(self, attrName):
        if attrName in self.graphAttrSpecs:
            del self.graphAttrSpecs[attrName]
        if attrName in self.graphAttrs:
            del self.graphAttrs[attrName]

    def addNodeAttrSpec(self, attrSpec):
        self.nodeAttrSpecs[attrSpec.name] = attrSpec

    def getNodeAttrSpec(self, attrName):
        return self.nodeAttrSpecs.get(attrName)

    def removeNodeAttr(self, attrName):
        if attrName in self.nodeAttrSpecs:
            del self.nodeAttrSpecs[attrName]
        if attrName in self.nodeAttrs:
            del self.nodeAttrs[attrName]

    def addEdgeAttrSpec(self, attrSpec):
        self.edgeAttrSpecs[attrSpec.name] = attrSpec

    def getEdgeAttrSpec(self, attrName):
        return self.edgeAttrSpecs.get(attrName)

    def removeEdgeAttr(self, attrName):
        if attrName in self.edgeAttrSpecs:
            del self.edgeAttrSpecs[attrName]
        if attrName in self.edgeAttrs:
            del self.edgeAttrs[attrName]

    def addAttrSpec(self, scope, attrSpec):
        self.attrSpecs[scope][attrSpecs.name] = attrSpec

    def getAttrSpec(self, scope, attrName):
        return self.attrSpecs[scope].get(attrName)

    def getNodeAttrValueSet(self, attrName, default=None):
        """Recupera o conjunto dos valores distintos de um atributo de nodo
        """
        attrDict = self.nodeAttrs.get(attrName)
        if attrDict is not None:
            valueSet = set(attrDict.values())
        else:
            valueSet = set()

        if default is not None:
            valueSet.add(default)

        return valueSet

    def getEdgeAttrValueSet(self, attrName, default=None):
        """Recupera o conjunto dos valores distintos de um atributo de aresta.
        """
        attrDict = self.edgeAttrs.get(attrName)
        if attrDict is not None:
            valueSet = set(attrDict.values())
        else:
            valueSet = set()

        if default is not None:
            valueSet.add(default)

        return valueSet

    def setNodeAttrFromDict(self, attrName, attrDict, default=None,
            attrType=None):
        self.nodeAttrs[attrName] = {}
        for node in self.nodes():
            value = attrDict.get(node, default)
            if value is not None:
                self.nodeAttrs[attrName][node] = value

        if attrType is not None:
            spec = AttrSpec(attrName, attrType)
            spec.default = default
            self.addNodeAttrSpec(spec)

    def setEdgeAttrFromDict(self, attrName, attrDict, default=None,
            attrType=None):
        self.edgeAttrs[attrName] = {}
        for edge in self.edges():
            value = attrDict.get(edge, default)
            if value is not None:
                self.edgeAttrs[attrName][edge] = value

        if attrType is not None:
            spec = AttrSpec(attrName, attrType)
            spec.default = None
            self.addEdgeAttrSpec(spec)

    def getNodeAttrNames(self):
        return set(self.nodeAttrs.keys())

    def getEdgeAttrNames(self):
        return set(self.edgeAttrs.keys())

    def getGraphAttrNames(self):
        return set(self.graphAttrs.keys())

    def setGraphAttr(self, attr, value):
        self.graphAttrs[attr] = value

    def getGraphAttr(self, attr, dflt=None):
        spec = self.graphAttrSpecs.get(attr)
        if spec is not None and spec.default is not None:
            dflt = spec.default
        return self.graphAttrs.get(attr, dflt)

    def setNodeAttr(self, node, attr, value):
        self.setElemAttr(MultiGraph.SCOPE_NODE, node, attr, value)

    def getNodeAttr(self, node, attr, dflt=None):
        return self.getElemAttr(MultiGraph.SCOPE_NODE, node, attr, dflt)

    def setEdgeAttr(self, edge, attr, value):
        self.setElemAttr(MultiGraph.SCOPE_EDGE, edge, attr, value)

    def getEdgeAttr(self, edge, attr, dflt=None):
        return self.getElemAttr(MultiGraph.SCOPE_EDGE, edge, attr, dflt)

    def getElemAttr(self, scope, elem, attr, dflt=None):
        if dflt is None:
            spec = self.attrSpecs[scope].get(attr)
            if spec is not None:
                dflt = spec.default
        return self.attrs[scope].get(attr,{}).get(elem, dflt)

    def setElemAttr(self, scope, elem, attr, value):
        attrDict = self.attrs[scope].setdefault(attr, {})
        attrDict[elem] = value

    def elements(self, scope):
        if scope == MultiGraph.SCOPE_NODE:
            return self.nodes()
        elif scope == MultiGraph.SCOPE_EDGE:
            return self.edges()
        else:
            raise ValueError('Invalid scope {0}'.format(scope))

    def hasAggregator(self, scope, name):
        """Verifica se existe agregator no escopo especificado com o nome
        fornecido.
        """
        return name in self.aggregators[scope]

    def addAggregator(self, scope, name, initValue=None):
        """Adiciona um novo agregador zerado ao grafo.

        Args:
            - scope: Escopo do agregador: SCOPE_EDGE ou SCOPE_NODE
            - name: Nome para o agregador
            - initValue: Valor de inicialização
        """
        if self.hasAggregator(scope, name):
            raise KeyError('Já existe agregador de nome {0}'.format(name))

        aggrMap = {}

        self.aggregators[scope][name] = aggrMap

        if initValue is not None:
            for elem in self.elements(scope):
                aggr = self.getElemAggregator(scope, elem, name)
                aggr += initValue

    def removeAggregator(self, scope, name):
        if scope not in self.aggregators:
            return

        if name not in self.aggregators[scope]:
            return

        del self.aggregators[scope][name]

    def createAggregatorFromAttribute(self, scope, attrName):
        """Cria um aggregador para os elementos do grafo que terá o mesmo nome
        do atributo fornecido e será inicializado com os valores deste atributo.

        Args:
            - scope: Escopo do agregador: SCOPE_EDGE ou SCOPE_NODE
            - name: Nome para o agregador
        """

        self.addAggregator(scope, attrName)
        for elem in self.elements(scope):
            v = self.getElemAttr(scope, elem, attrName)
            aggr = self.getElemAggregator(scope, elem, attrName)
            aggr += v

    def getAggregator(self, scope, name):
        """Recupera o mapa de agregadores de nome 'name' para o escopo de
        elementos indicado.

        Args:
            scope: Escopo de elementos do grafo
            name: Nome do agregador
        Return:
            Mapa de agregadores ou 'None' caso não exista
        """
        return self.aggregators[scope].get(name)

    def getElemAggregator(self, scope, elem, name):
        aggrMap = self.getAggregator(scope, name)

        if aggrMap is None:
            raise KeyError(
                'Aggregator "{0}" does not exists in scope "{1}"'.format(
                    name, scope))

        return aggrMap.setdefault(elem,NumericAggregator())

    def getAggregatorNames(self, scope):
        return set(self.aggregators[scope].keys())

    def createAttributesFromAggregator(self, scope, name, stats):
        if not set(stats).isubsetof(NumericAggregator.STAT_SET):
            raise ValueError('Invalid stats: {0}'.format(str(set(stats) -
                            NumericAggregator.STAT_SET)))

        aggrMap = self.getAggregator(scope, name)

        if aggrMap is None:
            raise KeyError(
                'There is no aggregator named "{0}" of scope "{1}"'.format(
                    name, scope))

        for stat in stats:
            statType = NumericAggregator.getStatType(stat)
            spec = AttrSpec(name+'_'+stat, statType)
            self.addAttrSpec(scope, spec)
            for elem in self.elements(scope):
                aggr = aggrMap.get(elem)
                if aggr:
                    v = getattr(aggr, stat)
                self.setElemAttr(scope, elem, spec.name, v)

    def classifyNodesRegularEquivalence(self, classAttr='class',
            preClassAttr=None, edgeClassAttr=None,
            regularType=REGULAR_TOTAL, ctrlFunc=_trueFunc):
        """Cria um atributo de nodos que os particiona em classes de
        equivalência de uma equivalência regular.

        :param classAttr: Nome do atributo de nodos que conterá a classe de
        equivalência a que o nodo foi atribuído.
        """

        classes = regularEquivalence(self, preClassAttr=preClassAttr,
                edgeClassAttr=edgeClassAttr, regularType=regularType,
                ctrlFunc=ctrlFunc)
        spec = AttrSpec(classAttr,'int')
        self.addNodeAttrSpec(spec)
        self.setNodeAttrFromDict(classAttr, classes)

    def spawnFromClassAttributes(self, nodeClassAttr=None, edgeClassAttr=None,
            nodeClassDflt=None, edgeClassDflt=None):
        """Cria um novo grafo cujos nodos são as classes de equivalência de
        nodos do grafo original e as relações das arestas são as classes de
        equivalência de arestas do grafo original de tal forma que o mapeamento
        do grafo original para o novo seja um homomorfismo de grafos. As classes
        de equivalência são definidas pelos valores dos atributos de nodos e de
        arestas fornecidos.

        O grafo gerado possui os seguintes atributos:

            Nodos:
                - O mesmo de 'nodeClassAttr' se este não for None
                - node_count: Contagem dos nodos originais mapeados em cada nodo
                      destino
            Arestas:
                - O valor de 'edgeClassAttr', se tiver sido configurado, ou
                  'relation', caso contrário
                - edge_count: Contagem de arestas mapeadas nesta aresta.
                - edge_srcCount: Numero de nodos originais distintos que são
                      origens das arestas mapeadas nesta aresta.
                - edge_tgtCount: Numero de nodos originais distintos que são
                      destinos das arestas mapeadas nesta aresta.

        :param nodeClassAttr: Atributo de nodos que indica para cada nodo sua
            classe. Se for None será assumido que cada nodo é sua própria
            classe.
        :param edgeClassAttr: Atributo de aresta que indica a classe da aresta.
            Se for None será assumido que a relação original da aresta é sua
            classe.
        :param nodeClassDflt: Classe default para nodos que não possuirem o
            atributo 'nodeClassAttr' setado.
        :param edgeClassDflt: Classe default para arestas que não possuirem o
            atributo 'edgeClassAttr' setado.

        :return: Grafo gerado
        """
        def nodeClassByAttr(node):
            return self.getNodeAttr(node, nodeClassAttr, nodeClassDflt)

        def nodeIdentity(node):
            return node

        def edgeClassByAttr(edge):
            return self.getEdgeAttr(edge, edgeClassAttr, edgeClassDflt)

        def edgeClassByRelation(edge):
            return edge[2]

        if nodeClassAttr is not None:
            nodeClass = nodeClassByAttr
        else:
            nodeClass = nodeIdentity

        if edgeClassAttr is not None:
            edgeClass = edgeClassByAttr
            relationAttr = edgeClassAttr
        else:
            edgeClass = edgeClassByRelation
            relationAttr = 'relation'

        newGraph = MultiGraph()

        nodeAggrNames = self.getAggregatorNames(self.SCOPE_NODE)
        edgeAggrNames = self.getAggregatorNames(self.SCOPE_EDGE)

        for name in nodeAggrNames:
            newGraph.addAggregator(self.SCOPE_NODE, name)
        for name in edgeAggrNames:
            newGraph.addAggregator(self.SCOPE_EDGE, name)

        # Estatísticas de regularidade
        nodeHits, edgeHits, edgeSrcHits, edgeTgtHits = fullMorphismStats(self,
                nodeClass, edgeClass)

        for node in self.nodes():
            newNode = nodeClass(node)
            newGraph.addNode(newNode)

            for aggr in nodeAggrNames:
                v = self.getElemAggregator(self.SCOPE_NODE, node, aggr)
                vnew = newGraph.getElemAggregator(self.SCOPE_NODE, newNode,
                        aggr)
                vnew += v

        for edge in self.edges():
            src, tgt, rel = edge
            newEdge = (nodeClass(src), nodeClass(tgt), edgeClass(edge))
            newGraph.addEdge(newEdge[0], newEdge[1], newEdge[2])

            for aggr in edgeAggrNames:
                v = self.getElemAggregator(self.SCOPE_EDGE, edge, aggr)
                vnew = newGraph.getElemAggregator(self.SCOPE_EDGE, newEdge,
                        aggr)
                vnew += v

        if nodeClassAttr is not None:
            spec = self.getNodeAttrSpec(nodeClassAttr)
            if spec is not None:
                newGraph.addNodeAttrSpec(spec)
            for node in newGraph.nodes():
                newGraph.setNodeAttr(node, nodeClassAttr, node)

        # TODO: poderíamos gerar nomes que garantissem que não entrarão em
        # conflito com algum nome de atrinuto fornecido.

        spec = AttrSpec(relationAttr, 'string')
        if spec is not None:
            newGraph.addEdgeAttrSpec(spec)
        for edge in newGraph.edges():
            newGraph.setEdgeAttr(edge, relationAttr, str(edge[2]))

        newGraph.setNodeAttrFromDict('node_count', nodeHits,
                default=0, attrType=int)
        newGraph.setEdgeAttrFromDict('edge_srcCount', edgeSrcHits,
                default=0, attrType=int)
        newGraph.setEdgeAttrFromDict('edge_tgtCount', edgeTgtHits,
                default=0, attrType=int)
        newGraph.setEdgeAttrFromDict('edge_count', edgeHits,
                default=0, attrType=int)

        return newGraph

    def writeDotFile(self, filePath, classAttr='class'):
        writeDotFile(self, filePath, classAttr)

    def writeGraphml(self, filePath):
        writeGraphml(self, filePath)

    def extractNodeFeatureVectors(self, attrs):
        """Cria um dicionário que maeia cada nodo a um vetor com os valores dos
        atributos fornecidos.

        :param attrs: Lista com os nomes dos atributos que devem compor o vetor
            de cada nodo.

        :return: Dicionário que mapeia cada nodo a seu vetor de valores
        """
        featureVectors = {}

        for node in self.nodes():
            vector = []
            for attr in attrs:
                vector.append(self.getNodeAttr(node, attr))

            featureVectors[node] = vector

        return featureVectors

    def extractEdgeFeatureVectors(self, attrs):
        """Cria um dicionário que maeia cada aresta a um vetor com os valores dos
        atributos fornecidos.

        :param attrs: Lista com os nomes dos atributos que devem compor o vetor
            de cada aresta.
        """
        featureVectors = {}

        for edge in self.edges():
            vector = []
            for attr in attrs:
                vector.append(self.getEdgeAttr(edge, attr))

            featureVectors[edge] = vector

        return featureVectors

def writeDotFile(graph, filePath, classAttr='class'):
    nodeColor = {}
    edgeColor = {}
    if classAttr is not None:
        classesSet = graph.getNodeAttrValueSet(classAttr, 0)
        hue = 0
        hueUpd = 1.0/len(classesSet)

        for c in classesSet:
            nodeColor[c] = '{0:f},1.0,1.0'.format(hue)
            hue += hueUpd
    else:
        classesSet = set([0])

    if len(graph.relations) > 0:
        hue = 0
        hueUpd = 1.0/len(graph.relations)
        for r in graph.relations:
            edgeColor[r] = '{0:f},1.0,0.5'.format(hue)
            hue += hueUpd

    baseName = os.path.basename(filePath)
    (graphName, ext) = os.path.splitext(baseName)
    if len(ext) == 0:
        filePath += '.dot'

    with open(filePath, 'w') as f:
        f.write("digraph {0} {{\n".format(graphName))

        f.write('  node [label="\\N", style=filled];\n')

        for node in graph.nodes():
            f.write('  "{0}" [fillcolor="{1}"];\n'.format(
                node,
                nodeColor.get(
                    graph.getNodeAttr(node, classAttr, 0),
                    '0.0,0.0,1.0')
                )
            )

        for node in graph.nodes():
            for node2, rel in graph.outNeighboors(node):
                f.write('  "{0}" -> "{1}" [color="{2}"];\n'.format(node, node2,
                            edgeColor.get(rel,'0.0,0.0,1.0')))

        f.write('}\n')

class AttrSpec(object):
    VALID_TYPES = ('float','double','int','long','boolean','string')
    NUMERIC_TYPES = ('float','double','int','long')

    def __init__(self, attr_name, attr_type, default=None):
        self.name = attr_name

        if isinstance(attr_type, str):
            self.type = attr_type
        else:
            self.type = self.typeFromPythonType(attr_type)

        self.setDefault(default)

    def fromStr(self, strValue):
        if self.type == 'float' or self.type == 'double':
            return float(strValue)
        if self.type == 'int' or self.type == 'long':
            return int(strValue)
        if self.type == 'boolean':
            return strValue.lower() in ('true','1','t')
        else:
            return strValue

    @staticmethod
    def typeFromPythonType(pytype):
        if pytype == int:
            return 'int'
        elif pytype == float:
            return 'double'
        elif pytype == str:
            return 'string'
        elif pytype == bool:
            return 'boolean'
        else:
            raise ValueError('Python type "{0}" not recognized'.format(
                str(pytype)))

    def setDefault(self,dfltValue):
        if isinstance(dfltValue, str):
            dfltValue = self.fromStr(dfltValue.strip())
        self.default = dfltValue

    def getGraphmlType(self):
        return self.type

    def getArffType(self):
        if self.type in AttrSpec.NUMERIC_TYPES:
            return 'numeric'
        elif self.type == 'string':
            return 'string'
        elif self.type == 'boolean':
            return 'numeric'
        else:
            return None

    def getArffValue(self, value):
        if self.type == 'boolean':
            return int(value)
        else:
            return value

def _computeAggregateFromSums(attr, specList, attrDicts, counts, sums, sumSqs):
    attrNameCount = attr+'_count'
    specList.append(AttrSpec(attrNameCount, 'int',0))
    attrDicts[attrNameCount] = {}
    attrNameMean = attr+'_mean'
    specList.append(AttrSpec(attrNameMean, 'double',0.0))
    attrDicts[attrNameMean] = {}
    attrNameStdev = attr+'_stdev'
    specList.append(AttrSpec(attrNameStdev, 'double',0.0))
    attrDicts[attrNameStdev] = {}

    for key in counts[attr].keys():
        # Number of elements
        n = counts[attr][key]
        # Sum of elements
        s = sums[attr][key] * 1.0
        # Sum of squares of elements
        sSq = sumSqs[attr][key] * 1.0

        attrDicts[attrNameCount][key] = n

        if n > 0:
            mean = s/n
            stdev = math.sqrt(sSq/n - pow(mean,2))
            attrDicts[attrNameMean][key] = mean
            attrDicts[attrNameStdev][key] = stdev

def aggregateClassAttr(gOri, nodeClassAttr=None, edgeClassAttr=None, nodeAttrs=None, edgeAttrs=None):
    """Cria dados agregados de atributos agrupados pelos valores dos atributos
    classificadores de nodos e arestas fornecidos.

    :param nodeClassAttr: Atributo de nodo usado para classificar os nodos.
    :param edgeClassAttr: Atributo de aresta usado para classificar as arestas.
    :param nodeAttrs: Lista dos atributos de nodos que devem ser agregados.
    :param edgeAttrs: Lista dos atributos de arestas que devem ser agregados.

    :return: (attrNodes, attrEdges, specNodes, specEdges), onde:

        attrNodes: Dicionario que associa cada atributo gerado a um dicionário
            com o valor do atributo para cada nodo.
        attrEdges: Mesmo que attrNodes para as arestas.
        specNodes: Lista de AttrSpecs que para os atributos de nodos gerados.
        specEdges: Mesmo que specNodes só que para arestas.

    Esta função visa fornecer a funcionalidade de uma agreção em SQL como a
    seguir::

        select count(*), avg(attr), stdev(attr) from nodes group by
        nodeClassAttr;
    """

    if nodeClassAttr is not None:
        nodeClassFun = lambda n: gOri.getNodeAttr(n, nodeClassAttr)
    else:
        nodeClassFun = lambda n: n
        nodeClassAttr='node'

    if edgeClassAttr is not None:
        edgeRelFun = lambda e: gOri.getEdgeAttr(e, edgeClassAttr)
    else:
        edgeRelFun = lambda e: e[2]
        edgeClassAttr = 'edge'

    if nodeAttrs == None:
        nodeAttrs = []
    if edgeAttrs == None:
        edgeAttrs = []

    edgeSrcSet = defaultdict(set)
    edgeTgtSet = defaultdict(set)
    nodeClassCounts = Counter()
    edgeClassCounts = Counter()
    nodeAttrCounts = defaultdict(Counter)
    nodeAttrSums = defaultdict(Counter)
    nodeAttrSumSqs = defaultdict(Counter)
    edgeAttrCounts = defaultdict(Counter)
    edgeAttrSums = defaultdict(Counter)
    edgeAttrSumSqs = defaultdict(Counter)

    for node in gOri.nodes():
        nodeClass = nodeClassFun(node)
        nodeClassCounts[nodeClass] += 1
        for attr in nodeAttrs:
            value = gOri.getNodeAttr(node, attr)
            if value is not None:
                nodeAttrCounts[attr][nodeClass] += 1
                nodeAttrSums[attr][nodeClass] += value
                nodeAttrSumSqs[attr][nodeClass] += value * value

    for (src, tgt, rel) in gOri.edges():
        srcClass = nodeClassFun(src)
        tgtClass = nodeClassFun(tgt)
        relClass = edgeRelFun((src, tgt, rel))
        edgeClass = (srcClass, tgtClass, relClass)
        edgeClassCounts[edgeClass] += 1
        edgeSrcSet[edgeClass].add(src)
        edgeTgtSet[edgeClass].add(tgt)
        for attr in edgeAttrs:
            value = gOri.getEdgeAttr((src, tgt, rel), attr)
            if value is not None:
                edgeAttrCounts[attr][edgeClass] += 1
                edgeAttrSums[attr][edgeClass] += value
                edgeAttrSumSqs[attr][edgeClass] += value * value

    # Computing node attrs
    nodeAttrDicts = {}
    nodeSpecs = []

    attrName = nodeClassAttr + '_count'
    nodeSpecs.append(AttrSpec(attrName, 'int',0))
    nodeAttrDicts[attrName] = dict(nodeClassCounts)

    for attr in nodeAttrs:
        _computeAggregateFromSums(attr, nodeSpecs, nodeAttrDicts, nodeAttrCounts,
                nodeAttrSums, nodeAttrSumSqs)

    # Computing edge attrs
    edgeAttrDicts = {}
    edgeSpecs = []

    attrName = edgeClassAttr + '_count'
    edgeSpecs.append(AttrSpec(attrName, 'int',0))
    edgeAttrDicts[attrName] = dict(edgeClassCounts)

    attrName = edgeClassAttr + '_srcCount'
    edgeSpecs.append(AttrSpec(attrName, 'int',0))
    edgeAttrDicts[attrName] = {}
    for edge, s in edgeSrcSet.items():
        edgeAttrDicts[attrName][edge] = len(s)

    attrName = edgeClassAttr + '_tgtCount'
    edgeSpecs.append(AttrSpec(attrName, 'int',0))
    edgeAttrDicts[attrName] = {}
    for edge, s in edgeTgtSet.items():
        edgeAttrDicts[attrName][edge] = len(s)

    for attr in edgeAttrs:
        _computeAggregateFromSums(attr, edgeSpecs, edgeAttrDicts, edgeAttrCounts,
                edgeAttrSums, edgeAttrSumSqs)

    return nodeAttrDicts, edgeAttrDicts, nodeSpecs, edgeSpecs

def addAttributeSetsToGraph(g, attrNodes={}, specNodes=[],
        attrEdges={}, specEdges=[]):

    for spec in specNodes:
        g.addNodeAttrSpec(spec)
    for spec in specEdges:
        g.addEdgeAttrSpec(spec)

    for attr, values in attrNodes.items():
        g.setNodeAttrFromDict(attr, values)

    for attr, values in attrEdges.items():
        g.setEdgeAttrFromDict(attr, values)

def weaklyConnectedComponents(g):
    """Associa a cada nodo do grafo a um número que representa a componente
    fracamente conexa a que o nodo pertence.

    :param g: grafo

    :return: Dicionário mapeando cada nodo à sua componente.
    """
    components = {}
    stack = []
    compNum = 0

    for node in g.nodes():
        if node in components:
            continue

        compNum += 1
        components[node] = compNum
        stack.append(node)

        while len(stack) > 0:
            n1 = stack.pop()

            for n2, r in g.neighboors(n1):
                if n2 in components:
                    continue
                components[n2] = compNum
                stack.append(n2)

    return components

def _createXmlKeyForAttrs(root, attrNames, attrSpecs, attrIds, forElem):
    for attr in attrNames:
        attrSpec = attrSpecs[attr]
        key  = ET.SubElement(root, 'key')
        key.set('id', attrIds[attrSpec.name])
        key.set('for', forElem)
        key.set('attr.name', attrSpec.name)
        key.set('attr.type', attrSpec.type)
        if attrSpec.default is not None:
            default = ET.SubElement(key, 'default')
            default.text = str(attrSpec.default)

def _createXmlDataForAttrs(root, attrNames, attrSpecs, attrIds, getAttrFun):
    for attr in attrNames:
        spec = attrSpecs[attr]
        value = getAttrFun(spec.name, spec.default)
        if value != spec.default:
            data = ET.SubElement(root, 'data')
            data.set('key', attrIds[spec.name])
            data.text = '{}'.format(value)

def writeGraphml(mGraph, filePath, encoding="UTF-8"):
    root = ET.Element('graphml')
    root.set('xmlns',
            'http://graphml.graphdrawing.org/xmlns')
    root.set('xmlns:xsi',
            'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation',
            "http://graphml.graphdrawing.org/xmlns"+
            " http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd")

    graphAttrs = sorted(mGraph.graphAttrSpecs.keys())
    graphAttrIDs = {}
    nodeAttrs = sorted(mGraph.nodeAttrSpecs.keys())
    nodeAttrIDs = {}
    edgeAttrs = sorted(mGraph.edgeAttrSpecs.keys())
    edgeAttrIDs = {}
    dataCount = 10
    for attrName in graphAttrs:
        graphAttrIDs[attrName] = 'd{}'.format(dataCount)
        dataCount += 1

    for attrName in nodeAttrs:
        nodeAttrIDs[attrName] = 'd{}'.format(dataCount)
        dataCount += 1

    for attrName in edgeAttrs:
        edgeAttrIDs[attrName] = 'd{}'.format(dataCount)
        dataCount += 1

    nodeIDs = {}
    for n, node in enumerate(mGraph.nodes()):
        if isinstance(node, int):
            nodeIDs[node] = '{}'.format(node)
        elif isinstance(node, str):
            nodeIDs[node] = node
        else:
            nodeIDs[node] = 'n{}'.format(n)

    baseName = os.path.basename(filePath)
    (graphName, ext) = os.path.splitext(baseName)
    if len(ext) == 0:
        filePath += '.graphml'

    _createXmlKeyForAttrs(root, graphAttrs, mGraph.graphAttrSpecs, graphAttrIDs,
            'graph')
    _createXmlKeyForAttrs(root, nodeAttrs, mGraph.nodeAttrSpecs, nodeAttrIDs,
            'node')
    _createXmlKeyForAttrs(root, edgeAttrs, mGraph.edgeAttrSpecs, edgeAttrIDs,
            'edge')

    graph = ET.SubElement(root, 'graph')
    graph.set('id',graphName)
    graph.set('edgedefault','directed')
    _createXmlDataForAttrs(graph, graphAttrs, mGraph.graphAttrSpecs,
            graphAttrIDs, mGraph.getGraphAttr)

    for vert in mGraph.nodes():
        node = ET.SubElement(graph, 'node')
        node.set('id', nodeIDs[vert])
        _createXmlDataForAttrs(node, nodeAttrs, mGraph.nodeAttrSpecs,
                nodeAttrIDs, lambda a, d: mGraph.getNodeAttr(vert, a, d))
    for v1, v2, rel in mGraph.edges():
        edge = ET.SubElement(graph, 'edge')
        edge.set('source', nodeIDs[v1])
        edge.set('target', nodeIDs[v2])
        _createXmlDataForAttrs(edge, edgeAttrs, mGraph.edgeAttrSpecs,
                edgeAttrIDs, lambda a, d: mGraph.getEdgeAttr((v1,v2,rel), a, d))

    tree = ET.ElementTree(root)
    tree.write(filePath, encoding=encoding, xml_declaration=True, method="xml")

def loadGraphml(fileName, relationAttr=EDGE_RELATION_ATTR):
    xtree = ET.parse(fileName)

    namespaces = {'g':"http://graphml.graphdrawing.org/xmlns"}

    graphAttrs = {}
    edgeAttrs = {}
    nodeAttrs = {}
    relationKey = None
    for xkey in xtree.iterfind('g:key',namespaces):
        attrName = xkey.get('attr.name')
        attrType = xkey.get('attr.type')
        if attrType in AttrSpec.VALID_TYPES:
            attrSpec = AttrSpec(attrName, attrType)
            if xkey.get('for') == 'edge':
                edgeAttrs[xkey.get('id')] = attrSpec
                if attrSpec.name == relationAttr:
                    relationKey = xkey.get('id')
            elif xkey.get('for') == 'node':
                nodeAttrs[xkey.get('id')] = attrSpec
            elif xkey.get('for') == 'graph':
                graphAttrs[xkey.get('id')] = attrSpec

            xdefault = xkey.find('g:default', namespaces)
            if xdefault is not None:
                attrSpec.setDefault(xdefault.text)

    xgraph = xtree.find('g:graph', namespaces)
    graph = MultiGraph()

    for xdata in xgraph.iterfind('g:data', namespaces):
        key = xdata.get('key')
        if key in graphAttrs:
            attrSpec = graphAttrs[key]
            value = attrSpec.fromStr(xdata.text)
            if value != attrSpec.default:
                graph.setGraphAttr(attrSpec.name, value)

    for xnode in xgraph.iterfind('g:node', namespaces):
        nid = xnode.get('id')
        graph.addNode(nid)
        for key in nodeAttrs.keys():
            if nodeAttrs[key].default is not None:
                attrSpec = nodeAttrs[key]
                graph.setNodeAttr(nid, attrSpec.name,
                    attrSpec.default)
        for xdata in xnode.iterfind('g:data', namespaces):
            key = xdata.get('key')
            if key in nodeAttrs:
                attrSpec = nodeAttrs[key]
                graph.setNodeAttr(nid, attrSpec.name,
                    attrSpec.fromStr(xdata.text))

    for xedge in xgraph.iterfind('g:edge', namespaces):
        src = xedge.get('source')
        tgt = xedge.get('target')
        rel = None
        if relationKey is not None:
            attrSpec = edgeAttrs[relationKey]
            rel = attrSpec.default
            xdata = xedge.find("g:data[@key='"+relationKey+"']", namespaces)
            if xdata is not None:
                rel = attrSpec.fromStr(xdata.text)
        else:
            rel = 0
            while graph.hasEdge(src,tgt,rel):
                rel += 1
        edge = (src, tgt, rel)
        graph.addEdge(src, tgt, rel)
        for key in edgeAttrs:
            if edgeAttrs[key].default is not None:
                attrSpec = edgeAttrs[key]
                graph.setEdgeAttr(edge, attrSpec.name,
                    attrSpec.default)
        for xdata in xedge.iterfind('g:data', namespaces):
            key = xdata.get('key')
            if key in edgeAttrs:
                attrSpec = edgeAttrs[key]
                graph.setEdgeAttr(edge, attrSpec.name,
                    attrSpec.fromStr(xdata.text))

    for attrSpec in graphAttrs.values():
        graph.addGraphAttrSpec(attrSpec)

    for attrSpec in nodeAttrs.values():
        graph.addNodeAttrSpec(attrSpec)

    for attrSpec in edgeAttrs.values():
        graph.addEdgeAttrSpec(attrSpec)

    return graph

if __name__ == "__main__":
    import random

    graph = MultiGraph()

    graph.addEdge(0,2,0)
    graph.addEdge(0,2,0)
    graph.addEdge(0,3,0)
    graph.addEdge(3,0,0)
    graph.addEdge(3,4,0)
    graph.addEdge(3,4,0)
    graph.addNode(5)
    graph.addEdge(0,5,0)
    graph.addEdge(3,5,0)
    graph.addEdge(0,6,0)
    graph.addEdge(6,3,0)
    graph.addEdge(6,5,0)
    graph.addEdge(6,2,0)
    graph.addEdge(6,4,0)
    graph.addEdge(5,3,0)
    graph.addEdge(5,6,0)
    graph.addEdge(5,0,0)

    classes = graph.classifyNodesRegularEquivalence('class')

    writeDotFile(graph, "original.dot")
    writeGraphml(graph, "original")

    newGraph = graph.spawnFromClassAttributes(nodeClassAttr='class')
    writeDotFile(newGraph, "novo.dot")
