from graph import loadGraphml, AttrSpec, agregateClassAttr

a = loadGraphml('data/teste.graphml', relationAttr='class')

nodeAttr, edgeAttr, nodeSpecs, edgeSpecs = agregateClassAttr(a, 'class', 'class', ['dias'],
['weight'])

b = a.spawnFromClassAttributes(nodeClassAttr='class',edgeClassAttr='class')
for spec in nodeSpecs:
    b.addNodeAttrSpec(spec)
for spec in edgeSpecs:
    b.addEdgeAttrSpec(spec)
for name, attrDict in nodeAttr.items():
    b.setNodeAttrFromDict(name, attrDict)
for name, attrDict in edgeAttr.items():
    b.setEdgeAttrFromDict(name, attrDict)

b.writeGraphml('data/b')

a.classifyNodesRegularEquivalence(classAttr='regClass')

nodeAttr, edgeAttr, nodeSpecs, edgeSpecs = agregateClassAttr(a, 'regClass', 'class', ['dias'],
['weight'])

b = a.spawnFromClassAttributes(nodeClassAttr='regClass',edgeClassAttr='class')
for spec in nodeSpecs:
    b.addNodeAttrSpec(spec)
for spec in edgeSpecs:
    b.addEdgeAttrSpec(spec)
for name, attrDict in nodeAttr.items():
    b.setNodeAttrFromDict(name, attrDict)
for name, attrDict in edgeAttr.items():
    b.setEdgeAttrFromDict(name, attrDict)

b.writeGraphml('data/c')
