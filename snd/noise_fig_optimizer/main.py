from .noise_analyzer import NXA
from. noise_powersupply import NSU
import numpy as np
import pandas as pd
import time


def get_data(nxa):
    nf_data = nxa.read_unc_noisefigure()
    cf = nxa.get_center_freq()
    span = nxa.get_span()

    numpoints = len(nf_data)
    fstart = float(cf)-float(span)/2
    fstop = float(cf)+float(span)/2

    xaxis = np.linspace(fstart, fstop, numpoints)

    df = pd.DataFrame(nf_data,xaxis)

    return df


if __name__ == '__main__':

    nxa = NXA()
    nsu = NSU()
    nxa.inst.timeout = 25000

    num_points = 11

    vd_range = np.linspace(1.3,1.6,num_points)
    vc_range = np.linspace(0.5,0.9,num_points)
    vg_range = np.linspace(0.05,0.4,num_points)

    dfs = []

    for vd in vd_range:
        nsu.set_voltdef(1, vd)
        for vc in vc_range:
            nsu.set_voltdef(2, vc)
            for vg in vg_range:
                nsu.set_voltdef(3, vg)

                print(f'vd: {vd}\n vc: {vc}\n vg: {vg}')

                time.sleep(0.1)
                df = get_data(nxa)

                df['vd']=vd
                df['vc']=vc
                df['vg']=vg

                dfs.append(df)
    

    out = pd.concat(dfs)
    out.to_csv('out.csv')