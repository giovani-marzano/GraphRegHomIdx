import tkinter as tk
import tkinter.ttk as ttk
from tkinter.simpledialog import Dialog
import tkinter.messagebox as messagebox
import re
from queue import Queue, Empty
import threading

class ListSelecOneFrame(ttk.Frame):
    def __init__(self, master, filterText='', **options):
        super().__init__(master, **options)

        self._filter = ''
        self._filterText = tk.StringVar(self, value=filterText)
        filterFrame = self._createFilterFrame()
        filterFrame.pack(side='top', fill='x', pady=1)

        listFrame = self._createListFrame()
        listFrame.pack(side='bottom', expand=True, fill='both', pady=1)

    def _createFilterFrame(self):
        filterFrame = ttk.Frame(self)

        label = ttk.Label(filterFrame, text='Filtro:')
        label.pack(side='left', padx=1)

        entry = ttk.Entry(filterFrame, textvariable=self._filterText)
        entry.pack(side='left', padx=1, expand=True, fill='x')

        button = ttk.Button(filterFrame, text='Aplicar',
            command=self._applyFilter)
        button.pack(side='right', padx=1)

        return filterFrame

    def _createListFrame(self):
        listFrame = ttk.Frame(self)
        listFrame.columnconfigure(0, weight=1)
        listFrame.rowconfigure(0, weight=1)

        selScrollH = ttk.Scrollbar(listFrame, orient=tk.HORIZONTAL)
        selScrollH.grid(row=1, column=0, sticky=tk.E+tk.W)
        selScrollV = ttk.Scrollbar(listFrame, orient=tk.VERTICAL)
        selScrollV.grid(row=0, column=1, sticky=tk.N+tk.S)

        self.listBox = tk.Listbox(listFrame,
            selectmode=tk.BROWSE,
            xscrollcommand=selScrollH.set,
            yscrollcommand=selScrollV.set)

        self.listBox.grid(row=0, column=0, sticky=tk.NSEW)

        selScrollV['command'] = self.listBox.yview
        selScrollH['command'] = self.listBox.xview

        return listFrame

    def _applyFilter(self):
        text = self._filterText.get()
        self._filter = text

        if len(text) == 0:
            self._itemsFilter = self._items
        else:
            regExp = re.compile(text, re.IGNORECASE)
            self._itemsFilter = []
            for item in self._items:
                if regExp.search(item) is not None:
                    self._itemsFilter.append(item)

        self._updateList()

    def setItems(self, items):
        self._items = items
        self._applyFilter()

    def getItems(self):
        return self._items

    def setFilter(self, filterText):
        self._filterText.set(filterText)
        self._applyFilter()

    def getFilter(self):
        return self._filter

    def _updateList(self):
        self.listBox.delete(0, tk.END)
        for item in self._itemsFilter:
            self.listBox.insert(tk.END, item)

    def getSelection(self):
        """Obtem a seleção realziada pelo usuário.

        getSelection() -> [(n, item)]

        :return: Lista de tuplas com a posição do item selecionado na lista
        original e o item selecionado.
        """
        cursel = list(map(int,self.listBox.curselection()))

        sel = []
        for n, item in enumerate(self._itemsFilter):
            if n in cursel:
                sel.append((n,item))

        return sel

    def setSelection(self, item):
        try:
            idx = self._items.index(item)
            self.listBox.selection_set(idx)
        except ValueError:
            pass

