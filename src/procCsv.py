
import csv
import math
import colorsys

CSV_CONFIG = {
    'delimiter': '\t',
    'lineterminator': '\n',
    'quotechar': '"',
    'escapechar': '\\',
    'doublequote': False,
    'quoting': csv.QUOTE_NONNUMERIC,
    'skipinitialspace': True
}

csv.register_dialect('tab-quoted', **CSV_CONFIG)

class PolyLinear(object):
    """Representa uma função composta por segmentos de linha.

    Os pontos que definem a função são uma lista de pares [(x0,y0), (x1,y1),
    ..., (xn,yn)] de forma que para valores de x entre x_k e x_k+1 o valor de y
    é obtido fazendo interpolação linear de (x_k,y_k) e (x_k+1, y_k+1).
    """

    def __init__(self, points):
        self.points = points

        if len(points) <= 1:
            raise ValueError("'points' must have at least 2 points.")

        x0 = float('-inf')
        for i, (x, y) in enumerate(points):
            if x <= x0:
                raise ValueError(
                    ("x value ({0}) in position {1} less or equal then "+
                    "x value ({2}) in position {3}").format(
                        x, i, x0, i-1))

    def __call__(self, x):
        k0 = -1

        for xp, yp in self.points:
            if xp > x:
                break
            k0 += 1

        if k0 < 0:
            k0 = 0
        elif k0 >= len(self.points) - 1:
            k0 = len(self.points) - 2

        k1 = k0 + 1

        x0, y0 = self.points[k0]
        x1, y1 = self.points[k1]

        a = (y1-y0)/(x1-x0)

        return a*(x-x0) + y0

def polyLinearFromNtiles(ntiles, oini, oend):
    """Create an PolyLinear where x values taken from n-tiles array and y values
    taken from the division of the oini-oend range in n-1 equal parts.

    Args:
        - ntiles: array with [xmin, p1, ..., pn-1, xmax] where pk are the values
          that divides the samples en k equal parts. For example, using
          quartiles we would have: [min, 1st quartile, median, 3th quartile,
          max]

        - oini: Min value of the output range.
        - oend: Max value of the output range.
    """

    delta = (oend-oini)/(len(ntiles)-1)

    points = [(ntiles[0],oini)]
    y = oini

    for x in ntiles:
        xk, yk = points[-1]
        if x > xk:
            points.append((x,y))
        y += delta

    return PolyLinear(points=points)

def processaCsv(fileIn, fileOut, procFuncs, outHeader=None, skipFirstRow=True):
    with open(fileIn, newline='') as fin, \
        open(fileOut, 'w', newline='') as fout:
        reader = csv.reader(fin, dialect='tab-quoted')
        writer = csv.writer(fout, dialect='tab-quoted')

        if skipFirstRow:
            for _ in reader:
                break

        if outHeader:
            writer.writerow(outHeader)

        for rowIn in reader:
            rowOut = []

            for func in procFuncs:
                r = func(rowIn)
                rowOut += r

            writer.writerow(rowOut)


def genColorFromNtiles(rowNum, ntiles, grays=False):
    """
    genColorFromNtiles(rowNum, ntiles, grays) ->
        colorValue([...,rowNum value, ...]) -> [color]
    """

    if grays:
        polyline = polyLinearFromNtiles(ntiles, 0.0, 1.0)
        def value2rgb(v):
            return colorsys.hsv_to_rgb(0.0, 0.0, v)
    else:
        polyline = polyLinearFromNtiles(ntiles, 2.0/3.0, 0.0)
        def value2rgb(v):
            return colorsys.hsv_to_rgb(v, 1.0, 1.0)

    def colorValue(rowIn):
        x = float(rowIn[rowNum])

        y = polyline(x)

        if y < 0: y = 0
        elif y > 1: y = 1

        r,g,b = value2rgb(y)
        r = round(r*255)
        g = round(g*255)
        b = round(b*255)

        color = "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

        return [color]

    return colorValue

def genNumElemToTamanho(rowNum, tamRef, numElemRef):
    """Gera uma função que converte numero de elementos em tamanho de nodo.

    genNumElemToTamanho(rowNum, tamRef, numElemRef) ->
            numElemToTamanho([...,numElem,...]) -> [tamanho]
    """

    alpha = (tamRef*tamRef)/numElemRef

    def numElemToTamanho(rowIn):
        """numElemToTamanho([...,numElem,...]) -> [tamanho]
        """

        numElem = float(rowIn[rowNum])

        return [math.sqrt(alpha*numElem)]

    return numElemToTamanho

def genIdentity(rowNum):
    """
    genIdentity(rowNum) ->
        identity([...,rowNum value,...]) -> [rowNum value]
    """

    def identity(rowIn):
        return [rowIn[rowNum]]

    return identity

if __name__ == '__main__':

    processaCsv('data/refsComLegenda.csv', 'data/procRefs.csv',
        outHeader=['node','tamanho',
            'Commenter_in_color',
            'Commenter_out_color',
            'Liker_in_color',
            'Liker_out_color',
            'Post_Author_in_color',
            'Post_Author_out_color',
            'Commenter_in_gray',
            'Commenter_out_gray',
            'Liker_in_gray',
            'Liker_out_gray',
            'Post_Author_in_gray',
            'Post_Author_out_gray',
            'Node silhouette_gray'
        ],
        procFuncs=[
            genIdentity(0),
            genNumElemToTamanho(8,100, 9910),
            genColorFromNtiles(1,[0.0, 0.0   , 9.15108e-9, 0.0117, 0.3082]),
            genColorFromNtiles(2,[0.0, 0.0   , 0.0512    , 0.1567, 0.6458]),
            genColorFromNtiles(3,[0.0, 0.0   , 2.36743e-8, 0.0314, 0.3758]),
            genColorFromNtiles(4,[0.0, 0.0385, 0.0810    , 0.1510, 0.5409]),
            genColorFromNtiles(6,[0.0, 0.0001, 0.0035    , 0.0972, 0.7917]),
            genColorFromNtiles(7,[0.0, 0.0   , 4.59648e-8, 0.3333, 0.4583]),
            genColorFromNtiles(1,[0.0, 0.0   , 9.15108e-9, 0.0117, 0.3082],True),
            genColorFromNtiles(2,[0.0, 0.0   , 0.0512    , 0.1567, 0.6458],True),
            genColorFromNtiles(3,[0.0, 0.0   , 2.36743e-8, 0.0314, 0.3758],True),
            genColorFromNtiles(4,[0.0, 0.0385, 0.0810    , 0.1510, 0.5409],True),
            genColorFromNtiles(6,[0.0, 0.0001, 0.0035    , 0.0972, 0.7917],True),
            genColorFromNtiles(7,[0.0, 0.0   , 4.59648e-8, 0.3333, 0.4583],True),
            genColorFromNtiles(5,[-0.2318, 0.0, 0.1003, 0.5156, 1.0],True),
        ])
