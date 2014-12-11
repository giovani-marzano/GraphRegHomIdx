#!/usr/bin/python3
# coding: utf-8

#---------------------------------------------------------------------
# Seção de importação de modulos
#---------------------------------------------------------------------
from __future__ import print_function

import os.path
import collections
import io
import logging
import logging.config
import csv

import sys

# Acrescentando o diretorio lib ao path. Lembrando que sys.path[0] representa o
# diretório onde este script se encontra

sys.path.append(os.path.join(sys.path[0],'lib'))

import graph as gr
import SOM.vectorBased as somV

if sys.version_info.major < 3:
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

#---------------------------------------------------------------------
# Variaveis globais de configuração
#---------------------------------------------------------------------

# Variavéis que controlam de onde os dados de entrada serão lidos
DIR_INPUT = '.'
ARQ_IN = os.path.join(DIR_INPUT,'entrada.csv')

# Configuracao de que colunas do arquivo csv que serao utilizadas
# Nome das colunas de identificacao
ID_ATTRS = ['id','di']
# Nome das colunas de valores
VALUE_ATTRS = ['a','b','c']

# Configuraçoes do formato do arquivo CSV
CSV_OPTIONS = {
    'delimiter': ';'
}

# Variáveis que controlam onde os dados de saida do script serão salvos
DIR_OUTPUT = 'data'
ARQ_SOM = os.path.join(DIR_OUTPUT,'SOM.graphml')
ARQ_CLASSES_SOM = os.path.join(DIR_OUTPUT, 'classesSOM.csv')

# Configurações para controlar o algoritmo SOM
SOM_CONFIG = {
    'Tipo': 'grid', # Pode ser 'grid' ou 'tree'
    'FVU': 0.2,
    'maxNodes': 3, #para TREE
    'neighWeightTrain': 0.25,
    'neighWeightRefine': 0.25,
    'maxStepsPerGeneration': 100,
    'MSTPeriod': 10,
    'nrows': 5, #numero de linhas
    'ncols': 4  #numero de colunas
}

# Configurações para controlar a geração de log pelo script
ARQ_LOG = os.path.join(DIR_OUTPUT,'log.txt')
LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'brief': {
            'format': '%(message)s'
        },
        'detail': {
            'format': '%(asctime)s|%(levelname)s:%(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'brief'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG'
    }
}

#---------------------------------------------------------------------
# Função principal do script
#---------------------------------------------------------------------
def main(log):
    """Função principal do script, executada no final do arquivo.
    """
    log.info('Carregando {}...'.format(ARQ_IN))
    elements, attrNames = carregaArquivo(ARQ_IN, idAttrs=ID_ATTRS,
            valueAttrs=VALUE_ATTRS)

    criaSOM(log, elements, attrNames)

#---------------------------------------------------------------------
# Definição das funções auxiliares e procedimentos macro do script
#---------------------------------------------------------------------

def carregaArquivo(fileName, idAttrs=[], valueAttrs=[]):

    csvReader = csv.reader(open(fileName, newline=''), **CSV_OPTIONS)

    elements = {}
    idCols = set()
    valueCols = set()
    attrNames = []

    elemNum = 0
    for campos in csvReader:
        if elemNum == 0:
            # Estamos lendo a primeira linha que possui o cabecalho
            cabecalho = campos
            for n, c in enumerate(campos):
                if c in idAttrs:
                    idCols.add(n)
                elif c in valueAttrs:
                    valueCols.add(n)
                    attrNames.append(c)
        else:
            id = [elemNum]
            vet = []
            for n, v in enumerate(campos):
                if n in idCols:
                    id.append(v)
                elif n in valueCols:
                    vet.append(float(v))
            elements[tuple(id)] = vet

        elemNum += 1

    return elements, attrNames

def criaSOM(log, elements, attrNames):
    som = somV.SOMap('SOM')
    som.conf.dictConfig(SOM_CONFIG)
    som.elements = list(elements.values())
    log.info('Treinando SOM...')
    if SOM_CONFIG['Tipo'] == 'grid':
        som.trainHexGrid(
            SOM_CONFIG.get('nrows', 5),
            SOM_CONFIG.get('ncols', 4)
        )
    else:
        som.trainGrowingTree()

    log.info('...ok')

    # Salvando o som de nodos
    gsom = somV.convertSOMapToMultiGraph(som,
            attrNames=attrNames, nodeIDAttr='ID')
    gsom.writeGraphml(ARQ_SOM)

