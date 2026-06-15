import os

import wx
from instrument_controller import Source
from agilent_signal_analyzer import PXA
from keithley_2600smu import SMU_K2611B
from HP6627A import PSU

from enr_gui import VirtualENRPanel
import time
import numpy as np
import pandas as pd

from motor_stepper_dumb import MotorController

from pico_tc08 import TC08
import metas_unclib as mu
import mu_helper as muh


#Disables instrument connections
#DEV_MODE = True

def calculate_standing_wave(ns_rl, mix_rl, horn_rl=-23):
	ns_vswr = (1+np.power(10,ns_rl/20))/(1-np.power(10,ns_rl/20))
	mix_vswr = (1+np.power(10,mix_rl/20))/(1-np.power(10,mix_rl/20))
	horn_vswr = (1+np.power(10,horn_rl/20))/(1-np.power(10,horn_rl/20))

	ns_gamma = (ns_vswr-1)/(ns_vswr+1)
	mix_gamma = (mix_vswr-1)/(mix_vswr+1)
	horn_gamma = (horn_vswr-1)/(horn_vswr+1)

	mix_horn_uncertainty = -20*np.log10(1-mix_gamma*horn_gamma)
	mix_ns_uncertainty = -20*np.log10(1-ns_gamma*mix_gamma)

	rsos = np.sqrt(mix_horn_uncertainty**2 + mix_ns_uncertainty**2)

	return rsos


def safeFname(path,fname,ext='.csv'):
    filename = os.path.join(path, fname+ext)
    
    inc = 2
    while os.path.exists(filename):
        filename = os.path.join(path, fname+'_m'+str(inc)+ext)
        inc += 1  
    
    return(filename)

class ENR():

    def __init__(self):

        app = wx.App(False)
        frame = wx.Frame(parent=None, size = (800,800))

        panel = ENRPanel(parent=frame)

        frame.Show()
        app.MainLoop()

