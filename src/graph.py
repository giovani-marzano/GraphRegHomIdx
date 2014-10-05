# coding: utf-8

import os.path
import xml.etree.ElementTree as ET

EDGE_RELATION_ATTR='_relation'

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

    def getNodeAttrNames(self):
        names = set()
        for attrDict in self.nodeAttrs.values():
            for name in attrDict.keys():
                names.add(name)
        return names

    def getEdgeAttrNames(self):
        names = set()
        for attrDict in self.edgeAttrs.values():
            for name in attrDict.keys():
                names.add(name)
        return names

def writeDotFile(graph, filePath, classAttr='class'):
    colorMap = {}
    if classAttr is not None:
        classesSet = graph.getNodeAttrValueSet(classAttr, 0)
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

        for node in graph.nodes():
            f.write('  {0} [fillcolor="{1}"];\n'.format(
                node,
                colorMap.get(
                    graph.nodeAttrs[node].get(classAttr,0),
                    '0.0,0.0,1.0')
                )
            )

        for node in graph.nodes():
            for node2, rel in graph.outNeighboors(node):
                f.write('  {0} -> {1};\n'.format(node, node2))

        f.write('}}\n')

def writeGraphml(mGraph, filePath):
    root = ET.Element('graphml')
    root.set('xmlns',
            'http://graphml.graphdrawing.org/xmlns')
    root.set('xmlns:xsi',
            'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation',
            "http://graphml.graphdrawing.org/xmlns"+
            " http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd")

    nodeAttrNames = mGraph.getNodeAttrNames()
    edgeAttrNames = mGraph.getEdgeAttrNames()

    nodeAttrIDs = {}
    for n, attr in enumerate(nodeAttrNames):
        nodeAttrIDs[attr] = 'dn{}'.format(n)

    edgeAttrIDs = {}
    superEdgeAtts = edgeAttrNames | set([EDGE_RELATION_ATTR])
    for n, attr in enumerate(superEdgeAtts):
        edgeAttrIDs[attr] = 'de{}'.format(n)

    nodeIDs = {}
    for n, node in enumerate(mGraph.nodes()):
        nodeIDs[node] = 'n{}'.format(n)

    baseName = os.path.basename(filePath)
    (graphName, ext) = os.path.splitext(baseName)
    if len(ext) == 0:
        filePath += '.graphml'

    key  = ET.SubElement(root, 'key')
    key.set('id', edgeAttrIDs[EDGE_RELATION_ATTR])
    key.set('for', 'edge')
    key.set('attr.name', EDGE_RELATION_ATTR)
    key.set('attr.type', 'int')

    graph = ET.SubElement(root, 'graph')
    graph.set('id',graphName)
    graph.set('edgedefault','directed')
    for vert in mGraph.nodes():
        node = ET.SubElement(graph, 'node')
        node.set('id', nodeIDs[vert])
        #for j in range(len(vert.refElem)):
        #    data = ET.SubElement(node, 'data')
        #    data.set('key', getNodeAttr(j))
        #    data.text = '{:f}'.format(vert.refElem[j])
    for v1, v2, rel in mGraph.edges():
        edge = ET.SubElement(graph, 'edge')
        edge.set('source', nodeIDs[v1])
        edge.set('target', nodeIDs[v2])
        data = ET.SubElement(edge, 'data')
        data.set('key',
                edgeAttrIDs[EDGE_RELATION_ATTR])
        data.text = '{}'.format(rel)
    tree = ET.ElementTree(root)
    tree.write(filePath)
