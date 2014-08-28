
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

    graphIm = (verts, edges, fSrcIm, fSrcIm)

    return (graphIm, fMapEdgeOriImg, fTypeIm)
