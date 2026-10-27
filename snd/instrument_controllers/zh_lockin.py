# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 15:38:17 2022

@author: treck
"""

import time
import numpy as np
import _thread
try:
    import zhinst.ziPython
    import zhinst.utils
    from zhinst.ziPython import ziListEnum
except:
    'install zhinst module to control Zurich Lockin'
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime
from scipy import signal
#import vdi_synth as vdis
#import agilent_signal_generator as asg

class ZHInst:

    def __init__(self, device):

        d = zhinst.ziPython.ziDiscovery()
        props = d.get(d.find(device))
        
        api_session = zhinst.ziPython.ziDAQServer(props['serveraddress'],
         props['serverport'], props['apilevel'])
        api_session.connectDevice(device, props['interfaces'][0])

        (daq, device, _) = zhinst.utils.create_api_session(
            device, props['apilevel'], server_host=props['serveraddress'], server_port=props['serverport']
        )
        
        zhinst.utils.api_server_version_check(daq)

        #api_session.listNodes('/DEV6017/SCOPES/0/SINGLE')
        self.daq = daq
        self.dev = device

    def get_scope_records(self, scopeModule, num_records=1):
        """
        Obtain scope records from the device using an instance of the Scope Module.
        """
        device = self.dev
        daq = self.daq


        # Tell the module to be ready to acquire data; reset the module's progress to 0.0.
        scopeModule.execute()

        # Enable the scope: Now the scope is ready to record data upon receiving triggers.
        daq.setInt("/%s/scopes/0/enable" % device, 1)
        daq.sync()

        start = time.time()
        timeout = 30  # [s]
        records = 0
        progress = 0
        # Wait until the Scope Module has received and processed the desired number of records.
        while (records < num_records) or (progress < 1.0):
            time.sleep(0.5)
            records = scopeModule.getInt("records")
            progress = scopeModule.progress()[0]
    #        print(
    #            f"Scope module has acquired {records} records (requested {num_records}). "
    #            f"Progress of current segment {100.0 * progress}%.",
    #            end="\r",
    #        )
            # Advanced use: It's possible to read-out data before all records have been recorded (or
            # even before all segments in a multi-segment record have been recorded). Note that complete
            # records are removed from the Scope Module and can not be read out again; the read-out data
            # must be managed by the client code. If a multi-segment record is read-out before all
            # segments have been recorded, the wave data has the same size as the complete data and
            # scope data points currently unacquired segments are equal to 0.
            #
            # data = scopeModule.read(True)
            # wave_nodepath = f"/{device}/scopes/0/wave"
            # if wave_nodepath in data:
            #   Do something with the data...
            if (time.time() - start) > timeout:
                # Break out of the loop if for some reason we're no longer receiving scope data from the
                # device.
                print(
                    f"\nScope Module did not return {num_records} records after {timeout} s - \
                        forcing stop."
                )
                break
    #    print("")
        daq.setInt("/%s/scopes/0/enable" % device, 0)

        # Read out the scope data from the module.
        data = scopeModule.read(True)

        # Stop the module; to use it again we need to call execute().
        scopeModule.finish()

        return data

    def demoddata_R(self, sample):
        R = np.sqrt(sample['x']**2 + sample['y']**2)
        return(R[0])

    def scopedata_avg(self, scope_records, scope_input_channel, scope_time=0
    ):
        """
        returns average of scope records.
        """
        wavelist = []
        for index, record in enumerate(scope_records):
            wave = record[0]["wave"][scope_input_channel, :]
            wavelist.append(wave)
            
            time = record[0]["timestamp"]
            
        wavemean = np.mean(wavelist)
        
        return(wavemean)
        
    def scopedata_list(self, scope_records, scope_input_channel, scope_time=0
    ):
        """
        returns average of scope records.
        """
        wavelist = []
        for index, record in enumerate(scope_records):
            wave = record[0]["wave"][scope_input_channel, :]
            wavelist.append(wave)
        
        return(wavelist[0])
        
    def configLockin(self, samp_rate=13, n_points=4092):
        daq = self.daq
        daq.setInt('/dev6017/system/extclk', 0)
        daq.setInt('/dev6017/demods/1/adcselect', 8)
        daq.setInt('/dev6017/demods/1/adcselect', 2)
        daq.setInt('/dev6017/extrefs/0/enable', 1)
        daq.setInt('/dev6017/demods/1/adcselect', 8)
        
        daq.setInt('/dev6017/demods/0/order', 8)
        daq.setDouble('/dev6017/demods/0/timeconstant', 0.191523895)

        # Set scope to 7kHz & 4092 pts5

        self.sampRate = 60e6/(2**samp_rate)

        daq.setInt('/dev6017/scopes/0/time', samp_rate)
        daq.setDouble('/dev6017/scopes/0/length', n_points)
        
        #Auto scale range
        daq.setInt('/dev6017/sigins/0/autorange', 1)
        
    def autoScale(self):
        #Auto scale range
        self.daq.setInt('/dev6017/sigins/0/autorange', 1)

    def getDCval(self):
        device = self.dev
        daq = self.daq
        
        daq.setInt('/dev6017/scopes/0/time', 3)
        # daq.setDouble('/dev6017/scopes/0/length', 4092)
        
        scopeModule = daq.scopeModule()
        wave_nodepath = f"/{device}/scopes/0/wave"
        scopeModule.subscribe(wave_nodepath)
        
        min_num_records = 1
        scope_in_channel = 0
        
        data_no_trig = self.get_scope_records(scopeModule, min_num_records)
        # scopedata = self.scopedata_list(data_no_trig[wave_nodepath], scope_in_channel)
        
        daq.setInt('/dev6017/scopes/0/time', 13)
        return(np.abs(self.scopedata_avg(data_no_trig[wave_nodepath], scope_in_channel)))

    def takeData(self, n=3):
        device = self.dev
        daq=self.daq
        scopeModule = daq.scopeModule()
        wave_nodepath = f"/{device}/scopes/0/wave"
        scopeModule.subscribe(wave_nodepath)

        out = []

        for k in range(n):
            data_no_trig = self.get_scope_records(scopeModule, 1)

            for index, record in enumerate(data_no_trig[wave_nodepath]):
                wave = record[0]["wave"][0, :]
                out.append(wave)

        return out


    def takePoint(self, scope_in_channel = 0, min_num_records = 1, n = 3):
        device = self.dev
        daq = self.daq
        scopeModule = daq.scopeModule()
        wave_nodepath = f"/{device}/scopes/0/wave"
        scopeModule.subscribe(wave_nodepath)
        #sampRate = self.sampRate  # hopefully this is set in the configLockin???
        chopfactor = 2.4
        Th = 293
        Tc = 80

        AC = []
        DC = []
        Y = []
        Tsys = []
        for nn in range(n):

            data_no_trig = self.get_scope_records(scopeModule, min_num_records)
            #scopedata = self.scopedata_list(data_no_trig[wave_nodepath], scope_in_channel)
            DC.append(np.abs(self.scopedata_avg(data_no_trig[wave_nodepath], scope_in_channel)))
            
            #fpdes, Pxx_den = signal.welch(scopedata, sampRate, nperseg=scopedata.shape[-1])
            #plt.semilogx(fpdes, Pxx_den)
           
            demoddat = daq.getSample('/{0}/demods/0/sample'.format(device))
            AC.append(self.demoddata_R(demoddat))
            
            Y.append((DC[nn] + AC[nn] * (chopfactor/2))/ (DC[nn] - AC[nn] * (chopfactor/2)))
            Tsys.append((Th - Y[nn]*Tc)/(Y[nn]-1))
        
        return (np.mean(DC),np.mean(AC),np.mean(Y),np.mean(Tsys))

# if __name__ == "__main__":
#     chopfactor = 2.4
#     Th = 293
#     Tc = 80
#     timeconst = 10
    
#     spath = r'T:\Engineer\Reck\SELFI\560IAMC_IFRework\SuperH_IFSystem4'

# #    fname = 'test '
 
#     mfactor = 1    
    
#     # Setup Frequency Sweep
#     #Low Channel
# #    fmin = 520   # GHz
# #    fmax = 570   # GHz
# #    fstep = 2
# #    
#     #Low Channel
#     fmin = 34   # GHz
#     fmax = 40   # GHz
#     atnval = 2
#     fstep = 1
#     fname = f'SELFI B1-04 USB 2ampingreybox 6dBIFAtten {fmin}-{fmax}GHz '

#     fpts = np.arange(fmin,fmax+fstep,fstep)/mfactor
 
# #    synth = vdis.Synth()
#     gpib_address = 'TCPIP::169.254.93.104::inst0::INSTR'
#     synth = asg.PSG(address=gpib_address)
#     synth.set_frequency(fpts[0])
#     synth.set_power(13)
#     synth.power_on()
    
#     # Setup Lockin
#     (daq, device, api_session) = setupLockin(device = 'dev6017')
    
#     clockbase = daq.getInt(f"/{device}/clockbase")
    
#     configLockin(daq)
    
#     min_num_records = 1
#     scope_in_channel = 0

#     scopeModule = daq.scopeModule()  
#     wave_nodepath = f"/{device}/scopes/0/wave"
#     scopeModule.subscribe(wave_nodepath)

# #    setupLockin(daq)

#     df = pd.DataFrame(columns=['RF Freq', 't', 'AC', 'DC', 'Y', 'Tsys'])

#     figDC = plt.figure(101)
#     axDC = plt.gca()
#     plt.title('DC')
#     plt.ion()
#     figTsys = plt.figure(102)
#     axTsys = plt.gca()
#     plt.title('Tsys')
#     plt.ion()
#     figSpec = plt.figure(103)
#     axSpec = plt.gca()
#     plt.title('Spectrum')
#     plt.ion()

#     sampRate = 7.32e3  # Hz  (should pull this from the Lockin)
#     start = time.time()
# #    daq.setInt('/dev6017/sigins/0/autorange', 1)
    
#     for f in fpts:
#         synth.set_frequency(f)
        
#         daq.setInt('/dev6017/sigins/0/autorange', 1)
#         time.sleep(timeconst)
        
#         (DC, AC, Y, Tsys) = takePoint(device, daq, scopeModule, scope_in_channel,min_num_records)
        
#         tstamp = time.time() - start
        
#         df = df.append({'RF Freq': f*mfactor,
#                     't': tstamp,
#                     'AC': AC,
#                     'DC': DC,
#                     'Y': Y,
#                     'Tsys': Tsys}, ignore_index=True)

#         print('-------------------------')
#         print('RF Freq: {0}'.format(f*mfactor))
#         print('time: {0}'.format(tstamp))
#         print('AC: {0:.3e}'.format(AC))
#         print('DC: {0:.3e}'.format(DC))
#         print('Y: {0:.4f}'.format(Y))
#         print('Tsys: {0}'.format(Tsys))
            
#         axDC.clear()
#         axDC.plot(df['RF Freq'], df['DC'])
# #            if df['t'].iloc[-1] > 60:
# #                axDC.set_xlim((df['t'].iloc[-1]-60, df['t'].iloc[-1]))
#         plt.pause(0.01)
#         figDC.canvas.draw()
        
#         axTsys.clear()
#         axTsys.plot(df['RF Freq'], df['Tsys'])
# #            if df['t'].iloc[-1] > 60:
# #                axTsys.set_xlim((df['t'].iloc[-1]-60, df['t'].iloc[-1]))
# #            axTsys.set_ylim((0, 0.2e6))
#         axTsys.set_title('$T_{sys}$')
#         axTsys.set_ylim((0,50000))
#         plt.pause(0.01)
#         figTsys.canvas.draw()
        
# #        axSpec.clear()
# #        axSpec.loglog(fpdes, Pxx_den)
# #        axSpec.set_xlim((1,200))
# #        axSpec.set_ylim((1e-16,1e-10))
# #        axSpec.set_xlabel(('Hz'))
# #        plt.pause(0.01)
# #        figSpec.canvas.draw()

#     # Clean up
#     scopeModule.clear()
    
#     # datetime object containing current date and time
#     now = datetime.now()
 
#     # dd/mm/YY H:M:S
#     dt_string = now.strftime(" %d_%m_%Y %H_%M_%S")
# #        print("date and time =", dt_string)	
            
#     fnameout = fname+dt_string+'.dat'
#     df.to_csv(os.path.join(spath,fnameout))

    
    




#     