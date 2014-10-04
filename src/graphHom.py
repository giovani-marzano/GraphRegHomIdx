# coding: utf-8

import graph as gm
import itertools

def createImageEdges(graph, mapVert, mapTypeEdge):
    """
    :param graph: Grafo original como uma tupla (V, E, tgt, dst), onde:
        - V é o conjunto de vertices
        - E é o conjunto de arestas
        - src é um mapeamento de uma aresta em seu vértice de origem
        - dst é um mapeamento de uma aresta em seu vértice de destino

    :param mapVert: mapeamento de cada vétice do grafo original em um
        vértice do grafo de destino: fMapVert: V -> Vd.

    :param mapTypeEdge: mapeamento de cada aresta do grafo original em um tipo
        de aresta para o grafo destino. Arestas do grafo destino serão criadas
        de modo que duas arestas do grafo original com tipos diferentes não
        mapeiem em uma mesma aresta do grafo destino.
    """

    (V, E, src, dst) = graph

    edges = set()
    mapEOrigEImg = dict()
    
    for eOrig in E:
        eAux = (mapVert(src(eOrig)), mapVert(dst(eOrig)), mapTypeEdge(eOrig))
        edges.add(eAux)
        mapEOrigEImg[eOrig] = eAux

    verts = set()
    for vOrig in V:
        verts.add(mapVert(vOrig))

    def fSrcIm(edge):
        return edge[0]

    def fDstIm(edge):
        return edge[1]

    def fTypeIm(edge):
        return edge[2]

    def fMapEdgeOriImg(eOrig):
        return mapEOrigEImg[eOrig]

    graphIm = (verts, edges, fSrcIm, fDstIm)

    return (graphIm, fMapEdgeOriImg, fTypeIm)

def createAdjIn(adjOut):
    """Cria uma lista de adjacências de saída a partir de uma lista de
    adjacências de entrada.

    :param adjOut: Lista de conjuntos. Cada vértice é uma posição da lista e o
        conjunto representa os vértices destino das arestas que saem deste
        vértice.

    :return: Lista de adjacencias de entrada de um vértice.
    """

    adjIn = []
    for l in adjOut:
        adjIn.append(set())

    for n1 in range(len(adjOut)):
        for n2 in adjOut[n1]:
            adjIn[n2].add(n1)

    return adjIn

def regularEquivalence(graph):
    # Todos os vértices começam na classe de equivalência 0.
    # Iremos processar os vértices em sequência numérica e atribuiremos as
    # clases de tal forma que o número de uma classe seja igual ao número do
    # vértice de menor número pertencente àquela classe.
    classesAnt = {node:None for node in graph.nodes()}
    classesNow = {node:None for node in graph.nodes()}
    changed = True

    while changed:
        print(classesAnt)
        changed = False
        for n1 in graph.nodes():
            if classesNow[n1] is not None:
                continue

            classesNow[n1] = n1
            if classesNow[n1] != classesAnt[n1]:
                changed = True

            # Conjuntos das classes de equivalencia que possuem arestas
            # entrando e saindo de n1
            classesInN1 = {(classesAnt[v], r) for v, r in graph.inNeighnoors(n1) }
            classesOutN1 = {(classesAnt[v], r) for v, r in graph.outNeighboors(n1)}

            for n2 in graph.nodes():
                if classesAnt[n2] != classesAnt[n1]:
                    # Se dois vertices nao estavam na mesma classe é porque já
                    # foram considerados incompatíveis.
                    continue
                if classesNow[n2] is not None:
                    # O vértice n2 já foi atribuido a uma classe, portanto não
                    # precisa ser processado
                    continue

                # Conjuntos das classes de equivalencia que possuem arestas
                # entrando e saindo de n2
                classesInN2 = {(classesAnt[v], r) for v, r in graph.inNeighnoors(n2)}
                classesOutN2 = {(classesAnt[v], r) for v, r in graph.outNeighboors(n2)}

                if classesInN1 == classesInN2 and classesOutN1 == classesOutN2:
                    classesNow[n2] = n1
                    if classesNow[n2] != classesAnt[n2]:
                        changed = True

        # Preparando os vetores de classes para a próxima iteração
        classesAux = classesAnt
        classesAnt = classesNow
        classesNow = classesAux
        for node in classesAux.keys():
            classesNow[node] = None

    return classesAnt

def fullMorphismFromEquiv(graph, classes):
    """Cria um homomorfismo de grafos cheio a partir de uma atribuição de
    vértices a classes de equivalência.

    :param adjOut: Lista de adjacências do grafo original.
    :param classes: Lista que mapeia cada véritice a sua classe.

    :return: grafo das classes de equivalencias.
    """

    newGraph = gm.MultiGraph()

    for src, tgt, rel in graph.edges():
        newGraph.addEdge( classes[src], classes[tgt], rel )

    return newGraph

if __name__ == "__main__":
    import random

    graph = gm.MultiGraph()

    graph.addEdge(0,2,0)
    graph.addEdge(0,2,1)
    graph.addEdge(0,3,0)
    graph.addEdge(3,0,0)
    graph.addEdge(3,4,0)
    graph.addEdge(3,4,1)

    classes = regularEquivalence(graph)
    graph.setNodeAttrFromDict('class', classes)

    graph.writeDotFile("original.dot")

    newGraph = fullMorphismFromEquiv(graph, classes)
    newGraph.writeDotFile("novo.dot")
