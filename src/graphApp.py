#!/usr/bin/python3
# coding: utf-8

import os.path
import sys
import logging
import logging.config
import traceback
import math

# Acrescentando o diretorio lib ao path. Lembrando que sys.path[0] representa o
# diretório onde este script se encontra
sys.path.append(os.path.join(sys.path[0],'lib'))

#---------------------------------------------------------------------
# Variaveis globais de configuração
#---------------------------------------------------------------------

# Configurações para controlar a geração de log pelo script
ARQ_LOG = 'graphApp.log'
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
# Classes de controle
#---------------------------------------------------------------------
import graph as gr
import csv

class GraphModel(object):
    def __init__(self, graphObj, name, filename=None):
        self.graph = graphObj
        self.name = name
        self.filename = filename

    def createGraphmlFilename(self):
        if self.filename:
            path, _ = os.path.splitext(self.filename)
            return path + '.graphml'
        else:
            return self.name + '.graphml'

class GraphAppControl(object):

    def __init__(self, logger):
        self.logger = logger
        self.csvDialect = csv.excel()
        self.graphModels = {}
        self.insertHandlers = []
        self.deleteHandlers = []
        self.changeHandlers = []

    def addInsertHandler(self, handler):
        """Insert handlers that will be called whenever a graph is inserted in
        the collection.

        Args:
            - handler: A callable that will be called with the inserted
              graphModel as its argument - handler(graphModel)
        """
        if handler not in self.insertHandlers:
            self.insertHandlers.append(handler)

    def _callInsertHandlers(self, graphModel):
        for handler in self.insertHandlers:
            try:
                handler(graphModel)
            except Exception as ex:
                self.logger.warning(str(ex))
                exStr = traceback.format_exc()
                self.logger.debug(exStr)

    def addDeleteHandler(self, handler):
        """Insert handlers that will be called whenever a graph is deleted from
        the collection.

        Args:
            - handler: A callable that will be called with the deleted
              graphModel as its argument - handler(graphModel)
        """
        if handler not in self.deleteHandlers:
            self.deleteHandlers.append(handler)

    def _callDeleteHandlers(self, graphModel):
        for handler in self.deleteHandlers:
            try:
                handler(graphModel)
            except Exception as ex:
                self.logger.warning(str(ex))
                exStr = traceback.format_exc()
                self.logger.debug(exStr)

    def addChangeHandler(self, handler):
        """Insert handlers that will be called whenever a graph is changed in
        the collection.

        Args:
            - handler: A callable that will be called with the changed
              graphModel as its argument - handler(graphModel)
        """
        if handler not in self.changeHandlers:
            self.changeHandlers.append(handler)

    def _callChangeHandlers(self, graphModel):
        for handler in self.changeHandlers:
            try:
                handler(graphModel)
            except Exception as ex:
                self.logger.warning(str(ex))
                exStr = traceback.format_exc()
                self.logger.debug(exStr)

    def generateNumericName(self):
        """Generates an available numeric name for graphs.
        Return:
            - A string with the available name
        """
        n = 1
        name = '{0:03}'.format(n)
        while name in self.graphModels:
            n += 1
            name = '{0:03}'.format(n)
        return name

    def getGraphNames(self):
        return sorted(self.graphModels.keys())

    def insertGraph(self, g, name=None, filename=None):
        if name is None or name == '':
            name = self.generateNumericName()

        if name in self.graphModels:
            raise ValueError('Já existe grafo com nome "{0}"'.format(name))

        gm = GraphModel(g, name, filename)
        self.graphModels[name] = gm
        self._callInsertHandlers(gm)

    def loadGraphml(self, filename, name=None,
            relationAttr=gr.EDGE_RELATION_ATTR):
        if name is None:
            name = self.generateNumericName()

        if name in self.graphModels:
            raise ValueError('Já existe grafo com nome "{0}"'.format(name))

        g = gr.loadGraphml(filename, relationAttr)
        self.insertGraph(g, name=name, filename=filename)

    def inspectGraphmlAttributes(self, filename):
        """Read from a graphml the names and types of graph attributes.

        Args:
            - filename: Path of the file to inspect

        Return:
            (graphAttrSpecs, nodeAttrSpecs, edgeAttrSpecs): Tuple of
            dictionaries of graph's attributes.
        """
        # OBS: Estamos lendo o grafo inteiro do arquivo, mas poderíamos criar
        # uma função de leitura específica para ler apenas os atributos para
        # sermos mais eficientes.
        g = gr.loadGraphml(filename)

        return (g.graphAttrSpecs, g.nodeAttrSpecs, g.edgeAttrSpecs)

    def removeGraph(self, graphName):
        """Remove a graph from the collection.

        Args:
            - graphName: Name of the graph to be removed
        """
        if graphName in self.graphModels:
            gmod = self.graphModels[graphName]
            del self.graphModels[graphName]
            self._callDeleteHandlers(gmod)

    def inspectCsv(self, filename):
        with open(filename, newline='') as f:
            self.csvDialect = csv.Sniffer().sniff(f.read(5000))
            f.seek(0)

            firstRow = []

            # Le a primeira linha para recuperar os nomes dos atributos
            reader = csv.reader(f, self.csvDialect)
            for row in reader:
                firstRow = row
                break

            return firstRow

    def loadCsvGraphEdges(self, filename, srcNodeCol, tgtNodeCol,
            name=None, relationCol=None, weightCol=None,
            firstRowIsHeading=False):

        g = gr.MultiGraph()

        relationAttr = 'Relation'
        weightAttr = 'EdgeCount'

        with open(filename, newline='') as f:
            reader = csv.reader(f, self.csvDialect)

            if firstRowIsHeading:
                for row in reader:
                    if relationCol is not None:
                        relationAttr = row[relationCol].strip()
                    if weightCol is not None:
                        weightAttr = row[weightCol].strip()
                    break

            spec = gr.AttrSpec(weightAttr, 'float', 1.0)
            g.addEdgeAttrSpec(spec)
            spec = gr.AttrSpec(relationAttr, 'string')
            g.addEdgeAttrSpec(spec)

            for row in reader:
                src = row[srcNodeCol].strip()
                tgt = row[tgtNodeCol].strip()
                rel = 0
                weigth = 1.0
                if relationCol is not None:
                    rel = row[relationCol].strip()
                if weightCol is not None:
                    weigth = float(row[weightCol])

                if g.hasEdge(src, tgt, rel):
                    oldWeight = g.getEdgeAttr((src, tgt, rel), weightAttr)
                    weigth += oldWeight
                    g.setEdgeAttr((src,tgt,rel), weightAttr, weigth)
                else:
                    g.addEdge(src, tgt, rel)
                    g.setEdgeAttr((src,tgt,rel), weightAttr, weigth)
                    g.setEdgeAttr((src,tgt,rel), relationAttr, rel)
            # end for
        #end with

        self.insertGraph(g, name, filename)

    def saveGraphml(self, name, filename=None):
        gmod = self.graphModels[name]

        if not filename:
            filename = gmod.createGraphmlFilename()

        gmod.graph.writeGraphml(filename)

        gmod.filename = filename

        self._callChangeHandlers(gmod)

    def newEmptyGraph(self, name):
        g = gr.MultiGraph()
        self.insertGraph(g, name)

    def readIdsAndAttrsFromCsv(filename, idCols,
            attrCols, attrSpecs,
            firstRowIsHeading):

        if len(idCols) > 1:
            def extractId(row, num):
                ids = []
                for c in idCols:
                    ids.append(row[c])
                return tuple(ids)

        elif len(idCols) == 1:
            def extractId(row, num):
                return row[idCols[0]]
        else:
            def extractId(row, num):
                return num

        with open(filename, newline='') as f:
            reader = csv.reader(f, self.csvDialect)

            attrDicts = {}
            for spec in attrSpecs:
                attrDicts[spec.name] = {}

            if firstRowIsHeading:
                for row in reader:
                    break

            itemNum = 1
            for row in reader:
                ids = extractId(row, itemNum)
                for i, spec in attrSpecs:
                    value = row[attrCols[i]]
                    value = spec.strToType(value)
                    attrDicts[spec.name][ids] = value
                itemNum += 1

        return attrDicts

    def importNodeAttrsFromCsv(graphName, filename, nodeCol,
            attrCols, attrSpecs,
            firstRowIsHeading):

        if graphName not in self.graphModels.keys():
            raise ValueError(
                "Grafo '{0}' não existe".format(graphName))

        gmod = self.graphModels[graphName]

        attrNames = gmod.graph.getNodeAttrNames()
        for spec in attrSpecs:
            if spec.name in attrNames:
                raise ValueError(
                    "Já existe atributo de nodo com nome '{0}'".format(spec.name))

        idCols = [nodeCol]
        attrDicts = readIdsAndAttrsFromCsv(filename, idCols, attrCols,
            attrSpecs, firstRowIsHeading)

        gr.addAttributeSetsToGraph(gmod.graph,
            attrNodes=attrDicts, specNodes=attrSpecs)

        self._callChangeHandlers(gmod)

    def importEdgeAttrsFromCsv(graphName, filename,
            srcCol, tgtCol, relCol,
            attrCols, attrSpecs,
            firstRowIsHeading):

        if graphName not in self.graphModels.keys():
            raise ValueError(
                "Grafo '{0}' não existe".format(graphName))

        gmod = self.graphModels[graphName]

        attrNames = gmod.graph.getEdgeAttrNames()
        for spec in attrSpecs:
            if spec.name in attrNames:
                raise ValueError(
                    "Já existe atributo de aresta com nome '{0}'".format(spec.name))

        idCols = [srcCol, tgtCol, relCol]
        attrDicts = readIdsAndAttrsFromCsv(filename, idCols, attrCols,
            attrSpecs, firstRowIsHeading)

        gr.addAttributeSetsToGraph(gmod.graph,
            attrEdges=attrDicts, specEdges=attrSpecs)

        self._callChangeHandlers(gmod)

    def validateNewAttrs(self, graphId, attrSpecs, attrScope):
        """Verify if the specs are valid as new attributes for the given graph.

        Args:
            - graphId: Graph name or graph model
            - attrSpecs: Sequence of AttrSpec
            - attrScope: 'graph', 'node' or 'edge'

        Return:
            - (True, '')
            - (False, errMsg)
        """
        if isinstance(graphId, str):
            gmod = self.graphModels[graphId]
        else:
            gmod = graphId

        if attrScope == 'graph':
            attrNames = gmod.graph.getGraphAttrNames()
        elif attrScope == 'node':
            attrNames = gmod.graph.getNodeAttrNames()
        elif attrScope == 'edge':
            attrNames = gmod.graph.getEdgeAttrNames()
        else:
            raise ValueError("Invalid attrScope: '{0}'".format(
                attrScope))

        specNames = set()
        repeatedNames = set()
        for spec in attrSpecs:
            if spec.name in specNames:
                repeatedNames.add(spec.name)
            else:
                specNames.add(spec.name)

        if '' in specNames:
            return (False, 'Não é permitido nome de atributo vazio.')

        if len(repeatedNames) > 0:
            errMsg = 'Os seguintes nomes de atributos estão repetidos:'
            ir = iter(repeatedNames)
            for name in ir:
                errMsg += ' '+name
                break
            for name in ir:
                errMsg += ', '+name
            return (False, errMsg)

        if not specNames.isdisjoint(attrNames):
            errMsg = 'O grafo já possue atributos com os seguintes nomes:'
            common = specNames.intersection(attrNames)
            ic = iter(common)
            for name in ic:
                errMsg += ' ' + name
                break
            for name in ic:
                errMsg += ', ' + name
            return (False, errMsg)

        return (True,'')

