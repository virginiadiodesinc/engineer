#Class used to control the Agilent PXA
#CXS (5/14/2021) - Adapted from SND (1/28/2014)

import pyvisa
import time
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt

class SMU_K2611B():
    #GPIB address 18 by default
    def __init__(self, address, **kwargs):
        rm = pyvisa.ResourceManager()
        self.inst = rm.open_resource(address)
    
    def reset(self):
        self.inst.write('smua.reset()')
        
    def setsourceOn(self):
        self.inst.write('smua.source.output = smua.OUTPUT_ON')
        
    def setsourceOff(self):
        self.inst.write('smua.source.output = smua.OUTPUT_OFF')      
                
    def takeIV(self, Imin=1e-9, Imax=1e-3, Vmax=1, numpts = 101, dtime=0.01):
        self.reset()
        
        self.inst.write('display.screen = display.SMUA')
        self.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS')
        self.inst.write('smua.measure.autorangei = smua.AUTORANGE_ON')
        self.inst.write('format.data = format.ASCII')
        self.inst.write('smua.nvbuffer1.clear()')
        self.inst.write('smua.nvbuffer1.appendmode = 1')
        self.inst.write('smua.nvbuffer1.collectsourcevalues = 1')
        self.inst.write('smua.measure.count = 1')
        self.inst.write('smua.source.func = smua.OUTPUT_DCAMPS')
        self.inst.write(f'smua.source.limitv = {Vmax}')
    
        self.inst.write(f'smua.source.leveli = {Imin}')
        
        self.setsourceOn()
    
        irange = np.logspace(np.log10(Imin),np.log10(Imax),numpts)
        for ii in irange:
            self.inst.write(f'smua.source.leveli = {ii}')
            time.sleep(dtime)
            self.inst.write('smua.measure.v(smua.nvbuffer1)')
        
        # And back down
        for ii in reversed(irange):
            self.inst.write(f'smua.source.leveli = {ii}')
            time.sleep(dtime)
            self.inst.write('smua.measure.v(smua.nvbuffer1)')        
    
        self.setsourceOff()

        # pull data from internal buffer
        redvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
        srcvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')
    
        df = pd.DataFrame({'Current (A)':srcvals[:numpts], 'Voltage Up (V)': redvals[:numpts], 
                           'Voltage Down (V)':[x for x in reversed(redvals[numpts:])]})
        
        df['Voltage avg (V)'] = (df['Voltage Up (V)']+df['Voltage Down (V)'])/2
        
        return(df)

