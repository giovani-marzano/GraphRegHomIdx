
import math
import random
import selfOrganizingMap as som

outer = [0, som.SOMap(lambda x,y: 0)]

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

    with open(fileName) as f:
        for line in f:
            dv = line.split()
            elem = []
            if len(dv) > 0:
                for i in indices:
                    elem.append(float(dv[i]))
                elements.append(elem)

    return elements

def writeDataFile(filename, elements):
    with open(filename,'w') as f:
        for elem in elements:
            for d in elem:
                f.write(str(d))
                f.write('\t')
            f.write('\n')
        

def writeSOMIterableElements(m, fileName):
    with open(fileName,'w') as fout:
        for node in m.nodes:
            nid = node.getID()
            for elem in node.elements:
                for d in elem:
                    fout.write(str(d))
                    fout.write('\t')
                fout.write(str(nid))
                fout.write('\n')
            fout.write('\n\n')

def writeSOMNodes(m, fileName):
    with open(fileName,'w') as fout:
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

def testSeeds():

    elements = readDatafile('seeds.txt', [0,1])

    m = som.SOMap(vectDist)
    m.elements = elements

    outer[1] = m

    m.trainAndGrow(0.1,10)

    writeSOMIterableElements(m, 'seedsRes.txt')

    return m

def randomCirc(cx,cy,raio):

    dis = random.uniform(0,raio)
    ang = random.uniform(0, 2*math.pi)

    return (cx + math.cos(ang) * dis,
        cy + math.sin(ang) * dis)

def createYCirculos(numSamples):

    circulos = [(0.0,-2.0,0.5),
        (0.0,0.0,0.5),
        (2.0,2.0,0.5),
        (-2.0,2.0,0.5)]

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

    m.trainAndGrow(0.1,10)

    writeSOMIterableElements(m, 'circulosRes.txt')
    writeSOMNodes(m, 'circulosNodes.txt')

    return m

createYCirculos(1200)
testCirculos()
#testSeeds()
