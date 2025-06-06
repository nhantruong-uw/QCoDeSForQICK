# most of the drivers only need a couple of these... moved all up here for clarity below
import ctypes  # only for DLL-based instrument
import sys
import time
from typing import Unpack

import numpy as np

from qcodes import validators as vals
from qcodes.instrument import (
    Instrument,
    InstrumentBaseKWArgs,
    InstrumentChannel,
    VisaInstrument,
    VisaInstrumentKWArgs,
)
from qcodes.instrument_drivers.AlazarTech.utils import TraceParameter
from qcodes.parameters import ManualParameter, MultiParameter, Parameter

import qick

#for logging
# from qcodes.dataset.measurements import Measurement
# from qcodes.dataset import initialise_or_create_database_at, load_or_create_experiment

# for individual experiments

NAME = ""
IP_ADDR = ""

# Xilinx ZYNQ RFSoC
class ZynqRfsoc(VisaInstrument):
    """
    Qcodes driver for Zynq Rfsoc board
    """
    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__ By using Unpack[VisaKWArgs] we ensure that the instrument class takes exactly the same keyword args as the base class
    # Visa instruments are also required to take name, address and terminator as arguments.
    # name and address should be positional arguments. To overwrite the default terminator or timeout
    # the attribute default_terminator or default_timeout should be defined as a class attribute in the instrument class
    # as shown below for the default_terminator
    default_terminator = "\r"

    def __init__(self, config_path: str, name = NAME, ip_addr = IP_ADDR, **kwargs: "Unpack[VisaInstrumentKWArgs]"):
        super().__init__(name, ip_addr, **kwargs)
        
        # initialize qick hardware
        # config_path is path to .json file of layout of hardware; add later
        self.cfg = qick.QickConfig(config_path)
        self.soc = qick.SocProxy(ip_addr, self.cfg)

        # add a new parameter

        # add new functions for more operations as needed

    def close(self):
        """Properly close instrument connection."""
        self.soc.close()
        super().close()

    class Experiment1D:
        def __init__(self):
            print("Experiment1D")

        def Ramsey(self):
            print("Ramsey")
        
    class Experiment2D:
        def __init__(self):
            print("Experiment2D")