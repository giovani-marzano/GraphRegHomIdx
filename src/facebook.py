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

# Nome do atributo de arestas do graphml que indica o tipo (relação) da aresta.
# No caso o tipo da aresta representa o tipo de interação entre duas pessoas no
# facebook.
RELATION_ATTR = 'Relationship'

# Nome do atributo de arestas do graphml que contém o peso da aresta. No caso o
# peso indica quantas interações de um determinado tipo ocorreram.
WEIGHT_ATTR = 'Edge Weight'

# Variavéis que controlam de onde os dados de entrada serão lidos
DIR_INPUT = 'data'
ARQ_IN = os.path.join(DIR_INPUT,'face.csv')

CSV_OPTIONS = {
    'delimiter': ';'
}

# Variáveis que controlam onde os dados de saida do script serão salvos
DIR_OUTPUT = 'data'
ARFF_NODOS = os.path.join(DIR_OUTPUT, 'nodos.arff')
ARFF_EDGES = os.path.join(DIR_OUTPUT, 'edges.arff')
ARQ_AGREGADO = os.path.join(DIR_OUTPUT,'agregado.graphml')
ARQ_PROCESSADO = os.path.join(DIR_OUTPUT,'processado.graphml')
ARQ_SOM_NODES = os.path.join(DIR_OUTPUT,'SOMNodes.graphml')
ARQ_SOM_GRID_NODES = os.path.join(DIR_OUTPUT,'SOMGridNodes.graphml')
ARQ_SOM_EDGES = os.path.join(DIR_OUTPUT,'SOMEdges.graphml')
ARQ_CLASSES_SOM = os.path.join(DIR_OUTPUT, 'classesSOM.graphml')

# Configurações para controlar o algoritmo SOM
SOM_NODES_CONFIG = {
    'FVU': 0.2,
    'maxNodes': 20,
    'neighWeightTrain': 0.25,
    'neighWeightRefine': 0.25,
    'maxStepsPerGeneration': 100,
    'MSTPeriod': 10
}

SOM_EDGES_CONFIG = {
    'FVU': 0.2,
    'maxNodes': 3,
    'neighWeightTrain': 0.25,
    'neighWeightRefine': 0.25,
    'maxStepsPerGeneration': 100,
    'MSTPeriod': 10
}

