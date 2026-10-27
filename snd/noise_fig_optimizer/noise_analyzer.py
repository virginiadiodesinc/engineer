#Extends PXA to pull noise measurements
from ..instrument_controllers.agilent_signal_analyzer import PXA
import pandas as pd

class NXA(PXA):

    def __init__(self, address=18, preset=False, use_cf=False):
        super().__init__(address=address,preset=preset,use_cf=use_cf)


    def read_unc_noisefigure(self):

        return self.inst.query_ascii_values(':READ:NFIG:ARR:DATA:UNC:NFIG?')



if __name__ == '__main__':

    nxa = NXA()
    nf = nxa.read_unc_noisefigure()

    nfdf = pd.DataFrame(nf)

    nfdf.to_csv('nf.csv')