#---------------------------------------------------------------------
# Classes GUI
#---------------------------------------------------------------------
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk as ttk
from tkinter.simpledialog import Dialog
import gui
import textwrap

class GraphAppGUI(tk.Frame):
    def __init__(self, master, control, logger, **options):
        super().__init__(master, **options)

        self.control = control
        self.graphToIid = {}
        self.iidToGraph = {}

        graphTree = ttk.Treeview(self,
            columns=('value', 'itemType'),
            displaycolumns=('value'),
            selectmode='browse',
            show='tree headings')

        scrollbarX = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=graphTree.xview)
        graphTree['xscrollcommand'] = scrollbarX.set
        scrollbarY = ttk.Scrollbar(self, orient=tk.VERTICAL, command=graphTree.yview)
        graphTree['yscrollcommand'] = scrollbarY.set

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        graphTree.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbarX.grid(row=1, column=0, sticky=tk.EW)
        scrollbarY.grid(row=0, column=1, sticky=tk.NS)

        sizegrip = ttk.Sizegrip(self)
        sizegrip.grid(row=1, column=1, sticky=tk.NSEW)

        self.graphTree = graphTree

        self._createMenu()

        control.addInsertHandler(self.updateGraphView)
        control.addChangeHandler(self.updateGraphView)
        control.addDeleteHandler(self.removeGraphView)

    def getGraphAndTreeIid(self, graphId):
        """Retrieve the graph's Treeview iid and it's GraphModel if they exist.

        Args:
            - graphId: Identifies the graph to be removed. It can a string
              representing the graph's Treeview iid or the graph's GraphModel.

        Return:
            (iid, graphModel)
                - iid: The Treview iid of the graph or None
                - graphModel: The graph's GraphModel or None
        """

        iid = None
        gmod = None
        if graphId in self.graphToIid:
            iid = self.graphToIid[graphId]
            gmod = graphId
        elif graphId in self.iidToGraph:
            iid = graphId
            gmod = self.iidToGraph[graphId]

        return (iid, gmod)

    def removeGraphView(self, graphId):
        """Remove a graph from the view.

        Args:
            - graphId: Identifies the graph to be removed. It can a string
              representing the graph's Treeview iid or the graph's GraphModel.

        Return:
            - The removed graphModel or None
        """

        iid, gmod = self.getGraphAndTreeIid(graphId)

        if iid is not None:
            self.graphTree.delete(iid)
            del self.graphToIid[gmod]
            del self.iidToGraph[iid]

        return gmod

    def updateGraphView(self, graphModel):
        """Inserts or updates a graph in the view.
        """
        pos = 'end'
        iid, _ = self.getGraphAndTreeIid(graphModel)

        # Removing the graph
        if iid is not None:
            pos = self.graphTree.index(iid)
            self.removeGraphView(iid)

        # (Re)inserting the graph
        filename = graphModel.filename or ''
        iid = self.graphTree.insert('', pos,
            text=graphModel.name,
            values=(filename, 'graph'))

        self.iidToGraph[iid] = graphModel
        self.graphToIid[graphModel] = iid

        secId = self.graphTree.insert(iid, 'end',
            text='Num. nodos:',
            values=(graphModel.graph.getNumNodes(), 'stats'))
        secId = self.graphTree.insert(iid, 'end',
            text='Num. arestas:',
            values=(graphModel.graph.getNumEdges(), 'stats'))

        relations = graphModel.graph.relations
        secId = self.graphTree.insert(iid, 'end',
            text='Tipos de arestas',
            values=(len(relations), 'relations'))
        for rel in relations:
            self.graphTree.insert(secId, 'end',
                text=rel,
                values=('', 'relation'))

        attrNames = graphModel.graph.getGraphAttrNames()
        secId = self.graphTree.insert(iid, 'end',
            text='Atributos de grafo',
            values=(len(attrNames), 'attrs'))
        for attr in sorted(attrNames):
            attrId = self.graphTree.insert(secId, 'end',
                text=attr,
                values=(graphModel.graph.getGraphAttr(attr), 'graphAttr'))
            spec = graphModel.graph.getGraphAttrSpec(attr)
            if spec is not None:
                self.graphTree.insert(attrId, 'end',
                    text='Tipo:',
                    values=(spec.type, 'attrType'))

        attrNames = graphModel.graph.getNodeAttrNames()
        secId = self.graphTree.insert(iid, 'end',
            text='Atributos de nodo',
            values=(len(attrNames), 'attrs'))
        for attr in sorted(attrNames):
            attrId = self.graphTree.insert(secId, 'end',
                text=attr,
                values=('', 'nodeAttr'))
            spec = graphModel.graph.getNodeAttrSpec(attr)
            if spec is not None:
                self.graphTree.item(attrId, values=(spec.type, 'nodeAttr'))
                if spec.default is not None:
                    self.graphTree.insert(attrId, 'end',
                        text='Default:',
                        values=(spec.default, 'attrDefault'))

        attrNames = graphModel.graph.getEdgeAttrNames()
        secId = self.graphTree.insert(iid, 'end',
            text='Atributos de aresta',
            values=(len(attrNames), 'attrs'))
        for attr in sorted(attrNames):
            attrId = self.graphTree.insert(secId, 'end',
                text=attr,
                values=('', 'edgeAttr'))
            spec = graphModel.graph.getEdgeAttrSpec(attr)
            if spec is not None:
                self.graphTree.item(attrId, values=(spec.type, 'nodeAttr'))
                if spec.default is not None:
                    self.graphTree.insert(attrId, 'end',
                        text='Default:',
                        values=(spec.default, 'attrDefault'))

    def getSelectedGraphIid(self):
        sel = self.graphTree.selection()

        iid = None
        if len(sel) > 0:
            iid = sel[0]
            while self.graphTree.parent(iid) != '':
                iid = self.graphTree.parent(iid)

        return iid

    def getSelectedGraph(self):
        iid = self.getSelectedGraphIid()
        if iid is not None:
            return self.iidToGraph[iid]
        else:
            return None

    def _createMenu(self):
        top = self.winfo_toplevel()
        self.menuBar = tk.Menu(top)
        top['menu'] = self.menuBar

        m = tk.Menu(self.menuBar)
        self.menuBar.add_cascade(label='Arquivo', menu=m)
        m.add_command(label='Abrir graphml...', command=self.menuCmdOpenGraphml)
        m.add_command(label='Abrir CSV...', command=self.menuCmdOpenCsvEdges)
        m.add_command(label='Salvar graphml...', command=self.menuCmdSaveGraphml)
        m.add_separator()
        m.add_command(label='Sair', command=self.menuCmdQuit)

        m = tk.Menu(self.menuBar)
        self.menuBar.add_cascade(label='Grafo', menu=m)
        m.add_command(label='Novo...', command=self.menuCmdNewGraph)
        m.add_command(label='Remover...', command=self.menuCmdRemoveGraph)
        m.add_separator()
        m.add_command(label='#Adicionar atributo...',
            command=self.menuCmdNotImplemented)
        m.add_command(label='#Remover atributo...',
            command=self.menuCmdNotImplemented)
        m.add_separator()
        m.add_command(label='#Morfismo cheio...',
            command=self.menuCmdNotImplemented)

        m = tk.Menu(self.menuBar)
        self.menuBar.add_cascade(label='Nodos', menu=m)
        m.add_command(label='#Importar atributos de csv...',
            command=self.menuCmdImportNodeAttr)
        m.add_command(label='#Exportar atributos para csv...',
            command=self.menuCmdNotImplemented)
        m.add_command(label='#Remover atributos...',
            command=self.menuCmdNotImplemented)
        m.add_separator()
        m.add_command(label='#Remover nodos...',
            command=self.menuCmdNotImplemented)
        m.add_separator()
        m.add_command(label='#Classificar por equivalência regular...',
            command=self.menuCmdNotImplemented)

        m = tk.Menu(self.menuBar)
        self.menuBar.add_cascade(label='Arestas', menu=m)
        m.add_command(label='#Importar atributos de csv...',
            command=self.menuCmdImportEdgeAttr)
        m.add_command(label='#Exportar atributos para csv...',
            command=self.menuCmdNotImplemented)
        m.add_command(label='#Remover atributos...',
            command=self.menuCmdNotImplemented)
        m.add_separator()
        m.add_command(label='#Remover arestas...',
            command=self.menuCmdNotImplemented)

    def menuCmdNotImplemented(self):
        d = AttributeConfigDialog(self, numAttrs=7, attrScope='edge',
            control=self.control, graphName=list(self.graphToIid.keys())[0])
        tk.messagebox.showinfo('Não implementado',
            'Funcionalidade ainda não implementada')

    def _cmdImportAttr(self, attrScope):
        gsel = self.getSelectedGraph()
        if gsel is not None:
            gsel = gsel.name
        d = ImportAttributesDialog(self, self.control, attrScope, gsel)

    def menuCmdImportEdgeAttr(self):
        self._cmdImportAttr('edge')

    def menuCmdImportNodeAttr(self):
        self._cmdImportAttr('node')

    def menuCmdQuit(self):
        self.quit()

    def menuCmdNewGraph(self):
        dialog = NewGraphDialog(self, self.control)

    def menuCmdOpenGraphml(self):
        dialog = OpenGraphmlDialog(self, self.control)

    def menuCmdOpenCsvEdges(self):
        dialog = OpenCsvEdgesDialog(self, self.control)

    def menuCmdRemoveGraph(self):
        items = sorted(self.control.graphModels.keys())
        selected = self.getSelectedGraph()
        if selected is not None:
            selected = selected.name
        dialog = gui.ListSelectionDialog(self, title='Remoção de grafo',
            text='Selecione o grafo a ser removido', items=items,
            selected=selected)
        if dialog.result is not None:
            for i, selection in dialog.result:
                self.control.removeGraph(selection)

    def menuCmdSaveGraphml(self):
        items = sorted(self.control.graphModels.keys())
        selected = self.getSelectedGraph()
        if selected is not None:
            selected = selected.name
        dialog = gui.ListSelectionDialog(self, title='Salvamento de grafo',
            text='Selecione o grafo a ser salvo como graphml', items=items,
            selected=selected)

        gmod = None
        if dialog.result is not None:
            for _, name in dialog.result:
                gmod = self.control.graphModels[name]
                break

        if gmod is not None:
            filename = gmod.createGraphmlFilename()
            dirpath, basename = os.path.split(filename)

            filename = tk.filedialog.asksaveasfilename(
                filetypes=[('graphml','*.graphml')],
                defaultextension='.graphml',
                initialfile=basename,
                initialdir=dirpath
                )
            if filename:
                self.control.saveGraphml(gmod.name, filename)

