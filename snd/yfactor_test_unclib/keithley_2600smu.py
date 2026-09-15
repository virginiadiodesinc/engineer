import pyvisa
import time
import numpy as np

class SMU_K2611B():
    #GPIB address 18 by default
    def __init__(self, address, **kwargs):

        address_string = f'GPIB0::{address}::INSTR'

        rm = pyvisa.ResourceManager()
        self.inst = rm.open_resource(address_string)

        self.initialize()


    def initialize(self):
        self.inst.write('display.screen = display.SMUA')
        self.inst.write('format.data = format.ASCII')
        self.inst.write('smua.nvbuffer1.clear()')
        self.inst.write('smua.nvbuffer1.appendmode = 1')
        self.inst.write('smua.nvbuffer1.collectsourcevalues = 1')
        self.inst.write('smua.measure.count = 1')       

    def initialize_iv(self):
        self.inst.write("smua.measure.delay = smua.DELAY_AUTO")
        self.inst.write("smua.measure.nplc = 1")
        self.inst.write("smua.measure.filter.count = 8")
        self.inst.write('smua.measure.filter.type = smua.FILTER_REPEAT_AVG')
        self.inst.write('smua.trigger.measure.v(smua.nvbuffer1)')
        self.inst.write('smua.trigger.measure.action = smua.ENABLE')
        self.inst.write('smua.measure.autorangei = smua.AUTORANGE_ON')
        self.set_mode_current_source()
        self.filter_on()

    def run_iv_tjr(self, compliance_v=1.2, start_amps=100e-9, stop_amps=1e-3, numpoints=30, dtime=0.05):
        irange = np.logspace(np.log10(start_amps),np.log10(stop_amps),numpoints)
        for ii in irange:
            self.inst.write(f'smua.source.leveli = {ii}')
            time.sleep(dtime)
            self.inst.write('smua.measure.v(smua.nvbuffer1)')
        
        # And back down
        for ii in reversed(irange):
            self.inst.write(f'smua.source.leveli = {ii}')
            time.sleep(dtime)
            self.inst.write('smua.measure.v(smua.nvbuffer1)')

    def get_iv_data(self):
        redvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
        srcvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')
        return srcvals,redvals

    def run_iv(self, compliance_v=1.2, start_amps=100e-9, stop_amps=1e-3, numpoints=30):
        self.initialize()
        self.initialize_iv()

        self.setsourceOn()
        self.set_voltage_limit(compliance_v)
        self.set_current_level(start_amps)
        self.set_current_sweep(start_amps, stop_amps, numpoints)
        self.inst.write(f'smua.trigger.count={numpoints}')

        self.trigger_init()

        #time.sleep(3) original code had this, I don't think it makes sense to be fixed.
        time.sleep(0.1*numpoints)

        source_values = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')
        measure_values = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')

        return source_values, measure_values

    def trigger_init(self):
        self.inst.write('smua.trigger.initiate()')

    def set_current_sweep(self, start_amps, stop_amps, numpoints):
        sweep_points = np.linspace(start_amps, stop_amps, numpoints)
        command = "{"
        for p in sweep_points:
            command+=f"{p}, "
        command = command[:-2] + "}"
        print(command)


        self.inst.write(f"smua.trigger.source.listi({command})")
        #self.inst.write(f"smua.trigger.source.logi({start_amps}, {stop_amps}, {numpoints})")

    def filter_on(self):
        self.inst.write('smua.measure.filter.enable = smua.FILTER_ON')

    def filter_off(self):
        self.inst.write('smua.measure.filter.enable = smua.FILTER_OFF')
    
    def reset(self):
        self.inst.write('smua.reset()')
        
    def setsourceOn(self):
        self.inst.write('smua.source.output = smua.OUTPUT_ON')
        
    def setsourceOff(self):
        self.inst.write('smua.source.output = smua.OUTPUT_OFF')

    def set_voltage_limit(self, Vmax):
        #voltage in volts
        self.inst.write(f'smua.source.limitv = {Vmax}')

    def set_current_limit(self, Imax):
        #current in amps
        self.inst.write(f'smua.source.limiti = {Imax}')

    def set_voltage_level(self, Vlevel):
        self.inst.write(f'smua.source.levelv = {Vlevel}')

    def set_current_level(self, Ilevel):
        self.inst.write(f'smua.source.leveli = {Ilevel}')

    def set_mode_current_source(self):
        self.inst.write('smua.source.func = smua.OUTPUT_DCAMPS')
        self.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS')
        self.inst.write('smua.source.autorangei = smua.AUTORANGE_ON')

    def set_mode_voltage_source(self):
        self.inst.write('smua.source.func = smua.OUTPUT_DCVOLTS')
        self.inst.write('display.smua.measure.func = display.MEASURE_DCAMPS')

    def add_current_reading_to_buffer(self):
        self.inst.write('smua.measure.i(smua.nvbuffer1)')

    def add_voltage_reading_to_buffer(self):
        self.inst.write('smua.measure.v(smua.nvbuffer1)')

    def read_value_buffer(self):
        vals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
        return vals

    def clear_value_buffer(self):
        self.inst.write('smua.nvbuffer1.clear()')

    def get_voltage(self):
        self.add_voltage_reading_to_buffer()
        val = self.read_value_buffer()[0]
        self.clear_value_buffer()
        return val

    def get_current(self):
        self.add_current_reading_to_buffer()
        val = self.read_value_buffer()[0]
        self.clear_value_buffer()
        return val

    # def takeIV(self, Imin=1e-9, Imax=1e-3, Vmax=1, numpts = 101, dtime=0.01):
    #     self.reset()
        
    #     self.inst.write('display.screen = display.SMUA')
    #     self.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS')
    #     self.inst.write('smua.measure.autorangei = smua.AUTORANGE_ON')
    #     self.inst.write('format.data = format.ASCII')
    #     self.inst.write('smua.nvbuffer1.clear()')
    #     self.inst.write('smua.nvbuffer1.appendmode = 1')
    #     self.inst.write('smua.nvbuffer1.collectsourcevalues = 1')
    #     self.inst.write('smua.measure.count = 1')
    #     self.inst.write('smua.source.func = smua.OUTPUT_DCAMPS')
    #     self.inst.write(f'smua.source.limitv = {Vmax}')
    
    #     self.inst.write(f'smua.source.leveli = {Imin}')
        
    #     self.setsourceOn()
    
    #     irange = np.logspace(np.log10(Imin),np.log10(Imax),numpts)
    #     for ii in irange:
    #         self.inst.write(f'smua.source.leveli = {ii}')
    #         time.sleep(dtime)
    #         self.inst.write('smua.measure.v(smua.nvbuffer1)')
        
    #     # And back down
    #     for ii in reversed(irange):
    #         self.inst.write(f'smua.source.leveli = {ii}')
    #         time.sleep(dtime)
    #         self.inst.write('smua.measure.v(smua.nvbuffer1)')        
    
    #     self.setsourceOff()

    #     # pull data from internal buffer
    #     redvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
    #     srcvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')
    
    #     df = pd.DataFrame({'Current (A)':srcvals[:numpts], 'Voltage Up (V)': redvals[:numpts], 
    #                        'Voltage Down (V)':[x for x in reversed(redvals[numpts:])]})
        
    #     df['Voltage avg (V)'] = (df['Voltage Up (V)']+df['Voltage Down (V)'])/2
        
    #     return(df)