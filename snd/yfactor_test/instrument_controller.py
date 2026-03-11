#attempting to make uniform wrappers for virtual instruments
#SND 09/23/2022

import functools
import os
import sys
sys.path.append(r'W:/durant/Python3/pretesting_branch/vdi_ssp/')

import pandas as pd
import numpy as np
import warnings
import time
import pyvisa

#for printing exception
import traceback

#grouping imports by function
#sources
#from util.vi.agilent_signal_generator import PSG
from util.vi.vdi_synth import PhysicalSynth
from util.vi.network_analyzer import PNA #this is really a source and receiver
from util.vi.keithley_smu import SMU_K2611B
from util.vi.HP6627A import PhysicalPSU

#analog daqs
from util.vi.ni_daq_usb import DAQ, DAQStream
from util.vi.vdi_daq import RFDAQ, PhysicalVDAQ
#VDI DAQs both made by Dave Kurtz
#the RF DAQ is 8 analog output channels with floating ground
#the VDAQ is 8 analog output channels and two analog input channels

#measurement devices
from util.vi.vdi_power_meter import PM5
from util.vi.agilent_signal_analyzer import PXA
from util.vi.agilent_power_meter import E4419B
from util.vi.vdi_fcounter import PhysicalFC
from util.vi.zh_lockin import ZHInst

class PSG():
    #Power limit in dbm, 15 by default
    def __init__(self, powerlimit=20, add='SGX', **kwargs):
        rm = pyvisa.ResourceManager()
        
        if type(add) == int:
            add = f'GPIB::{add}'
        self.inst = rm.open_resource(add)
        
        self._powerlim = powerlimit
        self.power_off()
        self.preset()

    #Property functions used to easily set and read frequency in GHz
    def set_frequency(self,frequency):
        self.inst.write(":FREQ %s GHZ" %(frequency))
    def get_frequency(self):
        return self.inst.ask_for_values(":FREQ?")[0]/1e9

    #Property functions used to easily set and read power in dBm
    def set_power(self,power):
        if self._powerlim < power:
            self.inst.write(":AMPL %s DBM" %(self._powerlim))
        else:
            self.inst.write(":AMPL %s DBM" %(power))
    def get_power(self):
        return self.inst.ask_for_values(":AMPL?")[0]

    #Creating properties so that settings can be treated like variables
    frequency=property(get_frequency,set_frequency)
    power = property(get_power,set_power)

    def power_on(self):
        self.inst.write(":OUTP 1")

    def power_off(self):
        self.inst.write(":OUTP 0")

    def freq_mult(self,mult):
        self.inst.write(":FREQ:MULT %s"%(mult))

    def preset(self):
        self.inst.write("*RST")      


def no_warnings(func):
    """
    Decorator function to silence warnings.
    https://realpython.com/primer-on-python-decorators/
    """
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return func(*args, **kwargs)
    return wrapper

class PSGWrapper(PSG):
    """
    This shouldn't be instantiated directly.
    Controller for PSG and MXG.
    Communicates via GPIB.

    Parameters
    ----------
    powerlimit : int (dBm)
        You will be unable to set power above this limit.
    address : int
        GPIB address of the MXG or PSG.

    See Also
    --------
    Source : factory class
    """
    def __init__(self, powerlimit=20, address=20, **kwargs):
        super(PSGWrapper, self).__init__(powerlimit = powerlimit, add=address)
    def set_f(self, freq):
        #frequency is in GHz
        self.set_frequency(freq)
    def set_p(self, power):
        #power in dBm
        self.set_power(power)
    def p_on(self):
        self.power_on()
    def p_off(self):
        self.power_off()

class SynthWrapper(PhysicalSynth):
    """
    This shouldn't be instantiated directly.
    Controller for VDI Synthesizers.
    Communicates via FTDI (USB).

    Parameters
    ----------
    address : string
        Serial number of the synthesizer.

    See Also
    --------
    Source : factory class
    """
    def __init__(self, address='vdis0017', **kwargs):
        self.address = address
    def set_f(self, freq):
        super(SynthWrapper, self).__init__(self.address)
        #frequency is in GHz
        self.set_frequency(freq)
        self.close()

