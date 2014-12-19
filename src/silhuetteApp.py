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

import silhouette as silhou

#---------------------------------------------------------------------
# Variaveis globais de configuração
#---------------------------------------------------------------------

# Configurações para controlar a geração de log pelo script
ARQ_LOG = 'silhuette.log'
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
class AppControl(object):
    """Classe que controla o caso de uso do aplicativo.

    Atributos: 

    - fileNameData: Nome do arquivo CSV com os dados a serem processados.

    - idAttrs: Lista com os nomes dos atributos que identificam os elementos.

    - valueAttrs: Lista com os nomes dos atributos de valor dos elementos.

    - clusterAttr: Nome do atributo que determina o cluster

    - fileNameElemSilh: Nome do arquivo CSV em que as silhuetas de cada elemento
      serão salvas.

    - fileNameRelat: Nome do arquivo TXT onde serão salvas a silhueta total e as
      silhuetas de cada cluster.

    - attrNames: Lista com os nomes de todos os atributos dispoíveis em no
      arquivo 'fileNameData'. É preenchida automaticamente quando 'fileNameData'
      for configurado.
    """

    def __init__(self, logger):
        """
        Args:

        - logger: Objeto usado para gerar mensagens de log
        """
        self.logger = logger

        self.fileNameElemSilh = ''
        self.fileNameRelat = ''
        self.clearDataFile()

    def clearDataFile(self):
        self.fileNameData = ''
        self.attrNames = []
        self.idAttrs = []
        self.valueAttrs = []
        self.clusterAttr = ''
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

    def setClusterAttr(self, attr):
        if attr in self.attrNames:
            self.clusterAttr = attr

    def _carregaDados(self):
        self.logger.info('Carregando {}...'.format(self.fileNameData))
        with open(self.fileNameData, newline='') as f:
            csvReader = csv.reader(f, self.csvDialect)

            elements = {}
            elemClusters = {}
            idCols = set()
            valueCols = set()
            clusterCol = -1

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
                        elif c == self.clusterAttr:
                            clusterCol = n
                else:
                    idList = [elemNum]
                    vet = []
                    cluster = 'None'
                    for n, v in enumerate(campos):
                        if n in idCols:
                            idList.append(v)
                        elif n in valueCols:
                            vet.append(float(v))
                        elif n == clusterCol:
                            cluster = v
                    elements[tuple(idList)] = vet
                    elemClusters[tuple(idList)] = cluster

                elemNum += 1
        self.logger.info('...ok')

        return elements, elemClusters

    def _writeClassificationCSV(self, elemClusters, elemSilh, neighboor):

        if self.fileNameElemSilh is None or self.fileNameElemSilh == '':
            return

        self.logger.info('Salvando {0}...'.format(self.fileNameElemSilh))
        with open(self.fileNameElemSilh, 'w', newline='') as f:
            csvWriter = csv.writer(f, self.csvDialect)
            csvWriter.writerow(['#'] + self.idAttrs +
                    ['silhouette', self.clusterAttr,
                        self.clusterAttr+'_vizinho'])
            for ids in sorted(elemClusters.keys()):
                row = list(ids) + [
                    elemSilh[ids], elemClusters[ids], neighboor[ids]
                    ]
                csvWriter.writerow(row)

        self.logger.info('...ok')

    def _writeClusterReport(self, totalSilh, clusSilh):
        if self.fileNameRelat is not None and self.fileNameRelat != '':
            self.logger.info('Salvando {0}...'.format(self.fileNameRelat))
            with open(self.fileNameRelat, 'w') as f:
                f.write('Total silhuette: {0}\n'.format(totalSilh))
                f.write('Clusters silhuettes:\n')
                for clIds in sorted(clusSilh.keys()):
                    f.write('  {0}: {1}\n'.format(clIds, clusSilh[clIds]))
            self.logger.info('...ok')

    def _calcSilhuettes(self, elements, elemClusters):
        self.logger.info('Calculando silhuetas...')
        retTuple = silhou.evaluateClusters2(elements, elemClusters)
        self.logger.info('...ok')
        return retTuple

    def processData(self):
        """Função principal do script, executada no final do arquivo.
        """
        elements, elemClusters = self._carregaDados()

        elemSilh, clusSilh, totalSilh, neighClust = self._calcSilhuettes(
                elements, elemClusters)

        self._writeClassificationCSV(elemClusters, elemSilh, neighClust)

        self._writeClusterReport(totalSilh, clusSilh) 


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

        self.master = master

        self.logger = logger
        self.control = AppControl(logger)

        row = 0

        # Arquivo de entrada
        self.arqIn = tk.StringVar()
        self.arqIn.set(self.control.fileNameData)

        label = tk.Label(self, text="Arquivo de entrada:", anchor=tk.CENTER)
        entry = tk.Entry(self, textvariable=self.arqIn, state='readonly')
        button = tk.Button(self, text='Abrir', command=self.do_btArqIn)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Lista de atributos de Identificação
        self.idAttrList = tk.StringVar()
        self.idAttrList.set(str(self.control.idAttrs))

        label = tk.Label(self, text="Atributos de Identificação:", anchor=tk.CENTER)
        entry = tk.Entry(self, textvariable=self.idAttrList, state='readonly')
        self.btIds = tk.Button(self, text='Selecionar', command=self.do_btIds)

        row = self._gridLabelEntryButton(label, entry, self.btIds, row)

        # Lista de atributos de valor
        self.valAttrList = tk.StringVar()
        self.valAttrList.set(str(self.control.valueAttrs))

        label = tk.Label(self, text="Atributos de valor:", anchor=tk.CENTER)
        entry = tk.Entry(self, textvariable=self.valAttrList, state='readonly')
        self.btValues = tk.Button(self, text='Selecionar',
                command=self.do_btValues)

        row = self._gridLabelEntryButton(label, entry, self.btValues, row)

        # Atributos de cluster
        self.clusterAttr = tk.StringVar()
        self.clusterAttr.set(str(self.control.clusterAttr))

        label = tk.Label(self, text="Atributo de cluster:", anchor=tk.CENTER)
        entry = tk.Entry(self, textvariable=self.clusterAttr, state='readonly')
        self.btCluster = tk.Button(self, text='Selecionar',
                command=self.do_btCluster)

        row = self._gridLabelEntryButton(label, entry, self.btCluster, row)

        # Arquivo de saida para as silhuetas de elementos
        self.arqOutElemSilh = tk.StringVar()
        self.arqOutElemSilh.set(self.control.fileNameElemSilh)

        label = tk.Label(self,
                text="Arquivo de saída para silhuetas de elementos:", anchor=tk.CENTER)
        entry = tk.Entry(self, textvariable=self.arqOutElemSilh, state='readonly')
        button = tk.Button(self, text='Selecionar', command=self.do_btArqOutElemSilh)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Arquivo de saida para as silhuetas de cluster e total
        self.arqOutClusSilh = tk.StringVar()
        self.arqOutClusSilh.set(self.control.fileNameRelat)

        label = tk.Label(self, text="Arquivo de saída para silhuetas de clusters:", anchor=tk.CENTER)
        entry = tk.Entry(self, textvariable=self.arqOutClusSilh, state='readonly')
        button = tk.Button(self, text='Selecionar',
            command=self.do_btArqOutClusSilh)

        row = self._gridLabelEntryButton(label, entry, button, row)

        # Botão de executar o processamento
        self.btGerarSilh = tk.Button(self, text='Gerar e salvar silhuetas',
            command=self.do_btGerarSilh)
        self.btGerarSilh.grid(row=row, column=0)

        row = self._gridButton(self.btGerarSilh, row)

        self.columnconfigure(0, weight=1)

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

    def do_btCluster(self):
        attrSel = gui.ListSelectionDialog(self, title="Seleção de atributo",
                text="Selecione o atributo que identifica os clusters.",
                items=self.control.attrNames, selected=self.control.clusterAttr)

        if attrSel.result is not None:
            for attrTuple in attrSel.result:
                attr = attrTuple[1]
                self.control.setClusterAttr(attr)
                self.clusterAttr.set(str(self.control.clusterAttr))

    def do_btArqIn(self):
        fileName = filedialog.askopenfilename(filetypes=[('CSV','*.csv')])
        if fileName != '':
            self.control.openDataFile(fileName)
            self.arqIn.set(self.control.fileNameData)
            self.idAttrList.set(str(self.control.idAttrs))
            self.valAttrList.set(str(self.control.valueAttrs))

    def do_btArqOutElemSilh(self):
        fileName = filedialog.asksaveasfilename(
            title='Arquivo para salvar silhuetas de elementos',
            filetypes=[('CSV','*.csv')], defaultextension='.csv')
        self.control.fileNameElemSilh = fileName
        self.arqOutElemSilh.set(fileName)

    def do_btArqOutClusSilh(self):
        fileName = filedialog.asksaveasfilename(
            title='Arquivo para salvar silhuetas de clusters',
            filetypes=[('TXT','*.txt')], defaultextension='.txt')
        self.control.fileNameRelat = fileName
        self.arqOutClusSilh.set(fileName)

    def do_btGerarSilh(self):
        if messagebox.askokcancel('Confirmar execução',
                'O programa irá realizar dos índices de silhueta.\n'+
                'Isto pode levar algum tempo.\n\n' +
                'Deseja continuar ?'):

            execDial = gui.ExecutionDialog(self, command=self.control.processData,
                title='Executando...')


#---------------------------------------------------------------------
# Execução do script
#---------------------------------------------------------------------
if __name__ == '__main__':
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger()
    app = tk.Tk()
    confGui = ConfigGUI(app, logger)
    confGui.pack(expand=True, fill='both')
    app.mainloop()
