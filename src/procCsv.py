#!/usr/bin/python3

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

def processaCsv(fileIn, fileOut,
        outHeader=None,
        procFuncs=[], filterFuncs=[]):

    with open(fileIn, newline='') as fin, \
        open(fileOut, 'w', newline='') as fout:

        dialectIn = csv.Sniffer().sniff(fin.read(2048))
        fin.seek(0)
        reader = csv.reader(fin, dialect=dialectIn)
        writer = csv.writer(fout, dialect='tab-quoted')

        rowNum = 0

        if outHeader:
            writer.writerow(outHeader)

        for rowIn in reader:
            doRow = True
            for filt in filterFuncs:
                if not filt(rowNum, rowIn):
                    doRow = False
                    break
            if doRow:
                rowOut = []
                for func in procFuncs:
                    r = func(rowIn)
                    rowOut += r

                writer.writerow(rowOut)

            rowNum += 1

def genSkipRows(rowsToSkip):
    def skipRows(rowNum, _):
        return rowNum not in rowsToSkip

    return skipRows

def genColorFromFunc(colNum, func, grays=False):
    """
    genColorFromFunc(colNum, ntiles, grays) ->
        colorValue([...,colNum value, ...]) -> [color]
    """

    if grays:
        def value2rgb(v):
            return colorsys.hsv_to_rgb(0.0, 0.0, v)
    else:
        def value2rgb(v):
            return colorsys.hsv_to_rgb(v, 1.0, 1.0)

    def colorValue(rowIn):
        x = float(rowIn[colNum])

        y = func(x)

        if y < 0: y = 0
        elif y > 1: y = 1

        r,g,b = value2rgb(y)
        r = round(r*255)
        g = round(g*255)
        b = round(b*255)

        color = "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

        return [color]

    return colorValue

def genColorFromNtiles(colNum, ntiles, grays=False):
    """
    genColorFromNtiles(colNum, ntiles, grays) ->
        colorValue([...,colNum value, ...]) -> [color]
    """

    if grays:
        polyline = polyLinearFromNtiles(ntiles, 1.0, 0.0)
    else:
        polyline = polyLinearFromNtiles(ntiles, 2.0/3.0, 0.0)

    return genColorFromFunc(colNum, polyline, grays)

def genNumElemToTamanho(colNum, tamRef, numElemRef):
    """Gera uma função que converte numero de elementos em tamanho de nodo.

    genNumElemToTamanho(colNum, tamRef, numElemRef) ->
            numElemToTamanho([...,numElem,...]) -> [tamanho]
    """

    alpha = (tamRef*tamRef)/numElemRef

    def numElemToTamanho(rowIn):
        """numElemToTamanho([...,numElem,...]) -> [tamanho]
        """

        numElem = float(rowIn[colNum])

        return [math.sqrt(alpha*numElem)]

    return numElemToTamanho

def genIdentity(colNum):
    """
    genIdentity(colNum) ->
        identity([...,colNum value,...]) -> [colNum value]
    """

    def identity(rowIn):
        return [rowIn[colNum]]

    return identity

#-------------------------------------------------------------------------
# Funções específicas dos experimentos
#-------------------------------------------------------------------------

def arestasVizinhancaDeSilhueta(arqIn,arqOut):
    """
    Processando os elementos do arquivo de silhuetas para classificar a relação
    com o vizinho de acordo com o sinal do índice de silhueta: positivo o
    elemento está mais próximo ao cluster vizinho que a outros clusters;
    negativo o elemento prefiria estar no cluster vizinho que no atual.

    Args:

    - arqIn: Caminho para arquivo de elementos gerados pelo aplicativo 'som'
    - arqOut: Caminho para o arquivo de saída
    """
    def silhouetteClass(v):
        if v < 0:
            return 'negative'
        else:
            return 'positive'

    processaCsv(arqIn,arqOut,
        outHeader=['ID','classe_som','silhouette','cluster_vizinho','Relation'],
        filterFuncs=[
            genSkipRows([0])
        ],
        procFuncs=[
            genIdentity(1),
            genIdentity(2),
            lambda r: [float(r[4])],
            genIdentity(5),
            lambda r: [silhouetteClass(float(r[4]))]
        ])

