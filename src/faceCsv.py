#!/usr/bin/python3

"""Script que processa um arquivo csv que contém as arestas como extraídas do
facebook pelo NodeXL.

O csv de entrada tem o seguinte formato::

    pessoa1;pessoa2;relação

, onde relação é o tipo de interação do pessoa1 para o pessoa2.

No arquivo aparecem multiplos registros com o mesmo valor de pessoa1, pessoa2
e relação, que indicam ocorrências múltiplas daquela interação. As arestas são
consideradas direcionadas, a menos que a relação apareça na lista
RELACOES_NAO_DIRECIONADAS.

O script gera outro csv com linhas na forma::
    
    id1;id2;relação;peso

, onde peso é a contagem de interações do tipo 'relação' entre pessoa1 e
pessoa2.
"""

import csv
import sys

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
    'Commenter',
]

CSV_OPTIONS = {
    'delimiter': '\t'
}

# Flag que indica se é para retirar sufixos numéricos que aparecerem no final
# dos nomes das pessoas.
RETIRAR_SUFIXO_NUMERICO = True

from collections import Counter
import re

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('Usage: {0} arqIn arqOut'.format(sys.argv[0]))
        sys.exit()

    namePattern = r'^ *(.*?)[0-9]* *$'
    namePat = re.compile(namePattern)
    nameCounter = Counter()
    pesos = {}

    def addEdge(src, tgt, rel):
        edge = (src, tgt, rel)
        p = pesos.get(edge, 0)
        p += 1
        pesos[edge] = p

    with open(sys.argv[1], 'r', newline='') as f:
        csvReader = csv.reader(f, **CSV_OPTIONS)

        for campos in csvReader:
            if RETIRAR_SUFIXO_NUMERICO:
                for i in range(2):
                    m = namePat.match(campos[i])
                    if m:
                        campos[i] = m.group(1)
                    else:
                        print('No match ', campos[i])

            if campos[2] in RELACOES_INCLUIDAS:
                addEdge(campos[0], campos[1], campos[2])
                if campos[2] in RELACOES_NAO_DIRECIONADAS:
                    addEdge(campos[1], campos[0], campos[2])
                
    with open(sys.argv[2], 'w', newline='') as f:
        csvWriter = csv.writer(f, **CSV_OPTIONS)
        for edge, p in pesos.items():
            row = list(edge)
            row.append(p)
            csvWriter.writerow(row)
