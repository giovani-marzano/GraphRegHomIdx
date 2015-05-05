#!/usr/bin/python3

import sys
import random
import array
import csv
import os.path
import numpy
import functools

from deap import base, creator, tools, algorithms

# Acrescentando o diretorio lib ao path. Lembrando que sys.path[0] representa o
# diretório onde este script se encontra
sys.path.append(os.path.join(sys.path[0],'lib'))

import graph as gr

#------------------------------------------------------------------------------
# Configurações
#------------------------------------------------------------------------------

FILE_IN='teste.graphml'
FILE_OUT='teste.csv'
LOG_FILE_OUT='testeLog.txt'

NUM_CLASS = 5

NUM_GEN = 100  # Número de gerações
POP_SIZE = 50

SEL_TOURN_SIZE = 10

# Probabilidades
CX_PB = 0.5
MUT_PB = 0.1
MUT_IND_PB = 0.05

RAND_SEED = 64

# Configurações de formato do csv de saída
CSV_OUT_CONFIG = {
    'delimiter': '\t',
    'lineterminator': '\n',
    'quotechar': '"',
    'escapechar': '\\',
    'doublequote': False,
    'quoting': csv.QUOTE_NONNUMERIC,
    'skipinitialspace': True
}
CSV_OUT_DIALECT='appcsvdialect'
csv.register_dialect(CSV_OUT_DIALECT, **CSV_OUT_CONFIG)

#------------------------------------------------------------------------------
# Funções auxiliares
#------------------------------------------------------------------------------
def edgeRelF(edge):
    """Função que recupera a relação de uma aresta
    """
    _, _, rel = edge
    return rel

def createRegIdxEvalFunction(g):
    """Cria uma função de avaliação de classificação para um grafo. A função de
    avaliação deve receber apenas uma lista de classes e retornar o índice de
    regularidade calculado.

    Return:

    - evaluate: Função de avaliação
    - nodeToIdx: O mapeamento de nodos do grafo para indice nas listas de
      classes
    """

    # Devemos mapear cada nodo para o inteiro que será o índice de sua classe na
    # classificação = a posição de seu gene no cromossomo do indivíduo
    nodeToIdx = {n:i for i, n in enumerate(g.nodes())}

    def evaluate(idxToClass):
        """Avalia o mapeamento de indice de nodo para classe fornecido.
        """
        def nodeClassF(node):
            i = nodeToIdx[node]
            return idxToClass[i]

        stats = gr.fullMorphismStats(g, nodeClassF, edgeRelF)
        regIdx = gr.calcGraphRegIdx(*stats)

        return (regIdx, )

    return evaluate, nodeToIdx

def numClassesEvalFunction(clsVet, numCls=1):
    """Avalia uma classificacao pelo número de classes presentes na mesma em
    relação ao número de classes total.
    """

    v = 1.0*len(set(clsVet))

    if v > numCls:
        return (1.0,)
    else:
        return (v/numCls, )

def initConstantClass(container, clsGen, n, mutate):
    """Cria uma instancia de container com n elementos iguais. O valor dos
    elementos é obtido através da função clsGen.
    """

    cls = clsGen()

    return container(cls for _ in range(n))

def initMutateConstantClass(container, n, mutpb=0.5, low=1, up=NUM_CLASS):
    cls = low

    ind = container(cls for _ in range(n))

    for i, _ in enumerate(ind):
        if random.random() < mutpb:
            ind[i] = random.randint(low, up)

    return ind

import heapq
from collections import deque

