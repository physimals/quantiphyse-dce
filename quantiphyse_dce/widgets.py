"""
Quantiphyse - Widgets for DCE MRI analysis

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.gui.widgets import QpWidget, Citation, TitleWidget, RunWidget
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, ChoiceOption, NumberListOption, BoolOption
from quantiphyse.utils import get_plugins

from ._version import __version__

class DceWidget(QpWidget):
    """
    Widget for DCE Pharmacokinetic modelling
    """

    def __init__(self, **kwargs):
        super(DceWidget, self).__init__(name="DCE Modelling", desc="DCE kinetic modelling",
                                        icon="dce", group="DCE-MRI", **kwargs)

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
        self.options.add("Contrast agent R1 relaxivity (l/mmol s)", NumericOption(minval=0, maxval=10, default=3.7), key="r1")
        self.options.add("Contrast agent R2 relaxivity (l/mmol s)", NumericOption(minval=0, maxval=10, default=4.8), key="r2")
        self.options.add("Flip angle (\N{DEGREE SIGN})", NumericOption(minval=0, maxval=90, default=12), key="fa")
        self.options.add("TR (ms)", NumericOption(minval=0, maxval=10, default=4.108), key="tr")
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
        QpWidget.__init__(self, name="Bayesian DCE", icon="dce", group="DCE-MRI", desc="DCE model fitting using Bayesian inference", **kwargs)

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
        self.input.add("ROI", DataOption(self.ivm, data=False, rois=True), key="roi", checked=True)
        self.input.add("T1 map", DataOption(self.ivm, include_3d=True, include_4d=False), key="t1", checked=True)
        self.input.option("t1").sig_changed.connect(self._t1_map_changed)
        vbox.addWidget(self.input)

        self.acquisition = OptionBox("Acquisition")
        self.acquisition.add("Contrast agent R1 relaxivity (l/mmol s)", NumericOption(minval=0, maxval=10, default=3.7), key="r1")
        self.acquisition.add("Flip angle (\N{DEGREE SIGN})", NumericOption(minval=0, maxval=90, default=12), key="fa")
        self.acquisition.add("TR (ms)", NumericOption(minval=0, maxval=10, default=4.108), key="tr")
        self.acquisition.add("Time between volumes (s)", NumericOption(minval=0, maxval=30, default=12), key="delt")
        vbox.addWidget(self.acquisition)

        self.model = OptionBox("Model options")
        self.model.add("Model", ChoiceOption(["Standard Tofts model",
                                              "Extended Tofts model (ETM)",
                                              "2 Compartment exchange model",
                                              "Compartmental Tissue Update (CTU) model",
                                              "Adiabatic Approximation to Tissue Homogeneity (AATH) Model"],
                                             ["dce_tofts",
                                              "dce_ETM",
                                              "dce_2CXM",
                                              "dce_CTU",
                                              "dce_AATH"]), key="model")
        self.model.add("AIF", ChoiceOption(["Population (Orton 2008)", "Population (Parker)", "Measured DCE signal", "Measured concentration curve"], ["orton", "parker", "signal", "conc"]), key="aif")
        self.model.add("Bolus injection time (s)", NumericOption(minval=0, maxval=60, default=30), key="tinj")
        self.model.add("AIF data values", NumberListOption([0, ]), key="aif-data")
        self.model.add("T1 (s)", NumericOption(minval=0.0, maxval=5.0, default=1.0), key="t10")
        self.model.add("Allow T1 to vary", BoolOption(default=False), key="infer-t10")
        self.model.add("Bolus arrival time (s)", NumericOption(minval=0, maxval=2.0, default=0), key="delay")
        self.model.add("Allow bolus arrival time to vary", BoolOption(default=False), key="infer-delay")
        self.model.add("Infer kep rather than ve", BoolOption(default=False), key="infer-kep")
        self.model.add("Infer flow", BoolOption(default=True), key="infer-fp")
        self.model.add("Infer permeability-surface area", BoolOption(default=False), key="infer-ps")
        self.model.add("Spatial regularization", BoolOption(default=False), key="spatial")
        self.model.option("model").sig_changed.connect(self._model_changed)
        self.model.option("aif").sig_changed.connect(self._aif_changed)
        vbox.addWidget(self.model)

        # Run button and progress
        vbox.addWidget(RunWidget(self, title="Run modelling"))
        vbox.addStretch(1)

        self._aif_changed()
        self._model_changed()

    def _t1_map_changed(self):
        self.model.set_visible("t10", "t1" not in self.input.values())

    def _aif_changed(self):
        aif_source = self.model.option("aif").value
        self.model.set_visible("tinj", aif_source not in ("signal", "conc"))
        self.model.set_visible("aif-data", aif_source in ("signal", "conc"))

    def _model_changed(self):
        self.model.set_visible("infer-kep", self.model.option("model").value in ("dce_tofts", "dce_ETM"))
        self.model.set_visible("infer-fp", self.model.option("model").value == "dce_AATH")
        self.model.set_visible("infer-ps", self.model.option("model").value == "dce_AATH")

    def processes(self):
        options = {
            "model-group" : "dce",
            "method" : "vb",
            "noise" : "white",
            "save-mean" : True,
            "save-model-fit" : True,
            "convergence" : "trialmode",
            "max-trials" : 20,
            "max-iterations" : 50,
            "infer-sig0" : True,
        }
        options.update(self.input.values())
        options.update(self.acquisition.values())
        options.update(self.model.values())

        # Extended Tofts model is the same model name but with inference of Vp
        if options["model"] == "dce_ETM":
            options["model"] = "dce_tofts"
            options["infer-vp"] = True

        # T1 map is an image prior
        if "t1" in options:
            options.update({
                "PSP_byname1" : "t10",
                "PSP_byname1_type" : "I",
                "PSP_byname1_image" : options.pop("t1")
            })
            if not options["infer-t10"]:
                # To treat the image prior as ground truth need to put T10
                # into the model but give the image prior a high precision so
                # the parameter doesn't actually have any freedom to vary
                options["infer-t10"] = True
                options["PSP_byname1_prec"] = 1e6

        # Delay time to include injection time for population AIF
        if "tinj" in options:
            options["delay"] = options["delay"] + options.pop("tinj")

        # Times in minutes and TR in s
        options["delt"] = options["delt"] / 60
        options["delay"] = options["delay"] / 60
        options["tr"] = options["tr"] / 1000

        # Spatial mode
        if options.pop("spatial", False):
            options["method"] = "spatialvb"
            options["param-spatial-priors"] = "M+"

        return {
            "Fabber" : options
        }
