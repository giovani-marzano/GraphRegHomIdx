#!/usr/bin/python3
# coding: utf-8

import graph as gr
import collections
import io
import sys

if sys.version < '3':
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

RELATION_ATTR='Relationship'
WEIGHT_ATTR='Edge Weight'
NODE_ID_ATTR='n-id'
NODE_NAME_ATTR='n-name'

def main():
    """Função principal do script, executada no final do arquivo.
    """
    geral = gr.loadGraphml('data/face.graphml', relationAttr=RELATION_ATTR)

    #limpezaDeAtributos(geral, [], [WEIGHT_ATTR, RELATION_ATTR])
    #imprimeAtributos(geral)

    # Pegando o conjunto de todos os tipos de arestas do grafo
    tiposIteracoes = geral.getEdgeAttrValueSet(RELATION_ATTR);

    # Agregando as arestas diferentes entre dois nós e contando os tipos de
    # arestas.
    novo, edgeIterations = relationShipParaAtributoDeAresta(
            geral, tiposIteracoes, WEIGHT_ATTR)

    nodeIterations = contandoIteracoesPorNodo(novo, tiposIteracoes)

    criaArffParaNodos(novo, 'data/nodos.arff', nodeIterations)
    criaArffParaArestas(novo, 'data/arestas.arff', edgeIterations)

    #novo.writeGraphml('data/processado.graphml')

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

def contandoIteracoesPorNodo(g, tiposIteracoes):
    """Soma em cada nodo o total de cada tipo de arestas de saída e de entrada
    que o nodo possui.

    Irá criar em cada nodo do grafo g atributos como Liker_in, Liker_out,
    Commenter_in, Commenter_out, etc.
    """

    atributos = []
    
    for tipo in tiposIteracoes:
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
        for tipo in tiposIteracoes:
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

    for k, v in count.items():
        print(k,v)

def limpezaDeAtributos(g, nodeAttrs, edgeAttrs):
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
            print("Removendo {}".format(name))
            g.removeNodeAttr(name)

    names = list(g.edgeAttrSpecs.keys())
    for name in names:
        if name not in edgeAttrs:
            print("Removendo {}".format(name))
            g.removeEdgeAttr(name)

def imprimeAtributos(g):
    print('Atributos de nodos:')
    for spec in g.nodeAttrSpecs.values():
        print('  "{0}": {1} {2}'.format(spec.name, spec.type, spec.default))
    print('Atributos de arestas:')
    for spec in g.edgeAttrSpecs.values():
        print('  "{0}": {1} {2}'.format(spec.name, spec.type, spec.default))

if __name__ == '__main__':
    main()
