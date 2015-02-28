import graph as gr
import os.path

DIR_DATA='data'

def grafoSoUmTipoAresta(a, tipo):
    b = a.spawnFromClassAttributes(edgeClassAttr='Relationship')

    print(tipo, b.getNumNodes(), b.getNumEdges())
    for edge in b.edges():
        if b.getEdgeAttr(edge, 'Relationship') == tipo:
            b.setEdgeAttr(edge, 'filtro', 1)
        else:
            b.setEdgeAttr(edge, 'filtro', 0)

    b.removeEdgeByAttr('filtro', 0)
    print(tipo, b.getNumNodes(), b.getNumEdges())

    b.classifyNodesRegularEquivalence('class')
    print("regular eqv ok")
    attrName = 'class '+tipo
    spec = gr.AttrSpec(attrName, 'int')
    a.addNodeAttrSpec(spec)
    for node in b.nodes():
        a.setNodeAttr(node, attrName, b.getNodeAttr(node, 'class'))

    nodeAttrs, edgeAttrs, nodeSpecs, edgeSpecs = gr.aggregateClassAttr(b,
        nodeClassAttr='class', edgeClassAttr='Relationship',
        edgeAttrs=['Edge Weight'])

    b = b.spawnFromClassAttributes(nodeClassAttr='class',
            edgeClassAttr='Relationship')

    components = gr.weaklyConnectedComponents(b)
    b.setNodeAttrFromDict('pattern',components, default=-1, attrType='int')

    for spec in nodeSpecs:
        b.addNodeAttrSpec(spec)
        b.setNodeAttrFromDict(spec.name, nodeAttrs[spec.name])
    for spec in edgeSpecs:
        b.addEdgeAttrSpec(spec)
        b.setEdgeAttrFromDict(spec.name, edgeAttrs[spec.name])

    print(tipo, b.getNumNodes(), b.getNumEdges())

    b.writeGraphml(os.path.join(DIR_DATA,tipo))
    print(tipo+' salvo')

a = gr.loadGraphml(os.path.join(DIR_DATA,'face.graphml'))
print('Original', a.getNumNodes(), a.getNumEdges())
a = a.spawnFromClassAttributes(edgeClassAttr='Relationship')
print('Relationship', a.getNumNodes(), a.getNumEdges())

grafoSoUmTipoAresta(a, 'Commenter')
grafoSoUmTipoAresta(a, 'Post Author')
grafoSoUmTipoAresta(a, 'User Tagged')
grafoSoUmTipoAresta(a, 'Liker')

print('Salvando faceMarcado...')
a.writeGraphml(os.path.join(DIR_DATA,'faceMarcado'))
print('...ok')
