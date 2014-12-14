"""Implementação de *Silhouette coeficientes* descrito no artigo "Silhouettes: a
graphical aid to the interpretation and validation of cluster analysis" de Peter
J. Rousseuw (1986).
"""

import math

def eucliDist(v1, v2):
    """Distância euclidiana entre dois vetores.
    """
    dist = 0.0

    for d1, d2 in zip(v1, v2):
        dist += (d1 - d2)**2

    return math.sqrt(dist)

def calcCoeficiente(a,b):
    return (b - a)/max(a,b)

def evaluateClusters(elemValues, elemClusters, dissFun=eucliDist):
    """ 
    """

    clusterCount = {}
    for c in elemClusters.values():
        n = clusterCount.get(c, 0)
        clusterCount[c] = n + 1

    if len(clusterCount.keys()) <= 1:
        raise ValueError(
                "Impossible to calculate silhouettes with less then 2 clusters")


    silhouette = {e: 0.0 for e in elemClusters.keys()}
    clusterSilhouette = {c: 0.0 for c in clusterCount.keys()}

    for e, c in elemClusters.items():

        # If element 'e' is alone in its cluster, its silhouette is 0.0 and
        # there is nothing to compute
        if clusterCount[c] <= 1:
            continue

        dissClusters = {}
        for ej, cj in elemClusters.items():
            if ej != e:
                diss = dissClusters.get(cj, 0.0)
                diss += dissFun(elemValues[e], elemValues[ej])
                dissClusters[cj] = diss

        a = 0
        bmin = float('inf')
        for cj, diss in dissClusters.items():
            if cj == c:
                a = diss/(clusterCount[c] - 1)
            elif clusterCount[cj] > 0:
                b = diss/clusterCount[cj]
                if b < bmin:
                    bmin = b

        s = calcCoeficiente(a, bmin)
        silhouette[e] = s
        clusterSilhouette[c] += s

    # At this point clusterSilhouette holds for each cluster the sum of its
    # elements silhouettes

    totalSilhouette = 0.0
    numElem = 0
    for c, n in clusterCount.items():
        if n > 0:
            numElem += n
            sumSilhouette = clusterSilhouette[c]
            totalSilhouette += sumSilhouette
            clusterSilhouette[c] = sumSilhouette/n

    if numElem > 0:
        totalSilhouette = totalSilhouette/numElem

    return silhouette, clusterSilhouette, totalSilhouette

def evaluateClusters2(elemValues, elemClusters):
    """
    Args:
        elemValues: {elem: list of atributes}
        elemClusters: {elem: cluster ID}
    """

    ICOUNT=0
    ISUM=1
    ISUMSQ=2

    # clusterData[cluster][ICOUNT] -> count of elements in cluster
    # clusterData[cluster][ISUM] -> list of atributes sums
    # clusterData[cluster][ISUMSQ] -> list of atributes sums of squares
    clustData = {}

    vetLen = 0
    for e, vet in elemValues.items():
        vetLen = len(vet)
        break

    # Calculating the number of elements for each cluster and the sums and sum
    # of squares of elements values
    for e, c in elemClusters.items():
        if c not in clustData:
            clustData[c] = [0, [0.0 for i in range(vetLen)],
                [0.0 for i in range(vetLen)]]

        clustData[c][ICOUNT] += 1
        for i in range(vetLen):
            v = elemValues[e][i]
            clustData[c][ISUM][i] += v
            clustData[c][ISUMSQ][i] += v*v

    silhouette = {e: 0.0 for e in elemClusters.keys()}
    clusterSilhouette = {c: 0.0 for c in clustData.keys()}

    for e, c in elemClusters.items():
        # If element 'e' is alone in its cluster, its silhouette is 0.0 and
        # there is nothing to compute
        if clustData[c][ICOUNT] <= 1:
            continue

        eVet = elemValues[e]

        a = 0.0
        bmin = float('inf')
        for cj, cjData in clustData.items():
            x = 0.0
            for i in range(vetLen):
                x += cjData[ICOUNT]*eVet[i]*eVet[i]
                x += -2*eVet[i]*cjData[ISUM][i]
                x += cjData[ISUMSQ][i]

            if c == cj:
                a = x/(cjData[ICOUNT]-1)
            else:
                # Invariant: cjData[ICOUNT] >= 1
                # Proof: clustData was construct from elemClusters. A cluster
                # with no elements would not get an entry in clustData
                b = x/cjData[ICOUNT]
                if b < bmin:
                    bmin = b

        s = calcCoeficiente(a, bmin)
        silhouette[e] = s
        clusterSilhouette[c] += s

    # At this point clusterSilhouette holds for each cluster the sum of its
    # elements silhouettes

    totalSilhouette = 0.0
    numElem = 0
    for c, cData in clustData.items():
        n = cData[ICOUNT]
        if n > 0:
            numElem += n
            sumSilhouette = clusterSilhouette[c]
            totalSilhouette += sumSilhouette
            clusterSilhouette[c] = sumSilhouette/n

    if numElem > 0:
        totalSilhouette = totalSilhouette/numElem

    return silhouette, clusterSilhouette, totalSilhouette