class PNASourceWrapper(PNA):
    """
    This shouldn't be instantiated directly.
    Controls one PNA source to mimic a Keysight synthesizer.
    Communicates via GPIB.

    Parameters
    ----------
    address : int
        GPIB address of the PNA.
    port : int
        Number of port. Can be 1, 2, 3, or 4.
    timeout_ms : int
        Timeout value.
    preset : bool
        Whether to preset the instrument on initialization.

    See Also
    --------
    Source : factory class
    """
    def __init__(self, address=16, port=1, timeout_ms=5000, preset=True, **kwargs):
        super(PNASourceWrapper, self).__init__(address=address, timeout_ms=timeout_ms)
        if preset:
            self.preset()
            self.set_sweep_type('CW')
            self.pow_couple()
        self.port = port
    def set_f(self, freq):
        #frequency in GHz
        self.set_frequency_cw(freq*1e9)
    def set_p(self, power):
        self.pow_ampl(power, self.port)
    def p_on(self):
        self.pow_mode('ON',self.port)
    def p_off(self):
        self.pow_mode('OFF',self.port)

class CurrentSource(SMU_K2611B):
    """
    This shouldn't be instantiated directly.
    Controls Keithley SMU K2611B to source current.

    Parameters
    ----------
    address : int
        GPIB address of the Keithley SMU.
    preset : bool
        Whether to preset on connection.

    See Also
    --------
    Source : factory class
    """
    def __init__(self, address = 11, preset=True, **kwargs):
        super(CurrentSource, self).__init__(address=f'GPIB0::{address}')
        if preset:
            self.inst.write('display.screen = display.SMUA')
            self.inst.write('display.smua.measure.func = display.MEASURE_DCAMPS')
            self.inst.write('smua.measure.autorangei = smua.AUTORANGE_ON')
            self.inst.write('smua.source.func = smua.OUTPUT_DCAMPS')

    #current in amps
    def set_i(self, current_a):
        self.inst.write(f'smua.source.leveli = {current_a}')

    def p_on(self):
        self.setsourceOn()

    def p_off(self):
        self.setsourceOff()

class VoltageSource(SMU_K2611B):
    """
    This shouldn't be instantiated directly.
    Controls Keithley SMU K2611B to source voltage.

    Parameters
    ----------
    address : int
        GPIB address of the Keithley SMU.
    preset : bool
        Whether to preset on connection.

    See Also
    --------
    Source : factory class
    """
    def __init__(self, address = 11, preset=True, **kwargs):
        super(VoltageSource, self).__init__(address=f'GPIB0::{address}')
        if preset:
            self.inst.write('display.screen = display.SMUA')
            self.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS')
            self.inst.write('smua.measure.autorangev = smua.AUTORANGE_ON')
            self.inst.write('smua.source.func = smua.OUTPUT_DCVOLTS')

    def set_v(self, voltage_v):
        self.inst.write(f'smua.source.levelv = {voltage_v}')

    def p_on(self):
        self.setsourceOn()

    def p_off(self):
        self.setsourceOff()    

class PSUWrapper(PhysicalPSU):
    """
    This shouldn't be instantiated directly.
    Controls one channel of HP6627A to source voltage or current.

    Parameters
    ----------
    address : int
        GPIB address of the HP6627A.
    channel : int
        Which channel to control. (1, 2, 3, or 4).

    See Also
    --------
    Source : factory class
    """
    def __init__(self, address=5, channel=1, **kwargs):
        super(PSUWrapper, self).__init__(address=f"GPIB0::{address}::INSTR",**kwargs)
        self.channel = channel
    def set_i(self, current_a):
        self.set_currdef(self.channel, current_a)
    def set_v(self, voltage_v):
        self.set_voltdef(self.channel, voltage_v)
    def p_on(self):
        self.set_output(self.channel,1)
    def p_off(self):
        self.set_output(self.channel,0)
        

