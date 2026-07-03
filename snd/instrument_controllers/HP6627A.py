# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 08:36:45 2022

@author: aleavesley
"""

"""Hewlett Packard 6627A DC Power Supply"""

import pyvisa
	
class PSU():
	#GBIP address XX
	def __init__(self, address="GPIB0::5::INSTR", **kwargs):
		rm = pyvisa.ResourceManager()

		if type(address) == int:
			address = f'GPIB0::{address}::INSTR'
			
		self.inst = rm.open_resource(address)

		#check that we connected successfully
		inst_id = self.get_id()
		print(f'Connected to {inst_id} at address {address}')
	
	def __del__(self):
		try:	self.cleanup()
		except:	pass
	
	def cleanup(self):
		print("closing power supply")
		self.set_output(1,0)
		self.set_output(2,0)
		self.set_output(3,0)
		self.set_output(4,0)
		self.inst.close()

	def get_id(self):
		return self.inst.query('ID?')
		
	def set_voltdef(self, channel, value):
		return self.inst.write('VSET %i,%f' %(channel,value))
	
	def get_voltdef(self, channel):
		return float(self.inst.query('VSET? %i' %(channel)))
	
	def get_voltout(self,channel):
		return float(self.inst.query('VOUT? %i' %(channel)))
	
	def set_currdef(self, channel, value):
		return self.inst.write('ISET %i,%f' %(channel,value))
	
	def get_currdef(self,channel):
		return float(self.inst.query('ISET? %i' %(channel)))
	
	def get_currout(self,channel):
		return float(self.inst.query('IOUT? %i' %(channel)))
	
	def set_output(self,channel,state):
		return self.inst.write('OUT %i,%i' %(channel,state))
	#state options: 0=off and 1=on
	
	def get_output(self,channel):
		return self.inst.query('OUT? %i' %(channel))
	
	def set_OVP(self,channel,value):
		return self.inst.write('OVSET %i,%f' %(channel,value))
	
	def get_OVP(self,channel):
		return float(self.inst.query('OVSET? %i' %(channel)))
	
	def set_OCP(self,channel,value):
		return self.inst.write('OCP %i,%f' %(channel,value))
	
	def get_OCP(self,channel):
		return float(self.inst.query('OCP? %i' %(channel)))
	
	def set_allon(self, state):
		return self.inst.write('DCPON %i' %(state))
	#turns all channels as power on
	#state options: 0 = CC+ off, 1 = CC+ on, 2 = CC- off, 3 = CC- on
	
	def set_unmask(self, channel, mask):
		return self.inst.write('UNMASK %i,%i' %(channel,mask))
	#mask options: 0-255
	
	def get_unmask(self, channel):
		return self.inst.query('UNMASK? %i' %(channel))
	
	def set_delay(self,channel,delay):
		return self.inst.write('DLY %i,%f' %(channel,delay))
	#delay is in seconds from 0-32 seconds
	
	def get_delay(self,channel):
		return float(self.inst.query('DLY? %i' %(channel)))
	
	def reset_overvolt(self,channel):
		return self.inst.write('OVRST %i' %(channel))
	
	def reset_overcurr(self,channel):
		return self.inst.write('OCRST %i' %(channel))
	
	def set_poweron(self, state):
		return self.inst.write('PON %i' %(state))
	
	def get_poweron(self):
		return self.inst.query('PON?')
	
	def get_status(self, channel):
		return self.inst.query('STS? %i' %(channel))
	
	def get_totalstatus(self, channel):
		return self.inst.query('ASTS? %i' %(channel))
	
	def get_fault(self, channel):
		return self.inst.query('FAULT? %i' %(channel))
	
	def get_error(self):
		return self.inst.query('ERR?')
	
	def set_disponoff(self, state):
		return self.inst.query('DSP %i' %(state))
	#state options: 0=off and 1=on
	
	def get_disponoff(self):
		return self.inst.query('DSP?')
	
	def set_StoreSettings(self, register):
		return self.inst.write('STO %i' %(register))
	#register options: 1-10; each register can be stored for faster set-up between std operations
	
	def set_RecallSettings(self, register):
		return self.inst.write('RCL %i' %(register))
	
	def set_clear(self):
		return self.inst.write('CLR')
	#returns PSU to power on status and all paramneters are returned to intial power on values; registers are not impacted, PON bit is cleared
	
	def get_model(self):
		return self.inst.query('ID?')
	
	def get_selftest(self):
		return self.inst.query('TEST?')
	
	def set_CalMode(self,state):
		return self.inst.write('CMODE %i' %(state))
	#state options: 0=off and 1=on	
	
	def get_CalMode(self):
		return self.inst.query('CMODE?')
	
	def set_CCal(self, channel, Ilo, Ihi):
		return self.inst.write('IDATA %i,%f,%f' %(channel,Ilo,Ihi))
	#Ilo and Ihi are measured values for the calibration --> this command is used to calibrate the current settings 
	
	def set_currHigh(self,channel):
		return self.inst.write('IHI %i' %(channel))
	
	def set_currLow(self,channel):
		return self.inst.write('ILO %i' %(channel))
	
	def set_VCal(self, channel, Vlo, Vhi):
		return self.inst.write('IDATA %i,%f,%f' %(channel,Vlo,Vhi))
	#Vlo and Vhi are measured values for the calibration --> this command is used to calibrate the voltage settings 
	
	def set_voltHigh(self,channel):
		return self.inst.write('VHI %i' %(channel))
	
	def set_voltLow(self,channel):
		return self.inst.write('VLO %i' %(channel))
	
	def set_OVCal(self, channel):
		return self.inst.write('OVCAL %i' %(channel))
	#cause the channel to go through the overvoltage calibration routine
	
	def get_firmware(self):
		return self.inst.query('ROM?')
	#gets the installed version of the hardware's firmware
	
	
	