class ListSelecManyFrame(ttk.Frame):
    def __init__(self, master, filterText='',
            selectmode=tk.BROWSE, **options):
        super().__init__(master, **options)

        self._filter = ''
        self._filterText = tk.StringVar(self, value=filterText)
        filterFrame = self._createFilterFrame()
        filterFrame.pack(side='top', fill='x', pady=1)

        selFrame, lbDisp, lbSelect= self._createSelectionFrame(self)
        self._lbDisp = lbDisp
        self._lbSelect = lbSelect
        selFrame.pack(side='bottom', expand=True, fill='both', pady=1)

    def _createFilterFrame(self):
        filterFrame = ttk.Frame(self)

        label = ttk.Label(filterFrame, text='Filtro:')
        label.pack(side='left', padx=1)

        entry = ttk.Entry(filterFrame, textvariable=self._filterText)
        entry.pack(side='left', padx=1, expand=True, fill='x')

        button = ttk.Button(filterFrame, text='Aplicar',
            command=self._applyFilter)
        button.pack(side='right', padx=1)

        return filterFrame

    def _createSelectionFrame(self, master):

        selFrame = ttk.Frame(master)

        selFrame.columnconfigure(0, weight=1)
        selFrame.columnconfigure(2, weight=1)
        selFrame.rowconfigure(1, weight=1)

        lbDisp = ttk.Label(selFrame, text='Disponiveis:')
        lbDisp.grid(row=0, column=0, sticky=tk.W)
        lbSel = ttk.Label(selFrame, text='Selecionados:')
        lbSel.grid(row=0, column=2, sticky=tk.W)

        dispFrame, dispList = self._createListFrame(selFrame)
        dispFrame.grid(row=1, column=0, sticky=tk.NSEW)

        btnFrame = self._createSelectButtons(selFrame)
        btnFrame.grid(row=1, column=1, sticky=tk.NS)

        selectedFrame, selectList = self._createListFrame(selFrame)
        selectedFrame.grid(row=1, column=2, sticky=tk.NSEW)

        return selFrame, dispList, selectList

    def _createSelectButtons(self, master):
        buttonFrame = ttk.Frame(master)

        btnSelect = tk.Button(buttonFrame, text='->', command=self._onBtnSelect)
        btnDeselect = tk.Button(buttonFrame, text='<-',
                command=self._onBtnDeselect)

        btnSelect.grid(row=1, column=0, sticky=tk.EW)
        btnDeselect.grid(row=2, column=0, sticky=tk.EW)

        return buttonFrame

    def _onBtnSelect(self):
        viewSel = self._lbDisp.curselection()

        for n in map(int, viewSel):
            itemId = self._dispIDs[n]
            self._itemsSelected[itemId] = True

        self._updateList()

    def _onBtnDeselect(self):
        viewSel = self._lbSelect.curselection()

        for n in map(int, viewSel):
            itemId = self._selectIDs[n]
            self._itemsSelected[itemId] = False

        self._updateList()

    def _createListFrame(self, master):
        listFrame = ttk.Frame(master)
        listFrame.columnconfigure(0, weight=1)
        listFrame.rowconfigure(0, weight=1)

        selScrollH = ttk.Scrollbar(listFrame, orient=tk.HORIZONTAL)
        selScrollH.grid(row=1, column=0, sticky=tk.E+tk.W)
        selScrollV = ttk.Scrollbar(listFrame, orient=tk.VERTICAL)
        selScrollV.grid(row=0, column=1, sticky=tk.N+tk.S)

        listBox = tk.Listbox(listFrame,
            selectmode=tk.EXTENDED,
            xscrollcommand=selScrollH.set,
            yscrollcommand=selScrollV.set)

        listBox.grid(row=0, column=0, sticky=tk.NSEW)

        selScrollV['command'] = listBox.yview
        selScrollH['command'] = listBox.xview

        return listFrame, listBox

    def _applyFilter(self):
        text = self._filterText.get()
        self._filter = text

        if len(text) == 0:
            for n in range(len(self._items)):
                self._itemsFilter[n] = True
        else:
            regExp = re.compile(text, re.IGNORECASE)
            for n, item in enumerate(self._items):
                if regExp.search(item) is not None:
                    self._itemsFilter[n] = True
                else:
                    self._itemsFilter[n] = False

        self._updateList()

    def setItems(self, items, selected=[]):
        self._items = items
        self._itemsFilter = [True for i in items]
        self._itemsSelected = [False for i in items]
        for i, item in enumerate(items):
            if item in selected:
                self._itemsSelected[i] = True

        self._applyFilter()

    def getItems(self):
        return self._items

    def setFilter(self, filterText):
        self._filterText.set(filterText)
        self._applyFilter()

    def getFilter(self):
        return self._filter

    def _updateList(self):
        self._lbSelect.delete(0,tk.END)
        self._lbDisp.delete(0,tk.END)
        self._dispIDs = []
        self._selectIDs = []

        for n, item in enumerate(self._items):
            if self._itemsFilter[n]:
                if self._itemsSelected[n]:
                    self._lbSelect.insert(tk.END, item)
                    self._selectIDs.append(n)
                else:
                    self._lbDisp.insert(tk.END, item)
                    self._dispIDs.append(n)

    def getSelection(self):
        """Obtem a seleção realziada pelo usuário.

        getSelection() -> [(n, item)]

        :return: Lista de tuplas com a posição do item selecionado na lista
        original e o item selecionado.
        """
        return [(n,it) for n, it in enumerate(self._items)
                    if self._itemsSelected[n]]