class AttributeConfigFrame(ttk.Frame):
    def __init__(self, master, numAttrs, **options):
        super().__init__(master, **options)

        self._numAttrs = numAttrs
        self.labels = [tk.StringVar() for i in range(numAttrs)]
        self.names = [tk.StringVar() for i in range(numAttrs)]
        self.types = [tk.StringVar() for i in range(numAttrs)]
        self.defaults = [tk.StringVar() for i in range(numAttrs)]

        self._createAttrGrid()

        # Setando os tipos para string por default
        for v in self.types:
            v.set('string')

        # Labels sequenciais por default
        for i in range(numAttrs):
            self.labels[i].set('{0:02}:'.format(i))

    def _createAttrGrid(self):
        typeNames = sorted(gr.AttrSpec.VALID_TYPES)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

        row = 0
        ws = []
        ws.append(ttk.Label(self, text=''))
        ws.append(ttk.Label(self, text='Nome'))
        ws.append(ttk.Label(self, text='Tipo'))
        #ws.append(ttk.Label(self, text='Default'))
        for col,w in enumerate(ws):
            w.grid(row=row, column=col, sticky=tk.EW)
        row += 1

        for i in range(self._numAttrs):
            ws = []
            ws.append(ttk.Label(self, textvariable=self.labels[i]))
            ws.append(ttk.Entry(self, textvariable=self.names[i]))
            ws.append(ttk.Combobox(self, textvariable=self.types[i],
                    values=typeNames, state='readonly'))
            #ws.append(ttk.Entry(self, textvariable=self.defaults[i]))
            for col,w in enumerate(ws):
                w.grid(row=row, column=col, sticky=tk.EW)
            row += 1

    def setLabels(self, labels):
        for i, v in enumerate(labels):
            self.labels[i].set(v)

    def setNames(self, names):
        for i, v in enumerate(names):
            self.names[i].set(v)

    def setTypes(self, types):
        for i, v in enumerate(types):
            self.types[i].set(v)

    def generateSpecs(self):
        specs = []
        for i in range(self._numAttrs):
            n = self.names[i].get().strip()
            t = self.types[i].get()
            #d = self.defaults[i].get().strip()
            #if d == '':
            #    d = None
            d = None
            specs.append(gr.AttrSpec(n,t,d))
        return specs

