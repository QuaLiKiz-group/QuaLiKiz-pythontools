from qualikiz_tools.qualikiz_io.inputfiles import Particle, Electron, Ion, IonList, QuaLiKizXpoint, QuaLiKizPlan
from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, xarray_to_pandas
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch, qlk_from_dir
import sys
import os
from IPython import embed
import sip
import json
from collections import OrderedDict
from warnings import warn

from PyQt4 import QtCore, QtGui
import pyqtgraph as pg

import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class InputFileWidget(QtGui.QWidget):
    def fillGui(self, dict_):
        for key, val in dict_.items():
            if isinstance(val, bool):
                getattr(self, key + 'Entry').setChecked(val)
            else:
                getattr(self, key + 'Entry').setText(str(val))

    def readGui(self):
        dict_ = {}
        for name in self.inputfiles_class.keynames:
            el = getattr(self, name + 'Entry')
            if isinstance(el, QtGui.QCheckBox):
                dict_[name] = el.isChecked()
            elif isinstance(el, QtGui.QLineEdit):
                dict_[name] = float(el.text())

        return dict_

    def toQLK(self):
        dict_ = self.readGui()
        return self.inputfiles_class(**dict_)


class ElectronWidget(InputFileWidget):
    inputfiles_class = Electron
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.setLayout(gbox)
        for ii, name in enumerate(self.inputfiles_class.keynames):
            setattr(self, name + 'Label', QtGui.QLabel(name + 'e'))
            getattr(self, name + 'Label').setAlignment(QtCore.Qt.AlignRight)
            setattr(self, name + 'Entry', QtGui.QLineEdit("1"))
            gbox.addWidget(getattr(self, name + 'Entry'), ii, 1)
            gbox.addWidget(getattr(self, name + 'Label'), ii, 0)

#class IonWidget(InputFileWidget):
#    inputfiles_class = Ion
#    def __init__(self):
#        super().__init__()
#        self.initUi()
#
#    def initUi(self):
#        gbox = QtGui.QGridLayout()
#        self.setLayout(gbox)
#        for ii, name in enumerate(self.inputfiles_class.keynames):
#            setattr(self, name + 'Label', QtGui.QLabel(name))
#            getattr(self, name + 'Label').setAlignment(QtCore.Qt.AlignRight)
#            setattr(self, name + 'Entry', QtGui.QLineEdit("1"))
#            gbox.addWidget(getattr(self, name + 'Entry'), ii, 1)
#            gbox.addWidget(getattr(self, name + 'Label'), ii, 0)
#        self.show()

class IonListWidget(QtGui.QWidget):
    inputfiles_class = IonList
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.AddIonButton = QtGui.QPushButton("Add Ion")
        self.AddIonButton.clicked.connect(self.add_row)
        self.DelIonButton = QtGui.QPushButton("Del Ion")
        self.DelIonButton.clicked.connect(self.del_row)
        self.setLayout(gbox)
        columns = Ion.keynames + Electron.keynames
        self.DataTable = QtGui.QTableWidget()
        self.DataTable.setColumnCount(len(columns))
        self.DataTable.setHorizontalHeaderLabels(columns)
        gbox.addWidget(self.DataTable)
        gbox.addWidget(self.AddIonButton)
        gbox.addWidget(self.DelIonButton)


    def add_row(self):
        idx = self.DataTable.rowCount()
        self.DataTable.insertRow(idx)
        self.DataTable.resizeRowsToContents()
        return idx

    def del_row(self):
        idx = self.DataTable.rowCount()
        self.DataTable.removeRow(idx - 1)
        self.DataTable.resizeRowsToContents()

    def fillGui(self, ion_list):
        self.clearGui()
        for ion in ion_list:
            idx = self.DataTable.rowCount()
            self.DataTable.insertRow(idx)

            for ii in range(self.DataTable.columnCount()):
                name = self.DataTable.horizontalHeaderItem(ii).text()
                self.DataTable.setItem(idx, ii, QtGui.QTableWidgetItem(str(ion[name])))

        self.DataTable.resizeRowsToContents()

    def clearGui(self):
        for __ in range(self.DataTable.rowCount()):
            self.del_row()

    def readGui(self):
        ionlist = []
        for row in range(self.DataTable.rowCount()):
            dict_ = {}
            for col in range(self.DataTable.columnCount()):
            #dict_ = self.DataTable
                name = self.DataTable.horizontalHeaderItem(col).text()
                el = self.DataTable.item(row, col)
                dict_[name] = float(el.text())
            ionlist.append(dict_)
        return ionlist

    def toQLK(self):
        ionlist = []
        for ion in self.readGui():
            ionlist.append(Ion(**ion))
        return IonList(*ionlist)

