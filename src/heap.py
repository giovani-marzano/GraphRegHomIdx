# coding: utf-8
"""Implementação de um heap mínimo segundo livro Algoritmos, Teoria e Prática de
Cormen et al.
"""

class HeapData(object):
    """Objetos que sao armazenados no heap.
    """

    def __init__(self, key, data):
        """Construtor.

        :param key: Chave para o dado no heap. Deve ser um tipo comparável.
        :param data: Dado a ser armazenado no heap.
        """

        self._heap = None
        self._index = None
        self._key = key
        self.data = data

    def changeKey(self, newKey):
        if self._heap == None:
            self._key = newKey
            return

        if newKey < self._key:
            self._key = newKey
            self._heap._goUpHeap(self)
        else:
            self._key = newKey
            self._heap._goDownHeap(self)

    def left(self):
        return (self._index*2 + 1)

    def right(self):
        return (self._index*2 + 2)

    def parent(self):
        return (self._index - 1)/2

    def getKey(self):
        return self._key

    def isInHeap(self):
        return self._heap != None

class Heap(object):
    """Um heap mínimo."""

    def __init__(self):
        self._list = []

    def push(self, key, data):
        hd = HeapData(key, data)
        hd._heap = self
        hd._index = len(self._list)
        self._list.append(hd)
        self._goUpHeap(hd)

        return hd

    def isEmpty(self):
        return len(self._list) == 0

    def pop(self):
        """Retira o menor elemento da lista

        :return: (key, data)
        """
        head = self._list[0]
        head._heap = None
        head._index = None

        last = self._list.pop()
        if len(self._list) > 0:
            last._index = 0
            self._list[0] = last
            self._goDownHeap(last)

        return (head._key, head.data)

    def _goDownHeap(self, hd):
        left = hd.left()
        right = hd.right()
        small = hd._index

        H = self._list

        if left < len(H) and H[left]._key < H[small]._key:
            small = left

        if right < len(H) and H[right]._key < H[small]._key:
            small = right

        if small != hd._index:
            H[small]._index = hd._index
            H[hd._index] = H[small]
            hd._index = small
            H[small] = hd

            self._goDownHeap(H[small])

    def _goUpHeap(self, hd):
        H = self._list

        parent = hd.parent()
        while hd._index > 0 and hd._key < H[parent]._key:
            H[parent]._index = hd._index
            H[hd._index] = H[parent]
            hd._index = parent
            H[parent] = hd
            parent = hd.parent()

# TEST
if __name__ == "__main__":
    import random

    a = range(20)
    random.shuffle(a)
    print(a)

    heap = Heap()
    for d in a:
        heap.push(d,d)
    
    b = []
    while not heap.isEmpty():
        (k,d) = heap.pop()
        b.append(d)
    print(b)

    a = []
    for d in range(20):
        a.append(heap.push(d,d))

    a[0].changeKey(10)
    a[10].changeKey(19)
    a[19].changeKey(9)
    a[18].changeKey(0)

    b = []
    while not heap.isEmpty():
        (k,d) = heap.pop()
        b.append(d)
    print(b)
