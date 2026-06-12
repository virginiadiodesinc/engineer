#Init file used to treat directories as packages

import wx
import numpy as np
import pandas as pd
import csv
import warnings

#Globally used paths to represent the location that data will be stored
MAIN_TEST_DATA_DIR = 'W:/Test Data'
ICON_FILE = "W:/Python3/vdi_ssp/util/static/wave.ico"

##Globally used variables for panel setup##
#Colors used for theming and status
BGND = wx.Colour(160,200,255)
STRT = wx.Colour(100,250,100)
STOP = wx.Colour(250,100,100)
BLNK = wx.Colour(-1,-1,-1,255)
PRPL = wx.Colour(100,100,255)
ORNG = wx.Colour(250,150,100)

# Change the background color to yellow if this is a dev program
if 'W:/Python3/vdi_ssp' not in __file__ and 'W:\\Python3\\vdi_ssp' not in __file__:
	BGND = wx.Colour(255,250,160)

#Panel and frame sizing
FRAME_MIN = (524,432)
FRAME_SIZE = (1400,800)
STXT_ALIGN = 4

#Reads every column of a file into a dataframe, inferring headers if
#possible and converting tpp files and frequency units appropriately
def readFile(path, get_info = False, get_header = False, correct_index = True, UCA = False):
	# Redirect .xlsx files
	if '.xlsx' in path:
		return readXLSX(path)
	
	#By default, infer the header and use no prefix
	read_frame = None
	header, prefix = 'infer', None
	columns = 2
	skiprows = 0
	
	#Will probably remove this
	if '.dat' in path:	
		DAT = True
		if 'UCA' in path:	UCA = True
	else:
		DAT = False
	
	#Determine the character to split by based on the file type
	split_char = ' ' if ((path.lower().rfind('.s1p') != -1) or (path.lower().rfind('.s2p')) != -1) else ','
	if ((path.lower().rfind('.dat') != -1)):	split_char = '\t'
	
	#Open the file to read line by line
	try:	fo = open(path, 'r')
	except FileNotFoundError as err:	raise FileNotFoundError(err)
	except Exception as err:	raise Exception("Error opening file \""+path+"\":\n"+str(err))
	
	#Quick new test to see if its one of those tab-delimited .s1p files
	text = fo.read()
	fo.close()
	if text.count('\t') > text.count(split_char):	split_char = '\t'
	
	fo = open(path, 'r')
	try:	my_file = csv.reader(fo, delimiter = split_char)
	except Exception as err:
		fo.close()
		raise Exception("Error opening file \""+path+"\":\n"+str(err))
	header_dict = {}
	for num, line in enumerate(my_file, -1):
		try:	#Check for when all non blank values can all be floats. If there are no values, go to the next line
			float_list = [float(s) for s in [v for v in line if v != '' and v != '-']]
			float_list[0]
		except:	#If not, use these items as the row column count and go to the next line
			if len(line) == 2 and len(line[0]) > 0 and line[0][-1] == ':':	header_dict[line[0]] = line[1]
			continue
		#The nunber of columns is the number of elements in this list
		columns = len(float_list)
		#If the values are on the first line of the file, then use prefixed headers
		if num < 0:	header, prefix = None, 'N'
		#Skip one under this many rows, load the file, and exit the loop
		skiprows=max(0,num)
		#Catch the "Information lost" warning for UCA files
		read_frame = pd.read_csv(path, sep=split_char, index_col=0, skiprows=skiprows, na_values='-', header=header)
		if prefix != None:	read_frame = read_frame.add_prefix(prefix)
		if UCA:
			with warnings.catch_warnings():
				warnings.simplefilter("ignore")
				read_frame = pd.read_csv(path, sep=split_char, index_col=False, skiprows=skiprows, na_values='-', header=header)
				if prefix != None:	read_frame = read_frame.add_prefix(prefix)
			read_frame.index = read_frame.pop(read_frame.columns[0])
		break
	fo.close()
	
	#If the read_frame is still None, return because no data was found
	if read_frame is None:	raise Exception(f"No data found in {path}")
	#Drop any 'END' lines (Useful for couplers)
	try:	read_frame.drop('END', axis=0, inplace=True)
	except:	pass
	#If any dataframe manipulation fails, tell the user that the file could not be read
	try:
		#Now, account for TPP files to convert units
		if 'tpp_mw' in path:	read_frame = read_frame.iloc[:,0:1].apply(mW_to_dBm)
		elif 'tpp_dbm' in path:	read_frame = read_frame.iloc[:,0:1]
		
		# Correct the index by default
		if correct_index:
			#If there is no index name, name it "Freq"
			if read_frame.index.names[0] == None or type(read_frame.index.names[0]) == int:	read_frame.index.rename("Freq", inplace=True)
			#Finally, correct frequency units
			if 'ghz' in read_frame.index.names[0].lower():
				pass
			elif 'mhz' in read_frame.index.names[0].lower():
				read_frame.index = read_frame.index.astype(float) / 1e3
			elif 'khz' in read_frame.index.names[0].lower():
				read_frame.index = read_frame.index.astype(float) / 1e6
			elif 'hz' in read_frame.index.names[0].lower():
				read_frame.index = read_frame.index.astype(float) / 1e9
			else:
				while np.mean(read_frame.index.astype(float)) > 2000:
					read_frame.index = read_frame.index.astype(float) / 1e3
			read_frame.index.rename("Frequency (GHz)", inplace=True)
		
		#Also, account for UCA files to convert format
		if UCA or DAT:
			freq_fac = 1
			info = ' '.join(read_frame.columns)
			ind = info.find('Freq fac: ')
			if ind != -1:	freq_fac = int(info[ind+10:].split(' ')[0])
			read_frame.index = read_frame.index * freq_fac
			if UCA:
				read_frame = read_frame.reset_index()
				read_frame = read_frame.pivot(index = read_frame.columns[-1], columns = read_frame.columns[0], values = read_frame.columns[1])
				read_frame.columns = [format(col, '.4f') + ' (GHz)' for col in read_frame.columns]
				#Correct "Unnamed: 5" index title
				if ':' in read_frame.index.name:	read_frame.rename_axis('UCA Input (V)', inplace=True)
	except Exception as err:	raise Exception("File \""+path+"\" opened but could not be read:\n"+str(err))
	
	#Output file data in a dict of other information if requested
	if get_info or get_header:
		out_dict = {'data': read_frame}
		if get_info:
			out_dict['start_freq'] = read_frame.index[0]
			out_dict['stop_freq'] = read_frame.index[-1]
			out_dict['points'] = len(read_frame.index)
			out_dict['header_rows'] = skiprows
			out_dict['data_columns'] = len(read_frame.columns)
		if get_header:
			out_dict['header'] = header_dict
		return out_dict
	
	return read_frame

