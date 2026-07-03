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

from smu_manager import KeithleyManager

import pickle

#Disables instrument connections
DEV_MODE = False

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
			self.smu_manager = None
			self.tc08 = None

		else:
			self.connect_instruments()

		self.switch_to_voltage_bias_mode()

	def connect_instruments(self):
		try:
			psg_address = int(self.m_textCtrl17.GetValue())
			self.psg = Source('psg',address=psg_address)
			self.m_checkBox3.SetValue(True)
		except:
			self.psg = Source('psg',address=psg_address,dummy=True)
			self.m_checkBox3.SetValue(False)
		try:
			exa_address = int(self.m_textCtrl18.GetValue())
			self.exa = PXA(address=exa_address)
			self.m_checkBox5.SetValue(True)
		except:
			self.m_checkBox5.SetValue(False)
		try:
			mc_name = self.m_textCtrl19.GetValue()
			self.mc = MotorController(mc_name,stepsize=1)
			self.m_checkBox7.SetValue(True)
		except:
			self.m_checkBox7.SetValue(False)
		try:
			psu_address = int(self.m_textCtrl20.GetValue())
			self.hp = PSU(address=psu_address)
			self.m_checkBox9.SetValue(True)
		except:
			self.m_checkBox9.SetValue(False)
	
		keithley_address = int(self.m_textCtrl23.GetValue())
		self.smu_manager = KeithleyManager(address=keithley_address)
		self.m_checkBox11.SetValue(self.smu_manager.get_connected_status())
		self.m_checkBox12.SetValue(self.smu_manager.get_power_status())

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
		self.speca_numpoints = float(self.speca_np.GetValue())
		self.meas_time = float(self.set_meas_time.GetValue())
		self.fstart = float(self.fstart_ghz.GetValue())
		self.fstop = float(self.fstop_ghz.GetValue())
		self.multval = float(self.mult.GetValue())
		self.lopower = float(self.lopower_dbm.GetValue())
		self.outpath = self.output_dir_picker.GetPath()
		self.npoints = int(self.num_points.GetValue())
		self.meas_delay = float(self.measdelay.GetValue())

		#bias parameters
		self.hp_channel = int(self.m_textCtrl27.GetValue())
		self.bias_voltage = float(self.m_textCtrl28.GetValue())
		self.start_current = float(self.m_textCtrl35.GetValue())/1e3
		self.stop_current = float(self.m_textCtrl29.GetValue())/1e3
		self.num_current_points = int(self.m_textCtrl36.GetValue())
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
		self.exa.set_numpoints(self.speca_numpoints)
		self.exa.set_sweep_time(self.meas_time)

		self.exa.set_rbw(self.rbw)
		self.exa.set_vbw(self.vbw)
		
		#self.exa.marker_setbandwidth(self.bw)
		self.exa.set_trace_detector('SAMP')
		sweep_time = self.exa.get_sweep_time()
		
		self.exa.marker_setcf(float(sweep_time)/2,'s')

		self.smu_manager.setup_current_source(ibias_ma=self.start_current, vlimit_v=self.voltage_limit)

		try:
			self.hp.set_currdef(self.hp_channel, self.current_limit)
			self.hp.set_voltdef(self.hp_channel, self.bias_voltage)
			self.set_hp_state(True)
		except:
			pass

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
			self.m_checkBox12.SetValue( self.smu_manager.toggle_off() )

		elif state == True:
			self.m_checkBox12.SetValue( self.smu_manager.toggle_on() )

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

	def SweepOnce(self):

		self.UpdateVariables()
		self.exa.set_numpoints(self.speca_numpoints)
		self.exa.set_sweep_time(self.meas_time)
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
			#time.sleep(self.meas_delay*2)

			coldtrace = self.exa.get_trace(single_sweep_mode=True)

			#coldval = float(self.exa.marker_getvalue())
			coldval = muh.ufloatfromsamples(coldtrace, desc='coldval')
			print(f"{counter} - {k*self.multval}: {coldval}dBm")

			try:
				temps.append(self.tc08.get_data(units='K')[1])
			except:
				pass

			self.mc.step_angle(0,65)
			#time.sleep(self.meas_delay*2)

			hottrace = self.exa.get_trace(single_sweep_mode=True)

			#hotval = float(self.exa.marker_getvalue())
			hotval = muh.ufloatfromsamples(hottrace, desc='hottrace')

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
			utemp = muh.ufloatfromsamples(temps,desc='temp')
			self.ln2_thot.SetValue( str(utemp) )
		except:
			utemp = 0

		return cold,hot

	def ChopNS(self):

		self.exa.set_numpoints(self.speca_numpoints)
		self.exa.set_sweep_time(self.meas_time)
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
			#time.sleep(self.meas_delay*2)

			coldtrace = self.exa.get_trace(single_sweep_mode=True)

			#coldval = float(self.exa.marker_getvalue())
			coldval = muh.ufloatfromsamples(coldtrace, desc='coldval')
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

			#time.sleep(self.meas_delay*2)
			hottrace = self.exa.get_trace(single_sweep_mode=True)

			#hotval = float(self.exa.marker_getvalue())
			hotval = muh.ufloatfromsamples(hottrace, desc='hottrace')
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
			utemp = muh.ufloatfromsamples(temps,desc='temp')
			self.roomtemp_k.SetValue( str(utemp) )
		except:
			utemp = 0

		return cold,hot

	def VerifySetup( self, event ):

		self.UpdateVariables()

		self.SetupInstruments()
		self.exa.set_numpoints(self.speca_numpoints)
		self.exa.set_sweep_time(self.meas_time)

		self.meas_delay = float(self.exa.get_sweep_time())
		self.measdelay.SetValue(str(self.meas_delay))

		self.set_smu_state(True)


		f = (self.fstart+self.fstop)/(2*self.multval)
		self.psg.set_frequency(f)
		time.sleep(self.meas_delay)
		
		time.sleep(1)

		trace = self.exa.get_trace(single_sweep_mode=True)
		val = muh.ufloatfromsamples(trace)

		self.exa.set_reflevel(val.value+25)
		self.exa.set_scalediv(5)

		self.verify_textbox.SetLabel(str(val))

	def ns_chopped_pressed( self, event ):
		event.Skip()
		self.UpdateVariables()

		#if we are current biasing get the range of bias values
		if self.ns_bias_mode == 'current':
			current_biases = np.linspace(self.start_current, self.stop_current, self.num_current_points)

			for current in current_biases:
				if self.run_iv_tests.GetValue():
					#take pre-IV
					iv_df = self.smu_manager.take_iv(1.2, 100e-9,1e-3, 30)
					iv_filename = self.output_filename.GetValue()+f"_{current*1e3}mA_preIV"
					iv_filename_fullpath = safeFname(self.outpath,iv_filename,'.csv')
					iv_df.to_csv(iv_filename_fullpath)

				self.smu_manager.setup_current_source(ibias_ma=current, vlimit_v=self.voltage_limit)
				self.nsoff, self.nson = self.ChopNS()

				filename_with_current = self.output_filename.GetValue()+f"_{current*1e3}mA"
				self.Calculate_NS(file_name = filename_with_current)

			if self.run_iv_tests.GetValue():
				#take post-IV
				iv_df = self.smu_manager.take_iv(1.2, 100e-9,1e-3, 30)
				post_iv_filename = self.output_filename.GetValue()+f"_{current*1e3}mA_postIV"
				post_iv_filename_fullpath = safeFname(self.outpath,post_iv_filename,'.csv')
				iv_df.to_csv(post_iv_filename_fullpath)
		elif self.ns_bias_mode == 'voltage':
			self.nsoff, self.nson = self.ChopNS()
			self.Calculate_NS(file_name = self.output_filename.GetValue())

		else:
			pass

	def MotorCW(self, event):
		self.mc.step_angle(1,1)

	def MotorCCW(self, event):
		self.mc.step_angle(0,1)

	def Output_csv( self, outdict, extension ):

		df = pd.DataFrame(index=outdict.keys())
		df['data'] = outdict.values()

		outfilename = safeFname(self.outpath, self.output_filename.GetValue()+extension,'.csv')
		df.to_csv(outfilename)

	def Calculate_NS( self, file_name ):
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
			outfilename = safeFname(self.outpath,file_name+'_unknown','.csv')
			df.to_csv(outfilename)

			pickle_filename = safeFname(self.outpath,file_name+'unknown','.pickle')
			pickle.dump(df,open(pickle_filename,'wb'))

		else:

			enr_caled = muh.read_csv(calfilepath,index_col=0)

			#df['Tns(K)'] = np.interp(df.index,enr_caled.index,enr_caled['Tns(K)'])
			df['Tns(K)'] = mu.unumlib.interpolation2(enr_caled.index,enr_caled['Tns(K)'],1,df.index)
			df['Treceiver(K)'] = (df['Tns(K)'] - df['Y']*df['rt(K)']) / (df['Y']-1)

			outfilename = safeFname(self.outpath,file_name,'.csv')
			df.to_csv(outfilename)

			pickle_filename = safeFname(self.outpath,file_name,'.pickle')
			pickle.dump(df,open(pickle_filename,'wb'))

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

		#save pickle also
		picklename = safeFname(self.outpath,self.output_filename.GetValue(),'.pickle')
		pickle.dump(df,open(picklename,'wb'))
		outfilename = safeFname(self.outpath,self.output_filename.GetValue(),'.csv')
		df.to_csv(outfilename)

	def create_ns_calfile( self, event ):
		rxpath = self.rx_tsys_in.GetPath()
		nspath = self.ns_unknown_in.GetPath()

		#pickles will keep the uncertainty budgets
		if 'pickle' in rxpath:
			caled_rx = pickle.load(open(rxpath,'rb'))
		else:
			caled_rx = muh.read_csv(rxpath,index_col=0)

		if 'pickle' in nspath:
			df = pickle.load(open(nspath,'rb'))
		else:
			df = muh.read_csv(nspath,index_col=0)

		#trx = np.interp(df.index,caled_rx.index,caled_rx['Treceiver(K)'])
		trx = mu.unumlib.interpolation2(caled_rx.index,caled_rx['Treceiver(K)'],1,df.index)
		taper_loss_lin = mu.unumlib.interpolation2(caled_rx.index,caled_rx['taper_loss_combined(lin)'],1,df.index)
		taper_loss_k = mu.unumlib.interpolation2(caled_rx.index,caled_rx['taper_loss_combined(K)'],1,df.index)
		trx_prime = (trx-taper_loss_k)/taper_loss_lin

		df['Trx'] = trx
		df['TaperLoss(lin)'] = taper_loss_lin
		df['TaperLoss(K)'] = taper_loss_k
		df['Trx_Prime'] = trx_prime
		df['Tns(K)'] = trx_prime*(df['Y']-1)+df['Y']*df['rt(K)']
		df['ENR'] = (df['Tns(K)']-df['rt(K)'])/df['rt(K)']
		df['ENR(dB)']=10*np.log10(df['ENR'])

		outfilename = safeFname(self.outpath,self.ns_cal_filename.GetValue(),'.csv')
		df.to_csv(outfilename)

		#also pickle the output to save the unc budget
		pickle_filename = safeFname(self.outpath,self.ns_cal_filename.GetValue(),'.pickle')
		pickle.dump(df,open(pickle_filename,'wb'))

	def switch_to_voltage_bias_mode( self ):
		self.m_checkBox1.SetValue(True)
		self.m_checkBox1.Disable()
		self.m_checkBox2.Enable()
		self.m_checkBox2.SetValue(False)

		self.ns_bias_mode = 'voltage'

	def switch_to_current_bias_mode( self ):
		self.m_checkBox2.SetValue(True)
		self.m_checkBox1.Enable()
		self.m_checkBox2.Disable()
		self.m_checkBox1.SetValue(False)

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

if __name__ == '__main__':
	a = ENR()