class NIDAQSource(DAQ):
    """
    This shouldn't be instantiated directly.
    Controls NI USB-6361 DAQ to source voltage from a single channel.

    Parameters
    ----------
    address : string
        Device name of the NI DAQ. Can be found in NI-MAX Software.
    channel : int
        Which channel to source from. Can be 0 or 1, corresponding to AO0 and AO1.

    See Also
    --------
    Source : factory class
    """
    def __init__(self, address = 'Dev1', channel = 0, **kwargs):
        super(NIDAQSource, self).__init__(name=address, **kwargs)
        self.channel = channel

    def set_v(self, voltage_v):
        self.set_voltage(voltage_v, self.channel)

class VDAQSource(PhysicalVDAQ):
    """
    This shouldn't be instantiated directly.
    Controls VDI RFVDAQ to source voltage from a single channel.
    Note this doesn't work with the VDI RFDAQ.

    Parameters
    ----------
    address : string
        Serial number of the VDI RFVDAQ.
    channel : int
        Which channel to source from. Can be 0 or 1, corresponding to AO0 and AO1.

    See Also
    --------
    Source : factory class
    """
    def __init__(self, address = 'RFVDAQ11', channel = 0, **kwargs):
        super(VDAQSource, self).__init__(sn=address)#, **kwargs)
        self.channel = channel

    def set_v(self, voltage_v):
        self.write_voltage(self.channel, voltage_v)

class Source:
    """
    Factory class for instantiating a variety of virtual instruments.
    In order to generalize the interface between multiple devices some devices lose specialized functionality.
    You can always use the ``Ancestor`` class directly instead of using this library.

    Parameters
    ----------
    insttype: string
        Chooses which class to instantiate.

        - ``"psg"``: PSGWrapper
        - ``"synth"``: SynthWrapper
        - ``"pnasource:"`` PNASourceWrapper
        - ``"keithley_i"``: CurrentSource
        - ``"keithley_v"``: VoltageSource
        - ``"hp6627"``: PSUWrapper
        - ``"nidaq"``: NIDAQSource
        - ``"vdaq"``: VDAQSource
        
    address : varies
        See related documentation per ``insttype`` for arguments. Some source types will require other ``kwargs``.
    dummy : bool
        Use ``dummy=False`` to make a fake instrument when debugging code.
        The instrument will not be instantiated and function calls will print to command line instead of executing.

    See Also
    --------
    PSGWrapper
    SynthWrapper
    PNASourceWrapper
    CurrentSource
    VoltageSource
    PSUWrapper
    NIDAQSource
    VDAQSource
    """
    _types = {
        "psg": PSGWrapper,
        "synth": SynthWrapper,
        "pnasource":PNASourceWrapper,
        "keithley_i":CurrentSource,
        "keithley_v":VoltageSource,
        "hp6627":PSUWrapper,
        "nidaq":NIDAQSource,
        "vdaq":VDAQSource,
        }
    def __init__(self, insttype, address, dummy=False, **kwargs):
        self.type = insttype
        if not self._types.get(insttype):
            raise ValueError(f'source instrument type {insttype} does not exist')
        #try:
        self.dummy=dummy

        try:
            self.inst = self._types[insttype](address=address, dummy=dummy, **kwargs)
        except Exception as e:
            if self.dummy:
                self.inst = None
            else:
                traceback.print_exc()

    def __repr__(self):
        return self.type

        #except:
        #    warnings.warn(f'could not connect to source type {insttype} at address {address}', stacklevel=2)
        #    self.inst = None

    def _dummy_decorator(func):
        @functools.wraps(func) #this decorator actually just passes through the docstrings or something
        def wrapper(self, *args, **kwargs):
            if not self.dummy:
                func(self, *args, **kwargs)
            else:
                print(f'{self},  function: {func.__name__},  args: {args},  kwargs: {kwargs}')

        return wrapper

    @_dummy_decorator
    def set_frequency(self, freq):
        if hasattr(self.inst, "set_f"):
            self.inst.set_f(freq)

    @_dummy_decorator
    def set_power(self, power):
        if hasattr(self.inst, "set_p"):
            self.inst.set_p(power)

    @_dummy_decorator
    def set_current(self, current_a):
        if hasattr(self.inst, "set_i"):
            self.inst.set_i(current_a)

    @_dummy_decorator
    def set_voltage(self, voltage_v):
        if hasattr(self.inst, "set_v"):
            self.inst.set_v(voltage_v)

    @_dummy_decorator
    def power_on(self):
        if hasattr(self.inst, "p_on"):
            self.inst.p_on()

    @_dummy_decorator
    def power_off(self):
        if hasattr(self.inst, "p_off"):
            self.inst.p_off()

