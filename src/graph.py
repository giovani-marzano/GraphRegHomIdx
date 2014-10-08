# coding: utf-8

import os.path
import xml.etree.ElementTree as ET

EDGE_RELATION_ATTR='_relation'

def regularEquivalence(graph):
    """Cria um mapeamento dos nodos do grafo a uma classe de equivalência
    regular.
    
    :param graph: Grafo a ser processado
    :return: mapa de nodos a um inteiro que representa a classe de
        equivalência a que pertence.
    """
    # Todos os vértices começam na classe de equivalência 0.
    # Iremos processar os vértices em sequência numérica e atribuiremos as
    # clases de tal forma que o número de uma classe seja igual ao número do
    # vértice de menor número pertencente àquela classe.
    nodeNumber = {}
    for n, node in enumerate(graph.nodes()):
        nodeNumber[node] = n
    classesAnt = {node:0 for node in graph.nodes()}
    classesNow = {node:None for node in graph.nodes()}
    changed = True

    while changed:
        changed = False
        for n1 in graph.nodes():
            if classesNow[n1] is not None:
                continue

            classesNow[n1] = nodeNumber[n1]
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
                    classesNow[n2] = classesNow[n1]
                    if classesNow[n2] != classesAnt[n2]:
                        changed = True

        # Preparando os vetores de classes para a próxima iteração
        classesAux = classesAnt
        classesAnt = classesNow
        classesNow = classesAux
        for node in classesAux.keys():
            classesNow[node] = None

    return classesAnt

