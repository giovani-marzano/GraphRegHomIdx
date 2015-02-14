#!/usr/bin/python3
# coding: utf-8

import os.path
import sys
import logging
import logging.config

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

#---------------------------------------------------------------------
# Classes GUI
#---------------------------------------------------------------------
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import gui

class GraphAppGUI(tk.Frame):
    def __init__(self, master, logger, **options):
        super().__init__(master, **options)

        panedWin = ttk.PanedWindow(self, orient=tk.VERTICAL)

        tv = ttk.Treeview(panedWin,
            columns=('value', 'itemType'),
            displaycolumns=('value'),
            selectmode='browse',
            show='tree headings')

        g1ID = tv.insert('', 'end', text='grafo1',
            values=('um/path/para/o/arquivo/aberto/item1',
                'graph'))
        tv.insert('', 'end', text='grafo2',
            values=('um/path/para/o/arquivo/aberto/item2',
                'graph'))

        grafId = tv.insert(g1ID,'end', text='Num. nodos:',
            values=(1000,'stats'))
        grafId = tv.insert(g1ID,'end', text='Num. arestas:',
            values=(23452,'stats'))
        grafId = tv.insert(g1ID,'end', text='Atributos de grafo',
            values=(2,'attrs'))
        nodoId = tv.insert(g1ID,'end', text='Atributos de nodo',
            values=(2,'attrs'))
        edgeId = tv.insert(g1ID,'end', text='Atributos de aresta',
            values=(2,'attrs'))
        print(grafId)

        iId = tv.insert(grafId, 'end', text='attr1',
            values=('3','graphAttr'))
        tv.insert(iId, 'end', text='Tipo:',
            values=('integer','attrType'))
        iId = tv.insert(grafId, 'end', text='attr2',
            values=('meu sai','graphAttr'))
        tv.insert(iId, 'end', text='Tipo:',
            values=('string','attrType'))
        iId = tv.insert(nodoId, 'end', text='attr1',
            values=('','nodeAttr'))
        tv.insert(iId, 'end', text='Tipo:',
            values=('integer','attrType'))
        tv.insert(iId, 'end', text='Default:',
            values=(0,'attrDefault'))
        iId = tv.insert(nodoId, 'end', text='attr2',
            values=('','nodeAttr'))
        tv.insert(iId, 'end', text='Tipo:',
            values=('integer','attrType'))
        tv.insert(iId, 'end', text='Default:',
            values=(0,'attrDefault'))
        iId = tv.insert(edgeId, 'end', text='attr1',
            values=('','edgeAttr'))
        tv.insert(iId, 'end', text='Tipo:',
            values=('integer','attrType'))
        tv.insert(iId, 'end', text='Default:',
            values=(0,'attrDefault'))
        iId = tv.insert(edgeId, 'end', text='attr2',
            values=('','edgeAttr'))
        tv.insert(iId, 'end', text='Tipo:',
            values=('integer','attrType'))
        tv.insert(iId, 'end', text='Default:',
            values=(0,'attrDefault'))

        panedWin.add(tv)

        panedWin.pack(expand=True, fill='both')

#---------------------------------------------------------------------
# Execução do script
#---------------------------------------------------------------------
if __name__ == '__main__':
    logging.config.dictConfig(LOG_CONFIG)
    logger = logging.getLogger()
    app = tk.Tk()
    app.title("Graph App")
    appGui = GraphAppGUI(app, logger)
    appGui.pack(expand=True, fill='both')
    app.mainloop()