#Reads a xlsx file into a dataframe of the first sheet
def readXLSX(path):
	dfs = pd.read_excel(path, sheet_name=None, index_col=0)
	return {k:v for k,v in dfs.items() if k != 'Header'}

#Convert from mW to dBm
def mW_to_dBm(mW):
	return 10*np.log10(np.absolute(mW))

"""=Functions that create dialog boxes to get user input or relay information to the user="""
#Displays a dialog box with error information
def errMsg(parent, prompt, msg, exception = None):
	if exception == None:
		message = msg
	else:	#Optionally pass in the actual exception to try and track down the root
		tb = exception.__traceback__
		#while tb.tb_next is not None:
		if tb.tb_next is not None:
			tb = tb.tb_next
		message = f"File: {tb.tb_frame.f_code.co_filename}\nLine: {tb.tb_lineno}\n\n{msg}"
	with wx.MessageDialog(parent, message, prompt, wx.OK|wx.ICON_ERROR|wx.STAY_ON_TOP) as dlg:
		if dlg.ShowModal() == wx.ID_OK:
			pass

#Displays a dialog box asking the user if they want to proceed
def cancelBox(parent, prompt, msg):
	with wx.MessageDialog(parent, msg, prompt, wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION|wx.CENTRE) as dlg:
		return dlg.ShowModal() == wx.ID_YES

"""===========Type definitions for wx objects with more inclusive constructors==========="""
class btrBtn(wx.Button):
	def __init__(self, parent, label, tag=None, func=None, sizer=None, **kwargs):
		super(btrBtn, self).__init__(parent=parent, label=label, **kwargs)
		self.bind(func)
		self.tag = tag
		self.sizer=sizer
	
	def bind(self, func):
		if func != None:	self.Bind(wx.EVT_BUTTON, func)
	def unbind(self):
		self.Unbind(wx.EVT_BUTTON)