def exp01_01():
    """Processamento para o experimento 01"""

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
            genColorFromNtiles(1,[0.0, 0.0   , 0.0   , 0.0117, 0.3082]),
            genColorFromNtiles(2,[0.0, 0.0   , 0.0512, 0.1567, 0.6458]),
            genColorFromNtiles(3,[0.0, 0.0   , 0.0   , 0.0314, 0.3758]),
            genColorFromNtiles(4,[0.0, 0.0385, 0.0810, 0.1510, 0.5409]),
            genColorFromNtiles(6,[0.0, 0.0001, 0.0035, 0.0972, 0.7917]),
            genColorFromNtiles(7,[0.0, 0.0   , 0.0   , 0.3333, 0.4583]),
            genColorFromNtiles(1,[0.0, 0.0   , 0.0   , 0.0117, 0.3082],True),
            genColorFromNtiles(2,[0.0, 0.0   , 0.0512, 0.1567, 0.6458],True),
            genColorFromNtiles(3,[0.0, 0.0   , 0.0   , 0.0314, 0.3758],True),
            genColorFromNtiles(4,[0.0, 0.0385, 0.0810, 0.1510, 0.5409],True),
            genColorFromNtiles(6,[0.0, 0.0001, 0.0035, 0.0972, 0.7917],True),
            genColorFromNtiles(7,[0.0, 0.0   , 0.0   , 0.3333, 0.4583],True),
            genColorFromNtiles(5,[-0.2318, 0.0, 0.1003, 0.5156, 1.0],True),
        ],
        filterFuncs=[genSkipRows([0])])

def exp01_03():
    arestasVizinhancaDeSilhueta('data/somGridElem.csv',
            'data/arestasSilhueta.csv')

def exp01():
    exp01_01()
    exp01_02()
    exp01_03()

def exp01_02():
    """Denormalizando os atributos: Multiplicando o atributo normalizado pelo
    valor máximo do atributo original. Isto porque o valor mínimo de todos os
    atributos é 0 e eles foram normalizados linermente para o intervalo [0,1].
    """

    processaCsv('data/refsComLegenda.csv', 'data/procRefsOrig.csv',
        outHeader=['node',
            'Commenter_in_ref_orig',
            'Commenter_out_ref_orig',
            'Liker_in_ref_orig',
            'Liker_out_ref_orig',
            'Post_Author_in_ref_orig',
            'Post_Author_out_ref_orig'
        ],
        procFuncs=[
            genIdentity(0),
            lambda r: [float(r[1]) * 139],
            lambda r: [float(r[2]) * 8],
            lambda r: [float(r[3]) * 541],
            lambda r: [float(r[4]) * 26],
            lambda r: [float(r[6]) * 12],
            lambda r: [float(r[7]) * 3],
        ],
        filterFuncs=[genSkipRows([0])])

def exp02_01():
    """
    Criando arquivos para cada atributo de nodo que possuam apenas os nodos em
    que o atributo seja maior que zero.

    Isto foi feito pois para todos os atributos muitos nodos os tem como zero. E
    queremos saber a distribuição (quartis) dos valores de cada atributo para os
    nodos que realmente possuem aquele atributo, ou seja, para as pessoas que
    realmente possuem aquele tipo de interação.
    """
    processaCsv('data/nodesNorm.csv','data/Post_Author_in.csv',
        outHeader=['ID','Post_Author_in'],
        filterFuncs=[
            genSkipRows([0]),
            lambda i, r: float(r[1]) > 0.0
        ],
        procFuncs=[
            genIdentity(0),
            lambda r: [float(r[1])]
        ])
    processaCsv('data/nodesNorm.csv','data/Post_Author_out.csv',
        outHeader=['ID','Post_Author_out'],
        filterFuncs=[
            genSkipRows([0]),
            lambda i, r: float(r[2]) > 0.0
        ],
        procFuncs=[
            genIdentity(0),
            lambda r: [float(r[2])]
        ])
    processaCsv('data/nodesNorm.csv','data/Commenter_in.csv',
        outHeader=['ID','Commenter_in'],
        filterFuncs=[
            genSkipRows([0]),
            lambda i, r: float(r[3]) > 0.0
        ],
        procFuncs=[
            genIdentity(0),
            lambda r: [float(r[3])]
        ])
    processaCsv('data/nodesNorm.csv','data/Commenter_out.csv',
        outHeader=['ID','Commenter_out'],
        filterFuncs=[
            genSkipRows([0]),
            lambda i, r: float(r[4]) > 0.0
        ],
        procFuncs=[
            genIdentity(0),
            lambda r: [float(r[4])]
        ])
    processaCsv('data/nodesNorm.csv','data/Liker_in.csv',
        outHeader=['ID','Liker_in'],
        filterFuncs=[
            genSkipRows([0]),
            lambda i, r: float(r[5]) > 0.0
        ],
        procFuncs=[
            genIdentity(0),
            lambda r: [float(r[5])]
        ])
    processaCsv('data/nodesNorm.csv','data/Liker_out.csv',
        outHeader=['ID','Liker_out'],
        filterFuncs=[
            genSkipRows([0]),
            lambda i, r: float(r[6]) > 0.0
        ],
        procFuncs=[
            genIdentity(0),
            lambda r: [float(r[6])]
        ])

