# coding: utf-8
import math
import collections

class NumericAggregator(object):
    """Agregador de valores núméricos.

    Agrega valores numéricos permitindo a posterior recuperação de estatísticas
    sobre a sequência de números processada.
    """

    STAT_SET = {'count', 'sumX', 'sumX2', 'min', 'max', 'mean', 'var',
        'sampleVar', 'stdef', 'sampleStdev'}

    def __init__(self):
        self._count = 0
        self._sum = 0.0
        self._sumOfSquares = 0.0
        self._min = float('inf')
        self._max = float('-inf')

    @staticmethod
    def getStatType(stat):
        if stat not in NumericAggregator.STAT_SET:
            raise ValueError('Invalid stat "{0}"'.format(stat))

        if stat == 'count':
            return int
        else:
            return float

    @property
    def count(self):
        return self._count

    @property
    def sumX(self):
        return self._sum

    @property
    def sumX2(self):
        return self._sumOfSquares

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def mean(self):
        if self._count > 0:
            return self._sum/self._count
        else:
            return float('nan')

    @property
    def var(self):
        if self._count > 0:
            return (self._sumOfSquares - self.mean**2)/self._count
        else:
            return float('nan')

    @property
    def sampleVar(self):
        if self._count > 1:
            return (self._sumOfSquares - self.mean**2)/(self._count - 1)
        else:
            return float('nan')

    @property
    def stdev(self):
        return math.sqrt(self.var)

    @property
    def sampleStdev(self):
        return math.sqrt(self.sampleVar)

    def __str__(self):
        if self._count > 0:
            return "({0},{1},{2},{3},{4})".format(
                self._count, self._sum,
                self._sumOfSquares,
                self._min, self._max)
        else:
            return "(0,)"

    def __iadd__(self, other):
        d_count = 0
        d_sum = 0.0
        d_sumOfSquares = 0.0
        d_min = float('inf')
        d_max = float('-inf')

        if isinstance(other, Aggregate):
            if other._count > 0:
                d_count = other._count
                d_sum = other._sum
                d_sumOfSquares = other._sumOfSquares
                d_min = other._min
                d_max = other._max
        elif (isinstance(other,int) or
              isinstance(other,float)):
            d_count = 1
            d_sum = other
            d_sumOfSquares = other**2
            d_min = other
            d_max = other
        elif other is None:
            d_count = 0
        else:
            return NotImplemented

        if d_count > 0:
            self._count += d_count
            self._sum += d_sum
            self._sumOfSquares += d_sumOfSquares
            if d_min < self._min:
                self._min = d_min
            if d_max > self._max:
                self._max = d_max

        return self

    def __add__(self, other):
        v = Aggregate()
        v += self
        v += other
        return v

class SymbolicAggregator(object):
    """Agregador de símbolos.
    """

    def __init__(self):
        self.counter = collection.Counter

    def __iadd__(self, other):
        if isinstance(other, SymbolicAggregator):
            self.counter += other.counter
        elif isinstance(other, collection.Counter):
            self.counter += other
        else:
            self[other] += 1

        return self

    def __add__(self, other):
        v = SymbolicAggregator()

        v += self
        v += other

        return v