def selDiverseTournament(individuals, k, compPoolSize, tournSize):
    """Escolha por torneio em que o vencedor de cada torneio não é apenas o com
    melhor fitness, mas também o que mais se difere dos vencedores dos últimos
    torneios realizados.

    A diferença dos indivíduos é obtida contando quantos genes correspondentes
    são diferentes entre dois indivíduos e dividindo pelo número total de genes.

    Considera-se que o valor ideal para fitness é 1.0 e a diversidade ideal
    também é 1.0. O ranking dos individous é obtido por quão próximo ele está do
    ponto (fit = 1.0, diff = 1.0)

    Args:

    - individuals: coleção de indivíduos a serem selecionados.
    - k: número de indivíduos que devem ser selecionados.
    - compPoolSize: Tamanho do pool de vencedores de torneios anteriores usados
      para comparação de diversidade.
    - tournSize: Número de indivíduos selecionados aleatoriamente para cada
      torneio.
    """

    chosen = []
    compPool = deque(maxlen=compPoolSize)
    for i in range(k):
        candidates = tools.selRandom(individuals, tournSize)
        rankHeap = []

        for cand in candidates:
            diff = 0.0
            n = 0
            for ind in compPool:
                n += 1
                for v1, v2 in zip(cand, ind):
                    if v1 != v2:
                        diff += 1
            if n > 0:
                diff = diff/(n*len(cand))
            else:
                diff = 1.0

            rank = (1.0 - diff)**2 + (1.0 - cand.fitness.values[0])**2

            heapq.heappush(rankHeap, (rank, cand))

        # Acrescentando o vencedor entre os escolhidos e no pool de comparação
        _, winner = heapq.heappop(rankHeap)
        chosen.append(winner)
        compPool.append(winner)

    return chosen

#------------------------------------------------------------------------------
# Corpo do script
#------------------------------------------------------------------------------

# Carregando o grafo do arquivo de entrada e criando a função de avaliação e
# mapeamento de indices
g = gr.loadGraphml(FILE_IN, relationAttr='relation')

print('Num edges {0}'.format(g.getNumEdges()))

# Removendo as arestas do tipo Liker
g.removeEdgeByAttr('relation','Liker')
print('Num edges {0}'.format(g.getNumEdges()))

evaluateRegIdx, nodeToIdx = createRegIdxEvalFunction(g)

# Função de avaliação
def evaluateRegIdxAndNumClass(ind):
    t1 = evaluateRegIdx(ind)
    t2 = numClassesEvalFunction(ind, numCls=NUM_CLASS)

    return (v1*v2 for v1, v2 in zip(t1,t2))

evaluateF = evaluateRegIdx

toolbox = base.Toolbox()

creator.create("FitnessMax", base.Fitness, weights=(1.0,))

# cada indivíduo será um array de inteiros sem sinal
creator.create("Individual", array.array, typecode='I',
        fitness=creator.FitnessMax)

toolbox.register('attr_class', random.randint, 1, NUM_CLASS)

toolbox.register('evaluate', evaluateF)
toolbox.register('mate', tools.cxOnePoint)
toolbox.register('mutate', tools.mutUniformInt, low=1, up=NUM_CLASS,
        indpb=MUT_IND_PB)
toolbox.register('select', tools.selTournament, tournsize=SEL_TOURN_SIZE)
# toolbox.register('select', selDiverseTournament, tournSize=SEL_TOURN_SIZE,
#        compPoolSize=SEL_TOURN_SIZE)

#toolbox.register('individual', tools.initRepeat, creator.Individual,
#        toolbox.attr_class, g.getNumNodes())
#toolbox.register('individual', initConstantClass, creator.Individual,
#        toolbox.attr_class, g.getNumNodes())
toolbox.register('individual', initMutateConstantClass, creator.Individual,
        g.getNumNodes())
toolbox.register('population', tools.initRepeat, list, toolbox.individual)

def main():
    random.seed(RAND_SEED)

    pop = toolbox.population(n=POP_SIZE)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    pop, log = algorithms.eaSimple(pop, toolbox,
        cxpb=CX_PB, mutpb=MUT_PB, ngen=NUM_GEN,
        stats=stats, halloffame=hof, verbose=True)

    return pop, log, hof

if __name__ == '__main__':
    pop, log, hof = main()

    print()
    print('Melhor {0}'.format(hof[0].fitness.values[0]))

    # salvando a melhor classificação
    with open(FILE_OUT, 'w', newline='') as f:
        writer = csv.writer(f, CSV_OUT_DIALECT)

        row = ['node', 'class']
        writer.writerow(row)

        for node in g.nodes():
            cls = hof[0][nodeToIdx[node]]
            row = [node, cls]
            writer.writerow(row)

    # salvando o log com estatísticas de cada geração
    with open(LOG_FILE_OUT, 'a') as f:
        f.write(str(log))
        f.write('\n\n\n')