class AttributeConfigDialog(Dialog):
    def __init__(self, master, numAttrs, attrScope, control, graphName,
            labels=[], names=[], specs=[]):

        self._numAttrs = numAttrs
        self.control = control
        self.graph = graphName
        self.attrScope = attrScope
        self.labels = labels
        self.names = names
        self.attrSpecs = specs

        super().__init__(master, 'Configuração de atributos')

    def body(self, master):
        self.confFrame = AttributeConfigFrame(master, self._numAttrs)
        self.confFrame.pack(expand=True, fill='both')

        self.confFrame.setLabels(self.labels)
        self.confFrame.setNames(self.names)

        names = [s.name for s in self.attrSpecs]
        types = [s.type for s in self.attrSpecs]

        self.confFrame.setNames(names)
        self.confFrame.setTypes(types)

        master.pack(expand=True, fill='both')

    def apply(self):
        self.result = True

    def validate(self):
        attrSpecs = self.confFrame.generateSpecs()
        isOk, msg = self.control.validateNewAttrs(
                graphId=self.graph, attrSpecs=attrSpecs,
                attrScope=self.attrScope)

        if not isOk:
            tk.messagebox.showerror('Atributos inválidos', msg)
        else:
            self.attrSpecs = attrSpecs

        return isOk

def gridLabelAndWidgets(row, labelWidth, label, *widgets):
    col = 0
    label['text'] = textwrap.fill(label['text'], labelWidth)
    label.grid(row=row, column=col, sticky=tk.EW)
    col += 1

    for w in widgets:
        w.grid(row=row, column=col, sticky=tk.EW)
        col += 1
    return row + 1