class ListSelectionDialog(Dialog):
    """Dialog that permits the user to select items from a list.
    """
    def __init__(self, parent, title=None,
            text='', items=[], selected=None, filterText=''):

        self._text = text
        self._items = items
        self._filterText = filterText
        self._initialSelection = selected
        self.result = None

        super().__init__(parent, title)

    def body(self, master):
        label = tk.Label(master, text=self._text)
        label.pack(side='top')

        self._selFrame = ListSelecOneFrame(master,
                filterText=self._filterText)

        self._selFrame.setItems(self._items)
        self._selFrame.pack(side='bottom', expand=True, fill='both')

        if self._initialSelection is not None:
            self._selFrame.setSelection(self._initialSelection)

        master.pack(expand=True, fill='both')

        return self._selFrame

    def apply(self):
        self.result = self._selFrame.getSelection()


class ListSelecManyDialog(Dialog):
    """Dialog that permits the user to select many items from a list.
    """
    def __init__(self, parent, title=None,
            text='', items=[], selected=[], filterText=''):

        self._text = text
        self._items = items
        self._selected = selected
        self._filterText = filterText
        self.result = []

        super().__init__(parent, title)

    def body(self, master):
        label = tk.Label(master, text=self._text)
        label.pack(side='top')

        self._selFrame = ListSelecManyFrame(master,
                filterText=self._filterText)

        self._selFrame.setItems(self._items, self._selected)
        self._selFrame.pack(side='bottom', expand=True, fill='both')

        master.pack(expand=True, fill='both')

        return self._selFrame

    def apply(self):
        self.result = self._selFrame.getSelection()


class ExecutionDialog(object):
    def __init__(self, master, command, title='Executando...'):

        self.queue = Queue()
        self.master = master
        self.command = command

        t = threading.Thread(target=self.execThread)

        self.window = tk.Toplevel(master)
        self.window.title(title)
        self.window.transient(master)
        self.window.grab_set()
        self.window.focus_set()
        self.window.protocol('WM_DELETE_WINDOW', self.closeCallback)

        p = ttk.Progressbar(self.window, orient=tk.HORIZONTAL, mode='indeterminate')
        p.pack(expand=True, fill='both')
        p.start()

        t.start()
        master.after(1000, self.periodicPool)
        master.wait_window(self.window)

    def closeDialog(self, result=('END',)):

        if result[0] == 'END':
            messagebox.showinfo('Info','Operação concluida.');
        elif result[0] == 'ERROR':
            messagebox.showerror('Erro',
                'Ocorreu um erro durante a execução:\n\n{0}'.format(result[1]))

        self.master.focus_set()
        self.window.destroy()

    def closeCallback(self):
        pass

    def execThread(self):
        try:
            self.command()
            self.queue.put(('END',))
        except Exception as ex:
            self.queue.put(('ERROR',str(ex)))
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

        if cont:
            self.master.after(1000, self.periodicPool)
        else:
            self.closeDialog(msg)


if __name__ == '__main__':
    app = tk.Tk()
    a = ListSelecManyFrame(app)
    a.pack(side='top', expand=True, fill='both')
    a.setItems(['ola', 'você', 'aí', ',blz?'])

    b = ttk.Button(app, text='teste')
    b.pack(side='bottom')

    def onClick():
        sel = a.getSelection()
        print(*sel)
        g = ListSelectionDialog(app, title='Teste dialog',
                text='Selecione uma lista', items=['cara','cura','cora'])
        print(g.result)

    b['command'] = onClick

    app.mainloop()
