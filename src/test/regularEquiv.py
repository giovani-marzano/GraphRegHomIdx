# coding: utf-8

import graph as gr
import os.path

if __name__ == '__main__':

    ARQ_IN = os.path.join('data', 'tesRegularEquiv.graphml')
    ARQ_OUT = os.path.join('data', 'reqEquivProcessado.graphml')
    
    # Le um arquivo de teste preparado em que os nodos possuem um atributo
    # 'preclass' que será utilziado como uma préclassificação dos nodos a partir
    # da qual se buscará uma relação de equivalência regular.
    g = gr.loadGraphml(ARQ_IN)

    g.classifyNodesRegularEquivalence(classAttr='c1')
    g.classifyNodesRegularEquivalence(classAttr='c2', preClassAttr='preclass')

    g.writeGraphml(ARQ_OUT) 
