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

def createDotGraph(adjList, classes, gvName="classes", class2color=None):
    import gv

    gh = gv.graph(gvName)
    nodes = range(len(adjList))

    for v in nodes:
        nh = gv.node(gh, str(v))
        if class2color is not None:
            gv.setv(nh, 'label', '')
            gv.setv(nh, 'fillcolor', class2color(classes[v]))
            gv.setv(nh, 'style', 'filled')
        else:
            gv.setv(nh, 'label', "{0}/{1}".format(v,classes[v]))

    for v in nodes:
        for (u, w) in adjList[v]:
            if v < u:
                eh = gv.edge(gh, str(v), str(u))
                gv.setv(eh, 'weight', str(w))

    return gh

def createClass2ColorFun(classes):
    classSet = set(classes)
    colorMap = {}
    hue = 0
    hueUpd = 1.0/len(classSet)

    for c in classSet:
        colorMap[c] = '{0:f},1.0,1.0'.format(hue)
        hue += hueUpd

    def class2color(cls):
        return colorMap.get(cls,'0.0,0.0,0.0')

    return class2color

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
    class2color = createClass2ColorFun(classes)
    gh = createDotGraph(adjList, classes, "teste", class2color)
    gv.write(gh, "teste.dot")
