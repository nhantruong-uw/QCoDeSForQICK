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
        self.prog = None
        self._enabled_params = {}

        # add new functions for more operations as needed

    # makes parameters toggleable; inserting/deleting them too much can cause issues with the program
    def _add_toggleable_parameter(self, name, getter=None, setter=None, unit=None):
        self._enabled_params[name] = True

        def safe_get():
            if not self._enabled_params[name]:
                raise RuntimeError(f"Parameter '{name}' is disabled")
            return getter() if getter else None

        def safe_set(value):
            if not self._enabled_params[name]:
                raise RuntimeError(f"Parameter '{name}' is disabled")
            if setter:
                setter(value)

        self.add_parameter(
            name,
            get_cmd=safe_get,
            set_cmd=safe_set if setter else False,
            unit=unit
        )

    def enable_parameter(self, name: str):
        if name in self._enabled_params:
            self._enabled_params[name] = True
        else:
            raise KeyError(f"No such toggleable parameter '{name}'")

    def disable_parameter(self, name: str):
        if name in self._enabled_params:
            self._enabled_params[name] = False
        else:
            raise KeyError(f"No such toggleable parameter '{name}'")

    def close(self):
        """Properly close instrument connection."""
        self.soc.close()
        super().close()

    class SendReceivePulse:
        def __init__(self, parent: "ZynqRfsoc"):
            self.parent = parent
            self.cfg = parent.cfg
            self.soc = parent.soc
            self.prog = None

            # Register toggleable QCoDeS parameters from cfg
            self._add_toggleable_parameter("relax_delay", unit="us", getter=lambda: self.cfg["relax_delay"])
            self._add_toggleable_parameter("pulse_freq", unit="MHz", getter=lambda: self.cfg["pulse_freq"])
            self._add_toggleable_parameter("res_ch", getter=lambda: self.cfg["res_ch"])
            self._add_toggleable_parameter("ro_chs", getter=lambda: self.cfg["ro_chs"])

        def initialize(self):
            cfg = self.cfg
            prog = qick.Program(self.soc, cfg)
            res_ch = cfg["res_ch"]

            prog.declare_gen(ch=res_ch, nqz=1)

            for ch in cfg["ro_chs"]:
                prog.declare_readout(ch=ch, length=cfg["readout_length"],
                                     freq=cfg["pulse_freq"], gen_ch=res_ch)

            freq = prog.freq2reg(cfg["pulse_freq"], gen_ch=res_ch, ro_ch=cfg["ro_chs"][0])
            phase = prog.deg2reg(cfg["res_phase"], gen_ch=res_ch)
            gain = cfg["pulse_gain"]
            prog.default_pulse_registers(ch=res_ch, freq=freq, phase=phase, gain=gain)

            style = cfg["pulse_style"]
            if style in ["flat_top", "arb"]:
                sigma = cfg["sigma"]
                prog.add_gauss(ch=res_ch, name="measure", sigma=sigma, length=sigma * 5)

            if style == "const":
                prog.set_pulse_registers(ch=res_ch, style=style, length=cfg["length"])
            elif style == "flat_top":
                prog.set_pulse_registers(ch=res_ch, style=style, waveform="measure", length=cfg["length"])
            elif style == "arb":
                prog.set_pulse_registers(ch=res_ch, style=style, waveform="measure")

            prog.synci(200)
            self.prog = prog

        def body(self):
            cfg = self.cfg
            if self.prog is None:
                raise RuntimeError("Program not initialized")

            self.prog.measure(pulse_ch=cfg["res_ch"],
                              adcs=cfg["ro_chs"],
                              pins=[0],
                              adc_trig_offset=cfg["adc_trig_offset"],
                              wait=True,
                              syncdelay=self.prog.us2cycles(cfg["relax_delay"]))

        def run_and_upload(self):
            if self.prog is None:
                raise RuntimeError("Program not initialized")
            compiled = self.soc.compile(self.prog)
            self.soc.load_program(compiled)
            self.soc.run()