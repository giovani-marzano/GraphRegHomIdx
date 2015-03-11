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
import SOM
import silhouette as silhou

#---------------------------------------------------------------------
# Variaveis globais de configuração
#---------------------------------------------------------------------

# Configurações para controlar a geração de log pelo script
ARQ_LOG = 'som.log'
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
        'arquivo': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detail',
            'filename': ARQ_LOG,
            'mode': 'w'
        }
    },
    'root': {
        'handlers': ['console', 'arquivo'],
        'level': 'DEBUG'
    }
}

#---------------------------------------------------------------------
# Classe de controle do aplicativo
#---------------------------------------------------------------------
class SOMAppControl(object):
    """Classe que controla o caso de uso do aplicativo.

    Atributos configuráveis:

    - fileNameData: Nome do arquivo CSV com os dados a serem processados.

    - idAttrs: Lista com os nomes dos atributos que identificam os elementos.

    - valueAttrs: Lista com os nomes dos atributos de valor dos elementos.

    - fileNameSOM: Nome do arquivo graphml no qual o SOM será salvo.

    - fileNameClusAssoc: Nome do arquivo CSV onde será salva a associação de
      cada elemento ao nodo do SOM a que ele foi atribuído.
    """

    def __init__(self, logger):
        """
        Args:

        - logger: Objeto usado para gerar mensagens de log
        """
        self.logger = logger

        self.fileNameSOM = ''
        self.fileNameClusAssoc = ''
        self.clearDataFile()

        # Tipo de SOM, pode ser 'tree' ou 'grid'
        self.SOMConf = {
            'Tipo': 'tree',
            'FVU': SOM.Config.FVU_DFLT,
            'maxNodes': SOM.Config.MAX_NODES_DFLT, #para TREE
            'neighWeightTrain': SOM.Config.NEIGH_WEIGHT_TRAIN_DFLT,
            'neighWeightRefine': SOM.Config.NEIGH_WEIGHT_REFINE_DFLT,
            'maxStepsPerGeneration': SOM.Config.MAX_STEPS_PER_GENERATION_DFLT,
            'MSTPeriod': SOM.Config.MST_PERIOD_DFLT,
            'nrows': 5, #numero de linhas
            'ncols': 4  #numero de colunas
        }

    def clearDataFile(self):
        self.fileNameData = ''
        self.idAttrs = []
        self.valueAttrs = []
        self.attrNames = []
        self.csvDialect = None

    def openDataFile(self,fileName):
        self.clearDataFile()

        f = open(fileName, newline='')
        self.csvDialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        self.fileNameData = fileName

        # Le a primeira linha para recuperar os nomes dos atributos
        reader = csv.reader(f, self.csvDialect)
        for row in reader:
            self.attrNames = row
            break

        f.close()

    def setIdAttrs(self, attrs):
        self.idAttrs = [ x for x in attrs if x in self.attrNames ]

    def setValueAttrs(self, attrs):
        self.valueAttrs = [ x for x in attrs if x in self.attrNames ]

    def _carregaDados(self):
        self.logger.info('Carregando {}...'.format(self.fileNameData))
        with open(self.fileNameData, newline='') as f:
            csvReader = csv.reader(f, self.csvDialect)

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
                        if c in self.idAttrs:
                            idCols.add(n)
                        elif c in self.valueAttrs:
                            valueCols.add(n)
                            attrNames.append(c)
                else:
                    idList = [elemNum]
                    vet = []
                    for n, v in enumerate(campos):
                        if n in idCols:
                            idList.append(v)
                        elif n in valueCols:
                            vet.append(float(v))
                    elements[tuple(idList)] = vet

                elemNum += 1
        self.logger.info('...ok')

        return elements, attrNames

    def _criaSOM(self, elements, attrNames):
        som = somV.SOMap('SOM')
        som.conf.dictConfig(self.SOMConf)
        som.elements = list(elements.values())
        self.logger.info('Treinando SOM...')
        if self.SOMConf['Tipo'] == 'grid':
            som.trainHexGrid(
                self.SOMConf.get('nrows', 5),
                self.SOMConf.get('ncols', 4)
            )
        else:
            som.trainGrowingTree()
        self.logger.info('...ok')

        self.logger.info('Classificando elementos...')
        classes, quantErr = som.classifyMapOfElements(elements)
        self.logger.info('...ok')

        self.logger.info('Calculando silhouette indices...')
        elemSilh, clusSilh, totalSilh, neighClust = silhou.evaluateClusters2(
                elements, classes)
        self.logger.info('...ok')

        # Salvando o som de nodos
        if self.fileNameSOM != '' and self.fileNameSOM is not None:
            self.logger.info('Salvando SOM...')
            gsom = somV.convertSOMapToMultiGraph(som,
                    attrNames=attrNames, nodeIDAttr='ID')

            spec = gr.AttrSpec('Total silhouette','double')
            gsom.addGraphAttrSpec(spec)
            gsom.setGraphAttr(spec.name, totalSilh)

            gsom.setNodeAttrFromDict('Node silhouette', clusSilh,
                    attrType='double', default=0)

            gsom.writeGraphml(self.fileNameSOM)
            self.logger.info('...ok')

        return classes, quantErr, elemSilh, neighClust

    def _writeClassificationCSV(self, classes, quantErr, elemSilh, neighboor):

        if self.fileNameClusAssoc is None or self.fileNameClusAssoc == '':
            return

        with open(self.fileNameClusAssoc, 'w', newline='') as f:
            csvWriter = csv.writer(f, self.csvDialect, escapechar='\\')
            csvWriter.writerow(['#'] + self.idAttrs +
                    ['classe_som','erro_de_quantizacao','silhouette','cluster_vizinho'])
            for ids in sorted(classes.keys()):
                row = list(ids) + [
                    classes[ids], quantErr[ids], elemSilh[ids], neighboor[ids]
                    ]
                csvWriter.writerow(row)

    def processData(self):
        """Função principal do script, executada no final do arquivo.
        """
        elements, attrNames = self._carregaDados()

        classes, erros, silh, neighClust = self._criaSOM(elements, attrNames)

        self._writeClassificationCSV(classes,erros,silh, neighClust)

