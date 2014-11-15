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
