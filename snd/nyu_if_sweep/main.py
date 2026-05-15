

from agilent_signal_analyzer import PXA
from agilent_signal_generator import PSG
import numpy as np
import time
import pandas as pd

if __name__ == '__main__':

	sa = PXA()
	sg = PSG(address=19)

	# user needs to set up the two LO sources

	if_start_ghz = 4
	if_stop_ghz = 8
	if_step = 0.5

	power_start = -20
	power_stop = 18
	power_step = 0.5

	fsweep_range = np.arange(if_start_ghz, if_stop_ghz+if_step, if_step)
	psweep_range = np.arange(power_start, power_stop+power_step, power_step)

	sg.power_on()

	sa.preset()
	sa.set_center_freq(if_start_ghz*1e3)
	sa.set_span(1)
	sa.marker_setcf(if_start_ghz*1e3)
	sa.marker_setbandwidth(0.1)
	sa.set_trace_detector('AVER')
	sa.set_rbw(5000)

	sweep_time = float( sa.get_sweep_time() ) *1.2

	df = pd.DataFrame(columns=['if freq (ghz)','psg power (dbm)','cable loss (db)','input power(dbm)','output power(dbm)','gain(db)'])
	cable_loss = pd.read_csv('cable_loss.csv', index_col=0)
	loss_dict = {}

	count = 0

	for if_freq in fsweep_range:
		loss_dict[if_freq] = np.interp(x=if_freq*1e9,xp=cable_loss.index,fp=cable_loss.values.flatten())

	for if_freq in fsweep_range:
		sg.set_power(-20)
		sg.set_frequency(if_freq)
		sa.set_center_freq(if_freq*1e3)
		sa.marker_setcf(if_freq*1e3)

		for power_level in psweep_range:

			sg.set_power(power_level)

			time.sleep(sweep_time)

			output_power = float( sa.marker_getvalue() )
			print(output_power)

			loss = loss_dict[if_freq]
			input_power = power_level+loss
			gain = output_power - input_power
			df.loc[count] = [if_freq, power_level, loss, input_power, output_power, gain]
			count+=1
			
	sg.power_off()
	df.to_csv('output.csv')