import os
import sys

sys.path.insert(1,os.path.join(sys.path[0],".."))

import math
import itertools
import random
import SOM.distanceBased as som
import SOM.vectorBased as somVet

import xml.etree.ElementTree as ET

from datetime import datetime

outer = [0, som.SOMap(lambda x,y: 0)]

data_dir = "data"

def vectDist(x,y):
    sumSq = 0.0

    # outer[0] += 1

    #if outer[0] % 1000 == 0:
    #    print outer[0], outer[1].numSteps

    for i in range(len(x)):
        diff = x[i] - y[i]
        sumSq += diff * diff

    return math.sqrt(sumSq)

def test1():
    elements = [1,2,3,4,5,6,7,21,22,23,24,25,26,27,42,43,43,44,45]

    def distFun(x,y):
        return abs(x-y)

    m = som.SOMap(distFun)
    m.elements = elements

    m.trainGrowingTree(0.6, 10)

    return m

def readDatafile(fileName, indices):
    elements = []

    with open(os.path.join(data_dir, fileName)) as f:
        for line in f:
            line = line.strip()
            if len(line) == 0 or line[0] == '#':
                continue

            dv = line.split()
            elem = []
            if len(dv) > 0:
                for i in indices:
                    elem.append(float(dv[i]))
                elements.append(elem)

    return elements

def writeDataFile(filename, elements):
    with open(os.path.join(data_dir,filename),'w') as f:
        for elem in elements:
            for d in elem:
                f.write(str(d))
                f.write('\t')
            f.write('\n')
        
def normalizeData(elements):

    numElem = len(elements)
    sumE = list(itertools.repeat(0, len(elements[0])))
    sumSqE = sumE[:]

    indices = range(len(elements[0]))
    for e in elements:
        for i in indices:
            sumE[i] += e[i]
            sumSqE[i] += e[i] * e[i]

    medias = map(lambda x: x/numElem, sumE)
    stdDev = map(lambda x,y: math.sqrt(x/numElem - (y*y)), sumSqE, medias)

    def normElem(elem):
        return map(lambda x,m,d: (x - m)/d, elem, medias, stdDev)

    return map(normElem, elements)

def normalizeFile(fileIN, listAttr, fileOut):
    elements = readDatafile(fileIN, listAttr)
    elements = normalizeData(elements)
    writeDataFile(fileOut, elements)

def writeSOMIterableElements(m, fileName):
    with open(os.path.join(data_dir,fileName),'w') as fout:
        for node in m.nodes:
            nid = node.getID()
            for elem in node.elements:
                for d in elem:
                    fout.write(str(d))
                    fout.write('\t')
                fout.write(str(nid))
                fout.write('\n')
            fout.write('\n\n')

def writeSOMVetElements(m, fileName):
    clusters = {}
    for elem in m.elements:
        (node, dist) = m.findNodeForElem(elem)
        nid = node.getID()
        listClus = clusters.setdefault(nid, [])
        listClus.append(elem)

    with open(os.path.join(data_dir,fileName),'w') as fout:
        for nid in sorted(clusters.keys()):
            for elem in clusters[nid]:
                for d in elem:
                    fout.write(str(d))
                    fout.write('\t')
                fout.write(str(nid))
                fout.write('\n')
            fout.write('\n\n')

def writeSOMNodes(m, fileName):
    with open(os.path.join(data_dir,fileName),'w') as fout:
        fout.write('#{0} {1} {2}\n'.format(
            m.FVU, len(m.nodes), m.numSteps))
        for node in m.nodes:
            for neigh in node.neighbors:
                for elem in [node.refElem, neigh.refElem]:
                    for d in elem:
                        fout.write(str(d))
                        fout.write('\t')
                    fout.write('\n')
                fout.write('\n')
            fout.write('\n')

