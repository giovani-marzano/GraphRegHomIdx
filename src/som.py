#!/usr/bin/python3
# coding: utf-8

#---------------------------------------------------------------------
# Seção de importação de modulos
#---------------------------------------------------------------------
from __future__ import print_function

import os.path
import collections
import io
import logging
import logging.config
import csv

import sys

# Acrescentando o diretorio lib ao path. Lembrando que sys.path[0] representa o
# diretório onde este script se encontra

sys.path.append(os.path.join(sys.path[0],'lib'))

import graph as gr
import SOM.vectorBased as somV

if sys.version_info.major < 3:
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

#---------------------------------------------------------------------
# Variaveis globais de configuração
#---------------------------------------------------------------------

# Variavéis que controlam de onde os dados de entrada serão lidos
DIR_INPUT = 'data'
ARQ_IN = os.path.join(DIR_INPUT,'entrada.csv')

# Configuracao de que colunas do arquivo csv que serao utilizadas
# Nome das colunas de identificacao
ID_ATTRS = ['id','di']
# Nome das colunas de valores
VALUE_ATTRS = ['a','b','c']

# Configuraçoes do formato do arquivo CSV
CSV_OPTIONS = {
    'delimiter': ';'
}

# Variáveis que controlam onde os dados de saida do script serão salvos
DIR_OUTPUT = 'data'
ARQ_SOM = os.path.join(DIR_OUTPUT,'SOM.graphml')
ARQ_CLASSES_SOM = os.path.join(DIR_OUTPUT, 'classesSOM.csv')

# Configurações para controlar o algoritmo SOM
SOM_CONFIG = {
    'Tipo': 'grid', # Pode ser 'grid' ou 'tree'
    'FVU': 0.2,
    'maxNodes': 3, #para TREE
    'neighWeightTrain': 0.25,
    'neighWeightRefine': 0.25,
    'maxStepsPerGeneration': 100,
    'MSTPeriod': 10,
    'nrows': 5, #numero de linhas
    'ncols': 4  #numero de colunas
}

# Configurações para controlar a geração de log pelo script
ARQ_LOG = os.path.join(DIR_OUTPUT,'log.txt')
LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'brief': {
            'format': '%(message)s'
        },
        'detail': {
            'format': '%(asctime)s|%(levelname)s:%(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'brief'
        },
        'arquivo': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detail',
            'filename': ARQ_LOG,
            'mode': 'w'
        }
    },
    'root': {
        'handlers': ['console', 'arquivo'],
        'level': 'DEBUG'
    }
}

#---------------------------------------------------------------------
# Função principal do script
#---------------------------------------------------------------------
def main(log):
    """Função principal do script, executada no final do arquivo.
    """
    log.info('Carregando {}...'.format(ARQ_IN))
    elements, attrNames = carregaArquivo(ARQ_IN, idAttrs=ID_ATTRS,
            valueAttrs=VALUE_ATTRS)

    criaSOM(log, elements, attrNames)

#---------------------------------------------------------------------
# Definição das funções auxiliares e procedimentos macro do script
#---------------------------------------------------------------------

def carregaArquivo(fileName, idAttrs=[], valueAttrs=[]):

    csvReader = csv.reader(open(ARQ_IN, newline=''), **CSV_OPTIONS)

    elements = {}
    idCols = set()
    valueCols = set()
    attrNames = []

    elemNum = 0
    for campos in csvReader:
        if elemNum == 0:
            # Estamos lendo a primeira linha que possui o cabecalho
            cabecalho = campos
            for n, c in enumerate(campos):
                if c in idAttrs:
                    idCols.add(n)
                elif c in valueAttrs:
                    valueCols.add(n)
                    attrNames.append(c)
        else:
            id = [elemNum]
            vet = []
            for n, v in enumerate(campos):
                if n in idCols:
                    id.append(v)
                elif n in valueCols:
                    vet.append(float(v))
            elements[tuple(id)] = vet

        elemNum += 1

    return elements, attrNames

def criaSOM(log, elements, attrNames):
    som = somV.SOMap('SOM')
    som.conf.dictConfig(SOM_CONFIG)
    som.elements = list(elements.values())
    log.info('Treinando SOM...')
    if SOM_CONFIG['Tipo'] == 'grid':
        som.trainHexGrid(
            SOM_CONFIG.get('nrows', 5),
            SOM_CONFIG.get('ncols', 4)
        )
    else:
        som.trainGrowingTree()

    log.info('...ok')

    # Salvando o som de nodos
    gsom = somV.convertSOMapToMultiGraph(som,
            attrNames=attrNames, nodeIDAttr='ID')
    gsom.writeGraphml(ARQ_SOM)

#---------------------------------------------------------------------
# Execução do script
#---------------------------------------------------------------------
if __name__ == '__main__':
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger()
    main(logger)