def exp02_02():
    """
    Gerando cores a partir dos valores de referência dos nodos do SOM.
    """
    processaCsv('data/refs.csv', 'data/procRefs.csv',
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
            genNumElemToTamanho(8,100, 10977),
            genColorFromNtiles(1,[0.0   , 0.0   , 0.0037, 0.0633, 0.1752]),
            genColorFromNtiles(2,[0.0   , 0.02  , 0.1381, 0.2120, 0.4500]),
            genColorFromNtiles(3,[0.0   , 0.0   , 0.0049, 0.1174, 0.4303]),
            genColorFromNtiles(4,[0.0246, 0.0408, 0.0809, 0.2110, 0.4365]),
            genColorFromNtiles(6,[0.0001, 0.0004, 0.0082, 0.1409, 0.4750]),
            genColorFromNtiles(7,[0.0   , 0.0   , 0.1667, 0.3394, 0.4222]),
            genColorFromNtiles(1,[0.0   , 0.0   , 0.0037, 0.0633, 0.1752],True),
            genColorFromNtiles(2,[0.0   , 0.0200, 0.1381, 0.2120, 0.4500],True),
            genColorFromNtiles(3,[0.0   , 0.0   , 0.0049, 0.1174, 0.4303],True),
            genColorFromNtiles(4,[0.0246, 0.0408, 0.0809, 0.2110, 0.4365],True),
            genColorFromNtiles(6,[0.0001, 0.0004, 0.0082, 0.1409, 0.4750],True),
            genColorFromNtiles(7,[0.0   , 0.0   , 0.1667, 0.3394, 0.4222],True),
            genColorFromNtiles(5,[-0.2534, 0.9773],True),
        ],
        filterFuncs=[genSkipRows([0])])

def exp03():
    """
    Processando os elementos do arquivo de silhuetas para classificar a relação
    com o vizinho de acordo com o sinal do índice de silhueta: positivo o
    elemento está mais próximo ao cluster vizinho que a outros clusters;
    negativo o elemento prefiria estar no cluster vizinho que no atual.
    """
    arestasVizinhancaDeSilhueta('data/somElem02.csv',
            'data/arestasSilhueta.csv')

def exp02():
    exp02_01()
    exp02_02()

def exp05():
    """Processando o arquivo do facebook para filtar os auto loops e considerar
    todas os tipos de interação como um só.
    """

    processaCsv('data/face2014-08.csv', 'data/noLoops2014-08.csv',
        outHeader=['src','tgt','relation','weight','const'],
        procFuncs=[
            genIdentity(0),
            genIdentity(1),
            genIdentity(2),
            genIdentity(3),
            lambda *a: [1],
        ],
        filterFuncs=[
            genSkipRows([0]),
            lambda rn, row: row[0] != row[1]
        ])

def exp09():
    """Processando o arquivo do facebook para retirar arestas do tipo Liker.
    """

    processaCsv('data/face2014-08.csv', 'data/semLiker.csv',
        outHeader=['src','tgt','relation','weight'],
        procFuncs=[
            genIdentity(0),
            genIdentity(1),
            genIdentity(2),
            genIdentity(3),
        ],
        filterFuncs=[
            genSkipRows([0]),
            lambda rn, row: row[2] != 'Liker'
        ])

if __name__ == '__main__':
    #exp01()
    #exp02()
    #exp03()
    #exp05()
    exp09()
    pass
