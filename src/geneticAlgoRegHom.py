#!/usr/bin/python3

import sys
import random
import array
import csv
import os.path
import numpy

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

MIN_CLASS = 1
MAX_CLASS = 7

NUM_GEN = 100  # Número de gerações
POP_SIZE = 50

SEL_TOURN_SIZE = 5

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

def createEvaluationFunction(g):
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

#------------------------------------------------------------------------------
# Corpo do script
#------------------------------------------------------------------------------

# Carregando o grafo do arquivo de entrada e criando a função de avaliação e
# mapeamento de indices
g = gr.loadGraphml(FILE_IN)

evaluateF, nodeToIdx = createEvaluationFunction(g)

# Configurando o arcabouço de algoritmo genético

creator.create("FitnessMax", base.Fitness, weights=(1.0,))

# cada indivíduo será um array de inteiros sem sinal
creator.create("Individual", array.array, typecode='I',
        fitness=creator.FitnessMax)

toolbox = base.Toolbox()

toolbox.register('attr_class', random.randint, MIN_CLASS, MAX_CLASS)

toolbox.register('individual', tools.initRepeat, creator.Individual,
        toolbox.attr_class, g.getNumNodes())
toolbox.register('population', tools.initRepeat, list, toolbox.individual)

toolbox.register('evaluate', evaluateF)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', tools.mutUniformInt, low=MIN_CLASS, up=MAX_CLASS,
        indpb=MUT_IND_PB)
toolbox.register('select', tools.selTournament, tournsize=SEL_TOURN_SIZE)

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

    with open(FILE_OUT, 'w', newline='') as f:
        writer = csv.writer(f, CSV_OUT_DIALECT)

        row = ['node', 'class']
        writer.writerow(row)

        for node in g.nodes():
            cls = hof[0][nodeToIdx[node]]
            row = [node, cls]
            writer.writerow(row)