#---------------------------------------------------------------------
# GUI
#---------------------------------------------------------------------
from tkinter.simpledialog import Dialog
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import gui

class ConfigGUI(tk.Frame):
    def __init__(self, master, logger, **options):
        global ARQ_IN

        ARQ_IN = ''

        super().__init__(master, **options)

        self.logger = logger

        self.arqIn = tk.StringVar()
        self.arqIn.set(ARQ_IN)
        frArqIn = tk.Frame(self)
        lbArqIn = tk.Label(frArqIn, text="Arquivo de entrada:")
        lbArqInFile = tk.Label(frArqIn, textvariable=self.arqIn)
        frArqIn.rowconfigure(0, weight=1)
        frArqIn.columnconfigure(1, weight=1)
        lbArqIn.grid(row=0, column=0, sticky=tk.EW)
        lbArqInFile.grid(row=0, column=1, sticky=tk.EW)
        frArqIn.grid(row=0, column=0, sticky=tk.EW)

        self.btArqIn = tk.Button(self, text='1: Selecionar o arquivo de entrada',
            command=self.doBtArqIn)
        self.btArqIn.grid(row=1, column=0, sticky=tk.EW)

        # Lista com os cabeçalhos dos dados
        self.headers = []

        self.btIds = tk.Button(self, text='2: Selecionar atributos de identificação',
            command=self.doBtIds)
        self.btIds.grid(row=2, column=0, sticky=tk.EW)

        self.btValues = tk.Button(self, text='3: Selecionar atributos de valor',
            command=self.doBtValues)
        self.btValues.grid(row=3, column=0, sticky=tk.EW)

        self.btConfSOM = tk.Button(self, text='4: Configurar SOM',
            command=self.doBtConfSOM)
        self.btConfSOM.grid(row=4, column=0, sticky=tk.EW)

        self.btGerarSOM = tk.Button(self, text='5: Gerar e salvar SOM',
            command=self.doBtGerarSOM)
        self.btGerarSOM.grid(row=5, column=0, sticky=tk.EW)

    def doBtConfSOM(self):
        confDialog = SOMConfDialog(self)

    def doBtGerarSOM(self):
        global ARQ_SOM

        fileName = filedialog.asksaveasfilename(
            title='Arquivo para salvar o SOM',
            filetypes=[('graphml','*.graphml')], defaultextension='.graphml')

        if fileName != '':
            ARQ_SOM = fileName

            if messagebox.askokcancel('Confirmar execução',
                'O programa irá gerar o SOM no arquivo especificado.\n' +
                'A janela de configuração irá se fechar. Acompanhe o treinamento\n' +
                'pelo terminal.'):

                # Destruindo a GUI.
                w = self.winfo_toplevel()
                self.after_idle(w.quit)
                w.destroy()

    def doBtValues(self):
        global VALUE_ATTRS

        attrSel = gui.ListSelecManyDialog(self, title="Seleção de atributos",
                text="Selecione os atributos que possuem os dados a serem processados.",
                items=self.headers)

        if attrSel.result is not None:
            VALUE_ATTRS = [ x for n, x in attrSel.result ]

    def doBtIds(self):
        global ID_ATTRS

        attrSel = gui.ListSelecManyDialog(self, title="Seleção de atributos",
                text="Selecione os atributos que identificam as amostras.",
                items=self.headers)

        if attrSel.result is not None:
            ID_ATTRS = [ x for n, x in attrSel.result ]

    def doBtArqIn(self):
        global ARQ_IN

        fileName = filedialog.askopenfilename(filetypes=[('CSV','*.csv')])
        if fileName != '':
            ARQ_IN = fileName
            self.arqIn.set(ARQ_IN)

            with open(fileName, newline='') as f:
                csvReader = csv.reader(f, **CSV_OPTIONS)
                for campos in csvReader:
                    self.headers = campos
                    break

            print(self.headers)