class MultiGraph(object):
    def __init__(self):
        self._adjOut = {}
        self._adjIn = {}
        self.nodeAttrs = {}
        self.edgeAttrs = {}
        self.relations = set()
        self.nodeAttrSpecs = {}
        self.edgeAttrSpecs = {}

    def addNode(self, node):
        if node not in self._adjOut:
            self._adjOut[node] = set()
            self._adjIn[node] = set()
            self.nodeAttrs[node] = {}

    def removeNode(self, node):
        if node in self._adjOut:
            del self._adjOut[node]
        if node in self._adjIn:
            del self._adjIn[node]
        if node in self.nodeAttrs:
            del self.nodeAttrs[node]

    def removeNodeByAttr(self, attrName, attrValue):
        def filterNodes(node):
            return self.getNodeAttr(node, attrName) == attrValue

        toRemove = list(filter(filterNodes, self.nodes()))
        for node in toRemove:
            self.removeNode(node)

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
        self.relations.add(relation)

    def removeEdge(self, source, target, relation):
        self._adjOut[source].discard((target, relation))
        self._adjIn[target].discard((source, relation))
        edge = (source, target, relation)
        if edge in self.edgeAttrs:
            del self.edgeAttrs[edge]

    def removeEdgeByAttr(self, attrName, attrValue):
        def filterEdges(edge):
            return self.getEdgeAttr(edge, attrName) == attrValue

        toRemove = list(filter(filterEdges, self.edges()))
        for src, tgt, rel in toRemove:
            self.removeEdge(src, tgt, rel)

    def nodes(self):
        return self._adjOut.keys()

    def edges(self):
        return self.edgeAttrs.keys()

    def outNeighboors(self, node):
        return iter(self._adjOut[node])

    def inNeighnoors(self, node):
        return iter(self._adjIn[node])

    def hasNode(self, node):
        return node in self._adjOut

    def hasEdge(self, src, tgt, rel):
        return (src, tgt, rel) in self.edgeAttrs

    def addNodeAttrSpec(self, attrSpec):
        self.nodeAttrSpecs[attrSpec.name] = attrSpec

    def getNodeAttrSpec(self, attrName):
        return self.nodeAttrSpecs.get(attrName)

    def addEdgeAttrSpec(self, attrSpec):
        self.edgeAttrSpecs[attrSpec.name] = attrSpec

    def getEdgeAttrSpec(self, attrName):
        return self.edgeAttrSpecs.get(attrName)

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

    def setEdgeAttrFromDict(self, attrName, attrDict, default=None):
        for edge in self.edges():
            value = attrDict.get(edge, default)
            if value is not None:
                self.edgeAttrs[edge][attrName] = value

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

    def setNodeAttr(self, node, attr, value):
        self.nodeAttrs[node][attr] = value

    def getNodeAttr(self, node, attr, dflt=None):
        return self.nodeAttrs[node].get(attr, dflt)

    def setEdgeAttr(self, edge, attr, value):
        self.edgeAttrs[edge][attr] = value

    def getEdgeAttr(self, edge, attr, dflt=None):
        return self.edgeAttrs[edge].get(attr, dflt)

    def classifyNodesRegularEquivalence(self, classAttr='class'):
        """Cria um atributo de nodos que os particiona em classes de
        equivalência de uma equivalência regular.
        
        :param classAttr: Nome do atributo de nodos que conterá a classe de
        equivalência a que o nodo foi atribuído.
        """

        classes = regularEquivalence(self)
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
            return self.nodeAttrs[node].get(nodeClassAttr, nodeClassDflt)

        def edgeClassByAttr(edge):
            return self.edgeAttrs[edge].get(edgeClassAttr, edgeClassDflt)

        def edgeClassByRelation(edge):
            return edge[2]

        if nodeClassAttr is not None:
            nodeClass = nodeClassByAttr
        else:
            nodeClass = id

        if edgeClassAttr is not None:
            edgeClass = edgeClassByAttr
        else:
            edgeClass = edgeClassByRelation

        newGraph = MultiGraph()

        nodeHits = {}
        edgeHits = {}

        for node in self.nodes():
            newNode = nodeClass(node)
            newGraph.addNode(newNode)
            count = nodeHits.get(newNode,0)
            nodeHits[newNode] = count + 1

        for edge in self.edges():
            src, tgt, rel = edge
            newEdge = (nodeClass(src), nodeClass(tgt), edgeClass(edge))
            newGraph.addEdge(newEdge[0], newEdge[1], newEdge[2])
            count = edgeHits.get(newEdge, 0)
            edgeHits[newEdge] = count + 1

        if nodeClassAttr is not None:
            spec = self.getNodeAttrSpec(nodeClassAttr)
            if spec is not None:
                newGraph.addNodeAttrSpec(spec)
            for node in newGraph.nodes():
                newGraph.nodeAttrs[node][nodeClassAttr] = node

        if edgeClassAttr is not None:
            spec = self.getEdgeAttrSpec(edgeClassAttr)
            if spec is not None:
                newGraph.addEdgeAttrSpec(spec)
            for edge in newGraph.edges():
                newGraph.edgeAttrs[edge][edgeClassAttr] = edge[2]

        spec = AttrSpec('hitCount', 'int', 1)
        newGraph.setNodeAttrFromDict('hitCount', nodeHits, 0)
        newGraph.addNodeAttrSpec(spec)
        newGraph.setEdgeAttrFromDict('hitCount', edgeHits, 0)
        newGraph.addEdgeAttrSpec(spec)

        return newGraph

    def writeDotFile(self, filePath, classAttr='class'):
        writeDotFile(self, filePath, classAttr)

    def writeGraphml(self, filePath):
        writeGraphml(self, filePath)

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
                    graph.nodeAttrs[node].get(classAttr,0),
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

    def __init__(self, attr_name, attr_type, default=None):
        self.name = attr_name
        self.type = attr_type
        self.default = default

    def strToType(self, strValue):
        if self.type == 'float' or self.type == 'double':
            return float(strValue)
        if self.type == 'int' or self.type == 'long':
            return int(strValue)
        if self.type == 'boolean':
            return strValue.lower() in ('true','1','t')
        else:
            return strValue

    def setDefault(self,dfltValue):
        if isinstance(dfltValue, str):
            dfltValue = self.strToType(dfltValue)
        self.default = dfltValue

    def forceDefault(self):
        if self.type == 'float' or self.type == 'double':
            self.default = 0.0
        if self.type == 'int' or self.type == 'long':
            self.default = 0
        if self.type == 'boolean':
            self.default = False
        else:
            self.default = ''

