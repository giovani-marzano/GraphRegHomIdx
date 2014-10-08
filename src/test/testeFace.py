import graph as gr
from datetime import datetime

arqIn='face.graphml'
arqOut='faceClassificado.graphml'
arqOutNoFriend='faceClassificadoNoFriend.graphml'
arqClasses='classes.graphml'
arqClassesNoFriend='classesNoFriend.graphml'
relationAttr='Relationship'

print(str(datetime.now()))
print("lendo '"+arqIn+"'...")
a = gr.loadGraphml(arqIn, relationAttr)
print("...ok", len(a.nodes()), len(a.edges()))

print(str(datetime.now()))
print("classificando...")
a.classifyNodesRegularEquivalence('regularClass')
print("...ok")

print(str(datetime.now()))
print("salvando em '"+arqOut+"'...")
a.writeGraphml(arqOut)
print("...ok")

print(str(datetime.now()))
print("gerando grafo de classes...")
b = a.spawnFromClassAttributes(
        nodeClassAttr='regularClass', edgeClassAttr=relationAttr)
print("...ok", len(b.nodes()), len(b.edges()))

print(str(datetime.now()))
print("salvando em '"+arqClasses+"'...")
b.writeGraphml(arqClasses)
print("...ok")

print(str(datetime.now()))
print("Retirando realcionamentos do tipo 'Friend'...")
a.removeEdgeByAttr(relationAttr, 'Friend')
print("...ok")

print(str(datetime.now()))
print("classificando...")
a.classifyNodesRegularEquivalence('regularClass')
print("...ok")

print(str(datetime.now()))
print("salvando em '"+arqOutNoFriend+"'...")
a.writeGraphml(arqOutNoFriend)
print("...ok")

print(str(datetime.now()))
print("gerando grafo de classes...")
b = a.spawnFromClassAttributes(
        nodeClassAttr='regularClass', edgeClassAttr=relationAttr)
print("...ok", len(b.nodes()), len(b.edges()))

print(str(datetime.now()))
print("salvando em '"+arqClassesNoFriend+"'...")
b.writeGraphml(arqClassesNoFriend)
print("...ok")

print(str(datetime.now()))