class ENRPanel(VirtualENRPanel):

    def __init__(self, **kwargs):
        VirtualENRPanel.__init__(self, **kwargs)

        if DEV_MODE:
            self.psg = None
            self.exa = None
            self.mc = None
            self.hp = None
            self.smu = None

        else:
            self.connect_instruments()

        self.switch_to_voltage_bias_mode()

    def connect_instruments(self):
        try:
            self.psg = Source('psg',address=20)
            self.m_checkBox3.SetValue(True)
        except:
            self.m_checkBox3.SetValue(False)
        try:
            self.exa = PXA()
            self.m_checkBox5.SetValue(True)
        except:
            self.m_checkBox5.SetValue(False)
        try:
            self.mc = MotorController("Dev1",stepsize=1)
            self.m_checkBox7.SetValue(True)
        except:
            self.m_checkBox7.SetValue(False)
        try:
            self.hp = PSU()
            self.m_checkBox9.SetValue(True)
        except:
            self.m_checkBox9.SetValue(False)
        try:
            self.smu = SMU_K2611B(address=18)
            self.m_checkBox11.SetValue(True)
        except:
            self.m_checkBox11.SetValue(False)

        try:
            self.tc08 = TC08()
            self.tc08.activate_channel(1)
            print('connected temp sensor')
        except:
            self.tc08 = None
            print('no temp sensor connected')

    def UpdateVariables(self):
        #sweep parameters
        self.vbw = int(float(self.vbw_hz.GetValue()))
        self.rbw = int(float(self.rbw_hz.GetValue()))
        self.cf = float(self.ifcenter_mhz.GetValue())
        self.bw = float(self.ifbw_mhz.GetValue())
        self.fstart = float(self.fstart_ghz.GetValue())
        self.fstop = float(self.fstop_ghz.GetValue())
        self.multval = float(self.mult.GetValue())
        self.lopower = float(self.lopower_dbm.GetValue())
        self.outpath = self.output_dir_picker.GetPath()
        self.npoints = int(self.num_points.GetValue())
        self.meas_delay = float(self.measdelay.GetValue()) *1.2

        #bias parameters
        self.hp_channel = int(self.m_textCtrl27.GetValue())
        self.bias_voltage = float(self.m_textCtrl28.GetValue())
        self.bias_current = float(self.m_textCtrl29.GetValue())/1e3
        self.voltage_limit = float(self.m_textCtrl26.GetValue())
        self.current_limit = float(self.m_textCtrl271.GetValue())/1e3

        #correction parameters
        self.taper1_db = float( self.m_textCtrl25.GetValue() )
        self.taper2_db = float ( self.m_textCtrl24.GetValue() )
        #self.tif = float( self.m_textCtrl281.GetValue() )

    def SetupInstruments(self):
        self.exa.preset()

        self.psg.set_power(self.lopower)
        self.set_psg_state(True)

        self.exa.set_center_freq(self.cf)
        self.exa.set_span(0)
        self.exa.set_numpoints(10001)
        self.exa.set_sweep_time(self.bw)

        self.exa.set_rbw(self.rbw)
        self.exa.set_vbw(self.vbw)
        
        #self.exa.marker_setbandwidth(self.bw)
        self.exa.set_trace_detector('AVER')
        sweep_time = self.exa.get_sweep_time()
        
        self.exa.marker_setcf(float(sweep_time)/2,'s')

        if self.ns_bias_mode == 'current':
            self.smu.set_mode_current_source()
            self.smu.set_voltage_limit(self.voltage_limit)
            self.smu.set_current_level(self.current_limit)
            self.set_smu_state(True)

        elif self.ns_bias_mode == 'voltage':
            self.hp.set_currdef(self.hp_channel, self.bias_current)
            self.hp.set_voltdef(self.hp_channel, self.bias_voltage)
            self.set_hp_state(True)

    def set_hp_state(self, state=False):
        if state == False:
            try:
                self.hp.set_output(self.hp_channel, 0)
                self.m_checkBox10.SetValue(False)
            except:
                pass

        elif state == True:
            try:
                self.hp.set_output(self.hp_channel, 1)
                self.m_checkBox10.SetValue(True)
            except:
                pass

    def set_smu_state(self, state=False):
        if state == False:
            try:
                self.smu.setsourceOff()
                self.m_checkBox12.SetValue(False)
            except:
                pass

        elif state == True:
            try:
                self.smu.setsourceOn()
                self.m_checkBox12.SetValue(True)
            except:
                pass                    

    def set_psg_state(self, state=False):
        if state == False:
            try:
                self.psg.power_off()
                self.m_checkBox4.SetValue(False)
            except:
                pass

        elif state == True:
            try:
                self.psg.power_on()
                self.m_checkBox4.SetValue(True)
            except:
                pass    

    def set_power_states(self, state=False):
        self.set_hp_state(state)
        self.set_smu_state(state)
        self.set_psg_state(state)       

    def psg_power_toggled( self, event ):
        event.Skip()
        self.set_psg_state(self.m_checkBox4.GetValue())

    def hp_power_toggled( self, event ):
        event.Skip()
        self.set_hp_state(self.m_checkBox10.GetValue())

    def smu_power_toggled( self, event ):
        event.Skip()
        self.set_smu_state(self.m_checkBox12.GetValue())

    def NoiseSweep(self, fps):
        #self.ifbw_mhz.SetValue(f'{bandwidth_mhz}')
        #self.output_filename.SetValue(f'{bandwidth_mhz}')

        self.numfpoints = fps
        self.output_filename.SetValue(f'{fps}')

        self.VerifySetup(None)

        self.ln2cold, self.ln2hot = self.SweepOnce()
        self.Calculate_LN2(None)

    def SweepOnce(self):

        self.UpdateVariables()
        self.exa.set_numpoints(10001)
        self.exa.set_sweep_time(self.bw)
        self.psg.set_power(self.lopower)

        #self.mc.step_angle(0,10)
        cold = {}
        hot = {}
        temps = []
        cw = False
        sweep_range = np.linspace(self.fstart/self.multval, self.fstop/self.multval, self.npoints)
        if sweep_range[0] == sweep_range[-1]:
            cw = True

        counter = 0

        for k in sweep_range:

            self.psg.set_frequency(k)
            time.sleep(self.meas_delay)

            coldtrace = self.exa.get_trace()

            #coldval = float(self.exa.marker_getvalue())
            coldval = mu.ufloatfromsamples(coldtrace, desc='coldval')
            print(f"{counter} - {k*self.multval}: {coldval}dBm")

            try:
                temps.append(self.tc08.get_data(units='K')[1])
            except:
                pass

            self.mc.step_angle(0,65)
            time.sleep(self.meas_delay)

            hottrace = self.exa.get_trace()

            #hotval = float(self.exa.marker_getvalue())
            hotval = mu.ufloatfromsamples(hottrace, desc='hottrace')

            print(f"{counter} - {k*self.multval}: {hotval}dBm")


            try:
                temps.append(self.tc08.get_data(units='K')[1])
            except:
                pass

            self.mc.step_angle(1,65)

            #self.mc.reset()

            if cw:
                cold[counter]=coldval
                hot[counter]=hotval
            else:
                cold[k*self.multval]=coldval
                hot[k*self.multval]=hotval

            counter = counter+1

        try:
            utemp = mu.ufloatfromsamples(temps,desc='temp')
            self.ln2_thot.SetValue( str(utemp) )
        except:
            utemp = 0

        return cold,hot

    def ChopNS(self):

        self.UpdateVariables()
        self.exa.set_numpoints(10001)
        self.exa.set_sweep_time(self.bw)
        self.psg.set_power(self.lopower)

        #self.mc.step_angle(0,10)
        cold = {}
        hot = {}
        temps = []

        cw = False
        sweep_range = np.linspace(self.fstart/self.multval, self.fstop/self.multval, self.npoints)
        if sweep_range[0] == sweep_range[-1]:
            cw = True

        counter = 0

        for k in sweep_range:

            self.psg.set_frequency(k)
            time.sleep(self.meas_delay)

            coldtrace = self.exa.get_trace()

            #coldval = float(self.exa.marker_getvalue())
            coldval = mu.ufloatfromsamples(coldtrace, desc='coldval')
            print(f"{counter} - {k*self.multval}: {coldval}dBm")

            try:
                temps.append(self.tc08.get_data(units='K')[1])
            except:
                pass

            #self.mc.step_angle(0,65)
            if self.ns_bias_mode == 'voltage':
                self.set_hp_state(True)
            elif self.ns_bias_mode == 'current':
                self.set_smu_state(True)

            time.sleep(self.meas_delay)
            hottrace = self.exa.get_trace()

            #hotval = float(self.exa.marker_getvalue())
            hotval = mu.ufloatfromsamples(hottrace, desc='hottrace')
            print(f"{counter} - {k*self.multval}: {hotval}dBm")

            try:
                temps.append(self.tc08.get_data(units='K')[1])
            except:
                pass

            #self.mc.step_angle(1,65)

            #self.mc.reset()
            if self.ns_bias_mode == 'voltage':
                self.set_hp_state(False)
            elif self.ns_bias_mode == 'current':
                self.set_smu_state(False)

            if cw:
                cold[counter]=coldval
                hot[counter]=hotval
            else:
                cold[k*self.multval]=coldval
                hot[k*self.multval]=hotval

            counter = counter+1

        try:
            utemp = mu.ufloatfromsamples(temps,desc='temp')
            self.roomtemp_k.SetValue( str(utemp) )
        except:
            utemp = 0

        return cold,hot

    def VerifySetup( self, event ):

        self.UpdateVariables()

        self.SetupInstruments()
        self.exa.set_numpoints(10001)
        self.exa.set_sweep_time(self.bw)

        self.meas_delay = float(self.exa.get_sweep_time())
        self.measdelay.SetValue(str(self.meas_delay))


        f = (self.fstart+self.fstop)/(2*self.multval)
        self.psg.set_frequency(f)
        time.sleep(self.meas_delay)
        
        time.sleep(1)

        trace = self.exa.get_trace()
        val = mu.ufloatfromsamples(trace)

        self.exa.set_reflevel(val.value+25)
        self.exa.set_scalediv(5)

        self.verify_textbox.SetLabel(str(val))

    def ns_chopped_pressed( self, event ):
        event.Skip()

        self.nsoff, self.nson = self.ChopNS()
        self.Calculate_NS()

    def MotorCW(self, event):
        self.mc.step_angle(1,1)

    def MotorCCW(self, event):
        self.mc.step_angle(0,1)

    def Output_csv( self, outdict, extension ):

        df = pd.DataFrame(index=outdict.keys())
        df['data'] = outdict.values()

        outfilename = safeFname(self.outpath, self.output_filename.GetValue()+extension,'.csv')
        df.to_csv(outfilename)

    def Calculate_NS( self ):
        '''
        if there's no input file then we can't solve for T hot
        instead just output raw data. Assume it will be used to 
        calibrate the noise source.

        if there is an input file interpolate, then output the Tsys
        '''
        calfilepath = self.ns_file_in.GetPath()
        roomtemp = muh.str_to_ufloat(self.roomtemp_k.GetValue())

        df = pd.DataFrame(index=self.nsoff.keys())
        df['nsoff(dBm)'] = self.nsoff.values()
        df['nson(dBm)'] = self.nson.values()

        df['Ylog'] = df['nson(dBm)']-df['nsoff(dBm)']
        df['Y'] = 10**(df['Ylog']/10)
        df['rt(K)'] = roomtemp

        if calfilepath == '':
            outfilename = safeFname(self.outpath,self.output_filename.GetValue()+'_unknown','.csv')
            df.to_csv(outfilename)

        else:

            enr_caled = muh.read_csv(calfilepath,index_col=0)

            #df['Tns(K)'] = np.interp(df.index,enr_caled.index,enr_caled['Tns(K)'])
            df['Tns(K)'] = mu.unumlib.interpolation2(enr_caled.index,enr_caled['Tns(K)'],1,df.index)
            df['Treceiver(K)'] = (df['Tns(K)'] - df['Y']*df['rt(K)']) / (df['Y']-1)

            outfilename = safeFname(self.outpath,self.output_filename.GetValue(),'.csv')
            df.to_csv(outfilename)

    def hotcold_chopped_pressed( self, event ):
        event.Skip()
        
        self.ln2cold, self.ln2hot = self.SweepOnce()
        self.Calculate_LN2()

    def get_horn_and_taper_correction(self):
        taper1_db = self.taper1_db
        taper2_db = self.taper2_db

        combined_loss_db = taper1_db+taper2_db
        combined_loss_lin = np.power(10, combined_loss_db/10)

        thot = muh.str_to_ufloat( self.ln2_thot.GetValue() )
        combined_temperature = (combined_loss_lin-1) * thot

        return combined_loss_lin, combined_temperature

    def Calculate_LN2( self ):
        thot = muh.str_to_ufloat(self.ln2_thot.GetValue())
        tcold = float(self.ln2_tcold.GetValue())

        df = pd.DataFrame(index=self.ln2cold.keys())
        df['ln2cold(dBm)'] = self.ln2cold.values()
        df['ln2hot(dBm)'] = self.ln2hot.values()
        df['Ylog'] = df['ln2hot(dBm)']-df['ln2cold(dBm)']
        df['Y'] = 10**(df['Ylog']/10)

        df['cold(K)'] = tcold

        df['hot(K)'] = thot

        df['Treceiver(K)'] = (df['hot(K)'] - df['Y']*df['cold(K)']) / (df['Y']-1)

        df['taper1_loss(db)'] = self.taper1_db
        df['taper2_loss(db)'] = self.taper2_db

        combined_loss_lin, combined_temperature = self.get_horn_and_taper_correction()

        df['taper_loss_combined(lin)'] = combined_loss_lin
        df['taper_loss_combined(K)'] = combined_temperature
        
        ######
        #can't calculate Tmix without more temperature points
        #df['Tif(K)'] = self.tif
        ######

        outfilename = safeFname(self.outpath,self.output_filename.GetValue(),'.csv')
        df.to_csv(outfilename)

    def create_ns_calfile( self, event ):
        rxpath = self.rx_tsys_in.GetPath()
        nspath = self.ns_unknown_in.GetPath()

        caled_rx = muh.read_csv(rxpath,index_col=0)
        df = muh.read_csv(nspath,index_col=0)

        #trx = np.interp(df.index,caled_rx.index,caled_rx['Treceiver(K)'])
        trx = mu.unumlib.interpolation2(caled_rx.index,caled_rx['Treceiver(K)'],1,df.index)

        df['Tns(K)'] = trx*(df['Y']-1)+df['Y']*df['rt(K)']
        df['ENR'] = (df['Tns(K)']-df['rt(K)'])/df['rt(K)']
        df['ENR(dB)']=10*np.log10(df['ENR'])

        outfilename = safeFname(self.outpath,self.ns_cal_filename.GetValue(),'.csv')
        df.to_csv(outfilename)

    def switch_to_voltage_bias_mode( self ):
        self.m_checkBox1.SetValue(True)
        self.m_checkBox1.Disable()
        self.m_checkBox2.Enable()
        self.m_textCtrl27.Enable()
        self.m_textCtrl28.Enable()
        self.m_textCtrl271.Enable()

        self.m_checkBox2.SetValue(False)
        self.m_textCtrl29.Disable()
        self.m_textCtrl26.Disable()

        self.ns_bias_mode = 'voltage'

    def switch_to_current_bias_mode( self ):
        self.m_checkBox2.SetValue(True)
        self.m_checkBox1.Enable()
        self.m_checkBox2.Disable()
        self.m_textCtrl27.Disable()
        self.m_textCtrl28.Disable()
        self.m_textCtrl271.Disable()

        self.m_checkBox1.SetValue(False)
        self.m_textCtrl29.Enable()
        self.m_textCtrl26.Enable()

        self.ns_bias_mode = 'current'

    def voltage_bias_checked( self, event ):
        event.Skip()
        self.switch_to_voltage_bias_mode()

    def current_bias_checked( self, event ):
        event.Skip()
        self.switch_to_current_bias_mode()

    def reconnect_instruments_pressed(self, event):
        event.Skip()

        self.connect_instruments()

    def measure_tif_roomtemp(self, event):
        self.UpdateVariables()
        self.exa.set_span(self.bw)

        hot_vals = []

        measure_time_seconds = 10
        num_sweeps = int( np.ceil(measure_time_seconds/self.meas_delay) )

        for j in range(num_sweeps):
            time.sleep(self.meas_delay)

            hotval = self.exa.marker_getvalue()
            hot_vals.append(hotval)

            self.m_staticText42.SetLabel( str(hotval) )

        self.hot_df = pd.DataFrame(hot_vals,columns=['db'])
        self.hot_df['linear'] = np.power(10,self.hot_df['db']/10)

        outfilename = safeFname(self.outpath,"tif_hot",'.csv')
        self.hot_df.to_csv(outfilename)

    def measure_tif_cold(self, event):
        self.UpdateVariables()
        self.exa.set_span(self.bw)

        measure_time_seconds = 120

        num_sweeps = int( np.ceil(measure_time_seconds/self.meas_delay) )

        cold_vals = []

        for j in range(num_sweeps):
            time.sleep(self.meas_delay)

            coldval = self.exa.marker_getvalue()
            cold_vals.append(coldval)
            self.m_staticText43.SetLabel( str(coldval) )

        self.cold_df = pd.DataFrame(cold_vals,columns=['db'])
        self.cold_df['linear'] = np.power(10,self.cold_df['db']/10)

        outfilename = safeFname(self.outpath,"tif_cold",'.csv')
        self.cold_df.to_csv(outfilename)

    def calculate_tif(self):
        hot_mean = self.hot_df.mean()['lin']

        #take the last 10% of cold_df?
        cold_df_length = len(self.cold_df)
        cold_df_start_index = np.floor( cold_df_length*0.9 )
        cold_df_subset = self.cold_df[cold_df_start_index:]

        cold_mean = cold_df_subset.mean()['lin']

        cable_loss_db = float( self.m_textCtrl291.GetValue() )
        cable_loss = np.power(10,cable_loss_db/10)

        thot = float( self.m_textCtrl30.GetValue() )

        cable_loss_temp = (cable_loss-1)*thot

        y = hot_mean/cold_mean
        tif_raw = (thot - y*(80)) / (y-1)

        self.tif = (tif_raw - cable_loss_temp) / cable_loss

        self.m_staticText45.SetLabel( str(self.tif ))

if __name__ == '__main__':
    a = ENR()