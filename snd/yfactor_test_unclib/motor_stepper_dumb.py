import nidaqmx
from nidaqmx.constants import LineGrouping

import time
import numpy as np


class MotorController():

    def __init__(self, dev_name, stepsize=0):
        #3 = full step
        #2 = half step
        #1 = quarter step
        #0 = eighth step
        if stepsize==0:
            self.step=[False, False]
        elif stepsize==1:
            self.step=[True, False]
        elif stepsize==2:
            self.step=[False, True]
        elif stepsize==3:
            self.step=[True, True]


        num = stepsize
        one_rotation=1600

        while num > 0:
            one_rotation = one_rotation/2
            num = num-1

        self.steps_per_rot = one_rotation
        self.dev_name = dev_name
        self.task = nidaqmx.Task()
        self.task.do_channels.add_do_chan(f'{self.dev_name}/port0/line0:4', line_grouping = LineGrouping.CHAN_PER_LINE)
        self.task.write(self.step+[True, False, False])
        self.task.start()

    def step_once(self, direction):
        #0 = ccw
        #1 = cw
        
        self.task.write(self.step+[True]+[True]+[bool(direction)])
        self.task.write(self.step+[True]+[False]+[bool(direction)])

    def step_angle(self, direction, deg):
        #direction 0 or 1
        #400 full steps, 800 half steps, 1600 quarter steps, 3200 eighth steps for one rotation

        num_steps = int(np.floor(self.steps_per_rot * (deg / 360)))

        for k in range(num_steps):
            self.step_once(direction)
            time.sleep(0.01)

    def reset(self):

        self.task.write(self.step+[False]+[True]+[True])
        time.sleep(0.01)
        self.task.write(self.step+[True]+[True]+[True])

    def close(self):

        self.task.stop()
        self.task.close()

if __name__=='__main__':

    a = MotorController("Dev1",2)

    for k in range(3):
        time.sleep(1)
        a.step_angle(0,70)

        time.sleep(1)

        a.step_angle(1,70)