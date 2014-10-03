# coding: utf-8

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

def regularEquivalence(adjOut):
    adjIn = createAdjIn(adjOut)

    NO_CLASS = -1

    # Todos os vértices começam na classe de equivalência 0.
    # Iremos processar os vértices em sequência numérica e atribuiremos as
    # clases de tal forma que o número de uma classe seja igual ao número do
    # vértice de menor número pertencente àquela classe.
    classesAnt = [0 for _ in adjOut]
    classesNow = [NO_CLASS for _ in adjOut]
    changed = True

    while changed:
        changed = False
        for n1 in range(len(adjOut)):
            if classesNow[n1] != NO_CLASS:
                continue

            classesNow[n1] = n1
            if classesNow[n1] != classesAnt[n1]:
                changed = True

            # Conjuntos das classes de equivalencia que possuem arestas
            # entrando e saindo de n1
            classesInN1  = {classesAnt[v] for v in adjIn[n1] }
            classesOutN1 = {classesAnt[v] for v in adjOut[n1]}

            for n2 in range(n1 + 1, len(adjOut)):
                if classesAnt[n2] != classesAnt[n1]:
                    # Se dois vertices nao estavam na mesma classe é porque já
                    # foram considerados incompatíveis.
                    continue
                if classesNow[n2] != NO_CLASS:
                    # O vértice n2 já foi atribuido a uma classe, portanto não
                    # precisa ser processado
                    continue

                # Conjuntos das classes de equivalencia que possuem arestas
                # entrando e saindo de n2
                classesInN2  = {classesAnt[v] for v in adjIn[n2] }
                classesOutN2 = {classesAnt[v] for v in adjOut[n2]}

                if classesInN1 == classesInN2 and classesOutN1 == classesOutN2:
                    classesNow[n2] = n1
                    if classesNow[n2] != classesAnt[n2]:
                        changed = True

        # Preparando os vetores de classes para a próxima iteração
        classesAnt = classesNow
        classesNow = [NO_CLASS for _ in classesAnt]

    return classesAnt

def fullMorphismFromEquiv(adjOut, classes):
    """Cria um homomorfismo de grafos cheio a partir de uma atribuição de
    vértices a classes de equivalência.

    :param adjOut: Lista de adjacências do grafo original.
    :param classes: Lista que mapeia cada véritice a sua classe.

    :return: (newAdjOut, newClasses):
        - newAdjOut: Lista de adjacencias do novo grafo
        - newClasses: Lista que mapeia cada vértice do novo grafo a uma classe
            de equivalência do grafo original
    """

    # Criando vertices para corresponder às classes de equivalencia
    newClasses = list({ v for v in classes })
    classToNewNode = { c:n for n, c in enumerate(newClasses) }
    classToOldNodes = { c:set() for c in newClasses }
    for v, c in enumerate(classes):
        classToOldNodes[c].add(v)

    newAdjOut = [ set() for _ in newClasses ]
    for newNode, c in enumerate(newClasses):
        for oldNode1 in classToOldNodes[c]:
            for oldNode2 in adjOut[oldNode1]:
                newNode2 = classToNewNode[classes[oldNode2]]
                newAdjOut[newNode].add(newNode2)

    return newAdjOut, newClasses

if __name__ == "__main__":
    import gv
    from graph import adjListToDotGraph

    adjList = [
        {1,2,3,4,5,7},
        {4},
        {5},
        {6},
        {},
        {},
        {},
        {0,3,8,9},
        {9},
        {}
    ]

    classes = regularEquivalence(adjList)

    gOri = adjListToDotGraph(adjList, classes, True, "original")

    (newAdjList, newClasses) = fullMorphismFromEquiv(adjList, classes)

    gNew = adjListToDotGraph(newAdjList, newClasses)

    gv.write(gOri, "original.dot")
    gv.write(gNew, "novo.dot")
