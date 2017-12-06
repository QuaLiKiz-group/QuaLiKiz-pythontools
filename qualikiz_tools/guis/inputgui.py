from qualikiz_tools.qualikiz_io.inputfiles import Particle, Electron, Ion, IonList, QuaLiKizXpoint, QuaLiKizPlan
from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, xarray_to_pandas
import sys
from IPython import embed

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

    def to_QLK(self):
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
        self.show()

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
        self.AddIonButton.clicked.connect(self.add_ion)
        self.DelIonButton = QtGui.QPushButton("Del Ion")
        self.DelIonButton.clicked.connect(self.del_ion)
        self.setLayout(gbox)
        columns = Ion.keynames + Electron.keynames
        self.DataTable = QtGui.QTableWidget()
        self.DataTable.setColumnCount(len(columns))
        self.DataTable.setHorizontalHeaderLabels(columns)
        gbox.addWidget(self.DataTable)
        gbox.addWidget(self.AddIonButton)
        gbox.addWidget(self.DelIonButton)

        self.show()

    def add_ion(self):
        idx = self.DataTable.rowCount()
        self.DataTable.insertRow(idx)
        self.DataTable.resizeRowsToContents()
        return idx

    def del_ion(self):
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

    def to_QLK(self):
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
        self.show()

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
        self.show()

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
        self.show()

    def fillGui(self, kthetarhos):
        getattr(self, 'kthetarhosEntry').setText(str(kthetarhos))

    def readGui(self):
        kr = getattr(self, 'kthetarhosEntry').text()[1:-1].split(',')
        kr = [float(el) for el in kr]

    def to_QLK(self):
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
        self.show()

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

        self.show()

    def openfile(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                  '.',"JSON files (*.json);;All files (*)")

        qualikiz_plan = QuaLiKizPlan.from_json(fname)
        self.parentWidget().fillGui(qualikiz_plan['xpoint_base'])


    def savefile(self):
        xpoint_base = self.parentWidget().to_QLK()
        dialog = QtGui.QFileDialog()
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setNameFilter('JSON files (*.json)')
        dialog.setDefaultSuffix('json')
        if dialog.exec_() == QtGui.QFileDialog.Accepted:
            fname = dialog.selectedFiles()[0]
        import json
        if fname != '':
            with open(fname, 'w') as file_:
                json.dump(xpoint_base, file_, indent=4)

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
        self.SaveLoadWidget = SaveLoadWidget()
        gbox.addWidget(self.ElectronWidget, 0, 0)
        gbox.addWidget(self.MetaWidget, 0, 1)
        gbox.addWidget(self.SpecialWidget, 2, 0)
        gbox.addWidget(self.GeometryWidget, 1, 0)
        gbox.addWidget(self.IonListWidget, 3, 0)
        gbox.addWidget(self.SaveLoadWidget, 3, 1)
        gbox.addWidget(self.NormWidget, 1, 1)
        self.show()

    def fillGui(self, xpoint_base):
        self.MetaWidget.fillGui(xpoint_base['meta'])
        self.SpecialWidget.fillGui(xpoint_base['kthetarhos'])
        self.GeometryWidget.fillGui(xpoint_base['geometry'])
        self.ElectronWidget.fillGui(xpoint_base['elec'])
        self.IonListWidget.fillGui(xpoint_base['ions'])
        self.NormWidget.fillGui(xpoint_base['norm'])

    def to_QLK(self):
        kthetarhos = self.SpecialWidget.to_QLK()
        elec = self.ElectronWidget.to_QLK()
        ions = self.IonListWidget.to_QLK()
        meta = self.MetaWidget.to_QLK()
        norm = self.NormWidget.to_QLK()
        geom = self.GeometryWidget.to_QLK()

        xpoint_base = QuaLiKizXpoint(kthetarhos, elec, ions, **geom, **norm, **meta)
        return xpoint_base

    def readGui(self):
        raise NotImplementedError



def main():
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('in')
    ex = QuaLiKizXpointWidget()
    qualikiz_plan = QuaLiKizPlan.from_json('../qualikiz_io/parameters_template.json')
    ex.fillGui(qualikiz_plan['xpoint_base'])

    sys.exit(app.exec_())

if __name__ == '__main__':

    main()