if __name__ == '__main__':
    # if running this file, do some stuff
    
    gpib_address = 'GPIB::16::INSTR'
    # tcp_address = 'TCPIP0::192.168.000.002::INSTR'
    smu = SMU_K2611B(gpib_address)
    
    df = smu.takeIV(1e-7, 1e-3, 1, 101, 0.01)
    
    # df.set_index('Voltage avg (V)')['Current (A)'].plot()
        
    #plt.figure(101)
    #plt.loglog(df['Voltage avg (V)'], df['Current (A)'])    

    # #Property functions used to easily set and read center frequency in MHz
    # def get_center_freq(self):
    #     return self.inst.query('FREQ:CENT?')
    # #Returns 0 if your frequency is out of bounds (assumes 50ghz pxa) (SND)
    # def set_center_freq(self, freq_mhz):
    #     if freq_mhz < 50e3:
    #         self.inst.write('FREQ:CENT %s MHz' %(freq_mhz))
    #         return 1
    #     return 0
    
    
    # #Property functions used to set and read continuous mode state (state is ON for on, OFF for off)
    # def get_continuous_mode(self):
    #     return self.inst.query('INIT:CONT?')
    # def set_continuous_mode(self, state):
    #     self.inst.write('INIT:CONT %s' %(state))
    
    
    # #Property functions used to set and read the frequency span
    # def set_span(self, freq_mhz):
    #     self.inst.write(':SENS:FREQ:SPAN %s MHz' %(freq_mhz))
    # def get_span(self):
    #     return self.inst.query(':SENS:FREQ:SPAN?')
    
    
    # #Property functions used to set and read res bandwidth
    # def set_rbw(self, freq_hz):
    #     self.inst.write('BWID:AUTO OFF')
    #     self.inst.write('BWID %s Hz' %(freq_hz))
    # def get_rbw(self):
    #     return self.inst.query('BWID?')
    
    # #functions for video bandwidth
    # def set_vbw(self, freq_hz):
    #     self.inst.write('BWID:VID:AUTO OFF')
    #     self.inst.write('BWID:VID %s Hz' %(freq_hz))
    # def get_vbw(self):
    #     return self.inst.query('BWID:VID?')
        
    # #Property functions used to set and read the number of points
    # def set_numpoints(self, numpoints):
    #     self.inst.write(':SENS:SWE:POIN %s' %(numpoints))
    # def get_numpoints(self):
    #     return int(self.inst.query_ascii_values(':SENS:SWE:POIN?')[0])
    
    
    # #Property functions used to set and read the reference level in dBm
    # def set_reflevel(self, level):
    #     self.inst.write('DISP:WIND:TRAC:Y:RLEV %s dBm' %(level))
    # def get_reflevel(self):
    #     return self.inst.query('DISP:WIND:TRAC:Y:RLEV?')
    
    
    # #Property functions used to set and read the scale per division in dB
    # def set_scalediv(self, scale):
    #     self.inst.write('DISP:WIND:TRAC:Y:PDIV %s DB' %(scale))
    # def get_scalediv(self):
    #     return self.inst.query('DISP:WIND:TRAC:Y:PDIV?')
    
    
    # def set_sweep_time(self, milliseconds):
    #     self.inst.write('SENS:SWE:TIME:AUTO OFF')
    #     self.inst.write('SENS:SWE:TIME %s ms' %(milliseconds))
    
    # #Creating properties so that settings can be treated like variables
    # center_freq = property(get_center_freq,set_center_freq)
    # continuous_mode = property(get_continuous_mode,set_continuous_mode)
    # span = property(get_span,set_span)
    # rbw = property(get_rbw,set_rbw)
    # vbw = property(get_vbw,set_vbw)
    # numpoints = property(get_numpoints,set_numpoints)
    # reflevel = property(get_reflevel,set_reflevel)
    # scalediv = property(get_scalediv,set_scalediv)
    
        
    # def get_ydata(self):
    #     return self.inst.query_ascii_values('TRAC? TRACE1')
    
    # def get_xdata(self):
    #     fstart = self.inst.query_ascii_values('SENS:FREQ:START?')[0]
    #     fstop = self.inst.query_ascii_values('SENS:FREQ:STOP?')[0]
    #     np = self.numpoints
        
    #     return numpy.linspace(fstart,fstop,np)
        
    
    # def save_file(self,file_name):
    #     self.inst.write('MMEM:DATA "%s"' %(file_name))
    
    # #saves in the default directory on PXA (SND)
    # def screen_shot(self,file_name):
    #     self.inst.write('MMEM:STOR:SCR "%s"' %(file_name))
    
    # def trigger_once(self):
    #     self.inst.write('*TRG')
    
    # def trigger_once_2(self):
    #     self.inst.write('INIT:IMM')
    
    # def preset(self):
    #     self.inst.write('SYST:PRES')
    
    # def send_opcheck(self):
    #     return self.inst.query('*OPC?')

    # #Returns the frequency and magnitude of the peak (I think)
    # def peak_search(self):
    #     self.inst.write(':CALC:MARK1:MAX')
    #     return (self.inst.query('CALC:MARK1:X?'),self.inst.query('CALC:MARK1:Y?'))

    # def set_rf_input(self):
    #     self.inst.write(':SENS:FEED RF')

    # def set_correction_off(self):
    #     self.inst.write('SENS:CORR:CSET:ALL OFF')
    
    # Imin=1e-9
    # Imax=1e-2
    # Vmax=1
    # numpts = 101
    # dtime = 0.05 # SEc

    # smu.inst.write('smua.reset()')
    # smu.inst.write('display.screen = display.SMUA')
    # smu.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS')
    # smu.inst.write('smua.measure.autorangei = smua.AUTORANGE_ON')
    # smu.inst.write('format.data = format.ASCII')
    # smu.inst.write('smua.nvbuffer1.clear()')
    # smu.inst.write('smua.nvbuffer1.appendmode = 1')
    # smu.inst.write('smua.nvbuffer1.collectsourcevalues = 1')
    # smu.inst.write('smua.measure.count = 1')
    # smu.inst.write('smua.source.func = smua.OUTPUT_DCAMPS')
    # smu.inst.write(f'smua.source.limitv = {Vmax}')

    # smu.inst.write(f'smua.source.leveli = {Imin}')
    
    # smu.inst.write('smua.source.output = smua.OUTPUT_ON')

    # irange = np.logspace(np.log10(Imin),np.log10(Imax),numpts)
    # for ii in irange:
    #     smu.inst.write(f'smua.source.leveli = {ii}')
    #     time.sleep(dtime)
    #     smu.inst.write('smua.measure.v(smua.nvbuffer1)')
    
    # # And back down
    # for ii in reversed(irange):
    #     smu.inst.write(f'smua.source.leveli = {ii}')
    #     time.sleep(dtime)
    #     smu.inst.write('smua.measure.v(smua.nvbuffer1)')        


    # smu.inst.write('smua.source.output = smua.OUTPUT_OFF')

    # redvals = smu.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
    # srcvals = smu.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')

    # df = pd.DataFrame({'Current (A)':srcvals[:numpts], 'Voltage Up (V)': redvals[:numpts], 
    #                    'Voltage Down (V)':[x for x in reversed(redvals[numpts:])]})
    
    # df.set_index('Current (A)').plot()