class btrTgl(wx.ToggleButton):
	def __init__(self, parent, header_dict={}, tag=None, labels=['Start','Stop'], colors=[STRT,STOP], state=True, func=None, sizer=None, datatype=bool, blocked=False, **kwargs):
		super(btrTgl, self).__init__(parent=parent, **kwargs)
		self.labels = labels
		self.colors = colors
		self.sizer = sizer
		self.datatype = datatype
		self.blocked = False
		self.toggle(state)
		self.blocked = blocked
		self.bind(func)
		
		#If a header dict was passed in, bind the tag to the getValue function
		if tag != None:		header_dict[tag] = self
		
	#Toggle or set the state, and change color and label
	def toggle(self, state=None, trigger=True):
		#If the button is blocked, just return(will not trigger previously bound events)
		if self.blocked:	return	self.SetValue(~self.GetValue())
		
		#If this was triggered by its own toggle event, then dont change the state
		if hasattr(state, 'EventType') and state.GetEventObject() == self:
			event = state
			state = [True,False].index(self.GetValue())
			self.SetLabel(self.labels[state])
			self.SetBackgroundColour(self.colors[state])
			
			#Run the next bound function if there is one
			if trigger:	event.Skip()
		
		#Otherwise, set the state manually
		else:
			if state != None:	self.setValue(state)
			else:				self.setValue(~self.getValue())
			state = [True,False].index(self.GetValue())
			self.SetLabel(self.labels[state])
			self.SetBackgroundColour(self.colors[state])
	def block(self, block=True):
		self.blocked = block
	
	def getValue(self):
		if self.datatype == str:	return self.GetLabel()
		else:						return self.GetValue()
	def setValue(self, val):
		if type(val) is bool:		self.SetValue(val)
		elif val in self.labels:
			self.SetValue([True,False][self.labels.index(val)])
			evt = wx.PyCommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.GetId())
			evt.SetEventObject(self)
			self.GetEventHandler().ProcessEvent(evt)
	def bind(self, func):
		if func != None:	self.Bind(wx.EVT_TOGGLEBUTTON, func)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.toggle)
	def unbind(self):
		self.Unbind(wx.EVT_TOGGLEBUTTON)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.toggle)

class btrChc(wx.ComboBox):
	def __init__(self, parent, choices=[''], header_dict={}, tag=None, combo=False, hint='', select=0, choice=None, func=None, sizer=None, datatype=None, **kwargs):
		#If its a normal choice box, run the correct constructor and bind to the choice event
		if not combo:
			super(btrChc, self).__init__(parent=parent, choices=choices, style=wx.CB_READONLY, **kwargs)
			self.event = wx.EVT_COMBOBOX
		#If its a combobox, leave out the styling and bind to the text edit event and add the hint
		else:
			super(btrChc, self).__init__(parent=parent, choices=choices, **kwargs)
			self.event = wx.EVT_TEXT
			self.SetHint(hint)
		
		self.sizer = sizer
		self.choices = choices
		self.combo = combo
		self.datatype = datatype
		self.SetSelection(select)
		self.setValue(choice)
		self.bind(func)
		
		#If a header dict was passed in, bind the tag to the getValue function
		if tag != None:		header_dict[tag] = self
	
	def getChoices(self):
		return self.choices
	def setChoices(self, choices=['']):
		if self.combo:	typed = self.GetValue()
		self.Clear()
		self.choices = choices
		for choice in choices:
			self.Append(choice)
		self.SetSelection(0)
		if self.combo:	self.setValue(typed)
	def getValue(self):
		if self.combo:
			val = self.GetValue()
		else:
			val = self.GetString(self.GetSelection())
		if self.datatype != None:
			try:	val = self.datatype(val)
			except Exception as err:	print("User requested " + str(self.datatype) + " but this conversion cannot be made to " + val, str(err))
		return val
	def setValue(self, val=None):
		if val in self.choices:	self.SetSelection(self.choices.index(val))
		elif type(val) is int:
			self.SetSelection(val)
		else:
			try:	self.SetValue(val)
			except:	pass
		evt = wx.PyCommandEvent(self.event.typeId, self.GetId())
		evt.SetEventObject(self)
		self.GetEventHandler().ProcessEvent(evt)
	def bind(self, func):
		if func != None:	self.Bind(self.event, func)
	def unbind(self):
		self.Unbind(self.event)

class btrTxt(wx.TextCtrl):
	def __init__(self, parent, header_dict={}, tag=None, hint='', func=None, sizer=None, datatype=None, **kwargs):
		if 'value' in kwargs and kwargs['value'] == None:
			kwargs['value'] = ''
		super(btrTxt, self).__init__(parent=parent, **kwargs)
		self.SetHint(hint)
		self.bind(func)
		self.datatype = datatype
		self.sizer = sizer
		
		#If a header dict was passed in, bind the tag to the getValue function
		if tag != None:		header_dict[tag] = self
	
	def getValue(self):
		val = self.GetValue()
		if self.datatype != None:
			# Special check for ints. Allowing them to be converted from float strings
			if self.datatype is int:
				try:	val = int(float(val))
				except Exception as err:	pass
			else:
				try:	val = self.datatype(val)
				except Exception as err:	pass#print("Warning: User requested " + str(self.datatype) + " but this conversion cannot be made to " + val, str(err))
		return val
	def setValue(self, val):
		self.SetValue(str(val))
		if self.datatype != None:
			try:	self.SetValue(str(self.datatype(val)))
			except:	pass
		
	def bind(self, func):
		if func != None:	self.Bind(wx.EVT_TEXT, func)
	def unbind(self):
		self.Unbind(wx.EVT_TEXT)

