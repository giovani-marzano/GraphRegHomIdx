# coding: utf-8

class NodeHandle(object):
    def __init__(self, graph):
        self.graph = graph

    def outNeighboors(self):
        """Return an iterator to the out neighboors of a node.
        """
        raise NotImplemented()

    def inNeighboors(self):
        """Return an iterator to the in neighboors of a node.
        """
        raise NotImplemented()

    def outEdges(self):
        """Return an iterator to the out edges of a node.
        """
        raise NotImplemented()

    def inEdges(self):
        """Return an iterator to the in edges of a node.
        """
        raise NotImplemented()

class EdgeHandle(object):
    def __init__(self, graph):
        self.graph = graph

    def source(self):
        """Return the edge's source node.
        """
        raise NotImplemented();

    def target(self):
        """Return the edge's target node.
        """
        raise NotImplemented();

    def relation(self):
        """Return the relation to which the edge belongs.
        """
        raise NotImplemented();

    def weight(self):
        """Return the edge's weight.
        """

class Graph(object):
    pass

def adjListToDotGraph(adjList, classes=None, directed=True, name="None"):
    import gv

    if classes:
        classesSet = list(set(classes))
        classesSet.sort()
        colorMap = {}
        hue = 0
        hueUpd = 1.0/len(classesSet)

        for c in classesSet:
            colorMap[c] = '{0:f},1.0,1.0'.format(hue)
            hue += hueUpd

    if directed:
        gh = gv.digraph(name)
    else:
        gh = gv.graph(name)

    nodes = range(len(adjList))

    for v in nodes:
        nh = gv.node(gh, str(v))
        if classes is not None:
            gv.setv(nh, 'fillcolor', colorMap[classes[v]])
            gv.setv(nh, 'style', 'filled')

    for v in nodes:
        for u in adjList[v]:
            if directed or v < u:
                eh = gv.edge(gh, str(v), str(u))

    return gh