class PXAPeakSearch(PXA):
    """
    This shouldn't be instantiated directly.

    Parameters
    ----------
    address : int
        GPIB address of the EXA, MXA, or PXA.
    preset : bool
        Whether to preset on instantiation.

    See Also
    --------
    Receiver : factory class
    """
    def __init__(self, address=18, preset=False, **kwargs):
        super(PXAPeakSearch, self).__init__(address=address, preset=preset, use_cf=False, **kwargs)
    def get_data(self):
        """
        This just peak searches and returns a tuple ``(freq, value)``.
        User has to set up the PXA manually.
        """
        self.trigger_once()
        self.send_opcheck()
        return self.peak_search()

class PM5Wrapper(PM5):
    """
    This shouldn't be instantiated directly.

    Parameters
    ----------
    address : string
        Serial number of PM4 or PM5.

    See Also
    --------
    Receiver : factory class
    """

    def __init__(self, address='123V', dummy=False, **kwargs):
        #super(PM5Wrapper, self).__init__(serial=address, **kwargs)
        self.address = address
        self.kw = kwargs
    def get_data(self):
        """
        Connects to the device, returns power in mW, and then disconnects.
        """
        super(PM5Wrapper, self).__init__(serial=self.address, **self.kw)

        #power in mW because sometimes it goes negative
        power = self.get_power()

        self.close()
        return power

class E4419BWrapper(E4419B):
    """
    This shouldn't be instantiated directly.
    Controls one channel of E4419B or N1913A.

    Parameters
    ----------
    address : int
        GPIB Address of the device.
    channel : int
        Channel can be ``1`` (corresponds to A) or ``2`` (corresponds to B)

    See Also
    --------
    Receiver : factory class
    """
    def __init__(self, address=13, channel=1, **kwargs):
        super(E4419BWrapper, self).__init__(address=address, **kwargs)
        self.set_units('DBM')
        self.channel=channel
    def get_data(self):
        """
        returns power in dBm
        """
        return self.get_power(channel=self.channel)

class FreqCounterWrapper(PhysicalFC):
    """
    This shouldn't be instantiated directly.
    Controls the VDI Frequency Counter via FTDI (USB).

    Parameters
    ----------
    address : string
        Serial number of the  device.

    See Also
    --------
    Receiver : factory class
    """
    def __init__(self, address='VDIF001', **kwargs):
        self.address = address
    def get_data(self):
        """
        returns frequency in GHz
        """
        super(FreqCounterWrapper, self).__init__(sn=self.address)
        freq = self.read_frequency()
        self.close()
        return freq