class btrChk(wx.CheckBox):
	def __init__(self, parent, header_dict={}, tag=None, state=True, func=None, sizer=None, blocked=False, **kwargs):
		super(btrChk, self).__init__(parent=parent, **kwargs)
		self.sizer = sizer
		self.toggle(state)
		self.block(blocked)
		self.bind(func)
		
		#If a header dict was passed in, bind the tag to the getValue function
		if tag != None:		header_dict[tag] = self
	
	def toggle(self, state=None, trigger=True):
		#If this what triggered by its own toggle event, then dont change the state and run the next bound function if there is one
		if hasattr(state, 'EventType') and state.GetEventObject() == self:
			if trigger:	state.Skip()
		
		#Otherwise, set the state manually
		else:
			if state != None:	self.setValue(state)
			else:				self.setValue(~self.getValue())
	def block(self, block=True):
		if block:	self.Disable()
		else:		self.Enable()
	
	def getValue(self):
		return self.GetValue()
	def setValue(self, val):
		if type(val) == str:
			if 'true' in val.lower():	val = True
			elif 'false' in val.lower():	val = False
		self.SetValue(val)
	def bind(self, func):
		if func != None:	self.Bind(wx.EVT_CHECKBOX, func)
		self.Bind(wx.EVT_CHECKBOX, self.toggle)
	def unbind(self):
		self.Unbind(wx.EVT_CHECKBOX)
		self.Bind(wx.EVT_CHECKBOX, self.toggle)

"""===================================Default app frame=================================="""
#Default app frame used to house test panels
class DefaultFrame(wx.Frame):	
	def __init__(self, name, test_panel):
		wx.Frame.__init__(self, None, wx.ID_ANY, name, size=FRAME_SIZE)
		self.SetMinSize(FRAME_MIN)
		self.panel = wx.Panel(self)

		#Create the main panel
		self.main_panel = test_panel(self.panel)

		self.box = wx.BoxSizer(wx.HORIZONTAL)
		self.box.Add(self.main_panel, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

		self.box.SetSizeHints(self.panel)
		self.panel.SetSizer(self.box)

		self.SetIcon(wx.Icon(ICON_FILE))
		self.Centre()
		self.Show()




"""===================================Other GUI help objects=================================="""


# Take a wxpython gui element and add text to the left (and optionally right,) returning a list of the elements
def labelObject(parent, l_label, obj, r_obj = None, r_label = None, r_space = None):
	# Add the left text
	if type(l_label) is str:
		left_text = (wx.StaticText(parent, label=l_label),0,wx.ALIGN_CENTER|wx.TOP,2)
	elif type(l_label) is tuple:	#it is a tuple including a size
		left_text = (wx.StaticText(parent, label=l_label[0], style=wx.ALIGN_RIGHT, size=(l_label[-1],-1)),0,wx.ALIGN_CENTER|wx.TOP,2)
	else:	#assume it is a wxpython onject
		left_text = (l_label,0,wx.ALIGN_CENTER|wx.RIGHT,4)
	
	obj_list = [left_text, (obj,0,wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT,4)]
	
	# Add a separated right object if there is one
	if r_obj is not None:
		obj_list += [(wx.StaticText(parent, label='-'),0,wx.ALIGN_CENTER|wx.TOP,2), (r_obj,0,wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT,4)]
	
	# Add a label at the right if there is one
	if r_label is not None:
		if type(r_label) is str:
			obj_list.append((wx.StaticText(parent, label=r_label),0,wx.ALIGN_CENTER|wx.TOP,2))
		else:	#it is a tuple including a size
			obj_list.append((wx.StaticText(parent, label=r_label[0], style=wx.ALIGN_RIGHT, size=(r_label[-1],-1)),0,wx.ALIGN_CENTER|wx.TOP,2))
	
	# Add any spacing
	if r_space is not None:
		obj_list.append(r_space)
	
	return obj_list


class sndTextCtrl(wx.Panel):
	def __init__(self, parent, value, label, **kwargs):
		wx.Panel.__init__(self, parent, size=(-1, 30))

		self.parent = parent

		hbox = wx.BoxSizer(wx.HORIZONTAL)

		self.mytextctrl = wx.TextCtrl(self, **kwargs)
		self.mytextctrl.SetValue('%s'%value)
		self.mylabel = wx.StaticText(self, label='%s'%label, **kwargs)

		hbox.Add(self.mylabel, flag = wx.LEFT)
		hbox.Add(self.mytextctrl,proportion = 1)

		self.SetSizer(hbox)
		self.Layout()

	def SetValue(self, value):
		self.mytextctrl.SetValue( str(value) )

	def GetValue(self):
		try:
			return int( self.mytextctrl.GetValue() )
		except:
			try:
				return float( self.mytextctrl.GetValue() )
			except:
				return self.mytextctrl.GetValue()

	def SetLabel(self, value):
		self.mylabel.SetLabel(value)