def writeSOMGraphml(m, name, nodeAttrNames=None):
    edgeAttrNames = []
    nodeAttrKeys = {}
    edgeAttrKeys = {}

    def getNodeAttr(n):
        if type(n) is int:
            idx = n
        else:
            idx = nodeAttrKeys[n]
        key = "dn{0}".format(idx)
        return key

    def getEdgeAttr(n):
        if type(n) is int:
            idx = n
        else:
            idx = edgeAttrKeys[n]
        key = "de{0}".format(idx)
        return key

    def addNodeAttr(n):
        if n in nodeAttrKeys:
            raise Exception("ja existe node {}".format(n))

        nodeAttrKeys[n] = len(nodeAttrNames)
        nodeAttrNames.append(n)

    def addEdgeAttr(n):
        if n in edgeAttrKeys:
            raise Exception("ja existe edge {}".format(n))

        edgeAttrKeys[n] = len(edgeAttrNames)
        edgeAttrNames.append(n)

    if nodeAttrNames is None:
        nodeAttrNames = []
    else:
        aux = nodeAttrNames
        nodeAttrNames = []
        for i in range(len(aux)):
            addNodeAttr(aux[i])

    for i in range(len(nodeAttrNames),len(m.elements[0])):
        addNodeAttr("attr{0}".format(i))

    addNodeAttr('somNumElem')
    addNodeAttr('somX')
    addNodeAttr('somY')
    addEdgeAttr('somDist')

    root = ET.Element('graphml')
    root.set('xmlns','http://graphml.graphdrawing.org/xmlns')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation', "http://graphml.graphdrawing.org/xmlns"+
            " http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd")

    for i in range(len(nodeAttrNames)):
        key  = ET.SubElement(root, 'key')
        key.set('id', getNodeAttr(i))
        key.set('for', 'node')
        key.set('attr.name', nodeAttrNames[i])
        key.set('attr.type', 'double')

    for i in range(len(edgeAttrNames)):
        key  = ET.SubElement(root, 'key')
        key.set('id', getEdgeAttr(i))
        key.set('for', 'edge')
        key.set('attr.name', edgeAttrNames[i])
        key.set('attr.type', 'double')

    graph = ET.SubElement(root, 'graph')
    graph.set('id',name)
    graph.set('edgedefault','undirected')
    for vert in m.nodes:
        node = ET.SubElement(graph, 'node')
        node.set('id', 'n{}'.format(vert.getID()))
        for j in range(len(vert.refElem)):
            data = ET.SubElement(node, 'data')
            data.set('key', getNodeAttr(j))
            data.text = '{:f}'.format(vert.refElem[j])
        data = ET.SubElement(node, 'data')
        data.set('key', getNodeAttr('somNumElem'))
        data.text = '{}'.format(vert.getNumElements())
        data = ET.SubElement(node, 'data')
        data.set('key', getNodeAttr('somX'))
        data.text = '{}'.format(vert.x)
        data = ET.SubElement(node, 'data')
        data.set('key', getNodeAttr('somY'))
        data.text = '{}'.format(vert.y)
    for v1 in m.nodes:
        for v2 in v1.neighbors:
            if v1.getID() < v2.getID():
                edge = ET.SubElement(graph, 'edge')
                edge.set('source', 'n{}'.format(v1.getID()))
                edge.set('target', 'n{}'.format(v2.getID()))
                data = ET.SubElement(edge, 'data')
                data.set('key', getEdgeAttr('somDist'))
                data.text = '{}'.format(v1.dist(v2.refElem))
    tree = ET.ElementTree(root)
    tree.write(os.path.join(data_dir,name+'.graphml'))

def writeSOMDotFile(m, fileName):
    import gv

    gh = gv.graph(fileName)
    vh = gv.protonode(gh)
    gv.setv(vh, 'shape', 'circle')

    for i in range(len(m.nodes)):
        for j in range(i+1,len(m.nodes)):
            n1 = m.nodes[i]
            n2 = m.nodes[j]
            eh = gv.edge(gh, str(n1.getID()), str(n2.getID()))
            gv.setv(eh, 'len', str(math.sqrt(n1.distSq(n2.refElem))))
            if n2 not in n1.neighbors:
                gv.setv(eh, 'w', '0.1')
                gv.setv(eh, 'style', 'invis')

    gv.write(gh, os.path.join(data_dir, fileName+".dot"))

def normalizeSeeds():
    normalizeFile('seeds.txt', [0,1,2,3,4,5,6], 'seedsNorm.txt')

def testSeeds(listAttr, maxNodes, FVU, wTrain, wRef, maxSteps):

    elements = readDatafile('seedsNorm.txt', listAttr)

    m = som.SOMap(vectDist, "Seeds Dist")
    m.elements = elements

    outer[1] = m

    m.conf.FVU = FVU
    m.conf.maxNodes = maxNodes
    m.conf.neighWeightTrain = wTrain
    m.conf.neighWeightRefine = wRef
    m.conf.neighWeightRefine = wRef
    m.conf.maxStepsPerGeneration = maxSteps

    print("\n==== " + str(datetime.now()) + " ====")
    m.trainGrowingTree()
    print("\n==== " + str(datetime.now()) + " ====")

    writeSOMVetElements(m, 'seedsRes.txt')
    writeSOMNodes(m, 'seedsNodes.txt')
    #writeSOMDotFile(m, 'seedsTree')
    writeSOMGraphml(m, 'seedsTree')

    return m