class ZurichLockin(ZHInst):
    """
    This shouldn't be instantiated directly.
    Controls the Zurich Instruments Lockin via USB.
    Need to first install the zurich software for this to work.

    Parameters
    ----------
    address : string
        Serial number of the  device.
    n_avgs : int
        Number of averages per ``get_data``\
    samp_rate : int
        Sample Rate = 60MHz / 2**``samp_rate``.
        For example 13 = 60MHz / 2**13 = 7.32KHz
    n_points : int
        Number of Points, can be 4092, 8184, or 16368.
    See Also
    --------
    Receiver : factory class
    """
    def __init__(self, address = 'dev6017', n_avgs = 1, samp_rate = 13, n_points = 4092, dummy=False, **kwargs):
        super(ZurichLockin, self).__init__(device=address, **kwargs)
        self.configLockin(samp_rate, n_points)
        self.numavgs = n_avgs

    def get_data(self):
        """
        returns a tuple ``(np.mean(DC), np.mean(AC), np.mean(Y), np.mean(Tsys))``
        """
        return self.takePoint(n=self.numavgs)
        #return(np.mean(DC),np.mean(AC),np.mean( Y),np.mean(Tsys))

    def auto_scale(self):
        self.autoScale()

class NIDAQRx(DAQ):
    """
    This shouldn't be instantiated directly.
    Controls NI USB-6361 DAQ to read voltage from a single channel.

    Parameters
    ----------
    address : string
        Device name of the NI DAQ. Can be found in NI-MAX Software.
    channel : int
        Which channel to read from. Can be 0 through 7, corresponding to AI0 through AI7.

    See Also
    --------
    Receiver : factory class
    """
    def __init__(self, address = 'Dev1', channel = 0, **kwargs):
        super(NIDAQRx, self).__init__(name=address, **kwargs)
        self.channel = channel

    def get_data(self):
        """
        returns a voltage
        """
        return self.get_voltage(self.channel)

class VDAQRx(PhysicalVDAQ):
    """
    This shouldn't be instantiated directly.
    Controls VDI RFVDAQ to source voltage from a single channel.
    Note this doesn't work with the VDI RFDAQ.

    Parameters
    ----------
    address : string
        Serial number of the VDI RFVDAQ.
    channel : int
        Which channel to source from. Can be 0 through 7, corresponding to AI0 through AI7.
    scale : int
        Sets the channel range.

        - ``1``: +/-2.5V
        - ``2``: +/-5V
        - ``3``: +/-10V

    See Also
    --------
    Receiver : factory class
    """

    def __init__(self, address = 'RFVDAQ11', channel = 0, scale=3, **kwargs):
        super(VDAQRx, self).__init__(sn=address, **kwargs)
        self.channel = channel
        self.scale = scale

    def get_data(self):
        """
        returns a voltage
        """
        return self.get_data(self.channel, self.scale)

class PNARx(PNA):
    """
    This shouldn't be instantiated directly.
    Save data from a PNA. Standard use would be PNA set up manually ahead of time, and use ``preset=False``.

    Parameters
    ----------
    address : int
        GPIB Address of the PNA.
    timeout_ms : int
        Timeout value in milliseconds.
    preset : bool
        Whether to preset on instantiation.

    See Also
    --------
    Receiver : factory class
    """

    def __init__(self, address=16, timeout_ms=5000, preset=False, **kwargs):
        super(PNARx, self).__init__(address=address, timeout_ms=timeout_ms)
        if preset:
            self.preset()
    def get_data(self):
        """
        returns a dictionary

            - key: measurement name
            - data: 2d array
        """
        data = {}
        self.sweep()
        for name,parm in self.get_meas_list():
            self.select_meas(name)
            data[name]=self.get_rdata()
        return data

class PSUCurrentRx(PhysicalPSU):
    """
    This shouldn't be instantiated directly.
    Save current from one channel of a HP6627.

    Parameters
    ----------
    address : int
        GPIB Address of the PSU.
    channel : int
        Which channel to read (1, 2, 3, or 4).

    See Also
    --------
    Receiver : factory class
    """

    def __init__(self, address=5, channel=1, **kwargs):
        super(PSUCurrentRx, self).__init__(address=f"GPIB0::{address}::INSTR",**kwargs)
        self.channel = channel

    def get_data(self):
        """
        return a current value
        """
        return self.get_currout(channel=self.channel)