class MetaWidget(InputFileWidget):
    inputfiles_class = QuaLiKizXpoint.Meta
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.setLayout(gbox)
        for ii, name in enumerate(self.inputfiles_class.keynames):
            setattr(self, name + 'Label', QtGui.QLabel(name))
            getattr(self, name + 'Label').setAlignment(QtCore.Qt.AlignRight)
            if name in ['coll_flag', 'rot_flag', 'verbose', 'separateflux']:
                setattr(self, name + 'Entry', QtGui.QCheckBox())
            else:
                setattr(self, name + 'Entry', QtGui.QLineEdit("1"))
            gbox.addWidget(getattr(self, name + 'Entry'), ii, 1)
            gbox.addWidget(getattr(self, name + 'Label'), ii, 0)

from itertools import chain
class GeometryWidget(InputFileWidget):
    inputfiles_class = QuaLiKizXpoint.Geometry
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.setLayout(gbox)
        for ii, name in enumerate(chain(self.inputfiles_class.in_args, self.inputfiles_class.extra_args)):
            setattr(self, name + 'Label', QtGui.QLabel(name))
            getattr(self, name + 'Label').setAlignment(QtCore.Qt.AlignRight)
            setattr(self, name + 'Entry', QtGui.QLineEdit("1"))
            gbox.addWidget(getattr(self, name + 'Entry'), ii, 1)
            gbox.addWidget(getattr(self, name + 'Label'), ii, 0)

def strToList(str):
    split = str[1:-1].split(',')
    return [float(el) for el in split]

class SpecialWidget(InputFileWidget):
    inputfiles_class = QuaLiKizXpoint.Special
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.setLayout(gbox)
        for ii, name in enumerate(['kthetarhos']):
            setattr(self, name + 'Label', QtGui.QLabel(name))
            getattr(self, name + 'Label').setAlignment(QtCore.Qt.AlignRight)
            setattr(self, name + 'Entry', QtGui.QLineEdit("1"))
            gbox.addWidget(getattr(self, name + 'Entry'), ii, 1)
            gbox.addWidget(getattr(self, name + 'Label'), ii, 0)

    def fillGui(self, kthetarhos):
        getattr(self, 'kthetarhosEntry').setText(str(kthetarhos))

    def readGui(self):
        kr = strToList(getattr(self, 'kthetarhosEntry').text())
        return kr

    def toQLK(self):
        special_dict = self.readGui()
        return self.inputfiles_class(special_dict)

class NormWidget(InputFileWidget):
    inputfiles_class = dict
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.setLayout(gbox)
        for ii, name in enumerate(['ninorm1', 'Ani1', 'QN_grad', 'x_rho', 'recalc_Nustar', 'recalc_Ti_Te_rel']):
            setattr(self, name + 'Label', QtGui.QLabel(name))
            getattr(self, name + 'Label').setAlignment(QtCore.Qt.AlignRight)
            setattr(self, name + 'Entry', QtGui.QCheckBox())
            gbox.addWidget(getattr(self, name + 'Entry'), ii, 1)
            gbox.addWidget(getattr(self, name + 'Label'), ii, 0)

    def readGui(self):
        dict_ = {}
        for ii, name in enumerate(['ninorm1', 'Ani1', 'QN_grad', 'x_rho', 'recalc_Nustar', 'recalc_Ti_Te_rel']):
            dict_[name] = getattr(self, name + 'Entry').isChecked()
        return dict_

class SaveLoadWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.setLayout(gbox)
        self.LoadFileButton = QtGui.QPushButton('Open file')
        self.LoadFileButton.clicked.connect(self.openfile)
        self.SaveFileButton = QtGui.QPushButton('Save file')
        self.SaveFileButton.clicked.connect(self.savefile)

        gbox.addWidget(self.LoadFileButton, 0, 0)
        gbox.addWidget(self.SaveFileButton, 0, 1)


    def openfile(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                  '.',"JSON files (*.json);;All files (*)")

        if fname != '':
            qualikiz_plan = QuaLiKizPlan.from_json(fname)
            base = self.topLevelWidget().base
            plan = self.topLevelWidget().plan
            base.fillGui(qualikiz_plan['xpoint_base'])
            plan.fillGui(qualikiz_plan['scan_type'], qualikiz_plan['scan_dict'])

    def savefile(self):
        qlk_plan = self.topLevelWidget().generateQLKPlan()
        dialog = QtGui.QFileDialog()
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setNameFilter('JSON files (*.json)')
        dialog.setDefaultSuffix('json')
        if dialog.exec_() == QtGui.QFileDialog.Accepted:
            fname = dialog.selectedFiles()[0]
            with open(fname, 'w') as file_:
                json.dump(qlk_plan, file_, indent=4)

class QuaLiKizXpointWidget(InputFileWidget):
    inputfiles_class = QuaLiKizXpoint
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        gbox = QtGui.QGridLayout()
        self.setLayout(gbox)

        self.ElectronWidget = ElectronWidget()
        self.MetaWidget = MetaWidget()
        self.SpecialWidget = SpecialWidget()
        self.GeometryWidget = GeometryWidget()
        self.IonListWidget = IonListWidget()
        self.NormWidget = NormWidget()
        gbox.addWidget(self.ElectronWidget, 0, 0)
        gbox.addWidget(self.MetaWidget, 0, 1)
        gbox.addWidget(self.SpecialWidget, 2, 0)
        gbox.addWidget(self.GeometryWidget, 1, 0)
        gbox.addWidget(self.IonListWidget, 3, 0)
        gbox.addWidget(self.NormWidget, 1, 1)

    def fillGui(self, xpoint_base):
        self.MetaWidget.fillGui(xpoint_base['meta'])
        self.SpecialWidget.fillGui(xpoint_base['kthetarhos'])
        self.GeometryWidget.fillGui(xpoint_base['geometry'])
        self.ElectronWidget.fillGui(xpoint_base['elec'])
        self.IonListWidget.fillGui(xpoint_base['ions'])
        self.NormWidget.fillGui(xpoint_base['norm'])

    def toQLK(self):
        special_dict = self.SpecialWidget.toQLK()
        kthetarhos = special_dict['kthetarhos']
        elec = self.ElectronWidget.toQLK()
        ions = self.IonListWidget.toQLK()
        meta = self.MetaWidget.toQLK()
        norm = self.NormWidget.toQLK()
        geom = self.GeometryWidget.toQLK()

        xpoint_base = QuaLiKizXpoint(kthetarhos, elec, ions, **geom, **norm, **meta)
        return xpoint_base

    def readGui(self):
        raise NotImplementedError

class ScanDictPairLayout(QtGui.QHBoxLayout):
    options = (['<...>'] +
               [name + 'i' for name in Ion.keynames] +
               [name + 'i' for name in Electron.keynames] +
               [name + 'e' for name in Electron.keynames] +
               Electron.keynames +
               QuaLiKizXpoint.Geometry.keynames +
               QuaLiKizXpoint.Meta.keynames)

    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.combo = QtGui.QComboBox()
        self.combo.addItems(self.__class__.options)
        self.combo.currentIndexChanged.connect(self.selectionchange)
        self.combo.oldval = self.combo.currentText()
        self.values = QtGui.QLineEdit("[1]")
        self.addWidget(self.combo)
        self.addWidget(self.values)

    def selectionchange(self, ii):
        if self.combo.oldval == '<...>':
            self.parentWidget().addpair()
        else:
            pass
        if self.combo.currentText() == '<...>':
            self.delete()
        else:
            self.combo.oldval = self.combo.currentText()

    def delete(self):
        self.combo.setParent(None)
        self.values.setParent(None)
        self.setParent(None)


class ScanDictWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.box = QtGui.QVBoxLayout()
        self.setLayout(self.box)
        self.addpair()
        self.box.addStretch()

    @property
    def pairs(self):
        res = [child for child in self.layout().children() if isinstance(child, ScanDictPairLayout) is True]
        return res

    def addpair(self, scan_dict_pair_layout=None):
        if scan_dict_pair_layout is None:
            scan_dict_pair_layout = ScanDictPairLayout()
        insert_idx = self.box.count() - 1
        self.box.insertLayout(insert_idx, scan_dict_pair_layout)
        return insert_idx

    def fillGui(self, scan_dict):
        self.clearGui()
        for key, val in scan_dict.items():
            scan_dict_pair = self.box.children()[-1]
            combo = scan_dict_pair.combo
            combo_idx = combo.findText(key)
            if combo_idx >= 0:
                combo.setCurrentIndex(combo_idx)
            else:
                warn('Scan variable {!s} is not known!'.format(scan_type))
            scan_dict_pair.values.setText(str(val))

    def clearGui(self):
        for scan_dict_pair in self.box.children():
            scan_dict_pair.delete()
        self.addpair()

class ScanTypeWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.box = QtGui.QHBoxLayout()
        self.setLayout(self.box)
        self.combo = QtGui.QComboBox()
        self.combo.addItems(['hyperedge', 'hyperrect', 'parallel'])
        self.box.addWidget(self.combo)

    def fillGui(self, scan_type):
        combo_idx = self.combo.findText(scan_type)
        if combo_idx >= 0:
            self.combo.setCurrentIndex(combo_idx)
        else:
            warn('Scan type {!s} is not known!'.format(scan_type))

class QuaLiKizPlanWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.box = QtGui.QVBoxLayout()
        self.setLayout(self.box)

        self.scanDictWidget = ScanDictWidget()
        self.scanTypeWidget = ScanTypeWidget()
        self.SaveLoadWidget = SaveLoadWidget()
        self.box.addWidget(self.scanTypeWidget)
        self.box.addWidget(self.scanDictWidget)
        self.box.addWidget(self.SaveLoadWidget)

    def readGui(self):
        dict_ = {'scan_type': self.scanTypeWidget.combo.currentText(),
                 'scan_dict': OrderedDict()
                 }
        for pair in self.scanDictWidget.pairs:
            name = pair.combo.currentText()
            if name != '<...>':
                lst = strToList(pair.values.text())
                dict_['scan_dict'][name] = lst

        return dict_

    def fillGui(self, scan_type, scan_dict):
        self.scanTypeWidget.fillGui(scan_type)
        self.scanDictWidget.fillGui(scan_dict)

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = fig = Figure(figsize=(width, height), dpi=dpi)
        for ii in range(1, 5):
            fig.add_subplot(2, 2, ii)
        #fig, self.axes = plt.subplots(2, 2, figsize=(width, height), dpi=dpi)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.cla()
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()

class QuaLiKizInputPlotWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.box = QtGui.QVBoxLayout()
        self.gbox = QtGui.QGridLayout()
        self.setLayout(self.box)
        self.gradlike = MyMplCanvas()
        self.box.addWidget(self.gradlike)

    def plotGradlike(self):
        embed()

class QuaLiKizInputWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.box = QtGui.QVBoxLayout()
        self.setLayout(self.box)

        self.qualikizInputPlot = QuaLiKizInputPlotWidget()
        self.box.addWidget(self.qualikizInputPlot)
        self.plotInputButton = QtGui.QPushButton("Plot Input")
        self.plotInputButton.clicked.connect(self.plot_input)
        self.box.addWidget(self.plotInputButton)

    def plot_input(self):
        top = self.topLevelWidget()
        panda_dict = top.generateInput()
        panda_dict['dimx']
        for ax in self.qualikizInputPlot.gradlike.fig.axes:
            ax.cla()

        efelike = panda_dict['dimx']
        efilike = panda_dict['nions']
        efilike['Ti_Te'] = efilike['Ti'] / efelike['Te']
        efelike['epsilon'] = efelike['Rmin'] * efelike['x'] / efelike['Ro']
        efelike['ft'] = 2 * (2 * efelike['epsilon']) ** .5 / np.pi #Trapped particle fraction
        efilike = efilike.unstack('nion').reset_index('dimx')
        efelike = efelike.reset_index('dimx')
        efelike.plot(x='dimx', y=['Ate', 'Te'], linestyle='--', ax=self.qualikizInputPlot.gradlike.fig.axes[0])
        efilike.plot(x='dimx', y=['Ati', 'Ti'], ax=self.qualikizInputPlot.gradlike.fig.axes[0])

        efelike.plot(x='dimx', y=['Ane', 'ne'], linestyle='--', ax=self.qualikizInputPlot.gradlike.fig.axes[1])
        efilike.plot(x='dimx', y=['Ani', 'normni'], ax=self.qualikizInputPlot.gradlike.fig.axes[1])

        efelike.plot(x='dimx', y=['ft'], linestyle='--', ax=self.qualikizInputPlot.gradlike.fig.axes[2])
        efilike.plot(x='dimx', y=['Ti_Te'], ax=self.qualikizInputPlot.gradlike.fig.axes[2])

        efelike.plot(x='dimx', y=['smag', 'q', 'alpha'], linestyle='--', ax=self.qualikizInputPlot.gradlike.fig.axes[3])
        #efilike.plot(x='dimx', y=['Ati', 'Ti'], ax=self.qualikizInputPlot.gradlike.fig.axes[3])
        self.qualikizInputPlot.gradlike.draw()

class QuaLiKizOutputWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.box = QtGui.QVBoxLayout()
        self.setLayout(self.box)
        self.runQLKButton = QtGui.QPushButton("Run QuaLiKiz")
        self.runQLKButton.clicked.connect(self.runQLK)
        self.box.addWidget(self.runQLKButton)

    def runQLK(self):
        # For now, just use bash
        machine = 'bash'
        try:
            _temp = __import__('qualikiz_tools.machine_specific.' + machine,
                               fromlist=['Run', 'Batch'])
        except ModuleNotFoundError:
            raise NotImplementedError('Machine {!s} not implemented yet'.format(machine))
        Run, Batch = _temp.Run, _temp.Batch


        cwd = os.curdir
        try:
            __, qlk_instance = qlk_from_dir(cwd, batch_class=Batch, run_class=Run)
        except Exception:
            print('Directory is not a QuaLiKiz dir, creating temp..')
            import uuid
            top = self.topLevelWidget()
            plan = top.generateQLKPlan()
            name = 'QLK' + str(uuid.uuid4())
            os.mkdir(name)
            run = Run(cwd, name, '../../../QuaLiKiz' , plan)
            batch = Batch(cwd, name, [run])
            embed()

        exit()

class QuaLiKizTabWidget(QtGui.QTabWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.base = QuaLiKizXpointWidget()
        qualikiz_plan = QuaLiKizPlan.from_json('../qualikiz_io/parameters_template.json')
        self.base.fillGui(qualikiz_plan['xpoint_base'])
        self.addTab(self.base ,"QuaLiKizXpoint")
        self.plan = QuaLiKizPlanWidget()
        self.plan.fillGui(qualikiz_plan['scan_type'], qualikiz_plan['scan_dict'])
        self.addTab(self.plan, "QuaLiKizPlan")
        self.input = QuaLiKizInputWidget()
        self.addTab(self.input, 'QuaLiKiz Input')
        self.output = QuaLiKizOutputWidget()
        self.addTab(self.output, 'QuaLiKiz Output')
        self.output.runQLKButton.click()
        self.show()

    def generateInput(self):
        qlk_plan = self.generateQLKPlan()
        panda_dict = qlk_plan.to_pandas()
        return panda_dict

    def generateQLKPlan(self):
        xpoint_base = self.base.toQLK()
        scan_plan = self.plan.readGui()
        qlk_plan = QuaLiKizPlan(scan_plan['scan_dict'], scan_plan['scan_type'], xpoint_base)
        return qlk_plan

def main():
    app = QtGui.QApplication(sys.argv)
    tabs = QuaLiKizTabWidget()
    app.setApplicationName('in')

    sys.exit(app.exec_())

if __name__ == '__main__':

    main()

