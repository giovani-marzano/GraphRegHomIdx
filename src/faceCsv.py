#!/usr/bin/python3

"""Script que processa um arquivo csv que contém as arestas como extraídas do
facebook pelo NodeXL.

Execute o script com a opção --help para informações sobre os parâmetros
aceitos.
"""

RELACOES_NAO_DIRECIONADAS = ['Friend']

#RELACOES_INCLUIDAS = [
#    'Liker',
#    'Post Author',
#    'Commenter',
#    'User Tagged'
#]

RELACOES_INCLUIDAS = [
    'Liker',
    'Post Author',
    'Commenter'
]

import csv

CSV_IN_OPTIONS = {
    'delimiter': '\t'
}
# Descomente a linha abaixo para que o formato do csv seja inferido a partir do
# arquivo de entrada.
#
# CSV_IN_OPTIONS = None

CSV_OUT_OPTIONS = {
    'delimiter': '\t',
    'lineterminator': '\n',
    'quotechar': '"',
    'escapechar': '\\',
    'doublequote': False,
    'quoting': csv.QUOTE_NONNUMERIC,
    'skipinitialspace': True
}
# Descomente a linha abaixo para que o formato do csv seja inferido a partir do
# arquivo de entrada.
#
# CSV_OUT_OPTIONS = None

import argparse
import re

def createArgParser():
    argParser = argparse.ArgumentParser(
        description="""Processa um arquivo csv que contém as arestas como
            extraídas do facebook pelo NodeXL""")

    argParser.add_argument('-H', '--header', action='store_true',
            default=False, dest='hasHeaders',
            help="""Indica que a primeira linha do csv é cabeçalho. O default é
                considerar que a primeira linha também é dado.""")

    argParser.add_argument('-w', '--weights', action='store_true',
            default=False, dest='hasWeight',
            help="""Indica que o arquivo csv de entrada possui uma coluna
            adicional com o peso de cada aresta.""")

    argParser.add_argument('-n', '--nodes', dest='arqNodes',
        metavar='arqNodes', default='',
        help="""Arquivo csv com uma tabela de tradução de nodos. O formato
            esperado é: Nodo, facebook id. A primeira coluna deve ter os
            identifadores como aparecem no arquivo de arestas. A segunda coluna
            é o identificador que será utilizado no arquivo de saída. Se o
            identificador de saída for no formato http://www.facebook.com/id,
            apenas a parte do id será mantida e o prefixo da página do facebook
            será retirado.""")

    argParser.add_argument('arqIn',
        help="""Arquivo csv de arestas de entrada. As três primeiras colunas do
            arquivo são interpretadas como: Nodo origem, Nodo destino, Tipo da
            aresta.""")
    argParser.add_argument('arqOut',
        help="""Arquivo csv de saída. As colunas geradas são: Nodo origem, Nodo
            destino, Tipo da aresta, Peso da aresta""")

    return argParser

def createNodeMap(arqNodes, hasHeader):

    idPattern = r"(?:(?:https?://)?www.facebook.com/)?(.*)"
    idRegExp = re.compile(idPattern)
    nodeMap = {}

    with open(arqNodes, 'r', newline='') as f:
        csvReader = csv.reader(f, dialect='facecsv-in')

        if hasHeader:
            for _  in csvReader:
                break

        for campos in csvReader:
            faceId = campos[1].strip()
            match = idRegExp.match(faceId)
            # print(faceId, match.group(1))
            faceId = match.group(1)

            nodeMap[campos[0].strip()] = faceId

    return nodeMap

if __name__ == '__main__':

    argParser = createArgParser()

    args = argParser.parse_args()

    with open(args.arqIn, 'r', newline='') as f:
        inspectedDialect = csv.Sniffer().sniff(f.read(2048))

    if CSV_IN_OPTIONS is not None:
        csv.register_dialect('facecsv-in', **CSV_IN_OPTIONS)
    else:
        csv.register_dialect('facecsv-in', inspectedDialect)

    if CSV_OUT_OPTIONS is not None:
        csv.register_dialect('facecsv-out', **CSV_OUT_OPTIONS)
    else:
        csv.register_dialect('facecsv-out', inspectedDialect)

    if args.arqNodes:
        nodeMap = createNodeMap(args.arqNodes, args.hasHeaders)
    else:
        nodeMap = {}

    pesos = {}
    def addEdge(src, tgt, rel, weight=1):
        src = nodeMap.get(src, src)
        tgt = nodeMap.get(tgt, tgt)
        edge = (src, tgt, rel)
        p = pesos.get(edge, 0)
        p += weight
        pesos[edge] = p

    with open(args.arqIn, 'r', newline='') as f:
        csvReader = csv.reader(f, dialect='facecsv-in')

        if args.hasHeaders:
            # Pulando a primeira linha
            for campos in csvReader:
                break

        for campos in csvReader:
            if campos[2] in RELACOES_INCLUIDAS:
                if args.hasWeight:
                    weight = float(campos[3])
                else:
                    weight = 1
                addEdge(campos[0], campos[1], campos[2], weight)
                if campos[2] in RELACOES_NAO_DIRECIONADAS:
                    addEdge(campos[1], campos[0], campos[2], weight)

    with open(args.arqOut, 'w', newline='') as f:
        csvWriter = csv.writer(f, dialect='facecsv-out')

        csvWriter.writerow(['src','tgt','relation','weight'])
        for edge, p in pesos.items():
            row = list(edge)
            row.append(p)
            csvWriter.writerow(row)