class NIDAQStream(DAQStream):
    """
    This shouldn't be instantiated directly.
    Controls NI USB-6361 DAQ to read voltages simultaneously from multiple channels.

    Parameters
    ----------
    address : string
        Device name of the NI DAQ. Can be found in NI-MAX Software.
    samp_rate : int
        Number of samples per second. Maximum 10e6 and reduces the more channels you use at once.
    test_duration : float
        Number of seconds of data to acquire when ``get_data`` is called.
    channels : list of strings
        List of channels to use. For example ``['ai0','ai1',ai2']``.

        Possible values ``ai0`` through ``ai7``.

        Note: ``len(ranges)`` must equal ``len(channels)``.
    ranges : list of floats
        List of ranges for each channel. For example ``[0.1, 5.0, 10.0]``.

        Possible values ``[0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]``

        Note: ``len(ranges)`` must equal ``len(channels)``.

    See Also
    --------
    Receiver : factory class
    """

    def __init__(self, address= 'Dev1', samp_rate=1e3, test_duration=1, channels=['ai0'], ranges=[10.0], **kwargs):
        super(NIDAQStream, self).__init__(devicename=address,
            sample_rate=samp_rate,
            test_duration=test_duration,
            channels=channels,
            ranges=ranges, **kwargs)

        print('test2')

    def get_data(self):
        #this returns a dataframe, index is time
        self.reset_measurement()
        
        data = self.start_multichan_test()
        
        return data

class TC08:
    """
    This shouldn't be instantiated directly.
    Save temperature from multiple channels of TC08

    Parameters
    ----------
    address : idk
        tbd
    channels : list
        Which channels to read. Takes about 100ms per channel.

        Example: ``[0,1,2]``


    See Also
    --------
    Receiver : factory class
    """

    def __init__(self, address='something', channels=[0,1], **kwargs):
        pass

    def get_data(self):
        """
        return a list of temperatures, one for each active channel.
        """
        out = [np.random.randint(50,100) for k in range(len(channels))]
        return out

class Receiver:
    """
    Factory class for instantiating a variety of virtual instruments.
    In order to generalize the interface between multiple devices some devices lose specialized functionality.
    You can always use the ``Ancestor`` class directly instead of using this library.

    Parameters
    ----------
    insttype: string
        Chooses which class to instantiate.

        - ``"pxa_peak"``: PXAPeakSearch
        - ``"pm5"``: PM5Wrapper
        - ``"e4419b:"`` E4419BWrapper
        - ``"fcounter"``: FreqCounterWrapper
        - ``"zurich"``: ZurichLockin
        - ``"nidaq"``: NIDAQRx
        - ``"vdaq"``: VDAQRx
        - ``"nistream"``: NIDAQStream
        - ``"pnareceiver"``: PNARx
        - ``"psurx_current"``: PSUCurrentRx
        - ``"tc08"``: TC08
        
    address : varies
        See related documentation per ``insttype`` for arguments. Some receiver types will require other ``kwargs``.
    dummy : bool
        Use ``dummy=False`` to make a fake instrument when debugging code.
        The instrument will not be instantiated and function calls will print to command line instead of executing.

    See Also
    --------
    PXAPeakSearch
    PM5Wrapper
    E4419BWrapper
    FreqCounterWrapper
    ZurichLockin
    NIDAQRx
    VDAQRx
    NIDAQStream
    PNARx
    PSUCurrentRx
    TC08
    """
    _types = {
        "pxa_peak": PXAPeakSearch, 
        'pm5': PM5Wrapper,
        'e4419b': E4419BWrapper,
        'fcounter': FreqCounterWrapper,
        'zurich': ZurichLockin,
        'nidaq': NIDAQRx,
        'vdaq': VDAQRx,
        'nistream': NIDAQStream,
        'pnareceiver': PNARx,
        'psurx_current': PSUCurrentRx,
        'tc08': TC08,
        }
    def __init__(self, insttype = "pxa_peak", address = 18, dummy=False,**kwargs):
        self.type=insttype
        self.add = address

        if not self._types.get(insttype):
            raise ValueError(f'receiver instrument type {insttype} does not exist', stacklevel=2)

        self.dummy=dummy

        try:
            self.inst = self._types[insttype](address=address, dummy=dummy, **kwargs)
        except Exception as e:
            if self.dummy:
                self.inst = None
            else:
                traceback.print_exc()

    def __repr__(self):
        return f'{self.type} @ {self.add}'

        #except:
        #    warnings.warn(f'could not connect to source type {insttype} at address {address}', stacklevel=2)
        #    self.inst = None

    def _dummy_decorator(func):
        @functools.wraps(func) #this decorator actually just passes through the docstrings or something
        def wrapper(self, *args, **kwargs):
            if not self.dummy:
                return func(self, *args, **kwargs)
            else:
                print(f'{self},  function: {func.__name__},  args: {args},  kwargs: {kwargs}')
                #just return a random float for some reason
                if func.__name__ == 'get_data':
                    return np.random.random_sample()*10
                # elif func.__name__ == 'get_datas':
                #     return pd.DataFrame(np.random.random_sample((self.inst.num_samples,self.inst.num_channels))*10,columns=self.inst.my_channels)

        return wrapper

    @_dummy_decorator
    def get_data(self):
        if hasattr(self.inst, 'get_data'):
            return self.inst.get_data()

    #a second get_data function that returns more than one value
    #I guess normally this will return a dataframe, for uniformity?
    # @_dummy_decorator
    # def get_datas(self):
    #     if hasattr(self.inst, 'get_datas'):
    #         return self.inst.get_datas()

