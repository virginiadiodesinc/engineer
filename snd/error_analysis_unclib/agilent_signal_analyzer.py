#Class used to control the Agilent PXA
#CXS (5/14/2021) - Adapted from SND (1/28/2014)

import pyvisa
import platform
import pandas as pd
import numpy as np

PXA_ADDRESS = 18
PXA_CAL_DATA_PATH = ''

class PXA():
	#GPIB address 18 by default
	def __init__(self, address=PXA_ADDRESS, preset = True, use_cf = True, **kwargs):
		rm = pyvisa.ResourceManager()
		self.inst = rm.open_resource("GPIB0::%s"%address)
		if preset:	self.preset()
		
		#This variable should be added to any outgoing power value gotten from RF input
		if use_cf:
			self.PXAcalfactor = self.calfactor(platform.node())
		else:
			self.PXAcalfactor = 0
		
		#Turn off automatic alignments while remotely controlled
		self.inst.write(':CAL:AUTO OFF')
	
	def __del__(self):
		#Turn auto alignments back on
		try:	self.inst.write(':CAL:AUTO ON')
		except:	pass

	def set_trace_detector(self, det_type='NORM'):
		'''
		det_type can be
		NORM - normal
		AVER - RMS
		POS - Peak
		SAMP - Sample
		NEG - Negative Peak
		'''
		self.inst.write(f':SENS:CHP:DET:FUNC {det_type}')

	def get_sweep_time(self):
		return self.inst.query(':SENS:SWE:TIME?')

	def marker_setbandwidth(self, bw):
		self.inst.write(':CALC:MARK:FUNC BPOW')
		self.inst.write(f':CALC:MARK:FUNC:BAND:SPAN {bw} MHz')

	def marker_setcf(self, cf):
		self.inst.write(f':CALC:MARK:X {cf} MHz')

	def marker_getvalue(self):
		return self.inst.query('CALC:MARK1:Y?')

	def get_trace_with_x(self):
		#over GPIB
		trace = self.get_trace()
		center = self.get_center_freq()
		span = self.get_span()

		numpoints = len(trace)
		fstart = float(center)-float(span)/2
		fstop = float(center)+float(span)/2

		xaxis = np.linspace(fstart, fstop, numpoints)

		return pd.DataFrame(trace, index=xaxis)

	def get_trace(self):
		#over GPIB
		return self.inst.query_ascii_values(':TRAC:DATA? TRACE1')
	
	#Used to identify the PXA being used to correctly set a Cal Factor
	def calfactor(self, user):
		cf = 0
		try:
			cf = pd.read_excel(pd.ExcelFile(PXA_CAL_DATA_PATH), index_col = 0).to_dict()[user]['Calfactor']
			print('PXA calfactor of %s for %s' %(cf, user))
		except:
			print('No PXA calfactor found for %s. Using default of %s' %(user, cf))
		return cf
	
	#Property functions used to easily set and read center frequency in MHz
	def get_center_freq(self):
		return self.inst.query('FREQ:CENT?')
	#Returns 0 if your frequency is out of bounds (assumes 50ghz pxa) (SND)
	def set_center_freq(self, freq_mhz):
		self.inst.write('FREQ:CENT %s MHz' %(freq_mhz))
	
	#Property functions used to set and read continuous mode state (state is ON for on, OFF for off)
	def get_continuous_mode(self):
		return self.inst.query('INIT:CONT?')
	def set_continuous_mode(self, state):
		self.inst.write('INIT:CONT %s' %(state))
	
	
	#Property functions used to set and read the frequency span
	def set_span(self, freq_mhz):
		self.inst.write(':SENS:FREQ:SPAN %s MHz' %(freq_mhz))
	def get_span(self):
		return self.inst.query(':SENS:FREQ:SPAN?')
	
	
	#Property functions used to set and read res bandwidth
	def set_rbw(self, freq_hz):
		self.inst.write(':SENS:BWID:RES:AUTO OFF')
		self.inst.write(':SENS:BWID:RES %s Hz' %(freq_hz))
	def get_rbw(self):
		return self.inst.query(':SENS:BWID:RES?')
	
	#Property functions used to set and read vbw
	def set_vbw(self, freq_hz):
		self.inst.write(':SENS:BWID:VID:AUTO OFF')
		self.inst.write(':SENS:BWID:VID %s Hz' %(freq_hz))
	def get_vbw(self):
		return self.inst.query(':SENS:BWID:VID?')
	
	#Property functions used to set and read the number of points
	def set_numpoints(self, numpoints):
		self.inst.write(':SENS:SWE:POIN %s' %(numpoints))
	def get_numpoints(self):
		return self.inst.query(':SENS:SWE:POIN?')
	
	
	#Property functions used to set and read the reference level in dBm
	def set_reflevel(self, level):
		self.inst.write('DISP:WIND:TRAC:Y:RLEV %s dBm' %(level))
	def get_reflevel(self):
		return self.inst.query('DISP:WIND:TRAC:Y:RLEV?')
	
	
	#Property functions used to set and read the scale per division in dB
	def set_scalediv(self, scale):
		self.inst.write('DISP:WIND:TRAC:Y:PDIV %s DB' %(scale))
	def get_scalediv(self):
		return self.inst.query('DISP:WIND:TRAC:Y:PDIV?')
	
	
	#Creating properties so that settings can be treated like variables
	center_freq = property(get_center_freq,set_center_freq)
	continuous_mode = property(get_continuous_mode,set_continuous_mode)
	span = property(get_span,set_span)
	rbw = property(get_rbw,set_rbw)
	vbw = property(get_vbw,set_vbw)
	numpoints = property(get_numpoints,set_numpoints)
	reflevel = property(get_reflevel,set_reflevel)
	scalediv = property(get_scalediv,set_scalediv)
	
	
	def save_file(self,file_name):
		self.inst.write('MMEM:DATA "%s"' %(file_name))
	
	#saves in the default directory on PXA (SND)
	def screen_shot(self,file_name):
		self.inst.write('MMEM:STOR:SCR "%s"' %(file_name))
	
	def trigger_once(self):
		self.inst.write('*TRG')
	
	def trigger_once_2(self):
		self.inst.write('INIT:IMM')
	
	def preset(self):
		self.inst.write('SYST:PRES')
	
	def send_opcheck(self):
		return self.inst.query('*OPC?')

	#Returns the frequency and magnitude of the peak (I think)
	def peak_search(self, correct=False):
		self.inst.write(':CALC:MARK1:MAX')
		if correct:	return (self.inst.query('CALC:MARK1:X?'),str(float(self.inst.query('CALC:MARK1:Y?'))+self.PXAcalfactor))
		else:		return (self.inst.query('CALC:MARK1:X?'),self.inst.query('CALC:MARK1:Y?'))

	def set_rf_input(self):
		self.inst.write(':SENS:FEED RF')

	def set_correction_off(self):
		self.inst.write('SENS:CORR:CSET:ALL OFF')

	#Aligns all on the PXA
	def align(self, which='all'):
		self.inst.write(':CAL:NPEN')