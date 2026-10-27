import wx
import pandas as pd
import numpy as np
import os
from compressiongui import compressionGUI

#added the compression sweep functions to this local copy of network_analyzer.py
#normally found in vdi_ssp.util.vi.network_analyzer
from network_analyzer import PNA
from FileReader import readFile

import time

import plotly.express as px
import plotly.offline as po

import matplotlib.pyplot as plt



#helper functions
def get_traces(pna):
    #this only works for frequency sweeps the way I formatted it afterwards
    pna.sweep()
    sweep_dict = pna.get_wq()
    df = pd.DataFrame.from_dict(sweep_dict)
    #the units of this are Freq(Hz)
    #and default index is 0-np
    df.index = df['Freq(Hz)']
    df.index = df.index/1e9
    df.index.name='Freq(GHz)'
    df = df.drop('Freq(Hz)',axis=1)
    
    return df

def get_psweep_trace(pna):
    #this is for power sweeps
    pna.sweep()
    sweep_dict = pna.get_wq()
    df = pd.DataFrame.from_dict(sweep_dict)
    #the units of this are Freq(Hz)
    #and default index is 0-np
    df.index = df['Freq(Hz)']
    df.index.name='Power(dB)'
    df = df.drop('Freq(Hz)',axis=1)
    
    return df

def pinforComp(s, cpoint=1):
    sp = s.dropna().reset_index()
    if len(sp) < 1: 
        return np.nan
    
    sps = sp.set_index(sp.columns[1]).sort_index()
    pcin = np.interp(-cpoint,sps.index,sps['Pin(dBm)'])
    
    sp['diff'] = np.abs(sp['Pin(dBm)']-pcin)
    pcini=sp['Pin(dBm)'].iloc[sp['diff'].idxmin()]
    
    return(pcini)

def findPout(s, pin):
    if np.isnan(pin):
        return np.nan
    else:
        return s.loc[pin]

#variable names to help with autofill?
# fstart_ghz
# fstop_ghz
# f_npts

# vnax_pmin
# vnax_pmax
# vnax_pstep

# vnax_p3power
# vnax_p4power

# rfmin_dbm
# rfmax_dbm

# compression_max_rf

# tpp_string
# vnax_rbw_hz
# outputdir
# debug_fname
# comp_fname
# debugwindow

# powercalexists



