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
ARQ_IN = os.path.join(DIR_INPUT,'teste.csv')

# Configuracao de que colunas do arquivo csv que serao utilizadas
# Nome das colunas de identificacao
ID_ATTRS = ['um']
# Nome das colunas de valores
VALUE_ATTRS = ['dois','tres','quatro']
CLASS_ATTRS = []

# Configuraçoes do formato do arquivo CSV
CSV_OPTIONS = {
    'delimiter': ','
}

# Variáveis que controlam onde os dados de saida do script serão salvos
DIR_OUTPUT = '.'
ARQ_RELAT = os.path.join(DIR_OUTPUT,'relatorio.txt')
ARQ_CLASSES_CLUSTERS = os.path.join(DIR_OUTPUT, 'classesCLUSTERS.csv')

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
# Função principal do script
#---------------------------------------------------------------------
def main(log):
    """Função principal do script, executada no final do arquivo.
    """
    log.info('Carregando {}...'.format(ARQ_IN))
    elements, elemClass = carregaArquivo(ARQ_IN, idAttrs=ID_ATTRS,
            valueAttrs=VALUE_ATTRS, classAttrs=CLASS_ATTRS)

    log.info('Calculando silhouette indices...')
    elemSilh, clusSilh, totalSilh, neighClust = silhou.evaluateClusters2(
            elements, elemClass)
    log.info('...ok')

    writeClassificationCSV(elemClass, elemSilh, neighClust)

    if ARQ_RELAT is not None and ARQ_RELAT != '':
        with open(ARQ_RELAT, 'w') as f:
            f.write('Total silhuette: {0}\n'.format(totalSilh))
            f.write('Clusters silhuettes:\n')
            for clIds in sorted(clusSilh.keys()):
                f.write('  {0}: {1}\n'.format(clIds, clusSilh[clIds]))

#---------------------------------------------------------------------
# Definição das funções auxiliares e procedimentos macro do script
#---------------------------------------------------------------------

def carregaArquivo(fileName, idAttrs=[], valueAttrs=[], classAttrs=[]):

    csvReader = csv.reader(open(fileName, newline=''), **CSV_OPTIONS)

    elements = {}
    elemClass = {}
    idCols = set()
    valueCols = set()
    classCols = set()

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
                elif c in classAttrs:
                    classCols.add(n)

        else:
            idList = [elemNum]
            vet = []
            cluster = []
            for n, v in enumerate(campos):
                if n in idCols:
                    idList.append(v)
                elif n in valueCols:
                    vet.append(float(v))
                elif n in classCols:
                    cluster.append(v)

            elements[tuple(idList)] = vet
            elemClass[tuple(idList)] = tuple(cluster)

        elemNum += 1

    return elements, elemClass


def writeClassificationCSV(classes, elemSilh, neighboor):

    if ARQ_CLASSES_CLUSTERS is None or ARQ_CLASSES_CLUSTERS == '':
        return

    with open(ARQ_CLASSES_CLUSTERS, 'w', newline='') as f:
        csvWriter = csv.writer(f, **CSV_OPTIONS)
        csvWriter.writerow(['#'] + ID_ATTRS + CLASS_ATTRS +
                ['silhouette'] + [str(x)+'_vizinho' for x in CLASS_ATTRS])
        for ids in sorted(classes.keys()):
            row = list(ids) + list(classes[ids]) + [elemSilh[ids]] + list(neighboor[ids])
            csvWriter.writerow(row)


#---------------------------------------------------------------------
# GUI
#---------------------------------------------------------------------
from tkinter.simpledialog import Dialog
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import gui
from queue import Queue, Empty
import threading

class ConfigGUI(tk.Frame):
    def __init__(self, master, logger, **options):
        global ARQ_IN

        ARQ_IN = ''

        super().__init__(master, **options)

        self.executar = False
        self.master = master

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

        self.btClasses = tk.Button(self, text='4: Selecionar atributos de classe',
            command=self.doBtClasses)
        self.btClasses.grid(row=4, column=0, sticky=tk.EW)

        self.btComputarSilh = tk.Button(self, text='5: Computar indices de silhueta',
            command=self.doBtComputarSilh)
        self.btComputarSilh.grid(row=5, column=0, sticky=tk.EW)

    def doBtComputarSilh(self):
        global ARQ_CLASSES_CLUSTERS
        global ARQ_RELAT

        ARQ_CLASSES_CLUSTERS = filedialog.asksaveasfilename(
            title='Arquivo para salvar elementos',
            filetypes=[('CSV','*.csv')], defaultextension='.csv')

        ARQ_RELAT = filedialog.asksaveasfilename(
            title='Arquivo para salvar clusters',
            filetypes=[('TXT','*.txt')], defaultextension='.txt')

        if ARQ_CLASSES_CLUSTERS != '':
            self.executar = True
            execDial = ExecutionDialog(self, self.logger)

            if execDial.result:
                messagebox.showinfo('Info', 'Geração concluída')
            else:
                messagebox.showerror('Error',
                    'Ocorreu um erro durante a geração.')


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

    def doBtClasses(self):
        global CLASS_ATTRS

        attrSel = gui.ListSelecManyDialog(self, title="Seleção de atributos",
                text="Selecione os atributos que identificam as classes.",
                items=self.headers)

        if attrSel.result is not None:
            CLASS_ATTRS = [ x for n, x in attrSel.result ]

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

class ExecutionDialog(Dialog):
    def __init__(self, master, logger):

        self.logger = logger
        self.queue = Queue()
        self.master = master

        t = threading.Thread(target=self.execThread)
        t.start()
        master.after(1000, self.periodicPool)

        self.result = False

        super().__init__(master,title='TESTE')

    def execThread(self):
        try:
            main(self.logger)
            self.queue.put(('END',))
        except Exception as ex:
            self.queue.put(('ERROR',))
            raise ex

    def periodicPool(self):
        msg = None
        cont = True
        try:
            msg = self.queue.get(False)
        except Empty:
            pass

        if msg is not None:
            cont = False
            if msg[0] == 'END':
                self.result = True
            elif msg[0] == 'ERROR':
                self.result = False

        if cont:
            self.master.after(1000, self.periodicPool)
        else:
            self.ok()

    def body(self, master):
        p = ttk.Progressbar(master, orient=tk.HORIZONTAL, mode='indeterminate')
        p.pack()
        p.start()
        master.pack()

    def buttonbox(self):
        pass

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
