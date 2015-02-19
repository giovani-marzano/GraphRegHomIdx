#!/usr/bin/python3
# coding: utf-8

import os.path
import sys
import logging
import logging.config
import traceback

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

class GraphModel(object):
    def __init__(self, graphObj, name, fileName=None):
        self.graph = graphObj
        self.name = name
        self.fileName = fileName

class GraphAppControl(object):
    def __init__(self, logger):
        self.logger = logger
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

    def loadGraphml(self, fileName, name=None,
            relationAttr=gr.EDGE_RELATION_ATTR):
        if name is None:
            n = 1
            name = '{0:03}'.format(n)
            while name in self.graphModels:
                n += 1
                name = '{0:03}'.format(n)

        if name in self.graphModels:
            return (False, 'Já existe grafo com nome "{0}"'.format(name))

        try:
            g = gr.loadGraphml(fileName, relationAttr)
            gm = GraphModel(g, name, fileName)
            self.graphModels[name] = gm
            self._callInsertHandlers(gm)
        except Exception as ex:
            self.logger.error(str(ex))
            exStr = traceback.format_exc()
            self.logger.debug(exStr)
            return (False, str(ex))
        else:
            return (True, '')

    def removeGraph(self, graphName):
        """Remove a graph from the collection.

        Args:
            - graphName: Name of the graph to be removed
        """
        if graphName in self.graphModels:
            gmod = self.graphModels[graphName]
            del self.graphModels[graphName]
            self._callDeleteHandlers(gmod)

#---------------------------------------------------------------------
# Classes GUI
#---------------------------------------------------------------------
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
from tkinter.simpledialog import Dialog
import gui

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

        self.graphTree = graphTree

        self._createMenu()

        control.addInsertHandler(self._updateGraphView)
        control.addChangeHandler(self._updateGraphView)
        control.addDeleteHandler(self._removeGraphView)

    def _getGraphAndTreeIid(self, graphId):
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

    def _removeGraphView(self, graphId):
        """Remove a graph from the view.

        Args:
            - graphId: Identifies the graph to be removed. It can a string
              representing the graph's Treeview iid or the graph's GraphModel.

        Return:
            - The removed graphModel or None
        """

        iid, gmod = self._getGraphAndTreeIid(graphId)

        if iid is not None:
            self.graphTree.delete(iid)
            del self.graphToIid[gmod]
            del self.iidToGraph[iid]

        return gmod

    def _updateGraphView(self, graphModel):
        """Inserts or updates a graph in the view.
        """
        pos = 'end'
        iid, _ = self._getGraphAndTreeIid(graphModel)

        # Removing the graph
        if iid is not None:
            pos = self.graphTree.index(iid)
            self._removeGraphView(iid)

        # (Re)inserting the graph
        iid = self.graphTree.insert('', pos,
            text=graphModel.name,
            values=(graphModel.fileName, 'graph'))

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

    def _createMenu(self):
        top = self.winfo_toplevel()
        self.menuBar = tk.Menu(top)
        top['menu'] = self.menuBar

        m = tk.Menu(self.menuBar)
        self.menuBar.add_cascade(label='Grafo', menu=m)
        m.add_command(label='Abrir graphml...', command=self._menuCmdOpenGraphml)
        m.add_command(label='Remover...', command=self._menuCmdRemoveGraph)

    def _menuCmdOpenGraphml(self):
        dialog = OpenGraphmlDialog(self, self.control, title="Abrir graphml")

    def _menuCmdRemoveGraph(self):
        items = sorted(self.control.graphModels.keys())
        dialog = gui.ListSelectionDialog(self, title='Remoção de grafo',
            text='Selecione o grafo a ser removido', items=items)
        if dialog.result is not None:
            for i, selection in dialog.result:
                self.control.removeGraph(selection)

class OpenGraphmlDialog(Dialog):
    def __init__(self, master, control, title=None):

        self.control = control
        self.arqIn = tk.StringVar()

        super().__init__(master, title)

    def body(self, master):
        master.columnconfigure(1, weight=1)
        nameLabel = ttk.Label(master, text='Nome para o grafo:')
        nameLabel.grid(row=0, column=0, sticky=tk.EW)
        self.nameEntry = ttk.Entry(master)
        self.nameEntry.grid(row=0, column=1, columnspan=2, sticky=tk.EW)

        fileLabel = ttk.Label(master, text='Arquivo:')
        fileLabel.grid(row=1, column=0, sticky=tk.EW)
        self.fileEntry = ttk.Entry(master, textvariable=self.arqIn)
        self.fileEntry.grid(row=1, column=1, sticky=tk.EW)
        fileButton = ttk.Button(master, text='Abrir...',
            command=self._doBtnFileOpen)
        fileButton.grid(row=1, column=2, sticky=tk.EW)

        relationLabel = ttk.Label(master, text='Atributo de relação:')
        relationLabel.grid(row=2, column=0, sticky=tk.EW)
        self.relationEntry = ttk.Entry(master)
        self.relationEntry.grid(row=2, column=1, columnspan=2, sticky=tk.EW)

        master.pack(expand=True, fill='both')

        return self.nameEntry

    def _doBtnFileOpen(self):
        fileName = tk.filedialog.askopenfilename(
            filetypes=[('graphml','*.graphml')])
        if fileName != '':
            self.arqIn.set(fileName)

    def apply(self):
        relation = self.relationEntry.get().strip()
        if len(relation) == 0:
            relation = None

        fileName = self.arqIn.get().strip()
        name = self.nameEntry.get().strip()
        if len(name) == 0:
            name = None

        ok, errmsg = self.control.loadGraphml(fileName, name, relation)

        if not ok:
            tk.messagebox.showerror('Erro', errmsg)


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
