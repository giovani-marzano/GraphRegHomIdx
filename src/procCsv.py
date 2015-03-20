
import csv
import math

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

def processaCsv(fileIn, fileOut, procFun, outHeader=None, skipFirstRow=True):
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
            rowOut = procFun(rowIn)
            writer.writerow(rowOut)

def genNumElemToTamanho(tamRef, numElemRef):
    """Gera uma função que converte numero de elementos em tamanho de nodo.

    genNumElemToTamanho(tamRef, numElemRef) ->
            numElemToTamanho([node, numElem]) -> [node, tamanho]
    """

    alpha = (tamRef*tamRef)/numElemRef

    def numElemToTamanho(rowIn):
        """numElemToTamanho([node, numElem]) -> [node, tamanho]
        """

        numElem = float(rowIn[1])

        return [rowIn[0], math.sqrt(alpha*numElem)]

    return numElemToTamanho


if __name__ == '__main__':

    processaCsv('somGridNumElem.csv', 'somGridTamanho.csv',
        genNumElemToTamanho(100, 9910), outHeader=['node','tamanho'])
