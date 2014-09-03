import os
import sys

sys.path.insert(1,os.path.join(sys.path[0],".."))

import math
import itertools
import random
import SOM.distanceBased as som
import SOM.vectorBased as somVet

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

    m.trainAndGrow(0.6, 10)

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
    m.trainAndGrow()
    print("\n==== " + str(datetime.now()) + " ====")

    writeSOMVetElements(m, 'seedsRes.txt')
    writeSOMNodes(m, 'seedsNodes.txt')
    writeSOMDotFile(m, 'seedsTree')

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
    m.conf.neighWeightRefine = wRef
    m.conf.maxStepsPerGeneration = maxSteps

    print("\n==== " + str(datetime.now()) + " ====")
    m.trainAndGrow()
    print("\n==== " + str(datetime.now()) + " ====")

    writeSOMVetElements(m, 'seedsVetRes.txt')
    writeSOMNodes(m, 'seedsVetNodes.txt')
    writeSOMDotFile(m, 'seedsVetTree')

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

    m.trainAndGrow(0.2,10)

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

    m.trainAndGrow()

    writeSOMVetElements(m, 'circulosVetRes.txt')
    writeSOMNodes(m, 'circulosVetNodes.txt')

    return m

#createYCirculos(1200)
#testCirculosVet(100, 0.05, 0.5, 0.5)
#testCirculosVet(10, 0.2, 0.5, 0.0)
#normalizeSeeds()
#testSeeds([0,1,2,3,4,5,6], 10, 0.2, 0.5, 0.1, 20)
#testVetSeeds([0,1,2,3,4,5,6], 10, 0.2, 0.5, 0.1, 20)
testSeeds([0,1,2,3,4,5,6], 100, 0.02, 0.5, 0.5, 20)
testVetSeeds([0,1,2,3,4,5,6], 100, 0.02, 0.5, 0.5, 20)
