'''
TEST: Dummy instrument
'''
import numpy as np
import qcodes as qc

## Multidimensional scanning module
from qcodes.dataset import (
    LinSweep,
    Measurement,
    dond,
    experiments,
    initialise_or_create_database_at,
    load_by_run_spec,
    load_or_create_experiment,
    plot_dataset,
)

## Dummy instruments for generating synthetic data
from qcodes.instrument_drivers.mock_instruments import (
    DummyInstrument,
    DummyInstrumentWithMeasurement,
)

## Using interactive widget
from qcodes.interactive_widget import experiments_widget

# dummy signal gen with two gates
dac = DummyInstrument("dac", gates=["ch1", "ch2"])

# A dummy digital multimeter that generates a synthetic data depending
# on the values set on the setter_instr, in this case the dummy dac
dmm = DummyInstrumentWithMeasurement("dmm", setter_instr=dac)
# prints out
'''
dmm:
        parameter value
--------------------------------------------------------------------------------
IDN :   None 
v1  :   0 (V)
v2  :   0 (V)
'''

dmm.print_readable_snapshot()