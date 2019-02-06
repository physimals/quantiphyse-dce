"""
Quantiphyse - Analysis process for DCE-MRI modelling

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import logging
import traceback

import numpy as np

from quantiphyse.utils import QpException
from quantiphyse.processes import Process

from .pk_model import PyPk

LOG = logging.getLogger(__name__)

def _run_pk(worker_id, queue, data, t1, r1, r2, delt, injt, tr1, te1, dce_flip_angle, dose, model_choice):
    """
    Simple function to run the c++ pk modelling code. Must be a function to work with multiprocessing
    """
    try:
        log = "PkModelling\n-----------\n"
        times = np.arange(0, data.shape[-1])*delt
        # conversion to minutes
        times = times/60.0

        injtmins = injt/60.0
        Dose = dose

        # conversion to seconds
        dce_TR = tr1/1000.0
        dce_TE = te1/1000.0

        #specify variable upper bounds and lower bounds
        ub = [10, 1, 0.5, 0.5]
        lb = [0, 0.05, -0.5, 0]

        # contiguous array
        data = np.ascontiguousarray(data, dtype=np.double)
        t1 = np.ascontiguousarray(t1, dtype=np.double)
        times = np.ascontiguousarray(times)
        if len(data) == 0:
            raise QpException("Pk Modelling - no unmasked data found!")

        Pkclass = PyPk(times, data, t1)
        Pkclass.set_bounds(ub, lb)
        Pkclass.set_parameters(r1, r2, dce_flip_angle, dce_TR, dce_TE, Dose)

        # Initialise fitting
        # Choose model type and injection time
        log += Pkclass.rinit(model_choice, injtmins).decode('utf-8')

        # Iteratively process 5000 points at a time
        size_step = max(1, np.around(data.shape[0]/5))
        size_tot = data.shape[0]
        steps1 = np.around(size_tot/size_step)
        num_row = 1.0  # Just a placeholder for the meanwhile

        log += "Number of voxels per step: %i\n" % size_step
        log += "Number of steps: %i\n" % steps1
        queue.put((num_row, 1))
        for ii in range(int(steps1)):
            if ii > 0:
                progress = float(ii) / float(steps1) * 100
                queue.put((num_row, progress))

            log += Pkclass.run(size_step).decode('utf-8')

        # Get outputs
        res1 = np.array(Pkclass.get_residual())
        fcurve1 = np.array(Pkclass.get_fitted_curve())
        params2 = np.array(Pkclass.get_parameters())

        # final update to progress bar
        queue.put((num_row, 100))
        return worker_id, True, (res1, fcurve1, params2, log)
    except:
        traceback.print_exc()
        return worker_id, False, sys.exc_info()[1]

class PkModellingProcess(Process):
    """
    Process which does DCE Pk modelling using the Tofts model and a choice of 
    population AIFs
    """

    PROCESS_NAME = "PkModelling"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, worker_fn=_run_pk, **kwargs)
        self.suffix = ""
        self.thresh = 0
        self.roi = None
        self.baseline = None
        self.grid = None
        self.nvols = 1
        
    def run(self, options):
        data = self.get_data(options)
        if data.ndim != 4: 
            raise QpException("Data must be 4D for DCE PK modelling")

        roi = self.get_roi(options, data.grid)
    
        self.suffix = options.pop('suffix', '')
        if self.suffix != "": self.suffix = "_" + self.suffix

        t1_name = options.pop("t1", "T10")
        if t1_name not in self.ivm.data:
            raise QpException("Could not find T1 map: %s" % t1_name)
        t1 = self.ivm.data[t1_name].resample(data.grid)

        R1 = options.pop('r1')
        R2 = options.pop('r2')
        DelT = options.pop('dt')
        InjT = options.pop('tinj')
        TR = options.pop('tr')
        TE = options.pop('te')
        FA = options.pop('fa')
        self.thresh = options.pop('ve-thresh')
        Dose = options.pop('dose', 0)
        model_choice = options.pop('model')

        # Baseline defaults to time points prior to injection
        baseline_tpts = int(1 + InjT / DelT)
        self.log("First %i time points used for baseline normalisation\n" % baseline_tpts)
        baseline = np.mean(data.raw()[:, :, :, :baseline_tpts], axis=-1)

        self.grid = data.grid
        self.nvols = data.nvols
        self.roi = roi.raw()
        data_vec = data.raw()[self.roi > 0]
        t1_vec = t1.raw()[self.roi > 0]
        self.baseline = baseline[self.roi > 0]

        # Normalisation of the image - convert to signal enhancement
        data_vec = data_vec / (np.tile(np.expand_dims(self.baseline, axis=-1), (1, data.nvols)) + 0.001) - 1

        args = [data_vec, t1_vec, R1, R2, DelT, InjT, TR, TE, FA, Dose, model_choice]
        self.start_bg(args)

    def timeout(self, queue):
        if queue.empty(): return
        while not queue.empty():
            _, progress = queue.get()
        self.sig_progress.emit(float(progress)/100)

    def finished(self, worker_output):
        """
        Add output data to the IVM
        """
        if self.status == Process.SUCCEEDED:
            # Only one worker - get its output
            var1 = worker_output[0]
            self.log(var1[3])

            # Params: Ktrans, ve, offset, vp
            ktrans = np.zeros(self.grid.shape)
            
            ktrans[self.roi > 0] = var1[2][:, 0] * (var1[2][:, 0] < 2.0) + 2 * (var1[2][:, 0] > 2.0)

            ve = np.zeros(self.grid.shape)
            ve[self.roi > 0] = var1[2][:, 1] * (var1[2][:, 1] < 2.0) + 2 * (var1[2][:, 1] > 2.0)
            ve *= (ve > 0)

            kep = ktrans / (ve + 0.001)
            kep[np.logical_or(np.isnan(kep), np.isinf(kep))] = 0
            kep *= (kep > 0)
            kep = kep * (kep < 2.0) + 2 * (kep >= 2.0)

            offset = np.zeros(self.grid.shape)
            offset[self.roi > 0] = var1[2][:, 2]

            vp = np.zeros(self.grid.shape)
            vp[self.roi > 0] = var1[2][:, 3]

            # Convert signal enhancement back to data curve
            sig = (var1[1] + 1) * (np.tile(np.expand_dims(self.baseline, axis=-1), (1, self.nvols)))
            estimated = np.zeros(list(self.grid.shape) + [self.nvols,])
            estimated[self.roi > 0] = sig

            # Thresholding according to upper limit
            p = np.percentile(ktrans, self.thresh)
            ktrans[ktrans > p] = p
            p = np.percentile(kep, self.thresh)
            kep[kep > p] = p

            self.ivm.add(ktrans, name='ktrans' + self.suffix, grid=self.grid, make_current=True)
            self.ivm.add(ve, name='ve' + self.suffix, grid=self.grid)
            self.ivm.add(kep, name='kep' + self.suffix, grid=self.grid)
            self.ivm.add(offset, name='offset' + self.suffix, grid=self.grid)
            self.ivm.add(vp, name='vp' + self.suffix, grid=self.grid)
            self.ivm.add(estimated, name="model_curves" + self.suffix, grid=self.grid)
            