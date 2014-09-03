import random

def clusterize(adjList, maxIterations):
    """
    :param adjList: Lista de adjacencias com os pesos da aresta.
        Lista de listas de tuplas:
        adjList[n] -> [(v1, p1),(v2, p2)...]
    """
    nodes = range(len(adjList))
    classes = []

    for n in nodes:
        classes.append(n)

    random.shuffle(nodes)
    nIter = 0
    changed = True
    while changed and nIter < maxIterations:
        nIter += 1
        changed = False

        for node in nodes:
            nClasses = {}
            for (v, w) in adjList[node]:
                weight = nClasses.get(classes[v], 0)
                weight += w
                nClasses[classes[v]] = weight

            best = classes[node]
            bestW = float('-inf')
            for (c, w) in nClasses.items():
                if w > bestW:
                    bestW = w
                    best = c
            if best != classes[node]:
                classes[node] = best
                changed = True

        random.shuffle(nodes)

    print("nIter: {0}".format(nIter))

    return classes

def createDotGraph(adjList, classes, gvName="classes"):
    import gv

    gh = gv.graph(gvName)
    nodes = range(len(adjList))

    for v in nodes:
        nh = gv.node(gh, str(v))
        gv.setv(nh, 'label', "{0}/{1}".format(v,classes[v]))

    for v in nodes:
        for (u, w) in adjList[v]:
            if v < u:
                eh = gv.edge(gh, str(v), str(u))
                gv.setv(eh, 'weight', str(w))

    return gh

if __name__ == "__main__":
    import gv

    adjList = [
        [(1,1),(2,1),(3,1),(4,1),(5,1)],
        [(0,1),(2,1),(3,1),(4,1),(6,1)],
        [(0,1),(1,1),(3,1),(4,1),(7,1)],
        [(0,1),(1,1),(2,1),(4,1),(8,1)],
        [(0,1),(1,1),(2,1),(3,1),(9,1)],

        [(6,1),(7,1),(8,1),(9,1),(0,1)],
        [(5,1),(7,1),(8,1),(9,1),(1,1)],
        [(5,1),(6,1),(8,1),(9,1),(2,1)],
        [(5,1),(6,1),(7,1),(9,1),(3,1)],
        [(5,1),(6,1),(7,1),(8,1),(4,1)],
    ]

    classes = clusterize(adjList, 100)
    gh = createDotGraph(adjList, classes, "teste")
    gv.write(gh, "teste.dot")
