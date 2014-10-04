# coding: utf-8

import os.path

class MultiGraph(object):
    def __init__(self):
        self._adjOut = {}
        self._adjIn = {}
        self.nodeAttrs = {}
        self.edgeAttrs = {}

    def addNode(self, node):
        if node not in self._adjOut:
            self._adjOut[node] = set()
            self._adjIn[node] = set()
            self.nodeAttrs[node] = {}

    def addEdge(self, source, target, relation):
        edgeTuple = (source, target, relation)

        if edgeTuple in self.edgeAttrs:
            # Aresta já existe
            return

        if source not in self._adjOut:
            self.addNode(source)
        if target not in self._adjOut:
            self.addNode(target)
        self._adjOut[source].add( (target, relation) )
        self._adjIn[target].add( (source, relation) )
        self.edgeAttrs[edgeTuple] = {}

    def nodes(self):
        return self._adjOut.keys()

    def edges(self):
        return self.edgeAttrs.keys()

    def outNeighboors(self, node):
        return iter(self._adjOut[node])

    def inNeighnoors(self, node):
        return iter(self._adjIn[node])

    def getNodeAttrValueSet(self, attrName, default=None):
        valueSet = set()
        for attrDict in self.nodeAttrs.values():
            valueSet.add(attrDict.get(attrName, default))

        return valueSet

    def setNodeAttrFromDict(self, attrName, attrDict, default=None):
        for node in self.nodes():
            value = attrDict.get(node, default)
            if value is not None:
                self.nodeAttrs[node][attrName] = value


    def writeDotFile(self, filePath, classAttr='class'):
        colorMap = {}
        if classAttr is not None:
            classesSet = self.getNodeAttrValueSet(classAttr, 0)
            hue = 0
            hueUpd = 1.0/len(classesSet)

            for c in classesSet:
                colorMap[c] = '{0:f},1.0,1.0'.format(hue)
                hue += hueUpd
        else:
            classesSet = set([0])

        baseName = os.path.basename(filePath)
        (graphName, ext) = os.path.splitext(baseName)
        if len(ext) == 0:
            filePath += '.dot'

        with open(filePath, 'w') as f:
            f.write("digraph {0} {{\n".format(graphName))

            f.write('  node [label="\\N", style=filled];\n')

            for node in self.nodes():
                f.write('  {0} [fillcolor="{1}"];\n'.format(
                    node,
                    colorMap.get(
                        self.nodeAttrs[node].get(classAttr,0),
                        '0.0,0.0,1.0')
                    )
                )

            for node in self.nodes():
                for node2, rel in self.outNeighboors(node):
                    f.write('  {0} -> {1};\n'.format(node, node2))

            f.write('}}\n')
