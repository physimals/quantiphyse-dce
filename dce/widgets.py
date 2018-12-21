"""
Quantiphyse - Widgets for DCE MRI analysis

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, Citation, TitleWidget, RunWidget
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, ChoiceOption, VectorOption
from quantiphyse.utils import get_plugins

from ._version import __version__

class DceWidget(QpWidget):
    """
    Widget for DCE Pharmacokinetic modelling
    """

    def __init__(self, **kwargs):
        super(DceWidget, self).__init__(name="DCE Modelling", desc="DCE kinetic modelling", 
                                        icon="pk", group="DCE-MRI", **kwargs)

    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)
        
        title = TitleWidget(self, help="pk", batch_btn=True, opts_btn=False)
        vbox.addWidget(title)

        self.input = OptionBox("Input data")
        self.input.add("DCE data", DataOption(self.ivm, include_3d=False, include_4d=True), key="data")
        self.input.add("ROI", DataOption(self.ivm, data=False, rois=True), key="roi")
        self.input.add("T1 map", DataOption(self.ivm, include_3d=True, include_4d=False), key="t1")
        vbox.addWidget(self.input)

        self.options = OptionBox("Options")
        self.options.add("Contrast agent R1 relaxivity", NumericOption(minval=0, maxval=10, default=3.7), key="r1")
        self.options.add("Contrast agent R2 relaxivity", NumericOption(minval=0, maxval=10, default=4.8), key="r2")
        self.options.add("Flip angle", NumericOption(minval=0, maxval=90, default=12), key="fa")
        self.options.add("TR (s)", NumericOption(minval=0, maxval=10, default=4.108), key="tr")
        self.options.add("TE (ms)", NumericOption(minval=0, maxval=10, default=1.832), key="te")
        self.options.add("Time between volumes (s)", NumericOption(minval=0, maxval=30, default=12), key="dt")
        self.options.add("Estimated injection time (s)", NumericOption(minval=0, maxval=60, default=30), key="tinj")
        self.options.add("Ktrans/kep percentile threshold", NumericOption(minval=0, maxval=100, default=100), key="ve-thresh")
        self.options.add("Dose (mM/kg) - preclinical only", NumericOption(minval=0, maxval=5, default=0.6), key="dose", visible=False)

        models = [
            "Clinical: Toft / OrtonAIF (3rd) with offset",
            "Clinical: Toft / OrtonAIF (3rd) no offset",
            "Preclinical: Toft / BiexpAIF (Heilmann)",
            "Preclinical: Ext Toft / BiexpAIF (Heilmann)",
        ]
        self.options.add("Pharmacokinetic model choice", ChoiceOption(models, [1, 2, 3, 4]), key="model")
        self.options.option("model").sig_changed.connect(self._aif_changed)
        vbox.addWidget(self.options)

        # Run button and progress
        vbox.addWidget(RunWidget(self, title="Run modelling"))
        vbox.addStretch(1)
        self._aif_changed()

    def _aif_changed(self):
        self.options.set_visible("dose", self.options.option("model").value in (2, 3))

    def processes(self):
        options = self.input.values()
        options.update(self.options.values())
        return {
            "PkModelling" : options
        }

FAB_CITE_TITLE = "Variational Bayesian inference for a non-linear forward model"
FAB_CITE_AUTHOR = "Chappell MA, Groves AR, Whitcher B, Woolrich MW."
FAB_CITE_JOURNAL = "IEEE Transactions on Signal Processing 57(1):223-236, 2009."

class FabberDceWidget(QpWidget):
    """
    DCE modelling, using the Fabber process
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="Fabber DCE", icon="dce", group="DCE-MRI", desc="Bayesian DCE modelling", **kwargs)
        
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

        self.input = OptionBox("Input data")
        self.input.add("DCE data", DataOption(self.ivm, include_3d=False, include_4d=True), key="data")
        self.input.add("ROI", DataOption(self.ivm, data=False, rois=True), key="roi")
        self.input.add("T1 map", DataOption(self.ivm, include_3d=True, include_4d=False), key="t1")
        vbox.addWidget(self.input)

        self.options = OptionBox("Options")
        self.options.add("R1", NumericOption(minval=0, maxval=10, default=3.7), key="r1")
        #self.options.add("R2", NumericOption(minval=0, maxval=10, default=4.8), key="r2")
        self.options.add("Flip angle", NumericOption(minval=0, maxval=90, default=12), key="fa")
        self.options.add("TR (s)", NumericOption(minval=0, maxval=10, default=4.108), key="tr")
        #self.options.add("TE (ms)", NumericOption(minval=0, maxval=10, default=1.832), key="te")
        self.options.add("Time between volumes (s)", NumericOption(minval=0, maxval=30, default=12), key="delt")
        self.options.add("Estimated injection time (s)", NumericOption(minval=0, maxval=60, default=30), key="delay")
        self.options.add("AIF", ChoiceOption(["Population (Orton 2008)", "Measured DCE signal", "Measured concentration curve"], ["orton", "signal", "conc"]), key="aif")
        self.options.add("AIF source", ChoiceOption(["Global sequence of values", "Voxelwise image"], ["global", "voxelwise"]), key="aif-source")
        self.options.add("AIF", VectorOption([0, ]), key="aif-data")
        self.options.add("AIF image", DataOption(self.ivm), key="suppdata")
        self.options.option("aif").sig_changed.connect(self._aif_changed)
        self.options.option("aif-source").sig_changed.connect(self._aif_changed)
        vbox.addWidget(self.options)

        # Run button and progress
        vbox.addWidget(RunWidget(self, title="Run modelling"))
        vbox.addStretch(1)

        self._aif_changed()

    def _aif_changed(self):
        self.options.set_visible("aif-source", self.options.option("aif").value != "orton")
        self.options.set_visible("suppdata", self.options.option("aif").value != "orton" and self.options.option("aif-source").value == "voxelwise")
        self.options.set_visible("aif-data", self.options.option("aif").value != "orton" and self.options.option("aif-source").value == "global")

    def processes(self):
        options = {
            "model-group" : "dce",
            "model" : "dce_tofts",
            "method" : "vb",
            "noise" : "white",
            "save-mean" : True,
            "save-model-fit" : True,
            "infer-t10" : True,
            "infer-delay" : True,
            "infer-sig0" : True,
            "auto-init-delay" : True,
            "PSP_byname1" : "t10",
            "PSP_byname1_type" : "I",
        }
        options.update(self.input.values())
        options.update(self.options.values())

        # Option modifications for Fabber
        options.pop("aif-source", None)
        options["PSP_byname1_image"] = options.pop("t1")

        # Times in minutes and TR in s
        options["delt"] = options["delt"] / 60 
        options["delay"] = options["delay"] / 60
        options["tr"] = options["tr"] / 1000

        return {
            "Fabber" : options
        }