class TestAllDevices:
    def __init__(self, **kwargs):
        self.source = Source("psg", address=20)
        self.source = Source("synth", address="VDIS001")
        self.source = Source("pnasource", address=16, port=1)
        self.source = Source("keithley_i", address=11)
        self.source = Source("keithley_v", address=11)
        self.source = Source("hp6627", address=5, channel=1)
        self.source = Source("nidaq", address="Dev1", channel=0)

        self.rx = Receiver("pxa_peak", address=18)
        self.rx = Receiver("pm5", address="123V")
        self.rx = Receiver("e4419b", address=13, channel=1)
        self.rx = Receiver("fcounter", address="VDIF001")
        self.rx = Receiver("zurich", address="dev6017", n_avgs=3)
        self.rx = Receiver("nidaq", address="Dev1", channel=0)

class Test:
    def __init__(self, **kwargs):
        self.source1 = Source("hp6627", address=5, channel=1)
        self.source1.set_voltage(5)
        self.source1.set_current(1)
        self.source1.power_on()
        time.sleep(5)

class ExampleTest:
    def __init__(self, **kwargs):
        #self.source = Source(insttype = "pnasource", address=16, port=1)
        self.source = Source(insttype = "psg", address=20)
        self.receiver = Receiver(insttype = "pxa_peak", address=18)
        #self.receiver = Receiver(insttype = "e4419b", address=13)
        self.pm = Receiver(insttype = 'pm5', address='321V')
        
        self.sweep(10, 15, 11)

    def sweep(self, fstart, fstop, n_points, sleeptime=0.1):
        rfs = np.linspace(fstart, fstop, n_points)

        self.source.power_on()

        for k in rfs:
            self.source.set_frequency(k)
            time.sleep(sleeptime)
            test1 = self.receiver.get_data()
            test2 = self.pm.get_data()

        self.source.power_off()


#by using this @no_warnings above a function you can suppress the warnings
#this makes errors printout get screwed up though, use at your own risk
#maybe ill clean this up later so it passes errors through somehow
class TestWithoutWarnings:
    @no_warnings
    def __init__(self):
        self.source = Source(insttype = "psg", address=1)
        self.receiver = Receiver(insttype = "pxa_peak", address=2)

    @no_warnings
    def do_stuff(self):
        self.source.power_on()
        self.receiver.get_data()
