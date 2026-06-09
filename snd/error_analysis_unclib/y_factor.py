import metas_unclib as mu
import numpy as np
import pandas as pd
import pico_tc08
import agilent_signal_analyzer
import time

def connect_exa():
	exa = agilent_signal_analyzer.PXA()
	exa.preset()

	#exa.set_continuous_mode(1)
	exa.set_center_freq(70)
	exa.set_span(0)
	exa.set_rbw(8e6)
	exa.set_vbw(1)
	exa.set_trace_detector('AVER')
	return exa

def get_exa_data(exa):
	return exa.get_trace()

def connect_picoscope(channel):
	picoscope = pico_tc08.TC08()
	picoscope.activate_channel(channel)
	return picoscope

def get_temperature(picoscope, channel):
	return picoscope.get_data()[channel]

def generate_noise(val=293, noise=1.5, num=101):
	noise_array = (np.random.rand(num) * noise * 2) - noise
	output = [val + j for j in noise_array]
	return output

def ufloat_from_noise(val, noise, desc=None, num=101):
	noise_array = generate_noise(val, noise, num)
	output = mu.ufloatfromsamples(noise_array, desc=desc)
	return output

def generate_fake_trx():
	#power_unc = 0.0013

	#thot = mu.ufloat(293,1.5, desc='thot')
	thot = ufloat_from_noise(293,1.5,'thot',101)
	#thot2 = ufloat_from_noise(293,1.5,'thot2',101)
	#tcold = ufloat_from_noise(78.5,1.5, 'tcold', 101)

	atn_db = mu.ufloat(10, 0.015, desc='atn_db')
	taper_db = mu.ufloat(0.125, 0.015, desc='taper_db')

	taper_atn_lin = np.power(10, (atn_db+taper_db)/10)
	taper_k = (taper_atn_lin - 1) * thot

	tmix = mu.ufloat(1000,20, desc='tmix')

	trx = tmix*taper_atn_lin + taper_k
	return trx

def generate_trx_df():
	df = pd.DataFrame()

	df['thot'] = [ufloat_from_noise(293,1.5,'thot',101) for j in range(101)]
	df['atn_db'] = mu.ufloat(10, 0.015, desc='atn_db')
	df['taper_db'] = mu.ufloat(0.125, 0.015, desc='taper_db')
	df['taper_atn_lin'] = np.power(10, (df['atn_db']+df['taper_db'])/10)
	df['taper_k'] = (df['taper_atn_lin'] - 1) * ( df['thot'] )
	df['tmix'] = mu.ufloat(1000,20, desc='tmix')
	df['trx'] = df['tmix']*df['taper_atn_lin']+df['taper_k']
	return df

if __name__ == '__main__':
	exa = connect_exa()
	pico = connect_picoscope(1)
	temps = []
	datas = []

	meas_delay = float(exa.get_sweep_time())

	for j in range(2):
		temps.append(get_temperature(pico,1))
		time.sleep(meas_delay)
		datas.append(get_exa_data(exa))