SOM_GRID_NODES_CONFIG = {
    'FVU': 0.2,
    'maxNodes': 20,
    'neighWeightTrain': 0.5,
    'neighWeightRefine': 0.25,
    'maxStepsPerGeneration': 100,
    'nrows': 5,
    'ncols': 4
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
    log.info('Carregando grafo {}...'.format(ARQ_IN))
    geral = carregaGrafo(ARQ_IN, relationAttr=RELATION_ATTR)
    log.info('... carregado: {} nodos e {} arestas'.format(geral.getNumNodes(),
                geral.getNumEdges()))

    log.info('Ocorrencias de arestas paralelas: {}'.format(
        contandoArestasComMesmaOrigemEDestino(geral)))

    preprocessaGrafo(geral, log)

    # Pegando o conjunto de todos os tipos de arestas do grafo
    tiposInteracoes = geral.getEdgeAttrValueSet(RELATION_ATTR);
    log.info('Tipos de relacionamentos no grafo: '+str(list(tiposInteracoes)))

    # processamentoTiposArestasAgregados(geral, log, tiposInteracoes)

    for tipo in tiposInteracoes:
        grafoEquivRegularSoUmTipoAresta(geral, tipo, log)

    log.info('Salvando {}...'.format(ARQ_PROCESSADO))
    geral.writeGraphml(ARQ_PROCESSADO)
    log.info('...ok')

#---------------------------------------------------------------------
# Definição das funções auxiliares e procedimentos macro do script
#---------------------------------------------------------------------

def carregaGrafo(fileName, relationAttr=RELATION_ATTR,
        weightAttr=WEIGHT_ATTR):

    _, ext = os.path.splitext(ARQ_IN)

    if ext == '.graphml':
        g = gr.loadGraphml(ARQ_IN, relationAttr=RELATION_ATTR)
    elif ext == '.csv':
        g = gr.MultiGraph()

        relSpec = gr.AttrSpec(relationAttr,'string')
        weiSpec = gr.AttrSpec(weightAttr, 'int', 0)

        g.addEdgeAttrSpec(relSpec)
        g.addEdgeAttrSpec(weiSpec)

        csvReader = csv.reader(open(ARQ_IN, newline=''), **CSV_OPTIONS)

        for campos in csvReader:
            src = campos[0]
            tgt = campos[1]
            rel = campos[2]
            weight = int(campos[3])

            g.addEdge(src, tgt, rel)
            e = (src, tgt, rel)
            g.setEdgeAttr(e, relSpec.name, rel)
            g.setEdgeAttr(e, weiSpec.name, weight)
    else:
        raise IOError("Tipo de arquivo não suportado - '{}'".format(ext))

    return g

def preprocessaGrafo(geral, log):
    limpezaDeAtributos(geral, [], [WEIGHT_ATTR, RELATION_ATTR], log)
    imprimeAtributos(geral, log)

    # No grafo que está sendo carregado o atributo WEIGHT_ATTR está como tipo
    # string e deveria ser inteiro. Aqui convertemos os valores de WEIGHT_ATTR
    # para inteiro
    weights = geral.extractEdgeFeatureVectors([WEIGHT_ATTR])
    geral.removeEdgeAttr(WEIGHT_ATTR)
    spec = gr.AttrSpec(WEIGHT_ATTR, 'int', 0)
    geral.addEdgeAttrSpec(spec)
    for edge, vet in weights.items():
        geral.setEdgeAttr(edge, WEIGHT_ATTR, int(vet[0]))

def processamentoTiposArestasAgregados(geral, log, tiposInteracoes):
    # Agregando as arestas diferentes entre dois nós e contando os tipos de
    # arestas.
    log.info('Agregando arestas...')
    novo, edgeInterations = relationShipParaAtributoDeAresta(
            geral, tiposInteracoes, WEIGHT_ATTR)
    log.info('...atributos criados:'+str(list(edgeInterations)))

    log.info('Agregando por nodo...')
    nodeInterations = contandoInteracoesPorNodo(novo, tiposInteracoes)
    log.info('...atributos criados:'+str(list(nodeInterations)))

    criaArffParaNodos(novo, ARFF_NODOS, nodeInterations)
    log.info('Arquivo {} criado'.format(ARFF_NODOS))
    criaArffParaArestas(novo, ARFF_EDGES, edgeInterations)
    log.info('Arquivo {} criado'.format(ARFF_EDGES))

    processaGrafoAgregadoComSOM(novo, log, nodeInterations, edgeInterations)

    log.info('Salvando grafo agregado em {}'.format(ARQ_AGREGADO))
    novo.writeGraphml(ARQ_AGREGADO)

def processaGrafoAgregadoComSOM(g, log, nodeInterations, edgeInterations):

    # Extraindo os vetores de nodos
    elements = g.extractNodeFeatureVectors(nodeInterations)

    criaSOMGridParaNodos(log, elements, nodeInterations)

    som = somV.SOMap('Nodes')
    som.conf.dictConfig(SOM_NODES_CONFIG)
    som.elements = list(elements.values())
    log.info('Treinando SOM para nodos...')
    som.trainGrowingTree()
    log.info('...ok')

    # Recuperando os classes geradas para cada nodo
    classes, quantErr = som.classifyMapOfElements(elements)

    # Atribuindo ao nodos do grafo as classes do SOM
    g.setNodeAttrFromDict('SOM_class', classes, default=-1, attrType='int')
    g.setNodeAttrFromDict('SOM_quantErr', quantErr, default=0, attrType='double')

    # Salvando o som de nodos
    gsom = somV.convertSOMapToMultiGraph(som,
            attrNames=nodeInterations, nodeIDAttr='SOM_class')
    gsom.writeGraphml(ARQ_SOM_NODES)

    # Mesma coisa para as arestas

    # Extraindo os vetores de arestas
    elements = g.extractEdgeFeatureVectors(edgeInterations)

    som = somV.SOMap('Edges')
    som.conf.dictConfig(SOM_EDGES_CONFIG)
    som.elements = list(elements.values())
    log.info('Treinando SOM para arestas...')
    som.trainGrowingTree()
    log.info('...ok')

    # Recuperando os classes geradas para cada aresta
    classes, quantErr = som.classifyMapOfElements(elements)

    # Atribuindo às arestas do grafo as classes do SOM
    g.setEdgeAttrFromDict('SOM_class', classes, default=-1, attrType='int')
    g.setEdgeAttrFromDict('SOM_quantErr', quantErr, default=0, attrType='double')

    # Salvando o som de nodos
    gsom = somV.convertSOMapToMultiGraph(som,
            attrNames=edgeInterations, nodeIDAttr='SOM_class')
    gsom.writeGraphml(ARQ_SOM_EDGES)

    # gerando grafo de classes
    gclass = g.spawnFromClassAttributes(nodeClassAttr='SOM_class',
            edgeClassAttr='SOM_class')

    # Computando atributos agregados
    attrNodes, attrEdges, specNodes, specEdges = gr.aggregateClassAttr(g,
        nodeClassAttr='SOM_class', edgeClassAttr='SOM_class',
        nodeAttrs=nodeInterations, edgeAttrs=edgeInterations)

    gr.addAttributeSetsToGraph(gclass,
        attrNodes=attrNodes, specNodes=specNodes,
        attrEdges=attrEdges, specEdges=specEdges)

    log.info("Salvando '{}': {} nodos e {} arestas...".format(ARQ_CLASSES_SOM,
                gclass.getNumNodes(), gclass.getNumEdges()))
    gclass.writeGraphml(ARQ_CLASSES_SOM)
    log.info('...ok')

def criaSOMGridParaNodos(log, elements, nodeInterations):
    som = somV.SOMap('Nodes HexGrid')
    som.conf.dictConfig(SOM_GRID_NODES_CONFIG)
    som.elements = list(elements.values())
    log.info('Treinando SOM Grid para nodos...')
    som.trainHexGrid(
        SOM_GRID_NODES_CONFIG.get('nrows', 5),
        SOM_GRID_NODES_CONFIG.get('ncols', 4)
    )
    log.info('...ok')

    # Salvando o som de nodos
    gsom = somV.convertSOMapToMultiGraph(som,
            attrNames=nodeInterations, nodeIDAttr='ID')
    gsom.writeGraphml(ARQ_SOM_GRID_NODES)


class CtrlRegEquiv(object):
    def __init__(self, graph, tipo, classAttr, iterLimit, dirOut, log):
        self.log = log
        self.tipo = tipo
        self.graph = graph
        self.classAttr = classAttr
        self.iterLimit = iterLimit
        self.filename = os.path.join(dirOut,'classes_'+tipo+'.csv')
        self.filenameGraph = os.path.join(dirOut,tipo)

        self.classesVet = []
        self.iterations = 0

    def procIteration(self, i, classes, done, classesParents):
        if i == 1:
            self.log.info('RegEquiv {0}:'.format(self.tipo))
        self.log.info('    iteration: {0}'.format(i))
        if not done:
            self.classesVet.append(classes)
            self.iterations = i

        if done or i >= self.iterLimit:
            spec = gr.AttrSpec(self.classAttr,'int')
            self.graph.addNodeAttrSpec(spec)
            self.graph.setNodeAttrFromDict(self.classAttr, classes)
            self.log.info('RegEquiv: {0} done'.format(self.tipo))

        return i < self.iterLimit

    def writeResult(self):
        self.log.info('Salvando {0}...'.format(self.filename))
        with open( self.filename, 'w', newline='') as f:
            writer = csv.writer(f)

            row = ['node'] + ['regClass_'+str(i) for i in range(self.iterations)]
            writer.writerow(row)

            for c in self.classesVet:
                keys = sorted(c.keys())
                break

            for k in keys:
                row = [k] + [c[k] for c in self.classesVet]
                writer.writerow(row)
        self.log.info('...ok')

        # end with

        for i, classes in enumerate(self.classesVet):
            classAttr = self.classAttr + str(i + 1)
            spec = gr.AttrSpec(classAttr,'int')
            self.graph.addNodeAttrSpec(spec)
            self.graph.setNodeAttrFromDict(classAttr, classes)

        for i in range(self.iterations):
            classAttr = self.classAttr + str(i + 1)
            g = self.graph.spawnFromClassAttributes(nodeClassAttr=classAttr,
                    edgeClassAttr=RELATION_ATTR)
            filename = self.filenameGraph + '_' + classAttr
            self.log.info('Salvando grafo {} com {} nodos e {} arestas...'.format(filename,
                    g.getNumNodes(), g.getNumEdges()))
            g.writeGraphml(filename)
            self.log.info('...ok')

def grafoEquivRegularSoUmTipoAresta(a, tipo, log):
    """Extrai do grafo original o subgrafo que possui apenas um dos tipos de
    aresta e produz o menor grafo de classes de equivalencia regular deste
    subgrafo. Anota o grafo original com estatísticas agregadas dos pesos de
    arestas.
    """
    nodeClassAttr = 'class'
    b = a.spawnFromClassAttributes(edgeClassAttr=RELATION_ATTR)

    tipo, b.getNumNodes(), b.getNumEdges()
    for edge in b.edges():
        if b.getEdgeAttr(edge, RELATION_ATTR) == tipo:
            b.setEdgeAttr(edge, 'filtro', 1)
        else:
            b.setEdgeAttr(edge, 'filtro', 0)

    b.removeEdgeByAttr('filtro', 0)
    log.info('Numero de arestas do tipo {}: {}'.format(tipo, b.getNumEdges()))

    ctrl = CtrlRegEquiv(graph=b, tipo=tipo, iterLimit=20, dirOut=DIR_OUTPUT,
            log=log, classAttr=nodeClassAttr)

    log.info("Calculando equivalencia regular para '{}'...".format(tipo))
    gr.regularEquivalence(b, ctrlFunc=ctrl.procIteration)
    ctrl.writeResult()
    log.info('...ok')

    attrName = tipo+'_regularClass'
    spec = gr.AttrSpec(attrName, 'int')
    a.addNodeAttrSpec(spec)
    for node in b.nodes():
        a.setNodeAttr(node, attrName, b.getNodeAttr(node, nodeClassAttr))

    nodeAttrs, edgeAttrs, nodeSpecs, edgeSpecs = gr.aggregateClassAttr(a,
        nodeClassAttr=attrName, edgeClassAttr=RELATION_ATTR,
        edgeAttrs=[WEIGHT_ATTR])

    b = b.spawnFromClassAttributes(nodeClassAttr=nodeClassAttr,
            edgeClassAttr=RELATION_ATTR)

    components = gr.weaklyConnectedComponents(b)
    b.setNodeAttrFromDict('component',components, default=0, attrType='int')

    for spec in nodeSpecs:
        b.addNodeAttrSpec(spec)
        b.setNodeAttrFromDict(spec.name, nodeAttrs[spec.name])
    for spec in edgeSpecs:
        b.addEdgeAttrSpec(spec)
        b.setEdgeAttrFromDict(spec.name, edgeAttrs[spec.name])

    fileName = os.path.join(DIR_OUTPUT,tipo+'.graphml')
    log.info('Salvando grafo {} com {} nodos e {} arestas...'.format(fileName,
            b.getNumNodes(), b.getNumEdges()))
    b.writeGraphml(fileName)
    log.info('...ok')

def criaArffParaNodos(g, fileName, attrs):
    """Cria um arquivo arff que lista os nodos o valor de cada atributo listado
    em attrSpecs.
    """

    attrSpecs = []
    for a in attrs:
        if a in g.nodeAttrSpecs:
            attrSpecs.append(g.nodeAttrSpecs[a])

    nodeType = None
    for node in g.nodes():
        if type(node) == str:
            nodeType = 'string'
        elif type(node) == int:
            nodeType = 'numeric'
        elif type(node) == float:
            nodeType = 'numeric'
        break

    if nodeType is None:
        raise TypeError("Node type not supported")

    with io.open(fileName, 'w', encoding='utf-8') as f:
        f.write(u('@relation "{}"\n\n'.format(fileName)))

        f.write(u('@attribute ID {}\n'.format(nodeType)))

        for spec in attrSpecs:
            valueType = spec.getArffType()
            if valueType is None:
                raise TypeError('Attribute "{0}" type {1} not supported'.format(
                    spec.name, spec.type))
            f.write(u('@attribute "{0}" {1}\n'.format(spec.name, valueType)))

        f.write(u('\n@data\n'))
        for node in g.nodes():
            if nodeType == 'string':
                f.write(u('"{}"').format(node))
            else:
                f.write(u('{}'.format(node)))
            for spec in attrSpecs:
                valueType = spec.getArffType()
                value = g.getNodeAttr(node, spec.name)
                value = spec.getArffValue(value)
                if valueType == 'string':
                    f.write(u(',"{}"').format(value))
                else:
                    f.write(u(',{}'.format(value)))
            f.write(u('\n'))

def criaArffParaArestas(g, fileName, attrs):
    """Cria um arquivo arff que lista as arestas e o valor de cada atributo
    listado em attrs.
    """

    attrSpecs = []
    for a in attrs:
        if a in g.edgeAttrSpecs:
            attrSpecs.append(g.edgeAttrSpecs[a])

    nodeType = None
    relType = None
    for src, tgt, rel in g.edges():
        if type(src) == str:
            nodeType = 'string'
        elif type(src) == int:
            nodeType = 'numeric'
        elif type(src) == float:
            nodeType = 'numeric'
        if type(rel) == str:
            relType = 'string'
        elif type(rel) == int:
            relType = 'numeric'
        elif type(rel) == float:
            relType = 'numeric'
        break

    if nodeType is None:
        raise TypeError("Node type not supported")
    if relType is None:
        raise TypeError("Relation type not supported")

    with io.open(fileName, 'w', encoding='utf-8') as f:
        f.write(u('@relation "{}"\n\n'.format(fileName)))

        f.write(u('@attribute "e-src" {}\n'.format(nodeType)))
        f.write(u('@attribute "e-tgt" {}\n'.format(nodeType)))
        f.write(u('@attribute "e-rel" {}\n'.format(relType)))

        for spec in attrSpecs:
            valueType = spec.getArffType()
            if valueType is None:
                raise TypeError('Attribute "{0}" type {1} not supported'.format(
                    spec.name, spec.type))
            f.write(u('@attribute "{0}" {1}\n'.format(spec.name, valueType)))

        f.write(u('\n@data\n'))
        for src, tgt, rel in g.edges():
            if nodeType == 'string':
                f.write(u('"{}"').format(src))
                f.write(u(',"{}"').format(tgt))
            else:
                f.write(u('{}'.format(src)))
                f.write(u(',{}'.format(tgt)))
            if relType == 'string':
                f.write(u(',"{}"').format(rel))
            else:
                f.write(u(',{}'.format(rel)))
            for spec in attrSpecs:
                valueType = spec.getArffType()
                value = g.getEdgeAttr((src,tgt,rel), spec.name)
                value = spec.getArffValue(value)
                if valueType == 'string':
                    f.write(u(',"{}"').format(value))
                else:
                    f.write(u(',{}'.format(value)))
            f.write(u('\n'))

def relationShipParaAtributoDeAresta(g, tiposArestas, weightAttr):
    """Transforma os atributos de Relationship e Edge Weigth em
    atributos que contam cada tipo de iteração: Liker, Commenter, etc
    """

    # Iremos criar outro grafo que possui apenas um tipo de aresta, ou seja,
    # iremos mesclar arestas de tipos diferentes em uma só.
    #
    # Para isso criamos um atributo de filtro com o mesmo valor para todas as
    # arestas...
    spec = gr.AttrSpec('tipo', 'int')
    spec.default = 1
    g.addEdgeAttrSpec(spec)

    # ... Agora todas as arestas tem o mesmo valor para o atributo 'tipo', pois
    # o default é 1.
    #
    # Criamos outro grafo utilizando o 'tipo' como classe de aresta. Não
    # usaremos nada como classe de nodos, então estes serão iguais ao do grafo
    # original.
    novo = g.spawnFromClassAttributes(edgeClassAttr='tipo')

    # Acrescentaremos atributos no novo grafo para contar cada tipo de interação
    # que as arestas representam.
    #
    # Cada tipo de aresta irá virar um atributo inteiro que conta quantas
    # iterações daquele tipo ocorreram
    atributos = []
    for tipo in tiposArestas:
        spec = gr.AttrSpec(tipo, 'int', 0)
        novo.addEdgeAttrSpec(spec)
        atributos.append(tipo)

    # Percorremos as arestas do grafo original somando os pesos no novo grafo. A
    # relação (rel) no grafo original é igual ao atributo Relationship, pois
    # este foi utilizado em 'main' para carregar o grafo do arquivo.
    for src, tgt, rel in g.edges():
        weight = g.getEdgeAttr((src, tgt, rel), weightAttr, 0)

        # O grafo original esta com weight como um atributo do tipo string, por
        # isso convertemos para inteiro
        weight = int(weight)

        count = novo.getEdgeAttr((src, tgt, 1), rel, 0)
        count += weight
        novo.setEdgeAttr((src, tgt, 1), rel, count)

    # Removemos o atributo 'tipo' criado dos grafos original e novo
    g.removeEdgeAttr('tipo')
    novo.removeEdgeAttr('tipo')

    return novo, atributos

def contandoInteracoesPorNodo(g, tiposInteracoes):
    """Soma em cada nodo o total de cada tipo de arestas de saída e de entrada
    que o nodo possui.

    Irá criar em cada nodo do grafo g atributos como Liker_in, Liker_out,
    Commenter_in, Commenter_out, etc.
    """

    atributos = []
    
    for tipo in tiposInteracoes:
        attrName = tipo+'_in'
        spec = gr.AttrSpec(attrName, 'int', 0)
        g.addNodeAttrSpec(spec)
        atributos.append(attrName)
        attrName = tipo+'_out'
        spec = gr.AttrSpec(attrName, 'int', 0)
        g.addNodeAttrSpec(spec)
        atributos.append(attrName)

    for edge in g.edges():
        src, tgt, _ = edge
        for tipo in tiposInteracoes:
            contEdge = g.getEdgeAttr(edge, tipo, 0)

            tipoOut = tipo+'_out'
            contNode = g.getNodeAttr(src, tipoOut, 0)
            contNode += contEdge
            g.setNodeAttr(src, tipoOut, contNode)

            tipoIn = tipo+'_in'
            contNode = g.getNodeAttr(tgt, tipoIn, 0)
            contNode += contEdge
            g.setNodeAttr(src, tipoIn, contNode)

    return atributos

def contandoArestasComMesmaOrigemEDestino(g):
    count = collections.Counter()

    for src, tgt, rel in g.edges():
        count[(src, tgt)] += 1

    paralelas = 0
    for v in count.values():
        if v > 1:
            paralelas += 1

    return paralelas

def limpezaDeAtributos(g, nodeAttrs, edgeAttrs, log):
    """Limpa os atributos de um grafo, mantendo apenas os atributos de
    interesse.

    Args:
        g: grafo
        nodeAttrs: Lista dos atributos de nodo que devem ser mantidos.
        edgeAttrs: Lista dos atributos de aresta que devem ser mantidos.
    """
    names = list(g.nodeAttrSpecs.keys())
    for name in names:
        if name not in nodeAttrs:
            log.debug("Removendo {}".format(name))
            g.removeNodeAttr(name)

    names = list(g.edgeAttrSpecs.keys())
    for name in names:
        if name not in edgeAttrs:
            log.debug("Removendo {}".format(name))
            g.removeEdgeAttr(name)

def imprimeAtributos(g, log):
    log.debug('Atributos de nodos:')
    for spec in g.nodeAttrSpecs.values():
        log.degug('  "{0}": {1} {2}'.format(spec.name, spec.type, spec.default))
    log.debug('Atributos de arestas:')
    for spec in g.edgeAttrSpecs.values():
        log.debug('  "{0}": {1} {2}'.format(spec.name, spec.type, spec.default))

#---------------------------------------------------------------------
# Execução do script
#---------------------------------------------------------------------
if __name__ == '__main__':
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger()
    main(logger)