class CompressionTest( compressionGUI ):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pna=None

    def import_from_vna(self):
        if not self.pna:
            self.pna = PNA(timeout_ms=5000)
        self.vnax_fstart_ghz = self.pna.f_start / 1e9
        self.vnax_fstop_ghz = self.pna.f_stop / 1e9

        self.vnax_p1power = int( self.pna.get_power_level(port=1) )
        self.vnax_p3power = int( self.pna.get_power_level(port=3) )
        self.vnax_p4power = int( self.pna.get_power_level(port=4) )

    def initVNA(self, event ):
        if not self.pna:
            self.pna = PNA(timeout_ms=5000)
        self.pna.delete_all_meas()
        self.pna.set_sweep_type('LIN')

        self.pna.if_bw = float(self.vnax_rbw_hz.GetValue())

        self.pna.create_meas('R1_1','R1_1',True)
        self.pna.create_meas('S21','S21',True)
        self.pna.set_display_format_all('mlog')
        self.pna.set_correction_state(0)
        self.pna.continuous=True

        self.pna.f_start = self.vnax_fstart_ghz * 1e9
        self.pna.f_stop = self.vnax_fstop_ghz * 1e9
        self.pna.f_npoints = int(self.f_npts.GetValue())

        self.pna.pow_couple(state=0)

    def run_tpp_adjust(self, event):
        current_wq = get_traces(self.pna)
        tpp_adjust = self.max_r1 - current_wq["R1_1"]


        #this creates self.tppdf
        #have to reload it in case user clicks the button twice
        self.load_tpp_file()

        interpolated_adjust = np.interp(self.tppdf.index, current_wq.index,\
            tpp_adjust, left=np.nan,right=np.nan)

        self.tppdf['Original TPP(dBm)'] = self.tppdf['Power(dBm)']
        self.tppdf['Power(dBm)'] = self.tppdf['Original TPP(dBm)'] - interpolated_adjust


    def load_tpp_file(self):
        tppfile = self.tpp_string.GetPath()
        self.tppdf = readFile(tppfile)
        #force first column to be named Power(dBm)
        self.tppdf = self.tppdf.rename(columns={self.tppdf.columns[0]:'Power(dBm)'})

    def plot_adjusted_tpp(self, event):
        self.tppdf.plot()
        plt.show()

    def find_appropriate_input_powers(self, event):
        self.import_from_vna()
        self.initVNA(event)

        self.tppdf = None
        
        self.pna.pow_couple(state=0)
        self.pna.power_on()

        #assume that the vna is already set up at maximum power
        max_wq = get_traces(self.pna)

        #save the max trace, in case we need to calibrate the VAR out
        self.max_r1 = max_wq["R1_1"]

        p1_max_power = int( self.pna.get_power_level(port=1) )
        ideal_max_power = p1_max_power
        ideal_min_power = -30
        max_power_found = False

        STEP_SIZE = 1
        GOAL_DELTA = 0.1
        OUTPUT_MIN_POWER = -45

        power_range = np.arange(p1_max_power, ideal_min_power, -1*STEP_SIZE)

        for power_level in power_range:
            self.pna.set_power_level(power_level,port=1)
            wq = get_traces(self.pna)

            max_delta_wq = abs( max_wq["R1_1"]-wq["R1_1"] ).max()
            if max_delta_wq > GOAL_DELTA:
                if not max_power_found:
                    ideal_max_power = power_level + STEP_SIZE
                    max_power_found = True

            if wq["R1_1"].max() < OUTPUT_MIN_POWER:
                break

        ideal_min_power = power_level

        self.vnax_pmin.SetValue(str(ideal_min_power))
        self.vnax_pmax.SetValue(str(ideal_max_power))

        self.pna.set_power_level(self.vnax_p1power, port=1)

    def runPowerSweep(self, event ):
        self.initVNA(event)

        if self.tppdf == None:
            self.load_tpp_file()
        
        maxdf = get_traces(self.pna)


        maxdf['tpp(dBm)'] = np.interp(maxdf.index,
            self.tppdf.index,
            self.tppdf['Power(dBm)'],
            left=np.nan,
            right=np.nan)
        maxdf['cf'] = maxdf['tpp(dBm)']-maxdf['R1_1']

        pstart = float(self.vnax_pmax.GetValue())
        pstop = float(self.vnax_pmin.GetValue())
        pstep_mag = abs(float(self.vnax_pstep.GetValue()))

        psweep = np.arange(pstart, pstop, pstep_mag*-1)

        #it was confusing to have the user specify the "minimum possible max value"
        #maxdf['goalmax_dbm'] = float(self.rfmax_dbm.GetValue())
        
        #instead just set it to ~20db down from maximum TPP
        #if the tppdf has been adjusted by the VAR, this still works

        POWER_CAL_OFFSET = 20
        maxdf['goalmax_dbm'] = self.tppdf['Power(dBm)'].max() - POWER_CAL_OFFSET

        #confusing to set the min. power into DUT as well, just set it to ~10dB below the max power.
        POWER_CAL_RANGE = 10
        maxdf['goalmin_dbm'] = maxdf['goalmax_dbm'] - POWER_CAL_RANGE

        maxdf['goal_r1'] = maxdf['goalmax_dbm']-maxdf['cf']
        maxdf['goal_r1_min'] = maxdf['goalmin_dbm']-maxdf['cf']

        self.power_df = pd.DataFrame()

        for k in psweep:

            self.pna.pow_ampl(k,1)
            tempdf = get_traces(self.pna)
            self.power_df[f'{k}'] = tempdf['R1_1']

            if (tempdf['R1_1'] < maxdf['goal_r1']).all():
                break

        maxinputpower = k

        psweep2 = np.arange(pstop,maxinputpower,pstep_mag*10)

        for k in psweep2:

            self.pna.pow_ampl(k,1)
            tempdf = get_traces(self.pna)
            self.power_df[f'{k}'] = tempdf['R1_1']

            if (tempdf['R1_1'] > maxdf['goal_r1_min']).all():
                break

        self.power_df.columns = self.power_df.columns.astype(float)
        self.power_df = self.power_df.reindex(sorted(self.power_df.columns),axis=1)

        fname = self.debug_fname.GetValue()

        outdir = self.outputdir.GetPath()

        self.power_df.to_csv(os.path.join(outdir,f'{fname}_debug_raw_power_df.csv'))
        self.tppdf.to_csv(os.path.join(outdir,f'{fname}_debug_tpp.csv'))
        maxdf.to_csv(os.path.join(outdir,f'{fname}_debug_initial_sweep.csv'))

        for k in self.power_df:
            self.power_df[k] = self.power_df[k]+maxdf['cf']
        self.power_df.to_csv(os.path.join(outdir,'debug_power_df.csv'))

        self.maxdf = maxdf.copy()
        self.powercalexists.SetValue(True)

    def checkSetup(self, event):

        #generate the min/max power from VNA and into DUT
        #output into debugwindow
        rf_max = float(self.compression_max_rf.GetValue())
        rf_min = rf_max - 60

        pdft = self.power_df.T
        df = pd.DataFrame()
        df.index = self.power_df.index

        df['min'] = pdft[pdft > rf_min].idxmin()
        df['max'] = pdft[pdft < rf_max].idxmax()

        dft = df.T
        out = []
        self.power_lookup_min = {}
        self.power_lookup_max = {}

        #print(dft)

        for k in dft:
            #k is frequency (ghz)
            minx = dft[k]['min'] #pna power
            maxx = dft[k]['max'] #pna power max

            miny = self.power_df[minx][k]
            maxy = self.power_df[maxx][k]

            self.power_lookup_min[k] = minx
            self.power_lookup_max[k] = maxx

            out.append(f'{k}: vna_out [{round(minx,3)},{round(maxx,3)}], amp_in [{round(miny,3)},{round(maxy,3)}]')

        self.debugwindow.SetValue("\n".join(out))

    def runCompSweep(self, event):
        self.checkSetup(event)
        
        #switch to power sweeps
        self.pna.set_sweep_type('POW')
        self.pna.set_p_start(1,-30)
        self.pna.set_p_start(1,-29)
        self.pna.f_npoints = int(self.psweep_npoints.GetValue())
        self.pna.if_bw = int(self.psweep_rbw.GetValue())

        self.pna.set_p_start(3, self.vnax_p3power )
        self.pna.set_p_start(4, self.vnax_p4power )
        self.pna.set_p_stop(3, self.vnax_p3power )
        self.pna.set_p_stop(4, self.vnax_p4power )

        fsweep = np.linspace(self.vnax_fstart_ghz,
            self.vnax_fstop_ghz,
            int(self.f_npts.GetValue()))

        alldfs = []

        for k in fsweep:
            self.pna.set_frequency_cw(k*1e9)
            self.pna.set_p_start(1,self.power_lookup_min[k])
            self.pna.set_p_stop(1,self.power_lookup_max[k])

            tempdf = get_psweep_trace(self.pna)

            tempdf['R1(dBm)'] = tempdf['R1_1']+self.maxdf['cf'][k]
            tempdf['S21(caled)'] = tempdf['S21']-self.maxdf['S21'][k]
            tempdf['frequency(ghz)'] = k
            alldfs.append(tempdf)

        outputdir = self.outputdir.GetPath()
        fname = self.comp_fname.GetValue()

        outputdf = pd.concat(alldfs)
        outputdf.to_csv(os.path.join(outputdir,fname))

    def loadHtmlFilePath( self, event ):
        self.html_outputdir.SetPath( self.outputdir.GetPath() )

    def compileHtml( self, event ):
        ssbackoff = float(self.ssbackoff.GetValue()) # dBm off the minimum variance   

        inputfile = self.html_inputfile.GetPath()
        basename = os.path.splitext(os.path.split(inputfile)[1])[0]
        
        # Add to GUI
        psatin = float(self.psat_input_power.GetValue()) # dBm (Power for saturation measurement)
        #######################
        psatcol = 'Psat@{:.1f}dBm'.format(float(psatin))

        df = pd.read_csv(inputfile,index_col=0)
        #rename R to Pin
        df = df.rename({'R1(dBm)':'Pin(dBm)'}, axis=1)

        # Raw output powers
        df['P(dBm)']=df['Pin(dBm)']+df['S21(caled)']
        fig = px.line(df,x=df['Pin(dBm)'],y=df['P(dBm)'],color='frequency(ghz)', 
                      title='Output Power vs Input Power')   
        fig.update_layout(xaxis_title='Input Power (dBm)', 
                          yaxis_title='Output Power (dBm)') 

        df['ssGain(dB)'] = 0
        flist = np.unique(df['frequency(ghz)'])
        f = flist[0]

        pgrid = np.linspace(round(df['Pin(dBm)'].min()), round(df['Pin(dBm)'].max()), 1001)

        # Slice on Frequency and interpolate S21 onto 
        dfg = pd.DataFrame()
        for f in flist:
           
            dfs = df.loc[df['frequency(ghz)']==f]
            dfs = dfs.set_index('Pin(dBm)')
            
            # get the min variance and find small signal gain        
            dfs['var'] = dfs['S21(caled)'].rolling(window=100).var() # close enough
            maxvari = dfs['var'].idxmax()      
            minvari = dfs['var'].loc[dfs.index<maxvari].idxmin()  # SS-gain at lower powers
            ssgain = dfs['S21(caled)'].loc[dfs.index<=minvari+ssbackoff].mean() 
            
            # build up the pin gridded slice
            dfgs = pd.DataFrame(index=pgrid)
            dfgs['S21(caled)'] = np.interp(dfgs.index, dfs.index, dfs['S21(caled)'],left=np.nan, right=np.nan)
            dfgs['frequency(ghz)'] = f
            dfgs['ssgain(dB)'] = ssgain
            
            dfg = pd.concat([dfg,dfgs.reset_index().rename(columns={'index':'Pin(dBm)'})])

        dfg['compression(dB)'] = dfg['S21(caled)']-dfg['ssgain(dB)']
        dfg['Pout(dBm)'] = dfg['S21(caled)']+dfg['Pin(dBm)']

        # Plot compression curves normalized to ss-gain
        fig2 = px.line(dfg,x=dfg['Pin(dBm)'],y=dfg['compression(dB)'],color='frequency(ghz)',
                       title='Compression vs Input Power')  
        fig2.update_layout(xaxis_title='Input Power (dBm)', 
                           yaxis_title='Compression Level (dB)') 


        # Plot the small signal gain
        dfgain = dfg.groupby('frequency(ghz)')['ssgain(dB)'].mean().to_frame()
        fig2p1 = px.line(dfgain,x=dfgain.index,y=dfgain['ssgain(dB)'],
                          title='Small Signal Gain')
        fig2p1.update_layout(xaxis_title='Frequency (GHz)', 
                             yaxis_title='Small Signal Gain (dB)') 

        ####################################
        # Find output power for a fixed input power  
        psat = []
        for f in flist:
            dfs = dfg.loc[dfg['frequency(ghz)']==f]
            
            psat.append({'frequency(ghz)':f,
                psatcol:np.interp(psatin, dfs['Pin(dBm)'], dfs['Pout(dBm)'])})
            
        dfpsat = pd.DataFrame(psat).set_index('frequency(ghz)')
        
        # Plot the output power at a specific input power
        fig2p2 = px.line(dfgain,x=dfpsat.index,y=dfpsat[psatcol], 
                         title='Output Power at {:0.1f}dBm Input'.format(psatin))
        fig2p2.update_layout(xaxis_title='Frequency (GHz)', 
                             yaxis_title='Output Power (dBm)') 

        ####################################
        # Calculate the compression points
        # pivot table to make finding the compression point easier
        dfp = dfg.pivot(index='Pin(dBm)',columns='frequency(ghz)')

        compl = np.arange(1,10.1,1)

        dfout = pd.DataFrame()
        for c in compl:
            pinforc = dfp['compression(dB)'].apply(lambda x: pinforComp(x,cpoint=c))
            poutforc = dfp['Pout(dBm)'].apply(lambda x: findPout(x, pinforc[x.name])) # NAN tolerant
            # poutforc = dfp['Pout(dBm)'].apply(lambda x: x.loc[pinforc[x.name]])
            
            dfb = pd.DataFrame([pinforc,poutforc]).T
            dfb = dfb.rename(columns={0:'PxdBin(dBm)',1:'PxdBout(dBm)'})
            dfb['Compression(dB)'] = c
            dfb = dfb.reset_index()
            
            dfout = pd.concat([dfout,dfb])

        dfout = dfout.rename(columns={'frequency(ghz)':'Frequency(GHz)'})
        fig3 = px.line(dfout,x=dfout['Frequency(GHz)'],y=dfout['PxdBout(dBm)'],
                       color='Compression(dB)',
                       title='Output Power over Compression Point')   
        fig3.update_layout(xaxis_title='Frequency (GHz)', 
                           yaxis_title='Output Power (dBm)') 

        time.sleep(1)  # Needed for some reason to get the second to last plot to work 

        fig4 = px.line(dfout,x=dfout['Frequency(GHz)'],y=dfout['PxdBin(dBm)'],
                       color='Compression(dB)',
                       title='Input Power over Compression Point') 
        fig4.update_layout(xaxis_title='Frequency (GHz)', 
                           yaxis_title='Input Power (dBm)') 

        # dfout is complete longform of compression points across frequency
        dfout.drop_duplicates().to_clipboard(excel=True, index=False, sep='\t')

        # dfcp is what CP will expect to see
        dfcp = pd.DataFrame()
        dfcp['P1dBin(dBm)'] = dfout.loc[dfout['Compression(dB)']==1].set_index('Frequency(GHz)')['PxdBin(dBm)']
        dfcp['P1dBout(dBm)'] = dfout.loc[dfout['Compression(dB)']==1].set_index('Frequency(GHz)')['PxdBout(dBm)']
        dfcp['P6dBin(dBm)'] = dfout.loc[dfout['Compression(dB)']==6].set_index('Frequency(GHz)')['PxdBin(dBm)']
        dfcp['P6dBout(dBm)'] = dfout.loc[dfout['Compression(dB)']==6].set_index('Frequency(GHz)')['PxdBout(dBm)']
        dfcp['Pmax(dBm)'] = dfout.loc[dfout['Compression(dB)']==10].set_index('Frequency(GHz)')['PxdBout(dBm)']

        dfcp['SS Gain(dB)'] = dfgain['ssgain(dB)']
        dfcp[psatcol] = dfpsat

        if self.show_html.GetValue(): #this is a bool, I checked the api
            po.plot(fig)
            time.sleep(0.5)
            po.plot(fig2)
            time.sleep(0.5)
            po.plot(fig2p1)
            time.sleep(0.5)
            po.plot(fig2p2)
            time.sleep(0.5)
            po.plot(fig3)
            time.sleep(0.5)
            po.plot(fig4)

        outputpath = self.html_outputdir.GetPath()

        po.plot(fig, filename=os.path.join(outputpath, basename+'_PinvPout.html'), auto_open=False)
        po.plot(fig2, filename=os.path.join(outputpath, basename+'_CompvPin.html'), auto_open=False)
        po.plot(fig2p1, filename=os.path.join(outputpath, basename+'_SSgain.html'), auto_open=False)
        po.plot(fig2p2, filename=os.path.join(outputpath, basename+'_Psat.html'), auto_open=False)
        po.plot(fig3, filename=os.path.join(outputpath, basename+'_PoutoCompPt.html'), auto_open=False)
        po.plot(fig4, filename=os.path.join(outputpath, basename+'_PinoCompPt.html'), auto_open=False)
        dfcp.to_csv(os.path.join(outputpath, basename+'_PsatSummary.csv'))

if __name__=='__main__':
    app = wx.App(False)
    a = CompressionTest(parent=None)
    a.Show()
    app.MainLoop()
    del app