def createOptionsCsvColumnSelection(colHeadings, hasHeadindRow=True,
        pseudoCols=[]):
    items = []

    idxWidth = max(len(colHeadings),len(pseudoCols))
    idxWidth = int(math.log10(idxWidth)) + 1
    idxFmt = '{{0: {0}}}: '.format(idxWidth)

    idxShift = len(pseudoCols)
    for i, n in enumerate(pseudoCols):
        fmt = idxFmt + '{1}'
        items.append(fmt.format(i-idxShift, n))

    if hasHeadindRow:
        for i, n in enumerate(colHeadings):
            fmt = idxFmt + '{1}'
            items.append(fmt.format(i, n))
    else:
        for i in range(len(colHeadings)):
            fmt = idxFmt + 'Coluna #{0}'
            items.append(fmt.format(i))

    return items, idxShift


class ImportAttributesDialog(Dialog):
    def __init__(self, master, control, attrScope, selectedGraph=''):

        self.control = control
        self.attrScope = attrScope

        self.graphName = tk.StringVar()
        if selectedGraph:
            self.graphName.set(selectedGraph)
        self.arqIn = tk.StringVar()
        self.hasHeadingRow = tk.BooleanVar()
        self.hasHeadingRow.set(True)
        self.colHeadings = []
        self.idCols = []
        self.attrCols = []
        self.attrColsTxt = tk.StringVar()

        self.attrSpecs = []

        super().__init__(master, 'Importação de atributos')

    def body(self, master):
        master.columnconfigure(1, weight=1)
        labelwidth = 25
        row = 0

        lb = ttk.Label(master, text='Grafo:', anchor=tk.E)
        entry = ttk.Entry(master, textvariable=self.graphName, state='readonly')
        btn = ttk.Button(master, text='Escolher...',
                command=self._doBtnChooseGraph)
        row = gridLabelAndWidgets(row, labelwidth, lb, entry, btn)

        lb = ttk.Label(master, text='Arquivo:', anchor=tk.E)
        entry = ttk.Entry(master, textvariable=self.arqIn, state='readonly')
        btn = ttk.Button(master, text='Escolher...',
                command=self._doBtnChooseFile)
        row = gridLabelAndWidgets(row, labelwidth, lb, entry, btn)

        lb = ttk.Label(master, text='A primeira linha do arquivo é cabeçalho')
        cb = ttk.Checkbutton(master, variable=self.hasHeadingRow)
        lb.grid(row=row, column=1, columnspan=2, sticky=tk.W)
        cb.grid(row=row, column=0, sticky=tk.E)
        row += 1

        if self.attrScope == 'edge':
            row = self._createIdColsGui(master, row, labelwidth,
                ['Coluna de origem da aresta:',
                    'Coluna de destino da aresta:',
                    'Coluna da relação da aresta:'])
            self.idSelectionTexts=[
                'Selecione a coluna que representa o nodo de origem da aresta.',
                'Selecione a coluna que representa o nodo de destino da aresta.',
                'Selecione a coluna que representa a relação da aresta.'
            ]
        elif self.attrScope == 'node':
            row = self._createIdColsGui(master, row, labelwidth,
                ['Coluna do nodo:'])
            self.idSelectionTexts=[
                'Selecione a coluna que representa o identificador do nodo.'
            ]

        lb = ttk.Label(master, text='Colunas de atributos:',
                justify=tk.RIGHT, anchor=tk.E)
        entry = ttk.Entry(master, textvariable=self.attrColsTxt,
                state='readonly')
        bt = ttk.Button(master, text='Escolher...', state='disabled',
                command=self._doBtnChooseAttrCols)
        row = gridLabelAndWidgets(row, labelwidth, lb, entry, bt)

        self.attrColsButton = bt

        bt = ttk.Button(master, text='Configurar atributos...',
                command=self._doBtnConfigAttrs, state='disabled')
        bt.grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        row += 1

        self.configAttrsButton = bt

        master.pack(fill='both', expand=True)

    def _createIdColsGui(self, master, row, labelwidth, texts):
        # Vetor de variaveis para armazenar os textos de cada componente do
        # identificador
        self.idColsTxtVet = []
        self.idColsButtonVet = []

        def createBtnFun(idx):
            return lambda : self._doBtnChooseId(idx)

        for i, text in enumerate(texts):
            var = tk.StringVar()
            lb = ttk.Label(master, text=text, justify=tk.RIGHT,
                    anchor=tk.E)
            entry = ttk.Entry(master, textvariable=var,
                    state='readonly')
            bt = ttk.Button(master, text='Escolher...', state=tk.DISABLED,
                    command=createBtnFun(i))
            row = gridLabelAndWidgets(row, labelwidth, lb, entry, bt)

            self.idColsTxtVet.append(var)
            self.idColsButtonVet.append(bt)

            self.idCols.append(-1)

        return row

    def _doBtnChooseGraph(self):
        graphs = self.control.getGraphNames()
        dialog = gui.ListSelectionDialog(self, title='Escolha de grafo',
            text='Escolha o grafo que receberá os atributos importados',
            items=graphs, selected=self.graphName.get())

        if dialog.result:
            for i, sel in dialog.result:
                self.graphName.set(sel)

    def _doBtnChooseFile(self):
        filename = tk.filedialog.askopenfilename(
            filetypes=[('csv','*.csv'),('txt','*.txt'),('all','*')])
        if filename:
            self.arqIn.set(filename)
            self.colHeadings = self.control.inspectCsv(filename)
            self._updateButtonStates()

    def _doBtnChooseAttrCols(self):
        items, idShift = createOptionsCsvColumnSelection(self.colHeadings,
                self.hasHeadingRow.get())

        selected = [n for i,n in enumerate(items) if i in self.attrCols]

        dialog = gui.ListSelecManyDialog(self,
            title='Seleção de colunas de atributos',
            text='Selecione as colunas que correspondem aos atributos '
                + 'que devem ser importados.',
            items=items, selected=selected)

        if dialog.result is not None:
            self.attrCols = [i for i, t in dialog.result]
            self.attrColsTxt.set(str(self.attrCols))
            self._updateButtonStates()
            self.attrSpecs = []

    def _updateButtonStates(self):
        btnState = tk.DISABLED
        if self.arqIn.get():
            btnState = tk.NORMAL

        self.attrColsButton['state'] = btnState
        for btn in self.idColsButtonVet:
            btn['state'] = btnState

        btnState = tk.DISABLED
        if len(self.attrCols) > 0 and self.graphName.get():
            btnState = tk.NORMAL

        self.configAttrsButton['state'] = btnState

    def _doBtnChooseId(self, idIdx):
        items, idxShift = createOptionsCsvColumnSelection(self.colHeadings,
                self.hasHeadingRow.get())

        selected=self.idColsTxtVet[idIdx].get()

        dialog = gui.ListSelectionDialog(self,
            title='Seleção de identificador',
            text=self.idSelectionTexts[idIdx],
            items=items, selected=selected)

        if dialog.result is not None:
            for i, v in dialog.result:
                self.idColsTxtVet[idIdx].set(v)
                self.idCols[idIdx] = i - idxShift
                break

    def _doBtnConfigAttrs(self):
        labels = ['Coluna {0}:'.format(c) for c in self.attrCols]

        if self.hasHeadingRow.get():
            names = [self.colHeadings[c] for c in self.attrCols]
        else:
            names = ['attr_{0}'.format[c] for c in self.attrCols]

        dialog = AttributeConfigDialog(self,
            numAttrs=len(self.attrCols), attrScope=self.attrScope,
            control=self.control, graphName=self.graphName.get(),
            labels=labels, names=names, specs=self.attrSpecs)

        if dialog.result:
            self.attrSpecs = dialog.attrSpecs

    def apply(self):
        pass

