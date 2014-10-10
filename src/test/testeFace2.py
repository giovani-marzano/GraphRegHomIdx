import graph as gr

def grafoSoUmTipoAresta(a, tipo):
    b = a.spawnFromClassAttributes(edgeClassAttr='Relationship')

    print(tipo, len(b.nodes()), len(b.edges()))
    for edge in b.edges():
        if b.getEdgeAttr(edge, 'Relationship') == tipo:
            b.setEdgeAttr(edge, 'filtro', 1)
        else:
            b.setEdgeAttr(edge, 'filtro', 0)

    b.removeEdgeByAttr('filtro', 0)
    print(tipo, len(b.nodes()), len(b.edges()))

    b.classifyNodesRegularEquivalence('class')
    attrName = 'class '+tipo
    spec = gr.AttrSpec(attrName, 'int')
    a.addNodeAttrSpec(spec)
    for node in b.nodes():
        a.setNodeAttr(node, attrName, b.getNodeAttr(node, 'class'))

    b = b.spawnFromClassAttributes(nodeClassAttr='class',
            edgeClassAttr='Relationship')
    b.writeGraphml(tipo)
    print(tipo, len(b.nodes()), len(b.edges()))

a = gr.loadGraphml('face.graphml')
print('Original', len(a.nodes()), len(a.edges()))
a = a.spawnFromClassAttributes(edgeClassAttr='Relationship')
print('Relationship', len(a.nodes()), len(a.edges()))

grafoSoUmTipoAresta(a, 'Commenter')
grafoSoUmTipoAresta(a, 'Post Author')
grafoSoUmTipoAresta(a, 'User Tagged')
grafoSoUmTipoAresta(a, 'Liker')

print('Salvando faceMarcado...')
a.writeGraphml('faceMarcado')
print('...ok')