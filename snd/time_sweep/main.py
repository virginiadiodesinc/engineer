from snd.instrument_controllers.instrument_controller import Source, Receiver
import time
import numpy as np
import pandas as pd

MEAS_DELAY = 2
FREQUENCY = 110
HARMONIC_FACTOR = 6

class Main():

    def __init__(self):

        self.psg=Source("psg",address=19)
        self.pm5=Receiver("pm5", address="306V")
        self.hp=Source("hp6627", address=5, channel=1)

    def setup(self):
        self.psg.set_power(0)
        self.psg.set_frequency(FREQUENCY/HARMONIC_FACTOR)
        self.psg.power_on()

        self.hp.set_voltage(9)
        self.hp.set_current(1)
        self.hp.power_on()

    def take_point(self,pre_delay_s):
        time.sleep(pre_delay_s)

        self.hp.power_on()

        time.sleep(MEAS_DELAY)

        val = self.pm5.get_data()
        print(val)

        self.hp.power_off()

        return val 

if __name__ == '__main__':
    #run from base directory
    #python -m snd.time_sweep.main
    main = Main()
    main.setup()

    vals = []
    times = []

    sweep_space = np.logspace(0.01,2.5,21)

    for j in sweep_space:
        val = main.take_point(j)
        
        vals.append(val)
        times.append(j)

    df = pd.DataFrame()
    df['time_s'] = times
    df['values_mw'] = vals
    df.to_csv('out.csv')