def testVetSeeds(listAttr, maxNodes, FVU, wTrain, wRef, maxSteps):

    elements = readDatafile('seedsNorm.txt', listAttr)

    m = somVet.SOMap("Seeds Vet")
    m.elements = elements

    outer[1] = m

    m.conf.FVU = FVU
    m.conf.maxNodes = maxNodes
    m.conf.neighWeightTrain = wTrain
    m.conf.neighWeightRefine = wRef
    m.conf.maxStepsPerGeneration = maxSteps

    print("\n==== " + str(datetime.now()) + " ====")
    m.trainGrowingTree()
    print("\n==== " + str(datetime.now()) + " ====")

    writeSOMVetElements(m, 'seedsVetRes.txt')
    writeSOMNodes(m, 'seedsVetNodes.txt')
    #writeSOMDotFile(m, 'seedsVetTree')
    writeSOMGraphml(m, 'seedsVetTree')

    return m

def testVetSeedsGrid(listAttr, nrows, ncols, trainWeight, refineWeight, maxSteps):

    elements = readDatafile('seedsNorm.txt', listAttr)

    m = somVet.SOMap("Seeds Vet")
    m.elements = elements

    outer[1] = m

    m.conf.neighWeightTrain = trainWeight
    m.conf.neighWeightRefine = refineWeight
    m.conf.maxStepsPerGeneration = maxSteps

    print("\n==== " + str(datetime.now()) + " ====")
    m.trainHexGrid(nrows, ncols)
    print("\n==== " + str(datetime.now()) + " ====")

    writeSOMVetElements(m, 'seedsVetGridRes.txt')
    writeSOMNodes(m, 'seedsVetGridNodes.txt')
    writeSOMGraphml(m, 'seedsVetGridTree')

    g = somVet.convertSOMapToMultiGraph(m)
    g.writeGraphml(os.path.join('data','gseedsGrid'))

    return m

def randomCirc(cx,cy,raio):

    dis = random.uniform(0,raio)
    ang = random.uniform(0, 2*math.pi)

    return (cx + math.cos(ang) * dis,
        cy + math.sin(ang) * dis)

def createYCirculos(numSamples):

    circulos = [(0.0,-2.0,1.0),
        (0.0,0.0,1.0),
        (1.0,1.0,1.0),
        (-1.0,1.0,1.0)]

    elements = []

    for c in circulos:
        for n in range(numSamples/4):
            dv = randomCirc(*c)
            elements.append(dv)

    writeDataFile('circulos.txt', elements)    

def testCirculos():

    elements = readDatafile('circulos.txt', [0,1])

    m = som.SOMap(vectDist)
    m.elements = elements

    outer[1] = m

    m.trainGrowingTree(0.2,10)

    writeSOMIterableElements(m, 'circulosRes.txt')
    writeSOMNodes(m, 'circulosNodes.txt')

    return m

def testCirculosVet(maxNodes, FVU, wTrain, wRef):

    elements = readDatafile('circulos.txt', [0,1])

    m = somVet.SOMap()
    m.elements = elements

    outer[1] = m

    m.conf.FVU = FVU
    m.conf.maxNodes = maxNodes
    m.conf.neighWeightTrain = wTrain
    m.conf.neighWeightRefine = wRef

    m.trainGrowingTree()

    writeSOMVetElements(m, 'circulosVetRes.txt')
    writeSOMNodes(m, 'circulosVetNodes.txt')

    return m

#createYCirculos(1200)
#testCirculosVet(100, 0.05, 0.5, 0.5)
#testCirculosVet(10, 0.2, 0.5, 0.0)
normalizeSeeds()
#testSeeds([0,1,2,3,4,5,6], 10, 0.2, 0.5, 0.1, 20)
#m = testVetSeeds([0,1,2,3,4,5,6], 10, 0.2, 0.5, 0.1, 20)
m = testVetSeedsGrid([0,1,2,3,4,5,6], 5, 9, 0.5, 0, 20)
#testSeeds([0,1,2,3,4,5,6], 100, 0.02, 0.5, 0.5, 20)
#testVetSeeds([0,1,2,3,4,5,6], 100, 0.02, 0.5, 0.5, 20)
