from qualikiz_tools.qualikiz_io.inputfiles import Particle, Electron, Ion, IonList, QuaLiKizXpoint, QuaLiKizPlan
from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, xarray_to_pandas
import sys
from IPython import embed
import sip
import json
from collections import OrderedDict

from PyQt4 import QtCore, QtGui
import pyqtgraph as pg

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
        for ion in ion_list:
            idx = self.DataTable.rowCount()
            self.DataTable.insertRow(idx)

            for ii in range(self.DataTable.columnCount()):
                name = self.DataTable.horizontalHeaderItem(ii).text()
                self.DataTable.setItem(idx, ii, QtGui.QTableWidgetItem(str(ion[name])))

        self.DataTable.resizeRowsToContents()

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

    def toQLK(self):
        kr = self.readGui()
        return self.inputfiles_class(kr)

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
            self.parentWidget().fillGui(qualikiz_plan['xpoint_base'])

    def savefile(self):
        base = self.topLevelWidget().base
        plan = self.topLevelWidget().plan
        xpoint_base = base.toQLK()
        scan_plan = plan.readGui()
        qlk_plan = QuaLiKizPlan(scan_plan['scan_dict'], scan_plan['scan_type'], xpoint_base)
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
        kthetarhos = self.SpecialWidget.toQLK()
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
            self.combo.setParent(None)
            self.values.setParent(None)
            self.setParent(None)
        else:
            self.combo.oldval = self.combo.currentText()

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

    def addpair(self):
        self.box.insertLayout(self.box.count() - 1, ScanDictPairLayout())

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
        self.addTab(self.plan, "QuaLiKizPlan")
        self.show()

def main():
    app = QtGui.QApplication(sys.argv)
    tabs = QuaLiKizTabWidget()
    app.setApplicationName('in')

    sys.exit(app.exec_())

if __name__ == '__main__':

    main()

