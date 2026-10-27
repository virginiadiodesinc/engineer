#vna class copied from scikit-rf, and then cleaned up to work with PyVISA >1.5 and Python3
#snd 05/12/2021

import numpy as np
import pandas as pd
import pyvisa
import time

#import ..mathFunctions as mf
#may need to rewrite these functions in the future?

class PNA():

	def __init__(self, address=16, channel=1, timeout_ms=5000, **kwargs):
		rm = pyvisa.ResourceManager()
		self.inst = rm.open_resource("GPIB::%s::INSTR"%address)
		self.channel = channel
		self.inst.timeout = timeout_ms
		self.set_data_precision()

	################# high level functions from vdi.vi.vna ###########
	################# maybe should be in a separate class? ###########

	''' S Parameters
	Sets up s-parameter measurements for a given set of ports
	
	This command 
		1. deletes all current measurments
	#. creates s-parameter measurements for the given port set.
	#. sets display format to `form`
	#. couples y-scale
	
	Parameters 
	------------
	ports : list of ints, str
		ports to measure on (ie [1,2])
		or name of measurement (ie "S21")
		
	form : str
		the format. see :func:`set_display_format`.
	'''
	def setup_s_parameters(self, if_bw = 1000, ports = [1,2], form = 'mlog'):
		self.delete_all_meas()
		
		if isinstance(ports,list):
			port_list = [(y,x) for x in ports for y in ports]
				#create traces
			for k in port_list:
				self.create_meas('s%i%i'%k,'s%i%i'%k,True)
		elif isinstance(ports,str):
			self.create_meas('%s'%ports,'%s' %ports,True)
		else:
			raise(ValueError('bad input'))
		self.corr_state_of_channel = False
		# set display to log mag
		self.set_display_format_all(form)
		self.if_bw = if_bw
		self.set_yscale_couple()
		self.continuous= True
		#self.timeout = 10

	''' Wave Quantities
	Sets up wave-quantitiy measurements for a given set of ports
	
	This command:
	
	1. deletes all current measurments
	#. creates a/b wave measurements for the given port set.
	#. sets display format to `form`
	#. couples y-scale
	
	Parameters 
	------------
	ports : list of ints
		ports to measure on (ie [1,2])
		
	form : str
		the format. see :func:`set_display_format`.
	'''
	def setup_wave_quantities(self, ports = [1,2], form = 'mlog', 
		if_bw=1000,  yscale_couple = True, yscale_auto=True, 
		arch = 'TXRX-TXRX'):

		self.delete_all_meas()
		#create traces

		#import pdb;pdb.set_trace()
		if arch == 'TXRX-TXRX':
			for k in ports:
				self.create_meas('a%i'%k,'a%i, %i'%(k,k),True)
				self.create_meas('b%i'%k,'b%i, %i'%(k,k),True)
		elif arch == 'TXRX':
			k= ports[0]
			self.create_meas('a%i'%k,'a%i, %i'%(k,k),True)
			self.create_meas('b%i'%k,'b%i, %i'%(k,k),True)
		elif arch == 'TXRX-RX':
			p1,p2 = ports
			self.create_meas('a%i'%(p1),'a%i, %i'%(p1,p1),True)
			self.create_meas('b%i'%(p1),'b%i, %i'%(p1,p1),True)
			self.create_meas('b%i'%(p2),'b%i, %i'%(p2,p1),True)
		elif arch == 'TX-RX':
			p1,p2 = ports
			self.create_meas('a%i'%(p1),'a%i, %i'%(p1,p1),True)
			self.create_meas('b%i'%(p2),'b%i, %i'%(p2,p1),True)
		self.set_display_format_all(form)

		self.if_bw =  if_bw
		self.continuous = True
		
		self.sweep()

		if yscale_auto:
			self.set_yscale_auto()
		if yscale_couple:
			self.set_yscale_couple()

	################# end high level functions from vdi.vi.vna #######
	################# maybe should be in a separate class? ###########


	################## functions from vdi.vna ########################

	def fom(self, fstart, fstop, n, m, fif_mhz, rfpower=None, lopower=None, channel=1, offset_on=3):
		#n is RF mult
		#m is LO mult
		#self.preset()

		self.fom_disp("Primary")
		self.fom_start(50e9,1)
		self.fom_div(n=n,rng=2)
		self.fom_div(n=m,rng=4)
		self.fom_offset(fif_mhz*1e6)
		self.fom_mult(n=0,rng=3) #set if multiplier to 0
		
		if offset_on == 3:
			self.fom_offset(fif=(-1*fif_mhz/m*1e6),rng=4)
		else:#the offset should be on 1
			self.fom_offset(fif=(-1*fif_mhz/n*1e6),rng=2)
		
		self.fom_state()
		self.fom_start(fstart*1e9,1)
		self.fom_stop(fstop*1e9,1)
		self.pow_couple(state=0)
		self.power_on()

		if rfpower is not None:
			self.pow_ampl(rfpower,1)
			self.pow_ampl(rfpower,2)
		if lopower is not None:
			self.pow_ampl(lopower,3)
			self.pow_ampl(lopower,4)

	#Set display axis. Options are: Primary, Source, Source2, Receivers
	def fom_disp(self, axis="Primary", channel=1):
		self.inst.write("SENS%d:FOM:DISP:SEL '%s'" %(channel, axis))

	#Set start frequency. rng: 1=Primary, 2=RF, 3=IF, 4=LO
	def fom_start(self, fstart, rng, channel=1):
		self.inst.write("SENS%d:FOM:RANG%d:FREQ:STAR %f" %(channel,rng,fstart))

	#Set stop frequency. rng: 2=RF, 3=IF, 4=LO
	def fom_stop(self, fstop, rng, channel=1):
		self.inst.write("SENS%d:FOM:RANG%d:FREQ:STOP %f" %(channel,rng,fstop))

	#Set divisor. rng: 2=RF, 3=IF, 4=LO
	def fom_div(self, n, rng, channel=1):
		self.inst.write("SENS%d:FOM:RANG%d:FREQ:DIV %d" %(channel,rng,n))

	#Set multiplier. rng: 2=RF, 3=IF, 4=LO
	def fom_mult(self, n, rng=3, channel=1):
		self.inst.write("SENS%d:FOM:RANG%d:FREQ:MULT %d" %(channel,rng,n))

	#Set range offset. rng: 2=RF, 3=IF, 4=LO
	def fom_offset(self, fif, rng=3, channel=1):
		self.inst.write("SENS%d:FOM:RANG%d:FREQ:OFFS %f" %(channel,rng,fif))

	#enable/disable FOM
	def fom_state(self, state=1, channel=1):
		self.inst.write("SENS%d:FOM:STAT %d" %(channel,state))

	def pow_couple(self, state=0, channel=1):
		self.inst.write("SOUR%d:POW:COUP %d" %(channel,state))

	def pow_ampl(self, plvl, port, channel=1):

		if type(port) == int:
			self.inst.write("SOUR%d:POW%d:LEV:IMM:AMPL %f" %(channel,port,plvl))
		else: #String handling added from ks_mixer PNA control file - not sure if it's necessary
			print("Port should be an int")
			#self.inst.write("SOUR%d:POW:LEV:IMM:AMPL %f, \"%s\"" %(channel,plvl,port))

	#state: AUTO/ON/OFF. port: 1/2/3/4
	def pow_mode(self, state, port, channel=1):
		
		if type(port) == int:
			self.inst.write("SOUR%d:POW%d:MODE %s" %(channel,port,state))
		else:
			print("Port should be an int")
			#self.inst.write("SOUR%d:POW:MODE %s, \"%s\"" %(channel,state,port))

	def preset(self):
		self.inst.write("SYST:PRES;*OPC?")

	def rf_power(self, state):
		if state:	state = 'ON'
		else:		state = 'OFF'
		self.inst.write("OUTP %s"%state)

	def power_on(self):
		self.pow_mode('AUTO',1)
		self.pow_mode('AUTO',2)
		self.pow_mode('ON',3)
		self.pow_mode('ON',4)

	def power_off(self):
		self.pow_mode('OFF',1)
		self.pow_mode('OFF',2)
		self.pow_mode('OFF',3)
		self.pow_mode('OFF',4)

	#Frequency in GHz
	def set_frequency(self, frequency,channel = 1):
		val = frequency * 1e9
		self.inst.write('sens%i:FREQ %f'%(channel,val)) 
	def get_frequency(self, channel = 1):
		frequency = float(self.inst.ask_for_values('sens%i:FREQ?'%(channel)))
		return frequency / 1e9
	frequency=property(get_frequency,set_frequency)

	################## end functions from vdi.vna ########################

	############# functions that alex wrote, and came from skrf.vi.vna ##############

	#Identifying string for the instrument
	def idn(self):
		return self.inst.query('*IDN?')

	#Ask for indication that operations complete
	def opc(self):
		return self.inst.query('*OPC?')

	#Set continuous sweeping ON/OFF
	def get_continuous(self):
		return ('CONT' in self.inst.query('sense:sweep:mode?'))
	def set_continuous(self, val):
		if val:	self.inst.write('sense:sweep:mode cont')
		else:	self.inst.write('sense:sweep:mode hold')
	continuous=property(get_continuous,set_continuous)

	#use 32 bits for data and 64 bits for frequency according to Keysight documentation
	def set_data_precision(self, bits=32):
		self.inst.write('FORM ascii')
	#"""
	#returns a pandas.DataFrame with S parameter data
	def get_sdata(self):
		#fixed format always real imaginary
		self.set_snp_format('ri')

		data = self.inst.query_ascii_values('Calc:Data:SnP?')
		#this is a serial list of columns with frequency first
		#then S11, S21, S12, S22, (real,imaginary) in order

		npoints = self.get_f_npoints()
		numchunks = len(data)/npoints

		split_array = np.array_split(data,numchunks)
		split_array = np.transpose(split_array)

		if numchunks==3: #then there is only one port data
			col_names = ['Freq (Hz)','S11_re','S11_im']
		elif numchunks==9: #then there is two port data
			col_names = ['Freq (Hz)','S11_re','S11_im',\
			'S21_re','S21_im','S12_re','S12_im',\
			'S22_re','S22_im']
		else:
			raise ValueError('get_sdata failed, erroneous number of columns of data')

		return pd.DataFrame(split_array,columns=col_names)

	#returns receiver data for all wave quantities
	def get_wq(self, cnum=1):
		out = {}
		out['Freq']=self.get_xaxis(cnum=cnum)

		for name, parm in self.get_meas_list():
			self.select_meas(name)
			out[name]=(self.get_rdata(cnum=cnum))

		return out

	def get_xaxis(self, cnum=1):
		return self.inst.query_ascii_values('calc%i:X?' %cnum)

	# reverting this to avoid potential issues, but left it in for later
	# def get_xaxis(self, cnum=1, firmware_ver=10):
	# 	'''
	# 	the older firmware SCPI command only works if you sweep() first
	# 	the newer command works any time
	# 	'''
	# 	if firmware_ver > 14:
	# 		return self.inst.query_ascii_values("CALC1:MEAS:X?")
	# 	else:
	# 		return self.inst.query_ascii_values('calc%i:X?' %cnum)

	def get_rdata(self, cnum=1):
		self.inst.write('calc%i:par:sel %s'%(cnum, self.get_active_meas()))
		return self.inst.query_ascii_values('calc%i:data? %s'%(cnum, 'FDATA'))

	def get_fdata(self, measnum=1, channel=1):

		'''
		new function by SND 10/27/2023
		this only works on firmware version 15.XX or newer
		'''
		return self.inst.query_ascii_values(f"CALC{channel}:MEAS{measnum}:DATA:FDATA?")



	#Initiates a sweep and waits for it to complete before returning
	#If vna is in continuous sweep mode then this puts it back
	def sweep(self, wait=True):
		was_cont = self.get_continuous()
		#Set channel to accept one trigger, then to hold
		#OPC holds off subsequent commands and places a "1" on the output buffer
		if wait:
			out = bool(self.inst.query("SENS:SWE:MODE SINGle;*OPC?"))
		else:
			self.inst.write("SENS:SWE:MODE SINGle")
			return None
		self.set_continuous(was_cont)
		return out

	''' Sweep Type
	Sets the type of analyzer sweep mode. First set sweep type, then set sweep
	parameters such as frequency or power settings.

	Parameters
	-------------
	val: str
		Choose from:
			LINear | LOGarithmic | POWer | CW | SEGMent | PHASe
			Note: SWEep TYPE cannot be set to SEGMent if there
			are no segments turned ON.
	'''
	def set_sweep_type(self,val):
		self.inst.write('sense%i:sweep:type %s'%(self.channel,val))
	def get_sweep_type(self):
		return self.inst.query('sense%i:sweep:type?'%self.channel)
	sweep_type = property(get_sweep_type, set_sweep_type)

	''' Sweep Mode
	Sets the number of trigger signals the specified channel will ACCEPT.
	See Triggering the PNA Using SCPI.

	Parameters
	-------------
	val: str
		Trigger mode. Choose from:
		HOLD - channel will not trigger
		CONTinuous - channel triggers indefinitely
		GROups - channel accepts the number of triggers specified with the last
		SENS:SWE:GRO:COUN <num>. This is one of the PNA overlapped
		commands. Learn more.
		SINGle - channel accepts ONE trigger, then goes to HOLD.
	'''
	def set_sweep_mode(self,val):
		self.write('sense%i:sweep:mode %s'%(self.channel,val))
	def get_sweep_mode(self):
		return self.inst.query('sense%i:sweep:mode?'%self.channel)
	sweep_mode = property(get_sweep_mode, set_sweep_mode)

	''' Trigger Mode
	Sets and reads the trigger mode for the specified channel.
	This determines what EACH signal will trigger.

	values
	----------

	['channel','sweep','point','trace']

	'''
	def set_trigger_mode(self,val):
		if val.lower() not in ['channel','sweep','point','trace']:
			raise ValueError('value must be a boolean')
		self.inst.write('sense%i:sweep:trigger:mode %s'%(self.channel, val))
	def get_trigger_mode(self):
		return self.inst.query('sense%i:sweep:trigger:mode?'%self.channel)
	trigger_mode = property(get_trigger_mode, set_trigger_mode)

	''' Trigger Source
	Sets the source of the sweep trigger signal. This command is
	a super-set of INITiate:CONTinuous which can NOT set the
	source to External.

	values
	--------

	EXTernal - external (rear panel) source.
	IMMediate - internal source sends continuous trigger signals
	MANual - sends one trigger signal when manually triggered from
		the front panel or INIT:IMM is sent.
	'''
	def set_trigger_source(self,val):
		self.inst.write('trigger:sequence:source %s'%val)
	def get_trigger_source(self):
		return self.inst.query('trigger:sequence:source?')
	trigger_source = property(get_trigger_source, set_trigger_source)

	#send a manual trigger signal
	def trigger(self):
		self.inst.write('INIT:IMM')

	#send a manual trigger signal, and don't return until operation is completed
	def trigger_and_wait_till_done(self):
		self.trigger()
		self.opc()

	## power
	''' Power Level
	Set the RF power level

	Parameters
	-----------
	num : float
		Source power in dBm
	'''
	def set_power_level(self, num, cnum=None, port=None):
		if cnum is None:	cnum = self.channel
		if port is None:	port = self.port
		self.inst.write('SOURce%i:POWer%i %f'%(cnum, port, num))
	def get_power_level(self):
		return float(self.inst.query('SOURce:POWer?'))
	power_level = property(get_power_level, set_power_level)

	''' Port Power
	Turn a given port's power on or off or auto

	Parameters
	----------
	mode  : str
		['on','off', 'auto']
	port : int
		the port (duh)
	'''
	def toggle_port_power(self, mode = 'on', port =1):
		if mode is True:	mode = 'on'
		elif mode is False:	mode = 'off'
		self.inst.write('source%i:power%i:mode %s'%(self.channel,port, mode))

	## IO - Frequency related
	''' Start frequency in Hz '''
	def get_f_start(self):
		return float(self.inst.query('sens%i:FREQ:STAR?'%(self.channel)))
	def set_f_start(self,f):
		self.inst.write('sens%i:FREQ:STAR %f'%(self.channel,f))
	f_start = property(get_f_start, set_f_start)

	''' Stop frequency in Hz '''
	def get_f_stop(self):
		return float(self.inst.query('sens%i:FREQ:STOP?'%(self.channel)))
	def set_f_stop(self,f):
		self.inst.write('sens%i:FREQ:STOP %f'%(self.channel,f))
	f_stop = property(get_f_stop, set_f_stop)

	''' Number of points for the measurement '''
	def get_f_npoints(self):
		return int(self.inst.query('sens%i:swe:poin?'%(self.channel)))
	def set_f_npoints(self, n):
		self.inst.write('sens%i:swe:poin %i'%(self.channel,n))
	f_npoints = property(get_f_npoints, set_f_npoints)
	npoints = f_npoints

	''' Continuous Wave Frequency
	Sets the Continuous Wave (or Fixed) frequency. Must also send
	SENS:SWEEP:TYPE CW to put the analyzer into CW sweep mode.

	Parameters
	--------------
	val : number
		CW frequency. Choose any number between the minimum and
		maximum frequency limits of the analyzer. Units are Hz.

	This command will accept MIN or MAX instead of a numeric
	parameter. See SCPI Syntax for more information
	'''
	def set_frequency_cw(self, val):
		self.inst.write('sens%i:FREQ %f'%(self.channel,val))
	def get_frequency_cw(self):
		return float(self.inst.query('sens%i:FREQ?'%(self.channel)))
	frequency_cw = property(get_frequency_cw, set_frequency_cw)

	##  IO - S-parameter and  Networks
	#the output format for snp data
	def set_snp_format(self, val= 'ri'):
		if val.lower() not in ['ma','ri','auto','disp']:
			raise ValueError('bad value for `val`')
		self.inst.write('MMEM:STOR:TRAC:FORM:SNP %s'%val)
	def get_snp_format(self):
		return self.inst.query('MMEM:STOR:TRAC:FORM:SNP?')
	snp_format = property(get_snp_format, set_snp_format)

	# def get_data(self, char='SDATA', cnum = None):
	#	 '''
	#	 Get data for current active measuremnent

	#	 Note that this doesnt do any sweep timing. It just gets whatever
	#	 data is in the registers according to char.  If you want the
	#	 data to be returned after a sweep has completed

	#	 Parameters
	#	 ------------
	#	 char : [SDATA, FDATA, RDATA]
	#		 type of data to return

	#	 '''
	#	 if cnum is None:
	#		 cnum = self.channel

	#	 self.inst.write('calc%i:par:sel \"%s\"'%(cnum, self.get_active_meas()))
	#	 data = npy.array(self.ask_for_values('CALC%i:Data? %s'%(cnum, char)))

	#	 if char.lower() == 'sdata':
	#		 #data = mf.scalar2Complex(data)
	#		 raise NotImplementedError

	#	 return data

	''' Switch Terms
	Get switch terms and return them as a tuple of Network objects.

	Returns
	--------
	forward, reverse : oneport switch term Networks
	'''
	def get_switch_terms(self, ports = [1,2]):
		raise NotImplementedError
		#need to rewrite the get_data stuff first

		p1,p2 = ports
		self.delete_all_meas()
		self.create_meas('forward switch term', 'a%i/b%i,%i'%(p2,p2,p1),True)
		forward = self.get_network()

		self.delete_all_meas()
		self.create_meas('reverse switch term', 'a%i/b%i,%i'%(p1,p1,p2),True)
		reverse = self.get_network()
		self.delete_all_meas()
		return forward, reverse

	## MEASUREMENT/TRACES
	''' Number of Traces
	The number of measurement traces that exist on the current channel

	Note that this may not be the same as the number of traces
	displayed because a measurement may exist, but not be associated
	with a trace.

	'''
	@property
	def ntraces(self):
		n = self.get_meas_list()
		if n is None:	return 0
		else:			return len(n)

	''' IF bandwidth '''
	@property
	def if_bw(self):
		return float(self.inst.query('sens%i:band?'%self.channel))

	@if_bw.setter
	def if_bw(self,n):
		self.inst.write('sens%i:band %i'%(self.channel,n))

	''' Display Trace
	Display a given measurement on specified trace number.

	Parameters
	------------
	window_n : int
		window number. If None, active window is used.
	trace_n : int
		trace number to display on. If None, a new trace is made.
	'''
	def set_yscale_auto(self, window_n=None, trace_n=None):
		if window_n is None:	window_n = ''
		if trace_n is None:		trace_n = self.ntraces+1
		self.inst.write('disp:wind%s:trac%s:y:scale:auto'%(str(window_n), str(trace_n)))

	''' Get current Trace
	Get window number and trace number either for the current measurement
	(if meas is empty) or for a specific measurement

	Returns
	----------
	out :  tuple
		tuple of the form (window_n, trace_n)
	'''
	def get_win_trace(self, meas=''):
		if meas:
			self.select_meas(meas)
		window_n = int(self.inst.query('CALC:PAR:WNUM?')[1:])
		trace_n = int(self.inst.query('CALC:PAR:TNUM?')[1:])
		return (window_n, trace_n)

	''' Get a list of existing measurements
	Returns
	----------
	out :  list
		list of tuples of the form, (name, measurement)
	'''
	def get_meas_list(self):
		meas_list = self.inst.query("CALC%i:PAR:CAT:EXT?"%self.channel)
		
		# if there isnt a single comma, then there arent any measurments
		meas = meas_list[1:-1].split(',')
		if len(meas)==1:	return None
		
		return [(meas[k],meas[k+1]) for k in range(0,len(meas)-1,2)]

	''' Get list of existing window numbers
	Returns
	----------
	out :  list
		list of window numbers
	'''
	def get_window_list(self):
		window_list = self.inst.query("DISP:CAT?")
		windows = window_list[1:-1].split(',')
		
		if 'EMPTY' in window_list:	return None
		return [int(k) for k in windows]

	''' Get the name of the active measurement '''
	def get_active_meas(self):
		return self.inst.query("SYST:ACT:MEAS?")

	''' Delete a measurement with name `name` '''
	def delete_meas(self,name):
		self.inst.write('calc%i:par:del %s'%(self.channel, name))

	''' Delete all measurements '''
	def delete_all_meas(self):
		self.inst.write('calc%i:par:del:all'%self.channel)

	def get_active_cset(self,channel =None, form = 'name'):
		if channel is None:	channel  = self.channel

		form = form.lower()
		if form not in ['name','guid']:
			raise ValueError ('bad value for `form`')

		out = self.inst.query('SENS%i:CORR:CSET:ACT? %s'%(channel,form) )[1:-1]

		if out =='No Cal Set selected':	return None
		else:							return out

	''' Create a new measurement.
	Parameters
	------------
	name : str
		name given to measurment
	meas : str
		something like
		* S11
		* a1/b1,1
		* A/R1,1
		* ...
	disp : bool
		to display the measurement or not

	Examples
	----------
	>>> p = PNA()
	>>> p.create_meas('my_meas', 'A/R1,1', True)
	'''
	def create_meas(self,name, meas, disp):
		self.inst.write('calc%i:par:def:ext \"%s\", \"%s\"'%(self.channel, name, meas))
		if disp:	self.display_trace(name)

	''' Make a specified measurement active
	Parameters
	------------
	name : str
		name of measurement. See :func:`get_meas_list`
	'''
	def select_meas(self,name):
		self.inst.write('calc%i:par:sel \"%s\"'%(self.channel, name))

	''' Set window arrangement for currently active measurements.
	Parameters
	------------
	arr : str
		Window arrangement.

	Choose from:
	* TILE - tiles existing windows
	* CASCade - overlaps existing windows
	* OVERlay - all traces placed in 1 window
	* STACk - 2 windows
	* SPLit - 3 windows
	* QUAD - 4 windows
	'''
	def set_window_arrangement(self, arr='overlay'):
		self.inst.write('disp:arr %s'%str(arr))

	''' Display a given measurement on specified trace number.
	Parameters
	------------
	name : str
		name of measurement. See :func:`get_meas_list`
	window_n : int
		window number. If None, active window is used.
	trace_n : int
		trace number to display on. If None, a new trace is made.
	form : str
		display format (see set_display_format())
	'''
	def display_trace(self,  name = '',window_n = None, trace_n=None, form='MLOG'):
		if window_n is None:	window_n = ''
		if trace_n is None:		trace_n = self.ntraces+1
		self.inst.write('disp:wind%s:trac%s:feed \"%s\"'%(str(window_n), str(trace_n), name))
		self.select_meas(name)
		self.set_display_format(form)

	''' Set the display format
	Choose from:
	* MLINear
	* MLOGarithmic
	* PHASe
	* UPHase 'Unwrapped phase
	* IMAGinary
	* REAL
	* POLar
	* SMITh
	* SADMittance 'Smith Admittance
	* SWR
	* GDELay 'Group Delay
	* KELVin
	* FAHRenheit
	* CELSius
	'''
	def set_display_format(self, form):
		self.inst.write('calc%i:form %s'%(self.channel,form))

	''' Set the display format for all measurements
	Choose from:
	* MLINear
	* MLOGarithmic
	* PHASe
	* UPHase 'Unwrapped phase
	* IMAGinary
	* REAL
	* POLar
	* SMITh
	* SADMittance 'Smith Admittance
	* SWR
	* GDELay 'Group Delay
	* KELVin
	* FAHRenheit
	* CELSius
	'''
	def set_display_format_all(self, form):
		self.func_on_all_traces(self.set_display_format, form)

	''' Run a function on all traces are active
	Loop through all measurements, and making each active, then
	subsequently run a command.

	Parameters
	------------
	func : func
		The function to run while each trace is active

	Examples
	---------
	>>> p = PNA()
	>>> p.func_on_all_traces(p.set_display_format, 'smith')
	'''
	def func_on_all_traces(self,func, *args, **kwargs):
		for name,parm in self.get_meas_list():
			self.select_meas(name)
			func(*args,**kwargs)

	''' Normalizes current measurement or specific measurements
	Parameters
	------------
	meas : list of strings or single string
		measurements to normalize
	op : string
		math operation to be applied.
		Choose from:

		* normal (no normalization active)
		* add
		* subtract
		* multiply
		* DIVide
	write_memory: bool
		write current trace to memory (True) or just activate normalisation (False)
	'''
	def normalize(self, meas=[], op='DIV', write_memory=True):
		if not meas:
			meas = self.get_active_meas()
		else: self.select_meas(meas)
		if write_memory:
			self.inst.write('CALC:MATH:MEM')
		self.inst.write('CALC:MATH:FUNC %s'%str(op))
	"""
	''' Enables time domain transform for current trace
	Parameters
	------------
	meas : list of strings or single string
		measurements to activate transform for
	center : float
		center time in [s]
	span : float
		span time in [s]
	'''
	def enable_transform(self, meas=[], center=0, span=2e-9):
		if not meas:
			meas = self.get_active_meas()
		else: self.select_meas(meas)
		self.inst.write('CALC:TRAN:TIME:CENT %e'%center)
		self.inst.write('CALC:TRAN:TIME:SPAN %e'%span)
		self.inst.write('CALC:TRAN:TIME:STAT ON')

	''' Enables time domain gating for current measurement or specified measurements
	Parameters
	------------
	meas : list of strings or single string
		measurements to enable gating for
	center : float
		center time in [s]
	span : float
		span time in [s]
	'''
	def enable_gating(self, meas=[], center=0, span=0.5e-9):
		if not meas:
			meas = self.get_active_meas()
		else: self.select_meas(meas)
		self.inst.write('CALC:FILT:TIME:CENT %e'%center)
		self.inst.write('CALC:FILT:TIME:SPAN %e'%span)
		self.inst.write('CALC:FILT:TIME:STAT ON')

	''' Disables time domain gating for current measurement or specified measurements
	Parameters
	------------
	meas : list of strings or single string
		measurements to disable gating for
	'''
	def disable_gating(self, meas=[]):
		if not meas:	meas = self.get_active_meas()
		else:			self.select_meas(meas)
		self.inst.write('CALC:FILT:TIME:STAT OFF')

	''' Set y-scale 'per division' value for given or current measurement
	Parameters
	------------
	pdiv : float
		per division
	rlev : float
		reference level
	rpos : int
		reference position on y-scale
	'''
	def set_yscale(self, meas='', pdiv=5, rlev=0, rpos=8):
		if not meas:	meas = self.get_active_meas()
		(w, t) = self.get_win_trace(meas=meas)
		self.inst.write('DISP:WIND%i:TRAC%i:Y:PDIV %f'%(w, t, pdiv))
		self.inst.write('DISP:WIND%i:TRAC%i:Y:RLEV %f'%(w, t, rlev))
		self.inst.write('DISP:WIND%i:TRAC%i:Y:RPOS %f'%(w, t, rpos))
	"""
	""" Set y-scale coupling
	Parameters
	------------
	method : ['off','all','window']
		controls the coupling method
	"""
	def set_yscale_couple(self, method= 'all' ,window_n = None, trace_n=None):
		if window_n is None:	window_n =''
		if trace_n is None:		trace_n =self.ntraces+1
		self.inst.write('disp:wind%s:trac%s:y:coup:meth %s'%(str(window_n), str(trace_n), method))
	"""

	## Correction related operations
	''' Toggle correction for given channel '''
	def set_corr_state_of_channel(self, val):
		val = 'on' if val else 'off'
		self.inst.write('sense%i:corr:state %s'%(self.channel, val))
	''' Return correction status for given channel '''
	def get_corr_state_of_channel(self):
		return bool(int(self.inst.query('sense%i:corr:state?'%self.channel)))
	corr_state_of_channel = property(get_corr_state_of_channel, set_corr_state_of_channel)

	''' Toggle correction for given measurement '''
	def set_corr_state_of_meas(self, val):
		val = 'on' if val else 'off'
		self.inst.write('calc%i:corr:state %s'%(self.channel, val))
	''' Return correction status for given measurement '''
	def get_corr_state_of_meas(self):
		return bool(int(self.inst.query('calc%i:corr:state?'%self.channel)))
	corr_state_of_meas = property(get_corr_state_of_meas, set_corr_state_of_meas)

	''' Get list of calsets on current channel
	Parameters
	------------
	form : 'name','guid'
		format of returned values

	Returns
	---------
	cset : list
		list of csets by guid or name
	'''
	def get_cset_list(self, form = 'name'):
		a =  self.inst.query('SENSE%i:CORRection:CSET:CATalog? %s'%(self.channel,form))
		return a[1:-1].split(',')

	''' Creates an empty calset '''
	def create_cset(self, name='skrfCal'):
		self.inst.write('SENS%i:CORR:CSET:CRE \'%s\''%(self.channel,name))

	''' Deletes a given calset '''
	def delete_cset(self, name):
		self.inst.write('SENS%i:CORR:CSET:DEL \'%s\''%(self.channel,name))

	''' Get the active calset name for a give channel.
	Parameters
	-------------
	chawornnel : int
		channel to apply cset to
	form : 'name' or 'guid'
		form of `cset` argument
	'''
	def get_active_cset(self,channel =None, form = 'name'):
		if channel is None:	channel  = self.channel

		form = form.lower()
		if form not in ['name','guid']:
			raise ValueError ('bad value for `form`')

		out = self.inst.query('SENS%i:CORR:CSET:ACT? %s'%(channel,form) )[1:-1]

		if out =='No Cal Set selected':	return None
		else:							return out

	''' Set the current active calset.
	Parameters
	-------------
	cset: str
		name of calset
	channel : int
		channel to apply cset to
	apply_stim_values : bool
		should the cset stimulus values be applied to the channel.
	'''
	def set_active_cset(self, cset, channel=None, apply_stim_values=True ):
		if channel is None:	channel  = self.channel

		available_csets = self.get_cset_list()
		if cset not in available_csets:
			raise ValueError('%s not in list of available csets'%cset)

		self.inst.write('SENS%i:CORR:CSET:ACT \'%s\',%i'%(channel,cset,int(apply_stim_values) ))

	''' Save the activer calset '''
	def save_active_cset(self,channel=None):
		if channel is None:
			channel  = self.channel
		self.inst.write('sense%i:correction:cset:save'%channel)

	''' Get list of calibration coefficients for current calset '''
	def get_cal_coefs_list(self):
		out = self.inst.query('SENS%i:CORR:CSET:ETERM:cat?'%self.channel)[1:-1]
		# agilent mixes the delimiter with values! this requires that
		# we use regex to only split on comma's that follow parenthesis
		return re.split('(?<=\)),',out)
	cal_coefs_list = property(get_cal_coefs_list)

	############# end functions that alex wrote, and came from skrf.vi.vna ##############
	#"""