import os

import wx
from instrument_controller import Source
from agilent_signal_analyzer import PXA
from keithley_2600smu import SMU_K2611B

from enr_gui import VirtualENRPanel
import time
import numpy as np
import pandas as pd

from motor_stepper_dumb import MotorController

DEV_MODE = True


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
		frame = wx.Frame(parent=None, size = (800,700))

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
			self.psg = Source('psg',address=20)
			self.exa = PXA()
			self.mc = MotorController("Dev1",stepsize=1)
			self.hp = Source('hp6627',address=5,channel=4)
			self.smu = SMU_K2611B(address=18)

	def UpdateVariables(self):
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
		self.meas_delay = float(self.measdelay.GetValue())

	def SetupInstruments(self):
		self.exa.preset()

		self.psg.set_power(self.lopower)
		self.psg.power_on()

		self.exa.set_center_freq(self.cf)
		self.exa.set_span(self.bw)
		self.exa.set_rbw(self.rbw)
		self.exa.set_vbw(self.vbw)
		self.exa.marker_setcf(self.cf)
		self.exa.marker_setbandwidth(self.bw)
		self.exa.set_trace_detector('AVER')

	def NoiseSweep(self, fps):
		#self.ifbw_mhz.SetValue(f'{bandwidth_mhz}')
		#self.output_filename.SetValue(f'{bandwidth_mhz}')

		self.numfpoints = fps
		self.output_filename.SetValue(f'{fps}')

		self.VerifySetup(None)

		self.ln2cold, self.ln2hot = self.SweepOnce()
		self.Calculate_LN2(None)

	def SweepOnceNoMotor(self):

		self.UpdateVariables()
		self.exa.set_span(self.bw)
		self.psg.set_power(self.lopower)

		#self.mc.step_angle(0,10)
		cold = {}
		hot = {}
		cw = False
		sweep_range = np.linspace(self.fstart/self.multval, self.fstop/self.multval, self.npoints)
		if sweep_range[0] == sweep_range[-1]:
			cw = True

		counter = 0

		for k in sweep_range:

			self.psg.set_frequency(k)
			time.sleep(self.meas_delay)

			coldval = float(self.exa.marker_getvalue())
			print(f"{counter} - {k*self.multval}: {coldval}dBm")

			self.mc.step_angle(0,65)
			time.sleep(self.meas_delay)
			hotval_raw = self.exa.marker_getvalue()
			print(hotval_raw)
			hotval = float(hotval_raw)
			print(hotval)
			print(f"{counter} - {k*self.multval}: {hotval}dBm")

			self.mc.step_angle(1,65)

			#self.mc.reset()

			if cw:
				cold[counter]=coldval
				hot[counter]=hotval
			else:
				cold[k*self.multval]=coldval
				hot[k*self.multval]=hotval

			counter = counter+1

		return cold,hot

	def SweepOnce(self):

		self.UpdateVariables()
		self.exa.set_span(self.bw)
		self.psg.set_power(self.lopower)

		#self.mc.step_angle(0,10)
		cold = {}
		hot = {}
		cw = False
		sweep_range = np.linspace(self.fstart/self.multval, self.fstop/self.multval, self.npoints)
		if sweep_range[0] == sweep_range[-1]:
			cw = True

		counter = 0

		for k in sweep_range:

			self.psg.set_frequency(k)
			time.sleep(self.meas_delay)

			coldval = float(self.exa.marker_getvalue())
			print(f"{counter} - {k*self.multval}: {coldval}dBm")

			self.mc.step_angle(0,65)
			time.sleep(self.meas_delay)
			hotval = float(self.exa.marker_getvalue())
			print(f"{counter} - {k*self.multval}: {hotval}dBm")

			self.mc.step_angle(1,65)

			#self.mc.reset()

			if cw:
				cold[counter]=coldval
				hot[counter]=hotval
			else:
				cold[k*self.multval]=coldval
				hot[k*self.multval]=hotval

			counter = counter+1

		return cold,hot

	def ChopNS(self):

		self.UpdateVariables()
		self.exa.set_span(self.bw)
		self.psg.set_power(self.lopower)

		self.hp.set_voltage(28)
		self.hp.set_current(.1)

		#self.mc.step_angle(0,10)
		cold = {}
		hot = {}
		cw = False
		sweep_range = np.linspace(self.fstart/self.multval, self.fstop/self.multval, self.npoints)
		if sweep_range[0] == sweep_range[-1]:
			cw = True

		counter = 0

		for k in sweep_range:

			self.psg.set_frequency(k)
			time.sleep(self.meas_delay)

			coldval = float(self.exa.marker_getvalue())
			print(f"{counter} - {k*self.multval}: {coldval}dBm")

			#self.mc.step_angle(0,65)
			self.hp.power_on()

			time.sleep(self.meas_delay)
			hotval = float(self.exa.marker_getvalue())
			print(f"{counter} - {k*self.multval}: {hotval}dBm")

			#self.mc.step_angle(1,65)

			#self.mc.reset()
			self.hp.power_off()

			if cw:
				cold[counter]=coldval
				hot[counter]=hotval
			else:
				cold[k*self.multval]=coldval
				hot[k*self.multval]=hotval

			counter = counter+1

		return cold,hot

	def VerifySetup( self, event ):

		self.UpdateVariables()

		self.SetupInstruments()
		self.exa.set_span(self.bw*2)

		self.meas_delay = float(self.exa.get_sweep_time())
		self.measdelay.SetValue(str(self.meas_delay))


		f = (self.fstart+self.fstop)/(2*self.multval)
		self.psg.set_frequency(f)
		time.sleep(self.meas_delay)

		val = self.exa.marker_getvalue()

		self.exa.set_reflevel(float(val)+25)
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
		roomtemp = float(self.roomtemp_k.GetValue())

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

			enr_caled = pd.read_csv(calfilepath,index_col=0)

			df['enr(K)'] = np.interp(df.index,enr_caled.index,enr_caled['T(K)'])
			df['T(K)'] = (df['enr(K)'] - df['Y']*df['rt(K)']) / (df['Y']-1)

			outfilename = safeFname(self.outpath,self.output_filename.GetValue(),'.csv')
			df.to_csv(outfilename)

	def hotcold_chopped_pressed( self, event ):
		event.Skip()
		
		self.ln2cold, self.ln2hot = self.SweepOnce()
		self.Calculate_LN2()

	def Calculate_LN2( self ):
		
		thot = float(self.ln2_thot.GetValue())
		tcold = float(self.ln2_tcold.GetValue())

		df = pd.DataFrame(index=self.ln2cold.keys())
		df['ln2cold(dBm)'] = self.ln2cold.values()
		df['ln2hot(dBm)'] = self.ln2hot.values()
		df['Ylog'] = df['ln2hot(dBm)']-df['ln2cold(dBm)']
		df['Y'] = 10**(df['Ylog']/10)

		df['cold(K)'] = tcold
		df['hot(K)'] = thot

		df['T(K)'] = (df['hot(K)'] - df['Y']*df['cold(K)']) / (df['Y']-1)

		outfilename = safeFname(self.outpath,self.output_filename.GetValue(),'.csv')
		df.to_csv(outfilename)

	def create_ns_calfile( self, event ):
		rxpath = self.rx_tsys_in.GetPath()
		nspath = self.ns_unknown_in.GetPath()

		caled_rx = pd.read_csv(rxpath,index_col=0)
		df = pd.read_csv(nspath,index_col=0)

		trx = np.interp(df.index,caled_rx.index,caled_rx['T(K)'])

		df['T(K)'] = trx*(df['Y']-1)+df['Y']*df['rt(K)']
		df['ENR'] = (df['T(K)']-df['rt(K)'])/df['rt(K)']
		df['ENR(dB)']=10*np.log10(df['ENR'])

		outfilename = safeFname(self.outpath,self.ns_cal_filename.GetValue(),'.csv')
		df.to_csv(outfilename)

	def voltage_bias_checked( self, event ):
		event.Skip()

		self.m_checkBox1.Disable()
		self.m_checkBox2.Enable()
		self.m_textCtrl27.Enable()
		self.m_textCtrl28.Enable()

		self.m_checkBox2.SetValue(False)
		self.m_textCtrl29.Disable()
		self.m_textCtrl26.Disable()

	def current_bias_checked( self, event ):
		event.Skip()

		self.m_checkBox1.Enable()
		self.m_checkBox2.Disable()
		self.m_textCtrl27.Disable()
		self.m_textCtrl28.Disable()

		self.m_checkBox1.SetValue(False)
		self.m_textCtrl29.Enable()
		self.m_textCtrl26.Enable()


if __name__ == '__main__':
	a = ENR()