def writeGraphml(mGraph, filePath, encoding="UTF-8"):
    root = ET.Element('graphml')
    root.set('xmlns',
            'http://graphml.graphdrawing.org/xmlns')
    root.set('xmlns:xsi',
            'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation',
            "http://graphml.graphdrawing.org/xmlns"+
            " http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd")

    nodeAttrIDs = {}
    edgeAttrIDs = {}
    dataCount = 0
    for attrName in mGraph.nodeAttrSpecs.keys():
        nodeAttrIDs[attrName] = 'd{}'.format(dataCount)
        dataCount += 1

    for attrName in mGraph.edgeAttrSpecs.keys():
        edgeAttrIDs[attrName] = 'd{}'.format(dataCount)
        dataCount += 1

    nodeIDs = {}
    for n, node in enumerate(mGraph.nodes()):
        if isinstance(node, int):
            nodeIDs[node] = 'n{}'.format(node)
        elif isinstance(node, str):
            nodeIDs[node] = node
        else:
            nodeIDs[node] = 'n{}'.format(n)

    baseName = os.path.basename(filePath)
    (graphName, ext) = os.path.splitext(baseName)
    if len(ext) == 0:
        filePath += '.graphml'

    for attrSpec in mGraph.nodeAttrSpecs.values():
        key  = ET.SubElement(root, 'key')
        key.set('id', nodeAttrIDs[attrSpec.name])
        key.set('for', 'node')
        key.set('attr.name', attrSpec.name)
        key.set('attr.type', attrSpec.type)
        if attrSpec.default is not None:
            default = ET.SubElement(key, 'default')
            default.text = str(attrSpec.default)
        
    for attrSpec in mGraph.edgeAttrSpecs.values():
        key  = ET.SubElement(root, 'key')
        key.set('id', edgeAttrIDs[attrSpec.name])
        key.set('for', 'edge')
        key.set('attr.name', attrSpec.name)
        key.set('attr.type', attrSpec.type)
        if attrSpec.default is not None:
            default = ET.SubElement(key, 'default')
            default.text = str(attrSpec.default)

    graph = ET.SubElement(root, 'graph')
    graph.set('id',graphName)
    graph.set('edgedefault','directed')
    for vert in mGraph.nodes():
        node = ET.SubElement(graph, 'node')
        node.set('id', nodeIDs[vert])
        for spec in mGraph.nodeAttrSpecs.values():
            value = mGraph.getNodeAttr(vert, spec.name, spec.default)
            if value != spec.default:
                data = ET.SubElement(node, 'data')
                data.set('key', nodeAttrIDs[spec.name])
                data.text = '{}'.format(value)
    for v1, v2, rel in mGraph.edges():
        edge = ET.SubElement(graph, 'edge')
        edge.set('source', nodeIDs[v1])
        edge.set('target', nodeIDs[v2])
        for spec in mGraph.edgeAttrSpecs.values():
            value = mGraph.getEdgeAttr((v1,v2,rel), spec.name, spec.default)
            if value != spec.default:
                data = ET.SubElement(edge, 'data')
                data.set('key', edgeAttrIDs[spec.name])
                data.text = '{}'.format(value)
    tree = ET.ElementTree(root)
    tree.write(filePath, encoding=encoding, xml_declaration=True, method="xml")

def loadGraphml(fileName, relationAttr=EDGE_RELATION_ATTR):
    xtree = ET.parse(fileName)

    namespaces = {'g':"http://graphml.graphdrawing.org/xmlns"}

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

            xdefault = xkey.find('g:default', namespaces)
            if xdefault is not None:
                attrSpec.setDefault(xdefault.text.strip())

            if relationKey is not None:
                # Forcing relation attribute to have a default
                edgeAttrs[relationKey].forceDefault()

    xgraph = xtree.find('g:graph', namespaces)
    graph = MultiGraph()

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
                    attrSpec.strToType(xdata.text))

    for xedge in xgraph.iterfind('g:edge', namespaces):
        src = xedge.get('source')
        tgt = xedge.get('target')
        rel = None
        if relationKey is not None:
            attrSpec = edgeAttrs[relationKey]
            rel = attrSpec.default
            xdata = xedge.find("g:data[@key='"+relationKey+"']", namespaces)
            if xdata is not None:
                rel = attrSpec.strToType(xdata.text)
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
                    attrSpec.strToType(xdata.text))

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