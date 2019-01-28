"""
DSC Quantiphyse plugin

Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""
import os

from .widgets import DceWidget, FabberDceWidget
from .process import PkModellingProcess

QP_MANIFEST = {
    "processes" : [PkModellingProcess,],
    "widgets" : [DceWidget, FabberDceWidget],
    "fabber_dirs" : [os.path.dirname(__file__)],
}
