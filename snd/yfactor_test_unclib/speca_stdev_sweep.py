import os
from agilent_signal_analyzer import PXA

import time
import numpy as np
import pandas as pd

import metas_unclib as mu
import mu_helper as muh

def get_stdev(pxa, num_points, meas_time, det_type='AVER'):
    start_time = time.time()
    
    pxa.set_numpoints(num_points)
    pxa.set_sweep_time(meas_time)
    pxa.set_trace_detector(det_type) #AVER or NORM
    
    pxa.inst.timeout = meas_time*3*1000 + 5000

    pxa.trigger_once()
    pxa.send_opcheck()
    
    trace = pxa.get_trace()
    val = muh.ufloatfromsamples(trace)
    
    duration = time.time()-start_time
    print(duration)
    return val.stdunc

def setup_pxa(pxa):
    pxa.preset()
    time.sleep(1)

    pxa.set_center_freq(70)
    pxa.set_span(0)

    pxa.set_rbw(8e6)
    pxa.set_vbw(1)
    
    pxa.set_continuous_mode('OFF')
    
def time_and_point_sweep(pxa):
    times = [0.1,1,10,100]
    points = [11,101,1001,10001,100001,1000001,10000001]

    # df_norms = pd.DataFrame()
    # df_norms.index = times
    # for p in points:
        # df_norms[p] = 0.0

    # df_avers = pd.DataFrame()
    # df_avers.index = times
    # for p in points:
        # df_avers[p] = 0.0

    df_samps = pd.DataFrame()
    df_samps.index = times
    for p in points:
        df_samps[p] = 0.0



    # for p in points:
        # for t in times:
            # df_norms.loc[t,p] = get_stdev(pxa,p,t,'NORM')

    # for p in points:
        # for t in times:
            # df_avers.loc[t,p] = get_stdev(pxa,p,t,'AVER')

    for p in points:
        for t in times:
            df_samps.loc[t,p] = get_stdev(pxa,p,t,'SAMP')

    # df_norms.to_csv('norms.csv')
    # df_avers.to_csv('avers.csv')
    df_samps.to_csv('samps2.csv')


if __name__ == '__main__':


    pxa = PXA()
    
    setup_pxa(pxa)

    time_and_point_sweep(pxa)
    
    # output_array = []
    
    # pxa.set_numpoints(11)
    # pxa.set_sweep_time(0.1)
    # pxa.set_trace_detector("NORM") #AVER or NORM
    
    # pxa.inst.timeout = 5000


    
    # for j in range(101):
    #     pxa.trigger_once()
    #     pxa.send_opcheck()
    
    #     trace = pxa.get_trace()
    #     output_array.append(trace)
        
    # df = pd.DataFrame(output_array)
    # df.to_csv('output_array.csv')