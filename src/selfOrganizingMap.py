# coding: utf-8

class SOMNode(object):
    """Representa um nodo do SOM generico.
    """

    def __init__(self, nid, refElem, distFun):
	"""Inicializa a instancia.

	:param nid: Identificador do nodo.
	:param refElem: Elemento de referência do nodo.
	:param distFun: Função de distancia a ser utilizada
	"""

	self._id = nid
	self.refElem = refElem
	self.distFun = distFun

	self.neighbors = []

	self.resetElements()

    def getID(self):
	"""Recupera o ID do nodo.
	"""

	return self._id

    def resetElements(self):
	"""Esvazia a lista de elementos.
	"""

	self.elements = []
	self.sumDist = 0
	self._meanElement = None
	self._meanSumDist = None
	self._secondBest = None
	self._secondBestDist = None

    def calcSumDistToElements(self, elem)
	"""Calcula a soma das distancias do elemento fornecido aos
	elementos atribuídos a este nodo.

	:param elem: Elemento que sera comparado
	
	:return: Soma das distancias
	"""

	sumDist = 0
	for e in self.elements:
	    sumDist += self.distFun(elem, e)

	return sumDist

    def _findMeanElement(self):
	mean = self.refElem
	meanSumDist = self.sumDist

	for candidate in self.elements:
	    candidateSumDist = self.calcSumDistToElements(candidate)

	    if candidateSumDist < meanSumDist:
		mean = candidate
		meanSumDist = candidateSumDist

	self._meanElement = mean
	self._meanSumDist = meanSumDist

    def getMeanElement(self):
	if self._meanElement == None:
	    self._findMeanElement()

	return self._meanElement

    def getMeanSumDist(self):
	if self._meanSumDist == None:
	    self._findMeanElement()

	return self._meanSumDist

    def getNumElements(self):
	return len(self.elements)

    def insert(self, elem, dist=None):
	"""Insere um elemento na lista de elementos."
	"""

	if dist == None:
	    dist = self.dist(elem)

	self.elements.append(elem)
	self.sumDist += dist

	if self._secondBest == None:
	    if dist > 0:
		self._secondBest = elem
		self._secondBestDist = dist
	elif dist > 0:
	    if dist < self._secondBestDist:
		self._secondBest = elem
		self._secondBestDist = dist

    def dist(self, elem):
	return self.distFun(self.refElem, elem)

    def _calcElemNetDist(self, elem):
	dist = self.distFun(elem, self.getMeanElement())

	weightedSumDist = dist * self.getNumElements()
	sumWeigths = self.getNumElements()

	for node in self.neighbors:
	    dist = self.distFun(elem, node.getMeanElement())
	    weight = 0.5 * self.getNumElements()
	    weightedSumDist += dist * weight
	    sumWeigths += weight

	return weightedSumDist/sumWeigths

    def updateRefElem(self):
	newRef = self.getMeanElement()
	newRefDist = self._calcElemNetDist(newRef)

	for elem in self.elements:
	    dist = self._calcElemNetDist(elem)

	    if dist < newRefDist:
		newRef = elem
		newRefDist = dist

	# TODO: update second best

	self.refElem = newRef


class SOMap(object):
    """Um mapa auto organizável.
    """

    def __init__(self, distFun):
	"""Construtor de um SOM.

	:param distFun: Função de distancia a ser utilizada
	"""
	self.distFun = distFun

	self.nodes = []
	self.elements = []

    def _assignOneElement(self, elem):

	bestNode = self.nodes[0]
	bestDist = bestNode.dist(elem)

	for node in self.nodes:
	    dist = node.dist(elem)
	    if dist < bestDist:
		bestDist = dist
		bestNode = node

	bestNode.insert(elem, bestDist)

    def _assignElements(self):

	for elem in self.elements:
	    self._assignOneElement(elem)

    def _resetNodes(self):
	for node in self.nodes:
	    node.resetElements()

    def _updateNodes(self):
	"""Atualiza os nodos com base nos elementos distribuídos.

	:return: Se houve atualização de algum nodo
	"""

	changed = False

	for node in self.nodes:
	    oldRef = node.refElem
	    node.updateRefElem()
	    if oldRef != node.refElem:
		changed = True
	
	return changed

    def _trainStep(self):
	"""Realiza um passo de treinamento.

	:return: Se hounve mudanca em algum nodo.
	"""
	
	self._resetNodes()
	self._assignElements()
	return self._updateNodes()