class SOMConfDialog(Dialog):
    def __init__(self, master):
        self.Tipo = tk.StringVar()
        self.FVU = tk.DoubleVar()
        self.maxNodes = tk.IntVar()
        self.neighWeightTrain = tk.DoubleVar()
        self.neighWeightRefine = tk.DoubleVar()
        self.maxStepsPerGeneration = tk.IntVar()
        self.MSTPeriod = tk.IntVar()
        self.nrows = tk.IntVar()
        self.ncols = tk.IntVar()

        self.Tipo.set(SOM_CONFIG.get('Tipo', 'grid'))
        self.FVU.set(SOM_CONFIG.get('FVU', 0.2))
        self.maxNodes.set(SOM_CONFIG.get('maxNodes', 20))
        self.neighWeightTrain.set(SOM_CONFIG.get('neighWeightTrain', 0.5))
        self.neighWeightRefine.set(SOM_CONFIG.get('neighWeightRefine', 0.5))
        self.maxStepsPerGeneration.set(SOM_CONFIG.get('maxStepsPerGeneration',
                    100))
        self.MSTPeriod.set(SOM_CONFIG.get('MSTPeriod',20))
        self.nrows.set(SOM_CONFIG.get('nrows', 10))
        self.ncols.set(SOM_CONFIG.get('ncols', 15))

        super().__init__(master, "Parâmetros SOM")

    def body(self, master):
        widgets = []
        lbTipo = tk.Label(master, text='Tipo de SOM:')
        frTipo = tk.Frame(master)
        rbTipoGrid = tk.Radiobutton(frTipo, text='grid', value='grid',
                variable=self.Tipo)
        rbTipoTree = tk.Radiobutton(frTipo, text='tree', value='tree',
                variable=self.Tipo)
        rbTipoGrid.grid(row=0, column=0, sticky=tk.EW)
        rbTipoTree.grid(row=0, column=1, sticky=tk.EW)
        widgets.append((lbTipo, frTipo))

        label = tk.Label(master, text='Máximo número de Nodos\n (tree SOM):')
        control = tk.Spinbox(master, from_=1, to=1000, increment=1,
            textvariable=self.maxNodes)
        widgets.append((label, control))

        label = tk.Label(master, text='Número de linhas da grade\n (grid SOM):')
        control = tk.Spinbox(master, from_=1, to=100, increment=1,
            textvariable=self.nrows)
        widgets.append((label, control))

        label = tk.Label(master, text='Número de colunas da grade\n (grid SOM):')
        control = tk.Spinbox(master, from_=1, to=100, increment=1,
            textvariable=self.ncols)
        widgets.append((label, control))

        label = tk.Label(master, text='Fraction of Variance\n' +
                'Unexplained (tree SOM)')
        control = tk.Spinbox(master, from_=0.05, to=0.95, increment=0.05,
            textvariable=self.FVU)
        widgets.append((label, control))

        label = tk.Label(master, text='Peso da vizinhança no\n treinamento:')
        control = tk.Spinbox(master, from_=0.0, to=0.9, increment=0.1,
            textvariable=self.neighWeightTrain)
        widgets.append((label, control))

        label = tk.Label(master, text='Peso da vizinhança no\n refinamento:')
        control = tk.Spinbox(master, from_=0.0, to=0.9, increment=0.1,
            textvariable=self.neighWeightRefine)
        widgets.append((label, control))

        label = tk.Label(master, text='Máximo de iterações\n por época:')
        control = tk.Spinbox(master, from_=1, to=10000, increment=1,
            textvariable=self.maxStepsPerGeneration)
        widgets.append((label, control))

        label = tk.Label(master, text='Iterações entre cálculo da\n' +
                'árvore geradora mínima (tree SOM):')
        control = tk.Spinbox(master, from_=1, to=10000, increment=1,
            textvariable=self.MSTPeriod)
        widgets.append((label, control))

        n = 0
        for label, control in widgets:
            label.grid(row=n, column=0, sticky=tk.EW)
            control.grid(row=n, column=1, sticky=tk.EW)
            n += 1

        master.pack(expand=True, fill='both')

    def apply(self):
        SOM_CONFIG['Tipo'] = self.Tipo.get()
        SOM_CONFIG['FVU'] = self.FVU.get()
        SOM_CONFIG['maxNodes'] = self.maxNodes.get()
        SOM_CONFIG['neighWeightTrain'] = self.neighWeightTrain.get()
        SOM_CONFIG['neighWeightRefine'] = self.neighWeightRefine.get()
        SOM_CONFIG['maxStepsPerGeneration'] = self.maxStepsPerGeneration.get()
        SOM_CONFIG['MSTPeriod'] = self.MSTPeriod.get()
        SOM_CONFIG['nrows'] = self.nrows.get()
        SOM_CONFIG['ncols'] = self.ncols.get()

#---------------------------------------------------------------------
# Execução do script
#---------------------------------------------------------------------
if __name__ == '__main__':
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger()
    app = tk.Tk()
    a = ConfigGUI(app, logger)
    a.pack(expand=True, fill='both')
    app.mainloop()
    logger.info("Iniciando processamento...")
    main(logger)