#---------------------------------------------------------------------
# GUI
#---------------------------------------------------------------------
from tkinter.simpledialog import Dialog
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import gui
import textwrap

class ConfigGUI(tk.Frame):
    def __init__(self, master, logger, **options):
        global ARQ_IN

        ARQ_IN = ''

        super().__init__(master, **options)

        self.executar = False
        self.master = master

        self.logger = logger
        self.control = SOMAppControl(logger)

        row = 0

        # Arquivo de entrada
        self.arqIn = tk.StringVar()
        self.arqIn.set(self.control.fileNameData)

        label = tk.Label(self, text="Arquivo de entrada:", justify=tk.RIGHT,
                anchor=tk.E)
        entry = tk.Entry(self, textvariable=self.arqIn, state='readonly')
        button = tk.Button(self, text='Abrir', command=self.do_btArqIn)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Lista de atributos de Identificação
        self.idAttrList = tk.StringVar()
        self.idAttrList.set(str(self.control.idAttrs))

        label = tk.Label(self, text="Atributos de Identificação:",
                justify=tk.RIGHT, anchor=tk.E)
        entry = tk.Entry(self, textvariable=self.idAttrList, state='readonly')
        button = tk.Button(self, text='Selecionar', command=self.do_btIds)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Lista de atributos de Identificação
        self.valAttrList = tk.StringVar()
        self.valAttrList.set(str(self.control.valueAttrs))

        label = tk.Label(self, text="Atributos de valor:", justify=tk.RIGHT,
                anchor=tk.E)
        entry = tk.Entry(self, textvariable=self.valAttrList, state='readonly')
        button = tk.Button(self, text='Selecionar', command=self.do_btValues)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Configurações do SOM
        button = tk.Button(self, text='Configuração do SOM...',
            command=self.do_btConfSOM)

        row = self._gridButton(button, row)

        # Arquivo de saida do SOM
        self.arqOutSOM = tk.StringVar()
        self.arqOutSOM.set(self.control.fileNameSOM)

        label = tk.Label(self, text="Arquivo de saída para o SOM:",
                justify=tk.RIGHT, anchor=tk.E)
        entry = tk.Entry(self, textvariable=self.arqOutSOM, state='readonly')
        button = tk.Button(self, text='Selecionar', command=self.do_btArqOutSOM)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Arquivo de saida para as associaçoes de cluster
        self.arqOutClusAssoc = tk.StringVar()
        self.arqOutClusAssoc.set(self.control.fileNameClusAssoc)

        label = tk.Label(self, text="Arquivo de saída para a " +
                "classificação dos elementos:", justify=tk.RIGHT, anchor=tk.E)
        entry = tk.Entry(self, textvariable=self.arqOutClusAssoc, state='readonly')
        button = tk.Button(self, text='Selecionar',
            command=self.do_btArqOutClussAssoc)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Botão de executar o processamento
        button = tk.Button(self, text='Gerar e salvar SOM',
            command=self.do_btGerarSOM)

        row = self._gridButton(button, row)

        self.columnconfigure(1, weight=1)

    def _gridLabelEntryButton(self, label, entry, button, row):
        """Put label, entry and button widgets in frame's grid. The
        specified row is used as base row.

        Return the next available row in the grid.
        """
        label['text'] = textwrap.fill(label['text'], 20)
        label.grid(row=row, column=0, sticky=tk.EW)
        entry.grid(row=row, column=1, sticky=tk.EW) 
        button.grid(row=row, column=2, sticky=tk.EW) 
        return row + 1

    def _gridButton(self, button, row):
        """Put button in frame's grid. The specified row is used as base row.

        Return the next available row in the grid.
        """
        button.grid(row=row, column=1, sticky=tk.EW) 
        return row + 1

    def do_btConfSOM(self):
        confDialog = SOMConfDialog(self, self.control.SOMConf)

    def do_btValues(self):
        attrSel = gui.ListSelecManyDialog(self, title="Seleção de atributos",
                text="Selecione os atributos que possuem os dados a serem processados.",
                items=self.control.attrNames, selected=self.control.valueAttrs)

        if attrSel.result is not None:
            attrs = [ x for n, x in attrSel.result ]
            self.control.setValueAttrs(attrs)
            self.valAttrList.set(str(self.control.valueAttrs))

    def do_btIds(self):
        attrSel = gui.ListSelecManyDialog(self, title="Seleção de atributos",
                text="Selecione os atributos que identificam as amostras.",
                items=self.control.attrNames, selected=self.control.idAttrs)

        if attrSel.result is not None:
            attrs = [ x for n, x in attrSel.result ]
            self.control.setIdAttrs(attrs)
            self.idAttrList.set(str(self.control.idAttrs))

    def do_btArqIn(self):
        fileName = filedialog.askopenfilename(filetypes=[('CSV','*.csv')])
        if fileName != '':
            self.control.openDataFile(fileName)
            self.arqIn.set(self.control.fileNameData)
            self.idAttrList.set(str(self.control.idAttrs))
            self.valAttrList.set(str(self.control.valueAttrs))

    def do_btArqOutSOM(self):
        fileName = filedialog.asksaveasfilename(
            title='Arquivo para salvar o SOM',
            filetypes=[('graphml','*.graphml')], defaultextension='.graphml')
        self.control.fileNameSOM = fileName
        self.arqOutSOM.set(fileName)

    def do_btArqOutClussAssoc(self):
        fileName = filedialog.asksaveasfilename(
            title='Arquivo para salvar a atribuição de classes',
            filetypes=[('CSV','*.csv')], defaultextension='.csv')
        self.control.fileNameClusAssoc = fileName
        self.arqOutClusAssoc.set(fileName)

    def do_btGerarSOM(self):
        if messagebox.askokcancel('Confirmar execução',
                'O programa irá realizar o treinamento do SOM.\n'+
                'Isto pode levar algum tempo.\n\n' +
                'Deseja continuar ?'):

            execDial = gui.ExecutionDialog(self, command=self.control.processData,
                title='Executando...')


class SOMConfDialog(Dialog):
    def __init__(self, master, SOM_CONFIG):

        self.SOM_CONFIG = SOM_CONFIG

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
        self.SOM_CONFIG['Tipo'] = self.Tipo.get()
        self.SOM_CONFIG['FVU'] = self.FVU.get()
        self.SOM_CONFIG['maxNodes'] = self.maxNodes.get()
        self.SOM_CONFIG['neighWeightTrain'] = self.neighWeightTrain.get()
        self.SOM_CONFIG['neighWeightRefine'] = self.neighWeightRefine.get()
        self.SOM_CONFIG['maxStepsPerGeneration'] = self.maxStepsPerGeneration.get()
        self.SOM_CONFIG['MSTPeriod'] = self.MSTPeriod.get()
        self.SOM_CONFIG['nrows'] = self.nrows.get()
        self.SOM_CONFIG['ncols'] = self.ncols.get()

#---------------------------------------------------------------------
# Execução do script
#---------------------------------------------------------------------
if __name__ == '__main__':
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger()
    app = tk.Tk()
    app.title('Self Organizing Map')
    confGui = ConfigGUI(app, logger)
    confGui.pack(expand=True, fill='both')
    app.mainloop()