class TestDialog(Dialog):
    def __init__(self, master):

        super().__init__(master, 'Teste')

    def body(self, master):
        f = AttributeConfigFrame(master, 15)
        f.pack()

        return f

class NewGraphDialog(Dialog):
    def __init__(self, master, control):

        self.control = control
        self.name = tk.StringVar()
        self.name.set(control.generateNumericName())

        super().__init__(master, 'Novo grafo vazio')

    def body(self, master):
        master.columnconfigure(1, weight=1)
        nameLabel = ttk.Label(master, text='Nome para o grafo:')
        nameLabel.grid(row=0, column=0, sticky=tk.EW)
        nameEntry = ttk.Entry(master, textvariable=self.name)
        nameEntry.grid(row=0, column=1, sticky=tk.EW)

        master.pack(expand=True, fill='both')

        return nameEntry

    def apply(self):
        try:
            name = self.name.get().strip()
            self.control.newEmptyGraph(name)
        except Exception as ex:
            errmsg = str(ex)
            self.control.logger.error(errmsg)
            trace = traceback.format_exc()
            self.control.logger.debug(trace)
            tk.messagebox.showerror('Erro',
                'Falha na criação: '+ errmsg)


class OpenGraphmlDialog(Dialog):
    def __init__(self, master, control):

        self.control = control
        self.arqIn = tk.StringVar()
        self.name = tk.StringVar()
        self.name.set(control.generateNumericName())
        self.relationAttr = tk.StringVar()
        self.edgeAttrs = []

        super().__init__(master, 'Carregamento de Graphml')

    def body(self, master):
        master.columnconfigure(1, weight=1)
        nameLabel = ttk.Label(master, text='Nome para o grafo:')
        nameLabel.grid(row=0, column=0, sticky=tk.EW)
        nameEntry = ttk.Entry(master, textvariable=self.name)
        nameEntry.grid(row=0, column=1, columnspan=2, sticky=tk.EW)

        fileLabel = ttk.Label(master, text='Arquivo:')
        fileLabel.grid(row=1, column=0, sticky=tk.EW)
        fileEntry = ttk.Entry(master, textvariable=self.arqIn, state='readonly')
        fileEntry.grid(row=1, column=1, sticky=tk.EW)
        fileButton = ttk.Button(master, text='Abrir...',
                command=self._doBtnFileOpen)
        fileButton.grid(row=1, column=2, sticky=tk.EW)

        relationLabel = ttk.Label(master, text='Atributo de relação:')
        relationLabel.grid(row=2, column=0, sticky=tk.EW)
        relationEntry = ttk.Entry(master, textvariable=self.relationAttr,
                state='readonly')
        relationEntry.grid(row=2, column=1, sticky=tk.EW)
        self.relationButton = ttk.Button(master, text='Escolher...',
            command=self._doBtnChooseRelation, state=tk.DISABLED)
        self.relationButton.grid(row=2, column=2, sticky=tk.EW)

        master.pack(expand=True, fill='both')

        return nameEntry

    def _doBtnFileOpen(self):
        filename = tk.filedialog.askopenfilename(
            filetypes=[('graphml','*.graphml')])
        if filename:
            self.arqIn.set(filename)
            _,_,edgeAttrs = self.control.inspectGraphmlAttributes(filename)
            self.edgeAttrs = sorted(edgeAttrs.keys())
            self.relationButton['state'] = tk.NORMAL

    def _doBtnChooseRelation(self):
        dialog = gui.ListSelectionDialog(self, title='Atributo de relação',
            text='Selecione o atributo que indica a relação ' +
                'a que cada aresta pertence (tipo da aresta).',
            items=self.edgeAttrs)

        if dialog.result is not None:
            for _, attr in dialog.result:
                self.relationAttr.set(attr)
                break

    def apply(self):
        relation = self.relationAttr.get().strip()
        if len(relation) == 0:
            relation = None

        filename = self.arqIn.get().strip()
        name = self.name.get().strip()
        if len(name) == 0:
            name = None

        try:
            self.control.loadGraphml(filename, name, relation)
        except Exception as ex:
            errmsg = str(ex)
            self.control.logger.error(errmsg)
            trace = traceback.format_exc()
            self.control.logger.debug(trace)
            tk.messagebox.showerror('Erro',
                'Falha no carregamento: '+ errmsg)

