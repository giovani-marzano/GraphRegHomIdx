import graph as gr

arqIn='face.graphml'
arqOut='faceClassificado.graphml'
arqClasses='classes.graphml'

print("lendo '"+arqIn+"'...")
a = gr.loadGraphml(arqIn, 'Relationship')
print("...ok")

print("classificando...")
a.classifyNodesRegularEquivalence('regularClass')
print("...ok")

print("salvando em '"+arqOut+"'...")
a.writeGraphml(arqOut)
print("...ok")

print("gerando grafo de classes...")
b = a.spawnFromClassAttributes(
        nodeClassAttr='regularClass', edgeClassAttr='Relationship')
print("...ok")

print("salvando em '"+arqClasses+"'...")
b.writeGraphml(arqClasses)
print("...ok")
