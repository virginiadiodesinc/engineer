#nidaq controller to adjust UCA
#snd 1/25/2022

try:
	import nidaqmx
	from nidaqmx.system import System
	from nidaqmx.stream_readers import AnalogSingleChannelReader
	from nidaqmx.stream_readers import AnalogMultiChannelReader
except:
	print('pip install nidaqmx to use nidaq')

import numpy as np
import time
import pandas as pd

class DAQ():

	def __init__(self, name='Dev1', **kwargs):

		system = System.local()
		device = system.devices[name]
		self.name = name

	def set_voltage(self, voltage, channel):
		#this is primarily designed for UCA, so I'm limiting it to 0-5V for safety		
		if voltage >=0 and voltage <=5:
			with nidaqmx.Task() as task:
				task.ao_channels.add_ao_voltage_chan(f'{self.name}/ao{channel}') 
				task.write(voltage)
		else:
			print('voltage out of range, try something between 0 and 5')

	def get_voltage(self, channel):

		with nidaqmx.Task() as task:
			task.ai_channels.add_ai_voltage_chan(f'{self.name}/ai{channel}')
			return task.read()

class DAQStream():

	def __init__(self, devicename='Dev1', sample_rate=1e3, test_duration=1, channels=[], ranges=[], dummy=False, **kwargs):
		#sample rate in hz
		#test duration in seconds

		#names array of stuff like [ai0, ai1, ai2]
		#corresponding ranges like [1.0, 1.0, 1.0]

		system = System.local()
		self.device = system.devices[devicename]
		self.devicename = devicename

		self.num_channels = 0
		self.my_channels = []

		self.sample_rate = int(sample_rate)
		self.num_samples = int(float(test_duration)*self.sample_rate)

		if not dummy:
			self.my_task = nidaqmx.Task()
			self.add_multichannel(names=channels, ch_ranges=ranges)
		else:
			self.my_channels = channels
			self.num_channels = len(channels)
		
	def add_channel(self, name, ch_range):
		#name like ai0, ai1, etc.
		#ch_range can be [0,1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
		
		self.my_task.ai_channels.add_ai_voltage_chan(f'{self.devicename}/{name}',min_val=ch_range*-1,max_val=ch_range)
		self.my_channels.append(name)
		self.num_channels += 1
		
	def add_multichannel(self, names, ch_ranges):
		#names array of stuff like [ai0, ai1, ai2]
		#corresponding ranges like [1.0, 1.0, 1.0]
		
		for k,j in zip(names, ch_ranges):
			self.add_channel(k,j)
			
		
	def start_multichan_test(self):
		num_samples = self.num_samples
		sample_rate = self.sample_rate
		
		#print(f"Mode: {nidaqmx.constants.AcquisitionType.CONTINUOUS}\nRate: {sample_rate}\n# of Samples: {num_samples}\n")
		self.my_task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,samps_per_chan=num_samples)
		
		time_series = []
		read_array = np.zeros((self.num_channels,num_samples))

		with self.my_task as task:
			reader = AnalogMultiChannelReader(task.in_stream)
		
			dump_array = np.zeros((self.num_channels,10))
			reader.read_many_sample(dump_array,number_of_samples_per_channel=10)
			
			t1 = time.time()
			reader.read_many_sample(read_array, number_of_samples_per_channel=num_samples, timeout=nidaqmx.constants.WAIT_INFINITELY)
					
			t2 = time.time()
			
			time_series = np.linspace(t1,t2,num_samples)
		
		df = pd.DataFrame()
		
		for k,j in zip(self.my_channels,range(self.num_channels)):
			
			df[k] = read_array[j]
		
		df.index = time_series
		
		return df
	
# 	def start_singlechan_test(self, num_samples, sample_rate):
		
# 		self.my_task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,samps_per_chan=num_samples)
		
# 		time_series = []
# 		read_array = np.zeros(num_samples)
# #        print(type(read_array))
		
# 		with self.my_task as task:
# 			reader = AnalogSingleChannelReader(task.in_stream)
		
# 			dump_array = np.zeros(10)
# 			reader.read_many_sample(dump_array,number_of_samples_per_channel=10)
			
# 			t1 = time.time()
# 			reader.read_many_sample(read_array, number_of_samples_per_channel=num_samples, timeout=nidaqmx.constants.WAIT_INFINITELY)
					
# 			t2 = time.time()
			
# 			time_series = np.linspace(t1,t2,num_samples)
		
# 		df = pd.DataFrame()
# 		df['v'] = read_array
# 		df.index = time_series
		
# 		return df
