"""
DSC Quantiphyse plugin

Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""
from quantiphyse.utils import get_local_shlib

from .widgets import DceWidget, FabberDceWidget

QP_MANIFEST = {
    "widgets" : [DceWidget,],
    "fabber-libs" : [get_local_shlib("fabber_models_dce", __file__)]
}