class OpenCsvEdgesDialog(Dialog):
    def __init__(self, master, control):

        self.control = control
        self.arqIn = tk.StringVar()
        self.name = tk.StringVar()
        self.name.set(control.generateNumericName())
        self.hasHeadingRow = tk.BooleanVar()
        self.hasHeadingRow.set(True)
        self.srcCol = tk.IntVar()
        self.srcCol.set(0)
        self.tgtCol = tk.IntVar()
        self.tgtCol.set(1)
        self.relCol = tk.IntVar()
        self.relCol.set(-1)
        self.weightCol = tk.IntVar()
        self.weightCol.set(-1)

        self.colHeadings = []

        super().__init__(master, 'Carregamento de CSV de arestas')

    def body(self, master):
        master.columnconfigure(1, weight=1)
        row = 0

        nameLabel = ttk.Label(master, text='Nome para o grafo:')
        nameLabel.grid(row=row, column=0, sticky=tk.E)
        nameEntry = ttk.Entry(master, textvariable=self.name)
        nameEntry.grid(row=row, column=1, columnspan=2, sticky=tk.EW)
        row += 1

        headingsLabel = ttk.Label(master, text='A primeia linha é cabeçalho:')
        headingsLabel.grid(row=row, column=0, sticky=tk.E)
        headingsCheck = ttk.Checkbutton(master, variable=self.hasHeadingRow)
        headingsCheck.grid(row=row, column=1, sticky=tk.W)
        row += 1

        fileLabel = ttk.Label(master, text='Arquivo:')
        fileLabel.grid(row=row, column=0, sticky=tk.E)
        fileEntry = ttk.Entry(master, textvariable=self.arqIn)
        fileEntry.grid(row=row, column=1, sticky=tk.EW)
        fileButton = ttk.Button(master, text='Abrir...',
            command=self._doBtnFileOpen)
        fileButton.grid(row=row, column=2, sticky=tk.EW)
        row += 1

        srcLabel = ttk.Label(master, text='Coluna do nodo de origem:')
        srcLabel.grid(row=row, column=0, sticky=tk.E)
        srcValLabel = ttk.Label(master, textvariable=self.srcCol)
        srcValLabel.grid(row=row, column=1, sticky=tk.W)
        self.srcButton = ttk.Button(master, text='Escolher...',
            command=self._doBtnChooseSrc, state=tk.DISABLED)
        self.srcButton.grid(row=row, column=2, sticky=tk.EW)
        row += 1

        tgtLabel = ttk.Label(master, text='Coluna do nodo de destino:')
        tgtLabel.grid(row=row, column=0, sticky=tk.E)
        tgtValLabel = ttk.Label(master, textvariable=self.tgtCol)
        tgtValLabel.grid(row=row, column=1, sticky=tk.W)
        self.tgtButton = ttk.Button(master, text='Escolher...',
            command=self._doBtnChooseTgt, state=tk.DISABLED)
        self.tgtButton.grid(row=row, column=2, sticky=tk.EW)
        row += 1

        relLabel = ttk.Label(master, text='Coluna da relação:')
        relLabel.grid(row=row, column=0, sticky=tk.E)
        relValLabel = ttk.Label(master, textvariable=self.relCol)
        relValLabel.grid(row=row, column=1, sticky=tk.W)
        self.relButton = ttk.Button(master, text='Escolher...',
            command=self._doBtnChooseRelation, state=tk.DISABLED)
        self.relButton.grid(row=row, column=2, sticky=tk.EW)
        row += 1

        weightLabel = ttk.Label(master, text='Coluna do peso:')
        weightLabel.grid(row=row, column=0, sticky=tk.E)
        weightValLabel = ttk.Label(master, textvariable=self.weightCol)
        weightValLabel.grid(row=row, column=1, sticky=tk.W)
        self.weightButton = ttk.Button(master, text='Escolher...',
            command=self._doBtnChooseWeight, state=tk.DISABLED)
        self.weightButton.grid(row=row, column=2, sticky=tk.EW)
        row += 1

        master.pack(expand=True, fill='both')

        return nameEntry

    def _doBtnFileOpen(self):
        filename = tk.filedialog.askopenfilename(
            filetypes=[('csv','*.csv'),('txt','*.txt'),('all','*')])
        if filename:
            self.arqIn.set(filename)
            self.colHeadings = self.control.inspectCsv(filename)
            self.srcButton['state'] = tk.NORMAL
            self.tgtButton['state'] = tk.NORMAL
            self.relButton['state'] = tk.NORMAL
            self.weightButton['state'] = tk.NORMAL

    def _chooseColumn(self, var, title, text, required=True):

        if required:
            pseudoCols = []
        else:
            pseudoCols = ['<nenhum>']

        items, idxShift = createOptionsCsvColumnSelection(self.colHeadings,
                self.hasHeadingRow.get(), pseudoCols)

        dialog = gui.ListSelectionDialog(self, title=title,
            text=text, items=items)

        if dialog.result is not None:
            for i, _ in dialog.result:
                var.set(i - idxShift)
                break

    def _doBtnChooseSrc(self):
        self._chooseColumn(self.srcCol,
            'Coluna do nodo de origem',
            'Selecione a coluna que indica o nodo de origem da aresta.',
            True)

    def _doBtnChooseTgt(self):
        self._chooseColumn(self.tgtCol,
            'Coluna do nodo de destino',
            'Selecione a coluna que indica o nodo de destino da aresta.',
            True)

    def _doBtnChooseWeight(self):
        self._chooseColumn(self.weightCol,
            'Coluna de peso da aresta',
            'Selecione a coluna que indica o peso da aresta.',
            False)

    def _doBtnChooseRelation(self):
        self._chooseColumn(self.relCol,
            'Coluna de relação da aresta',
            'Selecione a coluna que indica a qual relação ' +
            'a aresta pertence (tipo da aresta).',
            False)

    def apply(self):
        filename = self.arqIn.get().strip()
        name = self.name.get().strip()
        if len(name) == 0:
            name = None

        try:
            self.control.loadCsvGraphEdges(filename,
                self.srcCol.get(), self.tgtCol.get(), name,
                self.relCol.get(), self.weightCol.get(),
                self.hasHeadingRow.get())
        except Exception as ex:
            errmsg = str(ex)
            self.control.logger.error(errmsg)
            trace = traceback.format_exc()
            self.control.logger.debug(trace)
            tk.messagebox.showerror('Erro',
                'Falha no carregamento:\n\n'+ errmsg)

#---------------------------------------------------------------------
# Execução do script
#---------------------------------------------------------------------
if __name__ == '__main__':
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger()
    app = tk.Tk()
    app.title("Graph App")
    appControl = GraphAppControl(logger)
    appGui = GraphAppGUI(app, appControl, logger)
    appGui.pack(expand=True, fill='both')
    app.mainloop()
