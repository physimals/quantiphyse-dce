"""
Quantiphyse - Widgets for DCE MRI analysis

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

from PySide import QtGui

from quantiphyse.gui.dialogs import error_dialog
from quantiphyse.gui.widgets import QpWidget, Citation, TitleWidget
from quantiphyse.utils import debug, warn, get_plugins
from quantiphyse.utils.exceptions import QpException

from ._version import __version__
from .process import PkModellingProcess

class DceWidget(QpWidget):
    """
    Widget for DCE Pharmacokinetic modelling
    """

    def __init__(self, **kwargs):
        super(DceWidget, self).__init__(name="PK Modelling", desc="Pharmacokinetic Modelling", 
                                        icon="pk", group="DCE-MRI", **kwargs)

    def init_ui(self):
        main_vbox = QtGui.QVBoxLayout()
        
        title = TitleWidget(self, "PK Modelling", help="pk", batch_btn=True, opts_btn=False)
        main_vbox.addWidget(title)

        # Inputs
        param_box = QtGui.QGroupBox()
        param_box.setTitle('Parameters')
        input_grid = QtGui.QGridLayout()
        input_grid.addWidget(QtGui.QLabel('R1'), 0, 0)
        self.valR1 = QtGui.QLineEdit('3.7', self)
        input_grid.addWidget(self.valR1, 0, 1)
        input_grid.addWidget(QtGui.QLabel('R2'), 1, 0)
        self.valR2 = QtGui.QLineEdit('4.8', self)
        input_grid.addWidget(self.valR2, 1, 1)
        input_grid.addWidget(QtGui.QLabel('Flip Angle (degrees)'), 2, 0)
        self.valFA = QtGui.QLineEdit('12.0', self)
        input_grid.addWidget(self.valFA, 2, 1)
        input_grid.addWidget(QtGui.QLabel('TR (ms)'), 3, 0)
        self.valTR = QtGui.QLineEdit('4.108', self)
        input_grid.addWidget(self.valTR, 3, 1)
        input_grid.addWidget(QtGui.QLabel('TE (ms)'), 4, 0)
        self.valTE = QtGui.QLineEdit('1.832', self)
        input_grid.addWidget(self.valTE, 4, 1)
        input_grid.addWidget(QtGui.QLabel('delta T (s)'), 5, 0)
        self.valDelT = QtGui.QLineEdit('12', self)
        input_grid.addWidget(self.valDelT, 5, 1)
        input_grid.addWidget(QtGui.QLabel('Estimated Injection time (s)'), 6, 0)
        self.valInjT = QtGui.QLineEdit('30', self)
        input_grid.addWidget(self.valInjT, 6, 1)
        input_grid.addWidget(QtGui.QLabel('Ktrans/kep percentile threshold'), 7, 0)
        self.thresh1 = QtGui.QLineEdit('100', self)
        input_grid.addWidget(self.thresh1, 7, 1)
        input_grid.addWidget(QtGui.QLabel('Dose (mM/kg) (preclinical only)'), 8, 0)
        self.valDose = QtGui.QLineEdit('0.6', self)
        input_grid.addWidget(self.valDose, 8, 1)
        param_box.setLayout(input_grid)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(param_box)
        hbox.addStretch(2)
        main_vbox.addLayout(hbox)

        # Model choice
        aif_choice = QtGui.QGroupBox()
        aif_choice.setTitle('Pharmacokinetic model choice')
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('AIF choice'))
        self.combo = QtGui.QComboBox(self)
        self.combo.addItem("Clinical: Toft / OrtonAIF (3rd) with offset")
        self.combo.addItem("Clinical: Toft / OrtonAIF (3rd) no offset")
        self.combo.addItem("Preclinical: Toft / BiexpAIF (Heilmann)")
        self.combo.addItem("Preclinical: Ext Toft / BiexpAIF (Heilmann)")
        hbox.addWidget(self.combo)
        hbox.addStretch(1)
        aif_choice.setLayout(hbox)
        main_vbox.addWidget(aif_choice)

        # Run button and progress
        run_box = QtGui.QGroupBox()
        run_box.setTitle('Running')
        hbox = QtGui.QHBoxLayout()
        but_gen = QtGui.QPushButton('Run modelling', self)
        but_gen.clicked.connect(self.start_task)
        hbox.addWidget(but_gen)
        self.prog_gen = QtGui.QProgressBar(self)
        self.prog_gen.setStatusTip('Progress of Pk modelling. Be patient. Progress is only updated in chunks')
        hbox.addWidget(self.prog_gen)
        run_box.setLayout(hbox)
        main_vbox.addWidget(run_box)

        main_vbox.addStretch()
        self.setLayout(main_vbox)

        self.process = PkModellingProcess(self.ivm)
        self.process.sig_finished.connect(self.finished)
        self.process.sig_progress.connect(self.progress)

    def start_task(self):
        """
        Start running the PK modelling on button click
        """
        if self.ivm.main is None:
            error_dialog("No data loaded")
            return

        if self.ivm.current_roi is None:
            error_dialog("No ROI loaded - required for Pk modelling")
            return

        if "T10" not in self.ivm.data:
            error_dialog("No T10 map loaded - required for Pk modelling")
            return

        _, options = self.batch_options()
        self.prog_gen.setValue(0)
        self.process.run(options)

    def progress(self, progress):
        self.prog_gen.setValue(100*progress)

    def finished(self, status, output, log, exception):
        """ GUI updates on process completion """
        if status != self.process.SUCCEEDED:
            QtGui.QMessageBox.warning(None, "PK error", "PK modelling failed:\n\n" + str(exception),
                                      QtGui.QMessageBox.Close)

    def batch_options(self):
        options = {}
        options["r1"] = float(self.valR1.text())
        options["r2"] = float(self.valR2.text())
        options["dt"] = float(self.valDelT.text())
        options["tinj"] = float(self.valInjT.text())
        options["tr"] = float(self.valTR.text())
        options["te"] = float(self.valTE.text())
        options["fa"] = float(self.valFA.text())
        options["ve-thresh"] = float(self.thresh1.text())
        options["dose"] = float(self.valDose.text())
        options["model"] = self.combo.currentIndex() + 1

        return "PkModelling", options

FAB_CITE_TITLE = "Variational Bayesian inference for a non-linear forward model"
FAB_CITE_AUTHOR = "Chappell MA, Groves AR, Whitcher B, Woolrich MW."
FAB_CITE_JOURNAL = "IEEE Transactions on Signal Processing 57(1):223-236, 2009."

class FabberDceWidget(QpWidget):
    """
    DCE modelling, using the Fabber process
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="DCE", icon="fabber",  group="Fabber", desc="DCE modelling", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        try:
            self.FabberProcess = get_plugins("processes", "FabberProcess")[0]
        except IndexError:
            self.FabberProcess = None

        if self.FabberProcess is None:
            vbox.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install Fabber to use this widget"))
            return
        
        title = TitleWidget(self, help="fabber-dsc", subtitle="DSC modelling using the Fabber process %s" % __version__)
        vbox.addWidget(title)
              
        cite = Citation(FAB_CITE_TITLE, FAB_CITE_AUTHOR, FAB_CITE_JOURNAL)
        vbox.addWidget(cite)

        vbox.addStretch(1)

    def get_process(self):
        return self.FabberProcess(self.ivm)

    def batch_options(self):
        return "Fabber", self.get_rundata()

    def get_rundata(self):
        rundata = {}
        rundata["model-group"] = "dsc"
        rundata["save-mean"] = ""
        rundata["save-model-fit"] = ""
        rundata["noise"] = "white"
        rundata["max-iterations"] = "20"
        rundata["model"] = "dsc"
        return rundata
