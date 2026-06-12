import wx
import pandas as pd
import os

from recorder import btrBtn, btrTxt, btrChc, btrChk, MAIN_TEST_DATA_DIR, errMsg
from pretest import pretest, process_file, find_buildfile, pretest_info

from util.functions import readFile

from recorder.common.gui.plot import PlotWindow

#from attenuator import atten_format

# make larger overall sizer to place file dialog in
# then place file dialog which will open file to format

FRAME_MIN = (262,216)
FRAME_SIZE = (600,900)
STXT_ALIGN = 4

file_path = ""
build_file_path = "K:\build"

# app frame
class FormatFrame(wx.Frame):    
    def __init__(self, name, format_panel):
        wx.Frame.__init__(self, None, wx.ID_ANY, name, size = FRAME_SIZE)
        self.SetMinSize(FRAME_MIN)

        self.panel = wx.Panel(self)

        # not creating a notebook
        # create the main panel
        self.main_panel = format_panel(self.panel)

        # initializing the box in this frame method helped to get rid of formatting problem with all objects in top left corner
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.box.Add(self.main_panel, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        self.box.SetSizeHints(self.panel)
        self.panel.SetSizer(self.box)

        self.SetIcon(wx.Icon("J:\Engineer Directories\KDH\programs\pretesting\diode.ico"))
        self.Centre()
        self.Show()

# creating event for when formatting is done
myEVT_FRMTCOMPLETE = wx.NewEventType()
EVT_FRMTCOMPLETE = wx.PyEventBinder(myEVT_FRMTCOMPLETE, 1)

class FormatPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, size=(600,700))

        #Add order number sizer
        self.band_box = wx.BoxSizer(wx.HORIZONTAL)
        pretest_bands = ['WR6.0', 'WR6.5', 'WR8.0', 'WR8.6', 'WR9.0', 'WR10.0', 'WR12.0', 'WR15.0']
        self.band_chc = btrChc(self, choices=pretest_bands, choice='WR10.0', func=self.updateBand, size=(70,-1))
        self.start_txt = btrTxt(self, tag='Start (GHz)', value=str(75), size=(36,-1), datatype=float, style=wx.TE_CENTRE)
        self.stop_txt = btrTxt(self, tag='Stop (GHz)', value=str(110), size=(36,-1), datatype=float, style=wx.TE_CENTRE)
        components = ['IAMC', 'VDIC', 'SHM']
        self.comp_chc = btrChc(self, choices=components, func=self.updateComp, size=(70,-1))
        self.band_box.AddMany([(0,0,1),(wx.StaticText(self, label='Band: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN), (self.band_chc,1,wx.RIGHT,10),
                         (0,0,1), (wx.StaticText(self, label='Freq Range:'),0,wx.TOP|wx.RIGHT,STXT_ALIGN),
						 (self.start_txt,0,0,0), (wx.StaticText(self, label='-'),0,wx.TOP,STXT_ALIGN), (self.stop_txt,0,0,0),
						 (wx.StaticText(self, label='GHz'),0,wx.TOP|wx.LEFT,STXT_ALIGN), (0,0,1),
                         (wx.StaticText(self, label='Component: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN), (self.comp_chc,1,wx.RIGHT,10),
                         (0,0,1)])

        self.pretest_file_box = wx.BoxSizer(wx.HORIZONTAL)
        self.pretest_file_txt = btrTxt(self, hint='Choose a .csv or .dat file to format', size=(285,-1))
        pretest_file_btn = btrBtn(self, label='Select', func=self.selectPretestFile)
        pretest_file_btn.txt = self.pretest_file_txt
        pretest_file_btn.label = 'Pretest File'
        self.pretest_file_box.AddMany([(wx.StaticText(self, label='Pretest Data:'),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.pretest_file_txt,0,0,1),(pretest_file_btn,0,0,1)])

        self.build_box = wx.BoxSizer(wx.HORIZONTAL)
        self.build_file_txt = btrTxt(self, hint='Choose a build .txt file', size=(285,-1))
        build_file_btn = btrBtn(self, label='Select', func=self.selectPretestFile)
        build_file_btn.txt = self.build_file_txt
        build_file_btn.label = 'Build File'
        self.build_box.AddMany([(16,0,0),(wx.StaticText(self, label='Build File:'),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.build_file_txt,0,0,1),(build_file_btn,0,0,1)])

        self.setup_box = wx.StaticBoxSizer(wx.VERTICAL, self, "File Entry")
        self.setup_box.AddMany([(0,8,0), (self.band_box,0,wx.ALIGN_CENTER|wx.ALL,4),
                                (0,8,0), (self.pretest_file_box,0,wx.ALL|wx.ALIGN_CENTER,4),
                                (0,8,0), (self.build_box,0,wx.ALL|wx.ALIGN_CENTER,4),])

        #Add buttons for loading and inputting files
        self.load_box = wx.BoxSizer(wx.HORIZONTAL)
        load_file_btn = btrBtn(self, label='Load Info', func=self.loadInfo)
        self.load_box.AddMany([(0,0,1), (load_file_btn,0,0,1), (0,0,1)])

        #Add small text explainer
        self.explainer_text = wx.StaticText(self, label ="Load Info will display all the information found from pretesting and build files. Input Data will place it in the appropriate tracking document.")
        self.explainer_text.Wrap(400)

        #Create sizers for block info
        self.basic_info = wx.BoxSizer(wx.HORIZONTAL)
        self.block_txt = btrTxt(self, hint='RX_BX-XXX', size=(75, -1))
        self.rev2_txt = btrTxt(self, hint='A', size=(30, -1))
        self.type_txt = btrTxt(self, hint='M6', value='M6', size=(30, -1))
        self.tech_txt = btrTxt(self, hint='DBE', size=(40, -1))
        self.basic_info.AddMany([(wx.StaticText(self, label='Block: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.block_txt,2,wx.RIGHT,10),(8,0,0),
                                   (wx.StaticText(self, label='(X): '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.rev2_txt,1,wx.RIGHT,10),(20,0,0),
                                (wx.StaticText(self, label='Type: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.type_txt,1,wx.RIGHT,10),(8,0,0),
                                (wx.StaticText(self, label='Tech: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.tech_txt,1,wx.RIGHT,10)])
        
        #Create sizer for other info
        self.tsc_info = wx.BoxSizer(wx.HORIZONTAL)
        self.tsc_lot_txt = btrTxt(self, hint='20XXXXXX', size=(80,-1))
        self.tsc_info.AddMany([(wx.StaticText(self, label='TSC Lot: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.tsc_lot_txt,1,wx.RIGHT,STXT_ALIGN),(44,0,0)])
        
        #Create sizers for current info
        self.current_info = wx.BoxSizer(wx.HORIZONTAL)
        self.rf_off_txt = btrTxt(self, hint='XXX', size=(50,-1))
        self.rf_on_txt = btrTxt(self, hint='XXX', size=(50,-1))
        self.current_info.AddMany([(wx.StaticText(self, label='Current (mA)'),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(105,0,0),
                                   (wx.StaticText(self, label='RF Off: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.rf_off_txt,1,wx.RIGHT,10),(21,0,0),
                                (wx.StaticText(self, label='RF On: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.rf_on_txt,1,wx.RIGHT,10)])
        
        #Create sizers for RF info
        self.rf_info = wx.BoxSizer(wx.HORIZONTAL)
        self.typical_txt = btrTxt(self, hint='XX.XX', size=(50,-1))
        self.minimum_txt = btrTxt(self, hint='XX.XX', size=(50,-1))
        self.rf_info.AddMany([(wx.StaticText(self, label='RF Output (dBm)'),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(30,0,0),
                                   (wx.StaticText(self, label='Typical (Median): '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.typical_txt,1,wx.RIGHT,10),
                                (wx.StaticText(self, label='Minimum: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.minimum_txt,1,wx.RIGHT,10)])
        
        self.checkbox_info = wx.BoxSizer(wx.HORIZONTAL)
        self.partgood_chk = btrChk(self, state=False)
        self.tscgood_chc = btrChc(self, choices=['Yes', 'No', 'Unclear'], choice='Unclear', size=(70,-1))
        self.oscillation_chk = btrChk(self, state=False)
        self.checkbox_info.AddMany([(wx.StaticText(self, label='Part Good? '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.partgood_chk,0,wx.TOP|wx.RIGHT,STXT_ALIGN),(16,0,0),
                                (wx.StaticText(self, label='DC Oscillation? '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.oscillation_chk,0,wx.TOP|wx.RIGHT,STXT_ALIGN),(16,0,0),
                                (wx.StaticText(self, label='TSC Good? '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.tscgood_chc,0,wx.TOP|wx.RIGHT,STXT_ALIGN)])
        
        #Create sizer for notes info
        self.notes_info = wx.BoxSizer(wx.HORIZONTAL)
        self.comment_txt = btrTxt(self, hint='Comments on this revision', style=wx.TE_MULTILINE, size=(480,-1))
        self.notes_info.AddMany([(wx.StaticText(self, label='Notes: '),0,wx.TOP|wx.RIGHT,2),(self.comment_txt,0,0,STXT_ALIGN)])
        
        #Create sizer for date tested / link info
        self.last_info = wx.BoxSizer(wx.HORIZONTAL)
        self.date_built_txt = btrTxt(self, hint='XX\\XX\\20XX', size=(80, -1))
        self.date_tested_txt = btrTxt(self, hint='XX\\XX\\20XX', size=(80, -1))
        self.link_txt = btrTxt(self, hint='W:\Test Data\Engineer', size=(140, -1))
        self.last_info.AddMany([(wx.StaticText(self, label='Date Built: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.date_built_txt,1,wx.RIGHT,10),
                                  (wx.StaticText(self, label='Date Tested: '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.date_tested_txt,1,wx.RIGHT,10),
                                   (wx.StaticText(self, label='Link? '),0,wx.TOP|wx.RIGHT,STXT_ALIGN),(self.link_txt,2,wx.RIGHT,10)])
        
        self.rf_box = wx.StaticBoxSizer(wx.VERTICAL, self, 'RF Info')
        self.rf_box.AddMany([(0,8,0), (self.current_info,0,wx.ALIGN_LEFT|wx.ALL,4),
                                (0,8,0), (self.rf_info,0,wx.ALIGN_LEFT|wx.ALL,4),
                                (0,8,0), (self.checkbox_info,0,wx.ALIGN_LEFT|wx.ALL,4)])
        self.load_file_btn = btrBtn(self, label='Plot RF Data', func=self.plotRF)
        #Create another separate sizer for file info.
        self.info_box = wx.StaticBoxSizer(wx.VERTICAL, self, 'Data Entry')
        self.info_box.AddMany([(0,8,0), (self.basic_info,0,wx.ALIGN_LEFT|wx.ALL,4),
                                (0,8,0), (self.tsc_info,0,wx.ALIGN_LEFT|wx.ALL,4),
                                (0,8,0), self.rf_box, self.load_file_btn,
                                (0,8,0), (self.notes_info,0,wx.ALIGN_LEFT|wx.ALL,4),
                                (0,8,0), (self.last_info,0,wx.ALIGN_LEFT|wx.ALL,4),
                                (0,8,0)])
        
        self.input_box = wx.BoxSizer(wx.HORIZONTAL)
        input_file_btn = btrBtn(self, label='Input Data', func=self.inputPretestFile)
        self.input_box.AddMany([(0,0,1), (input_file_btn,0,0,1), (0,0,1)])

        self.fields_txt_list = [self.block_txt, self.rev2_txt, self.type_txt, self.tech_txt, self.tsc_lot_txt, self.rf_off_txt, self.rf_on_txt, self.typical_txt, self.minimum_txt,
                                  self.partgood_chk, self.tscgood_chc, self.oscillation_chk, self.comment_txt, self.date_built_txt, self.date_tested_txt, self.link_txt]

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.AddMany([(self.setup_box,0,wx.ALL|wx.CENTER,10), (self.load_box,0,wx.ALL|wx.CENTER,10),
                        (self.explainer_text,0,wx.ALL|wx.CENTER,10), (self.info_box,0,wx.ALL|wx.CENTER,10),
                        (self.input_box,0,wx.ALL|wx.CENTER,10)])
        
        self.SetSizer(self.box)
        
    def plotRF(self, event):
        filepath = self.pretest_file_txt.GetValue()
        if os.path.isfile(filepath):
            df = readFile(filepath)
            return PlotWindow(parent = self, data={'RF Power dBm': df}, title = f'TPP: {filepath}', name='TPP')

    #Ran when the 'Load Info' button is pressed
    def loadInfo(self, event):

        load_btn = event.GetEventObject()
        pretest_file_path = self.pretest_file_txt.GetValue() 

        settings = []
        build_file = None
        rf_info = None
        band = self.band_chc.GetValue()
        build_file_path = self.build_file_txt.GetValue()
        start = self.start_txt.GetValue()
        stop = self.stop_txt.GetValue()

        self.clearBoxes()

        if ('.txt' in build_file_path): #if we have a build .txt file already
            build_file = find_buildfile(parent = self, path = build_file_path)
            #returns df of build file info if found
            #we also should try to extract rf_info
            try:
                rf_info = process_file(pretest_file_path, file_type = 'csv', band = band, start = start, stop = stop, build_header = None)
            except:
                errMsg(self, msg = 'Please insert a pretest file', prompt='Cant process that file')
        else:
            #Process pretest files
            if '.dat' in pretest_file_path:
                #take header info which should already be in file --> see DBE function
                build_file = find_buildfile(parent = self, path = pretest_file_path)
                rf_info = process_file(pretest_file_path, file_type = 'dat', band = band, start = start, stop = stop)
            elif '.csv' in pretest_file_path:
                #check for build file
                try:
                    build_file = find_buildfile(parent = self, path = pretest_file_path)
                except AttributeError as error:
                    print('Attribute error when trying to find build file')
                    errMsg(self, msg = 'Please insert a build file or manually enter your build data', prompt='Cant find a build file with that block info')
                try:
                    print('build file is ' + str(build_file))
                    rf_info = process_file(pretest_file_path, file_type = 'csv', band = band, start = start, stop = stop, build_header = build_file)
                except KeyError as error: #elevate error handling to this level as we have access to wx fields
                    print('key error')
                    errMsg(self, msg = 'Please insert a build file or manually enter your build data', prompt='Cant find a build file with that block info')
                    return
            else:
                end_msg = wx.MessageBox(message = "Please select a .csv or .dat pretesting file", caption = "File Error", style = wx.ICON_ERROR)
                return
        #if not, attempt to load build info
        #extract rest of info from pretesting file

        #let's assume we have some build info -- what's left is to process the rest of the data
        print('rf info is ' + str(rf_info))
        print('build info is ' + str(build_file))

        self.update_BuildInfo(build_info = build_file, rf_info = rf_info)

    # Clears all values contained in wx fields in the GUI
    def clearBoxes(self):

        #set every field in the GUI to be an empty string before re-inputting data
        for field_txt in self.fields_txt_list:
            try: field_txt.SetValue("")
            except TypeError as Error: #in the case it is a check box, set value to False as opposed to empty string
                field_txt.SetValue(False) 
            except Exception as Error:
                print('could not set that field to be empty')

    def update_BuildInfo(self, build_info, rf_info):
        #basically take fields from loadBuildFile and place them in appropriate wx fields

        pretest_info[self.band_chc.GetValue()]['type_default']

        #if there is only block info, or just RF info (3 fields)
        if (rf_info == None) or (len(rf_info) == 3):
            #assume info is coming from .txt file --> build_info
            try: self.block_txt.SetValue(build_info['block'])
            except: print('could not find block name')
            try: self.rev2_txt.SetValue(build_info['block x'])
            except: print('could not find block letter')
            try: 
                if (build_info['type'] == ""):
                    self.type_txt.SetValue(pretest_info[self.band_chc.GetValue()]['type_default'])
                else:
                    self.type_txt.SetValue(build_info['type'])
            except: print('could not find block type')
            try: self.tech_txt.SetValue(build_info['technician'])
            except: print('could not find technician')
            try: self.date_built_txt.SetValue(build_info['date built'])
            except: print('could not find date built')
            try: self.tsc_lot_txt.SetValue(build_info['TSC lot'])
            except: print('could not find TSC lot #')
            try: self.date_tested_txt.SetValue(build_info['date tested'])
            except: print('could not find date tested')

            try: self.typical_txt.SetValue(str(rf_info['typ'])) 
            except KeyError as Error: print('could not find typical RF power')
            try: self.minimum_txt.SetValue(str(rf_info['min'])) 
            except KeyError as Error: print('could not find minimum RF power')
            try: self.rf_off_txt.SetValue(str(rf_info['current RF off']))
            except KeyError as Error: print('could not find RF off current')

        else: #try to set value but just print message if not there
            try: 
                self.block_txt.SetValue(rf_info['block']) 
            except KeyError as Error: print('could not find block name')
            try: 
                self.rev2_txt.SetValue(rf_info['block x']) 
            except KeyError as Error: print('could not find block letter')
            try: 
                if (rf_info['type'] == ""):
                    self.type_txt.SetValue(pretest_info[self.band_chc.GetValue()]['type_default'])
                else:
                    self.type_txt.SetValue(rf_info['type'])
            except KeyError as Error: print('could not find block type')
            try: self.tech_txt.SetValue(rf_info['technician']) 
            except KeyError as Error: print('could not find technician')
            try: self.date_built_txt.SetValue(rf_info['date built']) 
            except KeyError as Error: print('could not find date built')
            try: self.tsc_lot_txt.SetValue(rf_info['TSC lot']) 
            except KeyError as Error: print('could not find TSC lot #')
            try: self.typical_txt.SetValue(str(rf_info['typ'])) 
            except KeyError as Error: print('could not find typical RF power')
            try: self.minimum_txt.SetValue(str(rf_info['min'])) 
            except KeyError as Error: print('could not find minimum RF power')
            try: self.rf_off_txt.SetValue(str(rf_info['current RF off']))
            except KeyError as Error: print('could not find RF off current')    
            try: self.rf_on_txt.SetValue(str(rf_info['current RF on']))
            except KeyError as Error: print('could not find RF on current')                  

            try: self.date_tested_txt.SetValue(rf_info['date tested']) 
            except KeyError as Error: print('could not find date tested')

        try: self.link_txt.SetValue(self.pretest_file_txt.GetValue()) 
        except KeyError as Error: print('are you serious?')

    #Ran when the 'Input Data' button is pressed
    def inputPretestFile(self, event):

        input_btn = event.GetEventObject()
        band = self.band_chc.GetValue()

        #format block name to be R1_B1-07X
        if self.block_txt.GetValue() != None and self.rev2_txt.GetValue() != None: #if there is an actual string in the block_txt and rev_txt field
            if ('B' in self.block_txt.GetValue()):
                new_block_name = self.block_txt.GetValue()
            else:
                new_block_name = self.block_txt.GetValue()[0:2] + "_B" + self.block_txt.GetValue()[3:len(self.block_txt.GetValue())]
            x_name = self.block_txt.GetValue()[-1]

        if x_name.isdigit():
            x_name = 'A'

        osc_bool = self.bool_to_yorn(check_box=self.oscillation_chk)
        part_good = self.bool_to_yorn(check_box=self.partgood_chk)
        #tsc_good = self.bool_to_yorn(check_box=self.tscgood_chk)
        tsc_good = self.tscgood_chc.GetValue()

        # Block    X (A)     Type    I (mA)      Tech     Date Built      PCB Rev(hidden)    TSC Lot      Long Pad?    Typical (Median)      Minimum     Part Good?     TSC Good?     Archive?(hidden)    Notes  Date Tested  Link
        # Vb (V) --> this is in WR6.5 and WR12.0 tracking docs but no others. will be dealt with programatically

        #what of these "custom fields" should be added to the GUI? I don't think Vb or TTL = 0, PCB rev
        #need to figure out how to place all of these fields based on the band
        #these actually arent in the GUI --> sooo we can just place empty values in them? if the engineer wants to test they can add them in
        PCB_rev = ""
        TTL_0 = ""
        vb_good = ""

        #why do I need a comment in between these lines?
        rf_info_list = [new_block_name, x_name, self.type_txt.GetValue(), self.tech_txt.GetValue(), self.date_built_txt.GetValue(), self.tsc_lot_txt.GetValue(), PCB_rev, 
                          self.rf_off_txt.GetValue(), self.rf_on_txt.GetValue(), TTL_0, vb_good, self.typical_txt.GetValue(), self.minimum_txt.GetValue(), part_good, tsc_good, osc_bool,
                        self.comment_txt.GetValue(), self.date_tested_txt.GetValue(), self.link_txt.GetValue()],
        colm = ['Block', 'X', 'Type', 'Tech', 'Date Built', 'TSC Lot', 'PCB Rev', 'RF Off', 'RF On', 'TTL = 0', 'Vb (V)', 'Typical (Median)', 'Minimum', 
                  'Part Good?', 'TSC Good?', 'DC Oscillation?', 'Notes', 'Date Tested', 'Link to Data']
        
        #pretesting docs are totally rearranged --> just now need to know which fields apply to which band
        #create the dataframe the same way every time, just deal with the fields

        df = pd.DataFrame(rf_info_list, columns=colm)
        print(df)

        path = pretest_info[band]['link']
        #example_file_path = "J:\\Engineer Directories\\KDH\\programs\\pretesting\\9p0IAMC-HP_Tracking PERMANENT.xlsx"
        #reader = pd.read_excel(path), why cant i use this?
        reader = pd.read_excel(path)

        sheet_name = band[2:len(band)] + "IAMC-HP"
        print('writing to sheet ' + str(sheet_name))

        #try to access the pretest document
        #writer = pd.ExcelWriter("J:\Engineer Directories\KDH\programs\pretesting\9p0IAMC-HP_Tracking KDH Copy.xlsx", mode='a', if_sheet_exists='replace')
        with pd.ExcelWriter(path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=len(reader)+1)
            #specify the name of the sheet to write to

        end_msg = wx.MessageBox(message="Your pretest file is entered! ;D", caption="Cheers", style= wx.OK | wx.CENTRE)

        return
    
    def bool_to_yorn(self, check_box):

        if check_box.GetValue() == False:
            return_val = 'N'
        else:
            return_val = 'Y'

        return return_val

    def selectPretestFile(self, event):

        FILE_SELECT_DIR = MAIN_TEST_DATA_DIR

        file_select_box = event.GetEventObject()
        if (file_select_box.label == "Build File"):
            FILE_SELECT_DIR = "K:\\build"

        with wx.FileDialog(self, 'Select your pretest file', FILE_SELECT_DIR, '', '', wx.FD_OPEN|wx.FD_CHANGE_DIR) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                event.GetEventObject().txt.SetValue(dlg.GetPath())
                path = dlg.GetPath()

                file_type = path[len(path)-3:len(path)]

                if ((file_type != "csv") and (file_type != "dat") and (file_type != "txt")): # checking file is .csv, .dat, or .txt file
                    #err_msg = wx.MessageBox(message="Please select a .csv or .dat file", caption="File Error", style= wx.ICON_ERROR)
                    errMsg(self, msg = "Please select a .csv or .dat pretest file", prompt='Really?')

    #Runs when the band selection is changed
    def updateBand(self, event):    
        
        #this is being called by band_choice
        input_chc = event.GetEventObject()
        band = input_chc.GetValue()

        def_type = pretest_info[band]['type_default']
        band_start = pretest_info[band]['bounds'][0]
        band_stop = pretest_info[band]['bounds'][1]

        self.type_txt.SetValue(def_type)
        self.start_txt.SetValue(str(band_start))
        self.stop_txt.SetValue(str(band_stop))

    def updateComp(self, event):    
        pass

# main function to be run 
if __name__ == '__main__':
    app = wx.App()
    frame = FormatFrame("Pretesting Entry", FormatPanel)
    pretest()
    app.MainLoop()
    del app